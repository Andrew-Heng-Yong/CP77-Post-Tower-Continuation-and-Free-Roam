module PTFR.Housing

import Codeware.UI.*

// Quote the same EconomicAssignment and challenge used by each native purchase.
// Missing records/systems never fall back to a guessed price.
public abstract class HousingPrice {
  public static func Quote(game: GameInstance, id: String) -> Int32 {
    let players = GameInstance.GetPlayerSystem(game);
    if !IsDefined(players) { return -1; }
    let player = players.GetLocalPlayerMainGameObject() as PlayerPuppet;
    if !IsDefined(player) || player.IsReplacer() { return -1; }
    if Equals(id, "h10") { return 25000; }
    let assignment: TweakDBID;
    switch id {
      case "northside": assignment = t"EconomicAssignment.vs_apartment_dlc6_apart_wat_nid"; break;
      case "japantown": assignment = t"EconomicAssignment.vs_apartment_dlc6_apart_wbr_jpn"; break;
      case "glen": assignment = t"EconomicAssignment.vs_apartment_dlc6_apart_hey_gle"; break;
      case "corpo": assignment = t"EconomicAssignment.vs_apartment_dlc6_apart_cct_dtn"; break;
      default: return -1;
    }
    let record = TweakDBInterface.GetContentAssignmentRecord(assignment);
    if !IsDefined(record) || !IsDefined(GameInstance.GetStatsDataSystem(game)) || !IsDefined(GameInstance.GetTransactionSystem(game)) { return -1; }
    let quote = RPGManager.GetBluelinePaymentValue(player, record, EGameplayChallengeLevel.NONE);
    if quote <= 0 { return -1; }
    return quote;
  }

  public static func Label(id: String) -> String {
    switch id {
      case "h10": return "Megabuilding H10 apartment";
      case "northside": return "Northside apartment";
      case "japantown": return "Japantown apartment";
      case "glen": return "The Glen apartment";
      case "corpo": return "Corpo Plaza apartment";
    }
    return "Apartment";
  }
}

public abstract class HousingPurchaseLocation {
  public static func Path(id: String) -> String {
@@LOCATION_PATHS@@
    return "";
  }

  public static func Source(id: String) -> EntityID {
    let path = HousingPurchaseLocation.Path(id);
    if Equals(path, "") { return new EntityID(); }
    return Cast<EntityID>(ResolveNodeRef(CreateNodeRef(path), Cast<GlobalNodeRef>(GlobalNodeID.GetRoot())));
  }

  public static func Offset(id: String) -> Vector4 {
@@LOCATION_OFFSETS@@
    return new Vector4(0.0, 0.0, 0.0, 1.0);
  }

  // The four DLC6 sources are scene markers, not falsely claimed device entities.
  // A successful native transform query is required at the exact authored choice.
  public static func Validate(game: GameInstance, id: String, sourceDoor: EntityID) -> Bool {
    let players = GameInstance.GetPlayerSystem(game);
    if !IsDefined(players) { return false; }
    let player = players.GetLocalPlayerMainGameObject() as PlayerPuppet;
    let expected = HousingPurchaseLocation.Source(id);
    if !IsDefined(player) || player.IsReplacer() || !EntityID.IsDefined(expected) || expected != sourceDoor { return false; }
    let position: Vector4;
    if Equals(id, "h10") {
      let door = GameInstance.FindEntityByID(game, expected) as Door;
      if !IsDefined(door) { return false; }
      position = door.GetWorldPosition();
    } else {
      let transform: Transform;
      let globalRef = ResolveNodeRef(CreateNodeRef(HousingPurchaseLocation.Path(id)), Cast<GlobalNodeRef>(GlobalNodeID.GetRoot()));
      if !GameInstance.GetNodeTransform(game, globalRef, transform) { return false; }
      position = Transform.TransformPoint(transform, HousingPurchaseLocation.Offset(id));
    }
    return Vector4.Distance(player.GetWorldPosition(), position) <= 3.50;
  }
}

