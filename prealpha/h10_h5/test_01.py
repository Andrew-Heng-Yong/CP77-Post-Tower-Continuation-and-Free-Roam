from pathlib import Path
import hashlib,json,re,sys
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
sys.path.insert(0,str(W/'tools'))
from audit_wilson_vendor_owner import walk,graph_edges
from test_b0_ordinary_vendor_batch import handles
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def block(s,pat):
 m=re.search(pat,s);assert m,pat
 i=s.index('{',m.start());j=i+1;n=1
 while n:n+=(s[j]=='{')-(s[j]=='}');j+=1
 return s[m.start():j]
checks=[]
def ck(label,value):assert value,label;checks.append(label)
before=(W/'prealpha/h10_h4/candidate_01/compile_01/compiled.script').read_text(encoding='utf-8-sig')
after=(C/'compile_01/compiled.script').read_text(encoding='utf-8-sig')
ck('Entire compiled HousingState payment/persistence class unchanged',block(before,r'public class PTFR\.Housing\.HousingState\b')==block(after,r'public class PTFR\.Housing\.HousingState\b'))
for name in ('HousingPrice','HousingPurchaseLocation','HousingPurchasePopup','HousingMapH3','HousingDoorH2','HousingWebsite'):
 pat=r'public (?:abstract )?class PTFR\.Housing\.'+name+r'\b'
 ck('Compiled '+name+' unchanged',block(before,pat)==block(after,pat))
ui=(C/'package/r6/scripts/TowerContinued_Housing_H1/HousingPurchase.reds').read_text()
dev=(C/'package/r6/scripts/TowerContinued_Housing_H1/HousingDevices.reds').read_text()
src=(H/'HousingDialogueH5.reds').read_text()
tick=block(ui,r'  public static func Tick\b')
ck('Proximity tick cannot open any H10 popup','self.Show("h10"' not in tick and 'HousingDialogueH5.Tick(game)' in tick)
ck('Old native H10 popup retired','GenericMessageNotification.Show(' not in block(ui,r'public class HousingPurchaseUI\b'))
ck('Old popup callback has no transaction','Purchase(' not in block(ui,r'  protected cb func OnH10PurchaseClosedH3\b'))
ck('No duplicate device action','new HousingPurchaseAction()' not in dev)
ck('Old device callback inert','ui.Show(' not in block(dev,r'public final func OnHousingPurchaseAction\b'))
ck('One guarded new payment call',src.count('state.Purchase(')==1 and 'if accepted {' in src)
ck('Request consumed before payment',src.index('this.Set(q, n"PTFRH5_Request", 0);',src.index('if request != 0'))<src.index('state.Purchase('))
ck('Reload/reset disarms and clears pending request','this.armed = false; this.dismissed = false; this.initialized = true;' in src and 'HousingDialogueH5.Reset(game)' in ui)
ck('Exact UI price matches protected quote','this.quote == 25000' in src and 'quote == 25000' in src)
ck('No new persistent schema','persistent let' not in src)
ck('No duplicate money writer','RemoveItem' not in src+ui+dev)
for guard in ('StartupCoverLC1.GameplayReleased','HousingDoorH2.Unpaid','state.CanPurchase','HousingPurchaseLocation.Validate','UI_System.IsInMenu','this.source == door.GetEntityID()'):
 ck('H5 selection guard '+guard,guard in src)
