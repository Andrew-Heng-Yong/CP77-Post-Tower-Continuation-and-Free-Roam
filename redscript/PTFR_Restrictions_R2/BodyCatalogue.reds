module PTFR.RestrictionsR2

// Read-only compatibility boundary for the audited stock 2.31 modern Body tree.
// This validates identity, ownership, rank counts, tiers and ordered dependencies;
// it does not establish effect teardown or live stat-pool behavior.
public abstract class BodyCatalogue {

  public static func Types() -> array<gamedataNewPerkType> {
    let result: array<gamedataNewPerkType>;
    ArrayPush(result, gamedataNewPerkType.Body_Central_Milestone_1);
    ArrayPush(result, gamedataNewPerkType.Body_Central_Perk_1_1);
    ArrayPush(result, gamedataNewPerkType.Body_Central_Perk_1_2);
    ArrayPush(result, gamedataNewPerkType.Body_Central_Perk_1_3);
    ArrayPush(result, gamedataNewPerkType.Body_Central_Perk_1_4);
    ArrayPush(result, gamedataNewPerkType.Body_Right_Milestone_1);
    ArrayPush(result, gamedataNewPerkType.Body_Left_Milestone_2);
    ArrayPush(result, gamedataNewPerkType.Body_Left_Perk_2_1);
    ArrayPush(result, gamedataNewPerkType.Body_Left_Perk_2_3);
    ArrayPush(result, gamedataNewPerkType.Body_Left_Perk_2_4);
    ArrayPush(result, gamedataNewPerkType.Body_Right_Milestone_2);
    ArrayPush(result, gamedataNewPerkType.Body_Right_Perk_2_1);
    ArrayPush(result, gamedataNewPerkType.Body_Right_Perk_2_2);
    ArrayPush(result, gamedataNewPerkType.Body_Right_Perk_2_3);
    ArrayPush(result, gamedataNewPerkType.Body_Right_Perk_2_4);
    ArrayPush(result, gamedataNewPerkType.Body_Left_Milestone_3);
    ArrayPush(result, gamedataNewPerkType.Body_Left_Perk_3_1);
    ArrayPush(result, gamedataNewPerkType.Body_Left_Perk_3_2);
    ArrayPush(result, gamedataNewPerkType.Body_Left_Perk_3_3);
    ArrayPush(result, gamedataNewPerkType.Body_Left_Perk_3_4);
    ArrayPush(result, gamedataNewPerkType.Body_Inbetween_Left_3);
    ArrayPush(result, gamedataNewPerkType.Body_Central_Milestone_3);
    ArrayPush(result, gamedataNewPerkType.Body_Central_Perk_3_1);
    ArrayPush(result, gamedataNewPerkType.Body_Central_Perk_3_2);
    ArrayPush(result, gamedataNewPerkType.Body_Central_Perk_3_4);
    ArrayPush(result, gamedataNewPerkType.Body_Inbetween_Right_3);
    ArrayPush(result, gamedataNewPerkType.Body_Right_Milestone_3);
    ArrayPush(result, gamedataNewPerkType.Body_Right_Perk_3_1);
    ArrayPush(result, gamedataNewPerkType.Body_Right_Perk_3_2);
    ArrayPush(result, gamedataNewPerkType.Body_Master_Perk_1);
    ArrayPush(result, gamedataNewPerkType.Body_Master_Perk_2);
    ArrayPush(result, gamedataNewPerkType.Body_Master_Perk_3);
    ArrayPush(result, gamedataNewPerkType.Body_Master_Perk_5);
    return result;
  }

  public static func IsBody(type: gamedataNewPerkType) -> Bool {
    let record: ref<NewPerk_Record>;
    let attribute: wref<AttributeData_Record>;
    if EnumInt(type) < 0 || EnumInt(type) >= EnumInt(gamedataNewPerkType.Count) {
      return false;
    };
    record = RPGManager.GetNewPerkRecord(type);
    if !IsDefined(record) {
      return false;
    };
    attribute = record.Attribute();
    return IsDefined(attribute) && Equals(attribute.Type(), gamedataAttributeDataType.BodyAttributeData) && attribute.GetID() == t"NewPerks.BodyAttributeData";
  }

