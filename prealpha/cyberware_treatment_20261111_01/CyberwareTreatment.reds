// Appended to the installed R1 module by prepare.py.
public enum CyberwareTreatment {
  Unmanaged = 0,
  Remove = 1,
  Disabled = 2,
  Limited = 3,
  Functional = 4
}

public abstract class CyberwareTreatmentSettings {
  // Provisional flat bonuses. The native model and its parts remain intact.
  public static func TitaniumCarry() -> Float { return 20.0; }
  public static func ChitinArmor() -> Float { return 15.0; }
  public static func SubdermalArmor() -> Float { return 5.0; }
  public static func CarapaceArmor() -> Float { return 10.0; }

  public static func Tattoo(record: TweakDBID) -> Bool {
    return CyberwareTreatmentSettings.JohnnyTattoo(record) ||
      CyberwareTreatmentSettings.TogetherForever(record) ||
      CyberwareTreatmentSettings.TygerClaws(record);
  }

  public static func Level(id: ItemID) -> CyberwareTreatment {
    if !ItemID.IsValid(id) { return CyberwareTreatment.Unmanaged; }
    let record = ItemID.GetTDBID(id);
    let area = EquipmentSystem.GetEquipAreaType(id);
    if Equals(area, gamedataEquipmentArea.PersonalLink) { return CyberwareTreatment.Functional; }
    if !CyberwarePolicy.Area(area) { return CyberwareTreatment.Unmanaged; }
    if Equals(area, gamedataEquipmentArea.HandsCW) && CyberwareTreatmentSettings.Tattoo(record) {
      return CyberwareTreatment.Limited;
    }
    if Equals(area, gamedataEquipmentArea.ArmsCW) || Equals(area, gamedataEquipmentArea.ArmsCWStyle) ||
      Equals(area, gamedataEquipmentArea.HandsCW) {
      return CyberwareTreatment.Remove;
    }
    if Equals(area, gamedataEquipmentArea.EyesCW) && CyberwareTreatmentSettings.BasicKiroshi(record) {
      return CyberwareTreatment.Functional;
    }
    if CyberwareTreatmentSettings.TitaniumBones(record) || CyberwareTreatmentSettings.Chitin(record) ||
      CyberwareTreatmentSettings.SubdermalArmor(record) || CyberwareTreatmentSettings.Carapace(record) {
      return CyberwareTreatment.Limited;
    }
    return CyberwareTreatment.Disabled;
  }

  public static func RetainedModifier(id: ItemID) -> ref<gameStatModifierData> {
    let record = ItemID.GetTDBID(id);
    if CyberwareTreatmentSettings.TitaniumBones(record) {
      return RPGManager.CreateStatModifier(gamedataStatType.CarryCapacity, gameStatModifierType.Additive, CyberwareTreatmentSettings.TitaniumCarry());
    }
    let armor: Float;
    if CyberwareTreatmentSettings.Chitin(record) {
      armor = CyberwareTreatmentSettings.ChitinArmor();
    } else if CyberwareTreatmentSettings.SubdermalArmor(record) {
      armor = CyberwareTreatmentSettings.SubdermalArmor();
    } else if CyberwareTreatmentSettings.Carapace(record) {
      armor = CyberwareTreatmentSettings.CarapaceArmor();
    } else {
      return null;
    }
    return RPGManager.CreateStatModifier(gamedataStatType.Armor, gameStatModifierType.Additive, armor);
  }

  // STOCK_RECORD_PREDICATES
}

public class TreatedCyberware extends IScriptable {
  public let id: ItemID;
  public let nativeStatsSubtracted: Bool;
  public let retained: ref<gameStatModifierData>;
}

@addField(EquipmentSystemPlayerData)
private let ptfrTreated: array<ref<TreatedCyberware>>;

@addField(EquipmentSystemPlayerData)
private let ptfrSkippedPackages: array<ItemID>;

@addField(EquipmentSystemPlayerData)
private let ptfrEffectsVerified: Bool;

@addMethod(EquipmentSystemPlayerData)
private final const func PTFRFindTreatment(id: ItemID) -> Int32 {
  let i = 0;
  while i < ArraySize(this.ptfrTreated) {
    if this.ptfrTreated[i].id == id { return i; }
    i += 1;
  }
  return -1;
}

