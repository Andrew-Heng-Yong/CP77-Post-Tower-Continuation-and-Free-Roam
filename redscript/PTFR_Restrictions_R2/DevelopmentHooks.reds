module PTFR.RestrictionsR2

import PTFR.RestrictionsR1.*
import PTFR.RestrictionsR3.*

// Save-local evidence, not a snapshot that may be restored over later progress.
public struct BodySnapshot {
  public persistent let valid: Bool;
  public persistent let body: Int32;
  public persistent let liveBody: Float;
  public persistent let attributeSpent: Int32;
  public persistent let attributeUnspent: Int32;
  public persistent let primarySpent: Int32;
  public persistent let primaryUnspent: Int32;
  public persistent let relicSpent: Int32;
  public persistent let relicUnspent: Int32;
  public persistent let attributes: array<SAttribute>;
  public persistent let devPoints: array<SDevelopmentPoints>;
  public persistent let perkRanks: array<Int32>;
  public persistent let profTypes: array<Int32>;
  public persistent let profLevels: array<Int32>;
  public persistent let profXP: array<Int32>;
  public persistent let profSpent: array<Int32>;
  public persistent let legacyPerkTypes: array<Int32>;
  public persistent let legacyPerkRanks: array<Int32>;
}

public abstract class BodyHookScope {
  public static func IsRelicPerk(perk: gamedataNewPerkType) -> Bool {
    if EnumInt(perk) < 0 || EnumInt(perk) >= EnumInt(gamedataNewPerkType.Count) { return false; }
    let record = RPGManager.GetNewPerkRecord(perk);
    return IsDefined(record) && IsDefined(record.Attribute()) && Equals(record.Attribute().Type(), gamedataAttributeDataType.EspionageAttributeData);
  }
  public static func IsBodyPerk(perk: gamedataNewPerkType) -> Bool {
    if EnumInt(perk) < 0 || EnumInt(perk) >= EnumInt(gamedataNewPerkType.Count) { return false; }
    let record = RPGManager.GetNewPerkRecord(perk);
    return IsDefined(record) && IsDefined(record.Attribute()) && Equals(record.Attribute().Type(), gamedataAttributeDataType.BodyAttributeData);
  }
}

