module PTFR.HistorySnapshotHS1

import PTFR.ActivityStateR3.*
import PTFR.RestrictionsR1.*
import PTFR.RestrictionsR2.*
import PTFR.RestrictionsR3.*
import PTFR.Housing.*
import PTFR.RestorationBaseline.*

public struct SnapshotRowHS1 {
  public persistent let states: array<Int32>;
  public persistent let facts: array<Int32>;
  public persistent let counters: array<Int32>;
  public persistent let optional: array<Int32>;
  public persistent let tracked: array<Int32>;
  public persistent let stable: Bool;
  public persistent let legacyCertified: Bool;
}

// A new catalogue/system preserves every previously shipped persistent identity.
// JSON is a verified sidecar of this save-local payload, never a global import.
public class SnapshotStateHS1 extends ScriptableSystem {
  private persistent let schema: Int32;
  private persistent let catalogue: CName;
  private persistent let rows: array<SnapshotRowHS1>;
  private persistent let previousRows: array<SnapshotRowHS1>;
  private persistent let origin: CName;
  private persistent let ready: Bool;
  private persistent let frozen: Bool;
  private persistent let revision: Int32;
  private persistent let fileToken: CName;
  private persistent let faulted: Bool;
  private let running: Bool;
  private let epoch: Int32;
  private let exported: Bool;
  private let listeners: array<Uint32>;
  private let registered: Bool;
  private let sample: array<SnapshotRowHS1>;
  private let cursor: Int32;
  private let pass: Int32;
  private let changed: Bool;
  private let capturePost: Bool;
  private let lastCapture: Float;
  private let captureStarted: Float;
  private let detail: String;