@addMethod(EquipmentSystemPlayerData)
private final func PTFRCyberwareRestoreStarted() -> Void {
  // An equipment restore can run again on the same data object. Drop only
  // our transient stat handles before the native equip restoration.
  let stats = GameInstance.GetStatsSystem(this.m_owner.GetGame());
  let ownerID = Cast<StatsObjectID>(this.m_owner.GetEntityID());
  let i = 0;
  while i < ArraySize(this.ptfrTreated) {
    if IsDefined(this.ptfrTreated[i].retained) { stats.RemoveModifier(ownerID, this.ptfrTreated[i].retained); }
    i += 1;
  }
  ArrayClear(this.ptfrTreated);
  ArrayClear(this.ptfrSkippedPackages);
  this.ptfrEffectsVerified = false;
}

@wrapMethod(EquipmentSystemPlayerData)
private final func ApplyEquipGLPs(itemID: ItemID) -> Void {
  if CyberwarePolicy.Suppresses(this.m_owner, itemID) {
    this.ptfrEffectsVerified = false;
    if !ArrayContains(this.ptfrSkippedPackages, itemID) { ArrayPush(this.ptfrSkippedPackages, itemID); }
    return;
  }
  wrappedMethod(itemID);
}

@wrapMethod(EquipmentSystemPlayerData)
private final func RemoveEquipGLPs(itemID: ItemID) -> Void {
  // Initial handoff removal of already-applied packages takes the native
  // chain. Once suppressed, later native unequip has no package to release.
  if this.PTFRFindTreatment(itemID) >= 0 || ArrayContains(this.ptfrSkippedPackages, itemID) { return; }
  wrappedMethod(itemID);
}

@addMethod(EquipmentSystemPlayerData)
private final func PTFREquipPackages(item: wref<gameItemData>) -> array<TweakDBID> {
  let packages: array<wref<GameplayLogicPackage_Record>>;
  let parts: array<InnerItemData>;
  let ids: array<TweakDBID>;
  let record = RPGManager.GetItemRecord(item.GetID());
  if IsDefined(record) { record.OnEquip(packages); }
  item.GetItemParts(parts);
  let i = 0;
  while i < ArraySize(packages) { ArrayPush(ids, packages[i].GetID()); i += 1; }
  i = 0;
  while i < ArraySize(parts) {
    record = RPGManager.GetItemRecord(InnerItemData.GetItemID(parts[i]));
    if IsDefined(record) {
      ArrayClear(packages);
      record.OnEquip(packages);
      let j = 0;
      while j < ArraySize(packages) { ArrayPush(ids, packages[j].GetID()); j += 1; }
    }
    i += 1;
  }
  return ids;
}

@addMethod(EquipmentSystemPlayerData)
private final func PTFRPackageOwnershipSafe(item: wref<gameItemData>, packages: array<TweakDBID>) -> Bool {
  let ts = GameInstance.GetTransactionSystem(this.m_owner.GetGame());
  let i = 0;
  while i < ArraySize(this.m_equipment.equipAreas) {
    let slots = this.m_equipment.equipAreas[i].equipSlots;
    let j = 0;
    while j < ArraySize(slots) {
      let id = slots[j].itemID;
      if ItemID.IsValid(id) && id != item.GetID() && !CyberwarePolicy.Suppresses(this.m_owner, id) {
        let other = ts.GetItemData(this.m_owner, id);
        if IsDefined(other) {
          let active = this.PTFREquipPackages(other);
          let k = 0;
          while k < ArraySize(active) {
            if ArrayContains(packages, active[k]) { return false; }
            k += 1;
          }
        }
      }
      j += 1;
    }
    i += 1;
  }
  return true;
}

@addMethod(EquipmentSystemPlayerData)
private final func PTFRLiveEquipPackages(item: wref<gameItemData>) -> array<TweakDBID> {
  let applied: array<TweakDBID>;
  let found: array<TweakDBID>;
  GameInstance.GetGameplayLogicPackageSystem(this.m_owner.GetGame()).GetAppliedPackagesOfInstigator(this.m_owner, this.m_owner, applied);
  let packages = this.PTFREquipPackages(item);
  let i = 0;
  while i < ArraySize(packages) {
    if ArrayContains(applied, packages[i]) { ArrayPush(found, packages[i]); }
    i += 1;
  }
  return found;
}