  public static func ExpectedRanks(type: gamedataNewPerkType) -> Int32 {
    switch type {
      case gamedataNewPerkType.Body_Central_Milestone_1:
        return 1;
      case gamedataNewPerkType.Body_Central_Perk_1_1:
        return 1;
      case gamedataNewPerkType.Body_Central_Perk_1_2:
        return 1;
      case gamedataNewPerkType.Body_Central_Perk_1_3:
        return 1;
      case gamedataNewPerkType.Body_Central_Perk_1_4:
        return 1;
      case gamedataNewPerkType.Body_Right_Milestone_1:
        return 1;
      case gamedataNewPerkType.Body_Left_Milestone_2:
        return 2;
      case gamedataNewPerkType.Body_Left_Perk_2_1:
        return 1;
      case gamedataNewPerkType.Body_Left_Perk_2_3:
        return 1;
      case gamedataNewPerkType.Body_Left_Perk_2_4:
        return 1;
      case gamedataNewPerkType.Body_Right_Milestone_2:
        return 2;
      case gamedataNewPerkType.Body_Right_Perk_2_1:
        return 1;
      case gamedataNewPerkType.Body_Right_Perk_2_2:
        return 1;
      case gamedataNewPerkType.Body_Right_Perk_2_3:
        return 1;
      case gamedataNewPerkType.Body_Right_Perk_2_4:
        return 1;
      case gamedataNewPerkType.Body_Left_Milestone_3:
        return 3;
      case gamedataNewPerkType.Body_Left_Perk_3_1:
        return 1;
      case gamedataNewPerkType.Body_Left_Perk_3_2:
        return 1;
      case gamedataNewPerkType.Body_Left_Perk_3_3:
        return 1;
      case gamedataNewPerkType.Body_Left_Perk_3_4:
        return 1;
      case gamedataNewPerkType.Body_Inbetween_Left_3:
        return 1;
      case gamedataNewPerkType.Body_Central_Milestone_3:
        return 3;
      case gamedataNewPerkType.Body_Central_Perk_3_1:
        return 1;
      case gamedataNewPerkType.Body_Central_Perk_3_2:
        return 1;
      case gamedataNewPerkType.Body_Central_Perk_3_4:
        return 1;
      case gamedataNewPerkType.Body_Inbetween_Right_3:
        return 1;
      case gamedataNewPerkType.Body_Right_Milestone_3:
        return 3;
      case gamedataNewPerkType.Body_Right_Perk_3_1:
        return 1;
      case gamedataNewPerkType.Body_Right_Perk_3_2:
        return 1;
      case gamedataNewPerkType.Body_Master_Perk_1:
        return 1;
      case gamedataNewPerkType.Body_Master_Perk_2:
        return 1;
      case gamedataNewPerkType.Body_Master_Perk_3:
        return 1;
      case gamedataNewPerkType.Body_Master_Perk_5:
        return 1;
      default:
        return 0;
    };
  }

