from pathlib import Path
import hashlib,json,shutil
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01';G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
changes=[]
for name in ['HousingDevices.reds','HousingPurchase.reds']:
 rel='r6/scripts/TowerContinued_Housing_H1/'+name;p=G/rel;s=p.read_text(encoding='utf-8-sig')
 b=C/'before'/rel;b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,b)
 if name=='HousingDevices.reds':
  s=s.replace('public class HousingPurchaseAction extends ActionBool {','public class HousingPurchaseAction extends ActionBool {\n  // Use the existing vanilla choice metadata; the caption is our explicit quote.\n  public func GetTweakDBChoiceRecord() -> String { return "Pay"; }')
  s=s.replace('// Keep opening/closing and egress intact, including a save loaded indoors.','// Existing DLC payment guards remain; H2 restricts only unpaid H10 entry.')
  s=s.replace('  let player = context.processInitiatorObject as PlayerPuppet;','  let player = GetPlayer(game) as PlayerPuppet;')
  s=s.replace('  let action = new HousingPurchaseAction();','  // No open/force/quickhack choice is offered on the unpaid outside face.\n  if HousingDoorH2.DenyEntry(game, source) { ArrayClear(actions); }\n  let action = new HousingPurchaseAction();')
 else:
  s=s.replace('  private let m_popup: ref<HousingPurchasePopup>;','  private let m_popup: ref<HousingPurchasePopup>;\n  private let m_h10Offered: Bool;')
  s=s.replace('self.m_popup = null;', 'self.m_popup = null; self.m_h10Offered = false;')
  s=s.replace('this.m_popup = null; }', 'this.m_popup = null; this.m_h10Offered = false; }')
  # Cancellation intentionally keeps the proximity latch. Reset only on exit/reload.
  s=s.replace('if this.m_popup == popup { this.m_popup = null; this.m_h10Offered = false; }','if this.m_popup == popup { this.m_popup = null; }')
  needle='    let ids: array<String>;'
  assert s.count(needle)==1
  s=s.replace(needle,'''    HousingDoorH2.Tick(game);
    let h10 = HousingDoorH2.Door(game);
    if !IsDefined(h10) || Vector4.Distance(player.GetWorldPosition(), h10.GetWorldPosition()) > 5.0 {
      self.m_h10Offered = false;
    } else if !self.m_h10Offered && !IsDefined(self.m_popup) &&
      HousingDoorH2.Unpaid(game) && StartupCoverLC1.GameplayReleased(game) &&
      state.CanPurchase("h10", player) && HousingPurchaseLocation.Validate(game, "h10", h10.GetEntityID()) {
      let board = GameInstance.GetBlackboardSystem(game).Get(GetAllBlackboardDefs().UI_System);
      if IsDefined(board) && !board.GetBool(GetAllBlackboardDefs().UI_System.IsInMenu) && self.Show("h10", h10.GetEntityID()) {
        self.m_h10Offered = true;
        ModLog(n"PTFR_HousingH2", "H10 entrance purchase offered; explicit confirmation required.");
      }
    }
'''+needle)
 dest=C/'package'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(s,encoding='utf-8');changes.append({'target':rel,'before':sha(p),'after':sha(dest)})
rel='r6/scripts/TowerContinued_Housing_H1/HousingDoorH2.reds';dest=C/'package'/rel;assert not (G/rel).exists();shutil.copyfile(H/'HousingDoorH2.reds',dest);changes.append({'target':rel,'before':None,'after':sha(dest)})
(C/'changes_01.json').write_text(json.dumps(changes,indent=2)+'\n')
shutil.copyfile(W/'prealpha/loading_cover_lc3/compile_01.py',H/'compile_01.py')
print(json.dumps({'script_changes':len(changes)}))
