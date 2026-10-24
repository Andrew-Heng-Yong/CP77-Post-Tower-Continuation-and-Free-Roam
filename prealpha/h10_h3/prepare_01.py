from pathlib import Path
import hashlib,json,shutil
H=Path(__file__).resolve().parent; W=H.parent.parent; C=H/'candidate_01'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
rel='r6/scripts/TowerContinued_Housing_H1/HousingPurchase.reds'
before=C/'before'/rel; before.parent.mkdir(parents=True,exist_ok=True)
assert not before.exists();shutil.copyfile(G/rel,before)
s=before.read_text(encoding='utf-8-sig')
def replace(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
replace('      position = door.GetWorldPosition();','      return door.HousingAtEntranceH3(player, false);')
replace('  private let m_h10Offered: Bool;', '''  private let m_h10Offered: Bool;
  private let m_h10Status: String;
  private let m_h10StatusTicks: Int32;''')
replace('    if IsDefined(self) { self.m_popup = null; self.m_h10Offered = false; }', '''    if IsDefined(self) { self.m_popup = null; self.m_h10Offered = false; self.m_h10Status = ""; self.m_h10StatusTicks = 0; }
    let map = HousingMapH3.Get(game);
    if IsDefined(map) { map.Reset(); }''')
start=s.index('    let h10 = HousingDoorH2.Door(game);')
end=s.index('    let ids: array<String>;',start)
s=s[:start]+'''    let map = HousingMapH3.Get(game);
    if IsDefined(map) { map.Tick(); }
    let h10 = HousingDoorH2.Door(game);
    if !IsDefined(h10) || !h10.HousingAtEntranceH3(player, true) {
      self.m_h10Offered = false;
    } else if !self.m_h10Offered && !IsDefined(self.m_popup) &&
      HousingDoorH2.Unpaid(game) && StartupCoverLC1.GameplayReleased(game) &&
      state.CanPurchase("h10", player) && HousingPurchaseLocation.Validate(game, "h10", h10.GetEntityID()) {
      let board = GameInstance.GetBlackboardSystem(game).Get(GetAllBlackboardDefs().UI_System);
      if IsDefined(board) && !board.GetBool(GetAllBlackboardDefs().UI_System.IsInMenu) {
        self.Show("h10", h10.GetEntityID());
      }
    }
    // Log changed gate states near the apartment, plus a slow heartbeat. A
    // queued popup is not reported as visible until its own OnShow callback.
    if IsDefined(h10) && Vector4.Distance(player.GetWorldPosition(), h10.GetWorldPosition()) < 30.0 {
      let status = self.StatusH3();
      self.m_h10StatusTicks += 1;
      if NotEquals(status, self.m_h10Status) || self.m_h10StatusTicks >= 30 {
        self.m_h10Status = status; self.m_h10StatusTicks = 0;
        ModLog(n"PTFR_HousingH3", status);
      }
    }
''' + s[end:]
replace('    manager.ShowPopup(popup);\n    return true;', '''    if !manager.HousingTryShowH3(popup) {
      this.m_popup = null;
      return false;
    }
    ModLog(n"PTFR_HousingH3", "Purchase confirmation queued: " + id);
    return true;''')
replace('  public func Release(popup: ref<HousingPurchasePopup>) -> Void {', '''  public func ShownH3(popup: ref<HousingPurchasePopup>, id: String) -> Void {
    if !this.IsCurrent(popup) { return; }
    if Equals(id, "h10") { this.m_h10Offered = true; }
    ModLog(n"PTFR_HousingH3", "Purchase confirmation attached: " + id);
  }

  public func StatusH3() -> String {
    let game = this.GetGameInstance();
    let state = HousingState.Get(game);
    let player = GetPlayer(game) as PlayerPuppet;
    let door = HousingDoorH2.Door(game);
    let map = HousingMapH3.Get(game);
    if !IsDefined(state) || !IsDefined(player) { return "H10 systems/player unavailable"; }
    let manager = CustomPopupManager.GetInstance();
    return "H10: " + state.PurchaseBlockH3("h10", player) +
      " door=" + ToString(IsDefined(door)) +
      " entrance=" + ToString(IsDefined(door) && door.HousingAtEntranceH3(player, false)) +
      " released=" + ToString(StartupCoverLC1.GameplayReleased(game)) +
      " UI=" + ToString(IsDefined(manager) && manager.IsInitialized()) +
      " popup=" + ToString(IsDefined(this.m_popup)) + " shown=" + ToString(this.m_h10Offered) +
      " map=" + (IsDefined(map) ? map.Status() : "unavailable");
  }

  public func Release(popup: ref<HousingPurchasePopup>) -> Void {''')
replace('  protected cb func OnShow() -> Void {\n    super.OnShow();', '''  protected cb func OnShow() -> Void {
    super.OnShow();
    let ui = HousingPurchaseUI.Get(this.GetGame());
    if IsDefined(ui) { ui.ShownH3(this, this.m_property); }''')
dest=C/'package'/rel;dest.parent.mkdir(parents=True,exist_ok=True);assert not dest.exists();dest.write_text(s,encoding='utf-8')
extra='r6/scripts/TowerContinued_Housing_H1/HousingEntranceH3.reds'
assert not (G/extra).exists();shutil.copyfile(H/'HousingEntranceH3.reds',C/'package'/extra)
changes=[{'target':rel,'before':sha(before),'after':sha(dest)},{'target':extra,'before':None,'after':sha(C/'package'/extra)}]
(C/'changes_01.json').write_text(json.dumps(changes,indent=2)+'\n')
shutil.copyfile(W/'prealpha/h10_h2/compile_01.py',H/'compile_01.py')
print(json.dumps(changes,indent=2))