@addMethod(PlayerDevelopmentData)
public final func PTFRR2Snapshot() -> BodySnapshot {
  let result: BodySnapshot;
  let i: Int32;
  let j: Int32;
  let k: Int32;
  let index: Int32;
  let seenAttributes: array<gamedataStatType>;
  let seenPoints: array<gamedataDevelopmentPointType>;
  let seenBuckets: array<gamedataAttributeDataType>;
  let seenPerks: array<gamedataNewPerkType>;
  let seenProfs: array<gamedataProficiencyType>;
  let record: ref<NewPerk_Record>;
  if !IsDefined(this.m_owner) { return result; }
  result.attributes = this.m_attributes;
  result.devPoints = this.m_devPoints;
  while i < ArraySize(this.m_attributes) {
    if ArrayContains(seenAttributes, this.m_attributes[i].attributeName) { return result; }
    ArrayPush(seenAttributes, this.m_attributes[i].attributeName);
    if Equals(this.m_attributes[i].attributeName, gamedataStatType.Strength) { result.body = this.m_attributes[i].value; }
    i += 1;
  }
  if !ArrayContains(seenAttributes, gamedataStatType.Strength) || !ArrayContains(seenAttributes, gamedataStatType.Reflexes) ||
    !ArrayContains(seenAttributes, gamedataStatType.Intelligence) || !ArrayContains(seenAttributes, gamedataStatType.TechnicalAbility) ||
    !ArrayContains(seenAttributes, gamedataStatType.Cool) { return result; }
  result.liveBody = this.GetAttributeValue(gamedataStatType.Strength);
  if result.body < 3 || result.body > 20 || result.liveBody != Cast<Float>(result.body) { return result; }
  i = 0;
  while i < ArraySize(this.m_devPoints) {
    if ArrayContains(seenPoints, this.m_devPoints[i].type) || this.m_devPoints[i].unspent < 0 || this.m_devPoints[i].spent < 0 { return result; }
    ArrayPush(seenPoints, this.m_devPoints[i].type);
    i += 1;
  }
  index = this.GetDevPointsIndex(gamedataDevelopmentPointType.Attribute);
  if index < 0 { return result; }
  result.attributeSpent = this.m_devPoints[index].spent;
  result.attributeUnspent = this.m_devPoints[index].unspent;
  index = this.GetDevPointsIndex(gamedataDevelopmentPointType.Primary);
  if index < 0 { return result; }
  result.primarySpent = this.m_devPoints[index].spent;
  result.primaryUnspent = this.m_devPoints[index].unspent;
  index = this.GetDevPointsIndex(gamedataDevelopmentPointType.Espionage);
  if index < 0 { return result; }
  result.relicSpent = this.m_devPoints[index].spent;
  result.relicUnspent = this.m_devPoints[index].unspent;
  if result.attributeSpent < result.body - 3 { return result; }
  ArrayResize(result.perkRanks, EnumInt(gamedataNewPerkType.Count));
  i = 0;
  while i < ArraySize(this.m_attributesData) {
    if ArrayContains(seenBuckets, this.m_attributesData[i].type) || EnumInt(this.m_attributesData[i].type) < 0 ||
      EnumInt(this.m_attributesData[i].type) >= EnumInt(gamedataAttributeDataType.Count) { return result; }
    ArrayPush(seenBuckets, this.m_attributesData[i].type);
    j = 0;
    while j < ArraySize(this.m_attributesData[i].unlockedPerks) {
      let perk = this.m_attributesData[i].unlockedPerks[j];
      k = EnumInt(perk.type);
      if k < 0 || k >= EnumInt(gamedataNewPerkType.Count) || ArrayContains(seenPerks, perk.type) || perk.currLevel < 0 { return result; }
      ArrayPush(seenPerks, perk.type);
      record = RPGManager.GetNewPerkRecord(perk.type);
      if !IsDefined(record) || !IsDefined(record.Attribute()) || NotEquals(record.Attribute().Type(), this.m_attributesData[i].type) ||
        perk.currLevel > record.GetLevelsCount() { return result; }
      result.perkRanks[k] = perk.currLevel;
      j += 1;
    }
    i += 1;
  }
  if ArraySize(seenBuckets) != EnumInt(gamedataAttributeDataType.Count) { return result; }
  i = 0;
  while i < ArraySize(this.m_proficiencies) {
    if ArrayContains(seenProfs, this.m_proficiencies[i].type) { return result; }
    ArrayPush(seenProfs, this.m_proficiencies[i].type);
    ArrayPush(result.profTypes, EnumInt(this.m_proficiencies[i].type));
    ArrayPush(result.profLevels, this.m_proficiencies[i].currentLevel);
    ArrayPush(result.profXP, this.m_proficiencies[i].currentExp);
    ArrayPush(result.profSpent, this.m_proficiencies[i].spentPerkPoints);
    i += 1;
  }
  i = 0;
  while i < ArraySize(this.m_perkAreas) {
    j = 0;
    while j < ArraySize(this.m_perkAreas[i].boughtPerks) {
      ArrayPush(result.legacyPerkTypes, EnumInt(this.m_perkAreas[i].boughtPerks[j].type));
      ArrayPush(result.legacyPerkRanks, this.m_perkAreas[i].boughtPerks[j].currLevel);
      j += 1;
    }
    i += 1;
  }
  result.valid = true;
  return result;
}

@addMethod(PlayerDevelopmentSystem)
public final func PTFRR2SellRelicPerk(owner: ref<GameObject>, perk: gamedataNewPerkType) -> Bool {
  if !BodyPolicy.OwnRelicPerk(owner, perk) || !BodyPolicy.Safe(owner as PlayerPuppet) || !BodyHookScope.IsRelicPerk(perk) || RelicCatalogue.Cost(perk) == 0 { return false; }
  let chrome = CyberwarePolicy.Get(owner.GetGame());
  let equipment = EquipmentSystem.GetData(owner);
  // Jailbreak's native removal may queue Monowire part removal if an arm is
  // equipped. Require settled cyberware removal and an empty arm slot first.
  if !IsDefined(chrome) || !chrome.PTFRR2Ready(owner as PlayerPuppet) || !IsDefined(equipment) ||
    ItemID.IsValid(equipment.GetItemInEquipSlot(gamedataEquipmentArea.ArmsCW, 0)) { return false; }
  let data = this.GetDevelopmentData(owner);
  if !IsDefined(data) || data.IsNewPerkBought(perk) != 1 || !data.CheckIfAllnewPerkParentSold(perk) { return false; }
  let allowed = PlayerDevelopmentSystem.CanSellNewPerk(owner as PlayerPuppet, perk);
  if !allowed.success { return false; }
  return this.SellNewPerk(owner, perk);
}

