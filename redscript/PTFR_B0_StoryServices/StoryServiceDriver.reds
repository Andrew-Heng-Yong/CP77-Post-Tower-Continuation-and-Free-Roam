module PTFR.B0StoryServices

// Five-second pending-enable check; safety queried once only if an eligible site needs enablement.
// Native owners perform all approach, scene and departure work; no distance polling.
public class StoryServiceDriver extends ScriptableSystem {
  private let epoch: Int32;
  private let running: Bool;
  private func OnAttach() -> Void {
    this.epoch += 1;
    this.running = true;
    this.Schedule(this.epoch);
  }
  private func OnDetach() -> Void { this.running = false; this.epoch += 1; }
  private func Schedule(epoch: Int32) -> Void {
    let delays = GameInstance.GetDelaySystem(this.GetGameInstance());
    if IsDefined(delays) { delays.DelayCallback(StoryServiceTick.Create(this, epoch), 5.0, false); }
  }
  private func Eligible(q: ref<QuestsSystem>) -> Bool {
    return q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
      q.GetFact(n"PTFRP0_DR13") == 1 &&
      q.GetFact(n"q307_active") == 0 &&
      q.GetFact(n"q307_done") == 1 &&
      q.GetFact(n"q307_finished") == 1 &&
      q.GetFact(n"q307_2079") == 1 &&
      q.GetFact(n"q307_main_game_killed") == 1 &&
      q.GetFact(n"q305_johnny_scene_active") == 0 &&
      q.GetFact(n"q115_point_of_no_return") == 0 &&
      q.GetFact(n"q000_done") == 1 && q.GetFact(n"PTFRBASE_Suspended") == 0 && q.GetFact(n"PTFRB0ST_Suspended") == 0;
  }
  private func Site(q: ref<QuestsSystem>, enabled: CName, ready: CName, active: CName, excluded: CName, gate: CName, extra: Bool, commit: Bool) -> Bool {
    if !extra || q.GetFact(gate) <= 0 || q.GetFact(enabled) != 0 || q.GetFact(ready) != 1 || q.GetFact(active) != 0 || q.GetFact(excluded) != 0 { return false; }
    if commit { q.SetFact(enabled, 1); }
    return true;
  }
  private func Sites(q: ref<QuestsSystem>, commit: Bool) -> Bool {
    let pending = false;
    pending = this.Site(q, n"PTFRB0STFRED_Enabled", n"PTFRB0STFRED_Ready", n"PTFRB0STFRED_OwnerActive", n"PTFRB0STFRED_Excluded", n"wat_lch_melee_01_default_on", true, commit) || pending;
    pending = this.Site(q, n"PTFRB0STCASSIUS_Enabled", n"PTFRB0STCASSIUS_Ready", n"PTFRB0STCASSIUS_OwnerActive", n"PTFRB0STCASSIUS_Excluded", n"wat_nid_ripperdoc_01_default_on", true, commit) || pending;
    pending = this.Site(q, n"PTFRB0STPEPE_Enabled", n"PTFRB0STPEPE_Ready", n"PTFRB0STPEPE_OwnerActive", n"PTFRB0STPEPE_Excluded", n"elcoyote_barman_default_on", true, commit) || pending;
    pending = this.Site(q, n"PTFRB0STCHARLES_Enabled", n"PTFRB0STCHARLES_Ready", n"PTFRB0STCHARLES_OwnerActive", n"PTFRB0STCHARLES_Excluded", n"wat_kab_ripperdoc_03_default_on", true, commit) || pending;
    return pending;
  }
  private func Safe(player: ref<PlayerPuppet>) -> Bool {
    let game = this.GetGameInstance();
    let scene = GameInstance.GetSceneSystem(game).GetScriptInterface();
    let workspots = GameInstance.GetWorkspotSystem(game);
    if !IsDefined(scene) || !IsDefined(workspots) { return false; }
    if player.IsInCombat() || scene.IsEntityInScene(player.GetEntityID()) || workspots.IsActorInWorkspot(player) { return false; }
    let mount = GameInstance.GetMountingFacility(game).GetMountingInfoSingleWithObjects(player);
    if EntityID.IsDefined(mount.parentId) { return false; }
    let bb = player.GetPlayerStateMachineBlackboard();
    if !IsDefined(bb) { return false; }
    let high = bb.GetInt(GetAllBlackboardDefs().PlayerStateMachine.HighLevel);
    let tier = bb.GetInt(GetAllBlackboardDefs().PlayerStateMachine.SceneTier);
    if (high != 1 && high != 2) || (tier != 1 && tier != 2) { return false; }
    if GameInstance.GetQuestsContentSystem(game).IsTokensActivationBlocked() { return false; }
    let locks: array<gameSaveLock>;
    return !GameInstance.IsSavingLocked(game, locks);
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    let game = this.GetGameInstance();
    let q = GameInstance.GetQuestsSystem(game);
    if IsDefined(q) && this.Eligible(q) && this.Sites(q, false) {
      let player = GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
      if IsDefined(player) && this.Safe(player) { this.Sites(q, true); }
    }
    this.Schedule(epoch);
  }
}
public class StoryServiceTick extends DelayCallback {
  private let driver: wref<StoryServiceDriver>;
  private let epoch: Int32;
  public func Call() -> Void { if IsDefined(this.driver) { this.driver.Poll(this.epoch); } }
  public static func Create(driver: ref<StoryServiceDriver>, epoch: Int32) -> ref<StoryServiceTick> {
    let result = new StoryServiceTick(); result.driver = driver; result.epoch = epoch; return result;
  }
}
