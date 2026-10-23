module PTFR.ActivityStateR3
import PTFR.RestrictionsR1.*
import PTFR.JohnnyVoiceJV1.*

// Admission/bookkeeping only. The original stock graph performs all gameplay,
// calls, rewards, credit, tiers and cleanup. PA1 connects actual captured history.
// The explicit development route remains separate from that certificate.
public class NativeGigsU9 extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private func OnAttach() -> Void { this.running=true;this.Restored(); }
  private func OnDetach() -> Void { this.running=false;this.epoch+=1; }
  public func Restored() -> Void { this.epoch+=1;if this.running { this.Schedule(); } }
  private func Schedule() -> Void { GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(NativeGigsTickU9.Create(this,this.epoch),1.0,false); }
  public static func IDs() -> array<String> { return NativeGigDataU9.IDs(); }
  private func Fact(s: String) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(StringToName(s)); }
  private func Own(id: String,key: String) -> Int32 { return this.Fact("PTFRU9_"+id+"_"+key); }
  private func Set(id: String,key: String,v: Int32) -> Bool { let name="PTFRU9_"+id+"_"+key;GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(StringToName(name),v);return this.Fact(name)==v; }
  private func State(path: String,cls: String) -> Int32 { let jm=GameInstance.GetJournalManager(this.GetGameInstance());let e=jm.GetEntryByString(path,cls);return IsDefined(e) ? EnumInt(jm.GetEntryState(e)) : -1; }
  private func Root(i: Int32) -> Int32 { let a=NativeGigDataU9.Paths(i);return ArraySize(a)>0 ? this.State(a[0],"gameJournalQuest") : -1; }
  private func Tower() -> Bool { let s=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.JohnnyVoiceJV1.JohnnyVoiceJV1") as JohnnyVoiceJV1;return IsDefined(s) && s.CompletedTower(); }
  private func Support() -> Bool { let s=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.ActivityStateR3.GigPhoneU9") as GigPhoneU9;return IsDefined(s) && s.Supported(); }
  private func RetaliationCommonAdmissible() -> Bool {
    return this.Own("Retaliation","Ready")==1 && this.Own("Retaliation","Fault")==0 && (this.Own("Retaliation","Issued")==1 || (this.Own("Retaliation","Issued")==0 && this.Fact("sts_gang_retaliation_cancel")==0 && this.Fact("mws_chase_active")==0));
  }
  private func RetaliationAdmissible(gang: String) -> Bool { let id="Retaliation_"+gang;return this.RetaliationCommonAdmissible() && this.Own(id,"Fault")==0 && (this.Own(id,"Issued")==1 || (this.Own(id,"Issued")==0 && this.Fact("sts_"+gang+"_retaliation")==0)); }
  public func DependencyStatus() -> String {
    let out="Native U9 retaliation common ready/request/permit/issued/fault="+ToString(this.Own("Retaliation","Ready"))+"/"+ToString(this.Own("Retaliation","Request"))+"/"+ToString(this.Own("Retaliation","Permit"))+"/"+ToString(this.Own("Retaliation","Issued"))+"/"+ToString(this.Own("Retaliation","Fault"));
    let gangs: array<String>=["wraiths","6thstreet","animals","valentinos","maelstroms","tygerclaws"];let k=0;
    while k<ArraySize(gangs) { let id="Retaliation_"+gangs[k];out+="\n"+gangs[k]+" request/permit/issued/fault="+ToString(this.Own(id,"Request"))+"/"+ToString(this.Own(id,"Permit"))+"/"+ToString(this.Own(id,"Issued"))+"/"+ToString(this.Own(id,"Fault"))+" nativePending="+ToString(this.Fact("sts_"+gangs[k]+"_retaliation"));k+=1; };return out+" | Stock selectors require a new owned U9 gig. Historical pending gangs are untouched; other empty gangs can run.";
  }
  private func Terminal(i: Int32) -> Bool {
    let a=NativeGigDataU9.TerminalFacts(i);let k=0;while k<ArraySize(a) { if this.Fact(a[k])!=0 { return true; };k+=1; };return this.Root(i)==3;
  }
  private func EntrySafe(i: Int32) -> Bool {
    let paths=NativeGigDataU9.Paths(i);let classes=NativeGigDataU9.Classes(i);let k=0;
    if ArraySize(paths)==0 || ArraySize(paths)!=ArraySize(classes) { return false; }
    while k<ArraySize(paths) { if this.State(paths[k],classes[k])!=1 { return false; };k+=1; }
    let a=NativeGigDataU9.Facts(i);k=0;while k<ArraySize(a) { if this.Fact(a[k])!=0 { return false; };k+=1; }
    let prefix=Equals(NativeGigDataU9.Region(i),"ep1") ? "ep1/points_of_interest/street_stories/" : "points_of_interest/street_stories/";
    let poi=this.State(prefix+NativeGigDataU9.ID(i),"gameJournalPointOfInterestMappin");return poi==1 || poi==2;
  }
  private func OldUnused(i: Int32) -> Bool {
    let tags=NativeGigDataU9.LegacyTags(i);let keys: array<String>=["Queued","Request","Permit","Started","OwnerFinished","Fault","CounterClaim","CounterAck","RewardClaim","RewardAck","AccountClaim","AccountAck"];
    let k=0;let j=0;while k<ArraySize(tags) { j=0;while j<ArraySize(keys) { if this.Fact(tags[k]+"_"+keys[j])!=0 { return false; };j+=1; };k+=1; }
    let a=NativeGigDataU9.LegacyOwnerFacts(i);k=0;while k<ArraySize(a) { if this.Fact(a[k])!=0 { return false; };k+=1; };return true;
  }
  private func LegacyIdle() -> Bool {
    let a: array<String>=["PTFRU6_Padre_Request","PTFRU6_Padre_Issued","PTFRU7_Support_Request","PTFRU7_Support_Issued","PTFRU4_Jeopardy_Request","PTFRU4_Jeopardy_Started","PTFRU1_Shark_Request","PTFRU1_Shark_Started","PTFRB5_TierRequest","PTFRU8_Heywood_TierRequest"];
    let k=0;while k<ArraySize(a) { if this.Fact(a[k])!=0 { return false; };k+=1; }
    let regions: array<String>=["wat","wbr","hey","cct","std","bls","pac"];
    k=0;while k<ArraySize(regions) { if this.Fact("PTFRB7_"+regions[k]+"_TierRequest")!=0 { return false; };k+=1; }
    k=0;while k<NativeGigDataU9.Count() {
      let id=NativeGigDataU9.ID(k);if this.Fact("PTFRU8_"+id+"_Request")!=0 { return false; }
      let tags=NativeGigDataU9.LegacyTags(k);let j=0;
      while j<ArraySize(tags) {
        if (this.Fact(tags[j]+"_Queued")!=0 || this.Fact(tags[j]+"_Request")!=0 || this.Fact(tags[j]+"_Started")!=0) && this.Fact(tags[j]+"_OwnerFinished")!=1 { return false; };j+=1;
      };k+=1;
    };return true;
  }
  private func TierUntouched(i: Int32) -> Bool {
    let a=NativeGigDataU9.TierFacts(i);let k=0;while k<ArraySize(a) { if this.Fact(a[k])!=0 { return false; };k+=1; }
    a=NativeGigDataU9.TierMessages(i);k=0;while k<ArraySize(a) { if this.State(a[k],"gameJournalPhoneMessage")!=1 { return false; };k+=1; };return true;
  }
  private func HistoryLabel(id: String) -> String {
    let history=PreAlphaEntry.Get(this.GetGameInstance());
    return IsDefined(history) && history.Certified(id) ? "Certified actual pre-Tower unstarted history." : "DEVELOPMENT incomplete-as-unstarted; no certified history.";
  }
  public func Inspect(id: String) -> String {
    let i=NativeGigDataU9.Index(id);if i<0 { return "No staged U9 original owner for "+id+"; no fallback or history invention."; }
    return "Native U9 "+NativeGigDataU9.Title(i)+" ["+id+"]: ready/request/parentEntered/mainEntered/mainFinished/cleanupFinished="+ToString(this.Own(id,"Ready"))+"/"+ToString(this.Own(id,"Request"))+"/"+ToString(this.Own(id,"ParentEntered"))+"/"+ToString(this.Own(id,"Started"))+"/"+ToString(this.Own(id,"MainFinished"))+"/"+ToString(this.Own(id,"OwnerFinished"))+" permit/fault="+ToString(this.Own(id,"Permit"))+"/"+ToString(this.Own(id,"Fault"))+" root="+ToString(this.Root(i))+" terminal="+ToString(this.Terminal(i))+" entrySafe="+ToString(this.EntrySafe(i))+" oldUnused="+ToString(this.OldUnused(i))+" support/legacyIdle="+ToString(this.Support())+"/"+ToString(this.LegacyIdle())+" creditDone="+ToString(this.Own(id,"CreditDone"))+" "+NativeGigDataU9.Counter(i)+"="+ToString(this.Fact(NativeGigDataU9.Counter(i)))+" | "+this.HistoryLabel(id)+" Original parent/main/calls/rewards. Parent entry does not prove approach, briefing or live completion.";
  }
  public func InspectAll() -> String { let a=NativeGigsU9.IDs();let k=0;let out="";while k<ArraySize(a) { out+=this.Inspect(a[k])+"\n";k+=1; };return out; }
  public func Start(id: String,confirmation: String) -> String { return this.Request(id,confirmation,false); }
  private func Request(id: String,confirmation: String,certified: Bool) -> String {
    if certified { let history=PreAlphaEntry.Get(this.GetGameInstance());if !IsDefined(history) || !history.Certified(id) { return "Refused: no actual captured unstarted history. "+this.Inspect(id); } }
    if !GigBatchLockU9.Ready() { return "Consolidated PA1 package readiness unavailable."; }
    if !Equals(confirmation,"DISPOSABLE_SAVE") { return "Refused: DISPOSABLE_SAVE required."; }
    let i=NativeGigDataU9.Index(id);if i<0 { return this.Inspect(id); }
    if this.Own(id,"Request")!=0 { return "Already requested; no restart. "+this.Inspect(id); }
    if this.Terminal(i) { return "Preserved completed/terminal gig. "+this.Inspect(id); }
    if !this.Tower() || !this.LegacyIdle() { return "Refused: completed Tower and clean owner state required; load the selected clean pre-alpha fixture. "+this.Inspect(id); }
    if !this.EntrySafe(i) { return "Incomplete development candidate, but existing objective/fact state cannot be restarted safely; no reset. "+this.Inspect(id); }
    if !this.OldUnused(i) || this.Own(id,"Ready")!=1 || this.Own(id,"Revision")!=1 || this.Own(id,"ParentEntered")!=0 || this.Own(id,"Started")!=0 || this.Own(id,"OwnerFinished")!=0 || this.Own(id,"Fault")!=0 || this.Own(id,"CreditDone")!=0 { return "Refused: archive unavailable or owner already used. "+this.Inspect(id); }
    let gang=NativeGigDataU9.RetaliationGang(i);
    if NativeGigDataU9.NeedsRetaliation(i) && !this.RetaliationAdmissible(gang) { return "Refused: native consequence service unavailable or historical retaliation/chase pending for "+gang+"; nothing reset. "+this.DependencyStatus(); }
    let phone=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.ActivityStateR3.GigPhoneU9") as GigPhoneU9;
    if !IsDefined(phone) { return "Refused: U9 original phone support unavailable."; }
    phone.Start(confirmation);
    if this.Fact("PTFRU9_Support_Request")!=1 || this.Fact("PTFRU9_Support_Fault")!=0 { return "Phone support refused; no gig request. "+phone.Inspect(); }
    if NativeGigDataU9.NeedsRetaliation(i) {
      if !this.Set("Retaliation","Request",1) || !this.Set("Retaliation_"+gang,"Request",1) { this.Set("Retaliation","Fault",1);return "Native consequence request acknowledgement failed; no gig request."; }
    }
    if !this.Set(id,"Request",1) || !this.Set(NativeGigDataU9.Region(i),"TierRequest",1) { this.Set(id,"Fault",1);return "Own request acknowledgement failed; no retry."; }
    return "Queued original parent; support/native tiers/approach still apply. "+this.Inspect(id);
  }
  public func StartAll(confirmation: String) -> String { if !Equals(confirmation,"DISPOSABLE_SAVE") { return "Refused: DISPOSABLE_SAVE required."; };let a=NativeGigsU9.IDs();let k=0;let out="";while k<ArraySize(a) { out+=this.Start(a[k],confirmation)+"\n";k+=1; };return out; }
  public func RestoreCertified(id: String) -> String { return this.Request(id,"DISPOSABLE_SAVE",true); }
  public func TierStatus() -> String { let k=0;let out="Original U9 earned tiers; no forced counter/tiers/final reward.";while k<NativeGigDataU9.TierCount() { let id=NativeGigDataU9.TierID(k);out+="\n"+id+" entered/done="+ToString(this.Own(id,"Entered"))+"/"+ToString(this.Own(id,"Done"))+" untouched="+ToString(this.TierUntouched(k));k+=1; };return out; }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch!=this.epoch { return; };this.Schedule();
    let p=GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    let safe=GigBatchLockU9.Ready() && this.Tower() && this.Support() && this.LegacyIdle() && IsDefined(p) && CyberwarePolicy.Safe(p);let k=0;
    if this.Own("Retaliation","Request")==1 && this.Own("Retaliation","Issued")==0 {
      let permit=safe && this.RetaliationCommonAdmissible() ? 1 : 0;
      if this.Own("Retaliation","Permit")!=permit && !this.Set("Retaliation","Permit",permit) { this.Set("Retaliation","Fault",1); }
    }
    let gangs: array<String>=["wraiths","6thstreet","animals","valentinos","maelstroms","tygerclaws"];
    while k<ArraySize(gangs) { let id="Retaliation_"+gangs[k];
      if this.Own(id,"Request")==1 && this.Own(id,"Issued")==0 {
        let permit=safe && this.Own("Retaliation","Issued")==1 && this.RetaliationAdmissible(gangs[k]) ? 1 : 0;
        if this.Own(id,"Permit")!=permit && !this.Set(id,"Permit",permit) { this.Set(id,"Fault",1); }
      };k+=1;
    };k=0;
    while k<NativeGigDataU9.Count() {
      let id=NativeGigDataU9.ID(k);
      if this.Own(id,"Request")==1 && this.Own(id,"ParentEntered")==0 {
        let gangID="Retaliation_"+NativeGigDataU9.RetaliationGang(k);
        let consequenceReady=!NativeGigDataU9.NeedsRetaliation(k) || (this.Own("Retaliation","Issued")==1 && this.Own("Retaliation","Fault")==0 && this.Own(gangID,"Issued")==1 && this.Own(gangID,"Fault")==0);
        let permit=safe && consequenceReady && this.Own(id,"Fault")==0 && this.OldUnused(k) && this.EntrySafe(k) ? 1 : 0;
        if this.Own(id,"Permit")!=permit && !this.Set(id,"Permit",permit) { this.Set(id,"Fault",1); }
      }
      if this.Own(id,"Request")==1 && this.Own(id,"Started")==1 {
        let mapPermit=safe && this.Root(k)==1 && !this.Terminal(k) && this.Own(id,"Fault")==0 ? 1 : 0;
        if this.Own(id,"MapPermit")!=mapPermit { this.Set(id,"MapPermit",mapPermit); }
      };k+=1;
    }
    k=0;while k<NativeGigDataU9.TierCount() { let id=NativeGigDataU9.TierID(k);
      if this.Own(NativeGigDataU9.TierRegion(k),"TierRequest")==1 && this.Own(id,"Entered")==0 {
        let permit=safe && this.TierUntouched(k) ? 1 : 0;if this.Own(id,"Permit")!=permit { this.Set(id,"Permit",permit); }
      };k+=1;
    }
  }
}
public class NativeGigsTickU9 extends DelayCallback {
  private let owner: wref<NativeGigsU9>;private let epoch: Int32;
  public static func Create(owner: ref<NativeGigsU9>,epoch: Int32) -> ref<NativeGigsTickU9> { let t=new NativeGigsTickU9();t.owner=owner;t.epoch=epoch;return t; }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}
@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void { wrappedMethod(gameInstance);let s=GameInstance.GetScriptableSystemsContainer(gameInstance).Get(n"PTFR.ActivityStateR3.NativeGigsU9") as NativeGigsU9;if IsDefined(s) { s.Restored(); } }

