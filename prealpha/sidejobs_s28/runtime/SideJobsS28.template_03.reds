module PTFR.SideJobsS28

import PTFR.RestrictionsR2.*
import PTFR.RestrictionsR3.*
import PTFR.ActivityStateR3.*

// Fresh original entries only. Existing progress is preserved; unsupported
// continuation states defer. Native owners retain gameplay and reward writes.
public struct SideJobSampleS28 {
  public let states: array<Int32>;
  public let facts: array<Int32>;
  public let inventory: array<Int32>;
  public let vehicles: array<Bool>;
  public let valid: Bool;
  public let reason: String;
}

public class SideJobsS28 extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let warmup: Int32;
  private let previous: array<SideJobSampleS28>;

  public static func Get(game: GameInstance) -> ref<SideJobsS28> {
    return GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.SideJobsS28.SideJobsS28") as SideJobsS28;
  }
  private func Fact(name: String) -> Int32 {
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    return IsDefined(qs) ? qs.GetFactStr(name) : -2147483647;
  }
  private func Own(i: Int32, suffix: String) -> Int32 { return this.Fact(SideJobDataS28.Tag(i) + "_" + suffix); }
  private func Permit(i: Int32, allowed: Bool) -> Void {
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if !IsDefined(qs) || this.Own(i, "Issued") != 0 { return; }
    let value = allowed ? 1 : 0;
    let name = SideJobDataS28.Tag(i) + "_Permit";
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
    let i = 0; let empty: SideJobSampleS28;
    while i < SideJobDataS28.Count() {
      ArrayPush(this.previous, empty);
      // Never change a durable native Issued owner, including saved completion.
      if this.Own(i, "Issued") == 0 { this.Permit(i, false); }
      i += 1;
    }
    if this.running { this.Schedule(); }
  }
  private func Schedule() -> Void {
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(SideJobTickS28.Create(this, this.epoch), 1.0, false);
  }
  private func Read(i: Int32) -> SideJobSampleS28 {
    let sample: SideJobSampleS28;
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if !IsDefined(jm) || !IsDefined(qs) || jm.HasAnyDelayedStateChanges() { sample.reason = "Journal/facts unavailable or unsettled; state unknown."; return sample; }
    let paths = SideJobDataS28.Paths(i); let classes = SideJobDataS28.Classes(i);
    let first = SideJobDataS28.StatesA(i); let second = SideJobDataS28.StatesB(i);
    let names = SideJobDataS28.FactNames(i); let wanted = SideJobDataS28.FactValues(i);
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
    let items = SideJobDataS28.ItemNames(i);
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
    let vehicles = SideJobDataS28.VehicleNames(i);
    let vehicleSystem = GameInstance.GetVehicleSystem(this.GetGameInstance());
    if ArraySize(vehicles) > 0 {
      if !IsDefined(vehicleSystem) {
        sample.valid = false; sample.reason = "Vehicle ownership unavailable; state unknown."; return sample;
      }
      k = 0;
      let unlocked: Bool;
      while k < ArraySize(vehicles) {
        unlocked = vehicleSystem.IsVehiclePlayerUnlocked(TDBID.Create(vehicles[k]));
        ArrayPush(sample.vehicles, unlocked);
        if unlocked { sample.valid = false; sample.reason = "Existing vehicle ownership protected: " + vehicles[k]; }
        k += 1;
      }
    }
    if jm.HasAnyDelayedStateChanges() { sample.valid = false; sample.reason = "Journal changed during observation; waiting."; }
    return sample;
  }
  private func Same(a: SideJobSampleS28, b: SideJobSampleS28) -> Bool {
    if !a.valid || !b.valid || ArraySize(a.states) != ArraySize(b.states) || ArraySize(a.facts) != ArraySize(b.facts) || ArraySize(a.inventory) != ArraySize(b.inventory) || ArraySize(a.vehicles) != ArraySize(b.vehicles) { return false; }
    let i = 0;
    while i < ArraySize(a.states) { if a.states[i] != b.states[i] { return false; }; i += 1; }
    i = 0;
    while i < ArraySize(a.facts) { if a.facts[i] != b.facts[i] { return false; }; i += 1; }
    i = 0;
    while i < ArraySize(a.inventory) { if a.inventory[i] != b.inventory[i] { return false; }; i += 1; }
    i = 0;
    while i < ArraySize(a.vehicles) { if (a.vehicles[i] && !b.vehicles[i]) || (!a.vehicles[i] && b.vehicles[i]) { return false; }; i += 1; }
    return true;
  }
  private func FreshOwner(i: Int32) -> Bool {
    return this.Own(i, "Ready") == 1 && this.Own(i, "Revision") == 1 && this.Own(i, "Issued") == 0 &&
      this.Own(i, "Entered") == 0 && this.Own(i, "Finished") == 0 && this.Own(i, "Fault") == 0;
  }
  private func Ready(i: Int32) -> Bool {
    return this.running && this.warmup == 0 && this.Common() && this.Safe() && this.FreshOwner(i);
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    this.Schedule();
    if this.warmup > 0 { this.warmup -= 1; }
    if ArraySize(this.previous) != SideJobDataS28.Count() { this.Restored(); return; }
    let i = 0; let current: SideJobSampleS28; let empty: SideJobSampleS28;
    while i < SideJobDataS28.Count() {
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
    while i < SideJobDataS28.Count() {
      if this.Own(i, "Issued") == 1 { issued += 1; }
      if this.Own(i, "Permit") == 1 && this.Own(i, "Issued") == 0 { permitted += 1; }
      i += 1;
    }
    return "Side jobs S28: nativeEntries=" + ToString(SideJobDataS28.Count()) + " permitted/issued=" + ToString(permitted) + "/" + ToString(issued) +
      " postTowerReady=" + ToString(this.Common()) +
      " | Completed and existing progress preserved. Unsupported continuation defers without restart. Issued is not gameplay proof.";
  }
  public func Inspect(id: String) -> String {
    let i = SideJobDataS28.Index(id);
    if i < 0 {
      return "No S28 entry for " + id + "; no state changed.";
    }
    let sample = this.Read(i);
    return "Side job S28 " + SideJobDataS28.Title(i) + " [" + SideJobDataS28.ID(i) + "]: ready/permit/issued/finished=" + ToString(this.Own(i, "Ready")) + "/" +
      ToString(this.Own(i, "Permit")) + "/" + ToString(this.Own(i, "Issued")) + "/" + ToString(this.Own(i, "Finished")) + " fault=" + ToString(this.Own(i, "Fault")) +
      " currentMatch=" + ToString(sample.valid) + " safe=" + ToString(this.Safe()) +
      " | " + sample.reason + " Issued owners are not restarted.";
  }
}

