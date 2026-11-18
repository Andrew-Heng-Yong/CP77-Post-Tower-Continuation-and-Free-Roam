module PTFR.LoadingCoverLC1
import PTFR.SideJobsS2.*
import PTFR.SideJobsS22.*
import PTFR.SideJobsS23.*
import PTFR.SideJobsS24.*
import PTFR.SideJobsS25.*
import PTFR.SideJobsS27.*
import PTFR.SideJobsS28.*
import PTFR.GigsU10.*
import Codeware.UI.*
import PTFR.ActivityStateR3.*
import PTFR.HistorySnapshotHS1.*
import PTFR.RestrictionsR1.*
import PTFR.RestrictionsR2.*
import PTFR.RestrictionsR3.*
import PTFR.Housing.*
import PTFR.RestorationBaseline.*

// ORIGINAL: r6/scripts/TowerContinued_Loading_LC1/SetupAdaptersLC1.reds
public abstract class SetupAdaptersLC1 {
  public static func Ready(game:GameInstance) -> Bool {
    let container=GameInstance.GetScriptableSystemsContainer(game);
    let s0=container.Get(n"PTFR.SideJobsS2.SideJobsS2") as SideJobsS2;if !IsDefined(s0) || !s0.LC1SetupReady() { return false; }
    let s1=container.Get(n"PTFR.SideJobsS22.SideJobsS22") as SideJobsS22;if !IsDefined(s1) || !s1.LC1SetupReady() { return false; }
    let s2=container.Get(n"PTFR.SideJobsS23.SideJobsS23") as SideJobsS23;if !IsDefined(s2) || !s2.LC1SetupReady() { return false; }
    let s3=container.Get(n"PTFR.SideJobsS24.SideJobsS24") as SideJobsS24;if !IsDefined(s3) || !s3.LC1SetupReady() { return false; }
    let s4=container.Get(n"PTFR.SideJobsS25.SideJobsS25") as SideJobsS25;if !IsDefined(s4) || !s4.LC1SetupReady() { return false; }
    let s5=container.Get(n"PTFR.SideJobsS27.SideJobsS27") as SideJobsS27;if !IsDefined(s5) || !s5.LC1SetupReady() { return false; }
    let s6=container.Get(n"PTFR.SideJobsS28.SideJobsS28") as SideJobsS28;if !IsDefined(s6) || !s6.LC1SetupReady() { return false; }
    let s7=container.Get(n"PTFR.GigsU10.GigsU10") as GigsU10;if !IsDefined(s7) || !s7.LC1SetupReady() { return false; }
    return true;
  }
}