@addMethod(PlayerDevelopmentData)
public final func PTFRR2CompatibleBodyCosts(body: Int32) -> Bool {
  if !IsDefined(this.m_owner) || body < 3 || body > 20 { return false; }
  // Native ResetAttribute refunds one point per level. Match the Int32 cost
  // used by GetAttributeNextLevelCost, not the curve's raw Float precision.
  let curve = GameInstance.GetStatsDataSystem(this.m_owner.GetGame());
  let statName = EnumValueToName(n"gamedataStatType", Cast<Int64>(EnumInt(gamedataStatType.Strength)));
  let i = 4;
  while i <= body {
    let rawCost = curve.GetValueFromCurve(n"player_attributeLevelToCostIncrease", Cast<Float>(i), statName);
    // Reject non-finite/out-of-range values before the native-style conversion.
    if !(rawCost > 0.00 && rawCost < 2.00) { return false; }
    if Cast<Int32>(rawCost) != 1 { return false; }
    i += 1;
  }
  return true;
}

@addMethod(PlayerDevelopmentData)
public final func PTFRR2CanResetBody() -> Bool {
  let snapshot = this.PTFRR2Snapshot();
  return snapshot.valid && this.PTFRR2CompatibleBodyCosts(snapshot.body);
}

@addMethod(PlayerDevelopmentData)
public final func PTFRR2ResetBody() -> Bool {
  if !BodyPolicy.OwnBodyReset(this.m_owner) || !BodyPolicy.Safe(this.m_owner as PlayerPuppet) { return false; }
  let before = this.PTFRR2Snapshot();
  if !before.valid || !this.PTFRR2CompatibleBodyCosts(before.body) { return false; }
  let i = 0;
  while i < ArraySize(before.perkRanks) {
    if before.perkRanks[i] > 0 && BodyHookScope.IsBodyPerk(IntEnum<gamedataNewPerkType>(i)) { return false; }
    i += 1;
  }
  if before.body > 3 { this.ResetAttribute(gamedataStatType.Strength); }
  let after = this.PTFRR2Snapshot();
  return after.valid && after.body == 3 && after.liveBody == 3.00 &&
    after.attributeUnspent == before.attributeUnspent + before.body - 3 &&
    after.attributeSpent == before.attributeSpent - before.body + 3;
}

@addMethod(PlayerDevelopmentData)
public final func PTFRR2RelockBody() -> Bool {
  if !BodyPolicy.OwnMutation(this.m_owner) || !BodyPolicy.Safe(this.m_owner as PlayerPuppet) { return false; }
  let records: array<wref<NewPerk_Record>>;
  let body = RPGManager.GetAttributeDataRecord(gamedataAttributeDataType.BodyAttributeData);
  if !IsDefined(body) { return false; }
  body.Perks(records);
  let i = 0;
  while i < ArraySize(records) {
    if !IsDefined(records[i]) || !IsDefined(records[i].Tier()) || !BodyHookScope.IsBodyPerk(records[i].Type()) || this.IsNewPerkBought(records[i].Type()) != 0 { return false; }
    i += 1;
  }
  i = 0;
  while i < ArraySize(records) {
    if records[i].Tier().RequiredAttributePoints() > this.GetAttributePoints(gamedataAttributeDataType.BodyAttributeData) &&
      this.IsNewPerkUnlocked(records[i].Type()) {
      if !this.LockNewPerk(records[i].Type()) { return false; }
      let evt = new NewPerkLockedEvent();
      evt.perkType = records[i].Type();
      GameInstance.GetUISystem(this.m_owner.GetGame()).QueueEvent(evt);
    }
    i += 1;
  }
  return true;
}

