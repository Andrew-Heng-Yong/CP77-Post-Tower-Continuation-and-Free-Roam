module PTFR.RestorationBaseline

// Baseline-R1: startup for EXISTING native resources, not duplicate owners.
// No vanilla fact writer; counters, in-flight owners and interruptions retained.
public class RestorationBaseline extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let startupTicks: Int32;
  private let polls: Int32;
  private let writes: Int32;
  private let distances: Int32;
  private let safetyReads: Int32;
  private func OnAttach() -> Void {
    this.epoch += 1; this.running = true; this.startupTicks = 0;
    this.Schedule(this.epoch, 1.0);
  }
  private func OnDetach() -> Void { this.running = false; this.epoch += 1; }
  private func Schedule(epoch: Int32, seconds: Float) -> Void {
    let delay = GameInstance.GetDelaySystem(this.GetGameInstance());
    if IsDefined(delay) { delay.DelayCallback(RestorationBaselineTick.Create(this, epoch), seconds, false); }
  }
  public func GetPolls() -> Int32 { return this.polls; }
  public func GetWrites() -> Int32 { return this.writes; }
  public func GetDistances() -> Int32 { return this.distances; }
  public func GetSafetyReads() -> Int32 { return this.safetyReads; }
  private func Set(q: ref<QuestsSystem>, key: CName, value: Int32) -> Void {
    if q.GetFact(key) != value { q.SetFact(key, value); this.writes += 1; }
  }
  private func D2(p: Vector4, x: Float, y: Float, z: Float) -> Float {
    let dx = p.X-x; let dy = p.Y-y; let dz = p.Z-z;
    this.distances += 1;
    return dx*dx+dy*dy+dz*dz;
  }
  private func Far(q: ref<QuestsSystem>, p: Vector4, enabled: CName, near: CName, far: CName, gate: CName, x: Float, y: Float, z: Float) -> Void {
    if q.GetFact(enabled) != 1 { return; }
    let old = q.GetFact(far);
    if q.GetFact(near) != 1 && old != 1 { return; }
    let value: Int32;
    if q.GetFact(gate) != 1 { value = 1; } else {
      let d2 = this.D2(p,x,y,z);
      value = old == 1 ? (d2 >= 2025.0 ? 1 : 0) : (d2 > 3025.0 ? 1 : 0);
    }
    this.Set(q,far,value);
  }
  // PA5: acquire the existing H10 prefabs before approach, never near their
  // reconstructed collision. Node placements across all five native sectors
  // lie near z122.66..126.48; 75m vertical / 200m horizontal separation is
  // deliberately larger than their measured collision footprint. The original
  // tested corridor path stays unchanged. No new ownership facts are invented.
  private func H10OffsiteReady(q: ref<QuestsSystem>, p: Vector4) -> Bool {
    if !IsDefined(q) || q.GetFact(n"PTFRPA2_Teleported") != 1 ||
       q.GetFact(n"PTFRPA2_ControlReady") != 1 || q.GetFact(n"PTFRPA2_Fault") != 0 { return false; }
    // Comparisons reject NaN/infinite or uninitialized out-of-world positions.
    if !(p.X > -100000.0 && p.X < 100000.0 && p.Y > -100000.0 && p.Y < 100000.0 &&
         p.Z > -10000.0 && p.Z < 10000.0) { return false; }
    let dx = p.X+1382.02319; let dy = p.Y-1272.61865;
    return dx*dx+dy*dy >= 40000.0 || AbsF(p.Z-124.0) >= 75.0;
  }
  private func H10LayerReady(q: ref<QuestsSystem>, claimed: CName, entered: CName, hold: CName) -> Bool {
    return IsDefined(q) && q.GetFact(claimed) == 1 && q.GetFact(entered) == 1 && q.GetFact(hold) == 0;
  }
  // Positive native saved acknowledgements, not rendered-geometry proof.
  public func H10GeometryReady() -> Bool {
    let q = GameInstance.GetQuestsSystem(this.GetGameInstance());
    return this.H10LayerReady(q,n"PTFRB0H10_Claimed",n"PTFRB0H10_OwnerEntered",n"PTFRB0H10_Hold") &&
      this.H10LayerReady(q,n"PTFRB0H10L_Claimed",n"PTFRB0H10L_OwnerEntered",n"PTFRB0H10L_Hold") &&
      this.H10LayerReady(q,n"PTFRB0H10A_E_Claimed",n"PTFRB0H10A_E_OwnerEntered",n"PTFRB0H10A_E_Hold") &&
      this.H10LayerReady(q,n"PTFRB0H10A_B_Claimed",n"PTFRB0H10A_B_OwnerEntered",n"PTFRB0H10A_B_Hold") &&
      this.H10LayerReady(q,n"PTFRB0H10A_W_Claimed",n"PTFRB0H10A_W_OwnerEntered",n"PTFRB0H10A_W_Hold");
  }
  private func H10LayerStatus(q: ref<QuestsSystem>, prefix: String) -> String {
    return prefix + "=" + ToString(q.GetFact(StringToName(prefix+"_Ready"))) + "/" +
      ToString(q.GetFact(StringToName(prefix+"_Request"))) + "/" +
      ToString(q.GetFact(StringToName(prefix+"_Claimed"))) + "/" +
      ToString(q.GetFact(StringToName(prefix+"_OwnerEntered"))) + "/" +
      ToString(q.GetFact(StringToName(prefix+"_Hold"))) + "/" +
      ToString(q.GetFact(StringToName(prefix+"_Rejected")));
  }
  public func H10Status() -> String {
    let game = this.GetGameInstance();
    let q = GameInstance.GetQuestsSystem(game);
    if !IsDefined(q) { return "H10 PA5: quest system unavailable."; }
    let player = GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
    let location = "player unavailable";
    if IsDefined(player) {
      let p = player.GetWorldPosition();
      location = "offsite=" + ToString(this.H10OffsiteReady(q,p)) + " xyz=" +
        ToString(p.X) + "," + ToString(p.Y) + "," + ToString(p.Z);
    }
    return "H10 PA5: geometryAcknowledged=" + ToString(this.H10GeometryReady()) +
      " baselineReady/suspended=" + ToString(q.GetFact(n"PTFRBASE_Ready")) + "/" +
      ToString(q.GetFact(n"PTFRBASE_Suspended")) + " " + location +
      " | Ready/Request/Claimed/Entered/Hold/Rejected " +
      this.H10LayerStatus(q,"PTFRB0H10") + " " + this.H10LayerStatus(q,"PTFRB0H10L") + " " +
      this.H10LayerStatus(q,"PTFRB0H10A_E") + " " + this.H10LayerStatus(q,"PTFRB0H10A_B") + " " +
      this.H10LayerStatus(q,"PTFRB0H10A_W") +
      " | actions Ready/Enabled/Active/Interrupted=" + ToString(q.GetFact(n"PTFRB0H10P_Ready")) + "/" +
      ToString(q.GetFact(n"PTFRB0H10P_Enabled")) + "/" + ToString(q.GetFact(n"PTFRB0H10P_Active")) + "/" +
      ToString(q.GetFact(n"PTFRB0H10P_Interrupted")) + " apartment/interiorOwner=" +
      ToString(q.GetFact(n"apartment_on")) + "/" + ToString(q.GetFact(n"interior_manager_on")) +
      " | Native owner acknowledgements are not rendered-geometry proof; public building and purchase rules are separate.";
  }
  private func Startup(q: ref<QuestsSystem>, player: ref<PlayerPuppet>, p: Vector4) -> Void {
    if q.GetFact(n"PTFRBASE_Suspended") != 0 { return; }
    let game = this.GetGameInstance();
    let scenes = GameInstance.GetSceneSystem(game).GetScriptInterface();
    let workspots = GameInstance.GetWorkspotSystem(game);
    if !IsDefined(scenes) || !IsDefined(workspots) { return; }
    this.safetyReads += 1;
    if player.IsInCombat() || scenes.IsEntityInScene(player.GetEntityID()) || workspots.IsActorInWorkspot(player) { return; }
    let mounted = GameInstance.GetMountingFacility(game).GetMountingInfoSingleWithObjects(player);
    if EntityID.IsDefined(mounted.parentId) { return; }
    let board = player.GetPlayerStateMachineBlackboard();
    if !IsDefined(board) { return; }
    let high = board.GetInt(GetAllBlackboardDefs().PlayerStateMachine.HighLevel);
    let tier = board.GetInt(GetAllBlackboardDefs().PlayerStateMachine.SceneTier);
    if (high != 1 && high != 2) || (tier != 1 && tier != 2) { return; }
    if GameInstance.GetQuestsContentSystem(game).IsTokensActivationBlocked() { return; }
    let saveLocks: array<gameSaveLock>;
    if GameInstance.IsSavingLocked(game,saveLocks) { return; }
    // Only perform the pre-tested geometry acquisition from the supported H10
    // corridor. Never rebuild a floor beneath V or reset an already claimed owner.
    let dx = p.X+1382.02319; let dy = p.Y-1272.61865;
    let corridor = high == 1 && tier == 1 && dx*dx+dy*dy <= 3600.0 && AbsF(p.Z-122.869896) < 5.0
      && (AbsF(dx) > 8.04180908 || AbsF(dy) > 8.04180908);
    let h10Geometry = corridor || (high == 1 && tier == 1 && this.H10OffsiteReady(q,p));
    let h10 = this.D2(p,-1383.84473,1276.34424,124.820267) <= 400.0;
    let coyoteOutside = this.D2(p,-1244.82678,-984.757996,12.0170002) > 64.0;
    // PTFRB0NIDG_auto
    if q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
       q.GetFact(n"PTFRP0_DR13") == 1 &&
       q.GetFact(n"q307_active") == 0 &&
       q.GetFact(n"q307_done") == 1 &&
       q.GetFact(n"q307_finished") == 1 &&
       q.GetFact(n"q307_2079") == 1 &&
       q.GetFact(n"q307_main_game_killed") == 1 &&
       q.GetFact(n"q305_johnny_scene_active") == 0 &&
       q.GetFact(n"q115_point_of_no_return") == 0 &&
       q.GetFact(n"q000_done") == 1 &&
       q.GetFact(n"wat_nid_gunsmith_01_default_on") == 1 &&
       q.GetFact(n"PTFRB0NIDG_Ready") == 1 &&
       q.GetFact(n"PTFRB0NIDG_Enabled") == 0 &&
       q.GetFact(n"PTFRB0NIDG_Near") == 0 &&
       q.GetFact(n"PTFRB0NIDG_Far") == 0 &&
       q.GetFact(n"PTFRB0NIDG_Excluded") == 0 {
      this.Set(q,n"PTFRB0NIDG_Enabled",1);
    }
    // PTFRB0NIDF_auto
    if q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
       q.GetFact(n"PTFRP0_DR13") == 1 &&
       q.GetFact(n"q307_active") == 0 &&
       q.GetFact(n"q307_done") == 1 &&
       q.GetFact(n"q307_finished") == 1 &&
       q.GetFact(n"q307_2079") == 1 &&
       q.GetFact(n"q307_main_game_killed") == 1 &&
       q.GetFact(n"q305_johnny_scene_active") == 0 &&
       q.GetFact(n"q115_point_of_no_return") == 0 &&
       q.GetFact(n"q000_done") == 1 &&
       q.GetFact(n"wat_nid_foodshop_01_default_on") == 1 &&
       q.GetFact(n"PTFRB0NIDF_Ready") == 1 &&
       q.GetFact(n"PTFRB0NIDF_Enabled") == 0 &&
       q.GetFact(n"PTFRB0NIDF_Near") == 0 &&
       q.GetFact(n"PTFRB0NIDF_Far") == 0 &&
       q.GetFact(n"PTFRB0NIDF_Excluded") == 0 {
      this.Set(q,n"PTFRB0NIDF_Enabled",1);
    }
    // PTFRB0NIDM_auto
    if q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
       q.GetFact(n"PTFRP0_DR13") == 1 &&
       q.GetFact(n"q307_active") == 0 &&
       q.GetFact(n"q307_done") == 1 &&
       q.GetFact(n"q307_finished") == 1 &&
       q.GetFact(n"q307_2079") == 1 &&
       q.GetFact(n"q307_main_game_killed") == 1 &&
       q.GetFact(n"q305_johnny_scene_active") == 0 &&
       q.GetFact(n"q115_point_of_no_return") == 0 &&
       q.GetFact(n"q000_done") == 1 &&
       q.GetFact(n"wat_nid_medicstore_02_default_on") == 1 &&
       q.GetFact(n"PTFRB0NIDM_Ready") == 1 &&
       q.GetFact(n"PTFRB0NIDM_Enabled") == 0 &&
       q.GetFact(n"PTFRB0NIDM_Near") == 0 &&
       q.GetFact(n"PTFRB0NIDM_Far") == 0 &&
       q.GetFact(n"PTFRB0NIDM_Excluded") == 0 {
      this.Set(q,n"PTFRB0NIDM_Enabled",1);
    }
    // PTFRB0LCHV_auto
    if q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
       q.GetFact(n"PTFRP0_DR13") == 1 &&
       q.GetFact(n"q307_active") == 0 &&
       q.GetFact(n"q307_done") == 1 &&
       q.GetFact(n"q307_finished") == 1 &&
       q.GetFact(n"q307_2079") == 1 &&
       q.GetFact(n"q307_main_game_killed") == 1 &&
       q.GetFact(n"q305_johnny_scene_active") == 0 &&
       q.GetFact(n"q115_point_of_no_return") == 0 &&
       q.GetFact(n"q000_done") == 1 &&
       q.GetFact(n"wat_lch_clothingshop_01_default_on") == 1 &&
       q.GetFact(n"PTFRB0LCHV_Ready") == 1 &&
       q.GetFact(n"PTFRB0LCHV_Enabled") == 0 &&
       q.GetFact(n"PTFRB0LCHV_Near") == 0 &&
       q.GetFact(n"PTFRB0LCHV_Far") == 0 &&
       q.GetFact(n"PTFRB0LCHV_Excluded") == 0 {
      this.Set(q,n"PTFRB0LCHV_Enabled",1);
    }
    // PTFRB0SE5J_auto
    if q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
       q.GetFact(n"PTFRP0_DR13") == 1 &&
       q.GetFact(n"q307_active") == 0 &&
       q.GetFact(n"q307_done") == 1 &&
       q.GetFact(n"q307_finished") == 1 &&
       q.GetFact(n"q307_2079") == 1 &&
       q.GetFact(n"q307_main_game_killed") == 1 &&
       q.GetFact(n"q305_johnny_scene_active") == 0 &&
       q.GetFact(n"q115_point_of_no_return") == 0 &&
       q.GetFact(n"q000_done") == 1 &&
       q.GetFact(n"bls_ina_se5_junkshop_01_default_on") == 1 &&
       q.GetFact(n"PTFRB0SE5J_Ready") == 1 &&
       q.GetFact(n"PTFRB0SE5J_Enabled") == 0 &&
       q.GetFact(n"PTFRB0SE5J_Near") == 0 &&
       q.GetFact(n"PTFRB0SE5J_Far") == 0 &&
       q.GetFact(n"PTFRB0SE5J_Excluded") == 0 {
      this.Set(q,n"PTFRB0SE5J_Enabled",1);
    }
    // PTFRB0SE5M_auto
    if q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
       q.GetFact(n"PTFRP0_DR13") == 1 &&
       q.GetFact(n"q307_active") == 0 &&
       q.GetFact(n"q307_done") == 1 &&
       q.GetFact(n"q307_finished") == 1 &&
       q.GetFact(n"q307_2079") == 1 &&
       q.GetFact(n"q307_main_game_killed") == 1 &&
       q.GetFact(n"q305_johnny_scene_active") == 0 &&
       q.GetFact(n"q115_point_of_no_return") == 0 &&
       q.GetFact(n"q000_done") == 1 &&
       q.GetFact(n"bls_ina_se5_melee_01_default_on") == 1 &&
       q.GetFact(n"PTFRB0SE5M_Ready") == 1 &&
       q.GetFact(n"PTFRB0SE5M_Enabled") == 0 &&
       q.GetFact(n"PTFRB0SE5M_Near") == 0 &&
       q.GetFact(n"PTFRB0SE5M_Far") == 0 &&
       q.GetFact(n"PTFRB0SE5M_Excluded") == 0 {
      this.Set(q,n"PTFRB0SE5M_Enabled",1);
    }
    // PTFRB0RIPDTN_auto
    if q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
       q.GetFact(n"PTFRP0_DR13") == 1 &&
       q.GetFact(n"q307_active") == 0 &&
       q.GetFact(n"q307_done") == 1 &&
       q.GetFact(n"q307_finished") == 1 &&
       q.GetFact(n"q307_2079") == 1 &&
       q.GetFact(n"q307_main_game_killed") == 1 &&
       q.GetFact(n"q305_johnny_scene_active") == 0 &&
       q.GetFact(n"q115_point_of_no_return") == 0 &&
       q.GetFact(n"q000_done") == 1 &&
       q.GetFact(n"cct_dtn_ripdoc_01_default_on") == 1 &&
       q.GetFact(n"PTFRB0RIPDTN_Ready") == 1 &&
       q.GetFact(n"PTFRB0RIPDTN_Enabled") == 0 &&
       q.GetFact(n"PTFRB0RIPDTN_Near") == 0 &&
       q.GetFact(n"PTFRB0RIPDTN_Far") == 0 &&
       q.GetFact(n"PTFRB0RIPDTN_Excluded") == 0 {
      this.Set(q,n"PTFRB0RIPDTN_Enabled",1);
    }
    // PTFRB0NETCVI_auto
    if q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
       q.GetFact(n"PTFRP0_DR13") == 1 &&
       q.GetFact(n"q307_active") == 0 &&
       q.GetFact(n"q307_done") == 1 &&
       q.GetFact(n"q307_finished") == 1 &&
       q.GetFact(n"q307_2079") == 1 &&
       q.GetFact(n"q307_main_game_killed") == 1 &&
       q.GetFact(n"q305_johnny_scene_active") == 0 &&
       q.GetFact(n"q115_point_of_no_return") == 0 &&
       q.GetFact(n"q000_done") == 1 &&
       q.GetFact(n"pac_cvi_techstore_01") == 1 &&
       q.GetFact(n"PTFRB0NETCVI_Ready") == 1 &&
       q.GetFact(n"PTFRB0NETCVI_Enabled") == 0 &&
       q.GetFact(n"PTFRB0NETCVI_Near") == 0 &&
       q.GetFact(n"PTFRB0NETCVI_Far") == 0 &&
       q.GetFact(n"PTFRB0NETCVI_Excluded") == 0 {
      this.Set(q,n"PTFRB0NETCVI_Enabled",1);
    }
    // PTFRB0RIPWWD_auto
    if q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
       q.GetFact(n"PTFRP0_DR13") == 1 &&
       q.GetFact(n"q307_active") == 0 &&
       q.GetFact(n"q307_done") == 1 &&
       q.GetFact(n"q307_finished") == 1 &&
       q.GetFact(n"q307_2079") == 1 &&
       q.GetFact(n"q307_main_game_killed") == 1 &&
       q.GetFact(n"q305_johnny_scene_active") == 0 &&
       q.GetFact(n"q115_point_of_no_return") == 0 &&
       q.GetFact(n"q000_done") == 1 &&
       q.GetFact(n"pac_wwd_ripdoc_01_default_on") == 1 &&
       q.GetFact(n"PTFRB0RIPWWD_Ready") == 1 &&
       q.GetFact(n"PTFRB0RIPWWD_Enabled") == 0 &&
       q.GetFact(n"PTFRB0RIPWWD_Near") == 0 &&
       q.GetFact(n"PTFRB0RIPWWD_Far") == 0 &&
       q.GetFact(n"PTFRB0RIPWWD_Excluded") == 0 {
      this.Set(q,n"PTFRB0RIPWWD_Enabled",1);
    }
    // PTFRB0RIPARR_auto
    if q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
       q.GetFact(n"PTFRP0_DR13") == 1 &&
       q.GetFact(n"q307_active") == 0 &&
       q.GetFact(n"q307_done") == 1 &&
       q.GetFact(n"q307_finished") == 1 &&
       q.GetFact(n"q307_2079") == 1 &&
       q.GetFact(n"q307_main_game_killed") == 1 &&
       q.GetFact(n"q305_johnny_scene_active") == 0 &&
       q.GetFact(n"q115_point_of_no_return") == 0 &&
       q.GetFact(n"q000_done") == 1 &&
       q.GetFact(n"std_arr_ripperdoc_01_default_on") == 1 &&
       q.GetFact(n"PTFRB0RIPARR_Ready") == 1 &&
       q.GetFact(n"PTFRB0RIPARR_Enabled") == 0 &&
       q.GetFact(n"PTFRB0RIPARR_Near") == 0 &&
       q.GetFact(n"PTFRB0RIPARR_Far") == 0 &&
       q.GetFact(n"PTFRB0RIPARR_Excluded") == 0 {
      this.Set(q,n"PTFRB0RIPARR_Enabled",1);
    }
    // PTFRB0RIPRCR_auto
    if q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
       q.GetFact(n"PTFRP0_DR13") == 1 &&
       q.GetFact(n"q307_active") == 0 &&
       q.GetFact(n"q307_done") == 1 &&
       q.GetFact(n"q307_finished") == 1 &&
       q.GetFact(n"q307_2079") == 1 &&
       q.GetFact(n"q307_main_game_killed") == 1 &&
       q.GetFact(n"q305_johnny_scene_active") == 0 &&
       q.GetFact(n"q115_point_of_no_return") == 0 &&
       q.GetFact(n"q000_done") == 1 &&
       q.GetFact(n"std_rcr_ripperdoc_01_default_on") == 1 &&
       q.GetFact(n"PTFRB0RIPRCR_Ready") == 1 &&
       q.GetFact(n"PTFRB0RIPRCR_Enabled") == 0 &&
       q.GetFact(n"PTFRB0RIPRCR_Near") == 0 &&
       q.GetFact(n"PTFRB0RIPRCR_Far") == 0 &&
       q.GetFact(n"PTFRB0RIPRCR_Excluded") == 0 {
      this.Set(q,n"PTFRB0RIPRCR_Enabled",1);
    }
    // PTFRB0RIPHIL_auto
    if q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
       q.GetFact(n"PTFRP0_DR13") == 1 &&
       q.GetFact(n"q307_active") == 0 &&
       q.GetFact(n"q307_done") == 1 &&
       q.GetFact(n"q307_finished") == 1 &&
       q.GetFact(n"q307_2079") == 1 &&
       q.GetFact(n"q307_main_game_killed") == 1 &&
       q.GetFact(n"q305_johnny_scene_active") == 0 &&
       q.GetFact(n"q115_point_of_no_return") == 0 &&
       q.GetFact(n"q000_done") == 1 &&
       q.GetFact(n"wbr_hil_ripdoc_01_default_on") == 1 &&
       q.GetFact(n"PTFRB0RIPHIL_Ready") == 1 &&
       q.GetFact(n"PTFRB0RIPHIL_Enabled") == 0 &&
       q.GetFact(n"PTFRB0RIPHIL_Near") == 0 &&
       q.GetFact(n"PTFRB0RIPHIL_Far") == 0 &&
       q.GetFact(n"PTFRB0RIPHIL_Excluded") == 0 {
      this.Set(q,n"PTFRB0RIPHIL_Enabled",1);
    }
    // PTFRB0RIPJPN_auto
    if q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
       q.GetFact(n"PTFRP0_DR13") == 1 &&
       q.GetFact(n"q307_active") == 0 &&
       q.GetFact(n"q307_done") == 1 &&
       q.GetFact(n"q307_finished") == 1 &&
       q.GetFact(n"q307_2079") == 1 &&
       q.GetFact(n"q307_main_game_killed") == 1 &&
       q.GetFact(n"q305_johnny_scene_active") == 0 &&
       q.GetFact(n"q115_point_of_no_return") == 0 &&
       q.GetFact(n"q000_done") == 1 &&
       q.GetFact(n"wbr_jpn_ripdoc_01_default_on") == 1 &&
       q.GetFact(n"PTFRB0RIPJPN_Ready") == 1 &&
       q.GetFact(n"PTFRB0RIPJPN_Enabled") == 0 &&
       q.GetFact(n"PTFRB0RIPJPN_Near") == 0 &&
       q.GetFact(n"PTFRB0RIPJPN_Far") == 0 &&
       q.GetFact(n"PTFRB0RIPJPN_Excluded") == 0 {
      this.Set(q,n"PTFRB0RIPJPN_Enabled",1);
    }
    // PTFRB0JPNNET1_auto
    if q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
       q.GetFact(n"PTFRP0_DR13") == 1 &&
       q.GetFact(n"q307_active") == 0 &&
       q.GetFact(n"q307_done") == 1 &&
       q.GetFact(n"q307_finished") == 1 &&
       q.GetFact(n"q307_2079") == 1 &&
       q.GetFact(n"q307_main_game_killed") == 1 &&
       q.GetFact(n"q305_johnny_scene_active") == 0 &&
       q.GetFact(n"q115_point_of_no_return") == 0 &&
       q.GetFact(n"q000_done") == 1 &&
       q.GetFact(n"wbr_jpn_netrun_01_default_on") == 1 &&
       q.GetFact(n"PTFRB0JPNNET1_Ready") == 1 &&
       q.GetFact(n"PTFRB0JPNNET1_Enabled") == 0 &&
       q.GetFact(n"PTFRB0JPNNET1_Near") == 0 &&
       q.GetFact(n"PTFRB0JPNNET1_Far") == 0 &&
       q.GetFact(n"PTFRB0JPNNET1_Excluded") == 0 {
      this.Set(q,n"PTFRB0JPNNET1_Enabled",1);
    }
    // Wilson
    if q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
       q.GetFact(n"PTFRP0_DR13") == 1 &&
       q.GetFact(n"q307_active") == 0 &&
       q.GetFact(n"q307_done") == 1 &&
       q.GetFact(n"q307_finished") == 1 &&
       q.GetFact(n"q307_2079") == 1 &&
       q.GetFact(n"q307_main_game_killed") == 1 &&
       q.GetFact(n"q305_johnny_scene_active") == 0 &&
       q.GetFact(n"q115_point_of_no_return") == 0 &&
       q.GetFact(n"wat_lch_gunsmith_01_default_on") == 1 &&
       q.GetFact(n"q001_spawn_wilson_attention") == 0 &&
       q.GetFact(n"q101_spawn_wilson_attention") == 0 &&
       q.GetFact(n"mq011_active") == 0 &&
       q.GetFact(n"PTFRB0WV_Ready") == 1 &&
       q.GetFact(n"PTFRB0WV_Enabled") == 0 &&
       q.GetFact(n"PTFRB0WV_Near") == 0 &&
       q.GetFact(n"PTFRB0WV_SpawnActionOut") == 0 &&
       q.GetFact(n"PTFRB0WV_ActorDistanceGate") == 0 &&
       q.GetFact(n"PTFRB0WV_Excluded") == 0 {
      this.Set(q,n"PTFRB0WV_Enabled",1);
    }
    // PTFRB0H10_geometry
    if h10Geometry &&
       q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
       q.GetFact(n"PTFRP0_DR13") == 1 &&
       q.GetFact(n"q307_active") == 0 &&
       q.GetFact(n"q307_done") == 1 &&
       q.GetFact(n"q307_finished") == 1 &&
       q.GetFact(n"q307_2079") == 1 &&
       q.GetFact(n"q307_main_game_killed") == 1 &&
       q.GetFact(n"PTFRB0H10_Claimed") == 0 &&
       q.GetFact(n"PTFRB0H10_OwnerEntered") == 0 &&
       q.GetFact(n"PTFRB0H10_Hold") == 0 &&
       q.GetFact(n"PTFRB0H10_Ready") == 1 &&
       q.GetFact(n"PTFRB0H10_Request") == 0 &&
       q.GetFact(n"PTFRB0H10_Rejected") == 0 {
      this.Set(q,n"PTFRB0H10_Request",1);
    }
    // PTFRB0H10L_geometry
    if h10Geometry &&
       q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
       q.GetFact(n"PTFRP0_DR13") == 1 &&
       q.GetFact(n"q307_active") == 0 &&
       q.GetFact(n"q307_done") == 1 &&
       q.GetFact(n"q307_finished") == 1 &&
       q.GetFact(n"q307_2079") == 1 &&
       q.GetFact(n"q307_main_game_killed") == 1 &&
       q.GetFact(n"PTFRB0H10_Claimed") == 1 &&
       q.GetFact(n"PTFRB0H10_OwnerEntered") == 1 &&
       q.GetFact(n"PTFRB0H10L_Claimed") == 0 &&
       q.GetFact(n"PTFRB0H10L_OwnerEntered") == 0 &&
       q.GetFact(n"PTFRB0H10L_Hold") == 0 &&
       q.GetFact(n"PTFRB0H10L_Ready") == 1 &&
       q.GetFact(n"PTFRB0H10L_Request") == 0 &&
       q.GetFact(n"PTFRB0H10L_Rejected") == 0 {
      this.Set(q,n"PTFRB0H10L_Request",1);
    }
    // PTFRB0H10A_E_geometry
    if h10Geometry &&
       q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
       q.GetFact(n"PTFRP0_DR13") == 1 &&
       q.GetFact(n"q307_active") == 0 &&
       q.GetFact(n"q307_done") == 1 &&
       q.GetFact(n"q307_finished") == 1 &&
       q.GetFact(n"q307_2079") == 1 &&
       q.GetFact(n"q307_main_game_killed") == 1 &&
       q.GetFact(n"PTFRB0H10_Claimed") == 1 &&
       q.GetFact(n"PTFRB0H10_OwnerEntered") == 1 &&
       q.GetFact(n"PTFRB0H10L_Claimed") == 1 &&
       q.GetFact(n"PTFRB0H10L_OwnerEntered") == 1 &&
       q.GetFact(n"PTFRB0H10A_E_Claimed") == 0 &&
       q.GetFact(n"PTFRB0H10A_E_OwnerEntered") == 0 &&
       q.GetFact(n"PTFRB0H10A_E_Hold") == 0 &&
       q.GetFact(n"PTFRB0H10A_E_Ready") == 1 &&
       q.GetFact(n"PTFRB0H10A_E_Request") == 0 &&
       q.GetFact(n"PTFRB0H10A_E_Rejected") == 0 {
      this.Set(q,n"PTFRB0H10A_E_Request",1);
    }
    // PTFRB0H10A_B_geometry
    if h10Geometry &&
       q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
       q.GetFact(n"PTFRP0_DR13") == 1 &&
       q.GetFact(n"q307_active") == 0 &&
       q.GetFact(n"q307_done") == 1 &&
       q.GetFact(n"q307_finished") == 1 &&
       q.GetFact(n"q307_2079") == 1 &&
       q.GetFact(n"q307_main_game_killed") == 1 &&
       q.GetFact(n"PTFRB0H10_Claimed") == 1 &&
       q.GetFact(n"PTFRB0H10_OwnerEntered") == 1 &&
       q.GetFact(n"PTFRB0H10L_Claimed") == 1 &&
       q.GetFact(n"PTFRB0H10L_OwnerEntered") == 1 &&
       q.GetFact(n"PTFRB0H10A_E_Claimed") == 1 &&
       q.GetFact(n"PTFRB0H10A_E_OwnerEntered") == 1 &&
       q.GetFact(n"PTFRB0H10A_B_Claimed") == 0 &&
       q.GetFact(n"PTFRB0H10A_B_OwnerEntered") == 0 &&
       q.GetFact(n"PTFRB0H10A_B_Hold") == 0 &&
       q.GetFact(n"PTFRB0H10A_B_Ready") == 1 &&
       q.GetFact(n"PTFRB0H10A_B_Request") == 0 &&
       q.GetFact(n"PTFRB0H10A_B_Rejected") == 0 {
      this.Set(q,n"PTFRB0H10A_B_Request",1);
    }
    // PTFRB0H10A_W_geometry
    if h10Geometry &&
       q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
       q.GetFact(n"PTFRP0_DR13") == 1 &&
       q.GetFact(n"q307_active") == 0 &&
       q.GetFact(n"q307_done") == 1 &&
       q.GetFact(n"q307_finished") == 1 &&
       q.GetFact(n"q307_2079") == 1 &&
       q.GetFact(n"q307_main_game_killed") == 1 &&
       q.GetFact(n"PTFRB0H10_Claimed") == 1 &&
       q.GetFact(n"PTFRB0H10_OwnerEntered") == 1 &&
       q.GetFact(n"PTFRB0H10L_Claimed") == 1 &&
       q.GetFact(n"PTFRB0H10L_OwnerEntered") == 1 &&
       q.GetFact(n"PTFRB0H10A_B_Claimed") == 1 &&
       q.GetFact(n"PTFRB0H10A_B_OwnerEntered") == 1 &&
       q.GetFact(n"PTFRB0H10A_W_Claimed") == 0 &&
       q.GetFact(n"PTFRB0H10A_W_OwnerEntered") == 0 &&
       q.GetFact(n"PTFRB0H10A_W_Hold") == 0 &&
       q.GetFact(n"PTFRB0H10A_W_Ready") == 1 &&
       q.GetFact(n"PTFRB0H10A_W_Request") == 0 &&
       q.GetFact(n"PTFRB0H10A_W_Rejected") == 0 {
      this.Set(q,n"PTFRB0H10A_W_Request",1);
    }
    // H10 interactions
    if h10 &&
       q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
       q.GetFact(n"PTFRP0_DR13") == 1 &&
       q.GetFact(n"q307_active") == 0 &&
       q.GetFact(n"q307_done") == 1 &&
       q.GetFact(n"q307_finished") == 1 &&
       q.GetFact(n"q307_2079") == 1 &&
       q.GetFact(n"q307_main_game_killed") == 1 &&
       q.GetFact(n"q305_johnny_scene_active") == 0 &&
       q.GetFact(n"apartment_on") == 1 &&
       q.GetFact(n"interior_manager_on") == 0 &&
       q.GetFact(n"PTFRB0H10_Claimed") == 1 &&
       q.GetFact(n"PTFRB0H10_OwnerEntered") == 1 &&
       q.GetFact(n"PTFRB0H10L_Claimed") == 1 &&
       q.GetFact(n"PTFRB0H10L_OwnerEntered") == 1 &&
       q.GetFact(n"PTFRB0H10A_E_Claimed") == 1 &&
       q.GetFact(n"PTFRB0H10A_E_OwnerEntered") == 1 &&
       q.GetFact(n"PTFRB0H10A_B_Claimed") == 1 &&
       q.GetFact(n"PTFRB0H10A_B_OwnerEntered") == 1 &&
       q.GetFact(n"PTFRB0H10A_W_Claimed") == 1 &&
       q.GetFact(n"PTFRB0H10A_W_OwnerEntered") == 1 &&
       q.GetFact(n"PTFRB0H10M_Active") == 0 &&
       q.GetFact(n"PTFRB0H10I_M_Active") == 0 &&
       q.GetFact(n"PTFRB0H10I_H_Active") == 0 &&
       q.GetFact(n"PTFRB0H10I_B_Active") == 0 &&
       q.GetFact(n"PTFRB0H10I_S_Active") == 0 &&
       q.GetFact(n"PTFRB0H10I_W_Active") == 0 &&
       q.GetFact(n"PTFRB0H10P_Enabled") == 0 &&
       q.GetFact(n"PTFRB0H10P_Interrupted") == 0 &&
       q.GetFact(n"PTFRB0H10P_Ready") == 1 &&
       q.GetFact(n"PTFRB0H10P_Active") == 0 {
      this.Set(q,n"PTFRB0H10P_Enabled",1);
    }
    // Coyote public mirror
    if coyoteOutside &&
       q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
       q.GetFact(n"PTFRP0_DR13") == 1 &&
       q.GetFact(n"q307_active") == 0 &&
       q.GetFact(n"q307_done") == 1 &&
       q.GetFact(n"q307_finished") == 1 &&
       q.GetFact(n"q307_2079") == 1 &&
       q.GetFact(n"q307_main_game_killed") == 1 &&
       q.GetFact(n"q305_johnny_scene_active") == 0 &&
       q.GetFact(n"q115_point_of_no_return") == 0 &&
       q.GetFact(n"q000_done") == 1 &&
       q.GetFact(n"mirror_interaction_disabled") == 0 &&
       q.GetFact(n"PTFRCM1_Requested") == 0 &&
       q.GetFact(n"PTFRCM2_Boot") == 1 &&
       q.GetFact(n"PTFRCM2_Requested") == 0 &&
       q.GetFact(n"PTFRCM2_Active") == 0 &&
       q.GetFact(n"PTFRCM2_Interrupted") == 0 {
      this.Set(q,n"PTFRCM2_Requested",1);
    }
    // Native Afterlife owner can bootstrap an unarmed completed-Tower save as
    // well as switch a saved v5/v6 fallback. Never request both scene owners.
    if q.GetFact(n"mirror_interaction_disabled") == 0 && q.GetFact(n"PTFRALMA1_Requested") == 0 && q.GetFact(n"PTFRALMA2_Boot") == 1 &&
       q.GetFact(n"PTFRALMA2_Requested") == 0 && q.GetFact(n"PTFRALMA2_Active") == 0 &&
       q.GetFact(n"PTFRALMA2_Interrupted") == 0 && q.GetFact(n"PTFRB0ALM_Active") == 0 &&
       q.GetFact(n"PTFRB0ALM_Near") == 0 && q.GetFact(n"PTFRB0ALM_Interrupted") == 0 &&
       (q.GetFact(n"PTFRB0ALM_Enabled") == 0 || q.GetFact(n"PTFRB0ALM_Enabled") == 1) &&
       this.D2(p,-1438.97388,1039.22314,16.92) > 49.0 {
      this.Set(q,n"PTFRB0ALM_Enabled",0);
      if q.GetFact(n"PTFRB0ALM_Enabled") == 0 { this.Set(q,n"PTFRALMA2_Requested",1); }
    }
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    this.polls += 1;
    let game = this.GetGameInstance();
    let q = GameInstance.GetQuestsSystem(game);
    if !IsDefined(q) { this.Schedule(epoch,1.0); return; }
    let eligible = true;
    if q.GetFact(n"PostTowerFreeRoamActive") != 1 { eligible = false; }
    if q.GetFact(n"PTFRP0_DR13") != 1 { eligible = false; }
    if q.GetFact(n"q307_active") != 0 { eligible = false; }
    if q.GetFact(n"q307_done") != 1 { eligible = false; }
    if q.GetFact(n"q307_finished") != 1 { eligible = false; }
    if q.GetFact(n"q307_2079") != 1 { eligible = false; }
    if q.GetFact(n"q307_main_game_killed") != 1 { eligible = false; }
    if q.GetFact(n"q305_johnny_scene_active") != 0 { eligible = false; }
    if q.GetFact(n"q115_point_of_no_return") != 0 { eligible = false; }
    if q.GetFact(n"q000_done") != 1 { eligible = false; }
    // Keep watching across the real ending; never force completion or stop
    // permanently just because this session attached before the credits.
    if !eligible { this.Schedule(epoch,1.0); return; }
    let players = GameInstance.GetPlayerSystem(game);
    if !IsDefined(players) { this.Schedule(epoch,1.0); return; }
    let player = players.GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(player) { this.Schedule(epoch,1.0); return; }
    let p = player.GetWorldPosition();
    this.Set(q,n"PTFRBASE_Ready",1);
    if this.startupTicks <= 0 {
      this.Startup(q,player,p); this.startupTicks = 10;
    }
    this.startupTicks -= 1;
    this.Far(q,p,n"PTFRB0NIDG_Enabled", n"PTFRB0NIDG_Near", n"PTFRB0NIDG_Far",n"wat_nid_gunsmith_01_default_on",-1891.043210000,2730.455080000,7.454570000);
    this.Far(q,p,n"PTFRB0NIDF_Enabled", n"PTFRB0NIDF_Near", n"PTFRB0NIDF_Far",n"wat_nid_foodshop_01_default_on",-1914.454350000,2739.485350000,10.898680000);
    this.Far(q,p,n"PTFRB0NIDM_Enabled", n"PTFRB0NIDM_Near", n"PTFRB0NIDM_Far",n"wat_nid_medicstore_02_default_on",-1933.200810000,2744.163570000,10.450100000);
    this.Far(q,p,n"PTFRB0LCHV_Enabled", n"PTFRB0LCHV_Near", n"PTFRB0LCHV_Far",n"wat_lch_clothingshop_01_default_on",-1525.485600000,1702.873290000,18.320000000);
    this.Far(q,p,n"PTFRB0SE5J_Enabled", n"PTFRB0SE5J_Near", n"PTFRB0SE5J_Far",n"bls_ina_se5_junkshop_01_default_on",-986.821716000,-4418.158690000,64.313644400);
    this.Far(q,p,n"PTFRB0SE5M_Enabled", n"PTFRB0SE5M_Near", n"PTFRB0SE5M_Far",n"bls_ina_se5_melee_01_default_on",138.247818000,-4671.498050000,55.078262300);
    this.Far(q,p,n"PTFRB0RIPDTN_Enabled", n"PTFRB0RIPDTN_Near", n"PTFRB0RIPDTN_Far",n"cct_dtn_ripdoc_01_default_on",-2412.155030000,395.014343000,11.687105200);
    this.Far(q,p,n"PTFRB0NETREY_Enabled", n"PTFRB0NETREY_Near", n"PTFRB0NETREY_Far",n"hey_rey_netrunner_01_default_on",-854.184631000,-387.527466000,8.534561160);
    this.Far(q,p,n"PTFRB0NETCVI_Enabled", n"PTFRB0NETCVI_Near", n"PTFRB0NETCVI_Far",n"pac_cvi_techstore_01",-1908.163330000,-1924.152470000,49.309162100);
    this.Far(q,p,n"PTFRB0RIPWWD_Enabled", n"PTFRB0RIPWWD_Near", n"PTFRB0RIPWWD_Far",n"pac_wwd_ripdoc_01_default_on",-2606.360350000,-2501.317870000,17.860002500);
    this.Far(q,p,n"PTFRB0RIPARR_Enabled", n"PTFRB0RIPARR_Near", n"PTFRB0RIPARR_Far",n"std_arr_ripperdoc_01_default_on",-1066.001590000,-1270.503660000,11.456399000);
    this.Far(q,p,n"PTFRB0RIPRCR_Enabled", n"PTFRB0RIPRCR_Near", n"PTFRB0RIPRCR_Far",n"std_rcr_ripperdoc_01_default_on",585.669678000,-2180.274170000,42.390003200);
    this.Far(q,p,n"PTFRB0RIPHIL_Enabled", n"PTFRB0RIPHIL_Near", n"PTFRB0RIPHIL_Far",n"wbr_hil_ripdoc_01_default_on",-41.705440500,-53.523475600,7.183426380);
    this.Far(q,p,n"PTFRB0RIPJPN_Enabled", n"PTFRB0RIPJPN_Near", n"PTFRB0RIPJPN_Far",n"wbr_jpn_ripdoc_01_default_on",-707.342529000,868.738647000,11.816449200);
    this.Far(q,p,n"PTFRB0JPNNET1_Enabled", n"PTFRB0JPNNET1_Near", n"PTFRB0JPNNET1_Far",n"wbr_jpn_netrun_01_default_on",-354.645905000,1366.601440000,42.162101700);
    // Wilson's proved 80/84m Near driver, now independent of CET. Enabled and
    // native body markers are never cleared merely because a save loaded.
    if q.GetFact(n"PTFRB0WV_Enabled") == 1 {
      let allowed = true;
      if q.GetFact(n"PostTowerFreeRoamActive") != 1 { allowed = false; }
      if q.GetFact(n"PTFRP0_DR13") != 1 { allowed = false; }
      if q.GetFact(n"q307_active") != 0 { allowed = false; }
      if q.GetFact(n"q307_done") != 1 { allowed = false; }
      if q.GetFact(n"q307_finished") != 1 { allowed = false; }
      if q.GetFact(n"q307_2079") != 1 { allowed = false; }
      if q.GetFact(n"q307_main_game_killed") != 1 { allowed = false; }
      if q.GetFact(n"q305_johnny_scene_active") != 0 { allowed = false; }
      if q.GetFact(n"q115_point_of_no_return") != 0 { allowed = false; }
      if q.GetFact(n"wat_lch_gunsmith_01_default_on") != 1 { allowed = false; }
      if q.GetFact(n"q001_spawn_wilson_attention") != 0 { allowed = false; }
      if q.GetFact(n"q101_spawn_wilson_attention") != 0 { allowed = false; }
      if q.GetFact(n"mq011_active") != 0 { allowed = false; }
      let old = q.GetFact(n"PTFRB0WV_Near");
      let d2 = this.D2(p,-1450.37012,1318.43982,119.059998);
      let inside = allowed && (old == 1 ? d2 <= 7056.0 : d2 <= 6400.0);
      this.Set(q,n"PTFRB0WV_Near",inside ? 1 : 0);
    }
    this.Schedule(epoch,0.5);
  }
}
public class RestorationBaselineTick extends DelayCallback {
  private let driver: wref<RestorationBaseline>;
  private let epoch: Int32;
  public func Call() -> Void { if IsDefined(this.driver) { this.driver.Poll(this.epoch); } }
  public static func Create(driver: ref<RestorationBaseline>,epoch: Int32) -> ref<RestorationBaselineTick> {
    let c = new RestorationBaselineTick(); c.driver = driver; c.epoch = epoch; return c;
  }
}

