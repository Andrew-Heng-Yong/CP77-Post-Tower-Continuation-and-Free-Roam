module PTFR.ActivityStateR3
import PTFR.ActivityStateR3.*
import PTFR.RestrictionsR1.*
import PTFR.JohnnyVoiceJV1.*
import PTFR.GigPilotR1.*
import PTFR.RiteG2.*

// Experimental single entry into ORIGINAL Shark resources. No payout, journal,
// stock-fact, tier or completion repair. Facts below belong only to this trial.
public class NativeReuseU1 extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private func OnAttach() -> Void { this.running=true;this.Restored(); }
  private func OnDetach() -> Void { this.running=false;this.epoch+=1; }
  public func Restored() -> Void { this.epoch+=1;if this.running { this.Schedule(); } }
  private func Schedule() -> Void { GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(NativeReuseTickU1.Create(this,this.epoch),1.0,false); }
  private func Fact(s: String) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(StringToName(s)); }
  private func Own(s: String) -> Int32 { return this.Fact("PTFRU1_Shark_"+s); }
  private func Set(s: String,v: Int32) -> Bool { GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(StringToName("PTFRU1_Shark_"+s),v);return this.Own(s)==v; }
  private func Index() -> Int32 { return GigDataB7.Index("sts_wat_kab_06"); }
  private func State(path: String,cls: String) -> Int32 { let jm=GameInstance.GetJournalManager(this.GetGameInstance());let e=jm.GetEntryByString(path,cls);return IsDefined(e) ? EnumInt(jm.GetEntryState(e)) : -1; }
  private func Tower() -> Bool { let s=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.JohnnyVoiceJV1.JohnnyVoiceJV1") as JohnnyVoiceJV1;return IsDefined(s) && s.CompletedTower(); }
  private func Fresh() -> Bool {
    let i=this.Index();if i<0 { return false; };let paths=GigDataB7.Paths(i);let classes=GigDataB7.Classes(i);let k=0;
    while k<ArraySize(paths) { if this.State(paths[k],classes[k])!=1 { return false; };k+=1; }
    let facts=GigDataB7.Facts(i);k=0;while k<ArraySize(facts) { if this.Fact(facts[k])!=0 { return false; };k+=1; }
    let poi=this.State("points_of_interest/street_stories/sts_wat_kab_06","gameJournalPointOfInterestMappin");return poi==1 || poi==2;
  }
  private func OldUnused() -> Bool {
    let keys: array<String>=["Queued","Request","Permit","Started","OwnerFinished","Fault","CounterClaim","CounterAck","CountBase","Reward0_Claim","Reward0_Ack","Reward1_Claim","Reward1_Ack","Achievement0_Claim","Achievement0_Ack"];
    let k=0;while k<ArraySize(keys) { if this.Fact("PTFRB7_wat_kab_06_"+keys[k])!=0 { return false; };k+=1; };return true;
  }
  private func WatsonIdle() -> Bool {
    let c=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance());let g1=c.Get(n"PTFR.GigPilotR1.GigPilotR1") as GigPilotR1;let g2=c.Get(n"PTFR.RiteG2.RiteG2") as RiteG2;
    if !IsDefined(g1) || !IsDefined(g2) || g1.WatsonAccountBusy() || g2.WatsonAccountBusy() { return false; }
    let i=0;while i<GigDataB7.Count() { if Equals(GigDataB7.Region(i),"wat") { let tag=GigDataB7.Tag(i);if this.Fact(tag+"_Queued")!=0 && this.Fact(tag+"_OwnerFinished")!=1 { return false; } };i+=1; };return true;
  }
  public func Inspect() -> String {
    return "Native reuse U1 Shark: ready/request/entered/finished="+ToString(this.Own("Ready"))+"/"+ToString(this.Own("Request"))+"/"+ToString(this.Own("Started"))+"/"+ToString(this.Own("OwnerFinished"))+" permit="+ToString(this.Own("Permit"))+" fault="+ToString(this.Own("Fault"))+" tower="+ToString(this.Tower())+" fresh="+ToString(this.Fresh())+" oldUnused="+ToString(this.OldUnused())+" WatsonIdle="+ToString(this.WatsonIdle())+" root="+ToString(this.State("quests/street_stories/watson/kabuki/sts_wat_kab_06","gameJournalQuest"))+" nativeStart/finished/failed="+ToString(this.Fact("kab_06_start"))+"/"+ToString(this.Fact("kab_06_finished"))+"/"+ToString(this.Fact("sts_wat_kab_06_failed"))+" counterBase/current="+ToString(this.Own("CountBase"))+"/"+ToString(this.Fact("wat_sts_counter"))+" achievementBase/current="+ToString(this.Own("AchBase"))+"/"+ToString(this.Fact("wat_achievement"))+" | Original phases/calls/rewards; no custom payout acknowledgement or fixer-credit repair.";
  }
  public func TierStatus() -> String { return "Native Shark tiers 1/1_1/1_4="+ToString(this.Fact("sts_wat_kab_tier_1"))+"/"+ToString(this.Fact("sts_wat_kab_tier_1_1"))+"/"+ToString(this.Fact("sts_wat_kab_tier_1_4"))+". Prelude permits tier_1_4>0 OR (tier_1>0 AND tier_1_1==0); no forcing."; }
  public func Start(confirmation: String) -> String {
    if !Equals(confirmation,"DISPOSABLE_SAVE") { return "Refused: DISPOSABLE_SAVE required."; }
    if !this.Tower() || this.Own("Ready")!=1 || this.Own("Revision")!=1 { return "Refused: completed Tower and U1 archive ready required. "+this.Inspect(); }
    if this.Own("Request")!=0 { return "Already requested; no restart. "+this.Inspect(); }
    if !this.OldUnused() || !this.Fresh() || !this.WatsonIdle() { return "Refused: use a post-Tower snapshot BEFORE the B7 batch/Shark request; no prior Shark state or competing Watson owner. "+this.Inspect(); }
    if this.Own("Started")!=0 || this.Own("OwnerFinished")!=0 || this.Own("Fault")!=0 || this.Own("Permit")!=0 { return "Refused: interrupted/used trial; no restart. "+this.Inspect(); }
    if !this.Set("CountBase",this.Fact("wat_sts_counter")) || !this.Set("AchBase",this.Fact("wat_achievement")) || !this.Set("Request",1) { this.Set("Fault",1);return "Request readback failure; do not retry."; }
    return "Queued ORIGINAL Shark phase; close CET/menus, holster and stay outside encounter. "+this.Inspect();
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch!=this.epoch { return; };this.Schedule();
    if this.Own("Request")!=1 || this.Own("Started")!=0 { return; }
    let p=GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    let permit=this.Tower() && this.Own("Fault")==0 && this.OldUnused() && this.Fresh() && this.WatsonIdle() && IsDefined(p) && CyberwarePolicy.Safe(p) ? 1 : 0;
    if this.Own("Permit")!=permit && !this.Set("Permit",permit) { this.Set("Fault",1); }
  }
}
public class NativeReuseTickU1 extends DelayCallback {
  private let owner: wref<NativeReuseU1>;private let epoch: Int32;
  public static func Create(owner: ref<NativeReuseU1>,epoch: Int32) -> ref<NativeReuseTickU1> { let t=new NativeReuseTickU1();t.owner=owner;t.epoch=epoch;return t; }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}
@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void { wrappedMethod(gameInstance);let s=GameInstance.GetScriptableSystemsContainer(gameInstance).Get(n"PTFR.ActivityStateR3.NativeReuseU1") as NativeReuseU1;if IsDefined(s) { s.Restored(); } }
