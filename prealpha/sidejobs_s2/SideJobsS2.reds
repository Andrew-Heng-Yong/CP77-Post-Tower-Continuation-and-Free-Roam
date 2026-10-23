module PTFR.SideJobsS2

import PTFR.ActivityStateR3.*
import PTFR.RestrictionsR2.*
import PTFR.RestrictionsR3.*

// Separate additive history: the pinned R3/U9 catalogues are not changed.
// Only this layer's admission facts are written. Native owners keep all gameplay.
public struct SideJobSnapshotS2 {
  public persistent let states: array<Int32>;
  public persistent let facts: array<Int32>;
  public persistent let setup: array<Int32>;
  public persistent let fresh: Bool;
}

public class SideJobsS2 extends ScriptableSystem {
  private persistent let schema: Int32;
  private persistent let catalogue: CName;
  private persistent let baseline: array<SideJobSnapshotS2>;
  private persistent let eligible: array<Bool>;
  private persistent let ready: Bool;
  private persistent let frozen: Bool;
  private persistent let certified: Bool;
  private persistent let faulted: Bool;
  private persistent let captures: Int32;
  private let running: Bool;
  private let epoch: Int32;
  private let registered: Bool;
  private let listeners: array<Uint32>;
  private let lastCapture: Float;
  private let warmup: Int32;

