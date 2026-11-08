"""Actual serialized MQ030 retirement/lease regression; no engine simulation claim."""
from pathlib import Path
import sys,copy,itertools
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;C=O/'candidate_01';R=C/'repair_mq030'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,walk
from model import Resource,compare_graph
T=R/'verification_01';assert not T.exists(),'Fresh test evidence required'
a=Resource(read(R/'before.json')).normalize();b=Resource(read(R/'after.json')).normalize();ag=a['graphs']['root'];bg=b['graphs']['root'];checks=[]
def check(name,ok,evidence):
 checks.append({'name':name,'status':'PASS' if ok else 'FAIL','evidence':evidence});assert ok,name
def eq(x,fs):
 t=x['$type']
 if t=='questFactsDBCondition':return eq(x['type'],fs)
 if t=='questLogicalCondition':
  v=[eq(y,fs) for y in x['conditions']];return any(v) if x['operation']=='OR' else all(v) if x['operation']=='AND' else False
 if t=='questVarComparison_ConditionType':
  n=fs[x['factName']];v=x['value'];return {'Equal':n==v,'Greater':n>v,'Less':n<v,'GreaterOrEqual':n>=v,'LessOrEqual':n<=v}[x['comparisonType']]
 raise ValueError(t)
def cond(m,g,i):return m['graphs'][g]['nodes'][str(i)]['payload']['condition']
F='PTFRS23_MQ030_Finished';D='cct_dtn_cloth_01_default_on'
def safe_topology(g):
 incoming={tuple(e) for e in g['edges'] if e[2]=='1012'}
 return incoming=={('1022','True','1012','In'),('1023','True','1012','In')} and ['1007','Out','1012','In'] not in g['edges']
check('defective_before_releases_lease_without_helper_retirement',not safe_topology(ag) and ['1007','Out','1012','In'] in ag['edges'],'Reproduced native-finished+default-on/helper-active overlap route')
check('serialized_after_release_only_ack_or_already_retired_wait',safe_topology(bg),'1022 from helper.Out1;1023 from pending wait after previous helper.Out1')
required=[['1020','Out1','1022','In'],['1022','False','1021','In'],['1021','Out','1023','In'],['1023','False','1020','In1']]
check('actual_rechecks_connected_in_both_owner_states',all(e in bg['edges'] for e in required),required)
check('native_helper_output_is_terminating',b['graphs']['root/1020']['nodes']['1']['payload']['type']=='Terminating' and ['3','Out','5','Inactive'] in b['graphs']['root/1020']['edges'] and ['5','Out','1','In'] in b['graphs']['root/1020']['edges'],'Native pause3 -> mappin5.Inactive -> Terminating1 -> outer1020.Out1')
check('new_node_ids_exact_and_collision_free',set(bg['nodes'])-set(ag['nodes'])=={'1022','1023'} and set(ag['nodes'])<=set(bg['nodes']),'All prior node IDs retained; additions local to this graph, not ArchiveXL injection IDs')
check('root_prefabs_references_and_metadata_retained',a['root_prefabs']==b['root_prefabs'] and a['metadata']==b['metadata'] and a['refs']==b['refs'],'No actor/prefab/resource rebind')
check('all_retained_nodes_unchanged_except_two_explicit_conditions',all(n==bg['nodes'][i] for i,n in ag['nodes'].items() if i!='1021') and all(a['graphs'][gp]['nodes'][i]==n for gp,g in b['graphs'].items() if gp!='root' for i,n in g['nodes'].items() if not(gp=='root/1020' and i=='3')),'No native body/reward/journal/actor writes altered')
check('nested_graphs_and_edges_retained',all(g['edges']==a['graphs'][gp]['edges'] for gp,g in b['graphs'].items() if gp!='root'),'Only root transition edges change')
for gp,i in [('root/1020','3'),('root','1021')]:
 old=cond(a,gp,i);new=cond(b,gp,i)
 check('explicit_OR_retains_original_condition_'+gp+'_'+i,new['$type']=='questLogicalCondition' and new['operation']=='OR' and old in new['conditions'] and len(new['conditions'])==2,'Original native condition OR real owned Finished==1')
for i in ['1022','1023']:
 check('new_decision_reads_real_finished_'+i,eq(cond(b,'root',i),{F:1}) and not eq(cond(b,'root',i),{F:0}),'No synthetic acknowledgement or native state manufactured')
fixtures=[]
for state,default,finished in itertools.product(['active_helper','pending_rearm'],[0,1],[0,1]):
 fs={D:default,F:finished}
 if state=='active_helper':
  before_wake=eq(cond(a,'root/1020',3),fs);after_wake=eq(cond(b,'root/1020',3),fs)
  result='retire_then_release' if after_wake and finished else 'retire_then_wait' if after_wake else 'continue_owned_helper'
  valid=after_wake if finished else after_wake==before_wake
 else:
  before_wake=eq(cond(a,'root',1021),fs);after_wake=eq(cond(b,'root',1021),fs)
  result='release_without_reenter' if after_wake and finished else 'reenter_with_lease' if after_wake else 'wait_with_lease'
  valid=after_wake if finished else after_wake==before_wake
 fixtures.append({'state':state,'default_on':default,'finished':finished,'old_wakeup':before_wake,'new_wakeup':after_wake,'authored_result':result})
 check('fixture_'+state+'_default'+str(default)+'_finished'+str(finished),valid,fixtures[-1])
check('finished_after_last_false_recheck_still_holds_lease',['1023','False','1020','In1'] in bg['edges'] and eq(cond(b,'root/1020',3),{D:1,F:1}),'One extra owned helper epoch may occur; actual Terminating output still precedes lease release')
for name in ['early_release','lost_helper_finished_wakeup','lost_pending_finished_wakeup']:
 if name=='early_release':
  bad=copy.deepcopy(bg);bad['edges'].append(['1007','Out','1012','In']);detected=not safe_topology(bad)
 elif name=='lost_helper_finished_wakeup':detected=not eq(cond(a,'root/1020',3),{D:1,F:1})
 else:detected=not eq(cond(a,'root',1021),{D:0,F:1})
 check('real_resource_mutation_detected_'+name,detected,'Counter-oracle is native retirement ordering and real guard evaluation, not agreement with a generated fixture')
check('no_serialized_graph_errors',not b['errors'],b['errors'])
patch=read(R/'patch.json')
write(T/'tests.json',{'status':'PASS_FAILING_BEFORE_PASSING_AFTER_SERIALIZED_REPAIR','count':len(checks),'checks':checks,'fixtures':fixtures,'mutations':3,'diff':compare_graph(a,b),'before_sha256':patch['before'],'after_sha256':patch['after'],'engine_boundary':'Native Terminating graph acknowledgement checked statically; no in-game teardown, interruption or saved-owner transition observed'})
prior=read(O/'approved_changes_01.json')
prior['resources'].append({'depot':patch['depot'],'before':patch['before'],'after':patch['after'],'evidence':str(O/'agents/agent_e/verification_02/defect_mq030.json'),'tests':str(T/'tests.json'),'independent_review':patch['review'],'intent':'Native helper retirement acknowledged before releasing shared vendor lease; pending wait and saved identifiers preserved'})
write(O/'approved_changes_02.json',prior)
print({'status':'PASS','checks':len(checks),'bounded_state_fixtures':len(fixtures),'mutations':3,'changed_resources':len(prior['resources'])})
