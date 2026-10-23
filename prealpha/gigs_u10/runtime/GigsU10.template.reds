module PTFR.GigsU10

import PTFR.RestrictionsR2.*
import PTFR.RestrictionsR3.*
import PTFR.ActivityStateR3.*

// Fresh original entries only. Existing progress is preserved; unsupported
// continuation states defer. Native owners retain gameplay and reward writes.
public struct GigSampleU10 {
  public let states: array<Int32>;
  public let facts: array<Int32>;
  public let inventory: array<Int32>;
  public let valid: Bool;
  public let reason: String;
}

public class GigsU10 extends ScriptableSystem {
  // A genuine observation in this save before Tower; never backfilled after it.
  private persistent let familyHistorySchema: Int32;
  private persistent let familyPreTowerCompleted: Bool;
  private let historyPrevious: Bool;
  private let running: Bool;
  private let epoch: Int32;
  private let warmup: Int32;
  private let previous: array<GigSampleU10>;

  public static func Get(game: GameInstance) -> ref<GigsU10> {
    return GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.GigsU10.GigsU10") as GigsU10;
  }
  private func Fact(name: String) -> Int32 {
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    return IsDefined(qs) ? qs.GetFactStr(name) : -2147483647;
  }
  private func Own(i: Int32, suffix: String) -> Int32 { return this.Fact(GigDataU10.Tag(i) + "_" + suffix); }
  private func State(path: String) -> Int32 {
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    if !IsDefined(jm) { return -1; }
    let entry = jm.GetEntryByString(path, "gameJournalQuest");
    return IsDefined(entry) ? EnumInt(jm.GetEntryState(entry)) : -1;
  }
  private func BeforeTower() -> Bool {
    return this.Fact("PostTowerFreeRoamActive") == 0 && this.Fact("q307_active") == 0 &&
      this.Fact("q307_done") == 0 && this.Fact("q307_finished") == 0 && this.Fact("q307_2079") == 0 &&
      this.Fact("q307_main_game_killed") == 0 && this.Fact("q307_ep1_killed") == 0 && this.Fact("q307_debug_reset") == 0 &&
      this.Fact("q307_point_of_no_return") == 0 && this.Fact("q115_point_of_no_return") == 0 &&
      this.State("ep1/quests/main_quest/q307_before_tomorrow") == 1 && this.State("ep1/quests/main_quest/q307_tomorrow") == 1;
  }
  private func ObserveHistory() -> Void {
    if this.familyPreTowerCompleted || this.familyHistorySchema != 0 { return; }
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    if !IsDefined(jm) || jm.HasAnyDelayedStateChanges() || !this.BeforeTower() {
      this.historyPrevious = false; return;
    }
    let completed = this.State("quests/main_quest/act_01/q103_warhead") == 3 &&
      this.Fact("q103_done") >= 1 && this.Fact("q103_rogue_done") >= 1;
    if jm.HasAnyDelayedStateChanges() || !this.BeforeTower() { this.historyPrevious = false; return; }
    if completed && this.historyPrevious {
      this.familyHistorySchema = 1; this.familyPreTowerCompleted = true;
    }
    this.historyPrevious = completed;
  }
  private func HistoryReady(i: Int32) -> Bool {
    return NotEquals(GigDataU10.ID(i), "sts_wbr_hil_06") ||
      (this.familyHistorySchema == 1 && this.familyPreTowerCompleted);
  }
  private func Permit(i: Int32, allowed: Bool) -> Void {
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if !IsDefined(qs) || this.Own(i, "Issued") != 0 { return; }
    let value = allowed ? 1 : 0;
    let name = GigDataU10.Tag(i) + "_Permit";
    if qs.GetFactStr(name) != value { qs.SetFactStr(name, value); }
  }
  private func PreparePermit(i: Int32, allowed: Bool) -> Void {
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if !IsDefined(qs) || this.Own(i, "Issued") != 0 { return; }
    let name = GigDataU10.Tag(i) + "_PreparePermit"; let value = allowed ? 1 : 0;
    if qs.GetFactStr(name) != value { qs.SetFactStr(name, value); }
  }
  private func Dependencies(i: Int32) -> Bool {
    let names = GigDataU10.ServiceNames(i); let values = GigDataU10.ServiceValues(i);
    if ArraySize(names) != ArraySize(values) { return false; }
    let k = 0;
    while k < ArraySize(names) { if this.Fact(names[k]) != values[k] { return false; }; k += 1; }
    return true;
  }
  private func BaseCommon() -> Bool {
    if !IsDefined(GameInstance.GetQuestsSystem(this.GetGameInstance())) { return false; }
    let profile = ProfilePolicy.Get(this.GetGameInstance());
    return this.Fact("PostTowerFreeRoamActive") == 1 && this.Fact("PTFRP0_DR13") == 1 &&
      this.Fact("PTFRPA2_Finished") == 1 && this.Fact("PTFRPA2_Fault") == 0 &&
      this.Fact("q307_done") == 1 && this.Fact("q307_finished") == 1 && this.Fact("q307_2079") == 1 &&
      this.Fact("q307_main_game_killed") == 1 && this.Fact("q307_ep1_killed") == 1 &&
      this.Fact("q307_active") == 0 && this.Fact("q307_debug_reset") == 0 &&
      this.Fact("q115_point_of_no_return") == 0 && this.Fact("q305_johnny_scene_active") == 0 &&
      IsDefined(profile) && profile.PTFRPAComplete() && !profile.PTFRPAFaulted();
  }
  private func Common() -> Bool {
    let phone = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.ActivityStateR3.GigPhoneU9") as GigPhoneU9;
    return this.BaseCommon() && IsDefined(phone) && phone.Supported();
  }
  private func PrepareSupport() -> Void {
    if !this.BaseCommon() || !this.Safe() || this.warmup != 0 ||
      this.Fact("PTFRU9_Support_Request") != 0 || this.Fact("PTFRU9_Support_Issued") != 0 ||
      this.Fact("PTFRU9_Support_Fault") != 0 { return; }
    let phone = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.ActivityStateR3.GigPhoneU9") as GigPhoneU9;
    if !IsDefined(phone) { return; }
    let i = 0; let sample: GigSampleU10;
    while i < GigDataU10.Count() {
      if this.FreshOwner(i) && this.HistoryReady(i) {
        sample = this.Read(i);
        if sample.valid { phone.Start("DISPOSABLE_SAVE"); return; }
      }
      i += 1;
    }
  }
  private func MapPermit(i: Int32, allowed: Bool) -> Void {
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if !IsDefined(qs) { return; }
    let name = GigDataU10.Tag(i) + "_MapPermit"; let value = allowed ? 1 : 0;
    if qs.GetFactStr(name) != value { qs.SetFactStr(name, value); }
  }
  private func MapReady(i: Int32) -> Bool {
    if !this.Common() || !this.Safe() || this.Own(i, "Revision") != 1 || this.Own(i, "Issued") != 1 || this.Own(i, "Started") != 1 || this.Own(i, "OwnerFinished") != 0 || this.Own(i, "Fault") != 0 { return false; }
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    if !IsDefined(jm) || jm.HasAnyDelayedStateChanges() { return false; }
    let paths = GigDataU10.Paths(i); let entry = jm.GetEntryByString(paths[0], "gameJournalQuest");
    if !IsDefined(entry) || EnumInt(jm.GetEntryState(entry)) != 1 { return false; }
    let facts = GigDataU10.MapFactsZero(i); let k = 0;
    while k < ArraySize(facts) { if this.Fact(facts[k]) != 0 { return false; }; k += 1; }
    return !jm.HasAnyDelayedStateChanges();
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
    this.epoch += 1; this.warmup = 3; this.historyPrevious = false; ArrayClear(this.previous);
    let i = 0; let empty: GigSampleU10;
    while i < GigDataU10.Count() {
      ArrayPush(this.previous, empty);
      // Never change a durable native Issued owner, including saved completion.
      if this.Own(i, "Issued") == 0 { this.Permit(i, false); this.PreparePermit(i, false); }
      this.MapPermit(i, false);
      i += 1;
    }
    if this.running { this.Schedule(); }
  }
  private func Schedule() -> Void {
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(GigTickU10.Create(this, this.epoch), 1.0, false);
  }
  private func Read(i: Int32) -> GigSampleU10 {
    let sample: GigSampleU10;
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if !IsDefined(jm) || !IsDefined(qs) || jm.HasAnyDelayedStateChanges() { sample.reason = "Journal/facts unavailable or unsettled; state unknown."; return sample; }
    let paths = GigDataU10.Paths(i); let classes = GigDataU10.Classes(i);
    let first = GigDataU10.StatesA(i); let second = GigDataU10.StatesB(i);
    let names = GigDataU10.FactNames(i); let wanted = GigDataU10.FactValues(i);
    if ArraySize(paths) == 0 || ArraySize(paths) != ArraySize(classes) || ArraySize(paths) != ArraySize(first) || ArraySize(paths) != ArraySize(second) || ArraySize(names) != ArraySize(wanted) {
      sample.reason = "Adapter data shape mismatch; refused."; return sample;
    }
    let entry: wref<JournalEntry>; let state: Int32; let actual: Int32; let k = 0;
    sample.valid = true; sample.reason = "Native state matches the original beginning.";
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
    let items = GigDataU10.ItemNames(i);
    let players = GameInstance.GetPlayerSystem(this.GetGameInstance());
    let transaction = GameInstance.GetTransactionSystem(this.GetGameInstance());
    if ArraySize(items) > 0 {
      if !IsDefined(players) || !IsDefined(transaction) {
        sample.valid = false; sample.reason = "Inventory unavailable; state unknown."; return sample;
      }
      let player = players.GetLocalPlayerMainGameObject() as PlayerPuppet;
      if !IsDefined(player) || player.IsReplacer() {
        sample.valid = false; sample.reason = "Player inventory unavailable; state unknown."; return sample;
      }
      k = 0;
      while k < ArraySize(items) {
        actual = transaction.GetItemQuantity(player, ItemID.CreateQuery(TDBID.Create(items[k])));
        ArrayPush(sample.inventory, actual);
        if actual != 0 {
          sample.valid = false; sample.reason = "Quest item protected: " + items[k] + " quantity=" + ToString(actual);
        }
        k += 1;
      }
    }
    if jm.HasAnyDelayedStateChanges() { sample.valid = false; sample.reason = "Journal changed during observation; waiting."; }
    return sample;
  }
  private func Same(a: GigSampleU10, b: GigSampleU10) -> Bool {
    if !a.valid || !b.valid || ArraySize(a.states) != ArraySize(b.states) || ArraySize(a.facts) != ArraySize(b.facts) || ArraySize(a.inventory) != ArraySize(b.inventory) { return false; }
    let i = 0;
    while i < ArraySize(a.states) { if a.states[i] != b.states[i] { return false; }; i += 1; }
    i = 0;
    while i < ArraySize(a.facts) { if a.facts[i] != b.facts[i] { return false; }; i += 1; }
    i = 0;
    while i < ArraySize(a.inventory) { if a.inventory[i] != b.inventory[i] { return false; }; i += 1; }
    return true;
  }
  private func FreshOwner(i: Int32) -> Bool {
    return this.Own(i, "Ready") == 1 && this.Own(i, "Revision") == 1 && this.Own(i, "Issued") == 0 &&
      this.Own(i, "Started") == 0 && this.Own(i, "OwnerFinished") == 0 && this.Own(i, "Fault") == 0 &&
      this.Own(i, "CreditEntered") == 0 && this.Own(i, "CreditDone") == 0;
  }
  private func Ready(i: Int32) -> Bool {
    return this.running && this.warmup == 0 && this.Common() && this.Safe() && this.FreshOwner(i) && this.HistoryReady(i);
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    this.Schedule();
    this.ObserveHistory();
    if this.warmup > 0 { this.warmup -= 1; }
    if ArraySize(this.previous) != GigDataU10.Count() { this.Restored(); return; }
    this.PrepareSupport();
    let i = 0; let current: GigSampleU10; let empty: GigSampleU10;
    while i < GigDataU10.Count() {
      if this.Own(i, "Issued") == 0 {
        if this.Ready(i) {
          current = this.Read(i);
          // Separate consecutive ticks, not two immediate reads of one frame.
          this.PreparePermit(i, this.Same(this.previous[i], current) && this.Ready(i));
          this.Permit(i, this.Same(this.previous[i], current) && this.Ready(i) && this.Dependencies(i));
          this.previous[i] = current;
        } else {
          this.Permit(i, false); this.PreparePermit(i, false); this.previous[i] = empty;
        }
      }
      this.MapPermit(i, this.MapReady(i));
      i += 1;
    }
  }
  public func Status() -> String {
    let issued = 0; let permitted = 0; let i = 0;
    while i < GigDataU10.Count() {
      if this.Own(i, "Issued") == 1 { issued += 1; }
      if this.Own(i, "Permit") == 1 && this.Own(i, "Issued") == 0 { permitted += 1; }
      i += 1;
    }
    return "Gigs U10: nativeEntries=" + ToString(GigDataU10.Count()) + " permitted/issued=" + ToString(permitted) + "/" + ToString(issued) +
      " postTowerReady=" + ToString(this.Common()) + " familyPreTowerHistory=" + ToString(this.familyHistorySchema == 1 && this.familyPreTowerCompleted) +
      " | Completed and existing progress preserved. Unsupported continuation defers without restart. Issued is not gameplay proof.";
  }
  public func Inspect(id: String) -> String {
    let i = GigDataU10.Index(id);
    if i < 0 {
      return "No U10 entry for " + id + "; no state changed.";
    }
    let sample = this.Read(i);
    return "Gig U10 " + GigDataU10.Title(i) + " [" + GigDataU10.ID(i) + "]: ready/permit/issued/finished=" + ToString(this.Own(i, "Ready")) + "/" +
      ToString(this.Own(i, "Permit")) + "/" + ToString(this.Own(i, "Issued")) + "/" + ToString(this.Own(i, "OwnerFinished")) + " fault=" + ToString(this.Own(i, "Fault")) +
      " currentMatch=" + ToString(sample.valid) + " safe=" + ToString(this.Safe()) + " preTowerPrerequisiteKnown=" + ToString(this.HistoryReady(i)) +
      " | " + sample.reason + " Unknown prerequisite history defers. Issued owners are not restarted.";
  }
}

public class GigTickU10 extends DelayCallback {
  private let owner: wref<GigsU10>;
  private let epoch: Int32;
  public static func Create(owner: ref<GigsU10>, epoch: Int32) -> ref<GigTickU10> {
    let tick = new GigTickU10(); tick.owner = owner; tick.epoch = epoch; return tick;
  }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}

@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void {
  wrappedMethod(gameInstance);
  let owner = GigsU10.Get(gameInstance);
  if IsDefined(owner) { owner.Restored(); }
}

// GENERATED_DATA
