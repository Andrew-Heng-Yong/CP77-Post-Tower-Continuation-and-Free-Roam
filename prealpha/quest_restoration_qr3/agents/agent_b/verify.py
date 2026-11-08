"""Read-only vehicle quest contract verifier. Requires a fresh output directory."""
from pathlib import Path
import argparse,sys,json,gzip,copy,re,collections,hashlib
W=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args()
O=Path(args.output).resolve();assert not O.exists(),'Preserve pinned verification outputs';O.mkdir(parents=True)
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';I=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json')
PH3=W/'prealpha/phone_studios_ph3/candidate_01'
parent_base=W/'research/ncpd_scanner_n1/parents_02'
parent_inv={r['resource']:r for r in read(parent_base/'inventory.json')}
PAR=r'base\open_world\minor_activities\badlands\inland_avenue_se1\ma_bls_ina_se1_minor_activities.questphase'
BUG=r'base\open_world\bugfixing\ma\ma_ina_west_bugfixing.questphase'
specs=[{'id':'mq046_cave_vehicle','title':'Murk Man Returns Again Once More Forever','num':'40','tag':'PTFRS23_MQ046','private':r'towercontinued\sidejobs_s23\ep1\mq046_boot.questphase','native':r'base\open_world\minor_activities\badlands\inland_avenue_se1\ma_bls_ina_se1_40\ma_bls_ina_se1_40_phase.questphase','parent_node':141,'vehicle':'Vehicle.v_sport1_rayfield_caliburn_02_player','item':'Keycards.ma_bls_ina_se1_40_car_keys'},
 {'id':'mq047_ad_vehicle','title':'Dressed to Kill','num':'44','tag':'PTFRS23_MQ047','private':r'towercontinued\sidejobs_s23\ep1\mq047_boot.questphase','native':r'base\open_world\minor_activities\badlands\inland_avenue_se1\ma_bls_ina_se1_44\ma_bls_ina_se1_44_phase.questphase','parent_node':145,'vehicle':'Vehicle.v_standard25_thorton_colby_pickup_02_player','item':'Keycards.ma_bls_ina_se1_44_car_keys'}]
models={};pins=[];checks=[]
def check(name,ok,evidence):
 checks.append({'name':name,'status':'PASS' if ok else 'FAIL','evidence':evidence});assert ok,name
def load(d):
 if d in models:return models[d]
 if d in parent_inv:
  r=parent_inv[d];b=parent_base/'raw'/Path(d.replace('\\','/'));j=parent_base/'json'/Path(d.replace('\\','/'))
  j=Path(str(j)+'.json');expected=r['raw_sha256'];provider=r['archive'];assert sha(j)==r['json_sha256']
 else:
  r=I[d];j=Path(r['json']);expected=r['sha256'];provider=r['archive']
  b=PH3/'archive_source'/Path(d.replace('\\','/')) if d.startswith('towercontinued\\') else j.with_suffix('')
 assert b.is_file() and sha(b)==expected,(d,b)
 m=Resource(read(j)).normalize()
 if d in MI:
  old=json.loads(gzip.decompress(Path(MI[d]['normalized_model']).read_bytes()));old.setdefault('embedded_files',[])
  assert old==m,'Raw/cached model mismatch: '+d
 check('raw pin '+d,sha(b)==expected,{'binary':str(b),'sha256':expected})
 pins.append({'depot':d,'sha256':expected,'binary':str(b),'source_json':str(j),'json_sha256':sha(j),'provider':provider,'errors':m['errors']})
 models[d]=m;return m