// ORIGINAL: r6/scripts/TowerContinued_Loading_LC1/StartupCoverLC1.reds
// All UI/session state is transient. No completed migration or quest is reset.
public class StartupCoverLC1 extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let released: Bool;
  private let leaving: Bool;
  private let continuation: Bool;
  private let popup: ref<SetupPopupLC1>;
  private let creditsCoverRequested: Bool;
  private let creditsCanvas: ref<inkCanvas>;
  private let creditsView: ref<SetupCoverViewLC5>;
  private let visible: Bool;
  private let started: Float;
  private let stableSince: Float;
  private let stage: String;
  private let stageReason: CName;
  private let detail: String;
  private let attachedAt: Float;
  private let listener: Uint32;
  private let registered: Bool;
  private let rendered: Bool;
  private let completedSteps: Int32;
  private let engineStarted: Float;
  private let lastHeartbeat: Float;
  private let travelSampleAt: Float;
  private let presentationAt:Float;
  private let presentationTrips:Int32;
  private let presentationCaptures:Int32;
  private let presentationRepairState:Int32;
  private let presentationRepairAt:Float;
  private let presentationRepairActor:wref<PlayerPuppet>;
  private let presentationStateCaptures:Int32;
  private let presentationUIState:CName;
  private let photoRefresh: ref<TowerPhotoRefresh>;
  private let photoRefreshResult: CName;
  public static func Get(game: GameInstance) -> ref<StartupCoverLC1> {
    return GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.LoadingCoverLC1.StartupCoverLC1") as StartupCoverLC1;
  }
  public static func GameplayReleased(game: GameInstance) -> Bool {
    let s=StartupCoverLC1.Get(game);
    return IsDefined(s) && (!s.Required() || (s.released && !s.leaving));
  }
  private func Now() -> Float { return EngineTime.ToFloat(GameInstance.GetSimTime(this.GetGameInstance())); }
  private func EngineNow() -> Float { return EngineTime.ToFloat(GameInstance.GetEngineTime(this.GetGameInstance())); }
  private func Fact(n:CName) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(n); }
  private func TowerCompleted() -> Bool {
    return this.Fact(n"q307_2079")==1 &&
      this.Fact(n"q307_done")==1 && this.Fact(n"q307_finished")==1 && this.Fact(n"q307_active")==0;
  }
  private func Required() -> Bool {
    return this.Fact(n"PTFRPA2_Started")==1 && this.TowerCompleted();
  }
  private func OnAttach() -> Void {
    this.running=true;
    this.Restored();
    let pool=SetupPopupPoolLC1.Get();
    if IsDefined(pool) { pool.BindSession(this); }
  }
  private func OnDetach() -> Void {
    let pool=SetupPopupPoolLC1.Get();
    if IsDefined(pool) { pool.UnbindSession(this); }
    this.ClearPhotoRefresh();
    this.EndCreditsCover(n"session-detached");
    this.running=false;this.epoch+=1;this.Unregister();this.Drop();
  }
  private func Unregister() -> Void {
    if this.registered { GameInstance.GetQuestsSystem(this.GetGameInstance()).UnregisterListener(n"PTFRPA2_Started",this.listener);this.registered=false; }
  }
  public func Restored() -> Void {
    this.ClearPhotoRefresh();
    this.photoRefreshResult = n"";
    this.EndCreditsCover(n"session-restored");
    this.Unregister();this.Drop();this.epoch+=1;this.released=false;this.leaving=false;
    this.started=-1.0;this.stableSince=-1.0;this.attachedAt=-1.0;this.stage="";this.detail="";this.stageReason=n"";
    this.rendered=false;this.completedSteps=0;this.engineStarted=-1.0;this.lastHeartbeat=-1.0;
    this.continuation=false;
    this.travelSampleAt=0.0;
    this.presentationAt=0.0;this.presentationTrips=0;this.presentationCaptures=0;
    this.presentationRepairState=0;this.presentationRepairAt=0.0;
    this.presentationRepairActor=null;this.presentationStateCaptures=0;this.presentationUIState=n"";
    this.listener=GameInstance.GetQuestsSystem(this.GetGameInstance()).RegisterListener(n"PTFRPA2_Started",this,n"OnStarted");this.registered=true;
    this.Ensure();if this.running { this.Schedule(); }
  }
  protected cb func OnStarted(value:Int32) -> Bool { if value==1 { this.Ensure(); };return false; }

  // Called by the live credits menu before its native close handler.
  public func CoverCreditsExit() -> Void {
    if !this.running || this.leaving || this.released || this.continuation || this.creditsCoverRequested ||
       !this.TowerCompleted() || this.Fact(n"PTFRP0_DR02")!=1 ||
       this.Fact(n"PostTowerFreeRoamActive")!=0 || this.Fact(n"PTFRPA2_Finished")!=0 ||
       this.Fact(n"PTFRPA2_Fault")!=0 {
      return;
    }
    this.creditsCoverRequested=true;
    this.LogCreditsCover(n"credits-closing");
    if !this.AttachCreditsCover() { this.LogCreditsCover(n"cover-host-unavailable"); }
  }

  private func AttachCreditsCover() -> Bool {
    let ink=GameInstance.GetInkSystem();
    if !IsDefined(ink) { return false; }
    let layer=ink.GetLayer(n"inkSystemNotificationsLayer");
    if !IsDefined(layer) { return false; }
    let host=layer.GetVirtualWindow();
    if !IsDefined(host) || !host.IsVisible() || host.GetOpacity()<0.999 { return false; }
    if IsDefined(this.creditsCanvas) && this.creditsCanvas.GetParentWidget()==host { return true; }

    // Use the permanent, fade-independent window. Insert behind native prompts.
    this.RemoveCreditsCanvas();
    let canvas=new inkCanvas();
    canvas.SetName(n"PTFR_credits_setup_cover");
    canvas.SetAnchor(inkEAnchor.Fill);
    canvas.SetInteractive(false);
    canvas.SetVisible(false);
    canvas.SetOpacity(1.0);
    let index=0;
    if Equals(host.GetChildOrder(),inkEChildOrder.Backward) { index=-1; }
    canvas.Reparent(host,index);
    this.creditsCanvas=canvas;
    if canvas.GetParentWidget()!=host {
      this.RemoveCreditsCanvas();
      return false;
    }

    this.creditsView=SetupCoverViewLC5.Create(canvas);
    if StrLen(this.stage)>0 {
      this.creditsView.UpdateText(this.stage,this.detail);
      this.creditsView.UpdateProgress(this.completedSteps,12);
    }
    canvas.SetVisible(true);
    this.LogCreditsCover(n"cover-attached");
    return true;
  }

  private func MaintainCreditsCover() -> Void {
    if !this.creditsCoverRequested { return; }
    if !this.TowerCompleted() || this.Fact(n"PTFRP0_DR02")!=1 ||
       (!this.Required() && (this.started>=0.0 || this.Fact(n"PostTowerFreeRoamActive")!=0 ||
        this.Fact(n"PTFRPA2_Finished")!=0 || this.Fact(n"PTFRPA2_Fault")!=0)) {
      this.EndCreditsCover(n"handoff-cancelled");
      return;
    }
    this.AttachCreditsCover();
  }

  private func RemoveCreditsCanvas() -> Void {
    if IsDefined(this.creditsCanvas) {
      this.creditsCanvas.SetVisible(false);
      let parent=this.creditsCanvas.GetParentWidget() as inkCompoundWidget;
      if IsDefined(parent) { parent.RemoveChild(this.creditsCanvas); }
    }
    this.creditsCanvas=null;
    this.creditsView=null;
  }

  private func EndCreditsCover(reason:CName) -> Void {
    if !this.creditsCoverRequested { return; }
    this.RemoveCreditsCanvas();
    this.creditsCoverRequested=false;
    this.LogCreditsCover(reason);
  }

  private func LogCreditsCover(event:CName) -> Void {
    ModLog(n"PTFR_CreditsCover",NameToString(event)+" time="+ToString(this.EngineNow()));
  }

  public func Ensure() -> Void {
    if !this.running || this.released || this.leaving || NotEquals(this.photoRefreshResult, n"") || !this.Required() { return; }
    if this.started<0.0 {
      this.started=this.Now();this.engineStarted=this.EngineNow();
      // Classify once, when the arrival facts first become available in this
      // session. A new handoff retains its cover through final acknowledgement.
      this.continuation=this.Fact(n"PTFRPA2_Finished")==1;
      if this.continuation {
        this.SetStage("Checking restored Tower save","Setup checks are running in the background.");
      }
    }
    if this.continuation || IsDefined(this.popup) { return; }
    let manager=CustomPopupManager.GetInstance();
    if !IsDefined(manager) || !manager.IsInitialized() { return; }
    this.popup=SetupPopupPoolLC1.Get().Show(this,this.epoch);
  }
  public func Attached(epoch:Int32) -> Void {
    if !this.running || epoch!=this.epoch || this.leaving || !IsDefined(this.popup) { return; }
    this.visible=true;this.attachedAt=this.Now();
    this.SetStage("Preparing Tower continuation","Checking your save and the arrival state.");
    if this.creditsCoverRequested { this.LogCreditsCover(n"setup-popup-attached"); }
  }
  public func CoverFrame(epoch:Int32) -> Void {
    if this.Accepts(epoch) && this.visible {
      this.rendered=true;
      if this.creditsCoverRequested { this.LogCreditsCover(n"setup-popup-acknowledged"); }
    }
  }
  public func Accepts(epoch:Int32) -> Bool { return this.running && epoch==this.epoch && !this.leaving && !this.released && !this.continuation && this.Required(); }
  private func Drop() -> Void {
    if IsDefined(this.popup) { this.popup.Dismiss(); }
    this.popup=null;this.visible=false;this.rendered=false;
  }
  // Compatibility entry point only. The setup cover has no exit action.
  public func Leave(epoch:Int32) -> Void {}
  private func SetStage(stage:String,detail:String) -> Void {
    this.SetStageReason(stage,detail,n"");
  }
  private func SetStageReason(stage:String,detail:String,reason:CName) -> Void {
    if NotEquals(this.stage,stage) || NotEquals(this.stageReason,reason) {
      ModLog(n"PTFR_LoadingLC3","build=TH1 elapsedSim="+ToString(this.Now()-this.started)+" stage="+stage+" reason="+NameToString(reason)+" | "+detail);
    }
    this.stage=stage;this.detail=detail;this.stageReason=reason;
    this.UpdateCoverText(stage,detail);
    if IsDefined(this.popup) { this.popup.UpdateProgress(this.completedSteps,12); }
    if IsDefined(this.creditsView) { this.creditsView.UpdateProgress(this.completedSteps,12); }
  }
  private func UpdateCoverText(title:String,body:String) -> Void {
    if IsDefined(this.popup) { this.popup.UpdateText(title,body); }
    if IsDefined(this.creditsView) { this.creditsView.UpdateText(title,body); }
  }
  private func EndingFacts() -> String {
    return "active="+ToString(this.Fact(n"PostTowerFreeRoamActive"))+" DR13="+ToString(this.Fact(n"PTFRP0_DR13"))+
      " done/finished="+ToString(this.Fact(n"q307_done"))+"/"+ToString(this.Fact(n"q307_finished"))+
      " q307active="+ToString(this.Fact(n"q307_active"))+" 2079="+ToString(this.Fact(n"q307_2079"))+
      " killed="+ToString(this.Fact(n"q307_main_game_killed"))+"/"+ToString(this.Fact(n"q307_ep1_killed"))+
      " Johnny="+ToString(this.Fact(n"q305_johnny_scene_active"))+" PONR="+ToString(this.Fact(n"q115_point_of_no_return"))+
      " Q307Start/PONR="+ToString(this.Fact(n"q307_start"))+"/"+ToString(this.Fact(n"q307_point_of_no_return"))+
      " rooftop seated/call/confirm/wait="+ToString(this.Fact(n"q307_rooftop_q115_seated"))+"/"+
      ToString(this.Fact(n"q307_q115_call_done"))+"/"+ToString(this.Fact(n"q307_confirm_av_done"))+"/"+ToString(this.Fact(n"q307_q115_wait"))+
      " DR02/07/12="+ToString(this.Fact(n"PTFRP0_DR02"))+"/"+ToString(this.Fact(n"PTFRP0_DR07"))+"/"+ToString(this.Fact(n"PTFRP0_DR12"))+
      " Q115 test/suicide="+ToString(this.Fact(n"q115_var_test_def"))+"/"+ToString(this.Fact(n"q115_suicide_ending"))+
      " Q307 debug/roofTest="+ToString(this.Fact(n"q307_debug_reset"))+"/"+ToString(this.Fact(n"q307_rooftop_chicken"));
  }
  private func Heartbeat() -> Void {
    if this.EngineNow()-this.lastHeartbeat<5.0 { return; }this.lastHeartbeat=this.EngineNow();
    ModLog(n"PTFR_LoadingLC3",this.Status()+" engineElapsed="+ToString(this.EngineNow()-this.engineStarted)+
      " frame="+ToString(this.rendered)+" ack="+ToString(this.Fact(n"PTFRLC1_CoverReady"))+
      " teleported="+ToString(this.Fact(n"PTFRPA2_Teleported"))+" nativeFade="+ToString(this.Fact(n"PTFRPA3_CoverReleased"))+
      " camera="+ToString(this.Fact(n"PTFRPA4_CameraAligned"))+" control="+ToString(this.Fact(n"PTFRPA2_ControlReady"))+
      " prepared/reveal/finished="+ToString(this.Fact(n"PTFRPA2_Prepared"))+"/"+ToString(this.Fact(n"PTFRPA2_Reveal"))+"/"+ToString(this.Fact(n"PTFRPA2_Finished"))+
      " fault="+ToString(this.Fact(n"PTFRPA2_Fault"))+" | "+this.EndingFacts());
    if this.completedSteps>=10 {
      let game=this.GetGameInstance();let arrival=GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.ActivityStateR3.PreAlphaArrivalPA1") as PreAlphaArrivalPA1;
      let player=GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
      if IsDefined(arrival) { ModLog(n"PTFR_LoadingLC3","Control diagnostic: "+arrival.Status()+" bodySafe="+ToString(BodyPolicy.Safe(player))); }
      ModLog(n"PTFR_LoadingLC3","Housing purchase scenes north/japan/glen/corpo="+ToString(this.Fact(n"PTFRH1_northside_PurchaseSceneActive"))+"/"+ToString(this.Fact(n"PTFRH1_japantown_PurchaseSceneActive"))+"/"+ToString(this.Fact(n"PTFRH1_glen_PurchaseSceneActive"))+"/"+ToString(this.Fact(n"PTFRH1_corpo_PurchaseSceneActive")));
    }
  }
  private func Check() -> Bool {
    let game=this.GetGameInstance();let player=GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
    let arrival=GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.ActivityStateR3.PreAlphaArrivalPA1") as PreAlphaArrivalPA1;
    let entry=PreAlphaEntry.Get(game);let snapshot=SnapshotStateHS1.Get(game);
    let chrome=CyberwarePolicy.Get(game);let body=BodyPolicy.Get(game);let profile=ProfilePolicy.Get(game);
    let housing=HousingState.Get(game);
    let world=GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.RestorationBaseline.RestorationBaseline") as RestorationBaseline;
    this.completedSteps=1;
    if !IsDefined(player) || !player.IsAttached() || player.IsDead() || player.IsReplacer() { this.SetStage("Waiting for V","Waiting for the local player to finish loading.");return false; }
    this.completedSteps=2;
    if !IsDefined(entry) || !IsDefined(arrival) || !IsDefined(snapshot) ||
      !IsDefined(chrome) || !IsDefined(body) || !IsDefined(profile) || !IsDefined(housing) || !IsDefined(world) {
      this.SetStage("Setup module unavailable","entry/arrival/history/chrome/body/profile/housing/world: "+ToString(IsDefined(entry))+"/"+ToString(IsDefined(arrival))+"/"+ToString(IsDefined(snapshot))+"/"+ToString(IsDefined(chrome))+"/"+ToString(IsDefined(body))+"/"+ToString(IsDefined(profile))+"/"+ToString(IsDefined(housing))+"/"+ToString(IsDefined(world)));return false;
    }
    let ending = CyberwarePolicy.CompletionBlocker(game);
    if NotEquals(ending,n"") {
      let routeHold = Equals(ending,n"q115_route_conflict") || Equals(ending,n"q115_rooftop_unverified");
      this.SetStageReason(routeHold ? "Tower route needs verification" : "Finishing the ending handoff",
        NameToString(ending)+" | preparation fault="+ToString(this.Fact(n"PTFRPA2_Fault"))+"\n"+this.EndingFacts(),ending);
      return false;
    }
    if !entry.SnapshotInitializationHealthy() { this.SetStage("Entry setup stopped","The entry module reports a fault; setup remains covered.");return false; }
    let healthFailure=profile.LC1HealthFailure();
    if NotEquals(healthFailure,"") { this.SetStage("Health setup stopped",healthFailure);return false; }
    if (this.Fact(n"PTFRPA2_Fault")!=0 && this.Fact(n"PTFRPA2_Fault")!=2) || this.Fact(n"PTFRPA5O_Fault")!=0 ||
      this.Fact(n"PTFRH1_Fault")!=0 || profile.PTFRPAFaulted() || body.PTFRR3Faulted() || !chrome.PTFRR2Healthy() {
      let cd1Flags="Arrival/optics/housing faults: "+ToString(this.Fact(n"PTFRPA2_Fault"))+"/"+ToString(this.Fact(n"PTFRPA5O_Fault"))+"/"+ToString(this.Fact(n"PTFRH1_Fault"))+"\nBody/profile/cyberware fault: "+ToString(body.PTFRR3Faulted())+"/"+ToString(profile.PTFRPAFaulted())+"/"+ToString(!chrome.PTFRR2Healthy());
      if NotEquals(this.stage,"Setup stopped") {
        ModLog(n"PTFR_CyberwareCD1",cd1Flags+"\nBody: "+body.GetStatus()+"\nProfile: "+profile.GetStatus()+"\nCyberware: "+chrome.GetStatus()+"\nCyberware audit: "+chrome.GetAudit());
      }
      let profileFault=profile.PTFRPAFaulted() ? profile.GetStatus()+"\n" : "";
      this.SetStage("Setup stopped",profileFault+cd1Flags+"\n"+(!chrome.PTFRR2Healthy() ? "Cyberware item-preservation check failed." : "A setup safety check failed.")+"\nCD1 details are in CET gamelog.log. Keep the original test save.");return false;
    }
    let initialization=profile.LC1InitializationStatus();
    if !profile.PTFRPAConfigured() && NotEquals(initialization,"") {
      this.SetStage(profile.LC1InitializationHeld() ? "Profile initialization stopped" : "Waiting for profile initialization",initialization);return false;
    }
    this.completedSteps=3;
    if !snapshot.Ready() {
      if snapshot.Faulted() { this.SetStageReason("Quest history setup stopped",snapshot.Status(),n"snapshot_fault"); }
      else {
        let exportReady=snapshot.CanExport();
        this.SetStageReason(exportReady ? "Verifying quest history file" : "Recording quest history",snapshot.Status(),
          exportReady ? n"snapshot_export_pending" : n"snapshot_capture_pending");
      }
      return false;
    }
    this.completedSteps=4;
    let recovery=SnapshotRecoveryHS1.Get(game);
    if this.Fact(n"PTFRPA2_Fault")==2 {
      this.SetStageReason("Checking interrupted setup",IsDefined(recovery) ? recovery.Status() : "Preparation recovery is unavailable.",
        IsDefined(recovery) ? recovery.SetupBlocker() : n"recovery_module_unavailable");
      return false;
    }
    if !arrival.Completed() { this.SetStage("Preparing arrival","Waiting for the camera, optics and normal player control.");return false; }
    this.completedSteps=5;
    if !profile.PTFRPAComplete() || !profile.LC1PhysicalReady() || !profile.LC1LedgerValid(player) || !body.PTFRR3Complete() || !chrome.PTFRR2Ready(player) {
      this.SetStage("Updating V's profile",body.LC1Progress()+"\n"+profile.LC1Progress());return false;
    }
    this.completedSteps=6;
    if !housing.HousingReadyForReveal() { this.SetStage("Preparing homes","Waiting for housing and relationship access to be acknowledged.");return false; }
    this.completedSteps=7;
    if !world.H10GeometryReady() || (housing.Entitled("h10") && !world.H10ActionsArmed()) {
      this.SetStage("Preparing the world","Waiting for H10 geometry and the services your ownership permits.");return false;
    }
    this.completedSteps=8;
    if (!this.continuation && !entry.LC1DispatchChecked()) || this.Fact(n"PTFRPA2_Prepared")!=1 || this.Fact(n"PTFRPA2_Reveal")!=1 || this.Fact(n"PTFRPA2_Finished")!=1 {
      if IsDefined(recovery) && recovery.Resuming() {
        this.SetStageReason("Completing recovered setup",recovery.Status(),recovery.SetupBlocker());
      } else { this.SetStage("Completing the handoff","Waiting for the final native arrival acknowledgement."); }
      return false;
    }
    this.completedSteps=9;
    if !this.continuation && !SetupAdaptersLC1.Ready(game) { this.SetStage("Checking available jobs","Classifying supported jobs; preserving completed or unsupported progress.");return false; }
    this.completedSteps=10;
    if !this.continuation && (!arrival.LC1ControlReady() || !BodyPolicy.Safe(player)) { this.SetStage("Checking player control","Waiting for the final camera and safe player state.");return false; }
    if GameInstance.GetPlayerSystem(game).GetLocalPlayerControlledGameObject()!=player { this.SetStage("Checking player control","Waiting for V to be attached to the loaded world.");return false; }
    this.completedSteps=11;
    return true;
  }
  private func Schedule() -> Void { GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(SetupTickLC1.Create(this,this.epoch),0.10,false); }
  public func Poll(epoch:Int32) -> Void {
    if !this.running || epoch!=this.epoch { return; }this.Schedule();
    if this.leaving || this.released { return; }
    if IsDefined(this.photoRefresh) {
      // Fallback whenever simulation is running. CET drives the normal deadline
      // checks even when Photo Mode has paused simulation.
      if this.EngineNow() > this.photoRefresh.deadline + 1.0 {
        this.FinishPhotoRefresh(n"watchdog-timeout");
      }
      return;
    }
    this.MaintainCreditsCover();
    if !this.Required() { this.Drop();return; }
    if NotEquals(this.photoRefreshResult, n"") && GameInstance.GetPhotoModeSystem(this.GetGameInstance()).IsPhotoModeActive() {
      return;
    }
    this.Ensure();
    if !this.continuation && Equals(this.photoRefreshResult, n"") {
      if !this.visible { return; }
      // The first arrival acknowledges a drawn cover before releasing the native fade.
      if this.rendered && this.Fact(n"PTFRLC1_CoverReady")!=1 {
        GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(n"PTFRLC1_CoverReady",1);
      }
      if !this.rendered { this.SetStage("Preparing the loading cover","Waiting for the interface to draw.");this.Heartbeat();return; }
    }
    if !this.Check() {
      this.stableSince=-1.0;
      this.Heartbeat();
      if this.EngineNow()-this.engineStarted>=120.0 && IsDefined(this.popup) && Equals(this.stageReason,n"") {
        this.UpdateCoverText("Setup is taking longer than expected",this.stage+"\n"+this.detail);
      }
      return;
    }
    if this.stableSince<0.0 { this.stableSince=this.Now(); }
    if this.Now()-this.stableSince<1.0 { this.SetStage("Final checks","All setup stages acknowledged. Checking stability.");return; }
    if this.BeginPhotoRefresh() { return; }
    this.ReleaseSetup();
  }

  private func ReleaseSetup() -> Void {
    this.completedSteps=12;this.SetStage("Ready","All required setup checks passed.");this.Heartbeat();
    this.released=true;this.Drop();
    this.EndCreditsCover(n"setup-released");
  }

  private func BeginPhotoRefresh() -> Bool {
    // The credits cover is owned by this session's native credits close.
    // Restored completed saves and interrupted handoffs cannot open Photo Mode.
    if this.continuation || NotEquals(this.photoRefreshResult, n"") ||
       !this.creditsCoverRequested || !this.AttachCreditsCover() {
      return false;
    }
    let players = GameInstance.GetPlayerSystem(this.GetGameInstance());
    let player = players.GetLocalPlayerMainGameObject() as PlayerPuppet;
    let refresh = new TowerPhotoRefresh();
    refresh.player = player;
    refresh.deadline = this.EngineNow() + 2.5;
    this.photoRefresh = refresh;
    this.photoRefreshResult = n"waiting-for-setup-popup";
    this.SetStage("Refreshing V's view", "");
    // The permanent cover stays up while the blocking notification detaches.
    this.Drop();
    return true;
  }

  private func ClearPhotoRefresh() -> Void {
    let refresh = this.photoRefresh;
    this.photoRefresh = null;
    if IsDefined(refresh) { refresh.RemoveMenuCover(); }
  }

  private func FinishPhotoRefresh(result: CName, opt gameplayCameraReady: Bool) -> Void {
    this.photoRefreshResult = result;
    this.LogPhotoRefresh(result);
    this.ClearPhotoRefresh();
    if gameplayCameraReady {
      this.ReleaseSetup();
    } else {
      // Return control to the native UI if it is still up. Poll can finish the
      // ordinary setup checks when the original gameplay conditions return.
      this.stableSince = -1.0;
      this.EndCreditsCover(n"photo-refresh-ended");
    }
  }

  private func LogPhotoRefresh(event: CName) -> Void {
    ModLog(n"PTFR_PhotoRefresh", NameToString(event) + " time=" + ToString(this.EngineNow()));
  }

  public func PhotoRefreshStatus() -> String {
    return "Tower Photo Mode refresh: " + NameToString(this.photoRefreshResult);
  }

  public func PhotoRefreshUpdate() -> Bool {
    let refresh = this.photoRefresh;
    if !this.running || this.leaving || !IsDefined(refresh) { return false; }

    let game = this.GetGameInstance();
    let players = GameInstance.GetPlayerSystem(game);
    let player = refresh.player;
    let mode = GameInstance.GetPhotoModeSystem(game);
    let now = this.EngineNow();
    if !this.Required() || !IsDefined(player) || !player.IsAttached() || player.IsDead() ||
       players.GetLocalPlayerMainGameObject() != player ||
       players.GetLocalPlayerControlledGameObject() != player || !IsDefined(mode) {
      this.FinishPhotoRefresh(n"player-context-changed");
      return false;
    }

    switch refresh.state {
      case TowerPhotoRefreshState.WaitingForPopup:
        if mode.IsPhotoModeActive() {
          this.FinishPhotoRefresh(n"another-photo-mode-already-open");
          return false;
        }
        let pool = SetupPopupPoolLC1.Get();
        if now >= refresh.deadline {
          this.FinishPhotoRefresh(n"entry-not-ready");
          return false;
        }
        if !IsDefined(pool) || pool.HasPopup() || !this.AttachCreditsCover() || !this.PhotoGameplayReady(player) {
          return true;
        }

        if !refresh.armResumeQueued {
          refresh.armResumeQueued = true;
          this.QueueArmResume(player);
          // Give the queued player events gameplay time before Photo Mode pauses it.
          refresh.photoOpenAfter = this.Now() + 0.35;
          refresh.deadline = MaxF(refresh.deadline, now + 1.0);
          this.photoRefreshResult = n"arms-resume-queued";
          this.LogPhotoRefresh(this.photoRefreshResult);
          return true;
        }
        if this.Now() < refresh.photoOpenAfter || !mode.CanPhotoModeBeEnabled() { return true; }

        refresh.state = TowerPhotoRefreshState.Opening;
        refresh.deadline = now + 8.0;
        refresh.AttachMenuCover();
        this.photoRefreshResult = n"requested";
        this.LogPhotoRefresh(n"requested");
        let action = new questOpenPhotoMode_NodeType();
        action.factName = "";
        action.forceFppMode = false;
        action.alwaysAllowTPP = false;
        action.lockExitUntilScreenshot = false;
        action.blockOutfitOption = false;
        let node = new questUIManagerNodeDefinition();
        node.type = action;
        GameInstance.GetQuestsSystem(game).ExecuteNode(node, n"In");
        if !mode.IsPhotoModeActive() {
          this.FinishPhotoRefresh(n"entry-rejected");
          return false;
        }
        this.LogPhotoRefresh(n"native-active");
        return true;

      case TowerPhotoRefreshState.Opening:
        if !mode.IsPhotoModeActive() || refresh.menuHidden {
          this.FinishPhotoRefresh(n"photo-mode-interrupted");
          return false;
        }
        let timedOut = now >= refresh.deadline;
        let previewReady = refresh.introFinished && IsDefined(refresh.preview) &&
          refresh.preview.PTFRPhotoPreviewReady();
        if IsDefined(refresh.menu) && refresh.introFinished && refresh.menu.m_anyOptionChanged {
          this.FinishPhotoRefresh(n"photo-mode-user-interaction");
          return false;
        }
        if !timedOut && (!previewReady || now < refresh.earliestExit) { return true; }
        if !IsDefined(refresh.menu) || mode.IsExitLocked() {
          if !timedOut { return true; }
          this.FinishPhotoRefresh(n"photo-mode-exit-unavailable");
          return false;
        }

        refresh.state = TowerPhotoRefreshState.Closing;
        refresh.previewCompleted = previewReady && now >= refresh.earliestExit;
        refresh.cameraReadySince = -1.0;
        refresh.deadline = now + 4.0;
        this.photoRefreshResult = refresh.previewCompleted ? n"exit-requested" : n"exit-requested-after-preview-timeout";
        this.LogPhotoRefresh(this.photoRefreshResult);
        refresh.menu.OnExitConfirmed(true);
        return true;

      case TowerPhotoRefreshState.Closing:
        if now >= refresh.deadline {
          this.FinishPhotoRefresh(n"gameplay-camera-return-timeout");
          return false;
        }
        let photoBoard = GameInstance.GetBlackboardSystem(game).Get(GetAllBlackboardDefs().PhotoMode);
        if mode.IsPhotoModeActive() || !refresh.menuHidden || !IsDefined(photoBoard) ||
           photoBoard.GetBool(GetAllBlackboardDefs().PhotoMode.IsActive) || !this.PhotoGameplayReady(player) {
          refresh.cameraReadySince = -1.0;
          return true;
        }
        if refresh.cameraReadySince < 0.0 {
          refresh.cameraReadySince = now;
          return true;
        }
        if now - refresh.cameraReadySince < 0.25 { return true; }

        this.FinishPhotoRefresh(refresh.previewCompleted ? n"gameplay-camera-restored" : n"camera-restored-after-preview-timeout", true);
        return false;
    }
    return false;
  }

  private func QueueArmResume(player: ref<PlayerPuppet>) -> Void {
    // The same three start events that restored hands in the on-foot CET test.
    let upperBody = new PSMStartStateMachine();
    upperBody.stateMachineIdentifier.definitionName = n"UpperBody";
    player.QueueEvent(upperBody);

    let rightHand = new PSMStartStateMachine();
    rightHand.stateMachineIdentifier.definitionName = n"Equipment";
    rightHand.stateMachineIdentifier.referenceName = n"RightHand";
    player.QueueEvent(rightHand);

    let leftHand = new PSMStartStateMachine();
    leftHand.stateMachineIdentifier.definitionName = n"Equipment";
    leftHand.stateMachineIdentifier.referenceName = n"LeftHand";
    player.QueueEvent(leftHand);
  }

  private func PhotoGameplayReady(player: ref<PlayerPuppet>) -> Bool {
    let game = this.GetGameInstance();
    let arrival = GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.ActivityStateR3.PreAlphaArrivalPA1") as PreAlphaArrivalPA1;
    return IsDefined(arrival) && arrival.LC1ControlReady() && BodyPolicy.Safe(player) &&
      !player.IsInCombat() && !GameInstance.GetMountingFacility(game).IsMountedToAnything(player.GetEntityID());
  }

  public func PhotoMenuShown(menu: ref<gameuiPhotoModeMenuController>) -> Void {
    let refresh = this.photoRefresh;
    if !IsDefined(refresh) || NotEquals(refresh.state, TowerPhotoRefreshState.Opening) ||
       IsDefined(refresh.menu) || menu.GetPlayerControlledObject() != refresh.player ||
       !GameInstance.GetPhotoModeSystem(this.GetGameInstance()).IsPhotoModeActive() {
      return;
    }
    refresh.menu = menu;
    this.photoRefreshResult = n"menu-shown";
    this.LogPhotoRefresh(refresh.AttachMenuCover() ? n"menu-shown-covered" : n"menu-cover-unavailable");
  }

  public func PhotoMenuIntroFinished(menu: ref<gameuiPhotoModeMenuController>) -> Void {
    let refresh = this.photoRefresh;
    if !IsDefined(refresh) || refresh.menu != menu || refresh.menuHidden || refresh.introFinished ||
       NotEquals(refresh.state, TowerPhotoRefreshState.Opening) { return; }
    refresh.introFinished = true;
    refresh.earliestExit = this.EngineNow() + 0.20;
  }

  public func PhotoMenuHidden(menu: ref<gameuiPhotoModeMenuController>) -> Void {
    let refresh = this.photoRefresh;
    if !IsDefined(refresh) || refresh.menu != menu || refresh.menuHidden { return; }
    refresh.menuHidden = true;
    this.LogPhotoRefresh(n"menu-hidden");
  }

  public func PhotoPreviewSetup(preview: ref<PhotoModePlayerEntityComponent>, player: ref<PlayerPuppet>) -> Void {
    let refresh = this.photoRefresh;
    if !IsDefined(refresh) || NotEquals(refresh.state, TowerPhotoRefreshState.Opening) ||
       player != refresh.player || refresh.menuHidden { return; }
    refresh.preview = preview;
  }

  // Preserve credits-cover pause handling without presentation repair.
  public func HandleCreditsUIState(current: CName) -> Void {
    if !this.running || !this.creditsCoverRequested { return; }
    if Equals(current,n"inkPauseMenuState") {
      if IsDefined(this.photoRefresh) { this.FinishPhotoRefresh(n"pause-opened"); }
      else { this.EndCreditsCover(n"pause-opened"); }
    }
    else { this.MaintainCreditsCover(); }
  }
  public func Status() -> String { return "LC3 visible/released="+ToString(this.visible)+"/"+ToString(this.released)+" steps="+ToString(this.completedSteps)+"/12 elapsedSim="+ToString(this.Now()-this.started)+" | "+this.stage+" | "+this.detail; }
}

