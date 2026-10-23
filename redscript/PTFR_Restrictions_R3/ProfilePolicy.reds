module PTFR.RestrictionsR3

import PTFR.RestrictionsR1.*
import PTFR.RestrictionsR2.*

// New journal. Never rewrites R2's schema, counters or completed snapshot.
public class ProfilePolicy extends ScriptableSystem {
  private persistent let enabled: Bool;
  private persistent let profileID: CName;
  private persistent let revision: Int32;
  private persistent let fingerprint: CName;
  private persistent let blocked: array<gamedataNewPerkType>;
  private persistent let healthTarget: Float;
  private persistent let vitalsRequested: Bool;
  private persistent let stage: Int32; // 0 unused, 1 wait R2, 2 refund, 3 settle, 4 complete, 5 fault
  private persistent let expected: BodySnapshot;
  private persistent let inflight: Bool;
  private persistent let refunded: Int32;
  private persistent let starting: Int32;
  private persistent let handAttempted: Bool;
  private let running: Bool;
  private let epoch: Int32;
  private let actor: wref<PlayerPuppet>;
  private let queued: Bool;
  private let mutation: Bool;
  private let selected: gamedataNewPerkType;
  private let settled: Int32;
  private let warmup: Int32;
  private let cadence: Int32;
  private let detail: String;
  private let audit: String;
  private let physical: ref<ProfilePhysical>;

