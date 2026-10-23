module PTFR.B0CPZFood02

// Generated site calls come from the audited cohort. Native owners retain
// their complete vanilla scenes and own spawning, entry and exit.
public class CPZFood02Driver extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let polls: Int32;
  private let positionReads: Int32;
  private let distanceChecks: Int32;
  private let factReads: Int32;
  private let factWrites: Int32;
  private let autoTicks: Int32;

  private func OnAttach() -> Void {
    this.epoch += 1;
    this.running = true;
    this.autoTicks = 0;
    this.Schedule(this.epoch, 1.0);
  }
  private func OnDetach() -> Void {
    this.running = false;
    this.epoch += 1;
  }
  private func Schedule(epoch: Int32, seconds: Float) -> Void {
    let delays = GameInstance.GetDelaySystem(this.GetGameInstance());
    if IsDefined(delays) {
      delays.DelayCallback(CPZFood02Tick.Create(this, epoch), seconds, false);
    }
  }
  public func GetPolls() -> Int32 { return this.polls; }
  public func GetPositionReads() -> Int32 { return this.positionReads; }
  public func GetDistanceChecks() -> Int32 { return this.distanceChecks; }
  public func GetFactReads() -> Int32 { return this.factReads; }
  public func GetFactWrites() -> Int32 { return this.factWrites; }

  private func ReadFact(q: ref<QuestsSystem>, key: CName) -> Int32 {
    this.factReads += 1;
    return q.GetFact(key);
  }

  // Never reset an in-flight/saved native owner or an explicit exclusion.
  private func AutoSite(q: ref<QuestsSystem>, enabled: CName, ready: CName, excluded: CName, near: CName, far: CName, gate: CName, commit: Bool) -> Bool {
    if this.ReadFact(q, enabled) != 0 || this.ReadFact(q, excluded) != 0 ||
       this.ReadFact(q, ready) != 1 || this.ReadFact(q, near) != 0 ||
       this.ReadFact(q, far) != 0 || this.ReadFact(q, gate) <= 0 { return false; }
    if commit {
      q.SetFact(enabled, 1);
      this.factWrites += 1;
    }
    return true;
  }

  private func AutoEnable(q: ref<QuestsSystem>, player: ref<PlayerPuppet>) -> Void {
    if this.ReadFact(q, n"PTFRB0CPZF2_Suspended") != 0 || this.ReadFact(q, n"PTFRBASE_Suspended") != 0 { return; }
    let pending = false;
    pending = this.AutoSite(q, n"PTFRB0CPZF2_Enabled", n"PTFRB0CPZF2_Ready", n"PTFRB0CPZF2_Excluded", n"PTFRB0CPZF2_Near", n"PTFRB0CPZF2_Far", n"cct_cpz_food_02_default_on", false) || pending;
    if !pending { return; }
    // Expensive safety queries run once per activation attempt, not per shop
    // or departure tick. Original native eligibility is rechecked on entry.
    let game = this.GetGameInstance();
    let scene = GameInstance.GetSceneSystem(game).GetScriptInterface();
    let workspots = GameInstance.GetWorkspotSystem(game);
    if !IsDefined(scene) || !IsDefined(workspots) { return; }
    if player.IsInCombat() || scene.IsEntityInScene(player.GetEntityID()) ||
       workspots.IsActorInWorkspot(player) { return; }
    let mounting = GameInstance.GetMountingFacility(game).GetMountingInfoSingleWithObjects(player);
    if EntityID.IsDefined(mounting.parentId) { return; }
    let board = player.GetPlayerStateMachineBlackboard();
    if !IsDefined(board) { return; }
    let high = board.GetInt(GetAllBlackboardDefs().PlayerStateMachine.HighLevel);
    let tier = board.GetInt(GetAllBlackboardDefs().PlayerStateMachine.SceneTier);
    if (high != 1 && high != 2) || (tier != 1 && tier != 2) { return; }
    if GameInstance.GetQuestsContentSystem(game).IsTokensActivationBlocked() { return; }
    let locks: array<gameSaveLock>;
    if GameInstance.IsSavingLocked(game,locks) { return; }
    this.AutoSite(q, n"PTFRB0CPZF2_Enabled", n"PTFRB0CPZF2_Ready", n"PTFRB0CPZF2_Excluded", n"PTFRB0CPZF2_Near", n"PTFRB0CPZF2_Far", n"cct_cpz_food_02_default_on", true);
    if this.ReadFact(q, n"PTFRB0CPZF2_Mode") != 1 {
      q.SetFact(n"PTFRB0CPZF2_Mode", 1);
      this.factWrites += 1;
    }
    q.SetFact(n"PTFRB0CPZF2_AutoPasses", this.ReadFact(q, n"PTFRB0CPZF2_AutoPasses") + 1);
    this.factWrites += 1;
  }

  private func UpdateSite(q: ref<QuestsSystem>, p: Vector4, enabled: CName, near: CName, far: CName, gate: CName, x: Float, y: Float, z: Float, rearm2: Float, exit2: Float) -> Void {
    this.factReads += 1;
    if q.GetFact(enabled) != 1 { return; }
    this.factReads += 2;
    let old = q.GetFact(far);
    let nearValue = q.GetFact(near);
    // Do not force Far before this owner's first native entry.
    if nearValue != 1 && old != 1 { return; }
    this.factReads += 1;
    let value: Int32;
    if q.GetFact(gate) <= 0 {
      value = 1; // finish active service when vanilla availability closes
    } else {
      let dx = p.X - x;
      let dy = p.Y - y;
      let dz = p.Z - z;
      let d2 = dx * dx + dy * dy + dz * dz;
      this.distanceChecks += 1;
      value = old == 1 ? (d2 >= rearm2 ? 1 : 0) : (d2 > exit2 ? 1 : 0);
    }
    if value != old {
      q.SetFact(far, value);
      this.factWrites += 1;
    }
  }

  public func Poll(expectedEpoch: Int32) -> Void {
    if !this.running || expectedEpoch != this.epoch { return; }
    this.polls += 1;
    let game = this.GetGameInstance();
    let q = GameInstance.GetQuestsSystem(game);
    if !IsDefined(q) { this.Schedule(expectedEpoch, 1.0); return; }
    // Count exactly the fact reads executed, independent of short circuiting.
    this.factReads += 1;
    let mode = q.GetFact(n"PTFRB0CPZF2_Mode");
    this.factReads += 2;
    let challenge = q.GetFact(n"PTFRB0CPZF2_Challenge");
    let ack = q.GetFact(n"PTFRB0CPZF2_Ack");
    let eligible = true;
    this.factReads += 1;
    if q.GetFact(n"PostTowerFreeRoamActive") != 1 { eligible = false; }
    this.factReads += 1;
    if q.GetFact(n"PTFRP0_DR13") != 1 { eligible = false; }
    this.factReads += 1;
    if q.GetFact(n"q307_active") != 0 { eligible = false; }
    this.factReads += 1;
    if q.GetFact(n"q307_done") != 1 { eligible = false; }
    this.factReads += 1;
    if q.GetFact(n"q307_finished") != 1 { eligible = false; }
    this.factReads += 1;
    if q.GetFact(n"q307_2079") != 1 { eligible = false; }
    this.factReads += 1;
    if q.GetFact(n"q307_main_game_killed") != 1 { eligible = false; }
    this.factReads += 1;
    if q.GetFact(n"q305_johnny_scene_active") != 0 { eligible = false; }
    this.factReads += 1;
    if q.GetFact(n"q115_point_of_no_return") != 0 { eligible = false; }
    this.factReads += 1;
    if q.GetFact(n"q000_done") != 1 { eligible = false; }
    if !eligible { this.Schedule(expectedEpoch, 1.0); return; }
    if challenge != 0 && ack != challenge {
      q.SetFact(n"PTFRB0CPZF2_Ack", challenge);
      this.factWrites += 1;
    }
    let players = GameInstance.GetPlayerSystem(game);
    if !IsDefined(players) { this.Schedule(expectedEpoch, 1.0); return; }
    let player = players.GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(player) { this.Schedule(expectedEpoch, 1.0); return; }
    if this.autoTicks <= 0 {
      this.AutoEnable(q, player);
      this.autoTicks = 10;
    }
    this.autoTicks -= 1;
    mode = this.ReadFact(q, n"PTFRB0CPZF2_Mode");
    if mode != 1 { this.Schedule(expectedEpoch, 1.0); return; }
    let position = player.GetWorldPosition();
    this.positionReads += 1;
    this.UpdateSite(q, position, n"PTFRB0CPZF2_Enabled", n"PTFRB0CPZF2_Near", n"PTFRB0CPZF2_Far", n"cct_cpz_food_02_default_on", -1540.675290000, -304.291748000, -4.425808430, 2025.0, 2500.0);
    this.Schedule(expectedEpoch, 0.5);
  }
}

public class CPZFood02Tick extends DelayCallback {
  private let driver: wref<CPZFood02Driver>;
  private let epoch: Int32;
  public func Call() -> Void {
    if IsDefined(this.driver) { this.driver.Poll(this.epoch); }
  }
  public static func Create(driver: ref<CPZFood02Driver>, epoch: Int32) -> ref<CPZFood02Tick> {
    let result = new CPZFood02Tick();
    result.driver = driver;
    result.epoch = epoch;
    return result;
  }
}
