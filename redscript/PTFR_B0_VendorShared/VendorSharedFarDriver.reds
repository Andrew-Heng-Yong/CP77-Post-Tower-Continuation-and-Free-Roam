module PTFR.B0VendorShared

// Opt-in four-shop development driver. The existing native one-shop phases
// continue to own actor spawning, Trade scenes, and exit/rearm. This replaces
// four independent CET Far writers with one player-position query per tick.
// Only mod-owned facts are written; every vanilla shop/default fact is read.
public class VendorSharedFarDriver extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;

  private func OnAttach() -> Void {
    this.epoch += 1;
    this.running = true;
    this.Schedule(this.epoch, 1.0);
  }

  private func OnDetach() -> Void {
    this.running = false;
    this.epoch += 1;
  }

  private func Schedule(expectedEpoch: Int32, delay: Float) -> Void {
    let delaySystem = GameInstance.GetDelaySystem(this.GetGameInstance());
    if IsDefined(delaySystem) {
      delaySystem.DelayCallback(VendorSharedFarTick.Create(this, expectedEpoch), delay, false);
    }
  }

  private func FarValue(current: Int32, x: Float, y: Float, z: Float, cx: Float, cy: Float, cz: Float) -> Int32 {
    let dx = x - cx;
    let dy = y - cy;
    let dz = z - cz;
    let squared = dx * dx + dy * dy + dz * dz;
    if current == 1 {
      return squared >= 2025.0 ? 1 : 0; // remain far until within 45 m
    }
    return squared > 3025.0 ? 1 : 0; // become far beyond 55 m
  }

  public func Poll(expectedEpoch: Int32) -> Void {
    if !this.running || expectedEpoch != this.epoch {
      return;
    }
    let game = this.GetGameInstance();
    let quests = GameInstance.GetQuestsSystem(game);
    let players = GameInstance.GetPlayerSystem(game);
    if !IsDefined(quests) || !IsDefined(players) {
      this.Schedule(expectedEpoch, 1.0);
      return;
    }
    let player = players.GetLocalPlayerMainGameObject();
    if !IsDefined(player) {
      this.Schedule(expectedEpoch, 1.0);
      return;
    }

    let eligible = quests.GetFact(n"PostTowerFreeRoamActive") == 1
      && quests.GetFact(n"PTFRP0_DR13") == 1
      && quests.GetFact(n"q307_active") == 0
      && quests.GetFact(n"q307_done") == 1
      && quests.GetFact(n"q307_finished") == 1
      && quests.GetFact(n"q307_2079") == 1
      && quests.GetFact(n"q307_main_game_killed") == 1
      && quests.GetFact(n"q305_johnny_scene_active") == 0
      && quests.GetFact(n"q115_point_of_no_return") == 0;
    if !eligible {
      this.Schedule(expectedEpoch, 1.0);
      return;
    }

    // Start() supplies a new challenge and waits for this response before
    // switching the old CET writers off or enabling any owner. A saved Ack
    // cannot satisfy a new challenge after a failed redscript load.
    let challenge = quests.GetFact(n"PTFRB0VSH_Challenge");
    if challenge != 0 && quests.GetFact(n"PTFRB0VSH_Ack") != challenge {
      quests.SetFact(n"PTFRB0VSH_Ack", challenge);
    }

    if quests.GetFact(n"PTFRB0VSH_SharedMode") != 1 {
      this.Schedule(expectedEpoch, 1.0);
      return;
    }

    let position = player.GetWorldPosition();
    if quests.GetFact(n"PTFRB0NIDG_Enabled") == 1 && quests.GetFact(n"wat_nid_gunsmith_01_default_on") == 1 {
      let oldValue = quests.GetFact(n"PTFRB0NIDG_Far");
      let newValue = this.FarValue(oldValue, position.X, position.Y, position.Z, -1891.04321, 2730.45508, 7.45457);
      if oldValue != newValue { quests.SetFact(n"PTFRB0NIDG_Far", newValue); }
    }
    if quests.GetFact(n"PTFRB0NIDF_Enabled") == 1 && quests.GetFact(n"wat_nid_foodshop_01_default_on") == 1 {
      let oldValue = quests.GetFact(n"PTFRB0NIDF_Far");
      let newValue = this.FarValue(oldValue, position.X, position.Y, position.Z, -1914.45435, 2739.48535, 10.89868);
      if oldValue != newValue { quests.SetFact(n"PTFRB0NIDF_Far", newValue); }
    }
    if quests.GetFact(n"PTFRB0NIDM_Enabled") == 1 && quests.GetFact(n"wat_nid_medicstore_02_default_on") == 1 {
      let oldValue = quests.GetFact(n"PTFRB0NIDM_Far");
      let newValue = this.FarValue(oldValue, position.X, position.Y, position.Z, -1933.20081, 2744.16357, 10.45010);
      if oldValue != newValue { quests.SetFact(n"PTFRB0NIDM_Far", newValue); }
    }
    if quests.GetFact(n"PTFRB0LCHV_Enabled") == 1 && quests.GetFact(n"wat_lch_clothingshop_01_default_on") == 1 {
      let oldValue = quests.GetFact(n"PTFRB0LCHV_Far");
      let newValue = this.FarValue(oldValue, position.X, position.Y, position.Z, -1525.48560, 1702.87329, 18.32000);
      if oldValue != newValue { quests.SetFact(n"PTFRB0LCHV_Far", newValue); }
    }
    this.Schedule(expectedEpoch, 0.5);
  }
}

public class VendorSharedFarTick extends DelayCallback {
  private let driver: wref<VendorSharedFarDriver>;
  private let epoch: Int32;

  public func Call() -> Void {
    if IsDefined(this.driver) {
      this.driver.Poll(this.epoch);
    }
  }

  public static func Create(driver: ref<VendorSharedFarDriver>, epoch: Int32) -> ref<VendorSharedFarTick> {
    let callback = new VendorSharedFarTick();
    callback.driver = driver;
    callback.epoch = epoch;
    return callback;
  }
}
