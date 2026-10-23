module PTFR.ActivityStateR3

import PTFR.RestrictionsR1.*
import PTFR.JohnnyVoiceJV1.*

public struct FreshSlotB5 {
  public persistent let stage: Int32;
  public persistent let inflight: Bool;
  public persistent let countBase: Int32;
  public persistent let achBase: Int32;
  public persistent let accountPrepared: Bool;
  public persistent let counterAck: Bool;
}

// Temporary getter inputs, never stored as history or as a saved snapshot.
public struct RecoveryFactsB5 {
  public let ready: Int32;
  public let revision: Int32;
  public let request: Int32;
  public let started: Int32;
  public let finished: Int32;
  public let fault: Int32;
  public let rewardClaim: Int32;
  public let rewardAck: Int32;
  public let accountRequest: Int32;
  public let accountReady: Int32;
  public let accountClaim: Int32;
  public let accountAck: Int32;
  public let countBase: Int32;
  public let achBase: Int32;
  public let counterAck: Int32;
  public let count: Int32;
  public let ach: Int32;
  public let root: Int32;
  public let nativeFinished: Int32;
}

// Two source-reviewed fresh owners. Other whitelisted gigs are NOT implied.
public class FreshGigsB5 extends ScriptableSystem {
  private persistent let schema: Int32;
  private persistent let slots: array<FreshSlotB5>;
  private let running: Bool;
  private let epoch: Int32;
  private let warmup: Int32;
  private let ticks: array<Int32>;
  private let details: array<String>;
  private let recoveryChecked: array<Bool>;
  private func Init() -> Bool {
    if this.schema == 0 && ArraySize(this.slots) == 0 {
      let empty: FreshSlotB5; ArrayPush(this.slots,empty); ArrayPush(this.slots,empty); this.schema=1;
    }
    return this.schema==1 && ArraySize(this.slots)==2;
  }
  private func Shape() -> Bool { return this.schema==1 && ArraySize(this.slots)==2; }
  private func OnAttach() -> Void { this.running=true; this.Restored(); }
  private func OnDetach() -> Void { this.running=false; this.epoch+=1; }
  public func Restored() -> Void {
    this.epoch+=1; this.warmup=4; this.ticks=[0,0]; this.details=["",""]; this.recoveryChecked=[false,false];
    if this.Init() {
      let i=0; while i<2 {
        if this.slots[i].inflight || this.slots[i].stage<0 || this.slots[i].stage>5 { this.Fail(i,"Interrupted saved mutation; no resend. Reload original pre-test snapshot."); }
        i+=1;
      }
    }
    if this.running { this.Schedule(); }
  }
  private func Schedule() -> Void { GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(FreshTickB5.Create(this,this.epoch),1.0,false); }
  public static func Index(id: String) -> Int32 { return Equals(id,"sts_wbr_hil_07") ? 0 : Equals(id,"sts_wbr_hil_01") ? 1 : -1; }
  public static func ID(i: Int32) -> String { return i==0 ? "sts_wbr_hil_07" : "sts_wbr_hil_01"; }
  public static func Root(i: Int32) -> String { return "quests/street_stories/wesbrook/charter_hill/"+FreshGigsB5.ID(i); }
  public static func Paths(i: Int32) -> array<String> {
    let root=FreshGigsB5.Root(i); let phase=root+"/"+FreshGigsB5.ID(i);
    return i==0 ? [root,phase,phase+"/call_fixer",phase+"/drop_wallet",phase+"/scan",phase+"/get_in",root+"/brief",phase+"/get_to_vortex_den",phase+"/get_to_drainage_serwers"] :
      [root,phase,phase+"/drop_point",phase+"/go_to_councilman_apartment",phase+"/go_to_the_top_floor",phase+"/escape",phase+"/take_dps",phase+"/find",phase+"/be_unseen",root+"/brief"];
  }
  public static func Classes(i: Int32) -> array<String> {
    return i==0 ? ["gameJournalQuest","gameJournalQuestPhase","gameJournalQuestObjective","gameJournalQuestObjective","gameJournalQuestObjective","gameJournalQuestObjective","gameJournalQuestDescription","gameJournalQuestObjective","gameJournalQuestObjective"] :
      ["gameJournalQuest","gameJournalQuestPhase","gameJournalQuestObjective","gameJournalQuestObjective","gameJournalQuestObjective","gameJournalQuestObjective","gameJournalQuestObjective","gameJournalQuestObjective","gameJournalQuestObjective","gameJournalQuestDescription"];
  }
  public static func LocalNames(i: Int32) -> array<String> {
    return i==0 ? ["hil_07_start","hil_07_finished","hil_07_spawned","hil_07_comabt","hil_07_gang_retaliation","hil_07_paid","hil_07_backdoor","hil_07_second_flor","hil_07_track","sts_wbr_hil_07_shard","sts_wbr_hil_07_cleanup_fix","hil_07_vortex_asked","hil_07_location_known","hil_07_smokers_chat_not_interrupt"] :
      ["hil_01_start","hil_01_finished","hil_01_combat","hil_01_journal_test","sts_wbr_hil_01_depositary_receipt"];
  }
  private func Name(i: Int32, suffix: String) -> CName { return StringToName((i==0 ? "PTFRB5_H7_" : "PTFRB5_H1_")+suffix); }
  private func Fact(name: CName) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(name); }
  private func Own(i: Int32,suffix: String) -> Int32 { return this.Fact(this.Name(i,suffix)); }
  private func Set(name: CName,value: Int32) -> Void { GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(name,value); }
  private func Write(i: Int32,suffix: String,value: Int32) -> Bool { let name=this.Name(i,suffix); this.Set(name,value); return this.Fact(name)==value; }
  private func State(path: String,cls: String) -> Int32 { let jm=GameInstance.GetJournalManager(this.GetGameInstance()); let e=jm.GetEntryByString(path,cls); return IsDefined(e) ? EnumInt(jm.GetEntryState(e)) : -1; }
  private func Tower() -> Bool {
    let voice=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.JohnnyVoiceJV1.JohnnyVoiceJV1") as JohnnyVoiceJV1;
    return IsDefined(voice) && voice.CompletedTower();
  }
  private func Eligible(i: Int32) -> Bool {
    // Exact normal parent alternatives: Charter Hill root/37,39 and root/42,43.
    return (this.Fact(i==0 ? n"sts_wbr_hil_tier_1_1" : n"sts_wbr_hil_tier_1_2")>0) ||
      (this.Fact(n"sts_wbr_hil_tier_1")>0 && this.Fact(n"sts_wbr_hil_tier_1_1")==0);
  }
  private func FreshJournal(i: Int32) -> Bool {
    let paths=FreshGigsB5.Paths(i); let classes=FreshGigsB5.Classes(i); let k=0;
    while k<ArraySize(paths) { if this.State(paths[k],classes[k])!=1 { return false; }; k+=1; }; return true;
  }
  private func DatabankCount() -> Int32 {
    let p=GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(p) { return -1; }; let ts=GameInstance.GetTransactionSystem(this.GetGameInstance()); let items: array<wref<gameItemData>>; ts.GetItemList(p,items);
    let n=0; let k=0; while k<ArraySize(items) { if IsDefined(items[k]) && TDBID.ToNumber(ItemID.GetTDBID(items[k].GetID()))==171618873303ul { n+=ts.GetItemQuantity(p,items[k].GetID()); }; k+=1; }; return n;
  }
  private func FreshFacts(i: Int32) -> Bool {
    let names=FreshGigsB5.LocalNames(i);let k=0;while k<ArraySize(names) { if this.Fact(StringToName(names[k]))!=0 { return false; }; k+=1; }
    // A separately active clue-vendor scene or an already-collected databank is
    // an unsupported ownership/item stage, not permission to reset it.
    return i==0 ? this.Fact(n"wbr_hil_foodshop_02_default_on")==0 && this.Fact(n"wbr_hil_foodshop_02_drinking_active")==0 : this.DatabankCount()==0;
  }
  private func Unused(i: Int32) -> Bool {
    let names: array<String>=["Request","Started","OwnerFinished","Fault","RewardClaim","RewardAck","AccountRequest","AccountReady","AccountClaim","AccountAck","CountBase","AchBase","CounterAck"];
    let k=0;while k<ArraySize(names) { if this.Own(i,names[k])!=0 { return false; };k+=1; };return true;
  }
  private func CountsSafe() -> Bool { return this.Fact(n"wbr_sts_counter")>=0 && this.Fact(n"wbr_sts_counter")<2147483647 && this.Fact(n"wbr_achievement")>=0 && this.Fact(n"wbr_achievement")<2147483647; }
  // Pure classifier. A zeroed old B5 slot is adopted only from THIS owner's
  // surviving acknowledgements. It never decides freshness or pre-ending history.
  public static func RecoveryStage(f: RecoveryFactsB5) -> Int32 {
    if f.request==0 && f.started==0 && f.finished==0 && f.fault==0 && f.rewardClaim==0 && f.rewardAck==0 && f.accountRequest==0 && f.accountReady==0 && f.accountClaim==0 && f.accountAck==0 && f.countBase==0 && f.achBase==0 && f.counterAck==0 { return 0; }
    if f.ready!=1 || f.revision!=1 || f.request!=1 || f.fault!=0 { return 5; }
    if f.started<0 || f.started>1 || f.finished<0 || f.finished>1 || f.rewardClaim<0 || f.rewardClaim>1 || f.rewardAck<0 || f.rewardAck>1 || f.accountRequest<0 || f.accountRequest>1 || f.accountReady<0 || f.accountReady>1 || f.accountClaim<0 || f.accountClaim>1 || f.accountAck<0 || f.accountAck>1 || f.counterAck<0 || f.counterAck>1 { return 5; }
    if f.rewardAck>f.rewardClaim || f.accountReady>f.accountRequest || f.accountClaim>f.accountReady || f.accountAck>f.accountClaim || f.counterAck>f.accountAck { return 5; }
    if f.countBase<0 || f.countBase>=2147483647 || f.achBase<0 || f.achBase>=2147483647 || f.count<0 || f.ach<0 { return 5; }
    if f.root<1 || f.root>3 { return 5; }
    if f.started==0 && (f.finished!=0 || f.rewardClaim!=0 || f.rewardAck!=0 || f.accountRequest!=0 || f.accountReady!=0 || f.accountClaim!=0 || f.accountAck!=0 || f.counterAck!=0 || f.countBase!=0 || f.achBase!=0) { return 5; }
    if f.started==0 { return 2; }
    if f.accountRequest==0 && (f.countBase!=0 || f.achBase!=0) { return 5; }
    if f.accountReady==1 && (f.count<f.countBase || f.ach<f.achBase) { return 5; }
    if f.accountAck==1 && f.ach<f.achBase+1 { return 5; }
    if f.counterAck==1 && f.count<f.countBase+1 { return 5; }
    // Achievement ack but no fixer ack: only the untouched baseline permits
    // the existing one-shot PollSlot credit. Any higher total is ambiguous.
    if f.accountAck==1 && f.counterAck==0 && f.count!=f.countBase { return 5; }
    if f.finished==1 && (f.counterAck!=1 || f.rewardClaim!=1 || f.rewardAck!=1 || f.nativeFinished<1 || f.root!=3) { return 5; }
    if f.finished==1 { return 4; }
    return 3;
  }
  private func AdoptSavedOwner(i: Int32) -> Void {
    let slot=this.slots[i];
    if slot.stage!=0 || slot.inflight || slot.accountPrepared || slot.counterAck || slot.countBase!=0 || slot.achBase!=0 { return; }
    let f: RecoveryFactsB5;
    f.ready=this.Own(i,"Ready");f.revision=this.Own(i,"Revision");f.request=this.Own(i,"Request");f.started=this.Own(i,"Started");f.finished=this.Own(i,"OwnerFinished");f.fault=this.Own(i,"Fault");
    f.rewardClaim=this.Own(i,"RewardClaim");f.rewardAck=this.Own(i,"RewardAck");f.accountRequest=this.Own(i,"AccountRequest");f.accountReady=this.Own(i,"AccountReady");f.accountClaim=this.Own(i,"AccountClaim");f.accountAck=this.Own(i,"AccountAck");
    f.countBase=this.Own(i,"CountBase");f.achBase=this.Own(i,"AchBase");f.counterAck=this.Own(i,"CounterAck");f.count=this.Fact(n"wbr_sts_counter");f.ach=this.Fact(n"wbr_achievement");f.root=this.State(FreshGigsB5.Root(i),"gameJournalQuest");f.nativeFinished=this.Fact(i==0 ? n"hil_07_finished" : n"hil_01_finished");
    let recovered=FreshGigsB5.RecoveryStage(f);
    if recovered==0 { return; }
    slot.stage=recovered;
    if recovered==5 {
      this.slots[i]=slot;this.details[i]="B5.1 recovery refused: inconsistent saved request/outcome/account acknowledgements or ambiguous unacknowledged credit. No owner, payout or credit resend. Send Inspect and Sample; retain the original snapshot.";return;
    }
    slot.accountPrepared=f.accountReady==1;slot.counterAck=f.counterAck==1;
    if slot.accountPrepared { slot.countBase=f.countBase;slot.achBase=f.achBase; }
    this.slots[i]=slot;this.details[i]="B5.1 adopted saved owned acknowledgements; no owner restart, reward replay or repeated acknowledged credit.";
  }
  private func OtherOwnerIdle(i: Int32) -> Bool {
    // B6 can own its native prefab before proximity activates its quest root.
    if this.Fact(n"PTFRB6_J2_Request")!=0 && this.Fact(n"PTFRB6_J2_OwnerFinished")!=1 { return false; }
    let peer=1-i; if this.slots[peer].stage==2 || this.slots[peer].stage==3 || this.slots[peer].inflight || (this.slots[peer].stage==5 && this.Own(peer,"Request")!=0) { return false; }
    let ids: array<String>=["sts_wbr_hil_06","sts_wbr_jpn_01","sts_wbr_jpn_02","sts_wbr_jpn_03","sts_wbr_jpn_05","sts_wbr_jpn_12","sts_wbr_jpn_06","sts_wbr_jpn_09"];
    let k=0;while k<ArraySize(ids) { if this.State("quests/street_stories/wesbrook/"+(Equals(ids[k],"sts_wbr_hil_06") ? "charter_hill/" : "japan_town/")+ids[k],"gameJournalQuest")==2 { return false; };k+=1; }
    if this.State("quests/street_stories/heywood/vista_del_rey/sts_hey_rey_09","gameJournalQuest")==2 { return false; }
    return this.State(FreshGigsB5.Root(peer),"gameJournalQuest")!=2;
  }
  public func RestoreFresh(id: String) -> String {
    let i=FreshGigsB5.Index(id);if i<0 { return "Refused: B5 implements only Tyger and Vulture / Until Death Do Us Part."; }
    if !this.Shape() { return "Refused: B5 saved schema mismatch; no migration/reset."; }
    if this.slots[i].stage!=0 { return this.Inspect(id); }
    if !this.Tower() || !this.FreshJournal(i) || !this.FreshFacts(i) || !this.Unused(i) || !this.CountsSafe() || this.Own(i,"Ready")!=1 || this.Own(i,"Revision")!=1 || this.Fact(n"PTFRB5_TierReady")!=1 {
      return "Refused without mutation: requires fresh existing journals/local progress, no collected item or separate clue-vendor owner, genuine Tower and ready B5 archive. Inspect identifies the gates; completed replay/started continuation are not implemented.";
    }
    let poi=this.State("points_of_interest/street_stories/"+id,"gameJournalPointOfInterestMappin");
    if poi!=1 && poi!=2 { return "Preserved: missing/terminal POI; no reset."; }
    let slot=this.slots[i];slot.stage=1;this.slots[i]=slot;this.details[i]="Queued fresh native owner; existing fixer tier and shared-owner availability may defer activation.";
    return this.Inspect(id);
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch!=this.epoch { return; };this.Schedule();if !this.Shape() || !this.Tower() { return; }
    if this.warmup>0 { this.warmup-=1;return; }
    let p=GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;if !IsDefined(p) { return; }
    if (!this.recoveryChecked[0] || !this.recoveryChecked[1]) && GameInstance.GetJournalManager(this.GetGameInstance()).HasAnyDelayedStateChanges() { return; }
    let r=0;while r<2 {
      if !this.recoveryChecked[r] { this.AdoptSavedOwner(r);this.recoveryChecked[r]=true; }
      r+=1;
    }
    let i=0;while i<2 { this.PollSlot(i,p);i+=1; }
  }
  private func PollSlot(i: Int32,p: ref<PlayerPuppet>) -> Void {
    let slot=this.slots[i];
    // A saved credit ack may outlive its subsequent tier-request write. Reassert
    // only our idempotent earned-tier request, never a gig request or a counter.
    if (slot.stage==3 || slot.stage==4) && slot.counterAck && this.Own(i,"CounterAck")==1 && this.Fact(n"PTFRB5_TierRequest")==0 {
      this.Set(n"PTFRB5_TierRequest",1);
      if this.Fact(n"PTFRB5_TierRequest")!=1 { this.Fail(i,"Earned-tier request unacknowledged; credit will not repeat."); }
      return;
    }
    if slot.stage==0 || slot.stage==4 || slot.stage==5 { return; }
    if this.Own(i,"Fault")!=0 { this.Fail(i,"Native payout/account guard refused; no retry/compensation.");return; }
    let jm=GameInstance.GetJournalManager(this.GetGameInstance());
    if slot.stage==1 {
      if !CyberwarePolicy.Safe(p) { this.details[i]="Waiting: close CET/menus, holster, leave combat/vehicle/workspot.";return; }
      if !this.Eligible(i) || !this.OtherOwnerIdle(i) { this.details[i]="Waiting for native Wakako tier / another Westbrook owner's cleanup. No tier forcing.";return; }
      if !this.FreshJournal(i) || !this.FreshFacts(i) || !this.Unused(i) || !this.CountsSafe() { this.Fail(i,"Fresh stage/item/shared-vendor drift while queued; no reset.");return; }
      let path="points_of_interest/street_stories/"+FreshGigsB5.ID(i);let poi=this.State(path,"gameJournalPointOfInterestMappin");
      if slot.inflight {
        if jm.HasAnyDelayedStateChanges() { return; };if poi==2 { slot.inflight=false;this.slots[i]=slot;this.ticks[i]=0;return; }
        this.ticks[i]+=1;if this.ticks[i]>=12 { this.Fail(i,"POI activation unacknowledged; no resend."); };return;
      }
      if jm.HasAnyDelayedStateChanges() { return; }
      if poi==1 { slot.inflight=true;this.slots[i]=slot;jm.ChangeEntryState(path,"gameJournalPointOfInterestMappin",gameJournalEntryState.Active,JournalNotifyOption.DoNotNotify);return; }
      if poi!=2 { this.Fail(i,"POI became missing/terminal; no reset.");return; }
      slot.inflight=true;this.slots[i]=slot;
      if !this.Write(i,"Request",1) { this.Fail(i,"Native request not acknowledged; no resend.");return; }
      slot.stage=2;slot.inflight=false;this.slots[i]=slot;return;
    }
    if slot.stage==2 {
      if this.Own(i,"Started")!=1 { this.details[i]="Waiting for native boot. Do not force facts.";return; }
      slot.stage=3;this.slots[i]=slot;this.details[i]="Native fresh owner running. Approach its map marker; native scenes/trigger activate the journal. Wakako uses authored text.";
    }
    if slot.stage==3 {
      if this.Own(i,"AccountRequest")==1 && !slot.accountPrepared {
        if !this.OtherOwnerIdle(i) { this.details[i]="Completion accounting deferred: another Westbrook owner is active.";return; }
        if !this.CountsSafe() || this.Own(i,"AccountReady")!=0 || this.Own(i,"AccountClaim")!=0 || this.Own(i,"AccountAck")!=0 { this.Fail(i,"Unsupported accounting handoff; no resend.");return; }
        slot.inflight=true;slot.countBase=this.Fact(n"wbr_sts_counter");slot.achBase=this.Fact(n"wbr_achievement");this.slots[i]=slot;
        if !this.Write(i,"CountBase",slot.countBase) || !this.Write(i,"AchBase",slot.achBase) { this.Fail(i,"Derived completion baseline not acknowledged.");return; }
        slot.accountPrepared=true;this.slots[i]=slot;
        if !this.Write(i,"AccountReady",1) { this.Fail(i,"Accounting ready write not acknowledged.");return; }
        slot.inflight=false;this.slots[i]=slot;return;
      }
      if this.Own(i,"AccountAck")==1 && !slot.counterAck {
        // Native own Ack proves its achievement increment; later NCPD additions
        // are legitimate and never overwritten or required to equal the counter.
        if !slot.accountPrepared || this.Own(i,"AccountClaim")!=1 || this.Fact(n"wbr_achievement")<slot.achBase+1 || this.Fact(n"wbr_sts_counter")!=slot.countBase { this.Fail(i,"Fixer accounting changed during handoff; no recount.");return; }
        slot.inflight=true;this.slots[i]=slot;this.Set(n"wbr_sts_counter",slot.countBase+1);
        if this.Fact(n"wbr_sts_counter")!=slot.countBase+1 { this.Fail(i,"Fixer counter unacknowledged; no retry.");return; }
        slot.counterAck=true;this.slots[i]=slot;
        if !this.Write(i,"CounterAck",1) { this.Fail(i,"Owned credit acknowledgement failed; no recount.");return; }
        this.Set(n"PTFRB5_TierRequest",1);if this.Fact(n"PTFRB5_TierRequest")!=1 { this.Fail(i,"Earned-tier request unacknowledged; credit will not repeat.");return; }
        slot.inflight=false;this.slots[i]=slot;
      }
      if this.Own(i,"OwnerFinished")==1 {
        if !slot.counterAck || this.Own(i,"RewardClaim")!=1 || this.Own(i,"RewardAck")!=1 || this.Fact(i==0 ? n"hil_07_finished" : n"hil_01_finished")<1 || this.State(FreshGigsB5.Root(i),"gameJournalQuest")!=3 { this.Fail(i,"Owner ended without native terminal/payout/account acknowledgements; no replay.");return; }
        slot.stage=4;this.slots[i]=slot;this.details[i]="Native completion/output and one payout/fixer credit acknowledged. Earned tiers use their separate native fragment; final fixer rewards not restored.";
      }
    }
  }
  private func Fail(i: Int32,msg: String) -> Void { let slot=this.slots[i];slot.stage=5;this.slots[i]=slot;this.details[i]=msg;this.Write(i,"Fault",1); }
  public func Inspect(id: String) -> String {
    let i=FreshGigsB5.Index(id);if i<0 || !this.Shape() { return "B5: unsupported ID/schema."; }
    let slot=this.slots[i];let detail=ArraySize(this.details)==2 ? this.details[i] : "";
    return "Fresh B5.1 "+id+": stage="+ToString(slot.stage)+" inflight="+ToString(slot.inflight)+" ready/start/finished="+ToString(this.Own(i,"Ready"))+"/"+ToString(this.Own(i,"Started"))+"/"+ToString(this.Own(i,"OwnerFinished"))+
      " reward="+ToString(this.Own(i,"RewardClaim"))+"/"+ToString(this.Own(i,"RewardAck"))+" account="+ToString(this.Own(i,"AccountClaim"))+"/"+ToString(this.Own(i,"AccountAck"))+" counterAck="+ToString(slot.counterAck)+
      " baseCount/Ach="+ToString(slot.countBase)+"/"+ToString(slot.achBase)+" current="+ToString(this.Fact(n"wbr_sts_counter"))+"/"+ToString(this.Fact(n"wbr_achievement"))+" tierReady/Ack2="+ToString(this.Fact(n"PTFRB5_TierReady"))+"/"+ToString(this.Fact(n"PTFRB5_Tier2_Ack"))+" | tower="+ToString(this.Tower())+" freshJournal="+ToString(this.FreshJournal(i))+" freshFacts="+ToString(this.FreshFacts(i))+" nativeTier="+ToString(this.Eligible(i))+" otherOwnerIdle="+ToString(this.OtherOwnerIdle(i))+" root="+ToString(this.State(FreshGigsB5.Root(i),"gameJournalQuest"))+" fault="+ToString(this.Own(i,"Fault"))+" | "+detail;
  }
}
public class FreshTickB5 extends DelayCallback {
  private let owner: wref<FreshGigsB5>;private let epoch: Int32;
  public static func Create(owner: ref<FreshGigsB5>,epoch: Int32) -> ref<FreshTickB5> { let t=new FreshTickB5();t.owner=owner;t.epoch=epoch;return t; }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}
@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void {
  wrappedMethod(gameInstance);let s=GameInstance.GetScriptableSystemsContainer(gameInstance).Get(n"PTFR.ActivityStateR3.FreshGigsB5") as FreshGigsB5;if IsDefined(s) { s.Restored(); }
}