public enum TowerPhotoRefreshState {
  WaitingForPopup = 0,
  Opening = 1,
  Closing = 2
}

// This ticket belongs to one setup session and is discarded on restore/detach.
public class TowerPhotoRefresh extends IScriptable {
  public let state: TowerPhotoRefreshState;
  public let deadline: Float;
  public let armResumeQueued: Bool;
  public let photoOpenAfter: Float;
  public let player: wref<PlayerPuppet>;
  public let menu: wref<gameuiPhotoModeMenuController>;
  public let preview: wref<PhotoModePlayerEntityComponent>;
  public let introFinished: Bool;
  public let earliestExit: Float;
  public let previewCompleted: Bool;
  public let menuHidden: Bool;
  public let cameraReadySince: Float;
  private let menuCover: ref<inkCanvas>;

  public func AttachMenuCover() -> Bool {
    let ink = GameInstance.GetInkSystem();
    if !IsDefined(ink) { return false; }
    let layer = ink.GetLayer(n"inkPhotoModeLayer");
    if !IsDefined(layer) { return false; }
    let host = layer.GetVirtualWindow();
    if !IsDefined(host) { return false; }
    if IsDefined(this.menuCover) && this.menuCover.GetParentWidget() == host { return true; }

    // Mask the Photo Mode widgets within their own layer regardless of its
    // ordering relative to the permanent world cover.
    this.RemoveMenuCover();
    let canvas = new inkCanvas();
    canvas.SetName(n"PTFR_tower_photo_mode_cover");
    canvas.SetAnchor(inkEAnchor.Fill);
    canvas.SetInteractive(false);
    canvas.SetOpacity(1.0);
    canvas.SetVisible(true);
    let index = Equals(host.GetChildOrder(), inkEChildOrder.Backward) ? 0 : -1;
    canvas.Reparent(host, index);
    if canvas.GetParentWidget() != host { return false; }
    this.menuCover = canvas;
    let view = SetupCoverViewLC5.Create(canvas);
    view.UpdateText("Refreshing V's view", "");
    view.UpdateProgress(11, 12);
    return true;
  }

