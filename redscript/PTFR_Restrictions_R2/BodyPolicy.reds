module PTFR.RestrictionsR2

import PTFR.RestrictionsR1.*
import PTFR.RestrictionsR3.*

// Opt-in, save-local, one-way progression migration. No Health/Stamina writes.
public class BodyPolicy extends ScriptableSystem {
  private persistent let enabled: Bool;
  private persistent let schema: Int32;
  private persistent let stage: Int32; // 0 unused, 1 admission, 2 refund, 3 settle, 4 done, 5 fault
  private persistent let inflight: Bool;
  private persistent let expected: BodySnapshot;
  private persistent let refundedRanks: Int32;
  private persistent let refundedAttributes: Int32;
  private persistent let startingBody: Int32;
  private persistent let startingRanks: Int32;
  // Defaults false in existing schema-1 saves. Explicit command opts them in.
  private persistent let relicEnabled: Bool;
  private persistent let refundedRelicRanks: Int32;
  private persistent let refundedRelicPoints: Int32;
  private persistent let startingRelicRanks: Int32;
  private let beforeVitals: String;
  private let afterVitals: String;
  private let detail: String;
  private let audit: String;
  private let running: Bool;
  private let epoch: Int32;
  private let queued: Bool;
  private let actor: wref<PlayerPuppet>;
  private let warmup: Int32;
  private let readyTicks: Int32;
  private let settleTicks: Int32;
  private let previousHealth: Float;
  private let previousStamina: Float;
  private let previousHealthPool: Float;
  private let previousStaminaPool: Float;
  private let mutation: Int32; // 1 Body perk, 2 Body reset/relock, 3 Relic perk
  private let selected: gamedataNewPerkType;

