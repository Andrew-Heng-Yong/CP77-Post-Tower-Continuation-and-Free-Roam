module PTFR.ActivityStateR3

import PTFR.MinefieldG3.*

import PTFR.GigPilotR1.*
import PTFR.SideJobPilotS1.*
import PTFR.RiteG2.*

// Own save-local history only. No generic native fact/journal/actor reset.
public struct ActivitySnapshot {
  public persistent let states: array<Int32>;
  public persistent let optional: array<Int32>;
  public persistent let tracked: array<Bool>;
  public persistent let counters: array<Int32>;
  public persistent let facts: array<Int32>;
}

public class ActivityState extends ScriptableSystem {
  private persistent let schema: Int32;
  private persistent let fingerprint: CName;
  private persistent let baseline: ActivitySnapshot;
  private persistent let ready: Bool;
  private persistent let frozen: Bool;
  private persistent let certified: Bool;
  private persistent let boundary: CName;
  private persistent let captureCount: Int32;
  private persistent let autoAttempted: Bool;
  private persistent let sideFreshObserved: Bool; // Added S1; old saves default false, never fabricated.
  private persistent let faulted: Bool;
  private persistent let fault: CName;
  private let paths: array<String>;
  private let classes: array<String>;
  private let facts: array<String>;
  private let ids: array<String>;
  private let titles: array<String>;
  private let hashes: array<Uint32>;
  private let listeners: array<Uint32>;
  private let registered: Bool;
  private let epoch: Int32;
  private let running: Bool;
  private let dirty: Bool;
  private let lastCapture: Float;
  private let detail: String;

