module PTFR.AfterlifeIdlesR3

// R6 revision retains R3 class/resource identities for a two-file replacement.
// Repair only the original four community actors. Never spawn, reset a
// community, select actors by record alone, or take over a working routine.
public class BoothRoutineR3 extends IScriptable {
  public let entry: CName;
  public let spot: NodeRef;
  public let ready: CName;
  public let position: Vector4;
  public let actor: wref<NPCPuppet>;
  public let command: ref<AIUseWorkspotCommand>;
  public let requests: Int32;
  public let quiet: Int32;
  public let age: Int32;
  public let cooldown: Int32;
  public let lastPosition: Vector4;
  public let hasPosition: Bool;
  public let directStarts: Int32;

  public func Cancel() -> Void {
    if IsDefined(this.actor) && IsDefined(this.command) {
      let ai = this.actor.GetAIControllerComponent();
      if IsDefined(ai) { ai.CancelCommand(this.command); }
    }
    this.command = null;
    this.quiet = 0;
    this.age = 0;
  }

  public static func Create(entry: CName, spot: NodeRef, ready: CName, position: Vector4) -> ref<BoothRoutineR3> {
    let row = new BoothRoutineR3();
    row.entry = entry; row.spot = spot; row.ready = ready; row.position = position;
    return row;
  }
}