  public static func ExpectedThreshold(type: gamedataNewPerkType) -> Int32 {
    switch type {
      case gamedataNewPerkType.Body_Central_Milestone_1:
        return 4;
      case gamedataNewPerkType.Body_Central_Perk_1_1:
        return 4;
      case gamedataNewPerkType.Body_Central_Perk_1_2:
        return 4;
      case gamedataNewPerkType.Body_Central_Perk_1_3:
        return 4;
      case gamedataNewPerkType.Body_Central_Perk_1_4:
        return 4;
      case gamedataNewPerkType.Body_Right_Milestone_1:
        return 4;
      case gamedataNewPerkType.Body_Left_Milestone_2:
        return 9;
      case gamedataNewPerkType.Body_Left_Perk_2_1:
        return 9;
      case gamedataNewPerkType.Body_Left_Perk_2_3:
        return 9;
      case gamedataNewPerkType.Body_Left_Perk_2_4:
        return 9;
      case gamedataNewPerkType.Body_Right_Milestone_2:
        return 9;
      case gamedataNewPerkType.Body_Right_Perk_2_1:
        return 9;
      case gamedataNewPerkType.Body_Right_Perk_2_2:
        return 9;
      case gamedataNewPerkType.Body_Right_Perk_2_3:
        return 9;
      case gamedataNewPerkType.Body_Right_Perk_2_4:
        return 9;
      case gamedataNewPerkType.Body_Left_Milestone_3:
        return 15;
      case gamedataNewPerkType.Body_Left_Perk_3_1:
        return 15;
      case gamedataNewPerkType.Body_Left_Perk_3_2:
        return 15;
      case gamedataNewPerkType.Body_Left_Perk_3_3:
        return 15;
      case gamedataNewPerkType.Body_Left_Perk_3_4:
        return 15;
      case gamedataNewPerkType.Body_Inbetween_Left_3:
        return 15;
      case gamedataNewPerkType.Body_Central_Milestone_3:
        return 15;
      case gamedataNewPerkType.Body_Central_Perk_3_1:
        return 15;
      case gamedataNewPerkType.Body_Central_Perk_3_2:
        return 15;
      case gamedataNewPerkType.Body_Central_Perk_3_4:
        return 15;
      case gamedataNewPerkType.Body_Inbetween_Right_3:
        return 15;
      case gamedataNewPerkType.Body_Right_Milestone_3:
        return 15;
      case gamedataNewPerkType.Body_Right_Perk_3_1:
        return 15;
      case gamedataNewPerkType.Body_Right_Perk_3_2:
        return 15;
      case gamedataNewPerkType.Body_Master_Perk_1:
        return 20;
      case gamedataNewPerkType.Body_Master_Perk_2:
        return 20;
      case gamedataNewPerkType.Body_Master_Perk_3:
        return 20;
      case gamedataNewPerkType.Body_Master_Perk_5:
        return 20;
      default:
        return 0;
    };
  }

