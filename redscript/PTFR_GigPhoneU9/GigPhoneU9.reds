module PTFR.ActivityStateR3
import PTFR.RestrictionsR1.*
import PTFR.JohnnyVoiceJV1.*

// Admission only. One stock initializer owns all eight fixer controllers and
// its original shared interrupt/reset lifetime. No native protocol writes here.
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
    // U6/U7 own persistent phone services, not finite gigs: even a completed gig
    // does not make their phone owner available for a second initializer.
    if !this.AllZero(GigPhoneDataU9.PredecessorFacts()) { return false; }
    let tags: array<String>=["PTFRU1_Shark_","PTFRU4_Jeopardy_","PTFRG1_","PTFRG2_","PTFRG3_","PTFRB5_H7_","PTFRB5_H1_","PTFRB6_J2_"];
    let k=0;while k<ArraySize(tags) { if this.OldOwnerBusy(tags[k]) { return false; };k+=1; }
    let i=0;while i<GigDataB7.Count() { if this.OldOwnerBusy(GigDataB7.Tag(i)+"_") || this.OldOwnerBusy("PTFRU8_"+GigDataB7.ID(i)+"_") { return false; };i+=1; }
    return true;
  }
  private func IdleProtocol() -> Bool {
    if !this.AllZero(GigPhoneDataU9.IdleFacts()) { return false; }
    let starts=GigPhoneDataU9.BalanceStarts();let ends=GigPhoneDataU9.BalanceEnds();let k=0;
    while k<ArraySize(starts) { if this.Fact(starts[k])!=this.Fact(ends[k]) { return false; };k+=1; };return true;
  }
  public func Supported() -> Bool { return GigBatchLockU9.Ready() && this.Own("Issued")==1 && this.Own("Fault")==0 && this.OriginalLifetimeClosed() && this.LegacyIdle(); }
  public func Inspect() -> String {
    return "Gig phone U9: ready/request/issued="+ToString(this.Own("Ready"))+"/"+ToString(this.Own("Request"))+"/"+ToString(this.Own("Issued"))+" permit/fault="+ToString(this.Own("Permit"))+"/"+ToString(this.Own("Fault"))+" closed/legacyIdle/phoneIdle="+ToString(this.OriginalLifetimeClosed())+"/"+ToString(this.LegacyIdle())+"/"+ToString(this.IdleProtocol())+" | Eight original fixer controllers; one native interrupt/reset service. Issued is not audible-call proof. Existing U6/U7 saved services require pre-service save, not migration.";
  }
  public func Start(confirmation: String) -> String {
    if !GigBatchLockU9.Ready() { return "Refused: U9 CET entry interlocks not ready. Check installed U9 files and CET log; no request written."; }
    if !Equals(confirmation,"DISPOSABLE_SAVE") { return "Refused: DISPOSABLE_SAVE required."; }
    if this.Own("Request")!=0 || this.Own("Issued")!=0 { return "Already requested/issued; no restart. "+this.Inspect(); }
    if this.Own("Ready")!=1 || this.Own("Revision")!=1 || this.Own("Fault")!=0 || this.Own("Permit")!=0 { return "Refused: archive unavailable or interrupted request. "+this.Inspect(); }
    if !this.OriginalLifetimeClosed() || !this.LegacyIdle() || !this.IdleProtocol() { return "Refused: requires pre-U6/U7 idle post-Tower baseline and no pending legacy owners; no controller migration/reset. "+this.Inspect(); }
    if !this.Set("Request",1) { this.Set("Fault",1);return "Owned request readback failed; no retry."; }
    return "Queued original fixer phone service. Close CET/menus, holster and wait for issued=1 before approaching gigs. "+this.Inspect();
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch!=this.epoch { return; };this.Schedule();
    if this.Own("Request")!=1 || this.Own("Issued")!=0 { return; }
    let p=GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    let phone=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PhoneSystem") as PhoneSystem;
    let permit=GigBatchLockU9.Ready() && this.OriginalLifetimeClosed() && this.LegacyIdle() && this.IdleProtocol() && this.Own("Fault")==0 && IsDefined(p) && CyberwarePolicy.Safe(p) && IsDefined(phone) && phone.IsPhoneEnabled() && phone.IsCallingEnabled() && !GameInstance.GetPhoneManager(this.GetGameInstance()).IsPhoneCallActive() ? 1 : 0;
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
