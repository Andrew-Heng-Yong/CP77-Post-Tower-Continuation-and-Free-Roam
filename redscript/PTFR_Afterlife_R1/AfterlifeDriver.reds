module PTFR.AfterlifeR1

// Only arms mod-owned native controllers. No story facts or actor commands.
public class AfterlifeDriver extends ScriptableSystem {
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
    if IsDefined(delays) { delays.DelayCallback(AfterlifeTick.Create(this, epoch), 5.0, false); }
  }
  private func Eligible(q: ref<QuestsSystem>) -> Bool {
    return q.GetFact(n"PostTowerFreeRoamActive") == 1 && q.GetFact(n"PTFRP0_DR13") == 1 &&
      q.GetFact(n"q307_active") == 0 && q.GetFact(n"q307_done") == 1 &&
      q.GetFact(n"q307_finished") == 1 && q.GetFact(n"q307_2079") == 1 &&
      q.GetFact(n"q307_main_game_killed") == 1 && q.GetFact(n"q307_ep1_killed") == 1 &&
      q.GetFact(n"q305_johnny_scene_active") == 0 && q.GetFact(n"q115_point_of_no_return") == 0 &&
      q.GetFact(n"PTFRBASE_Suspended") == 0 && q.GetFact(n"PTFRWORLD_Suspended") == 0 &&
      q.GetFact(n"PTFRAL1_QuestOwns") == 0 && q.GetFact(n"PTFRAL1_Suspended") == 0 &&
      q.GetFact(n"PTFRAL1_DancersRegistered") == 1 && q.GetFact(n"PTFRAL1_PopulationRegistered") == 1;
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
    if IsDefined(q) && q.GetFact(n"PTFRAL1_Enabled") == 0 && this.Eligible(q) {
      let player = GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
      if IsDefined(player) && this.Safe(player) { q.SetFact(n"PTFRAL1_Enabled", 1); }
    }
    this.Schedule(epoch);
  }
}
public class AfterlifeTick extends DelayCallback {
  private let driver: wref<AfterlifeDriver>;
  private let epoch: Int32;
  public func Call() -> Void { if IsDefined(this.driver) { this.driver.Poll(this.epoch); } }
  public static func Create(driver: ref<AfterlifeDriver>, epoch: Int32) -> ref<AfterlifeTick> {
    let result = new AfterlifeTick(); result.driver = driver; result.epoch = epoch; return result;
  }
}
