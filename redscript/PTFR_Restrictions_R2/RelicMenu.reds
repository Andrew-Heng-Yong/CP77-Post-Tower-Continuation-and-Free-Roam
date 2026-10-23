module PTFR.RestrictionsR2

// Menu-only policy mask. Never writes ep1_tree_unlocked or any quest fact.
@addMethod(NewPerksCategoriesGameController)
private final func PTFRR2RelicClosed() -> Bool {
  let player = this.m_player;
  if !IsDefined(player) { player = this.GetPlayerControlledObject() as PlayerPuppet; }
  return BodyPolicy.BlockRelic(player);
}

@wrapMethod(NewPerksCategoriesGameController)
private final func UpdateJohnnyEspionageAttribute() -> Void {
  let closed = this.PTFRR2RelicClosed();
  if closed { this.m_isEspionageUnlocked = false; }
  wrappedMethod();
  if !closed { return; }
  inkWidgetRef.SetVisible(this.m_espionagePointsRef, false);
  let i = 0;
  while i < ArraySize(this.m_attributesControllersList) {
    // Do not expose the pre-expansion Johnny placeholder instead of the tree.
    if Equals(this.m_attributesControllersList[i].GetAttributeType(), PerkMenuAttribute.Espionage) ||
      Equals(this.m_attributesControllersList[i].GetAttributeType(), PerkMenuAttribute.Johnny) {
      this.m_attributesControllersList[i].GetRootWidget().SetVisible(false);
    }
    i += 1;
  }
}

@wrapMethod(NewPerksCategoriesGameController)
private final func OpenPerksScreen(statType: gamedataStatType, direction: NewPerkTabsArrowDirection) -> Void {
  if this.PTFRR2RelicClosed() && Equals(statType, gamedataStatType.Espionage) { return; }
  wrappedMethod(statType, direction);
}

@wrapMethod(NewPerksCategoriesGameController)
private final func InitializePerkScreen() -> Void {
  if this.PTFRR2RelicClosed() {
    this.m_isEspionageUnlocked = false;
    if Equals(this.m_currentStatScreen, gamedataStatType.Espionage) {
      this.CloseActiveScreen(); return;
    }
  }
  wrappedMethod();
}

@wrapMethod(NewPerksCategoriesGameController)
protected cb func OnTabMenuArrowClicked(evt: ref<NewPerksTabArrowClickedEvent>) -> Bool {
  // Native modulo then cycles five ordinary attributes, not six with Relic.
  if this.PTFRR2RelicClosed() { this.m_isEspionageUnlocked = false; }
  return wrappedMethod(evt);
}

@wrapMethod(NewPerksCategoriesGameController)
private final func PlayRelicIntroAnim() -> Void {
  if this.PTFRR2RelicClosed() { return; }
  wrappedMethod();
}
