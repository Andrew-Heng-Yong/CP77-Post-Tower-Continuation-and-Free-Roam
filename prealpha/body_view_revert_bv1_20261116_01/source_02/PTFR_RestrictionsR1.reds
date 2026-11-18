module PTFR.RestrictionsR1

// ORIGINAL: r6/scripts/PTFR_PreAlpha/PTFR_Restrictions_R1/CyberwarePolicy.reds
// Save-local preference. No quest facts, inventory grants, stat resets or saves.
public class CyberwarePolicy extends ScriptableSystem {
  private persistent let mode: Int32; // 0 automatic, 1 explicitly enabled, 2 No Nerf
  // Save-local receipt for the first Arms and Hands removal pass.
  private persistent let treatmentHandoff: Int32;
  private let running: Bool;
  private let epoch: Int32;
  private let warmup: Int32;
  private let actor: wref<PlayerPuppet>;
  private let attempts: array<ItemID>;
  private let fault: Bool;
  private let detail: String;
  private let pending: Int32;
  private let audit: String;
  private let refundReadyReported: Bool;
  private let handRefreshAttempts: Int32;
  private let handRefreshRequested: Bool;
  private let representationReturnQueued: Bool;

  public static func Get(game: GameInstance) -> ref<CyberwarePolicy> {
    return GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.RestrictionsR1.CyberwarePolicy") as CyberwarePolicy;
  }
  public static func Completed(game: GameInstance) -> Bool {
    return Equals(CyberwarePolicy.CompletionBlocker(game), n"");
  }
  public static func CompletionBlocker(game: GameInstance) -> CName {
    let q = GameInstance.GetQuestsSystem(game);
    if !IsDefined(q) { return n"quest_system_unavailable"; }
    if q.GetFact(n"q307_done") != 1 || q.GetFact(n"q307_finished") != 1 ||
       q.GetFact(n"q307_active") != 0 || q.GetFact(n"q307_2079") != 1 {
      return n"tower_cleanup_pending";
    }
    if q.GetFact(n"q307_main_game_killed") != 1 || q.GetFact(n"q307_ep1_killed") != 1 ||
       q.GetFact(n"q305_johnny_scene_active") != 0 {
      return n"tower_teardown_pending";
    }
    if q.GetFact(n"PostTowerFreeRoamActive") != 1 || q.GetFact(n"PTFRP0_DR13") != 1 {
      return n"retained_return_pending";
    }
    let ponr = q.GetFact(n"q115_point_of_no_return");
    if ponr == 0 { return n""; }
    if ponr != 1 || q.GetFact(n"q307_debug_reset") != 0 || q.GetFact(n"q307_rooftop_chicken") != 0 ||
       q.GetFact(n"q115_var_test_def") != 0 || q.GetFact(n"q115_suicide_ending") != 0 {
      return n"q115_route_conflict";
    }
    // Both vanilla Reed routes from the Q115 roof converge on the native
    // Q115 call and AV receipts. Retain the Q115 boundary as story history.
    if q.GetFact(n"q307_start") != 1 || q.GetFact(n"q307_point_of_no_return") != 1 ||
       q.GetFact(n"q307_rooftop_q115_seated") != 1 || q.GetFact(n"q307_q115_call_done") != 1 ||
       q.GetFact(n"q307_confirm_av_done") != 1 || q.GetFact(n"q307_q115_wait") != 0 {
      return n"q115_rooftop_unverified";
    }
    // The owned credits/arrival chain follows vanilla Q307 cleanup. This is
    // setup admission only. Individual activity and history gates stay separate.
    if q.GetFact(n"PTFRP0_DR02") != 1 || q.GetFact(n"PTFRP0_DR07") != 1 || q.GetFact(n"PTFRP0_DR12") != 1 ||
       q.GetFact(n"PTFRPA2_Started") != 1 || q.GetFact(n"PTFRPA2_Teleported") != 1 ||
       q.GetFact(n"PTFRPA3_CoverReleased") != 1 || q.GetFact(n"PTFRPA4_CameraAligned") != 1 ||
       q.GetFact(n"PTFRPA2_ControlReady") != 1 {
      return n"q115_retained_arrival_unverified";
    }
    return n"";
  }
  public static func Active(owner: ref<GameObject>) -> Bool {
    let player = owner as PlayerPuppet;
    if !IsDefined(player) || player.IsReplacer() { return false; }
    if GameInstance.GetPlayerSystem(owner.GetGame()).GetLocalPlayerMainGameObject() != owner { return false; }
    let game = owner.GetGame();
    let policy = CyberwarePolicy.Get(game);
    if !IsDefined(policy) || policy.mode == 2 || !CyberwarePolicy.Completed(game) { return false; }
    let q = GameInstance.GetQuestsSystem(game);
    // Recovery can validate history and saved ledgers while policy writes wait.
    return q.GetFact(n"q115_point_of_no_return") == 0 || q.GetFact(n"PTFRPA2_Fault") == 0;
  }
  public static func Area(area: gamedataEquipmentArea) -> Bool {
    return Equals(area, gamedataEquipmentArea.FrontalCortexCW) || Equals(area, gamedataEquipmentArea.SystemReplacementCW) ||
      Equals(area, gamedataEquipmentArea.ArmsCW) || Equals(area, gamedataEquipmentArea.ArmsCWStyle) || Equals(area, gamedataEquipmentArea.EyesCW) ||
      Equals(area, gamedataEquipmentArea.MusculoskeletalSystemCW) || Equals(area, gamedataEquipmentArea.HandsCW) ||
      Equals(area, gamedataEquipmentArea.NervousSystemCW) || Equals(area, gamedataEquipmentArea.CardiovascularSystemCW) ||
      Equals(area, gamedataEquipmentArea.IntegumentarySystemCW) || Equals(area, gamedataEquipmentArea.LegsCW);
  }
  public static func Suppresses(owner: ref<GameObject>, id: ItemID) -> Bool {
    if !CyberwarePolicy.Active(owner) { return false; }
    let level = CyberwareTreatmentSettings.Level(id);
    return Equals(level, CyberwareTreatment.Disabled) || Equals(level, CyberwareTreatment.Limited);
  }
  public static func MustUnequip(owner: ref<GameObject>, id: ItemID) -> Bool {
    let level = CyberwareTreatmentSettings.Level(id);
    return Equals(level, CyberwareTreatment.Remove) ||
      (Equals(level, CyberwareTreatment.Limited) && CyberwareTreatmentSettings.Tattoo(ItemID.GetTDBID(id)) &&
        CyberwarePolicy.Get(owner.GetGame()).treatmentHandoff < 1);
  }
  public static func Denied(owner: ref<GameObject>, id: ItemID) -> Bool {
    return CyberwarePolicy.Active(owner) &&
      (Equals(CyberwareTreatmentSettings.Level(id), CyberwareTreatment.Disabled) || CyberwarePolicy.MustUnequip(owner, id));
  }
  public static func ModificationDenied(owner: ref<GameObject>, id: ItemID) -> Bool {
    return CyberwarePolicy.Denied(owner, id) || CyberwarePolicy.Suppresses(owner, id);
  }
  public static func OperatingSystemDisabled(owner: ref<GameObject>) -> Bool {
    if !CyberwarePolicy.Active(owner) { return false; }
    let equipment = EquipmentSystem.GetData(owner);
    return IsDefined(equipment) &&
      CyberwarePolicy.Suppresses(owner, equipment.GetActiveItem(gamedataEquipmentArea.SystemReplacementCW));
  }
  private static func ArmAppearance(owner: ref<GameObject>) -> ref<CyberwareCustomizationSystem> {
    return GameInstance.GetScriptableSystemsContainer(owner.GetGame()).Get(n"CyberwareCustomizationSystem") as CyberwareCustomizationSystem;
  }
  private static func ArmAppearanceSettled(owner: ref<GameObject>) -> Bool {
    let system = CyberwarePolicy.ArmAppearance(owner);
    if !IsDefined(system) { return false; }
    let data = system.GetSavedData();
    return !data.enabled && data.switcherIndex == 0u && !data.hasMaxTacApperanceEquipped;
  }
  public static func DeniedAction(owner: ref<GameObject>, item: wref<gameItemData>, actionID: TweakDBID) -> Bool {
    if !IsDefined(item) { return false; }
    let action = TweakDBInterface.GetObjectActionRecord(actionID);
    if !IsDefined(action) { return false; }
    if Equals(action.ActionName(), n"Equip") { return CyberwarePolicy.Denied(owner, item.GetID()); }
    return (Equals(action.ActionName(), n"Use") || Equals(action.ActionName(), n"UseHealCharge")) &&
      CyberwarePolicy.ModificationDenied(owner, item.GetID());
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
    this.actor = null; this.fault = false; ArrayClear(this.attempts);
    this.handRefreshAttempts = 0;
    this.Schedule();
  }
  private func OnDetach() -> Void { this.running = false; this.epoch += 1; this.actor = null; }
  private func Schedule() -> Void {
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(PolicyTick.Create(this, this.epoch), 1.0, false);
  }
  public func Restored() -> Void {
    this.QueueRequest(new CyberwareTreatmentRestore());
  }
  private func OnCyberwareTreatmentRestore(request: ref<CyberwareTreatmentRestore>) -> Void {
    if !this.running { return; }
    this.epoch += 1;
    this.warmup = 4; this.actor = null; this.fault = false; ArrayClear(this.attempts);
    this.refundReadyReported = false;
    this.handRefreshAttempts = 0;
    this.Schedule();
  }
  public func Poll(epoch: Int32) -> Void {
    let request = new CyberwareTreatmentStep();
    request.epoch = epoch;
    this.QueueRequest(request);
  }
  private func OnCyberwareTreatmentStep(request: ref<CyberwareTreatmentStep>) -> Void {
    if !this.running || this.epoch != request.epoch { return; }
    this.Schedule();
    let player = GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(player) { this.detail = "Waiting for player"; return; }
    if this.actor != player {
      this.actor = player;
      this.warmup = 4;
      this.refundReadyReported = false;
      this.handRefreshAttempts = 0;
      ArrayClear(this.attempts);
    }
    if this.warmup > 0 { this.warmup -= 1; this.detail = "Load settling"; return; }
    let data = EquipmentSystem.GetData(player);
    if !IsDefined(data) { this.detail = "Waiting for equipment"; return; }
    if !CyberwarePolicy.Active(player) {
      this.pending = 0;
      if this.mode == 2 && data.PTFRHasTreatedCyberware() {
        if !CyberwarePolicy.Safe(player) { this.detail = "No Nerf waiting for safe gameplay"; return; }
        data.PTFRRestoreCyberwareEffects();
      }
      this.detail = "Inactive / No Nerf / outside completed Tower";
      return;
    }
    let ids = data.PTFRPendingCyberwareRemoval();
    this.pending = ArraySize(ids);
    if this.fault { this.detail = "STOPPED: conservation mismatch; reload pre-test save and inspect log"; return; }
    if this.pending == 0 { this.RefreshPostTowerHands(player, data); }
    if this.pending == 0 && this.treatmentHandoff >= 1 && data.PTFRCyberwareEffectsReady() &&
      CyberwarePolicy.ArmAppearanceSettled(player) {
      this.ReportRefundReadiness();
      this.detail = "Cyberware treatment settled";
      return;
    }
    if !CyberwarePolicy.Safe(player) { this.detail = "Pending safe gameplay; close menus, holster, leave combat/scene"; return; }
    let effectsReady = data.PTFRCyberwareEffectsReady() || data.PTFRReconcileCyberwareEffects();
    if this.pending == 0 {
      if !CyberwarePolicy.ArmAppearanceSettled(player) {
        let appearance = CyberwarePolicy.ArmAppearance(player);
        if IsDefined(appearance) {
          let reset = new ResetPostTowerArmAppearance();
          reset.owner = player;
          appearance.QueueRequest(reset);
        }
        this.detail = "Waiting for native arm appearance reset";
        return;
      }
      if this.treatmentHandoff < 1 {
        this.treatmentHandoff = 1;
        this.handRefreshAttempts = 4;
        this.handRefreshRequested = false;
        this.representationReturnQueued = false;
        ModLog(n"PTFR_Restrictions_R1", "Arms and Hands handoff complete; cosmetic tattoo refits enabled.");
      }
      if data.PTFRCyberwareTreatmentReady() { this.ReportRefundReadiness(); }
      this.detail = effectsReady ? "Cyberware treatment settled" : data.PTFRCyberwareTreatmentStatus();
      return;
    }
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
        let remaining = data.PTFRPendingCyberwareRemoval();
        this.pending = ArraySize(remaining);
        return;
      }
      i += 1;
    }
    this.detail = "Pending locked/unresolved items; inspect status, then Enable() to retry when safe";
  }
  private func RefreshPostTowerHands(player: ref<PlayerPuppet>, data: ref<EquipmentSystemPlayerData>) -> Void {
    if this.handRefreshAttempts == 0 { return; }
    let game = player.GetGame();
    // Let the native arrival finish before touching its live attachment. The
    // cover and refund ledger have their own readiness checks.
    if GetFact(game, n"PTFRPA2_Finished") != 1 ||
      GameInstance.GetPlayerSystem(game).GetLocalPlayerControlledGameObject() != player ||
      !CyberwarePolicy.ArmAppearanceSettled(player) || !CyberwarePolicy.Safe(player) { return; }

    this.handRefreshAttempts -= 1;
    let result = data.PTFRRefreshPostTowerHands(!this.handRefreshRequested);
    if Equals(result, PostTowerHandAttachment.Attached) {
      this.handRefreshAttempts = 0;
      ModLog(n"PTFR_Restrictions_R1", "Post-Tower stock hands attachment confirmed.");
      return;
    }
    if Equals(result, PostTowerHandAttachment.Requested) && !this.handRefreshRequested {
      this.handRefreshRequested = true;
      ModLog(n"PTFR_Restrictions_R1", "Post-Tower stock hands attachment refresh requested.");
    }
    if this.handRefreshAttempts == 0 {
      ModLog(n"PTFR_Restrictions_R1", "Post-Tower stock hands attachment could not be confirmed.");
    }
  }
  private func ReportRefundReadiness() -> Void {
    if this.refundReadyReported { return; }
    this.refundReadyReported = true;
    ModLog(n"PTFR_Restrictions_R1", "Arms and Hands settled; per-item treatments processed; equipment ready for profile refunds.");
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
    this.mode = 2;
    return "No Nerf selected. Retained effects restore when V is safe. Removed items can be equipped manually.";
  }
  public func GetStatus() -> String {
    let player = GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(player) { return "Waiting for V"; }
    let data = EquipmentSystem.GetData(player);
    let pending = 0;
    if IsDefined(data) && CyberwarePolicy.Active(player) { pending = ArraySize(data.PTFRPendingCyberwareRemoval()); }
    return "Cyberware mode=" + ToString(this.mode) + " pending removal=" + ToString(pending) +
      " ready for refunds=" + ToString(IsDefined(data) && this.PTFRR2Ready(player)) + " | " + this.detail;
  }
  public func GetAudit() -> String { return this.audit; }
  // Read-only admission for the opt-in Body migration; never clears a fault.
  public final func PTFRR2Healthy() -> Bool { return !this.fault; }
  public final func PTFRR2Ready(player: ref<PlayerPuppet>) -> Bool {
    let data = EquipmentSystem.GetData(player);
    if !IsDefined(data) { return false; }
    let ids = data.PTFRPendingCyberwareRemoval();
    return !this.fault && this.warmup == 0 && this.actor == player && CyberwarePolicy.Active(player) &&
      this.treatmentHandoff >= 1 && ArraySize(ids) == 0 && data.PTFRCyberwareTreatmentReady() &&
      CyberwarePolicy.ArmAppearanceSettled(player) && !data.IsEquipPending();
  }
}
public class CyberwareTreatmentRestore extends ScriptableSystemRequest {}
public class CyberwareTreatmentStep extends ScriptableSystemRequest { public let epoch: Int32; }

