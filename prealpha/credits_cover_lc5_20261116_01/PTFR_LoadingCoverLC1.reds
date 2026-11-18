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
    this.EndCreditsCover(n"session-detached");
    this.running=false;this.epoch+=1;this.Unregister();this.Drop();
  }
  private func Unregister() -> Void {
    if this.registered { GameInstance.GetQuestsSystem(this.GetGameInstance()).UnregisterListener(n"PTFRPA2_Started",this.listener);this.registered=false; }
  }
  public func Restored() -> Void {
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
    if !this.running || this.released || this.leaving || !this.Required() { return; }
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
    if this.travelSampleAt>0.0 && this.EngineNow()>=this.travelSampleAt {
      this.travelSampleAt=0.0;
      this.TraceFastTravel(n"follow-up");
    }
    if this.presentationAt>0.0 && this.EngineNow()>=this.presentationAt {
      this.presentationAt=0.0;
      if this.Required() && this.Fact(n"PTFRPA2_Finished")==1 {
        this.TracePresentation(n"ready-plus-3s");
      }
    }
    if this.leaving || this.released { return; }
    this.MaintainCreditsCover();
    this.FinishBodyReturnTP3();
    if !this.Required() { this.Drop();return; }
    this.Ensure();
    if !this.continuation {
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
    if !this.FinishPresentationTP2() { this.stableSince=-1.0;this.Heartbeat();return; }
    if this.stableSince<0.0 { this.stableSince=this.Now(); }
    if this.Now()-this.stableSince<1.0 { this.SetStage("Final checks","All setup stages acknowledged. Checking stability.");return; }
    this.completedSteps=12;this.SetStage("Ready","All required setup checks passed.");this.Heartbeat();
    this.released=true;this.Drop();
    this.EndCreditsCover(n"setup-released");
    this.presentationAt=this.EngineNow()+3.0;
  }
  private func TracePresentation(reason: CName) -> Void {
    if this.presentationCaptures>=10 { return; }
    this.presentationCaptures+=1;
    PresentationTraceTP1.Capture(this.GetGameInstance(),reason);
  }
  public func TraceFastTravel(stage: CName) -> Void {
    if !this.running || !this.Required() || this.Fact(n"PTFRPA2_Finished")!=1 { return; }
    if Equals(stage,n"native-start") {
      this.travelSampleAt=this.EngineNow()+5.0;
      this.presentationTrips+=1;
    }
    if this.presentationTrips>0 && this.presentationTrips<=3 &&
      (Equals(stage,n"native-start") || Equals(stage,n"follow-up") || Equals(stage,n"native-finished")) {
      this.TracePresentation(stage);
    }
    let game=this.GetGameInstance();
    let defs=GetAllBlackboardDefs().FastTRavelSystem;
    let boards=GameInstance.GetBlackboardSystem(game);
    let travel=boards.Get(defs);
    if !IsDefined(travel) { return; }
    let start=FromVariant<TweakDBID>(travel.GetVariant(defs.StartingPoint));
    let destination=FromVariant<TweakDBID>(travel.GetVariant(defs.DestinationPoint));
    let player=GameInstance.GetPlayerSystem(game).GetLocalPlayerControlledGameObject();
    let position="unavailable";
    if IsDefined(player) {
      let point=player.GetWorldPosition();
      position=ToString(point.X)+"/"+ToString(point.Y)+"/"+ToString(point.Z);
    }
    let popups=SetupPopupPoolLC1.Get();
    let ui=boards.Get(GetAllBlackboardDefs().UI_System);
    let inMenu=IsDefined(ui) && ui.GetBool(GetAllBlackboardDefs().UI_System.IsInMenu);
    ModLog(n"PTFR_FastTravel", NameToString(stage)+" start="+TDBID.ToStringDEBUG(start)+
      " destination="+TDBID.ToStringDEBUG(destination)+" player="+position+
      " started/loading/finished="+ToString(travel.GetBool(defs.FastTravelStarted))+"/"+
      ToString(travel.GetBool(defs.FastTravelLoadingScreenStarted))+"/"+
      ToString(travel.GetBool(defs.FastTravelLoadingScreenFinished))+
      " cover visible/released/popup="+ToString(this.visible)+"/"+ToString(this.released)+"/"+
      ToString(IsDefined(popups) && popups.HasPopup())+" inMenu="+ToString(inMenu));
  }
  // Native arrival, job and control checks have passed before this is called.
  // A presentation repair can wait briefly for stock hands, then yield to gameplay.
  private func FinishPresentationTP2() -> Bool {
    if this.continuation || this.presentationRepairState >= 4 { return true; }
    let now = this.EngineNow();
    if this.presentationRepairState == 3 {
      if now < this.presentationRepairAt { return false; }
      this.presentationRepairState = 4;
      this.TracePresentation(n"handoff-presentation-return");
      return true;
    }
    if this.presentationRepairState == 2 { return false; }
    if this.presentationRepairState == 0 {
      this.presentationRepairState = 1;
      this.presentationRepairAt = now + 4.0;
      this.SetStage("Restoring player appearance", "Finishing the transition back to gameplay.");
    }
    let game = this.GetGameInstance();
    let player = GameInstance.GetPlayerSystem(game).GetLocalPlayerControlledGameObject() as PlayerPuppet;
    let chrome = CyberwarePolicy.Get(game);
    if !this.Accepts(this.epoch) || !this.visible || !this.rendered || !IsDefined(this.popup) ||
       !IsDefined(player) || !player.IsAttached() || !IsDefined(chrome) || !chrome.PTFRTP2HandsSettled() ||
       (NotEquals(this.presentationUIState, n"") && NotEquals(this.presentationUIState, n"inkGameState")) {
      if now < this.presentationRepairAt { return false; }
      this.presentationRepairState = 4;
      ModLog(n"PTFR_PresentationTP2", "Appearance refresh skipped after waiting for stock hands or safe presentation.");
      return true;
    }

    this.TryEndingLoadingCleanup();
    this.presentationRepairActor = player;
    this.presentationRepairState = 2;
    this.presentationRepairAt = now + 1.0;
    player.QueueEvent(new ActivateTPPRepresentationEvent());
    ModLog(n"PTFR_PresentationTP2", "Body refresh: native representation activation queued under setup cover.");
    return false;
  }

  // These flags and controllers guard only the optional loading cleanup.
  private func TryEndingLoadingCleanup() -> Void {
    let game = this.GetGameInstance();
    let defs = GetAllBlackboardDefs().FastTRavelSystem;
    let travel = GameInstance.GetBlackboardSystem(game).Get(defs);
    if !IsDefined(travel) {
      ModLog(n"PTFR_PresentationTP2", "Ending loading cleanup skipped: travel blackboard unavailable.");
      return;
    }
    let started = travel.GetBool(defs.FastTravelStarted);
    let loading = travel.GetBool(defs.FastTravelLoadingScreenStarted);
    if started || loading {
      ModLog(n"PTFR_PresentationTP2", "Ending loading cleanup skipped: travel started/loading=" + ToString(started) + "/" + ToString(loading));
      return;
    }
    let ink = GameInstance.GetInkSystem();
    let controllerCount = -1;
    if IsDefined(ink) {
      let layer = ink.GetLayer(n"inkLoadingLayer");
      if IsDefined(layer) { controllerCount = ArraySize(layer.GetGameControllers()); }
    }
    if controllerCount != 0 {
      ModLog(n"PTFR_PresentationTP2", "Ending loading cleanup skipped: loading controller count=" + ToString(controllerCount));
      return;
    }
    this.popup.QueueBroadcastEvent(new inkHideLoadingScreenDelayedEvent());
    GameInstance.GetUISystem(game).RestorePreviousVisualState(n"inkEndGameLoadingState");
    ModLog(n"PTFR_PresentationTP2", "Ending loading cleanup requested.");
  }

  // Return the same actor before polling setup checks again. A new scene,
  // vehicle or possession can take over representation while the event settles.
  private func FinishBodyReturnTP3() -> Void {
    let now = this.EngineNow();
    if this.presentationRepairState != 2 || now < this.presentationRepairAt { return; }
    this.presentationRepairState = 3;
    this.presentationRepairAt = now + 1.0;
    let game = this.GetGameInstance();
    let player = this.presentationRepairActor;
    let players = GameInstance.GetPlayerSystem(game);
    if !this.Required() || !IsDefined(player) || !player.IsAttached() || player.IsDead() || player.IsReplacer() ||
       players.GetLocalPlayerMainGameObject() != player || players.GetLocalPlayerControlledGameObject() != player || players.IsInFreeCamera() {
      ModLog(n"PTFR_PresentationTP2", "Body refresh return skipped: original player is no longer in normal control.");
      return;
    }
    let scene = GameInstance.GetSceneSystem(game).GetScriptInterface();
    let mount = GameInstance.GetMountingFacility(game).GetMountingInfoSingleWithObjects(player);
    if !IsDefined(scene) || scene.IsEntityInScene(player.GetEntityID()) || EntityID.IsDefined(mount.parentId) ||
       GameInstance.GetWorkspotSystem(game).IsActorInWorkspot(player) {
      ModLog(n"PTFR_PresentationTP2", "Body refresh return yielded to a scene, vehicle or workspot.");
      return;
    }
    player.QueueEvent(new DeactivateTPPRepresentationEvent());
    ModLog(n"PTFR_PresentationTP2", "Body refresh: native first-person return queued under setup cover.");
  }

  public func TraceUIStateTP2(previous: CName, current: CName) -> Void {
    if !this.running { return; }
    if this.creditsCoverRequested {
      // Allow the native pause menu to present its own controls on interruption.
      if Equals(current,n"inkPauseMenuState") {
        this.EndCreditsCover(n"pause-opened");
      } else {
        this.MaintainCreditsCover();
      }
    }
    if !this.Required() { return; }
    this.presentationUIState=current;
    if this.presentationStateCaptures>=24 { return; }
    this.presentationStateCaptures+=1;
    ModLog(n"PTFR_PresentationTP2", "ink state="+NameToString(previous)+" -> "+NameToString(current)+
      " fresh="+ToString(!this.continuation)+" repair="+ToString(this.presentationRepairState));
  }
  public func Status() -> String { return "LC3 visible/released="+ToString(this.visible)+"/"+ToString(this.released)+" steps="+ToString(this.completedSteps)+"/12 elapsedSim="+ToString(this.Now()-this.started)+" | "+this.stage+" | "+this.detail; }
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

// Record native progress and the owned cover state around a post-Tower trip.
@wrapMethod(FastTravelSystem)
private final func SetFastTravelStarted() -> Void {
  wrappedMethod();
  let cover=StartupCoverLC1.Get(this.GetGameInstance());
  if IsDefined(cover) { cover.TraceFastTravel(n"native-start"); }
}

@wrapMethod(FastTravelSystem)
protected cb func OnLoadingScreenFinished(value: Bool) -> Bool {
  let result=wrappedMethod(value);
  if value {
    let cover=StartupCoverLC1.Get(this.GetGameInstance());
    if IsDefined(cover) { cover.TraceFastTravel(n"native-finished"); }
  }
  return result;
}


// TP1 reads presentation state only. Logical attachment/visibility fields do
// not prove rendered pixels; retain that distinction in every assessment.
public abstract class PresentationTraceTP1 {
  public static func Capture(game: GameInstance, reason: CName) -> Void {
    let player=GameInstance.GetPlayerSystem(game).GetLocalPlayerControlledGameObject() as PlayerPuppet;
    if !IsDefined(player) || !player.IsAttached() || player.IsReplacer() { return; }
    ModLog(n"PTFR_PresentationTP1", "capture="+NameToString(reason));
    let ts=GameInstance.GetTransactionSystem(game);
    let data=EquipmentSystem.GetData(player);
    if IsDefined(ts) && IsDefined(data) {
      let arm=ts.GetItemInSlot(player,t"AttachmentSlots.RightArm");
      ModLog(n"PTFR_PresentationTP1", "hands equipped="+TDBID.ToStringDEBUG(ItemID.GetTDBID(data.GetItemInEquipSlot(gamedataEquipmentArea.RightArm,0)))+
        " fists="+TDBID.ToStringDEBUG(ItemID.GetTDBID(data.GetItemInEquipSlot(gamedataEquipmentArea.BaseFists,0)))+
        " attached="+ToString(IsDefined(arm))+" spawning="+ToString(ts.IsSlotSpawningAnyItem(player,t"AttachmentSlots.RightArm")));
      if IsDefined(arm) { PresentationTraceTP1.Meshes(arm,n"RightArm"); }
    }
    PresentationTraceTP1.Meshes(player,n"player");
    let cw=GameInstance.GetScriptableSystemsContainer(game).Get(n"CyberwareCustomizationSystem") as CyberwareCustomizationSystem;
    if IsDefined(cw) {
      let saved=cw.GetSavedData();
      ModLog(n"PTFR_PresentationTP1", "customization enabled="+ToString(saved.enabled)+" switcher="+NameToString(saved.switcherName)+
        " index="+ToString(saved.switcherIndex)+" maxtac="+ToString(saved.hasMaxTacApperanceEquipped));
    }
    PresentationTraceTP1.Layer(n"inkLoadingLayer");
    PresentationTraceTP1.Layer(n"inkMenuLayer");
    PresentationTraceTP1.Layer(n"inkGameNotificationsLayer");
    PresentationTraceTP1.Layer(n"inkHUDLayer");
  }
  private static func Meshes(entity: ref<Entity>, label: CName) -> Void {
    let components=entity.GetComponents();
    let i=0;
    let count=0;
    while i<ArraySize(components) && count<32 {
      let mesh=components[i] as MeshComponent;
      if IsDefined(mesh) {
        ModLog(n"PTFR_PresentationTP1", NameToString(label)+" mesh="+NameToString(mesh.GetName())+
          " type="+NameToString(mesh.GetClassName())+" enabled="+ToString(mesh.IsEnabled())+
          " renderEnabled="+ToString(mesh.isEnabled)+" appearance="+NameToString(mesh.meshAppearance)+" mask="+ToString(mesh.chunkMask)+" plane="+ToString(EnumInt(mesh.renderingPlane)));
        count+=1;
      }
      let skin=components[i] as entSkinnedMeshComponent;
      if IsDefined(skin) && count<32 {
        ModLog(n"PTFR_PresentationTP1", NameToString(label)+" skinnedMesh="+NameToString(skin.GetName())+
          " type="+NameToString(skin.GetClassName())+" enabled="+ToString(skin.IsEnabled())+
          " renderEnabled="+ToString(skin.isEnabled)+" appearance="+NameToString(skin.meshAppearance)+
          " mask="+ToString(skin.chunkMask)+" visibilityParam="+NameToString(skin.visibilityAnimationParam)+
          " renderingPlaneParam="+NameToString(skin.renderingPlaneAnimationParam));
        count+=1;
      }
      i+=1;
    }
    ModLog(n"PTFR_PresentationTP1", NameToString(label)+" components="+ToString(ArraySize(components))+" meshesLogged="+ToString(count));
    let rep=entity.FindComponentByType(n"gameTPPRepresentationComponent") as gameTPPRepresentationComponent;
    if IsDefined(rep) {
      ModLog(n"PTFR_PresentationTP1", NameToString(label)+" TPP configuration detached/attached/affected="+
        ToString(ArraySize(rep.detachedObjectInfo))+"/"+ToString(ArraySize(rep.attachedObjectInfo))+"/"+ToString(ArraySize(rep.affectedAppearanceSlots)));
    }
  }
  private static func Layer(name: CName) -> Void {
    let ink=GameInstance.GetInkSystem();
    if !IsDefined(ink) { return; }
    let layer=ink.GetLayer(name);
    if !IsDefined(layer) { ModLog(n"PTFR_PresentationTP1", NameToString(name)+" unavailable");return; }
    let controllers=layer.GetGameControllers();
    ModLog(n"PTFR_PresentationTP1", NameToString(name)+" controllers="+ToString(ArraySize(controllers)));
    let i=0;
    let remaining=32;
    while i<ArraySize(controllers) && i<8 && remaining>0 {
      let controller=controllers[i];
      if IsDefined(controller) {
        let label=NameToString(name)+"/"+NameToString(controller.GetClassName());
        remaining-=PresentationTraceTP1.Widget(controller.GetRootWidget(),label,0,remaining);
      }
      i+=1;
    }
  }
  private static func Widget(widget: wref<inkWidget>, path: String, depth: Int32, budget: Int32) -> Int32 {
    if !IsDefined(widget) || budget<=0 { return 0; }
    let name=path+"/"+NameToString(widget.GetName());
    let size=widget.GetSize();
    ModLog(n"PTFR_PresentationTP1", name+" visible="+ToString(widget.IsVisible())+" opacity="+ToString(widget.GetOpacity())+
      " size="+ToString(size.X)+"/"+ToString(size.Y));
    let used=1;
    let group=widget as inkCompoundWidget;
    if depth<2 && IsDefined(group) {
      let i=0;
      while i<group.GetNumChildren() && used<budget && i<12 {
        used+=PresentationTraceTP1.Widget(group.GetWidgetByIndex(i),name,depth+1,budget-used);
        i+=1;
      }
    }
    return used;
  }
}

// Observe the real ink state transitions; keep the existing quick-load
// cancellation callback and all native loading behavior intact.
@wrapMethod(gameuiInGameMenuGameController)
protected cb func OnUiStateChangedSuccessfully(previousStateName: CName, currentStateName: CName) -> Bool {
  let result=wrappedMethod(previousStateName,currentStateName);
  let player=this.GetPlayerControlledObject();
  if IsDefined(player) {
    let cover=StartupCoverLC1.Get(player.GetGame());
    if IsDefined(cover) { cover.TraceUIStateTP2(previousStateName,currentStateName); }
  }
  return result;
}

