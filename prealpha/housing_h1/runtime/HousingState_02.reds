module PTFR.Housing

import PTFR.RestrictionsR3.*
import PTFR.RestorationBaseline.*

// Public beta save contract v1. Keep these class and field names/types forever.
// New stable-release fields must be additive and inert by default.
public class HousingRecord extends IScriptable {
  public persistent let id: CName;
  public persistent let lossApplied: Bool;
  // 0 unpaid, 1 debit pending, 2 paid, 3 native access acknowledged, 4 uncertain.
  public persistent let purchaseState: Int32;
  public persistent let debitAttempts: Int32;
  public persistent let quotedPrice: Int32;
  public persistent let balanceBefore: Int32;
  public persistent let balanceAfter: Int32;
  public persistent let debitReturned: Bool;
  public persistent let sourceDoor: EntityID;
  // Observed native history, not a manufactured ownership or completion proof.
  public persistent let preTowerFact: Int32;
  public persistent let captureKnown: Bool;
}

public class HousingState extends ScriptableSystem {
  private persistent let schemaVersion: Int32;
  private persistent let migrationRevision: Int32;
  private persistent let records: array<ref<HousingRecord>>;
  private persistent let activated: Bool;
  private persistent let captureReady: Bool;
  private persistent let captureFrozen: Bool;
  // 0 not activated, 1 actual pre-Tower observation, 2 late import/unknown history.
  private persistent let origin: Int32;
  private persistent let fault: CName;
  private let running: Bool;
  private let epoch: Int32;
  private let inCall: Bool;
  private let previousFacts: array<Int32>;
  private let previousValid: Bool;
  private let lastCapture: Float;
  private let registered: Bool;
  private let listeners: array<Uint32>;
  private let detail: String;

