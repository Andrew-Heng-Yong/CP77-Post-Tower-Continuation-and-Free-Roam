module PTFR.RestrictionsR1

@wrapMethod(RipperDocGameController)
private final func CheckIfCanEquip(itemData: wref<gameItemData>, equipped: wref<gameItemData>) -> Bool {
  if IsDefined(itemData) && CyberwarePolicy.Denied(this.m_player, itemData.GetID()) { return false; }
  return wrappedMethod(itemData, equipped);
}
@wrapMethod(RipperDocGameController)
private final func CheckIfCanEquip(itemData: wref<gameItemData>, itemArea: gamedataEquipmentArea) -> Bool {
  if IsDefined(itemData) && CyberwarePolicy.Denied(this.m_player, itemData.GetID()) { return false; }
  return wrappedMethod(itemData, itemArea);
}
@wrapMethod(RipperDocGameController)
private final func EquipCyberware(itemData: wref<gameItemData>) -> Bool {
  // Before native code unequips the old slot and animates the new installation.
  if IsDefined(itemData) && CyberwarePolicy.Denied(this.m_player, itemData.GetID()) {
    this.m_isInEquipPopup = false;
    return false;
  }
  return wrappedMethod(itemData);
}

@addField(RipperDocGameController)
private let ptfrr1BuyOnly: ItemID;
@addField(RipperDocGameController)
private let ptfrr1Buyback: Bool;
@addField(RipperDocGameController)
private let ptfrr1VendorRequirement: ref<VendorItemAdditionalData>;
@addField(VendorConfirmationPopupData)
public let ptfrr1BuyOnly: Bool;

@addMethod(RipperDocGameController)
private final func PTFRR1Price(id: ItemID, buyback: Bool) -> Int32 {
  return buyback ? this.m_VendorDataManager.GetSellingPrice(id) : this.m_VendorDataManager.GetBuyingPrice(id);
}

@wrapMethod(RipperDocGameController)
protected cb func OnSlotClick(evt: ref<ItemDisplayClickEvent>) -> Bool {
  let item = evt.uiInventoryItem;
  if !IsDefined(item) || !CyberwarePolicy.Denied(this.m_player, item.GetID()) || !evt.actionName.IsAction(n"click") ||
    !evt.displayContextData.IsVendorItem() || NotEquals(this.m_screen, CyberwareScreenType.Ripperdoc) { return wrappedMethod(evt); }
  if !this.m_isActivePanel || Equals(this.m_hoverArea, gamedataEquipmentArea.Invalid) || !this.m_isCapacityBarReady ||
    !this.m_isArmorBarReady || this.m_isPurchasing || IsDefined(this.m_tokenPopup) || ItemID.IsValid(this.ptfrr1BuyOnly) { return false; }
  let vendorData = evt.additionalData as VendorItemAdditionalData;
  // Let the vanilla notification path explain original vendor/story/funds requirements.
  if (IsDefined(vendorData) && !vendorData.IsAvailable) ||
    this.PTFRR1Price(item.GetID(), evt.isBuybackStack) > this.m_VendorDataManager.GetLocalPlayerCurrencyAmount() { return wrappedMethod(evt); }
  if item.GetItemData().HasTag(n"MustBeWearableToPurchase") &&
    !EquipmentSystem.GetData(this.m_player).PTFRR1OriginalPurchaseRequirements(item.GetItemData()) { return wrappedMethod(evt); }
  let popup = new VendorConfirmationPopupData();
  popup.notificationName = n"base\\gameplay\\gui\\widgets\\notifications\\vendor_confirmation.inkwidget";
  popup.isBlocking = true; popup.useCursor = true; popup.queueName = n"modal_popup";
  popup.inventoryItem = item; popup.quantity = 1;
  popup.type = VendorConfirmationPopupType.BuyNotEquipableCyberware;
  popup.price = this.PTFRR1Price(item.GetID(), evt.isBuybackStack);
  popup.ptfrr1BuyOnly = true;
  this.ptfrr1BuyOnly = item.GetID(); this.ptfrr1Buyback = evt.isBuybackStack;
  this.ptfrr1VendorRequirement = vendorData;
  this.m_isInEquipPopup = true; this.m_isPurchasing = true;
  this.m_tokenPopup = this.ShowGameNotification(popup);
  this.m_tokenPopup.RegisterListener(this, n"OnPTFRR1BuyClosed");
  this.m_buttonHintsController.Hide();
  return true;
}

