module PTFR.ActivityStateR3
import PTFR.ActivityStateR3.*
import PTFR.RestrictionsR1.*
import PTFR.JohnnyVoiceJV1.*

// Original Jeopardy phase pilot; only PTFRU4_Jeopardy_* bookkeeping is written.
public class NativeJeopardyU4 extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private func OnAttach() -> Void { this.running=true;this.Restored(); }
  private func OnDetach() -> Void { this.running=false;this.epoch+=1; }
  public func Restored() -> Void { this.epoch+=1;if this.running { this.Schedule(); } }
  private func Schedule() -> Void { GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(NativeJeopardyTickU4.Create(this,this.epoch),1.0,false); }
  private func Fact(s: String) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(StringToName(s)); }
  private func Own(s: String) -> Int32 { return this.Fact("PTFRU4_Jeopardy_"+s); }
  private func Set(s: String,v: Int32) -> Bool { GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(StringToName("PTFRU4_Jeopardy_"+s),v);return this.Own(s)==v; }
  private func State(path: String,cls: String) -> Int32 { let jm=GameInstance.GetJournalManager(this.GetGameInstance());let e=jm.GetEntryByString(path,cls);return IsDefined(e) ? EnumInt(jm.GetEntryState(e)) : -1; }
  private func Tower() -> Bool { let s=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.JohnnyVoiceJV1.JohnnyVoiceJV1") as JohnnyVoiceJV1;return IsDefined(s) && s.CompletedTower(); }
  private func Tier() -> Bool { return this.Fact("sts_hey_rey_tier_1_1")>0 || (this.Fact("sts_hey_rey_tier_1")>0 && this.Fact("sts_hey_rey_tier_1_1")==0); }
  // Development assumption affects admission, never certifies pre-Tower history.
  private func DevelopmentEligible() -> Bool {
    let root=this.State("quests/street_stories/heywood/vista_del_rey/sts_hey_rey_06","gameJournalQuest");
    return GigDataB7.Index("sts_hey_rey_06")>=0 && this.Tower() && root>=1 && root<=4 && root!=3 && this.Fact("rey_06_finished")==0;
  }
  // Supported native entry shape, not a test of historical freshness.
  private func RuntimeEntrySafe() -> Bool {
    let i=GigDataB7.Index("sts_hey_rey_06");if i<0 { return false; };let paths=GigDataB7.Paths(i);let classes=GigDataB7.Classes(i);let k=0;
    while k<ArraySize(paths) { if this.State(paths[k],classes[k])!=1 { return false; };k+=1; }
    let facts=GigDataB7.Facts(i);k=0;while k<ArraySize(facts) { if this.Fact(facts[k])!=0 { return false; };k+=1; }
    let poi=this.State("points_of_interest/street_stories/sts_hey_rey_06","gameJournalPointOfInterestMappin");return poi==1 || poi==2;
  }
  private func OldUnused() -> Bool {
    let keys: array<String>=["Queued","Request","Permit","Started","OwnerFinished","Fault","CounterClaim","CounterAck","CountBase","Reward0_Claim","Reward0_Ack","Achievement0_Claim","Achievement0_Ack"];
    let k=0;while k<ArraySize(keys) { if this.Fact("PTFRB7_hey_rey_06_"+keys[k])!=0 { return false; };k+=1; };return true;
  }
  private func HeywoodIdle() -> Bool {
    let i=0;while i<GigDataB7.Count() { if Equals(GigDataB7.Region(i),"hey") { let tag=GigDataB7.Tag(i);if this.Fact(tag+"_Queued")!=0 && this.Fact(tag+"_OwnerFinished")!=1 { return false; } };i+=1; };return true;
  }
  public func Inspect() -> String {
    return "Native Jeopardy U4: ready/request/entered/finished="+ToString(this.Own("Ready"))+"/"+ToString(this.Own("Request"))+"/"+ToString(this.Own("Started"))+"/"+ToString(this.Own("OwnerFinished"))+" permit="+ToString(this.Own("Permit"))+" fault="+ToString(this.Own("Fault"))+" tower="+ToString(this.Tower())+" tier="+ToString(this.Tier())+" devEligible="+ToString(this.DevelopmentEligible())+" entrySafe="+ToString(this.RuntimeEntrySafe())+" oldUnused="+ToString(this.OldUnused())+" HeywoodIdle="+ToString(this.HeywoodIdle())+" root="+ToString(this.State("quests/street_stories/heywood/vista_del_rey/sts_hey_rey_06","gameJournalQuest"))+" start/done="+ToString(this.Fact("rey_06_start"))+"/"+ToString(this.Fact("rey_06_finished"))+" Padre request/startDone/endRequest/endDone="+ToString(this.Fact("holo_padre_calls_v_start_activate"))+"/"+ToString(this.Fact("holo_padre_calls_v_start_done"))+"/"+ToString(this.Fact("holo_padre_calls_v_end_activate"))+"/"+ToString(this.Fact("holo_padre_calls_v_end_done"))+" phoneActive/Started="+ToString(this.Fact("holo_setup_active"))+"/"+ToString(this.Fact("holo_setup_started"))+" counterBase/current="+ToString(this.Own("CountBase"))+"/"+ToString(this.Fact("hey_sts_counter"))+" | DEVELOPMENT assumed unstarted, not certified history. Original phases/calls/rewards. First test startup and briefing only; stock fixer-credit dependency still pending.";
  }
  public func Start(confirmation: String) -> String {
    if !Equals(confirmation,"DISPOSABLE_SAVE") { return "Refused: DISPOSABLE_SAVE required."; }
    if !this.Tower() || this.Own("Ready")!=1 || this.Own("Revision")!=1 { return "Refused: completed Tower and U4 archive ready required. "+this.Inspect(); }
    if this.Own("Request")!=0 { return "Already requested; no restart. "+this.Inspect(); }
    if !this.DevelopmentEligible() { return "Refused: incomplete whitelisted post-Tower Jeopardy required; completed gigs are excluded. "+this.Inspect(); }
    if !this.RuntimeEntrySafe() { return "Development-eligible (assumed unstarted), but this native stage needs a cleanup/continuation adapter before safe entry; no state reset or duplicate owner. "+this.Inspect(); }
    if !this.Tier() || !this.OldUnused() || !this.HeywoodIdle() { return "Deferred: native tier or existing owner interlock; no tier forcing or duplicate owner. "+this.Inspect(); }
    if this.Own("Started")!=0 || this.Own("OwnerFinished")!=0 || this.Own("Fault")!=0 || this.Own("Permit")!=0 { return "Refused: used/interrupted trial; no restart. "+this.Inspect(); }
    if !this.Set("CountBase",this.Fact("hey_sts_counter")) || !this.Set("Request",1) { this.Set("Fault",1);return "Request readback failed; no retry."; }
    return "Development assumption: incomplete treated as unstarted; no history certified. Queued ORIGINAL Jeopardy. Close CET/menus and holster; then approach the native encounter. "+this.Inspect();
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch!=this.epoch { return; };this.Schedule();
    if this.Own("Request")!=1 || this.Own("Started")!=0 { return; }
    let p=GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    let permit=this.DevelopmentEligible() && this.Tier() && this.Own("Fault")==0 && this.OldUnused() && this.RuntimeEntrySafe() && this.HeywoodIdle() && IsDefined(p) && CyberwarePolicy.Safe(p) ? 1 : 0;
    if this.Own("Permit")!=permit && !this.Set("Permit",permit) { this.Set("Fault",1); }
  }
}
public class NativeJeopardyTickU4 extends DelayCallback {
  private let owner: wref<NativeJeopardyU4>;private let epoch: Int32;
  public static func Create(owner: ref<NativeJeopardyU4>,epoch: Int32) -> ref<NativeJeopardyTickU4> { let t=new NativeJeopardyTickU4();t.owner=owner;t.epoch=epoch;return t; }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}
@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void { wrappedMethod(gameInstance);let s=GameInstance.GetScriptableSystemsContainer(gameInstance).Get(n"PTFR.ActivityStateR3.NativeJeopardyU4") as NativeJeopardyU4;if IsDefined(s) { s.Restored(); } }