  public static func Get(game: GameInstance) -> ref<HousingState> {
    return GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.Housing.HousingState") as HousingState;
  }
  private func Fact(name: String) -> Int32 {
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    return IsDefined(qs) ? qs.GetFactStr(name) : -2147483647;
  }
  private func SetOwn(name: String, value: Int32) -> Void {
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if IsDefined(qs) && qs.GetFactStr(name) != value { qs.SetFactStr(name, value); }
  }
  private func Own(id: String, suffix: String) -> Int32 { return this.Fact("PTFRH1_" + id + "_" + suffix); }
  private func Now() -> Float { return EngineTime.ToFloat(GameInstance.GetSimTime(this.GetGameInstance())); }
  private func BeforeTower() -> Bool {
    // Match PA1's actual cutoff. q307 may be active while ordinary ownership can still change.
    return this.Fact("PostTowerFreeRoamActive") == 0 &&
      this.Fact("q307_done") == 0 && this.Fact("q307_finished") == 0 && this.Fact("q307_2079") == 0 &&
      this.Fact("q307_main_game_killed") == 0 && this.Fact("q307_ep1_killed") == 0 && this.Fact("q307_debug_reset") == 0 &&
      this.Fact("q307_point_of_no_return") == 0 && this.Fact("q115_point_of_no_return") == 0;
  }
  private func BoundaryNow() -> Bool {
    return this.Fact("q115_point_of_no_return") > 0 || this.Fact("q307_point_of_no_return") > 0 ||
      this.Fact("q307_2079") > 0 || this.Fact("q307_main_game_killed") > 0 || this.Fact("q307_ep1_killed") > 0 ||
      this.Fact("q307_done") > 0 || this.Fact("q307_finished") > 0 || this.Fact("PostTowerFreeRoamActive") > 0;
  }
  private func TeardownNow() -> Bool {
    return this.Fact("q307_2079") > 0 || this.Fact("q307_main_game_killed") > 0 || this.Fact("q307_ep1_killed") > 0 ||
      this.Fact("q307_done") > 0 || this.Fact("q307_finished") > 0 || this.Fact("PostTowerFreeRoamActive") > 0;
  }
  private func Register() -> Void {
    if this.registered { return; }
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if !IsDefined(qs) { return; }
    ArrayPush(this.listeners, qs.RegisterListener(n"q115_point_of_no_return", this, n"OnBoundary"));
    ArrayPush(this.listeners, qs.RegisterListener(n"q307_point_of_no_return", this, n"OnBoundary"));
    this.registered = true;
  }
  private func Unregister() -> Void {
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if this.registered && IsDefined(qs) && ArraySize(this.listeners) == 2 {
      qs.UnregisterListener(n"q115_point_of_no_return", this.listeners[0]);
      qs.UnregisterListener(n"q307_point_of_no_return", this.listeners[1]);
    }
    ArrayClear(this.listeners); this.registered = false;
  }
  protected cb func OnBoundary(value: Int32) -> Bool {
    if value > 0 && this.Valid() { this.FreezeCapture(true); }
    return false;
  }
  private func FreezeCapture(observedBoundary: Bool) -> Void {
    if this.captureFrozen || this.activated { return; }
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    let age = this.Now() - this.lastCapture;
    let known = observedBoundary && this.captureReady && this.previousValid && age >= 0.0 && age <= 2.5 &&
      !this.TeardownNow() && this.Fact("q307_debug_reset") == 0 && IsDefined(jm);
    if known { known = !jm.HasAnyDelayedStateChanges(); }
    let i = 0;
    while i < HousingData.Count() {
      if !this.records[i].captureKnown || this.records[i].preTowerFact != this.Fact(HousingData.HistoryFact(i)) { known = false; }
      i += 1;
    }
    if known { known = !jm.HasAnyDelayedStateChanges() && !this.TeardownNow(); }
    this.captureReady = known; this.captureFrozen = true;
    i = 0;
    while i < HousingData.Count() { this.records[i].captureKnown = known; i += 1; }
    this.previousValid = false;
  }
  private func Tower() -> Bool {
    return this.Fact("PostTowerFreeRoamActive") == 1 && this.Fact("PTFRP0_DR13") == 1 &&
      this.Fact("q307_done") == 1 && this.Fact("q307_finished") == 1 && this.Fact("q307_2079") == 1 &&
      this.Fact("q307_main_game_killed") == 1 && this.Fact("q307_ep1_killed") == 1 &&
      this.Fact("q307_active") == 0 && this.Fact("q307_debug_reset") == 0;
  }
  private func Record(id: String) -> ref<HousingRecord> {
    let i = HousingData.Index(id);
    if i < 0 || i >= ArraySize(this.records) { return null; }
    let record = this.records[i];
    return IsDefined(record) && Equals(record.id, StringToName(id)) ? record : null;
  }
  private func RecordValid(record: ref<HousingRecord>) -> Bool {
    if !IsDefined(record) || HousingData.Index(NameToString(record.id)) < 0 || record.purchaseState < 0 || record.purchaseState > 4 { return false; }
    if record.preTowerFact < -1 || record.preTowerFact > 1 || (record.captureKnown && record.preTowerFact < 0) { return false; }
    if record.purchaseState == 0 {
      return record.debitAttempts == 0 && record.quotedPrice == 0 && record.balanceBefore == 0 && record.balanceAfter == 0 && !record.debitReturned && !EntityID.IsDefined(record.sourceDoor);
    }
    if !record.lossApplied || record.debitAttempts != 1 || record.quotedPrice <= 0 || record.balanceBefore < record.quotedPrice ||
      record.balanceAfter < -1 || !EntityID.IsDefined(record.sourceDoor) { return false; }
    if record.purchaseState == 2 || record.purchaseState == 3 {
      return record.debitReturned && record.balanceAfter == record.balanceBefore - record.quotedPrice;
    }
    return true;
  }
  private func Valid() -> Bool {
    if this.schemaVersion != 1 || this.migrationRevision != 1 || ArraySize(this.records) != HousingData.Count() ||
      this.origin < 0 || this.origin > 2 || (this.activated && (!this.captureFrozen || this.origin == 0)) { return false; }
    if this.activated && ((this.origin == 1) != this.captureReady) { return false; }
    let i = 0;
    while i < HousingData.Count() {
      if !this.RecordValid(this.Record(HousingData.ID(i))) || (this.captureFrozen && this.captureReady && !this.records[i].captureKnown)) { return false; }
      i += 1;
    }
    return true;
  }
  private func Initialize() -> Bool {
    if this.schemaVersion != 0 { return this.Valid(); }
    if ArraySize(this.records) != 0 || this.activated || this.captureReady || this.captureFrozen || this.origin != 0 ||
      this.migrationRevision != 0 || this.Fact("PTFRH1_Ready") != 0 || this.Fact("PTFRH1_Revision") != 0 || this.Fact("PTFRH1_Fault") != 0 { return false; }
    let i = 0;
    while i < HousingData.Count() {
      let id = HousingData.ID(i);
      if this.Own(id, "Entitled") != 0 || this.Own(id, "LossPermit") != 0 || this.Own(id, "AccessPermit") != 0 ||
        this.Own(id, "LossApplied") != 0 || this.Own(id, "AccessApplied") != 0 { return false; }
      i += 1;
    }
    i = 0;
    while i < HousingData.Count() {
      let record = new HousingRecord(); record.id = StringToName(HousingData.ID(i)); record.preTowerFact = -1;
      ArrayPush(this.records, record); i += 1;
    }
    this.schemaVersion = 1; this.migrationRevision = 1;
    return this.Valid();
  }
  private func ObserveHistory() -> Void {
    if !this.activated && this.captureFrozen && this.BeforeTower() {
      // Returning to ordinary pre-ending play invalidates the old boundary witness.
      this.captureFrozen = false; this.captureReady = false; this.previousValid = false; this.lastCapture = -100.0;
      let k = 0;
      while k < HousingData.Count() { this.records[k].captureKnown = false; k += 1; }
    }
    if this.captureFrozen || this.activated { return; }
    if this.BoundaryNow() { this.FreezeCapture(false); return; }
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    if !IsDefined(jm) || jm.HasAnyDelayedStateChanges() || !this.BeforeTower() { this.previousValid = false; return; }
    let values: array<Int32>; let i = 0;
    while i < HousingData.Count() {
      let value = this.Fact(HousingData.HistoryFact(i));
      if value < 0 || value > 1 { this.previousValid = false; return; }
      ArrayPush(values, value); i += 1;
    }
    if jm.HasAnyDelayedStateChanges() || !this.BeforeTower() { this.previousValid = false; return; }
    let same = this.previousValid && ArraySize(this.previousFacts) == ArraySize(values);
    i = 0;
    while i < ArraySize(values) {
      if same && this.previousFacts[i] != values[i] { same = false; }
      i += 1;
    }
    if same {
      i = 0;
      while i < HousingData.Count() { this.records[i].preTowerFact = values[i]; this.records[i].captureKnown = true; i += 1; }
      this.captureReady = true;
      this.lastCapture = this.Now();
    }
    this.previousFacts = values; this.previousValid = true;
  }
  private func H10Quiet() -> Bool {
    return this.Fact("PTFRB0H10P_Active") == 0 && this.Fact("PTFRB0H10M_Active") == 0 &&
      this.Fact("PTFRB0H10I_M_Active") == 0 && this.Fact("PTFRB0H10I_H_Active") == 0 &&
      this.Fact("PTFRB0H10I_B_Active") == 0 && this.Fact("PTFRB0H10I_S_Active") == 0 && this.Fact("PTFRB0H10I_W_Active") == 0;
  }
  private func Player() -> ref<PlayerPuppet> {
    let players = GameInstance.GetPlayerSystem(this.GetGameInstance());
    return IsDefined(players) ? players.GetLocalPlayerMainGameObject() as PlayerPuppet : null;
  }
  private func SafeActor(player: ref<PlayerPuppet>) -> Bool {
    if !IsDefined(player) || player.IsDead() || player.IsReplacer() || player.IsInCombat() { return false; }
    let game = this.GetGameInstance(); let players = GameInstance.GetPlayerSystem(game);
    if !IsDefined(players) || players.GetLocalPlayerMainGameObject() != player || players.GetLocalPlayerControlledGameObject() != player || players.IsInFreeCamera() { return false; }
    let sceneSystem = GameInstance.GetSceneSystem(game);
    if !IsDefined(sceneSystem) { return false; }
    let scenes = sceneSystem.GetScriptInterface(); let bb = player.GetPlayerStateMachineBlackboard();
    let workspots = GameInstance.GetWorkspotSystem(game); let mounts = GameInstance.GetMountingFacility(game);
    let bd = GameInstance.GetScriptableSystemsContainer(game).Get(n"BraindanceSystem") as BraindanceSystem;
    if !IsDefined(scenes) || !IsDefined(bb) || !IsDefined(workspots) || !IsDefined(mounts) || !IsDefined(bd) { return false; }
    if bb.GetInt(GetAllBlackboardDefs().PlayerStateMachine.HighLevel) != 1 || bb.GetInt(GetAllBlackboardDefs().PlayerStateMachine.SceneTier) != 1 ||
      scenes.IsEntityInScene(player.GetEntityID()) || scenes.IsEntityInDialogue(player.GetEntityID()) || scenes.IsRewindableSectionActive() ||
      workspots.IsActorInWorkspot(player) || bd.GetIsInBraindance() { return false; }
    let mount = mounts.GetMountingInfoSingleWithObjects(player);
    return !EntityID.IsDefined(mount.parentId);
  }
  private func ProfileReady() -> Bool {
    let profile = ProfilePolicy.Get(this.GetGameInstance());
    return IsDefined(profile) && profile.PTFRPAComplete() && !profile.PTFRPAFaulted();
  }
  private func MigrationContext() -> Bool {
    if !this.Tower() || !this.ProfileReady() || this.Fact("PTFRPA2_Started") != 1 || this.Fact("PTFRPA2_Teleported") != 1 ||
      this.Fact("PTFRPA2_ControlReady") != 1 || this.Fact("PTFRPA2_Fault") != 0 || !this.H10Quiet() || !this.SafeActor(this.Player()) { return false; }
    let ui = GameInstance.GetBlackboardSystem(this.GetGameInstance()).Get(GetAllBlackboardDefs().UI_System);
    if !IsDefined(ui) || ui.GetBool(GetAllBlackboardDefs().UI_System.IsInMenu) { return false; }
    let baseline = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.RestorationBaseline.RestorationBaseline") as RestorationBaseline;
    return IsDefined(baseline) && baseline.H10GeometryReady();
  }
  private func Reconcile() -> Void {
    if !IsDefined(GameInstance.GetQuestsSystem(this.GetGameInstance())) { return; }
    let i = 0;
    while i < HousingData.Count() {
      let record = this.records[i];
      // A saved in-flight debit is never inferred from current money or replayed.
      if record.purchaseState == 1 { record.purchaseState = 4; }
      let loss = this.Own(NameToString(record.id), "LossApplied"); let access = this.Own(NameToString(record.id), "AccessApplied");
      if loss < 0 || loss > 1 || access < 0 || access > 1 { this.fault = n"native_ack_out_of_range"; return; }
      if loss == 1 {
        if !this.activated { this.fault = n"loss_ack_before_activation"; return; }
        record.lossApplied = true;
      }
      if access == 1 {
        if record.purchaseState != 2 && record.purchaseState != 3 { this.fault = n"access_ack_without_receipt"; return; }
        record.purchaseState = 3;
      }
      i += 1;
    }
  }
  private func Publish() -> Void {
    if !this.activated || !this.Valid() { return; }
    let healthy = Equals(this.fault, n""); let migration = healthy && this.MigrationContext(); let i = 0;
    this.SetOwn("PTFRH1_Revision", 1);
    while i < HousingData.Count() {
      let record = this.records[i]; let entitled = record.purchaseState == 2 || record.purchaseState == 3;
      this.SetOwn("PTFRH1_" + NameToString(record.id) + "_Entitled", entitled ? 1 : 0);
      this.SetOwn("PTFRH1_" + NameToString(record.id) + "_LossPermit", migration && !record.lossApplied && record.purchaseState == 0 ? 1 : 0);
      this.SetOwn("PTFRH1_" + NameToString(record.id) + "_AccessPermit", healthy && record.purchaseState == 2 && record.lossApplied ? 1 : 0);
      i += 1;
    }
    this.SetOwn("PTFRH1_Fault", healthy ? 0 : 1);
    this.SetOwn("PTFRH1_Ready", 1);
  }
  private func Quarantine() -> Void {
    // Preserve receipts and published access. Stop known pending operations only.
    let i = 0;
    while i < HousingData.Count() {
      let id = HousingData.ID(i);
      this.SetOwn("PTFRH1_" + id + "_LossPermit", 0);
      this.SetOwn("PTFRH1_" + id + "_AccessPermit", 0);
      this.SetOwn("PTFRH1_" + id + "_PurchaseReady", 0);
      i += 1;
    }
    this.SetOwn("PTFRH1_Fault", 1);
  }
  public func Enforcing() -> Bool { return this.Tower() && (this.activated || this.Fact("PTFRH1_Ready") == 1); }
  public func Entitled(id: String) -> Bool {
    if this.schemaVersion > 1 && HousingData.Index(id) >= 0 {
      return this.Fact("PTFRH1_Ready") == 1 && this.Own(id, "Entitled") == 1;
    }
    let record = this.Record(id);
    return this.schemaVersion == 1 && this.activated && this.RecordValid(record) && (record.purchaseState == 2 || record.purchaseState == 3);
  }
  public func HousingReadyForReveal() -> Bool {
    if !this.Valid() || !this.activated || !this.Tower() || !this.ProfileReady() || NotEquals(this.fault, n"") || this.Fact("PTFRH1_Ready") != 1 || this.Fact("PTFRH1_Fault") != 0 { return false; }
    if this.Fact("PTFRH1_RelationshipsApplied") != 1 { return false; }
    let i = 0;
    while i < HousingData.Count() {
      if !this.records[i].lossApplied || this.Own(NameToString(this.records[i].id), "LossApplied") != 1 { return false; }
      i += 1;
    }
    return true;
  }
  public func CanPurchase(id: String, player: ref<PlayerPuppet>) -> Bool {
    let record = this.Record(id);
    return !this.inCall && this.HousingReadyForReveal() && this.Fact("PTFRPA2_Finished") == 1 && this.SafeActor(player) &&
      this.RecordValid(record) && record.lossApplied && record.purchaseState == 0 && record.debitAttempts == 0 && this.Own(id, "AccessApplied") == 0 &&
      (Equals(id, "h10") || this.Fact("q101_done") >= 1);
  }
  public func Purchase(id: String, expectedPrice: Int32, sourceDoor: EntityID) -> Bool {
    let game = this.GetGameInstance(); let player = this.Player();
    if !this.CanPurchase(id, player) || !HousingPurchaseLocation.Validate(game, id, sourceDoor) { return false; }
    let price = HousingPrice.Quote(game, id);
    if price <= 0 || price != expectedPrice { this.detail = "Quote changed or unavailable; no payment."; return false; }
    let transaction = GameInstance.GetTransactionSystem(game);
    if !IsDefined(transaction) { return false; }
    let before = transaction.GetItemQuantity(player, MarketSystem.Money());
    if before < price || !this.CanPurchase(id, player) || !HousingPurchaseLocation.Validate(game, id, sourceDoor) || HousingPrice.Quote(game, id) != price { return false; }
    let record = this.Record(id);
    this.inCall = true;
    record.quotedPrice = price; record.balanceBefore = before; record.balanceAfter = -1; record.sourceDoor = sourceDoor;
    record.debitAttempts = 1; record.purchaseState = 1;
    // The only currency write in H1. Never called by Poll, attach, reload or migration.
    record.debitReturned = transaction.RemoveItem(player, MarketSystem.Money(), price);
    record.balanceAfter = transaction.GetItemQuantity(player, MarketSystem.Money());
    if record.debitReturned && record.balanceAfter == before - price {
      record.purchaseState = 2; this.detail = "Payment recorded; native access pending.";
    } else {
      record.purchaseState = 4; this.detail = "Payment result uncertain; no retry, refund or access grant was inferred.";
    }
    this.inCall = false;
    this.Publish();
    return record.purchaseState == 2;
  }
  private func OnAttach() -> Void { this.running = true; this.Restored(); }
  private func OnDetach() -> Void { this.Unregister(); this.running = false; this.epoch += 1; this.previousValid = false; }
  public func Restored() -> Void {
    HousingPurchaseUI.Reset(this.GetGameInstance());
    this.Unregister(); this.epoch += 1; this.inCall = false; this.previousValid = false; this.lastCapture = -100.0; ArrayClear(this.previousFacts);
    if !this.Initialize() { this.Quarantine(); this.detail = "Unsupported or inconsistent saved housing schema; retained without migration."; }
    else {
      if this.BoundaryNow() && !this.captureFrozen { this.FreezeCapture(false); }
      this.Reconcile(); this.Publish();
    }
    this.Register();
    if this.running { this.Schedule(); }
  }
  private func Schedule() -> Void {
    let delay = GameInstance.GetDelaySystem(this.GetGameInstance());
    if IsDefined(delay) { delay.DelayCallback(HousingTick.Create(this, this.epoch), 1.0, false); }
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    this.Schedule();
    if this.inCall { return; }
    if !this.Initialize() { this.Quarantine(); return; }
    this.Register();
    this.ObserveHistory();
    if !this.activated && this.MigrationContext() {
      if !this.captureFrozen { this.FreezeCapture(false); }
      this.origin = this.captureReady ? 1 : 2; this.activated = true;
    }
    this.Reconcile(); this.Publish();
    if this.HousingReadyForReveal() { HousingPurchaseUI.Tick(this.GetGameInstance()); }
  }
  public func Inspect(id: String) -> String {
    let record = this.Record(id);
    if !IsDefined(record) { return "Housing: unknown property or unavailable schema; no changes."; }
    return "Housing " + id + ": schema=" + ToString(this.schemaVersion) + " origin=" + ToString(this.origin) +
      " lossApplied=" + ToString(record.lossApplied) + " purchaseState=" + ToString(record.purchaseState) +
      " attempts=" + ToString(record.debitAttempts) + " price=" + ToString(record.quotedPrice) +
      " entitlement=" + ToString(this.Entitled(id)) + " fault=" + ToString(this.fault) + " | " + this.detail;
  }
}

