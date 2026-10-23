"""DT1 native checkpoint admission and direct-stock payload tests, not a live pass."""
import copy, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(Path(__file__).parent))
from research import graphs,walk,value,read
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def nodes(g):return {n['id']:n for n in g['nodes']}
def evaluate(c,s,outside=True,combat=False):
 t=c['$type']
 if t=='questLogicalCondition':return all(evaluate(x,s,outside,combat) for x in c['conditions'])
 if t=='questTriggerCondition':return outside
 if t=='questCharacterCondition':return not combat
 assert t=='questFactsDBCondition'
 p=c['type'];a=s.get(p['factName'],0);b=p['value'];return {'Equal':a==b,'Greater':a>b}[p['comparisonType']]
def run(build):
 m=read(build/'component.json');assert m['status']=='BUILT_DT1_GATE_LIVE_PENDING'
 for p,h in m['source_pins'].items():assert sha(ROOT/p)==h,p
 assert {'prealpha/ncpd_scanner_n1/native_inspect.py','tools/audit_activity_batches_b1.py','tools/catalog_gig_rollout_r2.py','tools/test_gig_pilot_r1.py'}<=set(m['source_pins'])
 assert len(m['resources'])==1 and len(m['boots'])==1 and m['official_overrides']==[]
 assert m['changed_native_edges']==[] and m['changed_native_properties']==[] and m['runtime_scripts_added']==0
 for p,h in m['resources'].items():assert sha(build/'source'/p)==h,p
 bg=graphs(build/'readback/gate_boot.json');assert set(bg)=={'root'}
 n=nodes(bg['root']);assert set(n)==set(range(6))
 assert set(map(tuple,bg['root']['edges']))=={(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'False',2,'In'),(3,'True',4,'In'),(4,'Out',5,'In1')}
 native=graphs(ROOT/m['official_sources'][0]['json'])['root'];p=copy.deepcopy(nodes(native)[13]);p['id']=5
 assert n[5]==p,'Original parent phase payload changed'
 assert (0,'Out',26,'In1') in map(tuple,native['edges']) and (26,'Out1',13,'In1') in map(tuple,native['edges'])
 ep1=graphs(ROOT/m['official_sources'][2]['json'])['root/10'];en=nodes(ep1)
 assert en[5]['phaseResource']['DepotPath']['$value']=='ep1\\openworld\\ep1_open_world.questphase'
 assert en[9]['$type']=='questCutControlNodeDefinition'
 assert {(8,'Out',9,'In'),(9,'CutSource',5,'CutDestination'),(9,'Out',10,'In')}<=set(map(tuple,ep1['edges']))
 assert en[10]['type']['factName']=='q307_ep1_killed' and en[10]['type']['value']==1
 assert any(x.get('type',{}).get('state')=='Succeeded' and x['type']['path']['realPath']=='ep1/quests/main_quest/q307_before_tomorrow' for x in en[8]['condition']['conditions'])
 stock=graphs(ROOT/m['official_sources'][1]['json']);sn=nodes(stock['root'])
 assert n[2]['condition']==n[3]['condition']
 c=n[2]['condition'];terms=c['conditions'];facts=[x['type'] for x in terms if x['$type']=='questFactsDBCondition']
 expected={'PostTowerFreeRoamActive':1,'PTFRP0_DR13':1,'PTFRPA2_Finished':1,'PTFRPA2_Fault':0,'q307_done':1,'q307_finished':1,'q307_2079':1,'q307_main_game_killed':1,'q307_ep1_killed':1,'q307_active':0,'q307_debug_reset':0,'q115_point_of_no_return':0,'q305_johnny_scene_active':0,'PTFRDT1_GateIssued':0,'q304_block_dogtown_gate':0,'wanted_level':0}
 assert m['guard_equal']==expected and m['guard_positive']==['ep1_side_content','q302_started']
 assert sorted((x['factName'],x['comparisonType'],x['value']) for x in facts)==sorted([(k,'Equal',v) for k,v in expected.items()]+[(k,'Greater',0) for k in m['guard_positive']])
 outside=nodes(stock['root/7'])[6]['condition'];no_combat=[x for x in sn[177]['condition']['conditions'] if x['$type']=='questCharacterCondition'][0]
 assert [x for x in terms if x['$type']=='questTriggerCondition']==[outside]
 assert [x for x in terms if x['$type']=='questCharacterCondition']==[no_combat]
 good=expected|{k:1 for k in m['guard_positive']};assert evaluate(c,good)
 cases=1
 for key,v in expected.items():
  for wrong in [-1,0,1,2]:
   if wrong!=v:assert not evaluate(c,good|{key:wrong}),(key,wrong);cases+=1
 for key in m['guard_positive']:
  for wrong in [-1,0]:assert not evaluate(c,good|{key:wrong});cases+=1
 assert not evaluate(c,good,outside=False) and not evaluate(c,good,combat=True);cases+=2
 # Earned story flags are only read. Native scanning/lockdown/lane branch payloads are untouched.
 writes=[x['type'] for x in n.values() if x['$type']=='questFactsDBManagerNodeDefinition']
 assert [(x['factName'],x['value'],x['setExactValue']) for x in writes]==[('PTFRDT1_GateReady',1,1),('PTFRDT1_GateIssued',1,1)]
 assert (5,'Out',7,'In1') in map(tuple,stock['root']['edges']) and (7,'Out1',181,'In') in map(tuple,stock['root']['edges'])
 assert nodes(stock['root/7'])[26]['condition']['type']=={'$type':'questVarComparison_ConditionType','comparisonType':'GreaterOrEqual','factName':'q302_started','value':1}
 assert (26,'Out',27,'In2') in map(tuple,stock['root/7']['edges']) and (27,'Out1',1,'In') in map(tuple,stock['root/7']['edges'])
 assert nodes(stock['root/7'])[1]['type']=='Terminating'
 assert sn[181]['actions'][0]['type']['action']=='Deactivate'
 for path,nodeids in [('root/3',[57,58]),('root/4',[16,17])]:
  for nodeid in nodeids:assert nodes(stock[path])[nodeid]['condition']['type']['factName']=='q304_block_dogtown_gate'
 assert all(p in stock for p in ['root/3/45','root/3/54','root/4/6','root/4/8'])
 # Same controller owns checkpoint guard escalation. Missing it loses both the
 # scan/open path and the native three-star response to checkpoint combat.
 combat_graph=stock['root/105'];cn=nodes(combat_graph);ce=set(map(tuple,combat_graph['edges']))
 assert cn[2]['condition']['type']['deviceConditionFunction']['$value']=='IsSystemInCombat'
 assert cn[2]['condition']['type']['objectRef']['$value']=='#combat_zone_gate_dvc_security_system'
 assert cn[3]['condition']['operation']=='OR'
 guards=cn[3]['condition']['conditions'];assert len(guards)==29
 assert all(x['type']['$type']=='questCharacterCombat_ConditionType' and x['type']['inverted']==0 and x['type']['objectRef']['reference']['$value']=='#combat_zone_gate_com' for x in guards)
 assert {(0,'Out',2,'In'),(0,'Out',3,'In'),(2,'Out',4,'In1'),(3,'Out',4,'In2'),(4,'Out1',10,'In'),(10,'True',5,'In')}<=ce
 assert cn[10]['condition']['type']=={'$type':'questVarComparison_ConditionType','comparisonType':'Less','factName':'wanted_level','value':3}
 assert cn[5]['managerName']=='PreventionSystem' and cn[5]['event']['$type']=='SetWantedLevel' and cn[5]['event']['wantedLevel']=='Heat_3'
 assert {(103,'Out',190,'In'),(190,'Out',105,'In1'),(105,'Out1',191,'In'),(191,'Out',123,'Inactive')}<=set(map(tuple,stock['root']['edges']))
 # Normal lane entry accepts Driving rather than a particular car model, so
 # native vehicle contracts use this same path. No courier exclusivity reset.
 for lane in ['root/4/6','root/4/8']:
  checks=[x for n2 in stock[lane]['nodes'] for x in walk(n2.get('condition',{}))]
  assert any(x.get('vehicleState')=='Driving' for x in checks)
  assert not any('courier' in str(x.get('factName','')).lower() for x in checks)
 resources={value(x) for x in walk(read(ROOT/m['official_sources'][1]['json'])) if x.get('$type')=='ResourcePath'}
 assert resources=={'0'},resources
 result={'status':'PASS_OFFLINE_NOT_LIVE','component_sha256':sha(build/'component.json'),'test_source_sha256':sha(__file__),'admission_cases':cases,'stock_graphs':len(stock),'stock_nodes_audited':sum(len(g['nodes']) for g in stock.values()),'source_pins':len(m['source_pins']),'native_writes_added':0,'live_crossing_verified':False}
 (build/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':run(Path(sys.argv[1]))