  private func Fact(name: CName) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(name); }
  private func Now() -> Float { return EngineTime.ToFloat(GameInstance.GetSimTime(this.GetGameInstance())); }
  private func BoundaryNow() -> Bool {
    return this.Fact(n"q115_point_of_no_return") > 0 || this.Fact(n"q307_point_of_no_return") > 0 ||
      this.Fact(n"q307_2079") > 0 || this.Fact(n"q307_main_game_killed") > 0 || this.Fact(n"q307_ep1_killed") > 0 ||
      this.Fact(n"q307_done") > 0 || this.Fact(n"q307_finished") > 0 || this.Fact(n"PostTowerFreeRoamActive") > 0;
  }
  private func Tower() -> Bool {
    return this.Fact(n"PostTowerFreeRoamActive") == 1 && this.Fact(n"PTFRP0_DR13") == 1 &&
      this.Fact(n"q307_done") == 1 && this.Fact(n"q307_finished") == 1 && this.Fact(n"q307_2079") == 1 &&
      this.Fact(n"q307_main_game_killed") == 1 && this.Fact(n"q307_ep1_killed") == 1 &&
      this.Fact(n"q307_active") == 0 && this.Fact(n"q115_point_of_no_return") == 0 && this.Fact(n"q305_johnny_scene_active") == 0;
  }
  private func LoadDefinition() -> Void {
    let page = 0;
    let i: Int32;
    let values: array<String>;
    ArrayClear(this.paths); ArrayClear(this.classes); ArrayClear(this.facts); ArrayClear(this.ids); ArrayClear(this.titles); ArrayClear(this.hashes);
    while ArraySize(this.paths) < ActivityDefinition.EntryCount() {
      values = ActivityDefinition.Paths(page); i = 0;
      while i < ArraySize(values) { ArrayPush(this.paths, values[i]); i += 1; }
      values = ActivityDefinition.Classes(page); i = 0;
      while i < ArraySize(values) { ArrayPush(this.classes, values[i]); i += 1; }
      page += 1;
    }
    page = 0;
    while ArraySize(this.facts) < ActivityDefinition.FactCount() {
      values = ActivityDefinition.FactNames(page); i = 0;
      while i < ArraySize(values) { ArrayPush(this.facts, values[i]); i += 1; }
      page += 1;
    }
    page = 0;
    while ArraySize(this.ids) < ActivityDefinition.JobCount() {
      values = ActivityDefinition.JobIDs(page); i = 0;
      while i < ArraySize(values) { ArrayPush(this.ids, values[i]); i += 1; }
      values = ActivityDefinition.JobTitles(page); i = 0;
      while i < ArraySize(values) { ArrayPush(this.titles, values[i]); i += 1; }
      page += 1;
    }
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    let entry: wref<JournalEntry>;
    i = 0;
    while i < ArraySize(this.paths) {
      entry = jm.GetEntryByString(this.paths[i], this.classes[i]);
      ArrayPush(this.hashes, IsDefined(entry) ? Cast<Uint32>(jm.GetEntryHash(entry)) : 0u);
      i += 1;
    }
  }
  private func OnAttach() -> Void { this.running = true; this.Restored(); }
  private func OnDetach() -> Void { this.Unregister(); this.running = false; this.epoch += 1; }
  public func Restored() -> Void {
    this.Unregister(); this.epoch += 1; this.LoadDefinition(); this.dirty = true; this.lastCapture = -100.00;
    if this.schema != 0 && (this.schema != 1 || NotEquals(this.fingerprint, ActivityDefinition.Fingerprint())) {
      this.faulted = true; this.fault = n"CatalogueMismatch_NoMigrationOrReplay";
    }
    if this.certified && (!this.ready || !this.frozen || this.schema != 1) {
      this.faulted = true; this.fault = n"InvalidCertificate_NoResetOrReplay";
    }
    if this.ready && (ArraySize(this.baseline.states) != ActivityDefinition.EntryCount() ||
      ArraySize(this.baseline.optional) != ActivityDefinition.EntryCount() || ArraySize(this.baseline.tracked) != ActivityDefinition.EntryCount() ||
      ArraySize(this.baseline.counters) != ActivityDefinition.EntryCount() || ArraySize(this.baseline.facts) != ActivityDefinition.FactCount() ||
      this.schema != 1 || this.captureCount <= 0) {
      this.faulted = true; this.fault = n"InvalidSnapshotShape_NoResetOrReplay";
    }
    if !this.faulted && this.BoundaryNow() && !this.frozen {
      // Loading a post-ending save cannot certify an old unfrozen pre-ending snapshot.
      this.frozen = true; this.certified = false; this.boundary = n"LoadedAfterBoundary_UnknownHistory";
    }
    if !this.faulted && !this.BoundaryNow() && this.frozen {
      // A pre-ending branch or vanilla One More Gig may be played normally again.
      this.frozen = false; this.certified = false; this.ready = false; this.autoAttempted = false;
      this.boundary = n"OrdinaryWorld_WaitingForFreshObservation";
    }
    this.Register();
    if this.running { this.Schedule(); }
  }
  private func Register() -> Void {
    if this.registered { return; }
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    ArrayPush(this.listeners, qs.RegisterListener(n"q115_point_of_no_return", this, n"OnEndingBoundary"));
    ArrayPush(this.listeners, qs.RegisterListener(n"q307_point_of_no_return", this, n"OnEndingBoundary"));
    GameInstance.GetJournalManager(this.GetGameInstance()).RegisterScriptCallback(this, n"OnJournalState", gameJournalListenerType.State);
    this.registered = true;
  }
  private func Unregister() -> Void {
    if !this.registered { return; }
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if ArraySize(this.listeners) == 2 {
      qs.UnregisterListener(n"q115_point_of_no_return", this.listeners[0]);
      qs.UnregisterListener(n"q307_point_of_no_return", this.listeners[1]);
    }
    GameInstance.GetJournalManager(this.GetGameInstance()).UnregisterScriptCallback(this, n"OnJournalState");
    ArrayClear(this.listeners); this.registered = false;
  }
  protected cb func OnEndingBoundary(value: Int32) -> Bool {
    if value > 0 { this.Freeze(n"NativePointOfNoReturnListener"); }
    return false;
  }
  protected cb func OnJournalState(entryHash: Uint32, className: CName, notifyOption: JournalNotifyOption, changeType: JournalChangeType) -> Bool {
    if this.frozen || this.faulted { return false; }
    if ArrayContains(this.hashes, entryHash) { this.dirty = true; }
    return false;
  }
  private func Freeze(reason: CName) -> Void {
    if this.frozen || this.faulted { return; }
    // Only downgrade adapter evidence at cutoff; never replace the baseline
    // with post-cleanup values or turn an old save's default false into true.
    if this.sideFreshObserved {
      let sidePilot = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.SideJobPilotS1.SideJobPilotS1") as SideJobPilotS1;
      if !IsDefined(sidePilot) || !sidePilot.FreshEvidence() { this.sideFreshObserved = false; }
    }
    // Keep the last fully acknowledged ordinary-world sample, never sample cleaned-up state.
    this.certified = this.ready && !this.dirty && this.Now() - this.lastCapture >= 0.00 && this.Now() - this.lastCapture <= 6.00;
    this.frozen = true; this.boundary = reason;
    this.detail = this.certified ? "Frozen pre-ending history; supported adapters only." : "History missing/stale/changed at cutoff; automatic restoration refused. Explicit override remains separate.";
  }
  private func ReadSnapshot() -> ActivitySnapshot {
    let s: ActivitySnapshot;
    let i = 0;
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    let entry: wref<JournalEntry>;
    let objective: wref<JournalQuestObjective>;
    let state: Int32;
    while i < ArraySize(this.paths) {
      entry = jm.GetEntryByString(this.paths[i], this.classes[i]);
      state = IsDefined(entry) ? EnumInt(jm.GetEntryState(entry)) : -1;
      ArrayPush(s.states, state >= 0 && state <= 4 ? state : -1);
      ArrayPush(s.tracked, IsDefined(entry) ? jm.IsEntryTracked(entry) : false);
      objective = entry as JournalQuestObjective;
      ArrayPush(s.optional, IsDefined(objective) ? (jm.GetIsObjectiveOptional(objective) ? 1 : 0) : -1);
      ArrayPush(s.counters, IsDefined(objective) ? jm.GetObjectiveCurrentCounter(objective) : -1);
      i += 1;
    }
    i = 0;
    while i < ArraySize(this.facts) { ArrayPush(s.facts, qs.GetFactStr(this.facts[i])); i += 1; }
    return s;
  }
  private func Same(a: ActivitySnapshot, b: ActivitySnapshot) -> Bool {
    if ArraySize(a.states) != ActivityDefinition.EntryCount() || ArraySize(a.facts) != ActivityDefinition.FactCount() ||
      ArraySize(b.states) != ArraySize(a.states) || ArraySize(b.facts) != ArraySize(a.facts) { return false; }
    let i = 0;
    while i < ArraySize(a.states) {
      if a.states[i] != b.states[i] || a.optional[i] != b.optional[i] || NotEquals(a.tracked[i], b.tracked[i]) || a.counters[i] != b.counters[i] { return false; }
      i += 1;
    }
    i = 0;
    while i < ArraySize(a.facts) { if a.facts[i] != b.facts[i] { return false; }; i += 1; }
    return true;
  }
  public func CaptureBeforeEnding() -> String {
    if this.faulted || this.frozen || this.BoundaryNow() { return "Refused: cannot manufacture pre-ending history after the cutoff, or replace mismatched history."; }
    if this.captureCount >= 2147483647 { return "Refused: snapshot generation overflow; prior history preserved."; }
    let player = GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject();
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    if !IsDefined(player) || jm.HasAnyDelayedStateChanges() { return "Waiting for a player and settled journal; no baseline replaced."; }
    let before = this.ReadSnapshot();
    let sidePilot = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.SideJobPilotS1.SideJobPilotS1") as SideJobPilotS1;
    let sideBefore = IsDefined(sidePilot) && sidePilot.FreshEvidence();
    let after = this.ReadSnapshot();
    let sideAfter = IsDefined(sidePilot) && sidePilot.FreshEvidence();
    if this.BoundaryNow() || jm.HasAnyDelayedStateChanges() || !this.Same(before, after) || NotEquals(sideBefore, sideAfter) {
      this.dirty = true; return "Refused: observation drift or cutoff during capture; prior history unchanged.";
    }
    this.baseline = after; this.schema = 1; this.fingerprint = ActivityDefinition.Fingerprint();
    this.sideFreshObserved = sideAfter;
    this.ready = true; this.dirty = false; this.certified = false; this.captureCount += 1; this.lastCapture = this.Now();
    this.detail = "Observed 71 gigs and 57 side/minor jobs in this save. No activity changed.";
    return this.GetStatus();
  }
  private func Schedule() -> Void {
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(ActivityTick.Create(this, this.epoch), 1.0, false);
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    this.Schedule();
    if this.faulted { return; }
    if !this.frozen && this.BoundaryNow() { this.Freeze(n"MonitorBoundary_NoLateResnapshot"); }
    if !this.frozen {
      if this.dirty || this.Now() - this.lastCapture >= 5.00 { this.CaptureBeforeEnding(); }
      return;
    }
    if this.certified && this.Tower() && !this.autoAttempted {
      this.autoAttempted = true; this.detail = this.RestoreSelected();
    }
  }
  private func Find(id: String) -> Int32 {
    let i = 0;
    while i < ArraySize(this.ids) { if Equals(id, this.ids[i]) { return i; }; i += 1; }
    return -1;
  }
  private func CurrentRoot(job: Int32) -> Int32 {
    let index = ActivityDefinition.RootIndex(job);
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    let entry = jm.GetEntryByString(this.paths[index], this.classes[index]);
    return IsDefined(entry) ? EnumInt(jm.GetEntryState(entry)) : -1;
  }
  public func Inspect(id: String) -> String {
    if Equals(id,"sts_wbr_jpn_02") {
      let fresh6=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.ActivityStateR3.FreshGigsB6") as FreshGigsB6;
      return IsDefined(fresh6) ? fresh6.Inspect()+" | certifiedFreshHistory="+ToString(this.B6FreshHistory()) : "Refused: B6 adapter missing.";
    }
    if FreshGigsB5.Index(id) >= 0 {
      let fresh = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.ActivityStateR3.FreshGigsB5") as FreshGigsB5;
      return IsDefined(fresh) ? fresh.Inspect(id) + " | certifiedFreshHistory=" + ToString(this.B5FreshHistory(id)) : "Refused: B5 adapter missing.";
    }
    let job = this.Find(id);
    if job < 0 { return "Not selected in the 71-gig/57-side-job catalogue."; }
    let index = ActivityDefinition.RootIndex(job);
    let old = this.ready && ArraySize(this.baseline.states) == ActivityDefinition.EntryCount() ? this.baseline.states[index] : -1;
    if Equals(id, "sts_bls_ina_07") {
      let minefield = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.MinefieldG3.MinefieldG3") as MinefieldG3;
      return IsDefined(minefield) ? minefield.Inspect() + " | pre-ending root=" + ToString(old) + " historyCertified=" + ToString(this.certified) + " earlyHistory=" + ToString(this.MinefieldHistory()) : "Refused: G3 adapter missing.";
    }
    if Equals(id, "sts_wat_nid_05") {
      let rite = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.RiteG2.RiteG2") as RiteG2;
      return IsDefined(rite) ? rite.Inspect() + " | pre-ending root=" + ToString(old) + " historyCertified=" + ToString(this.certified) + " exactHistory=" + ToString(this.RiteHistory()) : "Refused: G2 adapter missing.";
    }
    if Equals(id, "mq005_alley") {
      let sidePilot = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.SideJobPilotS1.SideJobPilotS1") as SideJobPilotS1;
      return IsDefined(sidePilot) ? sidePilot.Inspect() + " | pre-ending root=" + ToString(old) + " historyCertified=" + ToString(this.certified) + " freshEvidence=" + ToString(this.sideFreshObserved) : "Refused: S1 adapter missing.";
    }
    return this.titles[job] + " | pre-ending root=" + ToString(old) + " current=" + ToString(this.CurrentRoot(job)) +
      " historyCertified=" + ToString(this.certified) + " | " +
      (Equals(id, "sts_wat_nid_02") ? "Adapter: G1 exact inside-stage continuation only; no replay." : "Adapter not yet implemented. No reset or activation.");
  }
  public func RestoreSelected() -> String {
    if !this.Tower() || !this.frozen || !this.certified || this.faulted { return "Refused: requires genuine completed Tower and certified frozen pre-ending history."; }
    // Four scoped adapters. Catalogue coverage is not blanket owner restoration.
    let result = "Supported restoration: ";
    let job = this.Find("sts_wat_nid_02");
    let root = ActivityDefinition.RootIndex(job);
    if this.baseline.states[root] == 2 && this.CurrentRoot(job) == 4 {
      let pilot = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.GigPilotR1.GigPilotR1") as GigPilotR1;
      result += IsDefined(pilot) ? pilot.Restore() : "G1 adapter missing.";
    } else {
      result += "G1 not at supported started/cleanup state; preserved.";
    }
    job = this.Find("mq005_alley"); root = ActivityDefinition.RootIndex(job);
    if this.sideFreshObserved && this.baseline.states[root] == 1 && this.CurrentRoot(job) == 1 {
      let sidePilot = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.SideJobPilotS1.SideJobPilotS1") as SideJobPilotS1;
      result += " | S1: " + (IsDefined(sidePilot) ? sidePilot.RestoreFresh() : "Adapter missing.");
    } else {
      result += " | S1 no certified fresh encounter evidence; preserved.";
    }
    if this.RiteHistory() && this.CurrentRoot(this.Find("sts_wat_nid_05")) == 4 {
      let rite = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.RiteG2.RiteG2") as RiteG2;
      result += " | G2: " + (IsDefined(rite) ? rite.Restore() : "Adapter missing.");
    } else { result += " | G2 no certified exact pre-clinic history; preserved."; }
    if this.MinefieldHistory() {
      let minefield = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.MinefieldG3.MinefieldG3") as MinefieldG3;
      result += " | G3: " + (IsDefined(minefield) ? minefield.Restore() : "Adapter missing.");
    } else { result += " | G3 no certified early find-car history; preserved."; }
    return result + " | B5: " + this.RestoreGig("sts_wbr_hil_07") + " | " + this.RestoreGig("sts_wbr_hil_01") + " | B6: " + this.RestoreGig("sts_wbr_jpn_02") + " | Other 121 adapters pending; completed replay not implemented.";
  }
  // B4 can request one GIG without activating the separate Only Pain side job.
  // Original snapshot shape/fingerprint/cutoff and automatic dispatcher stay intact.
  public func BatchEpoch() -> Int32 { return this.epoch; }
  public func RestoreGig(id: String) -> String {
    if Equals(id,"sts_wbr_jpn_02") {
      if !this.B6FreshHistory() { return "Preserved: B6 needs certified untouched pre-ending history. No missing baseline facts invented; explicit fresh override available."; }
      let fresh6=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.ActivityStateR3.FreshGigsB6") as FreshGigsB6;
      return IsDefined(fresh6) ? fresh6.RestoreFresh() : "Refused: B6 adapter missing.";
    }
    if FreshGigsB5.Index(id) >= 0 {
      if !this.B5FreshHistory(id) { return "Preserved: B5 requires certified untouched pre-ending history; no history invented. Explicit fresh override remains available."; }
      let fresh = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.ActivityStateR3.FreshGigsB5") as FreshGigsB5;
      return IsDefined(fresh) ? fresh.RestoreFresh(id) : "Refused: B5 adapter missing.";
    }
    let job = this.Find(id);
    if job < 0 || job >= 71 { return "Refused: not in the immutable 71-gig history catalogue. No migration or invented history."; }
    if !this.Tower() || !this.frozen || !this.certified || this.faulted || !this.ready ||
      ArraySize(this.baseline.states) != ActivityDefinition.EntryCount() {
      return "Refused: requires genuine completed Tower and certified frozen pre-ending history.";
    }
    let old = this.baseline.states[ActivityDefinition.RootIndex(job)];
    let current = this.CurrentRoot(job);
    if old == 3 || current == 3 { return "Preserved: completed gig; no completed replay adapter."; }
    if old == 4 { return "Preserved: failed before ending; no reset."; }
    if Equals(id, "sts_wat_nid_02") {
      if old != 2 || current != 4 { return "Preserved: G1 requires its captured started/Tower-cleanup stage."; }
      let pilot = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.GigPilotR1.GigPilotR1") as GigPilotR1;
      return IsDefined(pilot) ? pilot.Restore() : "Refused: G1 adapter missing.";
    }
    if Equals(id, "sts_wat_nid_05") {
      if !this.RiteHistory() || current != 4 { return "Preserved: G2 requires certified exact pre-clinic history and current cleanup state."; }
      let rite = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.RiteG2.RiteG2") as RiteG2;
      return IsDefined(rite) ? rite.Restore() : "Refused: G2 adapter missing.";
    }
    if Equals(id, "sts_bls_ina_07") {
      if !this.MinefieldHistory() { return "Preserved: G3 requires certified early find-car history."; }
      let minefield = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.MinefieldG3.MinefieldG3") as MinefieldG3;
      return IsDefined(minefield) ? minefield.Restore() : "Refused: G3 adapter missing.";
    }
    return "Refused without mutation: gig owner/stage adapter not implemented. Catalogue coverage is not restoration.";
  }
  public func B7FreshHistory(id: String) -> Bool {
    let index=GigDataB7.Index(id);
    if index<0 || !this.Tower() || !this.frozen || !this.certified || this.faulted || !this.ready || ArraySize(this.baseline.states)!=ActivityDefinition.EntryCount() { return false; }
    let paths=GigDataB7.Paths(index);let k=0;let n: Int32;let found: Bool;
    while k<ArraySize(paths) {
      n=0;found=false;while n<ArraySize(this.paths) { if Equals(this.paths[n],paths[k]) { if this.baseline.states[n]!=1 { return false; };found=true;break; };n+=1; }
      if !found { return false; };k+=1;
    }
    let facts=GigDataB7.Facts(index);k=0;while k<ArraySize(facts) { if this.BaselineFact(facts[k])!=0 { return false; };k+=1; };return true;
  }
  private func BaselineFact(name: String) -> Int32 {
    if !this.ready || ArraySize(this.baseline.facts) != ArraySize(this.facts) { return -1; }
    let i = 0; while i < ArraySize(this.facts) { if Equals(this.facts[i], name) { return this.baseline.facts[i]; }; i += 1; }; return -1;
  }
  private func B6FreshHistory() -> Bool {
    if !this.Tower() || !this.frozen || !this.certified || this.faulted || !this.ready || ArraySize(this.baseline.states)!=ActivityDefinition.EntryCount() { return false; }
    let paths=FreshGigsB6.Paths();let k=0;let found: Bool;let n: Int32;
    while k<ArraySize(paths) {
      found=false;n=0;while n<ArraySize(this.paths) { if Equals(this.paths[n],paths[k]) { if this.baseline.states[n]!=1 { return false; };found=true;break; };n+=1; }
      if !found { return false; };k+=1;
    }
    let names=FreshGigsB6.LocalNames();k=0;while k<ArraySize(names) { if this.BaselineFact(names[k])!=0 { return false; };k+=1; };return true;
  }
  public func B5FreshHistory(id: String) -> Bool {
    if FreshGigsB5.Index(id) < 0 || !this.Tower() || !this.frozen || !this.certified || this.faulted || !this.ready || ArraySize(this.baseline.states) != ActivityDefinition.EntryCount() { return false; }
    let paths = FreshGigsB5.Paths(FreshGigsB5.Index(id)); let k = 0; let found: Bool; let n: Int32;
    while k < ArraySize(paths) {
      found = false; n = 0;
      while n < ArraySize(this.paths) { if Equals(this.paths[n], paths[k]) { if this.baseline.states[n] != 1 { return false; }; found = true; break; }; n += 1; }
      if !found { return false; }; k += 1;
    }
    let names = FreshGigsB5.LocalNames(FreshGigsB5.Index(id)); k = 0;
    // Missing old facts remain unknown. The Tyger scene facts absent from old
    // R3 history cannot be fabricated; its explicit override is supported.
    while k < ArraySize(names) { if this.BaselineFact(names[k]) != 0 { return false; }; k += 1; }; return true;
  }
  private func RiteHistory() -> Bool {
    if !this.frozen || !this.certified || this.faulted || !this.ready || ArraySize(this.baseline.states) != ActivityDefinition.EntryCount() { return false; }
    let job = this.Find("sts_wat_nid_05"); if job < 0 { return false; }
    let root = ActivityDefinition.RootIndex(job);
    let states: array<Int32> = [2, 2, 1, 1, 2, 1, 2];
    let i = 0; while i < 7 { if this.baseline.states[root + i] != states[i] { return false; }; i += 1; }
    return this.BaselineFact("nid_05_start") == 1 && this.BaselineFact("nid_05_finished") == 0 && this.BaselineFact("sts_wat_kab_nid_05_combat") == 0 &&
      this.BaselineFact("nid_05_after_holocall") == 0 && this.BaselineFact("nid_05_gang_retaliation") == 0 && this.BaselineFact("sts_wat_nid_05_ce_after_start") == 0 && this.BaselineFact("nid_05_testdef") == 0;
  }
  private func MinefieldHistory() -> Bool {
    if !this.frozen || !this.certified || this.faulted || !this.ready || ArraySize(this.baseline.states) != ActivityDefinition.EntryCount() { return false; }
    let job = this.Find("sts_bls_ina_07"); if job < 0 { return false; }; let root = ActivityDefinition.RootIndex(job);
    let states: array<Int32> = [2,2,1,2,1,1,1,1,1,1,1,1,1,1,2];
    let i = 0; while i < 15 { if this.baseline.states[root+i] != states[i] { return false; }; i += 1; }
    let zero: array<String> = ["ina_07_finished","ina_07_failed","ina_07_perfect","ina_07_test_def","sts_bls_ina_07_delivery_status","sts_bls_ina_07_chase_spawned","sts_bls_ina_07_reworked_chase_triggered","sts_bls_ina_07_chase_objective_active","ina_07_chase_is_on_east","ina_07_chase_is_on_east_01","ina_07_chase_is_on_west","ina_07_chase_is_on_west_02","ina_07_chase_lost"];
    i = 0; while i < ArraySize(zero) { if this.BaselineFact(zero[i]) != 0 { return false; }; i += 1; }
    // The immutable R3 global snapshot excludes '#' temporary facts. Native
    // readiness is checked live by G3; do not invent pre-ending ready evidence.
    return this.BaselineFact("ina_07_start") > 0;
  }
  public func Override(id: String, mode: String, confirmation: String) -> String {
    if !Equals(confirmation, "DISPOSABLE_SAVE") { return "Refused: explicit DISPOSABLE_SAVE acknowledgement required. Saved quest/world effects cannot be rolled back by file recovery."; }
    if this.faulted || !this.Tower() { return "Refused: mismatched catalogue or no genuine completed Tower. Override never bypasses ending/profile safety."; }
    if this.Find(id) < 0 { return "Refused: activity outside selected catalogue."; }
    if !Equals(mode, "resume") && !Equals(mode, "fresh") && !Equals(mode, "replay") { return "Refused: mode must be resume, fresh or replay."; }
    if Equals(id,"sts_wbr_jpn_02") {
      if !Equals(mode,"fresh") { return "Refused without mutation: B6 has fresh only; started/replay adapters absent."; }
      let fresh6=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.ActivityStateR3.FreshGigsB6") as FreshGigsB6;
      return IsDefined(fresh6) ? "Explicit history override; native fresh/tier/ownership guards retained: "+fresh6.RestoreFresh() : "Refused: B6 adapter missing.";
    }
    if FreshGigsB5.Index(id) >= 0 {
      if !Equals(mode, "fresh") { return "Refused without mutation: B5 implements fresh only, not started continuation/completed replay."; }
      let fresh = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.ActivityStateR3.FreshGigsB5") as FreshGigsB5;
      return IsDefined(fresh) ? "Explicit history override; fresh stage/native tier/ownership guards retained: " + fresh.RestoreFresh(id) : "Refused: B5 adapter missing.";
    }
    if Equals(id, "sts_bls_ina_07") && Equals(mode, "resume") {
      let minefield = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.MinefieldG3.MinefieldG3") as MinefieldG3;
      return IsDefined(minefield) ? "Explicit history override; saved early-stage/outcome guards retained: " + minefield.Restore() : "Refused: G3 adapter missing.";
    }
    if Equals(id, "sts_wat_nid_05") && Equals(mode, "resume") {
      let rite = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.RiteG2.RiteG2") as RiteG2;
      return IsDefined(rite) ? "Explicit history override; exact pre-clinic/outcome guards retained: " + rite.Restore() : "Refused: G2 adapter missing.";
    }
    if Equals(id, "mq005_alley") && Equals(mode, "fresh") {
      let sidePilot = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.SideJobPilotS1.SideJobPilotS1") as SideJobPilotS1;
      return IsDefined(sidePilot) ? "Explicit history override; native untouched-stage/outcome guards retained: " + sidePilot.RestoreFresh() : "Refused: S1 adapter missing.";
    }
    // Override skips ONLY the historical baseline requirement. It is NOT a
    // universal reset: actors/devices/loot/relationships/rewards need an adapter.
    if !Equals(id, "sts_wat_nid_02") || !Equals(mode, "resume") {
      return "Refused without mutation: requested fresh/resume/replay adapter not implemented. Snapshot and override dispatcher are not whitelist restoration.";
    }
    if this.CurrentRoot(this.Find(id)) == 3 { return "Refused: already completed; G1 has no completed-content replay adapter."; }
    let pilot = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.GigPilotR1.GigPilotR1") as GigPilotR1;
    if !IsDefined(pilot) { return "Refused: G1 adapter missing."; }
    return "Explicit history override; native stage/outcome guards retained: " + pilot.Restore();
  }
  public func GetStatus() -> String {
    return "Activity history R3: schema=" + ToString(this.schema) + " captures=" + ToString(this.captureCount) +
      " ready=" + ToString(this.ready) + " frozen=" + ToString(this.frozen) + " certified=" + ToString(this.certified) +
      " fault=" + ToString(this.faulted) + " | " + NameToString(this.boundary) + " | " + (this.faulted ? NameToString(this.fault) : this.detail);
  }
}

public class ActivityTick extends DelayCallback {
  private let owner: wref<ActivityState>;
  private let epoch: Int32;
  public static func Create(owner: ref<ActivityState>, epoch: Int32) -> ref<ActivityTick> {
    let tick = new ActivityTick(); tick.owner = owner; tick.epoch = epoch; return tick;
  }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}

@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void {
  wrappedMethod(gameInstance);
  let state = GameInstance.GetScriptableSystemsContainer(gameInstance).Get(n"PTFR.ActivityStateR3.ActivityState") as ActivityState;
  if IsDefined(state) { state.Restored(); }
}