@addMethod(EquipmentSystemPlayerData)
private final func PTFRApplyTreatment(id: ItemID) -> Bool {
  if this.PTFRFindTreatment(id) >= 0 { return true; }
  let game = this.m_owner.GetGame();
  let item = GameInstance.GetTransactionSystem(game).GetItemData(this.m_owner, id);
  if !IsDefined(item) { return false; }
  let livePackages = this.PTFRLiveEquipPackages(item);
  if ArraySize(livePackages) > 0 && !this.PTFRPackageOwnershipSafe(item, livePackages) {
    ModLog(n"PTFR_Restrictions_R1", "Cannot isolate shared equip package for " + CyberwareDiagnosticsCD1.Item(id));
    return false;
  }

  let treatment = new TreatedCyberware();
  treatment.id = id;
  if Equals(CyberwareTreatmentSettings.Level(id), CyberwareTreatment.Limited) {
    treatment.retained = CyberwareTreatmentSettings.RetainedModifier(id);
    if IsDefined(treatment.retained) &&
      !GameInstance.GetStatsSystem(game).AddModifier(Cast<StatsObjectID>(this.m_owner.GetEntityID()), treatment.retained) {
      return false;
    }
  }
  if ArraySize(livePackages) > 0 {
    ArrayRemove(this.ptfrSkippedPackages, id);
    this.RemoveEquipGLPs(id);
  }
  if item.UsesVariants() {
    item.SubtractStatsOnUnequip(this.m_owner);
    treatment.nativeStatsSubtracted = true;
  }
  ArrayPush(this.ptfrTreated, treatment);
  return true;
}

@addMethod(EquipmentSystemPlayerData)
public final func PTFRCyberwareEffectsReady() -> Bool {
  if !this.ptfrEffectsVerified { return false; }
  let ids = this.PTFRInstalledCyberware();
  let i = 0;
  while i < ArraySize(ids) {
    if CyberwarePolicy.Suppresses(this.m_owner, ids[i]) && this.PTFRFindTreatment(ids[i]) < 0 { return false; }
    i += 1;
  }
  return true;
}

@addMethod(EquipmentSystemPlayerData)
public final func PTFRReconcileCyberwareEffects() -> Bool {
  let ids = this.PTFRInstalledCyberware();
  let ok = true;
  let i = 0;
  while i < ArraySize(ids) {
    if CyberwarePolicy.Suppresses(this.m_owner, ids[i]) && !this.PTFRApplyTreatment(ids[i]) { ok = false; }
    i += 1;
  }
  this.ptfrEffectsVerified = ok && this.PTFRCyberwarePackagesCleared(ids);
  return this.ptfrEffectsVerified;
}

@addMethod(EquipmentSystemPlayerData)
private final func PTFRCyberwarePackagesCleared(ids: array<ItemID>) -> Bool {
  let ts = GameInstance.GetTransactionSystem(this.m_owner.GetGame());
  let i = 0;
  while i < ArraySize(ids) {
    if CyberwarePolicy.Suppresses(this.m_owner, ids[i]) {
      let item = ts.GetItemData(this.m_owner, ids[i]);
      if !IsDefined(item) || ArraySize(this.PTFRLiveEquipPackages(item)) > 0 { return false; }
    }
    i += 1;
  }
  return true;
}

@addMethod(EquipmentSystemPlayerData)
public final func PTFRHasTreatedCyberware() -> Bool {
  return ArraySize(this.ptfrTreated) > 0 || ArraySize(this.ptfrSkippedPackages) > 0;
}

@addMethod(EquipmentSystemPlayerData)
public final func PTFRRestoreCyberwareEffects() -> Void {
  // Called only by the explicit No Nerf transition when native V is safe.
  let effects = this.ptfrTreated;
  let skipped = this.ptfrSkippedPackages;
  this.PTFRCyberwareRestoreStarted();
  let ts = GameInstance.GetTransactionSystem(this.m_owner.GetGame());
  let i = 0;
  while i < ArraySize(effects) {
    let id = effects[i].id;
    let item = ts.GetItemData(this.m_owner, id);
    if IsDefined(item) && this.GetSlotIndex(id) >= 0 {
      this.ApplyEquipGLPs(id);
      if effects[i].nativeStatsSubtracted { item.AddStatsOnEquip(this.m_owner); }
    }
    ArrayRemove(skipped, id);
    i += 1;
  }
  i = 0;
  while i < ArraySize(skipped) {
    if this.GetSlotIndex(skipped[i]) >= 0 { this.ApplyEquipGLPs(skipped[i]); }
    i += 1;
  }
  PlayerPuppet.ChacheQuickHackListCleanup(this.m_owner as PlayerPuppet);
}

