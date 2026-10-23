module PTFR.B0AfterlifeMirror

// Single-site runtime replacement for the development CET proximity writer.
// The native questphase still owns the mirror scene and its one-second rearm.
public class AfterlifeMirrorDriver extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;

  private func OnAttach() -> Void {
    this.epoch += 1;
    this.running = true;
    // Let restored save facts and the player entity settle before the first read.
    let delaySystem = GameInstance.GetDelaySystem(this.GetGameInstance());
    if IsDefined(delaySystem) {
      delaySystem.DelayCallback(AfterlifeMirrorTick.Create(this, this.epoch), 1.0, false);
    }
  }

  private func OnDetach() -> Void {
    this.running = false;
    this.epoch += 1;
  }

  public func Poll(expectedEpoch: Int32) -> Void {
    if !this.running || expectedEpoch != this.epoch {
      return;
    }

    this.UpdateNear();

    let delaySystem = GameInstance.GetDelaySystem(this.GetGameInstance());
    if IsDefined(delaySystem) {
      delaySystem.DelayCallback(AfterlifeMirrorTick.Create(this, expectedEpoch), 0.5, false);
    }
  }

  private func UpdateNear() -> Void {
    let game = this.GetGameInstance();
    let quests = GameInstance.GetQuestsSystem(game);
    if !IsDefined(quests) {
      return;
    }

    let current = quests.GetFact(n"PTFRB0ALM_Near");
    let desired: Int32 = 0;
    let eligible = quests.GetFact(n"PTFRB0ALM_Enabled") == 1
      && quests.GetFact(n"PostTowerFreeRoamActive") == 1
      && quests.GetFact(n"PTFRP0_DR13") == 1
      && quests.GetFact(n"q307_active") == 0
      && quests.GetFact(n"q307_done") == 1
      && quests.GetFact(n"q307_finished") == 1
      && quests.GetFact(n"q307_2079") == 1
      && quests.GetFact(n"q307_main_game_killed") == 1
      && quests.GetFact(n"q305_johnny_scene_active") == 0
      && quests.GetFact(n"mirror_interaction_disabled") == 0
      && quests.GetFact(n"q115_point_of_no_return") == 0
      && quests.GetFact(n"PTFRB0ALM_Interrupted") == 0;

    if eligible {
      let player = GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject();
      if IsDefined(player) {
        let position = player.GetWorldPosition();
        let dx = position.X - (-1438.97388);
        let dy = position.Y - 1039.22314;
        let dz = position.Z - 16.92;
        let radius = current == 1 ? 7.0 : 5.5;
        if dx * dx + dy * dy + dz * dz <= radius * radius {
          desired = 1;
        }
      }
    }

    if current != desired {
      quests.SetFact(n"PTFRB0ALM_Near", desired);
    }
  }
}

public class AfterlifeMirrorTick extends DelayCallback {
  private let driver: wref<AfterlifeMirrorDriver>;
  private let epoch: Int32;

  public func Call() -> Void {
    if IsDefined(this.driver) {
      this.driver.Poll(this.epoch);
    }
  }

  public static func Create(driver: ref<AfterlifeMirrorDriver>, epoch: Int32) -> ref<AfterlifeMirrorTick> {
    let callback = new AfterlifeMirrorTick();
    callback.driver = driver;
    callback.epoch = epoch;
    return callback;
  }
}
