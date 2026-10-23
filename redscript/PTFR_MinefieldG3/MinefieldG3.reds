module PTFR.MinefieldG3

import PTFR.RestrictionsR1.*
import PTFR.JohnnyVoiceJV1.*

// Early find-car continuation only, not fresh start/completed replay.
public class MinefieldG3 extends ScriptableSystem {
  private persistent let enabled: Bool;
  private persistent let schema: Int32;
  private persistent let stage: Int32;
  private persistent let prepared: Int32;
  private persistent let inflight: Bool;
  private persistent let originalStates: array<Int32>;
  private persistent let countBase: Int32;
  private persistent let achBase: Int32;
  private persistent let accountPrepared: Bool;
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
    if this.enabled && (this.schema != 1 || this.inflight || ArraySize(this.originalStates) != 4 || this.stage < 1 || this.stage > 5) {
      this.Fail("Unsupported/interrupted G3 journal; no replay. Reload original pre-test snapshot.");
    }
    if this.running { this.Schedule(); }
  }
  private func Schedule() -> Void { GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(MinefieldTick.Create(this, this.epoch), 1.0, false); }
  private func Fact(name: CName) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(name); }
  private func Set(name: CName, value: Int32) -> Void { GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(name, value); }
  public static func Root() -> String { return "quests/street_stories/badlands/inland_avenue/sts_bls_ina_07"; }
  public static func Phase() -> String { return MinefieldG3.Root() + "/get_hdd_from_ghost_car"; }
  public static func PreparePaths() -> array<String> { return [MinefieldG3.Root(), MinefieldG3.Phase(), MinefieldG3.Phase() + "/find_car", "points_of_interest/street_stories/sts_bls_ina_07"]; }
  public static func PrepareClasses() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalPointOfInterestMappin"]; }
  private func State(path: String, cls: String) -> Int32 {
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    let entry = jm.GetEntryByString(path, cls); return IsDefined(entry) ? EnumInt(jm.GetEntryState(entry)) : -1;
  }
  private func Tower() -> Bool {
    let voice = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.JohnnyVoiceJV1.JohnnyVoiceJV1") as JohnnyVoiceJV1;
    return IsDefined(voice) && voice.CompletedTower();
  }
  private func LocalFacts() -> Bool {
    let zero: array<CName> = [n"ina_07_finished", n"ina_07_failed", n"ina_07_perfect", n"ina_07_test_def", n"sts_bls_ina_07_delivery_status", n"sts_bls_ina_07_chase_spawned", n"sts_bls_ina_07_reworked_chase_triggered", n"sts_bls_ina_07_chase_objective_active", n"ina_07_chase_is_on_east", n"ina_07_chase_is_on_east_01", n"ina_07_chase_is_on_west", n"ina_07_chase_is_on_west_02", n"ina_07_chase_lost"];
    let i = 0; while i < ArraySize(zero) { if this.Fact(zero[i]) != 0 { return false; }; i += 1; }
    return this.Fact(n"ina_07_start") > 0 && this.Fact(n"#ina_07_ready") > 0;
  }
  private func StaticJournal() -> Bool {
    let names: array<String> = ["get_inside", "run_away", "optional_investigation", "deliver_car", "leave_workshop", "leave_car", "approach_the_car", "get_rid_of_chase", "park_in_garage", "collect_reward", "dont_damage_the_car"];
    let i = 0; while i < ArraySize(names) { if this.State(MinefieldG3.Phase()+"/"+names[i], "gameJournalQuestObjective") != 1 { return false; }; i += 1; }
    return this.State(MinefieldG3.Root()+"/ina_07_briefing", "gameJournalQuestDescription") == 2;
  }
  private func OtherBadlandsIdle() -> Bool {
    // Shared garage/patrol and fixer accounting cannot be owned concurrently.
    // Missing/inactive/terminal unrelated journals are not freshness gates.
    let names: array<String> = ["sts_bls_ina_11", "sts_bls_ina_02", "sts_bls_ina_03", "sts_bls_ina_06", "sts_bls_ina_09", "sts_bls_ina_05", "sts_bls_ina_08", "sts_bls_ina_04"];
    let i = 0; while i < ArraySize(names) { if this.State("quests/street_stories/badlands/inland_avenue/"+names[i], "gameJournalQuest") == 2 { return false; }; i += 1; }
    return true;
  }
  private func CountsSafe() -> Bool {
    return this.Fact(n"bls_sts_counter") >= 0 && this.Fact(n"bls_sts_counter") < 2147483647 && this.Fact(n"bls_achievement") >= 0 && this.Fact(n"bls_achievement") < 2147483647;
  }
  private func OwnUnused() -> Bool {
    let names: array<CName> = [n"PTFRG3_Request",n"PTFRG3_Started",n"PTFRG3_OwnerFinished",n"PTFRG3_Fault",n"PTFRG3_NewCar",n"PTFRG3_RewardClaim",n"PTFRG3_RewardAck",n"PTFRG3_RewardReplayRefused",n"PTFRG3_AccountRequest",n"PTFRG3_AccountReady",n"PTFRG3_AccountClaim",n"PTFRG3_AccountAck",n"PTFRG3_CountBase",n"PTFRG3_AchBase",n"PTFRG3_CounterAck",n"PTFRG3_Borrow0",n"PTFRG3_Borrow1",n"PTFRG3_Borrow2",n"PTFRG3_Borrow3",n"PTFRG3_Borrow4",n"PTFRG3_Borrow5"];
    let i = 0; while i < ArraySize(names) { if this.Fact(names[i]) != 0 { return false; }; i += 1; }; return true;
  }
  private func Preflight(index: Int32, states: array<Int32>) -> Bool {
    if !this.Tower() || !this.LocalFacts() || !this.StaticJournal() || !this.OwnUnused() || !this.CountsSafe() || !this.OtherBadlandsIdle() ||
      this.Fact(n"PTFRG3_Ready") != 1 || this.Fact(n"PTFRG3_NativeRevision") != 1 || ArraySize(states) != 4 || GameInstance.GetJournalManager(this.GetGameInstance()).HasAnyDelayedStateChanges() { return false; }
    let paths = MinefieldG3.PreparePaths(); let classes = MinefieldG3.PrepareClasses();
    let i = 0; while i < 4 { if this.State(paths[i], classes[i]) != (i < index ? 2 : states[i]) { return false; }; i += 1; }
    return true;
  }
  public func Restore() -> String {
    if this.enabled { return this.GetStatus(); }
    if this.schema != 0 || this.stage != 0 || this.inflight { return "Refused: non-pristine owned journal; no restart/reset."; }
    let paths = MinefieldG3.PreparePaths(); let classes = MinefieldG3.PrepareClasses(); let states: array<Int32>;
    let i = 0; while i < 4 {
      let state = this.State(paths[i], classes[i]);
      if (i < 3 && state != 2 && state != 4) || (i == 3 && state != 1 && state != 2) { return "Refused: missing/terminal or unsupported current find-car stage. Completed replay is not implemented."; }
      ArrayPush(states, state); i += 1;
    }
    if !this.OtherBadlandsIdle() { return "Refused: another active Badlands gig may own the shared garage/patrol/accounting. Finish it first."; }
    if !this.Preflight(0, states) { return "Refused: requires settled early find-car journals, native start/ready, no chase/delivery/outcome, ready G3+JV1 and unused owned state. Inspect shows each gate; no facts reset."; }
    this.originalStates = states; this.schema = 1; this.enabled = true; this.stage = 1; this.prepared = 0;
    this.detail = "Queued Minefield continuation. Close CET/menus, holster, leave combat/vehicle/workspot."; return this.GetStatus();
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }; this.Schedule();
    if !this.enabled || this.stage == 4 || this.stage == 5 { return; }
    let player = GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(player) { return; }; if this.warmup > 0 { this.warmup -= 1; return; }
    if !this.Tower() { this.detail = "Waiting outside completed Tower; no mutation."; return; }
    if this.Fact(n"PTFRG3_Fault") != 0 || this.Fact(n"PTFRG3_RewardReplayRefused") != 0 { this.Fail("Native guard refused; no replay or compensation."); return; }
    if this.stage == 1 {
      if !CyberwarePolicy.Safe(player) { this.detail = "Waiting: close menus/CET, holster, leave combat/vehicle/workspot."; return; }
      if this.inflight {
        if GameInstance.GetJournalManager(this.GetGameInstance()).HasAnyDelayedStateChanges() { return; }
        if this.Preflight(this.prepared+1, this.originalStates) { this.prepared += 1; this.inflight = false; this.ackTicks = 0; return; }
        this.ackTicks += 1; if this.ackTicks >= 12 { this.Fail("Journal acknowledgement failed; no resend."); }; return;
      }
      if !this.Preflight(this.prepared, this.originalStates) { this.Fail("Stage/shared ownership drift during preparation; no reset."); return; }
      let paths = MinefieldG3.PreparePaths(); let classes = MinefieldG3.PrepareClasses();
      if this.prepared < 4 && this.State(paths[this.prepared],classes[this.prepared]) == 2 { this.prepared += 1; return; }
      this.inflight = true;
      if this.prepared < 4 {
        GameInstance.GetJournalManager(this.GetGameInstance()).ChangeEntryState(paths[this.prepared],classes[this.prepared],gameJournalEntryState.Active,JournalNotifyOption.DoNotNotify); this.ackTicks = 0; return;
      }
      this.countBase = this.Fact(n"bls_sts_counter"); this.achBase = this.Fact(n"bls_achievement");
      this.Set(n"PTFRG3_CountBase",this.countBase); this.Set(n"PTFRG3_AchBase",this.achBase);
      if this.Fact(n"PTFRG3_CountBase") != this.countBase || this.Fact(n"PTFRG3_AchBase") != this.achBase { this.Fail("Boot baseline not acknowledged; no request."); return; }
      this.Set(n"PTFRG3_Request",1); if this.Fact(n"PTFRG3_Request") != 1 { this.Fail("Owner request not acknowledged; no resend."); return; }
      this.stage = 2; this.inflight = false; return;
    }
    if this.stage == 2 {
      if this.Fact(n"PTFRG3_Started") != 1 { this.detail = "Waiting for owner; do not force facts."; return; }
      this.stage = 3; this.detail = "Native Minefield owner running. Find the vehicle, escape, and deliver it; Dakota debrief uses native text.";
    }
    if this.stage == 3 {
      // Snapshot accounting at completion, not at activation: legitimate other
      // achievements earned during the gig are not silently overwritten.
      if this.Fact(n"PTFRG3_AccountRequest") == 1 && !this.accountPrepared {
        if !this.OtherBadlandsIdle() { this.detail = "Completion waiting: another Badlands gig owns shared accounting."; return; }
        if !this.CountsSafe() || this.Fact(n"PTFRG3_AccountReady") != 0 || this.Fact(n"PTFRG3_AccountClaim") != 0 || this.Fact(n"PTFRG3_AccountAck") != 0 { this.Fail("Unsafe/interrupted accounting handoff; no retry."); return; }
        this.inflight = true; this.countBase = this.Fact(n"bls_sts_counter"); this.achBase = this.Fact(n"bls_achievement");
        this.Set(n"PTFRG3_CountBase",this.countBase); this.Set(n"PTFRG3_AchBase",this.achBase);
        if this.Fact(n"PTFRG3_CountBase") != this.countBase || this.Fact(n"PTFRG3_AchBase") != this.achBase { this.Fail("Completion baseline not acknowledged; no replay."); return; }
        this.accountPrepared = true; this.Set(n"PTFRG3_AccountReady",1);
        if this.Fact(n"PTFRG3_AccountReady") != 1 { this.Fail("Completion handoff not acknowledged; no replay."); return; }
        this.inflight = false; return;
      }
      if this.Fact(n"PTFRG3_AccountAck") == 1 && !this.counterAcknowledged {
        if !this.accountPrepared || this.Fact(n"PTFRG3_AccountClaim") != 1 || this.Fact(n"bls_achievement") != this.achBase+1 || this.Fact(n"bls_sts_counter") != this.countBase { this.Fail("Native completion accounting drift; no recount/compensation."); return; }
        this.inflight = true; this.Set(n"bls_sts_counter",this.countBase+1);
        if this.Fact(n"bls_sts_counter") != this.countBase+1 { this.Fail("Badlands counter not acknowledged; no replay."); return; }
        this.counterAcknowledged = true; this.Set(n"PTFRG3_CounterAck",1);
        if this.Fact(n"PTFRG3_CounterAck") != 1 { this.Fail("Owned counter acknowledgement failed; no recount."); return; }
        this.inflight = false;
      }
      if this.Fact(n"PTFRG3_OwnerFinished") == 1 {
        let failed = this.Fact(n"ina_07_failed") > 0;
        if !this.counterAcknowledged || (!failed && (this.Fact(n"ina_07_finished") != 1 || this.Fact(n"PTFRG3_RewardClaim") != 1 || this.Fact(n"PTFRG3_RewardAck") != 1)) || (failed && (this.Fact(n"PTFRG3_RewardClaim") != 0 || this.Fact(n"PTFRG3_RewardAck") != 0)) { this.Fail("Owner released without acknowledged native outcome; no replay."); return; }
        this.stage = 4; this.detail = failed ? "Native failure cleanup acknowledged; no payout or restart." : "Native reward/account and departure cleanup acknowledged. Fixer tiers/final rewards remain separate.";
      }
    }
  }
  private func Fail(message: String) -> Void { this.stage = 5; this.detail = message; if this.enabled { this.Set(n"PTFRG3_Fault",1); } }
  public func GetStatus() -> String {
    return "Minefield G3: stage="+ToString(this.stage)+" prepared="+ToString(this.prepared)+" enabled="+ToString(this.enabled)+" inflight="+ToString(this.inflight)+
      " ready/started/ownerFinished="+ToString(this.Fact(n"PTFRG3_Ready"))+"/"+ToString(this.Fact(n"PTFRG3_Started"))+"/"+ToString(this.Fact(n"PTFRG3_OwnerFinished"))+
      " reward="+ToString(this.Fact(n"PTFRG3_RewardClaim"))+"/"+ToString(this.Fact(n"PTFRG3_RewardAck"))+" account="+ToString(this.Fact(n"PTFRG3_AccountClaim"))+"/"+ToString(this.Fact(n"PTFRG3_AccountAck"))+
      " baseCount/Ach="+ToString(this.countBase)+"/"+ToString(this.achBase)+" counterAck="+ToString(this.counterAcknowledged)+" | "+this.detail;
  }
  public func Inspect() -> String {
    return this.GetStatus()+" | tower="+ToString(this.Tower())+" localFacts="+ToString(this.LocalFacts())+" journal="+ToString(this.StaticJournal())+" otherBadlandsIdle="+ToString(this.OtherBadlandsIdle())+
      " start/ready="+ToString(this.Fact(n"ina_07_start"))+"/"+ToString(this.Fact(n"#ina_07_ready"))+" outcome="+ToString(this.Fact(n"ina_07_finished"))+"/"+ToString(this.Fact(n"ina_07_failed"))+
      " delivery/chase="+ToString(this.Fact(n"sts_bls_ina_07_delivery_status"))+"/"+ToString(this.Fact(n"sts_bls_ina_07_chase_spawned"))+" currentCount/Ach="+ToString(this.Fact(n"bls_sts_counter"))+"/"+ToString(this.Fact(n"bls_achievement"))+
      " J="+ToString(this.State(MinefieldG3.Root(),"gameJournalQuest"))+"/"+ToString(this.State(MinefieldG3.Phase(),"gameJournalQuestPhase"))+"/"+ToString(this.State(MinefieldG3.Phase()+"/find_car","gameJournalQuestObjective"))+
      " fault/replay="+ToString(this.Fact(n"PTFRG3_Fault"))+"/"+ToString(this.Fact(n"PTFRG3_RewardReplayRefused"));
  }
}
public class MinefieldTick extends DelayCallback {
  private let owner: wref<MinefieldG3>; private let epoch: Int32;
  public static func Create(owner: ref<MinefieldG3>, epoch: Int32) -> ref<MinefieldTick> { let tick = new MinefieldTick(); tick.owner = owner; tick.epoch = epoch; return tick; }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}
@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void {
  wrappedMethod(gameInstance);
  let pilot = GameInstance.GetScriptableSystemsContainer(gameInstance).Get(n"PTFR.MinefieldG3.MinefieldG3") as MinefieldG3;
  if IsDefined(pilot) { pilot.Restored(); }
}