  public func RemoveMenuCover() -> Void {
    if IsDefined(this.menuCover) {
      this.menuCover.SetVisible(false);
      let parent = this.menuCover.GetParentWidget() as inkCompoundWidget;
      if IsDefined(parent) { parent.RemoveChild(this.menuCover); }
      this.menuCover = null;
    }
  }
}

public class SetupTickLC1 extends DelayCallback {
  private let owner:wref<StartupCoverLC1>;private let epoch:Int32;
  public static func Create(owner:ref<StartupCoverLC1>,epoch:Int32) -> ref<SetupTickLC1> { let t=new SetupTickLC1();t.owner=owner;t.epoch=epoch;return t; }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}

// A service survives save switches. Retire a pending old notification before
// opening another, so a refused duplicate queue cannot orphan the new blocker.
public class SetupPopupPoolLC1 extends ScriptableService {
  private let current:ref<SetupPopupLC1>;
  private let session:wref<StartupCoverLC1>;
  public static func Get() -> ref<SetupPopupPoolLC1> { return GameInstance.GetScriptableServiceContainer().GetService(n"PTFR.LoadingCoverLC1.SetupPopupPoolLC1") as SetupPopupPoolLC1; }
  public func BindSession(owner:ref<StartupCoverLC1>) -> Void { this.session=owner; }
  public func UnbindSession(owner:ref<StartupCoverLC1>) -> Void {
    if this.session==owner { this.session=null; }
  }
  public func CoverCreditsExit() -> Void {
    if IsDefined(this.session) { this.session.CoverCreditsExit(); }
  }
  public func Show(owner:ref<StartupCoverLC1>,epoch:Int32) -> ref<SetupPopupLC1> {
    if IsDefined(this.current) { return null; }
    this.current=new SetupPopupLC1();this.current.Bind(owner,epoch);
    CustomPopupManager.GetInstance().ShowPopup(this.current);return this.current;
  }
  public func HasPopup() -> Bool { return IsDefined(this.current); }
  public func Released(popup:ref<SetupPopupLC1>) -> Void { if this.current==popup { this.current=null; } }
}