  private static func ExpectedDependencies(type: gamedataNewPerkType) -> array<gamedataNewPerkType> {
    let result: array<gamedataNewPerkType>;
    switch type {
      case gamedataNewPerkType.Body_Central_Perk_1_1:
        ArrayPush(result, gamedataNewPerkType.Body_Central_Milestone_1);
        return result;
      case gamedataNewPerkType.Body_Central_Perk_1_2:
        ArrayPush(result, gamedataNewPerkType.Body_Central_Milestone_1);
        return result;
      case gamedataNewPerkType.Body_Central_Perk_1_3:
        ArrayPush(result, gamedataNewPerkType.Body_Central_Milestone_1);
        return result;
      case gamedataNewPerkType.Body_Central_Perk_1_4:
        ArrayPush(result, gamedataNewPerkType.Body_Central_Milestone_1);
        return result;
      case gamedataNewPerkType.Body_Left_Perk_2_1:
        ArrayPush(result, gamedataNewPerkType.Body_Left_Milestone_2);
        return result;
      case gamedataNewPerkType.Body_Left_Perk_2_3:
        ArrayPush(result, gamedataNewPerkType.Body_Left_Milestone_2);
        return result;
      case gamedataNewPerkType.Body_Left_Perk_2_4:
        ArrayPush(result, gamedataNewPerkType.Body_Left_Milestone_2);
        return result;
      case gamedataNewPerkType.Body_Right_Perk_2_1:
        ArrayPush(result, gamedataNewPerkType.Body_Right_Milestone_2);
        return result;
      case gamedataNewPerkType.Body_Right_Perk_2_2:
        ArrayPush(result, gamedataNewPerkType.Body_Right_Milestone_2);
        return result;
      case gamedataNewPerkType.Body_Right_Perk_2_3:
        ArrayPush(result, gamedataNewPerkType.Body_Right_Milestone_2);
        return result;
      case gamedataNewPerkType.Body_Right_Perk_2_4:
        ArrayPush(result, gamedataNewPerkType.Body_Right_Milestone_2);
        return result;
      case gamedataNewPerkType.Body_Left_Milestone_3:
        ArrayPush(result, gamedataNewPerkType.Body_Left_Milestone_2);
        return result;
      case gamedataNewPerkType.Body_Left_Perk_3_1:
        ArrayPush(result, gamedataNewPerkType.Body_Left_Milestone_3);
        return result;
      case gamedataNewPerkType.Body_Left_Perk_3_2:
        ArrayPush(result, gamedataNewPerkType.Body_Left_Milestone_3);
        return result;
      case gamedataNewPerkType.Body_Left_Perk_3_3:
        ArrayPush(result, gamedataNewPerkType.Body_Left_Milestone_3);
        return result;
      case gamedataNewPerkType.Body_Left_Perk_3_4:
        ArrayPush(result, gamedataNewPerkType.Body_Left_Milestone_3);
        return result;
      case gamedataNewPerkType.Body_Inbetween_Left_3:
        ArrayPush(result, gamedataNewPerkType.Body_Central_Perk_3_2);
        ArrayPush(result, gamedataNewPerkType.Body_Left_Perk_3_1);
        return result;
      case gamedataNewPerkType.Body_Central_Milestone_3:
        ArrayPush(result, gamedataNewPerkType.Body_Central_Milestone_1);
        return result;
      case gamedataNewPerkType.Body_Central_Perk_3_1:
        ArrayPush(result, gamedataNewPerkType.Body_Central_Milestone_3);
        return result;
      case gamedataNewPerkType.Body_Central_Perk_3_2:
        ArrayPush(result, gamedataNewPerkType.Body_Central_Milestone_3);
        return result;
      case gamedataNewPerkType.Body_Central_Perk_3_4:
        ArrayPush(result, gamedataNewPerkType.Body_Central_Milestone_3);
        return result;
      case gamedataNewPerkType.Body_Inbetween_Right_3:
        ArrayPush(result, gamedataNewPerkType.Body_Central_Perk_3_1);
        ArrayPush(result, gamedataNewPerkType.Body_Right_Perk_3_2);
        return result;
      case gamedataNewPerkType.Body_Right_Milestone_3:
        ArrayPush(result, gamedataNewPerkType.Body_Right_Milestone_2);
        return result;
      case gamedataNewPerkType.Body_Right_Perk_3_1:
        ArrayPush(result, gamedataNewPerkType.Body_Right_Milestone_3);
        return result;
      case gamedataNewPerkType.Body_Right_Perk_3_2:
        ArrayPush(result, gamedataNewPerkType.Body_Right_Milestone_3);
        return result;
      case gamedataNewPerkType.Body_Master_Perk_1:
        ArrayPush(result, gamedataNewPerkType.Body_Left_Milestone_3);
        return result;
      case gamedataNewPerkType.Body_Master_Perk_2:
        ArrayPush(result, gamedataNewPerkType.Body_Left_Milestone_3);
        return result;
      case gamedataNewPerkType.Body_Master_Perk_3:
        ArrayPush(result, gamedataNewPerkType.Body_Central_Milestone_3);
        return result;
      case gamedataNewPerkType.Body_Master_Perk_5:
        ArrayPush(result, gamedataNewPerkType.Body_Right_Milestone_3);
        return result;
      default:
        return result;
    };
  }

