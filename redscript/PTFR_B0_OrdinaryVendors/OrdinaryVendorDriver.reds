module PTFR.B0OrdinaryVendors

// Generated site calls come from the audited cohort. Native owners retain
// their complete vanilla scenes and own spawning, entry and exit.
public class OrdinaryVendorDriver extends ScriptableSystem {
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
      delays.DelayCallback(OrdinaryVendorTick.Create(this, epoch), seconds, false);
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
    if this.ReadFact(q, n"PTFRB0OVB_Suspended") != 0 { return; }
    let pending = false;
    pending = this.AutoSite(q, n"PTFRB0OV01_Enabled", n"PTFRB0OV01_Ready", n"PTFRB0OV01_Excluded", n"PTFRB0OV01_Near", n"PTFRB0OV01_Far", n"bls_ina_se1_clothingshop_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV02_Enabled", n"PTFRB0OV02_Ready", n"PTFRB0OV02_Excluded", n"PTFRB0OV02_Near", n"PTFRB0OV02_Far", n"bls_ina_se1_foodshop_02_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV03_Enabled", n"PTFRB0OV03_Ready", n"PTFRB0OV03_Excluded", n"PTFRB0OV03_Near", n"PTFRB0OV03_Far", n"bls_ina_se1_medicstore_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV04_Enabled", n"PTFRB0OV04_Ready", n"PTFRB0OV04_Excluded", n"PTFRB0OV04_Near", n"PTFRB0OV04_Far", n"cct_dtn_medic_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV05_Enabled", n"PTFRB0OV05_Ready", n"PTFRB0OV05_Excluded", n"PTFRB0OV05_Near", n"PTFRB0OV05_Far", n"hey_gle_gunsmith_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV06_Enabled", n"PTFRB0OV06_Ready", n"PTFRB0OV06_Excluded", n"PTFRB0OV06_Near", n"PTFRB0OV06_Far", n"pac_cvi_clothingshop_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV07_Enabled", n"PTFRB0OV07_Ready", n"PTFRB0OV07_Excluded", n"PTFRB0OV07_Near", n"PTFRB0OV07_Far", n"pac_cvi_foodshop_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV08_Enabled", n"PTFRB0OV08_Ready", n"PTFRB0OV08_Excluded", n"PTFRB0OV08_Near", n"PTFRB0OV08_Far", n"pac_cvi_medicstore_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV09_Enabled", n"PTFRB0OV09_Ready", n"PTFRB0OV09_Excluded", n"PTFRB0OV09_Near", n"PTFRB0OV09_Far", n"std_arr_clothingshop_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV10_Enabled", n"PTFRB0OV10_Ready", n"PTFRB0OV10_Excluded", n"PTFRB0OV10_Near", n"PTFRB0OV10_Far", n"std_arr_foodshop_02_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV11_Enabled", n"PTFRB0OV11_Ready", n"PTFRB0OV11_Excluded", n"PTFRB0OV11_Near", n"PTFRB0OV11_Far", n"std_arr_gunsmith_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV12_Enabled", n"PTFRB0OV12_Ready", n"PTFRB0OV12_Excluded", n"PTFRB0OV12_Near", n"PTFRB0OV12_Far", n"std_arr_medicstore_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV13_Enabled", n"PTFRB0OV13_Ready", n"PTFRB0OV13_Excluded", n"PTFRB0OV13_Near", n"PTFRB0OV13_Far", n"std_rcr_foodshop_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV14_Enabled", n"PTFRB0OV14_Ready", n"PTFRB0OV14_Excluded", n"PTFRB0OV14_Near", n"PTFRB0OV14_Far", n"std_rcr_gunsmith_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV15_Enabled", n"PTFRB0OV15_Ready", n"PTFRB0OV15_Excluded", n"PTFRB0OV15_Near", n"PTFRB0OV15_Far", n"wat_kab_junkshop_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV16_Enabled", n"PTFRB0OV16_Ready", n"PTFRB0OV16_Excluded", n"PTFRB0OV16_Near", n"PTFRB0OV16_Far", n"wat_kab_clothingshop_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV17_Enabled", n"PTFRB0OV17_Ready", n"PTFRB0OV17_Excluded", n"PTFRB0OV17_Near", n"PTFRB0OV17_Far", n"wat_lch_medicstore_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV18_Enabled", n"PTFRB0OV18_Ready", n"PTFRB0OV18_Excluded", n"PTFRB0OV18_Near", n"PTFRB0OV18_Far", n"wat_nid_clothingshop_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV19_Enabled", n"PTFRB0OV19_Ready", n"PTFRB0OV19_Excluded", n"PTFRB0OV19_Near", n"PTFRB0OV19_Far", n"wat_nid_medicstore_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV20_Enabled", n"PTFRB0OV20_Ready", n"PTFRB0OV20_Excluded", n"PTFRB0OV20_Near", n"PTFRB0OV20_Far", n"wbr_hil_clothingshop_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV21_Enabled", n"PTFRB0OV21_Ready", n"PTFRB0OV21_Excluded", n"PTFRB0OV21_Near", n"PTFRB0OV21_Far", n"wbr_jpn_melee_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV22_Enabled", n"PTFRB0OV22_Ready", n"PTFRB0OV22_Excluded", n"PTFRB0OV22_Near", n"PTFRB0OV22_Far", n"wbr_jpn_food_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV23_Enabled", n"PTFRB0OV23_Ready", n"PTFRB0OV23_Excluded", n"PTFRB0OV23_Near", n"PTFRB0OV23_Far", n"wbr_jpn_food_02_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV24_Enabled", n"PTFRB0OV24_Ready", n"PTFRB0OV24_Excluded", n"PTFRB0OV24_Near", n"PTFRB0OV24_Far", n"wbr_jpn_food_03_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0OV25_Enabled", n"PTFRB0OV25_Ready", n"PTFRB0OV25_Excluded", n"PTFRB0OV25_Near", n"PTFRB0OV25_Far", n"wbr_jpn_food_04_default_on", false) || pending;
    if !pending { return; }
    // Expensive safety queries run once per activation attempt, not per shop
    // or departure tick. Original native eligibility is rechecked on entry.
    let game = this.GetGameInstance();
    let scene = GameInstance.GetSceneSystem(game).GetScriptInterface();
    let workspots = GameInstance.GetWorkspotSystem(game);
    if !IsDefined(scene) || !IsDefined(workspots) { return; }
    if player.IsInCombat() || scene.IsEntityInScene(player.GetEntityID()) ||
       workspots.IsActorInWorkspot(player) { return; }
    this.AutoSite(q, n"PTFRB0OV01_Enabled", n"PTFRB0OV01_Ready", n"PTFRB0OV01_Excluded", n"PTFRB0OV01_Near", n"PTFRB0OV01_Far", n"bls_ina_se1_clothingshop_01_default_on", true);
    this.AutoSite(q, n"PTFRB0OV02_Enabled", n"PTFRB0OV02_Ready", n"PTFRB0OV02_Excluded", n"PTFRB0OV02_Near", n"PTFRB0OV02_Far", n"bls_ina_se1_foodshop_02_default_on", true);
    this.AutoSite(q, n"PTFRB0OV03_Enabled", n"PTFRB0OV03_Ready", n"PTFRB0OV03_Excluded", n"PTFRB0OV03_Near", n"PTFRB0OV03_Far", n"bls_ina_se1_medicstore_01_default_on", true);
    this.AutoSite(q, n"PTFRB0OV04_Enabled", n"PTFRB0OV04_Ready", n"PTFRB0OV04_Excluded", n"PTFRB0OV04_Near", n"PTFRB0OV04_Far", n"cct_dtn_medic_01_default_on", true);
    this.AutoSite(q, n"PTFRB0OV05_Enabled", n"PTFRB0OV05_Ready", n"PTFRB0OV05_Excluded", n"PTFRB0OV05_Near", n"PTFRB0OV05_Far", n"hey_gle_gunsmith_01_default_on", true);
    this.AutoSite(q, n"PTFRB0OV06_Enabled", n"PTFRB0OV06_Ready", n"PTFRB0OV06_Excluded", n"PTFRB0OV06_Near", n"PTFRB0OV06_Far", n"pac_cvi_clothingshop_01_default_on", true);
    this.AutoSite(q, n"PTFRB0OV07_Enabled", n"PTFRB0OV07_Ready", n"PTFRB0OV07_Excluded", n"PTFRB0OV07_Near", n"PTFRB0OV07_Far", n"pac_cvi_foodshop_01_default_on", true);
    this.AutoSite(q, n"PTFRB0OV08_Enabled", n"PTFRB0OV08_Ready", n"PTFRB0OV08_Excluded", n"PTFRB0OV08_Near", n"PTFRB0OV08_Far", n"pac_cvi_medicstore_01_default_on", true);
    this.AutoSite(q, n"PTFRB0OV09_Enabled", n"PTFRB0OV09_Ready", n"PTFRB0OV09_Excluded", n"PTFRB0OV09_Near", n"PTFRB0OV09_Far", n"std_arr_clothingshop_01_default_on", true);
    this.AutoSite(q, n"PTFRB0OV10_Enabled", n"PTFRB0OV10_Ready", n"PTFRB0OV10_Excluded", n"PTFRB0OV10_Near", n"PTFRB0OV10_Far", n"std_arr_foodshop_02_default_on", true);
    this.AutoSite(q, n"PTFRB0OV11_Enabled", n"PTFRB0OV11_Ready", n"PTFRB0OV11_Excluded", n"PTFRB0OV11_Near", n"PTFRB0OV11_Far", n"std_arr_gunsmith_01_default_on", true);
    this.AutoSite(q, n"PTFRB0OV12_Enabled", n"PTFRB0OV12_Ready", n"PTFRB0OV12_Excluded", n"PTFRB0OV12_Near", n"PTFRB0OV12_Far", n"std_arr_medicstore_01_default_on", true);
    this.AutoSite(q, n"PTFRB0OV13_Enabled", n"PTFRB0OV13_Ready", n"PTFRB0OV13_Excluded", n"PTFRB0OV13_Near", n"PTFRB0OV13_Far", n"std_rcr_foodshop_01_default_on", true);
    this.AutoSite(q, n"PTFRB0OV14_Enabled", n"PTFRB0OV14_Ready", n"PTFRB0OV14_Excluded", n"PTFRB0OV14_Near", n"PTFRB0OV14_Far", n"std_rcr_gunsmith_01_default_on", true);
    this.AutoSite(q, n"PTFRB0OV15_Enabled", n"PTFRB0OV15_Ready", n"PTFRB0OV15_Excluded", n"PTFRB0OV15_Near", n"PTFRB0OV15_Far", n"wat_kab_junkshop_01_default_on", true);
    this.AutoSite(q, n"PTFRB0OV16_Enabled", n"PTFRB0OV16_Ready", n"PTFRB0OV16_Excluded", n"PTFRB0OV16_Near", n"PTFRB0OV16_Far", n"wat_kab_clothingshop_01_default_on", true);
    this.AutoSite(q, n"PTFRB0OV17_Enabled", n"PTFRB0OV17_Ready", n"PTFRB0OV17_Excluded", n"PTFRB0OV17_Near", n"PTFRB0OV17_Far", n"wat_lch_medicstore_01_default_on", true);
    this.AutoSite(q, n"PTFRB0OV18_Enabled", n"PTFRB0OV18_Ready", n"PTFRB0OV18_Excluded", n"PTFRB0OV18_Near", n"PTFRB0OV18_Far", n"wat_nid_clothingshop_01_default_on", true);
    this.AutoSite(q, n"PTFRB0OV19_Enabled", n"PTFRB0OV19_Ready", n"PTFRB0OV19_Excluded", n"PTFRB0OV19_Near", n"PTFRB0OV19_Far", n"wat_nid_medicstore_01_default_on", true);
    this.AutoSite(q, n"PTFRB0OV20_Enabled", n"PTFRB0OV20_Ready", n"PTFRB0OV20_Excluded", n"PTFRB0OV20_Near", n"PTFRB0OV20_Far", n"wbr_hil_clothingshop_01_default_on", true);
    this.AutoSite(q, n"PTFRB0OV21_Enabled", n"PTFRB0OV21_Ready", n"PTFRB0OV21_Excluded", n"PTFRB0OV21_Near", n"PTFRB0OV21_Far", n"wbr_jpn_melee_01_default_on", true);
    this.AutoSite(q, n"PTFRB0OV22_Enabled", n"PTFRB0OV22_Ready", n"PTFRB0OV22_Excluded", n"PTFRB0OV22_Near", n"PTFRB0OV22_Far", n"wbr_jpn_food_01_default_on", true);
    this.AutoSite(q, n"PTFRB0OV23_Enabled", n"PTFRB0OV23_Ready", n"PTFRB0OV23_Excluded", n"PTFRB0OV23_Near", n"PTFRB0OV23_Far", n"wbr_jpn_food_02_default_on", true);
    this.AutoSite(q, n"PTFRB0OV24_Enabled", n"PTFRB0OV24_Ready", n"PTFRB0OV24_Excluded", n"PTFRB0OV24_Near", n"PTFRB0OV24_Far", n"wbr_jpn_food_03_default_on", true);
    this.AutoSite(q, n"PTFRB0OV25_Enabled", n"PTFRB0OV25_Ready", n"PTFRB0OV25_Excluded", n"PTFRB0OV25_Near", n"PTFRB0OV25_Far", n"wbr_jpn_food_04_default_on", true);
    if this.ReadFact(q, n"PTFRB0OVB_Mode") != 1 {
      q.SetFact(n"PTFRB0OVB_Mode", 1);
      this.factWrites += 1;
    }
    q.SetFact(n"PTFRB0OVB_AutoPasses", this.ReadFact(q, n"PTFRB0OVB_AutoPasses") + 1);
    this.factWrites += 1;
  }

  private func UpdateSite(q: ref<QuestsSystem>, p: Vector4, enabled: CName, near: CName, far: CName, gate: CName, x: Float, y: Float, z: Float) -> Void {
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
      value = old == 1 ? (d2 >= 2025.0 ? 1 : 0) : (d2 > 3025.0 ? 1 : 0);
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
    let mode = q.GetFact(n"PTFRB0OVB_Mode");
    this.factReads += 2;
    let challenge = q.GetFact(n"PTFRB0OVB_Challenge");
    let ack = q.GetFact(n"PTFRB0OVB_Ack");
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
      q.SetFact(n"PTFRB0OVB_Ack", challenge);
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
    mode = this.ReadFact(q, n"PTFRB0OVB_Mode");
    if mode != 1 { this.Schedule(expectedEpoch, 1.0); return; }
    let position = player.GetWorldPosition();
    this.positionReads += 1;
    this.UpdateSite(q, position, n"PTFRB0OV01_Enabled", n"PTFRB0OV01_Near", n"PTFRB0OV01_Far", n"bls_ina_se1_clothingshop_01_default_on", 1208.857540000, -564.018677000, 33.126113900);
    this.UpdateSite(q, position, n"PTFRB0OV02_Enabled", n"PTFRB0OV02_Near", n"PTFRB0OV02_Far", n"bls_ina_se1_foodshop_02_default_on", 1200.130000000, -549.330811000, 32.601287800);
    this.UpdateSite(q, position, n"PTFRB0OV03_Enabled", n"PTFRB0OV03_Near", n"PTFRB0OV03_Far", n"bls_ina_se1_medicstore_01_default_on", 3443.613770000, -1979.466430000, 99.577186600);
    this.UpdateSite(q, position, n"PTFRB0OV04_Enabled", n"PTFRB0OV04_Near", n"PTFRB0OV04_Far", n"cct_dtn_medic_01_default_on", -1883.524050000, 380.301819000, 28.705139200);
    this.UpdateSite(q, position, n"PTFRB0OV05_Enabled", n"PTFRB0OV05_Near", n"PTFRB0OV05_Far", n"hey_gle_gunsmith_01_default_on", -1894.863530000, -1019.362240000, 7.804468150);
    this.UpdateSite(q, position, n"PTFRB0OV06_Enabled", n"PTFRB0OV06_Near", n"PTFRB0OV06_Far", n"pac_cvi_clothingshop_01_default_on", -2476.088620000, -2539.303710000, 16.959373500);
    this.UpdateSite(q, position, n"PTFRB0OV07_Enabled", n"PTFRB0OV07_Near", n"PTFRB0OV07_Far", n"pac_cvi_foodshop_01_default_on", -1927.484380000, -1912.101560000, 49.302490200);
    this.UpdateSite(q, position, n"PTFRB0OV08_Enabled", n"PTFRB0OV08_Near", n"PTFRB0OV08_Far", n"pac_cvi_medicstore_01_default_on", -1899.875610000, -1900.820920000, 49.303035700);
    this.UpdateSite(q, position, n"PTFRB0OV09_Enabled", n"PTFRB0OV09_Near", n"PTFRB0OV09_Far", n"std_arr_clothingshop_01_default_on", -992.698792000, -1567.677120000, 25.700927700);
    this.UpdateSite(q, position, n"PTFRB0OV10_Enabled", n"PTFRB0OV10_Near", n"PTFRB0OV10_Far", n"std_arr_foodshop_02_default_on", -983.919617000, -1160.302730000, 11.655003500);
    this.UpdateSite(q, position, n"PTFRB0OV11_Enabled", n"PTFRB0OV11_Near", n"PTFRB0OV11_Far", n"std_arr_gunsmith_01_default_on", -995.590454000, -1587.636960000, 25.500146900);
    this.UpdateSite(q, position, n"PTFRB0OV12_Enabled", n"PTFRB0OV12_Near", n"PTFRB0OV12_Far", n"std_arr_medicstore_01_default_on", -1004.403930000, -1572.999150000, 25.701049800);
    this.UpdateSite(q, position, n"PTFRB0OV13_Enabled", n"PTFRB0OV13_Near", n"PTFRB0OV13_Far", n"std_rcr_foodshop_01_default_on", 323.517883000, -1625.694090000, 9.260000230);
    this.UpdateSite(q, position, n"PTFRB0OV14_Enabled", n"PTFRB0OV14_Near", n"PTFRB0OV14_Far", n"std_rcr_gunsmith_01_default_on", 572.663086000, -2192.382080000, 35.343036700);
    this.UpdateSite(q, position, n"PTFRB0OV15_Enabled", n"PTFRB0OV15_Near", n"PTFRB0OV15_Far", n"wat_kab_junkshop_01_default_on", -1021.710020000, 1440.389890000, 16.479999500);
    this.UpdateSite(q, position, n"PTFRB0OV16_Enabled", n"PTFRB0OV16_Near", n"PTFRB0OV16_Far", n"wat_kab_clothingshop_01_default_on", -1121.998540000, 1752.022340000, 33.755600000);
    this.UpdateSite(q, position, n"PTFRB0OV17_Enabled", n"PTFRB0OV17_Near", n"PTFRB0OV17_Far", n"wat_lch_medicstore_01_default_on", -1704.050050000, 1253.440060000, 18.522943500);
    this.UpdateSite(q, position, n"PTFRB0OV18_Enabled", n"PTFRB0OV18_Near", n"PTFRB0OV18_Far", n"wat_nid_clothingshop_01_default_on", -1901.512080000, 2506.321290000, 18.194152800);
    this.UpdateSite(q, position, n"PTFRB0OV19_Enabled", n"PTFRB0OV19_Near", n"PTFRB0OV19_Far", n"wat_nid_medicstore_01_default_on", -1589.546510000, 2085.027340000, 18.235050200);
    this.UpdateSite(q, position, n"PTFRB0OV20_Enabled", n"PTFRB0OV20_Near", n"PTFRB0OV20_Far", n"wbr_hil_clothingshop_01_default_on", -229.672913000, -33.460716200, 1.610816000);
    this.UpdateSite(q, position, n"PTFRB0OV21_Enabled", n"PTFRB0OV21_Near", n"PTFRB0OV21_Far", n"wbr_jpn_melee_01_default_on", -334.709869000, 562.970093000, 38.389003800);
    this.UpdateSite(q, position, n"PTFRB0OV22_Enabled", n"PTFRB0OV22_Near", n"PTFRB0OV22_Far", n"wbr_jpn_food_01_default_on", -651.121460000, 924.446838000, 9.389999390);
    this.UpdateSite(q, position, n"PTFRB0OV23_Enabled", n"PTFRB0OV23_Near", n"PTFRB0OV23_Far", n"wbr_jpn_food_02_default_on", -690.113220000, 775.194031000, 36.389171600);
    this.UpdateSite(q, position, n"PTFRB0OV24_Enabled", n"PTFRB0OV24_Near", n"PTFRB0OV24_Far", n"wbr_jpn_food_03_default_on", -645.409119000, 850.397461000, 18.901697200);
    this.UpdateSite(q, position, n"PTFRB0OV25_Enabled", n"PTFRB0OV25_Near", n"PTFRB0OV25_Far", n"wbr_jpn_food_04_default_on", -488.930206000, 582.986206000, 31.306205700);
    this.Schedule(expectedEpoch, 0.5);
  }
}

public class OrdinaryVendorTick extends DelayCallback {
  private let driver: wref<OrdinaryVendorDriver>;
  private let epoch: Int32;
  public func Call() -> Void {
    if IsDefined(this.driver) { this.driver.Poll(this.epoch); }
  }
  public static func Create(driver: ref<OrdinaryVendorDriver>, epoch: Int32) -> ref<OrdinaryVendorTick> {
    let result = new OrdinaryVendorTick();
    result.driver = driver;
    result.epoch = epoch;
    return result;
  }
}
