module PTFR.ActivityStateR3

import PTFR.RestrictionsR1.*

// Selective optical handback, not another camera activation. The native owner
// plays one stock player-camera reset event; this script never sets FOV/DOF.
public class CameraOpticsPA5 extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let stable: Int32;
  private let pendingTicks: Int32;
  private let returnTicks: Int32;
  private let lastFOV: Float;
  private let detail: String;
  // Detailed optics samples are logged; ownership lives in save-backed facts.
  private let before: String;
  private let after: String;

  public static func Get(game: GameInstance) -> ref<CameraOpticsPA5> {
    return GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.ActivityStateR3.CameraOpticsPA5") as CameraOpticsPA5;
  }
  private func Fact(name: CName) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(name); }
  private func Set(name: CName, value: Int32) -> Void { GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(name, value); }
  private func Player() -> ref<PlayerPuppet> { return GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet; }
  private func Authorized() -> Bool {
    return this.Fact(n"q307_done") == 1 && this.Fact(n"q307_finished") == 1 && this.Fact(n"q307_active") == 0 &&
      this.Fact(n"q307_2079") == 1 && this.Fact(n"q307_main_game_killed") == 1 && this.Fact(n"q307_ep1_killed") == 1 &&
      this.Fact(n"PTFRP0_DR07") == 1 && this.Fact(n"PTFRPA2_Started") == 1 && this.Fact(n"PTFRPA2_Teleported") == 1 &&
      this.Fact(n"PTFRPA3_CoverReleased") == 1 && this.Fact(n"PTFRPA2_ControlReady") == 1 &&
      this.Fact(n"PTFRPA4_CameraAligned") == 1 && this.Fact(n"PTFRPA2_Fault") == 0;
  }
  private func Safe(player: ref<PlayerPuppet>) -> Bool {
    if !IsDefined(player) || !CyberwarePolicy.Safe(player) { return false; }
    let game = this.GetGameInstance(); let ps = GameInstance.GetPlayerSystem(game);
    let bb = player.GetPlayerStateMachineBlackboard(); let si = GameInstance.GetSceneSystem(game).GetScriptInterface();
    if !IsDefined(bb) || !IsDefined(si) || ps.IsInFreeCamera() || ps.GetLocalPlayerControlledGameObject() != player { return false; }
    return bb.GetInt(GetAllBlackboardDefs().PlayerStateMachine.SceneTier) == 1 &&
      bb.GetInt(GetAllBlackboardDefs().PlayerStateMachine.HighLevel) == 1 && !si.IsEntityInScene(player.GetEntityID()) &&
      !GameInstance.GetPhoneManager(game).IsPhoneCallActive() &&
      !StatusEffectSystem.ObjectHasStatusEffect(player, t"GameplayRestriction.NoMovement") &&
      !StatusEffectSystem.ObjectHasStatusEffect(player, t"GameplayRestriction.NoCameraControl");
  }
  private func Aligned(player: ref<PlayerPuppet>) -> Bool {
    if !IsDefined(player) || !IsDefined(player.GetFPPCameraComponent()) { return false; }
    let cs = GameInstance.GetCameraSystem(this.GetGameInstance()); let view: Transform;
    if !IsDefined(cs) || !cs.GetActiveCameraWorldTransform(view) { return false; }
    let active = Transform.GetPosition(view); let m = player.GetFPPCameraComponent().GetLocalToWorld();
    let fp = Matrix.GetTranslation(m); let p = player.GetWorldPosition();
    let forward = cs.GetActiveCameraForward(); let expected = Matrix.GetDirectionVector(m);
    if !(Vector4.LengthSquared(forward) > 0.01) || !(Vector4.LengthSquared(expected) > 0.01) { return false; }
    return Vector4.DistanceSquared(active, fp) <= 0.5625 && Vector4.DistanceSquared(fp, p) <= 25.0 &&
      Vector4.Dot(Vector4.Normalize(forward), Vector4.Normalize(expected)) >= 0.97;
  }
  private func SampleValid(player: ref<PlayerPuppet>) -> Bool {
    if !IsDefined(player) || !IsDefined(player.GetFPPCameraComponent()) { return false; }
    let fpp = player.GetFPPCameraComponent(); let fov = GameInstance.GetCameraSystem(this.GetGameInstance()).GetActiveCameraFOV();
    // Deliberately not compared with the UI FOV slider: projection/modifiers may differ.
    // Component getters may expose zero/default sentinels while the selected
    // camera is valid. Require bounded finite data, not guessed defaults.
    return fov > 1.0 && fov < 179.0 && AbsF(fpp.GetFOV()) < 1000.0 &&
      AbsF(fpp.GetZoom()) < 1000.0 &&
      AbsF(fpp.fovOverrideWeight) < 1000.0 && AbsF(fpp.fovOverrideValue) < 1000.0 &&
      AbsF(fpp.zoomOverrideWeight) < 1000.0 && AbsF(fpp.zoomOverrideValue) < 1000.0 &&
      AbsF(fpp.zoomWeaponOverrideWeight) < 1000.0 && AbsF(fpp.zoomWeaponOverrideValue) < 1000.0;
  }
  public func Optics() -> String {
    let player = this.Player();
    if !IsDefined(player) || !IsDefined(player.GetFPPCameraComponent()) { return "optics=unavailable"; }
    let fpp = player.GetFPPCameraComponent();
    return "activeFOV=" + ToString(GameInstance.GetCameraSystem(this.GetGameInstance()).GetActiveCameraFOV()) +
      " fppFOV/zoom=" + ToString(fpp.GetFOV()) + "/" + ToString(fpp.GetZoom()) +
      " fovOverride=" + ToString(fpp.fovOverrideWeight) + "/" + ToString(fpp.fovOverrideValue) +
      " zoomOverride=" + ToString(fpp.zoomOverrideWeight) + "/" + ToString(fpp.zoomOverrideValue) +
      " weaponZoomOverride=" + ToString(fpp.zoomWeaponOverrideWeight) + "/" + ToString(fpp.zoomWeaponOverrideValue) +
      " sampleValid=" + ToString(this.SampleValid(player)) + " aligned=" + ToString(this.Aligned(player)) + " DOF=not-exposed";
  }
  public func Ready() -> Bool {
    return this.Fact(n"PTFRPA5O_Done") == 1 && this.Fact(n"PTFRPA5O_NativeOut") == 1 && this.Fact(n"PTFRPA5O_Fault") == 0;
  }
  public func Inspect() -> String {
    return "Optics PA5: owner/request/issued/out/done=" + ToString(this.Fact(n"PTFRPA5O_Ready")) + "/" +
      ToString(this.Fact(n"PTFRPA5O_Request")) + "/" + ToString(this.Fact(n"PTFRPA5O_Issued")) + "/" +
      ToString(this.Fact(n"PTFRPA5O_NativeOut")) + "/" + ToString(this.Fact(n"PTFRPA5O_Done")) +
      " fault=" + ToString(this.Fact(n"PTFRPA5O_Fault")) + " | " + this.Optics() + " | " + this.detail +
      " | before{" + this.before + "} after{" + this.after + "}";
  }
  public func Ensure() -> String {
    if this.Ready() { return "Optical reset already acknowledged; no replay. " + this.Inspect(); }
    if !this.Authorized() { return "Waiting for genuine post-credits PA4 handback. " + this.Inspect(); }
    return "One-shot optical handback pending safe gameplay; no direct optical write. " + this.Inspect();
  }
  public func Repair() -> String { return this.Ensure(); }
  private func OnAttach() -> Void { this.running = true; this.Restored(); }
  private func OnDetach() -> Void { this.running = false; this.epoch += 1; }
  public func Restored() -> Void {
    this.epoch += 1; this.stable = 0; this.pendingTicks = 0; this.returnTicks = 0; this.lastFOV = 0.0;
    this.before = "not captured in this loaded session"; this.after = "not captured in this loaded session";
    // Permit is ephemeral admission, never ownership, completion or a replay reset.
    this.Set(n"PTFRPA5O_Permit", 0);
    this.detail = "Waiting for safe post-credits optics handback; saved ownership is retained.";
    if this.running { this.Schedule(); }
  }
  private func Schedule() -> Void { GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(CameraOpticsTickPA5.Create(this, this.epoch), 0.25, false); }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    this.Schedule();
    if this.Ready() || this.Fact(n"PTFRPA5O_Fault") > 0 { return; }
    let player = this.Player();
    if this.Fact(n"PTFRPA5O_Issued") == 1 {
      this.Set(n"PTFRPA5O_Permit", 0);
      if this.Fact(n"PTFRPA5O_NativeOut") != 1 { this.detail = "Native reset owner running; ten-second native watchdog armed."; return; }
      if CyberwarePolicy.InMenu(this.GetGameInstance()) { this.stable = 0; return; }
      this.returnTicks += 1;
      if this.returnTicks > 120 {
        this.Set(n"PTFRPA5O_Fault", 5);
        this.detail = "Native reset returned but optics verification timed out after thirty out-of-menu seconds; no retry or forced readiness.";
        return;
      }
      if !this.Safe(player) || !this.Aligned(player) || !this.SampleValid(player) { this.stable = 0; this.detail = "Native reset returned; waiting for safe aligned camera and finite optics."; return; }
      let fov = GameInstance.GetCameraSystem(this.GetGameInstance()).GetActiveCameraFOV();
      if AbsF(fov - this.lastFOV) > 0.1 { this.stable = 0; }
      this.lastFOV = fov; this.stable += 1;
      if this.stable < 4 { return; }
      this.after = this.Optics(); this.Set(n"PTFRPA5O_Done", 1);
      this.detail = "Stock optical reset output and stable FOV acknowledged; visual DOF still requires playtest. No repeat on reload.";
      ModLog(n"PTFR_PreAlpha", "PA5 optics after: " + this.after); return;
    }
    if !this.Authorized() || this.Fact(n"PTFRPA5O_Ready") != 1 || !this.Safe(player) || !this.Aligned(player) || !this.SampleValid(player) {
      this.Set(n"PTFRPA5O_Permit", 0); this.stable = 0; this.pendingTicks = 0; return;
    }
    this.stable += 1; if this.stable < 4 { return; }
    if this.Fact(n"PTFRPA5O_Request") == 0 {
      this.before = this.Optics(); ModLog(n"PTFR_PreAlpha", "PA5 optics before: " + this.before);
      this.Set(n"PTFRPA5O_Request", 1);
    }
    this.Set(n"PTFRPA5O_Permit", 1);
    this.pendingTicks += 1;
    if this.pendingTicks > 80 {
      this.Set(n"PTFRPA5O_Permit", 0); this.Set(n"PTFRPA5O_Fault", 3);
      this.detail = "Native owner did not accept within twenty safe seconds; no retry or forced acknowledgement.";
    }
  }
}

public class CameraOpticsTickPA5 extends DelayCallback {
  private let owner: wref<CameraOpticsPA5>;
  private let epoch: Int32;
  public static func Create(owner: ref<CameraOpticsPA5>, epoch: Int32) -> ref<CameraOpticsTickPA5> {
    let cb = new CameraOpticsTickPA5(); cb.owner = owner; cb.epoch = epoch; return cb;
  }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}

@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void {
  wrappedMethod(gameInstance);
  let optics = CameraOpticsPA5.Get(gameInstance);
  if IsDefined(optics) { optics.Restored(); }
}
