module PTFR.RestrictionsR1

@addMethod(EquipmentSystemPlayerData)
public final const func PTFRCF1PreservesExactItem(id: ItemID) -> Bool {
  // This transient ID is set only around PTFRR1Remove's native UnequipItem call.
  return ItemID.IsValid(id) && ItemID.IsValid(this.ptfrr1PreserveParts) &&
    id == this.ptfrr1PreserveParts && CyberwarePolicy.Denied(this.m_owner, id);
}

@wrapMethod(PowerUpCyberwareEffector)
protected func Uninitialize(game: GameInstance) -> Void {
  // Native RemoveSlotGLPs runs before clearing the equipped item. Its Skeleton
  // effector deletes the enhanced instance here. PTFR promises to retain the
  // exact existing inventory/part tree, so suppress only that deletion while
  // its bounded native unequip is in progress. All other cleanup stays native.
  if IsDefined(this.m_playerData) && IsDefined(this.m_owner) &&
    this.m_playerData == EquipmentSystem.GetData(this.m_owner) &&
    Equals(this.m_targetEquipArea, gamedataEquipmentArea.MusculoskeletalSystemCW) &&
    this.m_targetEquipSlotIndex >= 0 &&
    this.m_targetEquipSlotIndex < this.m_playerData.GetNumberOfSlots(this.m_targetEquipArea, true) {
    let id = this.m_playerData.GetItemInEquipSlot(this.m_targetEquipArea, this.m_targetEquipSlotIndex);
    if this.m_playerData.PTFRCF1PreservesExactItem(id) {
      ModLog(n"PTFR_CyberwareCF1", "Preserved exact Skeleton instance during native slot cleanup: " +
        TDBID.ToStringDEBUG(ItemID.GetTDBID(id)) + " slot=" + ToString(this.m_targetEquipSlotIndex));
      return;
    }
  }
  wrappedMethod(game);
}