  public static func Valid() -> Bool {
    let body: ref<AttributeData_Record>;
    let bodyStat: wref<Attribute_Record>;
    let roster: array<gamedataNewPerkType>;
    let expected: ref<NewPerk_Record>;
    let actual: wref<NewPerk_Record>;
    let attribute: wref<AttributeData_Record>;
    let tier: wref<NewPerkTier_Record>;
    let level: wref<NewPerkLevelData_Record>;
    let requires: array<wref<NewPerk_Record>>;
    let expectedRequires: array<gamedataNewPerkType>;
    let dependency: ref<NewPerk_Record>;
    let type: gamedataNewPerkType;
    let i: Int32;
    let j: Int32;
    if EnumInt(gamedataNewPerkType.Count) != 189 {
      return false;
    };
    body = RPGManager.GetAttributeDataRecord(gamedataAttributeDataType.BodyAttributeData);
    if !IsDefined(body) {
      return false;
    };
    bodyStat = body.Attribute();
    if body.GetID() != t"NewPerks.BodyAttributeData" || NotEquals(body.Type(), gamedataAttributeDataType.BodyAttributeData) || !IsDefined(bodyStat) {
      return false;
    };
    if bodyStat.GetID() != t"BaseStats.Strength" {
      return false;
    };
    roster = BodyCatalogue.Types();
    if body.GetPerksCount() != 33 || ArraySize(roster) != 33 {
      return false;
    };
    i = 0;
    while i < ArraySize(roster) {
      type = roster[i];
      expected = RPGManager.GetNewPerkRecord(type);
      actual = body.GetPerksItem(i);
      if !IsDefined(expected) || !IsDefined(actual) {
        return false;
      };
      if expected.GetID() != TDBID.Create("NewPerks." + EnumValueToString("gamedataNewPerkType", Cast<Int64>(EnumInt(type)))) || actual.GetID() != expected.GetID() || NotEquals(actual.Type(), type) || NotEquals(expected.Type(), type) {
        return false;
      };
      attribute = actual.Attribute();
      tier = actual.Tier();
      if !IsDefined(attribute) || !IsDefined(tier) {
        return false;
      };
      if attribute.GetID() != body.GetID() || NotEquals(attribute.Type(), gamedataAttributeDataType.BodyAttributeData) || actual.GetLevelsCount() != BodyCatalogue.ExpectedRanks(type) || tier.RequiredAttributePoints() != BodyCatalogue.ExpectedThreshold(type) {
        return false;
      };
      j = 0;
      while j < actual.GetLevelsCount() {
        level = actual.GetLevelsItem(j);
        if !IsDefined(level) {
          return false;
        };
        j += 1;
      };
      expectedRequires = BodyCatalogue.ExpectedDependencies(type);
      ArrayClear(requires);
      actual.RequiresPerks(requires);
      if ArraySize(requires) != ArraySize(expectedRequires) {
        return false;
      };
      j = 0;
      while j < ArraySize(requires) {
        dependency = RPGManager.GetNewPerkRecord(expectedRequires[j]);
        if !IsDefined(requires[j]) || !IsDefined(dependency) {
          return false;
        };
        if requires[j].GetID() != dependency.GetID() || NotEquals(requires[j].Type(), expectedRequires[j]) {
          return false;
        };
        j += 1;
      };
      i += 1;
    };

    // Native rank selling scans dependents only within the owning attribute.
    // Refuse any cross-tree dependency on Body, even if currently unpurchased.
    // The installed stock audit verified all 189 enum records exist and no
    // non-Body record depends on Body. Do not silently accept an extended graph.
    i = 0;
    while i < EnumInt(gamedataNewPerkType.Count) {
      type = IntEnum<gamedataNewPerkType>(i);
      expected = RPGManager.GetNewPerkRecord(type);
      if !IsDefined(expected) {
        return false;
      };
      if expected.GetID() != TDBID.Create("NewPerks." + EnumValueToString("gamedataNewPerkType", Cast<Int64>(i))) || NotEquals(expected.Type(), type) {
        return false;
      };
      attribute = expected.Attribute();
      if !IsDefined(attribute) {
        return false;
      };
      if NotEquals(Equals(attribute.Type(), gamedataAttributeDataType.BodyAttributeData), ArrayContains(roster, type)) {
        return false;
      };
      ArrayClear(requires);
      expected.RequiresPerks(requires);
      j = 0;
      while j < ArraySize(requires) {
        if !IsDefined(requires[j]) {
          return false;
        };
        if EnumInt(requires[j].Type()) < 0 || EnumInt(requires[j].Type()) >= EnumInt(gamedataNewPerkType.Count) {
          return false;
        };
        dependency = RPGManager.GetNewPerkRecord(requires[j].Type());
        if !IsDefined(dependency) || dependency.GetID() != requires[j].GetID() {
          return false;
        };
        if !ArrayContains(roster, type) && ArrayContains(roster, requires[j].Type()) {
          return false;
        };
        j += 1;
      };
      i += 1;
    };
    return true;
  }
}
