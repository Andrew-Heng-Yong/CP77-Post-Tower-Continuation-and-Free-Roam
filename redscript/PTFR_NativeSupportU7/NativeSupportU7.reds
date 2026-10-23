module PTFR.ActivityStateR3
import PTFR.ActivityStateR3.*
import PTFR.RestrictionsR1.*
import PTFR.JohnnyVoiceJV1.*

// Admission/inspection only. Original graphs own phone protocol and fixer credit.
public class NativeSupportU7 extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private func OnAttach() -> Void { this.running=true;this.Restored(); }
  private func OnDetach() -> Void { this.running=false;this.epoch+=1; }
  public func Restored() -> Void { this.epoch+=1;if this.running { this.Schedule(); } }
  private func Schedule() -> Void { GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(NativeSupportTickU7.Create(this,this.epoch),1.0,false); }
  private func Fact(s: String) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(StringToName(s)); }
  private func Own(s: String) -> Int32 { return this.Fact("PTFRU7_Support_"+s); }
  private func Set(s: String,v: Int32) -> Bool { GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(StringToName("PTFRU7_Support_"+s),v);return this.Own(s)==v; }
  private func State(path: String) -> Int32 { let jm=GameInstance.GetJournalManager(this.GetGameInstance());let e=jm.GetEntryByString(path,"gameJournalQuest");return IsDefined(e) ? EnumInt(jm.GetEntryState(e)) : -1; }
  private func OriginalLifetimeClosed() -> Bool {
    let s=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.JohnnyVoiceJV1.JohnnyVoiceJV1") as JohnnyVoiceJV1;
    return IsDefined(s) && s.CompletedTower() && this.State("ep1/quests/main_quest/q307_before_tomorrow")==3 && this.Fact("q307_main_game_killed")==1 && this.Fact("q307_ep1_killed")==1 && this.Fact("q307_active")==0 && this.Fact("q307_debug_reset")==0;
  }
  private func UnusedPilot() -> Bool {
    let names: array<String>=["PTFRU6_Padre_Request","PTFRU6_Padre_Issued","PTFRU6_Padre_Permit","PTFRU4_Jeopardy_Request","PTFRU4_Jeopardy_Started","PTFRU4_Jeopardy_Permit","PTFRU4_Jeopardy_Fault","PTFRB7_hey_rey_06_Queued","PTFRB7_hey_rey_06_Started","PTFRB7_hey_rey_06_CounterClaim","PTFRB7_hey_rey_06_CounterAck","rey_06_start","rey_06_finished"];
    let k=0;while k<ArraySize(names) { if this.Fact(names[k])!=0 { return false; };k+=1; }
    return GigDataB7.Index("sts_hey_rey_06")>=0 && this.State("quests/street_stories/heywood/vista_del_rey/sts_hey_rey_06")==1;
  }
  private func IdleProtocol() -> Bool {
    let names: array<String>=["holo_setup_active","holo_setup_started","holo_interrupt_call","holo_active_call_interrupted","holo_reset","holo_force_reset","holo_reset_soft","holo_interrupt_call_manual","holo_interrupt_braindance","holo_padre_calls_v_start_activate","holo_padre_calls_v_start_activate_count","holo_padre_calls_v_start_done","holo_padre_calls_v_end_activate","holo_padre_calls_v_end_done","holo_padre_calls_v_rejected","holo_padre_calls_v_rejectable","holo_v_calls_padre_start_activate","holo_v_calls_padre_start_done","holo_v_calls_padre_end_activate","holo_v_calls_padre_end_done","audio_padre_calls_v_start_activate","audio_v_calls_padre_start_activate","audio_v_calls_padre_end_activate","phonecall_sebastian_padre_perez_with_player","phonecall_player_with_sebastian_padre_perez"];
    let k=0;while k<ArraySize(names) { if this.Fact(names[k])!=0 { return false; };k+=1; }
    return this.Fact("holo_padre_calls_v_start_count")==this.Fact("holo_padre_calls_v_end_count") && this.Fact("holo_v_calls_padre_start_count")==this.Fact("holo_v_calls_padre_end_count");
  }
  public func Inspect() -> String {
    return "Native support U7: ready/request/issued="+ToString(this.Own("Ready"))+"/"+ToString(this.Own("Request"))+"/"+ToString(this.Own("Issued"))+" permit/fault="+ToString(this.Own("Permit"))+"/"+ToString(this.Own("Fault"))+" closed/unused/idle="+ToString(this.OriginalLifetimeClosed())+"/"+ToString(this.UnusedPilot())+"/"+ToString(this.IdleProtocol())+" creditDone/base/current="+ToString(this.Own("CreditDone"))+"/"+ToString(this.Own("CountBase"))+"/"+ToString(this.Fact("hey_sts_counter"))+" JeopardyRoot/start/done/ownerFinished="+ToString(this.State("quests/street_stories/heywood/vista_del_rey/sts_hey_rey_06"))+"/"+ToString(this.Fact("rey_06_start"))+"/"+ToString(this.Fact("rey_06_finished"))+"/"+ToString(this.Fact("PTFRU4_Jeopardy_OwnerFinished"))+" phoneStart/end="+ToString(this.Fact("holo_padre_calls_v_start_count"))+"/"+ToString(this.Fact("holo_padre_calls_v_end_count"))+" setupActive/Started="+ToString(this.Fact("holo_setup_active"))+"/"+ToString(this.Fact("holo_setup_started"))+" interrupt/forceReset="+ToString(this.Fact("holo_interrupt_call"))+"/"+ToString(this.Fact("holo_force_reset"))+" | Original Padre/interrupt/cleanup phases and Jeopardy credit nodes. Issued is not live-call proof; no other contacts/tiers/final rewards restored.";
  }
  public func Start(confirmation: String) -> String {
    if !Equals(confirmation,"DISPOSABLE_SAVE") { return "Refused: DISPOSABLE_SAVE required."; }
    if this.Own("Request")!=0 || this.Own("Issued")!=0 { return "Already requested/issued; no restart. "+this.Inspect(); }
    if this.Own("Ready")!=1 || this.Own("Revision")!=1 || this.Own("Fault")!=0 || this.Own("Permit")!=0 || this.Own("CreditDone")!=0 { return "Refused: archive unavailable or used/interrupted request. "+this.Inspect(); }
    if !this.OriginalLifetimeClosed() || !this.UnusedPilot() || !this.IdleProtocol() { return "Refused: load original pre-U6/U4 post-Tower snapshot with idle phone; no owner migration or native reset. "+this.Inspect(); }
    if !this.Set("CountBase",this.Fact("hey_sts_counter")) || !this.Set("Request",1) { this.Set("Fault",1);return "Request readback failed; no retry."; }
    return "Queued U7 native phone support and Jeopardy credit watcher. Close menus and holster for5 seconds, Inspect issued1, then start U4 once. "+this.Inspect();
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch!=this.epoch { return; };this.Schedule();
    if this.Own("Request")!=1 || this.Own("Issued")!=0 { return; }
    let p=GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    let phone=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PhoneSystem") as PhoneSystem;
    let permit=this.OriginalLifetimeClosed() && this.UnusedPilot() && this.IdleProtocol() && this.Own("Fault")==0 && IsDefined(p) && CyberwarePolicy.Safe(p) && IsDefined(phone) && phone.IsPhoneEnabled() && phone.IsCallingEnabled() && !GameInstance.GetPhoneManager(this.GetGameInstance()).IsPhoneCallActive() ? 1 : 0;
    if this.Own("Permit")!=permit && !this.Set("Permit",permit) { this.Set("Fault",1); }
  }
}
public class NativeSupportTickU7 extends DelayCallback {
  private let owner: wref<NativeSupportU7>;private let epoch: Int32;
  public static func Create(owner: ref<NativeSupportU7>,epoch: Int32) -> ref<NativeSupportTickU7> { let t=new NativeSupportTickU7();t.owner=owner;t.epoch=epoch;return t; }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}
@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void { wrappedMethod(gameInstance);let s=GameInstance.GetScriptableSystemsContainer(gameInstance).Get(n"PTFR.ActivityStateR3.NativeSupportU7") as NativeSupportU7;if IsDefined(s) { s.Restored(); } }