public class SetupCoverViewLC5 extends IScriptable {
  private let title:ref<inkText>;
  private let body:ref<inkText>;
  private let progress:ref<inkRectangle>;
  private let progressLabel:ref<inkText>;

  public static func Create(root:ref<inkCompoundWidget>) -> ref<SetupCoverViewLC5> {
    let view=new SetupCoverViewLC5();
    view.Build(root);
    return view;
  }
  private func Build(root:ref<inkCompoundWidget>) -> Void {
    let bg=new inkRectangle();
    bg.SetName(n"opaqueCover");
    bg.SetAnchor(inkEAnchor.Centered);
    bg.SetAnchorPoint(Vector2(0.5,0.5));
    bg.SetSize(Vector2(32768.0,32768.0));
    bg.SetTintColor(new HDRColor(0.015,0.02,0.025,1.0));
    bg.SetOpacity(1.0);
    bg.SetInteractive(false);
    bg.Reparent(root);
    this.title=this.Text(root,"Preparing Tower continuation",-200.0,48);
    this.body=this.Text(root,"Please wait while your save is prepared.",-60.0,26);
    this.body.SetWrapping(true,1100.0,textWrappingPolicy.PerCharacter);
    let track=new inkRectangle();
    track.SetName(n"setupProgressTrack");
    track.SetSize(Vector2(760.0,18.0));
    track.SetAnchor(inkEAnchor.Centered);
    track.SetAnchorPoint(Vector2(0.5,0.5));
    track.SetMargin(inkMargin(0.0,115.0,0.0,0.0));
    track.SetTintColor(new HDRColor(0.12,0.17,0.20,1.0));
    track.Reparent(root);

    this.progress=new inkRectangle();
    this.progress.SetName(n"setupProgressFill");
    this.progress.SetSize(Vector2(0.0,18.0));
    this.progress.SetAnchor(inkEAnchor.Centered);
    this.progress.SetAnchorPoint(Vector2(0.0,0.5));
    this.progress.SetMargin(inkMargin(-380.0,115.0,0.0,0.0));
    this.progress.SetTintColor(new HDRColor(0.2,0.86,0.90,1.0));
    this.progress.Reparent(root);
    this.progressLabel=this.Text(root,"0%  |  0 / 12 setup checks",155.0,26);
  }
  private func Text(root:ref<inkCompoundWidget>,value:String,y:Float,size:Int32) -> ref<inkText> {
    let text=new inkText();
    text.SetFontFamily("base\\gameplay\\gui\\fonts\\raj\\raj.inkfontfamily");
    text.SetFontStyle(n"Medium");
    text.SetFontSize(size);
    text.SetText(value);
    text.SetAnchor(inkEAnchor.Centered);
    text.SetAnchorPoint(Vector2(0.5,0.5));
    text.SetMargin(inkMargin(0.0,y,0.0,0.0));
    text.SetTintColor(new HDRColor(0.9,0.95,0.96,1.0));
    text.Reparent(root);
    return text;
  }
  public func UpdateText(title:String,body:String) -> Void {
    this.title.SetText(title);
    this.body.SetText(body);
  }
  public func UpdateProgress(completed:Int32,total:Int32) -> Void {
    if total<=0 { return; }
    let count=Clamp(completed,0,total);
    let fraction=Cast<Float>(count)/Cast<Float>(total);
    this.progress.SetSize(Vector2(760.0*fraction,18.0));
    this.progressLabel.SetText(ToString(count*100/total)+"%  |  "+ToString(count)+" / "+ToString(total)+" setup checks");
  }
}