public class PolicyTick extends DelayCallback {
  private let policy: wref<CyberwarePolicy>;
  private let epoch: Int32;
  public static func Create(policy: ref<CyberwarePolicy>, epoch: Int32) -> ref<PolicyTick> {
    let tick = new PolicyTick(); tick.policy = policy; tick.epoch = epoch; return tick;
  }
  public func Call() -> Void { if IsDefined(this.policy) { this.policy.Poll(this.epoch); } }
}

// ORIGINAL: r6/scripts/PTFR_PreAlpha/PTFR_Restrictions_R1/CyberwarePreservationCF1.reds
@addMethod(EquipmentSystemPlayerData)
public final const func PTFRCF1PreservesExactItem(id: ItemID) -> Bool {
  // This transient ID is set only around PTFRR1Remove's native UnequipItem call.
  return ItemID.IsValid(id) && ItemID.IsValid(this.ptfrr1PreserveParts) &&
    id == this.ptfrr1PreserveParts && CyberwarePolicy.ModificationDenied(this.m_owner, id);
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
    if this.m_playerData.PTFRCF1PreservesExactItem(id) || CyberwarePolicy.Suppresses(this.m_owner, id) {
      ModLog(n"PTFR_CyberwareCF1", "Preserved exact Skeleton instance during native slot cleanup: " +
        TDBID.ToStringDEBUG(ItemID.GetTDBID(id)) + " slot=" + ToString(this.m_targetEquipSlotIndex));
      return;
    }
  }
  wrappedMethod(game);
}