@addMethod(RipperDocGameController)
protected cb func OnPTFRR1BuyClosed(data: ref<inkGameNotificationData>) -> Bool {
  let result = data as VendorConfirmationPopupCloseData;
  this.m_tokenPopup = null; this.m_isInEquipPopup = false;
  this.m_buttonHintsController.Show();
  if !IsDefined(result) || !result.confirm || !IsDefined(result.inventoryItem) || result.inventoryItem.GetID() != this.ptfrr1BuyOnly {
    this.ptfrr1BuyOnly = ItemID.None(); this.m_isPurchasing = false;
    this.AnimateMinigrids(); return false;
  }
  let item = result.inventoryItem.GetItemData();
  // Recheck original requirements and funds BEFORE committing the transaction.
  if (IsDefined(this.ptfrr1VendorRequirement) && !this.ptfrr1VendorRequirement.IsAvailable) ||
    this.PTFRR1Price(item.GetID(), this.ptfrr1Buyback) > this.m_VendorDataManager.GetLocalPlayerCurrencyAmount() ||
    (item.HasTag(n"MustBeWearableToPurchase") && !EquipmentSystem.GetData(this.m_player).PTFRR1OriginalPurchaseRequirements(item)) {
    this.ptfrr1BuyOnly = ItemID.None(); this.m_isPurchasing = false; return false;
  }
  // Intent remains buy-only even if the profile is changed by another script.
  if this.ptfrr1Buyback { this.m_VendorDataManager.BuybackItemFromVendor(item, 1); }
  else { this.m_VendorDataManager.BuyItemFromVendor(item, 1); }
  return true;
}

@wrapMethod(RipperDocGameController)
public final func OnItemBought(itemID: ItemID, itemData: wref<gameItemData>) -> Void {
  if ItemID.IsValid(this.ptfrr1BuyOnly) {
    // Inventory callbacks also report unrelated grants and generated parts.
    // Never let those enter native auto-install while our purchase is pending.
    if ItemID.GetTDBID(itemID) != ItemID.GetTDBID(this.ptfrr1BuyOnly) { return; }
    this.ptfrr1BuyOnly = ItemID.None(); this.ptfrr1Buyback = false;
    this.m_isPurchased = false; this.m_isPurchasing = false; this.m_isPurchaseEquip = false; this.m_isInEquipPopup = false;
    this.RemoveCachedVendorItem(itemID);
    this.m_InventoryManager.MarkToRebuild();
    this.PreparePlayerItems(); this.PrepareVendorItems(); this.RefreshInventoryNextFrame();
    this.HideInventoryTutorial();
    return; // No EquipCyberware, request, capacity change or installation animation.
  }
  wrappedMethod(itemID, itemData);
}

@wrapMethod(RipperDocGameController)
protected cb func OnBuyConfirmationPopupClosed(data: ref<inkGameNotificationData>) -> Bool {
  let result = data as VendorConfirmationPopupCloseData;
  // A formerly permitted buy-and-install may no longer be permitted. Cancel
  // before payment; never silently reinterpret that confirmation as buy-only.
  if IsDefined(result) && result.confirm && IsDefined(result.inventoryItem) && CyberwarePolicy.Denied(this.m_player, result.inventoryItem.GetID()) {
    result.confirm = false;
  }
  return wrappedMethod(data);
}

@wrapMethod(VendorConfirmationPopup)
protected cb func OnInitialize() -> Bool {
  let result = wrappedMethod();
  if IsDefined(this.m_data) && this.m_data.ptfrr1BuyOnly {
    inkTextRef.SetText(this.m_itemNameText, "Buy to inventory? Installation blocked by post-Tower restrictions.");
  }
  return result;
}

@wrapMethod(RipperDocGameController)
private final func SetButtonHintsHover(item: wref<UIInventoryItem>, isVendorItem: Bool) -> Void {
  wrappedMethod(item, isVendorItem);
  if IsDefined(item) && CyberwarePolicy.Denied(this.m_player, item.GetID()) {
    this.m_buttonHintsController.RemoveButtonHint(n"select");
    this.m_buttonHintsController.RemoveButtonHint(n"upgrade_perk");
    this.m_buttonHintsController.RemoveButtonHint(this.m_upgradeCWInputName);
    this.m_buttonHintsController.AddButtonHint(n"select", isVendorItem ? "Buy to inventory (installation blocked)" : "Installation blocked: post-Tower");
  }
}

