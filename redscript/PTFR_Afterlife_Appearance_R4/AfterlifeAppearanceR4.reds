module PTFR.AfterlifeAppearanceR4

// Restore only authored appearances for four exact original community entries.
// No spawning, record-based deduplication, crowd pool edits or AI commands.
public class BoothAppearanceR4 extends IScriptable {
  public let entry: CName;
  public let actor: wref<NPCPuppet>;
  public let attempted: Bool;
  public let quiet: Int32;
  public let hasPosition: Bool;
  public let lastPosition: Vector4;

  public static func Create(entry: CName) -> ref<BoothAppearanceR4> {
    let row = new BoothAppearanceR4();
    row.entry = entry;
    return row;
  }
}

public class AfterlifeAppearanceR4 extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let rows: array<ref<BoothAppearanceR4>>;

  private func OnAttach() -> Void {
    this.epoch += 1;
    this.running = true;
    ArrayClear(this.rows);
    ArrayPush(this.rows, BoothAppearanceR4.Create(n"merc_01"));
    ArrayPush(this.rows, BoothAppearanceR4.Create(n"merc_02"));
    ArrayPush(this.rows, BoothAppearanceR4.Create(n"merc_03"));
    ArrayPush(this.rows, BoothAppearanceR4.Create(n"merc_04"));
    this.Schedule();
  }
  private func OnDetach() -> Void {
    this.running = false;
    this.epoch += 1;
  }
  private func Schedule() -> Void {
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(AfterlifeAppearanceR4Tick.Create(this, this.epoch), 1.0, false);
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
      q.GetFact(n"PTFRAL3_Suspended") == 0 && q.GetFact(n"PTFRAL4_Suspended") == 0;
  }
  private func ResetQuiet(row: ref<BoothAppearanceR4>) -> Void {
    row.quiet = 0;
    row.hasPosition = false;
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    this.Schedule();
    let game = this.GetGameInstance();
    let q = GameInstance.GetQuestsSystem(game);
    let player = GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
    let scenes = GameInstance.GetSceneSystem(game).GetScriptInterface();
    if !IsDefined(q) || !IsDefined(player) || !IsDefined(scenes) || !this.Allowed(q) || player.IsInCombat() || scenes.IsEntityInScene(player.GetEntityID()) || Vector4.DistanceSquared(player.GetWorldPosition(), new Vector4(-1424.5, 1023.0, 16.9, 1.0)) > 900.0 {
      for row in this.rows { this.ResetQuiet(row); }
      return;
    }
    for row in this.rows { this.UpdateRow(row); }
  }
  private func UpdateRow(row: ref<BoothAppearanceR4>) -> Void {
    let game = this.GetGameInstance();
    let ids: array<EntityID>;
    let names: array<CName>;
    ArrayPush(names, row.entry);
    GetFixedEntityIdsFromEntityReference(CreateEntityReference("$/03_night_city/c_watson/little_china/#loc_q103_afterlife/loc_q103_afterlife_questdesign_prefabPGWI5FY/#afterlife_pr_default_community/#q005_com_afterlife_community", names), game, ids);
    if ArraySize(ids) != 1 { this.ResetQuiet(row); return; }
    let npc = GameInstance.FindEntityByID(game, ids[0]) as NPCPuppet;
    if !IsDefined(npc) || npc.GetRecordID() != t"Character.q005_afterlife_mercenary_male" { this.ResetQuiet(row); return; }
    if !IsDefined(row.actor) || row.actor != npc {
      row.actor = npc;
      row.attempted = false;
      this.ResetQuiet(row);
    }
    // Every authored phase for each of these four entries uses its own entry
    // name as appearance. All four names exist in the original entity template.
    let current = npc.GetCurrentAppearanceName();
    if Equals(current, row.entry) || row.attempted { this.ResetQuiet(row); return; }
    // Do not overwrite an unknown/custom appearance or choose a random skin.
    if NotEquals(current, n"merc_01") && NotEquals(current, n"merc_02") && NotEquals(current, n"merc_03") && NotEquals(current, n"merc_04") { this.ResetQuiet(row); return; }
    let scenes = GameInstance.GetSceneSystem(game).GetScriptInterface();
    let workspots = GameInstance.GetWorkspotSystem(game);
    let pos = npc.GetWorldPosition();
    if !IsDefined(scenes) || !IsDefined(workspots) || npc.IsDead() || ScriptedPuppet.IsDefeated(npc) || npc.IsAboutToDieOrDefeated() || NPCPuppet.IsInCombat(npc) || NotEquals(npc.GetHighLevelStateFromBlackboard(), gamedataNPCHighLevelState.Relaxed) || scenes.IsEntityInScene(npc.GetEntityID()) || workspots.IsActorInWorkspot(npc) || Vector4.DistanceSquared(pos, new Vector4(-1424.5, 1023.0, 16.9, 1.0)) > 36.0 {
      this.ResetQuiet(row); return;
    }
    if !row.hasPosition || Vector4.DistanceSquared(pos, row.lastPosition) > 0.01 { row.quiet = 0; }
    else { row.quiet += 1; }
    row.lastPosition = pos;
    row.hasPosition = true;
    if row.quiet < 3 { return; }
    // One request per retained actor, even if another owner later changes it.
    // Native SetAppearance AI task uses this API; dispatch is not render proof.
    row.attempted = true;
    npc.ScheduleAppearanceChange(row.entry);
    this.ResetQuiet(row);
  }
}

public class AfterlifeAppearanceR4Tick extends DelayCallback {
  private let driver: wref<AfterlifeAppearanceR4>;
  private let epoch: Int32;
  public func Call() -> Void { if IsDefined(this.driver) { this.driver.Poll(this.epoch); } }
  public static func Create(driver: ref<AfterlifeAppearanceR4>, epoch: Int32) -> ref<AfterlifeAppearanceR4Tick> {
    let tick = new AfterlifeAppearanceR4Tick();
    tick.driver = driver;
    tick.epoch = epoch;
    return tick;
  }
}