// ORIGINAL: r6/scripts/PTFR_PreAlpha/PTFR_Restrictions_R1/EquipmentHooks.reds
@addField(EquipmentSystemPlayerData)
private let ptfrr1PreserveParts: ItemID;

@wrapMethod(EquipmentSystemPlayerData)
public final func AssignItemToHotkey(newID: ItemID, hotkey: EHotkey) -> Void {
  // Buying a retained implant must not auto-bind its active ability.
  // None / ordinary replacement consumables from native unequip pass through.
  if CyberwarePolicy.ModificationDenied(this.m_owner, newID) { return; }
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
  if IsDefined(this.m_owner) && this.PTFRHasTreatedCyberware() { this.PTFRCyberwareRestoreStarted(); }
  wrappedMethod(); // Keep EquipmentEx and vanilla restoration chains intact.
  if IsDefined(this.m_owner) && this.m_owner == GameInstance.GetPlayerSystem(this.m_owner.GetGame()).GetLocalPlayerMainGameObject() {
    let policy = CyberwarePolicy.Get(this.m_owner.GetGame());
    if IsDefined(policy) { policy.Restored(); }
  }
}

@addMethod(EquipmentSystemPlayerData)
public final func PTFRPendingCyberwareRemoval() -> array<ItemID> {
  let ids = this.PTFRInstalledCyberware();
  let pending: array<ItemID>;
  let i = 0;
  while i < ArraySize(ids) {
    if CyberwarePolicy.MustUnequip(this.m_owner, ids[i]) { ArrayPush(pending, ids[i]); }
    i += 1;
  }
  return pending;
}

@addMethod(EquipmentSystemPlayerData)
public final func PTFRInstalledCyberware() -> array<ItemID> {
  let ids: array<ItemID>;
  let i = 0;
  let j: Int32;
  while i < ArraySize(this.m_equipment.equipAreas) {
    if CyberwarePolicy.Area(this.m_equipment.equipAreas[i].areaType) {
      j = 0;
      while j < ArraySize(this.m_equipment.equipAreas[i].equipSlots) {
        let id = this.m_equipment.equipAreas[i].equipSlots[j].itemID;
        if ItemID.IsValid(id) && !ArrayContains(ids, id) { ArrayPush(ids, id); }
        j += 1;
      }
    }
    i += 1;
  }
  return ids;
}

@addMethod(EquipmentSystemPlayerData)
public final func PTFRR1Remove(id: ItemID) -> Int32 {
  if !CyberwarePolicy.Active(this.m_owner) || !CyberwarePolicy.MustUnequip(this.m_owner, id) || !CyberwarePolicy.Safe(this.m_owner as PlayerPuppet) { return 0; }
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
  ModLog(n"PTFR_CyberwareCD1", "BEFORE item=" + CyberwareDiagnosticsCD1.Item(id) + " dataID=" + CyberwareDiagnosticsCD1.Item(item.GetID()) + " quantity=" + ToString(quantity) + " area/slot=" + ToString(area) + "/" + ToString(slot) + " parts=" + ToString(ArraySize(before)) + CyberwareDiagnosticsCD1.Parts(before));
  this.ptfrr1PreserveParts = id;
  this.UnequipItem(area, slot, false);
  this.ptfrr1PreserveParts = ItemID.None();
  // Native RemoveEquipGLPs processes the item AND attached parts. Retain the
  // owned part tree instead of relying on undocumented RemovePart disposition.
  let readback = ts.GetItemData(this.m_owner, id);
  if !IsDefined(readback) || ts.GetItemQuantity(this.m_owner, id) != quantity {
    ModLog(n"PTFR_CyberwareCD1", "FAIL item_or_quantity item=" + CyberwareDiagnosticsCD1.Item(id) + " readbackDefined=" + ToString(IsDefined(readback)) + " quantityBefore/after=" + ToString(quantity) + "/" + ToString(ts.GetItemQuantity(this.m_owner, id)) + " equippedNow=" + CyberwareDiagnosticsCD1.Item(this.GetItemInEquipSlot(area, slot)));
    return -1;
  }
  readback.GetItemParts(after);
  ModLog(n"PTFR_CyberwareCD1", "AFTER item=" + CyberwareDiagnosticsCD1.Item(id) + " dataID=" + CyberwareDiagnosticsCD1.Item(readback.GetID()) + " quantity=" + ToString(ts.GetItemQuantity(this.m_owner, id)) + " equippedNow=" + CyberwareDiagnosticsCD1.Item(this.GetItemInEquipSlot(area, slot)) + " parts=" + ToString(ArraySize(after)) + CyberwareDiagnosticsCD1.Parts(after));
  if ArraySize(before) != ArraySize(after) {
    ModLog(n"PTFR_CyberwareCD1", "FAIL part_count item=" + CyberwareDiagnosticsCD1.Item(id) + " before/after=" + ToString(ArraySize(before)) + "/" + ToString(ArraySize(after)));
    return -1;
  }
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
    if !found {
      ModLog(n"PTFR_CyberwareCD1", "FAIL part_identity_or_slot item=" + CyberwareDiagnosticsCD1.Item(id) + " beforeIndex=" + ToString(i));
      return -1;
    }
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
  if IsDefined(request) && CyberwarePolicy.Active(this.m_owner) {
    if CyberwarePolicy.ModificationDenied(this.m_owner, request.itemID) { return; }
    let area = EquipmentSystem.GetEquipAreaType(request.itemID);
    if CyberwarePolicy.Area(area) && (request.transferInstalledParts || request.removeOldItem) &&
      request.slotIndex >= 0 && request.slotIndex < this.GetNumberOfSlots(area, true) &&
      CyberwarePolicy.ModificationDenied(this.m_owner, this.GetItemInEquipSlot(area, request.slotIndex)) { return; }
  }
  wrappedMethod(request);
}

