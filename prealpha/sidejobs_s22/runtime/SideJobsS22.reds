module PTFR.SideJobsS22

import PTFR.RestrictionsR2.*
import PTFR.RestrictionsR3.*

// Current development policy is separate from S2's pre-ending certificate.
// This system writes only owned Permit facts; native adapters own all gameplay.
public struct SideJobSampleS22 {
  public let states: array<Int32>;
  public let facts: array<Int32>;
  public let valid: Bool;
  public let reason: String;
}

public class SideJobsS22 extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let warmup: Int32;
  private let previous: array<SideJobSampleS22>;

  public static func Get(game: GameInstance) -> ref<SideJobsS22> {
    return GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.SideJobsS22.SideJobsS22") as SideJobsS22;
  }
  private func Fact(name: String) -> Int32 {
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    return IsDefined(qs) ? qs.GetFactStr(name) : -2147483647;
  }
  private func Own(i: Int32, suffix: String) -> Int32 { return this.Fact(SideJobDataS22.Tag(i) + "_" + suffix); }
  private func Permit(i: Int32, allowed: Bool) -> Void {
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if !IsDefined(qs) || this.Own(i, "Issued") != 0 { return; }
    let value = allowed ? 1 : 0;
    let name = SideJobDataS22.Tag(i) + "_Permit";
    if qs.GetFactStr(name) != value { qs.SetFactStr(name, value); }
  }
  private func Common() -> Bool {
    if !IsDefined(GameInstance.GetQuestsSystem(this.GetGameInstance())) { return false; }
    let profile = ProfilePolicy.Get(this.GetGameInstance());
    return this.Fact("PostTowerFreeRoamActive") == 1 && this.Fact("PTFRP0_DR13") == 1 &&
      this.Fact("PTFRPA2_Finished") == 1 && this.Fact("PTFRPA2_Fault") == 0 &&
      this.Fact("q307_done") == 1 && this.Fact("q307_finished") == 1 && this.Fact("q307_2079") == 1 &&
      this.Fact("q307_main_game_killed") == 1 && this.Fact("q307_ep1_killed") == 1 &&
      this.Fact("q307_active") == 0 && this.Fact("q307_debug_reset") == 0 &&
      this.Fact("q115_point_of_no_return") == 0 && this.Fact("q305_johnny_scene_active") == 0 &&
      this.Fact("PTFRU9_Support_Issued") == 1 && this.Fact("PTFRU9_Support_Fault") == 0 &&
      IsDefined(profile) && profile.PTFRPAComplete() && !profile.PTFRPAFaulted();
  }
  private func Safe() -> Bool {
    let players = GameInstance.GetPlayerSystem(this.GetGameInstance());
    if !IsDefined(players) { return false; }
    let player = players.GetLocalPlayerMainGameObject() as PlayerPuppet;
    return IsDefined(player) && !player.IsDead() && !player.IsReplacer() && BodyPolicy.Safe(player);
  }
  private func OnAttach() -> Void { this.running = true; this.Restored(); }
  private func OnDetach() -> Void { this.running = false; this.epoch += 1; ArrayClear(this.previous); }
  public func Restored() -> Void {
    this.epoch += 1; this.warmup = 3; ArrayClear(this.previous);
    let i = 0; let empty: SideJobSampleS22;
    while i < SideJobDataS22.Count() {
      ArrayPush(this.previous, empty);
      // Never change a durable native Issued owner, including saved completion.
      if this.Own(i, "Issued") == 0 { this.Permit(i, false); }
      i += 1;
    }
    if this.running { this.Schedule(); }
  }
  private func Schedule() -> Void {
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(SideJobTickS22.Create(this, this.epoch), 1.0, false);
  }
  private func Read(i: Int32) -> SideJobSampleS22 {
    let sample: SideJobSampleS22;
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if !IsDefined(jm) || !IsDefined(qs) || jm.HasAnyDelayedStateChanges() { sample.reason = "Journal/facts unavailable or unsettled; state unknown."; return sample; }
    let paths = SideJobDataS22.Paths(i); let classes = SideJobDataS22.Classes(i);
    let first = SideJobDataS22.StatesA(i); let second = SideJobDataS22.StatesB(i);
    let names = SideJobDataS22.FactNames(i); let wanted = SideJobDataS22.FactValues(i);
    if ArraySize(paths) == 0 || ArraySize(paths) != ArraySize(classes) || ArraySize(paths) != ArraySize(first) || ArraySize(paths) != ArraySize(second) || ArraySize(names) != ArraySize(wanted) {
      sample.reason = "Adapter data shape mismatch; refused."; return sample;
    }
    let entry: wref<JournalEntry>; let state: Int32; let actual: Int32; let k = 0;
    sample.valid = true; sample.reason = "Native progress matches the bounded resume seam.";
    while k < ArraySize(paths) {
      entry = jm.GetEntryByString(paths[k], classes[k]);
      state = IsDefined(entry) ? EnumInt(jm.GetEntryState(entry)) : -1;
      ArrayPush(sample.states, state);
      if state != first[k] && state != second[k] {
        if sample.valid { sample.reason = "Progress protected: " + paths[k] + " state=" + ToString(state); }
        sample.valid = false;
      }
      k += 1;
    }
    k = 0;
    while k < ArraySize(names) {
      actual = qs.GetFactStr(names[k]); ArrayPush(sample.facts, actual);
      if actual != wanted[k] {
        if sample.valid { sample.reason = "Progress protected: " + names[k] + "=" + ToString(actual) + " expected=" + ToString(wanted[k]); }
        sample.valid = false;
      }
      k += 1;
    }
    if jm.HasAnyDelayedStateChanges() { sample.valid = false; sample.reason = "Journal changed during observation; waiting."; }
    return sample;
  }
  private func Same(a: SideJobSampleS22, b: SideJobSampleS22) -> Bool {
    if !a.valid || !b.valid || ArraySize(a.states) != ArraySize(b.states) || ArraySize(a.facts) != ArraySize(b.facts) { return false; }
    let i = 0;
    while i < ArraySize(a.states) { if a.states[i] != b.states[i] { return false; }; i += 1; }
    i = 0;
    while i < ArraySize(a.facts) { if a.facts[i] != b.facts[i] { return false; }; i += 1; }
    return true;
  }
  private func Ready(i: Int32) -> Bool {
    return this.running && this.warmup == 0 && this.Common() && this.Safe() &&
      this.Own(i, "Ready") == 1 && this.Own(i, "Issued") == 0 && this.Own(i, "Finished") == 0 && this.Own(i, "Fault") == 0;
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    this.Schedule();
    if this.warmup > 0 { this.warmup -= 1; }
    if ArraySize(this.previous) != SideJobDataS22.Count() { this.Restored(); return; }
    let i = 0; let current: SideJobSampleS22; let empty: SideJobSampleS22;
    while i < SideJobDataS22.Count() {
      if this.Own(i, "Issued") == 0 {
        if this.Ready(i) {
          current = this.Read(i);
          // Separate consecutive ticks, not two immediate reads of one frame.
          this.Permit(i, this.Same(this.previous[i], current) && this.Ready(i));
          this.previous[i] = current;
        } else {
          this.Permit(i, false); this.previous[i] = empty;
        }
      }
      i += 1;
    }
  }
  public func Status() -> String {
    let issued = 0; let permitted = 0; let i = 0;
    while i < SideJobDataS22.Count() {
      if this.Own(i, "Issued") == 1 { issued += 1; }
      if this.Own(i, "Permit") == 1 && this.Own(i, "Issued") == 0 { permitted += 1; }
      i += 1;
    }
    return "Side jobs S22: boundedAdapters=" + ToString(SideJobDataS22.Count()) + " permitted/issued=" + ToString(permitted) + "/" + ToString(issued) +
      " postTowerReady=" + ToString(this.Common()) + " | Current Failed/Inactive policy; progress retained; not certified pre-ending history. Issued is not gameplay proof. Unsupported stages remain unchanged.";
  }
  public func Inspect(id: String) -> String {
    let i = SideJobDataS22.Index(id);
    if i < 0 {
      if Equals(id, "mq306_dumpster") { return "No Easy Way Out: unsupported progress seam; native stage and item/choice/reward history remain unchanged. No generic restart applied."; }
      return "No S22 bounded adapter for " + id + "; no state changed.";
    }
    let sample = this.Read(i);
    return "Side job S22 " + SideJobDataS22.Title(i) + " [" + SideJobDataS22.ID(i) + "]: ready/permit/issued/finished=" + ToString(this.Own(i, "Ready")) + "/" +
      ToString(this.Own(i, "Permit")) + "/" + ToString(this.Own(i, "Issued")) + "/" + ToString(this.Own(i, "Finished")) + " fault=" + ToString(this.Own(i, "Fault")) +
      " currentMatch=" + ToString(sample.valid) + " safe=" + ToString(this.Safe()) + " | " + sample.reason + " Issued owners are not restarted.";
  }
}

