module PTFR.RestrictionsR3

import PTFR.RestrictionsR1.*
import PTFR.RestrictionsR2.*

@addMethod(PlayerDevelopmentSystem)
public final func PTFRR3SellPerk(owner: ref<GameObject>, perk: gamedataNewPerkType) -> Bool {
  if !ProfilePolicy.OwnPerk(owner, perk) || !BodyPolicy.Safe(owner as PlayerPuppet) ||
    !ProfilePolicy.PerkDenied(owner, perk) || !ProfilePolicy.EmptyNativeSideEffectSlots(owner as PlayerPuppet) { return false; }
  let data = this.GetDevelopmentData(owner);
  if !IsDefined(data) || data.IsNewPerkBought(perk) <= 0 || !data.CheckIfAllnewPerkParentSold(perk) { return false; }
  let admission = PlayerDevelopmentSystem.CanSellNewPerk(owner as PlayerPuppet, perk);
  if !admission.success { return false; }
  return this.SellNewPerk(owner, perk);
}

@wrapMethod(PlayerDevelopmentData)
private final const func GetNewPerkGLPackageTDBID(perkType: gamedataNewPerkType, perkLevel: Int32) -> TweakDBID {
  // Stock Built Different has one level pointing at absent record 91068214685.
  // Its purchase-rank gate is its behavior. Avoid the native-script null
  // dereference ONLY in our acknowledged sale, never invent a replacement GLP.
  if ProfilePolicy.OwnPerk(this.m_owner, perkType) && Equals(perkType, gamedataNewPerkType.Tech_Central_Perk_3_3) && perkLevel == 0 {
    let record = RPGManager.GetNewPerkRecord(perkType);
    let levels = TweakDBInterface.GetForeignKeyArray(t"NewPerks.Tech_Central_Perk_3_3.levels");
    if IsDefined(record) && ArraySize(levels) == 1 && TDBID.ToNumber(levels[0]) == 91068214685ul && !IsDefined(record.GetLevelsItem(0)) {
      return TDBID.None();
    }
  }
  return wrappedMethod(perkType, perkLevel);
}

@addMethod(EquipmentSystemPlayerData)
public final func PTFRR3MoveTattooToFirst() -> Bool {
  if !ProfilePolicy.OwnHand(this.m_owner) || !BodyPolicy.Safe(this.m_owner as PlayerPuppet) || this.IsEquipPending() { return false; }
  let area = this.GetEquipAreaIndex(gamedataEquipmentArea.HandsCW);
  if area < 0 || this.GetNumberOfSlots(gamedataEquipmentArea.HandsCW, true) != 2 { return false; }
  let id = this.GetItemInEquipSlot(area, 1);
  if !ItemID.IsValid(id) || ItemID.IsValid(this.GetItemInEquipSlot(area, 0)) { return false; }
  let record = ItemID.GetTDBID(id);
  if record != t"Items.CasiusTattoo" && record != t"Items.AdvancedCasiusTattoo" { return false; }
  if !CyberwarePolicy.Approved(record) { return false; }
  let ts = GameInstance.GetTransactionSystem(this.m_owner.GetGame());
  let item = ts.GetItemData(this.m_owner, id);
  if !IsDefined(item) || item.HasTag(n"UnequipBlocked") || !this.IsEquippable(item) { return false; }
  let count = ts.GetItemQuantity(this.m_owner, id);
  let before: array<InnerItemData>; let after: array<InnerItemData>;
  item.GetItemParts(before);
  this.ptfrr1PreserveParts = id;
  this.UnequipItem(area, 1, false);
  if !ItemID.IsValid(this.GetItemInEquipSlot(area, 1)) && !ItemID.IsValid(this.GetItemInEquipSlot(area, 0)) {
    this.EquipItem(id, 0, false, false);
  }
  this.ptfrr1PreserveParts = ItemID.None();
  let readback = ts.GetItemData(this.m_owner, id);
  if !IsDefined(readback) || ts.GetItemQuantity(this.m_owner, id) != count ||
    this.GetItemInEquipSlot(area, 0) != id || ItemID.IsValid(this.GetItemInEquipSlot(area, 1)) { return false; }
  readback.GetItemParts(after);
  if ArraySize(before) != ArraySize(after) { return false; }
  let i = 0; let j: Int32; let found: Bool;
  while i < ArraySize(before) {
    j = 0; found = false;
    while j < ArraySize(after) {
      if InnerItemData.GetItemID(before[i]) == InnerItemData.GetItemID(after[j]) && InnerItemData.GetSlotID(before[i]) == InnerItemData.GetSlotID(after[j]) { found = true; break; }
      j += 1;
    }
    if !found { return false; } i += 1;
  }
  return true;
}

@wrapMethod(ShootEvents)
protected final func OnEnter(stateContext: ref<StateContext>, scriptInterface: ref<StateGameScriptInterface>) -> Void {
  // Before native attack selection and the Shoot animation/event dispatch.
  ProfilePhysical.EnforceWeapon(this.GetWeaponObject(scriptInterface), scriptInterface.executionOwner);
  wrappedMethod(stateContext, scriptInterface);
}

@wrapMethod(DriverCombatFirearmsEvents)
private final func EnableSmartGunHandler(enable: Bool) -> Void {
  if CyberwarePolicy.Active(this.m_executionOwner) { wrappedMethod(false); return; }
  wrappedMethod(enable);
}

@wrapMethod(WeaponObject)
protected cb func OnGameAttached() -> Bool {
  wrappedMethod();
  ProfilePhysical.EnforceWeapon(this, this.GetOwner());
}

@addField(WeaponObject)
private let ptfrr3Straight: Bool;

@addMethod(WeaponObject)
public final func PTFRR3Straight(enabled: Bool) -> Void {
  if enabled { this.ptfrr3Straight = true; this.ShootStraight(true); }
  else { if this.ptfrr3Straight { this.ShootStraight(false); this.ptfrr3Straight = false; } }
}

@wrapMethod(WeaponObject)
protected cb func OnDetach() -> Bool {
  this.PTFRR3Straight(false);
  wrappedMethod();
}