@wrapMethod(RPGManager)
public final static func CanUpgradeCyberware(owner: ref<GameObject>, itemID: ItemID, isEquipped: Bool, selectedQuality: gamedataQuality, out upgradeItemQuality: gamedataQuality, out upgradeItemRecord: ref<Item_Record>, out costData: CyberwareUpgradeCostData, opt updateOutputOnFailure: Bool) -> Bool {
  if CyberwarePolicy.ModificationDenied(owner, itemID) { return false; }
  let result = wrappedMethod(owner, itemID, isEquipped, selectedQuality, upgradeItemQuality, upgradeItemRecord, costData, updateOutputOnFailure);
  if IsDefined(upgradeItemRecord) && CyberwarePolicy.ModificationDenied(owner, ItemID.FromTDBID(upgradeItemRecord.GetID())) { return false; }
  return result;
}

@wrapMethod(RPGManager)
public final static func HandleBuyShardPopupClosed(owner: ref<GameObject>, equippedItemId: ItemID, resultData: ref<RipperdocTokenPopupCloseData>) -> Void {
  // Before the upgrade charge and seed increment, not merely the later queue.
  if CyberwarePolicy.ModificationDenied(owner, equippedItemId) || (IsDefined(resultData.chosenOptionData) && CyberwarePolicy.ModificationDenied(owner, resultData.chosenOptionData.GetID())) { return; }
  wrappedMethod(owner, equippedItemId, resultData);
}

@wrapMethod(ItemActionsHelper)
public final static func UseItem(executor: wref<GameObject>, itemID: ItemID) -> Bool {
  if CyberwarePolicy.ModificationDenied(executor, itemID) { return false; }
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

// CD1 diagnostics only. No saved fields, retries or inventory writes.
public abstract class CyberwareDiagnosticsCD1 {
  public static func Item(id: ItemID) -> String {
    return TDBID.ToStringDEBUG(ItemID.GetTDBID(id)) + " hash=" + ToString(ItemID.GetCombinedHash(id)) + " seed=" + ToString(ItemID.GetRngSeed(id)) + " query=" + ToString(ItemID.IsQuery(id)) + " structure=" + ToString(EnumInt(ItemID.GetStructure(id)));
  }
  public static func Parts(parts: array<InnerItemData>) -> String {
    let text = ""; let i = 0;
    while i < ArraySize(parts) && i < 64 {
      text += " [" + ToString(i) + "] " + CyberwareDiagnosticsCD1.Item(InnerItemData.GetItemID(parts[i])) + " slot=" + TDBID.ToStringDEBUG(InnerItemData.GetSlotID(parts[i]));
      i += 1;
    }
    if i < ArraySize(parts) { text += " [diagnostic list capped at 64; all parts still checked]"; }
    return text;
  }
}

// ORIGINAL: r6/scripts/PTFR_PreAlpha/PTFR_Restrictions_R1/RipperdocHooks.reds
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
  if IsDefined(item) && CyberwarePolicy.ModificationDenied(this.m_player, item.GetID()) {
    this.m_buttonHintsController.RemoveButtonHint(n"upgrade_perk");
    this.m_buttonHintsController.RemoveButtonHint(this.m_upgradeCWInputName);
    if CyberwarePolicy.Denied(this.m_player, item.GetID()) && (isVendorItem || !item.IsEquipped()) {
      this.m_buttonHintsController.RemoveButtonHint(n"select");
      this.m_buttonHintsController.AddButtonHint(n"select", isVendorItem ? "Buy to inventory (installation blocked)" : "Installation blocked: post-Tower");
    }
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
  let item = this.GetUIInventoryItem();
  if !IsDefined(item) || !CyberwarePolicy.Denied(this.ptfrr1SlotPlayer, item.GetID()) { return; }
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
    let note = "Installed implants are disabled. You can remove them or buy items to inventory.";
    if Equals(data.category, gamedataEquipmentArea.ArmsCW) { note = "Combat arms cannot be refitted after the Tower."; }
    if Equals(data.category, gamedataEquipmentArea.EyesCW) { note = "Basic Kiroshi Optics remain functional. Other optics are disabled."; }
    if Equals(data.category, gamedataEquipmentArea.HandsCW) { note = "Stock tattoos can be refitted as cosmetic ink after the handoff."; }
    if Equals(data.category, gamedataEquipmentArea.MusculoskeletalSystemCW) { note = "Titanium Bones provide limited carry capacity. Other implants are disabled."; }
    if Equals(data.category, gamedataEquipmentArea.IntegumentarySystemCW) { note = "Chitin, Subdermal Armor and Carapace provide reduced armor. Other implants are disabled."; }
    inkTextRef.SetText(this.m_desc, note);
  }
}

// Appended to the installed R1 module by prepare.py.
public enum CyberwareTreatment {
  Unmanaged = 0,
  Remove = 1,
  Disabled = 2,
  Limited = 3,
  Functional = 4
}

public abstract class CyberwareTreatmentSettings {
  // Provisional flat bonuses. The native model and its parts remain intact.
  public static func TitaniumCarry() -> Float { return 20.0; }
  public static func ChitinArmor() -> Float { return 15.0; }
  public static func SubdermalArmor() -> Float { return 5.0; }
  public static func CarapaceArmor() -> Float { return 10.0; }

  public static func Tattoo(record: TweakDBID) -> Bool {
    return CyberwareTreatmentSettings.JohnnyTattoo(record) ||
      CyberwareTreatmentSettings.TogetherForever(record) ||
      CyberwareTreatmentSettings.TygerClaws(record);
  }

  public static func Level(id: ItemID) -> CyberwareTreatment {
    if !ItemID.IsValid(id) { return CyberwareTreatment.Unmanaged; }
    let record = ItemID.GetTDBID(id);
    let area = EquipmentSystem.GetEquipAreaType(id);
    if Equals(area, gamedataEquipmentArea.PersonalLink) { return CyberwareTreatment.Functional; }
    if !CyberwarePolicy.Area(area) { return CyberwareTreatment.Unmanaged; }
    if Equals(area, gamedataEquipmentArea.HandsCW) && CyberwareTreatmentSettings.Tattoo(record) {
      return CyberwareTreatment.Limited;
    }
    if Equals(area, gamedataEquipmentArea.ArmsCW) || Equals(area, gamedataEquipmentArea.ArmsCWStyle) ||
      Equals(area, gamedataEquipmentArea.HandsCW) {
      return CyberwareTreatment.Remove;
    }
    if Equals(area, gamedataEquipmentArea.EyesCW) && CyberwareTreatmentSettings.BasicKiroshi(record) {
      return CyberwareTreatment.Functional;
    }
    if CyberwareTreatmentSettings.TitaniumBones(record) || CyberwareTreatmentSettings.Chitin(record) ||
      CyberwareTreatmentSettings.SubdermalArmor(record) || CyberwareTreatmentSettings.Carapace(record) {
      return CyberwareTreatment.Limited;
    }
    return CyberwareTreatment.Disabled;
  }