// Native notification owns setup input blocking and the normal cover acknowledgement.
public class SetupPopupLC1 extends CustomPopup {
  private let owner:wref<StartupCoverLC1>;private let epoch:Int32;
  private let view:ref<SetupCoverViewLC5>;
  private let closing:Bool;
  public func Bind(owner:ref<StartupCoverLC1>,epoch:Int32) -> Void { this.owner=owner;this.epoch=epoch; }
  public func GetQueueName() -> CName { return n"PTFR_setup_LC1"; }
  public func IsBlocking() -> Bool { return true; }
  public func UseCursor() -> Bool { return false; }
  protected cb func OnCreate() -> Void {
    super.OnCreate();
    this.view=SetupCoverViewLC5.Create(this.GetRootCompoundWidget());
  }
  private func ActiveCover() -> Bool {
    return !this.closing && IsDefined(this.owner) && this.owner.Accepts(this.epoch);
  }
  protected cb func OnShow() -> Void {
    let root=this.GetRootWidget();
    if !this.ActiveCover() {
      root.SetVisible(false);
      GameInstance.GetDelaySystem(this.GetGame()).DelayCallback(SetupPopupCloseLC1.Create(this),0.0,false);
      return;
    }
    root.SetVisible(true);root.SetOpacity(1.0);
    this.owner.Attached(this.epoch);
    // Acknowledge a fully drawn cover for this session only.
    let alpha=new inkAnimTransparency();alpha.SetStartTransparency(1.0);alpha.SetEndTransparency(1.0);alpha.SetDuration(0.10);
    let anim=new inkAnimDef();anim.AddInterpolator(alpha);
    this.m_transitionAnimProxy=root.PlayAnimation(anim);
    this.m_transitionAnimProxy.RegisterToCallback(inkanimEventType.OnFinish,this,n"OnCoverFrame");
  }
  protected cb func OnCoverFrame(animProxy:ref<inkAnimProxy>) -> Bool {
    this.m_transitionAnimProxy=null;
    if !this.closing && IsDefined(this.owner) { this.owner.CoverFrame(this.epoch); }return false;
  }
  protected cb func OnHide() -> Void {
    if IsDefined(this.m_transitionAnimProxy) { this.m_transitionAnimProxy.Stop();this.m_transitionAnimProxy=null; }
    this.OnHidden();
  }
  protected cb func OnHidden() -> Void { super.OnHidden();SetupPopupPoolLC1.Get().Released(this); }
  protected cb func OnGlobalReleaseInput(evt:ref<inkPointerEvent>) -> Bool {
    if !this.ActiveCover() { return false; }
    evt.Handle();return true;
  }
  public func UpdateText(title:String,body:String) -> Void {
    if IsDefined(this.view) { this.view.UpdateText(title,body); }
  }
  public func UpdateProgress(completed:Int32,total:Int32) -> Void {
    if IsDefined(this.view) { this.view.UpdateProgress(completed,total); }
  }
  public func Dismiss() -> Void {
    this.closing=true;
    if this.IsInitialized() {
      this.GetRootWidget().SetVisible(false);
      this.Detach();
    }
  }
}

