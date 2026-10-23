module PTFR.ActivityStateR3
import PTFR.ActivityStateR3.*
import PTFR.RestrictionsR1.*
import PTFR.JohnnyVoiceJV1.*

// One post-Tower entry for the ORIGINAL Padre controller. No phone protocol writes.
public class NativePadreU6 extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private func OnAttach() -> Void { this.running=true;this.Restored(); }
  private func OnDetach() -> Void { this.running=false;this.epoch+=1; }
  public func Restored() -> Void { this.epoch+=1;if this.running { this.Schedule(); } }
  private func Schedule() -> Void { GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(NativePadreTickU6.Create(this,this.epoch),1.0,false); }
  private func Fact(s: String) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(StringToName(s)); }
  private func Own(s: String) -> Int32 { return this.Fact("PTFRU6_Padre_"+s); }
  private func Set(s: String,v: Int32) -> Bool { GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(StringToName("PTFRU6_Padre_"+s),v);return this.Own(s)==v; }
  private func State(path: String) -> Int32 { let jm=GameInstance.GetJournalManager(this.GetGameInstance());let e=jm.GetEntryByString(path,"gameJournalQuest");return IsDefined(e) ? EnumInt(jm.GetEntryState(e)) : -1; }
  // Source-backed shutdown: base root terminates and q307 cuts its phone-service phase.
  // This is not an introspection API for arbitrary third-party quest instances.
  private func OriginalLifetimeClosed() -> Bool {
    let s=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.JohnnyVoiceJV1.JohnnyVoiceJV1") as JohnnyVoiceJV1;
    return IsDefined(s) && s.CompletedTower() && this.State("ep1/quests/main_quest/q307_before_tomorrow")==3 && this.Fact("q307_main_game_killed")==1 && this.Fact("q307_ep1_killed")==1 && this.Fact("q307_active")==0 && this.Fact("q307_debug_reset")==0;
  }
  private func IdleProtocol() -> Bool {
    let names: array<String>=["holo_setup_active","holo_setup_started","holo_interrupt_call","holo_active_call_interrupted","holo_reset","holo_force_reset","holo_reset_soft","holo_padre_calls_v_start_activate","holo_padre_calls_v_start_activate_count","holo_padre_calls_v_start_done","holo_padre_calls_v_end_activate","holo_padre_calls_v_end_done","holo_padre_calls_v_rejected","holo_padre_calls_v_rejectable","holo_v_calls_padre_start_activate","holo_v_calls_padre_start_done","holo_v_calls_padre_end_activate","holo_v_calls_padre_end_done","audio_padre_calls_v_start_activate","audio_v_calls_padre_start_activate","audio_v_calls_padre_end_activate","phonecall_sebastian_padre_perez_with_player","phonecall_player_with_sebastian_padre_perez"];
    let k=0;while k<ArraySize(names) { if this.Fact(names[k])!=0 { return false; };k+=1; }
    return this.Fact("holo_padre_calls_v_start_count")==this.Fact("holo_padre_calls_v_end_count") && this.Fact("holo_v_calls_padre_start_count")==this.Fact("holo_v_calls_padre_end_count");
  }
  private func UnencounteredPilot() -> Bool {
    return this.State("quests/street_stories/heywood/vista_del_rey/sts_hey_rey_06")==1 && this.Fact("rey_06_start")==0 && this.Fact("rey_06_finished")==0 && this.Fact("PTFRB7_hey_rey_06_Queued")==0 && this.Fact("PTFRB7_hey_rey_06_Started")==0;
  }
  public func Inspect() -> String {
    return "Native Padre U6: ready/request/issued="+ToString(this.Own("Ready"))+"/"+ToString(this.Own("Request"))+"/"+ToString(this.Own("Issued"))+" permit/fault="+ToString(this.Own("Permit"))+"/"+ToString(this.Own("Fault"))+" originalLifetimeClosed="+ToString(this.OriginalLifetimeClosed())+" idle="+ToString(this.IdleProtocol())+" unencountered="+ToString(this.UnencounteredPilot())+" request/queue/startDone/endDone="+ToString(this.Fact("holo_padre_calls_v_start_activate"))+"/"+ToString(this.Fact("holo_padre_calls_v_start_activate_count"))+"/"+ToString(this.Fact("holo_padre_calls_v_start_done"))+"/"+ToString(this.Fact("holo_padre_calls_v_end_done"))+" start/endCounts="+ToString(this.Fact("holo_padre_calls_v_start_count"))+"/"+ToString(this.Fact("holo_padre_calls_v_end_count"))+" | Original Padre controller/scene referenced unchanged. Issued is entry bookkeeping, not call-success proof; no global initializer/reset. Shared interruption service and stock fixer credit remain separate.";
  }
  public func Start(confirmation: String) -> String {
    if !Equals(confirmation,"DISPOSABLE_SAVE") { return "Refused: DISPOSABLE_SAVE required."; }
    if this.Own("Request")!=0 || this.Own("Issued")!=0 { return "Already requested/issued; no restart. "+this.Inspect(); }
    if this.Own("Ready")!=1 || this.Own("Revision")!=1 || this.Own("Fault")!=0 || this.Own("Permit")!=0 { return "Refused: U6 archive not ready or interrupted request. "+this.Inspect(); }
    if !this.OriginalLifetimeClosed() || !this.UnencounteredPilot() || !this.IdleProtocol() { return "Refused: completed native shutdown, unused Jeopardy and idle balanced phone state required; nothing reset. "+this.Inspect(); }
    if !this.Set("Request",1) { this.Set("Fault",1);return "Request readback failed; no retry."; }
    return "Queued original Padre handler. Close CET/menus and holster for5 seconds, then Inspect before starting Jeopardy. "+this.Inspect();
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch!=this.epoch { return; };this.Schedule();
    if this.Own("Request")!=1 || this.Own("Issued")!=0 { return; }
    let p=GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    let phone=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PhoneSystem") as PhoneSystem;
    let permit=this.OriginalLifetimeClosed() && this.UnencounteredPilot() && this.IdleProtocol() && this.Own("Fault")==0 && IsDefined(p) && CyberwarePolicy.Safe(p) && IsDefined(phone) && phone.IsPhoneEnabled() && phone.IsCallingEnabled() && !GameInstance.GetPhoneManager(this.GetGameInstance()).IsPhoneCallActive() ? 1 : 0;
    if this.Own("Permit")!=permit && !this.Set("Permit",permit) { this.Set("Fault",1); }
  }
}
public class NativePadreTickU6 extends DelayCallback {
  private let owner: wref<NativePadreU6>;private let epoch: Int32;
  public static func Create(owner: ref<NativePadreU6>,epoch: Int32) -> ref<NativePadreTickU6> { let t=new NativePadreTickU6();t.owner=owner;t.epoch=epoch;return t; }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}
@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void { wrappedMethod(gameInstance);let s=GameInstance.GetScriptableSystemsContainer(gameInstance).Get(n"PTFR.ActivityStateR3.NativePadreU6") as NativePadreU6;if IsDefined(s) { s.Restored(); } }
