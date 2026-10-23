
// EzEstates still has a native fact-driven purchase entry on public computers.
// H1 uses the property entrance and durable receipt for every new transaction.
public abstract class HousingWebsite {
  public static func Enforcing() -> Bool {
    let state = HousingState.Get(GetGameInstance());
    return IsDefined(state) && state.Enforcing();
  }

  public static func IsPurchaseAddress(const address: script_ref<String>) -> Bool {
    return Equals(Deref(address), "NETdir://ezestates.web/for_rent/offers/watson/purchase") ||
      Equals(Deref(address), "NETdir://ezestates.web/for_rent/offers/westbrook/purchase") ||
      Equals(Deref(address), "NETdir://ezestates.web/for_rent/offers/heywood/purchase") ||
      Equals(Deref(address), "NETdir://ezestates.web/for_rent/offers/city/purchase");
  }

  public static func IsPurchaseFact(fact: CName) -> Bool {
@@WEBSITE_FACTS@@
    return false;
  }
}

@wrapMethod(BrowserController)
private final func LoadWebPage(const address: script_ref<String>) -> Void {
  if HousingWebsite.Enforcing() && HousingWebsite.IsPurchaseAddress(address) {
    GenericMessageNotification.Show(this.m_gameController, "Apartment purchase", "Visit the property to purchase this apartment.", null, GenericMessageNotificationType.OK);
    return;
  }
  wrappedMethod(address);
}

@wrapMethod(BrowserController)
private final func SetFacts(page: wref<JournalInternetPage>) -> Void {
  if !HousingWebsite.Enforcing() { wrappedMethod(page); return; }
  if !IsDefined(page) { return; }
  let owner = this.GetOwnerGameObject();
  if !IsDefined(owner) { return; }
  let factsToSet = page.GetFactsToSet();
  let i = 0;
  while i < ArraySize(factsToSet) {
    if NotEquals(factsToSet[i].factName, n"None") && !HousingWebsite.IsPurchaseFact(factsToSet[i].factName) {
      SetFactValue(owner.GetGame(), factsToSet[i].factName, factsToSet[i].factValue);
    }
    i += 1;
  }
}
