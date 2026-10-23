module PTFR.ActivityStateR3

import PTFR.RestrictionsR1.*
import PTFR.RestrictionsR2.*
import PTFR.RestrictionsR3.*
import PTFR.RestorationBaseline.*

public struct PreAlphaGigSnapshot {
  public persistent let states: array<Int32>;
  public persistent let facts: array<Int32>;
  public persistent let terminal: array<Int32>;
  // 1 unstarted, 2 started, 3 terminal, 4 unreadable/unsupported.
  public persistent let disposition: Int32;
}

// PA2 uses the native covered handoff before any restored-world activation.
// Production capture and the explicitly approved late-ending test are separate.
public class PreAlphaEntry extends ScriptableSystem {
  private persistent let schema: Int32;
  private persistent let catalogue: CName;
  private persistent let baseline: array<PreAlphaGigSnapshot>;
  private persistent let eligible: array<Bool>;
  private persistent let ready: Bool;
  private persistent let frozen: Bool;
  private persistent let certified: Bool;
  private persistent let endingObserved: Bool;
  private persistent let lateEndingTestArmed: Bool;
  private persistent let faulted: Bool;
  private persistent let fault: CName;
  private persistent let captures: Int32;
  private let running: Bool;
  private let epoch: Int32;
  private let registered: Bool;
  private let listeners: array<Uint32>;
  private let lastCapture: Float;
  private let lastAttempt: Float;
  private let activationTicks: Int32;
  private let results: array<String>;
  private let detail: String;

