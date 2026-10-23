module PTFR.B0OrdinaryBars

// Four native service owners. Full vanilla scenes perform all drink/dialogue
// operations. This system writes ONLY new mod-owned enable/departure facts.
public class OrdinaryBarDriver extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let autoTicks: Int32;
  private let polls: Int32;
  private let positionReads: Int32;
  private let distanceChecks: Int32;
  private let factReads: Int32;
  private let factWrites: Int32;
  private let departureQueries: Int32;
  private let departureChecked: Bool;
  private let departureSafe: Bool;
  private func OnAttach() -> Void {
    this.epoch += 1; this.running = true; this.autoTicks = 0;
    this.Schedule(this.epoch, 1.0);
  }
  private func OnDetach() -> Void { this.running = false; this.epoch += 1; }
  private func Schedule(epoch: Int32, seconds: Float) -> Void {
    let delay = GameInstance.GetDelaySystem(this.GetGameInstance());
    if IsDefined(delay) { delay.DelayCallback(OrdinaryBarTick.Create(this, epoch), seconds, false); }
  }
  public func GetPolls() -> Int32 { return this.polls; }
  public func GetPositionReads() -> Int32 { return this.positionReads; }
  public func GetDistanceChecks() -> Int32 { return this.distanceChecks; }
  public func GetFactReads() -> Int32 { return this.factReads; }
  public func GetFactWrites() -> Int32 { return this.factWrites; }
  public func GetDepartureQueries() -> Int32 { return this.departureQueries; }
  private func Read(q: ref<QuestsSystem>, f: CName) -> Int32 {
    this.factReads += 1; return q.GetFact(f);
  }
  private func Set(q: ref<QuestsSystem>, f: CName, value: Int32) -> Void {
    q.SetFact(f,value); this.factWrites += 1;
  }
  private func AutoSite(q: ref<QuestsSystem>, enabled: CName, ready: CName, excluded: CName, near: CName, far: CName, gate: CName, commit: Bool) -> Bool {
    if this.Read(q,enabled) != 0 || this.Read(q,ready) != 1 || this.Read(q,excluded) != 0 ||
       this.Read(q,near) != 0 || this.Read(q,far) != 0 || this.Read(q,gate) <= 0 { return false; }
    if commit { this.Set(q,enabled,1); }
    return true;
  }
  private func AutoEnable(q: ref<QuestsSystem>, player: ref<PlayerPuppet>) -> Void {
    if this.Read(q,n"PTFRB0BAR_Suspended") != 0 || this.Read(q,n"PTFRBASE_Suspended") != 0 { return; }
    let pending = false;
    pending = this.AutoSite(q, n"PTFRB0BAR01_Enabled", n"PTFRB0BAR01_Ready", n"PTFRB0BAR01_Excluded", n"PTFRB0BAR01_Near", n"PTFRB0BAR01_Far", n"cct_cpz_food_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0BAR02_Enabled", n"PTFRB0BAR02_Ready", n"PTFRB0BAR02_Excluded", n"PTFRB0BAR02_Near", n"PTFRB0BAR02_Far", n"std_arr_foodshop_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0BAR03_Enabled", n"PTFRB0BAR03_Ready", n"PTFRB0BAR03_Excluded", n"PTFRB0BAR03_Near", n"PTFRB0BAR03_Far", n"wat_nid_foodshop_02_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0BAR04_Enabled", n"PTFRB0BAR04_Ready", n"PTFRB0BAR04_Excluded", n"PTFRB0BAR04_Near", n"PTFRB0BAR04_Far", n"wbr_hil_foodshop_01_default_on", false) || pending;
    if !pending { return; }
    let game = this.GetGameInstance();
    let scenes = GameInstance.GetSceneSystem(game).GetScriptInterface();
    let workspots = GameInstance.GetWorkspotSystem(game);
    if !IsDefined(scenes) || !IsDefined(workspots) { return; }
    if player.IsInCombat() || scenes.IsEntityInScene(player.GetEntityID()) || workspots.IsActorInWorkspot(player) { return; }
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
    this.AutoSite(q, n"PTFRB0BAR01_Enabled", n"PTFRB0BAR01_Ready", n"PTFRB0BAR01_Excluded", n"PTFRB0BAR01_Near", n"PTFRB0BAR01_Far", n"cct_cpz_food_01_default_on", true);
    this.AutoSite(q, n"PTFRB0BAR02_Enabled", n"PTFRB0BAR02_Ready", n"PTFRB0BAR02_Excluded", n"PTFRB0BAR02_Near", n"PTFRB0BAR02_Far", n"std_arr_foodshop_01_default_on", true);
    this.AutoSite(q, n"PTFRB0BAR03_Enabled", n"PTFRB0BAR03_Ready", n"PTFRB0BAR03_Excluded", n"PTFRB0BAR03_Near", n"PTFRB0BAR03_Far", n"wat_nid_foodshop_02_default_on", true);
    this.AutoSite(q, n"PTFRB0BAR04_Enabled", n"PTFRB0BAR04_Ready", n"PTFRB0BAR04_Excluded", n"PTFRB0BAR04_Near", n"PTFRB0BAR04_Far", n"wbr_hil_foodshop_01_default_on", true);
    if this.Read(q,n"PTFRB0BAR_Mode") != 1 { this.Set(q,n"PTFRB0BAR_Mode",1); }
  }
  private func CanDepart(q: ref<QuestsSystem>, player: ref<PlayerPuppet>, drinking: CName) -> Bool {
    // Never clear a vanilla drinking flag or force V out of a workspot.
    if this.Read(q,drinking) != 0 { return false; }
    if !this.departureChecked {
      this.departureChecked = true;
      this.departureQueries += 1;
      let workspots = GameInstance.GetWorkspotSystem(this.GetGameInstance());
      this.departureSafe = IsDefined(workspots) && !workspots.IsActorInWorkspot(player);
    }
    return this.departureSafe;
  }
  private func UpdateSite(q: ref<QuestsSystem>, player: ref<PlayerPuppet>, p: Vector4, enabled: CName, near: CName, far: CName, gate: CName, drinking: CName, x: Float, y: Float, z: Float, rearm2: Float, exit2: Float) -> Void {
    if this.Read(q,enabled) != 1 { return; }
    let old = this.Read(q,far);
    if this.Read(q,near) != 1 && old != 1 { return; }
    let value: Int32;
    if this.Read(q,gate) <= 0 { value = 1; } else {
      let dx = p.X-x; let dy = p.Y-y; let dz = p.Z-z;
      let d2 = dx*dx+dy*dy+dz*dz; this.distanceChecks += 1;
      value = old == 1 ? (d2 >= rearm2 ? 1 : 0) : (d2 > exit2 ? 1 : 0);
    }
    // Check the expensive player workspot query only on a proposed departure,
    // at most once per tick, not four times during every ordinary sample.
    if old == 0 && value == 1 && !this.CanDepart(q,player,drinking) { return; }
    if value != old { this.Set(q,far,value); }
  }
  public func Poll(expectedEpoch: Int32) -> Void {
    if !this.running || expectedEpoch != this.epoch { return; }
    this.polls += 1;
    this.departureChecked = false; this.departureSafe = false;
    let game = this.GetGameInstance(); let q = GameInstance.GetQuestsSystem(game);
    if !IsDefined(q) { this.Schedule(expectedEpoch,1.0); return; }
    let eligible = true;
    if this.Read(q,n"PostTowerFreeRoamActive") != 1 { eligible = false; }
    if this.Read(q,n"PTFRP0_DR13") != 1 { eligible = false; }
    if this.Read(q,n"q307_active") != 0 { eligible = false; }
    if this.Read(q,n"q307_done") != 1 { eligible = false; }
    if this.Read(q,n"q307_finished") != 1 { eligible = false; }
    if this.Read(q,n"q307_2079") != 1 { eligible = false; }
    if this.Read(q,n"q307_main_game_killed") != 1 { eligible = false; }
    if this.Read(q,n"q305_johnny_scene_active") != 0 { eligible = false; }
    if this.Read(q,n"q115_point_of_no_return") != 0 { eligible = false; }
    if this.Read(q,n"q000_done") != 1 { eligible = false; }
    if !eligible { this.Schedule(expectedEpoch,1.0); return; }
    let players = GameInstance.GetPlayerSystem(game);
    if !IsDefined(players) { this.Schedule(expectedEpoch,1.0); return; }
    let player = players.GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(player) { this.Schedule(expectedEpoch,1.0); return; }
    if this.autoTicks <= 0 { this.AutoEnable(q,player); this.autoTicks = 10; }
    this.autoTicks -= 1;
    if this.Read(q,n"PTFRB0BAR_Mode") != 1 { this.Schedule(expectedEpoch,1.0); return; }
    let position = player.GetWorldPosition(); this.positionReads += 1;
    this.UpdateSite(q, player, position, n"PTFRB0BAR01_Enabled", n"PTFRB0BAR01_Near", n"PTFRB0BAR01_Far", n"cct_cpz_food_01_default_on", n"cct_dtn_food_02_drinking_active", -1521.818970000, -326.054718000, -4.519288060, 2025.0, 4225.0);
    this.UpdateSite(q, player, position, n"PTFRB0BAR02_Enabled", n"PTFRB0BAR02_Near", n"PTFRB0BAR02_Far", n"std_arr_foodshop_01_default_on", n"std_arr_foodshop_01_drinking_active", -723.739014000, -997.623169000, 7.712788580, 2025.0, 3025.0);
    this.UpdateSite(q, player, position, n"PTFRB0BAR03_Enabled", n"PTFRB0BAR03_Near", n"PTFRB0BAR03_Far", n"wat_nid_foodshop_02_default_on", n"wat_nid_foodshop_02_drinking_active", -1714.089360000, 2223.503170000, 87.270576500, 2025.0, 3025.0);
    this.UpdateSite(q, player, position, n"PTFRB0BAR04_Enabled", n"PTFRB0BAR04_Near", n"PTFRB0BAR04_Far", n"wbr_hil_foodshop_01_default_on", n"wbr_hil_01_drinking_active", -258.517578000, -57.567382800, 1.665508030, 2025.0, 3025.0);
    this.Schedule(expectedEpoch,0.5);
  }
}
public class OrdinaryBarTick extends DelayCallback {
  private let driver: wref<OrdinaryBarDriver>;
  private let epoch: Int32;
  public func Call() -> Void { if IsDefined(this.driver) { this.driver.Poll(this.epoch); } }
  public static func Create(driver: ref<OrdinaryBarDriver>, epoch: Int32) -> ref<OrdinaryBarTick> {
    let callback = new OrdinaryBarTick(); callback.driver = driver; callback.epoch = epoch; return callback;
  }
}
