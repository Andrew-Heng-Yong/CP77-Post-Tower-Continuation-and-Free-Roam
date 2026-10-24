module PTFR.LoadingCoverLC1

import Codeware.UI.*
import PTFR.ActivityStateR3.*
import PTFR.HistorySnapshotHS1.*
import PTFR.RestrictionsR1.*
import PTFR.RestrictionsR2.*
import PTFR.RestrictionsR3.*
import PTFR.Housing.*
import PTFR.RestorationBaseline.*

// All UI/session state is transient. No completed migration or quest is reset.
public class StartupCoverLC1 extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let released: Bool;
  private let leaving: Bool;
  private let continuation: Bool;
  private let popup: ref<SetupPopupLC1>;
  private let visible: Bool;
  private let started: Float;
  private let stableSince: Float;
  private let stage: String;
  private let detail: String;
  private let attachedAt: Float;
  private let listener: Uint32;
  private let registered: Bool;
  private let rendered: Bool;
  private let completedSteps: Int32;
  private let engineStarted: Float;
  private let lastHeartbeat: Float;
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
  private func Required() -> Bool {
    return this.Fact(n"PTFRPA2_Started")==1 && this.Fact(n"q307_2079")==1 &&
      this.Fact(n"q307_done")==1 && this.Fact(n"q307_finished")==1 && this.Fact(n"q307_active")==0;
  }
  private func OnAttach() -> Void { this.running=true;this.Restored(); }
  private func OnDetach() -> Void {
    this.running=false;this.epoch+=1;this.Unregister();this.Drop();
  }
  private func Unregister() -> Void {
    if this.registered { GameInstance.GetQuestsSystem(this.GetGameInstance()).UnregisterListener(n"PTFRPA2_Started",this.listener);this.registered=false; }
  }
  public func Restored() -> Void {
    this.Unregister();this.Drop();this.epoch+=1;this.released=false;this.leaving=false;
    this.started=-1.0;this.stableSince=-1.0;this.attachedAt=-1.0;this.stage="";this.detail="";
    this.rendered=false;this.completedSteps=0;this.engineStarted=-1.0;this.lastHeartbeat=-1.0;
    let game=this.GetGameInstance();let profile=ProfilePolicy.Get(game);let body=BodyPolicy.Get(game);let housing=HousingState.Get(game);
    // A completed save may load in combat, with a weapon, or in a vehicle.
    // Revalidate its receipts and physical state without demanding a new respec.
    this.continuation=this.Fact(n"PTFRPA2_Finished")==1 && IsDefined(profile) && profile.PTFRPAComplete() &&
      IsDefined(body) && body.PTFRR3Complete() && IsDefined(housing) && housing.HousingReadyForReveal();
    this.listener=GameInstance.GetQuestsSystem(this.GetGameInstance()).RegisterListener(n"PTFRPA2_Started",this,n"OnStarted");this.registered=true;
    this.Ensure();if this.running { this.Schedule(); }
  }
  protected cb func OnStarted(value:Int32) -> Bool { if value==1 { this.Ensure(); };return false; }
  public func Ensure() -> Void {
    if !this.running || this.released || this.leaving || !this.Required() { return; }
    if this.started<0.0 { this.started=this.Now();this.engineStarted=this.EngineNow(); }
    if IsDefined(this.popup) { return; }
    let manager=CustomPopupManager.GetInstance();
    if !IsDefined(manager) || !manager.IsInitialized() { return; }
    this.popup=SetupPopupPoolLC1.Get().Show(this,this.epoch);
  }
  public func Attached(epoch:Int32) -> Void {
    if !this.running || epoch!=this.epoch || this.leaving || !IsDefined(this.popup) { return; }
    this.visible=true;this.attachedAt=this.Now();
    this.SetStage("Preparing Tower continuation","Checking your save and the arrival state.");
  }
  public func CoverFrame(epoch:Int32) -> Void {
    if this.Accepts(epoch) && this.visible { this.rendered=true; }
  }
  public func Accepts(epoch:Int32) -> Bool { return this.running && epoch==this.epoch && !this.leaving && !this.released && this.Required(); }
  private func Drop() -> Void {
    if IsDefined(this.popup) { this.popup.Dismiss(); }
    this.popup=null;this.visible=false;this.rendered=false;
  }
  public func Leave(epoch:Int32) -> Void {
    if epoch!=this.epoch || this.leaving { return; }
    this.leaving=true;
    this.SetStage("Returning to the main menu","Setup has not been marked complete.");
    // Keep the blocker until player detach. Escape never exposes unfinished play.
    GameInstance.GetSystemRequestsHandler().GotoMainMenu();
  }
  private func SetStage(stage:String,detail:String) -> Void {
    if NotEquals(this.stage,stage) {
      ModLog(n"PTFR_LoadingLC2","elapsedSim="+ToString(this.Now()-this.started)+" stage="+stage+" | "+detail);
    }
    this.stage=stage;this.detail=detail;
    if IsDefined(this.popup) { this.popup.UpdateText(stage,detail);this.popup.UpdateProgress(this.completedSteps,12); }
  }
  private func EndingFacts() -> String {
    return "active="+ToString(this.Fact(n"PostTowerFreeRoamActive"))+" DR13="+ToString(this.Fact(n"PTFRP0_DR13"))+
      " done/finished="+ToString(this.Fact(n"q307_done"))+"/"+ToString(this.Fact(n"q307_finished"))+
      " q307active="+ToString(this.Fact(n"q307_active"))+" 2079="+ToString(this.Fact(n"q307_2079"))+
      " killed="+ToString(this.Fact(n"q307_main_game_killed"))+"/"+ToString(this.Fact(n"q307_ep1_killed"))+
      " Johnny="+ToString(this.Fact(n"q305_johnny_scene_active"))+" PONR="+ToString(this.Fact(n"q115_point_of_no_return"));
  }
  private func Heartbeat() -> Void {
    if this.EngineNow()-this.lastHeartbeat<5.0 { return; }this.lastHeartbeat=this.EngineNow();
    ModLog(n"PTFR_LoadingLC2",this.Status()+" engineElapsed="+ToString(this.EngineNow()-this.engineStarted)+
      " frame="+ToString(this.rendered)+" ack="+ToString(this.Fact(n"PTFRLC1_CoverReady"))+
      " teleported="+ToString(this.Fact(n"PTFRPA2_Teleported"))+" nativeFade="+ToString(this.Fact(n"PTFRPA3_CoverReleased"))+
      " camera="+ToString(this.Fact(n"PTFRPA4_CameraAligned"))+" control="+ToString(this.Fact(n"PTFRPA2_ControlReady"))+
      " prepared/reveal/finished="+ToString(this.Fact(n"PTFRPA2_Prepared"))+"/"+ToString(this.Fact(n"PTFRPA2_Reveal"))+"/"+ToString(this.Fact(n"PTFRPA2_Finished"))+
      " fault="+ToString(this.Fact(n"PTFRPA2_Fault"))+" | "+this.EndingFacts());
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
    if !CyberwarePolicy.Completed(game) { this.SetStage("Finishing the ending handoff","Waiting for the native transition to finish.\n"+this.EndingFacts());return false; }
    if !entry.SnapshotInitializationHealthy() { this.SetStage("Entry setup stopped","The entry module reports a fault. Press Esc to return to the main menu.");return false; }
    if (this.Fact(n"PTFRPA2_Fault")!=0 && this.Fact(n"PTFRPA2_Fault")!=2) || this.Fact(n"PTFRPA5O_Fault")!=0 ||
      this.Fact(n"PTFRH1_Fault")!=0 || profile.PTFRPAFaulted() || body.PTFRR3Faulted() || !chrome.PTFRR2Healthy() {
      this.SetStage("Setup stopped","Arrival/optics/housing faults: "+ToString(this.Fact(n"PTFRPA2_Fault"))+"/"+ToString(this.Fact(n"PTFRPA5O_Fault"))+"/"+ToString(this.Fact(n"PTFRH1_Fault"))+"\nBody: "+StrAfterFirst(body.GetStatus()," | ")+"\nProfile: "+StrAfterFirst(profile.GetStatus()," | "));return false;
    }
    this.completedSteps=3;
    if !snapshot.Ready() { this.SetStage("Recording quest history",snapshot.Status());return false; }
    this.completedSteps=4;
    if this.Fact(n"PTFRPA2_Fault")==2 { this.SetStage("Resuming interrupted setup","Checking the saved preparation timeout before continuing.");return false; }
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
      this.SetStage("Completing the handoff","Waiting for the final native arrival acknowledgement.");return false;
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
    if !this.Required() { this.Drop();return; }this.Ensure();
    if !this.visible { return; }
    // A render opportunity before the native fade may be released. The graph
    // waits on this owned acknowledgement, never on profile or Tier1 readiness.
    if this.rendered && this.Fact(n"PTFRLC1_CoverReady")!=1 {
      GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(n"PTFRLC1_CoverReady",1);
    }
    if !this.rendered { this.SetStage("Preparing the loading cover","Waiting for the interface to draw.");this.Heartbeat();return; }
    if !this.Check() {
      this.stableSince=-1.0;
      this.Heartbeat();
      if this.EngineNow()-this.engineStarted>=120.0 && IsDefined(this.popup) {
        this.popup.UpdateText("Setup is taking longer than expected",this.stage+"\n"+this.detail+"\nPress Esc to return to the main menu.");
      }
      return;
    }
    if this.stableSince<0.0 { this.stableSince=this.Now(); }
    if this.Now()-this.stableSince<1.0 { this.SetStage("Final checks","All setup stages acknowledged. Checking stability.");return; }
    this.completedSteps=12;this.SetStage("Ready","All required setup checks passed.");this.Heartbeat();
    this.released=true;this.Drop();
  }
  public func Status() -> String { return "LC2 visible/released="+ToString(this.visible)+"/"+ToString(this.released)+" steps="+ToString(this.completedSteps)+"/12 elapsedSim="+ToString(this.Now()-this.started)+" | "+this.stage+" | "+this.detail; }
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
  public static func Get() -> ref<SetupPopupPoolLC1> { return GameInstance.GetScriptableServiceContainer().GetService(n"PTFR.LoadingCoverLC1.SetupPopupPoolLC1") as SetupPopupPoolLC1; }
  public func Show(owner:ref<StartupCoverLC1>,epoch:Int32) -> ref<SetupPopupLC1> {
    if IsDefined(this.current) { return null; }
    this.current=new SetupPopupLC1();this.current.Bind(owner,epoch);
    CustomPopupManager.GetInstance().ShowPopup(this.current);return this.current;
  }
  public func Released(popup:ref<SetupPopupLC1>) -> Void { if this.current==popup { this.current=null; } }
}