@wrapMethod(EquipmentSystemPlayerData)
private final func EquipItem(itemID: ItemID, slotIndex: Int32, opt blockActiveSlotsUpdate: Bool, opt forceEquipWeapon: Bool) -> Void {
  if !CyberwarePolicy.Suppresses(this.m_owner, itemID) {
    wrappedMethod(itemID, slotIndex, blockActiveSlotsUpdate, forceEquipWeapon);
    return;
  }
  let priorSlot = this.GetSlotIndex(itemID);
  wrappedMethod(itemID, slotIndex, blockActiveSlotsUpdate, forceEquipWeapon);
  if CyberwarePolicy.Suppresses(this.m_owner, itemID) && this.GetSlotIndex(itemID) == slotIndex &&
    (priorSlot != slotIndex || this.PTFRFindTreatment(itemID) < 0) {
    // Native equip has just applied the per-instance variant stats.
    if !this.PTFRApplyTreatment(itemID) {
      ModLog(n"PTFR_Restrictions_R1", "Effect reconciliation pending for " + CyberwareDiagnosticsCD1.Item(itemID));
    }
  }
}

@wrapMethod(EquipmentSystemPlayerData)
private final func UnequipItem(equipAreaIndex: Int32, slotIndex: Int32, opt forceRemove: Bool) -> Void {
  let id = this.GetItemInEquipSlot(equipAreaIndex, slotIndex);
  let index = this.PTFRFindTreatment(id);
  let preserve = CyberwarePolicy.Suppresses(this.m_owner, id);
  if index < 0 && !preserve && !ArrayContains(this.ptfrSkippedPackages, id) {
    wrappedMethod(equipAreaIndex, slotIndex, forceRemove);
    return;
  }
  let item = GameInstance.GetTransactionSystem(this.m_owner.GetGame()).GetItemData(this.m_owner, id);
  if !IsDefined(item) || (!forceRemove && item.HasTag(n"UnequipBlocked")) {
    wrappedMethod(equipAreaIndex, slotIndex, forceRemove);
    return;
  }
  let previous = this.ptfrr1PreserveParts;
  this.ptfrr1PreserveParts = id;
  // Balance the exact native item subtraction in this synchronous unequip.
  // If native declines the request, leave the treatment in place.
  let restoreNativeStats = index >= 0 && this.ptfrTreated[index].nativeStatsSubtracted;
  if restoreNativeStats { item.AddStatsOnEquip(this.m_owner); }
  wrappedMethod(equipAreaIndex, slotIndex, forceRemove);
  this.ptfrr1PreserveParts = previous;
  if this.GetItemInEquipSlot(equipAreaIndex, slotIndex) == id {
    if restoreNativeStats { item.SubtractStatsOnUnequip(this.m_owner); }
    return;
  }
  if index >= 0 {
    let retained = this.ptfrTreated[index].retained;
    if IsDefined(retained) {
      GameInstance.GetStatsSystem(this.m_owner.GetGame()).RemoveModifier(Cast<StatsObjectID>(this.m_owner.GetEntityID()), retained);
    }
    ArrayErase(this.ptfrTreated, index);
  }
  this.ptfrEffectsVerified = false;
  ArrayRemove(this.ptfrSkippedPackages, id);
}

@wrapMethod(ItemModificationSystem)
private final func InstallItemPart(obj: ref<GameObject>, itemID: ItemID, partItemID: ItemID, opt slotID: TweakDBID) -> Bool {
  if CyberwarePolicy.ModificationDenied(obj, itemID) { return false; }
  return wrappedMethod(obj, itemID, partItemID, slotID);
}

@wrapMethod(ItemModificationSystem)
private final const func RemoveItemPart(obj: ref<GameObject>, itemID: ItemID, slotID: TweakDBID, shouldUpdateEntity: Bool) -> ItemID {
  if CyberwarePolicy.ModificationDenied(obj, itemID) { return ItemID.None(); }
  return wrappedMethod(obj, itemID, slotID, shouldUpdateEntity);
}

@wrapMethod(ItemModificationSystem)
private final func SwapItemPart(obj: ref<GameObject>, itemID: ItemID, partItemID: ItemID, slotID: TweakDBID) -> Bool {
  if CyberwarePolicy.ModificationDenied(obj, itemID) { return false; }
  return wrappedMethod(obj, itemID, partItemID, slotID);
}

@wrapMethod(EquipmentSystemPlayerData)
public final func OnGameplayEquipProgramsRequest(request: ref<GameplayEquipProgramsRequest>) -> Void {
  if CyberwarePolicy.OperatingSystemDisabled(this.m_owner) { return; }
  wrappedMethod(request);
}