@addMethod(PlayerDevelopmentData)
public final func PTFRR2PublishUI() -> Void {
  // Called after the policy has acknowledged the step and cleared authority.
  if BodyPolicy.BlockBody(this.m_owner) && BodyPolicy.Safe(this.m_owner as PlayerPuppet) { this.UpdateUIBB(); }
}

@addMethod(PlayerDevelopmentSystem)
public final func PTFRR2SellBodyPerk(owner: ref<GameObject>, perk: gamedataNewPerkType) -> Bool {
  if !BodyPolicy.OwnPerk(owner, perk) || !BodyPolicy.Safe(owner as PlayerPuppet) || !BodyHookScope.IsBodyPerk(perk) { return false; }
  let data = this.GetDevelopmentData(owner);
  if !IsDefined(data) || data.IsNewPerkBought(perk) <= 0 || !data.CheckIfAllnewPerkParentSold(perk) { return false; }
  let allowed = PlayerDevelopmentSystem.CanSellNewPerk(owner as PlayerPuppet, perk);
  if !allowed.success { return false; }
  // The SYSTEM method preserves telemetry and NewPerkSoldEvent for UI and owner.
  // The policy records readback acknowledgement before notifying UI inventory.
  return this.SellNewPerk(owner, perk);
}

@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void {
  wrappedMethod(gameInstance);
  let policy = BodyPolicy.Get(gameInstance);
  if IsDefined(policy) { policy.Restored(); }
  let profile = ProfilePolicy.Get(gameInstance);
  if IsDefined(profile) { profile.Restored(); }
}

@wrapMethod(PlayerDevelopmentSystem)
private final func OnAttributeBuy(request: ref<BuyAttribute>) -> Void {
  // Admission precedes the native m_grantAttributePoint addition, not just buy.
  if IsDefined(request) && (BodyPolicy.Busy(request.owner) ||
    (BodyPolicy.BlockBody(request.owner) && Equals(request.m_attributeType, gamedataStatType.Strength))) { return; }
  wrappedMethod(request);
}

@wrapMethod(PlayerDevelopmentData)
public final const func CanAttributeBeBought(type: gamedataStatType) -> Bool {
  if BodyPolicy.Busy(this.m_owner) || (BodyPolicy.BlockBody(this.m_owner) && Equals(type, gamedataStatType.Strength)) { return false; }
  return wrappedMethod(type);
}

@wrapMethod(PlayerDevelopmentData)
public final const func BuyAttribute(type: gamedataStatType) -> Bool {
  if BodyPolicy.Busy(this.m_owner) || (BodyPolicy.BlockBody(this.m_owner) && Equals(type, gamedataStatType.Strength)) { return false; }
  return wrappedMethod(type);
}

@wrapMethod(PlayerDevelopmentData)
private final const func CanNewPerkBeBought(perkType: gamedataNewPerkType, isEspionagePerk: Bool, isEspionageMilestonePerk: Bool) -> Bool {
  if ProfilePolicy.PerkDenied(this.m_owner, perkType) { return false; }
  if BodyPolicy.Busy(this.m_owner) || (BodyPolicy.BlockBody(this.m_owner) && BodyHookScope.IsBodyPerk(perkType)) { return false; }
  if BodyPolicy.BlockRelic(this.m_owner) && (isEspionagePerk || BodyHookScope.IsRelicPerk(perkType)) { return false; }
  return wrappedMethod(perkType, isEspionagePerk, isEspionageMilestonePerk);
}

@wrapMethod(PlayerDevelopmentData)
public final func BuyNewPerk(perkType: gamedataNewPerkType, opt forceBuy: Bool) -> Bool {
  if ProfilePolicy.PerkDenied(this.m_owner, perkType) { return false; }
  // forceBuy bypasses native CanNewPerkBeBought; it must not bypass this policy.
  if BodyPolicy.Busy(this.m_owner) || (BodyPolicy.BlockBody(this.m_owner) && BodyHookScope.IsBodyPerk(perkType)) { return false; }
  if BodyPolicy.BlockRelic(this.m_owner) && BodyHookScope.IsRelicPerk(perkType) { return false; }
  return wrappedMethod(perkType, forceBuy);
}

