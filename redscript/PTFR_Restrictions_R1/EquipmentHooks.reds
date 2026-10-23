module PTFR.RestrictionsR1

@addField(EquipmentSystemPlayerData)
private let ptfrr1PreserveParts: ItemID;

@wrapMethod(EquipmentSystemPlayerData)
public final func AssignItemToHotkey(newID: ItemID, hotkey: EHotkey) -> Void {
  // Buying a retained implant must not auto-bind its active ability.
  // None / ordinary replacement consumables from native unequip pass through.
  if CyberwarePolicy.Denied(this.m_owner, newID) { return; }
  wrappedMethod(newID, hotkey);
}

@addMethod(EquipmentSystemPlayerData)
public final const func PTFRR1OriginalPurchaseRequirements(itemData: wref<gameItemData>) -> Bool {
  // Exact current 2.31 IsEquippable checks, used ONLY for inventory purchase
  // admission. Never temporarily disable the install policy to call a wrapper.
  if !IsDefined(itemData) || RPGManager.IsItemBroken(itemData) { return false; }
  if !this.CheckEquipPrereqs(itemData.GetID(), itemData.GetVariant()) { return false; }
  let level = GameInstance.GetStatsSystem(this.m_owner.GetGame()).GetStatValue(Cast<StatsObjectID>(this.m_owner.GetEntityID()), gamedataStatType.Level);
  return level >= Cast<Float>(FloorF(itemData.GetStatValueByType(gamedataStatType.Level)));
}

@wrapMethod(EquipmentSystemPlayerData)
public final const func IsEquippable(itemData: wref<gameItemData>) -> Bool {
  if IsDefined(itemData) && CyberwarePolicy.Denied(this.m_owner, itemData.GetID()) { return false; }
  return wrappedMethod(itemData);
}

@wrapMethod(EquipmentSystemPlayerData)
public final func OnRestored() -> Void {
  wrappedMethod(); // Keep EquipmentEx and vanilla restoration chains intact.
  let policy = CyberwarePolicy.Get(this.m_owner.GetGame());
  if IsDefined(policy) { policy.Restored(); }
}

@addMethod(EquipmentSystemPlayerData)
public final func PTFRR1RestrictedEquipped() -> array<ItemID> {
  let ids: array<ItemID>;
  let i = 0;
  let j: Int32;
  while i < ArraySize(this.m_equipment.equipAreas) {
    if CyberwarePolicy.Area(this.m_equipment.equipAreas[i].areaType) {
      j = 0;
      while j < ArraySize(this.m_equipment.equipAreas[i].equipSlots) {
        let id = this.m_equipment.equipAreas[i].equipSlots[j].itemID;
        if CyberwarePolicy.Restricted(id) && !ArrayContains(ids, id) { ArrayPush(ids, id); }
        j += 1;
      }
    }
    i += 1;
  }
  return ids;
}

@addMethod(EquipmentSystemPlayerData)
public final func PTFRR1Remove(id: ItemID) -> Int32 {
  if !CyberwarePolicy.Denied(this.m_owner, id) || !CyberwarePolicy.Safe(this.m_owner as PlayerPuppet) { return 0; }
  let ts = GameInstance.GetTransactionSystem(this.m_owner.GetGame());
  let item = ts.GetItemData(this.m_owner, id);
  let area = this.GetEquipAreaIndex(EquipmentSystem.GetEquipAreaType(id));
  let slot = this.GetSlotIndex(id);
  if !IsDefined(item) || area < 0 || slot < 0 || item.HasTag(n"UnequipBlocked") { return 0; }
  if this.GetItemInEquipSlot(area, slot) != id { return 0; }
  let quantity = ts.GetItemQuantity(this.m_owner, id);
  let before: array<InnerItemData>;
  let after: array<InnerItemData>;
  item.GetItemParts(before);
  this.ptfrr1PreserveParts = id;
  this.UnequipItem(area, slot, false);
  this.ptfrr1PreserveParts = ItemID.None();
  // Native RemoveEquipGLPs processes the item AND attached parts. Retain the
  // owned part tree instead of relying on undocumented RemovePart disposition.
  let readback = ts.GetItemData(this.m_owner, id);
  if !IsDefined(readback) || ts.GetItemQuantity(this.m_owner, id) != quantity { return -1; }
  readback.GetItemParts(after);
  if ArraySize(before) != ArraySize(after) { return -1; }
  let i = 0;
  let j: Int32;
  let found: Bool;
  while i < ArraySize(before) {
    found = false; j = 0;
    while j < ArraySize(after) {
      if InnerItemData.GetItemID(before[i]) == InnerItemData.GetItemID(after[j]) &&
        InnerItemData.GetSlotID(before[i]) == InnerItemData.GetSlotID(after[j]) { found = true; break; }
      j += 1;
    }
    if !found { return -1; }
    i += 1;
  }
  ModLog(n"PTFR_Restrictions_R1", "Conserved " + TDBID.ToStringDEBUG(ItemID.GetTDBID(id)) + " quantity=" + ToString(quantity) + " attachedParts=" + ToString(ArraySize(after)));
  return this.GetItemInEquipSlot(area, slot) == ItemID.None() ? 1 : 0;
}

