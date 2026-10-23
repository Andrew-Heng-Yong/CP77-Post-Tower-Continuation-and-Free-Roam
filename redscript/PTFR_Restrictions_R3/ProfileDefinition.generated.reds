module PTFR.RestrictionsR3

// Generated from profiles/; do not hand-edit. Build-time loader, not hot reload.
public abstract class ProfileDefinition {
  public static func ID() -> String { return "tower_implant_focused"; }
  public static func Revision() -> Int32 { return 1; }
  public static func Fingerprint() -> String { return "EA4423FBE8A6DF1A3977417061BB8E582522C4EA9DFACCA5BC92F3906EDFD7D0"; }
  public static func Health() -> Float { return 150.000000; }
  public static func CyberwareAllowed(id: TweakDBID) -> Bool {
    return id == t"Items.AdvancedCasiusTattoo" ||
      id == t"Items.AdvancedKiroshiOpticsBareCommon" ||
      id == t"Items.AdvancedKiroshiOpticsBareCommonPlus" ||
      id == t"Items.AdvancedKiroshiOpticsBareEpic" ||
      id == t"Items.AdvancedKiroshiOpticsBareEpicPlus" ||
      id == t"Items.AdvancedKiroshiOpticsBareLegendary" ||
      id == t"Items.AdvancedKiroshiOpticsBareLegendaryPlus" ||
      id == t"Items.AdvancedKiroshiOpticsBareLegendaryPlusPlus" ||
      id == t"Items.AdvancedKiroshiOpticsBareRare" ||
      id == t"Items.AdvancedKiroshiOpticsBareRarePlus" ||
      id == t"Items.AdvancedKiroshiOpticsBareUncommon" ||
      id == t"Items.AdvancedKiroshiOpticsBareUncommonPlus" ||
      id == t"Items.CasiusTattoo";
  }
  public static func AllowedPerks() -> array<gamedataNewPerkType> {
    let result: array<gamedataNewPerkType>;
    ArrayPush(result, gamedataNewPerkType.Cool_Central_Milestone_1);
    ArrayPush(result, gamedataNewPerkType.Cool_Central_Milestone_3);
    ArrayPush(result, gamedataNewPerkType.Cool_Central_Perk_1_1);
    ArrayPush(result, gamedataNewPerkType.Cool_Central_Perk_1_2);
    ArrayPush(result, gamedataNewPerkType.Cool_Central_Perk_1_4);
    ArrayPush(result, gamedataNewPerkType.Cool_Central_Perk_3_1);
    ArrayPush(result, gamedataNewPerkType.Cool_Central_Perk_3_2);
    ArrayPush(result, gamedataNewPerkType.Cool_Central_Perk_3_4);
    ArrayPush(result, gamedataNewPerkType.Cool_Inbetween_Left_2);
    ArrayPush(result, gamedataNewPerkType.Cool_Inbetween_Right_3);
    ArrayPush(result, gamedataNewPerkType.Cool_Left_Milestone_2);
    ArrayPush(result, gamedataNewPerkType.Cool_Left_Milestone_3);
    ArrayPush(result, gamedataNewPerkType.Cool_Left_Perk_2_1);
    ArrayPush(result, gamedataNewPerkType.Cool_Left_Perk_2_2);
    ArrayPush(result, gamedataNewPerkType.Cool_Left_Perk_2_3);
    ArrayPush(result, gamedataNewPerkType.Cool_Left_Perk_2_4);
    ArrayPush(result, gamedataNewPerkType.Cool_Left_Perk_3_1);
    ArrayPush(result, gamedataNewPerkType.Cool_Left_Perk_3_2);
    ArrayPush(result, gamedataNewPerkType.Cool_Left_Perk_3_3);
    ArrayPush(result, gamedataNewPerkType.Cool_Left_Perk_3_4);
    ArrayPush(result, gamedataNewPerkType.Cool_Master_Perk_1);
    ArrayPush(result, gamedataNewPerkType.Cool_Master_Perk_2);
    ArrayPush(result, gamedataNewPerkType.Cool_Master_Perk_4);
    ArrayPush(result, gamedataNewPerkType.Cool_Right_Milestone_1);
    ArrayPush(result, gamedataNewPerkType.Cool_Right_Milestone_2);
    ArrayPush(result, gamedataNewPerkType.Cool_Right_Milestone_3);
    ArrayPush(result, gamedataNewPerkType.Cool_Right_Perk_1_1);
    ArrayPush(result, gamedataNewPerkType.Cool_Right_Perk_1_2);
    ArrayPush(result, gamedataNewPerkType.Cool_Right_Perk_2_1);
    ArrayPush(result, gamedataNewPerkType.Cool_Right_Perk_2_2);
    ArrayPush(result, gamedataNewPerkType.Cool_Right_Perk_2_3);
    ArrayPush(result, gamedataNewPerkType.Cool_Right_Perk_2_4);
    ArrayPush(result, gamedataNewPerkType.Cool_Right_Perk_3_1);
    ArrayPush(result, gamedataNewPerkType.Cool_Right_Perk_3_2);
    ArrayPush(result, gamedataNewPerkType.Cool_Right_Perk_3_4);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Left_Milestone_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Left_Perk_1_2);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Central_Milestone_1);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Central_Milestone_2);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Central_Milestone_3);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Central_Perk_1_1);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Central_Perk_1_2);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Central_Perk_1_3);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Central_Perk_1_4);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Central_Perk_2_1);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Central_Perk_2_2);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Central_Perk_2_3);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Central_Perk_2_4);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Central_Perk_3_2);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Central_Perk_3_3);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Inbetween_Right_2);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Left_Milestone_1);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Left_Milestone_2);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Left_Milestone_3);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Left_Perk_2_2);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Left_Perk_2_3);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Left_Perk_2_4);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Left_Perk_3_1);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Left_Perk_3_2);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Left_Perk_3_3);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Left_Perk_3_4);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Master_Perk_1);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Master_Perk_2);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Master_Perk_3);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Master_Perk_5);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Right_Milestone_2);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Right_Milestone_3);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Right_Perk_2_1);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Right_Perk_2_2);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Right_Perk_2_3);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Right_Perk_3_1);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Right_Perk_3_3);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Right_Perk_3_4);
    ArrayPush(result, gamedataNewPerkType.Tech_Left_Milestone_1);
    ArrayPush(result, gamedataNewPerkType.Tech_Left_Milestone_2);
    ArrayPush(result, gamedataNewPerkType.Tech_Left_Milestone_3);
    ArrayPush(result, gamedataNewPerkType.Tech_Left_Perk_1_1);
    ArrayPush(result, gamedataNewPerkType.Tech_Left_Perk_1_2);
    ArrayPush(result, gamedataNewPerkType.Tech_Left_Perk_2_1);
    ArrayPush(result, gamedataNewPerkType.Tech_Left_Perk_2_2);
    ArrayPush(result, gamedataNewPerkType.Tech_Left_Perk_2_3);
    ArrayPush(result, gamedataNewPerkType.Tech_Left_Perk_2_4);
    ArrayPush(result, gamedataNewPerkType.Tech_Left_Perk_3_01);
    ArrayPush(result, gamedataNewPerkType.Tech_Left_Perk_3_2);
    ArrayPush(result, gamedataNewPerkType.Tech_Left_Perk_3_3);
    ArrayPush(result, gamedataNewPerkType.Tech_Left_Perk_3_4);
    ArrayPush(result, gamedataNewPerkType.Tech_Master_Perk_5);
    ArrayPush(result, gamedataNewPerkType.Tech_Right_Milestone_1);
    ArrayPush(result, gamedataNewPerkType.Tech_Right_Milestone_3);
    ArrayPush(result, gamedataNewPerkType.Tech_Right_Perk_3_1);
    ArrayPush(result, gamedataNewPerkType.Tech_Right_Perk_3_2);
    ArrayPush(result, gamedataNewPerkType.Tech_Right_Perk_3_3);
    ArrayPush(result, gamedataNewPerkType.Tech_Right_Perk_3_4);
    return result;
  }
  public static func OtherBlocked() -> array<gamedataNewPerkType> {
    let result: array<gamedataNewPerkType>;
    ArrayPush(result, gamedataNewPerkType.Cool_Inbetween_Left_3);
    ArrayPush(result, gamedataNewPerkType.Cool_Left_Milestone_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Milestone_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Milestone_2);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Milestone_3);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Perk_1_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Perk_1_2);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Perk_1_3);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Perk_2_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Perk_2_2);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Perk_2_3);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Perk_2_4);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Perk_3_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Perk_3_2);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Perk_3_3);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Inbetween_Left_2);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Inbetween_Left_3);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Inbetween_Right_2);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Left_Milestone_2);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Left_Milestone_3);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Left_Perk_1_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Left_Perk_2_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Left_Perk_2_2);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Left_Perk_2_3);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Left_Perk_2_4);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Left_Perk_3_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Left_Perk_3_2);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Left_Perk_3_4);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Master_Perk_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Master_Perk_3);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Master_Perk_4);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Right_Milestone_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Right_Milestone_2);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Right_Milestone_3);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Right_Perk_2_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Right_Perk_2_2);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Right_Perk_3_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Right_Perk_3_2);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Inbetween_Left_3);
    ArrayPush(result, gamedataNewPerkType.Tech_Central_Milestone_2);
    ArrayPush(result, gamedataNewPerkType.Tech_Central_Milestone_3);
    ArrayPush(result, gamedataNewPerkType.Tech_Central_Perk_2_1);
    ArrayPush(result, gamedataNewPerkType.Tech_Central_Perk_2_2);
    ArrayPush(result, gamedataNewPerkType.Tech_Central_Perk_2_3);
    ArrayPush(result, gamedataNewPerkType.Tech_Central_Perk_2_4);
    ArrayPush(result, gamedataNewPerkType.Tech_Central_Perk_3_1);
    ArrayPush(result, gamedataNewPerkType.Tech_Central_Perk_3_2);
    ArrayPush(result, gamedataNewPerkType.Tech_Central_Perk_3_3);
    ArrayPush(result, gamedataNewPerkType.Tech_Central_Perk_3_4);
    ArrayPush(result, gamedataNewPerkType.Tech_Inbetween_Left_3);
    ArrayPush(result, gamedataNewPerkType.Tech_Inbetween_Right_2);
    ArrayPush(result, gamedataNewPerkType.Tech_Master_Perk_2);
    ArrayPush(result, gamedataNewPerkType.Tech_Master_Perk_3);
    return result;
  }
  public static func PreviousStrictBlocked() -> array<gamedataNewPerkType> {
    let result: array<gamedataNewPerkType>;
    ArrayPush(result, gamedataNewPerkType.Cool_Inbetween_Left_2);
    ArrayPush(result, gamedataNewPerkType.Cool_Inbetween_Left_3);
    ArrayPush(result, gamedataNewPerkType.Cool_Left_Milestone_1);
    ArrayPush(result, gamedataNewPerkType.Cool_Left_Perk_3_2);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Milestone_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Milestone_2);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Milestone_3);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Perk_1_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Perk_1_2);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Perk_1_3);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Perk_2_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Perk_2_2);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Perk_2_3);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Perk_2_4);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Perk_3_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Perk_3_2);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Central_Perk_3_3);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Inbetween_Left_2);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Inbetween_Left_3);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Inbetween_Right_2);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Left_Milestone_2);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Left_Milestone_3);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Left_Perk_1_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Left_Perk_2_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Left_Perk_2_2);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Left_Perk_2_3);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Left_Perk_2_4);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Left_Perk_3_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Left_Perk_3_2);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Left_Perk_3_4);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Master_Perk_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Master_Perk_3);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Master_Perk_4);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Right_Milestone_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Right_Milestone_2);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Right_Milestone_3);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Right_Perk_2_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Right_Perk_2_2);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Right_Perk_3_1);
    ArrayPush(result, gamedataNewPerkType.Intelligence_Right_Perk_3_2);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Central_Milestone_2);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Central_Milestone_3);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Central_Perk_2_1);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Central_Perk_2_2);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Central_Perk_2_3);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Central_Perk_2_4);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Central_Perk_3_2);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Central_Perk_3_3);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Inbetween_Left_3);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Inbetween_Right_2);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Master_Perk_3);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Master_Perk_5);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Right_Milestone_2);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Right_Milestone_3);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Right_Perk_2_1);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Right_Perk_2_2);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Right_Perk_2_3);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Right_Perk_3_1);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Right_Perk_3_3);
    ArrayPush(result, gamedataNewPerkType.Reflexes_Right_Perk_3_4);
    ArrayPush(result, gamedataNewPerkType.Tech_Central_Milestone_2);
    ArrayPush(result, gamedataNewPerkType.Tech_Central_Milestone_3);
    ArrayPush(result, gamedataNewPerkType.Tech_Central_Perk_2_1);
    ArrayPush(result, gamedataNewPerkType.Tech_Central_Perk_2_2);
    ArrayPush(result, gamedataNewPerkType.Tech_Central_Perk_2_3);
    ArrayPush(result, gamedataNewPerkType.Tech_Central_Perk_2_4);
    ArrayPush(result, gamedataNewPerkType.Tech_Central_Perk_3_1);
    ArrayPush(result, gamedataNewPerkType.Tech_Central_Perk_3_2);
    ArrayPush(result, gamedataNewPerkType.Tech_Central_Perk_3_3);
    ArrayPush(result, gamedataNewPerkType.Tech_Central_Perk_3_4);
    ArrayPush(result, gamedataNewPerkType.Tech_Inbetween_Left_3);
    ArrayPush(result, gamedataNewPerkType.Tech_Inbetween_Right_2);
    ArrayPush(result, gamedataNewPerkType.Tech_Master_Perk_2);
    ArrayPush(result, gamedataNewPerkType.Tech_Master_Perk_3);
    return result;
  }
}

