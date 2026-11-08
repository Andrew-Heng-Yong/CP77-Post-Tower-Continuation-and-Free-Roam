module PTFR.SideJobsS23
import PTFR.LoadingCoverLC1.*
import PTFR.HistorySnapshotHS1.*

import PTFR.RestrictionsR2.*
import PTFR.RestrictionsR3.*
import PTFR.SideJobPilotS1.*

// Current development policy is separate from S2's pre-ending certificate.
// This system writes only owned Permit facts; native adapters own all gameplay.
public struct SideJobSampleS23 {
  public let states: array<Int32>;
  public let facts: array<Int32>;
  public let valid: Bool;
  public let reason: String;
}

public class SideJobsS23 extends ScriptableSystem {
  private let running: Bool;
  private let lc1Passes: Int32;
  private let epoch: Int32;
  private let warmup: Int32;
  private let legacyFreshPrevious: Bool;
  private let previous: array<SideJobSampleS23>;
  private let skippyPreviousPresent: Bool;
  private let skippyLastStatus: String;

  public static func Get(game: GameInstance) -> ref<SideJobsS23> {
    return GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.SideJobsS23.SideJobsS23") as SideJobsS23;
  }
  private func Fact(name: String) -> Int32 {
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    return IsDefined(qs) ? qs.GetFactStr(name) : -2147483647;
  }
  private func Own(i: Int32, suffix: String) -> Int32 { return this.Fact(SideJobDataS23.Tag(i) + "_" + suffix); }
  private func Permit(i: Int32, allowed: Bool) -> Void {
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if !IsDefined(qs) || this.Own(i, "Issued") != 0 { return; }
    let value = allowed && StartupCoverLC1.GameplayReleased(this.GetGameInstance()) ? 1 : 0;
    let name = SideJobDataS23.Tag(i) + "_Permit";
    if qs.GetFactStr(name) != value { qs.SetFactStr(name, value); }
  }
  private func Common() -> Bool {
    if !SnapshotStateHS1.StartupReady(this.GetGameInstance()) { return false; }
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
    this.lc1Passes=0;
    this.epoch += 1; this.warmup = 3; this.legacyFreshPrevious = false; this.skippyPreviousPresent = false; this.skippyLastStatus = ""; ArrayClear(this.previous);
    let i = 0; let empty: SideJobSampleS23;
    while i < SideJobDataS23.Count() {
      ArrayPush(this.previous, empty);
      // Never change a durable native Issued owner, including saved completion.
      if this.Own(i, "Issued") == 0 { this.Permit(i, false); }
      i += 1;
    }
    if this.running { this.Schedule(); }
  }
  private func Schedule() -> Void {
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(SideJobTickS23.Create(this, this.epoch), 1.0, false);
  }
  private func Read(i: Int32) -> SideJobSampleS23 {
    let sample: SideJobSampleS23;
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if !IsDefined(jm) || !IsDefined(qs) || jm.HasAnyDelayedStateChanges() { sample.reason = "Journal/facts unavailable or unsettled; state unknown."; return sample; }
    let paths = SideJobDataS23.Paths(i); let classes = SideJobDataS23.Classes(i);
    let first = SideJobDataS23.StatesA(i); let second = SideJobDataS23.StatesB(i);
    let names = SideJobDataS23.FactNames(i); let minimum = SideJobDataS23.FactMin(i); let maximum = SideJobDataS23.FactMax(i);
    if ArraySize(paths) == 0 || ArraySize(paths) != ArraySize(classes) || ArraySize(paths) != ArraySize(first) || ArraySize(paths) != ArraySize(second) || ArraySize(names) != ArraySize(minimum) || ArraySize(names) != ArraySize(maximum) {
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
      if actual < minimum[k] || actual > maximum[k] {
        if sample.valid { sample.reason = "Progress protected: " + names[k] + "=" + ToString(actual) + " expected=" + ToString(minimum[k]) + ".." + ToString(maximum[k]); }
        sample.valid = false;
      }
      k += 1;
    }
    if i == 13 && !SnapshotStateHS1.Admits(this.GetGameInstance(), SideJobDataS23.ID(i)) {
      sample.valid = false; sample.reason = "Earlier Brendan routes require the existing history gate.";
    }
    if i == 13 && SnapshotStateHS1.Admits(this.GetGameInstance(), SideJobDataS23.ID(i)) && SnapshotStateHS1.AdmitsBrendanFinalQR13(this.GetGameInstance(), paths, sample.states, names, sample.facts) {
      sample.valid = true;
      sample.reason = "Verified pre-ending earned final Theo continuation; native choices retained.";
    }
    if i == 13 && this.Own(i, "Entered") == 0 && this.ReadBrendanHandoff(paths, sample.states, names, sample.facts) {
      sample.valid = true;
      sample.reason = "Earned Spray Paint complete. Starting the native Coin Operated Boy handoff from its six-hour wait.";
    }
    if jm.HasAnyDelayedStateChanges() { sample.valid = false; sample.reason = "Journal changed during observation; waiting."; }
    return sample;
  }
  private func ReadBrendanHandoff(paths: array<String>, states: array<Int32>, names: array<String>, facts: array<Int32>) -> Bool {
    return BrendanFinalDataQR13.State(paths, states, "quests/minor_quest/mq037_brendan") == 1 &&
      BrendanFinalDataQR13.State(paths, states, "quests/minor_quest/mq037_brendan/mq037_brendan") == 1 &&
      BrendanFinalDataQR13.State(paths, states, "quests/minor_quest/mq037_brendan/mq037_brendan/01_go_to_service") == 1 &&
      BrendanFinalDataQR13.State(paths, states, "quests/minor_quest/mq037_brendan/mq037_brendan/01_go_to_service/description") == 1 &&
      BrendanFinalDataQR13.State(paths, states, "quests/minor_quest/mq037_brendan/mq037_brendan/02_find_brendan") == 1 &&
      BrendanFinalDataQR13.State(paths, states, "quests/minor_quest/mq037_brendan/mq037_brendan/02b_ask_clerk") == 1 &&
      BrendanFinalDataQR13.State(paths, states, "quests/minor_quest/mq037_brendan/mq037_brendan/02c_destroy_turret") == 1 &&
      BrendanFinalDataQR13.State(paths, states, "quests/minor_quest/mq037_brendan/mq037_brendan/03_talk_brendan") == 1 &&
      BrendanFinalDataQR13.State(paths, states, "quests/minor_quest/mq037_brendan/mq037_brendan/04_talk_theo") == 1 &&
      BrendanFinalDataQR13.State(paths, states, "quests/minor_quest/mq037_brendan_dumpster") == 3 &&
      BrendanFinalDataQR13.State(paths, states, "quests/minor_quest/mq037_brendan_dumpster/mq037_brendan_dumpster/00_push_dumpster") == 3 &&
      BrendanFinalDataQR13.State(paths, states, "quests/minor_quest/mq037_brendan_dumpster/mq037_brendan_dumpster/01_talk_brendan") == 3 &&
      BrendanFinalDataQR13.State(paths, states, "quests/minor_quest/mq037_brendan_hooligan001") == 3 &&
      BrendanFinalDataQR13.State(paths, states, "quests/minor_quest/mq037_brendan_hooligan001/mq037_brendan_hooligan/00_deal_with_the_hooligan") == 3 &&
      BrendanFinalDataQR13.State(paths, states, "quests/minor_quest/mq037_brendan_hooligan001/mq037_brendan_hooligan/01_talk_with_brendan") == 3 &&
      BrendanFinalDataQR13.Fact(names, facts, "mq037_brendan_introduced") == 1 &&
      BrendanFinalDataQR13.Fact(names, facts, "mq037_clerk_aggroed") == 0 &&
      BrendanFinalDataQR13.Fact(names, facts, "mq037_clerk_convinced") == 0 &&
      BrendanFinalDataQR13.Fact(names, facts, "mq037_done") == 0 &&
      BrendanFinalDataQR13.Fact(names, facts, "mq037_final_scene_active") == 0;
  }
  private func Same(a: SideJobSampleS23, b: SideJobSampleS23) -> Bool {
    if !a.valid || !b.valid || ArraySize(a.states) != ArraySize(b.states) || ArraySize(a.facts) != ArraySize(b.facts) { return false; }
    let i = 0;
    while i < ArraySize(a.states) { if a.states[i] != b.states[i] { return false; }; i += 1; }
    i = 0;
    while i < ArraySize(a.facts) { if a.facts[i] != b.facts[i] { return false; }; i += 1; }
    return true;
  }
  private func LegacyInactive() -> Bool {
    if !SnapshotStateHS1.Admits(this.GetGameInstance(),"mq005_alley") { return false; }
    // The original public RestoreFresh() remains the authoritative preflight;
    // this call-site guard only avoids invoking it on used/completed owners.
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    if !IsDefined(jm) || jm.HasAnyDelayedStateChanges() { return false; }
    let entry = jm.GetEntryByString("quests/minor_quest/mq005_alley", "gameJournalQuest");
    return IsDefined(entry) && EnumInt(jm.GetEntryState(entry)) == 1 &&
      this.Fact("PTFRS1_Ready") == 1 && this.Fact("PTFRS1_NativeRevision") == 1 &&
      this.Fact("PTFRS1_Request") == 0 && this.Fact("PTFRS1_Started") == 0 &&
      this.Fact("PTFRS1_OwnerFinished") == 0 && this.Fact("PTFRS1_Fault") == 0 &&
      this.Fact("mq005_done") == 0;
  }
  private func Ready(i: Int32) -> Bool {
    if i != 13 && !SnapshotStateHS1.Admits(this.GetGameInstance(),SideJobDataS23.ID(i)) { return false; }
    if (i == 1 || i == 8) && this.Fact("PTFRSKIP_Ambient_Claimed") == 1 && this.Fact("PTFRSKIP_Ambient_Stopped") == 0 { return false; }
    if (i == 1 || i == 8) && this.Fact("PTFRSKIP_SC3_Claimed") == 1 && this.Fact("PTFRSKIP_SC3_Stopped") == 0 { return false; }
    return this.running && this.warmup == 0 && this.Common() && this.Safe() &&
      this.Own(i, "Ready") == 1 && this.Own(i, "Issued") == 0 && this.Own(i, "Finished") == 0 && this.Own(i, "Fault") == 0;
  }
  private func SkippyOwned() -> Bool {
    let players = GameInstance.GetPlayerSystem(this.GetGameInstance());
    let tx = GameInstance.GetTransactionSystem(this.GetGameInstance());
    if !IsDefined(players) || !IsDefined(tx) { return false; }
    let player = players.GetLocalPlayerMainGameObject() as PlayerPuppet;
    return IsDefined(player) && tx.GetItemQuantity(player, ItemID.CreateQuery(t"Items.mq007_skippy")) >= 1;
  }
  private func SkippyAmbient() -> Void {
    let game = this.GetGameInstance();
    let qs = GameInstance.GetQuestsSystem(game);
    if !IsDefined(qs) { this.skippyPreviousPresent = false; return; }
    let players = GameInstance.GetPlayerSystem(game);
    let player = IsDefined(players) ? players.GetLocalPlayerMainGameObject() as PlayerPuppet : null;
    let tower = this.Fact("PostTowerFreeRoamActive") == 1 && this.Fact("PTFRP0_DR13") == 1 &&
      this.Fact("q307_done") == 1 && this.Fact("q307_finished") == 1 &&
      this.Fact("q307_2079") == 1 && this.Fact("q307_main_game_killed") == 1 &&
      this.Fact("q307_ep1_killed") == 1 && this.Fact("q307_active") == 0 &&
      this.Fact("PTFRBASE_Suspended") == 0 && this.Fact("q305_johnny_scene_active") == 0 &&
      this.Fact("q115_point_of_no_return") == 0;
    let safe = this.running && this.warmup == 0 && tower && IsDefined(player) &&
      !player.IsDead() && !player.IsReplacer() && StartupCoverLC1.GameplayReleased(game);
    let history = SnapshotStateHS1.StartupReady(game);
    let progressed = this.Fact("mq007_skippy_enemies_total") > 0 ||
      this.Fact("mq007_skippy_50_enemies_defeated") > 0 || this.Fact("mq007_skippy_owner_known") > 0;
    let owned = this.SkippyOwned();
    let freshWanted = safe && history && this.Own(1, "Ready") == 1 && this.Own(1, "Issued") == 0 &&
      SnapshotStateHS1.Admits(game, SideJobDataS23.ID(1)) && this.Read(1).valid;
    let resumeWanted = safe && history && this.Own(8, "Ready") == 1 && this.Own(8, "Issued") == 0 &&
      this.Fact("PTFRS23_MQ007_ModeTalkConfirmed") == 1 && this.Read(8).valid;
    let storyOwns = this.Own(1, "Issued") == 1 || this.Own(8, "Issued") == 1;

    // SC1's Stopped writer is followed by a Terminating output. Keep that
    // receipt: clearing it on an already-ended saved owner cannot produce a
    // new acknowledgement. For a still-active owner use its existing stop
    // watcher; for an unclaimed owner cancel Request and latch its stop guard.
    if safe {
      if this.Fact("PTFRSKIP_Ambient_Claimed") == 0 && this.Fact("PTFRSKIP_Ambient_Request") == 1 {
        qs.SetFactStr("PTFRSKIP_Ambient_Request", 0);
      }
      if this.Fact("PTFRSKIP_Ambient_Stop") == 0 {
        qs.SetFactStr("PTFRSKIP_Ambient_Stop", 1);
      }
    }
    let oldRetired = this.Fact("PTFRSKIP_Ambient_Stopped") == 1 ||
      (this.Fact("PTFRSKIP_Ambient_Claimed") == 0 && this.Fact("PTFRSKIP_Ambient_Entered") == 0 &&
       this.Fact("PTFRSKIP_Ambient_Request") == 0 && this.Fact("PTFRSKIP_Ambient_Stop") == 1);
    if this.Fact("PTFRSKIP_SC3_Claimed") == 1 && this.Fact("PTFRSKIP_SC3_Stopped") == 0 &&
      (freshWanted || resumeWanted || storyOwns) && this.Fact("PTFRSKIP_SC3_Stop") == 0 {
      qs.SetFactStr("PTFRSKIP_SC3_Stop", 1);
    }
    if this.Fact("PTFRSKIP_SC3_Claimed") == 0 && this.Fact("PTFRSKIP_SC3_Request") == 1 &&
      (freshWanted || resumeWanted || storyOwns) {
      qs.SetFactStr("PTFRSKIP_SC3_Request", 0);
    }
    // The new persistent owner waits for the exact native equipped-Skippy
    // condition and re-arms that wait after every normal native TurnOff.
    let eligible = safe && oldRetired && (progressed || (history && owned)) &&
      !freshWanted && !resumeWanted && !storyOwns && this.Fact("PTFRSKIP_SC3_Ready") == 1 &&
      this.Fact("PTFRSKIP_SC3_Claimed") == 0 && this.Fact("PTFRSKIP_SC3_Entered") == 0 &&
      this.Fact("PTFRSKIP_SC3_Stop") == 0 && this.Fact("PTFRSKIP_SC3_Stopped") == 0;
    if eligible && this.skippyPreviousPresent && this.Fact("PTFRSKIP_SC3_Request") == 0 {
      qs.SetFactStr("PTFRSKIP_SC3_Request", 1);
    }
    this.skippyPreviousPresent = eligible;
    let status = "tower/safe/history/progress/owned=" + ToString(tower) + "/" + ToString(safe) + "/" +
      ToString(history) + "/" + ToString(progressed) + "/" + ToString(owned) +
      " oldRetired=" + ToString(oldRetired) + " oldClaimed/Stop/Stopped=" +
      ToString(this.Fact("PTFRSKIP_Ambient_Claimed")) + "/" + ToString(this.Fact("PTFRSKIP_Ambient_Stop")) +
      "/" + ToString(this.Fact("PTFRSKIP_Ambient_Stopped")) + " fresh/resume/story=" +
      ToString(freshWanted) + "/" + ToString(resumeWanted) + "/" + ToString(storyOwns) +
      " ready/request/claimed/entered/active/stop/stopped=" + ToString(this.Fact("PTFRSKIP_SC3_Ready")) +
      "/" + ToString(this.Fact("PTFRSKIP_SC3_Request")) + "/" + ToString(this.Fact("PTFRSKIP_SC3_Claimed")) +
      "/" + ToString(this.Fact("PTFRSKIP_SC3_Entered")) + "/" + ToString(this.Fact("PTFRSKIP_SC3_Active")) +
      "/" + ToString(this.Fact("PTFRSKIP_SC3_Stop")) + "/" + ToString(this.Fact("PTFRSKIP_SC3_Stopped"));
    if NotEquals(status, this.skippyLastStatus) {
      this.skippyLastStatus = status;
      ModLog(n"PTFR_SkippySC3", status);
    }
  }
  public func LC1SetupReady() -> Bool { return this.lc1Passes>=2 && this.running && this.warmup==0 && SnapshotStateHS1.StartupReady(this.GetGameInstance()) && IsDefined(ProfilePolicy.Get(this.GetGameInstance())) && ProfilePolicy.Get(this.GetGameInstance()).PTFRPAComplete() && this.Fact("PTFRPA2_Finished")==1; }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    this.Schedule();
    if this.warmup > 0 { this.warmup -= 1; }
    if ArraySize(this.previous) != SideJobDataS23.Count() { this.Restored(); return; }
    // Arm the EXISTING bounded Only Pain adapter; never create another owner.
    // Its untouched-journal/scene/POI checks and saved one-shot state stay intact.
    let pilot = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.SideJobPilotS1.SideJobPilotS1") as SideJobPilotS1;
    let fresh = this.warmup == 0 && this.Common() && this.Safe() && IsDefined(pilot) && this.LegacyInactive();
    if fresh && this.legacyFreshPrevious && StartupCoverLC1.GameplayReleased(this.GetGameInstance()) { pilot.RestoreFresh(); }
    this.legacyFreshPrevious = fresh;
    this.SkippyAmbient();
    let i = 0; let current: SideJobSampleS23; let empty: SideJobSampleS23;
    while i < SideJobDataS23.Count() {
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
      if this.running && this.warmup==0 && SnapshotStateHS1.StartupReady(this.GetGameInstance()) && IsDefined(ProfilePolicy.Get(this.GetGameInstance())) && ProfilePolicy.Get(this.GetGameInstance()).PTFRPAComplete() && this.Fact("PTFRPA2_Finished")==1 { this.lc1Passes=Min(this.lc1Passes+1,2); } else { this.lc1Passes=0; }
  }
  public func Status() -> String {
    let issued = 0; let permitted = 0; let i = 0;
    while i < SideJobDataS23.Count() {
      if this.Own(i, "Issued") == 1 { issued += 1; }
      if this.Own(i, "Permit") == 1 && this.Own(i, "Issued") == 0 { permitted += 1; }
      i += 1;
    }
    return "Side jobs S23: boundedAdapters=" + ToString(SideJobDataS23.Count()) + " permitted/issued=" + ToString(permitted) + "/" + ToString(issued) +
      " postTowerReady=" + ToString(this.Common()) + " | New activation Inactive-only; existing issued progress preserved; progress retained; not certified pre-ending history. Issued is not gameplay proof. Unsupported stages remain unchanged.";
  }
  public func Inspect(id: String) -> String {
    let i = SideJobDataS23.Index(id);
    if i < 0 {
      return "No S23 bounded adapter for " + id + "; no state changed.";
    }
    let sample = this.Read(i);
    return "Side job S23 " + SideJobDataS23.Title(i) + " [" + SideJobDataS23.ID(i) + "]: ready/permit/issued/finished=" + ToString(this.Own(i, "Ready")) + "/" +
      ToString(this.Own(i, "Permit")) + "/" + ToString(this.Own(i, "Issued")) + "/" + ToString(this.Own(i, "Finished")) + " fault=" + ToString(this.Own(i, "Fault")) +
      " currentMatch=" + ToString(sample.valid) + " safe=" + ToString(this.Safe()) + " | " + sample.reason + " Issued owners are not restarted.";
  }
}