  public static func Catalogue() -> CName { return n"S2_MQ032_MQ008_20261015_SOURCE_AUDIT_V1"; }
  public static func Get(game: GameInstance) -> ref<SideJobsS2> {
    return GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.SideJobsS2.SideJobsS2") as SideJobsS2;
  }
  private func Fact(name: String) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFactStr(name); }
  private func Own(i: Int32, key: String) -> Int32 { return this.Fact("PTFRS2_" + SideJobDataS2.Tag(i) + "_" + key); }
  private func SetPermit(i: Int32, allowed: Bool) -> Void {
    let value = allowed ? 1 : 0;
    if this.Own(i, "Permit") != value {
      GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFactStr("PTFRS2_" + SideJobDataS2.Tag(i) + "_Permit", value);
    }
  }
  private func SetRoute(i: Int32, route: Int32) -> Void {
    if this.Own(i, "AuthorizedRoute") != route {
      GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFactStr("PTFRS2_" + SideJobDataS2.Tag(i) + "_AuthorizedRoute", route);
    }
  }
  private func Now() -> Float { return EngineTime.ToFloat(GameInstance.GetSimTime(this.GetGameInstance())); }
  private func BoundaryNow() -> Bool {
    return this.Fact("q115_point_of_no_return") > 0 || this.Fact("q307_point_of_no_return") > 0 ||
      this.Fact("q307_2079") > 0 || this.Fact("q307_main_game_killed") > 0 || this.Fact("q307_ep1_killed") > 0 ||
      this.Fact("q307_done") > 0 || this.Fact("q307_finished") > 0 || this.Fact("PostTowerFreeRoamActive") > 0;
  }
  private func TeardownNow() -> Bool {
    return this.Fact("q307_2079") > 0 || this.Fact("q307_main_game_killed") > 0 || this.Fact("q307_ep1_killed") > 0 ||
      this.Fact("q307_done") > 0 || this.Fact("q307_finished") > 0 || this.Fact("PostTowerFreeRoamActive") > 0;
  }
  private func Common() -> Bool {
    let profile = ProfilePolicy.Get(this.GetGameInstance());
    return this.Fact("PostTowerFreeRoamActive") == 1 && this.Fact("PTFRP0_DR13") == 1 &&
      this.Fact("PTFRPA2_Finished") == 1 && this.Fact("PTFRPA2_Fault") == 0 &&
      this.Fact("q307_done") == 1 && this.Fact("q307_finished") == 1 && this.Fact("q307_2079") == 1 &&
      this.Fact("q307_main_game_killed") == 1 && this.Fact("q307_ep1_killed") == 1 &&
      this.Fact("q307_active") == 0 && this.Fact("q307_debug_reset") == 0 &&
      this.Fact("q115_point_of_no_return") == 0 && this.Fact("q305_johnny_scene_active") == 0 &&
      this.Fact("PTFRU9_Support_Issued") == 1 && this.Fact("PTFRU9_Support_Fault") == 0 &&
      IsDefined(profile) && profile.PTFRPAComplete() && !profile.PTFRPAFaulted();
  }
  private func OnAttach() -> Void { this.running = true; this.Restored(); }
  private func OnDetach() -> Void { this.Unregister(); this.running = false; this.epoch += 1; }
  public func Restored() -> Void {
    this.Unregister(); this.epoch += 1; this.lastCapture = -100.0; this.warmup = 3;
    // A saved pre-issue permit is not a new-session admission. Never reset Issued.
    let i = 0;
    while i < SideJobDataS2.Count() {
      if this.Own(i, "Issued") == 0 { this.SetPermit(i, false); this.SetRoute(i, 0); }
      i += 1;
    }
    if this.schema != 0 && (this.schema != 1 || NotEquals(this.catalogue, SideJobsS2.Catalogue())) { this.faulted = true; }
    if this.ready && !this.ShapeValid() { this.faulted = true; }
    if this.certified && (!this.ready || !this.frozen || ArraySize(this.eligible) != SideJobDataS2.Count()) { this.faulted = true; }
    if !this.faulted && this.BoundaryNow() && !this.frozen {
      this.frozen = true; this.certified = false; ArrayClear(this.eligible);
    }
    if !this.faulted && !this.BoundaryNow() && this.frozen {
      this.ready = false; this.frozen = false; this.certified = false; ArrayClear(this.eligible);
    }
    this.Register();
    if this.running { this.Schedule(); }
  }
  private func Register() -> Void {
    if this.registered { return; }
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    ArrayPush(this.listeners, qs.RegisterListener(n"q115_point_of_no_return", this, n"OnBoundary"));
    ArrayPush(this.listeners, qs.RegisterListener(n"q307_point_of_no_return", this, n"OnBoundary"));
    this.registered = true;
  }
  private func Unregister() -> Void {
    if !this.registered { return; }
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if ArraySize(this.listeners) == 2 {
      qs.UnregisterListener(n"q115_point_of_no_return", this.listeners[0]);
      qs.UnregisterListener(n"q307_point_of_no_return", this.listeners[1]);
    }
    ArrayClear(this.listeners); this.registered = false;
  }
  protected cb func OnBoundary(value: Int32) -> Bool {
    if value > 0 { this.Freeze(true); }
    return false;
  }
  private func Read(i: Int32) -> SideJobSnapshotS2 {
    let sample: SideJobSnapshotS2;
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    let paths = SideJobDataS2.Paths(i); let classes = SideJobDataS2.Classes(i);
    let names = SideJobDataS2.ZeroFacts(i); let setup = SideJobDataS2.SetupFacts(i);
    let k = 0;
    let entry: wref<JournalEntry>;
    if !IsDefined(jm) || jm.HasAnyDelayedStateChanges() || ArraySize(paths) == 0 || ArraySize(paths) != ArraySize(classes) { return sample; }
    while k < ArraySize(paths) {
      entry = jm.GetEntryByString(paths[k], classes[k]);
      ArrayPush(sample.states, IsDefined(entry) ? EnumInt(jm.GetEntryState(entry)) : -1); k += 1;
    }
    k = 0; while k < ArraySize(names) { ArrayPush(sample.facts, this.Fact(names[k])); k += 1; }
    k = 0; while k < ArraySize(setup) { ArrayPush(sample.setup, this.Fact(setup[k])); k += 1; }
    sample.fresh = this.SampleFresh(i, sample); return sample;
  }
  private func SampleFresh(i: Int32, sample: SideJobSnapshotS2) -> Bool {
    let paths = SideJobDataS2.Paths(i); let names = SideJobDataS2.ZeroFacts(i); let setup = SideJobDataS2.SetupFacts(i);
    if ArraySize(paths) == 0 || ArraySize(sample.states) != ArraySize(paths) || ArraySize(sample.facts) != ArraySize(names) || ArraySize(sample.setup) != ArraySize(setup) { return false; }
    let required = SideJobDataS2.FreshIndices(i);
    if ArraySize(required) == 0 { return false; }
    let k = 0;
    while k < ArraySize(required) {
      if required[k] < 0 || required[k] >= ArraySize(sample.states) || sample.states[required[k]] != 1 { return false; }
      k += 1;
    }
    k = 0; while k < ArraySize(sample.facts) { if sample.facts[k] != 0 { return false; }; k += 1; }
    // mq008's native passive setup is not player progression. Reject corrupt values.
    k = 0; while k < ArraySize(sample.setup) { if sample.setup[k] < 0 || sample.setup[k] > 1 { return false; }; k += 1; }
    return true;
  }
  private func Same(a: SideJobSnapshotS2, b: SideJobSnapshotS2) -> Bool {
    if NotEquals(a.fresh, b.fresh) || ArraySize(a.states) != ArraySize(b.states) || ArraySize(a.facts) != ArraySize(b.facts) || ArraySize(a.setup) != ArraySize(b.setup) { return false; }
    let k = 0; while k < ArraySize(a.states) { if a.states[k] != b.states[k] { return false; }; k += 1; }
    k = 0; while k < ArraySize(a.facts) { if a.facts[k] != b.facts[k] { return false; }; k += 1; }
    k = 0; while k < ArraySize(a.setup) { if a.setup[k] != b.setup[k] { return false; }; k += 1; }
    return true;
  }
  private func ShapeValid() -> Bool {
    if ArraySize(this.baseline) != SideJobDataS2.Count() { return false; }
    let i = 0;
    while i < SideJobDataS2.Count() {
      let paths = SideJobDataS2.Paths(i); let names = SideJobDataS2.ZeroFacts(i); let setup = SideJobDataS2.SetupFacts(i);
      if ArraySize(this.baseline[i].states) != ArraySize(paths) || ArraySize(this.baseline[i].facts) != ArraySize(names) || ArraySize(this.baseline[i].setup) != ArraySize(setup) { return false; }
      if this.baseline[i].fresh && !this.SampleFresh(i, this.baseline[i]) { return false; }
      i += 1;
    }
    return true;
  }
  public func CaptureBeforeEnding() -> String {
    if this.faulted || this.frozen || this.BoundaryNow() { return "No capture after cutoff; history preserved. " + this.Status(); }
    let game = this.GetGameInstance(); let jm = GameInstance.GetJournalManager(game);
    let player = GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(player) || player.IsDead() || player.IsReplacer() || !IsDefined(jm) || jm.HasAnyDelayedStateChanges() { return "Waiting for live V and settled journal."; }
    let sample: array<SideJobSnapshotS2>; let i = 0;
    while i < SideJobDataS2.Count() { ArrayPush(sample, this.Read(i)); i += 1; }
    i = 0;
    while i < SideJobDataS2.Count() { if !this.Same(sample[i], this.Read(i)) { return "Observation changed; earlier history preserved."; }; i += 1; }
    if this.BoundaryNow() || jm.HasAnyDelayedStateChanges() || this.captures >= 2147483647 { return "Capture not committed."; }
    this.baseline = sample; this.schema = 1; this.catalogue = SideJobsS2.Catalogue();
    this.ready = this.ShapeValid(); this.certified = false; this.captures += 1; this.lastCapture = this.Now();
    return this.Status();
  }
  private func Freeze(nativeBoundary: Bool) -> Void {
    if this.frozen || this.faulted { return; }
    let jm = GameInstance.GetJournalManager(this.GetGameInstance()); let age = this.Now() - this.lastCapture;
    this.certified = nativeBoundary && !this.TeardownNow() && this.ready && this.ShapeValid() && age >= 0.0 && age <= 6.0 && IsDefined(jm) && !jm.HasAnyDelayedStateChanges();
    ArrayClear(this.eligible); let i = 0;
    while i < SideJobDataS2.Count() {
      // Only downgrade original fresh evidence; never sample post-cleanup into it.
      let fresh = this.certified && this.baseline[i].fresh && this.Same(this.baseline[i], this.Read(i));
      ArrayPush(this.eligible, fresh); i += 1;
    }
    this.frozen = true;
  }
  public func Certified(id: String) -> Bool {
    let i = SideJobDataS2.Index(id);
    return i >= 0 && !this.faulted && this.schema == 1 && Equals(this.catalogue, SideJobsS2.Catalogue()) && this.ready && this.frozen && this.certified &&
      this.ShapeValid() && ArraySize(this.eligible) == SideJobDataS2.Count() && this.eligible[i];
  }
  private func DevelopmentArmed() -> Bool {
    let prior = PreAlphaEntry.Get(this.GetGameInstance());
    return IsDefined(prior) && prior.DevelopmentArmed();
  }
  private func CanPermit(i: Int32) -> Bool {
    if !this.running || this.warmup > 0 || this.faulted || !this.Common() || this.Own(i, "Ready") != 1 ||
      this.Own(i, "Issued") != 0 || this.Own(i, "Finished") != 0 || this.Own(i, "Fault") != 0 { return false; }
    if !this.Certified(SideJobDataS2.ID(i)) && !this.DevelopmentArmed() { return false; }
    let player = GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(player) || !BodyPolicy.Safe(player) { return false; }
    let before = this.Read(i); let after = this.Read(i);
    return before.fresh && after.fresh && this.Same(before, after);
  }
  // Public read-only final admission hook, suitable for a native scripted guard.
  public func Admissible(id: String) -> Bool { let i = SideJobDataS2.Index(id); return i >= 0 && this.CanPermit(i); }
  private func Schedule() -> Void { GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(SideJobTickS2.Create(this, this.epoch), 1.0, false); }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    this.Schedule();
    if this.warmup > 0 { this.warmup -= 1; }
    if !this.frozen && this.BoundaryNow() { this.Freeze(false); }
    if !this.frozen && this.Now() - this.lastCapture >= 5.0 { this.CaptureBeforeEnding(); }
    let i = 0;
    while i < SideJobDataS2.Count() {
      // Native Issued is durable and never cleared. Completed owners are untouched.
      if this.Own(i, "Issued") == 0 {
        let allowed = this.CanPermit(i);
        if allowed {
          this.SetRoute(i, this.Certified(SideJobDataS2.ID(i)) ? 1 : 2);
          // Native final admission also requires route1/2 and rechecks native state.
          this.SetPermit(i, this.Own(i, "AuthorizedRoute") == 1 || this.Own(i, "AuthorizedRoute") == 2);
        } else { this.SetPermit(i, false); this.SetRoute(i, 0); }
      }
      i += 1;
    }
  }
  public func Status() -> String {
    return "Native side jobs S2: historyReady/frozen/certified=" + ToString(this.ready) + "/" + ToString(this.frozen) + "/" + ToString(this.certified) +
      " captures=" + ToString(this.captures) + " development=" + ToString(this.DevelopmentArmed()) + " fault=" + ToString(this.faulted) + " | No native state reset; original gameplay/rewards.";
  }
  public func Inspect(id: String) -> String {
    let i = SideJobDataS2.Index(id); if i < 0 { return "Outside the two-job S2 batch."; }
    let sample = this.Read(i);
    return "Native side job S2 " + id + ": ready/permit/issued/finished=" + ToString(this.Own(i, "Ready")) + "/" + ToString(this.Own(i, "Permit")) + "/" +
      ToString(this.Own(i, "Issued")) + "/" + ToString(this.Own(i, "Finished")) + " certified=" + ToString(this.Certified(id)) + " development=" + ToString(this.DevelopmentArmed()) +
      " currentFresh=" + ToString(sample.fresh) + " route=" + ToString(this.Own(i, "AuthorizedRoute")) + " fault=" + ToString(this.faulted) + " | Issued is not live interaction or completion proof.";
  }
}

