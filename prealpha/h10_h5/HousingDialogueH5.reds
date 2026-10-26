module PTFR.Housing

import PTFR.LoadingCoverLC1.*

// The actor-free native choice writes Request only after explicit selection.
// Readiness, funds and pending UI requests are transient presentation state.
public class HousingDialogueH5 extends ScriptableSystem {
  private let initialized: Bool;
  private let armed: Bool;
  private let dismissed: Bool;
  private let quote: Int32;
  private let source: EntityID;

  public static func Get(game: GameInstance) -> ref<HousingDialogueH5> {
    return GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.Housing.HousingDialogueH5") as HousingDialogueH5;
  }
  public static func Reset(game: GameInstance) -> Void {
    let self = HousingDialogueH5.Get(game);
    if IsDefined(self) { self.initialized = false; self.armed = false; self.dismissed = false; }
  }
  private func OnAttach() -> Void { this.initialized = false; this.armed = false; this.dismissed = false; }
  private func OnDetach() -> Void { this.initialized = false; this.armed = false; }

  private func Set(q: ref<QuestsSystem>, name: CName, value: Int32) -> Void {
    if q.GetFact(name) != value { q.SetFact(name, value); }
  }
  private func Eligible(game: GameInstance, state: ref<HousingState>, player: ref<PlayerPuppet>, door: ref<Door>) -> Bool {
    if !IsDefined(state) || !IsDefined(player) || !IsDefined(door) || this.dismissed ||
      !StartupCoverLC1.GameplayReleased(game) || !HousingDoorH2.Unpaid(game) ||
      !state.CanPurchase("h10", player) || !HousingPurchaseLocation.Validate(game, "h10", door.GetEntityID()) { return false; }
    let board = GameInstance.GetBlackboardSystem(game).Get(GetAllBlackboardDefs().UI_System);
    return IsDefined(board) && !board.GetBool(GetAllBlackboardDefs().UI_System.IsInMenu);
  }
  public static func Tick(game: GameInstance) -> Void {
    let self = HousingDialogueH5.Get(game);
    if IsDefined(self) { self.Poll(); }
  }
  private func Poll() -> Void {
    let game = this.GetGameInstance();
    let q = GameInstance.GetQuestsSystem(game);
    if !IsDefined(q) { return; }
    if !this.initialized {
      this.Set(q, n"PTFRH5_Ready", 0); this.Set(q, n"PTFRH5_Funds", 0);
      this.Set(q, n"PTFRH5_Request", 0); this.Set(q, n"PTFRH5_Cancel", 0);
      this.armed = false; this.dismissed = false; this.initialized = true;
      return;
    }
    let player = GetPlayer(game) as PlayerPuppet;
    let state = HousingState.Get(game);
    let door = HousingDoorH2.Door(game);
    if !IsDefined(player) || !IsDefined(door) || !door.HousingAtEntranceH3(player, true) { this.dismissed = false; }
    let eligible = this.Eligible(game, state, player, door);
    let request = q.GetFact(n"PTFRH5_Request");
    let cancel = q.GetFact(n"PTFRH5_Cancel");
    if request != 0 || cancel != 0 {
      let accepted = this.armed && eligible && request == 1 && cancel == 0 &&
        this.source == door.GetEntityID() && this.quote == 25000;
      // Consume BEFORE calling the unchanged, single-debit payment operation.
      this.armed = false;
      this.Set(q, n"PTFRH5_Ready", 0); this.Set(q, n"PTFRH5_Funds", 0);
      this.Set(q, n"PTFRH5_Request", 0); this.Set(q, n"PTFRH5_Cancel", 0);
      if cancel != 0 { this.dismissed = true; }
      if accepted {
        this.dismissed = true;
        if state.Purchase("h10", this.quote, this.source) {
          HousingDoorH2.Tick(game);
          let map = HousingMapH3.Get(game);
          if IsDefined(map) { map.Tick(); }
          ModLog(n"PTFR_HousingH5", "Explicit dialogue purchase accepted; access/services reconciliation pending.");
        } else { ModLog(n"PTFR_HousingH5", "Dialogue purchase refused; no automatic retry. Step away to rearm."); }
      }
      return;
    }
    let transaction = GameInstance.GetTransactionSystem(game);
    let quote = HousingPrice.Quote(game, "h10");
    eligible = eligible && IsDefined(transaction) && quote == 25000;
    if eligible {
      this.source = door.GetEntityID(); this.quote = quote; this.armed = true;
      this.Set(q, n"PTFRH5_Funds", transaction.GetItemQuantity(player, MarketSystem.Money()) >= quote ? 1 : 0);
      this.Set(q, n"PTFRH5_Ready", 1);
    } else {
      this.armed = false;
      this.Set(q, n"PTFRH5_Ready", 0); this.Set(q, n"PTFRH5_Funds", 0);
    }
  }
}