  public static func Get(game: GameInstance) -> ref<ProfilePolicy> {
    return GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.RestrictionsR3.ProfilePolicy") as ProfilePolicy;
  }
  public static func Active(owner: ref<GameObject>) -> Bool {
    if !IsDefined(owner) || !CyberwarePolicy.Active(owner) { return false; }
    let policy = ProfilePolicy.Get(owner.GetGame());
    return IsDefined(policy) && policy.enabled;
  }
  public static func Busy(owner: ref<GameObject>) -> Bool {
    if !ProfilePolicy.Active(owner) { return false; }
    let policy = ProfilePolicy.Get(owner.GetGame());
    return policy.stage == 2 || policy.stage == 3;
  }
  public static func PerkDenied(owner: ref<GameObject>, perk: gamedataNewPerkType) -> Bool {
    if !ProfilePolicy.Active(owner) { return false; }
    if EnumInt(perk) < 0 || EnumInt(perk) >= EnumInt(gamedataNewPerkType.Count) || Equals(perk, gamedataNewPerkType.Cool_Right_Perk_3_3) { return true; }
    return ArrayContains(ProfilePolicy.Get(owner.GetGame()).blocked, perk);
  }
  public static func OwnPerk(owner: ref<GameObject>, perk: gamedataNewPerkType) -> Bool {
    if !ProfilePolicy.Busy(owner) { return false; }
    let policy = ProfilePolicy.Get(owner.GetGame());
    return policy.stage == 2 && policy.inflight && policy.mutation && policy.actor == owner && Equals(policy.selected, perk);
  }
  public static func OwnHand(owner: ref<GameObject>) -> Bool {
    if !ProfilePolicy.Active(owner) { return false; }
    let policy = ProfilePolicy.Get(owner.GetGame());
    return policy.actor == owner && policy.stage == 1 && policy.inflight && policy.handAttempted;
  }
  private func OnAttach() -> Void {
    this.running = true;
    this.Restored();
  }
  private func OnDetach() -> Void {
    this.running = false; this.epoch += 1; this.queued = false; this.mutation = false;
    if IsDefined(this.physical) { this.physical.Release(); }
    this.physical = null; this.actor = null;
  }
  public func Restored() -> Void {
    this.epoch += 1; this.queued = false; this.mutation = false;
    if IsDefined(this.physical) { this.physical.Release(); }
    this.physical = new ProfilePhysical();
    this.actor = null; this.warmup = 4; this.settled = 0;
    this.UpgradeImplantProfile();
    if this.enabled && !this.MatchesDefinition() { this.Fail("Profile revision/hash changed. Saved gates retained; no automatic migration."); }
    if this.inflight { this.Fail("Interrupted R3 journal. No replay/compensation; use the pre-test save."); }
    if this.running { this.Schedule(); }
  }
  private func Schedule() -> Void {
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(ProfileTick.Create(this, this.epoch), 0.25, false);
  }
  private func UpgradeImplantProfile() -> Void {
    // Reviewed one-way relaxation from either exact strict revision.
    // Keep snapshots, stages, historical refund counters and vitals opt-in.
    // In-flight/faulted/unknown saves must never be repaired by a profile switch.
    if !this.enabled || this.inflight || this.stage < 1 || this.stage > 4 { return; }
    if NotEquals(this.profileID, n"tower_strict") { return; }
    let versionOne = this.revision == 1 && this.healthTarget == 100.00 &&
      Equals(this.fingerprint, n"995DFBEA743A4FD89745DA7A5F880B033057D6AF470C57546C305E8DD17E31A1");
    let versionTwo = this.revision == 2 && this.healthTarget == 150.00 &&
      Equals(this.fingerprint, n"117BF6C7A6E0FE29A4E64C7A0583DB9E3A9914D5FE8C42F82637D5D6DB8DE1E1");
    if !versionOne && !versionTwo { return; }
    if NotEquals(ProfileDefinition.ID(), "tower_implant_focused") || ProfileDefinition.Revision() != 1 || ProfileDefinition.Health() != 150.00 ||
      NotEquals(ProfileDefinition.Fingerprint(), "EA4423FBE8A6DF1A3977417061BB8E582522C4EA9DFACCA5BC92F3906EDFD7D0") { return; }
    let previous = ProfileDefinition.PreviousStrictBlocked(); let i = 0;
    if ArraySize(previous) != ArraySize(this.blocked) { return; }
    while i < ArraySize(previous) { if NotEquals(previous[i], this.blocked[i]) { return; } i += 1; }
    let selection = ProfileDefinition.OtherBlocked(); i = 0;
    if ArraySize(selection) >= ArraySize(previous) { return; }
    while i < ArraySize(selection) { if !ArrayContains(previous, selection[i]) { return; } i += 1; }
    this.profileID = StringToName(ProfileDefinition.ID());
    this.blocked = selection;
    this.healthTarget = ProfileDefinition.Health();
    this.revision = ProfileDefinition.Revision();
    this.fingerprint = StringToName(ProfileDefinition.Fingerprint());
    this.Note("Implant-focused profile selected. Relaxed skills can be purchased normally; no ranks restored or points granted. Historical refund counters, journal and vitals activation unchanged.");
  }
  private func MatchesDefinition() -> Bool {
    let expected = ProfileDefinition.OtherBlocked(); let i = 0;
    if ArraySize(expected) != ArraySize(this.blocked) { return false; }
    while i < ArraySize(expected) { if NotEquals(expected[i], this.blocked[i]) { return false; } i += 1; }
    return Equals(this.profileID, StringToName(ProfileDefinition.ID())) && this.revision == ProfileDefinition.Revision() &&
      Equals(this.fingerprint, StringToName(ProfileDefinition.Fingerprint())) && this.healthTarget == ProfileDefinition.Health();
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    this.Schedule();
    let player = GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if this.actor != player {
      if IsDefined(this.physical) { this.physical.Release(); }
      this.physical = new ProfilePhysical(); this.actor = player; this.warmup = 4;
    }
    if !IsDefined(player) { return; }
    // Smart targeting is a Cyberware Only rule, not contingent on spending perks.
    this.physical.Update(player, this.enabled && this.vitalsRequested && this.stage >= 3 && this.stage <= 4 &&
      this.MatchesDefinition() && ProfilePolicy.Active(player), this.healthTarget);
    if !this.enabled || this.stage == 5 || this.queued || !ProfilePolicy.Active(player) { return; }
    if this.warmup > 0 { this.warmup -= 1; return; }
    this.cadence += 1; if this.cadence < 4 { return; } this.cadence = 0;
    if !BodyPolicy.Safe(player) { this.settled = 0; this.detail = "Waiting: safe gameplay, menus closed, holstered, no Overshield."; return; }
    let step = new ProfileStep(); step.epoch = this.epoch; step.player = player;
    this.queued = true; this.QueueRequest(step);
  }
  private func OnProfileStep(step: ref<ProfileStep>) -> Void {
    if step.epoch != this.epoch { return; } this.queued = false;
    let player = step.player;
    if !this.running || this.stage == 5 || this.actor != player || !ProfilePolicy.Active(player) || !BodyPolicy.Safe(player) { return; }
    if !this.MatchesDefinition() { this.Fail("Profile changed; journal not replayed."); return; }
    let legacy = BodyPolicy.Get(player.GetGame());
    if legacy.PTFRR3Faulted() { this.Fail("Existing Body/Relic journal faulted. It was not reset."); return; }
    if !legacy.PTFRR3Complete() { this.detail = "Waiting for existing Body/Relic migration: " + legacy.GetStatus(); return; }
    let chrome = CyberwarePolicy.Get(player.GetGame());
    if !chrome.PTFRR2Healthy() { this.Fail("Cyberware reconciliation fault."); return; }
    if !chrome.PTFRR2Ready(player) { this.detail = "Waiting for cyberware reconciliation."; return; }
    let data = PlayerDevelopmentSystem.GetData(player);
    if !IsDefined(data) { this.Fail("No development data."); return; }
    let current = data.PTFRR2Snapshot();
    if !current.valid || current.body != 3 || BodyPolicy.Total(current) != 0 || RelicCatalogue.Total(current) != 0 {
      this.Fail("Body/Relic completion invariant changed. No repeat refunds."); return;
    }
    if this.stage == 4 {
      if this.Total(current) != 0 { this.Fail("Restricted ranks reappeared; automatic repeat refunds refused."); }
      return;
    }
    if !ProfileCatalogue.Valid() { this.Fail("Stock perk catalogue changed; refund refused before mutation."); return; }
    if this.stage == 1 {
      let equipment = EquipmentSystem.GetData(player);
      if !IsDefined(equipment) { this.Fail("No equipment data."); return; }
      let second = ItemID.None();
      if equipment.GetNumberOfSlots(gamedataEquipmentArea.HandsCW, true) > 1 { second = equipment.GetItemInEquipSlot(gamedataEquipmentArea.HandsCW, 1); }
      if ItemID.IsValid(second) {
        if ItemID.IsValid(equipment.GetItemInEquipSlot(gamedataEquipmentArea.HandsCW, 0)) {
          this.detail = "Empty Hands slot 1 or move the second tattoo to inventory at a ripperdoc, then close menus."; return;
        }
        if this.handAttempted { this.Fail("Second Hands slot remained occupied after one relocation attempt."); return; }
        this.handAttempted = true; this.inflight = true;
        let moved = equipment.PTFRR3MoveTattooToFirst();
        if !moved { this.Fail("Tattoo relocation could not be acknowledged; no retry or perk refund."); return; }
        this.inflight = false; this.detail = "Tattoo moved with quantity/parts retained; waiting for equipment settling."; return;
      }
      if this.Total(current) > 2147483647 - current.primaryUnspent { this.Fail("Perk refund would overflow."); return; }
      this.expected = current; this.starting = this.Total(current); this.stage = 2;
      this.Note("Other-tree journal started with " + ToString(this.starting) + " purchased ranks. Completed Body/Relic refunds not replayed."); return;
    }
    if !BodyPolicy.Same(this.expected, current, -1, false) { this.Fail("Unexpected progression drift. No compensation/replay."); return; }
    if this.stage == 3 {
      if this.vitalsRequested && this.physical.Faulted() { this.detail = "HP module STOPPED; progression is not replayed. " + this.physical.Status(); return; }
      if this.vitalsRequested && !this.physical.HealthReady() { this.detail = "Waiting for HP readback: " + this.physical.Status(); return; }
      this.settled += 1; if this.settled < 4 { return; }
      this.stage = 4; this.Note("COMPLETE. Other-tree ranks refunded=" + ToString(this.refunded) + ". " + this.Measure()); return;
    }
    if this.stage != 2 || this.inflight { this.Fail("Unexpected R3 transaction state."); return; }
    if this.Total(current) == 0 { this.stage = 3; this.settled = 0; return; }
    this.RefundOne(player, data);
  }
  private func RefundOne(player: ref<PlayerPuppet>, data: ref<PlayerDevelopmentData>) -> Void {
    let i = 0;
    while i < ArraySize(this.blocked) {
      let perk = this.blocked[i]; let index = EnumInt(perk);
      if this.expected.perkRanks[index] > 0 && data.CheckIfAllnewPerkParentSold(perk) {
        let admission = PlayerDevelopmentSystem.CanSellNewPerk(player, perk);
        if !admission.success { this.Fail("Native slot/capacity admission refused for " + EnumValueToString("gamedataNewPerkType", Cast<Int64>(index))); return; }
        if !ProfilePolicy.EmptyNativeSideEffectSlots(player) { this.Fail("Native side-effect slot guard failed; no forced sale."); return; }
        this.selected = perk; this.inflight = true; this.mutation = true;
        let sold = PlayerDevelopmentSystem.GetInstance(player).PTFRR3SellPerk(player, perk);
        this.mutation = false;
        let after = data.PTFRR2Snapshot();
        if !sold || !BodyPolicy.Same(this.expected, after, index, false) { this.Fail("Rank/point acknowledgement failed; no retry."); return; }
        this.expected = after; this.refunded += 1; this.inflight = false;
        let notice = new SellNewPerk(); notice.Set(player, perk);
        UIInventoryScriptableSystem.GetInstance(player.GetGame()).QueueRequest(notice);
        data.PTFRR2PublishUI();
        this.Note("Refunded one " + EnumValueToString("gamedataNewPerkType", Cast<Int64>(index)) + " rank (" + ToString(this.refunded) + "/" + ToString(this.starting) + ")."); return;
      }
      i += 1;
    }
    this.Fail("No dependency-safe leaf. Force-selling refused.");
  }
  public static func EmptyNativeSideEffectSlots(player: ref<PlayerPuppet>) -> Bool {
    let e = EquipmentSystem.GetData(player);
    if !IsDefined(e) || e.IsEquipPending() { return false; }
    if e.GetNumberOfSlots(gamedataEquipmentArea.HandsCW, true) > 1 && ItemID.IsValid(e.GetItemInEquipSlot(gamedataEquipmentArea.HandsCW, 1)) { return false; }
    let i = 0;
    while i < e.GetNumberOfSlots(gamedataEquipmentArea.MusculoskeletalSystemCW, true) {
      if ItemID.IsValid(e.GetItemInEquipSlot(gamedataEquipmentArea.MusculoskeletalSystemCW, i)) { return false; } i += 1;
    }
    i = 0;
    while i < e.GetNumberOfSlots(gamedataEquipmentArea.IntegumentarySystemCW, true) {
      if ItemID.IsValid(e.GetItemInEquipSlot(gamedataEquipmentArea.IntegumentarySystemCW, i)) { return false; } i += 1;
    }
    return true;
  }
  private func Total(snapshot: BodySnapshot) -> Int32 {
    let n = 0; let i = 0;
    while i < ArraySize(this.blocked) { n += snapshot.perkRanks[EnumInt(this.blocked[i])]; i += 1; } return n;
  }
  public func FullNerf() -> String { return this.Apply(true); }
  public func FullNerfWithoutVitals() -> String { return this.Apply(false); }
  public func Apply(vitals: Bool) -> String {
    let game = this.GetGameInstance(); let player = GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !CyberwarePolicy.Completed(game) || !BodyPolicy.Safe(player) { return "Refused: completed Tower and safe normal gameplay required."; }
    if this.stage == 5 || this.inflight { return "Refused: fault/in-flight journal; no replay. " + this.GetStatus(); }
    if this.enabled {
      if !this.MatchesDefinition() { return "Refused: saved profile differs; no automatic migration."; }
      if vitals && !this.vitalsRequested && this.stage == 4 {
        this.vitalsRequested = true; this.Note("HP module enabled on completed migration; no refunds replayed.");
      } else { if vitals && !this.vitalsRequested { return "Wait until the no-vitals migration completes before enabling HP."; } }
      return "Not replayed. " + this.GetStatus();
    }
    if !ProfileCatalogue.Valid() { return "Refused: unsupported perk catalogue."; }
    let data = PlayerDevelopmentSystem.GetData(player);
    if !IsDefined(data) { return "Refused: progression data unavailable."; }
    let snapshot = data.PTFRR2Snapshot();
    if !snapshot.valid || snapshot.perkRanks[EnumInt(gamedataNewPerkType.Cool_Right_Perk_3_3)] != 0 { return "Refused: invalid snapshot or obsolete perk ownership."; }
    let legacy = BodyPolicy.Get(game);
    if !IsDefined(legacy) || legacy.PTFRR3Faulted() { return "Refused: existing Body/Relic journal faulted."; }
    let status = legacy.PTFRR3StartBodyRelic();
    if !BodyPolicy.BlockBody(player) || !BodyPolicy.BlockRelic(player) || legacy.PTFRR3Faulted() { return "Refused: " + status; }
    this.profileID = StringToName(ProfileDefinition.ID()); this.revision = ProfileDefinition.Revision(); this.fingerprint = StringToName(ProfileDefinition.Fingerprint());
    this.blocked = ProfileDefinition.OtherBlocked(); this.healthTarget = ProfileDefinition.Health();
    this.vitalsRequested = vitals; this.enabled = true; this.stage = 1; this.actor = player; this.warmup = 4;
    this.Note("Profile queued; Body/Relic preserved. HP requested=" + ToString(vitals) + "; stamina untouched."); return this.GetStatus();
  }
  private func Fail(message: String) -> Void { this.mutation = false; this.stage = 5; this.Note("STOPPED: " + message); }
  private func Note(message: String) -> Void { this.detail = message; this.audit += message + "\n"; ModLog(n"PTFR_Restrictions_R3", message); }
  public func GetAudit() -> String { return this.audit; }
  public func GetStatus() -> String {
    return "Profile R3 " + ToString(this.profileID) + " revision=" + ToString(this.revision) + " stage=" + ToString(this.stage) +
      " inflight=" + ToString(this.inflight) + " other ranks refunded=" + ToString(this.refunded) + "/" + ToString(this.starting) +
      " HP requested=" + ToString(this.vitalsRequested) + " | " + this.detail +
      " | " + (IsDefined(this.physical) ? this.physical.Status() : "Physical module not attached");
  }
  public func Measure() -> String {
    return BodyPolicy.Get(this.GetGameInstance()).PTFRR3MeasureNative() + " | R3 HP requested=" + ToString(this.vitalsRequested) +
      " target=" + ToString(this.healthTarget) + " | " + (IsDefined(this.physical) ? this.physical.Status() : "Physical module not attached");
  }
}

public class ProfileStep extends ScriptableSystemRequest { public let epoch: Int32; public let player: wref<PlayerPuppet>; }
public class ProfileTick extends DelayCallback {
  private let policy: wref<ProfilePolicy>; private let epoch: Int32;
  public static func Create(policy: ref<ProfilePolicy>, epoch: Int32) -> ref<ProfileTick> {
    let tick = new ProfileTick(); tick.policy = policy; tick.epoch = epoch; return tick;
  }
  public func Call() -> Void { if IsDefined(this.policy) { this.policy.Poll(this.epoch); } }
}
