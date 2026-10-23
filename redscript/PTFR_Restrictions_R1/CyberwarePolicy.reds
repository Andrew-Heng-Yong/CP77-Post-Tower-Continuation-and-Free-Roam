module PTFR.RestrictionsR1

import PTFR.RestrictionsR3.ProfileDefinition

// Save-local preference. No quest facts, inventory grants, stat resets or saves.
public class CyberwarePolicy extends ScriptableSystem {
  private persistent let mode: Int32; // 0 automatic, 1 explicitly enabled, 2 No Nerf
  private let running: Bool;
  private let epoch: Int32;
  private let warmup: Int32;
  private let actor: wref<PlayerPuppet>;
  private let attempts: array<ItemID>;
  private let fault: Bool;
  private let detail: String;
  private let pending: Int32;
  private let audit: String;

  public static func Get(game: GameInstance) -> ref<CyberwarePolicy> {
    return GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.RestrictionsR1.CyberwarePolicy") as CyberwarePolicy;
  }
  public static func Completed(game: GameInstance) -> Bool {
    let q = GameInstance.GetQuestsSystem(game);
    return IsDefined(q) && q.GetFact(n"PostTowerFreeRoamActive") == 1 && q.GetFact(n"PTFRP0_DR13") == 1 &&
      q.GetFact(n"q307_done") == 1 && q.GetFact(n"q307_finished") == 1 && q.GetFact(n"q307_active") == 0 &&
      q.GetFact(n"q307_2079") == 1 && q.GetFact(n"q307_main_game_killed") == 1 && q.GetFact(n"q307_ep1_killed") == 1 &&
      q.GetFact(n"q305_johnny_scene_active") == 0 && q.GetFact(n"q115_point_of_no_return") == 0;
  }
  public static func Active(owner: ref<GameObject>) -> Bool {
    let player = owner as PlayerPuppet;
    if !IsDefined(player) || player.IsReplacer() { return false; }
    if GameInstance.GetPlayerSystem(owner.GetGame()).GetLocalPlayerMainGameObject() != owner { return false; }
    let policy = CyberwarePolicy.Get(owner.GetGame());
    return IsDefined(policy) && policy.mode != 2 && CyberwarePolicy.Completed(owner.GetGame());
  }
  public static func Area(area: gamedataEquipmentArea) -> Bool {
    return Equals(area, gamedataEquipmentArea.FrontalCortexCW) || Equals(area, gamedataEquipmentArea.SystemReplacementCW) ||
      Equals(area, gamedataEquipmentArea.ArmsCW) || Equals(area, gamedataEquipmentArea.EyesCW) ||
      Equals(area, gamedataEquipmentArea.MusculoskeletalSystemCW) || Equals(area, gamedataEquipmentArea.HandsCW) ||
      Equals(area, gamedataEquipmentArea.NervousSystemCW) || Equals(area, gamedataEquipmentArea.CardiovascularSystemCW) ||
      Equals(area, gamedataEquipmentArea.IntegumentarySystemCW) || Equals(area, gamedataEquipmentArea.LegsCW);
  }
  public static func Approved(id: TweakDBID) -> Bool {
    return ProfileDefinition.CyberwareAllowed(id);
  }
  public static func Restricted(id: ItemID) -> Bool {
    return ItemID.IsValid(id) && CyberwarePolicy.Area(EquipmentSystem.GetEquipAreaType(id)) && !CyberwarePolicy.Approved(ItemID.GetTDBID(id));
  }
  public static func Denied(owner: ref<GameObject>, id: ItemID) -> Bool {
    return CyberwarePolicy.Active(owner) && CyberwarePolicy.Restricted(id);
  }
  public static func DeniedAction(owner: ref<GameObject>, item: wref<gameItemData>, actionID: TweakDBID) -> Bool {
    if !IsDefined(item) || !CyberwarePolicy.Denied(owner, item.GetID()) { return false; }
    let action = TweakDBInterface.GetObjectActionRecord(actionID);
    if !IsDefined(action) { return false; }
    return Equals(action.ActionName(), n"Use") || Equals(action.ActionName(), n"UseHealCharge") || Equals(action.ActionName(), n"Equip");
  }
  public static func InMenu(game: GameInstance) -> Bool {
    let bb = GameInstance.GetBlackboardSystem(game).Get(GetAllBlackboardDefs().UI_System);
    return !IsDefined(bb) || bb.GetBool(GetAllBlackboardDefs().UI_System.IsInMenu);
  }
  public static func Safe(player: ref<PlayerPuppet>) -> Bool {
    if !IsDefined(player) || player.IsReplacer() || player.IsDead() || player.IsInCombat() { return false; }
    let game = player.GetGame();
    if CyberwarePolicy.InMenu(game) { return false; }
    let scene = GameInstance.GetSceneSystem(game).GetScriptInterface();
    let bb = player.GetPlayerStateMachineBlackboard();
    if !IsDefined(scene) || !IsDefined(bb) { return false; }
    let high = bb.GetInt(GetAllBlackboardDefs().PlayerStateMachine.HighLevel);
    let tier = bb.GetInt(GetAllBlackboardDefs().PlayerStateMachine.SceneTier);
    if (high != 1 && high != 2) || (tier != 1 && tier != 2) { return false; }
    if scene.IsEntityInDialogue(player.GetEntityID()) || scene.IsRewindableSectionActive() ||
      GameInstance.GetQuestsContentSystem(game).IsTokensActivationBlocked() ||
      GameInstance.GetWorkspotSystem(game).IsActorInWorkspot(player) { return false; }
    let mount = GameInstance.GetMountingFacility(game).GetMountingInfoSingleWithObjects(player);
    if EntityID.IsDefined(mount.parentId) || GameInstance.GetTimeSystem(game).IsTimeDilationActive() { return false; }
    if EquipmentSystem.GetData(player).IsEquipPending() || StatusEffectSystem.ObjectHasStatusEffectWithTag(player, n"ActiveCamo") ||
      StatusEffectSystem.ObjectHasStatusEffectWithTag(player, n"CamoActiveOnPlayer") ||
      StatusEffectSystem.ObjectHasStatusEffectOfType(player, gamedataStatusEffectType.Berserk) ||
      StatusEffectSystem.ObjectHasStatusEffectOfType(player, gamedataStatusEffectType.Sandevistan) { return false; }
    // Let native weapon/gadget manipulation finish before removing installed arms.
    let ts = GameInstance.GetTransactionSystem(game);
    return ts.IsSlotEmpty(player, t"AttachmentSlots.WeaponRight") && ts.IsSlotEmpty(player, t"AttachmentSlots.WeaponLeft");
  }
  private func OnAttach() -> Void {
    this.running = true; this.epoch += 1; this.warmup = 4;
    this.actor = null; this.fault = false; ArrayClear(this.attempts); this.Schedule();
  }
  private func OnDetach() -> Void { this.running = false; this.epoch += 1; this.actor = null; }
  private func Schedule() -> Void {
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(PolicyTick.Create(this, this.epoch), 1.0, false);
  }
  public func Restored() -> Void {
    this.warmup = 4; this.actor = null; this.fault = false; ArrayClear(this.attempts);
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || this.epoch != epoch { return; }
    this.Schedule();
    let player = GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(player) { this.detail = "Waiting for player"; return; }
    if this.actor != player { this.actor = player; this.warmup = 4; ArrayClear(this.attempts); }
    if this.warmup > 0 { this.warmup -= 1; this.detail = "Load settling"; return; }
    if !CyberwarePolicy.Active(player) { this.pending = 0; this.detail = "Inactive / No Nerf / outside completed Tower"; return; }
    let data = EquipmentSystem.GetData(player);
    let ids = data.PTFRR1RestrictedEquipped();
    this.pending = ArraySize(ids);
    if this.fault { this.detail = "STOPPED: conservation mismatch; reload pre-test save and inspect log"; return; }
    if this.pending == 0 { this.detail = "No restricted installed items"; return; }
    if !CyberwarePolicy.Safe(player) { this.detail = "Pending safe gameplay; close menus, holster, leave combat/scene"; return; }
    let i = 0;
    while i < ArraySize(ids) {
      if !ArrayContains(this.attempts, ids[i]) {
        ArrayPush(this.attempts, ids[i]);
        let result = data.PTFRR1Remove(ids[i]);
        this.detail = "Unequip " + TDBID.ToStringDEBUG(ItemID.GetTDBID(ids[i])) + " result=" + ToString(result);
        this.audit += this.detail + "\n";
        ModLog(n"PTFR_Restrictions_R1", this.detail);
        if result < 0 { this.fault = true; }
        // One exact item per tick, once per load/manual retry. Never force a quest lock.
        let remaining = data.PTFRR1RestrictedEquipped();
        this.pending = ArraySize(remaining);
        return;
      }
      i += 1;
    }
    this.detail = "Pending locked/unresolved items; inspect status, then Enable() to retry when safe";
  }
  public func Enable() -> String {
    if !CyberwarePolicy.Completed(this.GetGameInstance()) { return "Refused: completed post-Tower free roam markers required; no story facts changed"; }
    let player = GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(player) || player.IsReplacer() { return "Refused: normal V required"; }
    if CyberwarePolicy.InMenu(this.GetGameInstance()) { return "Close the ripperdoc/menu before changing profile"; }
    if this.fault { return "Conservation fault latched: reload the pre-test save; automatic retry refused"; }
    this.mode = 1; ArrayClear(this.attempts); this.warmup = 1;
    return this.GetStatus();
  }
  public func NoNerf() -> String {
    if CyberwarePolicy.InMenu(this.GetGameInstance()) { return "Close the ripperdoc/menu before changing profile"; }
    this.mode = 2; return "No Nerf selected for this save. Owned items remain; re-equip manually. No old loadout restored.";
  }
  public func GetStatus() -> String {
    let player = GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    let remaining = "";
    if IsDefined(player) && CyberwarePolicy.Active(player) {
      let ids = EquipmentSystem.GetData(player).PTFRR1RestrictedEquipped();
      this.pending = ArraySize(ids);
      let i = 0;
      while i < ArraySize(ids) { remaining += " " + TDBID.ToStringDEBUG(ItemID.GetTDBID(ids[i])); i += 1; }
    }
    return "Cyberware R1 mode=" + ToString(this.mode) + " active=" + ToString(CyberwarePolicy.Active(player)) +
      " pending=" + ToString(this.pending) + " fault=" + ToString(this.fault) + " | " + this.detail + remaining;
  }
  public func GetAudit() -> String { return this.audit; }
  // Read-only admission for the opt-in Body migration; never clears a fault.
  public final func PTFRR2Healthy() -> Bool { return !this.fault; }
  public final func PTFRR2Ready(player: ref<PlayerPuppet>) -> Bool {
    let data = EquipmentSystem.GetData(player);
    if !IsDefined(data) { return false; }
    let ids = data.PTFRR1RestrictedEquipped();
    return !this.fault && this.warmup == 0 && this.actor == player && CyberwarePolicy.Active(player) &&
      ArraySize(ids) == 0 && !data.IsEquipPending();
  }
}
public class PolicyTick extends DelayCallback {
  private let policy: wref<CyberwarePolicy>;
  private let epoch: Int32;
  public static func Create(policy: ref<CyberwarePolicy>, epoch: Int32) -> ref<PolicyTick> {
    let tick = new PolicyTick(); tick.policy = policy; tick.epoch = epoch; return tick;
  }
  public func Call() -> Void { if IsDefined(this.policy) { this.policy.Poll(this.epoch); } }
}