def graph(d,gp='root'):return load(d)['graphs'][gp]
def node(d,i,gp='root'):return graph(d,gp)['nodes'][str(i)]
def edge(d,a,s,b,t,gp='root'):return [str(a),s,str(b),t] in graph(d,gp)['edges']
def typ(p,t):return [x for x in walk(p) if x.get('$type')==t]
def ev(p,fs,js,vs):
 t=p.get('$type')
 if t in ['questFactsDBCondition','questJournalCondition','questVehicleCondition']:return ev(p['type'],fs,js,vs)
 if t=='questLogicalCondition':
  a=[ev(x,fs,js,vs) for x in p['conditions']];op=p['operation']
  if op=='AND':return False if False in a else None if None in a else True
  r=True if True in a else None if None in a else False
  return (None if r is None else not r) if op=='NOR' else r if op=='OR' else None
 if t=='questVarComparison_ConditionType':
  f=p['factName']
  if f not in fs:return None
  a,b=fs[f],p['value'];return {'Equal':a==b,'Greater':a>b,'GreaterOrEqual':a>=b,'Less':a<b,'LessOrEqual':a<=b,'NotEqual':a!=b}[p['comparisonType']]
 if t=='questJournalEntryState_ConditionType':
  k=p['path']['realPath']
  return None if k not in js else (js[k]==p['state'])!=bool(p.get('inverted',0))
 if t=='questVehicleAvailable_ConditionType':return vs.get(p['vehicleName'])
 return None

