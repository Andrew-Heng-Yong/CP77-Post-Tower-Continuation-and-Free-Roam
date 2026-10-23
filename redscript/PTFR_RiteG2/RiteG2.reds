module PTFR.RiteG2

import PTFR.RestrictionsR1.*
import PTFR.GigPilotR1.*

// One audited continuation, never a completed replay or generic owner restart.
public class RiteG2 extends ScriptableSystem {
  private persistent let enabled: Bool;
  private persistent let schema: Int32;
  private persistent let stage: Int32;
  private persistent let prepared: Int32;
  private persistent let inflight: Bool;
  private persistent let poiState: gameJournalEntryState;
  private persistent let countBase: Int32;
  private persistent let counterAcknowledged: Bool;
  private let running: Bool;
  private let epoch: Int32;
  private let warmup: Int32;
  private let ackTicks: Int32;
  private let detail: String;

  private func OnAttach() -> Void { this.running = true; this.Restored(); }
  private func OnDetach() -> Void { this.running = false; this.epoch += 1; }
  public func Restored() -> Void {
    this.epoch += 1; this.warmup = 4;
    if this.enabled && (this.schema != 1 || this.inflight || (this.countBase != 3 && this.countBase != 4)) {
      this.Fail("Unsupported/interrupted G2 journal; no replay. Use the pre-test save.");
    }
    if this.running { this.Schedule(); }
  }
  private func Schedule() -> Void { GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(RiteTick.Create(this, this.epoch), 1.0, false); }
  private func Fact(name: CName) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(name); }
  private func Set(name: CName, value: Int32) -> Void { GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(name, value); }
  public static func Root() -> String { return "quests/street_stories/watson/northside_industrial_district/sts_wat_nid_05"; }
  public static func Phase() -> String { return RiteG2.Root() + "/sts_wat_nid_05"; }
  private func Entry(path: String, typeName: String) -> wref<JournalEntry> { return GameInstance.GetJournalManager(this.GetGameInstance()).GetEntryByString(path, typeName); }
  private func State(path: String, typeName: String) -> Int32 {
    let e = this.Entry(path, typeName); return IsDefined(e) ? EnumInt(GameInstance.GetJournalManager(this.GetGameInstance()).GetEntryState(e)) : -1;
  }
  private func Tower() -> Bool {
    return this.Fact(n"PostTowerFreeRoamActive") == 1 && this.Fact(n"PTFRP0_DR13") == 1 &&
      this.Fact(n"q307_done") == 1 && this.Fact(n"q307_finished") == 1 && this.Fact(n"q307_2079") == 1 &&
      this.Fact(n"q307_main_game_killed") == 1 && this.Fact(n"q307_ep1_killed") == 1 &&
      this.Fact(n"q307_active") == 0 && this.Fact(n"q115_point_of_no_return") == 0 && this.Fact(n"q305_johnny_scene_active") == 0;
  }
  private func LocalFacts() -> Bool {
    return this.Fact(n"nid_05_start") == 1 && this.Fact(n"nid_05_finished") == 0 && this.Fact(n"nid_05_after_holocall") == 0 &&
      this.Fact(n"nid_05_gang_retaliation") == 0 && this.Fact(n"sts_wat_kab_nid_05_combat") == 0 &&
      this.Fact(n"sts_wat_nid_05_ce_after_start") == 0 && this.Fact(n"nid_05_testdef") == 0 &&
      (this.Fact(n"sts_wat_nid_tier_1_1") > 0 || this.Fact(n"sts_wat_nid_tier_1") > 0);
  }
  private func KeycardCount() -> Int32 {
    let player = GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(player) { return -1; }
    let items: array<wref<gameItemData>>;
    let ts = GameInstance.GetTransactionSystem(this.GetGameInstance());
    ts.GetItemList(player, items);
    let count = 0;
    let i = 0;
    while i < ArraySize(items) {
      if IsDefined(items[i]) && TDBID.ToNumber(ItemID.GetTDBID(items[i].GetID())) == 100486752765ul { count += ts.GetItemQuantity(player, items[i].GetID()); }
      i += 1;
    }
    return count;
  }
  private func StaticJournal() -> Bool {
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    let names: array<String> = ["steal_recording", "escape_clinic", "find_recording"];
    let i = 0;
    while i < ArraySize(names) {
      let e = this.Entry(RiteG2.Phase() + "/" + names[i], "gameJournalQuestObjective") as JournalQuestObjective;
      if !IsDefined(e) || NotEquals(jm.GetEntryState(e), gameJournalEntryState.Inactive) || jm.GetIsObjectiveOptional(e) { return false; }
      i += 1;
    }
    return this.State(RiteG2.Root() + "/brief", "gameJournalQuestDescription") == 2 &&
      this.State("contacts/regina_jones/sts_wat_nid_05/brief", "gameJournalPhoneMessage") == 2 &&
      this.State("contacts/regina_jones/sts_wat_nid_05/debrief", "gameJournalPhoneMessage") == 1 &&
      this.State("contacts/regina_jones/sts_wat_nid_05/sts_wat_nid_05_debrief", "gameJournalPhoneMessage") == 1;
  }
  private func CountOK(base: Int32) -> Bool {
    return (base == 3 || base == 4) && this.Fact(n"wat_sts_counter") == base && this.Fact(n"wat_achievement") == base;
  }
  public func WatsonAccountBusy() -> Bool {
    if !this.enabled {
      if this.schema != 0 || this.stage != 0 || this.prepared != 0 || this.inflight || this.counterAcknowledged || this.countBase != 0 { return true; }
      return !this.OwnUnused();
    }
    return !(this.schema == 1 && !this.inflight && (this.countBase == 3 || this.countBase == 4) &&
      (this.stage == 3 || this.stage == 4) && this.counterAcknowledged && this.Fact(n"nid_05_finished") == 1 &&
      this.Fact(n"PTFRG2_CounterAck") == 1 && this.Fact(n"PTFRG2_AccountClaim") == 1 && this.Fact(n"PTFRG2_AccountAck") == 1 &&
      this.Fact(n"PTFRG2_RewardClaim") == 1 && this.Fact(n"PTFRG2_RewardAck") == 1 &&
      this.Fact(n"PTFRG2_Fault") == 0 && this.Fact(n"PTFRG2_RewardReplayRefused") == 0);
  }
  private func OtherWatsonIdle() -> Bool {
    let other = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.GigPilotR1.GigPilotR1") as GigPilotR1;
    return IsDefined(other) && !other.WatsonAccountBusy();
  }
  private func OwnUnused() -> Bool {
    let names: array<CName> = [n"PTFRG2_Request", n"PTFRG2_Started", n"PTFRG2_Fault", n"PTFRG2_RewardClaim", n"PTFRG2_RewardAck", n"PTFRG2_OwnerFinished", n"PTFRG2_AccountClaim", n"PTFRG2_AccountAck", n"PTFRG2_CounterAck", n"PTFRG2_RewardReplayRefused", n"PTFRG2_CountBase"];
    let i = 0; while i < ArraySize(names) { if this.Fact(names[i]) != 0 { return false; }; i += 1; }
    return true;
  }
  private func Preflight(index: Int32, base: Int32, poi: gameJournalEntryState) -> Bool {
    if !this.OtherWatsonIdle() || !this.Tower() || !this.LocalFacts() || !this.StaticJournal() || !this.OwnUnused() || !this.CountOK(base) ||
      this.KeycardCount() != 1 || this.Fact(n"PTFRG2_Ready") != 1 || this.Fact(n"PTFRG2_NativeRevision") != 1 ||
      GameInstance.GetJournalManager(this.GetGameInstance()).HasAnyDelayedStateChanges() { return false; }
    let paths: array<String> = [RiteG2.Root(), RiteG2.Phase(), RiteG2.Phase() + "/get_to_clinic", "points_of_interest/street_stories/sts_wat_nid_05"];
    let types: array<String> = ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalPointOfInterestMappin"];
    let i = 0;
    while i < 4 {
      let expected = i < index ? 2 : (i == 3 ? EnumInt(poi) : 4);
      if this.State(paths[i], types[i]) != expected { return false; }; i += 1;
    }
    return true;
  }
  public func Restore() -> String {
    if this.enabled { return this.GetStatus(); }
    if !this.OtherWatsonIdle() { return "Refused: Many Ways owns unfinished/uncertain Watson accounting; no concurrent adapter admission."; }
    let poi = this.Entry("points_of_interest/street_stories/sts_wat_nid_05", "gameJournalPointOfInterestMappin");
    if !IsDefined(poi) { return "Refused: native POI missing."; }
    let state = GameInstance.GetJournalManager(this.GetGameInstance()).GetEntryState(poi);
    if NotEquals(state, gameJournalEntryState.Inactive) && NotEquals(state, gameJournalEntryState.Active) { return "Refused: terminal/unsupported POI, no reset."; }
    let base = this.Fact(n"wat_sts_counter");
    if !this.Preflight(0, base, state) { return "Refused: requires exact pre-clinic Tower-cleanup stage, existing keycard=1, native eligibility, untouched outcomes and matching Watson totals 3/3 or 4/4. Inspect is read-only."; }
    this.countBase = base; this.poiState = state;
    this.schema = 1; this.enabled = true; this.stage = 1; this.prepared = 0;
    this.detail = "Queued Rite continuation. Close CET/menus, holster, leave combat/vehicle/workspot.";
    return this.GetStatus();
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || this.epoch != epoch { return; }; this.Schedule();
    if !this.enabled || this.stage == 5 || this.stage == 4 { return; }
    let player = GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(player) { return; }; if this.warmup > 0 { this.warmup -= 1; return; }
    if !this.Tower() { this.detail = "Waiting outside completed Tower; no mutation."; return; }
    if !this.counterAcknowledged && !this.OtherWatsonIdle() { this.Fail("Concurrent/uncertain Many Ways accounting; no counter replay or compensation."); return; }
    if this.Fact(n"PTFRG2_Fault") != 0 || this.Fact(n"PTFRG2_RewardReplayRefused") != 0 { this.Fail("Native account/reward guard refused; use pre-test save. No repair/replay."); return; }
    if this.stage == 1 {
      if !CyberwarePolicy.Safe(player) { this.detail = "Waiting: close menus/CET, holster, leave combat/vehicle/workspot."; return; }
      if this.inflight {
        if GameInstance.GetJournalManager(this.GetGameInstance()).HasAnyDelayedStateChanges() { return; }
        if this.Preflight(this.prepared + 1, this.countBase, this.poiState) { this.prepared += 1; this.inflight = false; this.ackTicks = 0; return; }
        this.ackTicks += 1; if this.ackTicks >= 12 { this.Fail("Journal acknowledgement failed; no resend."); }; return;
      }
      if !this.Preflight(this.prepared, this.countBase, this.poiState) { this.Fail("Admission drift during preparation; no reset/retry."); return; }
      this.inflight = true;
      if this.prepared < 4 {
        let paths: array<String> = [RiteG2.Root(), RiteG2.Phase(), RiteG2.Phase() + "/get_to_clinic", "points_of_interest/street_stories/sts_wat_nid_05"];
        let types: array<String> = ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalPointOfInterestMappin"];
        GameInstance.GetJournalManager(this.GetGameInstance()).ChangeEntryState(paths[this.prepared], types[this.prepared], gameJournalEntryState.Active, JournalNotifyOption.DoNotNotify);
        this.ackTicks = 0; return;
      }
      this.Set(n"PTFRG2_CountBase", this.countBase);
      if this.Fact(n"PTFRG2_CountBase") != this.countBase { this.Fail("Baseline fact acknowledgement failed; no request."); return; }
      this.Set(n"PTFRG2_Request", 1);
      if this.Fact(n"PTFRG2_Request") != 1 { this.Fail("Owner request acknowledgement failed; no replay."); return; }
      this.stage = 2; this.inflight = false; return;
    }
    if this.stage == 2 {
      if this.Fact(n"PTFRG2_Started") != 1 {
        if !this.LocalFacts() || !this.CountOK(this.countBase) { this.Fail("Admission drift before owner acknowledgement; no new request."); return; }
        this.detail = "Waiting for native owner; do not force facts."; return;
      }
      this.stage = 3; this.detail = "Native clinic owner running. Follow the objective; download via Personal Link.";
    }
    if this.stage == 3 {
      if this.Fact(n"nid_05_finished") == 1 && !this.counterAcknowledged {
        let target = this.countBase + 1;
        if this.Fact(n"PTFRG2_AccountClaim") != 1 || this.Fact(n"PTFRG2_AccountAck") != 1 || this.Fact(n"wat_achievement") != target || this.Fact(n"wat_sts_counter") != this.countBase {
          this.Fail("Completion accounting drift; no recount/compensation."); return;
        }
        this.inflight = true; this.Set(n"wat_sts_counter", target);
        if this.Fact(n"wat_sts_counter") != target { this.Fail("Watson acknowledgement failed; no replay."); return; }
        this.counterAcknowledged = true; this.Set(n"PTFRG2_CounterAck", 1);
        if this.Fact(n"PTFRG2_CounterAck") != 1 { this.Fail("Owned counter acknowledgement failed; no recount."); return; }
        this.inflight = false;
      }
      if this.Fact(n"PTFRG2_OwnerFinished") == 1 {
        if !this.counterAcknowledged || this.Fact(n"PTFRG2_RewardClaim") != 1 || this.Fact(n"PTFRG2_RewardAck") != 1 { this.Fail("Owner released without acknowledged native completion; no replay."); return; }
        this.stage = 4; this.detail = "Native reward and departure cleanup acknowledged. Tier unlock/final Regina reward are separate, not restored here.";
      }
    }
  }
  private func Fail(message: String) -> Void { this.stage = 5; this.detail = message; if this.enabled { this.Set(n"PTFRG2_Fault", 1); } }
  public func GetStatus() -> String {
    return "Rite G2.1: stage=" + ToString(this.stage) + " prepared=" + ToString(this.prepared) + " enabled=" + ToString(this.enabled) + " inflight=" + ToString(this.inflight) +
      " ready/started/ownerFinished=" + ToString(this.Fact(n"PTFRG2_Ready")) + "/" + ToString(this.Fact(n"PTFRG2_Started")) + "/" + ToString(this.Fact(n"PTFRG2_OwnerFinished")) +
      " reward=" + ToString(this.Fact(n"PTFRG2_RewardClaim")) + "/" + ToString(this.Fact(n"PTFRG2_RewardAck")) + " account=" + ToString(this.Fact(n"PTFRG2_AccountClaim")) + "/" + ToString(this.Fact(n"PTFRG2_AccountAck")) +
      " countBase=" + ToString(this.countBase) + " counterAck=" + ToString(this.counterAcknowledged) + " | " + this.detail;
  }
  public func Inspect() -> String {
    return this.GetStatus() + " | tower=" + ToString(this.Tower()) + " localFacts=" + ToString(this.LocalFacts()) + " journal=" + ToString(this.StaticJournal()) +
      " keycard=" + ToString(this.KeycardCount()) + " Watson/achievement=" + ToString(this.Fact(n"wat_sts_counter")) + "/" + ToString(this.Fact(n"wat_achievement")) +
      " countGate=" + ToString(this.CountOK(this.Fact(n"wat_sts_counter"))) + " fault/replayRefused=" + ToString(this.Fact(n"PTFRG2_Fault")) + "/" + ToString(this.Fact(n"PTFRG2_RewardReplayRefused")) +
      " otherWatsonIdle=" + ToString(this.OtherWatsonIdle()) +
      " J=" + ToString(this.State(RiteG2.Root(), "gameJournalQuest")) + "/" + ToString(this.State(RiteG2.Phase(), "gameJournalQuestPhase")) + "/" + ToString(this.State(RiteG2.Phase() + "/get_to_clinic", "gameJournalQuestObjective"));
  }
}
public class RiteTick extends DelayCallback {
  private let owner: wref<RiteG2>; private let epoch: Int32;
  public static func Create(owner: ref<RiteG2>, epoch: Int32) -> ref<RiteTick> { let tick = new RiteTick(); tick.owner = owner; tick.epoch = epoch; return tick; }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}
@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void {
  wrappedMethod(gameInstance);
  let pilot = GameInstance.GetScriptableSystemsContainer(gameInstance).Get(n"PTFR.RiteG2.RiteG2") as RiteG2;
  if IsDefined(pilot) { pilot.Restored(); }
}
