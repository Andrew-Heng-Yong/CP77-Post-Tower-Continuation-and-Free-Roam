module PTFR.ZetatechIdlesR12

// Add an interruptible native smoking workspot to the existing private Terry.
// Never spawn, resurrect, move or select an original q307 actor.
public class TerryIdleR12 extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let actor: wref<NPCPuppet>;
  private let command: ref<AIUseWorkspotCommand>;
  private let requests: Int32;
  private let cooldown: Int32;

  private func OnAttach() -> Void {
    this.epoch += 1;
    this.running = true;
    this.actor = null;
    this.command = null;
    this.requests = 0;
    this.cooldown = 0;
    this.Schedule(this.epoch);
  }
  private func OnDetach() -> Void {
    this.running = false;
    this.epoch += 1;
    this.CancelOwned();
  }
  private func Schedule(epoch: Int32) -> Void {
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(TerryIdleR12Tick.Create(this, epoch), 1.0, false);
  }
  private func Count(name: CName) -> Void {
    let q = GameInstance.GetQuestsSystem(this.GetGameInstance());
    q.SetFact(name, q.GetFact(name) + 1);
  }
  private func Allowed(q: ref<QuestsSystem>) -> Bool {
    return q.GetFact(n"PostTowerFreeRoamActive") == 1 && q.GetFact(n"PTFRP0_DR13") == 1 &&
      q.GetFact(n"q307_active") == 0 && q.GetFact(n"q307_done") == 1 &&
      q.GetFact(n"q307_finished") == 1 && q.GetFact(n"q307_2079") == 1 &&
      q.GetFact(n"q307_main_game_killed") == 1 && q.GetFact(n"q307_ep1_killed") == 1 &&
      q.GetFact(n"q305_johnny_scene_active") == 0 && q.GetFact(n"q115_point_of_no_return") == 0 &&
      q.GetFact(n"PTFRBASE_Suspended") == 0 && q.GetFact(n"PTFRWORLD_Suspended") == 0 &&
      q.GetFact(n"PTFRMV_Suspended") == 0 && q.GetFact(n"PTFRMV_QuestOwns") == 0 &&
      q.GetFact(n"PTFRMV_Enabled") == 1 && q.GetFact(n"PTFRMV_Applied") == 1 &&
      q.GetFact(n"PTFRMV_AccessRevision") == 11 && q.GetFact(n"PTFRMV12_TerrySpotReady") == 1;
  }
  private func CancelOwned() -> Void {
    if IsDefined(this.command) && IsDefined(this.actor) {
      let ai = this.actor.GetAIControllerComponent();
      if IsDefined(ai) { ai.CancelCommand(this.command); }
    }
    this.command = null;
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    this.Schedule(epoch);
    let q = GameInstance.GetQuestsSystem(this.GetGameInstance());
    let system = GameInstance.GetDynamicEntitySystem();
    if !IsDefined(q) || !IsDefined(system) || !system.IsReady() || !this.Allowed(q) {
      this.CancelOwned();
      return;
    }
    let ids = system.GetTaggedIDs(n"PTFRMV11_Terry");
    if ArraySize(ids) != 1 || !system.IsManaged(ids[0]) || !system.IsTagged(ids[0], n"PTFRMV11_Terry") { this.CancelOwned(); return; }
    let npc = system.GetEntity(ids[0]) as NPCPuppet;
    if !IsDefined(npc) || npc.GetRecordID() != t"Character.PTFRMV_Terry" { this.CancelOwned(); return; }
    if !IsDefined(this.actor) || this.actor != npc {
      this.CancelOwned();
      this.actor = npc;
      this.requests = 0;
      this.cooldown = 5;
    }
    let scene = GameInstance.GetSceneSystem(this.GetGameInstance()).GetScriptInterface();
    if npc.IsDead() || NPCPuppet.IsInCombat(npc) || !IsDefined(scene) || scene.IsEntityInScene(npc.GetEntityID()) {
      this.CancelOwned();
      this.cooldown = 20;
      return;
    }
    if this.cooldown > 0 { this.cooldown -= 1; return; }
    let ai = npc.GetAIControllerComponent();
    if !IsDefined(ai) { return; }
    if IsDefined(this.command) {
      let state = ai.GetCommandState(this.command);
      if Equals(state, AICommandState.Executing) || Equals(state, AICommandState.Enqueued) { return; }
      this.command = null;
      this.cooldown = 10;
      return;
    }
    if this.requests >= 3 || GameInstance.GetWorkspotSystem(this.GetGameInstance()).IsActorInWorkspot(npc) { return; }
    // Do not pull an actor back after fighting or chasing V away from this spot.
    let pos = npc.GetWorldPosition();
    let dx = pos.X + 1551.20374;
    let dy = pos.Y - 1172.57251;
    let dz = pos.Z - 16.3103752;
    if dx * dx + dy * dy + dz * dz > 25.0 { return; }
    let command = new AIUseWorkspotCommand();
    command.workspotNode = CreateNodeRef("$/03_night_city/#PTFRMV12_TerrySmoke");
    command.moveToWorkspot = true;
    command.movementType = moveMovementType.Walk;
    command.continueInCombat = false;
    command.forceEntryAnimName = n"None";
    command.jumpToEntry = false;
    this.requests += 1;
    if ai.SendCommand(command) {
      this.command = command;
      this.Count(n"PTFRMV12_TerryIdleRequests");
    } else {
      this.cooldown = 10;
      this.Count(n"PTFRMV12_TerryIdleFailures");
    }
  }
}
public class TerryIdleR12Tick extends DelayCallback {
  private let driver: wref<TerryIdleR12>;
  private let epoch: Int32;
  public func Call() -> Void { if IsDefined(this.driver) { this.driver.Poll(this.epoch); } }
  public static func Create(driver: ref<TerryIdleR12>, epoch: Int32) -> ref<TerryIdleR12Tick> {
    let tick = new TerryIdleR12Tick(); tick.driver = driver; tick.epoch = epoch; return tick;
  }
}
