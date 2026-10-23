module PTFR.StreetkidAuto

public class StreetkidAuto extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private func OnAttach() -> Void { this.epoch += 1; this.running = true; this.Schedule(this.epoch); }
  private func OnDetach() -> Void { this.running = false; this.epoch += 1; }
  private func Schedule(epoch: Int32) -> Void {
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(StreetkidAutoTick.Create(this,epoch),0.5,false);
  }
  private func Set(q: ref<QuestsSystem>, name: CName, value: Int32) -> Void {
    if q.GetFact(name) != value { q.SetFact(name,value); }
  }
  private func Eligible(q: ref<QuestsSystem>) -> Bool {
    return q.GetFact(n"PostTowerFreeRoamActive") == 1 && q.GetFact(n"PTFRP0_DR13") == 1 &&
      q.GetFact(n"q307_active") == 0 && q.GetFact(n"q307_done") == 1 && q.GetFact(n"q307_finished") == 1 &&
      q.GetFact(n"q307_2079") == 1 && q.GetFact(n"q000_done") == 1 && q.GetFact(n"q305_johnny_scene_active") == 0 &&
      q.GetFact(n"q115_point_of_no_return") == 0 && q.GetFact(n"PTFRBASE_Suspended") == 0 &&
      q.GetFact(n"PTFRSKA_Suspended") == 0 && q.GetFact(n"PTFRSKA_Interrupted") == 0 &&
      q.GetFact(n"PTFRSKA_Boot") == 1 && q.GetFact(n"PTFRSKA_Revision") == 5 &&
      q.GetFact(n"PTFRSKS1_Enabled") == 0 && q.GetFact(n"PTFRSKS2_Enabled") == 0 && q.GetFact(n"PTFRSKS2_Active") == 0 &&
      q.GetFact(n"PTFRSKS3_Enabled") == 0 && q.GetFact(n"PTFRSKS3_Active") == 0;
  }
  private func Safe(p: ref<PlayerPuppet>) -> Bool {
    let game = this.GetGameInstance();
    let scenes = GameInstance.GetSceneSystem(game).GetScriptInterface();
    let ws = GameInstance.GetWorkspotSystem(game);
    if !IsDefined(scenes) || !IsDefined(ws) || p.IsInCombat() { return false; }
    if scenes.IsEntityInScene(p.GetEntityID()) || ws.IsActorInWorkspot(p) { return false; }
    let mount = GameInstance.GetMountingFacility(game).GetMountingInfoSingleWithObjects(p);
    if EntityID.IsDefined(mount.parentId) { return false; }
    let bb = p.GetPlayerStateMachineBlackboard();
    if !IsDefined(bb) { return false; }
    let high = bb.GetInt(GetAllBlackboardDefs().PlayerStateMachine.HighLevel);
    let tier = bb.GetInt(GetAllBlackboardDefs().PlayerStateMachine.SceneTier);
    if (high != 1 && high != 2) || (tier != 1 && tier != 2) { return false; }
    if GameInstance.GetQuestsContentSystem(game).IsTokensActivationBlocked() { return false; }
    let locks: array<gameSaveLock>;
    return !GameInstance.IsSavingLocked(game,locks);
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    let game = this.GetGameInstance();
    let q = GameInstance.GetQuestsSystem(game);
    let p = GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if IsDefined(q) && IsDefined(p) {
      let pos = p.GetWorldPosition();
      let dx = pos.X + 1261.891;
      let dy = pos.Y + 1001.635;
      let dz = pos.Z - 12.03;
      let d2 = dx*dx + dy*dy + dz*dz;
      // Departure only ends an unused prompt. Never interrupt a seated action.
      this.Set(q,n"PTFRSKA_Depart",d2 > 49.0 ? 1 : 0);
      let permit = false;
      if d2 <= 4.84 && q.GetFact(n"PTFRSKA_Active") == 0 && this.Eligible(q) {
        permit = this.Safe(p);
      }
      this.Set(q,n"PTFRSKA_Enabled",permit ? 1 : 0);
    }
    this.Schedule(epoch);
  }
}
public class StreetkidAutoTick extends DelayCallback {
  private let driver: wref<StreetkidAuto>;
  private let epoch: Int32;
  public func Call() -> Void { if IsDefined(this.driver) { this.driver.Poll(this.epoch); } }
  public static func Create(driver: ref<StreetkidAuto>,epoch: Int32) -> ref<StreetkidAutoTick> {
    let c = new StreetkidAutoTick(); c.driver = driver; c.epoch = epoch; return c;
  }
}