public class SetupPopupCloseLC1 extends DelayCallback {
  private let popup:wref<SetupPopupLC1>;
  public static func Create(popup:ref<SetupPopupLC1>) -> ref<SetupPopupCloseLC1> { let c=new SetupPopupCloseLC1();c.popup=popup;return c; }
  public func Call() -> Void { if IsDefined(this.popup) { this.popup.Dismiss(); } }
}

@wrapMethod(MenuScenario_FinalBoards)
protected cb func OnCloseFinalBoardsRequest() -> Bool {
  let menus=this.GetMenusState();
  if IsDefined(menus) && menus.IsMenuOpened(n"finalboards_credits") {
    let pool=SetupPopupPoolLC1.Get();
    if IsDefined(pool) { pool.CoverCreditsExit(); }
  }
  return wrappedMethod();
}

@wrapMethod(PopupsManager)
protected cb func OnPlayerAttach(playerPuppet:ref<GameObject>) -> Bool {
  wrappedMethod(playerPuppet);
  let s=StartupCoverLC1.Get(playerPuppet.GetGame());if IsDefined(s) { s.Ensure(); }
}
@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance:GameInstance) -> Void {
  wrappedMethod(gameInstance);let s=StartupCoverLC1.Get(gameInstance);if IsDefined(s) { s.Restored(); }
}

