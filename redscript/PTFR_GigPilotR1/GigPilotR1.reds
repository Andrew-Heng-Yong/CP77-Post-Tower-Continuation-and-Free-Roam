module PTFR.GigPilotR1

import PTFR.RestrictionsR1.*
import PTFR.RiteG2.*

// Single, explicitly selected exception to fresh-only policy. No global resets.
public class GigPilotR1 extends ScriptableSystem {
  private persistent let enabled: Bool;
  private persistent let schema: Int32;
  private persistent let stage: Int32; // 0 unused, 1 prepare, 2 request, 3 native run, 4 done, 5 refused/fault
  private persistent let prepared: Int32;
  private persistent let inflight: Bool;
  private persistent let foreignState: gameJournalEntryState;
  private persistent let foreignOptional: Bool;
  private persistent let foreignTracked: Bool;
  private persistent let counterAcknowledged: Bool;
  private let faultDetail: String;
  private let detail: String;
  private let running: Bool;
  private let epoch: Int32;
  private let warmup: Int32;
  private let ackTicks: Int32;

  private func OnAttach() -> Void { this.running = true; this.Restored(); }
  private func OnDetach() -> Void { this.running = false; this.epoch += 1; }
  public func Restored() -> Void {
    this.epoch += 1; this.warmup = 4;
    if this.enabled && (this.schema != 1 || this.inflight) {
      this.Fail("Unsupported/interrupted pilot journal. No replay; use the pre-test save.");
    }
    if this.running { this.Schedule(); }
  }
  private func Schedule() -> Void {
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(GigTick.Create(this, this.epoch), 1.0, false);
  }
  private func Fact(name: CName) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(name); }
  private func Set(name: CName, value: Int32) -> Void { GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(name, value); }
  public static func Root() -> String { return "quests/street_stories/watson/northside_industrial_district/sts_wat_nid_02"; }
  public static func Phase() -> String { return GigPilotR1.Root() + "/sts_wat_nid_02"; }
  public static func Foreign() -> String { return "quests/street_stories/pacifica/coastview/sts_pac_cvi_02/sts_pac_cvi_02/get_to_the_van"; }
  private func Entry(path: String, typeName: String) -> wref<JournalEntry> {
    return GameInstance.GetJournalManager(this.GetGameInstance()).GetEntryByString(path, typeName);
  }
  private func Is(path: String, typeName: String, state: gameJournalEntryState) -> Bool {
    let entry = this.Entry(path, typeName);
    return IsDefined(entry) && Equals(GameInstance.GetJournalManager(this.GetGameInstance()).GetEntryState(entry), state);
  }
  private func Tower() -> Bool {
    return this.Fact(n"PostTowerFreeRoamActive") == 1 && this.Fact(n"PTFRP0_DR13") == 1 &&
      this.Fact(n"q307_done") == 1 && this.Fact(n"q307_finished") == 1 && this.Fact(n"q307_2079") == 1 &&
      this.Fact(n"q307_main_game_killed") == 1 && this.Fact(n"q307_ep1_killed") == 1 &&
      this.Fact(n"q307_active") == 0 && this.Fact(n"q115_point_of_no_return") == 0 && this.Fact(n"q305_johnny_scene_active") == 0;
  }
  private func LocalFacts() -> Bool {
    return this.Fact(n"nid_02_start") == 1 && this.Fact(n"sts_wat_nid_02_combat_triggered") == 1 &&
      this.Fact(n"nid_02_finished") == 0 && this.Fact(n"sts_wat_nid_02_fail") == 0 &&
      this.Fact(n"sts_wat_nid_02_delivery_status") == 0 && this.Fact(n"nid_02_optional_counter") == 0 &&
      this.Fact(n"sts_wat_nid_02_chase_objective_active") == 0 &&
      this.Fact(n"sts_wat_nid_02_mappin_part_1") == 0 && this.Fact(n"sts_wat_nid_02_mappin_part_2") == 0 &&
      this.Fact(n"wat_sts_counter") == 3 && this.Fact(n"wat_achievement") == 3 &&
      this.Fact(n"sts_wat_nid_tier_1") == 1 && this.Fact(n"sts_wat_nid_tier_1_1") == 1;
  }
  private func OtherObjectives() -> Bool {
    let names: array<String> = ["info", "get_into", "convey", "get_authorization", "find_the_van", "get_out", "steal", "optional", "get_reward", "get_out1"];
    let i = 0;
    while i < ArraySize(names) {
      if !this.Is(GigPilotR1.Phase() + "/" + names[i], "gameJournalQuestObjective", gameJournalEntryState.Inactive) { return false; }
      i += 1;
    }
    return true;
  }
  private func Messages() -> Bool {
    return this.Is("contacts/regina_jones/sts_wat_nid_02/brief", "gameJournalPhoneMessage", gameJournalEntryState.Active) &&
      this.Is(GigPilotR1.Root() + "/brief", "gameJournalQuestDescription", gameJournalEntryState.Active) &&
      this.Is("contacts/regina_jones/sts_wat_nid_02/sts_wat_nid_02_debrief_success", "gameJournalPhoneMessage", gameJournalEntryState.Inactive) &&
      this.Is("contacts/regina_jones/sts_wat_nid_02/sts_wat_nid_02_debrief_fail", "gameJournalPhoneMessage", gameJournalEntryState.Inactive);
  }
  private func Preflight(index: Int32) -> Bool {
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    if !this.OtherWatsonIdle() || !this.Tower() || !this.LocalFacts() || !this.OtherObjectives() || !this.Messages() || jm.HasAnyDelayedStateChanges() ||
      this.Fact(n"PTFRG1_Ready") != 1 || this.Fact(n"PTFRG1_NativeRevision") != 1 ||
      this.Fact(n"PTFRG1_Request") != 0 || this.Fact(n"PTFRG1_Started") != 0 || this.Fact(n"PTFRG1_Fault") != 0 ||
      this.Fact(n"PTFRG1_RewardClaim") != 0 || this.Fact(n"PTFRG1_RewardAck") != 0 || this.Fact(n"PTFRG1_OwnerFinished") != 0 { return false; }
    let paths: array<String> = [GigPilotR1.Root(), GigPilotR1.Phase(), GigPilotR1.Phase() + "/inside", "points_of_interest/street_stories/sts_wat_nid_02"];
    let types: array<String> = ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalPointOfInterestMappin"];
    let i = 0;
    while i < 4 {
      let state = i < index ? gameJournalEntryState.Active : (i == 3 ? gameJournalEntryState.Inactive : gameJournalEntryState.Failed);
      if !this.Is(paths[i], types[i], state) { return false; }
      i += 1;
    }
    return this.Is("quests/street_stories/watson/little_china/sts_wat_lch_05", "gameJournalQuest", gameJournalEntryState.Succeeded) &&
      this.Is("quests/street_stories/pacifica/coastview/sts_pac_cvi_02", "gameJournalQuest", gameJournalEntryState.Succeeded);
  }
  private func ForeignSame() -> Bool {
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    let entry = this.Entry(GigPilotR1.Foreign(), "gameJournalQuestObjective") as JournalQuestObjective;
    return IsDefined(entry) && Equals(jm.GetEntryState(entry), this.foreignState) &&
      Equals(jm.GetIsObjectiveOptional(entry), this.foreignOptional) && Equals(jm.IsEntryTracked(entry), this.foreignTracked);
  }
  public func Restore() -> String {
    if this.enabled { return this.GetStatus(); }
    if !this.OtherWatsonIdle() { return "Refused: Rite owns unfinished/uncertain Watson accounting; no concurrent adapter admission."; }
    if !this.Preflight(0) { return "Refused: requires completed Tower, pilot archive ready, exact audited inside stage, native tiers/counters and untouched outcomes. Inspect() is read-only."; }
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    let entry = this.Entry(GigPilotR1.Foreign(), "gameJournalQuestObjective") as JournalQuestObjective;
    if !IsDefined(entry) || !Equals(jm.GetEntryState(entry), gameJournalEntryState.Inactive) ||
      jm.GetIsObjectiveOptional(entry) || jm.IsEntryTracked(entry) { return "Refused: foreign journal control differs from audited save."; }
    this.foreignState = jm.GetEntryState(entry); this.foreignOptional = jm.GetIsObjectiveOptional(entry); this.foreignTracked = jm.IsEntryTracked(entry);
    this.schema = 1; this.enabled = true; this.stage = 1; this.prepared = 0;
    this.detail = "Queued Many Ways continuation. Close CET/menus, holster and leave combat/vehicle/workspot.";
    return this.GetStatus();
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || this.epoch != epoch { return; }
    this.Schedule();
    if !this.enabled || this.stage == 5 || this.stage == 4 { return; }
    let player = GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(player) { return; }
    if this.warmup > 0 { this.warmup -= 1; return; }
    if !this.Tower() { this.detail = "Waiting outside completed-Tower world; no mutation."; return; }
    if !this.counterAcknowledged && !this.OtherWatsonIdle() { this.Fail("Concurrent/uncertain Rite accounting; no counter replay or compensation."); return; }
    if !this.ForeignSame() { this.Fail("Foreign journal control changed. No corrective write/replay."); return; }
    if this.stage == 1 {
      if !CyberwarePolicy.Safe(player) { this.detail = "Waiting: close menus/CET, holster, leave combat/vehicle/workspot."; return; }
      if this.inflight {
        // Native journal writes can be delayed. Read back; never resend a write.
        if GameInstance.GetJournalManager(this.GetGameInstance()).HasAnyDelayedStateChanges() { return; }
        if this.Preflight(this.prepared + 1) {
          this.prepared += 1; this.inflight = false; this.ackTicks = 0;
          this.detail = "Acknowledged journal entry " + ToString(this.prepared) + "/4."; return;
        }
        this.ackTicks += 1;
        if this.ackTicks >= 12 { this.Fail("Journal acknowledgement failed; no retry. Use the pre-test save."); }
        return;
      }
      if !this.Preflight(this.prepared) { this.Fail("Admission drift during journal preparation; no reset or retry."); return; }
      if this.prepared < 4 { this.PrepareOne(); return; }
      this.inflight = true;
      this.Set(n"PTFRG1_Request", 1);
      if this.Fact(n"PTFRG1_Request") != 1 { this.Fail("Request acknowledgement failed; no replay."); return; }
      this.stage = 2; this.inflight = false; this.detail = "Requested native gig owner; waiting for its acknowledgement."; return;
    }
    if this.stage == 2 {
      if this.Fact(n"PTFRG1_Started") != 1 { this.detail = "Waiting for native owner; do not force facts or rerun a start."; return; }
      this.stage = 3; this.detail = "Native owner running. Go to Revere Courier Services and use the computer's Personal Link.";
    }
    if this.stage == 3 {
      if this.Fact(n"PTFRG1_RewardReplayRefused") != 0 { this.Fail("Native reward replay was refused."); return; }
      if this.Fact(n"nid_02_finished") == 1 && !this.counterAcknowledged {
        // Exact 3->4 bridge replaces the killed Watson counting loop. Never restart
        // its additive global counter/tier/final-reward logic. No tier is crossed.
        let count = this.Fact(n"wat_sts_counter");
        if count != 3 && count != 4 { this.Fail("Watson counter drift; no recount/compensation."); return; }
        this.inflight = true;
        if count == 3 { this.Set(n"wat_sts_counter", 4); }
        if this.Fact(n"wat_sts_counter") != 4 { this.Fail("Counter acknowledgement failed; no replay."); return; }
        this.counterAcknowledged = true; this.Set(n"PTFRG1_CounterAck", 1); this.inflight = false;
      }
      if this.Fact(n"PTFRG1_OwnerFinished") == 1 {
        this.stage = 4;
        this.detail = this.Fact(n"nid_02_finished") == 1 ? "Native success cleanup finished. Reward and reload checks still require a live test." : "Native owner finished without success; failure is preserved, not restarted.";
      }
    }
  }
  private func PrepareOne() -> Void {
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    let paths: array<String> = [GigPilotR1.Root(), GigPilotR1.Phase(), GigPilotR1.Phase() + "/inside", "points_of_interest/street_stories/sts_wat_nid_02"];
    let types: array<String> = ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalPointOfInterestMappin"];
    this.inflight = true;
    let accepted = jm.ChangeEntryState(paths[this.prepared], types[this.prepared], gameJournalEntryState.Active, JournalNotifyOption.DoNotNotify);
    this.ackTicks = 0;
    this.detail = "Journal request " + ToString(this.prepared + 1) + "/4 returned " + ToString(accepted) + "; waiting for native acknowledgement.";
  }
  // Persistent enabled is set synchronously before Restore returns, including
  // queued stage 1 with Request=0. Faults/interrupted ownership remain blocking.
  // A native owner may still be cleaning up after fully acknowledged accounting.
  public func WatsonAccountBusy() -> Bool {
    if !this.enabled {
      if this.schema != 0 || this.stage != 0 || this.prepared != 0 || this.inflight || this.counterAcknowledged { return true; }
      let names: array<CName> = [n"PTFRG1_Request", n"PTFRG1_Started", n"PTFRG1_Fault", n"PTFRG1_RewardClaim", n"PTFRG1_RewardAck", n"PTFRG1_OwnerFinished", n"PTFRG1_CounterAck", n"PTFRG1_RewardReplayRefused"];
      let i = 0; while i < ArraySize(names) { if this.Fact(names[i]) != 0 { return true; }; i += 1; }
      return false;
    }
    return !(this.schema == 1 && !this.inflight && (this.stage == 3 || this.stage == 4) &&
      this.counterAcknowledged && this.Fact(n"nid_02_finished") == 1 && this.Fact(n"PTFRG1_CounterAck") == 1 &&
      this.Fact(n"PTFRG1_RewardClaim") == 1 && this.Fact(n"PTFRG1_RewardAck") == 1 &&
      this.Fact(n"PTFRG1_Fault") == 0 && this.Fact(n"PTFRG1_RewardReplayRefused") == 0);
  }
  private func OtherWatsonIdle() -> Bool {
    let other = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.RiteG2.RiteG2") as RiteG2;
    return IsDefined(other) && !other.WatsonAccountBusy();
  }
  private func Fail(message: String) -> Void {
    this.stage = 5; this.faultDetail = message; this.detail = message;
    // This blocks an unstarted native owner; never terminate an already-running
    // quest or try to undo native world/reward effects.
    if this.enabled { this.Set(n"PTFRG1_Fault", 1); }
  }
  public func GetStatus() -> String {
    return "Gig pilot Many Ways: stage=" + ToString(this.stage) + " prepared=" + ToString(this.prepared) +
      " enabled=" + ToString(this.enabled) + " inflight=" + ToString(this.inflight) +
      " ready=" + ToString(this.Fact(n"PTFRG1_Ready")) + " started=" + ToString(this.Fact(n"PTFRG1_Started")) +
      " rewardClaim/Ack=" + ToString(this.Fact(n"PTFRG1_RewardClaim")) + "/" + ToString(this.Fact(n"PTFRG1_RewardAck")) +
      " | " + (this.stage == 5 ? this.faultDetail : this.detail);
  }
  public func Inspect() -> String {
    return this.GetStatus() + " | tower=" + ToString(this.Tower()) + " localFacts=" + ToString(this.LocalFacts()) +
      " otherObjectives=" + ToString(this.OtherObjectives()) + " messages=" + ToString(this.Messages()) +
      " preflight=" + ToString(this.Preflight(this.prepared));
  }
}

public class GigTick extends DelayCallback {
  private let owner: wref<GigPilotR1>;
  private let epoch: Int32;
  public static func Create(owner: ref<GigPilotR1>, epoch: Int32) -> ref<GigTick> {
    let tick = new GigTick(); tick.owner = owner; tick.epoch = epoch; return tick;
  }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}

@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void {
  wrappedMethod(gameInstance);
  let pilot = GameInstance.GetScriptableSystemsContainer(gameInstance).Get(n"PTFR.GigPilotR1.GigPilotR1") as GigPilotR1;
  if IsDefined(pilot) { pilot.Restored(); }
}
