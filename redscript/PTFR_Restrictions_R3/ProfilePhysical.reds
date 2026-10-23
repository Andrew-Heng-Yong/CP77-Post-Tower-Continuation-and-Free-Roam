module PTFR.RestrictionsR3

import PTFR.RestrictionsR1.*
import PTFR.RestrictionsR2.*

// All modifiers are unsaved and removed only by retained reference. Never
// ForceModifier/UnforceStat, broad modifier removal, or global TweakDB edits.
public class ProfilePhysical extends IScriptable {
  private let player: wref<PlayerPuppet>;
  private let smart: ref<gameStatModifierData>;
  private let health: ref<gameStatModifierData>;
  private let healthFactor: Float;
  private let weapon: wref<WeaponObject>;
  private let weaponMods: array<ref<gameStatModifierData>>;
  private let ready: Bool;
  private let fault: Bool;
  private let detail: String;
  private let ceiling: Float;
  private let pendingClamp: Int32;
  private let clampSent: Bool;

  public static func EnforceWeapon(weapon: ref<WeaponObject>, owner: ref<GameObject>) -> Void {
    if !IsDefined(weapon) || !IsDefined(owner) || !CyberwarePolicy.Active(owner) || weapon.GetOwner() != owner { return; }
    let record = weapon.GetWeaponRecord();
    if !IsDefined(record) || !IsDefined(record.Evolution()) || NotEquals(record.Evolution().Type(), gamedataWeaponEvolution.Smart) { return; }
    weapon.PTFRR3Straight(true);
    let event = new EnableSmartGunHandlerEvent(); event.owner = owner; event.enable = false;
    weapon.QueueEvent(event);
  }
  private func ClearWeapon() -> Void {
    if IsDefined(this.weapon) {
      let stats = GameInstance.GetStatsSystem(this.weapon.GetGame());
      let id = Cast<StatsObjectID>(this.weapon.GetEntityID()); let i = 0;
      while i < ArraySize(this.weaponMods) { stats.RemoveModifier(id, this.weaponMods[i]); i += 1; }
      // Undo only the flag this module asserted, never alter another weapon.
      this.weapon.PTFRR3Straight(false);
    }
    ArrayClear(this.weaponMods); this.weapon = null;
  }
  private func DropHealth() -> Void {
    if IsDefined(this.player) && IsDefined(this.health) {
      this.BeginClamp();
      GameInstance.GetStatsSystem(this.player.GetGame()).RemoveModifier(Cast<StatsObjectID>(this.player.GetEntityID()), this.health);
    }
    this.health = null; this.healthFactor = 1.00; this.ready = false;
  }
  public func Release() -> Void {
    this.ClearWeapon(); this.DropHealth();
    if IsDefined(this.player) && IsDefined(this.smart) {
      GameInstance.GetStatsSystem(this.player.GetGame()).RemoveModifier(Cast<StatsObjectID>(this.player.GetEntityID()), this.smart);
    }
    this.smart = null; this.player = null; this.pendingClamp = 0; this.clampSent = false;
  }
  private func BeginClamp() -> Void {
    let pools = GameInstance.GetStatPoolsSystem(this.player.GetGame());
    let now = pools.GetStatPoolValue(Cast<StatsObjectID>(this.player.GetEntityID()), gamedataStatPoolType.Health, false);
    if this.pendingClamp > 0 { this.ceiling = MinF(this.ceiling, now); } else { this.ceiling = now; }
    this.pendingClamp = 12; this.clampSent = false;
  }
  private func CorrectPending() -> Void {
    if this.pendingClamp <= 0 || !IsDefined(this.player) || this.player.IsDead() { return; }
    let pools = GameInstance.GetStatPoolsSystem(this.player.GetGame()); let id = Cast<StatsObjectID>(this.player.GetEntityID());
    let now = pools.GetStatPoolValue(id, gamedataStatPoolType.Health, false);
    let maximum = GameInstance.GetStatsSystem(this.player.GetGame()).GetStatValue(id, gamedataStatType.Health);
    let poolMaximum = pools.GetStatPoolMaxPointValue(id, gamedataStatPoolType.Health);
    if AbsF(poolMaximum - maximum) < 0.05 {
      let excess = now - this.ceiling;
      if excess <= 0.01 { this.pendingClamp = 0; this.clampSent = false; return; }
      if !this.clampSent {
        // Exactly one negative request, then acknowledge; never queue repeated
        // subtraction while the pool service still holds the previous request.
        pools.RequestChangingStatPoolValue(id, gamedataStatPoolType.Health, -excess, this.player, false, false);
        this.clampSent = true;
      }
    }
    this.pendingClamp -= 1;
    if this.pendingClamp == 0 { this.Stop("HP pool acknowledgement timed out; correction was not replayed"); }
  }
  public func Update(player: ref<PlayerPuppet>, useHealth: Bool, target: Float) -> Void {
    if this.player != player { this.Release(); this.player = player; this.healthFactor = 1.00; }
    this.CorrectPending();
    if !CyberwarePolicy.Active(player) {
      this.ClearWeapon(); this.DropHealth();
      if IsDefined(this.smart) { GameInstance.GetStatsSystem(player.GetGame()).RemoveModifier(Cast<StatsObjectID>(player.GetEntityID()), this.smart); this.smart = null; }
      this.detail = "Inactive; owned modifiers removed"; return;
    }
    let stats = GameInstance.GetStatsSystem(player.GetGame()); let id = Cast<StatsObjectID>(player.GetEntityID());
    if !IsDefined(this.smart) {
      this.smart = RPGManager.CreateStatModifier(gamedataStatType.HasSmartLink, gameStatModifierType.Multiplier, 0.00);
      if !stats.AddModifier(id, this.smart) { this.smart = null; this.detail = "Smart Link modifier admission failed"; }
    }
    let currentWeapon = GameInstance.GetTransactionSystem(player.GetGame()).GetItemInSlot(player, t"AttachmentSlots.WeaponRight") as WeaponObject;
    if currentWeapon != this.weapon { this.ClearWeapon(); }
    if IsDefined(currentWeapon) && Equals(RPGManager.GetWeaponEvolution(currentWeapon.GetItemID()), gamedataWeaponEvolution.Smart) {
      if !IsDefined(this.weapon) {
        this.weapon = currentWeapon;
        this.AddWeaponZero(gamedataStatType.SmartGunAdsMaxLockedTargets);
        this.AddWeaponZero(gamedataStatType.SmartGunHipMaxLockedTargets);
        this.AddWeaponZero(gamedataStatType.SmartGunTrackMultipleEntitiesInADS);
      }
      ProfilePhysical.EnforceWeapon(this.weapon, player);
    }
    if !useHealth { this.DropHealth(); this.detail = "HP overrides OFF; Smart Link stat=" + ToString(stats.GetStatValue(id, gamedataStatType.HasSmartLink)); return; }
    if this.fault { return; }
    if player.IsDead() || player.IsReplacer() { return; }
    if this.pendingClamp > 0 { this.detail = "Waiting for single HP pool adjustment acknowledgement"; return; }
    let maximum = stats.GetStatValue(id, gamedataStatType.Health);
    let pools = GameInstance.GetStatPoolsSystem(player.GetGame());
    let poolMaximum = pools.GetStatPoolMaxPointValue(id, gamedataStatPoolType.Health);
    if !(maximum > 0.00 && maximum < 1000000.00 && target >= 1.00 && target <= 100000.00) { this.Stop("Invalid Health maximum"); return; }
    if AbsF(maximum - target) > 0.02 {
      // Initial activation waits for safe gameplay. Subsequent buff changes
      // reconcile the owned factor from readback, never from a stacked penalty.
      if !IsDefined(this.health) && !BodyPolicy.Safe(player) { this.detail = "Waiting to activate HP in safe gameplay"; return; }
      this.BeginClamp(); this.ready = false;
      let nextFactor = this.healthFactor * target / maximum;
      if !(nextFactor > 0.000001 && nextFactor < 100000.00) { this.Stop("Invalid HP scaling factor"); return; }
      if IsDefined(this.health) && !stats.RemoveModifier(id, this.health) { this.Stop("Could not remove owned HP modifier"); return; }
      this.health = RPGManager.CreateStatModifier(gamedataStatType.Health, gameStatModifierType.Multiplier, nextFactor);
      if !stats.AddModifier(id, this.health) { this.health = null; this.Stop("Could not apply owned HP modifier"); return; }
      this.healthFactor = nextFactor;
      let readback = stats.GetStatValue(id, gamedataStatType.Health);
      if AbsF(readback - target) > 0.05 { this.Stop("HP modifier readback differs from target; no broad cleanup"); return; }
      this.detail = "HP modifier applied; awaiting pool readback"; return;
    }
    this.ready = AbsF(poolMaximum - target) < 0.05 && this.pendingClamp == 0;
    this.detail = "HP max stat=" + ToString(maximum) + " pool=" + ToString(poolMaximum) + " Smart Link stat=" + ToString(stats.GetStatValue(id, gamedataStatType.HasSmartLink));
  }
  private func AddWeaponZero(type: gamedataStatType) -> Void {
    let modifier = RPGManager.CreateStatModifier(type, gameStatModifierType.Multiplier, 0.00);
    if GameInstance.GetStatsSystem(this.weapon.GetGame()).AddModifier(Cast<StatsObjectID>(this.weapon.GetEntityID()), modifier) { ArrayPush(this.weaponMods, modifier); }
  }
  private func Stop(message: String) -> Void {
    this.fault = true; this.ready = false; this.detail = "STOPPED: " + message;
    ModLog(n"PTFR_Restrictions_R3", this.detail);
  }
  public func HealthReady() -> Bool { return this.ready && !this.fault; }
  public func Faulted() -> Bool { return this.fault; }
  public func Status() -> String { return this.detail; }
}