  public static func Get(game: GameInstance) -> ref<BodyPolicy> {
    return GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.RestrictionsR2.BodyPolicy") as BodyPolicy;
  }
  public static func BlockBody(owner: ref<GameObject>) -> Bool {
    if !IsDefined(owner) || !CyberwarePolicy.Active(owner) { return false; }
    let policy = BodyPolicy.Get(owner.GetGame());
    return IsDefined(policy) && policy.enabled;
  }
  public static func Busy(owner: ref<GameObject>) -> Bool {
    if ProfilePolicy.Busy(owner) { return true; }
    if !BodyPolicy.BlockBody(owner) { return false; }
    let policy = BodyPolicy.Get(owner.GetGame());
    return policy.stage >= 1 && policy.stage <= 3;
  }
  public static func BlockRelic(owner: ref<GameObject>) -> Bool {
    return BodyPolicy.BlockBody(owner) && BodyPolicy.Get(owner.GetGame()).relicEnabled;
  }
  public static func OwnMutation(owner: ref<GameObject>) -> Bool {
    if !IsDefined(owner) { return false; }
    let policy = BodyPolicy.Get(owner.GetGame());
    return IsDefined(policy) && policy.inflight && policy.actor == owner && policy.mutation > 0;
  }
  public static func OwnPerk(owner: ref<GameObject>, perk: gamedataNewPerkType) -> Bool {
    if ProfilePolicy.OwnPerk(owner, perk) { return true; }
    if !BodyPolicy.OwnMutation(owner) { return false; }
    let policy = BodyPolicy.Get(owner.GetGame());
    return (policy.mutation == 1 || (policy.mutation == 3 && policy.relicEnabled)) && Equals(policy.selected, perk);
  }
  public static func OwnRelicPerk(owner: ref<GameObject>, perk: gamedataNewPerkType) -> Bool {
    return BodyPolicy.OwnPerk(owner, perk) && BodyPolicy.BlockRelic(owner) && BodyPolicy.Get(owner.GetGame()).mutation == 3;
  }
  public static func OwnBodyReset(owner: ref<GameObject>) -> Bool {
    if !BodyPolicy.OwnMutation(owner) { return false; }
    return BodyPolicy.Get(owner.GetGame()).mutation == 2;
  }
  public static func Safe(player: ref<PlayerPuppet>) -> Bool {
    if !IsDefined(player) || !IsDefined(EquipmentSystem.GetData(player)) { return false; }
    if !CyberwarePolicy.Safe(player) { return false; }
    let pools = GameInstance.GetStatPoolsSystem(player.GetGame());
    // Do not respec during Adrenaline; native rank-sale owner events still run.
    return pools.GetStatPoolValue(Cast<StatsObjectID>(player.GetEntityID()), gamedataStatPoolType.Overshield, false) <= 0.00;
  }
  private func OnAttach() -> Void {
    this.running = true;
    this.Restored();
  }
  private func OnDetach() -> Void {
    this.running = false; this.epoch += 1; this.queued = false;
    this.actor = null; this.mutation = 0;
  }
  public func Restored() -> Void {
    this.epoch += 1; this.queued = false; this.actor = null; this.mutation = 0;
    this.warmup = 4; this.readyTicks = 0; this.settleTicks = 0;
    if this.stage != 0 && this.schema != 1 { this.Fail("Unsupported saved migration schema; no replay."); }
    if this.stage == 4 { this.detail = "Previously completed; Measure() reads current HP/stamina without changing them."; }
    if this.stage == 5 { this.detail = "STOPPED in this save. No replay; consult the log or use the pre-test save."; }
    if this.inflight { this.Fail("Interrupted mutation journal. No replay or compensation; use the pre-test save."); }
    if this.running { this.Schedule(); }
  }
  private func Schedule() -> Void {
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(BodyTick.Create(this, this.epoch), 1.0, false);
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || this.epoch != epoch { return; }
    this.Schedule();
    if !this.enabled || this.stage == 5 || this.queued { return; }
    let player = GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(player) { return; }
    if this.actor != player {
      this.actor = player; this.warmup = 4; this.readyTicks = 0; this.settleTicks = 0;
    }
    if this.warmup > 0 { this.warmup -= 1; return; }
    if !BodyPolicy.BlockBody(player) { this.detail = "Inactive profile; refunded progression is not restored."; return; }
    if !BodyPolicy.Safe(player) {
      this.readyTicks = 0; this.settleTicks = 0;
      this.detail = "Waiting: close menus, holster, leave combat/scene/workspot; no Overshield."; return;
    }
    let request = new BodyStep();
    request.epoch = this.epoch; request.player = player;
    this.queued = true;
    this.QueueRequest(request);
  }
  private func OnBodyStep(request: ref<BodyStep>) -> Void {
    if request.epoch != this.epoch { return; }
    this.queued = false;
    if !this.running || this.stage == 5 || !this.enabled || this.actor != request.player { return; }
    let player = request.player;
    if GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() != player ||
      !BodyPolicy.BlockBody(player) || !BodyPolicy.Safe(player) { return; }
    let chrome = CyberwarePolicy.Get(this.GetGameInstance());
    if !IsDefined(chrome) || !chrome.PTFRR2Healthy() {
      this.Fail("Cyberware policy fault; Body transaction stopped."); return;
    }
    if !chrome.PTFRR2Ready(player) {
      this.readyTicks = 0; this.settleTicks = 0;
      this.detail = "Waiting for restricted cyberware removal and native equipment settling."; return;
    }
    let data = PlayerDevelopmentSystem.GetData(player);
    if !IsDefined(data) { this.Fail("Player development data unavailable."); return; }
    let current = data.PTFRR2Snapshot();
    if !current.valid || (this.stage != 4 && !BodyCatalogue.Valid()) { this.Fail("Unsupported progression ledger or modified Body catalogue."); return; }
    if this.relicEnabled && !RelicCatalogue.Valid() { this.Fail("Unsupported Relic catalogue; refund stopped."); return; }
    if this.stage == 4 {
      // A completed migration is never replayed, even if something else edits Body.
      if current.body != 3 || BodyPolicy.Total(current) != 0 || (this.relicEnabled && RelicCatalogue.Total(current) != 0) {
        this.Fail("Restricted attributes/perks changed after completion. Automatic repeat refund refused.");
      }
      return;
    }
    if this.stage == 1 {
      this.readyTicks += 1;
      if this.readyTicks < 3 { return; }
      if !data.PTFRR2CanResetBody() || !BodyPolicy.Headroom(current) { this.Fail("Body reset preflight failed: stored/live value, unit costs or attribute ledger."); return; }
      if this.relicEnabled && !RelicCatalogue.Headroom(current) { this.Fail("Relic point refund would overflow."); return; }
      this.expected = current;
      this.startingBody = current.body; this.startingRanks = BodyPolicy.Total(current);
      if this.relicEnabled { this.startingRelicRanks = RelicCatalogue.Total(current); }
      this.beforeVitals = this.Measure(); this.stage = 2;
      this.Note("Started: Body " + ToString(this.startingBody) + ", purchased Body ranks " + ToString(this.startingRanks) + ". " + this.beforeVitals);
      return;
    }
    if !BodyPolicy.Same(this.expected, current, -1, false) {
      this.Fail("Progression changed outside the expected step. No compensation or replay performed."); return;
    }
    if this.stage == 3 {
      if this.relicEnabled && RelicCatalogue.Total(current) > 0 { this.RefundRelicOne(player, data); return; }
      this.Settle(player); return;
    }
    if this.stage != 2 || this.inflight { this.Fail("Unexpected migration stage or outstanding mutation."); return; }
    if BodyPolicy.Total(current) > 0 { this.RefundOne(player, data); return; }
    this.ResetBody(player, data);
  }
  private func RefundOne(player: ref<PlayerPuppet>, data: ref<PlayerDevelopmentData>) -> Void {
    let types = BodyCatalogue.Types();
    let i = 0;
    while i < ArraySize(types) {
      let perk = types[i];
      let index = EnumInt(perk);
      if this.expected.perkRanks[index] > 0 && data.CheckIfAllnewPerkParentSold(perk) {
        let result = PlayerDevelopmentSystem.CanSellNewPerk(player, perk);
        if !result.success { this.Fail("Native perk refund admission refused."); return; }
        this.selected = perk; this.inflight = true; this.mutation = 1;
        // The native system method queues the normal owner/UI event synchronously.
        // No independently queued native mutation survives this journal step.
        let sold = PlayerDevelopmentSystem.GetInstance(player).PTFRR2SellBodyPerk(player, perk);
        this.mutation = 0;
        let after = data.PTFRR2Snapshot();
        if !sold || !BodyPolicy.Same(this.expected, after, index, false) {
          this.Fail("Perk rank/point/effect-path acknowledgement failed; no retry."); return;
        }
        this.expected = after; this.refundedRanks += 1; this.inflight = false;
        let notification = new SellNewPerk(); notification.Set(player, perk);
        UIInventoryScriptableSystem.GetInstance(player.GetGame()).QueueRequest(notification);
        data.PTFRR2PublishUI();
        this.Note("Refunded one " + EnumValueToString("gamedataNewPerkType", Cast<Int64>(index)) + " rank. Total " + ToString(this.refundedRanks) + "/" + ToString(this.startingRanks));
        return;
      }
      i += 1;
    }
    this.Fail("No ordinary dependency-safe Body refund available; force-selling refused.");
  }
  private func ResetBody(player: ref<PlayerPuppet>, data: ref<PlayerDevelopmentData>) -> Void {
    if !data.PTFRR2CanResetBody() { this.Fail("Body reset preflight no longer valid."); return; }
    let refund = this.expected.body - 3;
    this.inflight = true; this.mutation = 2;
    let reset = data.PTFRR2ResetBody();
    if reset { reset = data.PTFRR2RelockBody(); }
    this.mutation = 0;
    let after = data.PTFRR2Snapshot();
    if !reset || !BodyPolicy.Same(this.expected, after, -1, true) || BodyPolicy.Total(after) != 0 {
      this.Fail("Body reset/attribute accounting acknowledgement failed; no retry."); return;
    }
    this.expected = after; this.refundedAttributes += refund; this.inflight = false;
    this.stage = 3; this.settleTicks = 0;
    data.PTFRR2PublishUI();
    this.Note("Body is 3. Refunded attribute points: " + ToString(this.refundedAttributes) + ". Waiting for native HP/stamina maxima to settle.");
  }
  private func RefundRelicOne(player: ref<PlayerPuppet>, data: ref<PlayerDevelopmentData>) -> Void {
    if this.inflight || !this.relicEnabled || this.stage != 3 || !RelicCatalogue.Headroom(this.expected) {
      this.Fail("Invalid Relic refund stage, journal or point headroom."); return;
    }
    let types = RelicCatalogue.Types();
    let i = 0;
    while i < ArraySize(types) {
      let perk = types[i];
      let index = EnumInt(perk);
      if this.expected.perkRanks[index] > 0 && data.CheckIfAllnewPerkParentSold(perk) {
        let result = PlayerDevelopmentSystem.CanSellNewPerk(player, perk);
        if !result.success { this.Fail("Native Relic refund admission refused."); return; }
        let cost = RelicCatalogue.Cost(perk);
        this.selected = perk; this.inflight = true; this.mutation = 3;
        let sold = PlayerDevelopmentSystem.GetInstance(player).PTFRR2SellRelicPerk(player, perk);
        this.mutation = 0;
        let after = data.PTFRR2Snapshot();
        if !sold || !BodyPolicy.Same(this.expected, after, index, false, cost) {
          this.Fail("Relic rank/point acknowledgement failed; no retry."); return;
        }
        this.expected = after; this.refundedRelicRanks += 1; this.refundedRelicPoints += cost; this.inflight = false;
        this.settleTicks = 0;
        let notification = new SellNewPerk(); notification.Set(player, perk);
        UIInventoryScriptableSystem.GetInstance(player.GetGame()).QueueRequest(notification);
        data.PTFRR2PublishUI();
        this.Note("Refunded Relic perk " + EnumValueToString("gamedataNewPerkType", Cast<Int64>(index)) +
          ". Relic points returned: " + ToString(this.refundedRelicPoints));
        return;
      }
      i += 1;
    }
    this.Fail("No dependency-safe Relic refund available; force-selling refused.");
  }
  private func Settle(player: ref<PlayerPuppet>) -> Void {
    let id = Cast<StatsObjectID>(player.GetEntityID());
    let stats = GameInstance.GetStatsSystem(player.GetGame());
    let pools = GameInstance.GetStatPoolsSystem(player.GetGame());
    let hp = stats.GetStatValue(id, gamedataStatType.Health);
    let stamina = stats.GetStatValue(id, gamedataStatType.Stamina);
    let hpPool = pools.GetStatPoolMaxPointValue(id, gamedataStatPoolType.Health);
    let staminaPool = pools.GetStatPoolMaxPointValue(id, gamedataStatPoolType.Stamina);
    if !(hp > 0.00 && hp < 1000000.00 && stamina > 0.00 && stamina < 1000000.00 &&
      hpPool > 0.00 && hpPool < 1000000.00 && staminaPool > 0.00 && staminaPool < 1000000.00) {
      this.Fail("Invalid HP/stamina measurement; progression not reversed."); return;
    }
    if AbsF(hp - this.previousHealth) < 0.01 && AbsF(stamina - this.previousStamina) < 0.01 &&
      AbsF(hpPool - this.previousHealthPool) < 0.01 && AbsF(staminaPool - this.previousStaminaPool) < 0.01 {
      this.settleTicks += 1;
    } else { this.settleTicks = 0; }
    this.previousHealth = hp; this.previousStamina = stamina;
    this.previousHealthPool = hpPool; this.previousStaminaPool = staminaPool;
    if this.settleTicks < 4 { return; }
    this.afterVitals = this.Measure(); this.stage = 4;
    this.Note("COMPLETE. Native maxima stable for four samples; no direct HP/stamina override. " + this.afterVitals);
  }
  private func Fail(reason: String) -> Void {
    this.mutation = 0; this.stage = 5;
    this.Note("STOPPED: " + reason);
  }
  private func Note(message: String) -> Void {
    this.detail = message; this.audit += message + "\n";
    ModLog(n"PTFR_Restrictions_R2", message);
  }
  public func FullNerfWithoutVitals() -> String {
    return ProfilePolicy.Get(this.GetGameInstance()).FullNerfWithoutVitals();
  }
  public func PTFRR3Complete() -> Bool { return this.enabled && this.relicEnabled && this.stage == 4 && !this.inflight; }
  public func PTFRR3Faulted() -> Bool { return this.stage == 5 || this.inflight; }
  public func PTFRR3StartBodyRelic() -> String {
    if this.stage != 0 {
      if !this.relicEnabled { return this.IncludeRelic(); }
      return "Not replayed. " + this.GetStatus();
    }
    let game = this.GetGameInstance();
    if !CyberwarePolicy.Completed(game) { return "Refused: genuine completed Tower required; no story facts changed."; }
    let player = GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(player) || !BodyPolicy.Safe(player) { return "Refused: normal V in safe gameplay required. Close menus, holster and leave combat/scene/Overshield."; }
    let data = PlayerDevelopmentSystem.GetData(player);
    if !IsDefined(data) { return "Refused: progression not ready."; }
    let snapshot = data.PTFRR2Snapshot();
    if !snapshot.valid || !BodyCatalogue.Valid() || !data.PTFRR2CanResetBody() || !BodyPolicy.Headroom(snapshot) {
      return "Refused: unsupported Body catalogue, progression ledger, effective Body or purchase costs.";
    }
    if !RelicCatalogue.Valid() || !RelicCatalogue.Headroom(snapshot) { return "Refused: unsupported Relic catalogue or point headroom."; }
    let chrome = CyberwarePolicy.Get(game);
    if !IsDefined(chrome) || !chrome.PTFRR2Healthy() { return "Refused: resolve cyberware policy fault first."; }
    let chromeStatus = chrome.Enable();
    if !CyberwarePolicy.Active(player) { return "Refused: " + chromeStatus; }
    this.enabled = true; this.schema = 1; this.stage = 1; this.actor = player; this.relicEnabled = true;
    this.warmup = 4; this.readyTicks = 0;
    this.Note("Queued ONE-WAY Body 3 / Body and Relic perk refunds; cyberware policy enabled. Restricted perk purchases blocked; HP/stamina overrides OFF. Keep menus closed until COMPLETE.");
    return this.GetStatus();
  }
  public func IncludeRelic() -> String {
    if this.relicEnabled { return "Not replayed. " + this.GetStatus(); }
    if !this.enabled || this.schema != 1 || this.stage < 1 || this.stage > 4 || this.inflight {
      return "Refused: an active, non-faulted Body migration with no in-flight step is required.";
    }
    let game = this.GetGameInstance();
    let player = GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !CyberwarePolicy.Completed(game) || !BodyPolicy.BlockBody(player) || !BodyPolicy.Safe(player) {
      return "Refused: completed Tower, active Full Nerf and safe gameplay required.";
    }
    let chrome = CyberwarePolicy.Get(game);
    let data = PlayerDevelopmentSystem.GetData(player);
    if !IsDefined(chrome) || !chrome.PTFRR2Healthy() || !IsDefined(data) { return "Refused: policy or progression unavailable/faulted."; }
    let current = data.PTFRR2Snapshot();
    if !current.valid || !BodyCatalogue.Valid() || !RelicCatalogue.Valid() || !RelicCatalogue.Headroom(current) {
      return "Refused: unsupported progression, perk catalogue or Relic point headroom.";
    }
    if this.stage == 4 {
      if current.body != 3 || BodyPolicy.Total(current) != 0 { return "Refused: completed Body state changed; no repeat refund."; }
      // New Relic extension snapshots current legitimate non-Body progress;
      // it never re-enters Body refund/reset stages or zeroes old refund counts.
      this.expected = current; this.stage = 3;
    } else {
      if this.stage != 1 && !BodyPolicy.Same(this.expected, current, -1, false) { return "Refused: unfinished Body journal has external progression changes."; }
    }
    this.relicEnabled = true; this.startingRelicRanks = RelicCatalogue.Total(current);
    // Retire old queued ticks/steps before extending an existing journal.
    this.epoch += 1; this.queued = false;
    this.actor = player; this.warmup = 4; this.readyTicks = 0; this.settleTicks = 0;
    if this.running { this.Schedule(); }
    this.Note("Relic extension queued. Native Relic points will be refunded; purchases blocked while Full Nerf is active. Body refunds are not replayed.");
    return this.GetStatus();
  }
  public func Measure() -> String {
    return ProfilePolicy.Get(this.GetGameInstance()).Measure();
  }
  public func PTFRR3MeasureNative() -> String {
    let player = GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(player) || player.IsReplacer() { return "No normal player to measure."; }
    let id = Cast<StatsObjectID>(player.GetEntityID());
    let stats = GameInstance.GetStatsSystem(player.GetGame());
    let pools = GameInstance.GetStatPoolsSystem(player.GetGame());
    let data = PlayerDevelopmentSystem.GetData(player);
    if !IsDefined(data) { return "Progression not ready."; }
    let snapshot = data.PTFRR2Snapshot();
    return "Body=" + ToString(snapshot.body) + " HP=" + ToString(pools.GetStatPoolValue(id, gamedataStatPoolType.Health, false)) +
      "/" + ToString(pools.GetStatPoolMaxPointValue(id, gamedataStatPoolType.Health)) + " (max stat=" + ToString(stats.GetStatValue(id, gamedataStatType.Health)) +
      ") Stamina=" + ToString(pools.GetStatPoolValue(id, gamedataStatPoolType.Stamina, false)) + "/" +
      ToString(pools.GetStatPoolMaxPointValue(id, gamedataStatPoolType.Stamina)) + " (max stat=" + ToString(stats.GetStatValue(id, gamedataStatType.Stamina)) +
      ") Attribute unspent=" + ToString(snapshot.attributeUnspent) + " Perk unspent=" + ToString(snapshot.primaryUnspent) +
      " Relic unspent=" + ToString(snapshot.relicUnspent);
  }
  public func GetStatus() -> String {
    let player = GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
    return "Full Nerf R2 stage=" + ToString(this.stage) + " enabled=" + ToString(this.enabled) + " active=" + ToString(BodyPolicy.BlockBody(player)) + " inflight=" + ToString(this.inflight) +
      " Body perk ranks refunded=" + ToString(this.refundedRanks) + " Attribute points refunded=" + ToString(this.refundedAttributes) +
      " Relic enabled=" + ToString(this.relicEnabled) + " Relic perks refunded=" + ToString(this.refundedRelicRanks) +
      "/" + ToString(this.startingRelicRanks) + " Relic points refunded=" + ToString(this.refundedRelicPoints) +
      " | " + this.detail;
  }
  public func GetAudit() -> String { return this.audit; }
  public static func Headroom(snapshot: BodySnapshot) -> Bool {
    // Bounded stock maximum refunds (41 ranks, 17 attributes) cannot overflow.
    return snapshot.valid && snapshot.primaryUnspent <= 2147483606 && snapshot.attributeUnspent <= 2147483630;
  }
  public static func Total(snapshot: BodySnapshot) -> Int32 {
    let types = BodyCatalogue.Types();
    let total = 0;
    let i = 0;
    while i < ArraySize(types) { total += snapshot.perkRanks[EnumInt(types[i])]; i += 1; }
    return total;
  }
  // Compare the entire persistent progression view, allowing ONLY the one native
  // refund delta. Modern Primary.spent intentionally does not decrease on sale.
  public static func Same(a: BodySnapshot, b: BodySnapshot, soldIndex: Int32, reset: Bool, opt relicCost: Int32) -> Bool {
    if !a.valid || !b.valid { return false; }
    if relicCost != 0 && (reset || soldIndex < 0 || soldIndex >= EnumInt(gamedataNewPerkType.Count) ||
      RelicCatalogue.Cost(IntEnum<gamedataNewPerkType>(soldIndex)) != relicCost) { return false; }
    let attributeDelta = reset ? a.body - 3 : 0;
    let rankDelta = soldIndex >= 0 ? 1 : 0;
    let primaryDelta = relicCost == 0 ? rankDelta : 0;
    if b.body != a.body - attributeDelta || AbsF(b.liveBody - Cast<Float>(b.body)) > 0.01 ||
      b.attributeUnspent != a.attributeUnspent + attributeDelta || b.attributeSpent != a.attributeSpent - attributeDelta ||
      b.primaryUnspent != a.primaryUnspent + primaryDelta || b.primarySpent != a.primarySpent ||
      b.relicUnspent != a.relicUnspent + relicCost || b.relicSpent != a.relicSpent { return false; }
    if ArraySize(a.attributes) != ArraySize(b.attributes) || ArraySize(a.devPoints) != ArraySize(b.devPoints) ||
      ArraySize(a.perkRanks) != ArraySize(b.perkRanks) || ArraySize(a.profTypes) != ArraySize(b.profTypes) ||
      ArraySize(a.legacyPerkTypes) != ArraySize(b.legacyPerkTypes) { return false; }
    if ArraySize(a.perkRanks) != EnumInt(gamedataNewPerkType.Count) ||
      ArraySize(a.profTypes) != ArraySize(a.profLevels) || ArraySize(a.profTypes) != ArraySize(a.profXP) || ArraySize(a.profTypes) != ArraySize(a.profSpent) ||
      ArraySize(b.profTypes) != ArraySize(b.profLevels) || ArraySize(b.profTypes) != ArraySize(b.profXP) || ArraySize(b.profTypes) != ArraySize(b.profSpent) ||
      ArraySize(a.legacyPerkTypes) != ArraySize(a.legacyPerkRanks) || ArraySize(b.legacyPerkTypes) != ArraySize(b.legacyPerkRanks) { return false; }
    let i = 0;
    while i < ArraySize(a.attributes) {
      let delta = Equals(a.attributes[i].attributeName, gamedataStatType.Strength) ? attributeDelta : 0;
      if NotEquals(a.attributes[i].attributeName, b.attributes[i].attributeName) || a.attributes[i].id != b.attributes[i].id ||
        b.attributes[i].value != a.attributes[i].value - delta { return false; }
      i += 1;
    }
    i = 0;
    while i < ArraySize(a.devPoints) {
      let unspent = a.devPoints[i].unspent;
      let spent = a.devPoints[i].spent;
      if Equals(a.devPoints[i].type, gamedataDevelopmentPointType.Primary) { unspent += primaryDelta; }
      if Equals(a.devPoints[i].type, gamedataDevelopmentPointType.Espionage) { unspent += relicCost; }
      if Equals(a.devPoints[i].type, gamedataDevelopmentPointType.Attribute) { unspent += attributeDelta; spent -= attributeDelta; }
      if NotEquals(a.devPoints[i].type, b.devPoints[i].type) || b.devPoints[i].unspent != unspent || b.devPoints[i].spent != spent { return false; }
      i += 1;
    }
    i = 0;
    while i < ArraySize(a.perkRanks) {
      if b.perkRanks[i] != a.perkRanks[i] - (i == soldIndex ? 1 : 0) { return false; }
      i += 1;
    }
    i = 0;
    while i < ArraySize(a.profTypes) {
      if a.profTypes[i] != b.profTypes[i] || a.profLevels[i] != b.profLevels[i] ||
        a.profXP[i] != b.profXP[i] || a.profSpent[i] != b.profSpent[i] { return false; }
      i += 1;
    }
    i = 0;
    while i < ArraySize(a.legacyPerkTypes) {
      if a.legacyPerkTypes[i] != b.legacyPerkTypes[i] || a.legacyPerkRanks[i] != b.legacyPerkRanks[i] { return false; }
      i += 1;
    }
    return true;
  }
}

public class BodyStep extends ScriptableSystemRequest {
  public let epoch: Int32;
  public let player: wref<PlayerPuppet>;
}
public class BodyTick extends DelayCallback {
  private let policy: wref<BodyPolicy>;
  private let epoch: Int32;
  public static func Create(policy: ref<BodyPolicy>, epoch: Int32) -> ref<BodyTick> {
    let tick = new BodyTick(); tick.policy = policy; tick.epoch = epoch; return tick;
  }
  public func Call() -> Void { if IsDefined(this.policy) { this.policy.Poll(this.epoch); } }
}
