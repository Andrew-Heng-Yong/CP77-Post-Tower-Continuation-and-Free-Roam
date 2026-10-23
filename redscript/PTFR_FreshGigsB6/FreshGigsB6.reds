module PTFR.ActivityStateR3
import PTFR.RestrictionsR1.*
import PTFR.JohnnyVoiceJV1.*

// Separate persistent slot: the tested two-slot B5 schema is not resized.
public class FreshGigsB6 extends ScriptableSystem {
  private persistent let schema: Int32;
  private persistent let slot: FreshSlotB5;
  private let running: Bool;
  private let epoch: Int32;
  private let warmup: Int32;
  private let ticks: Int32;
  private let detail: String;
  private func OnAttach() -> Void { this.running=true;this.Restored(); }
  private func OnDetach() -> Void { this.running=false;this.epoch+=1; }
  public func Restored() -> Void {
    if this.schema==0 { this.schema=1; }
    this.epoch+=1;this.warmup=4;this.ticks=0;this.detail="";
    if this.slot.inflight || this.slot.stage<0 || this.slot.stage>5 { this.Fail("Interrupted saved mutation; no resend. Retain the original snapshot."); }
    if this.running { this.Schedule(); }
  }
  private func Schedule() -> Void { GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(FreshTickB6.Create(this,this.epoch),1.0,false); }
  public static func Root() -> String { return "quests/street_stories/wesbrook/japan_town/sts_wbr_jpn_02"; }
  public static func Paths() -> array<String> {
    let r=FreshGigsB6.Root();let p=r+"/sts_wbr_jpn_02";
    return [r,p,p+"/get_to_the_basement",p+"/rescue_bill1",p+"/escape_workshop_with_bill",p+"/tell_lauren_to_get_to_car",p+"/find_way_inside",p+"/get_inside",r+"/jpn_02_brief"];
  }
  public static func Classes() -> array<String> { return ["gameJournalQuest","gameJournalQuestPhase","gameJournalQuestObjective","gameJournalQuestObjective","gameJournalQuestObjective","gameJournalQuestObjective","gameJournalQuestObjective","gameJournalQuestObjective","gameJournalQuestDescription"]; }
  public static func LocalNames() -> array<String> { return ["jpn_02_start","jpn_02_finished","jpn_02_npcs_move","jpn_02_all_killed","jpn_02_first_ground_chat_end","jpn_02_testdef","jpn_02_torturere_defeated_in_lauren","jpn_02_torturere_defeated_in_room"]; }
  private func Fact(name: CName) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(name); }
  private func Own(suffix: String) -> Int32 { return this.Fact(StringToName("PTFRB6_J2_"+suffix)); }
  private func Write(suffix: String,value: Int32) -> Bool { let n=StringToName("PTFRB6_J2_"+suffix);GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(n,value);return this.Fact(n)==value; }
  private func State(path: String,cls: String) -> Int32 { let jm=GameInstance.GetJournalManager(this.GetGameInstance());let e=jm.GetEntryByString(path,cls);return IsDefined(e) ? EnumInt(jm.GetEntryState(e)) : -1; }
  private func Tower() -> Bool { let v=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.JohnnyVoiceJV1.JohnnyVoiceJV1") as JohnnyVoiceJV1;return IsDefined(v) && v.CompletedTower(); }
  private func Fresh() -> Bool {
    let paths=FreshGigsB6.Paths();let classes=FreshGigsB6.Classes();let k=0;
    while k<ArraySize(paths) { if this.State(paths[k],classes[k])!=1 { return false; };k+=1; }
    let names=FreshGigsB6.LocalNames();k=0;while k<ArraySize(names) { if this.Fact(StringToName(names[k]))!=0 { return false; };k+=1; };return true;
  }
  private func Unused() -> Bool { let names: array<String>=["Request","Started","OwnerFinished","Fault","RewardClaim","RewardAck","AccountRequest","AccountReady","AccountClaim","AccountAck","CountBase","AchBase","CounterAck"];let k=0;while k<ArraySize(names) { if this.Own(names[k])!=0 { return false; };k+=1; };return true; }
  private func CountsSafe() -> Bool { return this.Fact(n"wbr_sts_counter")>=0 && this.Fact(n"wbr_sts_counter")<2147483647 && this.Fact(n"wbr_achievement")>=0 && this.Fact(n"wbr_achievement")<2147483647; }
  private func Eligible() -> Bool {
    // Parent root/69 OR root/70 through root/68, not a debug alternative.
    return this.Fact(n"sts_wbr_jpn_tier_1_2")>0 || (this.Fact(n"sts_wbr_jpn_tier_1")>0 && this.Fact(n"sts_wbr_jpn_tier_1_1")==0);
  }
  private func OtherOwnerIdle() -> Bool {
    let tags: array<String>=["PTFRB5_H7_","PTFRB5_H1_"];let k=0;
    while k<ArraySize(tags) { if this.Fact(StringToName(tags[k]+"Request"))!=0 && this.Fact(StringToName(tags[k]+"OwnerFinished"))!=1 { return false; };k+=1; }
    let ids: array<String>=["sts_wbr_hil_07","sts_wbr_hil_01","sts_wbr_hil_06","sts_wbr_jpn_01","sts_wbr_jpn_03","sts_wbr_jpn_05","sts_wbr_jpn_12","sts_wbr_jpn_06","sts_wbr_jpn_09"];
    k=0;while k<ArraySize(ids) { if this.State("quests/street_stories/wesbrook/"+(StrContains(ids[k],"_hil_") ? "charter_hill/" : "japan_town/")+ids[k],"gameJournalQuest")==2 { return false; };k+=1; }
    return this.State("quests/street_stories/heywood/vista_del_rey/sts_hey_rey_09","gameJournalQuest")!=2;
  }
  public func RestoreFresh() -> String {
    if this.schema!=1 { return "Refused: B6 schema mismatch; no reset/migration."; }
    if this.slot.stage!=0 { return this.Inspect(); }
    if !this.Tower() || !this.Fresh() || !this.Unused() || !this.CountsSafe() || this.Own("Ready")!=1 || this.Own("Revision")!=1 || this.Fact(n"PTFRB5_TierReady")!=1 { return "Refused without mutation: requires untouched We Have Your Wife journal/local progress, genuine Tower and ready B6/B5 archives. Started/replay adapters absent; send Inspect."; }
    let poi=this.State("points_of_interest/street_stories/sts_wbr_jpn_02","gameJournalPointOfInterestMappin");if poi!=1 && poi!=2 { return "Preserved missing/terminal POI; no reset."; }
    this.slot.stage=1;this.detail="Queued We Have Your Wife; native tier and shared Westbrook owner work may defer it.";return this.Inspect();
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch!=this.epoch { return; };this.Schedule();if this.schema!=1 || !this.Tower() { return; }
    if this.warmup>0 { this.warmup-=1;return; }
    let p=GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;if !IsDefined(p) { return; }
    let jm=GameInstance.GetJournalManager(this.GetGameInstance());
    if this.slot.stage==0 || this.slot.stage==4 || this.slot.stage==5 { return; }
    if this.Own("Fault")!=0 { this.Fail("Native payout/account guard refused; no retry.");return; }
    if this.slot.stage==1 {
      if !CyberwarePolicy.Safe(p) { this.detail="Waiting: close menus/CET, holster and leave combat/vehicle/workspot.";return; }
      if !this.Eligible() || !this.OtherOwnerIdle() { this.detail="Waiting for native Wakako tier / another Westbrook owner's cleanup. No forcing.";return; }
      if !this.Fresh() || !this.Unused() || !this.CountsSafe() { this.Fail("Fresh local stage drift while queued; no reset.");return; }
      let path="points_of_interest/street_stories/sts_wbr_jpn_02";let poi=this.State(path,"gameJournalPointOfInterestMappin");
      if this.slot.inflight {
        if jm.HasAnyDelayedStateChanges() { return; };if poi==2 { this.slot.inflight=false;this.ticks=0;return; }
        this.ticks+=1;if this.ticks>=12 { this.Fail("POI activation not acknowledged; no resend."); };return;
      }
      if jm.HasAnyDelayedStateChanges() { return; }
      if poi==1 { this.slot.inflight=true;jm.ChangeEntryState(path,"gameJournalPointOfInterestMappin",gameJournalEntryState.Active,JournalNotifyOption.DoNotNotify);return; }
      if poi!=2 { this.Fail("POI became missing/terminal; no reset.");return; }
      this.slot.inflight=true;if !this.Write("Request",1) { this.Fail("Request not acknowledged; no resend.");return; };this.slot.stage=2;this.slot.inflight=false;return;
    }
    if this.slot.stage==2 { if this.Own("Started")!=1 { this.detail="Waiting for native boot; do not force facts.";return; };this.slot.stage=3;this.detail="Native We Have Your Wife owner running; approach workshop. Native scene/trigger controls journal activation."; }
    if this.slot.stage==3 {
      if this.Own("AccountRequest")==1 && !this.slot.accountPrepared {
        if !this.OtherOwnerIdle() { this.detail="Accounting deferred: another Westbrook owner active.";return; }
        if !this.CountsSafe() || this.Own("AccountReady")!=0 || this.Own("AccountClaim")!=0 || this.Own("AccountAck")!=0 { this.Fail("Unsupported accounting handoff; no resend.");return; }
        this.slot.inflight=true;this.slot.countBase=this.Fact(n"wbr_sts_counter");this.slot.achBase=this.Fact(n"wbr_achievement");
        if !this.Write("CountBase",this.slot.countBase) || !this.Write("AchBase",this.slot.achBase) { this.Fail("Baseline not acknowledged.");return; }
        this.slot.accountPrepared=true;if !this.Write("AccountReady",1) { this.Fail("AccountReady not acknowledged.");return; };this.slot.inflight=false;return;
      }
      if this.Own("AccountAck")==1 && !this.slot.counterAck {
        if !this.slot.accountPrepared || this.Own("AccountClaim")!=1 || this.Fact(n"wbr_achievement")<this.slot.achBase+1 || this.Fact(n"wbr_sts_counter")!=this.slot.countBase { this.Fail("Accounting changed during handoff; no recount.");return; }
        this.slot.inflight=true;GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(n"wbr_sts_counter",this.slot.countBase+1);
        if this.Fact(n"wbr_sts_counter")!=this.slot.countBase+1 { this.Fail("Fixer counter unacknowledged; no retry.");return; }
        this.slot.counterAck=true;if !this.Write("CounterAck",1) { this.Fail("Credit acknowledgement failed; no recount.");return; };this.slot.inflight=false;
      }
      if this.slot.counterAck && this.Own("CounterAck")==1 && this.Fact(n"PTFRB5_TierRequest")==0 { GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(n"PTFRB5_TierRequest",1);if this.Fact(n"PTFRB5_TierRequest")!=1 { this.Fail("Tier request unacknowledged; credit will not repeat.");return; } }
      if this.Own("OwnerFinished")==1 {
        if !this.slot.counterAck || this.Own("RewardClaim")!=1 || this.Own("RewardAck")!=1 || this.Fact(n"jpn_02_finished")!=1 || this.State(FreshGigsB6.Root(),"gameJournalQuest")!=3 { this.Fail("Native owner ended outside supported success acknowledgement path; no replay/reset.");return; }
        this.slot.stage=4;this.detail="Native completion, one payout/credit and departure cleanup acknowledged. Fixer final rewards remain separate.";
      }
    }
  }
  private func Fail(message: String) -> Void { this.slot.stage=5;this.detail=message;this.Write("Fault",1); }
  public func Inspect() -> String {
    return "Fresh B6 We Have Your Wife: stage="+ToString(this.slot.stage)+" inflight="+ToString(this.slot.inflight)+" ready/start/finished="+ToString(this.Own("Ready"))+"/"+ToString(this.Own("Started"))+"/"+ToString(this.Own("OwnerFinished"))+" reward="+ToString(this.Own("RewardClaim"))+"/"+ToString(this.Own("RewardAck"))+" account="+ToString(this.Own("AccountClaim"))+"/"+ToString(this.Own("AccountAck"))+" counterAck="+ToString(this.slot.counterAck)+" base="+ToString(this.slot.countBase)+"/"+ToString(this.slot.achBase)+" current="+ToString(this.Fact(n"wbr_sts_counter"))+"/"+ToString(this.Fact(n"wbr_achievement"))+" tower="+ToString(this.Tower())+" fresh="+ToString(this.Fresh())+" nativeTier="+ToString(this.Eligible())+" otherOwnerIdle="+ToString(this.OtherOwnerIdle())+" root="+ToString(this.State(FreshGigsB6.Root(),"gameJournalQuest"))+" fault="+ToString(this.Own("Fault"))+" | "+this.detail;
  }
}
public class FreshTickB6 extends DelayCallback {
  private let owner: wref<FreshGigsB6>;private let epoch: Int32;
  public static func Create(owner: ref<FreshGigsB6>,epoch: Int32) -> ref<FreshTickB6> { let t=new FreshTickB6();t.owner=owner;t.epoch=epoch;return t; }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}
@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void { wrappedMethod(gameInstance);let s=GameInstance.GetScriptableSystemsContainer(gameInstance).Get(n"PTFR.ActivityStateR3.FreshGigsB6") as FreshGigsB6;if IsDefined(s) { s.Restored(); } }
