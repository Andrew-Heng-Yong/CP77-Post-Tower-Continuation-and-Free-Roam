"""Use native H10 confirmation; retain the DLC popup implementation and guards."""
from pathlib import Path
import shutil,json,hashlib
H=Path(__file__).resolve().parent;C=H/'candidate_01';G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
root=C/'package/r6/scripts/TowerContinued_Housing_H1'
extra=(H/'HousingEntranceH3.reds').read_text()
a=extra.index('// ShowPopup has no return value');b=extra.index('// Read-only diagnostics.')
extra=extra[:a]+extra[b:]
a=extra.index('// Read-only diagnostics.');b=extra.index('// Reuse the single original H10 POI.')
method=extra[a:b].replace('@addMethod(PTFR.Housing.HousingState)\n','')
extra=extra[:a]+extra[b:]
extra+='''
@wrapMethod(PopupsManager)
protected cb func OnPlayerAttach(playerPuppet: ref<GameObject>) -> Bool {
  wrappedMethod(playerPuppet);
  if IsDefined(playerPuppet) {
    let ui = HousingPurchaseUI.Get(playerPuppet.GetGame());
    if IsDefined(ui) { ui.BindControllerH3(this); }
  }
}

@wrapMethod(PopupsManager)
protected cb func OnPlayerDetach(playerPuppet: ref<GameObject>) -> Bool {
  if IsDefined(playerPuppet) {
    let ui = HousingPurchaseUI.Get(playerPuppet.GetGame());
    if IsDefined(ui) { ui.BindControllerH3(null); }
  }
  wrappedMethod(playerPuppet);
}
'''
(H/'HousingEntranceH3.reds').write_text(extra);(root/'HousingEntranceH3.reds').write_text(extra)
rel='r6/scripts/TowerContinued_Housing_H1/HousingState.reds'
before=C/'before'/rel;assert not before.exists();shutil.copyfile(G/rel,before)
s=before.read_text(encoding='utf-8-sig');marker='  public func Inspect(id: String) -> String {';assert s.count(marker)==1
s=s.replace(marker,method+'\n'+marker);(root/'HousingState.reds').write_text(s,encoding='utf-8')
s=(root/'HousingPurchase.reds').read_text(encoding='utf-8-sig')
def rep(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
rep('  private let m_h10Status: String;', '''  private let m_controllerH3: wref<inkGameController>;
  private let m_tokenH3: ref<inkGameNotificationToken>;
  private let m_serialH3: Int32;
  private let m_quoteH3: Int32;
  private let m_sourceH3: EntityID;
  private let m_h10Status: String;''')
rep('self.m_h10StatusTicks = 0; }','self.m_h10StatusTicks = 0; self.m_tokenH3 = null; self.m_serialH3 += 1; }')
rep('    } else if !self.m_h10Offered && !IsDefined(self.m_popup) &&','    } else if !self.m_h10Offered && !IsDefined(self.m_popup) && !IsDefined(self.m_tokenH3) &&')
rep('let canOffer = StartupCoverLC1.GameplayReleased(game) && !IsDefined(self.m_popup) &&','let canOffer = StartupCoverLC1.GameplayReleased(game) && !IsDefined(self.m_popup) && !IsDefined(self.m_tokenH3) &&')
rep('    if IsDefined(this.m_popup) { return false; }','    if IsDefined(this.m_popup) || IsDefined(this.m_tokenH3) { return false; }\n    if Equals(id, "h10") { return this.ShowH10NativeH3(source); }')
rep('''    if !manager.HousingTryShowH3(popup) {
      this.m_popup = null;
      return false;
    }
    ModLog(n"PTFR_HousingH3", "Purchase confirmation queued: " + id);''','    manager.ShowPopup(popup);')
a=s.index('  public func ShownH3(');b=s.index('  public func StatusH3()',a)
s=s[:a]+'''  public func BindControllerH3(controller: ref<inkGameController>) -> Void {
    this.m_controllerH3 = controller;
    if !IsDefined(controller) { this.m_tokenH3 = null; this.m_serialH3 += 1; }
  }

  private func ShowH10NativeH3(source: EntityID) -> Bool {
    let game = this.GetGameInstance();
    let state = HousingState.Get(game);
    let player = GetPlayer(game) as PlayerPuppet;
    if !IsDefined(this.m_controllerH3) || !IsDefined(state) || !IsDefined(player) ||
      !StartupCoverLC1.GameplayReleased(game) || !state.CanPurchase("h10", player) ||
      !HousingPurchaseLocation.Validate(game, "h10", source) { return false; }
    let board = GameInstance.GetBlackboardSystem(game).Get(GetAllBlackboardDefs().UI_System);
    if !IsDefined(board) || board.GetBool(GetAllBlackboardDefs().UI_System.IsInMenu) { return false; }
    let transaction = GameInstance.GetTransactionSystem(game);
    let quote = HousingPrice.Quote(game, "h10");
    if !IsDefined(transaction) || quote <= 0 { return false; }
    this.m_serialH3 += 1;
    this.m_quoteH3 = quote; this.m_sourceH3 = source;
    let enough = transaction.GetItemQuantity(player, MarketSystem.Money()) >= quote;
    let message = "Purchase the Megabuilding H10 apartment for €$" + IntToString(quote) + "?";
    if !enough { message = "Price: €$" + IntToString(quote) + "\\nYou do not have enough money to purchase this apartment."; }
    this.m_tokenH3 = GenericMessageNotification.Show(this.m_controllerH3, this.m_serialH3,
      "Megabuilding H10 apartment", message, enough ? GenericMessageNotificationType.YesNo : GenericMessageNotificationType.OK);
    if !IsDefined(this.m_tokenH3) { return false; }
    this.m_tokenH3.RegisterListener(this, n"OnH10PurchaseClosedH3");
    this.m_h10Offered = true;
    ModLog(n"PTFR_HousingH3", "H10 native purchase confirmation requested; €$" + IntToString(quote));
    return true;
  }

  protected cb func OnH10PurchaseClosedH3(data: ref<inkGameNotificationData>) -> Bool {
    let result = data as GenericMessageNotificationCloseData;
    if !IsDefined(this.m_tokenH3) || !IsDefined(result) || result.identifier != this.m_serialH3 { return false; }
    this.m_tokenH3 = null;
    // Consume this confirmation before any debit. Repeat callbacks, stale UI,
    // cancel and insufficient-funds OK can never invoke payment.
    this.m_serialH3 += 1;
    if NotEquals(result.result, GenericMessageNotificationResult.Yes) { return false; }
    let state = HousingState.Get(this.GetGameInstance());
    if IsDefined(state) && state.Purchase("h10", this.m_quoteH3, this.m_sourceH3) {
      HousingDoorH2.Tick(this.GetGameInstance());
      let map = HousingMapH3.Get(this.GetGameInstance());
      if IsDefined(map) { map.Tick(); }
      ModLog(n"PTFR_HousingH3", "H10 payment receipt accepted; native access/services pending.");
    } else if IsDefined(this.m_controllerH3) {
      GenericMessageNotification.Show(this.m_controllerH3, "Apartment purchase",
        "The purchase could not be completed. Check your funds and approach the apartment door again.", GenericMessageNotificationType.OK);
      ModLog(n"PTFR_HousingH3", "H10 purchase refused by existing payment guards.");
    }
  }

'''+s[b:]
rep('" UI=" + ToString(IsDefined(manager) && manager.IsInitialized()) +','" nativeUI=" + ToString(IsDefined(this.m_controllerH3)) +')
rep('" popup=" + ToString(IsDefined(this.m_popup)) + " shown=" + ToString(this.m_h10Offered) +','" popup=" + ToString(IsDefined(this.m_tokenH3)) + " offered=" + ToString(this.m_h10Offered) +')
rep('''    let ui = HousingPurchaseUI.Get(this.GetGame());
    if IsDefined(ui) { ui.ShownH3(this, this.m_property); }
''','')
s=s.replace('    // queued popup is not reported as visible until its own OnShow callback.','    // notification request is not a claim that the user saw the prompt.')
(root/'HousingPurchase.reds').write_text(s,encoding='utf-8')
files=[]
for p in root.glob('*.reds'):
 target=str(p.relative_to(C/'package')).replace('\\','/');b=C/'before'/target
 files.append({'target':target,'before':sha(b) if b.exists() else None,'after':sha(p)})
(C/'changes_02.json').write_text(json.dumps(files,indent=2)+'\n')
print(json.dumps(files,indent=2))
