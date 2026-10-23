module PTFR.ActivityStateR3

import PTFR.RestrictionsR1.*

// One native node teleport after normal Tower credits/content cleanup.
// Exact original H10 streetfront player spawn; never the apartment dataterm.
public class PreAlphaArrivalPA1 extends ScriptableSystem {
  // 0 dormant, 1 requested, 2 dispatched, 3 acknowledged, 4 needs inspection.
  private persistent let stage: Int32;
  private let detail: String;
  private let running: Bool;
  private let epoch: Int32;
  private let safeTicks: Int32;
  private let landedTicks: Int32;
  private let observedTicks: Int32;

  public static func Destination() -> NodeRef {
    let path = "$/03_night_city/c_watson/little_china/loc_megabuilding_a_prefab4KCU2IQ/loc_megabuilding_a_questdesign_prefabT5LKYXQ/#q001_pr_v_room/#cp77_spwn_performance_test";
    return CreateNodeRef(path);
  }
  public static func Position() -> Vector4 { return new Vector4(-1432.13672, 1261.04565, 23.0654984, 1.0); }
  private func Authorized() -> Bool {
    let entry = PreAlphaEntry.Get(this.GetGameInstance());
    return IsDefined(entry) && entry.PostEndingAuthorized() && CyberwarePolicy.Completed(this.GetGameInstance());
  }
  private func OnAttach() -> Void { this.running = true; this.Restored(); }
  private func OnDetach() -> Void { this.running = false; this.epoch += 1; }
  public func Restored() -> Void {
    this.epoch += 1; this.safeTicks = 0; this.landedTicks = 0; this.observedTicks = 0;
    // Persisted dispatched/completed stages are never converted back to request.
    this.detail = "Dormant; awaiting authorized completed Tower.";
    if this.stage == 1 { this.detail = "Saved arrival request pending safe gameplay; nothing dispatched yet."; }
    if this.stage == 2 { this.detail = "Saved native teleport dispatch; observing position only, never reissuing."; }
    if this.stage == 3 { this.detail = "Saved H10 arrival complete; no repeat teleport or ownership grant."; }
    if this.stage == 4 { this.detail = "Saved arrival verification failure; no retry. Inspect player position/log."; }
    if this.running { this.Schedule(); }
  }
  private func Schedule() -> Void {
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(PreAlphaArrivalTickPA1.Create(this, this.epoch), 1.0, false);
  }
  public func Begin() -> String {
    if this.stage != 0 { return this.Status(); }
    if !this.Authorized() { return "H10 arrival waiting for authorized post-credits Tower cleanup."; }
    this.stage = 1; this.detail = "Waiting for safe, unmounted gameplay before native H10 street teleport.";
    return this.Status();
  }
  public func Completed() -> Bool { return this.stage == 3; }
  public func Status() -> String {
    return "H10 arrival PA1: stage=" + ToString(this.stage) + " completed=" + ToString(this.Completed()) +
      " observedLanding=" + ToString(this.landedTicks) + " | " + this.detail;
  }
  private func NearTarget(player: ref<PlayerPuppet>) -> Bool {
    let point = player.GetWorldPosition(); let target = PreAlphaArrivalPA1.Position();
    let dx = point.X - target.X; let dy = point.Y - target.Y;
    return dx * dx + dy * dy <= 100.0 && AbsF(point.Z - target.Z) <= 2.0;
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    this.Schedule();
    if this.stage == 0 || this.stage == 3 || this.stage == 4 { return; }
    if !this.Authorized() { this.safeTicks = 0; this.landedTicks = 0; return; }
    let game = this.GetGameInstance();
    let player = GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(player) || player.IsReplacer() || player.IsDead() { this.safeTicks = 0; this.landedTicks = 0; return; }
    if this.stage == 1 {
      if !CyberwarePolicy.Safe(player) || GameInstance.GetPhoneManager(game).IsPhoneCallActive() {
        this.safeTicks = 0; return;
      }
      this.safeTicks += 1; if this.safeTicks < 3 { return; }
      let facility = GameInstance.GetTeleportationFacility(game);
      if !IsDefined(facility) { this.detail = "Native teleport facility unavailable; nothing dispatched."; return; }
      // Stock FastTravelSystem uses this same native node operation without a
      // destination-residency prerequisite. Native code owns streaming/placement.
      // Persist intent first. Never repeat the request, including after reload.
      this.stage = 2; this.observedTicks = 0; this.landedTicks = 0;
      this.detail = "Native H10 node teleport dispatched once; awaiting observed street position. No ownership granted.";
      facility.TeleportToNode(player, PreAlphaArrivalPA1.Destination());
      return;
    }
    // This acknowledges observable position, not a claim that a raycast or
    // authored marker alone proves rendered collision. Physical footing is live QA.
    let ui = GameInstance.GetBlackboardSystem(game).Get(GetAllBlackboardDefs().UI_System);
    if !IsDefined(ui) || ui.GetBool(GetAllBlackboardDefs().UI_System.IsInMenu) { return; }
    this.observedTicks += 1;
    // One observation within 10m permits ordinary walking after the transition.
    // No freeze or demand that the player remain motionless for several seconds.
    if this.NearTarget(player) { this.landedTicks = 1; }
    if this.landedTicks == 1 {
      this.stage = 3;
      this.detail = "H10 street arrival acknowledged at authored position; no repeat on reload/death, no housing ownership grant.";
      ModLog(n"PTFR_PreAlpha", this.Status()); return;
    }
    if this.observedTicks >= 60 {
      this.stage = 4;
      this.detail = "Native teleport was dispatched but H10 street position was not observed within 60 live samples. No automatic retry; inspect current position/log before further action.";
      ModLog(n"PTFR_PreAlpha", this.Status());
    }
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
