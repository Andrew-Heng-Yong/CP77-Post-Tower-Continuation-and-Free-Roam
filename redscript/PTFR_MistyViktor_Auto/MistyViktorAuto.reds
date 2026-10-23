module PTFR.MistyViktorAuto

// Arms the already-installed R7 world owner after genuine Tower completion.
// Never writes a story fact, variant, door, actor or world node directly.
public class MistyViktorAuto extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;

  private func OnAttach() -> Void {
    this.epoch += 1;
    this.running = true;
    this.Schedule(this.epoch, 1.0);
  }
  private func OnDetach() -> Void {
    this.running = false;
    this.epoch += 1;
  }
  private func Schedule(epoch: Int32, seconds: Float) -> Void {
    let delay = GameInstance.GetDelaySystem(this.GetGameInstance());
    if IsDefined(delay) { delay.DelayCallback(MistyViktorAutoTick.Create(this, epoch), seconds, false); }
  }
  private func Completed(q: ref<QuestsSystem>) -> Bool {
    return q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
      q.GetFact(n"PTFRP0_DR13") == 1 && q.GetFact(n"q307_active") == 0 &&
      q.GetFact(n"q307_done") == 1 && q.GetFact(n"q307_finished") == 1 &&
      q.GetFact(n"q307_2079") == 1 && q.GetFact(n"q307_main_game_killed") == 1 &&
      q.GetFact(n"q307_ep1_killed") == 1 && q.GetFact(n"q305_johnny_scene_active") == 0 &&
      q.GetFact(n"q115_point_of_no_return") == 0 &&
      q.GetFact(n"PTFRBASE_Suspended") == 0 && q.GetFact(n"PTFRWORLD_Suspended") == 0 &&
      q.GetFact(n"PTFRMV_Suspended") == 0 && q.GetFact(n"PTFRMV_QuestOwns") == 0 &&
      q.GetFact(n"PTFRMV_Registered") == 1 && q.GetFact(n"PTFRMV_Revision") == 7;
  }
  private func Safe(p: ref<PlayerPuppet>) -> Bool {
    if !IsDefined(p) || p.IsInCombat() { return false; }
    let game = this.GetGameInstance();
    let scenes = GameInstance.GetSceneSystem(game).GetScriptInterface();
    let workspots = GameInstance.GetWorkspotSystem(game);
    if !IsDefined(scenes) || !IsDefined(workspots) { return false; }
    if scenes.IsEntityInScene(p.GetEntityID()) || workspots.IsActorInWorkspot(p) { return false; }
    let mounting = GameInstance.GetMountingFacility(game).GetMountingInfoSingleWithObjects(p);
    if EntityID.IsDefined(mounting.parentId) { return false; }
    if GameInstance.GetQuestsContentSystem(game).IsTokensActivationBlocked() { return false; }
    let locks: array<gameSaveLock>;
    if GameInstance.IsSavingLocked(game, locks) { return false; }
    let pos = p.GetWorldPosition();
    let dx = pos.X + 1542.0;
    let dy = pos.Y - 1210.0;
    return dx * dx + dy * dy > 6400.0;
  }
  public func Poll(expectedEpoch: Int32) -> Void {
    if !this.running || expectedEpoch != this.epoch { return; }
    let game = this.GetGameInstance();
    let q = GameInstance.GetQuestsSystem(game);
    let p = GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if IsDefined(q) && this.Safe(p) {
      let desired = this.Completed(q) ? 1 : 0;
      if q.GetFact(n"PTFRMV_Enabled") != desired { q.SetFact(n"PTFRMV_Enabled", desired); }
    }
    this.Schedule(expectedEpoch, 2.0);
  }
}

public class MistyViktorAutoTick extends DelayCallback {
  private let driver: wref<MistyViktorAuto>;
  private let epoch: Int32;
  public func Call() -> Void { if IsDefined(this.driver) { this.driver.Poll(this.epoch); } }
  public static func Create(driver: ref<MistyViktorAuto>, epoch: Int32) -> ref<MistyViktorAutoTick> {
    let tick = new MistyViktorAutoTick();
    tick.driver = driver; tick.epoch = epoch;
    return tick;
  }
}
