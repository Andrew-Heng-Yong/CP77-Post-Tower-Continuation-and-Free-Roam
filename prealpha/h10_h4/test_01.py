"""Guard regression: preserve payment and migration; relax only ambient scene."""
from pathlib import Path
import hashlib,json,re
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def block(s,pat):
 m=re.search(pat,s);assert m,pat
 i=s.index('{',m.start());j=i+1;n=1
 while n:n+=(s[j]=='{')-(s[j]=='}');j+=1
 return s[m.start():j]
checks=[]
def ck(n,b):
 assert b,n
 checks.append(n)
old=(C/'before/r6/scripts/TowerContinued_Housing_H1/HousingState.reds').read_text(encoding='utf-8-sig')
new=(C/'package/r6/scripts/TowerContinued_Housing_H1/HousingState.reds').read_text(encoding='utf-8-sig')
safe=block(old,r'  private func SafeActor\b');purchase=block(new,r'  private func PurchaseSafeActor\b')
expected=safe.replace('SafeActor(player:', 'PurchaseSafeActor(player:').replace('scenes.IsEntityInScene(player.GetEntityID()) || ', '')
ck('Purchase actor guard duplicates every original check except ambient scene membership',purchase==expected)
ck('Original migration actor guard unchanged',block(new,r'  private func SafeActor\b')==safe)
ck('Migration continues to use original actor guard',block(new,r'  private func MigrationContext\b')==block(old,r'  private func MigrationContext\b') and 'this.SafeActor(this.Player())' in new)
for name in ['Purchase','Entitled','HousingReadyForReveal','Reconcile','Publish','Initialize','RecordValid','Tower','Restored','Poll']:
 pat=r'  (?:public|private) func '+name+r'\b'
 ck('HousingState.'+name+' unchanged',block(new,pat)==block(old,pat))
can_old=block(old,r'  public func CanPurchase\b');can_new=block(new,r'  public func CanPurchase\b')
ck('Eligibility uses new guard with all original payment/ownership/prerequisite conditions',can_new==can_old.replace('this.SafeActor(player)','this.PurchaseSafeActor(player)'))
diag_old=block(old,r'(?m)^\s*public func PurchaseBlockH3\b');diag_new=block(new,r'(?m)^\s*public func PurchaseBlockH3\b')
ck('Read-only status uses same purchase guard',diag_new==diag_old.replace('this.SafeActor(player)','this.PurchaseSafeActor(player)'))
ck('No new persistent fields',re.findall(r'(?m)^\s*public persistent let [^;]+;',old)==re.findall(r'(?m)^\s*public persistent let [^;]+;',new))
ck('No new currency or fact write',new.count('transaction.RemoveItem(')==old.count('transaction.RemoveItem(')==1 and new.count('SetFact(')==old.count('SetFact('))
ck('No added door/map/quest source edits',sha(G/'r6/scripts/TowerContinued_Housing_H1/HousingPurchase.reds')==sha(W/'prealpha/h10_h3/candidate_01/package/r6/scripts/TowerContinued_Housing_H1/HousingPurchase.reds') and sha(G/'r6/scripts/TowerContinued_Housing_H1/HousingEntranceH3.reds')==sha(W/'prealpha/h10_h3/candidate_01/package/r6/scripts/TowerContinued_Housing_H1/HousingEntranceH3.reds'))
diag=read(C/'diagnosis_01/inputs.json')
ck('Observed live failure had enterable entrance, released cover, native UI, and scene flag',any('entrance=true released=true nativeUI=true popup=false' in s and 'high=1 tier=1 scene=true dialogue=false combat=false' in s for s in diag['diagnostic_rows']))
ck('No live purchase confirmation on failing H3 run',not any('purchase confirmation requested' in s for s in diag['diagnostic_rows']))
for p,h in diag['saves'].items():ck('User save file unchanged '+str(Path(p).relative_to(Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077'))),sha(Path(p))==h)
base=(W/'prealpha/h10_h3/candidate_01/compile_04/compiled.script').read_text(encoding='utf-8-sig');result=C/'compile_01';c=(result/'compiled.script').read_text(encoding='utf-8-sig')
b=block(base,r'public class PTFR\.Housing\.HousingState\b');n=block(c,r'public class PTFR\.Housing\.HousingState\b')
for name in ['SafeActor','MigrationContext','Purchase','Entitled','HousingReadyForReveal','Reconcile','Publish','Initialize','RecordValid','Tower']:
 pat=r'  (?:public|private)(?: final)? func '+name+r'\b'
 ck('Compiled method unchanged '+name,block(n,pat)==block(b,pat))
ck('Compiled purchase guard excludes ambient scene only', 'IsEntityInScene(' not in block(n,r'  public func PurchaseSafeActor\b') and 'IsEntityInDialogue(' in block(n,r'  public func PurchaseSafeActor\b'))
ck('Full stack SCC and EquipmentEX passed',read(result/'result.json')['sources']==90 and read(result/'result.json')['full_scc_equipmentex'] and read(result/'result.json')['status']=='PASS_FULL_SCC_NOT_LIVE')
ck('Compiled exact candidate source',sha(result/'scripts/game/TowerContinued_Housing_H1/HousingState.reds')==sha(C/'package/r6/scripts/TowerContinued_Housing_H1/HousingState.reds'))
report={'status':'PASS_H4_OFFLINE_NOT_LIVE','checks':checks,'count':len(checks),'compiled_sha256':sha(result/'cache/compiled.redscripts'),'diagnostic_log_sha256':diag['log_sha256'],'save_files_checked':len(diag['saves']),'live_result':'pending'}
out=C/'tests_01.json';assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='checks'}))