load(PAR);load(BUG)
for s in specs:
 P,N=s['private'],s['native'];load(P);load(N);tag=s['tag'];vid=s['vehicle'];pn=s['parent_node']
 check(s['id']+' native district startup delay/body payload exact',node(P,173,'root/100')['payload']==node(PAR,173)['payload'] and node(P,pn,'root/100')['payload']==node(PAR,pn)['payload'],{'native_parent':PAR,'private_graph':'root/100','delay':173,'body':pn})
 check(s['id']+' connected native In1 route',edge(P,0,'Out',173,'In','root/100') and edge(P,173,'Out',pn,'In1','root/100') and edge(P,92,'Out',100,'In1'),{'private_graph':'root/100','body_socket':'In1'})
 check(s['id']+' original parent prefab obligations empty',not load(PAR)['root_prefabs'] and not node(PAR,pn)['payload']['phaseInstancePrefabs'],{'root_prefabs':load(PAR)['root_prefabs'],'native_node':pn})
 check(s['id']+' private native prefab obligation retained',load(N)['root_prefabs']==['#loc_ma_bls_ina_se1_'+s['num']+'_openworld'],{'native_root_prefabs':load(N)['root_prefabs']})
 check(s['id']+' preclaim rearm and postclaim failure cut',all(edge(P,*x) for x in [(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'False',2,'In'),(3,'True',4,'In'),(4,'Out',89,'In'),(89,'Out',90,'In'),(90,'False',91,'In'),(90,'True',92,'In'),(92,'Out',102,'In'),(102,'Out',101,'In')]),{'pause':2,'recheck':3,'Issued':4,'delay':89,'recheck_claim':90,'Fault':91,'Entered':92,'native_success_observer':102,'Finished':101})
 check(s['id']+' postclaim tickdelay2',node(P,89)['payload']['condition']['type']['tickCount']==2,{'node':89})
 for ni,issued in [(2,0),(3,0),(90,1)]:
  cond=node(P,ni)['payload']['condition'];fs={x['factName']:x['value'] for x in typ(cond,'questVarComparison_ConditionType')};js={x['path']['realPath']:'Inactive' for x in typ(cond,'questJournalEntryState_ConditionType')};vs={vid:False}
  check(s['id']+f' guard{ni} positive',ev(cond,fs,js,vs) is True,{'native_vehicle_not_owned':vid,'Issued':issued})
  check(s['id']+f' guard{ni} owns vehicle refusal',ev(cond,fs,js,{vid:True}) is False,vid)
  check(s['id']+f' guard{ni} unknown vehicle does not become NOR success',ev(cond,fs,js,{}) is not True,vid)
  for path in js:
   for state in ['Active','Succeeded','Failed']:
    check(s['id']+f' guard{ni} refuses {state} '+path,ev(cond,fs,js|{path:state},vs) is False,{'node':ni,'path':path,'state':state})
   missing=dict(js);del missing[path];check(s['id']+f' guard{ni} refuses missing '+path,ev(cond,fs,missing,vs) is not True,path)
  for f in ['q307_done',tag+'_Fault',tag+'_Finished','ma_bls_ina_se1_'+s['num']+'_finished']:
   x=dict(fs);x[f]=0 if fs[f] else 1
   check(s['id']+f' guard{ni} refuses changed '+f,ev(cond,x,js,vs) is False,{'fact':f,'value':x[f]})
  x=dict(fs);x[tag+'_Issued']=1-issued;check(s['id']+f' guard{ni} refuses wrong receipt',ev(cond,x,js,vs) is False,{'Issued':1-issued})
 check(s['id']+' wrapper only owned fact writes',all(x['factName'].startswith(tag+'_') for gr in load(P)['graphs'].values() for n in gr['nodes'].values() for x in n['writes']),{'wrapper':P})
 check(s['id']+' completion waits original Succeeded',node(P,102)['reads'][0]['state']=='Succeeded' and node(P,102)['reads'][0]['path']['realPath']=='quests/minor_quest/'+s['id'],{'observer':102,'receipt':101})
 allp=[n['payload'] for gr in load(N)['graphs'].values() for n in gr['nodes'].values()]
 check(s['id']+' no phone requests SMS or ack dependencies in body',not any(('audio_' in str(p) or 'holo_' in str(p)) for p in allp) and not any('Phone' in x.get('$type','') or 'SendMessage' in x.get('$type','') for p in allp for x in walk(p)),{'native_body':N,'scope':'No phone protocol in complete phase graphs; native journal Onscreen email read is local world content'})
 def path_check(edges):return all(edge(N,*e) for e in edges)
 if s['num']=='40':
  check('MQ046 q103 two days tier5 preserved',node(N,30)['reads'][0]['factName']=='q103_done' and node(N,30)['reads'][0]['value']==1 and node(N,31)['payload']['condition']['type']['days']==2 and value(node(N,34)['payload']['condition']['type']['tierID'])=='StreetCredTier.VehicleTier5' and path_check([(0,'Out',30,'In'),(30,'Out',31,'In'),(31,'Out',34,'In'),(34,'Out',121,'In'),(121,'Out',32,'In')]),{'nodes':[30,31,34],'elapsed_scope':'Native wait begins when this fresh owner enters, not fabricated pre-Tower elapsed history'})
  check('MQ046 native reward and completion branches',path_check([(81,'Out',48,'In'),(48,'Out',118,'In'),(118,'Out',120,'In'),(120,'True',117,'In'),(120,'False',119,'In'),(119,'Out',117,'In'),(117,'Out',83,'In'),(117,'Out',88,'Succeeded'),(88,'Out',89,'Succeeded'),(89,'Out',87,'In'),(87,'Out',1,'In')]) and node(N,83)['payload']['type']['vehicle']==vid and node(N,83)['payload']['type']['enable']==1,{'enable':83,'mount':117,'objective':88,'quest':89})
  item=106;johnny=[(45,'Out',67,'In'),(67,'Out',68,'In'),(68,'Out',113,'In'),(113,'Out',69,'In'),(69,'Out',70,'In'),(70,'Out',71,'In'),(71,'Out',72,'In')]
 else:
  check('MQ047 native trigger variant and spawn path',path_check([(0,'Out',109,'In'),(109,'Out',72,'In'),(72,'Out',75,'In'),(75,'Out',74,'In'),(74,'Out',33,'In'),(33,'Out',107,'In'),(107,'Out',76,'In'),(76,'Out',106,'In')]),{'trigger':72,'spawn_ambient':75,'loot_variant':74,'player_vehicle':76})
  check('MQ047 native reward completion and parallel cleanup',path_check([(55,'Out',41,'In'),(41,'Out',100,'In'),(100,'Out',99,'In'),(99,'Out',57,'In'),(99,'Out',60,'Succeeded'),(60,'Out',61,'Succeeded'),(61,'Out',59,'In'),(59,'Out',1,'In'),(82,'Out',84,'In'),(84,'Out',85,'In')]) and node(N,57)['payload']['type']['vehicle']==vid and node(N,57)['payload']['type']['enable']==1,{'enable':57,'mount':99,'objective':60,'quest':61,'AV_cleanup':85})
  item=87;johnny=[(40,'Out',50,'In'),(50,'Out',39,'In'),(39,'Out',43,'In'),(43,'Out',44,'In'),(44,'Out',93,'In'),(93,'Out',45,'In'),(45,'Out',46,'In'),(46,'Out',47,'In'),(47,'Out',48,'In')]
 check(s['id']+' native quantity-one keycard',any(value(x.get('itemID'))==s['item'] and x.get('quantity')==1 for x in typ(node(N,item)['payload'],'questAddRemoveItem_NodeTypeParams')),{'node':item,'item':s['item']})
 check(s['id']+' native supporting Johnny cleanup route connected',path_check(johnny),johnny)
 # Real-resource mutations are checked against independent native donor/route expectations.
 bad=copy.deepcopy(node(P,pn,'root/100')['payload']);bad['phaseResource']['DepotPath']['$value']='missing.questphase'
 check(s['id']+' mutation rejects wrong body donor',bad!=node(PAR,pn)['payload'],{'mutation':'wrong private body ref'})
 bad=copy.deepcopy(graph(P,'root/100'));bad['edges'].remove(['173','Out',str(pn),'In1'])
 check(s['id']+' mutation rejects disconnected native entry',['173','Out',str(pn),'In1'] not in bad['edges'],{'oracle':'connected native In1 predicate above','mutation':'removed edge'})
 bad=copy.deepcopy(node(P,3)['payload']['condition'])
 for x in typ(bad,'questJournalEntryState_ConditionType'):
  if x['path']['realPath']=='quests/minor_quest/'+s['id']:x['state']='Active'
 fs={x['factName']:x['value'] for x in typ(node(P,3)['payload']['condition'],'questVarComparison_ConditionType')};js={x['path']['realPath']:'Inactive' for x in typ(bad,'questJournalEntryState_ConditionType')};js['quests/minor_quest/'+s['id']]='Active'
 check(s['id']+' mutation catches active-owner admission',ev(bad,fs,js,{vid:False}) is True and ev(node(P,3)['payload']['condition'],fs,js,{vid:False}) is False,{'mutation':'root Inactive changed Active'})
 bad=copy.deepcopy(node(P,3)['payload']['condition']);v=typ(bad,'questVehicleAvailable_ConditionType')[0]
 for x in typ(bad,'questLogicalCondition'):
  if v in [y.get('type') for y in x.get('conditions',[])]:x['operation']='OR'
 check(s['id']+' mutation catches owned-car inversion',ev(bad,fs,{p:'Inactive' for p in js},{vid:True}) is True,{'mutation':'NOR availability replaced OR'})

