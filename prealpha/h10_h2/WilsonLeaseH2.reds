module PTFR.Housing

public abstract class WilsonLeaseH2 {
  public static func Reconcile(game: GameInstance) -> Void {
    let q = GameInstance.GetQuestsSystem(game);
    if !IsDefined(q) { return; }
    // S23 reserved Wilson BEFORE the original content-token wait. A retained
    // pre-entry waiter may hold that obsolete reservation indefinitely. H2's
    // native graph acquires it after those waits and marks the new acquisition
    // BEFORE setting QuestOwns, so this repair cannot release a current lease.
    if q.GetFact(n"PTFRH2_WV_LegacyReleased") != 0 || q.GetFact(n"PTFRH2_WV_LeaseRequested") != 0 ||
      q.GetFact(n"PTFRB0WV_QuestOwns") != 1 || q.GetFact(n"PTFRB0WV_Released") != 1 ||
      q.GetFact(n"PTFRB0WV_Ready") != 1 || q.GetFact(n"PTFRB0WV_Enabled") != 1 ||
      q.GetFact(n"PTFRB0WV_Near") != 0 || q.GetFact(n"PTFRB0WV_SpawnActionOut") != 0 ||
      q.GetFact(n"PTFRB0WV_ActorDistanceGate") != 0 || q.GetFact(n"PTFRB0WV_Excluded") != 0 ||
      q.GetFact(n"PTFRS23_MQ011_Ready") != 1 || q.GetFact(n"PTFRS23_MQ011_Issued") != 0 ||
      q.GetFact(n"PTFRS23_MQ011_Entered") != 0 || q.GetFact(n"PTFRS23_MQ011_Finished") != 0 ||
      q.GetFact(n"PTFRS23_MQ011_Fault") != 0 || q.GetFact(n"mq011_active") != 0 ||
      q.GetFact(n"q001_spawn_wilson_attention") != 0 || q.GetFact(n"q101_spawn_wilson_attention") != 0 ||
      q.GetFact(n"wat_lch_gunsmith_01_default_on") < 1 ||
      q.GetFact(n"PostTowerFreeRoamActive") != 1 || q.GetFact(n"PTFRPA2_Finished") != 1 ||
      q.GetFact(n"PTFRPA2_Fault") != 0 || q.GetFact(n"q307_done") != 1 ||
      q.GetFact(n"q307_finished") != 1 || q.GetFact(n"q307_2079") != 1 ||
      q.GetFact(n"q307_main_game_killed") != 1 || q.GetFact(n"q307_active") != 0 ||
      q.GetFact(n"q115_point_of_no_return") != 0 || q.GetFact(n"q305_johnny_scene_active") != 0 { return; }
    q.SetFact(n"PTFRH2_WV_LegacyReleased", 1);
    q.SetFact(n"PTFRB0WV_QuestOwns", 0);
    ModLog(n"PTFR_HousingH2", "Released obsolete pre-entry Wilson reservation; existing quest waiter preserved.");
  }
}
