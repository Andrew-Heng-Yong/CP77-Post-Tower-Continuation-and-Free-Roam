module PTFR.TimeAuto

// Only requests the already-installed one-shot native source-None unpause
// when a settled, completed Tower session is actually still paused.
public class TimeAuto extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let elapsed: Float;
  private func OnAttach() -> Void { this.epoch += 1; this.running = true; this.elapsed = 0.0; this.Schedule(this.epoch,1.0); }
  private func OnDetach() -> Void { this.running = false; this.epoch += 1; }
  private func Schedule(epoch: Int32, seconds: Float) -> Void {
    let delay = GameInstance.GetDelaySystem(this.GetGameInstance());
    if IsDefined(delay) { delay.DelayCallback(TimeAutoTick.Create(this,epoch),seconds,false); }
  }
  private func Eligible(q: ref<QuestsSystem>) -> Bool {
    return q.GetFact(n"PostTowerFreeRoamActive") == 1 && q.GetFact(n"PTFRP0_DR13") == 1 &&
      q.GetFact(n"q307_active") == 0 && q.GetFact(n"q307_done") == 1 &&
      q.GetFact(n"q307_finished") == 1 && q.GetFact(n"q307_2079") == 1 &&
      q.GetFact(n"q307_main_game_killed") == 1 &&
      q.GetFact(n"PTFRB0TU_Ready") == 1 && q.GetFact(n"PTFRB0TU_Request") == 0 &&
      q.GetFact(n"PTFRB0TU_Done") == 0 && q.GetFact(n"PTFRB0TU_Rejected") == 0 &&
      q.GetFact(n"PTFRB0H10M_Active") == 0 && q.GetFact(n"PTFRB0H10I_M_Active") == 0 &&
      q.GetFact(n"PTFRB0H10I_H_Active") == 0 && q.GetFact(n"PTFRB0H10I_B_Active") == 0 &&
      q.GetFact(n"PTFRB0H10I_S_Active") == 0 && q.GetFact(n"PTFRB0H10I_W_Active") == 0;
  }
  private func Safe(p: ref<PlayerPuppet>) -> Bool {
    if !IsDefined(p) || p.IsInCombat() { return false; }
    let game = this.GetGameInstance();
    let scenes = GameInstance.GetSceneSystem(game).GetScriptInterface();
    let ws = GameInstance.GetWorkspotSystem(game);
    if !IsDefined(scenes) || !IsDefined(ws) { return false; }
    if scenes.IsEntityInScene(p.GetEntityID()) || ws.IsActorInWorkspot(p) { return false; }
    let mount = GameInstance.GetMountingFacility(game).GetMountingInfoSingleWithObjects(p);
    if EntityID.IsDefined(mount.parentId) { return false; }
    if GameInstance.GetQuestsContentSystem(game).IsTokensActivationBlocked() { return false; }
    let locks: array<gameSaveLock>;
    if GameInstance.IsSavingLocked(game,locks) { return false; }
    let board = p.GetPlayerStateMachineBlackboard();
    if !IsDefined(board) { return false; }
    let high = board.GetInt(GetAllBlackboardDefs().PlayerStateMachine.HighLevel);
    let tier = board.GetInt(GetAllBlackboardDefs().PlayerStateMachine.SceneTier);
    return (high == 1 || high == 2) && (tier == 1 || tier == 2);
  }
  public func Poll(expectedEpoch: Int32) -> Void {
    if !this.running || expectedEpoch != this.epoch { return; }
    this.elapsed += 2.0;
    let game = this.GetGameInstance();
    let q = GameInstance.GetQuestsSystem(game);
    let p = GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
    let time = GameInstance.GetTimeSystem(game);
    if IsDefined(q) && IsDefined(time) && this.elapsed >= 5.0 && this.Eligible(q) && this.Safe(p) {
      if time.IsPausedState() && !time.IsTimeDilationActive(n"TimeSkip") {
        q.SetFact(n"PTFRB0TU_Request",1);
      }
    }
    if IsDefined(q) && (q.GetFact(n"PTFRB0TU_Done") == 1 || q.GetFact(n"PTFRB0TU_Rejected") == 1) { return; }
    this.Schedule(expectedEpoch,2.0);
  }
}

public class TimeAutoTick extends DelayCallback {
  private let driver: wref<TimeAuto>;
  private let epoch: Int32;
  public func Call() -> Void { if IsDefined(this.driver) { this.driver.Poll(this.epoch); } }
  public static func Create(driver: ref<TimeAuto>,epoch: Int32) -> ref<TimeAutoTick> {
    let tick = new TimeAutoTick(); tick.driver = driver; tick.epoch = epoch; return tick;
  }
}