public class SideJobTickS2 extends DelayCallback {
  private let owner: wref<SideJobsS2>; private let epoch: Int32;
  public static func Create(owner: ref<SideJobsS2>, epoch: Int32) -> ref<SideJobTickS2> { let tick = new SideJobTickS2(); tick.owner = owner; tick.epoch = epoch; return tick; }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}

@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void {
  wrappedMethod(gameInstance);
  let owner = SideJobsS2.Get(gameInstance); if IsDefined(owner) { owner.Restored(); }
}

public abstract class SideJobDataS2 {
  public static func Count() -> Int32 { return 2; }
  public static func ID(i: Int32) -> String { return i == 0 ? "mq032_sacrum" : (i == 1 ? "mq008_party" : ""); }
  public static func Tag(i: Int32) -> String { return i == 0 ? "MQ032" : (i == 1 ? "MQ008" : ""); }
  public static func Index(id: String) -> Int32 { return Equals(id, "mq032_sacrum") ? 0 : (Equals(id, "mq008_party") ? 1 : -1); }
  public static func Paths(i: Int32) -> array<String> {
    if i == 0 { return [
      "quests/minor_quest/mq032_sacrum", "quests/minor_quest/mq032_sacrum/mq032_sacrum",
      "quests/minor_quest/mq032_sacrum/mq032_sacrum/01_hook", "quests/minor_quest/mq032_sacrum/mq032_sacrum/01_hook/description",
      "quests/minor_quest/mq032_sacrum/mq032_sacrum/01_hook/description_johnny", "quests/minor_quest/mq032_sacrum/mq032_sacrum/02_maelstrom",
      "quests/minor_quest/mq032_sacrum/mq032_sacrum/03_monk", "quests/minor_quest/mq032_sacrum/mq032_sacrum/04_loot",
      "quests/minor_quest/mq032_sacrum/description", "quests/minor_quest/mq032_sacrum/description_johnny",
      "quests/minor_quest/mq032_sacrum/mq032_alternative_title"
    ]; }
    if i == 1 { return [
      "quests/minor_quest/mq008_party", "quests/minor_quest/mq008_party/mq008_party",
      "quests/minor_quest/mq008_party/mq008_party/01_check_whats_up", "quests/minor_quest/mq008_party/mq008_party/01_check_whats_up/description",
      "quests/minor_quest/mq008_party/mq008_party/02_speak_rep", "quests/minor_quest/mq008_party/mq008_party/03_first_spot",
      "quests/minor_quest/mq008_party/mq008_party/04_drink_spot1", "quests/minor_quest/mq008_party/mq008_party/05_shoot_bottles1",
      "quests/minor_quest/mq008_party/mq008_party/04_drink_spot2", "quests/minor_quest/mq008_party/mq008_party/03_first_spot1",
      "quests/minor_quest/mq008_party/mq008_party/05_shoot_bottles2", "quests/minor_quest/mq008_party/mq008_party/15_back_to_rep",
      "quests/minor_quest/mq008_party/mq008_party/03_first_spot2", "quests/minor_quest/mq008_party/mq008_party/03_first_spot3",
      "quests/minor_quest/mq008_party/mq008_party/04_drink_spot3", "quests/minor_quest/mq008_party/mq008_party/04_drink_spot4",
      "quests/minor_quest/mq008_party/mq008_party/05_shoot_bottles3", "quests/minor_quest/mq008_party/mq008_party/05_shoot_bottles4",
      "quests/minor_quest/mq008_party/mq008_party/16_talk_results", "quests/minor_quest/mq008_party/mq008_party/03a_points",
      "quests/minor_quest/mq008_party/mq008_party/02a_take_gun", "quests/minor_quest/mq008_party/mq008_party/17_pick_up_the_reward"
    ]; }
    let empty: array<String>; return empty;
  }
  public static func Classes(i: Int32) -> array<String> {
    if i == 0 { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestDescription", "gameJournalQuestDescription", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestDescription", "gameJournalQuestDescription", "gameJournalQuestTitleModifier"]; }
    if i == 1 { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestDescription", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective"]; }
    let empty: array<String>; return empty;
  }
  public static func FreshIndices(i: Int32) -> array<Int32> {
    // Sacrum cosmetic/title entries are observed for exact cutoff comparison,
    // not used as gameplay freshness gates. Root+phase+three real objectives are.
    if i == 0 { return [0, 1, 2, 5, 6]; }
    if i == 1 { return [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]; }
    let empty: array<Int32>; return empty;
  }
  public static func ZeroFacts(i: Int32) -> array<String> {
    if i == 0 { return ["mq032_complete", "mq032_dead", "mq032_help", "mq032_monk1_met", "mq032_saved", "mq032_nonlethal", "mq032_no_help", "mq032_01_whatIgnorance", "mq032_monk_get_up", "mq032_stop_idle_gestures", "mq032_03_01_Copy", "mq032_03_02_Human", "mq032_test_def", "mq032_skip_epilogue"]; }
    if i == 1 { return ["mq008_done", "mq008_agreed_to_competition", "mq008_know_rules", "mq008_leaving_spot2", "mq008_left", "mq008_no_competition", "mq008_final_score", "mq008_player_cheated", "mq008_points_20_30", "mq008_points_31_38", "mq008_points_39_43", "mq008_points_less_20", "mq008_points_more_than_43", "mq008_reward_unsealed", "mq008_shooting1_done", "mq008_shooting2_done", "mq008_shooting3_done", "mq008_shooting4_done", "mq008_talks_finished", "mq008_v_starts_competition", "mq008_v_wins", "mq008_representative_defeated", "mq008_telem_combat", "mq008_golden_knuckles_owned", "mq008_quest_item_tags_cleaned", "mq008_time_to_spot1", "v_offends_boss", "mq008_prevention_system_off"]; }
    let empty: array<String>; return empty;
  }
  public static func SetupFacts(i: Int32) -> array<String> {
    if i == 1 { return ["mq008_active", "mq008_quest_comm_on"]; }
    let empty: array<String>; return empty;
  }
}
