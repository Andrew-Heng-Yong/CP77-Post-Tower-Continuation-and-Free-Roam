module PTFR.Housing

import Codeware.UI.*

// An automatic door's interaction volumes can extend beyond its entity pivot.
// Keep the original short-distance fallback for unloaded/disabled triggers.
@addMethod(Door)
public final func HousingAtEntranceH3(player: ref<PlayerPuppet>, leaving: Bool) -> Bool {
  if !IsDefined(player) || player.IsReplacer() ||
    !HousingDevices.Matches(this.GetEntityID(), HousingPurchaseLocation.Path("h10")) ||
    GetPlayer(this.GetGame()) != player { return false; }
  if IsDefined(this.m_triggerComponent) && this.m_triggerComponent.IsEntityOverlapping(player) { return true; }
  if IsDefined(this.m_triggerSideOne) && this.m_triggerSideOne.IsEntityOverlapping(player) { return true; }
  if IsDefined(this.m_triggerSideTwo) && this.m_triggerSideTwo.IsEntityOverlapping(player) { return true; }
  return Vector4.Distance(player.GetWorldPosition(), this.GetWorldPosition()) <= (leaving ? 5.0 : 3.5);
}

// Reuse the single original H10 POI. A for-sale marker is presentation only:
// entitlement, apartment services, native purchase history and FT are untouched.
public class HousingMapH3 extends ScriptableSystem {
  private let m_id: NewMappinID;
  private let m_cached: Bool;
  private let m_retry: Int32;
  private let m_status: String;

  public static func Get(game: GameInstance) -> ref<HousingMapH3> {
    return GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.Housing.HousingMapH3") as HousingMapH3;
  }
  public func Reset() -> Void { this.m_cached = false; this.m_retry = 0; this.m_status = "not checked"; }
  private func OnAttach() -> Void { this.Reset(); }
  private func OnDetach() -> Void { this.Reset(); }
  public func Status() -> String { return this.m_status; }

  public func Tick() -> Void {
    let game = this.GetGameInstance();
    let state = HousingState.Get(game);
    if !IsDefined(state) || !state.Enforcing() || !state.HousingReadyForReveal() { return; }
    let jm = GameInstance.GetJournalManager(game);
    let ms = GameInstance.GetMappinSystem(game);
    if !IsDefined(jm) || !IsDefined(ms) || jm.HasAnyDelayedStateChanges() { return; }
    let entry = jm.GetEntryByString("points_of_interest/safehouses/v_room", "gameJournalPointOfInterestMappin");
    if !IsDefined(entry) { this.m_status = "H10 journal POI unavailable"; return; }
    // H1 hid this POI on loss. Make the exact marker available for its new sale
    // variant. This is not a quest activation or a grant of apartment access.
    if NotEquals(jm.GetEntryState(entry), gameJournalEntryState.Active) {
      jm.ChangeEntryState("points_of_interest/safehouses/v_room", "gameJournalPointOfInterestMappin",
        gameJournalEntryState.Active, JournalNotifyOption.DoNotNotify);
      this.m_status = "H10 POI activation requested";
      return;
    }
    let hash = Cast<Uint32>(jm.GetEntryHash(entry));
    let poi: ref<PointOfInterestMappin>;
    if this.m_cached {
      poi = ms.GetMappin(this.m_id) as PointOfInterestMappin;
      if !IsDefined(poi) || poi.GetJournalPathHash() != hash { this.m_cached = false; poi = null; }
    }
    if !this.m_cached {
      if this.m_retry > 0 { this.m_retry -= 1; return; }
      this.m_retry = 4;
      let pins = ms.GetAllMappins();
      let i = 0;
      while i < ArraySize(pins) {
        poi = pins[i] as PointOfInterestMappin;
        if IsDefined(poi) && poi.GetJournalPathHash() == hash {
          this.m_id = poi.GetNewMappinID(); this.m_cached = true; break;
        }
        poi = null; i += 1;
      }
    }
    if !IsDefined(poi) { this.m_status = "waiting for original H10 POI"; return; }
    let paid = state.Entitled("h10");
    let variant = paid ? gamedataMappinVariant.ApartmentVariant : gamedataMappinVariant.Zzz05_ApartmentToPurchaseVariant;
    if NotEquals(poi.GetVariant(), variant) { ms.ChangeMappinVariant(this.m_id, variant); }
    if !poi.IsActive() { ms.SetMappinActive(this.m_id, true); }
    this.m_status = paid ? "owned H10 icon" : "purchasable H10 icon";
  }
}

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
