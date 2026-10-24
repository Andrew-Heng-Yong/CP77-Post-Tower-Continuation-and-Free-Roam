"""Offline checks of actual compiled payment guards and exact H10 map scope."""
from pathlib import Path
import hashlib,json,re
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
checks=[]
def ck(name,ok):
 assert ok,name
 checks.append(name)
def block(s,pattern):
 m=re.search(pattern,s);assert m,pattern
 a=s.index('{',m.start());i=a+1;level=1
 while level:level+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[m.start():i]
P=C/'package/r6/scripts/TowerContinued_Housing_H1'
p=(P/'HousingPurchase.reds').read_text(encoding='utf-8-sig');e=(P/'HousingEntranceH3.reds').read_text(encoding='utf-8-sig');state=(P/'HousingState.reds').read_text(encoding='utf-8-sig')
old=(C/'before/r6/scripts/TowerContinued_Housing_H1/HousingState.reds').read_text(encoding='utf-8-sig')
a=state.index('// Read-only diagnostics.');b=state.index('  public func Inspect(',a)
ck('HousingState differs only by a read-only diagnostic method',state[:a]+state[b:]==old)
oldp=(C/'before/r6/scripts/TowerContinued_Housing_H1/HousingPurchase.reds').read_text(encoding='utf-8-sig')
for cls in ['HousingPrice','HousingPurchasePopup','HousingWebsite']:
 pat=r'public (?:abstract )?class '+cls+r'\b'
 ck(cls+' implementation preserved',block(p,pat)==block(oldp,pat))
ck('Website guards unchanged',p[p.index('@wrapMethod(BrowserController)'):]==oldp[oldp.index('@wrapMethod(BrowserController)'):])
for method in ['Path','Source','Offset']:
 pat=r'  public static func '+method+r'\b'
 ck('Exact location catalogue '+method+' retained',block(p,pat)==block(oldp,pat))
ck('All DLC entrance transforms/radii preserved',block(p,r'  public static func Validate\b').split('    } else {')[1]==block(oldp,r'  public static func Validate\b').split('    } else {')[1])
ck('H10 actions and confirmation use identical native entrance validator','return door.HousingAtEntranceH3(player, false);' in p and p.count('HousingPurchaseLocation.Validate(game, "h10", source)')==1)
ck('Only exact H10/local player gets trigger extension',all(x in e for x in ['HousingDevices.Matches(this.GetEntityID(), HousingPurchaseLocation.Path("h10"))','GetPlayer(this.GetGame()) != player','player.IsReplacer()']))
door=(W/'prealpha/h10_h2/candidate_01/diagnosis_01/Door.script').read_text()
for field in ['m_triggerComponent','m_triggerSideOne','m_triggerSideTwo']:
 ck('Use native loaded trigger '+field,field+'.IsEntityOverlapping(player)' in e and field+': ref<TriggerComponent>' in door)
ck('Cancel stays latched until leaving door volume and five-metre fallback','!h10.HousingAtEntranceH3(player, true)' in p and 'leaving ? 5.0 : 3.5' in e and 'this.m_h10Offered = false' not in block(p,r'  protected cb func OnH10PurchaseClosedH3\b'))
cb=block(p,r'  protected cb func OnH10PurchaseClosedH3\b')
ck('Stale and duplicate confirmations consumed before durable transaction',cb.index('result.identifier != this.m_serialH3')<cb.index('this.m_tokenH3 = null')<cb.index('this.m_serialH3 += 1')<cb.index('GenericMessageNotificationResult.Yes')<cb.index('state.Purchase('))
ck('Cancellation/insufficient money never autocharge','GenericMessageNotificationType.YesNo : GenericMessageNotificationType.OK' in p and 'NotEquals(result.result, GenericMessageNotificationResult.Yes)' in cb)
ck('Single H10 debit entry; original H1 transaction owns the debit',p.count('state.Purchase("h10"')==1 and 'RemoveItem' not in p+e and old.count('transaction.RemoveItem(')==1)
ck('Reset and detach invalidate pending callbacks',all('m_serialH3 += 1' in block(p,pat) for pat in [r'  public static func Reset\b',r'  private func OnDetach\b',r'  public func BindControllerH3\b']))
ck('H10 uses native notification token, not the custom popup queue',all(x in block(p,r'  private func ShowH10NativeH3\b') for x in ['GenericMessageNotification.Show','m_tokenH3.RegisterListener','!state.CanPurchase','!HousingPurchaseLocation.Validate','UI_System.IsInMenu','!StartupCoverLC1.GameplayReleased']) and 'CustomPopupManager' not in block(p,r'  private func ShowH10NativeH3\b'))
ck('No forced ownership, money, service, door or quest writes added',all(x not in e for x in ['SetFact','RemoveItem','GiveItem','SetIsLocked','SetIsOpened','RegisterMappin(']))
paths=re.findall(r'"(points_of_interest/[^"]+)"',e)
ck('Only original H10 journal POI is touched',paths==['points_of_interest/safehouses/v_room']*2)
ck('Mappin selected by exact journal hash, never proximity or name','poi.GetJournalPathHash() == hash' in e and 'poi.GetJournalPathHash() != hash' in e)
ck('No synthetic or duplicate markers','RegisterMappin(' not in e and 'UnregisterMappin' not in e)
ck('Both map variants derive from preserved receipt authority','let paid = state.Entitled("h10");' in e and 'paid ? gamedataMappinVariant.ApartmentVariant : gamedataMappinVariant.Zzz05_ApartmentToPurchaseVariant' in e)
ck('H10 map change runs only after enforced housing is ready','!state.Enforcing() || !state.HousingReadyForReveal()' in e)
ck('Global mappin scans stop once cached and are throttled when absent','if !this.m_cached {' in e and 'this.m_retry = 4' in e and 'this.m_retry > 0' in e)
ck('New marker cache is transient and reset on reload','persistent let' not in e and 'map.Reset();' in p)
ck('Native POI template missing purchase offer is null guarded', 'if apartmentOffer != null {' in (W/'prealpha/h10_h2/candidate_01/compile_04/compiled.script').read_text())

