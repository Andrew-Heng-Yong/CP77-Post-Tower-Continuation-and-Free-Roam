module PTFR.SideJobPilotS1

import PTFR.RestrictionsR1.*

// A one-shot fresh native owner, not a journal-only resurrection or replay.
public class SideJobPilotS1 extends ScriptableSystem {
  private persistent let enabled: Bool;
  private persistent let schema: Int32;
  private persistent let stage: Int32; // 0 unused, 1 queued, 2 requested, 3 native running, 4 released, 5 fault
  private persistent let inflight: Bool;
  private persistent let fault: CName;
  private let running: Bool;
  private let epoch: Int32;
  private let warmup: Int32;
  private let detail: String;
  private let departureSamples: Int32;

  private func Fact(name: CName) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(name); }
  private func Set(name: CName, value: Int32) -> Void { GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(name, value); }
  private func OnAttach() -> Void { this.running = true; this.Restored(); }
  private func OnDetach() -> Void { this.running = false; this.epoch += 1; }
  public func Restored() -> Void {
    this.epoch += 1; this.warmup = 4; this.departureSamples = 0;
    if this.enabled && (this.schema != 1 || this.inflight || this.stage < 1 || this.stage > 5) {
      this.Fail(n"InterruptedOrUnsupported_NoReplay");
    }
    if this.running { this.Schedule(); }
  }
  private func Schedule() -> Void {
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(SideTick.Create(this, this.epoch), 1.0, false);
  }
  public static func Paths() -> array<String> {
    return ["quests/minor_quest/mq005_alley", "quests/minor_quest/mq005_alley/mq005_main",
      "quests/minor_quest/mq005_alley/mq005_main/01_deal_with_cops",
      "quests/minor_quest/mq005_alley/mq005_main/01_deal_with_cops/description",
      "quests/minor_quest/mq005_alley/mq005_main/02_check_on_corpo",
      "quests/minor_quest/mq005_alley/mq005_main/03_talk_to_corpo"];
  }
  public static func Classes() -> array<String> {
    return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective",
      "gameJournalQuestDescription", "gameJournalQuestObjective", "gameJournalQuestObjective"];
  }
  public static func OwnedNativeFacts() -> array<CName> {
    // Includes scene-only facts absent from the R3 questphase-only catalogue.
    return [n"mq005_done", n"mq005_police_done", n"mq005_police_left",
      n"mq005_01_admition_of_guilt", n"mq005_01_admition_of_guilt_BLOCK",
      n"mq005_01_full_story", n"mq005_block_punching_choice"];
  }
  private func State(path: String, className: String) -> Int32 {
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    let entry = jm.GetEntryByString(path, className);
    return IsDefined(entry) ? EnumInt(jm.GetEntryState(entry)) : -1;
  }
  private func PoiState() -> Int32 { return this.State("points_of_interest/minor_quests/mq005_alley", "gameJournalPointOfInterestMappin"); }
  private func NativeEligibility() -> Bool {
    // Stock minorquests path: q001_done -> q005_done -> q101_enable_side_content.
    return this.Fact(n"q001_done") > 0 && this.Fact(n"q005_done") > 0 && this.Fact(n"q101_enable_side_content") > 0;
  }
  private func UntouchedStage() -> Bool {
    let facts = SideJobPilotS1.OwnedNativeFacts();
    let paths = SideJobPilotS1.Paths(); let classes = SideJobPilotS1.Classes();
    let i = 0;
    while i < ArraySize(facts) { if this.Fact(facts[i]) != 0 { return false; }; i += 1; }
    i = 0;
    while i < ArraySize(paths) { if this.State(paths[i], classes[i]) != 1 { return false; }; i += 1; }
    return this.NativeEligibility() && !GameInstance.GetJournalManager(this.GetGameInstance()).HasAnyDelayedStateChanges();
  }
  public func FreshEvidence() -> Bool {
    // Automatic admission requires a pre-ending, available POI as well as the
    // source-audited untouched stage. Old certificates cannot invent this proof.
    return this.UntouchedStage() && this.PoiState() == 2;
  }
  private func Tower() -> Bool {
    return this.Fact(n"PostTowerFreeRoamActive") == 1 && this.Fact(n"PTFRP0_DR13") == 1 &&
      this.Fact(n"q307_done") == 1 && this.Fact(n"q307_finished") == 1 && this.Fact(n"q307_2079") == 1 &&
      this.Fact(n"q307_main_game_killed") == 1 && this.Fact(n"q307_ep1_killed") == 1 &&
      this.Fact(n"q307_active") == 0 && this.Fact(n"q115_point_of_no_return") == 0 && this.Fact(n"q305_johnny_scene_active") == 0;
  }
  private func Preflight() -> Bool {
    let poi = this.PoiState();
    return this.Tower() && this.UntouchedStage() && (poi == 1 || poi == 2) && this.Fact(n"wanted_level") == 0 &&
      this.Fact(n"PTFRS1_Ready") == 1 && this.Fact(n"PTFRS1_NativeRevision") == 1 &&
      this.Fact(n"PTFRS1_Request") == 0 && this.Fact(n"PTFRS1_Started") == 0 && this.Fact(n"PTFRS1_Fault") == 0 &&
      this.Fact(n"PTFRS1_RewardClaim") == 0 && this.Fact(n"PTFRS1_RewardAck") == 0 &&
      this.Fact(n"PTFRS1_RewardReplayRefused") == 0 && this.Fact(n"PTFRS1_OwnerFinished") == 0;
  }
  private func CompletedPoliceLeftRoute() -> Bool {
    // S1.1 recovery is deliberately limited to the observed successful route.
    // Never infer completion or set vanilla facts from a mod-owned flag alone.
    return this.enabled && this.schema == 1 && this.stage == 3 && !this.inflight && this.Tower() &&
      this.Fact(n"PTFRS1_Ready") == 1 && this.Fact(n"PTFRS1_NativeRevision") == 1 &&
      this.Fact(n"PTFRS1_Request") == 1 && this.Fact(n"PTFRS1_Started") == 1 &&
      this.Fact(n"PTFRS1_Fault") == 0 && this.Fact(n"PTFRS1_RewardReplayRefused") == 0 &&
      this.Fact(n"PTFRS1_RewardClaim") == 1 && this.Fact(n"PTFRS1_RewardAck") == 1 &&
      this.Fact(n"mq005_done") == 1 && this.Fact(n"mq005_police_left") == 1 && this.Fact(n"mq005_police_done") == 0 &&
      this.State("quests/minor_quest/mq005_alley", "gameJournalQuest") == 3 &&
      this.State("quests/minor_quest/mq005_alley/mq005_main", "gameJournalQuestPhase") == 3 &&
      this.State("quests/minor_quest/mq005_alley/mq005_main/02_check_on_corpo", "gameJournalQuestObjective") == 3 &&
      this.State("quests/minor_quest/mq005_alley/mq005_main/03_talk_to_corpo", "gameJournalQuestObjective") == 3;
  }
  private func FarFromEncounter(player: ref<PlayerPuppet>) -> Bool {
    // Native mq005 start waypoint (-998.80719,-81.47656). Horizontal distance
    // is conservative: moving vertically alone can never release the fallback.
    let position = player.GetWorldPosition();
    if !(position.X > -10000000.0 && position.X < 10000000.0 && position.Y > -10000000.0 && position.Y < 10000000.0) { return false; }
    let dx = position.X + 998.80719; let dy = position.Y + 81.47656;
    return dx * dx + dy * dy >= 250000.0;
  }
  private func CheckDeparture(player: ref<PlayerPuppet>) -> Void {
    if this.Fact(n"PTFRS1_CleanupDeparture") != 0 { return; }
    if !this.CompletedPoliceLeftRoute() || !CyberwarePolicy.Safe(player) || !this.FarFromEncounter(player) {
      this.departureSamples = 0; return;
    }
    this.departureSamples += 1;
    if this.departureSamples < 5 { return; }
    // Only arms the alternative condition on the already-running cleanup waits.
    // They retain the native outside-trigger gate and deactivation/join/output.
    this.Set(n"PTFRS1_CleanupDeparture", 1);
    this.detail = "Completed route departed >=500m; native cleanup fallback armed. No encounter or reward replay.";
  }
  public func RestoreFresh() -> String {
    if this.enabled { return this.GetStatus(); }
    if !this.Preflight() { return "Refused: Only Pain requires completed Tower, ready archive, native unlocks, all six journal entries Inactive and seven encounter/scene facts zero. No completion/failure/progress reset. Inspect() shows admission."; }
    this.enabled = true; this.schema = 1; this.stage = 1;
    this.detail = "Queued fresh Only Pain owner. Close CET/menus, holster, leave combat/vehicle/workspot.";
    return this.GetStatus();
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    this.Schedule();
    if !this.enabled || this.stage == 4 || this.stage == 5 { return; }
    let player = GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(player) { return; }
    if this.warmup > 0 { this.warmup -= 1; return; }
    if !this.Tower() { this.detail = "Waiting outside completed-Tower world; no mutation."; return; }
    if this.stage == 1 {
      if !CyberwarePolicy.Safe(player) { this.detail = "Waiting: close CET/menus, holster, leave combat/vehicle/workspot."; return; }
      if !this.Preflight() { this.Fail(n"AdmissionDrift_NoResetOrRetry"); return; }
      this.inflight = true; this.Set(n"PTFRS1_Request", 1);
      if this.Fact(n"PTFRS1_Request") != 1 { this.Fail(n"RequestNotAcknowledged_NoReplay"); return; }
      this.stage = 2; this.inflight = false;
    }
    if this.stage == 2 {
      if this.Fact(n"PTFRS1_Started") != 1 { this.detail = "Waiting for native owner acknowledgement; do not force facts or rerun start."; return; }
      this.stage = 3; this.detail = "Native Only Pain owner running. Approach its encounter in Vista del Rey; native scene controls journal activation.";
    }
    if this.stage == 3 {
      if this.Fact(n"PTFRS1_RewardReplayRefused") != 0 { this.Fail(n"NativeCompletionRewardReplayRefused"); return; }
      this.CheckDeparture(player);
      if this.Fact(n"PTFRS1_OwnerFinished") == 1 {
        this.stage = 4; this.detail = this.Fact(n"mq005_done") == 1 ? "Native encounter and departure cleanup finished; no replay." : "Native owner released without completed outcome; no restart or reset.";
      }
    }
  }
  private func Fail(reason: CName) -> Void {
    this.stage = 5; this.fault = reason;
    if this.enabled { this.Set(n"PTFRS1_Fault", 1); }
    // Never forcibly terminate a running owner or compensate a native reward.
  }
  public func GetStatus() -> String {
    return "Side-job pilot Only Pain: stage=" + ToString(this.stage) + " enabled=" + ToString(this.enabled) +
      " inflight=" + ToString(this.inflight) + " ready=" + ToString(this.Fact(n"PTFRS1_Ready")) +
      " started=" + ToString(this.Fact(n"PTFRS1_Started")) + " done=" + ToString(this.Fact(n"mq005_done")) +
      " rewardClaim/Ack=" + ToString(this.Fact(n"PTFRS1_RewardClaim")) + "/" + ToString(this.Fact(n"PTFRS1_RewardAck")) +
      " ownerFinished=" + ToString(this.Fact(n"PTFRS1_OwnerFinished")) + " | " + (this.stage == 5 ? NameToString(this.fault) : this.detail);
  }
  public func Inspect() -> String {
    let out = this.GetStatus() + " | tower=" + ToString(this.Tower()) + " nativeEligible=" + ToString(this.NativeEligibility()) +
      " untouched=" + ToString(this.UntouchedStage()) + " POI=" + ToString(this.PoiState()) + " preflight=" + ToString(this.Preflight());
    let paths = SideJobPilotS1.Paths(); let classes = SideJobPilotS1.Classes(); let facts = SideJobPilotS1.OwnedNativeFacts(); let i = 0;
    while i < ArraySize(paths) { out += " J" + ToString(i) + "=" + ToString(this.State(paths[i], classes[i])); i += 1; }
    i = 0;
    while i < ArraySize(facts) { out += " " + NameToString(facts[i]) + "=" + ToString(this.Fact(facts[i])); i += 1; }
    out += " | cleanupS1.1 departure=" + ToString(this.Fact(n"PTFRS1_CleanupDeparture")) +
      " entered=" + ToString(this.Fact(n"PTFRS1_CleanupEntered")) +
      " waits=" + ToString(this.Fact(n"PTFRS1_CorpoDepartureAck")) + "/" + ToString(this.Fact(n"PTFRS1_CarsDepartureAck")) +
      " deactivated=" + ToString(this.Fact(n"PTFRS1_CorpoCleanupAck")) + "/" + ToString(this.Fact(n"PTFRS1_CarsCleanupAck")) +
      " joined=" + ToString(this.Fact(n"PTFRS1_CleanupJoined"));
    return out;
  }
}

public class SideTick extends DelayCallback {
  private let owner: wref<SideJobPilotS1>;
  private let epoch: Int32;
  public static func Create(owner: ref<SideJobPilotS1>, epoch: Int32) -> ref<SideTick> {
    let tick = new SideTick(); tick.owner = owner; tick.epoch = epoch; return tick;
  }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}

@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void {
  wrappedMethod(gameInstance);
  let pilot = GameInstance.GetScriptableSystemsContainer(gameInstance).Get(n"PTFR.SideJobPilotS1.SideJobPilotS1") as SideJobPilotS1;
  if IsDefined(pilot) { pilot.Restored(); }
}