r=read(C/'native_readback/h10_purchase.scene.json')['Data']['RootChunk']
ns={h['Data']['nodeId']['id']:h['Data'] for h in r['sceneGraph']['Data']['graph']}
ck('No actor acquisition',r['actors']==r['playerActors']==[] and all(not(v.get('$type')=='scnActorId' and v['id']!=4294967295) for v in walk(r)))
ck('Six scene nodes only',set(ns)=={2,1540,1542,1546,1569,1570})
choice=ns[1542];door=re.search(r'if Equals\(id, "h10"\) \{ return "([^"]+)";',ui).group(1)
ck('Native on-screen choice bound to exact door',choice['mode']=='attachToGameObject' and choice['atgoParams']['nodeRef']['$value']==door and choice['atgoParams']['visualizerStyle']=='onScreen')
ck('Owner and shape are local',choice['shapeParams']['Data']['customActivationRange']==3.5 and choice['shapeParams']['Data']['customIndicationRange']==5.0)
ck('No automatic/single-choice selection',all(o['isSingleChoice']==0 and o['timedCondition'] is None and o['gameplayAction']['$value']=='0' for o in choice['options']))
ck('Buy/cancel choices with inactive insufficient-funds row',[o['type']['properties'] for o in choice['options']]==[1,4,0])
edges=[(i,o['stamp']['name'],o['stamp']['ordinal'],d['nodeId']['id']) for i,n in ns.items() for o in n.get('outputSockets',[]) for d in o['destinations']]
ck('Request writer only entered by explicit buy selection',[(a,s,o) for a,s,o,b in edges if b==1540]==[(1542,0,0)])
ck('Cancel writer only entered by Not now',[(a,s,o) for a,s,o,b in edges if b==1570]==[(1542,0,2)])
ck('Start only presents UI and cancellation watcher',set(b for a,s,o,b in edges if a==1546)=={1542,1569})
writes={v['factName']:v['value'] for v in walk(r) if v.get('$type')=='questSetVar_NodeType'}
ck('Native scene never grants ownership or charges',writes=={'PTFRH5_Request':1,'PTFRH5_Cancel':1})
ck('All paths after choice end scene',(1540,0,0,2) in edges and (1570,0,0,2) in edges and (1569,0,0,2) in edges)
ck('Readiness cancellation watcher',any(v.get('factName')=='PTFRH5_Ready' and v.get('value')==0 for v in walk(ns[1569])))
labels=['Purchase apartment — €$25,000','Not enough money — €$25,000 required','Not now']
ck('Embedded English labels exact',[p['content'] for p in r['locStore']['vpEntries']]==labels)
for i,sc in enumerate(r['screenplayStore']['options']):
 vd=r['locStore']['vdEntries'][i];vp=r['locStore']['vpEntries'][vd['vpeIndex']]
 ck('Localization mapping '+str(i),sc['locstringId']==vd['locstringId'] and vd['variantId']==vp['variantId'] and vd['localeId']=='en_us')
o=read(C/'native_readback/h10_purchase.questphase.json')['Data']['RootChunk'];g=o['graph']['Data'];n={h['Data']['id']:h['Data'] for h in g['nodes']}
ck('Owner contains only waits and a scene',set(n)=={0,1,2,3} and not any(v.get('$type')=='questSetVar_NodeType' for v in walk(o)))
ck('Owner location matches choice',n[2]['sceneLocation']['nodeRef']['$value']==door)
oe=graph_edges(g,'root',handles(o));ck('Owner waits for Ready0 before rearming',{(e['source_node_id'],e['source_socket'],e['destination_node_id']) for e in oe}=={(0,'Out',1),(1,'Out',2),(2,'out',3),(2,'Default INT',3),(3,'Out',1)})
# Request/receipt contract cases. This model documents adverse ordering; the
# compiled HousingState comparison above verifies the actual debit implementation.
def consume(armed=True,eligible=True,request=1,cancel=0,source=True,quote=25000,balance=25000,paid=False,initialized=True):
 if not initialized:return False,0
 accepted=armed and eligible and request==1 and cancel==0 and source and quote==25000
 return False,int(accepted and balance>=quote and not paid)
ck('One explicit affordable selection can buy',consume()[1]==1)
for kw in ({'armed':False},{'eligible':False},{'request':0},{'request':2},{'cancel':1},{'source':False},{'quote':25001},{'balance':24999},{'paid':True},{'initialized':False}):
 ck('Adverse selection '+str(kw),consume(**kw)[1]==0)
armed,debits=consume();ck('Duplicate callback rejected after consume',debits==1 and consume(armed=armed)[1]==0)
comp=read(C/'compile_01/result.json');ck('Full91source SCC includes EquipmentEX',comp['status']=='PASS_FULL_SCC_NOT_LIVE' and comp['sources']==91 and comp['full_scc_equipmentex'])
for row in read(C/'script_changes_01.json'):
 p=G/row['target'];ck('Original script baseline '+row['target'],(sha(p) if p.exists() else None)==row['before'])
 ck('Exact compiled candidate '+row['target'],sha(C/'compile_01/scripts/game'/Path(row['target']).relative_to('r6/scripts'))==row['after'])
S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077');old=read(W/'diagnostics/scene_membership_20261025_01/inputs_01/receipt.json')
ck('All saved files remain unchanged',{str(p.relative_to(S)):sha(p) for p in S.rglob('*') if p.is_file()}==old['save_hashes'])
fs=read(W/'recovery/fred_scene_fs1_01/receipt.json')['files'][0];ck('FS1 Fred repair preserved',sha(G/fs['target'])==fs['after'])
files=list(H.glob('*.*'))+[C/'native_01.json',C/'script_changes_01.json',C/'compile_01/result.json',C/'compile_01/cache/compiled.redscripts']+list((C/'native_readback').glob('*.json'))
out={'status':'PASS_H5_OFFLINE_LIVE_PENDING','count':len(checks),'checks':checks,'sources':{str(p):sha(p) for p in files},'saved_files':len(old['save_hashes']),'compiled_sha256':comp['compiled_sha256'],'limits':['Native UI placement, selection, cancellation and save reload require live verification.','English labels only; other languages not tested.','Request contract model is not engine execution.']}
p=C/'tests_01.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('checks','sources')}))