public class AfterlifeIdlesR3 extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let rows: array<ref<BoothRoutineR3>>;

  private func OnAttach() -> Void {
    this.epoch += 1;
    this.running = true;
    ArrayClear(this.rows);
    ArrayPush(this.rows, BoothRoutineR3.Create(n"merc_01", CreateNodeRef("$/03_night_city/#PTFRAL3_Merc01"), n"PTFRAL3_Merc01Ready", new Vector4(-1424.50439, 1023.75653, 16.9300003, 1.0)));
    ArrayPush(this.rows, BoothRoutineR3.Create(n"merc_02", CreateNodeRef("$/03_night_city/#PTFRAL3_Merc02"), n"PTFRAL3_Merc02Ready", new Vector4(-1423.26575, 1021.67981, 16.8999977, 1.0)));
    ArrayPush(this.rows, BoothRoutineR3.Create(n"merc_03", CreateNodeRef("$/03_night_city/#PTFRAL3_Merc03"), n"PTFRAL3_Merc03Ready", new Vector4(-1425.74207, 1022.95142, 16.8699989, 1.0)));
    ArrayPush(this.rows, BoothRoutineR3.Create(n"merc_04", CreateNodeRef("$/03_night_city/#PTFRAL3_Merc04"), n"PTFRAL3_Merc04Ready", new Vector4(-1423.35522, 1023.35358, 16.9099998, 1.0)));
    this.Schedule();
  }
  private func OnDetach() -> Void {
    this.running = false; this.epoch += 1;
    for row in this.rows { row.Cancel(); }
  }
  private func Schedule() -> Void {
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(AfterlifeIdlesR3Tick.Create(this, this.epoch), 0.25, false);
  }
  private func Allowed(q: ref<QuestsSystem>) -> Bool {
    return q.GetFact(n"PostTowerFreeRoamActive") == 1 && q.GetFact(n"PTFRP0_DR13") == 1 &&
      q.GetFact(n"q307_active") == 0 && q.GetFact(n"q307_done") == 1 &&
      q.GetFact(n"q307_finished") == 1 && q.GetFact(n"q307_2079") == 1 &&
      q.GetFact(n"q307_main_game_killed") == 1 && q.GetFact(n"q307_ep1_killed") == 1 &&
      q.GetFact(n"q305_johnny_scene_active") == 0 && q.GetFact(n"q115_point_of_no_return") == 0 &&
      q.GetFact(n"PTFRBASE_Suspended") == 0 && q.GetFact(n"PTFRWORLD_Suspended") == 0 &&
      q.GetFact(n"PTFRAL1_Enabled") == 1 && q.GetFact(n"PTFRAL1_QuestOwns") == 0 && q.GetFact(n"PTFRAL1_Suspended") == 0 &&
      q.GetFact(n"q103_done") == 1 && q.GetFact(n"q103_active") == 0 &&
      q.GetFact(n"q005_done") == 1 && q.GetFact(n"q005_plan_finished") == 1 &&
      q.GetFact(n"PTFRAL2_Migration") == 2 && q.GetFact(n"PTFRAL2_LocalActive") == 1 &&
      q.GetFact(n"PTFRAL3_Suspended") == 0 && q.GetFact(n"PTFRAL3_WorldApplied") == 1;
  }
  private func Count(q: ref<QuestsSystem>, name: CName) -> Void {
    q.SetFact(name, q.GetFact(name) + 1);
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    this.Schedule();
    let game = this.GetGameInstance();
    let q = GameInstance.GetQuestsSystem(game);
    let player = GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
    let scenes = GameInstance.GetSceneSystem(game).GetScriptInterface();
    let workspots = GameInstance.GetWorkspotSystem(game);
    if !IsDefined(q) || !IsDefined(player) || !IsDefined(scenes) || !IsDefined(workspots) || !this.Allowed(q) || player.IsInCombat() || scenes.IsEntityInScene(player.GetEntityID()) {
      for row in this.rows { row.Cancel(); row.cooldown = 5; }
      return;
    }
    for row in this.rows { this.UpdateRow(row, q); }
  }
  private func UpdateRow(row: ref<BoothRoutineR3>, q: ref<QuestsSystem>) -> Void {
    let game = this.GetGameInstance();
    let ids: array<EntityID>;
    let names: array<CName>;
    ArrayPush(names, row.entry);
    // Vanilla core/systems/questSystem uses this native resolver. An empty or
    // ambiguous result is UNKNOWN, never permission to respawn or guess.
    GetFixedEntityIdsFromEntityReference(CreateEntityReference("$/03_night_city/c_watson/little_china/#loc_q103_afterlife/loc_q103_afterlife_questdesign_prefabPGWI5FY/#afterlife_pr_default_community/#q005_com_afterlife_community", names), game, ids);
    if ArraySize(ids) != 1 || q.GetFact(row.ready) != 1 {
      row.Cancel(); row.hasPosition = false; return;
    }
    let npc = GameInstance.FindEntityByID(game, ids[0]) as NPCPuppet;
    if !IsDefined(npc) || npc.GetRecordID() != t"Character.q005_afterlife_mercenary_male" {
      row.Cancel(); row.hasPosition = false; return;
    }
    if !IsDefined(row.actor) || row.actor != npc {
      row.Cancel(); row.actor = npc; row.requests = 0; row.directStarts = 0;
      row.cooldown = RandRange(0, 4); row.hasPosition = false;
    }
    let scene = GameInstance.GetSceneSystem(game).GetScriptInterface();
    let workspots = GameInstance.GetWorkspotSystem(game);
    let pos = npc.GetWorldPosition();
    if npc.IsDead() || ScriptedPuppet.IsDefeated(npc) || npc.IsAboutToDieOrDefeated() || NPCPuppet.IsInCombat(npc) || NotEquals(npc.GetHighLevelStateFromBlackboard(), gamedataNPCHighLevelState.Relaxed) || scene.IsEntityInScene(npc.GetEntityID()) || Vector4.DistanceSquared(pos, row.position) > 9.0 {
      row.Cancel(); row.cooldown = 80; row.hasPosition = false; return;
    }
    let ai = npc.GetAIControllerComponent();
    if !IsDefined(ai) { row.Cancel(); return; }
    if IsDefined(row.command) {
      let state = ai.GetCommandState(row.command);
      if Equals(state, AICommandState.Executing) || Equals(state, AICommandState.Enqueued) {
        if workspots.IsActorInWorkspot(npc) { row.age = 0; return; }
        row.age += 1;
        if row.age < 80 { return; }
        row.Cancel(); row.cooldown = 80;
        this.Count(q, n"PTFRAL3_Timeouts");
        return;
      }
      row.command = null; row.cooldown = 40; row.quiet = 0;
      return;
    }
    if row.cooldown > 0 { row.cooldown -= 1; row.hasPosition = false; return; }
    if row.requests >= 3 || workspots.IsActorInWorkspot(npc) { row.quiet = 0; row.hasPosition = false; return; }
    // Direct idle admission is restricted to the authored anchor: <=35cm,
    // <=15cm vertical error, exact actor, relaxed and scene/workspot-free.
    // Else retain a five-second stationary gate and ordinary walking entry.
    let atAnchor = Vector4.DistanceSquared(pos, row.position) <= 0.1225 && AbsF(pos.Z - row.position.Z) <= 0.15;
    if !row.hasPosition || Vector4.DistanceSquared(pos, row.lastPosition) > 0.01 { row.quiet = 0; }
    else { row.quiet += 1; }
    row.lastPosition = pos; row.hasPosition = true;
    if row.quiet < (atAnchor ? 2 : 20) { return; }
    let command = new AIUseWorkspotCommand();
    command.workspotNode = row.spot;
    command.moveToWorkspot = !atAnchor;
    command.movementType = moveMovementType.Walk;
    command.continueInCombat = false;
    command.forceEntryAnimName = n"None";
    command.jumpToEntry = atAnchor;
    if atAnchor {
      let entry: WorkEntryId; entry.id = 2u;
      command.entryId = entry;
    }
    row.requests += 1; row.quiet = 0; row.age = 0;
    if ai.SendCommand(command) {
      row.command = command; this.Count(q, n"PTFRAL3_Requests");
      if atAnchor { row.directStarts += 1; }
    } else {
      row.cooldown = 80; this.Count(q, n"PTFRAL3_Failures");
    }
  }
  public func GetStatus() -> String {
    let result = "Booth R6";
    let workspots = GameInstance.GetWorkspotSystem(this.GetGameInstance());
    for row in this.rows {
      let active = IsDefined(row.actor) && workspots.IsActorInWorkspot(row.actor);
      result += " | " + NameToString(row.entry) + " requests=" + ToString(row.requests) +
        " direct=" + ToString(row.directStarts) + " workspot=" + ToString(active);
    }
    return result;
  }
}
public class AfterlifeIdlesR3Tick extends DelayCallback {
  private let driver: wref<AfterlifeIdlesR3>;
  private let epoch: Int32;
  public func Call() -> Void { if IsDefined(this.driver) { this.driver.Poll(this.epoch); } }
  public static func Create(driver: ref<AfterlifeIdlesR3>, epoch: Int32) -> ref<AfterlifeIdlesR3Tick> {
    let tick = new AfterlifeIdlesR3Tick(); tick.driver = driver; tick.epoch = epoch; return tick;
  }
}
