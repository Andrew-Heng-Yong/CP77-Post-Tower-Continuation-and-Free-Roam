module PTFR.TowerJournalAuto

// Production bridge for the previously live-verified exact q307 journal
// reconciler. The reconciler itself remains the only JournalManager writer.
public class TowerJournalAuto extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let completed: Bool;
  private let cleanup: ref<PTFRTowerJournalCleanup>;

  private func OnAttach() -> Void {
    this.epoch += 1;
    this.running = true;
    this.completed = false;
    this.cleanup = null;
    this.Schedule(this.epoch, 1.0);
  }
  private func OnDetach() -> Void {
    this.running = false;
    this.epoch += 1;
    if IsDefined(this.cleanup) { this.cleanup.Cancel(); }
    this.cleanup = null;
  }
  private func Schedule(epoch: Int32, seconds: Float) -> Void {
    let delay = GameInstance.GetDelaySystem(this.GetGameInstance());
    if IsDefined(delay) { delay.DelayCallback(TowerJournalAutoTick.Create(this,epoch),seconds,false); }
  }
  private func Eligible(q: ref<QuestsSystem>) -> Bool {
    return q.GetFact(n"PostTowerFreeRoamActive") == 1 && q.GetFact(n"PTFRP0_DR13") == 1 &&
      q.GetFact(n"q307_active") == 0 && q.GetFact(n"q307_done") == 1 &&
      q.GetFact(n"q307_finished") == 1 && q.GetFact(n"q307_2079") == 1 &&
      q.GetFact(n"q307_main_game_killed") == 1 && q.GetFact(n"q307_ep1_killed") == 1 &&
      q.GetFact(n"q305_johnny_scene_active") == 0 && q.GetFact(n"q115_point_of_no_return") == 0 &&
      q.GetFact(n"PTFRBASE_Suspended") == 0 && q.GetFact(n"PTFRTJ_Suspended") == 0;
  }
  public func Poll(expectedEpoch: Int32) -> Void {
    if !this.running || expectedEpoch != this.epoch || this.completed { return; }
    let game = this.GetGameInstance();
    let q = GameInstance.GetQuestsSystem(game);
    let p = GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(q) || !IsDefined(p) || !this.Eligible(q) {
      this.Schedule(expectedEpoch, 2.0);
      return;
    }
    if !IsDefined(this.cleanup) {
      this.cleanup = new PTFRTowerJournalCleanup();
      let prepared = this.cleanup.Prepare(p);
      if Equals(prepared,"NOT_READY") {
        this.cleanup = null;
        this.Schedule(expectedEpoch, 2.0);
        return;
      }
      if NotEquals(prepared,"PREPARED") {
        q.SetFact(n"PTFRTJA_State",2); // Refused without any journal write.
        this.completed = true;
        return;
      }
      let requested = this.cleanup.Apply(p);
      if NotEquals(requested,"REQUESTED") {
        q.SetFact(n"PTFRTJA_State",2);
        this.completed = true;
        return;
      }
      q.SetFact(n"PTFRTJA_State",3); // Native request in progress.
      this.Schedule(expectedEpoch, 0.5);
      return;
    }
    let status = this.cleanup.GetStatus();
    if Equals(status,"REQUESTED") {
      this.Schedule(expectedEpoch, 0.5);
      return;
    }
    q.SetFact(n"PTFRTJA_State",Equals(status,"VERIFIED_JOURNAL_STATE") ? 1 : 4);
    this.completed = true; // A partial or refused result never retries blindly.
  }
}

public class TowerJournalAutoTick extends DelayCallback {
  private let driver: wref<TowerJournalAuto>;
  private let epoch: Int32;
  public func Call() -> Void { if IsDefined(this.driver) { this.driver.Poll(this.epoch); } }
  public static func Create(driver: ref<TowerJournalAuto>, epoch: Int32) -> ref<TowerJournalAutoTick> {
    let tick = new TowerJournalAutoTick();
    tick.driver = driver; tick.epoch = epoch;
    return tick;
  }
}