@wrapMethod(EquipmentSystemPlayerData)
private final func UnequipCyberwareParts(cyberwareData: wref<gameItemData>) -> Void {
  if IsDefined(cyberwareData) && ItemID.IsValid(this.ptfrr1PreserveParts) && this.ptfrr1PreserveParts == cyberwareData.GetID() { return; }
  wrappedMethod(cyberwareData);
}

@wrapMethod(EquipmentSystemPlayerData)
public final func OnReplaceEquipmentRequest(request: ref<ReplaceEquipmentRequest>) -> Void {
  // Before GiveItems, old-item unequip, transfer and RemoveItem.
  if IsDefined(request) && CyberwarePolicy.Denied(this.m_owner, request.itemID) { return; }
  wrappedMethod(request);
}

@wrapMethod(RPGManager)
public final static func CanUpgradeCyberware(owner: ref<GameObject>, itemID: ItemID, isEquipped: Bool, selectedQuality: gamedataQuality, out upgradeItemQuality: gamedataQuality, out upgradeItemRecord: ref<Item_Record>, out costData: CyberwareUpgradeCostData, opt updateOutputOnFailure: Bool) -> Bool {
  if CyberwarePolicy.Denied(owner, itemID) { return false; }
  let result = wrappedMethod(owner, itemID, isEquipped, selectedQuality, upgradeItemQuality, upgradeItemRecord, costData, updateOutputOnFailure);
  if IsDefined(upgradeItemRecord) && CyberwarePolicy.Denied(owner, ItemID.FromTDBID(upgradeItemRecord.GetID())) { return false; }
  return result;
}

@wrapMethod(RPGManager)
public final static func HandleBuyShardPopupClosed(owner: ref<GameObject>, equippedItemId: ItemID, resultData: ref<RipperdocTokenPopupCloseData>) -> Void {
  // Before the upgrade charge and seed increment, not merely the later queue.
  if CyberwarePolicy.Denied(owner, equippedItemId) || (IsDefined(resultData.chosenOptionData) && CyberwarePolicy.Denied(owner, resultData.chosenOptionData.GetID())) { return; }
  wrappedMethod(owner, equippedItemId, resultData);
}

@wrapMethod(ItemActionsHelper)
public final static func UseItem(executor: wref<GameObject>, itemID: ItemID) -> Bool {
  if CyberwarePolicy.Denied(executor, itemID) { return false; }
  return wrappedMethod(executor, itemID);
}

// These are independent overloads in 2.31; neither delegates to the other.
@wrapMethod(ItemActionsHelper)
public final static func ProcessItemAction(gi: GameInstance, executor: wref<GameObject>, itemData: wref<gameItemData>, actionID: TweakDBID, fromInventory: Bool) -> Bool {
  if CyberwarePolicy.DeniedAction(executor, itemData, actionID) { return false; }
  return wrappedMethod(gi, executor, itemData, actionID, fromInventory);
}
@wrapMethod(ItemActionsHelper)
public final static func ProcessItemAction(gi: GameInstance, executor: wref<GameObject>, itemData: wref<gameItemData>, actionID: TweakDBID, fromInventory: Bool, quantity: Int32) -> Bool {
  if CyberwarePolicy.DeniedAction(executor, itemData, actionID) { return false; }
  return wrappedMethod(gi, executor, itemData, actionID, fromInventory, quantity);
}