// Base CustomPopup only: no InGamePopup modal context, pause, time dilation,
// movement status effect or scene tier override. Native notification blocks input.
public class SetupPopupLC1 extends CustomPopup {
  private let owner:wref<StartupCoverLC1>;private let epoch:Int32;
  private let title:ref<inkText>;private let body:ref<inkText>;private let closing:Bool;
  private let progress:ref<inkRectangle>;private let progressLabel:ref<inkText>;
  public func Bind(owner:ref<StartupCoverLC1>,epoch:Int32) -> Void { this.owner=owner;this.epoch=epoch; }
  public func GetQueueName() -> CName { return n"PTFR_setup_LC1"; }
  public func IsBlocking() -> Bool { return true; }
  public func UseCursor() -> Bool { return false; }
  protected cb func OnCreate() -> Void {
    super.OnCreate();
    let bg=new inkRectangle();bg.SetName(n"opaqueCover");bg.SetAnchor(inkEAnchor.Centered);bg.SetAnchorPoint(Vector2(0.5,0.5));
    bg.SetSize(Vector2(32768.0,32768.0));bg.SetTintColor(new HDRColor(0.015,0.02,0.025,1.0));bg.SetOpacity(1.0);bg.Reparent(this.GetRootCompoundWidget());
    this.title=this.Text("Preparing Tower continuation",-200.0,48);this.body=this.Text("Please wait while your save is prepared.",-60.0,26);
    this.body.SetWrapping(true,1100.0,textWrappingPolicy.PerCharacter);
    let track=new inkRectangle();track.SetName(n"setupProgressTrack");track.SetSize(Vector2(760.0,18.0));
    track.SetAnchor(inkEAnchor.Centered);track.SetAnchorPoint(Vector2(0.5,0.5));track.SetMargin(inkMargin(0.0,115.0,0.0,0.0));
    track.SetTintColor(new HDRColor(0.12,0.17,0.20,1.0));track.Reparent(this.GetRootCompoundWidget());
    this.progress=new inkRectangle();this.progress.SetName(n"setupProgressFill");this.progress.SetSize(Vector2(0.0,18.0));
    this.progress.SetAnchor(inkEAnchor.Centered);this.progress.SetAnchorPoint(Vector2(0.0,0.5));this.progress.SetMargin(inkMargin(-380.0,115.0,0.0,0.0));
    this.progress.SetTintColor(new HDRColor(0.2,0.86,0.90,1.0));this.progress.Reparent(this.GetRootCompoundWidget());
    this.progressLabel=this.Text("0%  |  0 / 12 setup checks",155.0,26);
    this.Text("ESC  Return to main menu",215.0,24);
  }
  private func Text(value:String,y:Float,size:Int32) -> ref<inkText> {
    let text=new inkText();text.SetFontFamily("base\\gameplay\\gui\\fonts\\raj\\raj.inkfontfamily");text.SetFontStyle(n"Medium");text.SetFontSize(size);
    text.SetText(value);text.SetAnchor(inkEAnchor.Centered);text.SetAnchorPoint(Vector2(0.5,0.5));text.SetMargin(inkMargin(0.0,y,0.0,0.0));
    text.SetTintColor(new HDRColor(0.9,0.95,0.96,1.0));text.Reparent(this.GetRootCompoundWidget());return text;
  }
  protected cb func OnShow() -> Void {
    this.GetRootWidget().SetOpacity(1.0);
    if !this.closing && IsDefined(this.owner) && this.owner.Accepts(this.epoch) {
      this.owner.Attached(this.epoch);
      // UI animation completion is independent of the simulation clock. Keep
      // full opacity throughout; acknowledge only this attached session.
      let alpha=new inkAnimTransparency();alpha.SetStartTransparency(1.0);alpha.SetEndTransparency(1.0);alpha.SetDuration(0.10);
      let anim=new inkAnimDef();anim.AddInterpolator(alpha);
      this.m_transitionAnimProxy=this.GetRootWidget().PlayAnimation(anim);
      this.m_transitionAnimProxy.RegisterToCallback(inkanimEventType.OnFinish,this,n"OnCoverFrame");
    }
    else { GameInstance.GetDelaySystem(this.GetGame()).DelayCallback(SetupPopupCloseLC1.Create(this),0.0,false); }
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
    if evt.IsAction(n"cancel") && IsDefined(this.owner) { this.owner.Leave(this.epoch); }
    evt.Handle();return true;
  }
  public func UpdateText(title:String,body:String) -> Void {
    if IsDefined(this.title) { this.title.SetText(title); }
    if IsDefined(this.body) { this.body.SetText(body); }
  }
  public func UpdateProgress(completed:Int32,total:Int32) -> Void {
    if !IsDefined(this.progress) || !IsDefined(this.progressLabel) || total<=0 { return; }
    let count=Clamp(completed,0,total);let fraction=Cast<Float>(count)/Cast<Float>(total);
    this.progress.SetSize(Vector2(760.0*fraction,18.0));
    this.progressLabel.SetText(ToString(count*100/total)+"%  |  "+ToString(count)+" / "+ToString(total)+" setup checks");
  }
  public func Dismiss() -> Void { this.closing=true;if this.IsInitialized() { this.Detach(); } }
}

public class SetupPopupCloseLC1 extends DelayCallback {
  private let popup:wref<SetupPopupLC1>;
  public static func Create(popup:ref<SetupPopupLC1>) -> ref<SetupPopupCloseLC1> { let c=new SetupPopupCloseLC1();c.popup=popup;return c; }
  public func Call() -> Void { if IsDefined(this.popup) { this.popup.Dismiss(); } }
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