  public static func RetainedModifier(id: ItemID) -> ref<gameStatModifierData> {
    let record = ItemID.GetTDBID(id);
    if CyberwareTreatmentSettings.TitaniumBones(record) {
      return RPGManager.CreateStatModifier(gamedataStatType.CarryCapacity, gameStatModifierType.Additive, CyberwareTreatmentSettings.TitaniumCarry());
    }
    let armor: Float;
    if CyberwareTreatmentSettings.Chitin(record) {
      armor = CyberwareTreatmentSettings.ChitinArmor();
    } else if CyberwareTreatmentSettings.SubdermalArmor(record) {
      armor = CyberwareTreatmentSettings.SubdermalArmor();
    } else if CyberwareTreatmentSettings.Carapace(record) {
      armor = CyberwareTreatmentSettings.CarapaceArmor();
    } else {
      return null;
    }
    return RPGManager.CreateStatModifier(gamedataStatType.Armor, gameStatModifierType.Additive, armor);
  }

  public static func JohnnyTattoo(record: TweakDBID) -> Bool {
    return record == t"Items.CasiusTattoo" ||
      record == t"Items.AdvancedCasiusTattoo";
  }

  public static func TogetherForever(record: TweakDBID) -> Bool {
    return record == t"Items.SilverhandTattoo" ||
      record == t"Items.AdvancedSilverhandTattoo";
  }

  public static func TygerClaws(record: TweakDBID) -> Bool {
    return record == t"Items.YakuzaTattoo" ||
      record == t"Items.AdvancedYakuzaTattoo" ||
      record == t"Items.AdvancedYakuzaTattooUncommon" ||
      record == t"Items.AdvancedYakuzaTattooUncommonPlus" ||
      record == t"Items.AdvancedYakuzaTattooRare" ||
      record == t"Items.AdvancedYakuzaTattooRarePlus" ||
      record == t"Items.AdvancedYakuzaTattooEpic" ||
      record == t"Items.AdvancedYakuzaTattooEpicPlus" ||
      record == t"Items.AdvancedYakuzaTattooLegendary" ||
      record == t"Items.AdvancedYakuzaTattooLegendaryPlus" ||
      record == t"Items.AdvancedYakuzaTattooLegendaryPlusPlus";
  }

  public static func TitaniumBones(record: TweakDBID) -> Bool {
    return record == t"Items.TitaniumInfusedBonesCommon" ||
      record == t"Items.TitaniumInfusedBonesUncommon" ||
      record == t"Items.TitaniumInfusedBonesRare" ||
      record == t"Items.AdvancedTitaniumInfusedBonesCommon" ||
      record == t"Items.AdvancedTitaniumInfusedBonesCommonPlus" ||
      record == t"Items.AdvancedTitaniumInfusedBonesUncommon" ||
      record == t"Items.AdvancedTitaniumInfusedBonesUncommonPlus" ||
      record == t"Items.AdvancedTitaniumInfusedBonesRare" ||
      record == t"Items.AdvancedTitaniumInfusedBonesRarePlus" ||
      record == t"Items.AdvancedTitaniumInfusedBonesEpic" ||
      record == t"Items.AdvancedTitaniumInfusedBonesEpicPlus" ||
      record == t"Items.AdvancedTitaniumInfusedBonesLegendary" ||
      record == t"Items.AdvancedTitaniumInfusedBonesLegendaryPlus" ||
      record == t"Items.AdvancedTitaniumInfusedBonesLegendaryPlusPlus" ||
      TDBID.ToNumber(record) == 169911475159ul ||
      TDBID.ToNumber(record) == 171594206120ul ||
      TDBID.ToNumber(record) == 180261958180ul ||
      TDBID.ToNumber(record) == 185922612573ul ||
      TDBID.ToNumber(record) == 185978810275ul ||
      TDBID.ToNumber(record) == 186931960455ul ||
      TDBID.ToNumber(record) == 189439444180ul ||
      TDBID.ToNumber(record) == 195673396803ul ||
      TDBID.ToNumber(record) == 206014209057ul ||
      TDBID.ToNumber(record) == 206465263695ul ||
      TDBID.ToNumber(record) == 225590903736ul;
  }

  public static func Chitin(record: TweakDBID) -> Bool {
    return record == t"Items.IconicAdvancedChitonCommon" ||
      record == t"Items.IconicAdvancedChitonCommonPlus" ||
      record == t"Items.IconicAdvancedChitonUncommon" ||
      record == t"Items.IconicAdvancedChitonUncommonPlus" ||
      record == t"Items.IconicAdvancedChitonRare" ||
      record == t"Items.IconicAdvancedChitonRarePlus" ||
      record == t"Items.IconicAdvancedChitonEpic" ||
      record == t"Items.IconicAdvancedChitonEpicPlus" ||
      record == t"Items.IconicAdvancedChitonLegendary" ||
      record == t"Items.IconicAdvancedChitonLegendaryPlus" ||
      record == t"Items.IconicAdvancedChitonLegendaryPlusPlus";
  }

  public static func SubdermalArmor(record: TweakDBID) -> Bool {
    return record == t"Items.AdvancedBoringPlatingCommon" ||
      record == t"Items.AdvancedBoringPlatingCommonPlus" ||
      record == t"Items.AdvancedBoringPlatingUncommon" ||
      record == t"Items.AdvancedBoringPlatingUncommonPlus" ||
      record == t"Items.AdvancedBoringPlatingRare" ||
      record == t"Items.AdvancedBoringPlatingRarePlus" ||
      record == t"Items.AdvancedBoringPlatingEpic" ||
      record == t"Items.AdvancedBoringPlatingEpicPlus" ||
      record == t"Items.AdvancedBoringPlatingLegendary" ||
      record == t"Items.AdvancedBoringPlatingLegendaryPlus" ||
      record == t"Items.AdvancedBoringPlatingLegendaryPlusPlus";
  }

  public static func Carapace(record: TweakDBID) -> Bool {
    return record == t"Items.AdvancedWeirdTankyPlatingCommon" ||
      record == t"Items.AdvancedWeirdTankyPlatingUncommon" ||
      record == t"Items.AdvancedWeirdTankyPlatingUncommonPlus" ||
      record == t"Items.AdvancedWeirdTankyPlatingRare" ||
      record == t"Items.AdvancedWeirdTankyPlatingRarePlus" ||
      record == t"Items.AdvancedWeirdTankyPlatingEpic" ||
      record == t"Items.AdvancedWeirdTankyPlatingEpicPlus" ||
      record == t"Items.AdvancedWeirdTankyPlatingLegendary" ||
      record == t"Items.AdvancedWeirdTankyPlatingLegendaryPlus" ||
      record == t"Items.AdvancedWeirdTankyPlatingLegendaryPlusPlus";
  }

  public static func BasicKiroshi(record: TweakDBID) -> Bool {
    return record == t"Items.AdvancedKiroshiOpticsBareCommon" ||
      record == t"Items.AdvancedKiroshiOpticsBareCommonPlus" ||
      record == t"Items.AdvancedKiroshiOpticsBareUncommon" ||
      record == t"Items.AdvancedKiroshiOpticsBareUncommonPlus" ||
      record == t"Items.AdvancedKiroshiOpticsBareRare" ||
      record == t"Items.AdvancedKiroshiOpticsBareRarePlus" ||
      record == t"Items.AdvancedKiroshiOpticsBareEpic" ||
      record == t"Items.AdvancedKiroshiOpticsBareEpicPlus" ||
      record == t"Items.AdvancedKiroshiOpticsBareLegendary" ||
      record == t"Items.AdvancedKiroshiOpticsBareLegendaryPlus" ||
      record == t"Items.AdvancedKiroshiOpticsBareLegendaryPlusPlus";
  }
}

public class TreatedCyberware extends IScriptable {
  public let id: ItemID;
  public let nativeStatsSubtracted: Bool;
  public let retained: ref<gameStatModifierData>;
}

@addField(EquipmentSystemPlayerData)
private let ptfrTreated: array<ref<TreatedCyberware>>;

@addField(EquipmentSystemPlayerData)
private let ptfrSkippedPackages: array<ItemID>;