public class SideJobTickS23 extends DelayCallback {
  private let owner: wref<SideJobsS23>;
  private let epoch: Int32;
  public static func Create(owner: ref<SideJobsS23>, epoch: Int32) -> ref<SideJobTickS23> {
    let tick = new SideJobTickS23(); tick.owner = owner; tick.epoch = epoch; return tick;
  }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}

@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void {
  wrappedMethod(gameInstance);
  let owner = SideJobsS23.Get(gameInstance);
  if IsDefined(owner) { owner.Restored(); }
}

public abstract class SideJobDataS23 {
  public static func Count() -> Int32 { return 24; }
  public static func ID(i: Int32) -> String {
    if i == 0 { return "mq024_sandra"; }
    if i == 1 { return "mq007_smartgun"; }
    if i == 2 { return "mq035_ozob"; }
    if i == 3 { return "mq012_stud"; }
    if i == 4 { return "mq002_veterans"; }
    if i == 5 { return "mq021_guide"; }
    if i == 6 { return "mq041_corpo"; }
    if i == 7 { return "mq044_jakes_vehicle"; }
    if i == 8 { return "mq007_smartgun"; }
    if i == 9 { return "mq013_punks"; }
    if i == 10 { return "mq030_melisa"; }
    if i == 11 { return "mq011_wilson"; }
    if i == 12 { return "mq038_neweridentity"; }
    if i == 13 { return "mq037_brendan"; }
    if i == 14 { return "mq049_edgerunners"; }
    if i == 15 { return "mq026_conspiracy"; }
    if i == 16 { return "mq306_dumpster"; }
    if i == 17 { return "q304_splinter_stash"; }
    if i == 18 { return "wst_ep1_11_bill_meeting"; }
    if i == 19 { return "wst_ep1_05"; }
    if i == 20 { return "wst_ep1_04"; }
    if i == 21 { return "sts_ep1_08_steven_meeting_night_city"; }
    if i == 22 { return "mq046_cave_vehicle"; }
    if i == 23 { return "mq047_ad_vehicle"; }
    return "";
  }
  public static func Title(i: Int32) -> String {
    if i == 0 { return "Full Disclosure"; }
    if i == 1 { return "Machine Gun"; }
    if i == 2 { return "Send in the Clowns"; }
    if i == 3 { return "Burning Desire/Night Moves"; }
    if i == 4 { return "Gun Music"; }
    if i == 5 { return "Fortunate Son"; }
    if i == 6 { return "War Pigs"; }
    if i == 7 { return "Sex on Wheels"; }
    if i == 8 { return "Machine Gun - confirmed post-mode-conversation resume"; }
    if i == 9 { return "A Day in the Life"; }
    if i == 10 { return "Bullets"; }
    if i == 11 { return "Shoot to Thrill"; }
    if i == 12 { return "Big in Japan"; }
    if i == 13 { return "Coin Operated Boy"; }
    if i == 14 { return "Over the Edge"; }
    if i == 15 { return "The Prophet's Song"; }
    if i == 16 { return "No Easy Way Out"; }
    if i == 17 { return "Voodoo Treasure"; }
    if i == 18 { return "New Person, Same Old Mistakes"; }
    if i == 19 { return "Go Your Own Way"; }
    if i == 20 { return "Addicted to Chaos"; }
    if i == 21 { return "The Show Must Go On"; }
    if i == 22 { return "Murk Man Returns Again Once More Forever"; }
    if i == 23 { return "Dressed to Kill"; }
    return "";
  }
  public static func Tag(i: Int32) -> String {
    if i == 0 { return "PTFRS23_MQ024"; }
    if i == 1 { return "PTFRS23_MQ007"; }
    if i == 2 { return "PTFRS23_MQ035"; }
    if i == 3 { return "PTFRS23_MQ012"; }
    if i == 4 { return "PTFRS23_MQ002"; }
    if i == 5 { return "PTFRS23_MQ021"; }
    if i == 6 { return "PTFRS23_MQ041"; }
    if i == 7 { return "PTFRS23_MQ044"; }
    if i == 8 { return "PTFRS23_MQ007_RESUME"; }
    if i == 9 { return "PTFRS23_MQ013"; }
    if i == 10 { return "PTFRS23_MQ030"; }
    if i == 11 { return "PTFRS23_MQ011"; }
    if i == 12 { return "PTFRS23_MQ038"; }
    if i == 13 { return "PTFRS23_MQ037"; }
    if i == 14 { return "PTFRS23_MQ049"; }
    if i == 15 { return "PTFRS23_MQ026"; }
    if i == 16 { return "PTFRS23_MQ306"; }
    if i == 17 { return "PTFRS23_VOODOO"; }
    if i == 18 { return "PTFRS23_BILL"; }
    if i == 19 { return "PTFRS23_HASAN"; }
    if i == 20 { return "PTFRS23_RINDER"; }
    if i == 21 { return "PTFRS23_STEVEN"; }
    if i == 22 { return "PTFRS23_MQ046"; }
    if i == 23 { return "PTFRS23_MQ047"; }
    return "";
  }
  public static func Index(id: String) -> Int32 {
    if Equals(id, "mq024_sandra") || Equals(id, "PTFRS23_MQ024") { return 0; }
    if Equals(id, "mq007_smartgun") || Equals(id, "PTFRS23_MQ007") { return 1; }
    if Equals(id, "mq035_ozob") || Equals(id, "PTFRS23_MQ035") { return 2; }
    if Equals(id, "mq012_stud") || Equals(id, "PTFRS23_MQ012") { return 3; }
    if Equals(id, "mq002_veterans") || Equals(id, "PTFRS23_MQ002") { return 4; }
    if Equals(id, "mq021_guide") || Equals(id, "PTFRS23_MQ021") { return 5; }
    if Equals(id, "mq041_corpo") || Equals(id, "PTFRS23_MQ041") { return 6; }
    if Equals(id, "mq044_jakes_vehicle") || Equals(id, "PTFRS23_MQ044") { return 7; }
    if Equals(id, "mq007_smartgun") || Equals(id, "PTFRS23_MQ007_RESUME") { return 8; }
    if Equals(id, "mq013_punks") || Equals(id, "PTFRS23_MQ013") { return 9; }
    if Equals(id, "mq030_melisa") || Equals(id, "PTFRS23_MQ030") { return 10; }
    if Equals(id, "mq011_wilson") || Equals(id, "PTFRS23_MQ011") { return 11; }
    if Equals(id, "mq038_neweridentity") || Equals(id, "PTFRS23_MQ038") { return 12; }
    if Equals(id, "mq037_brendan") || Equals(id, "PTFRS23_MQ037") { return 13; }
    if Equals(id, "mq049_edgerunners") || Equals(id, "PTFRS23_MQ049") { return 14; }
    if Equals(id, "mq026_conspiracy") || Equals(id, "PTFRS23_MQ026") { return 15; }
    if Equals(id, "mq306_dumpster") || Equals(id, "PTFRS23_MQ306") { return 16; }
    if Equals(id, "q304_splinter_stash") || Equals(id, "PTFRS23_VOODOO") { return 17; }
    if Equals(id, "wst_ep1_11_bill_meeting") || Equals(id, "PTFRS23_BILL") { return 18; }
    if Equals(id, "wst_ep1_05") || Equals(id, "PTFRS23_HASAN") { return 19; }
    if Equals(id, "wst_ep1_04") || Equals(id, "PTFRS23_RINDER") { return 20; }
    if Equals(id, "sts_ep1_08_steven_meeting_night_city") || Equals(id, "PTFRS23_STEVEN") { return 21; }
    if Equals(id, "mq046_cave_vehicle") || Equals(id, "PTFRS23_MQ046") { return 22; }
    if Equals(id, "mq047_ad_vehicle") || Equals(id, "PTFRS23_MQ047") { return 23; }
    return -1;
  }
  public static func Paths(i: Int32) -> array<String> {
    if i == 0 { return SideJobDataS23.Paths0(); }
    if i == 1 { return SideJobDataS23.Paths1(); }
    if i == 2 { return SideJobDataS23.Paths2(); }
    if i == 3 { return SideJobDataS23.Paths3(); }
    if i == 4 { return SideJobDataS23.Paths4(); }
    if i == 5 { return SideJobDataS23.Paths5(); }
    if i == 6 { return SideJobDataS23.Paths6(); }
    if i == 7 { return SideJobDataS23.Paths7(); }
    if i == 8 { return SideJobDataS23.Paths8(); }
    if i == 9 { return SideJobDataS23.Paths9(); }
    if i == 10 { return SideJobDataS23.Paths10(); }
    if i == 11 { return SideJobDataS23.Paths11(); }
    if i == 12 { return SideJobDataS23.Paths12(); }
    if i == 13 { return SideJobDataS23.Paths13(); }
    if i == 14 { return SideJobDataS23.Paths14(); }
    if i == 15 { return SideJobDataS23.Paths15(); }
    if i == 16 { return SideJobDataS23.Paths16(); }
    if i == 17 { return SideJobDataS23.Paths17(); }
    if i == 18 { return SideJobDataS23.Paths18(); }
    if i == 19 { return SideJobDataS23.Paths19(); }
    if i == 20 { return SideJobDataS23.Paths20(); }
    if i == 21 { return SideJobDataS23.Paths21(); }
    if i == 22 { return SideJobDataS23.Paths22(); }
    if i == 23 { return SideJobDataS23.Paths23(); }
    let empty: array<String>; return empty;
  }
  public static func Paths0() -> array<String> { return ["quests/minor_quest/mq024_sandra", "quests/minor_quest/mq024_sandra/description", "quests/minor_quest/mq024_sandra/mq024_sandra", "quests/minor_quest/mq024_sandra/mq024_sandra/01_find_data_carrier", "quests/minor_quest/mq024_sandra/mq024_sandra/02_call_sandra", "quests/minor_quest/mq024_sandra/mq024_sandra/02_call_sandra/description", "quests/minor_quest/mq024_sandra/mq024_sandra/03_meet_sandra", "quests/minor_quest/mq024_sandra/mq024_sandra/04_defeat_sandra"]; }
  public static func Paths1() -> array<String> { return ["quests/minor_quest/mq007_smartgun", "quests/minor_quest/mq007_smartgun/mq007_smartgun", "quests/minor_quest/mq007_smartgun/mq007_smartgun/01_deliver_skippy", "quests/minor_quest/mq007_smartgun/mq007_smartgun/01_deliver_skippy/description", "quests/minor_quest/mq007_smartgun/mq007_smartgun/02_put_skippy_down", "quests/minor_quest/mq007_smartgun/mq007_smartgun/03_talk_to_regina"]; }
  public static func Paths2() -> array<String> { return ["quests/minor_quest/mq035_ozob", "quests/minor_quest/mq035_ozob/mq035_ozob", "quests/minor_quest/mq035_ozob/mq035_ozob/00_call_ozob", "quests/minor_quest/mq035_ozob/mq035_ozob/00_call_ozob/description", "quests/minor_quest/mq035_ozob/mq035_ozob/02_meet_ozob", "quests/minor_quest/mq035_ozob/mq035_ozob/02_meet_ozob/description", "quests/minor_quest/mq035_ozob/mq035_ozob/03_drive_to_casino", "quests/minor_quest/mq035_ozob/mq035_ozob/04_wait", "quests/minor_quest/mq035_ozob/mq035_ozob/05_drive_to_ambush", "quests/minor_quest/mq035_ozob/mq035_ozob/06_kill_enemies", "quests/minor_quest/mq035_ozob/mq035_ozob/07_talk_ozob", "quests/minor_quest/mq035_ozob/mq035_ozob/honk", "quests/minor_quest/mq035_ozob/mq035_ozob/return_to_car", "quests/minor_quest/mq035_ozob/mq035_ozob/wait_for_ozob_to_get_in_car"]; }
  public static func Paths3() -> array<String> { return ["quests/minor_quest/mq012_stud", "quests/minor_quest/mq012_stud/00_stud", "quests/minor_quest/mq012_stud/00_stud/000_lose_heat", "quests/minor_quest/mq012_stud/00_stud/00_find_out", "quests/minor_quest/mq012_stud/00_stud/00_find_out/description_new", "quests/minor_quest/mq012_stud/00_stud/01_talk_man", "quests/minor_quest/mq012_stud/00_stud/01b_help", "quests/minor_quest/mq012_stud/00_stud/02_get_car", "quests/minor_quest/mq012_stud/00_stud/02b_return_to_car", "quests/minor_quest/mq012_stud/00_stud/03_drive_ripperdoc", "quests/minor_quest/mq012_stud/00_stud/04_stop_at_ripper", "quests/minor_quest/mq012_stud/00_stud/05_wait_for_call", "quests/minor_quest/mq012_stud/00_stud/06_talk_to_stud"]; }
  public static func Paths4() -> array<String> { return ["quests/minor_quest/mq002_veterans", "quests/minor_quest/mq002_veterans/mq002_veterans", "quests/minor_quest/mq002_veterans/mq002_veterans/01_intro", "quests/minor_quest/mq002_veterans/mq002_veterans/01_intro/mq002_description", "quests/minor_quest/mq002_veterans/mq002_veterans/02_deal", "quests/minor_quest/mq002_veterans/mq002_veterans/03_fight", "quests/minor_quest/mq002_veterans/mq002_veterans/04_summary"]; }
  public static func Paths5() -> array<String> { return ["quests/minor_quest/mq021_guide", "quests/minor_quest/mq021_guide/mq021_guide", "quests/minor_quest/mq021_guide/mq021_guide/04_meeting", "quests/minor_quest/mq021_guide/mq021_guide/04_meeting/mq021_description", "quests/minor_quest/mq021_guide/mq021_guide/05_participate_meeting", "quests/minor_quest/mq021_guide/mq021_guide/06_defend", "quests/minor_quest/mq021_guide/mq021_guide/07_1_kill_doctor", "quests/minor_quest/mq021_guide/mq021_guide/07_2_get_suitcase", "quests/minor_quest/mq021_guide/mq021_guide/07_confront_doctor", "quests/minor_quest/mq021_guide/mq021_guide/08_outcome", "quests/minor_quest/mq021_guide/mq021_guide/09_ending", "quests/minor_quest/mq021_guide/mq021_guide/10_ending_wait", "quests/minor_quest/mq021_guide/mq021_guide/11_ending_read"]; }
  public static func Paths6() -> array<String> { return ["quests/minor_quest/mq041_corpo", "quests/minor_quest/mq041_corpo/corpo", "quests/minor_quest/mq041_corpo/corpo/01_find_the_briefcase", "quests/minor_quest/mq041_corpo/corpo/01_find_the_briefcase/description", "quests/minor_quest/mq041_corpo/corpo/01a_talk_with_johnny", "quests/minor_quest/mq041_corpo/corpo/01a_talk_with_johnny1", "quests/minor_quest/mq041_corpo/corpo/01b_lift_the_dumpster", "quests/minor_quest/mq041_corpo/corpo/02_open_the_briefcase", "quests/minor_quest/mq041_corpo/corpo/03_talk_with_stranger", "quests/minor_quest/mq041_corpo/corpo/04_confront_frank"]; }
  public static func Paths7() -> array<String> { return ["quests/minor_quest/mq044_jakes_vehicle", "quests/minor_quest/mq044_jakes_vehicle/mq044_jakes_vehicle", "quests/minor_quest/mq044_jakes_vehicle/mq044_jakes_vehicle/01_reach_garage", "quests/minor_quest/mq044_jakes_vehicle/mq044_jakes_vehicle/01_reach_garage/brief", "quests/minor_quest/mq044_jakes_vehicle/mq044_jakes_vehicle/03_get_in_car", "quests/minor_quest/mq044_jakes_vehicle/mq044_jakes_vehicle/04_leave_area"]; }
  public static func Paths8() -> array<String> { return ["quests/minor_quest/mq007_smartgun", "quests/minor_quest/mq007_smartgun/mq007_smartgun", "quests/minor_quest/mq007_smartgun/mq007_smartgun/01_deliver_skippy", "quests/minor_quest/mq007_smartgun/mq007_smartgun/01_deliver_skippy/description", "quests/minor_quest/mq007_smartgun/mq007_smartgun/02_put_skippy_down", "quests/minor_quest/mq007_smartgun/mq007_smartgun/03_talk_to_regina"]; }
  public static func Paths9() -> array<String> { return ["quests/minor_quest/mq013_punks", "quests/minor_quest/mq013_punks/00_punks", "quests/minor_quest/mq013_punks/00_punks/00_talk_shopkeep", "quests/minor_quest/mq013_punks/00_punks/00_talk_shopkeep/description", "quests/minor_quest/mq013_punks/00_punks/01_decide", "quests/minor_quest/mq013_punks/00_punks/02_deal_with_punks", "quests/minor_quest/mq013_punks/00_punks/03_defeat_punks", "quests/minor_quest/mq013_punks/00_punks/04_talk_shopkeep"]; }
  public static func Paths10() -> array<String> { return ["quests/minor_quest/mq030_melisa", "quests/minor_quest/mq030_melisa/01_melisa", "quests/minor_quest/mq030_melisa/01_melisa/01_defeat_psycho", "quests/minor_quest/mq030_melisa/01_melisa/01_defeat_psycho/description", "quests/minor_quest/mq030_melisa/01_melisa/02_approach_max_tac", "quests/minor_quest/mq030_melisa/01_melisa/03_sit_down", "quests/minor_quest/mq030_melisa/01_melisa/04_talk_to_melisa"]; }
  public static func Paths11() -> array<String> { return ["quests/minor_quest/mq011_wilson", "quests/minor_quest/mq011_wilson/00_wilson", "quests/minor_quest/mq011_wilson/00_wilson/00_talk_wilson", "quests/minor_quest/mq011_wilson/00_wilson/00_talk_wilson/description", "quests/minor_quest/mq011_wilson/00_wilson/01_go_to_wilson", "quests/minor_quest/mq011_wilson/00_wilson/02_talk_to_wilson", "quests/minor_quest/mq011_wilson/00_wilson/03_enter_range", "quests/minor_quest/mq011_wilson/00_wilson/04_listen_instructions", "quests/minor_quest/mq011_wilson/01_competition", "quests/minor_quest/mq011_wilson/01_competition/000_wait", "quests/minor_quest/mq011_wilson/01_competition/000b_wait", "quests/minor_quest/mq011_wilson/01_competition/00_shoot", "quests/minor_quest/mq011_wilson/01_competition/00b_ready", "quests/minor_quest/mq011_wilson/01_competition/01_go_wilson", "quests/minor_quest/mq011_wilson/01_competition/01b_talk_to_wilson", "quests/minor_quest/mq011_wilson/01_competition/02_grab_prize", "quests/minor_quest/mq011_wilson/description"]; }
  public static func Paths12() -> array<String> { return ["quests/minor_quest/mq038_neweridentity", "quests/minor_quest/mq038_neweridentity/mq038_neweridentity", "quests/minor_quest/mq038_neweridentity/mq038_neweridentity/01_fishing_village", "quests/minor_quest/mq038_neweridentity/mq038_neweridentity/01_fishing_village/mq038_description", "quests/minor_quest/mq038_neweridentity/mq038_neweridentity/02_find_dumpster", "quests/minor_quest/mq038_neweridentity/mq038_neweridentity/02b_call_darryl", "quests/minor_quest/mq038_neweridentity/mq038_neweridentity/03_recover_body", "quests/minor_quest/mq038_neweridentity/mq038_neweridentity/04_deliver_to_car", "quests/minor_quest/mq038_neweridentity/mq038_neweridentity/05_hide_trunk", "quests/minor_quest/mq038_neweridentity/mq038_neweridentity/06_deliver_northside", "quests/minor_quest/mq038_neweridentity/mq038_neweridentity/06_enter_car", "quests/minor_quest/mq038_neweridentity/mq038_neweridentity/08_talk_cargo", "quests/minor_quest/mq038_neweridentity/mq038_neweridentity/09_leave_car"]; }
  public static func Paths13() -> array<String> { return ["quests/minor_quest/mq037_brendan", "quests/minor_quest/mq037_brendan/mq037_brendan", "quests/minor_quest/mq037_brendan/mq037_brendan/01_go_to_service", "quests/minor_quest/mq037_brendan/mq037_brendan/01_go_to_service/description", "quests/minor_quest/mq037_brendan/mq037_brendan/02_find_brendan", "quests/minor_quest/mq037_brendan/mq037_brendan/02b_ask_clerk", "quests/minor_quest/mq037_brendan/mq037_brendan/02c_destroy_turret", "quests/minor_quest/mq037_brendan/mq037_brendan/03_talk_brendan", "quests/minor_quest/mq037_brendan/mq037_brendan/04_talk_theo", "quests/minor_quest/mq037_brendan_dumpster", "quests/minor_quest/mq037_brendan_dumpster/mq037_brendan_dumpster", "quests/minor_quest/mq037_brendan_dumpster/mq037_brendan_dumpster/00_push_dumpster", "quests/minor_quest/mq037_brendan_dumpster/mq037_brendan_dumpster/00_push_dumpster/description", "quests/minor_quest/mq037_brendan_dumpster/mq037_brendan_dumpster/01_talk_brendan", "quests/minor_quest/mq037_brendan_hooligan001", "quests/minor_quest/mq037_brendan_hooligan001/mq037_brendan_hooligan", "quests/minor_quest/mq037_brendan_hooligan001/mq037_brendan_hooligan/00_deal_with_the_hooligan", "quests/minor_quest/mq037_brendan_hooligan001/mq037_brendan_hooligan/01_talk_with_brendan"]; }
  public static func Paths14() -> array<String> { return ["quests/minor_quest/mq049_edgerunners", "quests/minor_quest/mq049_edgerunners/01_el_captian", "quests/minor_quest/mq049_edgerunners/01_el_captian/01_text_capitan", "quests/minor_quest/mq049_edgerunners/01_el_captian/02_wait", "quests/minor_quest/mq049_edgerunners/02_falco", "quests/minor_quest/mq049_edgerunners/02_falco/01_respond_to_falco", "quests/minor_quest/mq049_edgerunners/03_gift", "quests/minor_quest/mq049_edgerunners/03_gift/02_pick_up_gift", "quests/minor_quest/mq049_edgerunners/desc"]; }
  public static func Paths15() -> array<String> { return ["quests/minor_quest/mq026_conspiracy", "quests/minor_quest/mq026_conspiracy/stash", "quests/minor_quest/mq026_conspiracy/stash/01_01_find_stash", "quests/minor_quest/mq026_conspiracy/stash/01_01_find_stash/mq026_desc", "quests/minor_quest/mq026_conspiracy/stash/01_01b_return_factory", "quests/minor_quest/mq026_conspiracy/stash/01_02_find_stash", "quests/minor_quest/mq026_conspiracy/stash/01_02a_suspicious", "quests/minor_quest/mq026_conspiracy/stash/01_03_loot_corpse", "quests/minor_quest/mq026_conspiracy/stash/01_04_confront", "quests/minor_quest/mq026_conspiracy/stash/01_05_hide", "quests/minor_quest/mq026_conspiracy/stash/01_05a_talk", "quests/minor_quest/mq026_conspiracy/stash/01_05b_wait", "quests/minor_quest/mq026_conspiracy/stash/01_06b_take_out_carrier", "quests/minor_quest/mq026_conspiracy/stash/01_07_return", "quests/minor_quest/mq026_conspiracy/stash/01_07b_disciple", "quests/minor_quest/mq026_conspiracy/stash/01_08_what", "quests/minor_quest/mq026_conspiracy/stash/01_09_johnny"]; }
  public static func Paths16() -> array<String> { return ["ep1/quests/minor_quest/mq306_dumpster", "ep1/quests/minor_quest/mq306_dumpster/01_intro", "ep1/quests/minor_quest/mq306_dumpster/01_intro/01_find_aaron", "ep1/quests/minor_quest/mq306_dumpster/01_intro/01_read_coach_message", "ep1/quests/minor_quest/mq306_dumpster/01_intro/01_wait_for_match", "ep1/quests/minor_quest/mq306_dumpster/01_intro/01a_talk_to_bookie", "ep1/quests/minor_quest/mq306_dumpster/01_intro/01b_wait_for_fight", "ep1/quests/minor_quest/mq306_dumpster/01_intro/02_talk_aaron", "ep1/quests/minor_quest/mq306_dumpster/01_intro/02a_consider_talking_to_aaron", "ep1/quests/minor_quest/mq306_dumpster/01_intro/03_text_viktor", "ep1/quests/minor_quest/mq306_dumpster/02_scav_base", "ep1/quests/minor_quest/mq306_dumpster/02_scav_base/01_meet_aaron", "ep1/quests/minor_quest/mq306_dumpster/02_scav_base/01a_wait_for_aaron", "ep1/quests/minor_quest/mq306_dumpster/02_scav_base/02_follow_aaron", "ep1/quests/minor_quest/mq306_dumpster/02_scav_base/02_talk_aaron", "ep1/quests/minor_quest/mq306_dumpster/02_scav_base/03_clinic", "ep1/quests/minor_quest/mq306_dumpster/02_scav_base/04_combat", "ep1/quests/minor_quest/mq306_dumpster/03_ripperdoc", "ep1/quests/minor_quest/mq306_dumpster/03_ripperdoc/01_talk_damir", "ep1/quests/minor_quest/mq306_dumpster/03_ripperdoc/02_wait", "ep1/quests/minor_quest/mq306_dumpster/03_ripperdoc/03_talk_angie", "ep1/quests/minor_quest/mq306_dumpster/03_ripperdoc/04_combat", "ep1/quests/minor_quest/mq306_dumpster/03_ripperdoc/05_talk_aaron", "ep1/quests/minor_quest/mq306_dumpster/03_ripperdoc/06_leave_base", "ep1/quests/minor_quest/mq306_dumpster/03_ripperdoc/07a_wait_news_aaron", "ep1/quests/minor_quest/mq306_dumpster/03_ripperdoc/07b_wait_news_angie", "ep1/quests/minor_quest/mq306_dumpster/04a_aaron_meeting", "ep1/quests/minor_quest/mq306_dumpster/04a_aaron_meeting/01_reply_text", "ep1/quests/minor_quest/mq306_dumpster/04a_aaron_meeting/01a_read_aaron_message", "ep1/quests/minor_quest/mq306_dumpster/04a_aaron_meeting/02_meet_aaron", "ep1/quests/minor_quest/mq306_dumpster/04a_aaron_meeting/03a_talk_bartender", "ep1/quests/minor_quest/mq306_dumpster/04a_aaron_meeting/03b_talk_angie", "ep1/quests/minor_quest/mq306_dumpster/04a_aaron_meeting/03c_talk_aaron", "ep1/quests/minor_quest/mq306_dumpster/04a_aaron_meeting/04a_alley", "ep1/quests/minor_quest/mq306_dumpster/04a_aaron_meeting/04b_combat", "ep1/quests/minor_quest/mq306_dumpster/04a_aaron_meeting/05_talk_johnny", "ep1/quests/minor_quest/mq306_dumpster/04b_angie_meeting", "ep1/quests/minor_quest/mq306_dumpster/04b_angie_meeting/01_reply_text", "ep1/quests/minor_quest/mq306_dumpster/04b_angie_meeting/02_meet_angie", "ep1/quests/minor_quest/mq306_dumpster/04b_angie_meeting/03talk_to_angie", "ep1/quests/minor_quest/mq306_dumpster/description", "ep1/contacts/aaron/mq306/01a_aaron_dive", "ep1/contacts/aaron/mq306/02a_ch_dive_reply", "ep1/contacts/aaron/mq306/03a_aaron_disgraced", "ep1/contacts/aaron/mq306/03a_aaron_disgraced_reply", "ep1/contacts/aaron/mq306/03b_aaron_abroad"]; }
  public static func Paths17() -> array<String> { return ["ep1/quests/minor_quest/q304_splinter_stash", "ep1/quests/minor_quest/q304_splinter_stash/01_stash", "ep1/quests/minor_quest/q304_splinter_stash/01_stash/01_find_stash", "ep1/quests/minor_quest/q304_splinter_stash/desc"]; }
  public static func Paths18() -> array<String> { return ["ep1/quests/minor_quest/wst_ep1_11_bill_meeting", "ep1/quests/minor_quest/wst_ep1_11_bill_meeting/description", "ep1/quests/minor_quest/wst_ep1_11_bill_meeting/wst_ep1_11", "ep1/quests/minor_quest/wst_ep1_11_bill_meeting/wst_ep1_11/meet_bill", "ep1/quests/minor_quest/wst_ep1_11_bill_meeting/wst_ep1_11/read_message", "ep1/quests/minor_quest/wst_ep1_11_bill_meeting/wst_ep1_11/talk_bill"]; }
  public static func Paths19() -> array<String> { return ["ep1/quests/minor_quest/wst_ep1_05", "ep1/quests/minor_quest/wst_ep1_05/description", "ep1/quests/minor_quest/wst_ep1_05/wst_ep1_05", "ep1/quests/minor_quest/wst_ep1_05/wst_ep1_05/go_to_hasan_apartment", "ep1/quests/minor_quest/wst_ep1_05/wst_ep1_05/read_message_from_hands", "ep1/quests/minor_quest/wst_ep1_05/wst_ep1_05/speak_with_hasan", "ep1/quests/minor_quest/wst_ep1_05/wst_ep1_05/take_the_gun"]; }
  public static func Paths20() -> array<String> { return ["ep1/quests/minor_quest/wst_ep1_04", "ep1/quests/minor_quest/wst_ep1_04/description", "ep1/quests/minor_quest/wst_ep1_04/wst_ep1_04", "ep1/quests/minor_quest/wst_ep1_04/wst_ep1_04/enter_the_code", "ep1/quests/minor_quest/wst_ep1_04/wst_ep1_04/go_to_rinders_garage", "ep1/quests/minor_quest/wst_ep1_04/wst_ep1_04/loot_the_box"]; }
  public static func Paths21() -> array<String> { return ["ep1/quests/minor_quest/sts_ep1_08_steven_meeting_night_city", "ep1/quests/minor_quest/sts_ep1_08_steven_meeting_night_city/steven_default_night_city", "ep1/quests/minor_quest/sts_ep1_08_steven_meeting_night_city/steven_default_night_city/read_message_from_steven", "ep1/quests/minor_quest/sts_ep1_08_steven_meeting_night_city/steven_default_night_city/steven_meeting", "ep1/quests/minor_quest/sts_ep1_08_steven_meeting_night_city/steven_default_night_city/talk_with_steven", "ep1/quests/minor_quest/sts_ep1_08_steven_meeting_night_city/steven_default_night_city_description", "ep1/contacts/steven_santos/sts_ep1_08/biomonitor_destroyed_meeting_invitation"]; }
  public static func Paths22() -> array<String> { return ["quests/minor_quest/mq046_cave_vehicle", "quests/minor_quest/mq046_cave_vehicle/mq046_container", "quests/minor_quest/mq046_cave_vehicle/mq046_container/get_inside_car", "quests/minor_quest/mq046_cave_vehicle/mq046_container/investigate", "quests/minor_quest/mq046_cave_vehicle/mq046_desc"]; }
  public static func Paths23() -> array<String> { return ["quests/minor_quest/mq047_ad_vehicle", "quests/minor_quest/mq047_ad_vehicle/mq046_set", "quests/minor_quest/mq047_ad_vehicle/mq046_set/get_inside_car", "quests/minor_quest/mq047_ad_vehicle/mq046_set/investigate", "quests/minor_quest/mq047_ad_vehicle/mq047_desc"]; }
  public static func Classes(i: Int32) -> array<String> {
    if i == 0 { return SideJobDataS23.Classes0(); }
    if i == 1 { return SideJobDataS23.Classes1(); }
    if i == 2 { return SideJobDataS23.Classes2(); }
    if i == 3 { return SideJobDataS23.Classes3(); }
    if i == 4 { return SideJobDataS23.Classes4(); }
    if i == 5 { return SideJobDataS23.Classes5(); }
    if i == 6 { return SideJobDataS23.Classes6(); }
    if i == 7 { return SideJobDataS23.Classes7(); }
    if i == 8 { return SideJobDataS23.Classes8(); }
    if i == 9 { return SideJobDataS23.Classes9(); }
    if i == 10 { return SideJobDataS23.Classes10(); }
    if i == 11 { return SideJobDataS23.Classes11(); }
    if i == 12 { return SideJobDataS23.Classes12(); }
    if i == 13 { return SideJobDataS23.Classes13(); }
    if i == 14 { return SideJobDataS23.Classes14(); }
    if i == 15 { return SideJobDataS23.Classes15(); }
    if i == 16 { return SideJobDataS23.Classes16(); }
    if i == 17 { return SideJobDataS23.Classes17(); }
    if i == 18 { return SideJobDataS23.Classes18(); }
    if i == 19 { return SideJobDataS23.Classes19(); }
    if i == 20 { return SideJobDataS23.Classes20(); }
    if i == 21 { return SideJobDataS23.Classes21(); }
    if i == 22 { return SideJobDataS23.Classes22(); }
    if i == 23 { return SideJobDataS23.Classes23(); }
    let empty: array<String>; return empty;
  }
  public static func Classes0() -> array<String> { return ["gameJournalQuest", "gameJournalQuestDescription", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestDescription", "gameJournalQuestObjective", "gameJournalQuestObjective"]; }
  public static func Classes1() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestDescription", "gameJournalQuestObjective", "gameJournalQuestObjective"]; }
  public static func Classes2() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestDescription", "gameJournalQuestObjective", "gameJournalQuestDescription", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective"]; }
  public static func Classes3() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestDescription", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective"]; }
  public static func Classes4() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestDescription", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective"]; }
  public static func Classes5() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestDescription", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective"]; }
  public static func Classes6() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestDescription", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective"]; }
  public static func Classes7() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestDescription", "gameJournalQuestObjective", "gameJournalQuestObjective"]; }
  public static func Classes8() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestDescription", "gameJournalQuestObjective", "gameJournalQuestObjective"]; }
  public static func Classes9() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestDescription", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective"]; }
  public static func Classes10() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestDescription", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective"]; }
  public static func Classes11() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestDescription", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestDescription"]; }
  public static func Classes12() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestDescription", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective"]; }
  public static func Classes13() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestDescription", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestDescription", "gameJournalQuestObjective", "gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestObjective"]; }
  public static func Classes14() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestDescription"]; }
  public static func Classes15() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestDescription", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective"]; }
  public static func Classes16() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestDescription", "gameJournalPhoneMessage", "gameJournalPhoneChoiceGroup", "gameJournalPhoneMessage", "gameJournalPhoneChoiceGroup", "gameJournalPhoneMessage"]; }
  public static func Classes17() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestDescription"]; }
  public static func Classes18() -> array<String> { return ["gameJournalQuest", "gameJournalQuestDescription", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective"]; }
  public static func Classes19() -> array<String> { return ["gameJournalQuest", "gameJournalQuestDescription", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective"]; }
  public static func Classes20() -> array<String> { return ["gameJournalQuest", "gameJournalQuestDescription", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective"]; }
  public static func Classes21() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestDescription", "gameJournalPhoneMessage"]; }
  public static func Classes22() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestDescription"]; }
  public static func Classes23() -> array<String> { return ["gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestObjective", "gameJournalQuestDescription"]; }
  public static func StatesA(i: Int32) -> array<Int32> {
    if i == 0 { return SideJobDataS23.StatesA0(); }
    if i == 1 { return SideJobDataS23.StatesA1(); }
    if i == 2 { return SideJobDataS23.StatesA2(); }
    if i == 3 { return SideJobDataS23.StatesA3(); }
    if i == 4 { return SideJobDataS23.StatesA4(); }
    if i == 5 { return SideJobDataS23.StatesA5(); }
    if i == 6 { return SideJobDataS23.StatesA6(); }
    if i == 7 { return SideJobDataS23.StatesA7(); }
    if i == 8 { return SideJobDataS23.StatesA8(); }
    if i == 9 { return SideJobDataS23.StatesA9(); }
    if i == 10 { return SideJobDataS23.StatesA10(); }
    if i == 11 { return SideJobDataS23.StatesA11(); }
    if i == 12 { return SideJobDataS23.StatesA12(); }
    if i == 13 { return SideJobDataS23.StatesA13(); }
    if i == 14 { return SideJobDataS23.StatesA14(); }
    if i == 15 { return SideJobDataS23.StatesA15(); }
    if i == 16 { return SideJobDataS23.StatesA16(); }
    if i == 17 { return SideJobDataS23.StatesA17(); }
    if i == 18 { return SideJobDataS23.StatesA18(); }
    if i == 19 { return SideJobDataS23.StatesA19(); }
    if i == 20 { return SideJobDataS23.StatesA20(); }
    if i == 21 { return SideJobDataS23.StatesA21(); }
    if i == 22 { return SideJobDataS23.StatesA22(); }
    if i == 23 { return SideJobDataS23.StatesA23(); }
    let empty: array<Int32>; return empty;
  }
  public static func StatesA0() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesA1() -> array<Int32> { return [1, 1, 1, 1, 1, 1]; }
  public static func StatesA2() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesA3() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesA4() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesA5() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesA6() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesA7() -> array<Int32> { return [1, 1, 1, 1, 1, 1]; }
  public static func StatesA8() -> array<Int32> { return [1, 1, 1, 1, 1, 1]; }
  public static func StatesA9() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesA10() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesA11() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesA12() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesA13() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesA14() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesA15() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesA16() -> array<Int32> { return [1, 4, 3, 3, 1, 3, 3, 3, 1, 1, 4, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 1, 3, 3, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 1, 1, 1]; }
  public static func StatesA17() -> array<Int32> { return [1, 1, 1, 1]; }
  public static func StatesA18() -> array<Int32> { return [1, 1, 1, 1, 1, 1]; }
  public static func StatesA19() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesA20() -> array<Int32> { return [1, 1, 1, 1, 1, 1]; }
  public static func StatesA21() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesA22() -> array<Int32> { return [1, 1, 1, 1, 1]; }
  public static func StatesA23() -> array<Int32> { return [1, 1, 1, 1, 1]; }
  public static func StatesB(i: Int32) -> array<Int32> {
    if i == 0 { return SideJobDataS23.StatesB0(); }
    if i == 1 { return SideJobDataS23.StatesB1(); }
    if i == 2 { return SideJobDataS23.StatesB2(); }
    if i == 3 { return SideJobDataS23.StatesB3(); }
    if i == 4 { return SideJobDataS23.StatesB4(); }
    if i == 5 { return SideJobDataS23.StatesB5(); }
    if i == 6 { return SideJobDataS23.StatesB6(); }
    if i == 7 { return SideJobDataS23.StatesB7(); }
    if i == 8 { return SideJobDataS23.StatesB8(); }
    if i == 9 { return SideJobDataS23.StatesB9(); }
    if i == 10 { return SideJobDataS23.StatesB10(); }
    if i == 11 { return SideJobDataS23.StatesB11(); }
    if i == 12 { return SideJobDataS23.StatesB12(); }
    if i == 13 { return SideJobDataS23.StatesB13(); }
    if i == 14 { return SideJobDataS23.StatesB14(); }
    if i == 15 { return SideJobDataS23.StatesB15(); }
    if i == 16 { return SideJobDataS23.StatesB16(); }
    if i == 17 { return SideJobDataS23.StatesB17(); }
    if i == 18 { return SideJobDataS23.StatesB18(); }
    if i == 19 { return SideJobDataS23.StatesB19(); }
    if i == 20 { return SideJobDataS23.StatesB20(); }
    if i == 21 { return SideJobDataS23.StatesB21(); }
    if i == 22 { return SideJobDataS23.StatesB22(); }
    if i == 23 { return SideJobDataS23.StatesB23(); }
    let empty: array<Int32>; return empty;
  }
  public static func StatesB0() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesB1() -> array<Int32> { return [1, 1, 1, 1, 1, 1]; }
  public static func StatesB2() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesB3() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesB4() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesB5() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesB6() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesB7() -> array<Int32> { return [1, 1, 1, 1, 1, 1]; }
  public static func StatesB8() -> array<Int32> { return [1, 1, 1, 1, 1, 1]; }
  public static func StatesB9() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesB10() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesB11() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesB12() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesB13() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesB14() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesB15() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesB16() -> array<Int32> { return [1, 4, 3, 3, 1, 3, 3, 3, 1, 1, 4, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 1, 3, 3, 3, 1, 4, 4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 3, 3, 1, 1, 1]; }
  public static func StatesB17() -> array<Int32> { return [1, 1, 1, 1]; }
  public static func StatesB18() -> array<Int32> { return [1, 1, 1, 1, 1, 1]; }
  public static func StatesB19() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesB20() -> array<Int32> { return [1, 1, 1, 1, 1, 1]; }
  public static func StatesB21() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1]; }
  public static func StatesB22() -> array<Int32> { return [1, 1, 1, 1, 1]; }
  public static func StatesB23() -> array<Int32> { return [1, 1, 1, 1, 1]; }
  public static func FactNames(i: Int32) -> array<String> {
    if i == 0 { return SideJobDataS23.FactNames0(); }
    if i == 1 { return SideJobDataS23.FactNames1(); }
    if i == 2 { return SideJobDataS23.FactNames2(); }
    if i == 3 { return SideJobDataS23.FactNames3(); }
    if i == 4 { return SideJobDataS23.FactNames4(); }
    if i == 5 { return SideJobDataS23.FactNames5(); }
    if i == 6 { return SideJobDataS23.FactNames6(); }
    if i == 7 { return SideJobDataS23.FactNames7(); }
    if i == 8 { return SideJobDataS23.FactNames8(); }
    if i == 9 { return SideJobDataS23.FactNames9(); }
    if i == 10 { return SideJobDataS23.FactNames10(); }
    if i == 11 { return SideJobDataS23.FactNames11(); }
    if i == 12 { return SideJobDataS23.FactNames12(); }
    if i == 13 { return SideJobDataS23.FactNames13(); }
    if i == 14 { return SideJobDataS23.FactNames14(); }
    if i == 15 { return SideJobDataS23.FactNames15(); }
    if i == 16 { return SideJobDataS23.FactNames16(); }
    if i == 17 { return SideJobDataS23.FactNames17(); }
    if i == 18 { return SideJobDataS23.FactNames18(); }
    if i == 19 { return SideJobDataS23.FactNames19(); }
    if i == 20 { return SideJobDataS23.FactNames20(); }
    if i == 21 { return SideJobDataS23.FactNames21(); }
    if i == 22 { return SideJobDataS23.FactNames22(); }
    if i == 23 { return SideJobDataS23.FactNames23(); }
    let empty: array<String>; return empty;
  }
  public static func FactNames0() -> array<String> { return ["mq024_active", "mq024_combat_sandra", "mq024_done", "mq024_hook_taken", "mq024_sandra_opened_door", "mq024_test_with_sts", "mq024_hacked_data_carrier"]; }
  public static func FactNames1() -> array<String> { return ["mq007_done", "mq007_debug", "mq007_opt_A", "mq007_skippy_50_enemies_defeated", "mq007_skippy_50_enemies_killed_and_stoneColdKiller", "mq007_skippy_50_enemies_maimed", "mq007_skippy_enemies_lethal", "mq007_skippy_enemies_non_lethal", "mq007_skippy_enemies_total", "mq007_skippy_owner_known", "mq007_skippy_re_acquiring_done", "mq007_skippy_goes_emo", "mq007_skippy_stash"]; }
  public static func FactNames2() -> array<String> { return ["mq035_car_ride", "mq035_done", "mq035_drive_chat", "mq035_ow_despawn"]; }
  public static func FactNames3() -> array<String> { return ["mq012_arrived_in_car", "mq012_can_stop_at_ripperdoc", "mq012_debug", "mq012_disable_blockade", "mq012_disabled_truck_blockade", "mq012_done", "mq012_kids_past_danger", "mq012_stud_dead", "mq012_stud_stop_pose", "mq012_active"]; }
  public static func FactNames4() -> array<String> { return ["mq002_deal_broken_combat", "mq002_deal_proceeded", "mq002_done", "mq002_escaped", "mq002_escaped_combat", "mq002_sniper_noticed", "mq002_active"]; }
  public static func FactNames5() -> array<String> { return ["mq021_active", "mq021_bob_ending_approached", "mq021_done", "mq021_happy_ending"]; }
  public static func FactNames6() -> array<String> { return ["mq041_corpo_started", "mq041_debug", "mq041_done"]; }
  public static func FactNames7() -> array<String> { return ["mq044_done", "mq044_started", "mq_044_started_in_main"]; }
  public static func FactNames8() -> array<String> { return ["mq007_done", "mq007_debug", "mq007_opt_A", "mq007_skippy_50_enemies_defeated", "mq007_skippy_50_enemies_killed_and_stoneColdKiller", "mq007_skippy_50_enemies_maimed", "mq007_skippy_enemies_lethal", "mq007_skippy_enemies_non_lethal", "mq007_skippy_enemies_total", "mq007_skippy_owner_known", "mq007_skippy_re_acquiring_done", "mq007_skippy_goes_emo", "mq007_skippy_stash", "mq007_interrupt_skippy_dialogue", "mq007_rapid_interrupt", "PTFRS23_MQ007_ModeTalkConfirmed", "PTFRS23_MQ007_Issued"]; }
  public static func FactNames9() -> array<String> { return ["mq013_active", "mq013_dealt_with_punks_somehow", "mq013_done", "mq013_far_away", "mq013_punch", "mq013_punk_combat_shopkeeper", "mq013_punk_combat_start", "mq013_punks_dead_before_scene", "mq013_punks_defeated", "sq024_mq013_active_timeskipped", "std_arr_foodshop_03_dead", "std_arr_foodshop_03_default_on", "std_arr_foodshop_03_discount_on"]; }
  public static func FactNames10() -> array<String> { return ["cct_dtn_cloth_01_default_on", "mq030_active", "mq030_done", "mq030_failed", "mq030_kill_scene", "mq030_maxtac_arrived", "mq030_zane_grateful", "mq030_zane_met"]; }
  public static func FactNames11() -> array<String> { return ["holo_wilson_calls_v_end_activate", "holo_wilson_calls_v_start_activate", "mq011_active", "mq011_done", "mq011_shooting_over", "wat_lch_gunsmith_01_default_on", "wilson_shooting_range_left"]; }
  public static func FactNames12() -> array<String> { return ["mq038_active", "mq038_deliver_inactive", "mq038_done", "mq038_dumpster_opened", "mq038_fake_01_opened", "mq038_fake_02_opened", "mq038_hide_inactive"]; }
  public static func FactNames13() -> array<String> { return ["hey_rey_techstore_01_default_on", "mq037_01_05Sure", "mq037_brendan_introduced", "mq037_clerk_aggroed", "mq037_clerk_convinced", "mq037_done", "mq037_final_scene_active", "mq037_kill_token_block_loop", "mq037_post_girl_scene_on", "mq037_vandal_painted_brendan"]; }
  public static func FactNames14() -> array<String> { return ["mq049_done", "mq049_falco_done", "mq049_finished", "mq049_jacket_looted", "mq049_reyes_distance_comment", "mq049_started"]; }
  public static func FactNames15() -> array<String> { return ["mq018_begged_once", "mq018_ramble_pause", "mq018_select", "mq026_active", "mq026_big_donation", "mq026_car_chase", "mq026_chip", "mq026_conspiracies", "mq026_cyberspace_done", "mq026_cyberspace_start", "mq026_death_stop_content_lock", "mq026_debug", "mq026_disturbed", "mq026_done", "mq026_eyes_done", "mq026_eyes_start", "mq026_first_conspiracy_done", "mq026_handover", "mq026_is_rambling", "mq026_lilith_done", "mq026_lookat_loop", "mq026_mib_fighting", "mq026_mib_ready", "mq026_nomads_beaten", "mq026_nomads_done", "mq026_nomads_start", "mq026_preach_skipped", "mq026_prophet_beaten", "mq026_reptilians_done", "mq026_reptilians_start", "mq026_skip_first_ramble", "mq026_small_donation", "mq026_started", "mq026_stop_preach", "mq026_take_chip", "mq026_vampire_done", "mq026_vampire_start", "mq027_50_prophet", "mq027_5_prophet", "PTFRS25_MQ026_FRESH_Issued"]; }
  public static func FactNames16() -> array<String> { return ["mq306_active", "mq306_started", "mq306_quest_accepted", "mq306_done", "mq306_finished", "mq306_animals_dead", "mq306_fight_clean", "mq306_dive", "mq306_intimidate", "mq306_truth", "mq306_aaron_intimidate_end", "mq306_aaron_path", "mq306_angie_path", "mq306_offer_declined", "mq306_bartender_done", "mq306_03_angie_turned", "mq306_clinic_reached", "mq306_leaving_ripper", "mq306_testdef"]; }
  public static func FactNames17() -> array<String> { return []; }
  public static func FactNames18() -> array<String> { return ["wst_ep1_11_hotdog_finished", "wst_ep1_11_ncpd_start", "wst_ep1_11_ncpd_finished", "bill_default_on", "sts_ep1_10_debug_fact_1111", "ws_ep1_11_chicken_test_journal_start", "PTFRB0S4BILL_Enabled", "PTFRB0S4BILL_OwnerActive", "PTFRB0S4BILL_QuestOwns", "sts_ep1_10_finished"]; }
  public static func FactNames19() -> array<String> { return ["wst_ep1_05_active", "wst_ep1_05_start", "wst_ep1_05_finished", "wst_ep1_05_gun_taken", "wst_ep1_05_gun_reveal", "sts_ep1_04_blueprints_hasan", "hasan_default_on", "sts_ep1_04_blueprints_corpo", "sts_ep1_04_mr_hands_holo_convinced"]; }
  public static func FactNames20() -> array<String> { return ["wst_ep1_04_active", "wst_ep1_04_start", "wst_ep1_04_finished", "wst_ep1_04_gun_taken", "sts_ep1_03_dogtag_obtained"]; }
  public static func FactNames21() -> array<String> { return ["sts_ep1_08_biomonitor_ana", "steven_santos_default_on", "PTFRU9_sts_ep1_08_ParentEntered", "PTFRU9_sts_ep1_08_Started", "sts_ep1_08_finished"]; }
  public static func FactNames22() -> array<String> { return ["ma_bls_ina_se1_40_start", "ma_bls_ina_se1_40_finished"]; }
  public static func FactNames23() -> array<String> { return ["ma_bls_ina_se1_44_start", "ma_bls_ina_se1_44_finished"]; }
  public static func FactMin(i: Int32) -> array<Int32> {
    if i == 0 { return SideJobDataS23.FactMin0(); }
    if i == 1 { return SideJobDataS23.FactMin1(); }
    if i == 2 { return SideJobDataS23.FactMin2(); }
    if i == 3 { return SideJobDataS23.FactMin3(); }
    if i == 4 { return SideJobDataS23.FactMin4(); }
    if i == 5 { return SideJobDataS23.FactMin5(); }
    if i == 6 { return SideJobDataS23.FactMin6(); }
    if i == 7 { return SideJobDataS23.FactMin7(); }
    if i == 8 { return SideJobDataS23.FactMin8(); }
    if i == 9 { return SideJobDataS23.FactMin9(); }
    if i == 10 { return SideJobDataS23.FactMin10(); }
    if i == 11 { return SideJobDataS23.FactMin11(); }
    if i == 12 { return SideJobDataS23.FactMin12(); }
    if i == 13 { return SideJobDataS23.FactMin13(); }
    if i == 14 { return SideJobDataS23.FactMin14(); }
    if i == 15 { return SideJobDataS23.FactMin15(); }
    if i == 16 { return SideJobDataS23.FactMin16(); }
    if i == 17 { return SideJobDataS23.FactMin17(); }
    if i == 18 { return SideJobDataS23.FactMin18(); }
    if i == 19 { return SideJobDataS23.FactMin19(); }
    if i == 20 { return SideJobDataS23.FactMin20(); }
    if i == 21 { return SideJobDataS23.FactMin21(); }
    if i == 22 { return SideJobDataS23.FactMin22(); }
    if i == 23 { return SideJobDataS23.FactMin23(); }
    let empty: array<Int32>; return empty;
  }
  public static func FactMin0() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 0]; }
  public static func FactMin1() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]; }
  public static func FactMin2() -> array<Int32> { return [0, 0, 0, 0]; }
  public static func FactMin3() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]; }
  public static func FactMin4() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 0]; }
  public static func FactMin5() -> array<Int32> { return [0, 0, 0, 0]; }
  public static func FactMin6() -> array<Int32> { return [0, 0, 0]; }
  public static func FactMin7() -> array<Int32> { return [0, 0, 0]; }
  public static func FactMin8() -> array<Int32> { return [0, 0, 0, 1, 0, 1, 11, 51, 95, 0, 0, 0, 0, 0, 0, 1, 0]; }
  public static func FactMin9() -> array<Int32> { return [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]; }
  public static func FactMin10() -> array<Int32> { return [1, 0, 0, 0, 0, 0, 0, 0]; }
  public static func FactMin11() -> array<Int32> { return [0, 0, 0, 0, 0, 1, 0]; }
  public static func FactMin12() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 0]; }
  public static func FactMin13() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]; }
  public static func FactMin14() -> array<Int32> { return [0, 0, 0, 0, 0, 0]; }
  public static func FactMin15() -> array<Int32> { return [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0]; }
  public static func FactMin16() -> array<Int32> { return [1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0]; }
  public static func FactMin17() -> array<Int32> { return []; }
  public static func FactMin18() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 0, 0, 0, 1]; }
  public static func FactMin19() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 1, 1, 1]; }
  public static func FactMin20() -> array<Int32> { return [0, 0, 0, 0, 1]; }
  public static func FactMin21() -> array<Int32> { return [0, 0, 0, 0, 1]; }
  public static func FactMin22() -> array<Int32> { return [0, 0]; }
  public static func FactMin23() -> array<Int32> { return [0, 0]; }
  public static func FactMax(i: Int32) -> array<Int32> {
    if i == 0 { return SideJobDataS23.FactMax0(); }
    if i == 1 { return SideJobDataS23.FactMax1(); }
    if i == 2 { return SideJobDataS23.FactMax2(); }
    if i == 3 { return SideJobDataS23.FactMax3(); }
    if i == 4 { return SideJobDataS23.FactMax4(); }
    if i == 5 { return SideJobDataS23.FactMax5(); }
    if i == 6 { return SideJobDataS23.FactMax6(); }
    if i == 7 { return SideJobDataS23.FactMax7(); }
    if i == 8 { return SideJobDataS23.FactMax8(); }
    if i == 9 { return SideJobDataS23.FactMax9(); }
    if i == 10 { return SideJobDataS23.FactMax10(); }
    if i == 11 { return SideJobDataS23.FactMax11(); }
    if i == 12 { return SideJobDataS23.FactMax12(); }
    if i == 13 { return SideJobDataS23.FactMax13(); }
    if i == 14 { return SideJobDataS23.FactMax14(); }
    if i == 15 { return SideJobDataS23.FactMax15(); }
    if i == 16 { return SideJobDataS23.FactMax16(); }
    if i == 17 { return SideJobDataS23.FactMax17(); }
    if i == 18 { return SideJobDataS23.FactMax18(); }
    if i == 19 { return SideJobDataS23.FactMax19(); }
    if i == 20 { return SideJobDataS23.FactMax20(); }
    if i == 21 { return SideJobDataS23.FactMax21(); }
    if i == 22 { return SideJobDataS23.FactMax22(); }
    if i == 23 { return SideJobDataS23.FactMax23(); }
    let empty: array<Int32>; return empty;
  }
  public static func FactMax0() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 1]; }
  public static func FactMax1() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]; }
  public static func FactMax2() -> array<Int32> { return [0, 0, 0, 0]; }
  public static func FactMax3() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 0, 0, 0, 1]; }
  public static func FactMax4() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 1]; }
  public static func FactMax5() -> array<Int32> { return [0, 0, 0, 0]; }
  public static func FactMax6() -> array<Int32> { return [0, 0, 0]; }
  public static func FactMax7() -> array<Int32> { return [0, 0, 0]; }
  public static func FactMax8() -> array<Int32> { return [0, 0, 0, 1, 0, 1, 11, 51, 95, 0, 0, 0, 0, 0, 0, 1, 0]; }
  public static func FactMax9() -> array<Int32> { return [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]; }
  public static func FactMax10() -> array<Int32> { return [1, 0, 0, 0, 0, 0, 0, 0]; }
  public static func FactMax11() -> array<Int32> { return [0, 0, 0, 0, 0, 1, 0]; }
  public static func FactMax12() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 0]; }
  public static func FactMax13() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]; }
  public static func FactMax14() -> array<Int32> { return [0, 0, 0, 0, 0, 0]; }
  public static func FactMax15() -> array<Int32> { return [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0]; }
  public static func FactMax16() -> array<Int32> { return [1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0]; }
  public static func FactMax17() -> array<Int32> { return []; }
  public static func FactMax18() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 0, 0, 0, 2147483647]; }
  public static func FactMax19() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 2147483647, 2147483647, 2147483647]; }
  public static func FactMax20() -> array<Int32> { return [0, 0, 0, 0, 2147483647]; }
  public static func FactMax21() -> array<Int32> { return [0, 0, 0, 0, 2147483647]; }
  public static func FactMax22() -> array<Int32> { return [0, 0]; }
  public static func FactMax23() -> array<Int32> { return [0, 0]; }
}

