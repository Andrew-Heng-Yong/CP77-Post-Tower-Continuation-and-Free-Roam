module PTFR.AfterlifeNativeBootstrapA4

// One-site post-Tower startup switch for the tested A2 native Afterlife owner.
// The v5/v6 implementation stays installed as rollback. On an ordinary
// post-Tower save loaded outside the mirror, this disables v5 and requests A2.
// No story or vanilla quest facts are written.
public class AfterlifeNativeBootstrapA4 extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let attempts: Int32;

  private func OnAttach() -> Void {
    this.epoch += 1;
    this.attempts = 0;
    this.running = false; // Baseline-R1 owns this job; serialized type retained for rollback.
    this.Schedule(this.epoch);
  }

  private func OnDetach() -> Void {
    this.running = false;
    this.epoch += 1;
  }

  private func Schedule(expectedEpoch: Int32) -> Void {
    let delaySystem = GameInstance.GetDelaySystem(this.GetGameInstance());
    if IsDefined(delaySystem) {
      delaySystem.DelayCallback(AfterlifeNativeBootstrapTickA4.Create(this, expectedEpoch), 1.0, false);
    }
  }

  public func Poll(expectedEpoch: Int32) -> Void {
    if !this.running || expectedEpoch != this.epoch {
      return;
    }
    this.attempts += 1;
    if this.attempts > 300 {
      // Keep the saved v5/v6 fallback unchanged if the native owner did not
      // become safe to request within five minutes of attaching.
      this.running = false;
      return;
    }

    let game = this.GetGameInstance();
    let quests = GameInstance.GetQuestsSystem(game);
    let playerSystem = GameInstance.GetPlayerSystem(game);
    if !IsDefined(quests) || !IsDefined(playerSystem) {
      this.Schedule(expectedEpoch);
      return;
    }
    let player = playerSystem.GetLocalPlayerMainGameObject();
    if !IsDefined(player) {
      this.Schedule(expectedEpoch);
      return;
    }

    // A non-Tower load is outside this one-site feature. The genuine ending
    // and all story branches remain untouched.
    if quests.GetFact(n"PostTowerFreeRoamActive") != 1 ||
       quests.GetFact(n"PTFRP0_DR13") != 1 ||
       quests.GetFact(n"q307_active") != 0 ||
       quests.GetFact(n"q307_done") != 1 ||
       quests.GetFact(n"q307_finished") != 1 ||
       quests.GetFact(n"q307_2079") != 1 ||
       quests.GetFact(n"q307_main_game_killed") != 1 ||
       quests.GetFact(n"q305_johnny_scene_active") != 0 ||
       quests.GetFact(n"mirror_interaction_disabled") != 0 ||
       quests.GetFact(n"q115_point_of_no_return") != 0 {
      this.running = false;
      return;
    }

    let requested = quests.GetFact(n"PTFRALMA2_Requested");
    let oldEnabled = quests.GetFact(n"PTFRB0ALM_Enabled");
    if requested == 1 && oldEnabled == 0 {
      // Saved A2 state, such as the validated outside/idle ManualSave-16.
      // The native owner resumes from the save without a new writer call.
      this.running = false;
      return;
    }
    if requested != 0 || oldEnabled != 1 ||
       quests.GetFact(n"PTFRB0ALM_Interrupted") != 0 ||
       quests.GetFact(n"PTFRALMA2_Interrupted") != 0 {
      // Inconsistent or interrupted state: never create dual scene owners.
      this.running = false;
      return;
    }
    if quests.GetFact(n"PTFRALMA2_Boot") != 1 ||
       quests.GetFact(n"PTFRB0ALM_Near") != 0 ||
       quests.GetFact(n"PTFRB0ALM_Active") != 0 {
      this.Schedule(expectedEpoch);
      return;
    }

    let position = player.GetWorldPosition();
    let dx = position.X - (-1438.97388);
    let dy = position.Y - 1039.22314;
    let dz = position.Z - 16.92;
    if dx * dx + dy * dy + dz * dz <= 49.0 {
      // Wait until V physically leaves the mirror area before switching owner.
      this.Schedule(expectedEpoch);
      return;
    }

    quests.SetFact(n"PTFRB0ALM_Enabled", 0);
    if quests.GetFact(n"PTFRB0ALM_Enabled") != 0 {
      this.running = false;
      return;
    }
    quests.SetFact(n"PTFRALMA2_Requested", 1);
    if quests.GetFact(n"PTFRALMA2_Requested") != 1 {
      // Request failed before A2 could start. Restore only our mod-owned
      // v5 flag, leaving the already working scene owner available.
      quests.SetFact(n"PTFRB0ALM_Enabled", 1);
    }
    this.running = false;
  }
}

public class AfterlifeNativeBootstrapTickA4 extends DelayCallback {
  private let driver: wref<AfterlifeNativeBootstrapA4>;
  private let epoch: Int32;

  public func Call() -> Void {
    if IsDefined(this.driver) {
      this.driver.Poll(this.epoch);
    }
  }

  public static func Create(driver: ref<AfterlifeNativeBootstrapA4>, epoch: Int32) -> ref<AfterlifeNativeBootstrapTickA4> {
    let callback = new AfterlifeNativeBootstrapTickA4();
    callback.driver = driver;
    callback.epoch = epoch;
    return callback;
  }
}
