module PTFR.ActivityStateR3
import PTFR.RestrictionsR1.*
import PTFR.JohnnyVoiceJV1.*
import PTFR.GigPilotR1.*
import PTFR.RiteG2.*

// Saved progress lives in per-owner quest facts, not a resizable script slot
// array. Loading a save never fabricates history or reissues an existing owner.
public class GigFamilyB7 extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let warmup: Int32;
  private let autoCursor: Int32;
  private func OnAttach() -> Void { this.running=true;this.Restored(); }
  private func OnDetach() -> Void { this.running=false;this.epoch+=1; }
  public func Restored() -> Void { this.epoch+=1;this.warmup=5;this.autoCursor=0;if this.running { this.Schedule(); } }
  private func Schedule() -> Void { GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(GigTickB7.Create(this,this.epoch),1.0,false); }
  private func Fact(name: String) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(StringToName(name)); }
  private func Set(name: String,value: Int32) -> Bool { GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(StringToName(name),value);return this.Fact(name)==value; }
  private func Own(i: Int32,suffix: String) -> Int32 { return this.Fact(GigDataB7.Tag(i)+"_"+suffix); }
  private func Write(i: Int32,suffix: String,value: Int32) -> Bool { return this.Set(GigDataB7.Tag(i)+"_"+suffix,value); }
  private func State(path: String,cls: String) -> Int32 { let jm=GameInstance.GetJournalManager(this.GetGameInstance());let e=jm.GetEntryByString(path,cls);return IsDefined(e) ? EnumInt(jm.GetEntryState(e)) : -1; }
  private func Root(i: Int32) -> Int32 { let paths=GigDataB7.Paths(i);return this.State(paths[0],"gameJournalQuest"); }
  private func Tower() -> Bool { let s=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.JohnnyVoiceJV1.JohnnyVoiceJV1") as JohnnyVoiceJV1;return IsDefined(s) && s.CompletedTower(); }
  private func Fresh(i: Int32) -> Bool {
    let paths=GigDataB7.Paths(i);let classes=GigDataB7.Classes(i);let k=0;
    while k<ArraySize(paths) { if this.State(paths[k],classes[k])!=1 { return false; };k+=1; }
    let facts=GigDataB7.Facts(i);k=0;while k<ArraySize(facts) { if this.Fact(facts[k])!=0 { return false; };k+=1; }
    let poi=this.State("points_of_interest/street_stories/"+GigDataB7.ID(i),"gameJournalPointOfInterestMappin");return poi==1 || poi==2;
  }
  private func Unused(i: Int32) -> Bool {
    let keys: array<String>=["Queued","Request","Started","OwnerFinished","Fault","CounterClaim","CounterAck","CountBase"];
    let rewards=GigDataB7.Rewards(i);let achievements=GigDataB7.Achievements(i);let k=0;
    while k<ArraySize(rewards) { ArrayPush(keys,rewards[k]+"_Claim");ArrayPush(keys,rewards[k]+"_Ack");k+=1; }
    k=0;while k<ArraySize(achievements) { ArrayPush(keys,achievements[k]+"_Claim");ArrayPush(keys,achievements[k]+"_Ack");k+=1; }
    k=0;while k<ArraySize(keys) { if this.Own(i,keys[k])!=0 { return false; };k+=1; };return true;
  }
  private func LegacyIdle(region: String) -> Bool {
    if Equals(region,"wat") {
      let g1=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.GigPilotR1.GigPilotR1") as GigPilotR1;
      let g2=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.RiteG2.RiteG2") as RiteG2;
      if !IsDefined(g1) || !IsDefined(g2) || g1.WatsonAccountBusy() || g2.WatsonAccountBusy() { return false; }
    }
    let tags: array<String>;
    if Equals(region,"bls") { tags=["PTFRG3"]; }
    if Equals(region,"wbr") { tags=["PTFRB5_H7","PTFRB5_H1","PTFRB6_J2"]; }
    let k=0;while k<ArraySize(tags) { if this.Fact(tags[k]+"_Request")!=0 && this.Fact(tags[k]+"_OwnerFinished")!=1 { return false; };k+=1; };return true;
  }
  public func IDs() -> array<String> { return GigDataB7.Selected(); }
  public func Coverage() -> String { return "B7: "+ToString(GigDataB7.Count())+" new fresh + 6 existing gig adapters; "+ToString(66-GigDataB7.Count())+" exceptional adapters pending. Completed/failed gigs preserved; native tiers may defer requests."; }
  public func Implemented(id: String) -> Bool { return GigDataB7.Index(id)>=0; }
  public func Inspect(id: String) -> String {
    let i=GigDataB7.Index(id);if i<0 { return "PENDING_ADAPTER "+id+": "+GigDataB7.Pending(id); }
    let phase=this.Own(i,"Fault")!=0 ? "FAULT: no resend" : this.Own(i,"OwnerFinished")==1 ? "native cleanup finished" : this.Own(i,"Started")==1 ? "native owner running; approach location" : this.Own(i,"Request")==1 ? "waiting for native tier/prelude" : this.Own(i,"Queued")==1 ? "queued; waiting for safe/shared-owner idle" : "unused";
    return "Family B7 "+GigDataB7.Title(i)+" ["+id+"]: "+phase+" | ready/queued/request/started/finished="+ToString(this.Own(i,"Ready"))+"/"+ToString(this.Own(i,"Queued"))+"/"+ToString(this.Own(i,"Request"))+"/"+ToString(this.Own(i,"Started"))+"/"+ToString(this.Own(i,"OwnerFinished"))+" root="+ToString(this.Root(i))+" counterClaim/Ack="+ToString(this.Own(i,"CounterClaim"))+"/"+ToString(this.Own(i,"CounterAck"))+" base/current="+ToString(this.Own(i,"CountBase"))+"/"+ToString(this.Fact(GigDataB7.Region(i)+"_sts_counter"))+" fault="+ToString(this.Own(i,"Fault"));
  }
  public func Restore(id: String,overrideHistory: Bool) -> String {
    let i=GigDataB7.Index(id);if i<0 { return this.Inspect(id); }
    if !this.Tower() { return "Refused: genuine completed Tower required."; }
    if this.Own(i,"Queued")==1 || this.Own(i,"Request")==1 { return this.Inspect(id); }
    if this.Root(i)==3 || this.Root(i)==4 { return "Preserved completed/failed gig: "+id+". No replay/reset."; }
    if !this.Fresh(i) { return "Preserved started/ambiguous stage: "+id+". This family handles fresh gigs only; no reset."; }
    if !this.Unused(i) { return "Refused: orphaned owned ledger; no owner/reward resend. "+this.Inspect(id); }
    if this.Own(i,"Ready")!=1 || this.Own(i,"Revision")!=1 { return "Refused: B7 native archive not ready; restart after installation. "+id; }
    if !overrideHistory {
      let history=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.ActivityStateR3.ActivityState") as ActivityState;
      if !IsDefined(history) || !history.B7FreshHistory(id) { return "Preserved: no certified fresh pre-ending history for "+id+"; explicit disposable-save override is available."; }
    }
    if !this.Write(i,"Queued",1) { return "Fault: queued acknowledgement failed; no automatic retry. "+id; };return this.Inspect(id);
  }
  private func CompletionAck(i: Int32) -> Bool {
    if this.Root(i)!=3 || this.Own(i,"Started")!=1 { return false; }
    let facts=GigDataB7.FinishedFacts(i);let k=0;let finished=false;
    while k<ArraySize(facts) { if this.Fact(facts[k])==1 { finished=true; };k+=1; };if !finished { return false; }
    let rewards=GigDataB7.Rewards(i);k=0;
    while k<ArraySize(rewards) { if this.Own(i,rewards[k]+"_Claim")==1 && this.Own(i,rewards[k]+"_Ack")==1 { return true; };k+=1; };return false;
  }
  private func Credit(i: Int32) -> Void {
    if this.Own(i,"CounterAck")==1 {
      let name=Equals(GigDataB7.Region(i),"wbr") ? "PTFRB5_TierRequest" : "PTFRB7_"+GigDataB7.Region(i)+"_TierRequest";
      if this.Fact(name)==0 { this.Set(name,1); };return;
    }
    if this.Own(i,"CounterClaim")!=0 { this.Write(i,"Fault",1);return; }
    // Native completion plus owned payout acknowledgement, not the potentially
    // long-lived aftermath owner. Cleanup stays native and is never forced.
    if !this.CompletionAck(i) || !this.LegacyIdle(GigDataB7.Region(i)) { return; }
    let counter=GigDataB7.Region(i)+"_sts_counter";let base=this.Fact(counter);
    if base<0 || base>=2147483647 { this.Write(i,"Fault",1);return; }
    if !this.Write(i,"CountBase",base) || !this.Write(i,"CounterClaim",1) { this.Write(i,"Fault",1);return; }
    if !this.Set(counter,base+1) || !this.Write(i,"CounterAck",1) { this.Write(i,"Fault",1); }
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch!=this.epoch { return; };this.Schedule();if this.warmup>0 { this.warmup-=1;return; }
    if !this.Tower() { return; };let p=GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;if !IsDefined(p) { return; }
    let safe=CyberwarePolicy.Safe(p);let i=0;
    while i<GigDataB7.Count() {
      if this.Own(i,"Queued")==1 && this.Own(i,"Fault")==0 {
        if this.Own(i,"Request")==0 {
          if safe && this.LegacyIdle(GigDataB7.Region(i)) {
            if !this.Fresh(i) { this.Write(i,"Fault",1); } else {
              if !this.Write(i,"Permit",1) || !this.Write(i,"Request",1) { this.Write(i,"Fault",1); }
            }
          }
        } else {
          if this.Own(i,"Started")==0 {
            let permit=safe && this.LegacyIdle(GigDataB7.Region(i)) ? 1 : 0;
            if this.Own(i,"Permit")!=permit { this.Write(i,"Permit",permit); }
          } else { this.Credit(i); }
        }
      };i+=1;
    }
    // One history check per tick, independent of the older R3 autoAttempted
    // field. Missing old baseline entries/facts remain unknown, never recaptured.
    if this.autoCursor<GigDataB7.Count() { this.Restore(GigDataB7.ID(this.autoCursor),false);this.autoCursor+=1; }
  }
}
public class GigTickB7 extends DelayCallback {
  private let owner: wref<GigFamilyB7>;private let epoch: Int32;
  public static func Create(owner: ref<GigFamilyB7>,epoch: Int32) -> ref<GigTickB7> { let t=new GigTickB7();t.owner=owner;t.epoch=epoch;return t; }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}
@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void { wrappedMethod(gameInstance);let s=GameInstance.GetScriptableSystemsContainer(gameInstance).Get(n"PTFR.ActivityStateR3.GigFamilyB7") as GigFamilyB7;if IsDefined(s) { s.Restored(); } }