public class HousingPurchaseUI extends ScriptableSystem {
  private let m_popup: ref<HousingPurchasePopup>;

  public static func Get(game: GameInstance) -> ref<HousingPurchaseUI> {
    return GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.Housing.HousingPurchaseUI") as HousingPurchaseUI;
  }

  public static func Reset(game: GameInstance) -> Void {
    let self = HousingPurchaseUI.Get(game);
    if IsDefined(self) { self.m_popup = null; }
  }

  private func OnAttach() -> Void { this.m_popup = null; }
  private func OnDetach() -> Void { this.m_popup = null; }

  public func IsCurrent(popup: ref<HousingPurchasePopup>) -> Bool {
    return IsDefined(this.m_popup) && this.m_popup == popup;
  }

  public static func Tick(game: GameInstance) -> Void {
    let self = HousingPurchaseUI.Get(game);
    let state = HousingState.Get(game);
    let quests = GameInstance.GetQuestsSystem(game);
    let player = GetPlayer(game) as PlayerPuppet;
    if !IsDefined(self) || !IsDefined(state) || !IsDefined(quests) || !IsDefined(player) { return; }
    let ids: array<String>;
    ArrayPush(ids, "northside"); ArrayPush(ids, "japantown"); ArrayPush(ids, "glen"); ArrayPush(ids, "corpo");
    let i = 0;
    while i < ArraySize(ids) {
      let id = ids[i];
      let request = StringToName("PTFRH1_" + id + "_PurchaseRequest");
      let ready = StringToName("PTFRH1_" + id + "_PurchaseReady");
      let canOffer = !IsDefined(self.m_popup) && state.CanPurchase(id, player);
      let readyValue = 0;
      if canOffer { readyValue = 1; }
      if quests.GetFact(ready) != readyValue { quests.SetFact(ready, readyValue); }
      if quests.GetFact(request) == 1 && !IsDefined(self.m_popup) {
        let source = HousingPurchaseLocation.Source(id);
        // Clear stale requests away from the authored entrance. No transaction.
        if !HousingPurchaseLocation.Validate(game, id, source) || state.Entitled(id) {
          quests.SetFact(request, 0);
        } else if canOffer && self.Show(id, source) {
          // Hold the native owner before acknowledging its request.
          quests.SetFact(ready, 0);
          quests.SetFact(request, 0);
        }
      }
      i += 1;
    }
  }

  public func Show(id: String, source: EntityID) -> Bool {
    if IsDefined(this.m_popup) { return false; }
    let game = this.GetGameInstance();
    let player = GetPlayer(game) as PlayerPuppet;
    let state = HousingState.Get(game);
    let manager = CustomPopupManager.GetInstance();
    if !IsDefined(state) || !IsDefined(manager) || !manager.IsInitialized() || !state.CanPurchase(id, player) || !HousingPurchaseLocation.Validate(game, id, source) { return false; }
    let quote = HousingPrice.Quote(game, id);
    if quote <= 0 { return false; }
    let popup = new HousingPurchasePopup();
    popup.Configure(id, quote, source);
    this.m_popup = popup;
    manager.ShowPopup(popup);
    return true;
  }

  public func Release(popup: ref<HousingPurchasePopup>) -> Void {
    if this.m_popup == popup { this.m_popup = null; }
  }
}

public class HousingPurchasePopup extends InGamePopup {
  private let m_property: String;
  private let m_quote: Int32;
  private let m_source: EntityID;
  private let m_buy: ref<PopupButton>;
  private let m_cancel: ref<PopupButton>;
  private let m_message: ref<inkText>;
  private let m_attempted: Bool;

  public func Configure(id: String, quote: Int32, source: EntityID) -> Void {
    this.m_property = id;
    this.m_quote = quote;
    this.m_source = source;
  }