compile=C/'compile_04';result=read(compile/'result.json')
ck('Full 90-source SCC including EquipmentEX passed',result['status']=='PASS_FULL_SCC_NOT_LIVE' and result['sources']==90 and result['full_scc_equipmentex'])
for f in P.glob('*.reds'):
 ck('Compiled final source '+f.name,sha(f)==sha(compile/'scripts/game/TowerContinued_Housing_H1'/f.name))
compiled=(compile/'compiled.script').read_text(encoding='utf-8-sig');prior=(W/'prealpha/h10_h2/candidate_01/compile_04/compiled.script').read_text(encoding='utf-8-sig')
sc=block(compiled,r'public class PTFR\.Housing\.HousingState\b');so=block(prior,r'public class PTFR\.Housing\.HousingState\b')
for name in ['CanPurchase','Purchase','SafeActor','Entitled','HousingReadyForReveal','Reconcile','Publish','Initialize','RecordValid','Tower']:
 pat=r'  (?:public|private)(?: final)? func '+name+r'\b'
 ck('Actual compiled HousingState.'+name+' bytecode readback unchanged',block(sc,pat)==block(so,pat))
for cls in ['HousingRecord','HousingState']:
 pat=r'public class PTFR\.Housing\.'+cls+r'\b'
 ck('Saved fields stable '+cls,re.findall(r'^  .*persistent let .*;',block(compiled,pat),re.M)==re.findall(r'^  .*persistent let .*;',block(prior,pat),re.M))
for cls,name,tokens in [('PTFR.Housing.HousingPurchaseUI','OnH10PurchaseClosedH3',['GenericMessageNotificationResult.Yes','this.m_serialH3 += 1','Purchase("h10"']),('PTFR.Housing.HousingMapH3','Tick',['points_of_interest/safehouses/v_room','GetJournalPathHash','ChangeMappinVariant','ApartmentToPurchaseVariant','Entitled("h10"'])]:
 c=block(compiled,r'public class '+re.escape(cls)+r'\b');m=block(c,r'  (?:public|protected|private)(?: final| cb)? func '+name+r'\b')
 ck('Final compiled branches '+cls+'.'+name,all(x in m for x in tokens))
# Bound the unchanged core/lock/services and every save to the actual diagnosis.
inputs=read(C/'diagnosis_02/inputs.json')
for path,h in inputs['saves'].items():ck('Save unchanged '+str(Path(path).relative_to(Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077'))),sha(Path(path))==h)
for name in ['HousingDevices.reds','HousingDoorH2.reds','WilsonLeaseH2.reds']:
 ck('Retain installed H2 '+name,sha(G/'r6/scripts/TowerContinued_Housing_H1'/name)==sha(C/'diagnosis_01/context'/name))
report={'status':'PASS_H3_OFFLINE_NOT_LIVE','checks':checks,'count':len(checks),'sources':{str(f):sha(f) for f in P.glob('*.reds')},'compiled_sha256':sha(compile/'cache/compiled.redscripts'),'live_cause':'H2 pivot-range/custom-popup candidates, not isolated in live logs','live_test':'pending'}
out=C/'tests_01.json';assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['checks','sources']}))