  public static func Get(game: GameInstance) -> ref<SnapshotStateHS1> {
    return GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.HistorySnapshotHS1.SnapshotStateHS1") as SnapshotStateHS1;
  }
  public static func StartupReady(game: GameInstance) -> Bool {
    let s=SnapshotStateHS1.Get(game); return IsDefined(s) && s.Ready();
  }
  public static func Admits(game: GameInstance,id: String) -> Bool {
    let s=SnapshotStateHS1.Get(game); return IsDefined(s) && s.Allows(id);
  }
  public static func FamilyAccepted(game: GameInstance) -> Bool {
    let s=SnapshotStateHS1.Get(game);return IsDefined(s) && s.FamilyPrerequisite();
  }
  private func Fact(name: String) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFactStr(name); }
  private func Now() -> Float { return EngineTime.ToFloat(GameInstance.GetSimTime(this.GetGameInstance())); }
  private func Boundary() -> Bool {
    return this.Fact("q115_point_of_no_return")>0 || this.Fact("q307_point_of_no_return")>0 ||
      this.Fact("q307_2079")>0 || this.Fact("q307_main_game_killed")>0 || this.Fact("q307_ep1_killed")>0 ||
      this.Fact("q307_done")>0 || this.Fact("q307_finished")>0 || this.Fact("PostTowerFreeRoamActive")>0;
  }
  private func Teardown() -> Bool {
    return this.Fact("q307_2079")>0 || this.Fact("q307_main_game_killed")>0 || this.Fact("q307_ep1_killed")>0 ||
      this.Fact("q307_done")>0 || this.Fact("q307_finished")>0 || this.Fact("PostTowerFreeRoamActive")>0;
  }
  private func Tower() -> Bool { return CyberwarePolicy.Completed(this.GetGameInstance()) && this.Fact("q307_debug_reset")==0; }
  private func OnAttach() -> Void { this.running=true; this.Restored(); }
  private func OnDetach() -> Void { this.Unregister(); this.running=false; this.epoch+=1; this.exported=false; }
  private func ResetRead() -> Void { this.cursor=0;this.pass=0;this.changed=false;ArrayClear(this.sample); }
  public func Restored() -> Void {
    this.Unregister();this.epoch+=1;this.exported=false;this.lastCapture=-100.0;this.ResetRead();
    if this.schema!=0 && (this.schema!=1 || NotEquals(this.catalogue,SnapshotDataHS1.Fingerprint())) { this.faulted=true; }
    if this.ready && (!this.Shape(this.rows) || this.revision<=0 || this.schema!=1) { this.faulted=true; }
    if this.frozen && (!this.ready || (NotEquals(this.origin,n"pre_ending") && NotEquals(this.origin,n"post_ending_fallback"))) { this.faulted=true; }
    if !this.faulted && this.frozen && !this.Boundary() {
      // Preserve the former branch's evidence, but do not apply its outcomes to a pre-ending branch.
      this.previousRows=this.rows;this.ready=false;this.frozen=false;this.fileToken=n"";this.origin=n"";
    }
    if !this.faulted && !this.frozen && this.Boundary() {
      // An unfrozen old sample is not promoted to a verified pre-ending snapshot on load.
      if this.ready { this.previousRows=this.rows; }
      this.ready=false;this.origin=n"";this.fileToken=n"";
    }
    this.Register(); if this.running { this.Schedule(); }
  }
  private func Register() -> Void {
    if this.registered { return; }
    let q=GameInstance.GetQuestsSystem(this.GetGameInstance());
    ArrayPush(this.listeners,q.RegisterListener(n"q115_point_of_no_return",this,n"OnBoundary"));
    ArrayPush(this.listeners,q.RegisterListener(n"q307_point_of_no_return",this,n"OnBoundary"));this.registered=true;
  }
  private func Unregister() -> Void {
    if !this.registered { return; }
    let q=GameInstance.GetQuestsSystem(this.GetGameInstance());
    if ArraySize(this.listeners)==2 {
      q.UnregisterListener(n"q115_point_of_no_return",this.listeners[0]);
      q.UnregisterListener(n"q307_point_of_no_return",this.listeners[1]);
    }
    ArrayClear(this.listeners);this.registered=false;
  }
  protected cb func OnBoundary(value: Int32) -> Bool {
    if value<=0 || this.frozen || this.faulted { return false; }
    let jm=GameInstance.GetJournalManager(this.GetGameInstance());
    let age=this.Now()-this.lastCapture;
    if this.ready && age>=0.0 && age<=6.0 && !this.Teardown() && IsDefined(jm) && !jm.HasAnyDelayedStateChanges() {
      // Check the exact snapshot again at the native boundary; changed history is not certified.
      let i=0;
      while i<SnapshotDataHS1.Count() { if !this.Same(this.rows[i],this.ReadRow(i)) { this.rows[i].stable=false; };i+=1; }
      if !this.Teardown() && !jm.HasAnyDelayedStateChanges() {
        this.frozen=true;this.origin=n"pre_ending";this.exported=false;this.fileToken=n"";
        this.detail="Pre-ending snapshot frozen; awaiting verified JSON export.";
      }
    }
    this.ResetRead();return false;
  }
  private func ReadRow(i: Int32) -> SnapshotRowHS1 {
    let row: SnapshotRowHS1;row.stable=true;
    let jm=GameInstance.GetJournalManager(this.GetGameInstance());
    let paths=SnapshotDataHS1.Paths(i);let classes=SnapshotDataHS1.Classes(i);let names=SnapshotDataHS1.Facts(i);
    let k=0;let entry:wref<JournalEntry>;let objective:wref<JournalQuestObjective>;
    while k<ArraySize(paths) {
      entry=jm.GetEntryByString(paths[k],classes[k]);
      ArrayPush(row.states,IsDefined(entry)?EnumInt(jm.GetEntryState(entry)):-1);
      objective=entry as JournalQuestObjective;
      ArrayPush(row.counters,IsDefined(objective)?jm.GetObjectiveCurrentCounter(objective):-1);
      ArrayPush(row.optional,IsDefined(objective)?(jm.GetIsObjectiveOptional(objective)?1:0):-1);
      ArrayPush(row.tracked,IsDefined(entry)?(jm.IsEntryTracked(entry)?1:0):-1);k+=1;
    }
    k=0;while k<ArraySize(names) { ArrayPush(row.facts,this.Fact(names[k]));k+=1; }
    let legacy=PreAlphaEntry.Get(this.GetGameInstance());
    row.legacyCertified=IsDefined(legacy) && legacy.Certified(SnapshotDataHS1.ID(i));
    return row;
  }
  private func Same(a: SnapshotRowHS1,b: SnapshotRowHS1) -> Bool {
    if ArraySize(a.states)!=ArraySize(b.states) || ArraySize(a.facts)!=ArraySize(b.facts) { return false; }
    let k=0;while k<ArraySize(a.states) {
      if a.states[k]!=b.states[k] || a.counters[k]!=b.counters[k] || a.optional[k]!=b.optional[k] || a.tracked[k]!=b.tracked[k] { return false; };k+=1;
    }
    k=0;while k<ArraySize(a.facts) { if a.facts[k]!=b.facts[k] { return false; };k+=1; }return true;
  }
  private func Shape(rows: array<SnapshotRowHS1>) -> Bool {
    if ArraySize(rows)!=SnapshotDataHS1.Count() { return false; }
    let i=0;while i<ArraySize(rows) {
      let paths=SnapshotDataHS1.Paths(i);let names=SnapshotDataHS1.Facts(i);
      if ArraySize(rows[i].states)!=ArraySize(paths) || ArraySize(rows[i].facts)!=ArraySize(names) ||
        ArraySize(rows[i].counters)!=ArraySize(rows[i].states) || ArraySize(rows[i].optional)!=ArraySize(rows[i].states) || ArraySize(rows[i].tracked)!=ArraySize(rows[i].states) { return false; };i+=1;
    }return true;
  }
  private func Schedule() -> Void { GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(SnapshotTickHS1.Create(this,this.epoch),0.10,false); }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch!=this.epoch { return; }this.Schedule();
    if this.faulted || this.frozen { return; }
    let game=this.GetGameInstance();let jm=GameInstance.GetJournalManager(game);
    let player=GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(jm) || !IsDefined(player) || player.IsReplacer() || player.IsDead() || jm.HasAnyDelayedStateChanges() { this.ResetRead();return; }
    let post=this.Tower();
    if !post && this.Boundary() { this.ResetRead();return; }
    if this.pass==0 {
      if !post && this.Now()-this.lastCapture<5.0 { return; }
      this.capturePost=post;this.captureStarted=this.Now();this.pass=1;
    }
    if NotEquals(post,this.capturePost) || this.Now()-this.captureStarted>15.0 { this.ResetRead();return; }
    let budget=0;let row:SnapshotRowHS1;
    while budget<16 && this.cursor<SnapshotDataHS1.Count() {
      row=this.ReadRow(this.cursor);
      if this.pass==1 { ArrayPush(this.sample,row); }
      else { if !this.Same(this.sample[this.cursor],row) { this.sample[this.cursor].stable=false; } }
      this.cursor+=1;budget+=1;
    }
    if this.cursor<SnapshotDataHS1.Count() { return; }
    if this.pass==1 { this.pass=2;this.cursor=0;return; }
    if jm.HasAnyDelayedStateChanges() || NotEquals(this.Tower(),this.capturePost) || (!post && this.Boundary()) { this.ResetRead();return; }
    if !this.Shape(this.sample) || this.revision>=2147483647 { this.faulted=true;this.detail="Snapshot schema or revision failure; prior evidence retained.";return; }
    if post && this.ready { this.previousRows=this.rows; }
    this.rows=this.sample;this.schema=1;this.catalogue=SnapshotDataHS1.Fingerprint();this.ready=true;this.revision+=1;
    this.lastCapture=this.Now();this.exported=false;this.fileToken=n"";
    if post { this.frozen=true;this.origin=n"post_ending_fallback";this.detail="Accepted current-state fallback captured once; awaiting JSON export."; }
    else { this.origin=n"pre_ending_candidate";this.detail="Ordinary-world snapshot refreshed; freeze at native cutoff."; }
    this.ResetRead();
  }
  public func Ready() -> Bool { return !this.faulted && this.ready && this.frozen && this.exported; }
  public func CanExport() -> Bool { return !this.faulted && this.ready && this.frozen; }
  public func Epoch() -> Int32 { return this.epoch; }
  public func Revision() -> Int32 { return this.revision; }
  public func FileToken() -> String { return Equals(this.fileToken,n"") ? "" : NameToString(this.fileToken); }
  public func Exported() -> Bool { return this.exported; }
  public func Count() -> Int32 { return SnapshotDataHS1.Count(); }
  public func AckFile(epoch: Int32,revision: Int32,token: String) -> Bool {
    if epoch!=this.epoch || revision!=this.revision || !this.CanExport() || Equals(token,"") { return false; }
    this.fileToken=StringToName(token);this.exported=true;this.detail="Snapshot JSON verified; restoration uses this save-local baseline.";return true;
  }
  public func ReportIOFailure(epoch: Int32,revision: Int32) -> Void {
    if epoch==this.epoch && revision==this.revision { this.exported=false;this.detail="Snapshot file unavailable; new admissions wait. Existing owners are not reset."; }
  }
  public func Allows(id: String) -> Bool {
    let i=SnapshotDataHS1.Index(id);
    if !this.Ready() || i<0 || !this.rows[i].stable || ArraySize(this.rows[i].states)==0 { return false; }
    // Failed in the accepted baseline remains failed; Active needs an existing supported resume adapter.
    return this.rows[i].states[0]==1 || this.rows[i].states[0]==2;
  }
  public func FreshU9(id: String) -> Bool {
    let i=SnapshotDataHS1.Index(id);if !this.Allows(id) || i<0 { return false; }
    let indices=SnapshotDataHS1.U9StateIndices(i);if ArraySize(indices)==0 { return false; }
    let k=0;while k<ArraySize(indices) { if this.rows[i].states[indices[k]]!=1 { return false; };k+=1; }
    indices=SnapshotDataHS1.U9FactIndices(i);k=0;
    while k<ArraySize(indices) { if this.rows[i].facts[indices[k]]!=0 { return false; };k+=1; }return true;
  }
  public func FamilyPrerequisite() -> Bool {
    let i=SnapshotDataHS1.Index("sts_wbr_hil_06");if !this.Ready() || i<0 || !this.rows[i].stable { return false; }
    let paths=SnapshotDataHS1.Paths(i);let names=SnapshotDataHS1.Facts(i);let k=0;let root=false;let done=false;let rogue=false;
    while k<ArraySize(paths) { if Equals(paths[k],"quests/main_quest/act_01/q103_warhead") { root=this.rows[i].states[k]==3; };k+=1; }
    k=0;while k<ArraySize(names) {
      if Equals(names[k],"q103_done") { done=this.rows[i].facts[k]>=1; }
      if Equals(names[k],"q103_rogue_done") { rogue=this.rows[i].facts[k]>=1; }k+=1;
    }return root && done && rogue;
  }
  private func IntJSON(values: array<Int32>) -> String {
    let out="[";let i=0;while i<ArraySize(values) { if i>0 { out+=","; };out+=ToString(values[i]);i+=1; }return out+"]";
  }
  public func HeaderJSON() -> String {
    if !this.CanExport() { return ""; }
    return "{\"schema\":1,\"catalogue\":\""+NameToString(this.catalogue)+"\",\"origin\":\""+NameToString(this.origin)+"\",\"revision\":"+ToString(this.revision)+",\"rows\":[";
  }
  public func RowJSON(i: Int32) -> String {
    if !this.CanExport() || i<0 || i>=ArraySize(this.rows) { return ""; }
    let row=this.rows[i];
    return "{\"definition\":"+SnapshotDataHS1.MetadataJSON(i)+",\"states\":"+this.IntJSON(row.states)+",\"facts\":"+this.IntJSON(row.facts)+
      ",\"counters\":"+this.IntJSON(row.counters)+",\"optional\":"+this.IntJSON(row.optional)+",\"tracked\":"+this.IntJSON(row.tracked)+
      ",\"stable\":"+(row.stable?"true":"false")+",\"legacy_pre_ending_certificate\":"+(row.legacyCertified?"true":"false")+"}";
  }
  public func Status() -> String {
    return "Snapshot HS1 origin="+NameToString(this.origin)+" ready/frozen/exported="+ToString(this.ready)+"/"+ToString(this.frozen)+"/"+ToString(this.exported)+" revision="+ToString(this.revision)+" fault="+ToString(this.faulted)+" file="+this.FileToken()+" | "+this.detail;
  }
}
public class SnapshotTickHS1 extends DelayCallback {
  private let owner:wref<SnapshotStateHS1>;
  private let epoch:Int32;
  public static func Create(owner:ref<SnapshotStateHS1>,epoch:Int32) -> ref<SnapshotTickHS1> { let c=new SnapshotTickHS1();c.owner=owner;c.epoch=epoch;return c; }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}

