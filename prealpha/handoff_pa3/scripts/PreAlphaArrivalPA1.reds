module PTFR.ActivityStateR3

import PTFR.RestrictionsR1.*

// PA3: native final-board graph owns the fade, scoped cleanup and ONE teleport.
// This observer only acknowledges actual readiness. It never teleports, resets
// story facts, removes arbitrary restrictions, or loads/saves a game.
// Retain the old class/fields for serialization; old dev saves are not migrated.
public class PreAlphaArrivalPA1 extends ScriptableSystem {
  private persistent let stage: Int32;
  private let detail: String;
  private let running: Bool;
  private let epoch: Int32;
  private let safeTicks: Int32;
  private let landedTicks: Int32;
  private let observedTicks: Int32;

  public static func Position() -> Vector4 { return new Vector4(-1432.13672, 1261.04565, 23.0654984, 1.0); }
  private func Fact(name: CName) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(name); }
  private func Set(name: CName, value: Int32) -> Void { GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(name, value); }
  private func Authorized() -> Bool {
    return this.Fact(n"PTFRPA2_Started") == 1 && this.Fact(n"PTFRP0_DR07") == 1 &&
      this.Fact(n"q307_done") == 1 && this.Fact(n"q307_finished") == 1 && this.Fact(n"q307_active") == 0 &&
      this.Fact(n"q307_2079") == 1 && this.Fact(n"q307_main_game_killed") == 1 && this.Fact(n"q307_ep1_killed") == 1;
  }
  private func OnAttach() -> Void { this.running = true; this.Restored(); }
  private func OnDetach() -> Void { this.running = false; this.epoch += 1; }
  public func Restored() -> Void {
    this.epoch += 1; this.safeTicks = 0; this.landedTicks = 0; this.observedTicks = 0;
    this.detail = "Awaiting the PA3 native post-credits handoff; no legacy-save migration.";
    if this.running { this.Schedule(); }
  }
  private func Schedule() -> Void {
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(PreAlphaArrivalTickPA1.Create(this, this.epoch), 0.25, false);
  }
  public func Begin() -> String { return this.Status(); }
  public func Completed() -> Bool { return this.Fact(n"PTFRPA3_CoverReleased") == 1 && this.Fact(n"PTFRPA2_ControlReady") == 1 && this.Fact(n"PTFRPA2_Fault") == 0; }
  private func NearTarget(player: ref<PlayerPuppet>) -> Bool {
    let p = player.GetWorldPosition(); let t = PreAlphaArrivalPA1.Position();
    let dx = p.X - t.X; let dy = p.Y - t.Y;
    return dx * dx + dy * dy <= 100.0 && AbsF(p.Z - t.Z) <= 2.0;
  }
  private func Player() -> ref<PlayerPuppet> {
    return GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
  }
  private func ControlReady(player: ref<PlayerPuppet>) -> Bool {
    if !IsDefined(player) || !CyberwarePolicy.Safe(player) { return false; }
    let game = this.GetGameInstance(); let bb = player.GetPlayerStateMachineBlackboard();
    let scene = GameInstance.GetSceneSystem(game).GetScriptInterface();
    if !IsDefined(bb) || !IsDefined(scene) { return false; }
    // Full gameplay, not just acceptance of a native SetTier request.
    return bb.GetInt(GetAllBlackboardDefs().PlayerStateMachine.SceneTier) == 1 &&
      bb.GetInt(GetAllBlackboardDefs().PlayerStateMachine.HighLevel) == 1 &&
      !scene.IsEntityInScene(player.GetEntityID()) &&
      !StatusEffectSystem.ObjectHasStatusEffect(player, t"GameplayRestriction.NoMovement") &&
      !GameInstance.GetPhoneManager(game).IsPhoneCallActive();
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    this.Schedule();
    if !this.Authorized() || this.Fact(n"PTFRPA2_Finished") == 1 || this.Fact(n"PTFRPA2_Fault") > 0 { return; }
    if this.Fact(n"PTFRPA2_Teleported") != 1 { this.detail = "Native covered placement/cleanup in progress."; return; }
    if this.Fact(n"PTFRPA3_CoverReleased") != 1 { this.detail = "Releasing the native blackout before checking gameplay readiness."; return; }
    let player = this.Player();
    this.observedTicks += 1;
    if this.Fact(n"PTFRPA2_ControlReady") == 0 {
      if !this.ControlReady(player) || !this.NearTarget(player) { this.safeTicks = 0; this.detail = "Waiting for H10 position and actual free-player state; native watchdog remains armed."; return; }
      this.safeTicks += 1; if this.safeTicks < 4 { return; }
      this.landedTicks = 1; this.stage = 3;
      this.Set(n"PTFRPA2_ControlReady", 1);
      this.detail = "H10 position and full gameplay/control checks passed; initializing approved restoration/profile.";
      return;
    }
    // Recheck controls AFTER profile + initial gig admission, then let the
    // native graph finish. Screen is already uncovered; stock-tier waits do not hold entry.
    if this.Fact(n"PTFRPA2_Prepared") == 1 {
      if !this.ControlReady(player) { this.safeTicks = 0; this.detail = "Preparation returned; waiting for final player-control check."; return; }
      this.safeTicks += 1; if this.safeTicks < 8 { return; }
      this.Set(n"PTFRPA2_Reveal", 1);
      this.detail = "Preparation and final control check passed; native completion requested.";
    }
  }

  private func ReadinessReason(player: ref<PlayerPuppet>) -> String {
    if !IsDefined(player) { return "no player"; }
    if player.IsDead() || player.IsReplacer() { return "dead or replacer"; }
    if CyberwarePolicy.InMenu(this.GetGameInstance()) { return "menu open"; }
    if player.IsInCombat() { return "combat"; }
    let bb = player.GetPlayerStateMachineBlackboard();
    if !IsDefined(bb) { return "player state unavailable"; }
    if bb.GetInt(GetAllBlackboardDefs().PlayerStateMachine.SceneTier) != 1 ||
      bb.GetInt(GetAllBlackboardDefs().PlayerStateMachine.HighLevel) != 1 { return "not full gameplay"; }
    if !CyberwarePolicy.Safe(player) { return "holster / equipment / scene / mount / time-status gate"; }
    if !this.ControlReady(player) { return "scene / movement / phone gate"; }
    if !this.NearTarget(player) && this.Fact(n"PTFRPA2_ControlReady") == 0 { return "outside H10 arrival bounds"; }
    return "ready";
  }
  public func Status() -> String {
    let p = this.Player(); let live = "player=absent";
    if IsDefined(p) {
      let bb = p.GetPlayerStateMachineBlackboard(); let scene = GameInstance.GetSceneSystem(this.GetGameInstance()).GetScriptInterface();
      let pos = p.GetWorldPosition();
      live = "xyz=" + ToString(pos.X) + "," + ToString(pos.Y) + "," + ToString(pos.Z);
      if IsDefined(bb) { live += " tier/high=" + ToString(bb.GetInt(GetAllBlackboardDefs().PlayerStateMachine.SceneTier)) + "/" + ToString(bb.GetInt(GetAllBlackboardDefs().PlayerStateMachine.HighLevel)); }
      if IsDefined(scene) { live += " scene/dialogue/camera=" + ToString(scene.IsEntityInScene(p.GetEntityID())) + "/" + ToString(scene.IsEntityInDialogue(p.GetEntityID())) + "/" + ToString(scene.GetSceneSystemCameraControlEnabled()); }
      live += " noMovement=" + ToString(StatusEffectSystem.ObjectHasStatusEffect(p, t"GameplayRestriction.NoMovement")) +
        " workspot=" + ToString(GameInstance.GetWorkspotSystem(this.GetGameInstance()).IsActorInWorkspot(p)) +
        " tokensBlocked=" + ToString(GameInstance.GetQuestsContentSystem(this.GetGameInstance()).IsTokensActivationBlocked());
    }
    let message = this.detail;
    if this.Fact(n"PTFRPA2_Fault") == 1 { message = "STOPPED: control-readiness timeout; no automatic retry. Screen uncovered."; }
    if this.Fact(n"PTFRPA2_Fault") == 2 { message = "STOPPED: preparation timeout; no automatic retry. Screen uncovered."; }
    if this.Fact(n"PTFRPA2_Finished") == 1 { message = "Handoff complete; no repeat transfer on load."; }
    return "H10 transition PA3: started/teleported/control/prepared/reveal/finished=" + ToString(this.Fact(n"PTFRPA2_Started")) + "/" +
      ToString(this.Fact(n"PTFRPA2_Teleported")) + "/" + ToString(this.Fact(n"PTFRPA2_ControlReady")) + "/" +
      ToString(this.Fact(n"PTFRPA2_Prepared")) + "/" + ToString(this.Fact(n"PTFRPA2_Reveal")) + "/" + ToString(this.Fact(n"PTFRPA2_Finished")) +
      " coverReleased=" + ToString(this.Fact(n"PTFRPA3_CoverReleased")) + " fault=" + ToString(this.Fact(n"PTFRPA2_Fault")) + " | " + live + " | gate=" + this.ReadinessReason(p) + " | " + message;
  }
}

public class PreAlphaArrivalTickPA1 extends DelayCallback {
  private let owner: wref<PreAlphaArrivalPA1>; private let epoch: Int32;
  public static func Create(owner: ref<PreAlphaArrivalPA1>, epoch: Int32) -> ref<PreAlphaArrivalTickPA1> {
    let tick = new PreAlphaArrivalTickPA1(); tick.owner = owner; tick.epoch = epoch; return tick;
  }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}

@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void {
  wrappedMethod(gameInstance);
  let arrival = GameInstance.GetScriptableSystemsContainer(gameInstance).Get(n"PTFR.ActivityStateR3.PreAlphaArrivalPA1") as PreAlphaArrivalPA1;
  if IsDefined(arrival) { arrival.Restored(); }
}
