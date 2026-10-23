"""Independent artifact, native-boundary, negative-admission and lifecycle checks."""
import copy, json, sys, binascii
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'prealpha/courier_c1'),str(ROOT/'prealpha/ncpd_scanner_n1'),str(ROOT/'tools')]
from native_inspect import SafeResource
from audit_activity_batches_b1 import flatten
from catalog_gig_rollout_r2 import read,sha,walk,value
from research import resources
IDS={3,15,21,22,23,25,26,27,28,29,30,33,34,35,36,37,38,41,42,43,44,45,46,47,48}
COMMON={'PostTowerFreeRoamActive':1,'PTFRP0_DR13':1,'PTFRPA2_Finished':1,'PTFRPA2_Fault':0,'q307_done':1,'q307_finished':1,'q307_2079':1,'q307_main_game_killed':1,'q307_ep1_killed':1,'q307_active':0,'q307_debug_reset':0,'q115_point_of_no_return':0,'q305_johnny_scene_active':0,'PTFRU9_Support_Issued':1,'PTFRU9_Support_Fault':0}
ACTIVE=['sa_ep1_couriers_active','sa_ep1_courier_car_mounted_1st_time','sa_ep1_courier_hacking_mounted_1st_time','sa_ep1_courier_hacking_mission_active','sa_ep1_courier_introduction_quest_active','sa_ep1_courier_outro_active','sa_ep1_courier_loop_blocked_by_outro','sa_ep1_courier_force_despawn_and_block','sa_ep1_courier_holocall_status_active','sa_ep1_courier_external_tests','sa_ep1_courier_retrofixing_fullreset','sa_ep1_courier_retrofixing_killallsignals','sa_ep1_courier_retrofixing_killdistrictssignal','sa_ep1_courier_retrofixing_killmainphase','sa_ep1_courier_retrofixing_killloopphase','sa_ep1_courier_retrofixing_signal_inject','sa_ep1_courier_retrofixing_reactivate_signal']
POS=['ep1_installed','ep1_active','ep1_side_content']
def graph(path):
 r=SafeResource(read(path));return r,{g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
def nodes(g):return {n['id']:n for n in g['nodes']}
def edges(g):return {tuple(e) for e in g['edges']}
def evaluate(c,state):
 if c['$type']=='questLogicalCondition':
  vals=[evaluate(x,state) for x in c['conditions']]
  return all(vals) if c['operation']=='AND' else any(vals)
 assert c['$type']=='questFactsDBCondition',c
 t=c['type'];op=t['comparisonType']
 a=state.get(t.get('factName',t.get('factName1')),0)
 b=state.get(t['factName2'],0) if 'factName2' in t else t['value']
 return {'Equal':a==b,'NotEqual':a!=b,'Greater':a>b,'GreaterOrEqual':a>=b,'Less':a<b,'LessOrEqual':a<=b}[op]
def terms(c):return [(x['type']['factName'],x['type']['comparisonType'],x['type']['value']) for x in c['conditions'] if x['$type']=='questFactsDBCondition' and x['type']['$type']=='questVarComparison_ConditionType']

def verify(build):
 m=read(build/'build.json');assert m['status']=='BUILT_C1_LIVE_PENDING'
 assert len(m['resources'])==3 and len(m['files'])==2 and len(m['boots'])==2
 assert m['packed_readback'] and m['native_scenes_unchanged'] and m['runtime_scripts_added']==0 and not m['official_overrides']
 assert m['mod_override']==r'towercontinued\gig_phone_u9\fixer_cleanup.questphase'
 for f in m['files']:assert sha(build/Path(f['relative']).name)==f['sha256']
 for p,h in m['source_pins'].items():assert sha(ROOT/p)==h,p
 for p,h in m['resources'].items():assert sha(build/'source'/p)==h
 nr,ng=graph(ROOT/(m['parent_source'].replace('/raw/','/json/')+'.json'))
 pr,pg=graph(build/'readback/courier.json');pn=nodes(pg['root']);on=nodes(ng['root'])
 assert set(pn)==IDS|{1000,1001,1002,1003,1004}
 for i in IDS:assert pn[i]==on[i],('stock payload',i)
 native_edges={e for e in edges(ng['root']) if e[0] in IDS and e[2] in IDS}
 added={(1000,'Out',1001,'In'),(1001,'Out',1002,'In'),(1002,'Out',1003,'In'),(1003,'False',1002,'In'),(1003,'True',1004,'In'),(1004,'Out',3,'start'),(1004,'Out',15,'In1')}
 assert edges(pg['root'])==native_edges|added
 assert set(pg)=={'root','root/15'} and not pg['root/15']['nodes']
 assert pn[3]['phaseResource']['DepotPath']['$value']==r'ep1\openworld\sandbox_activities\courier_sandbox_activity.questphase'
 assert pn[1002]['condition']==pn[1003]['condition']
 eq=COMMON|{'PTFRC1_Support_Issued':1,'PTFRC1_Issued':0}|dict.fromkeys(ACTIVE,0)
 assert sorted(terms(pn[1002]['condition']))==sorted([(k,'Equal',v) for k,v in eq.items()]+[(k,'Greater',0) for k in POS])
 good=eq|dict.fromkeys(POS,1);c=pn[1002]['condition'];assert evaluate(c,good)
 negatives=0
 for k,v in eq.items():assert not evaluate(c,good|{k:1-v}),k;negatives+=1
 for k in POS:assert not evaluate(c,good|{k:0}),k;negatives+=1
 intro='sa_ep1_courier_introduction_quest_';outro='sa_ep1_courier_outro_'
 # Fresh onboarding, completed onboarding, no replay/migration of partial stories.
 assert evaluate(c,good|{intro+'started':1,intro+'finished':1})
 assert not evaluate(c,good|{intro+'started':1,intro+'finished':0})
 assert not evaluate(c,good|{outro+'available':1})
 assert evaluate(c,good|{outro+'available':1,outro+'finished':1})
 assert evaluate(c,good|{outro+'available':1,outro+'failed':1})
 # Save/reload admission is one-shot, not a per-session restart.
 assert not evaluate(c,good|{'PTFRC1_Issued':1})
 for i,f in [(1001,'PTFRC1_Ready'),(1004,'PTFRC1_Issued')]:assert pn[i]['type']=={'$type':'questSetVar_NodeType','factName':f,'setExactValue':1,'value':1}
 sr,sg=graph(build/'readback/support.json');sn=nodes(sg['root'])
 ir,ig=graph(ROOT/(m['support_init'].replace('/raw/','/json/')+'.json'))
 assert set(sn)=={0,1,2,3,4,22} and sn[22]==nodes(ig['root'])[22]
 assert edges(sg['root'])=={(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'False',2,'In'),(3,'True',4,'In'),(4,'Out',22,'In1')}
 assert sn[2]['condition']==sn[3]['condition']
 sc=sn[2]['condition'];sp=m['support_guard'];assert all(sp.get(k)==v for k,v in COMMON.items())
 assert sorted(terms(sc))==sorted([(k,'Equal',v) for k,v in sp.items()]+[(k,'Greater',0) for k in POS])
 ps=sp|dict.fromkeys(POS,1);assert evaluate(sc,ps)
 for k,v in sp.items():assert not evaluate(sc,ps|{k:1-v}),k;negatives+=1
 for start,end in m['support_balances']:
  assert evaluate(sc,ps|{start:7,end:7}) and not evaluate(sc,ps|{start:8,end:7});negatives+=1
 # Cleanup retains every previous N1/fixer node and the native timeout.
 _,old=graph(ROOT/'prealpha/ncpd_scanner_n1/build/n1_01/readback/fixer_cleanup.json')
 _,new=graph(build/'readback/fixer_cleanup.json');nn=nodes(new['root']);oo=nodes(old['root'])
 _,ep=graph(ROOT/(m['cleanup_source'].replace('/raw/','/json/')+'.json'))
 assert set(nn)==set(oo)|{600,601}
 for k,n in oo.items():assert nn[k]==n
 for new_id,old_id in [(600,84),(601,83)]:
  want=copy.deepcopy(nodes(ep['root'])[old_id]);want['id']=new_id;assert nn[new_id]==want
 want=edges(old['root'])-{(424,'Out1',6,'In2')}
 want|={(424,'Out1',600,'In'),(600,'True',601,'In1'),(600,'False',6,'In2'),(601,'Out1',6,'In2')}
 assert edges(new['root'])==want
 assert set(new)=={'root','root/601'}
 assert nodes(new['root/601'])==nodes(ep['root/83']) and edges(new['root/601'])==edges(ep['root/83'])
 # Native dependency closure and progression gates: originals are referenced,
 # not packed/edited, and the one-time stories retain their stock decisions.
 rs=resources();missing=set();scenes=[]
 for depot,p in rs.items():
  if 'courier' not in depot and 'officer_daniels' not in depot:continue
  obj=read(p)
  for x in walk(obj):
   if x.get('$type')=='ResourcePath' and x.get('$storage')=='string':
    ref=x.get('$value','')
    if ref.endswith(('.questphase','.scene')) and ref not in rs:missing.add(ref)
  if depot.endswith('.scene'):
   actors=[a['actorName'] for a in obj['Data']['RootChunk'].get('actors',[])]
   assert not any(x.lower() in ('panam','judy','kerry') for x in actors),(depot,actors)
   for actor in obj['Data']['RootChunk'].get('actors',[]):
    if actor['actorName'].lower()=='johnny':
     assert actor['acquisitionPlan']=='spawnDespawn'
     assert actor['spawnDespawnParams']['specRecordId']['$value']=='Character.Silverhand'
   scenes.append({'resource':depot,'actors':actors})
 assert not missing,missing
 _,root=graph(rs[r'ep1\openworld\sandbox_activities\courier_sandbox_activity.questphase'])
 cond=nodes(root['root'])[130]['condition']
 state={outro+'finished':0,outro+'failed':0,outro+'available':0,'sa_ep1_courier_succesfull_deliveries':7}
 assert evaluate(cond,state)
 for fact in (outro+'finished',outro+'failed',outro+'available'):assert not evaluate(cond,state|{fact:1});negatives+=1
 assert not evaluate(cond,state|{'sa_ep1_courier_succesfull_deliveries':6})
 # Native entry initializes ready_to_start; we do not claim exact old timer
 # restoration. Native cooldown loops and counters remain in their resource.
 assert nodes(root['root'])[85]['type']['factName']=='sa_ep1_courier_ready_to_start'
 ids=[binascii.crc_hqx((p+':1').encode(),0xffff) for p in m['boots']]
 assert len(set(ids))==2 and not set(ids)&{r['id'] for r in m['installed_injections']}
 stock=read(ROOT/'research/q307_extracted/json/ep1/quest/ep1.quest.json')
 assert not set(ids)&{n['Data']['id'] for n in stock['Data']['RootChunk']['graph']['Data']['nodes']}
 xl=(build/'00_TowerContinued_Courier_C1.archive.xl').read_text()
 assert xl.count('    - path: ')==2 and xl.count('      parent: ep1\\quest\\ep1.quest')==2
 assert xl.count('        node: [1]')==2 and xl.count('        socket: Out')==2
 for p in m['boots']:assert xl.count('    - path: '+p+'\n')==1
 return {'status':'PASS_NOT_LIVE','build_sha256':sha(build/'build.json'),'tester_sha256':sha(Path(__file__)),'native_nodes_exact':len(IDS)+1+len(oo)+2+len(nodes(ep['root/83'])),'negative_admission_cases':negatives,'native_phase_scene_closure':len(rs),'scene_cast':scenes,'native_payload_edges_preserved':True,'existing_ncpd_cleanup_preserved':True,'no_preending_or_issued_readmission':True,'limitations':['No live car spawn/call/delivery/reward/cooldown/reload or future story validation.','Native entry sets ready_to_start; it does not reconstruct the exact remaining pre-Tower timer.','Partial pre-Tower contracts and unfinished one-time stories are not migrated.']}

if __name__=='__main__':
 build=ROOT/'prealpha/courier_c1/build'/sys.argv[1];out=build/'tests.json';assert not out.exists()
 result=verify(build);out.write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in result.items() if k!='scene_cast'},indent=2))