// Bounded continuation of the exact retained PA2 preparation-timeout branch.
// The native timeout cut both waiters; clearing Fault alone cannot finish it.
// Never replay any ending/arrival owner, and never write a native story fact.
public class SnapshotRecoveryHS1 extends ScriptableSystem {
  private persistent let schema:Int32;
  private persistent let phase:Int32;
  private persistent let originalFault:Int32;
  private let running:Bool;
  private let epoch:Int32;
  private let stable:Int32;
  public static func Get(game:GameInstance) -> ref<SnapshotRecoveryHS1> {
    return GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.HistorySnapshotHS1.SnapshotRecoveryHS1") as SnapshotRecoveryHS1;
  }
  private func Fact(n:CName) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(n); }
  private func OnAttach() -> Void { this.running=true;this.Restored(); }
  private func OnDetach() -> Void { this.running=false;this.epoch+=1; }
  public func Restored() -> Void {
    this.epoch+=1;this.stable=0;
    if (this.schema!=0 && this.schema!=1) || (this.phase!=0 && (this.schema!=1 || this.originalFault!=2)) { this.phase=99; }
    if this.running { this.Schedule(); }
  }
  private func Schedule() -> Void { GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(SnapshotRecoveryTickHS1.Create(this,this.epoch),0.25,false); }
  private func BaseReady() -> Bool {
    let game=this.GetGameInstance();let player=GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
    let profile=ProfilePolicy.Get(game);let entry=PreAlphaEntry.Get(game);
    return SnapshotStateHS1.StartupReady(game) && CyberwarePolicy.Completed(game) && this.Fact(n"q307_debug_reset")==0 &&
      IsDefined(entry) && entry.SnapshotInitializationHealthy() &&
      this.Fact(n"PTFRPA2_Started")==1 && this.Fact(n"PTFRPA2_Teleported")==1 &&
      this.Fact(n"PTFRPA2_ControlReady")==1 && this.Fact(n"PTFRPA3_CoverReleased")==1 &&
      this.Fact(n"PTFRPA4_CameraAligned")==1 && this.Fact(n"PTFRPA5O_Ready")==1 && this.Fact(n"PTFRPA5O_Done")==1 &&
      this.Fact(n"PTFRPA5O_NativeOut")==1 && this.Fact(n"PTFRPA5O_Fault")==0 && this.Fact(n"PTFRH1_Fault")==0 &&
      IsDefined(profile) && !profile.PTFRPAFaulted() && IsDefined(player) && BodyPolicy.Safe(player);
  }
  private func ExactFailedPreparation() -> Bool {
    return this.Fact(n"PTFRPA2_Fault")==2 && this.Fact(n"PTFRPA2_Prepared")==0 &&
      this.Fact(n"PTFRPA2_Reveal")==0 && this.Fact(n"PTFRPA2_Finished")==0;
  }
  private func SetOwned(name:CName,value:Int32) -> Bool {
    GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(name,value);return this.Fact(name)==value;
  }
  public func Poll(epoch:Int32) -> Void {
    if !this.running || epoch!=this.epoch { return; }this.Schedule();
    if this.phase==3 || this.phase==99 { return; }
    if !this.BaseReady() { this.stable=0;return; }
    if this.phase==0 {
      if !this.ExactFailedPreparation() { this.stable=0;return; }
      this.stable+=1;if this.stable<4 { return; }
      this.schema=1;this.originalFault=2;this.phase=1;this.stable=0;
    }
    if this.phase==1 {
      if this.ExactFailedPreparation() {
        if !this.SetOwned(n"PTFRPA2_Fault",0) { this.phase=99;return; }
      } else { if this.Fact(n"PTFRPA2_Fault")!=0 || this.Fact(n"PTFRPA2_Finished")!=0 { this.phase=99;return; } }
      this.phase=2;return;
    }
    if this.phase!=2 || this.Fact(n"PTFRPA2_Fault")!=0 { return; }
    if this.Fact(n"PTFRPA2_Finished")==1 { this.phase=3;return; }
    let game=this.GetGameInstance();let housing=HousingState.Get(game);let profile=ProfilePolicy.Get(game);
    let arrival=GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.ActivityStateR3.PreAlphaArrivalPA1") as PreAlphaArrivalPA1;
    let world=GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.RestorationBaseline.RestorationBaseline") as RestorationBaseline;
    if this.Fact(n"PTFRPA2_Prepared")!=1 || this.Fact(n"PTFRPA2_Reveal")!=1 || !IsDefined(arrival) || !arrival.Completed() ||
      !IsDefined(housing) || !housing.HousingReadyForReveal() || !profile.PTFRPAComplete() || !IsDefined(world) || !world.H10GeometryReady() {
      this.stable=0;return;
    }
    if housing.Entitled("h10") && !world.H10ActionsArmed() { this.stable=0;return; }
    this.stable+=1;if this.stable<4 { return; }
    if this.SetOwned(n"PTFRPA2_Finished",1) { this.phase=3; } else { this.phase=99; }
  }
  public func Status() -> String { return "HS1 preparation continuation phase="+ToString(this.phase)+" originalFault="+ToString(this.originalFault)+" (0 unused, 1 recorded, 2 resuming, 3 finished, 99 stopped)"; }
}
public class SnapshotRecoveryTickHS1 extends DelayCallback {
  private let owner:wref<SnapshotRecoveryHS1>;
  private let epoch:Int32;
  public static func Create(owner:ref<SnapshotRecoveryHS1>,epoch:Int32) -> ref<SnapshotRecoveryTickHS1> { let c=new SnapshotRecoveryTickHS1();c.owner=owner;c.epoch=epoch;return c; }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}
@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance:GameInstance) -> Void {
  wrappedMethod(gameInstance);let s=SnapshotStateHS1.Get(gameInstance);if IsDefined(s) { s.Restored(); }
  let recovery=SnapshotRecoveryHS1.Get(gameInstance);if IsDefined(recovery) { recovery.Restored(); }
}
