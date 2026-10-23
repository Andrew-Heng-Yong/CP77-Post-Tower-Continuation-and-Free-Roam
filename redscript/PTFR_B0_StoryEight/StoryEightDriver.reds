module PTFR.B0StoryEight

// Five-second pending-enable check; safety queried once only if an eligible site needs enablement.
// Native owners perform all approach, scene and departure work; no distance polling.
public class StoryEightDriver extends ScriptableSystem {
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
    if IsDefined(delays) { delays.DelayCallback(StoryEightTick.Create(this, epoch), 5.0, false); }
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
      q.GetFact(n"q000_done") == 1 && q.GetFact(n"PTFRBASE_Suspended") == 0 && q.GetFact(n"PTFRB0S4_Suspended") == 0;
  }
  private func Site(q: ref<QuestsSystem>, enabled: CName, ready: CName, active: CName, excluded: CName, gate: CName, extra: Bool, commit: Bool) -> Bool {
    if !extra || q.GetFact(gate) <= 0 || q.GetFact(enabled) != 0 || q.GetFact(ready) != 1 || q.GetFact(active) != 0 || q.GetFact(excluded) != 0 { return false; }
    if commit { q.SetFact(enabled, 1); }
    return true;
  }
  private func Sites(q: ref<QuestsSystem>, commit: Bool) -> Bool {
    let pending = false;
    pending = this.Site(q, n"PTFRB0S4NIX_Enabled", n"PTFRB0S4NIX_Ready", n"PTFRB0S4NIX_OwnerActive", n"PTFRB0S4NIX_Excluded", n"nix_default_on", q.GetFact(n"PTFRB0S4NIX_QuestOwns") == 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0S4YOKO_Enabled", n"PTFRB0S4YOKO_Ready", n"PTFRB0S4YOKO_OwnerActive", n"PTFRB0S4YOKO_Excluded", n"wat_kab_netrunner_01_default_on", q.GetFact(n"PTFRB0S4YOKO_QuestOwns") == 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0S4MATEO_Enabled", n"PTFRB0S4MATEO_Ready", n"PTFRB0S4MATEO_OwnerActive", n"PTFRB0S4MATEO_Excluded", n"wat_kab_foodshop_02_default_on", q.GetFact(n"PTFRB0S4MATEO_QuestOwns") == 0 && q.GetFact(n"q004_done") > 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0S4FINGERS_Enabled", n"PTFRB0S4FINGERS_Ready", n"PTFRB0S4FINGERS_OwnerActive", n"PTFRB0S4FINGERS_Excluded", n"wbr_jpn_ripdoc_02_default_on", q.GetFact(n"PTFRB0S4FINGERS_QuestOwns") == 0 && q.GetFact(n"q105_fingers_killed") == 0 && q.GetFact(n"q105_02_active") == 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0S4VIKTOR_Enabled", n"PTFRB0S4VIKTOR_Ready", n"PTFRB0S4VIKTOR_OwnerActive", n"PTFRB0S4VIKTOR_Excluded", n"victor_vector_default_on", q.GetFact(n"PTFRB0S4VIKTOR_QuestOwns") == 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0S4KARIM_Enabled", n"PTFRB0S4KARIM_Ready", n"PTFRB0S4KARIM_OwnerActive", n"PTFRB0S4KARIM_Excluded", n"wbr_jpn_cloth_02_default_on", q.GetFact(n"PTFRB0S4KARIM_QuestOwns") == 0 && q.GetFact(n"mq023_done") > 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0S4RONALD_Enabled", n"PTFRB0S4RONALD_Ready", n"PTFRB0S4RONALD_OwnerActive", n"PTFRB0S4RONALD_Excluded", n"q302_ronald_tree", q.GetFact(n"PTFRB0S4RONALD_QuestOwns") == 0 && q.GetFact(n"q307_ep1_killed") == 1 && q.GetFact(n"q302_done") > 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0S4BILL_Enabled", n"PTFRB0S4BILL_Ready", n"PTFRB0S4BILL_OwnerActive", n"PTFRB0S4BILL_Excluded", n"bill_default_on", q.GetFact(n"PTFRB0S4BILL_QuestOwns") == 0 && q.GetFact(n"q307_ep1_killed") == 1 && q.GetFact(n"sts_ep1_10_finished") > 0 && q.GetFact(n"sts_ep1_10_dodger_dead") > 0 && q.GetFact(n"wst_ep1_11_hotdog_finished") > 0, commit) || pending;
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
public class StoryEightTick extends DelayCallback {
  private let driver: wref<StoryEightDriver>;
  private let epoch: Int32;
  public func Call() -> Void { if IsDefined(this.driver) { this.driver.Poll(this.epoch); } }
  public static func Create(driver: ref<StoryEightDriver>, epoch: Int32) -> ref<StoryEightTick> {
    let result = new StoryEightTick(); result.driver = driver; result.epoch = epoch; return result;
  }
}