@wrapMethod(EquipmentSystemPlayerData)
public final func OnPartInstallRequest(request: ref<PartInstallRequest>) -> Void {
  if IsDefined(request) && CyberwarePolicy.Suppresses(this.m_owner, request.itemID) { return; }
  wrappedMethod(request);
}

@wrapMethod(EquipmentSystemPlayerData)
public final func OnPartUninstallRequest(request: ref<PartUninstallRequest>) -> Void {
  if IsDefined(request) && CyberwarePolicy.Suppresses(this.m_owner, request.itemID) { return; }
  wrappedMethod(request);
}

@wrapMethod(EquipmentSystem)
public final static func IsCyberdeckEquipped(owner: ref<GameObject>) -> Bool {
  if CyberwarePolicy.OperatingSystemDisabled(owner) { return false; }
  return wrappedMethod(owner);
}

@wrapMethod(Device)
protected const final func IsCyberdeckEquippedOnPlayer() -> Bool {
  if CyberwarePolicy.OperatingSystemDisabled(GetPlayer(this.GetGame())) { return false; }
  return wrappedMethod();
}

@wrapMethod(RPGManager)
public final static func GetPlayerQuickHackListWithQuality(player: wref<PlayerPuppet>) -> array<PlayerQuickhackData> {
  if CyberwarePolicy.OperatingSystemDisabled(player) { PlayerPuppet.ChacheQuickHackListCleanup(player); }
  return wrappedMethod(player);
}

@wrapMethod(QuickHackableHelper)
public final static func TryToCycleOverclockedState(player: ref<GameObject>) -> Bool {
  if CyberwarePolicy.OperatingSystemDisabled(player) { return false; }
  return wrappedMethod(player);
}

@wrapMethod(PlayerPuppet)
private final func ActivateIconicCyberware() -> Void {
  if CyberwarePolicy.OperatingSystemDisabled(this) { return; }
  wrappedMethod();
}

public class ResetPostTowerArmAppearance extends ScriptableSystemRequest {
  public let owner: wref<GameObject>;
}

@addMethod(CyberwareCustomizationSystem)
private final func OnResetPostTowerArmAppearance(request: ref<ResetPostTowerArmAppearance>) -> Void {
  if request.owner != this.m_playerPuppet || !CyberwarePolicy.Active(request.owner) ||
    !CyberwarePolicy.Safe(request.owner as PlayerPuppet) { return; }
  let equipment = EquipmentSystem.GetData(request.owner);
  if !IsDefined(equipment) || ItemID.IsValid(equipment.GetActiveItem(gamedataEquipmentArea.ArmsCW)) ||
    ItemID.IsValid(equipment.GetActiveItem(gamedataEquipmentArea.ArmsCWStyle)) { return; }
  if this.savedData.enabled || this.savedData.switcherIndex != 0u {
    this.savedData.enabled = false;
    this.savedData.switcherIndex = 0u;
    this.RestoreCyberwareCustomization(true);
  }
  if this.savedData.hasMaxTacApperanceEquipped { this.RemoveMaxTacApperance(); }
}

@wrapMethod(CoolExitJumpEvents)
protected func OnEnter(stateContext: ref<StateContext>, scriptInterface: ref<StateGameScriptInterface>) -> Void {
  let owner = scriptInterface.executionOwner;
  let disableLegBoost = false;
  if CyberwarePolicy.Active(owner) {
    let equipment = EquipmentSystem.GetData(owner);
    if IsDefined(equipment) {
      let legs = equipment.GetActiveItem(gamedataEquipmentArea.LegsCW);
      let magnitude = stateContext.GetTemporaryIntParameter(n"coolExitMagnitude");
      disableLegBoost = CyberwarePolicy.Suppresses(owner, legs) && ItemID.IsOfTDBID(legs, t"Items.ReinforcedMusclesRare") &&
        magnitude.valid && Equals(IntEnum<vehicleCoolExitImpulseLevel>(magnitude.value), vehicleCoolExitImpulseLevel.MaxImpulse) &&
        !stateContext.GetTemporaryVectorParameter(n"exitMomentum").valid;
    }
  }
  wrappedMethod(stateContext, scriptInterface);
  if disableLegBoost {
    let impulse = stateContext.GetTemporaryVectorParameter(n"impulse");
    if impulse.valid {
      let value = impulse.value;
      value.Z -= this.GetStaticFloatParameterDefault("chargeJumpHeight", 10.0);
      stateContext.SetTemporaryVectorParameter(n"impulse", value, true);
    }
  }
}