@wrapMethod(PlayerDevelopmentData)
public final func SellNewPerk(perkType: gamedataNewPerkType, out perkLevelSold: Int32) -> Bool {
  if BodyPolicy.Busy(this.m_owner) && !BodyPolicy.OwnPerk(this.m_owner, perkType) { perkLevelSold = 0; return false; }
  return wrappedMethod(perkType, perkLevelSold);
}

@wrapMethod(PlayerDevelopmentData)
public final func ForceSellNewPerk(perkType: gamedataNewPerkType, out perkLevelSold: Int32) -> Bool {
  if BodyPolicy.Busy(this.m_owner) { perkLevelSold = 0; return false; }
  return wrappedMethod(perkType, perkLevelSold);
}

@wrapMethod(PlayerDevelopmentData)
public final const func ResetAttribute(type: gamedataStatType) -> Void {
  if BodyPolicy.Busy(this.m_owner) && !(BodyPolicy.OwnBodyReset(this.m_owner) && Equals(type, gamedataStatType.Strength)) { return; }
  wrappedMethod(type);
}

@wrapMethod(PlayerDevelopmentData)
public final const func SellAttribute(type: gamedataStatType) -> Bool {
  if BodyPolicy.Busy(this.m_owner) { return false; }
  return wrappedMethod(type);
}

@wrapMethod(PlayerDevelopmentData)
public final const func ResetAttributes() -> Void {
  if BodyPolicy.Busy(this.m_owner) { return; }
  wrappedMethod();
}

@wrapMethod(PlayerDevelopmentData)
public final const func SellAllAttributes() -> Void {
  if BodyPolicy.Busy(this.m_owner) { return; }
  wrappedMethod();
}

@wrapMethod(PlayerDevelopmentData)
public final func ResetNewPerks() -> Void {
  if BodyPolicy.Busy(this.m_owner) { return; }
  wrappedMethod();
}

@wrapMethod(PlayerDevelopmentData)
public final const func ResetAllDevPoints() -> Void {
  if BodyPolicy.Busy(this.m_owner) { return; }
  wrappedMethod();
}

@wrapMethod(PlayerDevelopmentData)
public final const func ClearAllDevPoints() -> Void {
  if BodyPolicy.Busy(this.m_owner) { return; }
  wrappedMethod();
}

@wrapMethod(PlayerDevelopmentData)
public final const func SetDevelopmentsPoint(type: gamedataDevelopmentPointType, value: Int32) -> Void {
  if BodyPolicy.Busy(this.m_owner) { return; }
  wrappedMethod(type, value);
}

@wrapMethod(PlayerDevelopmentDataManager)
public final func IsPerkUpgradeable(data: ref<BasePerkDisplayData>, opt showNotification: Bool) -> Bool {
  let modern = data as NewPerkDisplayData;
  if BodyPolicy.Busy(this.m_player) || (IsDefined(modern) && (ProfilePolicy.PerkDenied(this.m_player, modern.m_type) || (BodyPolicy.BlockBody(this.m_player) && BodyHookScope.IsBodyPerk(modern.m_type)) ||
    (BodyPolicy.BlockRelic(this.m_player) && BodyHookScope.IsRelicPerk(modern.m_type)))) {
    if showNotification {
      let evt = new UIMenuNotificationEvent();
      evt.m_notificationType = UIMenuNotificationType.PerksLocked;
      GameInstance.GetUISystem(this.m_player.GetGame()).QueueEvent(evt);
    }
    return false;
  }
  return wrappedMethod(data, showNotification);
}

@wrapMethod(PlayerDevelopmentDataManager)
public final func IsNewPerkRefundable(data: ref<NewPerkDisplayData>) -> Bool {
  if BodyPolicy.Busy(this.m_player) { return false; }
  return wrappedMethod(data);
}

@wrapMethod(NewPerksCategoriesGameController)
protected cb func OnResetConfirmed(data: ref<inkGameNotificationData>) -> Bool {
  // Native UI consumes its one-time respec fact after both data calls, even if
  // either declined. Reject before that callback's own state/fact side effects.
  if BodyPolicy.Busy(this.m_player) {
    this.m_resetConfirmationToken = null;
    return false;
  }
  return wrappedMethod(data);
}