  protected cb func OnCreate() -> Void {
    super.OnCreate();
    let header = InGamePopupHeader.Create();
    header.SetTitle(HousingPrice.Label(this.m_property));
    header.Reparent(this.m_container);
    let message = new inkText();
    message.SetName(n"purchaseDescription");
    message.SetFontFamily("base\\gameplay\\gui\\fonts\\raj\\raj.inkfontfamily");
    message.SetFontStyle(n"Regular");
    message.SetFontSize(42);
    message.SetMargin(new inkMargin(90.0, 200.0, 60.0, 0.0));
    message.SetSize(new Vector2(1320.0, 260.0));
    message.SetWrapping(true);
    message.SetText("Purchase this apartment for €$" + IntToString(this.m_quote) + "?\nYour home access is restored after payment.");
    message.Reparent(this.m_container);
    this.m_message = message;
    this.m_buy = PopupButton.Create();
    this.m_buy.SetText("Purchase — €$" + IntToString(this.m_quote));
    this.m_buy.SetInputAction(n"UI_Apply");
    this.m_buy.GetRootWidget().SetHAlign(inkEHorizontalAlign.Left);
    this.m_buy.SetPosition(380.0, 600.0);
    this.m_buy.SetWidth(500.0);
    this.m_buy.Reparent(this.m_container);
    this.m_buy.RegisterToCallback(n"OnBtnClick", this, n"OnPurchaseClick");
    this.m_cancel = PopupButton.Create();
    this.m_cancel.SetText("Cancel");
    this.m_cancel.SetInputAction(n"cancel");
    this.m_cancel.GetRootWidget().SetHAlign(inkEHorizontalAlign.Left);
    this.m_cancel.SetPosition(950.0, 600.0);
    this.m_cancel.Reparent(this.m_container);
    this.m_cancel.RegisterToCallback(n"OnBtnClick", this, n"OnCancelClick");
  }

  protected cb func OnShow() -> Void {
    super.OnShow();
    let player = GetPlayer(this.GetGame());
    let transaction = GameInstance.GetTransactionSystem(this.GetGame());
    if !IsDefined(player) || !IsDefined(transaction) || transaction.GetItemQuantity(player, MarketSystem.Money()) < this.m_quote {
      this.m_buy.SetDisabled(true);
      this.m_message.SetText("Price: €$" + IntToString(this.m_quote) + "\nYou do not have enough money to purchase this apartment.");
    }
  }

  protected cb func OnPurchaseClick(widget: wref<inkWidget>) -> Void { this.ConfirmPurchase(); }
  protected cb func OnCancelClick(widget: wref<inkWidget>) -> Void { this.Close(); }

  protected cb func OnGlobalReleaseInput(evt: ref<inkPointerEvent>) -> Bool {
    if evt.IsAction(n"UI_Apply") && !evt.IsHandled() && this.IsTopPopup() {
      this.ConfirmPurchase();
      evt.Handle();
      return true;
    }
    return super.OnGlobalReleaseInput(evt);
  }

  private func ConfirmPurchase() -> Void {
    if this.m_attempted || !IsDefined(this.m_buy) || this.m_buy.IsDisabled() || !this.IsTopPopup() { return; }
    let ui = HousingPurchaseUI.Get(this.GetGame());
    if !IsDefined(ui) || !ui.IsCurrent(this) { this.Close(); return; }
    this.m_attempted = true;
    this.m_buy.SetDisabled(true);
    let state = HousingState.Get(this.GetGame());
    if IsDefined(state) && state.Purchase(this.m_property, this.m_quote, this.m_source) {
      this.Close();
    } else {
      this.m_message.SetText("The purchase could not be completed. Close this window and check the apartment again.");
      this.m_cancel.SetText("Close");
    }
  }

  protected cb func OnHidden() -> Void {
    let ui = HousingPurchaseUI.Get(this.GetGame());
    super.OnHidden();
    if IsDefined(ui) { ui.Release(this); }
  }

  public func GetName() -> CName { return n"PTFRHousingPurchase"; }
  public func GetQueueName() -> CName { return n"ptfr_housing_purchase"; }
  public func UseCursor() -> Bool { return true; }
}