// Separate presentation from native SetLocked/IsLocked so browsing still works.
@addField(InventoryItemDisplayController)
private let ptfrr1SlotPlayer: wref<GameObject>;
@addField(InventoryItemDisplayController)
private let ptfrr1SlotArea: gamedataEquipmentArea;

@addMethod(InventoryItemDisplayController)
public final func PTFRR1Slot(player: ref<GameObject>, area: gamedataEquipmentArea) -> Void {
  this.ptfrr1SlotPlayer = player; this.ptfrr1SlotArea = area;
  this.NewUpdateLocked(this.GetUIInventoryItem());
}
@addMethod(InventoryItemDisplayController)
private final func PTFRR1PaintLock() -> Void {
  if !CyberwarePolicy.Active(this.ptfrr1SlotPlayer) || !CyberwarePolicy.Area(this.ptfrr1SlotArea) || this.m_isLocked || this.m_isPerkRequiredCyberware { return; }
  let mixed = Equals(this.ptfrr1SlotArea, gamedataEquipmentArea.EyesCW) || Equals(this.ptfrr1SlotArea, gamedataEquipmentArea.HandsCW);
  let item = this.GetUIInventoryItem();
  if mixed && (!IsDefined(item) || !CyberwarePolicy.Restricted(item.GetID())) { return; }
  inkWidgetRef.SetState(this.m_widgetWrapper, n"Locked"); inkWidgetRef.SetVisible(this.m_lockIcon, true);
  let i = 0;
  while i < ArraySize(this.m_backgroundFrames) { inkWidgetRef.SetState(this.m_backgroundFrames[i], n"Locked"); i += 1; }
}
@wrapMethod(InventoryItemDisplayController)
protected func NewUpdateLocked(itemData: ref<UIInventoryItem>) -> Void { wrappedMethod(itemData); this.PTFRR1PaintLock(); }
@wrapMethod(InventoryItemDisplayController)
protected func UpdateLocked() -> Void { wrappedMethod(); this.PTFRR1PaintLock(); }

@wrapMethod(CyberwareInventoryMiniGrid)
protected cb func OnSlotSpawned(widget: ref<inkWidget>, userData: ref<IScriptable>) -> Bool {
  let result = wrappedMethod(widget, userData);
  let controller = widget.GetController() as InventoryItemDisplayController;
  if IsDefined(controller) { controller.PTFRR1Slot(this.m_player, this.m_equipArea); }
  return result;
}
@wrapMethod(CyberwareInventoryMiniGrid)
public final func UpdateData(equipArea: gamedataEquipmentArea, playerEquipAreaInventory: script_ref<[wref<UIInventoryItem>]>, opt screen: CyberwareScreenType) -> Void {
  wrappedMethod(equipArea, playerEquipAreaInventory, screen);
  let i = 0;
  while i < ArraySize(this.m_gridData) { this.m_gridData[i].PTFRR1Slot(this.m_player, equipArea); i += 1; }
}

@addField(RipperdocCategoryTooltipData)
public let ptfrr1Active: Bool;

@wrapMethod(RipperDocGameController)
private final func ShowCategoryTooltip(equipArea: gamedataEquipmentArea) -> Void {
  if !CyberwarePolicy.Active(this.m_player) { wrappedMethod(equipArea); return; }
  let data = new RipperdocCategoryTooltipData();
  data.category = equipArea;
  data.availableItems = this.GetCachedAvailableItemCounters(equipArea);
  data.ownedItems = data.availableItems - this.GetCachedVendorItemCounters(equipArea);
  data.screenType = this.m_screen; data.ptfrr1Active = true;
  this.m_TooltipsManager.AttachToCursor();
  this.m_TooltipsManager.ShowTooltip(n"RipperdocCategoryTooltip", data, this.m_defaultTooltipsMargin);
}

@wrapMethod(RipperdocCategoryTooltip)
public func SetData(tooltipData: ref<ATooltipData>) -> Void {
  wrappedMethod(tooltipData);
  let data = tooltipData as RipperdocCategoryTooltipData;
  if IsDefined(data) && data.ptfrr1Active && CyberwarePolicy.Area(data.category) {
    let note = "Installation blocked by post-Tower restrictions. Browse and buy to inventory.";
    if Equals(data.category, gamedataEquipmentArea.EyesCW) { note = "Only stock Basic Kiroshi Optics may be installed. Other models: inventory purchases only."; }
    if Equals(data.category, gamedataEquipmentArea.HandsCW) { note = "Only Tattoo: Johnny's Special may be installed. Other models: inventory purchases only."; }
    inkTextRef.SetText(this.m_desc, note);
  }
}