public class SideJobTickS22 extends DelayCallback {
  private let owner: wref<SideJobsS22>;
  private let epoch: Int32;
  public static func Create(owner: ref<SideJobsS22>, epoch: Int32) -> ref<SideJobTickS22> {
    let tick = new SideJobTickS22(); tick.owner = owner; tick.epoch = epoch; return tick;
  }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}

@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void {
  wrappedMethod(gameInstance);
  let owner = SideJobsS22.Get(gameInstance);
  if IsDefined(owner) { owner.Restored(); }
}

public abstract class SideJobDataS22 {
  public static func Count() -> Int32 { return 4; }
  public static func ID(i: Int32) -> String {
    if i == 0 { return "mq025_psycho_brawl"; }
    if i == 1 { return "sq025_delamain"; }
    if i == 2 { return "q304_car_retrieval"; }
    if i == 3 { return "sq_q001_wakako"; }
    return "";
  }
  public static func Title(i: Int32) -> String {
    if i == 0 { return "Beat on the Brat"; }
    if i == 1 { return "Epistrophy"; }
    if i == 2 { return "Moving Heat"; }
    if i == 3 { return "The Gig"; }
    return "";
  }
  public static func Tag(i: Int32) -> String {
    if i == 0 { return "PTFRS22_MQ025"; }
    if i == 1 { return "PTFRS22_SQ025"; }
    if i == 2 { return "PTFRS22_Q304"; }
    if i == 3 { return "PTFRS22_SQ_Q001"; }
    return "";
  }
  public static func Index(id: String) -> Int32 {
    if Equals(id, "mq025_psycho_brawl") || Equals(id, "PTFRS22_MQ025") { return 0; }
    if Equals(id, "sq025_delamain") || Equals(id, "PTFRS22_SQ025") { return 1; }
    if Equals(id, "q304_car_retrieval") || Equals(id, "PTFRS22_Q304") { return 2; }
    if Equals(id, "sq_q001_wakako") || Equals(id, "PTFRS22_SQ_Q001") { return 3; }
    return -1;
  }
  public static func Paths(i: Int32) -> array<String> {
    if i == 0 { return SideJobDataS22.Paths0(); }
    if i == 1 { return SideJobDataS22.Paths1(); }
    if i == 2 { return SideJobDataS22.Paths2(); }
    if i == 3 { return SideJobDataS22.Paths3(); }
    let empty: array<String>; return empty;
  }
  public static func Paths0() -> array<String> { return ["quests/minor_quest/mq025_psycho_brawl", "quests/minor_quest/mq025_psycho_brawl/find_fights", "quests/minor_quest/mq025_psycho_brawl/find_fights/find_kabuki", "quests/minor_quest/mq025_psycho_brawl/find_fights/fin_arroyo", "quests/minor_quest/mq025_psycho_brawl/find_fights/find_glen", "quests/minor_quest/mq025_psycho_brawl/find_fights/find_club", "quests/minor_quest/mq025_psycho_brawl/find_fights/find_pacifica", "quests/minor_quest/mq025_02_kabuki", "quests/minor_quest/mq025_03_arroyo", "quests/minor_quest/mq025_05_glen", "quests/minor_quest/mq025_07_fight_club", "quests/minor_quest/mq025_06_pacifica"]; }
  public static func Paths1() -> array<String> { return ["quests/side_quest/sq025_delamain", "quests/side_quest/sq025_delamain/02_briefing/02_02_leave_garage", "quests/side_quest/sq025_delamain/02_briefing/02_01c_take_scanner", "quests/side_quest/sq025_delamain/02_briefing/02_01_follow_delamain", "quests/side_quest/sq025_delamain/02_briefing/02_02b_talk_delamain", "quests/side_quest/sq025_delamain/02_briefing/02_00_talk_delamain", "quests/side_quest/sq025_delamain/03_scan", "quests/side_quest/sq025_delamain/03_scan/03_02_scan_delamains", "quests/side_quest/sq025_delamain/04_scan_types/04_01_return", "quests/side_quest/sq025c02_sad", "quests/side_quest/sq025c03_mean", "quests/side_quest/sq025c07_suicidal", "quests/side_quest/sq025c01_angry", "quests/side_quest/sq025c04_manic", "quests/side_quest/sq025c05_scared", "quests/side_quest/sq025c06_mean"]; }
  public static func Paths2() -> array<String> { return ["ep1/quests/minor_quest/q304_car_retrieval", "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval", "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/01_reach_the_door", "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/02_use_the_panel_in_the_security_room_to_open_the_shutter", "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/03_get_to_the_car", "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/04_get_into_the_car", "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/05_connect_to_the_cars_onboard_computer_and_wipe_the_memory", "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/02_find_a_way_in", "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/01_reach_the_door1", "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/07_escape_with_the_car", "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/01_answer_to_ashlay_message", "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/03_wait_until_ashlay_opens_the_door", "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/04_dont_kill_or_alert_anyone", "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/01_wait_for_ashlay_message", "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/08_play_along", "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/05_clear_the_area", "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/09_go_back_to_the_car", "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/01_answer_to_ashlay_message2", "ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/05_clear_the_area_retro", "ep1/quests/minor_quest/q304_car_retrieval/description"]; }
  public static func Paths3() -> array<String> { return ["quests/side_quest/sq_q001_wakako", "quests/side_quest/sq_q001_wakako/wakako", "quests/side_quest/sq_q001_wakako/wakako/00_reward", "quests/side_quest/sq_q001_wakako/wakako/01_reward", "quests/side_quest/sq_q001_wakako/wakako/02_reward"]; }
  public static func Classes(i: Int32) -> array<String> {
    if i == 0 { return SideJobDataS22.Classes0(); }
    if i == 1 { return SideJobDataS22.Classes1(); }
    if i == 2 { return SideJobDataS22.Classes2(); }
    if i == 3 { return SideJobDataS22.Classes3(); }
    let empty: array<String>; return empty;
  }
  public static func Classes0() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuest", "gameJournalQuest", "gameJournalQuest", "gameJournalQuest", "gameJournalQuest"]; }
  public static func Classes1() -> array<String> { return ["gameJournalQuest", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuest", "gameJournalQuest", "gameJournalQuest", "gameJournalQuest", "gameJournalQuest", "gameJournalQuest", "gameJournalQuest"]; }
  public static func Classes2() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestDescription"]; }
  public static func Classes3() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective"]; }
  public static func StatesA(i: Int32) -> array<Int32> {
    if i == 0 { return SideJobDataS22.StatesA0(); }
    if i == 1 { return SideJobDataS22.StatesA1(); }
    if i == 2 { return SideJobDataS22.StatesA2(); }
    if i == 3 { return SideJobDataS22.StatesA3(); }
    let empty: array<Int32>; return empty;
  }
  public static func StatesA0() -> array<Int32> { return [4, 4, 4, 4, 4, 4, 1, 1, 1, 1, 1, 1]; }
  public static func StatesA1() -> array<Int32> { return [1, 3, 3, 3, 3, 3, 1, 1, 1, 3, 3, 3, 1, 1, 1, 1]; }
  public static func StatesA2() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1, 1, 1, 1, 1, 1, 1, 1, 2]; }
  public static func StatesA3() -> array<Int32> { return [1, 1, 3, 3, 1]; }
  public static func StatesB(i: Int32) -> array<Int32> {
    if i == 0 { return SideJobDataS22.StatesB0(); }
    if i == 1 { return SideJobDataS22.StatesB1(); }
    if i == 2 { return SideJobDataS22.StatesB2(); }
    if i == 3 { return SideJobDataS22.StatesB3(); }
    let empty: array<Int32>; return empty;
  }
  public static func StatesB0() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesB1() -> array<Int32> { return [4, 3, 3, 3, 3, 3, 4, 4, 1, 3, 3, 3, 4, 4, 4, 4]; }
  public static func StatesB2() -> array<Int32> { return [4, 4, 4, 1, 1, 1, 1, 1, 1, 1, 3, 1, 1, 1, 1, 1, 1, 1, 1, 2]; }
  public static func StatesB3() -> array<Int32> { return [4, 4, 3, 3, 4]; }
  public static func FactNames(i: Int32) -> array<String> {
    if i == 0 { return SideJobDataS22.FactNames0(); }
    if i == 1 { return SideJobDataS22.FactNames1(); }
    if i == 2 { return SideJobDataS22.FactNames2(); }
    if i == 3 { return SideJobDataS22.FactNames3(); }
    let empty: array<String>; return empty;
  }
  public static func FactNames0() -> array<String> { return ["mq025_quest_started", "mq025_trainer_skipped", "mq025_02_kabuki_active", "mq025_03_arroyo_active", "mq025_05_glen_active", "mq025_07_fight_club", "mq025_06_pacifica_active", "mq025_02_cheer_active", "mq025_02_chosen", "mq025_02_fight_active", "mq025_02_fight_started", "mq025_02_player_wins", "mq025_03_chosen", "mq025_03_fight_active", "mq025_03_fight_started", "mq025_03_player_wins", "mq025_05_chosen", "mq025_05_fight_active", "mq025_05_fight_started", "mq025_05_gave_money", "mq025_05_player_wins", "mq025_06_chosen", "mq025_06_ozob_fight_started", "mq025_06_ozob_player_wins", "mq025_06_pacifica_fight_active", "mq025_07_chosen", "mq025_07_fight_started", "mq025_07_fight_starts", "mq025_07_player_wins", "mq025_08_final_fight_active", "mq025_08_finale_player_wins", "mq025_08_finale_started", "mq025_buck_dead", "mq025_cash", "mq025_choose_fight", "mq025_done", "mq025_finale_started", "mq025_fist_fight_quest_start", "mq025_ozob_exploded", "mq025_razor_walks", "mq025_rhino_dead", "mq025_rhino_happy", "mq025_test_definition", "mq025_trainer_angry", "mq025_twin_01_down", "mq025_twin_02_down", "mq025_twins_player_down", "ozob_weakspot_nose_destroyed", "wwd_05_done"]; }
  public static func FactNames1() -> array<String> { return ["sq025_active", "sq025_briefing_scene_done", "sq025_scans_done", "sq025_sad_done", "sq025_mean_done", "sq025_suicidal_done", "sq025_angry_done", "sq025_manic_done", "sq025_scared_done", "sq025_deep_done", "sq025_angry_talk_start", "sq025_angry_talk_end", "sq025_manic_talk_start", "sq025_manic_talk_end", "sq025_manic_talk_disconnect", "sq025_scared_talk_start", "sq025_scared_talk_end", "sq025_scared_committed", "sq025_scared_crashed", "sq025_deep_active", "sq025_deep_av_running", "sq025_deep_vehicle_screen", "sq025_debug", "sq025_done", "sq025_clean", "sq025_failed", "sq025_failed_momentarily", "sq025_delamain_done", "sq025_disabled", "sq025_initialize_fail", "sq025_delamain_destroyed", "sq025_delamain_damaged", "sq025_delamain_damaged_counter", "sq025_resurgence_start", "sq025_scan_savelock", "holo_delamain_deep_vehicle_talk", "sq025_scan_angry_intro_done", "sq025_scan_manic_intro_done", "sq025_scan_scared_intro_done", "sq025_scan_deep_intro_done"]; }
  public static func FactNames2() -> array<String> { return ["q304_car_retrieval_accepted", "q304_car_retrieval_active", "q304_car_retrieval_car_entered", "q304_car_retrieval_car_ready2go", "q304_car_retrieval_combat_started", "q304_car_retrieval_done", "q304_car_retrieval_driver2_spawned", "q304_car_retrieval_finished", "q304_car_retrieval_got_spotted", "q304_car_retrieval_guards_killed", "q304_car_retrieval_inner_patrol_car_moving", "q304_car_retrieval_player_spotted", "q304_car_retrieval_player_spotted_2", "q304_car_retrieval_started", "q304_car_retrieval_truck_finished_ride", "q304_car_retrieval_truck_reached_inner", "q304_car_retrieval_van_reached_inner", "q304_car_retrival_on_top_of_truck", "q304_first_track_at_the_end_of_spline", "q304_retrofix_56524_on"]; }
  public static func FactNames3() -> array<String> { return ["sq_q001_done", "q001_wakako_reward_given"]; }
  public static func FactValues(i: Int32) -> array<Int32> {
    if i == 0 { return SideJobDataS22.FactValues0(); }
    if i == 1 { return SideJobDataS22.FactValues1(); }
    if i == 2 { return SideJobDataS22.FactValues2(); }
    if i == 3 { return SideJobDataS22.FactValues3(); }
    let empty: array<Int32>; return empty;
  }
  public static func FactValues0() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]; }
  public static func FactValues1() -> array<Int32> { return [1, 1, 3, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1]; }
  public static func FactValues2() -> array<Int32> { return [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]; }
  public static func FactValues3() -> array<Int32> { return [0, 1]; }
}

