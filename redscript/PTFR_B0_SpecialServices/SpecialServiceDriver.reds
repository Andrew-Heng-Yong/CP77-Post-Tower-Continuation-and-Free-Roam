module PTFR.B0SpecialServices

// Five-second pending-enable check; safety queried once only if an eligible site needs enablement.
// Native owners perform all approach, scene and departure work; no distance polling.
public class SpecialServiceDriver extends ScriptableSystem {
  private let epoch: Int32;
  private let running: Bool;
  private func OnAttach() -> Void {
    this.epoch += 1;
    this.running = true;
    this.Schedule(this.epoch);
  }
  private func OnDetach() -> Void { this.running = false; this.epoch += 1; }
  private func Schedule(epoch: Int32) -> Void {
    let delays = GameInstance.GetDelaySystem(this.GetGameInstance());
    if IsDefined(delays) { delays.DelayCallback(SpecialServiceTick.Create(this, epoch), 5.0, false); }
  }
  private func Eligible(q: ref<QuestsSystem>) -> Bool {
    return q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
      q.GetFact(n"PTFRP0_DR13") == 1 &&
      q.GetFact(n"q307_active") == 0 &&
      q.GetFact(n"q307_done") == 1 &&
      q.GetFact(n"q307_finished") == 1 &&
      q.GetFact(n"q307_2079") == 1 &&
      q.GetFact(n"q307_main_game_killed") == 1 &&
      q.GetFact(n"q305_johnny_scene_active") == 0 &&
      q.GetFact(n"q115_point_of_no_return") == 0 &&
      q.GetFact(n"q000_done") == 1 &&
      q.GetFact(n"q307_ep1_killed") == 1 && q.GetFact(n"PTFRBASE_Suspended") == 0 && q.GetFact(n"PTFRB0SP_Suspended") == 0;
  }
  private func Site(q: ref<QuestsSystem>, enabled: CName, ready: CName, active: CName, excluded: CName, gate: CName, extra: Bool, commit: Bool) -> Bool {
    if !extra || q.GetFact(gate) <= 0 || q.GetFact(enabled) != 0 || q.GetFact(ready) != 1 || q.GetFact(active) != 0 || q.GetFact(excluded) != 0 { return false; }
    if commit { q.SetFact(enabled, 1); }
    return true;
  }
  private func Sites(q: ref<QuestsSystem>, commit: Bool) -> Bool {
    let pending = false;
    pending = this.Site(q, n"PTFRB0SP01_Enabled", n"PTFRB0SP01_Ready", n"PTFRB0SP01_OwnerActive", n"PTFRB0SP01_Excluded", n"cz_con_gunsmith_01_default_on", q.GetFact(n"ep1_side_content") > 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0SP02_Enabled", n"PTFRB0SP02_Ready", n"PTFRB0SP02_OwnerActive", n"PTFRB0SP02_Excluded", n"cz_con_clothingshop_01_default_on", q.GetFact(n"ep1_side_content") > 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0SP03_Enabled", n"PTFRB0SP03_Ready", n"PTFRB0SP03_OwnerActive", n"PTFRB0SP03_Excluded", n"cz_con_ripdoc_01_default_on", q.GetFact(n"ep1_side_content") > 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0SP04_Enabled", n"PTFRB0SP04_Ready", n"PTFRB0SP04_OwnerActive", n"PTFRB0SP04_Excluded", n"cz_con_medicstore_01_default_on", q.GetFact(n"ep1_side_content") > 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0SP05_Enabled", n"PTFRB0SP05_Ready", n"PTFRB0SP05_OwnerActive", n"PTFRB0SP05_Excluded", n"cz_con_junkshop_01_default_on", q.GetFact(n"ep1_side_content") > 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0SP06_Enabled", n"PTFRB0SP06_Ready", n"PTFRB0SP06_OwnerActive", n"PTFRB0SP06_Excluded", n"cz_con_foodshop_01_default_on", q.GetFact(n"ep1_side_content") > 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0SP07_Enabled", n"PTFRB0SP07_Ready", n"PTFRB0SP07_OwnerActive", n"PTFRB0SP07_Excluded", n"cz_stadium_gunsmith_01_default_on", q.GetFact(n"ep1_side_content") > 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0SP08_Enabled", n"PTFRB0SP08_Ready", n"PTFRB0SP08_OwnerActive", n"PTFRB0SP08_Excluded", n"cz_stadium_ripperdoc_01_default_on", q.GetFact(n"ep1_side_content") > 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0SP09_Enabled", n"PTFRB0SP09_Ready", n"PTFRB0SP09_OwnerActive", n"PTFRB0SP09_Excluded", n"cz_stadium_clothing_01_default_on", q.GetFact(n"ep1_side_content") > 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0SP10_Enabled", n"PTFRB0SP10_Ready", n"PTFRB0SP10_OwnerActive", n"PTFRB0SP10_Excluded", n"cz_stadium_junk_01_default_on", q.GetFact(n"ep1_side_content") > 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0SP11_Enabled", n"PTFRB0SP11_Ready", n"PTFRB0SP11_OwnerActive", n"PTFRB0SP11_Excluded", n"cz_stadium_netrunner_01_default_on", q.GetFact(n"ep1_side_content") > 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0SP12_Enabled", n"PTFRB0SP12_Ready", n"PTFRB0SP12_OwnerActive", n"PTFRB0SP12_Excluded", n"cz_stadium_black_market_01_default_on", q.GetFact(n"ep1_side_content") > 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0SP13_Enabled", n"PTFRB0SP13_Ready", n"PTFRB0SP13_OwnerActive", n"PTFRB0SP13_Excluded", n"cz_stadium_medic_01_default_on", q.GetFact(n"ep1_side_content") > 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0SP14_Enabled", n"PTFRB0SP14_Ready", n"PTFRB0SP14_OwnerActive", n"PTFRB0SP14_Excluded", n"cz_stadium_food_01_default_on", q.GetFact(n"ep1_side_content") > 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0SP15_Enabled", n"PTFRB0SP15_Ready", n"PTFRB0SP15_OwnerActive", n"PTFRB0SP15_Excluded", n"cz_stadium_food_02_default_on", q.GetFact(n"ep1_side_content") > 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0SP16_Enabled", n"PTFRB0SP16_Ready", n"PTFRB0SP16_OwnerActive", n"PTFRB0SP16_Excluded", n"cz_stadium_food_03_default_on", q.GetFact(n"ep1_side_content") > 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0SP17_Enabled", n"PTFRB0SP17_Ready", n"PTFRB0SP17_OwnerActive", n"PTFRB0SP17_Excluded", n"cz_monument_ripperdoc_farida_default_on", q.GetFact(n"ep1_side_content") > 0 && q.GetFact(n"q304_out_of_faridas_clinic") > 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0SP18_Enabled", n"PTFRB0SP18_Ready", n"PTFRB0SP18_OwnerActive", n"PTFRB0SP18_Excluded", n"cz_monument_ripperdoc_anderson_default_on", q.GetFact(n"ep1_side_content") > 0 && q.GetFact(n"sts_ep1_01_vendor_active") > 0, commit) || pending;
    pending = this.Site(q, n"PTFRB0SP19_Enabled", n"PTFRB0SP19_Ready", n"PTFRB0SP19_OwnerActive", n"PTFRB0SP19_Excluded", n"cz_monument_medical_odel_default_on", q.GetFact(n"ep1_side_content") > 0 && q.GetFact(n"sts_ep1_01_vendor_active_odel") > 0, commit) || pending;
    return pending;
  }
  private func Safe(player: ref<PlayerPuppet>) -> Bool {
    let game = this.GetGameInstance();
    let scene = GameInstance.GetSceneSystem(game).GetScriptInterface();
    let workspots = GameInstance.GetWorkspotSystem(game);
    if !IsDefined(scene) || !IsDefined(workspots) { return false; }
    if player.IsInCombat() || scene.IsEntityInScene(player.GetEntityID()) || workspots.IsActorInWorkspot(player) { return false; }
    let mount = GameInstance.GetMountingFacility(game).GetMountingInfoSingleWithObjects(player);
    if EntityID.IsDefined(mount.parentId) { return false; }
    let bb = player.GetPlayerStateMachineBlackboard();
    if !IsDefined(bb) { return false; }
    let high = bb.GetInt(GetAllBlackboardDefs().PlayerStateMachine.HighLevel);
    let tier = bb.GetInt(GetAllBlackboardDefs().PlayerStateMachine.SceneTier);
    if (high != 1 && high != 2) || (tier != 1 && tier != 2) { return false; }
    if GameInstance.GetQuestsContentSystem(game).IsTokensActivationBlocked() { return false; }
    let locks: array<gameSaveLock>;
    return !GameInstance.IsSavingLocked(game, locks);
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    let game = this.GetGameInstance();
    let q = GameInstance.GetQuestsSystem(game);
    if IsDefined(q) && this.Eligible(q) && this.Sites(q, false) {
      let player = GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
      if IsDefined(player) && this.Safe(player) { this.Sites(q, true); }
    }
    this.Schedule(epoch);
  }
}
public class SpecialServiceTick extends DelayCallback {
  private let driver: wref<SpecialServiceDriver>;
  private let epoch: Int32;
  public func Call() -> Void { if IsDefined(this.driver) { this.driver.Poll(this.epoch); } }
  public static func Create(driver: ref<SpecialServiceDriver>, epoch: Int32) -> ref<SpecialServiceTick> {
    let result = new SpecialServiceTick(); result.driver = driver; result.epoch = epoch; return result;
  }
}