@addField(EquipmentSystemPlayerData)
private let ptfrEffectsVerified: Bool;

@addField(EquipmentSystemPlayerData)
private let ptfrTreatmentStatus: String;

@addMethod(EquipmentSystemPlayerData)
private final const func PTFRFindTreatment(id: ItemID) -> Int32 {
  let i = 0;
  while i < ArraySize(this.ptfrTreated) {
    if this.ptfrTreated[i].id == id { return i; }
    i += 1;
  }
  return -1;
}

@addMethod(EquipmentSystemPlayerData)
private final func PTFRCyberwareRestoreStarted() -> Void {
  // An equipment restore can run again on the same data object. Drop only
  // our transient stat handles before the native equip restoration.
  let stats = GameInstance.GetStatsSystem(this.m_owner.GetGame());
  let ownerID = Cast<StatsObjectID>(this.m_owner.GetEntityID());
  let i = 0;
  while i < ArraySize(this.ptfrTreated) {
    if IsDefined(this.ptfrTreated[i].retained) { stats.RemoveModifier(ownerID, this.ptfrTreated[i].retained); }
    i += 1;
  }
  ArrayClear(this.ptfrTreated);
  ArrayClear(this.ptfrSkippedPackages);
  this.ptfrEffectsVerified = false;
  this.ptfrTreatmentStatus = "";
}

@wrapMethod(EquipmentSystemPlayerData)
private final func ApplyEquipGLPs(itemID: ItemID) -> Void {
  if CyberwarePolicy.Suppresses(this.m_owner, itemID) {
    this.ptfrEffectsVerified = false;
    if !ArrayContains(this.ptfrSkippedPackages, itemID) { ArrayPush(this.ptfrSkippedPackages, itemID); }
    return;
  }
  wrappedMethod(itemID);
}

@wrapMethod(EquipmentSystemPlayerData)
private final func RemoveEquipGLPs(itemID: ItemID) -> Void {
  // Initial handoff removal of already-applied packages takes the native
  // chain. Once suppressed, later native unequip has no package to release.
  if this.PTFRFindTreatment(itemID) >= 0 || ArrayContains(this.ptfrSkippedPackages, itemID) { return; }
  wrappedMethod(itemID);
}

@addMethod(EquipmentSystemPlayerData)
private final func PTFREquipPackages(item: wref<gameItemData>) -> array<TweakDBID> {
  let packages: array<wref<GameplayLogicPackage_Record>>;
  let parts: array<InnerItemData>;
  let ids: array<TweakDBID>;
  let record = RPGManager.GetItemRecord(item.GetID());
  if IsDefined(record) { record.OnEquip(packages); }
  item.GetItemParts(parts);
  let i = 0;
  while i < ArraySize(packages) { ArrayPush(ids, packages[i].GetID()); i += 1; }
  i = 0;
  while i < ArraySize(parts) {
    record = RPGManager.GetItemRecord(InnerItemData.GetItemID(parts[i]));
    if IsDefined(record) {
      ArrayClear(packages);
      record.OnEquip(packages);
      let j = 0;
      while j < ArraySize(packages) { ArrayPush(ids, packages[j].GetID()); j += 1; }
    }
    i += 1;
  }
  return ids;
}

@addMethod(EquipmentSystemPlayerData)
private final func PTFRPackageOwnershipSafe(item: wref<gameItemData>, packages: array<TweakDBID>) -> Bool {
  let ts = GameInstance.GetTransactionSystem(this.m_owner.GetGame());
  let i = 0;
  while i < ArraySize(this.m_equipment.equipAreas) {
    let slots = this.m_equipment.equipAreas[i].equipSlots;
    let j = 0;
    while j < ArraySize(slots) {
      let id = slots[j].itemID;
      if ItemID.IsValid(id) && id != item.GetID() && !CyberwarePolicy.Suppresses(this.m_owner, id) {
        let other = ts.GetItemData(this.m_owner, id);
        if IsDefined(other) {
          let active = this.PTFREquipPackages(other);
          let k = 0;
          while k < ArraySize(active) {
            if ArrayContains(packages, active[k]) { return false; }
            k += 1;
          }
        }
      }
      j += 1;
    }
    i += 1;
  }
  return true;
}

@addMethod(EquipmentSystemPlayerData)
private final func PTFRLiveEquipPackages(item: wref<gameItemData>) -> array<TweakDBID> {
  let applied: array<TweakDBID>;
  let found: array<TweakDBID>;
  GameInstance.GetGameplayLogicPackageSystem(this.m_owner.GetGame()).GetAppliedPackagesOfInstigator(this.m_owner, this.m_owner, applied);
  let packages = this.PTFREquipPackages(item);
  let i = 0;
  while i < ArraySize(packages) {
    if ArrayContains(applied, packages[i]) { ArrayPush(found, packages[i]); }
    i += 1;
  }
  return found;
}

@addMethod(EquipmentSystemPlayerData)
private final func PTFRApplyTreatment(id: ItemID) -> Bool {
  if this.PTFRFindTreatment(id) >= 0 { return true; }
  let game = this.m_owner.GetGame();
  let item = GameInstance.GetTransactionSystem(game).GetItemData(this.m_owner, id);
  if !IsDefined(item) {
    this.PTFRNoteTreatmentStatus("Waiting for exact installed item " + CyberwareDiagnosticsCD1.Item(id));
    return false;
  }
  let livePackages = this.PTFRLiveEquipPackages(item);
  if ArraySize(livePackages) > 0 && !this.PTFRPackageOwnershipSafe(item, livePackages) {
    this.PTFRNoteTreatmentStatus("Cannot isolate shared equip package for " + CyberwareDiagnosticsCD1.Item(id));
    return false;
  }

  let treatment = new TreatedCyberware();
  treatment.id = id;
  if Equals(CyberwareTreatmentSettings.Level(id), CyberwareTreatment.Limited) {
    treatment.retained = CyberwareTreatmentSettings.RetainedModifier(id);
    if IsDefined(treatment.retained) &&
      !GameInstance.GetStatsSystem(game).AddModifier(Cast<StatsObjectID>(this.m_owner.GetEntityID()), treatment.retained) {
      this.PTFRNoteTreatmentStatus("Retained modifier admission pending for " + CyberwareDiagnosticsCD1.Item(id));
      return false;
    }
  }
  // Vanilla equipment applies each record and part GLP with V as both
  // target and instigator. Retire those references through the matching
  // instigator overload, leaving other instigators alone.
  let glps = GameInstance.GetGameplayLogicPackageSystem(game);
  let i = 0;
  while i < ArraySize(livePackages) {
    glps.RemovePackageOfInstigator(this.m_owner, this.m_owner, livePackages[i]);
    i += 1;
  }
  if item.UsesVariants() {
    item.SubtractStatsOnUnequip(this.m_owner);
    treatment.nativeStatsSubtracted = true;
  }
  ArrayPush(this.ptfrTreated, treatment);
  return true;
}

@addMethod(EquipmentSystemPlayerData)
public final func PTFRCyberwareEffectsReady() -> Bool {
  return this.ptfrEffectsVerified && this.PTFRCyberwareTreatmentReady();
}

@addMethod(EquipmentSystemPlayerData)
public final func PTFRCyberwareTreatmentReady() -> Bool {
  // The refund ledger depends on completed per-instance treatment and
  // stable slots. A package ID cannot identify a residual contribution.
  let ids = this.PTFRInstalledCyberware();
  let i = 0;
  while i < ArraySize(ids) {
    if CyberwarePolicy.Suppresses(this.m_owner, ids[i]) && this.PTFRFindTreatment(ids[i]) < 0 { return false; }
    i += 1;
  }
  return true;
}

