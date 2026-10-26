from pathlib import Path
import hashlib,json,shutil
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01';G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
C.mkdir(exist_ok=False)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
rows=[]
for name in ('HousingPurchase.reds','HousingDevices.reds'):
 rel='r6/scripts/TowerContinued_Housing_H1/'+name;b=C/'before'/rel;b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(G/rel,b)
 s=b.read_text(encoding='utf-8-sig')
 if name=='HousingPurchase.reds':
  start=s.index('    let h10 = HousingDoorH2.Door(game);',s.index('public static func Tick'))
  end=s.index('    // Log changed gate states',start)
  s=s[:start]+'    HousingDialogueH5.Tick(game);\n    let h10 = HousingDoorH2.Door(game);\n'+s[end:]
  s=s.replace('    let map = HousingMapH3.Get(game);\n    if IsDefined(map) { map.Reset(); }','    HousingDialogueH5.Reset(game);\n    let map = HousingMapH3.Get(game);\n    if IsDefined(map) { map.Reset(); }',1)
  s=s.replace('if Equals(id, "h10") { return this.ShowH10NativeH3(source); }','if Equals(id, "h10") { return false; } // H5: only an explicit native dialogue selection may purchase.')
  a=s.index('    let game = this.GetGameInstance();',s.index('  private func ShowH10NativeH3'))
  z=s.index('\n  public func StatusH3()',a)
  s=s[:a]+'''    // Retained signature for compatibility; the automatic H3 popup is retired.
    return false;
  }

  protected cb func OnH10PurchaseClosedH3(data: ref<inkGameNotificationData>) -> Bool {
    // A stale callback from the retired popup must never debit money.
    this.m_tokenH3 = null; this.m_serialH3 += 1;
    return false;
  }
''' +s[z:]
  s=s.replace('" popup=" + ToString(IsDefined(this.m_tokenH3)) + " offered=" + ToString(this.m_h10Offered) +','" dialogueReady=" + IntToString(GameInstance.GetQuestsSystem(game).GetFact(n"PTFRH5_Ready")) +')
 else:
  a=s.index('  let player = GetPlayer(game) as PlayerPuppet;',s.index('@wrapMethod(DoorControllerPS)'))
  z=s.index('\n}\n',a)
  s=s[:a]+'''  // H5 supplies a native dialogue hub, so do not add a competing device action.
  if HousingDoorH2.DenyEntry(game, source) { ArrayClear(actions); }
  return result;'''+s[z:]
  a=s.index('  let game = this.GetGameInstance();',s.index('public final func OnHousingPurchaseAction'))
  z=s.index('\n}\n',a)
  s=s[:a]+'''  // Compatibility handler for a stale old device choice. No popup or payment.
  return EntityNotificationType.DoNotNotifyEntity;'''+s[z:]
 out=C/'package'/rel;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(s,encoding='utf-8')
 rows.append({'target':rel,'before':sha(b),'after':sha(out)})
rel='r6/scripts/TowerContinued_Housing_H1/HousingDialogueH5.reds';out=C/'package'/rel
assert not (G/rel).exists();shutil.copyfile(H/'HousingDialogueH5.reds',out)
rows.append({'target':rel,'before':None,'after':sha(out)})
(C/'script_changes_01.json').write_text(json.dumps(rows,indent=2)+'\n')
shutil.copyfile(W/'prealpha/h10_h4/compile_01.py',H/'compile_01.py')
print(json.dumps(rows))
