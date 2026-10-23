module PTFR.B0DeferredVendors

// Two narrow native owners; no story/default/market fact writes.
public class DeferredVendorDriver extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private func OnAttach() -> Void {
    this.epoch += 1;
    this.running = true;
    this.Schedule(this.epoch);
  }
  private func OnDetach() -> Void { this.running = false; this.epoch += 1; }
  private func Schedule(epoch: Int32) -> Void {
    let d = GameInstance.GetDelaySystem(this.GetGameInstance());
    if IsDefined(d) { d.DelayCallback(DeferredVendorTick.Create(this, epoch), 0.5, false); }
  }
  private func SetIfChanged(q: ref<QuestsSystem>, key: CName, value: Int32) -> Void {
    if q.GetFact(key) != value { q.SetFact(key, value); }
  }
  private func Site(q: ref<QuestsSystem>, p: Vector4, safe: Bool, allowed: Bool, suspended: Bool,
      ready: CName, enabled: CName, excluded: CName, near: CName, approach: CName, far: CName,
      x: Float, y: Float, z: Float, entry2: Float, exit2: Float) -> Void {
    let active = q.GetFact(near) == 1;
    let isEnabled = q.GetFact(enabled) == 1;
    if !suspended && allowed && safe && !active && q.GetFact(excluded) == 0 &&
       q.GetFact(ready) == 1 && q.GetFact(enabled) == 0 && q.GetFact(far) == 0 {
      q.SetFact(enabled, 1);
      isEnabled = true;
    }
    let dx = p.X-x;
    let dy = p.Y-y;
    let dz = p.Z-z;
    let d2 = dx*dx+dy*dy+dz*dz;
    // Entry is observed at the resolved scene anchor instead of acquiring
    // the broad #loading_conditions prefab. Native actor-distance stays vanilla.
    let enter = isEnabled && allowed && !suspended && d2 < entry2 && (active || safe);
    if active {
      this.SetIfChanged(q, far, d2 > exit2 || !allowed ? 1 : 0);
    } else {
      // Reset only the completed owner's exit signal, never its saved Near or
      // native counters. Write Far before opening a new approach request.
      this.SetIfChanged(q, far, 0);
    }
    this.SetIfChanged(q, approach, enter ? 1 : 0);
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    let game = this.GetGameInstance();
    let q = GameInstance.GetQuestsSystem(game);
    if !IsDefined(q) { this.Schedule(epoch); return; }
    let eligible = true;
    if q.GetFact(n"PostTowerFreeRoamActive") != 1 { eligible = false; }
    if q.GetFact(n"PTFRP0_DR13") != 1 { eligible = false; }
    if q.GetFact(n"q307_active") != 0 { eligible = false; }
    if q.GetFact(n"q307_done") != 1 { eligible = false; }
    if q.GetFact(n"q307_finished") != 1 { eligible = false; }
    if q.GetFact(n"q307_2079") != 1 { eligible = false; }
    if q.GetFact(n"q307_main_game_killed") != 1 { eligible = false; }
    if q.GetFact(n"q305_johnny_scene_active") != 0 { eligible = false; }
    if q.GetFact(n"q115_point_of_no_return") != 0 { eligible = false; }
    if q.GetFact(n"q000_done") != 1 { eligible = false; }
    if !eligible { this.Schedule(epoch); return; }
    let ps = GameInstance.GetPlayerSystem(game);
    if !IsDefined(ps) { this.Schedule(epoch); return; }
    let player = ps.GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(player) { this.Schedule(epoch); return; }
    let scenes = GameInstance.GetSceneSystem(game).GetScriptInterface();
    let workspots = GameInstance.GetWorkspotSystem(game);
    if !IsDefined(scenes) || !IsDefined(workspots) { this.Schedule(epoch); return; }
    let safe = !player.IsInCombat() && !scenes.IsEntityInScene(player.GetEntityID()) && !workspots.IsActorInWorkspot(player);
    let position = player.GetWorldPosition();
    let suspended = q.GetFact(n"PTFRB0DOV_Suspended") != 0;
    this.Site(q, position, safe, q.GetFact(n"wbr_jpn_tech_01_default_on") > 0, suspended, n"PTFRB0DOVC_Ready", n"PTFRB0DOVC_Enabled", n"PTFRB0DOVC_Excluded", n"PTFRB0DOVC_Near", n"PTFRB0DOVC_Approach", n"PTFRB0DOVC_Far", -678.719971000, 916.069946000, 11.399998700, 6400.0, 7225.0);
    this.Site(q, position, safe, q.GetFact(n"wbr_jpn_netrun_02_default_on") > 0 && q.GetFact(n"jpn_05_finished") > 0 && q.GetFact(n"wbr_jpn_netrun_02_market_system_added") > 0, suspended, n"PTFRB0DOVN_Ready", n"PTFRB0DOVN_Enabled", n"PTFRB0DOVN_Excluded", n"PTFRB0DOVN_Near", n"PTFRB0DOVN_Approach", n"PTFRB0DOVN_Far", -489.667969000, 577.855469000, 27.302368200, 2500.0, 3025.0);
    this.Schedule(epoch);
  }
}
public class DeferredVendorTick extends DelayCallback {
  private let driver: wref<DeferredVendorDriver>;
  private let epoch: Int32;
  public func Call() -> Void { if IsDefined(this.driver) { this.driver.Poll(this.epoch); } }
  public static func Create(driver: ref<DeferredVendorDriver>, epoch: Int32) -> ref<DeferredVendorTick> {
    let c = new DeferredVendorTick(); c.driver = driver; c.epoch = epoch; return c;
  }
}