  // This package is for the user-selected ManualSave10 Things Done Changed run.
  // Disable this constant for production. It never creates a history certificate.
  public static func DevelopmentLateEnding() -> Bool { return true; }
  public static func Catalogue() -> CName { return n"9B4DE2CCE8871939008B8CD43CCA42734D17F4847768E134CA9E0C9CE688342D"; }
  public static func Get(game: GameInstance) -> ref<PreAlphaEntry> {
    return GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.ActivityStateR3.PreAlphaEntry") as PreAlphaEntry;
  }
  private func Fact(name: CName) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(name); }
  private func Now() -> Float { return EngineTime.ToFloat(GameInstance.GetSimTime(this.GetGameInstance())); }
  private func State(path: String, cls: String) -> Int32 {
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    let entry = jm.GetEntryByString(path, cls);
    return IsDefined(entry) ? EnumInt(jm.GetEntryState(entry)) : -1;
  }
  private func Completed() -> Bool { return CyberwarePolicy.Completed(this.GetGameInstance()); }
  private func BoundaryNow() -> Bool {
    return this.Fact(n"q115_point_of_no_return") > 0 || this.Fact(n"q307_point_of_no_return") > 0 ||
      this.Fact(n"q307_2079") > 0 || this.Fact(n"q307_main_game_killed") > 0 || this.Fact(n"q307_ep1_killed") > 0 ||
      this.Fact(n"q307_done") > 0 || this.Fact(n"q307_finished") > 0 || this.Fact(n"PostTowerFreeRoamActive") > 0;
  }
  private func TeardownNow() -> Bool {
    return this.Fact(n"q307_2079") > 0 || this.Fact(n"q307_main_game_killed") > 0 || this.Fact(n"q307_ep1_killed") > 0 ||
      this.Fact(n"q307_done") > 0 || this.Fact(n"q307_finished") > 0 || this.Fact(n"PostTowerFreeRoamActive") > 0;
  }
  private func LateEndingFixture() -> Bool {
    return PreAlphaEntry.DevelopmentLateEnding() && this.Fact(n"q307_active") == 1 && this.Fact(n"q307_2079") == 1 &&
      this.Fact(n"q307_main_game_killed") == 1 && this.Fact(n"q307_ep1_killed") == 1 &&
      this.Fact(n"q307_done") == 0 && this.Fact(n"q307_finished") == 0 &&
      this.Fact(n"PostTowerFreeRoamActive") == 0 && this.Fact(n"PTFRP0_DR13") == 0 &&
      this.State("ep1/quests/main_quest/q307_tomorrow", "gameJournalQuest") == 2;
  }
  private func OnAttach() -> Void { this.running = true; this.Restored(); }
  private func OnDetach() -> Void { this.Unregister(); this.running = false; this.epoch += 1; }
  public func Restored() -> Void {
    this.Unregister(); this.epoch += 1; this.lastCapture = -100.0; this.lastAttempt = -100.0; this.activationTicks = 0;
    ArrayClear(this.results);
    let i = 0; while i < NativeGigDataU9.Count() { ArrayPush(this.results, "Not attempted in this loaded session."); i += 1; }
    if this.schema != 0 && (this.schema != 1 || NotEquals(this.catalogue, PreAlphaEntry.Catalogue())) {
      this.Fail("Saved PA1 history schema/catalogue mismatch.");
    }
    if this.ready && !this.ShapeValid() { this.Fail("Saved PA1 history is incomplete."); }
    if this.certified && (!this.ready || !this.frozen || ArraySize(this.eligible) != NativeGigDataU9.Count()) {
      this.Fail("Invalid PA1 certificate; history preserved.");
    }
    this.ArmLateTest();
    if !this.faulted && this.BoundaryNow() && !this.frozen {
      this.frozen = true; this.certified = false;
      this.detail = "Loaded after cutoff: pre-Tower history unknown.";
    }
    if !this.faulted && !this.BoundaryNow() && this.frozen {
      this.frozen = false; this.certified = false; this.ready = false; this.endingObserved = false; this.lateEndingTestArmed = false;
      ArrayClear(this.eligible);
    }
    this.Register();
    if this.running { this.Schedule(); }
  }
  private func ArmLateTest() -> Void {
    if this.faulted || this.lateEndingTestArmed || !this.LateEndingFixture() { return; }
    this.lateEndingTestArmed = true; this.schema = 1; this.catalogue = PreAlphaEntry.Catalogue();
    this.detail = "Things Done Changed test armed. Finish the ending normally; incomplete gigs will use the DEVELOPMENT assumption after credits.";
    ModLog(n"PTFR_PreAlpha", this.detail);
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
  private func ReadGig(i: Int32) -> PreAlphaGigSnapshot {
    let snap: PreAlphaGigSnapshot;
    let paths = NativeGigDataU9.Paths(i); let classes = NativeGigDataU9.Classes(i);
    let facts = NativeGigDataU9.Facts(i); let terminal = NativeGigDataU9.TerminalFacts(i);
    let k = 0;
    if ArraySize(paths) == 0 || ArraySize(paths) != ArraySize(classes) { snap.disposition = 4; return snap; }
    while k < ArraySize(paths) { ArrayPush(snap.states, this.State(paths[k], classes[k])); k += 1; }
    k = 0; while k < ArraySize(facts) { ArrayPush(snap.facts, this.Fact(StringToName(facts[k]))); k += 1; }
    k = 0; while k < ArraySize(terminal) { ArrayPush(snap.terminal, this.Fact(StringToName(terminal[k]))); k += 1; }
    snap.disposition = this.Classify(snap); return snap;
  }
  private func Classify(snap: PreAlphaGigSnapshot) -> Int32 {
    if ArraySize(snap.states) == 0 { return 4; }
    if snap.states[0] == 3 || snap.states[0] == 4 { return 3; }
    let k = 0; while k < ArraySize(snap.terminal) { if snap.terminal[k] != 0 { return 3; }; k += 1; }
    k = 0; while k < ArraySize(snap.states) { if snap.states[k] < 1 || snap.states[k] > 4 { return 4; }; k += 1; }
    k = 0; while k < ArraySize(snap.states) { if snap.states[k] != 1 { return 2; }; k += 1; }
    // The U9 data lists local progression evidence, omitting native tier and
    // ordinary ready/prestate gates. Nonzero ancillary facts remain unsupported.
    k = 0; while k < ArraySize(snap.facts) { if snap.facts[k] != 0 { return 4; }; k += 1; }
    return 1;
  }
  private func Same(a: PreAlphaGigSnapshot, b: PreAlphaGigSnapshot) -> Bool {
    if a.disposition != b.disposition || ArraySize(a.states) != ArraySize(b.states) ||
      ArraySize(a.facts) != ArraySize(b.facts) || ArraySize(a.terminal) != ArraySize(b.terminal) { return false; }
    let i = 0; while i < ArraySize(a.states) { if a.states[i] != b.states[i] { return false; }; i += 1; }
    i = 0; while i < ArraySize(a.facts) { if a.facts[i] != b.facts[i] { return false; }; i += 1; }
    i = 0; while i < ArraySize(a.terminal) { if a.terminal[i] != b.terminal[i] { return false; }; i += 1; }
    return true;
  }
  private func ShapeValid() -> Bool {
    if NativeGigDataU9.Count() != 72 || ArraySize(this.baseline) != NativeGigDataU9.Count() { return false; }
    let i = 0; while i < NativeGigDataU9.Count() {
      let paths = NativeGigDataU9.Paths(i); let facts = NativeGigDataU9.Facts(i); let terminal = NativeGigDataU9.TerminalFacts(i);
      if ArraySize(this.baseline[i].states) != ArraySize(paths) ||
        ArraySize(this.baseline[i].facts) != ArraySize(facts) ||
        ArraySize(this.baseline[i].terminal) != ArraySize(terminal) { return false; }
      i += 1;
    }
    return true;
  }
  public func CaptureBeforeEnding() -> String {
    if this.faulted || this.frozen || this.BoundaryNow() { return "Capture unavailable after cutoff; no history replaced. " + this.Status(); }
    let game = this.GetGameInstance();
    let player = GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
    let jm = GameInstance.GetJournalManager(game);
    if !IsDefined(player) || player.IsReplacer() || player.IsDead() || jm.HasAnyDelayedStateChanges() { return "Waiting for live V and settled journal."; }
    let sample: array<PreAlphaGigSnapshot>; let i = 0;
    while i < NativeGigDataU9.Count() { ArrayPush(sample, this.ReadGig(i)); i += 1; }
    i = 0; while i < NativeGigDataU9.Count() {
      if !this.Same(sample[i], this.ReadGig(i)) { return "Capture changed while reading; last observation retained."; }
      i += 1;
    }
    if this.BoundaryNow() || jm.HasAnyDelayedStateChanges() || this.captures >= 2147483647 { return "Capture not committed; cutoff/journal change or generation limit."; }
    this.baseline = sample; this.schema = 1; this.catalogue = PreAlphaEntry.Catalogue();
    this.ready = this.ShapeValid(); this.captures += 1; this.lastCapture = this.Now();
    this.detail = "Current 72-gig whitelist observed in the actual pre-ending world. Snapshot freezes at native cutoff.";
    return this.Status();
  }
  private func Freeze(nativeBoundary: Bool) -> Void {
    if this.frozen || this.faulted { return; }
    this.endingObserved = true;
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    let age = this.Now() - this.lastCapture;
    this.certified = nativeBoundary && !this.TeardownNow() && this.ready && this.ShapeValid() &&
      age >= 0.0 && age <= 6.0 && !jm.HasAnyDelayedStateChanges();
    ArrayClear(this.eligible);
    let i = 0;
    while i < NativeGigDataU9.Count() {
      // A changed gig loses eligibility individually; later cleared facts cannot
      // turn it into fresh history. Never overwrite the pre-ending snapshot.
      let fresh = this.certified && this.baseline[i].disposition == 1 && this.Same(this.baseline[i], this.ReadGig(i));
      ArrayPush(this.eligible, fresh); i += 1;
    }
    this.frozen = true;
    this.detail = this.certified ? "Actual pre-ending snapshot frozen; only unchanged unstarted gigs certified." : "Cutoff observed without a timely certified snapshot; gig history remains unknown.";
    ModLog(n"PTFR_PreAlpha", this.detail);
  }
  public func Certified(id: String) -> Bool {
    let i = NativeGigDataU9.Index(id);
    return !this.faulted && this.schema == 1 && Equals(this.catalogue, PreAlphaEntry.Catalogue()) &&
      this.ready && this.frozen && this.certified && i >= 0 && ArraySize(this.eligible) == NativeGigDataU9.Count() && this.eligible[i];
  }
  public func DevelopmentArmed() -> Bool { return !this.faulted && PreAlphaEntry.DevelopmentLateEnding() && this.lateEndingTestArmed && !this.certified; }
  private func Activated() -> Bool { return !this.faulted && this.Completed() && (this.endingObserved || this.certified || this.DevelopmentArmed()); }
  public func PostEndingAuthorized() -> Bool { return this.Activated(); }
  private func Schedule() -> Void { GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(PreAlphaTick.Create(this, this.epoch), 1.0, false); }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    this.Schedule(); if this.faulted { return; }
    this.ArmLateTest();
    if !this.frozen && this.BoundaryNow() { this.Freeze(false); }
    if !this.frozen && this.Now() - this.lastCapture >= 5.0 { this.CaptureBeforeEnding(); }
    if this.Fact(n"PTFRPA2_Fault") > 0 { this.detail = "Transition failed; inspect Arrival(). No automatic retry."; return; }
    if !this.Activated() { this.activationTicks = 0; return; }
    let game = this.GetGameInstance();
    let player = GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(player) || !BodyPolicy.Safe(player) { this.activationTicks = 0; return; }
    this.activationTicks += 1; if this.activationTicks < 3 { return; }
    let arrival = GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.ActivityStateR3.PreAlphaArrivalPA1") as PreAlphaArrivalPA1;
    if !IsDefined(arrival) { this.detail = "H10 arrival module missing."; return; }
    if !arrival.Completed() { arrival.Begin(); this.detail = arrival.Status(); return; }
    let profile = ProfilePolicy.Get(game);
    if !IsDefined(profile) { this.detail = "Profile module missing."; return; }
    if profile.PTFRPAFaulted() { this.detail = "Profile transaction fault: " + profile.GetStatus(); return; }
    if !profile.PTFRPAConfigured() {
      this.detail = profile.FullNerf();
      // Refunds stay in the existing durable one-shot policy, including reload.
      return;
    }
    if !profile.PTFRPAComplete() { this.detail = "Waiting for accepted profile to finish: " + profile.GetStatus(); return; }
    if this.Now() - this.lastAttempt < 5.0 { return; }
    this.lastAttempt = this.Now(); if !this.Dispatch() { return; }
    // PA5: wait for real geometry owner acknowledgements, not just included files.
    // Interaction prompts remain location-driven; this does not grant ownership.
    let restoration = GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.RestorationBaseline.RestorationBaseline") as RestorationBaseline;
    if !IsDefined(restoration) { this.detail = "H10 restoration module missing."; return; }
    if !restoration.H10GeometryReady() { this.detail = restoration.H10Status(); return; }
    // One admission pass is preparation, not proof every stock tier is unlocked.
    // Native graph will reveal gameplay only after this and a fresh control check.
    if this.Fact(n"PTFRPA2_ControlReady") == 1 && this.Fact(n"PTFRPA2_Fault") == 0 {
      GameInstance.GetQuestsSystem(game).SetFact(n"PTFRPA2_Prepared", 1);
    }
  }
  private func Dispatch() -> Bool {
    let gigs = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.ActivityStateR3.NativeGigsU9") as NativeGigsU9;
    if !IsDefined(gigs) { this.detail = "Native gig module missing."; return false; }
    let i = 0; while i < NativeGigDataU9.Count() {
      let id = NativeGigDataU9.ID(i);
      let result: String;
      if this.Certified(id) { result = gigs.RestoreCertified(id); }
      else { if this.DevelopmentArmed() { result = gigs.Start(id, "DISPOSABLE_SAVE"); }
      else { result = "Excluded: no certified unstarted pre-Tower history."; } }
      if NotEquals(this.results[i], result) { this.results[i] = result; ModLog(n"PTFR_PreAlpha", id + " | " + result); }
      i += 1;
    }
    this.detail = this.DevelopmentArmed() ? "Late-ending DEVELOPMENT dispatch: incomplete assumed unstarted; stock runtime/terminal guards remain." : "Certified pre-Tower dispatch: only observed unstarted whitelist entries.";
    return true;
  }
  private func Fail(message: String) -> Void { this.faulted = true; this.fault = StringToName(message); ModLog(n"PTFR_PreAlpha", message); }
  public func Status() -> String {
    let count = 0; let i = 0; while i < ArraySize(this.eligible) { if this.eligible[i] { count += 1; }; i += 1; }
    let profile = ProfilePolicy.Get(this.GetGameInstance());
    return "Pre-alpha PA2: ready/frozen/certified=" + ToString(this.ready) + "/" + ToString(this.frozen) + "/" + ToString(this.certified) +
      " certifiedUnstarted=" + ToString(count) + "/72 captures=" + ToString(this.captures) +
      " lateEndingTest=" + ToString(this.DevelopmentArmed()) + " completedTower=" + ToString(this.Completed()) +
      " activated=" + ToString(this.Activated()) + " profileComplete=" + ToString(IsDefined(profile) && profile.PTFRPAComplete()) +
      " fault=" + ToString(this.fault) + " | " + this.detail;
  }
  public func Inspect(id: String) -> String {
    let i = NativeGigDataU9.Index(id); if i < 0 { return "Not on the current 72-gig whitelist."; }
    let history = this.ready && i < ArraySize(this.baseline) ? this.baseline[i].disposition : 4;
    return id + " history=1fresh/2started/3terminal/4unknown:" + ToString(history) + " certified=" + ToString(this.Certified(id)) +
      " lateDevelopmentAssumption=" + ToString(this.DevelopmentArmed()) + " | " + (i < ArraySize(this.results) ? this.results[i] : "Awaiting attached coordinator.");
  }
  public func InspectAll() -> String {
    let out = this.Status(); let i = 0; while i < NativeGigDataU9.Count() { out += "\n" + this.Inspect(NativeGigDataU9.ID(i)); i += 1; }; return out;
  }
}

public class PreAlphaTick extends DelayCallback {
  private let owner: wref<PreAlphaEntry>; private let epoch: Int32;
  public static func Create(owner: ref<PreAlphaEntry>, epoch: Int32) -> ref<PreAlphaTick> {
    let tick = new PreAlphaTick(); tick.owner = owner; tick.epoch = epoch; return tick;
  }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}

@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void {
  wrappedMethod(gameInstance);
  let entry = PreAlphaEntry.Get(gameInstance); if IsDefined(entry) { entry.Restored(); }
}
