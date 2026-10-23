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

// GENERATED_DATA