public abstract class HousingData {
  public static func Count() -> Int32 { return 5; }
  public static func ID(i: Int32) -> String {
    if i == 0 { return "h10"; } if i == 1 { return "northside"; } if i == 2 { return "japantown"; }
    if i == 3 { return "glen"; } if i == 4 { return "corpo"; } return "";
  }
  public static func Index(id: String) -> Int32 {
    let i = 0; while i < HousingData.Count() { if Equals(HousingData.ID(i), id) { return i; }; i += 1; } return -1;
  }
  public static func HistoryFact(i: Int32) -> String {
    if i == 0 { return "apartment_on"; } if i == 1 { return "dlc6_apart_wat_nid_purchased"; }
    if i == 2 { return "dlc6_apart_wbr_jpn_purchased"; } if i == 3 { return "dlc6_apart_hey_gle_purchased"; }
    if i == 4 { return "dlc6_apart_cct_dtn_purchased"; } return "";
  }
}

public class HousingTick extends DelayCallback {
  private let owner: wref<HousingState>; private let epoch: Int32;
  public static func Create(owner: ref<HousingState>, epoch: Int32) -> ref<HousingTick> {
    let tick = new HousingTick(); tick.owner = owner; tick.epoch = epoch; return tick;
  }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}

@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void {
  wrappedMethod(gameInstance);
  let housing = HousingState.Get(gameInstance); if IsDefined(housing) { housing.Restored(); }
}
