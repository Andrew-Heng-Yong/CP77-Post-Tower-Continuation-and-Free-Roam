module PTFR.ActivityStateR3
import PTFR.RestrictionsR1.*
import PTFR.JohnnyVoiceJV1.*

// Development admission only. Original gig/phone/progression graphs perform
// gameplay. No native fact, reward, journal or historical snapshot writes here.
public class NativeHeywoodU8 extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private func OnAttach() -> Void { this.running=true;this.Restored(); }
  private func OnDetach() -> Void { this.running=false;this.epoch+=1; }
  public func Restored() -> Void { this.epoch+=1;if this.running { this.Schedule(); } }
  private func Schedule() -> Void { GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(NativeHeywoodTickU8.Create(this,this.epoch),1.0,false); }
  public static func IDs() -> array<String> { return ["sts_hey_gle_06","sts_hey_gle_04","sts_hey_spr_01","sts_hey_rey_08","sts_hey_gle_01","sts_hey_spr_03","sts_hey_spr_06"]; }
  private func Index(id: String) -> Int32 { let ids=NativeHeywoodU8.IDs();return ArrayContains(ids,id) ? GigDataB7.Index(id) : -1; }
  private func Fact(name: String) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(StringToName(name)); }
  private func Own(id: String,key: String) -> Int32 { return this.Fact("PTFRU8_"+id+"_"+key); }
  private func Set(id: String,key: String,value: Int32) -> Bool { let name="PTFRU8_"+id+"_"+key;GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(StringToName(name),value);return this.Fact(name)==value; }
  private func State(path: String,cls: String) -> Int32 { let jm=GameInstance.GetJournalManager(this.GetGameInstance());let e=jm.GetEntryByString(path,cls);return IsDefined(e) ? EnumInt(jm.GetEntryState(e)) : -1; }
  private func Root(i: Int32) -> Int32 { let p=GigDataB7.Paths(i);return this.State(p[0],"gameJournalQuest"); }
  private func Support() -> Bool {
    let s=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.JohnnyVoiceJV1.JohnnyVoiceJV1") as JohnnyVoiceJV1;
    return IsDefined(s) && s.CompletedTower() && this.Fact("PTFRU7_Support_Issued")==1 && this.Fact("PTFRU7_Support_Fault")==0;
  }
  private func LegacyIdle() -> Bool {
    if this.Fact("PTFRB7_hey_TierRequest")!=0 { return false; }
    if this.Fact("PTFRU4_Jeopardy_Request")!=0 && this.Fact("PTFRU4_Jeopardy_OwnerFinished")!=1 { return false; }
    let i=0;while i<GigDataB7.Count() {
      if Equals(GigDataB7.Region(i),"hey") {
        let tag=GigDataB7.Tag(i);
        if (this.Fact(tag+"_Queued")!=0 || this.Fact(tag+"_Request")!=0 || this.Fact(tag+"_Started")!=0) && this.Fact(tag+"_OwnerFinished")!=1 { return false; }
      };i+=1;
    };return true;
  }
  private func OldUnused(i: Int32) -> Bool {
    let tag=GigDataB7.Tag(i);let keys: array<String>=["Queued","Request","Permit","Started","OwnerFinished","Fault","CounterClaim","CounterAck"];
    let rewards=GigDataB7.Rewards(i);let achievements=GigDataB7.Achievements(i);let k=0;
    while k<ArraySize(rewards) { ArrayPush(keys,rewards[k]+"_Claim");ArrayPush(keys,rewards[k]+"_Ack");k+=1; }
    k=0;while k<ArraySize(achievements) { ArrayPush(keys,achievements[k]+"_Claim");ArrayPush(keys,achievements[k]+"_Ack");k+=1; }
    k=0;while k<ArraySize(keys) { if this.Fact(tag+"_"+keys[k])!=0 { return false; };k+=1; };return true;
  }
  private func Terminal(i: Int32) -> Bool {
    let names=GigDataB7.FinishedFacts(i);let k=0;while k<ArraySize(names) { if this.Fact(names[k])!=0 { return true; };k+=1; };return this.Root(i)==3;
  }
  private func EntrySafe(i: Int32) -> Bool {
    let paths=GigDataB7.Paths(i);let classes=GigDataB7.Classes(i);let k=0;
    while k<ArraySize(paths) { if this.State(paths[k],classes[k])!=1 { return false; };k+=1; }
    let facts=GigDataB7.Facts(i);k=0;while k<ArraySize(facts) { if this.Fact(facts[k])!=0 { return false; };k+=1; }
    let poi=this.State("points_of_interest/street_stories/"+GigDataB7.ID(i),"gameJournalPointOfInterestMappin");return poi==1 || poi==2;
  }
  private func MapTier(id: String) -> Bool {
    if Equals(id,"sts_hey_gle_06") || Equals(id,"sts_hey_gle_04") { return this.Fact("sts_hey_gle_tier_1_1")>0 || (this.Fact("sts_hey_gle_tier_1")>0 && this.Fact("sts_hey_gle_tier_1_1")==0); }
    if Equals(id,"sts_hey_spr_01") { return this.Fact("sts_hey_spr_tier_1_1")>0 || (this.Fact("sts_hey_spr_tier_1")>0 && this.Fact("sts_hey_spr_tier_1_1")==0); }
    if Equals(id,"sts_hey_rey_08") { return this.Fact("sts_hey_rey_tier_1_2")>0 || (this.Fact("sts_hey_rey_tier_1")>0 && this.Fact("sts_hey_rey_tier_1_1")==0); }
    if Equals(id,"sts_hey_gle_01") { return this.Fact("sts_hey_gle_tier_2")>0; }
    if Equals(id,"sts_hey_spr_03") { return this.Fact("sts_hey_spr_tier_2")>0; }
    return Equals(id,"sts_hey_spr_06") && this.Fact("sts_hey_spr_tier_4")>0;
  }
  private func TierSuffix(n: Int32) -> String { if n==4 { return "1_2"; };if n==7 { return "2"; };if n==10 { return "3"; };return "4"; }
  private func TierUntouched(n: Int32) -> Bool {
    let suffix=this.TierSuffix(n);
    if this.Fact("sts_hey_gle_tier_"+suffix)!=0 || this.Fact("sts_hey_rey_tier_"+suffix)!=0 || this.Fact("sts_hey_spr_tier_"+suffix)!=0 { return false; }
    if n==11 { return true; }
    let message=n==4 ? "001" : n==7 ? "002" : "003";
    return this.State("contacts/sebastian_padre_perez/padre_global_msg/new_sts_"+message,"gameJournalPhoneMessage")==1;
  }
  public func Inspect(id: String) -> String {
    let i=this.Index(id);if i<0 { return "Outside U8 seven-gig whitelist. Jeopardy remains U4/U7; no fallback."; }
    return "Native Heywood U8 "+GigDataB7.Title(i)+" ["+id+"]: ready/request/entered/finished="+ToString(this.Own(id,"Ready"))+"/"+ToString(this.Own(id,"Request"))+"/"+ToString(this.Own(id,"Started"))+"/"+ToString(this.Own(id,"OwnerFinished"))+" permit/fault="+ToString(this.Own(id,"Permit"))+"/"+ToString(this.Own(id,"Fault"))+" root="+ToString(this.Root(i))+" terminal="+ToString(this.Terminal(i))+" entrySafe="+ToString(this.EntrySafe(i))+" oldUnused="+ToString(this.OldUnused(i))+" support/legacyIdle="+ToString(this.Support())+"/"+ToString(this.LegacyIdle())+" nativeTier="+ToString(this.MapTier(id))+" mapEntered="+ToString(this.Own(id,"MapEntered"))+" creditDone="+ToString(this.Own(id,"CreditDone"))+" Heywood="+ToString(this.Fact("hey_sts_counter"))+" | DEVELOPMENT incomplete-as-unstarted, not certified history. Original gameplay/calls/rewards; Hot Merchandise has no connected stock fixer-credit branch.";
  }
  public func InspectAll() -> String { let ids=NativeHeywoodU8.IDs();let k=0;let out="";while k<ArraySize(ids) { out+=this.Inspect(ids[k])+"\n";k+=1; };return out; }
  public func Start(id: String,confirmation: String) -> String {
    if !Equals(confirmation,"DISPOSABLE_SAVE") { return "Refused: DISPOSABLE_SAVE required."; }
    let i=this.Index(id);if i<0 { return this.Inspect(id); }
    if this.Own(id,"Request")!=0 { return "Already requested; no restart. "+this.Inspect(id); }
    if this.Terminal(i) { return "Preserved completed/terminal gig. "+this.Inspect(id); }
    if !this.Support() || !this.LegacyIdle() { return "Deferred: requires existing U7 support and no unfinished legacy Heywood owner/tier service. "+this.Inspect(id); }
    if !this.EntrySafe(i) { return "Incomplete development candidate, but saved objective/fact state needs a continuation adapter; not reset. "+this.Inspect(id); }
    if !this.OldUnused(i) || this.Own(id,"Ready")!=1 || this.Own(id,"Revision")!=1 || this.Own(id,"Started")!=0 || this.Own(id,"OwnerFinished")!=0 || this.Own(id,"CreditDone")!=0 || this.Own(id,"MapEntered")!=0 || this.Own(id,"Fault")!=0 || this.Own(id,"Permit")!=0 { return "Refused: archive unavailable or an owner/ledger already used. "+this.Inspect(id); }
    if !this.Set(id,"Request",1) || !this.Set("Heywood","TierRequest",1) { this.Set(id,"Fault",1);return "Own request acknowledgement failed; no retry."; }
    return "Queued original gig; native tiers/approach still apply. "+this.Inspect(id);
  }
  public func StartAll(confirmation: String) -> String {
    if !Equals(confirmation,"DISPOSABLE_SAVE") { return "Refused: DISPOSABLE_SAVE required."; }
    let ids=NativeHeywoodU8.IDs();let k=0;let out="";while k<ArraySize(ids) { out+=this.Start(ids[k],confirmation)+"\n";k+=1; };return out;
  }
  public func TierStatus() -> String {
    let ns: array<Int32>=[4,7,10,11];let k=0;let out="Native U8 earned tiers; counter="+ToString(this.Fact("hey_sts_counter"));
    while k<ArraySize(ns) { let id="Tier"+ToString(ns[k]);out+=" | "+id+" entered/done="+ToString(this.Own(id,"Entered"))+"/"+ToString(this.Own(id,"Done"))+" untouched="+ToString(this.TierUntouched(ns[k]));k+=1; };return out+" | Native thresholds retained; excluded gigs do not receive synthetic credit. Final fixer reward not restored here.";
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch!=this.epoch { return; };this.Schedule();
    let p=GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    let safe=this.Support() && this.LegacyIdle() && IsDefined(p) && CyberwarePolicy.Safe(p);
    let ids=NativeHeywoodU8.IDs();let k=0;
    while k<ArraySize(ids) { let id=ids[k];let i=this.Index(id);
      if i>=0 && this.Own(id,"Request")==1 && this.Own(id,"Started")==0 {
        let permit=safe && this.Own(id,"Fault")==0 && this.OldUnused(i) && this.EntrySafe(i) ? 1 : 0;
        if this.Own(id,"Permit")!=permit && !this.Set(id,"Permit",permit) { this.Set(id,"Fault",1); }
      }
      if i>=0 && this.Own(id,"Request")==1 && this.Own(id,"MapEntered")==0 {
        let mapPermit=safe && this.Own(id,"Fault")==0 && this.OldUnused(i) && this.Root(i)==1 && !this.Terminal(i) && this.MapTier(id) ? 1 : 0;
        if this.Own(id,"MapPermit")!=mapPermit && !this.Set(id,"MapPermit",mapPermit) { this.Set(id,"Fault",1); }
      };k+=1;
    }
    let ns: array<Int32>=[4,7,10,11];k=0;
    while k<ArraySize(ns) { let id="Tier"+ToString(ns[k]);
      if this.Own("Heywood","TierRequest")==1 && this.Own(id,"Entered")==0 {
        let permit=safe && this.TierUntouched(ns[k]) ? 1 : 0;
        if this.Own(id,"Permit")!=permit { this.Set(id,"Permit",permit); }
      };k+=1;
    }
  }
}
public class NativeHeywoodTickU8 extends DelayCallback {
  private let owner: wref<NativeHeywoodU8>;private let epoch: Int32;
  public static func Create(owner: ref<NativeHeywoodU8>,epoch: Int32) -> ref<NativeHeywoodTickU8> { let t=new NativeHeywoodTickU8();t.owner=owner;t.epoch=epoch;return t; }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}
@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void { wrappedMethod(gameInstance);let s=GameInstance.GetScriptableSystemsContainer(gameInstance).Get(n"PTFR.ActivityStateR3.NativeHeywoodU8") as NativeHeywoodU8;if IsDefined(s) { s.Restored(); } }
