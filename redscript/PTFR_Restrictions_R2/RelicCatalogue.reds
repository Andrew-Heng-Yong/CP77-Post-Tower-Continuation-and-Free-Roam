module PTFR.RestrictionsR2

// Stock Relic tree: nine one-rank perks, three 3-point milestones and six
// 1-point children. Native script costs, not the unused level.pointsCost flat.
public abstract class RelicCatalogue {
  public static func Types() -> array<gamedataNewPerkType> {
    let result: array<gamedataNewPerkType>;
    ArrayPush(result, gamedataNewPerkType.Espionage_Central_Milestone_1);
    ArrayPush(result, gamedataNewPerkType.Espionage_Central_Perk_1_1);
    ArrayPush(result, gamedataNewPerkType.Espionage_Central_Perk_1_2);
    ArrayPush(result, gamedataNewPerkType.Espionage_Central_Perk_1_3);
    ArrayPush(result, gamedataNewPerkType.Espionage_Central_Perk_1_4);
    ArrayPush(result, gamedataNewPerkType.Espionage_Left_Milestone_Perk);
    ArrayPush(result, gamedataNewPerkType.Espionage_Left_Perk_1_2);
    ArrayPush(result, gamedataNewPerkType.Espionage_Right_Milestone_1);
    ArrayPush(result, gamedataNewPerkType.Espionage_Right_Perk_1_1);
    return result;
  }
  public static func Cost(perk: gamedataNewPerkType) -> Int32 {
    let types = RelicCatalogue.Types();
    if !ArrayContains(types, perk) { return 0; }
    return Equals(perk, gamedataNewPerkType.Espionage_Central_Milestone_1) ||
      Equals(perk, gamedataNewPerkType.Espionage_Left_Milestone_Perk) ||
      Equals(perk, gamedataNewPerkType.Espionage_Right_Milestone_1) ? 3 : 1;
  }
  public static func Dependencies(perk: gamedataNewPerkType) -> array<gamedataNewPerkType> {
    let result: array<gamedataNewPerkType>;
    switch perk {
      case gamedataNewPerkType.Espionage_Central_Perk_1_1:
      case gamedataNewPerkType.Espionage_Central_Perk_1_2:
      case gamedataNewPerkType.Espionage_Central_Perk_1_3:
      case gamedataNewPerkType.Espionage_Central_Perk_1_4:
        ArrayPush(result, gamedataNewPerkType.Espionage_Central_Milestone_1); break;
      case gamedataNewPerkType.Espionage_Left_Perk_1_2:
        ArrayPush(result, gamedataNewPerkType.Espionage_Left_Milestone_Perk); break;
      case gamedataNewPerkType.Espionage_Right_Perk_1_1:
        ArrayPush(result, gamedataNewPerkType.Espionage_Right_Milestone_1); break;
    }
    return result;
  }
  public static func Total(snapshot: BodySnapshot) -> Int32 {
    let types = RelicCatalogue.Types();
    let total = 0;
    let i = 0;
    while i < ArraySize(types) { total += snapshot.perkRanks[EnumInt(types[i])]; i += 1; }
    return total;
  }
  public static func Headroom(snapshot: BodySnapshot) -> Bool {
    if !snapshot.valid || ArraySize(snapshot.perkRanks) != EnumInt(gamedataNewPerkType.Count) { return false; }
    let types = RelicCatalogue.Types();
    let points = 0;
    let i = 0;
    while i < ArraySize(types) {
      let rank = snapshot.perkRanks[EnumInt(types[i])];
      if rank < 0 || rank > 1 { return false; }
      points += rank * RelicCatalogue.Cost(types[i]);
      i += 1;
    }
    return snapshot.relicUnspent >= 0 && snapshot.relicUnspent <= 2147483647 - points;
  }
  public static func Valid() -> Bool {
    if EnumInt(gamedataNewPerkType.Count) != 189 { return false; }
    let tree = RPGManager.GetAttributeDataRecord(gamedataAttributeDataType.EspionageAttributeData);
    if !IsDefined(tree) || tree.GetID() != t"NewPerks.EspionageAttributeData" ||
      NotEquals(tree.Type(), gamedataAttributeDataType.EspionageAttributeData) || !IsDefined(tree.Attribute()) { return false; }
    if tree.Attribute().GetID() != t"BaseStats.Espionage" || tree.GetPerksCount() != 9 { return false; }
    let types = RelicCatalogue.Types();
    let i = 0;
    let j: Int32;
    let requires: array<wref<NewPerk_Record>>;
    while i < ArraySize(types) {
      let expected = RPGManager.GetNewPerkRecord(types[i]);
      let actual = tree.GetPerksItem(i);
      if !IsDefined(expected) || !IsDefined(actual) || actual.GetID() != expected.GetID() || NotEquals(actual.Type(), types[i]) ||
        expected.GetID() != TDBID.Create("NewPerks." + EnumValueToString("gamedataNewPerkType", Cast<Int64>(EnumInt(types[i])))) { return false; }
      if !IsDefined(actual.Attribute()) || actual.Attribute().GetID() != tree.GetID() ||
        actual.GetLevelsCount() != 1 || !IsDefined(actual.GetLevelsItem(0)) ||
        !IsDefined(actual.Tier()) || actual.Tier().RequiredAttributePoints() != 0 { return false; }
      let deps = RelicCatalogue.Dependencies(types[i]);
      ArrayClear(requires); actual.RequiresPerks(requires);
      if ArraySize(requires) != ArraySize(deps) { return false; }
      j = 0;
      while j < ArraySize(deps) {
        let dependency = RPGManager.GetNewPerkRecord(deps[j]);
        if !IsDefined(requires[j]) || !IsDefined(dependency) || requires[j].GetID() != dependency.GetID() || NotEquals(requires[j].Type(), deps[j]) { return false; }
        j += 1;
      }
      i += 1;
    }
    // Native dependency checks are tree-local: refuse cross-tree dependents.
    i = 0;
    while i < EnumInt(gamedataNewPerkType.Count) {
      let type = IntEnum<gamedataNewPerkType>(i);
      let record = RPGManager.GetNewPerkRecord(type);
      if !IsDefined(record) || !IsDefined(record.Attribute()) || NotEquals(record.Type(), type) ||
        record.GetID() != TDBID.Create("NewPerks." + EnumValueToString("gamedataNewPerkType", Cast<Int64>(i))) { return false; }
      if NotEquals(Equals(record.Attribute().Type(), gamedataAttributeDataType.EspionageAttributeData), ArrayContains(types, type)) { return false; }
      ArrayClear(requires); record.RequiresPerks(requires);
      j = 0;
      while j < ArraySize(requires) {
        if !IsDefined(requires[j]) { return false; }
        if EnumInt(requires[j].Type()) < 0 || EnumInt(requires[j].Type()) >= EnumInt(gamedataNewPerkType.Count) { return false; }
        let dependency = RPGManager.GetNewPerkRecord(requires[j].Type());
        if !IsDefined(dependency) || requires[j].GetID() != dependency.GetID() { return false; }
        if !ArrayContains(types, type) && ArrayContains(types, requires[j].Type()) { return false; }
        j += 1;
      }
      i += 1;
    }
    return true;
  }
}