public abstract class ProfileCatalogue {
  public static func Valid() -> Bool {
    if EnumInt(gamedataNewPerkType.Count) != 189 { return false; }
    let treeBody = TweakDBInterface.GetAttributeDataRecord(t"NewPerks.BodyAttributeData");
    if !IsDefined(treeBody) || treeBody.GetPerksCount() != 33 { return false; }
    let treeEspionage = TweakDBInterface.GetAttributeDataRecord(t"NewPerks.EspionageAttributeData");
    if !IsDefined(treeEspionage) || treeEspionage.GetPerksCount() != 9 { return false; }
    let treeCool = TweakDBInterface.GetAttributeDataRecord(t"NewPerks.CoolAttributeData");
    if !IsDefined(treeCool) || treeCool.GetPerksCount() != 37 { return false; }
    let treeTech = TweakDBInterface.GetAttributeDataRecord(t"NewPerks.TechnicalAbilityAttributeData");
    if !IsDefined(treeTech) || treeTech.GetPerksCount() != 34 { return false; }
    let treeIntelligence = TweakDBInterface.GetAttributeDataRecord(t"NewPerks.IntelligenceAttributeData");
    if !IsDefined(treeIntelligence) || treeIntelligence.GetPerksCount() != 38 { return false; }
    let treeReflexes = TweakDBInterface.GetAttributeDataRecord(t"NewPerks.ReflexesAttributeData");
    if !IsDefined(treeReflexes) || treeReflexes.GetPerksCount() != 37 { return false; }
    if !ProfileCatalogue.R0() { return false; }
    if !ProfileCatalogue.R1() { return false; }
    if !ProfileCatalogue.R2() { return false; }
    if !ProfileCatalogue.R3() { return false; }
    if !ProfileCatalogue.R4() { return false; }
    if !ProfileCatalogue.R5() { return false; }
    if !ProfileCatalogue.R6() { return false; }
    if !ProfileCatalogue.R7() { return false; }
    if !ProfileCatalogue.R8() { return false; }
    if !ProfileCatalogue.R9() { return false; }
    if !ProfileCatalogue.R10() { return false; }
    if !ProfileCatalogue.R11() { return false; }
    if !ProfileCatalogue.R12() { return false; }
    if !ProfileCatalogue.R13() { return false; }
    if !ProfileCatalogue.R14() { return false; }
    if !ProfileCatalogue.R15() { return false; }
    if !ProfileCatalogue.R16() { return false; }
    if !ProfileCatalogue.R17() { return false; }
    if !ProfileCatalogue.R18() { return false; }
    if !ProfileCatalogue.R19() { return false; }
    if !ProfileCatalogue.R20() { return false; }
    if !ProfileCatalogue.R21() { return false; }
    if !ProfileCatalogue.R22() { return false; }
    if !ProfileCatalogue.R23() { return false; }
    if !ProfileCatalogue.R24() { return false; }
    if !ProfileCatalogue.R25() { return false; }
    if !ProfileCatalogue.R26() { return false; }
    if !ProfileCatalogue.R27() { return false; }
    if !ProfileCatalogue.R28() { return false; }
    if !ProfileCatalogue.R29() { return false; }
    if !ProfileCatalogue.R30() { return false; }
    if !ProfileCatalogue.R31() { return false; }
    if !ProfileCatalogue.R32() { return false; }
    if !ProfileCatalogue.R33() { return false; }
    if !ProfileCatalogue.R34() { return false; }
    if !ProfileCatalogue.R35() { return false; }
    if !ProfileCatalogue.R36() { return false; }
    if !ProfileCatalogue.R37() { return false; }
    if !ProfileCatalogue.R38() { return false; }
    if !ProfileCatalogue.R39() { return false; }
    if !ProfileCatalogue.R40() { return false; }
    if !ProfileCatalogue.R41() { return false; }
    if !ProfileCatalogue.R42() { return false; }
    if !ProfileCatalogue.R43() { return false; }
    if !ProfileCatalogue.R44() { return false; }
    if !ProfileCatalogue.R45() { return false; }
    if !ProfileCatalogue.R46() { return false; }
    if !ProfileCatalogue.R47() { return false; }
    if !ProfileCatalogue.R48() { return false; }
    if !ProfileCatalogue.R49() { return false; }
    if !ProfileCatalogue.R50() { return false; }
    if !ProfileCatalogue.R51() { return false; }
    if !ProfileCatalogue.R52() { return false; }
    if !ProfileCatalogue.R53() { return false; }
    if !ProfileCatalogue.R54() { return false; }
    if !ProfileCatalogue.R55() { return false; }
    if !ProfileCatalogue.R56() { return false; }
    if !ProfileCatalogue.R57() { return false; }
    if !ProfileCatalogue.R58() { return false; }
    if !ProfileCatalogue.R59() { return false; }
    if !ProfileCatalogue.R60() { return false; }
    if !ProfileCatalogue.R61() { return false; }
    if !ProfileCatalogue.R62() { return false; }
    if !ProfileCatalogue.R63() { return false; }
    if !ProfileCatalogue.R64() { return false; }
    if !ProfileCatalogue.R65() { return false; }
    if !ProfileCatalogue.R66() { return false; }
    if !ProfileCatalogue.R67() { return false; }
    if !ProfileCatalogue.R68() { return false; }
    if !ProfileCatalogue.R69() { return false; }
    if !ProfileCatalogue.R70() { return false; }
    if !ProfileCatalogue.R71() { return false; }
    if !ProfileCatalogue.R72() { return false; }
    if !ProfileCatalogue.R73() { return false; }
    if !ProfileCatalogue.R74() { return false; }
    if !ProfileCatalogue.R75() { return false; }
    if !ProfileCatalogue.R76() { return false; }
    if !ProfileCatalogue.R77() { return false; }
    if !ProfileCatalogue.R78() { return false; }
    if !ProfileCatalogue.R79() { return false; }
    if !ProfileCatalogue.R80() { return false; }
    if !ProfileCatalogue.R81() { return false; }
    if !ProfileCatalogue.R82() { return false; }
    if !ProfileCatalogue.R83() { return false; }
    if !ProfileCatalogue.R84() { return false; }
    if !ProfileCatalogue.R85() { return false; }
    if !ProfileCatalogue.R86() { return false; }
    if !ProfileCatalogue.R87() { return false; }
    if !ProfileCatalogue.R88() { return false; }
    if !ProfileCatalogue.R89() { return false; }
    if !ProfileCatalogue.R90() { return false; }
    if !ProfileCatalogue.R91() { return false; }
    if !ProfileCatalogue.R92() { return false; }
    if !ProfileCatalogue.R93() { return false; }
    if !ProfileCatalogue.R94() { return false; }
    if !ProfileCatalogue.R95() { return false; }
    if !ProfileCatalogue.R96() { return false; }
    if !ProfileCatalogue.R97() { return false; }
    if !ProfileCatalogue.R98() { return false; }
    if !ProfileCatalogue.R99() { return false; }
    if !ProfileCatalogue.R100() { return false; }
    if !ProfileCatalogue.R101() { return false; }
    if !ProfileCatalogue.R102() { return false; }
    if !ProfileCatalogue.R103() { return false; }
    if !ProfileCatalogue.R104() { return false; }
    if !ProfileCatalogue.R105() { return false; }
    if !ProfileCatalogue.R106() { return false; }
    if !ProfileCatalogue.R107() { return false; }
    if !ProfileCatalogue.R108() { return false; }
    if !ProfileCatalogue.R109() { return false; }
    if !ProfileCatalogue.R110() { return false; }
    if !ProfileCatalogue.R111() { return false; }
    if !ProfileCatalogue.R112() { return false; }
    if !ProfileCatalogue.R113() { return false; }
    if !ProfileCatalogue.R114() { return false; }
    if !ProfileCatalogue.R115() { return false; }
    if !ProfileCatalogue.R116() { return false; }
    if !ProfileCatalogue.R117() { return false; }
    if !ProfileCatalogue.R118() { return false; }
    if !ProfileCatalogue.R119() { return false; }
    if !ProfileCatalogue.R120() { return false; }
    if !ProfileCatalogue.R121() { return false; }
    if !ProfileCatalogue.R122() { return false; }
    if !ProfileCatalogue.R123() { return false; }
    if !ProfileCatalogue.R124() { return false; }
    if !ProfileCatalogue.R125() { return false; }
    if !ProfileCatalogue.R126() { return false; }
    if !ProfileCatalogue.R127() { return false; }
    if !ProfileCatalogue.R128() { return false; }
    if !ProfileCatalogue.R129() { return false; }
    if !ProfileCatalogue.R130() { return false; }
    if !ProfileCatalogue.R131() { return false; }
    if !ProfileCatalogue.R132() { return false; }
    if !ProfileCatalogue.R133() { return false; }
    if !ProfileCatalogue.R134() { return false; }
    if !ProfileCatalogue.R135() { return false; }
    if !ProfileCatalogue.R136() { return false; }
    if !ProfileCatalogue.R137() { return false; }
    if !ProfileCatalogue.R138() { return false; }
    if !ProfileCatalogue.R139() { return false; }
    if !ProfileCatalogue.R140() { return false; }
    if !ProfileCatalogue.R141() { return false; }
    if !ProfileCatalogue.R142() { return false; }
    if !ProfileCatalogue.R143() { return false; }
    if !ProfileCatalogue.R144() { return false; }
    if !ProfileCatalogue.R145() { return false; }
    if !ProfileCatalogue.R146() { return false; }
    if !ProfileCatalogue.R147() { return false; }
    if !ProfileCatalogue.R148() { return false; }
    if !ProfileCatalogue.R149() { return false; }
    if !ProfileCatalogue.R150() { return false; }
    if !ProfileCatalogue.R151() { return false; }
    if !ProfileCatalogue.R152() { return false; }
    if !ProfileCatalogue.R153() { return false; }
    if !ProfileCatalogue.R154() { return false; }
    if !ProfileCatalogue.R155() { return false; }
    if !ProfileCatalogue.R156() { return false; }
    if !ProfileCatalogue.R157() { return false; }
    if !ProfileCatalogue.R158() { return false; }
    if !ProfileCatalogue.R159() { return false; }
    if !ProfileCatalogue.R160() { return false; }
    if !ProfileCatalogue.R161() { return false; }
    if !ProfileCatalogue.R162() { return false; }
    if !ProfileCatalogue.R163() { return false; }
    if !ProfileCatalogue.R164() { return false; }
    if !ProfileCatalogue.R165() { return false; }
    if !ProfileCatalogue.R166() { return false; }
    if !ProfileCatalogue.R167() { return false; }
    if !ProfileCatalogue.R168() { return false; }
    if !ProfileCatalogue.R169() { return false; }
    if !ProfileCatalogue.R170() { return false; }
    if !ProfileCatalogue.R171() { return false; }
    if !ProfileCatalogue.R172() { return false; }
    if !ProfileCatalogue.R173() { return false; }
    if !ProfileCatalogue.R174() { return false; }
    if !ProfileCatalogue.R175() { return false; }
    if !ProfileCatalogue.R176() { return false; }
    if !ProfileCatalogue.R177() { return false; }
    if !ProfileCatalogue.R178() { return false; }
    if !ProfileCatalogue.R179() { return false; }
    if !ProfileCatalogue.R180() { return false; }
    if !ProfileCatalogue.R181() { return false; }
    if !ProfileCatalogue.R182() { return false; }
    if !ProfileCatalogue.R183() { return false; }
    if !ProfileCatalogue.R184() { return false; }
    if !ProfileCatalogue.R185() { return false; }
    if !ProfileCatalogue.R186() { return false; }
    if !ProfileCatalogue.R187() { return false; }
    return true;
  }
  private static func R0() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Central_Milestone_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Central_Milestone_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 0 { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 179128377566ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 179380228168ul { return false; }
    return true;
  }
  private static func R1() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Central_Milestone_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Central_Milestone_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 3 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Central_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 3 { return false; }
    if TDBID.ToNumber(levels[0]) != 178678663256ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 178041547124ul { return false; }
    if TDBID.ToNumber(levels[1]) != 178735664193ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 178030882157ul { return false; }
    if TDBID.ToNumber(levels[2]) != 178590285930ul { return false; }
    if !IsDefined(record.GetLevelsItem(2)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[2] + t".dataPackage")) != 182685672366ul { return false; }
    return true;
  }
  private static func R2() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Central_Perk_1_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Central_Perk_1_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Central_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 165359360536ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 163630730146ul { return false; }
    return true;
  }
  private static func R3() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Central_Perk_1_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Central_Perk_1_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Central_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 166323201757ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 163756898151ul { return false; }
    return true;
  }
  private static func R4() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Central_Perk_1_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Central_Perk_1_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Central_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 166142259870ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 164145193764ul { return false; }
    return true;
  }
  private static func R5() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Central_Perk_1_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Central_Perk_1_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Central_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 166609870679ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 164612902637ul { return false; }
    return true;
  }
  private static func R6() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Central_Perk_3_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Central_Perk_3_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Central_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 166837035993ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 164304155235ul { return false; }
    return true;
  }
  private static func R7() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Central_Perk_3_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Central_Perk_3_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Central_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 166997139228ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 165235084966ul { return false; }
    return true;
  }
  private static func R8() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Central_Perk_3_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Central_Perk_3_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Central_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 167064589824ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 165672150678ul { return false; }
    return true;
  }
  private static func R9() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Inbetween_Left_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Inbetween_Left_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 2 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Central_Perk_3_2" { return false; }
    if !IsDefined(deps[1]) || deps[1].GetID() != t"NewPerks.Body_Left_Perk_3_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 166782899850ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 164483843888ul { return false; }
    return true;
  }
  private static func R10() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Inbetween_Right_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Inbetween_Right_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 2 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Central_Perk_3_1" { return false; }
    if !IsDefined(deps[1]) || deps[1].GetID() != t"NewPerks.Body_Right_Perk_3_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 168599320746ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 171132070160ul { return false; }
    return true;
  }
  private static func R11() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Left_Milestone_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Left_Milestone_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 2 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 0 { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 2 { return false; }
    if TDBID.ToNumber(levels[0]) != 167013530646ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 163423083834ul { return false; }
    if TDBID.ToNumber(levels[1]) != 163404552483ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 167169471524ul { return false; }
    return true;
  }
  private static func R12() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Left_Milestone_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Left_Milestone_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 3 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Left_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 3 { return false; }
    if TDBID.ToNumber(levels[0]) != 167330916437ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 163674147193ul { return false; }
    if TDBID.ToNumber(levels[1]) != 163692186976ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 167426695271ul { return false; }
    if TDBID.ToNumber(levels[2]) != 171552881706ul { return false; }
    if !IsDefined(record.GetLevelsItem(2)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[2] + t".dataPackage")) != 168029543686ul { return false; }
    return true;
  }
  private static func R13() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Left_Perk_2_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Left_Perk_2_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Left_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 152986287123ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 150453366185ul { return false; }
    return true;
  }
  private static func R14() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Left_Perk_2_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Left_Perk_2_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Left_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 153281320085ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 151016834351ul { return false; }
    return true;
  }
  private static func R15() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Left_Perk_2_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Left_Perk_2_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Left_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 153883130204ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 151618808038ul { return false; }
    return true;
  }
  private static func R16() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Left_Perk_3_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Left_Perk_3_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 151921861587ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 153649345129ul { return false; }
    return true;
  }
  private static func R17() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Left_Perk_3_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Left_Perk_3_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 152046837526ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 154614353580ul { return false; }
    return true;
  }
  private static func R18() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Left_Perk_3_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Left_Perk_3_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 152232889173ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 154228808431ul { return false; }
    return true;
  }
  private static func R19() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Left_Perk_3_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Left_Perk_3_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 150687245980ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 152683263782ul { return false; }
    return true;
  }
  private static func R20() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Master_Perk_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Master_Perk_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 20 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 150343179537ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 152877108395ul { return false; }
    return true;
  }
  private static func R21() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Master_Perk_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Master_Perk_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 20 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 151274643924ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 153035649134ul { return false; }
    return true;
  }
  private static func R22() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Master_Perk_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Master_Perk_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 20 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Central_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 151126078871ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 153391572013ul { return false; }
    return true;
  }
  private static func R23() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Master_Perk_5);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Master_Perk_5" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 20 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Right_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 151880633373ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 153641803175ul { return false; }
    return true;
  }
  private static func R24() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Right_Milestone_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Right_Milestone_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 0 { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 168207040699ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 170471362817ul { return false; }
    return true;
  }
  private static func R25() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Right_Milestone_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Right_Milestone_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 2 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 0 { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 2 { return false; }
    if TDBID.ToNumber(levels[0]) != 169238187240ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 169809522116ul { return false; }
    if TDBID.ToNumber(levels[1]) != 172678567280ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 174709048522ul { return false; }
    return true;
  }
  private static func R26() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Right_Milestone_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Right_Milestone_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 3 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Right_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 3 { return false; }
    if TDBID.ToNumber(levels[0]) != 169384532139ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 170155882887ul { return false; }
    if TDBID.ToNumber(levels[1]) != 175484681806ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 172700327778ul { return false; }
    if TDBID.ToNumber(levels[2]) != 172651191163ul { return false; }
    if !IsDefined(record.GetLevelsItem(2)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[2] + t".dataPackage")) != 174523877098ul { return false; }
    return true;
  }
  private static func R27() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Right_Perk_2_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Right_Perk_2_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Right_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 157890469287ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 156129299485ul { return false; }
    return true;
  }
  private static func R28() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Right_Perk_2_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Right_Perk_2_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Right_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 158822326626ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 156288495832ul { return false; }
    return true;
  }
  private static func R29() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Right_Perk_2_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Right_Perk_2_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Right_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 158611240225ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 156581635227ul { return false; }
    return true;
  }
  private static func R30() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Right_Perk_2_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Right_Perk_2_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Right_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 156927138024ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 154897697106ul { return false; }
    return true;
  }
  private static func R31() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Right_Perk_3_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Right_Perk_3_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Right_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 156590715633ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 0ul { return false; }
    return true;
  }
  private static func R32() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Body_Right_Perk_3_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Body_Right_Perk_3_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.BodyAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Body_Right_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 155608858274ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 157337513752ul { return false; }
    return true;
  }
  private static func R33() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Central_Milestone_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Central_Milestone_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 0 { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 180326307851ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 177792371121ul { return false; }
    return true;
  }
  private static func R34() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Central_Milestone_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Central_Milestone_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 3 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Central_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 3 { return false; }
    if TDBID.ToNumber(levels[0]) != 178873958427ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 177363902775ul { return false; }
    if TDBID.ToNumber(levels[1]) != 177383122222ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 178969085993ul { return false; }
    if TDBID.ToNumber(levels[2]) != 182688087712ul { return false; }
    if !IsDefined(record.GetLevelsItem(2)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[2] + t".dataPackage")) != 0ul { return false; }
    return true;
  }
  private static func R35() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Central_Perk_1_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Central_Perk_1_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Central_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 167334236996ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 165036196606ul { return false; }
    return true;
  }
  private static func R36() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Central_Perk_1_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Central_Perk_1_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Central_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 166638186369ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 164641226299ul { return false; }
    return true;
  }
  private static func R37() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Central_Perk_1_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Central_Perk_1_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Central_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 166571910813ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 166420715019ul { return false; }
    return true;
  }
  private static func R38() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Central_Perk_3_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Central_Perk_3_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Central_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 166120221317ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 164089576255ul { return false; }
    return true;
  }
  private static func R39() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Central_Perk_3_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Central_Perk_3_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Central_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 165692069440ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 163427715066ul { return false; }
    return true;
  }
  private static func R40() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Central_Perk_3_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Central_Perk_3_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Central_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 167086272458ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 0ul { return false; }
    return true;
  }
  private static func R41() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Inbetween_Left_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Inbetween_Left_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Left_Perk_2_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 166291065749ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 0ul { return false; }
    return true;
  }
  private static func R42() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Inbetween_Left_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Inbetween_Left_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Central_Perk_3_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 166828732224ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 165905915862ul { return false; }
    return true;
  }
  private static func R43() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Inbetween_Right_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Inbetween_Right_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Right_Perk_3_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 168927862698ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 168105979708ul { return false; }
    return true;
  }
  private static func R44() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Left_Milestone_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Left_Milestone_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 0 { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 166858357017ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 164290963619ul { return false; }
    return true;
  }
  private static func R45() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Left_Milestone_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Left_Milestone_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 2 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 0 { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 2 { return false; }
    if TDBID.ToNumber(levels[0]) != 166967199196ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 163444368624ul { return false; }
    if TDBID.ToNumber(levels[1]) != 165789957496ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 0ul { return false; }
    return true;
  }
  private static func R46() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Left_Milestone_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Left_Milestone_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 3 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Left_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 3 { return false; }
    if TDBID.ToNumber(levels[0]) != 167361008031ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 163635540147ul { return false; }
    if TDBID.ToNumber(levels[1]) != 165601798459ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 169996988325ul { return false; }
    if TDBID.ToNumber(levels[2]) != 167687797254ul { return false; }
    if !IsDefined(record.GetLevelsItem(2)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[2] + t".dataPackage")) != 171484157697ul { return false; }
    return true;
  }
  private static func R47() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Left_Perk_2_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Left_Perk_2_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Left_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 150842225295ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 152100307481ul { return false; }
    return true;
  }
  private static func R48() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Left_Perk_2_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Left_Perk_2_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Left_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 151673355996ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 153702821734ul { return false; }
    return true;
  }
  private static func R49() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Left_Perk_2_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Left_Perk_2_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Left_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 151130446345ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 151516392095ul { return false; }
    return true;
  }
  private static func R50() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Left_Perk_2_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Left_Perk_2_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Left_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 150918776662ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 153452582636ul { return false; }
    return true;
  }
  private static func R51() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Left_Perk_3_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Left_Perk_3_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 153149529561ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 151152561251ul { return false; }
    return true;
  }
  private static func R52() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Left_Perk_3_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Left_Perk_3_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 152771322140ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 150473289894ul { return false; }
    return true;
  }
  private static func R53() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Left_Perk_3_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Left_Perk_3_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 154377471433ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 152582124895ul { return false; }
    return true;
  }
  private static func R54() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Left_Perk_3_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Left_Perk_3_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 154131962006ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 152403331372ul { return false; }
    return true;
  }
  private static func R55() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Master_Perk_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Master_Perk_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 20 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 154458727195ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 152194282145ul { return false; }
    return true;
  }
  private static func R56() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Master_Perk_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Master_Perk_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 20 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 153813000158ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 151782510180ul { return false; }
    return true;
  }
  private static func R57() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Master_Perk_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Master_Perk_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 20 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 2 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Central_Milestone_3" { return false; }
    if !IsDefined(deps[1]) || deps[1].GetID() != t"NewPerks.Cool_Right_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 153744660162ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 153492809300ul { return false; }
    return true;
  }
  private static func R58() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Right_Milestone_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Right_Milestone_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 0 { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 168766412589ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 171031807639ul { return false; }
    return true;
  }
  private static func R59() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Right_Milestone_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Right_Milestone_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 2 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 0 { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 2 { return false; }
    if TDBID.ToNumber(levels[0]) != 167600790398ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 171459443282ul { return false; }
    if TDBID.ToNumber(levels[1]) != 171474337355ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 167689491276ul { return false; }
    return true;
  }
  private static func R60() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Right_Milestone_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Right_Milestone_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 3 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Right_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 3 { return false; }
    if TDBID.ToNumber(levels[0]) != 167817383741ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 171743931921ul { return false; }
    if TDBID.ToNumber(levels[1]) != 171728546312ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 167980402447ul { return false; }
    if TDBID.ToNumber(levels[2]) != 172548637124ul { return false; }
    if !IsDefined(record.GetLevelsItem(2)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[2] + t".dataPackage")) != 174799180903ul { return false; }
    return true;
  }
  private static func R61() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Right_Perk_1_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Right_Perk_1_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Right_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 158071173584ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 157752066374ul { return false; }
    return true;
  }
  private static func R62() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Right_Perk_1_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Right_Perk_1_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Right_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 156821667203ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 155059612729ul { return false; }
    return true;
  }
  private static func R63() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Right_Perk_2_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Right_Perk_2_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Right_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 156030523345ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 0ul { return false; }
    return true;
  }
  private static func R64() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Right_Perk_2_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Right_Perk_2_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Right_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 155066489730ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 156827617848ul { return false; }
    return true;
  }
  private static func R65() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Right_Perk_2_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Right_Perk_2_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Right_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 156679470935ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 154850938817ul { return false; }
    return true;
  }
  private static func R66() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Right_Perk_2_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Right_Perk_2_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Right_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 156392268296ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 158657803186ul { return false; }
    return true;
  }
  private static func R67() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Right_Perk_3_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Right_Perk_3_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Right_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 158421825671ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 0ul { return false; }
    return true;
  }
  private static func R68() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Right_Perk_3_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Right_Perk_3_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Right_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 158295131202ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 155728827896ul { return false; }
    return true;
  }
  private static func R69() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Cool_Right_Perk_3_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Cool_Right_Perk_3_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.CoolAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Cool_Right_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 157441228232ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 0ul { return false; }
    return true;
  }
  private static func R70() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Espionage_Central_Milestone_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Espionage_Central_Milestone_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.EspionageAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 0 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 0 { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 198853080668ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 198568183498ul { return false; }
    return true;
  }
  private static func R71() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Espionage_Central_Perk_1_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Espionage_Central_Perk_1_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.EspionageAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 0 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Espionage_Central_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 184792270958ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 187358714324ul { return false; }
    return true;
  }
  private static func R72() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Espionage_Central_Perk_1_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Espionage_Central_Perk_1_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.EspionageAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 0 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Espionage_Central_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 185907299389ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 185756775595ul { return false; }
    return true;
  }
  private static func R73() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Espionage_Central_Perk_1_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Espionage_Central_Perk_1_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.EspionageAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 0 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Espionage_Central_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 186286559358ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 185363882216ul { return false; }
    return true;
  }
  private static func R74() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Espionage_Central_Perk_1_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Espionage_Central_Perk_1_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.EspionageAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 0 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Espionage_Central_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 185974197537ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 188272106651ul { return false; }
    return true;
  }
  private static func R75() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Espionage_Left_Milestone_Perk);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Espionage_Left_Milestone_Perk" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.EspionageAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 0 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 0 { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 200503312945ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 201224549031ul { return false; }
    return true;
  }
  private static func R76() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Espionage_Left_Perk_1_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Espionage_Left_Perk_1_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.EspionageAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 0 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Espionage_Left_Milestone_Perk" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 174351846832ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 171818048522ul { return false; }
    return true;
  }
  private static func R77() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Espionage_Right_Milestone_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Espionage_Right_Milestone_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.EspionageAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 0 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 0 { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 191395217760ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 189129691354ul { return false; }
    return true;
  }
  private static func R78() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Espionage_Right_Perk_1_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Espionage_Right_Perk_1_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.EspionageAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 0 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Espionage_Right_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 178401787766ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 0ul { return false; }
    return true;
  }
  private static func R79() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Central_Milestone_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Central_Milestone_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 0 { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 211053589430ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 213587550732ul { return false; }
    return true;
  }
  private static func R80() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Central_Milestone_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Central_Milestone_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 2 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Central_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 2 { return false; }
    if TDBID.ToNumber(levels[0]) != 212287111141ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 212655562441ul { return false; }
    if TDBID.ToNumber(levels[1]) != 212234009596ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 212671109840ul { return false; }
    return true;
  }
  private static func R81() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Central_Milestone_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Central_Milestone_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 3 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Central_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 3 { return false; }
    if TDBID.ToNumber(levels[0]) != 212503833510ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 212940180106ul { return false; }
    if TDBID.ToNumber(levels[1]) != 212556509119ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 212925189779ul { return false; }
    if TDBID.ToNumber(levels[2]) != 212415062932ul { return false; }
    if !IsDefined(record.GetLevelsItem(2)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[2] + t".dataPackage")) != 218272620438ul { return false; }
    return true;
  }
  private static func R82() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Central_Perk_1_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Central_Perk_1_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Central_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 200159055007ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 197625224485ul { return false; }
    return true;
  }
  private static func R83() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Central_Perk_1_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Central_Perk_1_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Central_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 200318251098ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 198557082080ul { return false; }
    return true;
  }
  private static func R84() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Central_Perk_1_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Central_Perk_1_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Central_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 200598807577ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 198333412771ul { return false; }
    return true;
  }
  private static func R85() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Central_Perk_2_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Central_Perk_2_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Central_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 197627914910ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 200160836388ul { return false; }
    return true;
  }
  private static func R86() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Central_Perk_2_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Central_Perk_2_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Central_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 198542071387ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 0ul { return false; }
    return true;
  }
  private static func R87() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Central_Perk_2_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Central_Perk_2_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Central_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 198331630104ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 200596116386ul { return false; }
    return true;
  }
  private static func R88() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Central_Perk_2_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Central_Perk_2_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Central_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 198795194321ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 201059516011ul { return false; }
    return true;
  }
  private static func R89() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Central_Perk_3_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Central_Perk_3_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Central_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 200823567710ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 199096083684ul { return false; }
    return true;
  }
  private static func R90() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Central_Perk_3_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Central_Perk_3_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Central_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 199926642957ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 201788574107ul { return false; }
    return true;
  }
  private static func R91() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Central_Perk_3_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Central_Perk_3_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Central_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 201543802328ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 199547882594ul { return false; }
    return true;
  }
  private static func R92() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Inbetween_Left_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Inbetween_Left_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Central_Perk_2_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 201195869262ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 198662948340ul { return false; }
    return true;
  }
  private static func R93() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Inbetween_Left_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Inbetween_Left_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 2 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Left_Perk_3_1" { return false; }
    if !IsDefined(deps[1]) || deps[1].GetID() != t"NewPerks.Intelligence_Central_Perk_3_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 201046507533ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 199015993783ul { return false; }
    return true;
  }
  private static func R94() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Inbetween_Right_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Inbetween_Right_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 2 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Central_Perk_2_1" { return false; }
    if !IsDefined(deps[1]) || deps[1].GetID() != t"NewPerks.Intelligence_Right_Perk_2_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 202499964220ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 205033925766ul { return false; }
    return true;
  }
  private static func R95() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Left_Milestone_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Left_Milestone_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 0 { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 200622302914ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 198357825400ul { return false; }
    return true;
  }
  private static func R96() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Left_Milestone_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Left_Milestone_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 2 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Left_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 2 { return false; }
    if TDBID.ToNumber(levels[0]) != 201738644113ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 197946051517ul { return false; }
    if TDBID.ToNumber(levels[1]) != 201861541512ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 197869227940ul { return false; }
    return true;
  }
  private static func R97() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Left_Milestone_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Left_Milestone_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 3 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Left_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 3 { return false; }
    if TDBID.ToNumber(levels[0]) != 201594273490ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 197601665022ul { return false; }
    if TDBID.ToNumber(levels[1]) != 201470884555ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 197679111143ul { return false; }
    if TDBID.ToNumber(levels[2]) != 201346512608ul { return false; }
    if !IsDefined(record.GetLevelsItem(2)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[2] + t".dataPackage")) != 204110735846ul { return false; }
    return true;
  }
  private static func R98() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Left_Perk_1_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Left_Perk_1_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Left_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 187092804450ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 185062191832ul { return false; }
    return true;
  }
  private static func R99() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Left_Perk_1_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Left_Perk_1_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Left_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 187738398631ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 185474076189ul { return false; }
    return true;
  }
  private static func R100() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Left_Perk_2_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Left_Perk_2_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Left_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 185060803939ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 187090244825ul { return false; }
    return true;
  }
  private static func R101() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Left_Perk_2_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Left_Perk_2_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Left_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 185488308646ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 0ul { return false; }
    return true;
  }
  private static func R102() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Left_Perk_2_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Left_Perk_2_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Left_Perk_2_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 186018094451ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 185632419301ul { return false; }
    return true;
  }
  private static func R103() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Left_Perk_2_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Left_Perk_2_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Left_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 186242596908ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 188003766678ul { return false; }
    return true;
  }
  private static func R104() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Left_Perk_3_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Left_Perk_3_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 188306758307ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 186008750873ul { return false; }
    return true;
  }
  private static func R105() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Left_Perk_3_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Left_Perk_3_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 188684445286ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 186687518684ul { return false; }
    return true;
  }
  private static func R106() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Left_Perk_3_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Left_Perk_3_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 188616109946ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 187324063724ul { return false; }
    return true;
  }
  private static func R107() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Master_Perk_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Master_Perk_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 20 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 186997564513ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 184967050715ul { return false; }
    return true;
  }
  private static func R108() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Master_Perk_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Master_Perk_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 20 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Central_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 187487112423ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 185725033821ul { return false; }
    return true;
  }
  private static func R109() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Master_Perk_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Master_Perk_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 20 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 2 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Central_Milestone_3" { return false; }
    if !IsDefined(deps[1]) || deps[1].GetID() != t"NewPerks.Intelligence_Right_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 187963220270ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 186201043092ul { return false; }
    return true;
  }
  private static func R110() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Right_Milestone_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Right_Milestone_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 0 { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 202621231608ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 203376398702ul { return false; }
    return true;
  }
  private static func R111() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Right_Milestone_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Right_Milestone_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 2 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 0 { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 2 { return false; }
    if TDBID.ToNumber(levels[0]) != 202209991997ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 206068907025ul { return false; }
    if TDBID.ToNumber(levels[1]) != 206908511318ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 209477628259ul { return false; }
    return true;
  }
  private static func R112() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Right_Milestone_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Right_Milestone_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 3 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Right_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 3 { return false; }
    if TDBID.ToNumber(levels[0]) != 201928247678ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 205853485138ul { return false; }
    if TDBID.ToNumber(levels[1]) != 209437802344ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 207720000203ul { return false; }
    if TDBID.ToNumber(levels[2]) != 207578588896ul { return false; }
    if !IsDefined(record.GetLevelsItem(2)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[2] + t".dataPackage")) != 206756304502ul { return false; }
    return true;
  }
  private static func R113() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Right_Perk_2_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Right_Perk_2_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Right_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 192812930740ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 191454045730ul { return false; }
    return true;
  }
  private static func R114() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Right_Perk_2_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Right_Perk_2_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Right_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 191830809319ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 189834759005ul { return false; }
    return true;
  }
  private static func R115() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Right_Perk_3_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Right_Perk_3_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Right_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 190354438626ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 192385083480ul { return false; }
    return true;
  }
  private static func R116() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Intelligence_Right_Perk_3_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Intelligence_Right_Perk_3_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.IntelligenceAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Intelligence_Right_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 190783096103ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 193047450781ul { return false; }
    return true;
  }
  private static func R117() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Central_Milestone_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Central_Milestone_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 0 { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 196800710788ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 196045682706ul { return false; }
    return true;
  }
  private static func R118() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Central_Milestone_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Central_Milestone_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 2 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Central_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 2 { return false; }
    if TDBID.ToNumber(levels[0]) != 197227820097ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 193369986413ul { return false; }
    if TDBID.ToNumber(levels[1]) != 193320849780ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 195250430434ul { return false; }
    return true;
  }
  private static func R119() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Central_Milestone_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Central_Milestone_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 3 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Central_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 3 { return false; }
    if TDBID.ToNumber(levels[0]) != 197514665986ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 193588412718ul { return false; }
    if TDBID.ToNumber(levels[1]) != 193636926775ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 197334738992ul { return false; }
    if TDBID.ToNumber(levels[2]) != 201548637376ul { return false; }
    if !IsDefined(record.GetLevelsItem(2)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[2] + t".dataPackage")) != 200156058710ul { return false; }
    return true;
  }
  private static func R120() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Central_Perk_1_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Central_Perk_1_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Central_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 181072142729ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 181994688799ul { return false; }
    return true;
  }
  private static func R121() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Central_Perk_1_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Central_Perk_1_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Central_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 180677025100ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 182103551450ul { return false; }
    return true;
  }
  private static func R122() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Central_Perk_1_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Central_Perk_1_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Central_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 180494240015ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 182289480089ul { return false; }
    return true;
  }
  private static func R123() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Central_Perk_1_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Central_Perk_1_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Central_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 182035604678ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 180743951440ul { return false; }
    return true;
  }
  private static func R124() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Central_Perk_2_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Central_Perk_2_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Central_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 183716345630ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 181987813028ul { return false; }
    return true;
  }
  private static func R125() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Central_Perk_2_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Central_Perk_2_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Central_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 184680827867ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 182114359905ul { return false; }
    return true;
  }
  private static func R126() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Central_Perk_2_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Central_Perk_2_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Central_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 184292401048ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 182295432738ul { return false; }
    return true;
  }
  private static func R127() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Central_Perk_2_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Central_Perk_2_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Central_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 184612848327ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 182751048273ul { return false; }
    return true;
  }
  private static func R128() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Central_Perk_3_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Central_Perk_3_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Central_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 181619401869ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 181434782747ul { return false; }
    return true;
  }
  private static func R129() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Central_Perk_3_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Central_Perk_3_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Central_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 181078589528ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 183344124386ul { return false; }
    return true;
  }
  private static func R130() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Inbetween_Left_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Inbetween_Left_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 2 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Left_Perk_3_1" { return false; }
    if !IsDefined(deps[1]) || deps[1].GetID() != t"NewPerks.Reflexes_Central_Perk_3_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 182495948059ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 180566629773ul { return false; }
    return true;
  }
  private static func R131() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Inbetween_Right_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Inbetween_Right_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 2 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Central_Perk_2_1" { return false; }
    if !IsDefined(deps[1]) || deps[1].GetID() != t"NewPerks.Reflexes_Right_Perk_2_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 188048305217ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 186051214843ul { return false; }
    return true;
  }
  private static func R132() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Left_Milestone_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Left_Milestone_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 0 { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 182332111682ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 184329071352ul { return false; }
    return true;
  }
  private static func R133() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Left_Milestone_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Left_Milestone_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 2 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 0 { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 2 { return false; }
    if TDBID.ToNumber(levels[0]) != 181418145553ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 183934080573ul { return false; }
    if TDBID.ToNumber(levels[1]) != 183127089842ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 181537968053ul { return false; }
    return true;
  }
  private static func R134() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Left_Milestone_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Left_Milestone_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 3 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Left_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 3 { return false; }
    if TDBID.ToNumber(levels[0]) != 181095768914ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 183679599230ul { return false; }
    if TDBID.ToNumber(levels[1]) != 181797559286ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 186437859483ul { return false; }
    if TDBID.ToNumber(levels[2]) != 184974262335ul { return false; }
    if !IsDefined(record.GetLevelsItem(2)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[2] + t".dataPackage")) != 185566862286ul { return false; }
    return true;
  }
  private static func R135() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Left_Perk_2_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Left_Perk_2_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Left_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 170354878483ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 168325314985ul { return false; }
    return true;
  }
  private static func R136() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Left_Perk_2_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Left_Perk_2_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Left_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 170700454992ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 168166649322ul { return false; }
    return true;
  }
  private static func R137() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Left_Perk_2_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Left_Perk_2_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Left_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 171176579481ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 168642609187ul { return false; }
    return true;
  }
  private static func R138() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Left_Perk_3_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Left_Perk_3_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 168157379456ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 168878590742ul { return false; }
    return true;
  }
  private static func R139() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Left_Perk_3_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Left_Perk_3_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 169256941523ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 171554809449ul { return false; }
    return true;
  }
  private static func R140() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Left_Perk_3_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Left_Perk_3_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 169634751376ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 171363381802ul { return false; }
    return true;
  }
  private static func R141() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Left_Perk_3_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Left_Perk_3_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 167963364953ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 169691897827ul { return false; }
    return true;
  }
  private static func R142() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Master_Perk_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Master_Perk_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 20 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 167770830292ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 170035176558ul { return false; }
    return true;
  }
  private static func R143() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Master_Perk_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Master_Perk_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 20 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 168416413969ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 170447067307ul { return false; }
    return true;
  }
  private static func R144() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Master_Perk_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Master_Perk_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 20 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Central_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 168948313540ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 170592095464ul { return false; }
    return true;
  }
  private static func R145() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Master_Perk_5);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Master_Perk_5" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 20 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Right_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 168879973592ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 170910463330ul { return false; }
    return true;
  }
  private static func R146() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Right_Milestone_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Right_Milestone_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 2 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Central_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 2 { return false; }
    if TDBID.ToNumber(levels[0]) != 188875459648ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 185083407724ul { return false; }
    if TDBID.ToNumber(levels[1]) != 191482494222ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 192774000024ul { return false; }
    return true;
  }
  private static func R147() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Right_Milestone_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Right_Milestone_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 3 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Right_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 3 { return false; }
    if TDBID.ToNumber(levels[0]) != 188687177731ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 184695109935ul { return false; }
    if TDBID.ToNumber(levels[1]) != 190927281666ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 191564971822ul { return false; }
    if TDBID.ToNumber(levels[2]) != 191617088311ul { return false; }
    if !IsDefined(record.GetLevelsItem(2)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[2] + t".dataPackage")) != 191041934896ul { return false; }
    return true;
  }
  private static func R148() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Right_Perk_2_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Right_Perk_2_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Right_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 172469888752ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 174768846666ul { return false; }
    return true;
  }
  private static func R149() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Right_Perk_2_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Right_Perk_2_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Right_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 173519121059ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 172093119029ul { return false; }
    return true;
  }
  private static func R150() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Right_Perk_2_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Right_Perk_2_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Right_Perk_2_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 173710294752ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 171915578998ul { return false; }
    return true;
  }
  private static func R151() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Right_Perk_3_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Right_Perk_3_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Right_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 175717185840ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 173686532234ul { return false; }
    return true;
  }
  private static func R152() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Right_Perk_3_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Right_Perk_3_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Right_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 174759764256ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 175145308598ul { return false; }
    return true;
  }
  private static func R153() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Reflexes_Right_Perk_3_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Reflexes_Right_Perk_3_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.ReflexesAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Reflexes_Right_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 175357496553ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 174534966399ul { return false; }
    return true;
  }
  private static func R154() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Central_Milestone_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Central_Milestone_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 2 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 0 { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 2 { return false; }
    if TDBID.ToNumber(levels[0]) != 179908644862ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 176318738130ul { return false; }
    if TDBID.ToNumber(levels[1]) != 176261933771ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 180082411468ul { return false; }
    return true;
  }
  private static func R155() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Central_Milestone_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Central_Milestone_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 3 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Central_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 3 { return false; }
    if TDBID.ToNumber(levels[0]) != 180189338557ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 176531012241ul { return false; }
    if TDBID.ToNumber(levels[1]) != 176588373640ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 180300845967ul { return false; }
    if TDBID.ToNumber(levels[2]) != 183457439590ul { return false; }
    if !IsDefined(record.GetLevelsItem(2)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[2] + t".dataPackage")) != 0ul { return false; }
    return true;
  }
  private static func R156() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Central_Perk_2_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Central_Perk_2_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Central_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 167105083560ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 165880137790ul { return false; }
    return true;
  }
  private static func R157() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Central_Perk_2_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Central_Perk_2_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Central_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 166005781755ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 164278199617ul { return false; }
    return true;
  }
  private static func R158() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Central_Perk_2_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Central_Perk_2_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Central_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 166191702200ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 0ul { return false; }
    return true;
  }
  private static func R159() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Central_Perk_2_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Central_Perk_2_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Central_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 166793661809ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 164494580939ul { return false; }
    return true;
  }
  private static func R160() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Central_Perk_3_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Central_Perk_3_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Central_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 164797667326ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 166559843908ul { return false; }
    return true;
  }
  private static func R161() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Central_Perk_3_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Central_Perk_3_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Central_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 163481312173ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 0ul { return false; }
    return true;
  }
  private static func R162() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Central_Perk_3_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Central_Perk_3_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Central_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 91068214685ul { return false; }
    if IsDefined(record.GetLevelsItem(0)) { return false; } // exact stock absent binding
    return true;
  }
  private static func R163() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Central_Perk_3_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Central_Perk_3_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Central_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 163546632881ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 165577147147ul { return false; }
    return true;
  }
  private static func R164() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Inbetween_Left_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Inbetween_Left_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 2 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Left_Perk_3_01" { return false; }
    if !IsDefined(deps[1]) || deps[1].GetID() != t"NewPerks.Tech_Central_Perk_3_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 164617970349ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 166613988119ul { return false; }
    return true;
  }
  private static func R165() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Inbetween_Right_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Inbetween_Right_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Central_Perk_2_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 171592789622ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 0ul { return false; }
    return true;
  }
  private static func R166() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Left_Milestone_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Left_Milestone_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 0 { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 163925312610ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 166224238040ul { return false; }
    return true;
  }
  private static func R167() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Left_Milestone_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Left_Milestone_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 2 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Left_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 2 { return false; }
    if TDBID.ToNumber(levels[0]) != 164890658865ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 165527267613ul { return false; }
    if TDBID.ToNumber(levels[1]) != 167409048978ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 163710202005ul { return false; }
    return true;
  }
  private static func R168() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Left_Milestone_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Left_Milestone_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 3 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Left_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 3 { return false; }
    if TDBID.ToNumber(levels[0]) != 165142649970ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 165847678302ul { return false; }
    if TDBID.ToNumber(levels[1]) != 167187073489ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 163386516694ul { return false; }
    if TDBID.ToNumber(levels[2]) != 170904382230ul { return false; }
    if !IsDefined(record.GetLevelsItem(2)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[2] + t".dataPackage")) != 168104709667ul { return false; }
    return true;
  }
  private static func R169() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Left_Perk_1_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Left_Perk_1_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Left_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 152566461150ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 150804243300ul { return false; }
    return true;
  }
  private static func R170() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Left_Perk_1_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Left_Perk_1_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Left_Milestone_1" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 153480482331ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 150947700641ul { return false; }
    return true;
  }
  private static func R171() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Left_Perk_2_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Left_Perk_2_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Left_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 150798406879ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 152559437157ul { return false; }
    return true;
  }
  private static func R172() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Left_Perk_2_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Left_Perk_2_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Left_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 150957467674ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 153491437984ul { return false; }
    return true;
  }
  private static func R173() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Left_Perk_2_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Left_Perk_2_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Left_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 151175248985ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 0ul { return false; }
    return true;
  }
  private static func R174() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Left_Perk_2_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Left_Perk_2_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 9 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Left_Milestone_2" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 151781265808ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 153810829354ul { return false; }
    return true;
  }
  private static func R175() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Left_Perk_3_01);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Left_Perk_3_01" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 155576308102ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 157304963132ul { return false; }
    return true;
  }
  private static func R176() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Left_Perk_3_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Left_Perk_3_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 154153973722ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 152425440864ul { return false; }
    return true;
  }
  private static func R177() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Left_Perk_3_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Left_Perk_3_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 154403988377ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 152105955875ul { return false; }
    return true;
  }
  private static func R178() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Left_Perk_3_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Left_Perk_3_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Left_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 152862494288ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 150564626410ul { return false; }
    return true;
  }
  private static func R179() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Master_Perk_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Master_Perk_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 20 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 2 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Left_Milestone_3" { return false; }
    if !IsDefined(deps[1]) || deps[1].GetID() != t"NewPerks.Tech_Central_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 153449892120ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 150917011618ul { return false; }
    return true;
  }
  private static func R180() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Master_Perk_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Master_Perk_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 20 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Central_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 153228975451ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 151198485729ul { return false; }
    return true;
  }
  private static func R181() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Master_Perk_5);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Master_Perk_5" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 20 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Right_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 154051732689ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 151518950763ul { return false; }
    return true;
  }
  private static func R182() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Right_Milestone_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Right_Milestone_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 4 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 0 { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 169859318308ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 167863309214ul { return false; }
    return true;
  }
  private static func R183() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Right_Milestone_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Right_Milestone_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 3 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 0 { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 3 { return false; }
    if TDBID.ToNumber(levels[0]) != 171087141428ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 168503606040ul { return false; }
    if TDBID.ToNumber(levels[1]) != 168526429953ul { return false; }
    if !IsDefined(record.GetLevelsItem(1)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[1] + t".dataPackage")) != 171182985734ul { return false; }
    if TDBID.ToNumber(levels[2]) != 172380646755ul { return false; }
    if !IsDefined(record.GetLevelsItem(2)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[2] + t".dataPackage")) != 175217854550ul { return false; }
    return true;
  }
  private static func R184() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Right_Perk_3_1);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Right_Perk_3_1" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Right_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 158508565506ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 157049418900ul { return false; }
    return true;
  }
  private static func R185() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Right_Perk_3_2);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Right_Perk_3_2" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Right_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 158348998855ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 157459597393ul { return false; }
    return true;
  }
  private static func R186() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Right_Perk_3_3);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Right_Perk_3_3" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Right_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 157994118276ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 157809237010ul { return false; }
    return true;
  }
  private static func R187() -> Bool {
    let record = RPGManager.GetNewPerkRecord(gamedataNewPerkType.Tech_Right_Perk_3_4);
    if !IsDefined(record) || record.GetID() != t"NewPerks.Tech_Right_Perk_3_4" || !IsDefined(record.Attribute()) ||
      record.Attribute().GetID() != t"NewPerks.TechnicalAbilityAttributeData" ||
      record.GetLevelsCount() != 1 || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != 15 { return false; }
    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);
    if ArraySize(deps) != 1 { return false; }
    if !IsDefined(deps[0]) || deps[0].GetID() != t"NewPerks.Tech_Right_Milestone_3" { return false; }
    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");
    if ArraySize(levels) != 1 { return false; }
    if TDBID.ToNumber(levels[0]) != 158281019867ul { return false; }
    if !IsDefined(record.GetLevelsItem(0)) { return false; }
    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[0] + t".dataPackage")) != 155747213409ul { return false; }
    return true;
  }
}