@addMethod(EquipmentSystemPlayerData)
public final func PTFRReconcileCyberwareEffects() -> Bool {
  let ids = this.PTFRInstalledCyberware();
  let ok = true;
  let i = 0;
  while i < ArraySize(ids) {
    if CyberwarePolicy.Suppresses(this.m_owner, ids[i]) && !this.PTFRApplyTreatment(ids[i]) { ok = false; }
    i += 1;
  }
  if !ok { this.ptfrEffectsVerified = false; return false; }
  let residual = this.PTFRResidualCyberwarePackage(ids);
  this.ptfrEffectsVerified = StrLen(residual) == 0;
  this.PTFRNoteTreatmentStatus(this.ptfrEffectsVerified ? "Cyberware treatment settled" : residual);
  return this.ptfrEffectsVerified;
}

@addMethod(EquipmentSystemPlayerData)
private final func PTFRResidualCyberwarePackage(ids: array<ItemID>) -> String {
  let ts = GameInstance.GetTransactionSystem(this.m_owner.GetGame());
  let i = 0;
  while i < ArraySize(ids) {
    if CyberwarePolicy.Suppresses(this.m_owner, ids[i]) {
      let item = ts.GetItemData(this.m_owner, ids[i]);
      if !IsDefined(item) { return "Waiting for exact installed item " + CyberwareDiagnosticsCD1.Item(ids[i]); }
      let packages = this.PTFRLiveEquipPackages(item);
      if ArraySize(packages) > 0 {
        return "Native package still listed for " + TDBID.ToStringDEBUG(ItemID.GetTDBID(ids[i])) +
          ": " + TDBID.ToStringDEBUG(packages[0]);
      }
    }
    i += 1;
  }
  return "";
}

@addMethod(EquipmentSystemPlayerData)
private final func PTFRNoteTreatmentStatus(status: String) -> Void {
  if Equals(this.ptfrTreatmentStatus, status) { return; }
  this.ptfrTreatmentStatus = status;
  ModLog(n"PTFR_Restrictions_R1", status);
}

@addMethod(EquipmentSystemPlayerData)
public final func PTFRCyberwareTreatmentStatus() -> String {
  return this.ptfrTreatmentStatus;
}

@addMethod(EquipmentSystemPlayerData)
public final func PTFRHasTreatedCyberware() -> Bool {
  return ArraySize(this.ptfrTreated) > 0 || ArraySize(this.ptfrSkippedPackages) > 0;
}

@addMethod(EquipmentSystemPlayerData)
public final func PTFRRestoreCyberwareEffects() -> Void {
  // Called only by the explicit No Nerf transition when native V is safe.
  let effects = this.ptfrTreated;
  let skipped = this.ptfrSkippedPackages;
  this.PTFRCyberwareRestoreStarted();
  let ts = GameInstance.GetTransactionSystem(this.m_owner.GetGame());
  let i = 0;
  while i < ArraySize(effects) {
    let id = effects[i].id;
    let item = ts.GetItemData(this.m_owner, id);
    if IsDefined(item) && this.GetSlotIndex(id) >= 0 {
      this.ApplyEquipGLPs(id);
      if effects[i].nativeStatsSubtracted { item.AddStatsOnEquip(this.m_owner); }
    }
    ArrayRemove(skipped, id);
    i += 1;
  }
  i = 0;
  while i < ArraySize(skipped) {
    if this.GetSlotIndex(skipped[i]) >= 0 { this.ApplyEquipGLPs(skipped[i]); }
    i += 1;
  }
  PlayerPuppet.ChacheQuickHackListCleanup(this.m_owner as PlayerPuppet);
}

@wrapMethod(EquipmentSystemPlayerData)
private final func EquipItem(itemID: ItemID, slotIndex: Int32, opt blockActiveSlotsUpdate: Bool, opt forceEquipWeapon: Bool) -> Void {
  if !CyberwarePolicy.Suppresses(this.m_owner, itemID) {
    wrappedMethod(itemID, slotIndex, blockActiveSlotsUpdate, forceEquipWeapon);
    return;
  }
  let priorSlot = this.GetSlotIndex(itemID);
  wrappedMethod(itemID, slotIndex, blockActiveSlotsUpdate, forceEquipWeapon);
  if CyberwarePolicy.Suppresses(this.m_owner, itemID) && this.GetSlotIndex(itemID) == slotIndex &&
    (priorSlot != slotIndex || this.PTFRFindTreatment(itemID) < 0) {
    // Native equip has just applied the per-instance variant stats.
    if !this.PTFRApplyTreatment(itemID) {
      ModLog(n"PTFR_Restrictions_R1", "Effect reconciliation pending for " + CyberwareDiagnosticsCD1.Item(itemID));
    }
  }
}

@wrapMethod(EquipmentSystemPlayerData)
private final func UnequipItem(equipAreaIndex: Int32, slotIndex: Int32, opt forceRemove: Bool) -> Void {
  let id = this.GetItemInEquipSlot(equipAreaIndex, slotIndex);
  let index = this.PTFRFindTreatment(id);
  let preserve = CyberwarePolicy.Suppresses(this.m_owner, id);
  if index < 0 && !preserve && !ArrayContains(this.ptfrSkippedPackages, id) {
    wrappedMethod(equipAreaIndex, slotIndex, forceRemove);
    return;
  }
  let item = GameInstance.GetTransactionSystem(this.m_owner.GetGame()).GetItemData(this.m_owner, id);
  if !IsDefined(item) || (!forceRemove && item.HasTag(n"UnequipBlocked")) {
    wrappedMethod(equipAreaIndex, slotIndex, forceRemove);
    return;
  }
  let previous = this.ptfrr1PreserveParts;
  this.ptfrr1PreserveParts = id;
  // Balance the exact native item subtraction in this synchronous unequip.
  // If native declines the request, leave the treatment in place.
  let restoreNativeStats = index >= 0 && this.ptfrTreated[index].nativeStatsSubtracted;
  if restoreNativeStats { item.AddStatsOnEquip(this.m_owner); }
  wrappedMethod(equipAreaIndex, slotIndex, forceRemove);
  this.ptfrr1PreserveParts = previous;
  if this.GetItemInEquipSlot(equipAreaIndex, slotIndex) == id {
    if restoreNativeStats { item.SubtractStatsOnUnequip(this.m_owner); }
    return;
  }
  if index >= 0 {
    let retained = this.ptfrTreated[index].retained;
    if IsDefined(retained) {
      GameInstance.GetStatsSystem(this.m_owner.GetGame()).RemoveModifier(Cast<StatsObjectID>(this.m_owner.GetEntityID()), retained);
    }
    ArrayErase(this.ptfrTreated, index);
  }
  this.ptfrEffectsVerified = false;
  ArrayRemove(this.ptfrSkippedPackages, id);
}

@wrapMethod(ItemModificationSystem)
private final func InstallItemPart(obj: ref<GameObject>, itemID: ItemID, partItemID: ItemID, opt slotID: TweakDBID) -> Bool {
  if CyberwarePolicy.ModificationDenied(obj, itemID) { return false; }
  return wrappedMethod(obj, itemID, partItemID, slotID);
}

@wrapMethod(ItemModificationSystem)
private final const func RemoveItemPart(obj: ref<GameObject>, itemID: ItemID, slotID: TweakDBID, shouldUpdateEntity: Bool) -> ItemID {
  if CyberwarePolicy.ModificationDenied(obj, itemID) { return ItemID.None(); }
  return wrappedMethod(obj, itemID, slotID, shouldUpdateEntity);
}

@wrapMethod(ItemModificationSystem)
private final func SwapItemPart(obj: ref<GameObject>, itemID: ItemID, partItemID: ItemID, slotID: TweakDBID) -> Bool {
  if CyberwarePolicy.ModificationDenied(obj, itemID) { return false; }
  return wrappedMethod(obj, itemID, partItemID, slotID);
}

