module PTFR.B0VendorVariants

// Generated site calls come from the audited cohort. Native owners retain
// their complete vanilla scenes and own spawning, entry and exit.
public class VendorVariantDriver extends ScriptableSystem {
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
      delays.DelayCallback(VendorVariantTick.Create(this, epoch), seconds, false);
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
    if this.ReadFact(q, n"PTFRB0VV_Suspended") != 0 { return; }
    let pending = false;
    pending = this.AutoSite(q, n"PTFRB0VV01_Enabled", n"PTFRB0VV01_Ready", n"PTFRB0VV01_Excluded", n"PTFRB0VV01_Near", n"PTFRB0VV01_Far", n"bls_ina_se1_gunsmith_02_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0VV02_Enabled", n"PTFRB0VV02_Ready", n"PTFRB0VV02_Excluded", n"PTFRB0VV02_Near", n"PTFRB0VV02_Far", n"bls_ina_se5_foodshop_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0VV03_Enabled", n"PTFRB0VV03_Ready", n"PTFRB0VV03_Excluded", n"PTFRB0VV03_Near", n"PTFRB0VV03_Far", n"pac_wwd_melee_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0VV04_Enabled", n"PTFRB0VV04_Ready", n"PTFRB0VV04_Excluded", n"PTFRB0VV04_Near", n"PTFRB0VV04_Far", n"std_rcr_clothingshop_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0VV05_Enabled", n"PTFRB0VV05_Ready", n"PTFRB0VV05_Excluded", n"PTFRB0VV05_Near", n"PTFRB0VV05_Far", n"std_rcr_medicstore_01_default_on", false) || pending;
    pending = this.AutoSite(q, n"PTFRB0VV06_Enabled", n"PTFRB0VV06_Ready", n"PTFRB0VV06_Excluded", n"PTFRB0VV06_Near", n"PTFRB0VV06_Far", n"wbr_jpn_medic_01_default_on", false) || pending;
    if !pending { return; }
    // Expensive safety queries run once per activation attempt, not per shop
    // or departure tick. Original native eligibility is rechecked on entry.
    let game = this.GetGameInstance();
    let scene = GameInstance.GetSceneSystem(game).GetScriptInterface();
    let workspots = GameInstance.GetWorkspotSystem(game);
    if !IsDefined(scene) || !IsDefined(workspots) { return; }
    if player.IsInCombat() || scene.IsEntityInScene(player.GetEntityID()) ||
       workspots.IsActorInWorkspot(player) { return; }
    this.AutoSite(q, n"PTFRB0VV01_Enabled", n"PTFRB0VV01_Ready", n"PTFRB0VV01_Excluded", n"PTFRB0VV01_Near", n"PTFRB0VV01_Far", n"bls_ina_se1_gunsmith_02_default_on", true);
    this.AutoSite(q, n"PTFRB0VV02_Enabled", n"PTFRB0VV02_Ready", n"PTFRB0VV02_Excluded", n"PTFRB0VV02_Near", n"PTFRB0VV02_Far", n"bls_ina_se5_foodshop_01_default_on", true);
    this.AutoSite(q, n"PTFRB0VV03_Enabled", n"PTFRB0VV03_Ready", n"PTFRB0VV03_Excluded", n"PTFRB0VV03_Near", n"PTFRB0VV03_Far", n"pac_wwd_melee_01_default_on", true);
    this.AutoSite(q, n"PTFRB0VV04_Enabled", n"PTFRB0VV04_Ready", n"PTFRB0VV04_Excluded", n"PTFRB0VV04_Near", n"PTFRB0VV04_Far", n"std_rcr_clothingshop_01_default_on", true);
    this.AutoSite(q, n"PTFRB0VV05_Enabled", n"PTFRB0VV05_Ready", n"PTFRB0VV05_Excluded", n"PTFRB0VV05_Near", n"PTFRB0VV05_Far", n"std_rcr_medicstore_01_default_on", true);
    this.AutoSite(q, n"PTFRB0VV06_Enabled", n"PTFRB0VV06_Ready", n"PTFRB0VV06_Excluded", n"PTFRB0VV06_Near", n"PTFRB0VV06_Far", n"wbr_jpn_medic_01_default_on", true);
    if this.ReadFact(q, n"PTFRB0VV_Mode") != 1 {
      q.SetFact(n"PTFRB0VV_Mode", 1);
      this.factWrites += 1;
    }
    q.SetFact(n"PTFRB0VV_AutoPasses", this.ReadFact(q, n"PTFRB0VV_AutoPasses") + 1);
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
    let mode = q.GetFact(n"PTFRB0VV_Mode");
    this.factReads += 2;
    let challenge = q.GetFact(n"PTFRB0VV_Challenge");
    let ack = q.GetFact(n"PTFRB0VV_Ack");
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
      q.SetFact(n"PTFRB0VV_Ack", challenge);
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
    mode = this.ReadFact(q, n"PTFRB0VV_Mode");
    if mode != 1 { this.Schedule(expectedEpoch, 1.0); return; }
    let position = player.GetWorldPosition();
    this.positionReads += 1;
    this.UpdateSite(q, position, n"PTFRB0VV01_Enabled", n"PTFRB0VV01_Near", n"PTFRB0VV01_Far", n"bls_ina_se1_gunsmith_02_default_on", 1677.701170000, -775.941833000, 49.850002300, 2025.0, 7225.0);
    this.UpdateSite(q, position, n"PTFRB0VV02_Enabled", n"PTFRB0VV02_Near", n"PTFRB0VV02_Far", n"bls_ina_se5_foodshop_01_default_on", -3491.316650000, -4009.709230000, 77.019989000, 2025.0, 3025.0);
    this.UpdateSite(q, position, n"PTFRB0VV03_Enabled", n"PTFRB0VV03_Near", n"PTFRB0VV03_Far", n"pac_wwd_melee_01_default_on", -2520.948000000, -2473.637210000, 16.809999500, 5625.0, 7225.0);
    this.UpdateSite(q, position, n"PTFRB0VV04_Enabled", n"PTFRB0VV04_Near", n"PTFRB0VV04_Far", n"std_rcr_clothingshop_01_default_on", 250.143951000, -1468.719730000, 9.500000000, 225.0, 625.0);
    this.UpdateSite(q, position, n"PTFRB0VV05_Enabled", n"PTFRB0VV05_Near", n"PTFRB0VV05_Far", n"std_rcr_medicstore_01_default_on", 420.602722000, -1442.774050000, 15.204635600, 625.0, 1225.0);
    this.UpdateSite(q, position, n"PTFRB0VV06_Enabled", n"PTFRB0VV06_Near", n"PTFRB0VV06_Far", n"wbr_jpn_medic_01_default_on", -440.720795000, 1437.824830000, 37.279304500, 2025.0, 4096.0);
    this.Schedule(expectedEpoch, 0.5);
  }
}

public class VendorVariantTick extends DelayCallback {
  private let driver: wref<VendorVariantDriver>;
  private let epoch: Int32;
  public func Call() -> Void {
    if IsDefined(this.driver) { this.driver.Poll(this.epoch); }
  }
  public static func Create(driver: ref<VendorVariantDriver>, epoch: Int32) -> ref<VendorVariantTick> {
    let result = new VendorVariantTick();
    result.driver = driver;
    result.epoch = epoch;
    return result;
  }
}