script=PH3/'package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds';jv=PH3/'package/r6/scripts/PTFR_Consolidated/PTFR_JohnnyVoiceJV1.reds'
txt=script.read_text(encoding='utf-8-sig');jtxt=jv.read_text(encoding='utf-8-sig')
check('current S23 missing journals fail closed',('IsDefined(entry) ? EnumInt(jm.GetEntryState(entry)) : -1' in txt and 'if !a.valid || !b.valid' in txt and 'if this.Own(i, "Issued") == 0' in txt),{'script':str(script),'sha256':sha(script)})
check('current JV1 visual only supporting-voice policy',all(x in jtxt for x in ['TemporaryHide(true)','Character.Silverhand','actor.GetComponents()','this.CompletedTower()']) and 'SetFact' not in jtxt,{'script':str(jv),'sha256':sha(jv),'scope':'Code mechanism only; voice/rendering/camera focus behavior is LIVE_ONLY'})
trace={d:{'metadata':m['metadata'],'root_prefabs':m['root_prefabs'],'graphs':{gp:{'entries':g['entries'],'edges':g['edges'],'nodes':g['nodes']} for gp,g in m['graphs'].items()}} for d,m in models.items()}
write(O/'source_pins.json',pins);write(O/'graph_evidence.json',trace)
write(O/'tests.json',{'status':'PASS_SCOPED_STATIC_NOT_FULL_CERTIFICATION','count':len(checks),'checks':checks,'mutations':8,'runtime_changes':[],'script_inputs':[{ 'path':str(script),'sha256':sha(script)},{'path':str(jv),'sha256':sha(jv)}]})
write(O/'provider_requests.json',sorted(models))
print(json.dumps({'status':'PASS_SCOPED_STATIC_NOT_FULL_CERTIFICATION','checks':len(checks),'binary_pins':len(pins),'mutations':8}))
