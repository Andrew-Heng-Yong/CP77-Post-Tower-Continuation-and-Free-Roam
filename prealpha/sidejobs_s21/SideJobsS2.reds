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
  // S2.1: explicit disposable-save authorization, saved only with this batch.
  private persistent let explicitDevelopment: Bool;
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
  // Does not certify history, reset native state, or issue any owner directly.
  // Safe to request from CET; CanPermit still waits for actual safe gameplay.
  public func EnableFreshFixture(confirmation: String) -> String {
    if NotEquals(confirmation, "DISPOSABLE_SAVE") { return "Refused: use DISPOSABLE_SAVE only on a separate disposable test save. " + this.Status(); }
    if this.faulted || !this.Common() { return "Refused: S2 fault or genuine post-Tower handoff/profile/support is not ready. " + this.Status(); }
    this.explicitDevelopment = true;
    return "S2.1 fresh-fixture authorization only; not failed-job restoration. History unchanged. Close CET/menus for admission. " + this.Status();
  }
  private func DevelopmentArmed() -> Bool {
    if this.faulted { return false; }
    let prior = PreAlphaEntry.Get(this.GetGameInstance());
    return this.explicitDevelopment || (IsDefined(prior) && prior.DevelopmentArmed());
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
  // Manual read-only inventory. A Failed root is a candidate, not a restored job.
  public func FailedReport() -> String {
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    if !IsDefined(jm) || jm.HasAnyDelayedStateChanges() { return "S2.1 FailedReport unavailable: journal missing or unsettled; counts unknown. No state changed."; }
    let ids = SideJobFailureDataS21.IDs(); let titles = SideJobFailureDataS21.Titles(); let paths = SideJobFailureDataS21.Paths();
    if ArraySize(ids) != SideJobFailureDataS21.Count() || ArraySize(titles) != ArraySize(ids) || ArraySize(paths) != ArraySize(ids) { return "S2.1 FailedReport unavailable: roster shape mismatch. No state changed."; }
    let inactive = 0; let active = 0; let succeeded = 0; let failed = 0; let unknown = 0; let i = 0; let state: Int32;
    let entry: wref<JournalEntry>;
    let lines = "";
    while i < ArraySize(ids) {
      entry = jm.GetEntryByString(paths[i], "gameJournalQuest");
      state = IsDefined(entry) ? EnumInt(jm.GetEntryState(entry)) : -1;
      if state == 1 { inactive += 1; } else {
        if state == 2 { active += 1; } else {
          if state == 3 { succeeded += 1; } else {
            if state == 4 { failed += 1; lines += "\nFAILED " + ids[i] + " | " + titles[i] + " | candidate, adapter pending"; } else { unknown += 1; lines += "\nUNKNOWN " + ids[i] + " | " + titles[i] + " | state=" + ToString(state); }
          }
        }
      }
      i += 1;
    }
    if jm.HasAnyDelayedStateChanges() { return "S2.1 FailedReport discarded: journal changed while reading; retry once settled. Counts unknown. No state changed."; }
    return "S2.1 FailedReport READ ONLY: postTowerReady=" + ToString(this.Common()) + " (context only, NOT admission) whitelist=58 inactive/active/succeeded/failed/unknown=" + ToString(inactive) + "/" + ToString(active) + "/" + ToString(succeeded) + "/" + ToString(failed) + "/" + ToString(unknown) + " | Failed roots are candidates; adapter pending, nothing restored." + lines;
  }
  // Catalogue-bound progress evidence only, not full scene/item or execution history.
  public func FailedDetails() -> String {
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if !IsDefined(jm) || !IsDefined(qs) || jm.HasAnyDelayedStateChanges() { return "S2.1 FailedDetails unavailable: journal/fact systems missing or unsettled. No state changed."; }
    let ids = SideJobFailureDataS21.IDs(); let titles = SideJobFailureDataS21.Titles(); let roots = SideJobFailureDataS21.Paths();
    if ArraySize(ids) != SideJobFailureDataS21.Count() || ArraySize(titles) != ArraySize(ids) || ArraySize(roots) != ArraySize(ids) { return "S2.1 FailedDetails unavailable: roster shape mismatch. No state changed."; }
    let i = 0; let k: Int32; let state: Int32; let failed = 0; let unknown = 0;
    let root: wref<JournalEntry>; let entry: wref<JournalEntry>;
    let paths: array<String>; let classes: array<String>; let facts: array<String>;
    let lines = this.FailedReport() + "\nS2.1 FailedDetails READ ONLY: catalogue journal/fact evidence, NOT full scene/item/execution history. Failed candidates only; adapters pending.";
    while i < ArraySize(ids) {
      root = jm.GetEntryByString(roots[i], "gameJournalQuest");
      state = IsDefined(root) ? EnumInt(jm.GetEntryState(root)) : -1;
      if state == 4 {
        failed += 1;
        lines += "\nFAILED " + ids[i] + " | " + titles[i] + " | candidate, adapter pending";
        paths = SideJobFailureDataS21.DetailPaths(i); classes = SideJobFailureDataS21.DetailClasses(i); facts = SideJobFailureDataS21.FactNames(i);
        if ArraySize(paths) == 0 { lines += "\nnoDetailCoverage: root is known; no bound journal/fact detail catalogue."; } else {
          if ArraySize(paths) != ArraySize(classes) { return "S2.1 FailedDetails discarded: detail shape mismatch. No state changed."; }
          k = 0;
          while k < ArraySize(paths) {
            entry = jm.GetEntryByString(paths[k], classes[k]);
            state = IsDefined(entry) ? EnumInt(jm.GetEntryState(entry)) : -1;
            lines += "\nJ " + paths[k] + " [" + classes[k] + "]=" + ToString(state);
            k += 1;
          }
          k = 0;
          while k < ArraySize(facts) {
            lines += "\nF " + facts[k] + "=" + ToString(qs.GetFactStr(facts[k]));
            k += 1;
          }
        }
        if EnumInt(jm.GetEntryState(root)) != 4 { return "S2.1 FailedDetails discarded: failed root changed during observation. No state changed."; }
      } else {
        if state < 1 || state > 4 { unknown += 1; lines += "\nUNKNOWN " + ids[i] + " | " + titles[i] + " | root state=" + ToString(state) + "; no detail inference."; }
      }
      i += 1;
    }
    if jm.HasAnyDelayedStateChanges() { return "S2.1 FailedDetails discarded: journal changed while reading; retry once settled. No state changed."; }
    return lines + "\nFailed roots observed=" + ToString(failed) + " unknown roots=" + ToString(unknown) + ". No state changed.";
  }
  public func Status() -> String {
    return "Native side jobs S2: historyReady/frozen/certified=" + ToString(this.ready) + "/" + ToString(this.frozen) + "/" + ToString(this.certified) +
      " captures=" + ToString(this.captures) + " development=" + ToString(this.DevelopmentArmed()) + " explicitFreshFixture=" + ToString(this.explicitDevelopment) + " fault=" + ToString(this.faulted) + " | No native state reset; original gameplay/rewards.";
  }
  public func Inspect(id: String) -> String {
    let i = SideJobDataS2.Index(id); if i < 0 { return "Outside the two-job S2 batch."; }
    let sample = this.Read(i);
    return "Native side job S2 " + id + ": ready/permit/issued/finished=" + ToString(this.Own(i, "Ready")) + "/" + ToString(this.Own(i, "Permit")) + "/" +
      ToString(this.Own(i, "Issued")) + "/" + ToString(this.Own(i, "Finished")) + " certified=" + ToString(this.Certified(id)) + " development=" + ToString(this.DevelopmentArmed()) +
      " explicitFreshFixture=" + ToString(this.explicitDevelopment) + " currentFresh=" + ToString(sample.fresh) + " route=" + ToString(this.Own(i, "AuthorizedRoute")) + " fault=" + ToString(this.faulted) + " | Issued is not live interaction or completion proof.";
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

public abstract class SideJobFailureDataS21 {
  public static func Count() -> Int32 { return 58; }
  public static func IDs() -> array<String> {
    return [
      "sq_q001_wilson",
      "sq_q001_wakako",
      "mq045_victor_debt",
      "mq024_sandra",
      "mq007_smartgun",
      "mq035_ozob",
      "mq013_punks",
      "mq030_melisa",
      "mq012_stud",
      "mq011_wilson",
      "mq010_barry",
      "mq005_alley",
      "mq008_party",
      "mq032_sacrum",
      "mq305_combat_zone_report",
      "q304_splinter_stash",
      "mq038_neweridentity",
      "mq037_brendan_dumpster",
      "mq037_brendan_hooligan001",
      "mq037_brendan",
      "mq049_edgerunners",
      "wst_ep1_11_bill_meeting",
      "wst_ep1_05",
      "wst_ep1_04",
      "mq047_ad_vehicle",
      "mq046_cave_vehicle",
      "mq025_psycho_brawl",
      "mq025_02_kabuki",
      "mq025_03_arroyo",
      "mq025_05_glen",
      "mq025_07_fight_club",
      "mq025_06_pacifica",
      "sq025_delamain",
      "sq025c01_angry",
      "sq025c05_scared",
      "sq025c02_sad",
      "sq025c04_manic",
      "sq025c06_mean",
      "sq025c07_suicidal",
      "sq025c03_mean",
      "07_nc_underground",
      "sq024_city_race",
      "sq024_badlands_race",
      "sq024_santo_domingo_race",
      "sq024_the_big_race",
      "sq025_0_pickup",
      "sq025_compensation",
      "sq018_jackie",
      "mq044_jakes_vehicle",
      "mq002_veterans",
      "mq021_guide",
      "mq041_corpo",
      "sts_ep1_08_steven_meeting_night_city",
      "q304_car_retrieval",
      "mq019_paparazzi",
      "mq306_dumpster",
      "mq015_wizardbook",
      "mq026_conspiracy"
    ];
  }
  public static func Titles() -> array<String> {
    return [
      "The Gun",
      "The Gig",
      "Paid in Full",
      "Full Disclosure",
      "Machine Gun",
      "Send in the Clowns",
      "A Day in the Life",
      "Bullets",
      "Burning Desire/Night Moves",
      "Shoot to Thrill",
      "Happy Together",
      "Only Pain",
      "Stadium Love",
      "Sacrum Profanum / Losing My Religion",
      "Shot by Both Sides",
      "Voodoo Treasure",
      "Big in Japan",
      "I Can See Clearly Now",
      "Spray Paint",
      "Coin Operated Boy",
      "Over the Edge",
      "New Person, Same Old Mistakes",
      "Go Your Own Way",
      "Addicted to Chaos",
      "Dressed to Kill",
      "Murk Man Returns Again Once More Forever",
      "Beat on the Brat",
      "Beat on the Brat: Kabuki",
      "Beat on the Brat: Arroyo",
      "Beat on the Brat: The Glen",
      "Beat on the Brat: Rancho Coronado",
      "Beat on the Brat: Pacifica",
      "Epistrophy",
      "Epistrophy: Wellsprings",
      "Epistrophy: Northside",
      "Epistrophy: North Oak",
      "Epistrophy: Rancho Coronado",
      "Epistrophy: Badlands",
      "Epistrophy: The Glen",
      "Epistrophy: Coastview",
      "The Beast in Me",
      "The Beast in Me: City Center",
      "The Beast in Me: Badlands",
      "The Beast in Me: Santo Domingo",
      "The Beast in Me: The Big Race",
      "Human Nature",
      "Tune Up",
      "Heroes",
      "Sex on Wheels",
      "Gun Music",
      "Fortunate Son",
      "War Pigs",
      "The Show Must Go On",
      "Moving Heat",
      "Violence",
      "No Easy Way Out",
      "Spellbound",
      "The Prophet's Song"
    ];
  }
  public static func Paths() -> array<String> {
    return [
      "quests/side_quest/sq_q001_wilson",
      "quests/side_quest/sq_q001_wakako",
      "quests/minor_quest/mq045_victor_debt",
      "quests/minor_quest/mq024_sandra",
      "quests/minor_quest/mq007_smartgun",
      "quests/minor_quest/mq035_ozob",
      "quests/minor_quest/mq013_punks",
      "quests/minor_quest/mq030_melisa",
      "quests/minor_quest/mq012_stud",
      "quests/minor_quest/mq011_wilson",
      "quests/minor_quest/mq010_barry",
      "quests/minor_quest/mq005_alley",
      "quests/minor_quest/mq008_party",
      "quests/minor_quest/mq032_sacrum",
      "ep1/quests/minor_quest/mq305_combat_zone_report",
      "ep1/quests/minor_quest/q304_splinter_stash",
      "quests/minor_quest/mq038_neweridentity",
      "quests/minor_quest/mq037_brendan_dumpster",
      "quests/minor_quest/mq037_brendan_hooligan001",
      "quests/minor_quest/mq037_brendan",
      "quests/minor_quest/mq049_edgerunners",
      "ep1/quests/minor_quest/wst_ep1_11_bill_meeting",
      "ep1/quests/minor_quest/wst_ep1_05",
      "ep1/quests/minor_quest/wst_ep1_04",
      "quests/minor_quest/mq047_ad_vehicle",
      "quests/minor_quest/mq046_cave_vehicle",
      "quests/minor_quest/mq025_psycho_brawl",
      "quests/minor_quest/mq025_02_kabuki",
      "quests/minor_quest/mq025_03_arroyo",
      "quests/minor_quest/mq025_05_glen",
      "quests/minor_quest/mq025_07_fight_club",
      "quests/minor_quest/mq025_06_pacifica",
      "quests/side_quest/sq025_delamain",
      "quests/side_quest/sq025c01_angry",
      "quests/side_quest/sq025c05_scared",
      "quests/side_quest/sq025c02_sad",
      "quests/side_quest/sq025c04_manic",
      "quests/side_quest/sq025c06_mean",
      "quests/side_quest/sq025c07_suicidal",
      "quests/side_quest/sq025c03_mean",
      "quests/meta/07_nc_underground",
      "quests/side_quest/sq024_city_race",
      "quests/side_quest/sq024_badlands_race",
      "quests/side_quest/sq024_santo_domingo_race",
      "quests/side_quest/sq024_the_big_race",
      "quests/side_quest/sq025_0_pickup",
      "quests/side_quest/sq025_compensation",
      "quests/side_quest/sq018_jackie",
      "quests/minor_quest/mq044_jakes_vehicle",
      "quests/minor_quest/mq002_veterans",
      "quests/minor_quest/mq021_guide",
      "quests/minor_quest/mq041_corpo",
      "ep1/quests/minor_quest/sts_ep1_08_steven_meeting_night_city",
      "ep1/quests/minor_quest/q304_car_retrieval",
      "quests/minor_quest/mq019_paparazzi",
      "ep1/quests/minor_quest/mq306_dumpster",
      "quests/minor_quest/mq015_wizardbook",
      "quests/minor_quest/mq026_conspiracy"
    ];
  }
  public static func DetailPaths(i: Int32) -> array<String> {
    if i == 0 { return [
      "quests/side_quest/sq_q001_wilson",
      "quests/side_quest/sq_q001_wilson/wilson",
      "quests/side_quest/sq_q001_wilson/wilson/meet_wilson",
      "quests/side_quest/sq_q001_wilson/wilson/02_talk_to_wilson",
      "quests/side_quest/sq_q001_wilson/wilson/03_enter_range",
      "quests/side_quest/sq_q001_wilson/desc"
    ]; }
    if i == 1 { return [
      "quests/side_quest/sq_q001_wakako",
      "quests/side_quest/sq_q001_wakako/wakako",
      "quests/side_quest/sq_q001_wakako/wakako/01_reward",
      "quests/side_quest/sq_q001_wakako/wakako/00_reward",
      "quests/side_quest/sq_q001_wakako/wakako/00_reward/description",
      "quests/side_quest/sq_q001_wakako/wakako/02_reward"
    ]; }
    if i == 2 { return [
      "quests/minor_quest/mq045_victor_debt",
      "quests/minor_quest/mq045_victor_debt/mq045_debt",
      "quests/minor_quest/mq045_victor_debt/mq045_debt/mq045_pay_off_victor",
      "quests/minor_quest/mq045_victor_debt/mq045_desc"
    ]; }
    if i == 3 { return [
      "quests/minor_quest/mq024_sandra",
      "quests/minor_quest/mq024_sandra/mq024_sandra",
      "quests/minor_quest/mq024_sandra/mq024_sandra/01_find_data_carrier",
      "quests/minor_quest/mq024_sandra/mq024_sandra/02_call_sandra",
      "quests/minor_quest/mq024_sandra/mq024_sandra/02_call_sandra/description",
      "quests/minor_quest/mq024_sandra/mq024_sandra/03_meet_sandra",
      "quests/minor_quest/mq024_sandra/mq024_sandra/04_defeat_sandra",
      "quests/minor_quest/mq024_sandra/description"
    ]; }
    if i == 4 { return [
      "quests/minor_quest/mq007_smartgun",
      "quests/minor_quest/mq007_smartgun/mq007_smartgun",
      "quests/minor_quest/mq007_smartgun/mq007_smartgun/01_deliver_skippy",
      "quests/minor_quest/mq007_smartgun/mq007_smartgun/01_deliver_skippy/description",
      "quests/minor_quest/mq007_smartgun/mq007_smartgun/02_put_skippy_down",
      "quests/minor_quest/mq007_smartgun/mq007_smartgun/03_talk_to_regina"
    ]; }
    if i == 5 { return [
      "quests/minor_quest/mq035_ozob",
      "quests/minor_quest/mq035_ozob/mq035_ozob",
      "quests/minor_quest/mq035_ozob/mq035_ozob/02_meet_ozob",
      "quests/minor_quest/mq035_ozob/mq035_ozob/02_meet_ozob/description",
      "quests/minor_quest/mq035_ozob/mq035_ozob/03_drive_to_casino",
      "quests/minor_quest/mq035_ozob/mq035_ozob/04_wait",
      "quests/minor_quest/mq035_ozob/mq035_ozob/05_drive_to_ambush",
      "quests/minor_quest/mq035_ozob/mq035_ozob/06_kill_enemies",
      "quests/minor_quest/mq035_ozob/mq035_ozob/07_talk_ozob",
      "quests/minor_quest/mq035_ozob/mq035_ozob/00_call_ozob",
      "quests/minor_quest/mq035_ozob/mq035_ozob/00_call_ozob/description",
      "quests/minor_quest/mq035_ozob/mq035_ozob/wait_for_ozob_to_get_in_car",
      "quests/minor_quest/mq035_ozob/mq035_ozob/return_to_car",
      "quests/minor_quest/mq035_ozob/mq035_ozob/honk"
    ]; }
    if i == 6 { return [
      "quests/minor_quest/mq013_punks",
      "quests/minor_quest/mq013_punks/00_punks",
      "quests/minor_quest/mq013_punks/00_punks/00_talk_shopkeep",
      "quests/minor_quest/mq013_punks/00_punks/00_talk_shopkeep/description",
      "quests/minor_quest/mq013_punks/00_punks/01_decide",
      "quests/minor_quest/mq013_punks/00_punks/02_deal_with_punks",
      "quests/minor_quest/mq013_punks/00_punks/03_defeat_punks",
      "quests/minor_quest/mq013_punks/00_punks/04_talk_shopkeep"
    ]; }
    if i == 7 { return [
      "quests/minor_quest/mq030_melisa",
      "quests/minor_quest/mq030_melisa/01_melisa",
      "quests/minor_quest/mq030_melisa/01_melisa/01_defeat_psycho",
      "quests/minor_quest/mq030_melisa/01_melisa/01_defeat_psycho/description",
      "quests/minor_quest/mq030_melisa/01_melisa/02_approach_max_tac",
      "quests/minor_quest/mq030_melisa/01_melisa/03_sit_down",
      "quests/minor_quest/mq030_melisa/01_melisa/04_talk_to_melisa"
    ]; }
    if i == 8 { return [
      "quests/minor_quest/mq012_stud",
      "quests/minor_quest/mq012_stud/00_stud",
      "quests/minor_quest/mq012_stud/00_stud/00_find_out",
      "quests/minor_quest/mq012_stud/00_stud/00_find_out/description_new",
      "quests/minor_quest/mq012_stud/00_stud/01_talk_man",
      "quests/minor_quest/mq012_stud/00_stud/02_get_car",
      "quests/minor_quest/mq012_stud/00_stud/03_drive_ripperdoc",
      "quests/minor_quest/mq012_stud/00_stud/01b_help",
      "quests/minor_quest/mq012_stud/00_stud/04_stop_at_ripper",
      "quests/minor_quest/mq012_stud/00_stud/05_wait_for_call",
      "quests/minor_quest/mq012_stud/00_stud/06_talk_to_stud",
      "quests/minor_quest/mq012_stud/00_stud/02b_return_to_car",
      "quests/minor_quest/mq012_stud/00_stud/000_lose_heat"
    ]; }
    if i == 9 { return [
      "quests/minor_quest/mq011_wilson",
      "quests/minor_quest/mq011_wilson/00_wilson",
      "quests/minor_quest/mq011_wilson/00_wilson/00_talk_wilson",
      "quests/minor_quest/mq011_wilson/00_wilson/00_talk_wilson/description",
      "quests/minor_quest/mq011_wilson/00_wilson/01_go_to_wilson",
      "quests/minor_quest/mq011_wilson/00_wilson/02_talk_to_wilson",
      "quests/minor_quest/mq011_wilson/00_wilson/03_enter_range",
      "quests/minor_quest/mq011_wilson/00_wilson/04_listen_instructions",
      "quests/minor_quest/mq011_wilson/01_competition",
      "quests/minor_quest/mq011_wilson/01_competition/00_shoot",
      "quests/minor_quest/mq011_wilson/01_competition/000_wait",
      "quests/minor_quest/mq011_wilson/01_competition/00b_ready",
      "quests/minor_quest/mq011_wilson/01_competition/01_go_wilson",
      "quests/minor_quest/mq011_wilson/01_competition/02_grab_prize",
      "quests/minor_quest/mq011_wilson/01_competition/000b_wait",
      "quests/minor_quest/mq011_wilson/01_competition/01b_talk_to_wilson",
      "quests/minor_quest/mq011_wilson/description"
    ]; }
    if i == 10 { return [
      "quests/minor_quest/mq010_barry",
      "quests/minor_quest/mq010_barry/mq010_barry",
      "quests/minor_quest/mq010_barry/mq010_barry/01_hook",
      "quests/minor_quest/mq010_barry/mq010_barry/02_wait_for_barry",
      "quests/minor_quest/mq010_barry/mq010_barry/03_talk_to_barry",
      "quests/minor_quest/mq010_barry/mq010_barry/04_columbarium",
      "quests/minor_quest/mq010_barry/mq010_barry/05_tell_police",
      "quests/minor_quest/mq010_barry/mq010_barry/06_see_what_happened",
      "quests/minor_quest/mq010_barry/mq010_barry/04a_andrew_plaque",
      "quests/minor_quest/mq010_barry/mq010_barry/03a_try_talking_to_barry",
      "quests/minor_quest/mq010_barry/desc"
    ]; }
    if i == 11 { return [
      "quests/minor_quest/mq005_alley",
      "quests/minor_quest/mq005_alley/mq005_main",
      "quests/minor_quest/mq005_alley/mq005_main/01_deal_with_cops",
      "quests/minor_quest/mq005_alley/mq005_main/01_deal_with_cops/description",
      "quests/minor_quest/mq005_alley/mq005_main/02_check_on_corpo",
      "quests/minor_quest/mq005_alley/mq005_main/03_talk_to_corpo"
    ]; }
    if i == 12 { return [
      "quests/minor_quest/mq008_party",
      "quests/minor_quest/mq008_party/mq008_party",
      "quests/minor_quest/mq008_party/mq008_party/01_check_whats_up",
      "quests/minor_quest/mq008_party/mq008_party/01_check_whats_up/description",
      "quests/minor_quest/mq008_party/mq008_party/02_speak_rep",
      "quests/minor_quest/mq008_party/mq008_party/03_first_spot",
      "quests/minor_quest/mq008_party/mq008_party/04_drink_spot1",
      "quests/minor_quest/mq008_party/mq008_party/05_shoot_bottles1",
      "quests/minor_quest/mq008_party/mq008_party/04_drink_spot2",
      "quests/minor_quest/mq008_party/mq008_party/03_first_spot1",
      "quests/minor_quest/mq008_party/mq008_party/05_shoot_bottles2",
      "quests/minor_quest/mq008_party/mq008_party/15_back_to_rep",
      "quests/minor_quest/mq008_party/mq008_party/03_first_spot2",
      "quests/minor_quest/mq008_party/mq008_party/03_first_spot3",
      "quests/minor_quest/mq008_party/mq008_party/04_drink_spot3",
      "quests/minor_quest/mq008_party/mq008_party/04_drink_spot4",
      "quests/minor_quest/mq008_party/mq008_party/05_shoot_bottles3",
      "quests/minor_quest/mq008_party/mq008_party/05_shoot_bottles4",
      "quests/minor_quest/mq008_party/mq008_party/16_talk_results",
      "quests/minor_quest/mq008_party/mq008_party/03a_points",
      "quests/minor_quest/mq008_party/mq008_party/02a_take_gun",
      "quests/minor_quest/mq008_party/mq008_party/17_pick_up_the_reward"
    ]; }
    if i == 13 { return [
      "quests/minor_quest/mq032_sacrum",
      "quests/minor_quest/mq032_sacrum/mq032_sacrum",
      "quests/minor_quest/mq032_sacrum/mq032_sacrum/01_hook",
      "quests/minor_quest/mq032_sacrum/mq032_sacrum/01_hook/description",
      "quests/minor_quest/mq032_sacrum/mq032_sacrum/01_hook/description_johnny",
      "quests/minor_quest/mq032_sacrum/mq032_sacrum/02_maelstrom",
      "quests/minor_quest/mq032_sacrum/mq032_sacrum/03_monk",
      "quests/minor_quest/mq032_sacrum/mq032_sacrum/04_loot",
      "quests/minor_quest/mq032_sacrum/description",
      "quests/minor_quest/mq032_sacrum/description_johnny"
    ]; }
    if i == 14 { return [
      "ep1/quests/minor_quest/mq305_combat_zone_report",
      "ep1/quests/minor_quest/mq305_combat_zone_report/placeholder",
      "ep1/quests/minor_quest/mq305_combat_zone_report/placeholder/placeholder",
      "ep1/quests/minor_quest/mq305_combat_zone_report/placeholder/read_briefing_from_mr_hands",
      "ep1/quests/minor_quest/mq305_combat_zone_report/placeholder/read_briefing_from_mr_hands1",
      "ep1/quests/minor_quest/mq305_combat_zone_report/placeholder/read_briefing_from_mr_hands2",
      "ep1/quests/minor_quest/mq305_combat_zone_report/02_apartment",
      "ep1/quests/minor_quest/mq305_combat_zone_report/02_apartment/find_building",
      "ep1/quests/minor_quest/mq305_combat_zone_report/02_apartment/talk_with_stranger",
      "ep1/quests/minor_quest/mq305_combat_zone_report/02_apartment/search_for_clues",
      "ep1/quests/minor_quest/mq305_combat_zone_report/02_apartment/enter_apartment",
      "ep1/quests/minor_quest/mq305_combat_zone_report/02_apartment/pick_a_not_with_coordinates_from_board",
      "ep1/quests/minor_quest/mq305_combat_zone_report/02_apartment/send_message_to_mr_hands",
      "ep1/quests/minor_quest/mq305_combat_zone_report/02_apartment/read_mr_hands_message",
      "ep1/quests/minor_quest/mq305_combat_zone_report/03_lab_explore",
      "ep1/quests/minor_quest/mq305_combat_zone_report/03_lab_explore/find_the_location_in_cz",
      "ep1/quests/minor_quest/mq305_combat_zone_report/03_lab_explore/ride_the_elevator_down",
      "ep1/quests/minor_quest/mq305_combat_zone_report/03_lab_explore/open_main_lab_door",
      "ep1/quests/minor_quest/mq305_combat_zone_report/03_lab_explore/find_the_main_entrance",
      "ep1/quests/minor_quest/mq305_combat_zone_report/03_lab_explore/talk_to_bree",
      "ep1/quests/minor_quest/mq305_combat_zone_report/03_lab_explore/follow_bree",
      "ep1/quests/minor_quest/mq305_combat_zone_report/03_lab_explore/neutralize_defensive_systems",
      "ep1/quests/minor_quest/mq305_combat_zone_report/03_lab_explore/check_the_hallway",
      "ep1/quests/minor_quest/mq305_combat_zone_report/03_lab_explore/scan_area_for_traps",
      "ep1/quests/minor_quest/mq305_combat_zone_report/04_lab_confrontation",
      "ep1/quests/minor_quest/mq305_combat_zone_report/04_lab_confrontation/check_computer",
      "ep1/quests/minor_quest/mq305_combat_zone_report/04_lab_confrontation/get_off_computer",
      "ep1/quests/minor_quest/mq305_combat_zone_report/04_lab_confrontation/exit_lab",
      "ep1/quests/minor_quest/mq305_combat_zone_report/04_lab_confrontation/watch_video_on_computer",
      "ep1/quests/minor_quest/mq305_combat_zone_report/04_lab_confrontation/kill_dante",
      "ep1/quests/minor_quest/mq305_combat_zone_report/04_lab_confrontation/talk_to_dante",
      "ep1/quests/minor_quest/mq305_combat_zone_report/04_lab_confrontation/talk_to_bree",
      "ep1/quests/minor_quest/mq305_combat_zone_report/04_lab_confrontation/talk_to_bree_or_dante",
      "ep1/quests/minor_quest/mq305_combat_zone_report/04_lab_confrontation/step_aside",
      "ep1/quests/minor_quest/mq305_combat_zone_report/04_lab_confrontation/decide_bree_fate",
      "ep1/quests/minor_quest/mq305_combat_zone_report/05_outcome",
      "ep1/quests/minor_quest/mq305_combat_zone_report/05_outcome/talk_to_mr_hands",
      "ep1/quests/minor_quest/mq305_combat_zone_report/05_outcome/deliver_data_to_drop_point",
      "ep1/quests/minor_quest/mq305_combat_zone_report/description"
    ]; }
    if i == 15 { return [
      "ep1/quests/minor_quest/q304_splinter_stash",
      "ep1/quests/minor_quest/q304_splinter_stash/01_stash",
      "ep1/quests/minor_quest/q304_splinter_stash/01_stash/01_find_stash",
      "ep1/quests/minor_quest/q304_splinter_stash/desc"
    ]; }
    if i == 16 { return [
      "quests/minor_quest/mq038_neweridentity",
      "quests/minor_quest/mq038_neweridentity/mq038_neweridentity",
      "quests/minor_quest/mq038_neweridentity/mq038_neweridentity/01_fishing_village",
      "quests/minor_quest/mq038_neweridentity/mq038_neweridentity/01_fishing_village/mq038_description",
      "quests/minor_quest/mq038_neweridentity/mq038_neweridentity/02_find_dumpster",
      "quests/minor_quest/mq038_neweridentity/mq038_neweridentity/03_recover_body",
      "quests/minor_quest/mq038_neweridentity/mq038_neweridentity/04_deliver_to_car",
      "quests/minor_quest/mq038_neweridentity/mq038_neweridentity/05_hide_trunk",
      "quests/minor_quest/mq038_neweridentity/mq038_neweridentity/06_deliver_northside",
      "quests/minor_quest/mq038_neweridentity/mq038_neweridentity/06_enter_car",
      "quests/minor_quest/mq038_neweridentity/mq038_neweridentity/08_talk_cargo",
      "quests/minor_quest/mq038_neweridentity/mq038_neweridentity/02b_call_darryl",
      "quests/minor_quest/mq038_neweridentity/mq038_neweridentity/09_leave_car"
    ]; }
    if i == 17 { return [
      "quests/minor_quest/mq037_brendan_dumpster",
      "quests/minor_quest/mq037_brendan_dumpster/mq037_brendan_dumpster",
      "quests/minor_quest/mq037_brendan_dumpster/mq037_brendan_dumpster/00_push_dumpster",
      "quests/minor_quest/mq037_brendan_dumpster/mq037_brendan_dumpster/00_push_dumpster/description",
      "quests/minor_quest/mq037_brendan_dumpster/mq037_brendan_dumpster/01_talk_brendan"
    ]; }
    if i == 18 { return [
      "quests/minor_quest/mq037_brendan_hooligan001",
      "quests/minor_quest/mq037_brendan_hooligan001/mq037_brendan_hooligan",
      "quests/minor_quest/mq037_brendan_hooligan001/mq037_brendan_hooligan/00_deal_with_the_hooligan",
      "quests/minor_quest/mq037_brendan_hooligan001/mq037_brendan_hooligan/01_talk_with_brendan"
    ]; }
    if i == 19 { return [
      "quests/minor_quest/mq037_brendan",
      "quests/minor_quest/mq037_brendan/mq037_brendan",
      "quests/minor_quest/mq037_brendan/mq037_brendan/01_go_to_service",
      "quests/minor_quest/mq037_brendan/mq037_brendan/01_go_to_service/description",
      "quests/minor_quest/mq037_brendan/mq037_brendan/02_find_brendan",
      "quests/minor_quest/mq037_brendan/mq037_brendan/03_talk_brendan",
      "quests/minor_quest/mq037_brendan/mq037_brendan/04_talk_theo",
      "quests/minor_quest/mq037_brendan/mq037_brendan/02b_ask_clerk",
      "quests/minor_quest/mq037_brendan/mq037_brendan/02c_destroy_turret"
    ]; }
    if i == 20 { return [
      "quests/minor_quest/mq049_edgerunners",
      "quests/minor_quest/mq049_edgerunners/desc",
      "quests/minor_quest/mq049_edgerunners/01_el_captian",
      "quests/minor_quest/mq049_edgerunners/01_el_captian/01_text_capitan",
      "quests/minor_quest/mq049_edgerunners/01_el_captian/02_wait",
      "quests/minor_quest/mq049_edgerunners/02_falco",
      "quests/minor_quest/mq049_edgerunners/02_falco/01_respond_to_falco",
      "quests/minor_quest/mq049_edgerunners/03_gift",
      "quests/minor_quest/mq049_edgerunners/03_gift/02_pick_up_gift"
    ]; }
    if i == 21 { return [
      "ep1/quests/minor_quest/wst_ep1_11_bill_meeting",
      "ep1/quests/minor_quest/wst_ep1_11_bill_meeting/wst_ep1_11",
      "ep1/quests/minor_quest/wst_ep1_11_bill_meeting/wst_ep1_11/meet_bill",
      "ep1/quests/minor_quest/wst_ep1_11_bill_meeting/wst_ep1_11/talk_bill",
      "ep1/quests/minor_quest/wst_ep1_11_bill_meeting/wst_ep1_11/read_message",
      "ep1/quests/minor_quest/wst_ep1_11_bill_meeting/description"
    ]; }
    if i == 22 { return [
      "ep1/quests/minor_quest/wst_ep1_05",
      "ep1/quests/minor_quest/wst_ep1_05/wst_ep1_05",
      "ep1/quests/minor_quest/wst_ep1_05/wst_ep1_05/go_to_hasan_apartment",
      "ep1/quests/minor_quest/wst_ep1_05/wst_ep1_05/speak_with_hasan",
      "ep1/quests/minor_quest/wst_ep1_05/wst_ep1_05/take_the_gun",
      "ep1/quests/minor_quest/wst_ep1_05/wst_ep1_05/read_message_from_hands",
      "ep1/quests/minor_quest/wst_ep1_05/description"
    ]; }
    if i == 23 { return [
      "ep1/quests/minor_quest/wst_ep1_04",
      "ep1/quests/minor_quest/wst_ep1_04/wst_ep1_04",
      "ep1/quests/minor_quest/wst_ep1_04/wst_ep1_04/go_to_rinders_garage",
      "ep1/quests/minor_quest/wst_ep1_04/wst_ep1_04/loot_the_box",
      "ep1/quests/minor_quest/wst_ep1_04/wst_ep1_04/enter_the_code",
      "ep1/quests/minor_quest/wst_ep1_04/description"
    ]; }
    if i == 24 { return [
      "quests/minor_quest/mq047_ad_vehicle",
      "quests/minor_quest/mq047_ad_vehicle/mq047_desc",
      "quests/minor_quest/mq047_ad_vehicle/mq046_set",
      "quests/minor_quest/mq047_ad_vehicle/mq046_set/investigate",
      "quests/minor_quest/mq047_ad_vehicle/mq046_set/get_inside_car"
    ]; }
    if i == 25 { return [
      "quests/minor_quest/mq046_cave_vehicle",
      "quests/minor_quest/mq046_cave_vehicle/mq046_desc",
      "quests/minor_quest/mq046_cave_vehicle/mq046_container",
      "quests/minor_quest/mq046_cave_vehicle/mq046_container/investigate",
      "quests/minor_quest/mq046_cave_vehicle/mq046_container/get_inside_car"
    ]; }
    if i == 26 { return [
      "quests/minor_quest/mq025_psycho_brawl",
      "quests/minor_quest/mq025_psycho_brawl/psycho_brawl",
      "quests/minor_quest/mq025_psycho_brawl/psycho_brawl/win_fights",
      "quests/minor_quest/mq025_psycho_brawl/psycho_brawl/wait",
      "quests/minor_quest/mq025_psycho_brawl/psycho_brawl/return",
      "quests/minor_quest/mq025_psycho_brawl/psycho_brawl/talk",
      "quests/minor_quest/mq025_psycho_brawl/psycho_brawl/ready",
      "quests/minor_quest/mq025_psycho_brawl/psycho_brawl/fight_mrellis",
      "quests/minor_quest/mq025_psycho_brawl/psycho_brawl/ring",
      "quests/minor_quest/mq025_psycho_brawl/psycho_brawl/prepare",
      "quests/minor_quest/mq025_psycho_brawl/psycho_brawl/talk1",
      "quests/minor_quest/mq025_psycho_brawl/psycho_brawl/victor",
      "quests/minor_quest/mq025_psycho_brawl/psycho_brawl/wait_02",
      "quests/minor_quest/mq025_psycho_brawl/psycho_brawl/wait_03",
      "quests/minor_quest/mq025_psycho_brawl/psycho_brawl/barricade",
      "quests/minor_quest/mq025_psycho_brawl/fistfight",
      "quests/minor_quest/mq025_psycho_brawl/fistfight/fight",
      "quests/minor_quest/mq025_psycho_brawl/fistfight/talk_trainer",
      "quests/minor_quest/mq025_psycho_brawl/fistfight/repeat_until_win",
      "quests/minor_quest/mq025_psycho_brawl/fistfight/enter_ring",
      "quests/minor_quest/mq025_psycho_brawl/fistfight/ready",
      "quests/minor_quest/mq025_psycho_brawl/fistfight/talk_razor",
      "quests/minor_quest/mq025_psycho_brawl/description",
      "quests/minor_quest/mq025_psycho_brawl/find_fights",
      "quests/minor_quest/mq025_psycho_brawl/find_fights/find_kabuki",
      "quests/minor_quest/mq025_psycho_brawl/find_fights/fin_arroyo",
      "quests/minor_quest/mq025_psycho_brawl/find_fights/find_glen",
      "quests/minor_quest/mq025_psycho_brawl/find_fights/find_pacifica",
      "quests/minor_quest/mq025_psycho_brawl/find_fights/find_club"
    ]; }
    if i == 27 { return [
      "quests/minor_quest/mq025_02_kabuki",
      "quests/minor_quest/mq025_02_kabuki/kabuki",
      "quests/minor_quest/mq025_02_kabuki/kabuki/02_kabuki_fight",
      "quests/minor_quest/mq025_02_kabuki/kabuki/02_kabuki_fight/description",
      "quests/minor_quest/mq025_02_kabuki/kabuki/02_talk",
      "quests/minor_quest/mq025_02_kabuki/kabuki/02_talk/description_kabuki",
      "quests/minor_quest/mq025_02_kabuki/kabuki/04_fight"
    ]; }
    if i == 28 { return [
      "quests/minor_quest/mq025_03_arroyo",
      "quests/minor_quest/mq025_03_arroyo/arroyo",
      "quests/minor_quest/mq025_03_arroyo/arroyo/03_arroyo_fight",
      "quests/minor_quest/mq025_03_arroyo/arroyo/03_arroyo_fight/description",
      "quests/minor_quest/mq025_03_arroyo/arroyo/03_fight",
      "quests/minor_quest/mq025_03_arroyo/arroyo/03_talk",
      "quests/minor_quest/mq025_03_arroyo/arroyo/03_talk/description_arroyo"
    ]; }
    if i == 29 { return [
      "quests/minor_quest/mq025_05_glen",
      "quests/minor_quest/mq025_05_glen/glen",
      "quests/minor_quest/mq025_05_glen/glen/05_glen_fight",
      "quests/minor_quest/mq025_05_glen/glen/05_glen_fight/description",
      "quests/minor_quest/mq025_05_glen/glen/05_fight",
      "quests/minor_quest/mq025_05_glen/glen/05_talk",
      "quests/minor_quest/mq025_05_glen/glen/05_talk/description_glen"
    ]; }
    if i == 30 { return [
      "quests/minor_quest/mq025_07_fight_club",
      "quests/minor_quest/mq025_07_fight_club/club",
      "quests/minor_quest/mq025_07_fight_club/club/07_fight",
      "quests/minor_quest/mq025_07_fight_club/club/07_club_fight",
      "quests/minor_quest/mq025_07_fight_club/club/07_club_fight/description",
      "quests/minor_quest/mq025_07_fight_club/club/07_talk",
      "quests/minor_quest/mq025_07_fight_club/club/07_talk/description_club"
    ]; }
    if i == 31 { return [
      "quests/minor_quest/mq025_06_pacifica",
      "quests/minor_quest/mq025_06_pacifica/pacifica",
      "quests/minor_quest/mq025_06_pacifica/pacifica/06_fight_ozob",
      "quests/minor_quest/mq025_06_pacifica/pacifica/06_pacifica_fight",
      "quests/minor_quest/mq025_06_pacifica/pacifica/06_pacifica_fight/description",
      "quests/minor_quest/mq025_06_pacifica/pacifica/06_talk_ozob",
      "quests/minor_quest/mq025_06_pacifica/pacifica/06_talk_ozob/description_pacifica",
      "quests/minor_quest/mq025_06_pacifica/pacifica/06_talk_announcer"
    ]; }
    if i == 32 { return [
      "quests/side_quest/sq025_delamain",
      "quests/side_quest/sq025_delamain/02_briefing",
      "quests/side_quest/sq025_delamain/02_briefing/02_01_follow_delamain",
      "quests/side_quest/sq025_delamain/02_briefing/02_02_leave_garage",
      "quests/side_quest/sq025_delamain/02_briefing/02_03_refused",
      "quests/side_quest/sq025_delamain/02_briefing/02_02b_talk_delamain",
      "quests/side_quest/sq025_delamain/02_briefing/02_01c_take_scanner",
      "quests/side_quest/sq025_delamain/02_briefing/02_00_talk_delamain",
      "quests/side_quest/sq025_delamain/02_briefing/02_00_talk_delamain/sq025b_desc",
      "quests/side_quest/sq025_delamain/02_briefing/02_04_refused_talk",
      "quests/side_quest/sq025_delamain/02_briefing/02_03a_return_later",
      "quests/side_quest/sq025_delamain/03_scan",
      "quests/side_quest/sq025_delamain/03_scan/03_01_find_delamain",
      "quests/side_quest/sq025_delamain/03_scan/03_02_scan_delamains",
      "quests/side_quest/sq025_delamain/03_scan/03_03_scan_talk",
      "quests/side_quest/sq025_delamain/04_scan_types",
      "quests/side_quest/sq025_delamain/04_scan_types/04_01_return",
      "quests/side_quest/sq025_delamain/04_scan_types/04_02_return_scanner",
      "quests/side_quest/sq025_delamain/04_scan_types/04_03_talk_del"
    ]; }
    if i == 33 { return [
      "quests/side_quest/sq025c01_angry",
      "quests/side_quest/sq025c01_angry/01_find_angry",
      "quests/side_quest/sq025c01_angry/01_find_angry/01_find_angry",
      "quests/side_quest/sq025c01_angry/01_find_angry/01_find_angry/sq025_angry_desc",
      "quests/side_quest/sq025c01_angry/01_find_angry/01a_scan_angry",
      "quests/side_quest/sq025c01_angry/01_find_angry/01b_disable_angry",
      "quests/side_quest/sq025c01_angry/01_find_angry/01c_return_angry",
      "quests/side_quest/sq025c01_angry/01_find_angry/01d_destroy_angry",
      "quests/side_quest/sq025c01_angry/01_find_angry/01x_complete_angry",
      "quests/side_quest/sq025c01_angry/01_find_angry/01w_wait_angry"
    ]; }
    if i == 34 { return [
      "quests/side_quest/sq025c05_scared",
      "quests/side_quest/sq025c05_scared/05_find_scared",
      "quests/side_quest/sq025c05_scared/05_find_scared/05_find_scared",
      "quests/side_quest/sq025c05_scared/05_find_scared/05_find_scared/sq025_scared_desc",
      "quests/side_quest/sq025c05_scared/05_find_scared/05a_scan_scared",
      "quests/side_quest/sq025c05_scared/05_find_scared/05b_disable_scared",
      "quests/side_quest/sq025c05_scared/05_find_scared/05c_return_scared",
      "quests/side_quest/sq025c05_scared/05_find_scared/05x_complete_scared",
      "quests/side_quest/sq025c05_scared/05_find_scared/05w_wait_scared"
    ]; }
    if i == 35 { return [
      "quests/side_quest/sq025c02_sad",
      "quests/side_quest/sq025c02_sad/02_find_sad",
      "quests/side_quest/sq025c02_sad/02_find_sad/02_find_sad",
      "quests/side_quest/sq025c02_sad/02_find_sad/02_find_sad/sq025_sad_desc",
      "quests/side_quest/sq025c02_sad/02_find_sad/02a_scan_sad",
      "quests/side_quest/sq025c02_sad/02_find_sad/02b_disable_sad",
      "quests/side_quest/sq025c02_sad/02_find_sad/02c_return_sad",
      "quests/side_quest/sq025c02_sad/02_find_sad/02d_enter_car",
      "quests/side_quest/sq025c02_sad/02_find_sad/02e_drive_home",
      "quests/side_quest/sq025c02_sad/02_find_sad/02c_return_sad1",
      "quests/side_quest/sq025c02_sad/02_find_sad/02x_complete_sad",
      "quests/side_quest/sq025c02_sad/02_find_sad/02w_wait_sad",
      "quests/side_quest/sq025c02_sad/02_find_sad/02g_leave_sad",
      "quests/side_quest/sq025c02_sad/02_find_sad/02d_2_return_car_sad"
    ]; }
    if i == 36 { return [
      "quests/side_quest/sq025c04_manic",
      "quests/side_quest/sq025c04_manic/04_find_manic",
      "quests/side_quest/sq025c04_manic/04_find_manic/04_find_manic",
      "quests/side_quest/sq025c04_manic/04_find_manic/04_find_manic/sq025_manic_desc",
      "quests/side_quest/sq025c04_manic/04_find_manic/04a_scan_manic",
      "quests/side_quest/sq025c04_manic/04_find_manic/04b_disable_manic",
      "quests/side_quest/sq025c04_manic/04_find_manic/04c_return_manic",
      "quests/side_quest/sq025c04_manic/04_find_manic/04d_destroy_flamingos",
      "quests/side_quest/sq025c04_manic/04_find_manic/04e_talk_manic",
      "quests/side_quest/sq025c04_manic/04_find_manic/05x_complete_manic",
      "quests/side_quest/sq025c04_manic/04_find_manic/04w_wait_manic"
    ]; }
    if i == 37 { return [
      "quests/side_quest/sq025c06_mean",
      "quests/side_quest/sq025c06_mean/06_find_mean",
      "quests/side_quest/sq025c06_mean/06_find_mean/06_find_mean",
      "quests/side_quest/sq025c06_mean/06_find_mean/06_find_mean/sq025_deep_desc",
      "quests/side_quest/sq025c06_mean/06_find_mean/06a_scan_deep",
      "quests/side_quest/sq025c06_mean/06_find_mean/06b_disable_deep",
      "quests/side_quest/sq025c06_mean/06_find_mean/06c_return_deep",
      "quests/side_quest/sq025c06_mean/06_find_mean/06bb_enter_deep",
      "quests/side_quest/sq025c06_mean/06_find_mean/06d_exit_deep",
      "quests/side_quest/sq025c06_mean/06_find_mean/06x_complete_deep",
      "quests/side_quest/sq025c06_mean/06_find_mean/06w_wait_deep"
    ]; }
    if i == 38 { return [
      "quests/side_quest/sq025c07_suicidal",
      "quests/side_quest/sq025c07_suicidal/07_find_suicidal",
      "quests/side_quest/sq025c07_suicidal/07_find_suicidal/07_find_suicidal",
      "quests/side_quest/sq025c07_suicidal/07_find_suicidal/07_find_suicidal/sq025_suicidal_desc",
      "quests/side_quest/sq025c07_suicidal/07_find_suicidal/07a_scan_suicidal",
      "quests/side_quest/sq025c07_suicidal/07_find_suicidal/07b_disable_suicidal",
      "quests/side_quest/sq025c07_suicidal/07_find_suicidal/07c_return_suicidal",
      "quests/side_quest/sq025c07_suicidal/07_find_suicidal/07x_complete_suicidal",
      "quests/side_quest/sq025c07_suicidal/07_find_suicidal/071w_wait_suidial"
    ]; }
    if i == 39 { return [
      "quests/side_quest/sq025c03_mean",
      "quests/side_quest/sq025c03_mean/03_find_mean",
      "quests/side_quest/sq025c03_mean/03_find_mean/03_find_mean",
      "quests/side_quest/sq025c03_mean/03_find_mean/03_find_mean/sq025_mean_desc",
      "quests/side_quest/sq025c03_mean/03_find_mean/03a_scan_mean",
      "quests/side_quest/sq025c03_mean/03_find_mean/03b_disable_mean",
      "quests/side_quest/sq025c03_mean/03_find_mean/03c_return_mean",
      "quests/side_quest/sq025c03_mean/03_find_mean/04_defeat_goons",
      "quests/side_quest/sq025c03_mean/03_find_mean/03e_talk",
      "quests/side_quest/sq025c03_mean/03_find_mean/03x_complete_mean",
      "quests/side_quest/sq025c03_mean/03_find_mean/03w_wait_mean"
    ]; }
    if i == 40 { return [
      "quests/meta/07_nc_underground",
      "quests/meta/07_nc_underground/00_hook",
      "quests/meta/07_nc_underground/00_hook/01_talk_claire",
      "quests/meta/07_nc_underground/00_hook/01_talk_claire/description",
      "quests/meta/07_nc_underground/00_hook/03_text_claire",
      "quests/meta/07_nc_underground/01_garage",
      "quests/meta/07_nc_underground/01_garage/01_talk_to_clair",
      "quests/meta/07_nc_underground/01_garage/00a_claire_garage",
      "quests/meta/07_nc_underground/02_big_race_call",
      "quests/meta/07_nc_underground/02_big_race_call/00_wait_for_cal",
      "quests/meta/07_nc_underground/02_big_race_call/000a_wait_badlands",
      "quests/meta/07_nc_underground/02_big_race_call/000b_wait_santo",
      "quests/meta/07_nc_underground/02_big_race_call/000a1_read_message",
      "quests/meta/07_nc_underground/02_big_race_call/000b1_read_message",
      "quests/meta/07_nc_underground/02_big_race_call/02a_read_message",
      "quests/meta/07_nc_underground/02_big_race_call/000_wait_city",
      "quests/meta/07_nc_underground/02_big_race_call/000a_read_message",
      "quests/meta/07_nc_underground/02_big_race_call/03_text_claire",
      "quests/meta/07_nc_underground/06_sampson",
      "quests/meta/07_nc_underground/06_sampson/05_confront_sampson",
      "quests/meta/07_nc_underground/06_sampson/07_talk_claire",
      "quests/meta/07_nc_underground/07_forlorn_hope",
      "quests/meta/07_nc_underground/07_forlorn_hope/000_get_in",
      "quests/meta/07_nc_underground/07_forlorn_hope/03_talk_claire",
      "quests/meta/07_nc_underground/07_forlorn_hope/04_drive",
      "quests/meta/07_nc_underground/03_races",
      "quests/meta/07_nc_underground/03_races/00_beat_races",
      "quests/meta/07_nc_underground/03_races/01_complete_big_race",
      "quests/meta/07_nc_underground/description"
    ]; }
    if i == 41 { return [
      "quests/side_quest/sq024_city_race",
      "quests/side_quest/sq024_city_race/02_santo_domingo_race",
      "quests/side_quest/sq024_city_race/02_santo_domingo_race/01_talk_claire",
      "quests/side_quest/sq024_city_race/02_santo_domingo_race/03_get_in",
      "quests/side_quest/sq024_city_race/02_santo_domingo_race/04_beat_race",
      "quests/side_quest/sq024_city_race/02_santo_domingo_race/00_go_to_race",
      "quests/side_quest/sq024_city_race/02_santo_domingo_race/00_go_to_race/description",
      "quests/side_quest/sq024_city_race/02_santo_domingo_race/01b_call_claire",
      "quests/side_quest/sq024_city_race/02_santo_domingo_race/05_stop_at_finish",
      "quests/side_quest/sq024_city_race/02_santo_domingo_race/09_talk_claire",
      "quests/side_quest/sq024_city_race/02_santo_domingo_race/10_get_in_drive_garage",
      "quests/side_quest/sq024_city_race/02_santo_domingo_race/11_drive_garage",
      "quests/side_quest/sq024_city_race/02_santo_domingo_race/02_take_shard",
      "quests/side_quest/sq024_city_race/02_santo_domingo_race/03b_get_in_v",
      "quests/side_quest/sq024_city_race/02_santo_domingo_race/03c_wait_for_race",
      "quests/side_quest/sq024_city_race/02_santo_domingo_race/000_go_back",
      "quests/side_quest/sq024_city_race/02_santo_domingo_race/000b_text_claire",
      "quests/side_quest/sq024_city_race/02_santo_domingo_race/01d_wait_for_claire"
    ]; }
    if i == 42 { return [
      "quests/side_quest/sq024_badlands_race",
      "quests/side_quest/sq024_badlands_race/02_santo_domingo_race",
      "quests/side_quest/sq024_badlands_race/02_santo_domingo_race/01_talk_claire",
      "quests/side_quest/sq024_badlands_race/02_santo_domingo_race/03_get_in",
      "quests/side_quest/sq024_badlands_race/02_santo_domingo_race/04_beat_race",
      "quests/side_quest/sq024_badlands_race/02_santo_domingo_race/00a_go_to_race",
      "quests/side_quest/sq024_badlands_race/02_santo_domingo_race/00a_go_to_race/description",
      "quests/side_quest/sq024_badlands_race/02_santo_domingo_race/01b_call_claire",
      "quests/side_quest/sq024_badlands_race/02_santo_domingo_race/05_stop_at_finish",
      "quests/side_quest/sq024_badlands_race/02_santo_domingo_race/09_talk_claire",
      "quests/side_quest/sq024_badlands_race/02_santo_domingo_race/10_get_in_drive_garage",
      "quests/side_quest/sq024_badlands_race/02_santo_domingo_race/11_drive_garage",
      "quests/side_quest/sq024_badlands_race/02_santo_domingo_race/03b_wait_for_race",
      "quests/side_quest/sq024_badlands_race/02_santo_domingo_race/000_go_back",
      "quests/side_quest/sq024_badlands_race/02_santo_domingo_race/000b_text_claire",
      "quests/side_quest/sq024_badlands_race/02_santo_domingo_race/01d_wait_for_claire"
    ]; }
    if i == 43 { return [
      "quests/side_quest/sq024_santo_domingo_race",
      "quests/side_quest/sq024_santo_domingo_race/02_santo_domingo_race",
      "quests/side_quest/sq024_santo_domingo_race/02_santo_domingo_race/00a_go_to_race",
      "quests/side_quest/sq024_santo_domingo_race/02_santo_domingo_race/00a_go_to_race/description",
      "quests/side_quest/sq024_santo_domingo_race/02_santo_domingo_race/01_talk_claire",
      "quests/side_quest/sq024_santo_domingo_race/02_santo_domingo_race/03_get_in",
      "quests/side_quest/sq024_santo_domingo_race/02_santo_domingo_race/04_beat_race",
      "quests/side_quest/sq024_santo_domingo_race/02_santo_domingo_race/01b_call_claire",
      "quests/side_quest/sq024_santo_domingo_race/02_santo_domingo_race/06_talk_claire",
      "quests/side_quest/sq024_santo_domingo_race/02_santo_domingo_race/08_drive_with_claire",
      "quests/side_quest/sq024_santo_domingo_race/02_santo_domingo_race/09_talk_claire",
      "quests/side_quest/sq024_santo_domingo_race/02_santo_domingo_race/10_get_in_drive_garage",
      "quests/side_quest/sq024_santo_domingo_race/02_santo_domingo_race/11_drive_garage",
      "quests/side_quest/sq024_santo_domingo_race/02_santo_domingo_race/08b_follow_claire",
      "quests/side_quest/sq024_santo_domingo_race/02_santo_domingo_race/08c_sit",
      "quests/side_quest/sq024_santo_domingo_race/02_santo_domingo_race/03b_get_in_v",
      "quests/side_quest/sq024_santo_domingo_race/02_santo_domingo_race/03c_wait_race",
      "quests/side_quest/sq024_santo_domingo_race/02_santo_domingo_race/000_go_back",
      "quests/side_quest/sq024_santo_domingo_race/02_santo_domingo_race/000b_text_claire",
      "quests/side_quest/sq024_santo_domingo_race/02_santo_domingo_race/01c_wait_for_claire"
    ]; }
    if i == 44 { return [
      "quests/side_quest/sq024_the_big_race",
      "quests/side_quest/sq024_the_big_race/02_santo_domingo_race",
      "quests/side_quest/sq024_the_big_race/02_santo_domingo_race/03_get_in",
      "quests/side_quest/sq024_the_big_race/02_santo_domingo_race/04_beat_race",
      "quests/side_quest/sq024_the_big_race/02_santo_domingo_race/04c_stay_close",
      "quests/side_quest/sq024_the_big_race/02_santo_domingo_race/01_go_to_race",
      "quests/side_quest/sq024_the_big_race/02_santo_domingo_race/01_go_to_race/description",
      "quests/side_quest/sq024_the_big_race/02_santo_domingo_race/02_approach_claire",
      "quests/side_quest/sq024_the_big_race/02_santo_domingo_race/02b_talk_claire",
      "quests/side_quest/sq024_the_big_race/02_santo_domingo_race/05_follow_sampson_or_continue",
      "quests/side_quest/sq024_the_big_race/02_santo_domingo_race/06a_follow_sampson",
      "quests/side_quest/sq024_the_big_race/02_santo_domingo_race/06b_beat_race",
      "quests/side_quest/sq024_the_big_race/02_santo_domingo_race/03b_wait_for_race",
      "quests/side_quest/sq024_the_big_race/02_santo_domingo_race/07_stop_car",
      "quests/side_quest/sq024_the_big_race/02_santo_domingo_race/08_talk_claire",
      "quests/side_quest/sq024_the_big_race/02_santo_domingo_race/03c_get_in_v",
      "quests/side_quest/sq024_the_big_race/02_santo_domingo_race/000_call_claire",
      "quests/side_quest/sq024_the_big_race/02_santo_domingo_race/000_go_back",
      "quests/side_quest/sq024_the_big_race/02_santo_domingo_race/000b_text_claire",
      "quests/side_quest/sq024_the_big_race/02_santo_domingo_race/00c_wait_for_claire"
    ]; }
    if i == 45 { return [
      "quests/side_quest/sq025_0_pickup",
      "quests/side_quest/sq025_0_pickup/pickup",
      "quests/side_quest/sq025_0_pickup/pickup/00_debug_trigger",
      "quests/side_quest/sq025_0_pickup/pickup/00_debug_trigger/sq025a_desc",
      "quests/side_quest/sq025_0_pickup/pickup/00b_debug_spawn",
      "quests/side_quest/sq025_0_pickup/pickup/00c_talk_johnny",
      "quests/side_quest/sq025_0_pickup/pickup/01_leave_car",
      "quests/side_quest/sq025_0_pickup/pickup/02_read_msg",
      "quests/side_quest/sq025_0_pickup/pickup/03_wait",
      "quests/side_quest/sq025_0_pickup/pickup/00a_go_parking_lot"
    ]; }
    if i == 46 { return [
      "quests/side_quest/sq025_compensation",
      "quests/side_quest/sq025_compensation/01_hook",
      "quests/side_quest/sq025_compensation/01_hook/01_01_collect_reward",
      "quests/side_quest/sq025_compensation/01_hook/01_01_collect_reward/sq025a2_desc",
      "quests/side_quest/sq025_compensation/01_hook/01_02_get_inside",
      "quests/side_quest/sq025_compensation/01_hook/01_02_receptionist"
    ]; }
    if i == 47 { return [
      "quests/side_quest/sq018_jackie",
      "quests/side_quest/sq018_jackie/00_holocall",
      "quests/side_quest/sq018_jackie/00_holocall/01_read_messages",
      "quests/side_quest/sq018_jackie/00_holocall/02_call_mama_welles",
      "quests/side_quest/sq018_jackie/00_holocall/04_talk_with_mama_welles",
      "quests/side_quest/sq018_jackie/00_holocall/03_get_package",
      "quests/side_quest/sq018_jackie/00_holocall/01_read_messages1",
      "quests/side_quest/sq018_jackie/01_mama_welles",
      "quests/side_quest/sq018_jackie/01_mama_welles/01_visit_el_coyote",
      "quests/side_quest/sq018_jackie/01_mama_welles/02_talk_with_mama_welles",
      "quests/side_quest/sq018_jackie/01_mama_welles/03_take_keycard",
      "quests/side_quest/sq018_jackie/01_mama_welles/02a_sit_down",
      "quests/side_quest/sq018_jackie/02_storage",
      "quests/side_quest/sq018_jackie/02_storage/01_got_to_jackies_storage",
      "quests/side_quest/sq018_jackie/02_storage/04_open_storage",
      "quests/side_quest/sq018_jackie/02_storage/05_go_through_jackies_stuff",
      "quests/side_quest/sq018_jackie/02_storage/06_pick_things_for_ofrenda",
      "quests/side_quest/sq018_jackie/02_storage/05_talk_with_misty",
      "quests/side_quest/sq018_jackie/02_storage/04a_find_a_key",
      "quests/side_quest/sq018_jackie/02_storage/04b_open_door",
      "quests/side_quest/sq018_jackie/02_storage/05a_optional_talk_misty",
      "quests/side_quest/sq018_jackie/03_el_coyote_funeral",
      "quests/side_quest/sq018_jackie/03_el_coyote_funeral/01_go_to_el_coyote",
      "quests/side_quest/sq018_jackie/03_el_coyote_funeral/02_talk_with_mama_welles",
      "quests/side_quest/sq018_jackie/03_el_coyote_funeral/03_leave_things_ofrenda",
      "quests/side_quest/sq018_jackie/03_el_coyote_funeral/04_talk_with_valentinos",
      "quests/side_quest/sq018_jackie/03_el_coyote_funeral/05_talk_with_misty",
      "quests/side_quest/sq018_jackie/03_el_coyote_funeral/06_talk_with_victor_vector",
      "quests/side_quest/sq018_jackie/03_el_coyote_funeral/07_leave_funeral",
      "quests/side_quest/sq018_jackie/03_el_coyote_funeral/03_take_part_in_ceremony",
      "quests/side_quest/sq018_jackie/03_el_coyote_funeral/03b_drink",
      "quests/side_quest/sq018_jackie/03_el_coyote_funeral/03c_make_toast",
      "quests/side_quest/sq018_jackie/03_el_coyote_funeral/03a_sit_down",
      "quests/side_quest/sq018_jackie/03_el_coyote_funeral/04b_talk_with_padre",
      "quests/side_quest/sq018_jackie/03_el_coyote_funeral/04c_talk_with_pepe",
      "quests/side_quest/sq018_jackie/description"
    ]; }
    if i == 48 { return [
      "quests/minor_quest/mq044_jakes_vehicle",
      "quests/minor_quest/mq044_jakes_vehicle/mq044_jakes_vehicle",
      "quests/minor_quest/mq044_jakes_vehicle/mq044_jakes_vehicle/01_reach_garage",
      "quests/minor_quest/mq044_jakes_vehicle/mq044_jakes_vehicle/01_reach_garage/brief",
      "quests/minor_quest/mq044_jakes_vehicle/mq044_jakes_vehicle/03_get_in_car",
      "quests/minor_quest/mq044_jakes_vehicle/mq044_jakes_vehicle/04_leave_area"
    ]; }
    if i == 49 { return [
      "quests/minor_quest/mq002_veterans",
      "quests/minor_quest/mq002_veterans/mq002_veterans",
      "quests/minor_quest/mq002_veterans/mq002_veterans/01_intro",
      "quests/minor_quest/mq002_veterans/mq002_veterans/01_intro/mq002_description",
      "quests/minor_quest/mq002_veterans/mq002_veterans/02_deal",
      "quests/minor_quest/mq002_veterans/mq002_veterans/03_fight",
      "quests/minor_quest/mq002_veterans/mq002_veterans/04_summary"
    ]; }
    if i == 50 { return [
      "quests/minor_quest/mq021_guide",
      "quests/minor_quest/mq021_guide/mq021_guide",
      "quests/minor_quest/mq021_guide/mq021_guide/04_meeting",
      "quests/minor_quest/mq021_guide/mq021_guide/04_meeting/mq021_description",
      "quests/minor_quest/mq021_guide/mq021_guide/05_participate_meeting",
      "quests/minor_quest/mq021_guide/mq021_guide/06_defend",
      "quests/minor_quest/mq021_guide/mq021_guide/07_confront_doctor",
      "quests/minor_quest/mq021_guide/mq021_guide/08_outcome",
      "quests/minor_quest/mq021_guide/mq021_guide/09_ending",
      "quests/minor_quest/mq021_guide/mq021_guide/07_2_get_suitcase",
      "quests/minor_quest/mq021_guide/mq021_guide/10_ending_wait",
      "quests/minor_quest/mq021_guide/mq021_guide/07_1_kill_doctor",
      "quests/minor_quest/mq021_guide/mq021_guide/11_ending_read"
    ]; }
    if i == 51 { return [
      "quests/minor_quest/mq041_corpo",
      "quests/minor_quest/mq041_corpo/corpo",
      "quests/minor_quest/mq041_corpo/corpo/01_find_the_briefcase",
      "quests/minor_quest/mq041_corpo/corpo/01_find_the_briefcase/description",
      "quests/minor_quest/mq041_corpo/corpo/02_open_the_briefcase",
      "quests/minor_quest/mq041_corpo/corpo/03_talk_with_stranger",
      "quests/minor_quest/mq041_corpo/corpo/04_confront_frank",
      "quests/minor_quest/mq041_corpo/corpo/01a_talk_with_johnny",
      "quests/minor_quest/mq041_corpo/corpo/01b_lift_the_dumpster",
      "quests/minor_quest/mq041_corpo/corpo/01a_talk_with_johnny1"
    ]; }
    if i == 52 { return [
      "ep1/quests/minor_quest/sts_ep1_08_steven_meeting_night_city",
      "ep1/quests/minor_quest/sts_ep1_08_steven_meeting_night_city/steven_default_night_city",
      "ep1/quests/minor_quest/sts_ep1_08_steven_meeting_night_city/steven_default_night_city/steven_meeting",
      "ep1/quests/minor_quest/sts_ep1_08_steven_meeting_night_city/steven_default_night_city/read_message_from_steven",
      "ep1/quests/minor_quest/sts_ep1_08_steven_meeting_night_city/steven_default_night_city/talk_with_steven",
      "ep1/quests/minor_quest/sts_ep1_08_steven_meeting_night_city/steven_default_night_city_description"
    ]; }
    if i == 53 { return [
      "ep1/quests/minor_quest/q304_car_retrieval",
      "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval",
      "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/01_reach_the_door",
      "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/02_use_the_panel_in_the_security_room_to_open_the_shutter",
      "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/03_get_to_the_car",
      "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/04_get_into_the_car",
      "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/05_connect_to_the_cars_onboard_computer_and_wipe_the_memory",
      "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/02_find_a_way_in",
      "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/01_reach_the_door1",
      "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/07_escape_with_the_car",
      "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/01_answer_to_ashlay_message",
      "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/03_wait_until_ashlay_opens_the_door",
      "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/04_dont_kill_or_alert_anyone",
      "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/01_wait_for_ashlay_message",
      "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/08_play_along",
      "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/05_clear_the_area",
      "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/09_go_back_to_the_car",
      "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/01_answer_to_ashlay_message2",
      "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/05_clear_the_area_retro",
      "ep1/quests/minor_quest/q304_car_retrieval/description"
    ]; }
    if i == 54 { return [
      "quests/minor_quest/mq019_paparazzi",
      "quests/minor_quest/mq019_paparazzi/01_notell_motel",
      "quests/minor_quest/mq019_paparazzi/01_notell_motel/01_go_to_notell_motel",
      "quests/minor_quest/mq019_paparazzi/01_notell_motel/02_talk_with_client",
      "quests/minor_quest/mq019_paparazzi/01_notell_motel/02a_sit_down",
      "quests/minor_quest/mq019_paparazzi/00_hook",
      "quests/minor_quest/mq019_paparazzi/00_hook/01_read_message",
      "quests/minor_quest/mq019_paparazzi/00_hook/01_read_message/description",
      "quests/minor_quest/mq019_paparazzi/03_riot_night_club",
      "quests/minor_quest/mq019_paparazzi/03_riot_night_club/01_go_to_riot",
      "quests/minor_quest/mq019_paparazzi/03_riot_night_club/02_ask_about_liam",
      "quests/minor_quest/mq019_paparazzi/03_riot_night_club/02_find_liam",
      "quests/minor_quest/mq019_paparazzi/03_riot_night_club/03_check_vip_lounge",
      "quests/minor_quest/mq019_paparazzi/03_riot_night_club/04_talk_with_johnny",
      "quests/minor_quest/mq019_paparazzi/03_riot_night_club/03a_confront_liam",
      "quests/minor_quest/mq019_paparazzi/03_riot_night_club/03b_defeat_security",
      "quests/minor_quest/mq019_paparazzi/03_riot_night_club/05_steal_recordings",
      "quests/minor_quest/mq019_paparazzi/03_riot_night_club/03b_leave_vip_lounge",
      "quests/minor_quest/mq019_paparazzi/03_riot_night_club/00_suspend_quest",
      "quests/minor_quest/mq019_paparazzi/03_riot_night_club/02b_break_into_security",
      "quests/minor_quest/mq019_paparazzi/03_riot_night_club/02d_check_cameras",
      "quests/minor_quest/mq019_paparazzi/03_riot_night_club/02c_check_computer",
      "quests/minor_quest/mq019_paparazzi/05_holocall",
      "quests/minor_quest/mq019_paparazzi/05_holocall/01_call_client",
      "quests/minor_quest/mq019_paparazzi/05_holocall/02_send_data",
      "quests/minor_quest/mq019_paparazzi/06_finale",
      "quests/minor_quest/mq019_paparazzi/06_finale/01_pick_up",
      "quests/minor_quest/mq019_paparazzi/06_finale/02_go_to_notell",
      "quests/minor_quest/mq019_paparazzi/06_finale/03_talk_with_client",
      "quests/minor_quest/mq019_paparazzi/06_finale/04_move_body",
      "quests/minor_quest/mq019_paparazzi/06_finale/04a_ask_about_wounds"
    ]; }
    let empty: array<String>; return empty;
  }
  public static func DetailClasses(i: Int32) -> array<String> {
    if i == 0 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription"
    ]; }
    if i == 1 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective"
    ]; }
    if i == 2 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription"
    ]; }
    if i == 3 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription"
    ]; }
    if i == 4 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 5 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 6 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 7 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 8 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 9 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription"
    ]; }
    if i == 10 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription"
    ]; }
    if i == 11 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 12 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 13 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestDescription"
    ]; }
    if i == 14 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription"
    ]; }
    if i == 15 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription"
    ]; }
    if i == 16 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 17 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective"
    ]; }
    if i == 18 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 19 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 20 { return [
      "gameJournalQuest",
      "gameJournalQuestDescription",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective"
    ]; }
    if i == 21 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription"
    ]; }
    if i == 22 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription"
    ]; }
    if i == 23 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription"
    ]; }
    if i == 24 { return [
      "gameJournalQuest",
      "gameJournalQuestDescription",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 25 { return [
      "gameJournalQuest",
      "gameJournalQuestDescription",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 26 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 27 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective"
    ]; }
    if i == 28 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription"
    ]; }
    if i == 29 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription"
    ]; }
    if i == 30 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription"
    ]; }
    if i == 31 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective"
    ]; }
    if i == 32 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 33 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 34 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 35 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 36 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 37 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 38 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 39 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 40 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription"
    ]; }
    if i == 41 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 42 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 43 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 44 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 45 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 46 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 47 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription"
    ]; }
    if i == 48 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 49 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 50 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 51 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    if i == 52 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription"
    ]; }
    if i == 53 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription"
    ]; }
    if i == 54 { return [
      "gameJournalQuest",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestDescription",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestPhase",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective",
      "gameJournalQuestObjective"
    ]; }
    let empty: array<String>; return empty;
  }
  public static func FactNames(i: Int32) -> array<String> {
    if i == 0 { return SideJobFailureDataS21.FactNames0(); }
    if i == 1 { return SideJobFailureDataS21.FactNames1(); }
    if i == 2 { return SideJobFailureDataS21.FactNames2(); }
    if i == 3 { return SideJobFailureDataS21.FactNames3(); }
    if i == 4 { return SideJobFailureDataS21.FactNames4(); }
    if i == 5 { return SideJobFailureDataS21.FactNames5(); }
    if i == 6 { return SideJobFailureDataS21.FactNames6(); }
    if i == 7 { return SideJobFailureDataS21.FactNames7(); }
    if i == 8 { return SideJobFailureDataS21.FactNames8(); }
    if i == 9 { return SideJobFailureDataS21.FactNames9(); }
    if i == 10 { return SideJobFailureDataS21.FactNames10(); }
    if i == 11 { return SideJobFailureDataS21.FactNames11(); }
    if i == 12 { return SideJobFailureDataS21.FactNames12(); }
    if i == 13 { return SideJobFailureDataS21.FactNames13(); }
    if i == 14 { return SideJobFailureDataS21.FactNames14(); }
    if i == 15 { return SideJobFailureDataS21.FactNames15(); }
    if i == 16 { return SideJobFailureDataS21.FactNames16(); }
    if i == 17 { return SideJobFailureDataS21.FactNames17(); }
    if i == 18 { return SideJobFailureDataS21.FactNames18(); }
    if i == 19 { return SideJobFailureDataS21.FactNames19(); }
    if i == 20 { return SideJobFailureDataS21.FactNames20(); }
    if i == 21 { return SideJobFailureDataS21.FactNames21(); }
    if i == 22 { return SideJobFailureDataS21.FactNames22(); }
    if i == 23 { return SideJobFailureDataS21.FactNames23(); }
    if i == 24 { return SideJobFailureDataS21.FactNames24(); }
    if i == 25 { return SideJobFailureDataS21.FactNames25(); }
    if i == 26 { return SideJobFailureDataS21.FactNames26(); }
    if i == 27 { return SideJobFailureDataS21.FactNames27(); }
    if i == 28 { return SideJobFailureDataS21.FactNames28(); }
    if i == 29 { return SideJobFailureDataS21.FactNames29(); }
    if i == 30 { return SideJobFailureDataS21.FactNames30(); }
    if i == 31 { return SideJobFailureDataS21.FactNames31(); }
    if i == 32 { return SideJobFailureDataS21.FactNames32(); }
    if i == 33 { return SideJobFailureDataS21.FactNames33(); }
    if i == 34 { return SideJobFailureDataS21.FactNames34(); }
    if i == 35 { return SideJobFailureDataS21.FactNames35(); }
    if i == 36 { return SideJobFailureDataS21.FactNames36(); }
    if i == 37 { return SideJobFailureDataS21.FactNames37(); }
    if i == 38 { return SideJobFailureDataS21.FactNames38(); }
    if i == 39 { return SideJobFailureDataS21.FactNames39(); }
    if i == 40 { return SideJobFailureDataS21.FactNames40(); }
    if i == 41 { return SideJobFailureDataS21.FactNames41(); }
    if i == 42 { return SideJobFailureDataS21.FactNames42(); }
    if i == 43 { return SideJobFailureDataS21.FactNames43(); }
    if i == 44 { return SideJobFailureDataS21.FactNames44(); }
    if i == 45 { return SideJobFailureDataS21.FactNames45(); }
    if i == 46 { return SideJobFailureDataS21.FactNames46(); }
    if i == 47 { return SideJobFailureDataS21.FactNames47(); }
    if i == 48 { return SideJobFailureDataS21.FactNames48(); }
    if i == 49 { return SideJobFailureDataS21.FactNames49(); }
    if i == 50 { return SideJobFailureDataS21.FactNames50(); }
    if i == 51 { return SideJobFailureDataS21.FactNames51(); }
    if i == 52 { return SideJobFailureDataS21.FactNames52(); }
    if i == 53 { return SideJobFailureDataS21.FactNames53(); }
    if i == 54 { return SideJobFailureDataS21.FactNames54(); }
    let empty: array<String>; return empty;
  }
  public static func FactNames0() -> array<String> {
    let empty: array<String>; return empty;
  }
  public static func FactNames1() -> array<String> {
    let empty: array<String>; return empty;
  }
  public static func FactNames2() -> array<String> {
    let empty: array<String>; return empty;
  }
  public static func FactNames3() -> array<String> {
    return [
      "codex_sandra_dorsett",
      "holo_v_calls_sandra_dorsett_end_activate",
      "holo_v_calls_sandra_dorsett_start_activate",
      "kab_05_activated",
      "mq024_active",
      "mq024_combat_sandra",
      "mq024_done",
      "mq024_hacked_data_carrier",
      "mq024_hook_taken",
      "mq024_sandra_opened_door",
      "mq024_test_with_sts",
      "q000_done",
      "q101_done",
      "q305_haunted_weapon_random_whisper_02",
      "q305_haunted_weapon_random_whisper_02_used",
      "travelling_merchant_lives"
    ];
  }
  public static func FactNames4() -> array<String> {
    return [
      "gmpl_npc_defeated_by_player",
      "gmpl_npc_downed_by_player",
      "gmpl_npc_incapacitated_by_player",
      "gmpl_npc_killed_by_player",
      "mq007_debug",
      "mq007_done",
      "mq007_interrupt_skippy_dialogue",
      "mq007_opt_A",
      "mq007_rapid_interrupt",
      "mq007_skippy_50_enemies_defeated",
      "mq007_skippy_50_enemies_killed_and_stoneColdKiller",
      "mq007_skippy_50_enemies_maimed",
      "mq007_skippy_aiming",
      "mq007_skippy_annoyed",
      "mq007_skippy_annoyed_active",
      "mq007_skippy_cheer",
      "mq007_skippy_cheer_active",
      "mq007_skippy_enemies_lethal",
      "mq007_skippy_enemies_non_lethal",
      "mq007_skippy_enemies_total",
      "mq007_skippy_frown",
      "mq007_skippy_frown_active",
      "mq007_skippy_goes_emo",
      "mq007_skippy_happy",
      "mq007_skippy_happy_active",
      "mq007_skippy_owner_known",
      "mq007_skippy_re_acquiring_done",
      "mq007_skippy_reload",
      "mq007_skippy_sad",
      "mq007_skippy_sad_active",
      "mq007_skippy_scared",
      "mq007_skippy_scared_active",
      "mq007_skippy_smile",
      "mq007_skippy_smile_active",
      "mq007_skippy_stash",
      "mq007_skippy_wow",
      "mq007_skippy_wow_active",
      "q001_show_sts_tut",
      "reggie_default_on",
      "sts_loop_start",
      "travelling_merchant_lives"
    ];
  }
  public static func FactNames5() -> array<String> {
    return [
      "audio_v_calls_ozob_end_activate",
      "audio_v_calls_ozob_start_activate",
      "ep1_standalone",
      "mq035_car_ride",
      "mq035_done",
      "mq035_drive_chat",
      "mq035_ow_despawn",
      "travelling_merchant_lives",
      "wanted_level"
    ];
  }
  public static func FactNames6() -> array<String> {
    return [
      "disable_tutorials",
      "mq013_active",
      "mq013_dealt_with_punks_somehow",
      "mq013_done",
      "mq013_far_away",
      "mq013_punch",
      "mq013_punk_combat_shopkeeper",
      "mq013_punk_combat_start",
      "mq013_punks_dead_before_scene",
      "mq013_punks_defeated",
      "q000_done",
      "q101_done",
      "sq024_mq013_active_timeskipped",
      "std_arr_foodshop_03_dead",
      "std_arr_foodshop_03_default_on",
      "std_arr_foodshop_03_discount_on",
      "travelling_merchant_lives",
      "tv_on"
    ];
  }
  public static func FactNames7() -> array<String> {
    return [
      "cct_dtn_cloth_01_default_on",
      "mq030_active",
      "mq030_done",
      "mq030_failed",
      "mq030_kill_scene",
      "mq030_maxtac_arrived",
      "mq030_zane_grateful",
      "mq030_zane_met",
      "travelling_merchant_lives"
    ];
  }
  public static func FactNames8() -> array<String> {
    return [
      "disable_tutorials",
      "holo_mr_stud_calls_v_end_activate",
      "holo_mr_stud_calls_v_start_activate",
      "mq012_active",
      "mq012_arrived_in_car",
      "mq012_can_stop_at_ripperdoc",
      "mq012_debug",
      "mq012_disable_blockade",
      "mq012_disabled_truck_blockade",
      "mq012_done",
      "mq012_kids_past_danger",
      "mq012_stud_dead",
      "mq012_stud_stop_pose",
      "q000_done",
      "q001_going_to_rd_by_car",
      "q001_ripperdoc_done",
      "save_lock_fact_waiting_forever",
      "travelling_merchant_lives",
      "wanted_level"
    ];
  }
  public static func FactNames9() -> array<String> {
    return [
      "disable_tutorials",
      "ep1_standalone",
      "holo_wilson_calls_v_end_activate",
      "holo_wilson_calls_v_start_activate",
      "mq011_active",
      "mq011_done",
      "mq011_shooting_over",
      "q001_start_wilson_quest",
      "q101_done",
      "travelling_merchant_lives",
      "wat_lch_gunsmith_01_default_on",
      "wilson_shooting_range_left"
    ];
  }
  public static func FactNames10() -> array<String> {
    return [
      "mq010_active",
      "mq010_asked_about_andrew",
      "mq010_barry_turned_cyberpsycho",
      "mq010_done",
      "mq010_johnny_spawned",
      "mq010_know_about_andrew",
      "mq010_objective_started",
      "mq010_reactivate_scene",
      "mq010_talk_about_barry",
      "mq010_talk_to_barry_maybe",
      "mq010_testfact_told_police",
      "mq010_told_police_ab_andrew",
      "q000_done",
      "q101_done",
      "travelling_merchant_lives",
      "wanted_level"
    ];
  }
  public static func FactNames11() -> array<String> {
    return [
      "mq005_done",
      "mq005_police_done",
      "mq005_police_left",
      "travelling_merchant_lives",
      "wanted_level"
    ];
  }
  public static func FactNames12() -> array<String> {
    return [
      "mq008_active",
      "mq008_bonus_points_enabled",
      "mq008_done",
      "mq008_final_score",
      "mq008_golden_knuckles_owned",
      "mq008_player_cheated",
      "mq008_poster_destroyer_fix",
      "mq008_quest_comm_on",
      "mq008_quest_item_tags_cleaned",
      "mq008_representative_defeated",
      "mq008_reward_unsealed",
      "mq008_shooting1_done",
      "mq008_shooting2_done",
      "mq008_shooting3_done",
      "mq008_shooting4_done",
      "mq008_talks_finished",
      "mq008_telem_combat",
      "mq008_time_to_spot1",
      "mq008_v_starts_competition",
      "mq008_v_wins",
      "radio_on",
      "travelling_merchant_lives",
      "v_offends_boss"
    ];
  }
  public static func FactNames13() -> array<String> {
    return [
      "disable_tutorials",
      "mq032_complete",
      "mq032_dead",
      "mq032_help",
      "mq032_monk1_met",
      "mq032_nonlethal",
      "mq032_saved",
      "mq032_skip_epilogue",
      "mq032_test_def",
      "q101_enable_side_content",
      "travelling_merchant_lives",
      "tv_on"
    ];
  }
  public static func FactNames14() -> array<String> {
    return [
      "air_traffic_off",
      "ep1_standalone",
      "holo_mr_hands_calls_v_end_activate",
      "holo_mr_hands_calls_v_end_done",
      "holo_mr_hands_calls_v_start_activate",
      "holo_mr_hands_calls_v_start_done",
      "holo_v_calls_mr_hands_end_activate",
      "holo_v_calls_mr_hands_end_done",
      "holo_v_calls_mr_hands_start_activate",
      "holo_v_calls_mr_hands_start_done",
      "mq305_01_active",
      "mq305_01_done",
      "mq305_02_active",
      "mq305_02_done",
      "mq305_03_active",
      "mq305_03_done",
      "mq305_04_active",
      "mq305_04_bunker_dante_introduced_himself",
      "mq305_04_done",
      "mq305_04_johnny_despawned",
      "mq305_04b_start_turret_combat",
      "mq305_04b_start_turret_combat_2",
      "mq305_04b_told_about_max_jones",
      "mq305_05_active",
      "mq305_05_done",
      "mq305_V_told_Bree_hide",
      "mq305_active",
      "mq305_both_killed",
      "mq305_bree_dead",
      "mq305_bree_in_standoff_position",
      "mq305_dante_dying_cut_combat_shouts",
      "mq305_dante_killed",
      "mq305_dante_picked_data",
      "mq305_dante_picked_shard",
      "mq305_debug_run",
      "mq305_done",
      "mq305_failed",
      "mq305_finished",
      "mq305_johnny_comment_all_dead_trigger_01",
      "mq305_johnny_comment_all_dead_trigger_02",
      "mq305_johnny_comment_all_dead_trigger_03a",
      "mq305_johnny_comment_all_dead_trigger_03b",
      "mq305_johnny_comment_all_dead_trigger_04a",
      "mq305_johnny_comment_all_dead_trigger_04b",
      "mq305_johnny_comment_all_dead_trigger_04c",
      "mq305_johnny_comment_all_dead_trigger_05",
      "mq305_johnny_comment_all_dead_trigger_06",
      "mq305_lab_johnny_comments_on_max_jones_finished",
      "mq305_lab_mines_02_deactivated",
      "mq305_lab_mines_03_deactivated",
      "mq305_lab_mines_04_deactivated",
      "mq305_lab_mines_06_deactivated",
      "mq305_lab_mines_07_deactivated",
      "mq305_lab_turret_04_destroyed",
      "mq305_lab_turret_05_destroyed",
      "mq305_lab_turrets_01_deactivated",
      "mq305_lab_turrets_02_deactivated",
      "mq305_lab_turrets_03_deactivated",
      "mq305_lab_turrets_1_cameras_hacked",
      "mq305_lab_turrets_1_defeated",
      "mq305_lab_turrets_1_mines_deactivated",
      "mq305_lab_turrets_1_trigger_fight",
      "mq305_lab_turrets_1_trigger_scan",
      "mq305_lab_turrets_2_cameras_hacked",
      "mq305_lab_turrets_2_defeated",
      "mq305_lab_turrets_2_mines_deactivated",
      "mq305_lab_turrets_2_trigger_fight",
      "mq305_lab_turrets_2_trigger_scan",
      "mq305_mr_hands_sell_data",
      "mq305_mr_hands_sends_briefing",
      "mq305_netwatch_play_line",
      "mq305_started",
      "mq305_started_from_chicken_test_2",
      "mq305_started_from_chicken_test_3",
      "mq305_started_from_chicken_test_4",
      "mq305_started_from_chicken_test_5",
      "mq305_took_over_camera",
      "mq305_v_has_data",
      "mq305_v_killed_bree",
      "mq305_v_picked_shard_from_dante",
      "mr_hands_default_on",
      "travelling_merchant",
      "travelling_merchant_lives"
    ];
  }
  public static func FactNames15() -> array<String> {
    let empty: array<String>; return empty;
  }
  public static func FactNames16() -> array<String> {
    return [
      "holo_interrupt_call_manual",
      "mq038_active",
      "mq038_deliver_inactive",
      "mq038_done",
      "mq038_dumpster_opened",
      "mq038_fake_01_opened",
      "mq038_fake_02_opened",
      "mq038_hide_inactive",
      "q005_start",
      "travelling_merchant_lives"
    ];
  }
  public static func FactNames17() -> array<String> {
    return [
      "hey_rey_techstore_01_default_on",
      "mq037_01_05Sure",
      "mq037_brendan_introduced",
      "mq037_clerk_aggroed",
      "mq037_clerk_convinced",
      "mq037_done",
      "mq037_final_scene_active",
      "mq037_kill_token_block_loop",
      "mq037_post_girl_scene_on",
      "mq037_vandal_painted_brendan",
      "travelling_merchant_lives"
    ];
  }
  public static func FactNames18() -> array<String> {
    return [
      "hey_rey_techstore_01_default_on",
      "mq037_01_05Sure",
      "mq037_brendan_introduced",
      "mq037_clerk_aggroed",
      "mq037_clerk_convinced",
      "mq037_done",
      "mq037_final_scene_active",
      "mq037_kill_token_block_loop",
      "mq037_post_girl_scene_on",
      "mq037_vandal_painted_brendan",
      "travelling_merchant_lives"
    ];
  }
  public static func FactNames19() -> array<String> {
    return [
      "hey_rey_techstore_01_default_on",
      "mq037_01_05Sure",
      "mq037_brendan_introduced",
      "mq037_clerk_aggroed",
      "mq037_clerk_convinced",
      "mq037_done",
      "mq037_final_scene_active",
      "mq037_kill_token_block_loop",
      "mq037_post_girl_scene_on",
      "mq037_vandal_painted_brendan",
      "travelling_merchant_lives"
    ];
  }
  public static func FactNames20() -> array<String> {
    return [
      "mq049_done",
      "mq049_falco_done",
      "mq049_finished",
      "mq049_jacket_looted",
      "mq049_reyes_distance_comment",
      "mq049_started",
      "q101_enable_side_content"
    ];
  }
  public static func FactNames21() -> array<String> {
    return [
      "bill_default_on",
      "ep1_standalone",
      "sts_ep1_10_debug_fact_1111",
      "sts_ep1_10_dodger_dead",
      "ws_ep1_11_chicken_test_journal_start",
      "wst_ep1_11_hotdog_finished",
      "wst_ep1_11_ncpd_finished",
      "wst_ep1_11_ncpd_start"
    ];
  }
  public static func FactNames22() -> array<String> {
    let empty: array<String>; return empty;
  }
  public static func FactNames23() -> array<String> {
    let empty: array<String>; return empty;
  }
  public static func FactNames24() -> array<String> {
    let empty: array<String>; return empty;
  }
  public static func FactNames25() -> array<String> {
    let empty: array<String>; return empty;
  }
  public static func FactNames26() -> array<String> {
    return [
      "creole_translator_unlocked",
      "disable_tutorials",
      "ep1_standalone",
      "glossary_6thstreet",
      "mq025_02_cheer_active",
      "mq025_02_chosen",
      "mq025_02_fight_active",
      "mq025_02_fight_started",
      "mq025_02_kabuki_active",
      "mq025_02_player_wins",
      "mq025_03_arroyo_active",
      "mq025_03_chosen",
      "mq025_03_fight_active",
      "mq025_03_fight_started",
      "mq025_03_player_wins",
      "mq025_05_chosen",
      "mq025_05_fight_active",
      "mq025_05_fight_started",
      "mq025_05_gave_money",
      "mq025_05_glen_active",
      "mq025_05_player_wins",
      "mq025_06_chosen",
      "mq025_06_ozob_fight_started",
      "mq025_06_ozob_player_wins",
      "mq025_06_pacifica_active",
      "mq025_06_pacifica_fight_active",
      "mq025_07_chosen",
      "mq025_07_fight_club",
      "mq025_07_fight_started",
      "mq025_07_fight_starts",
      "mq025_07_player_wins",
      "mq025_08_final_fight_active",
      "mq025_08_finale_player_wins",
      "mq025_08_finale_started",
      "mq025_buck_dead",
      "mq025_cash",
      "mq025_choose_fight",
      "mq025_done",
      "mq025_finale_started",
      "mq025_fist_fight_quest_start",
      "mq025_ozob_exploded",
      "mq025_quest_started",
      "mq025_razor_walks",
      "mq025_rhino_dead",
      "mq025_rhino_happy",
      "mq025_test_definition",
      "mq025_trainer_angry",
      "mq025_trainer_skipped",
      "mq025_twin_01_down",
      "mq025_twin_02_down",
      "mq025_twins_player_down",
      "mq035_done",
      "ozob_weakspot_nose_destroyed",
      "padre_default_on",
      "q000_done",
      "q001_wakeup_scene_done",
      "q101_enable_side_content",
      "q110_done",
      "q301_started",
      "travelling_merchant_lives",
      "wat_lch_melee_01_default_on",
      "watson_prolog_unlock",
      "wwd_05_done"
    ];
  }
  public static func FactNames27() -> array<String> {
    return [
      "creole_translator_unlocked",
      "disable_tutorials",
      "ep1_standalone",
      "glossary_6thstreet",
      "mq025_02_cheer_active",
      "mq025_02_chosen",
      "mq025_02_fight_active",
      "mq025_02_fight_started",
      "mq025_02_kabuki_active",
      "mq025_02_player_wins",
      "mq025_03_arroyo_active",
      "mq025_03_chosen",
      "mq025_03_fight_active",
      "mq025_03_fight_started",
      "mq025_03_player_wins",
      "mq025_05_chosen",
      "mq025_05_fight_active",
      "mq025_05_fight_started",
      "mq025_05_gave_money",
      "mq025_05_glen_active",
      "mq025_05_player_wins",
      "mq025_06_chosen",
      "mq025_06_ozob_fight_started",
      "mq025_06_ozob_player_wins",
      "mq025_06_pacifica_active",
      "mq025_06_pacifica_fight_active",
      "mq025_07_chosen",
      "mq025_07_fight_club",
      "mq025_07_fight_started",
      "mq025_07_fight_starts",
      "mq025_07_player_wins",
      "mq025_08_final_fight_active",
      "mq025_08_finale_player_wins",
      "mq025_08_finale_started",
      "mq025_buck_dead",
      "mq025_cash",
      "mq025_choose_fight",
      "mq025_done",
      "mq025_finale_started",
      "mq025_fist_fight_quest_start",
      "mq025_ozob_exploded",
      "mq025_quest_started",
      "mq025_razor_walks",
      "mq025_rhino_dead",
      "mq025_rhino_happy",
      "mq025_test_definition",
      "mq025_trainer_angry",
      "mq025_trainer_skipped",
      "mq025_twin_01_down",
      "mq025_twin_02_down",
      "mq025_twins_player_down",
      "mq035_done",
      "ozob_weakspot_nose_destroyed",
      "padre_default_on",
      "q000_done",
      "q001_wakeup_scene_done",
      "q101_enable_side_content",
      "q110_done",
      "q301_started",
      "travelling_merchant_lives",
      "wat_lch_melee_01_default_on",
      "watson_prolog_unlock",
      "wwd_05_done"
    ];
  }
  public static func FactNames28() -> array<String> {
    return [
      "creole_translator_unlocked",
      "disable_tutorials",
      "ep1_standalone",
      "glossary_6thstreet",
      "mq025_02_cheer_active",
      "mq025_02_chosen",
      "mq025_02_fight_active",
      "mq025_02_fight_started",
      "mq025_02_kabuki_active",
      "mq025_02_player_wins",
      "mq025_03_arroyo_active",
      "mq025_03_chosen",
      "mq025_03_fight_active",
      "mq025_03_fight_started",
      "mq025_03_player_wins",
      "mq025_05_chosen",
      "mq025_05_fight_active",
      "mq025_05_fight_started",
      "mq025_05_gave_money",
      "mq025_05_glen_active",
      "mq025_05_player_wins",
      "mq025_06_chosen",
      "mq025_06_ozob_fight_started",
      "mq025_06_ozob_player_wins",
      "mq025_06_pacifica_active",
      "mq025_06_pacifica_fight_active",
      "mq025_07_chosen",
      "mq025_07_fight_club",
      "mq025_07_fight_started",
      "mq025_07_fight_starts",
      "mq025_07_player_wins",
      "mq025_08_final_fight_active",
      "mq025_08_finale_player_wins",
      "mq025_08_finale_started",
      "mq025_buck_dead",
      "mq025_cash",
      "mq025_choose_fight",
      "mq025_done",
      "mq025_finale_started",
      "mq025_fist_fight_quest_start",
      "mq025_ozob_exploded",
      "mq025_quest_started",
      "mq025_razor_walks",
      "mq025_rhino_dead",
      "mq025_rhino_happy",
      "mq025_test_definition",
      "mq025_trainer_angry",
      "mq025_trainer_skipped",
      "mq025_twin_01_down",
      "mq025_twin_02_down",
      "mq025_twins_player_down",
      "mq035_done",
      "ozob_weakspot_nose_destroyed",
      "padre_default_on",
      "q000_done",
      "q001_wakeup_scene_done",
      "q101_enable_side_content",
      "q110_done",
      "q301_started",
      "travelling_merchant_lives",
      "wat_lch_melee_01_default_on",
      "watson_prolog_unlock",
      "wwd_05_done"
    ];
  }
  public static func FactNames29() -> array<String> {
    return [
      "creole_translator_unlocked",
      "disable_tutorials",
      "ep1_standalone",
      "glossary_6thstreet",
      "mq025_02_cheer_active",
      "mq025_02_chosen",
      "mq025_02_fight_active",
      "mq025_02_fight_started",
      "mq025_02_kabuki_active",
      "mq025_02_player_wins",
      "mq025_03_arroyo_active",
      "mq025_03_chosen",
      "mq025_03_fight_active",
      "mq025_03_fight_started",
      "mq025_03_player_wins",
      "mq025_05_chosen",
      "mq025_05_fight_active",
      "mq025_05_fight_started",
      "mq025_05_gave_money",
      "mq025_05_glen_active",
      "mq025_05_player_wins",
      "mq025_06_chosen",
      "mq025_06_ozob_fight_started",
      "mq025_06_ozob_player_wins",
      "mq025_06_pacifica_active",
      "mq025_06_pacifica_fight_active",
      "mq025_07_chosen",
      "mq025_07_fight_club",
      "mq025_07_fight_started",
      "mq025_07_fight_starts",
      "mq025_07_player_wins",
      "mq025_08_final_fight_active",
      "mq025_08_finale_player_wins",
      "mq025_08_finale_started",
      "mq025_buck_dead",
      "mq025_cash",
      "mq025_choose_fight",
      "mq025_done",
      "mq025_finale_started",
      "mq025_fist_fight_quest_start",
      "mq025_ozob_exploded",
      "mq025_quest_started",
      "mq025_razor_walks",
      "mq025_rhino_dead",
      "mq025_rhino_happy",
      "mq025_test_definition",
      "mq025_trainer_angry",
      "mq025_trainer_skipped",
      "mq025_twin_01_down",
      "mq025_twin_02_down",
      "mq025_twins_player_down",
      "mq035_done",
      "ozob_weakspot_nose_destroyed",
      "padre_default_on",
      "q000_done",
      "q001_wakeup_scene_done",
      "q101_enable_side_content",
      "q110_done",
      "q301_started",
      "travelling_merchant_lives",
      "wat_lch_melee_01_default_on",
      "watson_prolog_unlock",
      "wwd_05_done"
    ];
  }
  public static func FactNames30() -> array<String> {
    return [
      "creole_translator_unlocked",
      "disable_tutorials",
      "ep1_standalone",
      "glossary_6thstreet",
      "mq025_02_cheer_active",
      "mq025_02_chosen",
      "mq025_02_fight_active",
      "mq025_02_fight_started",
      "mq025_02_kabuki_active",
      "mq025_02_player_wins",
      "mq025_03_arroyo_active",
      "mq025_03_chosen",
      "mq025_03_fight_active",
      "mq025_03_fight_started",
      "mq025_03_player_wins",
      "mq025_05_chosen",
      "mq025_05_fight_active",
      "mq025_05_fight_started",
      "mq025_05_gave_money",
      "mq025_05_glen_active",
      "mq025_05_player_wins",
      "mq025_06_chosen",
      "mq025_06_ozob_fight_started",
      "mq025_06_ozob_player_wins",
      "mq025_06_pacifica_active",
      "mq025_06_pacifica_fight_active",
      "mq025_07_chosen",
      "mq025_07_fight_club",
      "mq025_07_fight_started",
      "mq025_07_fight_starts",
      "mq025_07_player_wins",
      "mq025_08_final_fight_active",
      "mq025_08_finale_player_wins",
      "mq025_08_finale_started",
      "mq025_buck_dead",
      "mq025_cash",
      "mq025_choose_fight",
      "mq025_done",
      "mq025_finale_started",
      "mq025_fist_fight_quest_start",
      "mq025_ozob_exploded",
      "mq025_quest_started",
      "mq025_razor_walks",
      "mq025_rhino_dead",
      "mq025_rhino_happy",
      "mq025_test_definition",
      "mq025_trainer_angry",
      "mq025_trainer_skipped",
      "mq025_twin_01_down",
      "mq025_twin_02_down",
      "mq025_twins_player_down",
      "mq035_done",
      "ozob_weakspot_nose_destroyed",
      "padre_default_on",
      "q000_done",
      "q001_wakeup_scene_done",
      "q101_enable_side_content",
      "q110_done",
      "q301_started",
      "travelling_merchant_lives",
      "wat_lch_melee_01_default_on",
      "watson_prolog_unlock",
      "wwd_05_done"
    ];
  }
  public static func FactNames31() -> array<String> {
    return [
      "creole_translator_unlocked",
      "disable_tutorials",
      "ep1_standalone",
      "glossary_6thstreet",
      "mq025_02_cheer_active",
      "mq025_02_chosen",
      "mq025_02_fight_active",
      "mq025_02_fight_started",
      "mq025_02_kabuki_active",
      "mq025_02_player_wins",
      "mq025_03_arroyo_active",
      "mq025_03_chosen",
      "mq025_03_fight_active",
      "mq025_03_fight_started",
      "mq025_03_player_wins",
      "mq025_05_chosen",
      "mq025_05_fight_active",
      "mq025_05_fight_started",
      "mq025_05_gave_money",
      "mq025_05_glen_active",
      "mq025_05_player_wins",
      "mq025_06_chosen",
      "mq025_06_ozob_fight_started",
      "mq025_06_ozob_player_wins",
      "mq025_06_pacifica_active",
      "mq025_06_pacifica_fight_active",
      "mq025_07_chosen",
      "mq025_07_fight_club",
      "mq025_07_fight_started",
      "mq025_07_fight_starts",
      "mq025_07_player_wins",
      "mq025_08_final_fight_active",
      "mq025_08_finale_player_wins",
      "mq025_08_finale_started",
      "mq025_buck_dead",
      "mq025_cash",
      "mq025_choose_fight",
      "mq025_done",
      "mq025_finale_started",
      "mq025_fist_fight_quest_start",
      "mq025_ozob_exploded",
      "mq025_quest_started",
      "mq025_razor_walks",
      "mq025_rhino_dead",
      "mq025_rhino_happy",
      "mq025_test_definition",
      "mq025_trainer_angry",
      "mq025_trainer_skipped",
      "mq025_twin_01_down",
      "mq025_twin_02_down",
      "mq025_twins_player_down",
      "mq035_done",
      "ozob_weakspot_nose_destroyed",
      "padre_default_on",
      "q000_done",
      "q001_wakeup_scene_done",
      "q101_enable_side_content",
      "q110_done",
      "q301_started",
      "travelling_merchant_lives",
      "wat_lch_melee_01_default_on",
      "watson_prolog_unlock",
      "wwd_05_done"
    ];
  }
  public static func FactNames32() -> array<String> {
    return [
      "air_traffic_off",
      "delamain_briefing_talk",
      "delamain_default_on",
      "delamain_main_screen_loaded",
      "delamain_main_screen_talk",
      "delamain_main_screen_talk_active",
      "delamain_receptionist_talk",
      "delamain_receptionist_talk_active",
      "ep1_standalone",
      "holo_active_call_interrupted",
      "holo_delamain_angry_calls_v_active",
      "holo_delamain_angry_calls_v_end_activate",
      "holo_delamain_angry_calls_v_end_done",
      "holo_delamain_calls_v_active",
      "holo_delamain_calls_v_end_activate",
      "holo_delamain_calls_v_end_done",
      "holo_delamain_calls_v_start_activate",
      "holo_delamain_deep_calls_v_active",
      "holo_delamain_deep_calls_v_end_activate",
      "holo_delamain_deep_calls_v_end_done",
      "holo_delamain_deep_vehicle_talk",
      "holo_delamain_manic_calls_v_active",
      "holo_delamain_manic_calls_v_end_activate",
      "holo_delamain_manic_calls_v_end_done",
      "holo_delamain_mean_calls_v_active",
      "holo_delamain_mean_calls_v_end_activate",
      "holo_delamain_mean_calls_v_end_done",
      "holo_delamain_sad_calls_v_active",
      "holo_delamain_sad_calls_v_end_activate",
      "holo_delamain_sad_calls_v_end_done",
      "holo_delamain_scared_calls_v_active",
      "holo_delamain_scared_calls_v_end_activate",
      "holo_delamain_scared_calls_v_end_done",
      "holo_delamain_suicidal_calls_v_active",
      "holo_delamain_suicidal_calls_v_end_activate",
      "holo_delamain_suicidal_calls_v_end_done",
      "holo_setup_active",
      "holo_setup_started",
      "mean_cleanup_started",
      "mq027_busy",
      "phonecall_delamain_with_player",
      "q000_done",
      "q101_done",
      "q101_enable_side_content",
      "q103_done",
      "q105_done",
      "q112_done",
      "q115_point_of_no_return",
      "q307_point_of_no_return",
      "saq025_fate_sealed",
      "sq012_fact_river_driving_from_diner",
      "sq012_fact_suspend_sq025",
      "sq024_city_race_countdown_end",
      "sq024_city_race_finished",
      "sq024_santo_domingo_race_finished",
      "sq024_santo_domingo_race_started",
      "sq025_active",
      "sq025_angry_done",
      "sq025_angry_talk_end",
      "sq025_angry_talk_start",
      "sq025_briefing_scene_done",
      "sq025_buy_car",
      "sq025_cardrop_button_pressed",
      "sq025_clean",
      "sq025_debug",
      "sq025_deep_active",
      "sq025_deep_av_running",
      "sq025_deep_done",
      "sq025_deep_vehicle_screen",
      "sq025_delamain_damaged",
      "sq025_delamain_damaged_counter",
      "sq025_delamain_dd_reception",
      "sq025_delamain_default",
      "sq025_delamain_destroyed",
      "sq025_delamain_done",
      "sq025_disabled",
      "sq025_done",
      "sq025_failed",
      "sq025_failed_momentarily",
      "sq025_fate_sealed",
      "sq025_garage_gate_unlocked",
      "sq025_initialize_fail",
      "sq025_manic_done",
      "sq025_manic_talk_disconnect",
      "sq025_manic_talk_end",
      "sq025_manic_talk_start",
      "sq025_mean_committed",
      "sq025_mean_done",
      "sq025_mean_talk_02_end",
      "sq025_mean_talk_02_start",
      "sq025_mean_talk_03_end",
      "sq025_mean_talk_03_start",
      "sq025_mean_talk_end",
      "sq025_mean_talk_start",
      "sq025_office_exit_unlock",
      "sq025_power_button_pressed",
      "sq025_power_out",
      "sq025_reception_scene",
      "sq025_reception_scene_real_delamain",
      "sq025_reception_scene_real_delamain_transition",
      "sq025_resurgence_start",
      "sq025_roundabout",
      "sq025_sad_done",
      "sq025_sad_mounted",
      "sq025_sad_talk_end",
      "sq025_sad_talk_open",
      "sq025_sad_talk_start",
      "sq025_scan_angry_intro_done",
      "sq025_scan_deep_intro_done",
      "sq025_scan_manic_intro_done",
      "sq025_scan_mean_intro_done",
      "sq025_scan_sad_intro_done",
      "sq025_scan_savelock",
      "sq025_scan_scared_intro_done",
      "sq025_scan_should_be_active",
      "sq025_scan_suicidal_intro_done",
      "sq025_scans_done",
      "sq025_scared_committed",
      "sq025_scared_crashed",
      "sq025_scared_done",
      "sq025_scared_talk_end",
      "sq025_scared_talk_start",
      "sq025_skip_reception",
      "sq025_smalltalk",
      "sq025_suicidal_done",
      "sq025_suicidal_talk_cut",
      "sq025_suicidal_talk_end",
      "sq025_suicidal_talk_start",
      "sq025_traffic_jam",
      "sq025_trafficjam_poi_removed",
      "travelling_merchant_lives"
    ];
  }
  public static func FactNames33() -> array<String> {
    return [
      "air_traffic_off",
      "delamain_briefing_talk",
      "delamain_default_on",
      "delamain_main_screen_loaded",
      "delamain_main_screen_talk",
      "delamain_main_screen_talk_active",
      "delamain_receptionist_talk",
      "delamain_receptionist_talk_active",
      "ep1_standalone",
      "holo_active_call_interrupted",
      "holo_delamain_angry_calls_v_active",
      "holo_delamain_angry_calls_v_end_activate",
      "holo_delamain_angry_calls_v_end_done",
      "holo_delamain_calls_v_active",
      "holo_delamain_calls_v_end_activate",
      "holo_delamain_calls_v_end_done",
      "holo_delamain_calls_v_start_activate",
      "holo_delamain_deep_calls_v_active",
      "holo_delamain_deep_calls_v_end_activate",
      "holo_delamain_deep_calls_v_end_done",
      "holo_delamain_deep_vehicle_talk",
      "holo_delamain_manic_calls_v_active",
      "holo_delamain_manic_calls_v_end_activate",
      "holo_delamain_manic_calls_v_end_done",
      "holo_delamain_mean_calls_v_active",
      "holo_delamain_mean_calls_v_end_activate",
      "holo_delamain_mean_calls_v_end_done",
      "holo_delamain_sad_calls_v_active",
      "holo_delamain_sad_calls_v_end_activate",
      "holo_delamain_sad_calls_v_end_done",
      "holo_delamain_scared_calls_v_active",
      "holo_delamain_scared_calls_v_end_activate",
      "holo_delamain_scared_calls_v_end_done",
      "holo_delamain_suicidal_calls_v_active",
      "holo_delamain_suicidal_calls_v_end_activate",
      "holo_delamain_suicidal_calls_v_end_done",
      "holo_setup_active",
      "holo_setup_started",
      "mean_cleanup_started",
      "mq027_busy",
      "phonecall_delamain_with_player",
      "q000_done",
      "q101_done",
      "q101_enable_side_content",
      "q103_done",
      "q105_done",
      "q112_done",
      "q115_point_of_no_return",
      "q307_point_of_no_return",
      "saq025_fate_sealed",
      "sq012_fact_river_driving_from_diner",
      "sq012_fact_suspend_sq025",
      "sq024_city_race_countdown_end",
      "sq024_city_race_finished",
      "sq024_santo_domingo_race_finished",
      "sq024_santo_domingo_race_started",
      "sq025_active",
      "sq025_angry_done",
      "sq025_angry_talk_end",
      "sq025_angry_talk_start",
      "sq025_briefing_scene_done",
      "sq025_buy_car",
      "sq025_cardrop_button_pressed",
      "sq025_clean",
      "sq025_debug",
      "sq025_deep_active",
      "sq025_deep_av_running",
      "sq025_deep_done",
      "sq025_deep_vehicle_screen",
      "sq025_delamain_damaged",
      "sq025_delamain_damaged_counter",
      "sq025_delamain_dd_reception",
      "sq025_delamain_default",
      "sq025_delamain_destroyed",
      "sq025_delamain_done",
      "sq025_disabled",
      "sq025_done",
      "sq025_failed",
      "sq025_failed_momentarily",
      "sq025_fate_sealed",
      "sq025_garage_gate_unlocked",
      "sq025_initialize_fail",
      "sq025_manic_done",
      "sq025_manic_talk_disconnect",
      "sq025_manic_talk_end",
      "sq025_manic_talk_start",
      "sq025_mean_committed",
      "sq025_mean_done",
      "sq025_mean_talk_02_end",
      "sq025_mean_talk_02_start",
      "sq025_mean_talk_03_end",
      "sq025_mean_talk_03_start",
      "sq025_mean_talk_end",
      "sq025_mean_talk_start",
      "sq025_office_exit_unlock",
      "sq025_power_button_pressed",
      "sq025_power_out",
      "sq025_reception_scene",
      "sq025_reception_scene_real_delamain",
      "sq025_reception_scene_real_delamain_transition",
      "sq025_resurgence_start",
      "sq025_roundabout",
      "sq025_sad_done",
      "sq025_sad_mounted",
      "sq025_sad_talk_end",
      "sq025_sad_talk_open",
      "sq025_sad_talk_start",
      "sq025_scan_angry_intro_done",
      "sq025_scan_deep_intro_done",
      "sq025_scan_manic_intro_done",
      "sq025_scan_mean_intro_done",
      "sq025_scan_sad_intro_done",
      "sq025_scan_savelock",
      "sq025_scan_scared_intro_done",
      "sq025_scan_should_be_active",
      "sq025_scan_suicidal_intro_done",
      "sq025_scans_done",
      "sq025_scared_committed",
      "sq025_scared_crashed",
      "sq025_scared_done",
      "sq025_scared_talk_end",
      "sq025_scared_talk_start",
      "sq025_skip_reception",
      "sq025_smalltalk",
      "sq025_suicidal_done",
      "sq025_suicidal_talk_cut",
      "sq025_suicidal_talk_end",
      "sq025_suicidal_talk_start",
      "sq025_traffic_jam",
      "sq025_trafficjam_poi_removed",
      "travelling_merchant_lives"
    ];
  }
  public static func FactNames34() -> array<String> {
    return [
      "air_traffic_off",
      "delamain_briefing_talk",
      "delamain_default_on",
      "delamain_main_screen_loaded",
      "delamain_main_screen_talk",
      "delamain_main_screen_talk_active",
      "delamain_receptionist_talk",
      "delamain_receptionist_talk_active",
      "ep1_standalone",
      "holo_active_call_interrupted",
      "holo_delamain_angry_calls_v_active",
      "holo_delamain_angry_calls_v_end_activate",
      "holo_delamain_angry_calls_v_end_done",
      "holo_delamain_calls_v_active",
      "holo_delamain_calls_v_end_activate",
      "holo_delamain_calls_v_end_done",
      "holo_delamain_calls_v_start_activate",
      "holo_delamain_deep_calls_v_active",
      "holo_delamain_deep_calls_v_end_activate",
      "holo_delamain_deep_calls_v_end_done",
      "holo_delamain_deep_vehicle_talk",
      "holo_delamain_manic_calls_v_active",
      "holo_delamain_manic_calls_v_end_activate",
      "holo_delamain_manic_calls_v_end_done",
      "holo_delamain_mean_calls_v_active",
      "holo_delamain_mean_calls_v_end_activate",
      "holo_delamain_mean_calls_v_end_done",
      "holo_delamain_sad_calls_v_active",
      "holo_delamain_sad_calls_v_end_activate",
      "holo_delamain_sad_calls_v_end_done",
      "holo_delamain_scared_calls_v_active",
      "holo_delamain_scared_calls_v_end_activate",
      "holo_delamain_scared_calls_v_end_done",
      "holo_delamain_suicidal_calls_v_active",
      "holo_delamain_suicidal_calls_v_end_activate",
      "holo_delamain_suicidal_calls_v_end_done",
      "holo_setup_active",
      "holo_setup_started",
      "mean_cleanup_started",
      "mq027_busy",
      "phonecall_delamain_with_player",
      "q000_done",
      "q101_done",
      "q101_enable_side_content",
      "q103_done",
      "q105_done",
      "q112_done",
      "q115_point_of_no_return",
      "q307_point_of_no_return",
      "saq025_fate_sealed",
      "sq012_fact_river_driving_from_diner",
      "sq012_fact_suspend_sq025",
      "sq024_city_race_countdown_end",
      "sq024_city_race_finished",
      "sq024_santo_domingo_race_finished",
      "sq024_santo_domingo_race_started",
      "sq025_active",
      "sq025_angry_done",
      "sq025_angry_talk_end",
      "sq025_angry_talk_start",
      "sq025_briefing_scene_done",
      "sq025_buy_car",
      "sq025_cardrop_button_pressed",
      "sq025_clean",
      "sq025_debug",
      "sq025_deep_active",
      "sq025_deep_av_running",
      "sq025_deep_done",
      "sq025_deep_vehicle_screen",
      "sq025_delamain_damaged",
      "sq025_delamain_damaged_counter",
      "sq025_delamain_dd_reception",
      "sq025_delamain_default",
      "sq025_delamain_destroyed",
      "sq025_delamain_done",
      "sq025_disabled",
      "sq025_done",
      "sq025_failed",
      "sq025_failed_momentarily",
      "sq025_fate_sealed",
      "sq025_garage_gate_unlocked",
      "sq025_initialize_fail",
      "sq025_manic_done",
      "sq025_manic_talk_disconnect",
      "sq025_manic_talk_end",
      "sq025_manic_talk_start",
      "sq025_mean_committed",
      "sq025_mean_done",
      "sq025_mean_talk_02_end",
      "sq025_mean_talk_02_start",
      "sq025_mean_talk_03_end",
      "sq025_mean_talk_03_start",
      "sq025_mean_talk_end",
      "sq025_mean_talk_start",
      "sq025_office_exit_unlock",
      "sq025_power_button_pressed",
      "sq025_power_out",
      "sq025_reception_scene",
      "sq025_reception_scene_real_delamain",
      "sq025_reception_scene_real_delamain_transition",
      "sq025_resurgence_start",
      "sq025_roundabout",
      "sq025_sad_done",
      "sq025_sad_mounted",
      "sq025_sad_talk_end",
      "sq025_sad_talk_open",
      "sq025_sad_talk_start",
      "sq025_scan_angry_intro_done",
      "sq025_scan_deep_intro_done",
      "sq025_scan_manic_intro_done",
      "sq025_scan_mean_intro_done",
      "sq025_scan_sad_intro_done",
      "sq025_scan_savelock",
      "sq025_scan_scared_intro_done",
      "sq025_scan_should_be_active",
      "sq025_scan_suicidal_intro_done",
      "sq025_scans_done",
      "sq025_scared_committed",
      "sq025_scared_crashed",
      "sq025_scared_done",
      "sq025_scared_talk_end",
      "sq025_scared_talk_start",
      "sq025_skip_reception",
      "sq025_smalltalk",
      "sq025_suicidal_done",
      "sq025_suicidal_talk_cut",
      "sq025_suicidal_talk_end",
      "sq025_suicidal_talk_start",
      "sq025_traffic_jam",
      "sq025_trafficjam_poi_removed",
      "travelling_merchant_lives"
    ];
  }
  public static func FactNames35() -> array<String> {
    return [
      "air_traffic_off",
      "delamain_briefing_talk",
      "delamain_default_on",
      "delamain_main_screen_loaded",
      "delamain_main_screen_talk",
      "delamain_main_screen_talk_active",
      "delamain_receptionist_talk",
      "delamain_receptionist_talk_active",
      "ep1_standalone",
      "holo_active_call_interrupted",
      "holo_delamain_angry_calls_v_active",
      "holo_delamain_angry_calls_v_end_activate",
      "holo_delamain_angry_calls_v_end_done",
      "holo_delamain_calls_v_active",
      "holo_delamain_calls_v_end_activate",
      "holo_delamain_calls_v_end_done",
      "holo_delamain_calls_v_start_activate",
      "holo_delamain_deep_calls_v_active",
      "holo_delamain_deep_calls_v_end_activate",
      "holo_delamain_deep_calls_v_end_done",
      "holo_delamain_deep_vehicle_talk",
      "holo_delamain_manic_calls_v_active",
      "holo_delamain_manic_calls_v_end_activate",
      "holo_delamain_manic_calls_v_end_done",
      "holo_delamain_mean_calls_v_active",
      "holo_delamain_mean_calls_v_end_activate",
      "holo_delamain_mean_calls_v_end_done",
      "holo_delamain_sad_calls_v_active",
      "holo_delamain_sad_calls_v_end_activate",
      "holo_delamain_sad_calls_v_end_done",
      "holo_delamain_scared_calls_v_active",
      "holo_delamain_scared_calls_v_end_activate",
      "holo_delamain_scared_calls_v_end_done",
      "holo_delamain_suicidal_calls_v_active",
      "holo_delamain_suicidal_calls_v_end_activate",
      "holo_delamain_suicidal_calls_v_end_done",
      "holo_setup_active",
      "holo_setup_started",
      "mean_cleanup_started",
      "mq027_busy",
      "phonecall_delamain_with_player",
      "q000_done",
      "q101_done",
      "q101_enable_side_content",
      "q103_done",
      "q105_done",
      "q112_done",
      "q115_point_of_no_return",
      "q307_point_of_no_return",
      "saq025_fate_sealed",
      "sq012_fact_river_driving_from_diner",
      "sq012_fact_suspend_sq025",
      "sq024_city_race_countdown_end",
      "sq024_city_race_finished",
      "sq024_santo_domingo_race_finished",
      "sq024_santo_domingo_race_started",
      "sq025_active",
      "sq025_angry_done",
      "sq025_angry_talk_end",
      "sq025_angry_talk_start",
      "sq025_briefing_scene_done",
      "sq025_buy_car",
      "sq025_cardrop_button_pressed",
      "sq025_clean",
      "sq025_debug",
      "sq025_deep_active",
      "sq025_deep_av_running",
      "sq025_deep_done",
      "sq025_deep_vehicle_screen",
      "sq025_delamain_damaged",
      "sq025_delamain_damaged_counter",
      "sq025_delamain_dd_reception",
      "sq025_delamain_default",
      "sq025_delamain_destroyed",
      "sq025_delamain_done",
      "sq025_disabled",
      "sq025_done",
      "sq025_failed",
      "sq025_failed_momentarily",
      "sq025_fate_sealed",
      "sq025_garage_gate_unlocked",
      "sq025_initialize_fail",
      "sq025_manic_done",
      "sq025_manic_talk_disconnect",
      "sq025_manic_talk_end",
      "sq025_manic_talk_start",
      "sq025_mean_committed",
      "sq025_mean_done",
      "sq025_mean_talk_02_end",
      "sq025_mean_talk_02_start",
      "sq025_mean_talk_03_end",
      "sq025_mean_talk_03_start",
      "sq025_mean_talk_end",
      "sq025_mean_talk_start",
      "sq025_office_exit_unlock",
      "sq025_power_button_pressed",
      "sq025_power_out",
      "sq025_reception_scene",
      "sq025_reception_scene_real_delamain",
      "sq025_reception_scene_real_delamain_transition",
      "sq025_resurgence_start",
      "sq025_roundabout",
      "sq025_sad_done",
      "sq025_sad_mounted",
      "sq025_sad_talk_end",
      "sq025_sad_talk_open",
      "sq025_sad_talk_start",
      "sq025_scan_angry_intro_done",
      "sq025_scan_deep_intro_done",
      "sq025_scan_manic_intro_done",
      "sq025_scan_mean_intro_done",
      "sq025_scan_sad_intro_done",
      "sq025_scan_savelock",
      "sq025_scan_scared_intro_done",
      "sq025_scan_should_be_active",
      "sq025_scan_suicidal_intro_done",
      "sq025_scans_done",
      "sq025_scared_committed",
      "sq025_scared_crashed",
      "sq025_scared_done",
      "sq025_scared_talk_end",
      "sq025_scared_talk_start",
      "sq025_skip_reception",
      "sq025_smalltalk",
      "sq025_suicidal_done",
      "sq025_suicidal_talk_cut",
      "sq025_suicidal_talk_end",
      "sq025_suicidal_talk_start",
      "sq025_traffic_jam",
      "sq025_trafficjam_poi_removed",
      "travelling_merchant_lives"
    ];
  }
  public static func FactNames36() -> array<String> {
    return [
      "air_traffic_off",
      "delamain_briefing_talk",
      "delamain_default_on",
      "delamain_main_screen_loaded",
      "delamain_main_screen_talk",
      "delamain_main_screen_talk_active",
      "delamain_receptionist_talk",
      "delamain_receptionist_talk_active",
      "ep1_standalone",
      "holo_active_call_interrupted",
      "holo_delamain_angry_calls_v_active",
      "holo_delamain_angry_calls_v_end_activate",
      "holo_delamain_angry_calls_v_end_done",
      "holo_delamain_calls_v_active",
      "holo_delamain_calls_v_end_activate",
      "holo_delamain_calls_v_end_done",
      "holo_delamain_calls_v_start_activate",
      "holo_delamain_deep_calls_v_active",
      "holo_delamain_deep_calls_v_end_activate",
      "holo_delamain_deep_calls_v_end_done",
      "holo_delamain_deep_vehicle_talk",
      "holo_delamain_manic_calls_v_active",
      "holo_delamain_manic_calls_v_end_activate",
      "holo_delamain_manic_calls_v_end_done",
      "holo_delamain_mean_calls_v_active",
      "holo_delamain_mean_calls_v_end_activate",
      "holo_delamain_mean_calls_v_end_done",
      "holo_delamain_sad_calls_v_active",
      "holo_delamain_sad_calls_v_end_activate",
      "holo_delamain_sad_calls_v_end_done",
      "holo_delamain_scared_calls_v_active",
      "holo_delamain_scared_calls_v_end_activate",
      "holo_delamain_scared_calls_v_end_done",
      "holo_delamain_suicidal_calls_v_active",
      "holo_delamain_suicidal_calls_v_end_activate",
      "holo_delamain_suicidal_calls_v_end_done",
      "holo_setup_active",
      "holo_setup_started",
      "mean_cleanup_started",
      "mq027_busy",
      "phonecall_delamain_with_player",
      "q000_done",
      "q101_done",
      "q101_enable_side_content",
      "q103_done",
      "q105_done",
      "q112_done",
      "q115_point_of_no_return",
      "q307_point_of_no_return",
      "saq025_fate_sealed",
      "sq012_fact_river_driving_from_diner",
      "sq012_fact_suspend_sq025",
      "sq024_city_race_countdown_end",
      "sq024_city_race_finished",
      "sq024_santo_domingo_race_finished",
      "sq024_santo_domingo_race_started",
      "sq025_active",
      "sq025_angry_done",
      "sq025_angry_talk_end",
      "sq025_angry_talk_start",
      "sq025_briefing_scene_done",
      "sq025_buy_car",
      "sq025_cardrop_button_pressed",
      "sq025_clean",
      "sq025_debug",
      "sq025_deep_active",
      "sq025_deep_av_running",
      "sq025_deep_done",
      "sq025_deep_vehicle_screen",
      "sq025_delamain_damaged",
      "sq025_delamain_damaged_counter",
      "sq025_delamain_dd_reception",
      "sq025_delamain_default",
      "sq025_delamain_destroyed",
      "sq025_delamain_done",
      "sq025_disabled",
      "sq025_done",
      "sq025_failed",
      "sq025_failed_momentarily",
      "sq025_fate_sealed",
      "sq025_garage_gate_unlocked",
      "sq025_initialize_fail",
      "sq025_manic_done",
      "sq025_manic_talk_disconnect",
      "sq025_manic_talk_end",
      "sq025_manic_talk_start",
      "sq025_mean_committed",
      "sq025_mean_done",
      "sq025_mean_talk_02_end",
      "sq025_mean_talk_02_start",
      "sq025_mean_talk_03_end",
      "sq025_mean_talk_03_start",
      "sq025_mean_talk_end",
      "sq025_mean_talk_start",
      "sq025_office_exit_unlock",
      "sq025_power_button_pressed",
      "sq025_power_out",
      "sq025_reception_scene",
      "sq025_reception_scene_real_delamain",
      "sq025_reception_scene_real_delamain_transition",
      "sq025_resurgence_start",
      "sq025_roundabout",
      "sq025_sad_done",
      "sq025_sad_mounted",
      "sq025_sad_talk_end",
      "sq025_sad_talk_open",
      "sq025_sad_talk_start",
      "sq025_scan_angry_intro_done",
      "sq025_scan_deep_intro_done",
      "sq025_scan_manic_intro_done",
      "sq025_scan_mean_intro_done",
      "sq025_scan_sad_intro_done",
      "sq025_scan_savelock",
      "sq025_scan_scared_intro_done",
      "sq025_scan_should_be_active",
      "sq025_scan_suicidal_intro_done",
      "sq025_scans_done",
      "sq025_scared_committed",
      "sq025_scared_crashed",
      "sq025_scared_done",
      "sq025_scared_talk_end",
      "sq025_scared_talk_start",
      "sq025_skip_reception",
      "sq025_smalltalk",
      "sq025_suicidal_done",
      "sq025_suicidal_talk_cut",
      "sq025_suicidal_talk_end",
      "sq025_suicidal_talk_start",
      "sq025_traffic_jam",
      "sq025_trafficjam_poi_removed",
      "travelling_merchant_lives"
    ];
  }
  public static func FactNames37() -> array<String> {
    return [
      "air_traffic_off",
      "delamain_briefing_talk",
      "delamain_default_on",
      "delamain_main_screen_loaded",
      "delamain_main_screen_talk",
      "delamain_main_screen_talk_active",
      "delamain_receptionist_talk",
      "delamain_receptionist_talk_active",
      "ep1_standalone",
      "holo_active_call_interrupted",
      "holo_delamain_angry_calls_v_active",
      "holo_delamain_angry_calls_v_end_activate",
      "holo_delamain_angry_calls_v_end_done",
      "holo_delamain_calls_v_active",
      "holo_delamain_calls_v_end_activate",
      "holo_delamain_calls_v_end_done",
      "holo_delamain_calls_v_start_activate",
      "holo_delamain_deep_calls_v_active",
      "holo_delamain_deep_calls_v_end_activate",
      "holo_delamain_deep_calls_v_end_done",
      "holo_delamain_deep_vehicle_talk",
      "holo_delamain_manic_calls_v_active",
      "holo_delamain_manic_calls_v_end_activate",
      "holo_delamain_manic_calls_v_end_done",
      "holo_delamain_mean_calls_v_active",
      "holo_delamain_mean_calls_v_end_activate",
      "holo_delamain_mean_calls_v_end_done",
      "holo_delamain_sad_calls_v_active",
      "holo_delamain_sad_calls_v_end_activate",
      "holo_delamain_sad_calls_v_end_done",
      "holo_delamain_scared_calls_v_active",
      "holo_delamain_scared_calls_v_end_activate",
      "holo_delamain_scared_calls_v_end_done",
      "holo_delamain_suicidal_calls_v_active",
      "holo_delamain_suicidal_calls_v_end_activate",
      "holo_delamain_suicidal_calls_v_end_done",
      "holo_setup_active",
      "holo_setup_started",
      "mean_cleanup_started",
      "mq027_busy",
      "phonecall_delamain_with_player",
      "q000_done",
      "q101_done",
      "q101_enable_side_content",
      "q103_done",
      "q105_done",
      "q112_done",
      "q115_point_of_no_return",
      "q307_point_of_no_return",
      "saq025_fate_sealed",
      "sq012_fact_river_driving_from_diner",
      "sq012_fact_suspend_sq025",
      "sq024_city_race_countdown_end",
      "sq024_city_race_finished",
      "sq024_santo_domingo_race_finished",
      "sq024_santo_domingo_race_started",
      "sq025_active",
      "sq025_angry_done",
      "sq025_angry_talk_end",
      "sq025_angry_talk_start",
      "sq025_briefing_scene_done",
      "sq025_buy_car",
      "sq025_cardrop_button_pressed",
      "sq025_clean",
      "sq025_debug",
      "sq025_deep_active",
      "sq025_deep_av_running",
      "sq025_deep_done",
      "sq025_deep_vehicle_screen",
      "sq025_delamain_damaged",
      "sq025_delamain_damaged_counter",
      "sq025_delamain_dd_reception",
      "sq025_delamain_default",
      "sq025_delamain_destroyed",
      "sq025_delamain_done",
      "sq025_disabled",
      "sq025_done",
      "sq025_failed",
      "sq025_failed_momentarily",
      "sq025_fate_sealed",
      "sq025_garage_gate_unlocked",
      "sq025_initialize_fail",
      "sq025_manic_done",
      "sq025_manic_talk_disconnect",
      "sq025_manic_talk_end",
      "sq025_manic_talk_start",
      "sq025_mean_committed",
      "sq025_mean_done",
      "sq025_mean_talk_02_end",
      "sq025_mean_talk_02_start",
      "sq025_mean_talk_03_end",
      "sq025_mean_talk_03_start",
      "sq025_mean_talk_end",
      "sq025_mean_talk_start",
      "sq025_office_exit_unlock",
      "sq025_power_button_pressed",
      "sq025_power_out",
      "sq025_reception_scene",
      "sq025_reception_scene_real_delamain",
      "sq025_reception_scene_real_delamain_transition",
      "sq025_resurgence_start",
      "sq025_roundabout",
      "sq025_sad_done",
      "sq025_sad_mounted",
      "sq025_sad_talk_end",
      "sq025_sad_talk_open",
      "sq025_sad_talk_start",
      "sq025_scan_angry_intro_done",
      "sq025_scan_deep_intro_done",
      "sq025_scan_manic_intro_done",
      "sq025_scan_mean_intro_done",
      "sq025_scan_sad_intro_done",
      "sq025_scan_savelock",
      "sq025_scan_scared_intro_done",
      "sq025_scan_should_be_active",
      "sq025_scan_suicidal_intro_done",
      "sq025_scans_done",
      "sq025_scared_committed",
      "sq025_scared_crashed",
      "sq025_scared_done",
      "sq025_scared_talk_end",
      "sq025_scared_talk_start",
      "sq025_skip_reception",
      "sq025_smalltalk",
      "sq025_suicidal_done",
      "sq025_suicidal_talk_cut",
      "sq025_suicidal_talk_end",
      "sq025_suicidal_talk_start",
      "sq025_traffic_jam",
      "sq025_trafficjam_poi_removed",
      "travelling_merchant_lives"
    ];
  }
  public static func FactNames38() -> array<String> {
    return [
      "air_traffic_off",
      "delamain_briefing_talk",
      "delamain_default_on",
      "delamain_main_screen_loaded",
      "delamain_main_screen_talk",
      "delamain_main_screen_talk_active",
      "delamain_receptionist_talk",
      "delamain_receptionist_talk_active",
      "ep1_standalone",
      "holo_active_call_interrupted",
      "holo_delamain_angry_calls_v_active",
      "holo_delamain_angry_calls_v_end_activate",
      "holo_delamain_angry_calls_v_end_done",
      "holo_delamain_calls_v_active",
      "holo_delamain_calls_v_end_activate",
      "holo_delamain_calls_v_end_done",
      "holo_delamain_calls_v_start_activate",
      "holo_delamain_deep_calls_v_active",
      "holo_delamain_deep_calls_v_end_activate",
      "holo_delamain_deep_calls_v_end_done",
      "holo_delamain_deep_vehicle_talk",
      "holo_delamain_manic_calls_v_active",
      "holo_delamain_manic_calls_v_end_activate",
      "holo_delamain_manic_calls_v_end_done",
      "holo_delamain_mean_calls_v_active",
      "holo_delamain_mean_calls_v_end_activate",
      "holo_delamain_mean_calls_v_end_done",
      "holo_delamain_sad_calls_v_active",
      "holo_delamain_sad_calls_v_end_activate",
      "holo_delamain_sad_calls_v_end_done",
      "holo_delamain_scared_calls_v_active",
      "holo_delamain_scared_calls_v_end_activate",
      "holo_delamain_scared_calls_v_end_done",
      "holo_delamain_suicidal_calls_v_active",
      "holo_delamain_suicidal_calls_v_end_activate",
      "holo_delamain_suicidal_calls_v_end_done",
      "holo_setup_active",
      "holo_setup_started",
      "mean_cleanup_started",
      "mq027_busy",
      "phonecall_delamain_with_player",
      "q000_done",
      "q101_done",
      "q101_enable_side_content",
      "q103_done",
      "q105_done",
      "q112_done",
      "q115_point_of_no_return",
      "q307_point_of_no_return",
      "saq025_fate_sealed",
      "sq012_fact_river_driving_from_diner",
      "sq012_fact_suspend_sq025",
      "sq024_city_race_countdown_end",
      "sq024_city_race_finished",
      "sq024_santo_domingo_race_finished",
      "sq024_santo_domingo_race_started",
      "sq025_active",
      "sq025_angry_done",
      "sq025_angry_talk_end",
      "sq025_angry_talk_start",
      "sq025_briefing_scene_done",
      "sq025_buy_car",
      "sq025_cardrop_button_pressed",
      "sq025_clean",
      "sq025_debug",
      "sq025_deep_active",
      "sq025_deep_av_running",
      "sq025_deep_done",
      "sq025_deep_vehicle_screen",
      "sq025_delamain_damaged",
      "sq025_delamain_damaged_counter",
      "sq025_delamain_dd_reception",
      "sq025_delamain_default",
      "sq025_delamain_destroyed",
      "sq025_delamain_done",
      "sq025_disabled",
      "sq025_done",
      "sq025_failed",
      "sq025_failed_momentarily",
      "sq025_fate_sealed",
      "sq025_garage_gate_unlocked",
      "sq025_initialize_fail",
      "sq025_manic_done",
      "sq025_manic_talk_disconnect",
      "sq025_manic_talk_end",
      "sq025_manic_talk_start",
      "sq025_mean_committed",
      "sq025_mean_done",
      "sq025_mean_talk_02_end",
      "sq025_mean_talk_02_start",
      "sq025_mean_talk_03_end",
      "sq025_mean_talk_03_start",
      "sq025_mean_talk_end",
      "sq025_mean_talk_start",
      "sq025_office_exit_unlock",
      "sq025_power_button_pressed",
      "sq025_power_out",
      "sq025_reception_scene",
      "sq025_reception_scene_real_delamain",
      "sq025_reception_scene_real_delamain_transition",
      "sq025_resurgence_start",
      "sq025_roundabout",
      "sq025_sad_done",
      "sq025_sad_mounted",
      "sq025_sad_talk_end",
      "sq025_sad_talk_open",
      "sq025_sad_talk_start",
      "sq025_scan_angry_intro_done",
      "sq025_scan_deep_intro_done",
      "sq025_scan_manic_intro_done",
      "sq025_scan_mean_intro_done",
      "sq025_scan_sad_intro_done",
      "sq025_scan_savelock",
      "sq025_scan_scared_intro_done",
      "sq025_scan_should_be_active",
      "sq025_scan_suicidal_intro_done",
      "sq025_scans_done",
      "sq025_scared_committed",
      "sq025_scared_crashed",
      "sq025_scared_done",
      "sq025_scared_talk_end",
      "sq025_scared_talk_start",
      "sq025_skip_reception",
      "sq025_smalltalk",
      "sq025_suicidal_done",
      "sq025_suicidal_talk_cut",
      "sq025_suicidal_talk_end",
      "sq025_suicidal_talk_start",
      "sq025_traffic_jam",
      "sq025_trafficjam_poi_removed",
      "travelling_merchant_lives"
    ];
  }
  public static func FactNames39() -> array<String> {
    return [
      "air_traffic_off",
      "delamain_briefing_talk",
      "delamain_default_on",
      "delamain_main_screen_loaded",
      "delamain_main_screen_talk",
      "delamain_main_screen_talk_active",
      "delamain_receptionist_talk",
      "delamain_receptionist_talk_active",
      "ep1_standalone",
      "holo_active_call_interrupted",
      "holo_delamain_angry_calls_v_active",
      "holo_delamain_angry_calls_v_end_activate",
      "holo_delamain_angry_calls_v_end_done",
      "holo_delamain_calls_v_active",
      "holo_delamain_calls_v_end_activate",
      "holo_delamain_calls_v_end_done",
      "holo_delamain_calls_v_start_activate",
      "holo_delamain_deep_calls_v_active",
      "holo_delamain_deep_calls_v_end_activate",
      "holo_delamain_deep_calls_v_end_done",
      "holo_delamain_deep_vehicle_talk",
      "holo_delamain_manic_calls_v_active",
      "holo_delamain_manic_calls_v_end_activate",
      "holo_delamain_manic_calls_v_end_done",
      "holo_delamain_mean_calls_v_active",
      "holo_delamain_mean_calls_v_end_activate",
      "holo_delamain_mean_calls_v_end_done",
      "holo_delamain_sad_calls_v_active",
      "holo_delamain_sad_calls_v_end_activate",
      "holo_delamain_sad_calls_v_end_done",
      "holo_delamain_scared_calls_v_active",
      "holo_delamain_scared_calls_v_end_activate",
      "holo_delamain_scared_calls_v_end_done",
      "holo_delamain_suicidal_calls_v_active",
      "holo_delamain_suicidal_calls_v_end_activate",
      "holo_delamain_suicidal_calls_v_end_done",
      "holo_setup_active",
      "holo_setup_started",
      "mean_cleanup_started",
      "mq027_busy",
      "phonecall_delamain_with_player",
      "q000_done",
      "q101_done",
      "q101_enable_side_content",
      "q103_done",
      "q105_done",
      "q112_done",
      "q115_point_of_no_return",
      "q307_point_of_no_return",
      "saq025_fate_sealed",
      "sq012_fact_river_driving_from_diner",
      "sq012_fact_suspend_sq025",
      "sq024_city_race_countdown_end",
      "sq024_city_race_finished",
      "sq024_santo_domingo_race_finished",
      "sq024_santo_domingo_race_started",
      "sq025_active",
      "sq025_angry_done",
      "sq025_angry_talk_end",
      "sq025_angry_talk_start",
      "sq025_briefing_scene_done",
      "sq025_buy_car",
      "sq025_cardrop_button_pressed",
      "sq025_clean",
      "sq025_debug",
      "sq025_deep_active",
      "sq025_deep_av_running",
      "sq025_deep_done",
      "sq025_deep_vehicle_screen",
      "sq025_delamain_damaged",
      "sq025_delamain_damaged_counter",
      "sq025_delamain_dd_reception",
      "sq025_delamain_default",
      "sq025_delamain_destroyed",
      "sq025_delamain_done",
      "sq025_disabled",
      "sq025_done",
      "sq025_failed",
      "sq025_failed_momentarily",
      "sq025_fate_sealed",
      "sq025_garage_gate_unlocked",
      "sq025_initialize_fail",
      "sq025_manic_done",
      "sq025_manic_talk_disconnect",
      "sq025_manic_talk_end",
      "sq025_manic_talk_start",
      "sq025_mean_committed",
      "sq025_mean_done",
      "sq025_mean_talk_02_end",
      "sq025_mean_talk_02_start",
      "sq025_mean_talk_03_end",
      "sq025_mean_talk_03_start",
      "sq025_mean_talk_end",
      "sq025_mean_talk_start",
      "sq025_office_exit_unlock",
      "sq025_power_button_pressed",
      "sq025_power_out",
      "sq025_reception_scene",
      "sq025_reception_scene_real_delamain",
      "sq025_reception_scene_real_delamain_transition",
      "sq025_resurgence_start",
      "sq025_roundabout",
      "sq025_sad_done",
      "sq025_sad_mounted",
      "sq025_sad_talk_end",
      "sq025_sad_talk_open",
      "sq025_sad_talk_start",
      "sq025_scan_angry_intro_done",
      "sq025_scan_deep_intro_done",
      "sq025_scan_manic_intro_done",
      "sq025_scan_mean_intro_done",
      "sq025_scan_sad_intro_done",
      "sq025_scan_savelock",
      "sq025_scan_scared_intro_done",
      "sq025_scan_should_be_active",
      "sq025_scan_suicidal_intro_done",
      "sq025_scans_done",
      "sq025_scared_committed",
      "sq025_scared_crashed",
      "sq025_scared_done",
      "sq025_scared_talk_end",
      "sq025_scared_talk_start",
      "sq025_skip_reception",
      "sq025_smalltalk",
      "sq025_suicidal_done",
      "sq025_suicidal_talk_cut",
      "sq025_suicidal_talk_end",
      "sq025_suicidal_talk_start",
      "sq025_traffic_jam",
      "sq025_trafficjam_poi_removed",
      "travelling_merchant_lives"
    ];
  }
  public static func FactNames40() -> array<String> {
    let empty: array<String>; return empty;
  }
  public static func FactNames41() -> array<String> {
    return [
      "RacePlayerDistanceFromSpline",
      "claire_default_on",
      "disable_combat_events",
      "disable_tutorials",
      "holo_claire_calls_v_end_activate",
      "holo_claire_calls_v_start_activate",
      "holo_v_calls_claire_end_activate",
      "holo_v_calls_claire_start_activate",
      "impossibru_fact",
      "q103_active_claire_scene",
      "q105_done",
      "radio_on",
      "sa_ep1_courier_outro_part_dam",
      "sq024_active",
      "sq024_all_races_start",
      "sq024_badlands_cleanup_done",
      "sq024_badlands_countdown_end",
      "sq024_badlands_race_accepted_ride_back",
      "sq024_badlands_race_bet_wrong",
      "sq024_badlands_race_end_left_claire_alone",
      "sq024_badlands_race_finished",
      "sq024_badlands_race_left_together",
      "sq024_badlands_race_opponent_finish",
      "sq024_badlands_race_started",
      "sq024_badlands_race_won",
      "sq024_badlands_sandstorm_entered",
      "sq024_badlands_tpp_camera",
      "sq024_bd_rcr_at_end_1",
      "sq024_bd_rcr_at_end_2",
      "sq024_bd_rcr_at_end_3",
      "sq024_bd_rcr_at_end_4",
      "sq024_bd_rcr_at_end_5",
      "sq024_bd_rcr_finish_1",
      "sq024_bd_rcr_finish_2",
      "sq024_bd_rcr_finish_3",
      "sq024_bd_rcr_finish_4",
      "sq024_bd_rcr_finish_5",
      "sq024_bd_wraiths_in_car",
      "sq024_big_race_bet_wrong",
      "sq024_big_race_cleanup",
      "sq024_big_race_continue_sampson_2",
      "sq024_big_race_countdown_end",
      "sq024_big_race_inside_car",
      "sq024_big_race_opponent_finish",
      "sq024_big_race_prevention_fail",
      "sq024_big_race_started",
      "sq024_big_race_won",
      "sq024_big_rcr_at_end_1",
      "sq024_big_rcr_at_end_2",
      "sq024_big_rcr_at_end_3",
      "sq024_big_rcr_at_end_4",
      "sq024_big_rcr_at_end_sampson",
      "sq024_big_rcr_finish_1",
      "sq024_big_rcr_finish_2",
      "sq024_big_rcr_finish_3",
      "sq024_big_rcr_finish_4",
      "sq024_big_rcr_finish_sampson",
      "sq024_big_use_v_car",
      "sq024_cc_at_garage",
      "sq024_chicken_afterlife",
      "sq024_chicken_bd_start",
      "sq024_chicken_big_start",
      "sq024_chicken_city_start",
      "sq024_chicken_sd_start",
      "sq024_city_race_accepted_ride_back",
      "sq024_city_race_bet_wrong",
      "sq024_city_race_cleanup_done",
      "sq024_city_race_countdown_end",
      "sq024_city_race_crowd_spawned",
      "sq024_city_race_end_left_claire_alone",
      "sq024_city_race_enemy_finish",
      "sq024_city_race_finished",
      "sq024_city_race_inside_car",
      "sq024_city_race_left_together",
      "sq024_city_race_won",
      "sq024_city_rcr_at_end_1",
      "sq024_city_rcr_at_end_2",
      "sq024_city_rcr_at_end_3",
      "sq024_city_rcr_at_end_4",
      "sq024_city_rcr_at_end_5",
      "sq024_city_rcr_finish_1",
      "sq024_city_rcr_finish_2",
      "sq024_city_rcr_finish_3",
      "sq024_city_rcr_finish_4",
      "sq024_city_rcr_finish_5",
      "sq024_city_use_v_car",
      "sq024_claire_at_damn_failed",
      "sq024_claire_big_at_car",
      "sq024_claire_meeting_garage_active",
      "sq024_claire_pissed",
      "sq024_claire_stop_combat",
      "sq024_continue_but_wont_kill_sampson",
      "sq024_current_place_count",
      "sq024_current_race_checkpoint_fact_add",
      "sq024_current_race_chekpoint_fact_add",
      "sq024_done",
      "sq024_drive_with_claire_end",
      "sq024_emergency_kill_quest",
      "sq024_end_at_santo_domingo",
      "sq024_fail_in_race_nr",
      "sq024_failed_at_badlands",
      "sq024_garage_talk_started",
      "sq024_generic_race_bet_wrong",
      "sq024_hook_done",
      "sq024_impossibru_fact",
      "sq024_leave_together_santo_domingo_race",
      "sq024_player_race_place_counter",
      "sq024_prevention_fail",
      "sq024_quest_declined",
      "sq024_race_win_conversation_done",
      "sq024_races_left",
      "sq024_rocket_land",
      "sq024_sampson_crash_fx_stop",
      "sq024_sampson_crashed",
      "sq024_sampson_dead",
      "sq024_sampson_escaped",
      "sq024_sampson_scene_left_area",
      "sq024_sampson_vehicle_damaged_in_race",
      "sq024_sampson_was_in_damage_trigger",
      "sq024_sampson_was_not_damaged",
      "sq024_santo_domingo_countdown_end",
      "sq024_santo_domingo_race_accepted_ride",
      "sq024_santo_domingo_race_actually_rode_back",
      "sq024_santo_domingo_race_bet_wrong",
      "sq024_santo_domingo_race_cleanup_muamar_done",
      "sq024_santo_domingo_race_finished",
      "sq024_santo_domingo_race_started",
      "sq024_santo_domingo_race_won",
      "sq024_sd_finish_chicken",
      "sq024_sd_race_opponent_finish",
      "sq024_sd_rcr_at_end_1",
      "sq024_sd_rcr_at_end_2",
      "sq024_sd_rcr_at_end_3",
      "sq024_sd_rcr_at_end_4",
      "sq024_sd_rcr_at_end_5",
      "sq024_sd_rcr_finish_1",
      "sq024_sd_rcr_finish_2",
      "sq024_sd_rcr_finish_3",
      "sq024_sd_rcr_finish_4",
      "sq024_sd_rcr_finish_5",
      "sq024_sd_v_car",
      "sq024_skipped_time",
      "sq024_swapped_claire_car_with_real_one",
      "sq024_test_definition",
      "sq024_tt_claire_gun_equiped",
      "sq024_v_finished_bd_race",
      "sq024_v_finished_big_race",
      "sq024_v_finished_cc_race",
      "sq024_v_finished_sd_race",
      "sq024_v_said_not_interested_at_start",
      "sq031_active",
      "sq031_claire_scene_end",
      "travelling_merchant_lives",
      "wanted_level"
    ];
  }
  public static func FactNames42() -> array<String> {
    return [
      "RacePlayerDistanceFromSpline",
      "claire_default_on",
      "disable_combat_events",
      "disable_tutorials",
      "holo_claire_calls_v_end_activate",
      "holo_claire_calls_v_start_activate",
      "holo_v_calls_claire_end_activate",
      "holo_v_calls_claire_start_activate",
      "impossibru_fact",
      "q103_active_claire_scene",
      "q105_done",
      "radio_on",
      "sa_ep1_courier_outro_part_dam",
      "sq024_active",
      "sq024_all_races_start",
      "sq024_badlands_cleanup_done",
      "sq024_badlands_countdown_end",
      "sq024_badlands_race_accepted_ride_back",
      "sq024_badlands_race_bet_wrong",
      "sq024_badlands_race_end_left_claire_alone",
      "sq024_badlands_race_finished",
      "sq024_badlands_race_left_together",
      "sq024_badlands_race_opponent_finish",
      "sq024_badlands_race_started",
      "sq024_badlands_race_won",
      "sq024_badlands_sandstorm_entered",
      "sq024_badlands_tpp_camera",
      "sq024_bd_rcr_at_end_1",
      "sq024_bd_rcr_at_end_2",
      "sq024_bd_rcr_at_end_3",
      "sq024_bd_rcr_at_end_4",
      "sq024_bd_rcr_at_end_5",
      "sq024_bd_rcr_finish_1",
      "sq024_bd_rcr_finish_2",
      "sq024_bd_rcr_finish_3",
      "sq024_bd_rcr_finish_4",
      "sq024_bd_rcr_finish_5",
      "sq024_bd_wraiths_in_car",
      "sq024_big_race_bet_wrong",
      "sq024_big_race_cleanup",
      "sq024_big_race_continue_sampson_2",
      "sq024_big_race_countdown_end",
      "sq024_big_race_inside_car",
      "sq024_big_race_opponent_finish",
      "sq024_big_race_prevention_fail",
      "sq024_big_race_started",
      "sq024_big_race_won",
      "sq024_big_rcr_at_end_1",
      "sq024_big_rcr_at_end_2",
      "sq024_big_rcr_at_end_3",
      "sq024_big_rcr_at_end_4",
      "sq024_big_rcr_at_end_sampson",
      "sq024_big_rcr_finish_1",
      "sq024_big_rcr_finish_2",
      "sq024_big_rcr_finish_3",
      "sq024_big_rcr_finish_4",
      "sq024_big_rcr_finish_sampson",
      "sq024_big_use_v_car",
      "sq024_cc_at_garage",
      "sq024_chicken_afterlife",
      "sq024_chicken_bd_start",
      "sq024_chicken_big_start",
      "sq024_chicken_city_start",
      "sq024_chicken_sd_start",
      "sq024_city_race_accepted_ride_back",
      "sq024_city_race_bet_wrong",
      "sq024_city_race_cleanup_done",
      "sq024_city_race_countdown_end",
      "sq024_city_race_crowd_spawned",
      "sq024_city_race_end_left_claire_alone",
      "sq024_city_race_enemy_finish",
      "sq024_city_race_finished",
      "sq024_city_race_inside_car",
      "sq024_city_race_left_together",
      "sq024_city_race_won",
      "sq024_city_rcr_at_end_1",
      "sq024_city_rcr_at_end_2",
      "sq024_city_rcr_at_end_3",
      "sq024_city_rcr_at_end_4",
      "sq024_city_rcr_at_end_5",
      "sq024_city_rcr_finish_1",
      "sq024_city_rcr_finish_2",
      "sq024_city_rcr_finish_3",
      "sq024_city_rcr_finish_4",
      "sq024_city_rcr_finish_5",
      "sq024_city_use_v_car",
      "sq024_claire_at_damn_failed",
      "sq024_claire_big_at_car",
      "sq024_claire_meeting_garage_active",
      "sq024_claire_pissed",
      "sq024_claire_stop_combat",
      "sq024_continue_but_wont_kill_sampson",
      "sq024_current_place_count",
      "sq024_current_race_checkpoint_fact_add",
      "sq024_current_race_chekpoint_fact_add",
      "sq024_done",
      "sq024_drive_with_claire_end",
      "sq024_emergency_kill_quest",
      "sq024_end_at_santo_domingo",
      "sq024_fail_in_race_nr",
      "sq024_failed_at_badlands",
      "sq024_garage_talk_started",
      "sq024_generic_race_bet_wrong",
      "sq024_hook_done",
      "sq024_impossibru_fact",
      "sq024_leave_together_santo_domingo_race",
      "sq024_player_race_place_counter",
      "sq024_prevention_fail",
      "sq024_quest_declined",
      "sq024_race_win_conversation_done",
      "sq024_races_left",
      "sq024_rocket_land",
      "sq024_sampson_crash_fx_stop",
      "sq024_sampson_crashed",
      "sq024_sampson_dead",
      "sq024_sampson_escaped",
      "sq024_sampson_scene_left_area",
      "sq024_sampson_vehicle_damaged_in_race",
      "sq024_sampson_was_in_damage_trigger",
      "sq024_sampson_was_not_damaged",
      "sq024_santo_domingo_countdown_end",
      "sq024_santo_domingo_race_accepted_ride",
      "sq024_santo_domingo_race_actually_rode_back",
      "sq024_santo_domingo_race_bet_wrong",
      "sq024_santo_domingo_race_cleanup_muamar_done",
      "sq024_santo_domingo_race_finished",
      "sq024_santo_domingo_race_started",
      "sq024_santo_domingo_race_won",
      "sq024_sd_finish_chicken",
      "sq024_sd_race_opponent_finish",
      "sq024_sd_rcr_at_end_1",
      "sq024_sd_rcr_at_end_2",
      "sq024_sd_rcr_at_end_3",
      "sq024_sd_rcr_at_end_4",
      "sq024_sd_rcr_at_end_5",
      "sq024_sd_rcr_finish_1",
      "sq024_sd_rcr_finish_2",
      "sq024_sd_rcr_finish_3",
      "sq024_sd_rcr_finish_4",
      "sq024_sd_rcr_finish_5",
      "sq024_sd_v_car",
      "sq024_skipped_time",
      "sq024_swapped_claire_car_with_real_one",
      "sq024_test_definition",
      "sq024_tt_claire_gun_equiped",
      "sq024_v_finished_bd_race",
      "sq024_v_finished_big_race",
      "sq024_v_finished_cc_race",
      "sq024_v_finished_sd_race",
      "sq024_v_said_not_interested_at_start",
      "sq031_active",
      "sq031_claire_scene_end",
      "travelling_merchant_lives",
      "wanted_level"
    ];
  }
  public static func FactNames43() -> array<String> {
    return [
      "RacePlayerDistanceFromSpline",
      "claire_default_on",
      "disable_combat_events",
      "disable_tutorials",
      "holo_claire_calls_v_end_activate",
      "holo_claire_calls_v_start_activate",
      "holo_v_calls_claire_end_activate",
      "holo_v_calls_claire_start_activate",
      "impossibru_fact",
      "q103_active_claire_scene",
      "q105_done",
      "radio_on",
      "sa_ep1_courier_outro_part_dam",
      "sq024_active",
      "sq024_all_races_start",
      "sq024_badlands_cleanup_done",
      "sq024_badlands_countdown_end",
      "sq024_badlands_race_accepted_ride_back",
      "sq024_badlands_race_bet_wrong",
      "sq024_badlands_race_end_left_claire_alone",
      "sq024_badlands_race_finished",
      "sq024_badlands_race_left_together",
      "sq024_badlands_race_opponent_finish",
      "sq024_badlands_race_started",
      "sq024_badlands_race_won",
      "sq024_badlands_sandstorm_entered",
      "sq024_badlands_tpp_camera",
      "sq024_bd_rcr_at_end_1",
      "sq024_bd_rcr_at_end_2",
      "sq024_bd_rcr_at_end_3",
      "sq024_bd_rcr_at_end_4",
      "sq024_bd_rcr_at_end_5",
      "sq024_bd_rcr_finish_1",
      "sq024_bd_rcr_finish_2",
      "sq024_bd_rcr_finish_3",
      "sq024_bd_rcr_finish_4",
      "sq024_bd_rcr_finish_5",
      "sq024_bd_wraiths_in_car",
      "sq024_big_race_bet_wrong",
      "sq024_big_race_cleanup",
      "sq024_big_race_continue_sampson_2",
      "sq024_big_race_countdown_end",
      "sq024_big_race_inside_car",
      "sq024_big_race_opponent_finish",
      "sq024_big_race_prevention_fail",
      "sq024_big_race_started",
      "sq024_big_race_won",
      "sq024_big_rcr_at_end_1",
      "sq024_big_rcr_at_end_2",
      "sq024_big_rcr_at_end_3",
      "sq024_big_rcr_at_end_4",
      "sq024_big_rcr_at_end_sampson",
      "sq024_big_rcr_finish_1",
      "sq024_big_rcr_finish_2",
      "sq024_big_rcr_finish_3",
      "sq024_big_rcr_finish_4",
      "sq024_big_rcr_finish_sampson",
      "sq024_big_use_v_car",
      "sq024_cc_at_garage",
      "sq024_chicken_afterlife",
      "sq024_chicken_bd_start",
      "sq024_chicken_big_start",
      "sq024_chicken_city_start",
      "sq024_chicken_sd_start",
      "sq024_city_race_accepted_ride_back",
      "sq024_city_race_bet_wrong",
      "sq024_city_race_cleanup_done",
      "sq024_city_race_countdown_end",
      "sq024_city_race_crowd_spawned",
      "sq024_city_race_end_left_claire_alone",
      "sq024_city_race_enemy_finish",
      "sq024_city_race_finished",
      "sq024_city_race_inside_car",
      "sq024_city_race_left_together",
      "sq024_city_race_won",
      "sq024_city_rcr_at_end_1",
      "sq024_city_rcr_at_end_2",
      "sq024_city_rcr_at_end_3",
      "sq024_city_rcr_at_end_4",
      "sq024_city_rcr_at_end_5",
      "sq024_city_rcr_finish_1",
      "sq024_city_rcr_finish_2",
      "sq024_city_rcr_finish_3",
      "sq024_city_rcr_finish_4",
      "sq024_city_rcr_finish_5",
      "sq024_city_use_v_car",
      "sq024_claire_at_damn_failed",
      "sq024_claire_big_at_car",
      "sq024_claire_meeting_garage_active",
      "sq024_claire_pissed",
      "sq024_claire_stop_combat",
      "sq024_continue_but_wont_kill_sampson",
      "sq024_current_place_count",
      "sq024_current_race_checkpoint_fact_add",
      "sq024_current_race_chekpoint_fact_add",
      "sq024_done",
      "sq024_drive_with_claire_end",
      "sq024_emergency_kill_quest",
      "sq024_end_at_santo_domingo",
      "sq024_fail_in_race_nr",
      "sq024_failed_at_badlands",
      "sq024_garage_talk_started",
      "sq024_generic_race_bet_wrong",
      "sq024_hook_done",
      "sq024_impossibru_fact",
      "sq024_leave_together_santo_domingo_race",
      "sq024_player_race_place_counter",
      "sq024_prevention_fail",
      "sq024_quest_declined",
      "sq024_race_win_conversation_done",
      "sq024_races_left",
      "sq024_rocket_land",
      "sq024_sampson_crash_fx_stop",
      "sq024_sampson_crashed",
      "sq024_sampson_dead",
      "sq024_sampson_escaped",
      "sq024_sampson_scene_left_area",
      "sq024_sampson_vehicle_damaged_in_race",
      "sq024_sampson_was_in_damage_trigger",
      "sq024_sampson_was_not_damaged",
      "sq024_santo_domingo_countdown_end",
      "sq024_santo_domingo_race_accepted_ride",
      "sq024_santo_domingo_race_actually_rode_back",
      "sq024_santo_domingo_race_bet_wrong",
      "sq024_santo_domingo_race_cleanup_muamar_done",
      "sq024_santo_domingo_race_finished",
      "sq024_santo_domingo_race_started",
      "sq024_santo_domingo_race_won",
      "sq024_sd_finish_chicken",
      "sq024_sd_race_opponent_finish",
      "sq024_sd_rcr_at_end_1",
      "sq024_sd_rcr_at_end_2",
      "sq024_sd_rcr_at_end_3",
      "sq024_sd_rcr_at_end_4",
      "sq024_sd_rcr_at_end_5",
      "sq024_sd_rcr_finish_1",
      "sq024_sd_rcr_finish_2",
      "sq024_sd_rcr_finish_3",
      "sq024_sd_rcr_finish_4",
      "sq024_sd_rcr_finish_5",
      "sq024_sd_v_car",
      "sq024_skipped_time",
      "sq024_swapped_claire_car_with_real_one",
      "sq024_test_definition",
      "sq024_tt_claire_gun_equiped",
      "sq024_v_finished_bd_race",
      "sq024_v_finished_big_race",
      "sq024_v_finished_cc_race",
      "sq024_v_finished_sd_race",
      "sq024_v_said_not_interested_at_start",
      "sq031_active",
      "sq031_claire_scene_end",
      "travelling_merchant_lives",
      "wanted_level"
    ];
  }
  public static func FactNames44() -> array<String> {
    return [
      "RacePlayerDistanceFromSpline",
      "claire_default_on",
      "disable_combat_events",
      "disable_tutorials",
      "holo_claire_calls_v_end_activate",
      "holo_claire_calls_v_start_activate",
      "holo_v_calls_claire_end_activate",
      "holo_v_calls_claire_start_activate",
      "impossibru_fact",
      "q103_active_claire_scene",
      "q105_done",
      "radio_on",
      "sa_ep1_courier_outro_part_dam",
      "sq024_active",
      "sq024_all_races_start",
      "sq024_badlands_cleanup_done",
      "sq024_badlands_countdown_end",
      "sq024_badlands_race_accepted_ride_back",
      "sq024_badlands_race_bet_wrong",
      "sq024_badlands_race_end_left_claire_alone",
      "sq024_badlands_race_finished",
      "sq024_badlands_race_left_together",
      "sq024_badlands_race_opponent_finish",
      "sq024_badlands_race_started",
      "sq024_badlands_race_won",
      "sq024_badlands_sandstorm_entered",
      "sq024_badlands_tpp_camera",
      "sq024_bd_rcr_at_end_1",
      "sq024_bd_rcr_at_end_2",
      "sq024_bd_rcr_at_end_3",
      "sq024_bd_rcr_at_end_4",
      "sq024_bd_rcr_at_end_5",
      "sq024_bd_rcr_finish_1",
      "sq024_bd_rcr_finish_2",
      "sq024_bd_rcr_finish_3",
      "sq024_bd_rcr_finish_4",
      "sq024_bd_rcr_finish_5",
      "sq024_bd_wraiths_in_car",
      "sq024_big_race_bet_wrong",
      "sq024_big_race_cleanup",
      "sq024_big_race_continue_sampson_2",
      "sq024_big_race_countdown_end",
      "sq024_big_race_inside_car",
      "sq024_big_race_opponent_finish",
      "sq024_big_race_prevention_fail",
      "sq024_big_race_started",
      "sq024_big_race_won",
      "sq024_big_rcr_at_end_1",
      "sq024_big_rcr_at_end_2",
      "sq024_big_rcr_at_end_3",
      "sq024_big_rcr_at_end_4",
      "sq024_big_rcr_at_end_sampson",
      "sq024_big_rcr_finish_1",
      "sq024_big_rcr_finish_2",
      "sq024_big_rcr_finish_3",
      "sq024_big_rcr_finish_4",
      "sq024_big_rcr_finish_sampson",
      "sq024_big_use_v_car",
      "sq024_cc_at_garage",
      "sq024_chicken_afterlife",
      "sq024_chicken_bd_start",
      "sq024_chicken_big_start",
      "sq024_chicken_city_start",
      "sq024_chicken_sd_start",
      "sq024_city_race_accepted_ride_back",
      "sq024_city_race_bet_wrong",
      "sq024_city_race_cleanup_done",
      "sq024_city_race_countdown_end",
      "sq024_city_race_crowd_spawned",
      "sq024_city_race_end_left_claire_alone",
      "sq024_city_race_enemy_finish",
      "sq024_city_race_finished",
      "sq024_city_race_inside_car",
      "sq024_city_race_left_together",
      "sq024_city_race_won",
      "sq024_city_rcr_at_end_1",
      "sq024_city_rcr_at_end_2",
      "sq024_city_rcr_at_end_3",
      "sq024_city_rcr_at_end_4",
      "sq024_city_rcr_at_end_5",
      "sq024_city_rcr_finish_1",
      "sq024_city_rcr_finish_2",
      "sq024_city_rcr_finish_3",
      "sq024_city_rcr_finish_4",
      "sq024_city_rcr_finish_5",
      "sq024_city_use_v_car",
      "sq024_claire_at_damn_failed",
      "sq024_claire_big_at_car",
      "sq024_claire_meeting_garage_active",
      "sq024_claire_pissed",
      "sq024_claire_stop_combat",
      "sq024_continue_but_wont_kill_sampson",
      "sq024_current_place_count",
      "sq024_current_race_checkpoint_fact_add",
      "sq024_current_race_chekpoint_fact_add",
      "sq024_done",
      "sq024_drive_with_claire_end",
      "sq024_emergency_kill_quest",
      "sq024_end_at_santo_domingo",
      "sq024_fail_in_race_nr",
      "sq024_failed_at_badlands",
      "sq024_garage_talk_started",
      "sq024_generic_race_bet_wrong",
      "sq024_hook_done",
      "sq024_impossibru_fact",
      "sq024_leave_together_santo_domingo_race",
      "sq024_player_race_place_counter",
      "sq024_prevention_fail",
      "sq024_quest_declined",
      "sq024_race_win_conversation_done",
      "sq024_races_left",
      "sq024_rocket_land",
      "sq024_sampson_crash_fx_stop",
      "sq024_sampson_crashed",
      "sq024_sampson_dead",
      "sq024_sampson_escaped",
      "sq024_sampson_scene_left_area",
      "sq024_sampson_vehicle_damaged_in_race",
      "sq024_sampson_was_in_damage_trigger",
      "sq024_sampson_was_not_damaged",
      "sq024_santo_domingo_countdown_end",
      "sq024_santo_domingo_race_accepted_ride",
      "sq024_santo_domingo_race_actually_rode_back",
      "sq024_santo_domingo_race_bet_wrong",
      "sq024_santo_domingo_race_cleanup_muamar_done",
      "sq024_santo_domingo_race_finished",
      "sq024_santo_domingo_race_started",
      "sq024_santo_domingo_race_won",
      "sq024_sd_finish_chicken",
      "sq024_sd_race_opponent_finish",
      "sq024_sd_rcr_at_end_1",
      "sq024_sd_rcr_at_end_2",
      "sq024_sd_rcr_at_end_3",
      "sq024_sd_rcr_at_end_4",
      "sq024_sd_rcr_at_end_5",
      "sq024_sd_rcr_finish_1",
      "sq024_sd_rcr_finish_2",
      "sq024_sd_rcr_finish_3",
      "sq024_sd_rcr_finish_4",
      "sq024_sd_rcr_finish_5",
      "sq024_sd_v_car",
      "sq024_skipped_time",
      "sq024_swapped_claire_car_with_real_one",
      "sq024_test_definition",
      "sq024_tt_claire_gun_equiped",
      "sq024_v_finished_bd_race",
      "sq024_v_finished_big_race",
      "sq024_v_finished_cc_race",
      "sq024_v_finished_sd_race",
      "sq024_v_said_not_interested_at_start",
      "sq031_active",
      "sq031_claire_scene_end",
      "travelling_merchant_lives",
      "wanted_level"
    ];
  }
  public static func FactNames45() -> array<String> {
    return [
      "air_traffic_off",
      "delamain_briefing_talk",
      "delamain_default_on",
      "delamain_main_screen_loaded",
      "delamain_main_screen_talk",
      "delamain_main_screen_talk_active",
      "delamain_receptionist_talk",
      "delamain_receptionist_talk_active",
      "ep1_standalone",
      "holo_active_call_interrupted",
      "holo_delamain_angry_calls_v_active",
      "holo_delamain_angry_calls_v_end_activate",
      "holo_delamain_angry_calls_v_end_done",
      "holo_delamain_calls_v_active",
      "holo_delamain_calls_v_end_activate",
      "holo_delamain_calls_v_end_done",
      "holo_delamain_calls_v_start_activate",
      "holo_delamain_deep_calls_v_active",
      "holo_delamain_deep_calls_v_end_activate",
      "holo_delamain_deep_calls_v_end_done",
      "holo_delamain_deep_vehicle_talk",
      "holo_delamain_manic_calls_v_active",
      "holo_delamain_manic_calls_v_end_activate",
      "holo_delamain_manic_calls_v_end_done",
      "holo_delamain_mean_calls_v_active",
      "holo_delamain_mean_calls_v_end_activate",
      "holo_delamain_mean_calls_v_end_done",
      "holo_delamain_sad_calls_v_active",
      "holo_delamain_sad_calls_v_end_activate",
      "holo_delamain_sad_calls_v_end_done",
      "holo_delamain_scared_calls_v_active",
      "holo_delamain_scared_calls_v_end_activate",
      "holo_delamain_scared_calls_v_end_done",
      "holo_delamain_suicidal_calls_v_active",
      "holo_delamain_suicidal_calls_v_end_activate",
      "holo_delamain_suicidal_calls_v_end_done",
      "holo_setup_active",
      "holo_setup_started",
      "mean_cleanup_started",
      "mq027_busy",
      "phonecall_delamain_with_player",
      "q000_done",
      "q101_done",
      "q101_enable_side_content",
      "q103_done",
      "q105_done",
      "q112_done",
      "q115_point_of_no_return",
      "q307_point_of_no_return",
      "saq025_fate_sealed",
      "sq012_fact_river_driving_from_diner",
      "sq012_fact_suspend_sq025",
      "sq024_city_race_countdown_end",
      "sq024_city_race_finished",
      "sq024_santo_domingo_race_finished",
      "sq024_santo_domingo_race_started",
      "sq025_active",
      "sq025_angry_done",
      "sq025_angry_talk_end",
      "sq025_angry_talk_start",
      "sq025_briefing_scene_done",
      "sq025_buy_car",
      "sq025_cardrop_button_pressed",
      "sq025_clean",
      "sq025_debug",
      "sq025_deep_active",
      "sq025_deep_av_running",
      "sq025_deep_done",
      "sq025_deep_vehicle_screen",
      "sq025_delamain_damaged",
      "sq025_delamain_damaged_counter",
      "sq025_delamain_dd_reception",
      "sq025_delamain_default",
      "sq025_delamain_destroyed",
      "sq025_delamain_done",
      "sq025_disabled",
      "sq025_done",
      "sq025_failed",
      "sq025_failed_momentarily",
      "sq025_fate_sealed",
      "sq025_garage_gate_unlocked",
      "sq025_initialize_fail",
      "sq025_manic_done",
      "sq025_manic_talk_disconnect",
      "sq025_manic_talk_end",
      "sq025_manic_talk_start",
      "sq025_mean_committed",
      "sq025_mean_done",
      "sq025_mean_talk_02_end",
      "sq025_mean_talk_02_start",
      "sq025_mean_talk_03_end",
      "sq025_mean_talk_03_start",
      "sq025_mean_talk_end",
      "sq025_mean_talk_start",
      "sq025_office_exit_unlock",
      "sq025_power_button_pressed",
      "sq025_power_out",
      "sq025_reception_scene",
      "sq025_reception_scene_real_delamain",
      "sq025_reception_scene_real_delamain_transition",
      "sq025_resurgence_start",
      "sq025_roundabout",
      "sq025_sad_done",
      "sq025_sad_mounted",
      "sq025_sad_talk_end",
      "sq025_sad_talk_open",
      "sq025_sad_talk_start",
      "sq025_scan_angry_intro_done",
      "sq025_scan_deep_intro_done",
      "sq025_scan_manic_intro_done",
      "sq025_scan_mean_intro_done",
      "sq025_scan_sad_intro_done",
      "sq025_scan_savelock",
      "sq025_scan_scared_intro_done",
      "sq025_scan_should_be_active",
      "sq025_scan_suicidal_intro_done",
      "sq025_scans_done",
      "sq025_scared_committed",
      "sq025_scared_crashed",
      "sq025_scared_done",
      "sq025_scared_talk_end",
      "sq025_scared_talk_start",
      "sq025_skip_reception",
      "sq025_smalltalk",
      "sq025_suicidal_done",
      "sq025_suicidal_talk_cut",
      "sq025_suicidal_talk_end",
      "sq025_suicidal_talk_start",
      "sq025_traffic_jam",
      "sq025_trafficjam_poi_removed",
      "travelling_merchant_lives"
    ];
  }
  public static func FactNames46() -> array<String> {
    return [
      "air_traffic_off",
      "delamain_briefing_talk",
      "delamain_default_on",
      "delamain_main_screen_loaded",
      "delamain_main_screen_talk",
      "delamain_main_screen_talk_active",
      "delamain_receptionist_talk",
      "delamain_receptionist_talk_active",
      "ep1_standalone",
      "holo_active_call_interrupted",
      "holo_delamain_angry_calls_v_active",
      "holo_delamain_angry_calls_v_end_activate",
      "holo_delamain_angry_calls_v_end_done",
      "holo_delamain_calls_v_active",
      "holo_delamain_calls_v_end_activate",
      "holo_delamain_calls_v_end_done",
      "holo_delamain_calls_v_start_activate",
      "holo_delamain_deep_calls_v_active",
      "holo_delamain_deep_calls_v_end_activate",
      "holo_delamain_deep_calls_v_end_done",
      "holo_delamain_deep_vehicle_talk",
      "holo_delamain_manic_calls_v_active",
      "holo_delamain_manic_calls_v_end_activate",
      "holo_delamain_manic_calls_v_end_done",
      "holo_delamain_mean_calls_v_active",
      "holo_delamain_mean_calls_v_end_activate",
      "holo_delamain_mean_calls_v_end_done",
      "holo_delamain_sad_calls_v_active",
      "holo_delamain_sad_calls_v_end_activate",
      "holo_delamain_sad_calls_v_end_done",
      "holo_delamain_scared_calls_v_active",
      "holo_delamain_scared_calls_v_end_activate",
      "holo_delamain_scared_calls_v_end_done",
      "holo_delamain_suicidal_calls_v_active",
      "holo_delamain_suicidal_calls_v_end_activate",
      "holo_delamain_suicidal_calls_v_end_done",
      "holo_setup_active",
      "holo_setup_started",
      "mean_cleanup_started",
      "mq027_busy",
      "phonecall_delamain_with_player",
      "q000_done",
      "q101_done",
      "q101_enable_side_content",
      "q103_done",
      "q105_done",
      "q112_done",
      "q115_point_of_no_return",
      "q307_point_of_no_return",
      "saq025_fate_sealed",
      "sq012_fact_river_driving_from_diner",
      "sq012_fact_suspend_sq025",
      "sq024_city_race_countdown_end",
      "sq024_city_race_finished",
      "sq024_santo_domingo_race_finished",
      "sq024_santo_domingo_race_started",
      "sq025_active",
      "sq025_angry_done",
      "sq025_angry_talk_end",
      "sq025_angry_talk_start",
      "sq025_briefing_scene_done",
      "sq025_buy_car",
      "sq025_cardrop_button_pressed",
      "sq025_clean",
      "sq025_debug",
      "sq025_deep_active",
      "sq025_deep_av_running",
      "sq025_deep_done",
      "sq025_deep_vehicle_screen",
      "sq025_delamain_damaged",
      "sq025_delamain_damaged_counter",
      "sq025_delamain_dd_reception",
      "sq025_delamain_default",
      "sq025_delamain_destroyed",
      "sq025_delamain_done",
      "sq025_disabled",
      "sq025_done",
      "sq025_failed",
      "sq025_failed_momentarily",
      "sq025_fate_sealed",
      "sq025_garage_gate_unlocked",
      "sq025_initialize_fail",
      "sq025_manic_done",
      "sq025_manic_talk_disconnect",
      "sq025_manic_talk_end",
      "sq025_manic_talk_start",
      "sq025_mean_committed",
      "sq025_mean_done",
      "sq025_mean_talk_02_end",
      "sq025_mean_talk_02_start",
      "sq025_mean_talk_03_end",
      "sq025_mean_talk_03_start",
      "sq025_mean_talk_end",
      "sq025_mean_talk_start",
      "sq025_office_exit_unlock",
      "sq025_power_button_pressed",
      "sq025_power_out",
      "sq025_reception_scene",
      "sq025_reception_scene_real_delamain",
      "sq025_reception_scene_real_delamain_transition",
      "sq025_resurgence_start",
      "sq025_roundabout",
      "sq025_sad_done",
      "sq025_sad_mounted",
      "sq025_sad_talk_end",
      "sq025_sad_talk_open",
      "sq025_sad_talk_start",
      "sq025_scan_angry_intro_done",
      "sq025_scan_deep_intro_done",
      "sq025_scan_manic_intro_done",
      "sq025_scan_mean_intro_done",
      "sq025_scan_sad_intro_done",
      "sq025_scan_savelock",
      "sq025_scan_scared_intro_done",
      "sq025_scan_should_be_active",
      "sq025_scan_suicidal_intro_done",
      "sq025_scans_done",
      "sq025_scared_committed",
      "sq025_scared_crashed",
      "sq025_scared_done",
      "sq025_scared_talk_end",
      "sq025_scared_talk_start",
      "sq025_skip_reception",
      "sq025_smalltalk",
      "sq025_suicidal_done",
      "sq025_suicidal_talk_cut",
      "sq025_suicidal_talk_end",
      "sq025_suicidal_talk_start",
      "sq025_traffic_jam",
      "sq025_trafficjam_poi_removed",
      "travelling_merchant_lives"
    ];
  }
  public static func FactNames47() -> array<String> {
    return [
      "air_traffic_off",
      "coyote_community_activated",
      "elcoyote_barman_default_on",
      "gustavo_on_spot",
      "holo_v_calls_mama_welles_end_activate",
      "holo_v_calls_mama_welles_start_activate",
      "holo_v_calls_mama_welles_start_done",
      "mama_welles_default_on",
      "misty_default_on",
      "mq033_misty_dialogue_on",
      "mq033_misty_tarot_talk_needed",
      "padre_default_on",
      "phonecall_player_with_mama_welles",
      "q000_done",
      "q003_jackie_motorcycle_upgraded",
      "q005_jackie_stay_notell",
      "q005_jackie_to_mama",
      "q115_point_of_no_return",
      "rey_01_finished",
      "sq018_01_funeral_preparations",
      "sq018_03_ball_ofrenda",
      "sq018_03_belt_ofrenda",
      "sq018_03_book_ofrenda",
      "sq018_03_done",
      "sq018_03_funeral_active",
      "sq018_03_padre_onspot",
      "sq018_03_pepe_onspot",
      "sq018_03_tequila_ofrenda",
      "sq018_03_victor_onspot",
      "sq018_03_victor_started",
      "sq018_03a_misty_invited",
      "sq018_04b_gus_drink",
      "sq018_04b_val_drink",
      "sq018_active",
      "sq018_dbg_start_apartment",
      "sq018_dbg_start_el_coyote_cojo",
      "sq018_done",
      "travelling_merchant_lives",
      "valentino_on_spot",
      "victor_vector_default_on"
    ];
  }
  public static func FactNames48() -> array<String> {
    return [
      "gle_06_succeed",
      "mq044_done",
      "mq044_started",
      "mq_044_started_in_main",
      "travelling_merchant_lives"
    ];
  }
  public static func FactNames49() -> array<String> {
    return [
      "carol_default_on",
      "cassidy_default_on",
      "mq002_active",
      "mq002_deal_broken_combat",
      "mq002_deal_proceeded",
      "mq002_done",
      "mq002_escaped",
      "mq002_escaped_combat",
      "mq002_sniper_noticed",
      "nomad_camp_01_active_combat",
      "q115_point_of_no_return",
      "sq004_done",
      "sq027_active",
      "sq027_camp_abandoned",
      "sq027_camp_moved",
      "sq027_done",
      "teddy_default_on",
      "travelling_merchant_lives"
    ];
  }
  public static func FactNames50() -> array<String> {
    return [
      "bob_default_on",
      "mq021_active",
      "mq021_bob_ending_approached",
      "mq021_done",
      "mq021_happy_ending",
      "q000_done",
      "q115_point_of_no_return",
      "sq027_active",
      "sq027_camp_abandoned",
      "sq027_camp_moved",
      "sq027_done",
      "travelling_merchant_lives"
    ];
  }
  public static func FactNames51() -> array<String> {
    return [
      "air_traffic_off",
      "ep1_standalone",
      "holo_frank_calls_v_end_activate",
      "holo_frank_calls_v_start_activate",
      "mq041_corpo_started",
      "mq041_debug",
      "mq041_done",
      "q110_done",
      "travelling_merchant_lives",
      "wanted_level"
    ];
  }
  public static func FactNames52() -> array<String> {
    let empty: array<String>; return empty;
  }
  public static func FactNames53() -> array<String> {
    return [
      "air_traffic_off",
      "q304_06_netrunners_car_parked_front",
      "q304_car_retrieval_accepted",
      "q304_car_retrieval_active",
      "q304_car_retrieval_car_entered",
      "q304_car_retrieval_car_ready2go",
      "q304_car_retrieval_combat_started",
      "q304_car_retrieval_done",
      "q304_car_retrieval_driver2_spawned",
      "q304_car_retrieval_finished",
      "q304_car_retrieval_got_spotted",
      "q304_car_retrieval_guards_killed",
      "q304_car_retrieval_inner_patrol_car_moving",
      "q304_car_retrieval_player_spotted",
      "q304_car_retrieval_player_spotted_2",
      "q304_car_retrieval_started",
      "q304_car_retrieval_truck_finished_ride",
      "q304_car_retrieval_truck_reached_inner",
      "q304_car_retrieval_van_reached_inner",
      "q304_car_retrival_on_top_of_truck",
      "q304_first_track_at_the_end_of_spline",
      "q304_retrofix_56524_on"
    ];
  }
  public static func FactNames54() -> array<String> {
    return [
      "holo_v_calls_lizzy_end_activate",
      "holo_v_calls_lizzy_start_activate",
      "mq019_03_active",
      "mq019_03_barman_talked",
      "mq019_03_bouncer_talked",
      "mq019_03_liam_vip_lounge",
      "mq019_04_champagne",
      "mq019_05_didnt_tell_lizzy",
      "mq019_dbg_riot",
      "mq019_dbg_start",
      "mq019_done",
      "mq019_liam_disposed",
      "mq019_liam_disposed_failed",
      "q000_done",
      "riot_closed",
      "sq017_active",
      "sq017_done",
      "travelling_merchant_lives",
      "wat_lch_foodshop_03_default_on"
    ];
  }
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