@wrapMethod(EquipmentSystemPlayerData)
public final func OnGameplayEquipProgramsRequest(request: ref<GameplayEquipProgramsRequest>) -> Void {
  if CyberwarePolicy.OperatingSystemDisabled(this.m_owner) { return; }
  wrappedMethod(request);
}

@wrapMethod(EquipmentSystemPlayerData)
public final func OnPartInstallRequest(request: ref<PartInstallRequest>) -> Void {
  if IsDefined(request) && CyberwarePolicy.Suppresses(this.m_owner, request.itemID) { return; }
  wrappedMethod(request);
}

@wrapMethod(EquipmentSystemPlayerData)
public final func OnPartUninstallRequest(request: ref<PartUninstallRequest>) -> Void {
  if IsDefined(request) && CyberwarePolicy.Suppresses(this.m_owner, request.itemID) { return; }
  wrappedMethod(request);
}

@wrapMethod(EquipmentSystem)
public final static func IsCyberdeckEquipped(owner: ref<GameObject>) -> Bool {
  if CyberwarePolicy.OperatingSystemDisabled(owner) { return false; }
  return wrappedMethod(owner);
}

@wrapMethod(Device)
protected const final func IsCyberdeckEquippedOnPlayer() -> Bool {
  if CyberwarePolicy.OperatingSystemDisabled(GetPlayer(this.GetGame())) { return false; }
  return wrappedMethod();
}

@wrapMethod(RPGManager)
public final static func GetPlayerQuickHackListWithQuality(player: wref<PlayerPuppet>) -> array<PlayerQuickhackData> {
  if CyberwarePolicy.OperatingSystemDisabled(player) { PlayerPuppet.ChacheQuickHackListCleanup(player); }
  return wrappedMethod(player);
}

@wrapMethod(QuickHackableHelper)
public final static func TryToCycleOverclockedState(player: ref<GameObject>) -> Bool {
  if CyberwarePolicy.OperatingSystemDisabled(player) { return false; }
  return wrappedMethod(player);
}

@wrapMethod(PlayerPuppet)
private final func ActivateIconicCyberware() -> Void {
  if CyberwarePolicy.OperatingSystemDisabled(this) { return; }
  wrappedMethod();
}

public enum PostTowerHandAttachment {
  Waiting = 0,
  Requested = 1,
  Attached = 2
}

@addMethod(EquipmentSystemPlayerData)
public final func PTFRRefreshPostTowerHands(rebuild: Bool) -> PostTowerHandAttachment {
  if (this.GetEquipAreaIndex(gamedataEquipmentArea.ArmsCW) >= 0 &&
      this.GetNumberOfItemsInEquipmentArea(gamedataEquipmentArea.ArmsCW) > 0) ||
     (this.GetEquipAreaIndex(gamedataEquipmentArea.ArmsCWStyle) >= 0 &&
      this.GetNumberOfItemsInEquipmentArea(gamedataEquipmentArea.ArmsCWStyle) > 0) {
    return PostTowerHandAttachment.Waiting;
  }
  let player = this.m_owner as PlayerPuppet;
  let ts = GameInstance.GetTransactionSystem(player.GetGame());
  let slot = t"AttachmentSlots.RightArm";
  if ts.IsSlotSpawningAnyItem(player, slot) { return PostTowerHandAttachment.Waiting; }

  let fists = this.GetItemInEquipSlot(gamedataEquipmentArea.BaseFists, 0);
  if ItemID.GetTDBID(fists) != ItemID.GetTDBID(this.GetBaseFistsItemID()) || !ts.HasItem(player, fists) {
    this.HandleArmsCWUnequip(player);
    return PostTowerHandAttachment.Requested;
  }
  let record = TweakDBInterface.GetWeaponItemRecord(ItemID.GetTDBID(fists));
  if !IsDefined(record) || !IsDefined(record.HolsteredItem()) { return PostTowerHandAttachment.Waiting; }

  let stockHands = record.HolsteredItem().GetID();
  let equipped = this.GetItemInEquipSlot(gamedataEquipmentArea.RightArm, 0);
  let attachment = ts.GetItemInSlot(player, slot);
  if ItemID.GetTDBID(equipped) != stockHands || !ts.HasItem(player, equipped) ||
    (IsDefined(attachment) && !ts.HasItemInSlot(player, slot, equipped)) {
    EquipmentSystemPlayerData.UpdateArmSlot(player, fists, true);
    return PostTowerHandAttachment.Requested;
  }

  // A saved equipment slot can be correct while its live visual is stale.
  // Rebuild only the matching stock attachment and keep the owned instance.
  let attached = IsDefined(attachment);
  if attached {
    if !rebuild { return PostTowerHandAttachment.Attached; }
    if !ts.RemoveItemFromSlot(player, slot, true) { return PostTowerHandAttachment.Waiting; }
  } else if !ts.IsSlotEmpty(player, slot) {
    return PostTowerHandAttachment.Waiting;
  }
  if ts.AddItemToSlot(player, slot, equipped, true) || attached { return PostTowerHandAttachment.Requested; }
  return PostTowerHandAttachment.Waiting;
}

public class ResetPostTowerArmAppearance extends ScriptableSystemRequest {
  public let owner: wref<GameObject>;
}

@addMethod(CyberwareCustomizationSystem)
private final func OnResetPostTowerArmAppearance(request: ref<ResetPostTowerArmAppearance>) -> Void {
  if request.owner != this.m_playerPuppet || !CyberwarePolicy.Active(request.owner) ||
    !CyberwarePolicy.Safe(request.owner as PlayerPuppet) { return; }
  let equipment = EquipmentSystem.GetData(request.owner);
  if !IsDefined(equipment) || ItemID.IsValid(equipment.GetActiveItem(gamedataEquipmentArea.ArmsCW)) ||
    ItemID.IsValid(equipment.GetActiveItem(gamedataEquipmentArea.ArmsCWStyle)) { return; }
  if this.savedData.enabled || this.savedData.switcherIndex != 0u {
    this.savedData.enabled = false;
    this.savedData.switcherIndex = 0u;
    this.RestoreCyberwareCustomization(true);
  }
  if this.savedData.hasMaxTacApperanceEquipped { this.RemoveMaxTacApperance(); }
}

@wrapMethod(CoolExitJumpEvents)
protected func OnEnter(stateContext: ref<StateContext>, scriptInterface: ref<StateGameScriptInterface>) -> Void {
  let owner = scriptInterface.executionOwner;
  let disableLegBoost = false;
  if CyberwarePolicy.Active(owner) {
    let equipment = EquipmentSystem.GetData(owner);
    if IsDefined(equipment) {
      let legs = equipment.GetActiveItem(gamedataEquipmentArea.LegsCW);
      let magnitude = stateContext.GetTemporaryIntParameter(n"coolExitMagnitude");
      disableLegBoost = CyberwarePolicy.Suppresses(owner, legs) && ItemID.IsOfTDBID(legs, t"Items.ReinforcedMusclesRare") &&
        magnitude.valid && Equals(IntEnum<vehicleCoolExitImpulseLevel>(magnitude.value), vehicleCoolExitImpulseLevel.MaxImpulse) &&
        !stateContext.GetTemporaryVectorParameter(n"exitMomentum").valid;
    }
  }
  wrappedMethod(stateContext, scriptInterface);
  if disableLegBoost {
    let impulse = stateContext.GetTemporaryVectorParameter(n"impulse");
    if impulse.valid {
      let value = impulse.value;
      value.Z -= this.GetStaticFloatParameterDefault("chargeJumpHeight", 10.0);
      stateContext.SetTemporaryVectorParameter(n"impulse", value, true);
    }
  }
}