public class SideJobTickS28 extends DelayCallback {
  private let owner: wref<SideJobsS28>;
  private let epoch: Int32;
  public static func Create(owner: ref<SideJobsS28>, epoch: Int32) -> ref<SideJobTickS28> {
    let tick = new SideJobTickS28(); tick.owner = owner; tick.epoch = epoch; return tick;
  }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}

@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void {
  wrappedMethod(gameInstance);
  let owner = SideJobsS28.Get(gameInstance);
  if IsDefined(owner) { owner.Restored(); }
}

// These read-only prerequisites run inside the native admission condition.
// They do not convert a sampled Permit into vehicle ownership or item writes.
public class PTFRS28HighwaymanVehicleUnownedPrereq extends IScriptablePrereq {
  public const func IsFulfilled(game: GameInstance, context: ref<IScriptable>) -> Bool {
    let player = context as PlayerPuppet;
    let players = GameInstance.GetPlayerSystem(game);
    let vehicles = GameInstance.GetVehicleSystem(game);
    if !IsDefined(player) || !IsDefined(players) || !IsDefined(vehicles) { return false; }
    let localPlayer = players.GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(localPlayer) || player != localPlayer || player.IsReplacer() { return false; }
    return !vehicles.IsVehiclePlayerUnlocked(TDBID.Create("Vehicle.v_sportbike2_arch_tyger_player"));
  }
}

public class PTFRS28HoonVehicleUnownedPrereq extends IScriptablePrereq {
  public const func IsFulfilled(game: GameInstance, context: ref<IScriptable>) -> Bool {
    let player = context as PlayerPuppet;
    let players = GameInstance.GetPlayerSystem(game);
    let vehicles = GameInstance.GetVehicleSystem(game);
    if !IsDefined(player) || !IsDefined(players) || !IsDefined(vehicles) { return false; }
    let localPlayer = players.GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(localPlayer) || player != localPlayer || player.IsReplacer() { return false; }
    return !vehicles.IsVehiclePlayerUnlocked(TDBID.Create("Vehicle.v_sport2_quadra_type66_nomad_tribute"));
  }
}

public class PTFRS28HoonWorldKeyAbsentPrereq extends IScriptablePrereq {
  public const func IsFulfilled(game: GameInstance, context: ref<IScriptable>) -> Bool {
    let player = context as PlayerPuppet;
    let players = GameInstance.GetPlayerSystem(game);
    let transaction = GameInstance.GetTransactionSystem(game);
    if !IsDefined(player) || !IsDefined(players) || !IsDefined(transaction) { return false; }
    let localPlayer = players.GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(localPlayer) || player != localPlayer || player.IsReplacer() { return false; }
    let crateRef = CreateNodeRef("$/03_night_city/c_watson/northside/loc_mq050_ken_block_tribute_prefabIK2VAKA/loc_mq050_ken_block_tribute_gameplay_prefabJPVRKTI/loc_mq050_ken_block_tribute_loot_prefabPU3FSXA/#mq050_main_loot");
    let globalRef = ResolveNodeRef(crateRef, Cast<GlobalNodeRef>(GlobalNodeID.GetRoot()));
    let crate = GameInstance.FindEntityByID(game, Cast<EntityID>(globalRef)) as GameObject;
    if !IsDefined(crate) { return false; }
    return transaction.GetItemQuantity(crate, ItemID.CreateQuery(TDBID.Create("Keycards.mq050_car_keys"))) == 0;
  }
}

// GENERATED_DATA
