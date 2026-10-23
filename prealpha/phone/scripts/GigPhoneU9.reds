module PTFR.ActivityStateR3
import PTFR.RestrictionsR1.*
import PTFR.JohnnyVoiceJV1.*

// Consolidated pre-alpha admission. Native request/queue/setup flags protect
// pending calls. Lifetime scene-entry counters are diagnostics, not an idle lock.
public class GigPhoneU9 extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private func OnAttach() -> Void { this.running=true;this.Restored(); }
  private func OnDetach() -> Void { this.running=false;this.epoch+=1; }
  public func Restored() -> Void { this.epoch+=1;if this.running { this.Schedule(); } }
  private func Schedule() -> Void { GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(GigPhoneTickU9.Create(this,this.epoch),1.0,false); }
  private func Fact(s: String) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(StringToName(s)); }
  private func Own(s: String) -> Int32 { return this.Fact("PTFRU9_Support_"+s); }
  private func Set(s: String,v: Int32) -> Bool { GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(StringToName("PTFRU9_Support_"+s),v);return this.Own(s)==v; }
  private func AllZero(names: array<String>) -> Bool { let k=0;while k<ArraySize(names) { if this.Fact(names[k])!=0 { return false; };k+=1; };return true; }
  private func OriginalLifetimeClosed() -> Bool {
    let s=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.JohnnyVoiceJV1.JohnnyVoiceJV1") as JohnnyVoiceJV1;
    let jm=GameInstance.GetJournalManager(this.GetGameInstance());let e=jm.GetEntryByString("ep1/quests/main_quest/q307_before_tomorrow","gameJournalQuest");
    return IsDefined(s) && s.CompletedTower() && IsDefined(e) && EnumInt(jm.GetEntryState(e))==3 && this.Fact("q307_main_game_killed")==1 && this.Fact("q307_ep1_killed")==1 && this.Fact("q307_active")==0 && this.Fact("q307_debug_reset")==0;
  }
  private func OldOwnerBusy(tag: String) -> Bool {
    return (this.Fact(tag+"Request")!=0 || this.Fact(tag+"Queued")!=0 || this.Fact(tag+"Permit")!=0 || this.Fact(tag+"Started")!=0) && this.Fact(tag+"OwnerFinished")!=1;
  }
  private func LegacyIdle() -> Bool {
    if !this.AllZero(GigPhoneDataU9.PredecessorFacts()) { return false; }
    let tags: array<String>=["PTFRU1_Shark_","PTFRU4_Jeopardy_","PTFRG1_","PTFRG2_","PTFRG3_","PTFRB5_H7_","PTFRB5_H1_","PTFRB6_J2_"];
    let k=0;while k<ArraySize(tags) { if this.OldOwnerBusy(tags[k]) { return false; };k+=1; }
    let i=0;while i<NativeGigDataU9.Count() {
      tags=NativeGigDataU9.LegacyTags(i);k=0;
      while k<ArraySize(tags) { if this.OldOwnerBusy(tags[k]+"_") { return false; };k+=1; }
      if !this.AllZero(NativeGigDataU9.LegacyOwnerFacts(i)) || this.OldOwnerBusy("PTFRU8_"+NativeGigDataU9.ID(i)+"_") { return false; };i+=1;
    };return true;
  }
  private func IdleProtocol() -> Bool { return this.AllZero(GigPhoneDataU9.IdleFacts()); }
  private func LivePhoneIdle() -> Bool {
    let phone=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PhoneSystem") as PhoneSystem;
    return IsDefined(phone) && phone.IsPhoneEnabled() && phone.IsCallingEnabled() && !GameInstance.GetPhoneManager(this.GetGameInstance()).IsPhoneCallActive();
  }
  public func ProtocolStatus() -> String {
    let names=GigPhoneDataU9.IdleFacts();let k=0;let out="";
    while k<ArraySize(names) { let v=this.Fact(names[k]);if v!=0 { out+=names[k]+"="+ToString(v)+"; "; };k+=1; }
    return Equals(out,"") ? "No pending protocol facts." : out;
  }
  public func CounterStatus() -> String {
    let starts=GigPhoneDataU9.BalanceStarts();let ends=GigPhoneDataU9.BalanceEnds();let k=0;let out="Lifetime counters (informational): ";
    while k<ArraySize(starts) { if this.Fact(starts[k])!=this.Fact(ends[k]) { out+=starts[k]+"="+ToString(this.Fact(starts[k]))+" / "+ends[k]+"="+ToString(this.Fact(ends[k]))+"; "; };k+=1; };return out;
  }
  public func Supported() -> Bool { return GigBatchLockU9.Ready() && this.Own("Issued")==1 && this.Own("Fault")==0 && this.OriginalLifetimeClosed() && this.LegacyIdle(); }
  public func Inspect() -> String {
    return "Pre-alpha phone: ready/revision/request/issued="+ToString(this.Own("Ready"))+"/"+ToString(this.Own("Revision"))+"/"+ToString(this.Own("Request"))+"/"+ToString(this.Own("Issued"))+" permit/fault="+ToString(this.Own("Permit"))+"/"+ToString(this.Own("Fault"))+" closed/legacyIdle/protocolIdle/livePhoneIdle="+ToString(this.OriginalLifetimeClosed())+"/"+ToString(this.LegacyIdle())+"/"+ToString(this.IdleProtocol())+"/"+ToString(this.LivePhoneIdle())+" | "+this.ProtocolStatus()+" | Eight original fixer controllers and native interrupt/reset service; historical counter differences do not block admission.";
  }
  public func Start(confirmation: String) -> String {
    if !GigBatchLockU9.Ready() { return "Refused: consolidated package unavailable; no request written."; }
    if !Equals(confirmation,"DISPOSABLE_SAVE") { return "Refused: DISPOSABLE_SAVE required."; }
    if this.Own("Request")!=0 || this.Own("Issued")!=0 { return "Already requested/issued; no restart. "+this.Inspect(); }
    if this.Own("Ready")!=1 || this.Own("Revision")!=2 || this.Own("Fault")!=0 || this.Own("Permit")!=0 { return "Refused: pre-alpha phone archive unavailable or interrupted request. "+this.Inspect(); }
    if !this.OriginalLifetimeClosed() || !this.LegacyIdle() || !this.IdleProtocol() || !this.LivePhoneIdle() { return "Waiting: completed Tower shutdown and idle phone with no legacy service required. "+this.Inspect(); }
    if !this.Set("Request",1) { this.Set("Fault",1);return "Owned request readback failed; no retry."; }
    return "Queued original fixer phone service. Close CET/menus and wait for issued=1. "+this.Inspect();
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch!=this.epoch { return; };this.Schedule();
    if this.Own("Request")!=1 || this.Own("Issued")!=0 { return; }
    let p=GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    let permit=GigBatchLockU9.Ready() && this.OriginalLifetimeClosed() && this.LegacyIdle() && this.IdleProtocol() && this.LivePhoneIdle() && this.Own("Fault")==0 && this.Own("Revision")==2 && IsDefined(p) && CyberwarePolicy.Safe(p) ? 1 : 0;
    if this.Own("Permit")!=permit && !this.Set("Permit",permit) { this.Set("Fault",1); }
  }
}
public class GigPhoneTickU9 extends DelayCallback {
  private let owner: wref<GigPhoneU9>;private let epoch: Int32;
  public static func Create(owner: ref<GigPhoneU9>,epoch: Int32) -> ref<GigPhoneTickU9> { let t=new GigPhoneTickU9();t.owner=owner;t.epoch=epoch;return t; }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}
@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void { wrappedMethod(gameInstance);let s=GameInstance.GetScriptableSystemsContainer(gameInstance).Get(n"PTFR.ActivityStateR3.GigPhoneU9") as GigPhoneU9;if IsDefined(s) { s.Restored(); } }