// Keep the existing credits-cover pause behavior.
@wrapMethod(gameuiInGameMenuGameController)
protected cb func OnUiStateChangedSuccessfully(previousStateName: CName, currentStateName: CName) -> Bool {
  let result=wrappedMethod(previousStateName,currentStateName);
  let player=this.GetPlayerControlledObject();
  if IsDefined(player) {
    let cover=StartupCoverLC1.Get(player.GetGame());
    if IsDefined(cover) { cover.HandleCreditsUIState(currentStateName); }
  }
  return result;
}

@wrapMethod(gameuiPhotoModeMenuController)
protected cb func OnShow(reversedUI: Bool) -> Bool {
  let result = wrappedMethod(reversedUI);
  let player = this.GetPlayerControlledObject();
  if IsDefined(player) {
    let cover = StartupCoverLC1.Get(player.GetGame());
    if IsDefined(cover) { cover.PhotoMenuShown(this); }
  }
  return result;
}

@wrapMethod(gameuiPhotoModeMenuController)
protected cb func OnIntroAnimEnded(proxy: ref<inkAnimProxy>) -> Bool {
  let result = wrappedMethod(proxy);
  let player = this.GetPlayerControlledObject();
  if IsDefined(player) {
    let cover = StartupCoverLC1.Get(player.GetGame());
    if IsDefined(cover) { cover.PhotoMenuIntroFinished(this); }
  }
  return result;
}

@wrapMethod(gameuiPhotoModeMenuController)
protected cb func OnHide() -> Bool {
  let player = this.GetPlayerControlledObject();
  let result = wrappedMethod();
  if IsDefined(player) {
    let cover = StartupCoverLC1.Get(player.GetGame());
    if IsDefined(cover) { cover.PhotoMenuHidden(this); }
  }
  return result;
}

@wrapMethod(PhotoModePlayerEntityComponent)
private final func SetupInventory(isCurrentPlayerObjectCustomizable: Bool) -> Void {
  wrappedMethod(isCurrentPlayerObjectCustomizable);
  let player = this.mainPuppet;
  if IsDefined(player) && player == this.currentPuppet && IsDefined(this.fakePuppet) && this.fakePuppet != player {
    let cover = StartupCoverLC1.Get(player.GetGame());
    if IsDefined(cover) { cover.PhotoPreviewSetup(this, player); }
  }
}

@addMethod(PhotoModePlayerEntityComponent)
public final func PTFRPhotoPreviewReady() -> Bool {
  return ArraySize(this.loadingItems) == 0 && ArraySize(this.loadingVisualItems) == 0;
}

