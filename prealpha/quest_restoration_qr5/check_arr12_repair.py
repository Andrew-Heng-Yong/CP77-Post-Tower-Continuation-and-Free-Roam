"""Actual serialized before/after ARR12 regression and preservation checks."""
from pathlib import Path
import sys,argparse,copy,collections
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk
from model import Resource,reachable

def run(out):
 assert not out.exists(),'Fresh output required'
 C=O/'candidate_01';R=C/'repair_arr12';plan=read(C/'repair_plan.json');patch=read(R/'patch.json');ep=read(O/'source_epoch_00.json')
 docs={k:read(R/(k+'.json'))for k in ['native','before','after']};models={k:Resource(d).normalize()for k,d in docs.items()};tests=[];mutations=[]
 def ck(name,ok,e):tests.append({'name':name,'status':'PASS'if ok else'FAIL','evidence':e});assert ok,name
 for k,m in models.items():ck('decoded_actual_readback '+k,not m['errors'],m['errors'])
 native=models['native'];before=models['before'];after=models['after'];g0=before['graphs']['root/10'];g=after['graphs']['root/10'];ng=native['graphs']['root/3'];monitor=after['graphs']['root/10/1202']
 def exact_monitor(m):
  if 'root/10/1202'not in m['graphs']:return False
  expected=copy.deepcopy(ng);expected['edges'].remove(['0','Out','15','In']);expected['edges'].append(['0','Out','13','In']);expected['edges'].sort()
  expected['reachable']=sorted(reachable(expected['nodes'],expected['edges'],expected['entries'].values()));expected['unreachable']=sorted(set(expected['nodes'])-set(expected['reachable']))
  if m['graphs']['root/10/1202']!=expected:return False
  return all(m['graphs'].get('root/10/1202'+p[len('root/3'):])==gr for p,gr in native['graphs'].items()if p.startswith('root/3/'))
 ck('failing_before_missing_future_consumer',not exact_monitor(before),{'expected':'FAIL_MISSING_NATIVE_MONITOR','source_sha256':patch['before']})
 ck('passing_after_exact_native_monitor_except_retired_prefix',exact_monitor(after),{'native_sha256':plan['native']['sha256'],'remove':['0','Out','15','In'],'add':['0','Out','13','In']})
 expected_edges=collections.Counter(map(tuple,g0['edges']));expected_edges[('65003','Out','8','In')]-=1;expected_edges+=collections.Counter([('65003','Out','1200','In'),('1200','True','1201','In'),('1201','Out','1202','In1'),('1201','Out','8','In')])
 ck('only_approved_parent_edge_delta',collections.Counter(map(tuple,g['edges']))==expected_edges,'One removed, four added')
 ck('only_three_new_local_ids',set(g['nodes'])==set(g0['nodes'])|{'1200','1201','1202'},list(set(g['nodes'])-set(g0['nodes'])))
 for gp,gr in before['graphs'].items():
  if gp=='root/10':
   for ident,n in gr['nodes'].items():ck('old_node_payload_identity_sockets '+ident,g['nodes'][ident]==n,{'graph':gp,'node':ident})
  else:ck('unchanged_old_graph '+gp,after['graphs'][gp]==gr,gp)
 for key in ['type','metadata','metadata_sha256','root_prefabs','embedded_files']:ck('unchanged_resource_metadata '+key,after[key]==before[key],key)
 expected_outer=copy.deepcopy(native['graphs']['root']['nodes']['3']);expected_outer['id']='1202';expected_outer['payload']['id']=1202
 ck('exact_native_outer_phase_metadata',all(g['nodes']['1202'][k]==v for k,v in expected_outer.items()if k!='payload_sha256'),'Only outer node ID3→1202')
 guard=g['nodes']['1200'];reads=guard['reads'];want=plan['guard_facts'];condition=guard['payload']['condition']
 ck('exact_immediate_AND_guard',guard['type']=='questConditionNodeDefinition' and condition['operation']=='AND' and len(reads)==len(want)and {r['factName']:r['value']for r in reads}==want and all(r['comparisonType']=='Equal'for r in reads),want)
 ck('future_only_guard_ingress',[e for e in g['edges']if e[2]=='1200']==[['65003','Out','1200','In']]and not[e for e in g['edges']if e[0]=='1200'and e[1]=='False'],'No new poll/onattach/retry or false path')
 def admit(f,event=True):return event and all(f.get(k,0)==v for k,v in want.items())
 for arm in [0,1]:ck('legitimate_old_arm_history '+str(arm),admit(want|{'arr_12_fail_loop_start':arm}),{'arm':arm,'native_arm_not_modified':True})
 ck('old_receipts_without_future_event_do_not_adopt',not admit(want,False),'Fixture models actual event requirement, not engine scheduling')
 for key,v in want.items():ck('changed_guard_refuses '+key,not admit(want|{key:1-v}),{'expected':v})
 ck('absent_positive_provenance_rejects_as_zero',all(not admit({k:v for k,v in want.items()if k!=key})for key,v in want.items()if v==1),'Absent expected0 is accepted; not historical proof')
 ck('owned_claim_only',g['nodes']['1201']['writes']==[{'$type':'questSetVar_NodeType','factName':plan['claim_fact'],'setExactValue':1,'value':1}],plan['claim_fact'])
 ck('old_arm_nodes_preserved_but_unreachable',all(monitor['nodes'][i]==ng['nodes'][i]for i in ['14','15'])and not {'14','15'}&set(monitor['reachable']),'No reset/write of old arm receipt can execute from new input')
 ck('native_failure_writer_dominates_reward_and_end',not {'20','22'}&reachable(monitor['nodes'],[e for e in monitor['edges']if e[0]!='8'and e[2]!='8'],['0']),'All static routes to followup/reward pass native failed1 producer8; native scene conditions separately reviewed')
 ck('monitor_has_no_added_prefab_lease',not g['nodes']['1202']['prefabs']and all(not n['prefabs']for gp,gr in after['graphs'].items()if gp.startswith('root/10/1202')for n in gr['nodes'].values()),'Existing exact native main support stays unchanged; placement not decoded')
 def raw_node(doc,ids):
  rr=Resource(doc);gr=rr.d(rr.root['graph'])
  for ident in ids:
   n=next(rr.d(h)for h in gr['nodes']if rr.d(h)['id']==ident)
   if 'phaseGraph'in n:gr=rr.d(n['phaseGraph'])
  return rr,n
 cases=[('lost_native_failed_flag',[10,1202,8],lambda n,r:r.d(n['type']).__setitem__('value',0)),('changed_native_terminating_output',[10,1202,1],lambda n,r:n.__setitem__('type','Exit')),('changed_native_reward_exclusion',[10,1202,25],lambda n,r:r.d(r.d(n['condition'])['type']).__setitem__('value',1))]
 for label,ids,edit in cases:
  bad=copy.deepcopy(docs['after']);rr,n=raw_node(bad,ids)
  edit(n,rr)
  detected=not exact_monitor(Resource(bad).normalize());mutations.append({'fault':label,'detected':detected});ck('raw_mutation '+label,detected,ids)
 # Native32 cancellation uses condition8 -> terminating output9, not cut sockets.
 bad=copy.deepcopy(docs['after']);rr,n=raw_node(bad,[10,1202,32]);nested=rr.d(n['phaseGraph']);rr,cleanup=raw_node(bad,[10,1202,32,8]);edge_handles=[]
 for sh in cleanup['sockets']:
  sock=rr.d(sh)
  if sock['name'].get('$value')=='Out':edge_handles.extend(rr.hid(ch)for ch in sock.get('connections',[]))
 ck('native_nested_cleanup_connection_exists',len(edge_handles)==1,'Raw32:8.Out→9.In is the mutation target')
 selected=edge_handles[0]
 for h in nested['nodes']:
  for sh in rr.d(h).get('sockets',[]):
   sock=rr.d(sh);sock['connections']=[ch for ch in sock.get('connections',[])if rr.hid(ch)!=selected]
 detected=not exact_monitor(Resource(bad).normalize());mutations.append({'fault':'missing_raw_nested_cleanup_connection','detected':detected});ck('raw_mutation_nested_cleanup',detected,selected)
 expected=dict(ep['source_resources']);expected[plan['depot']]=patch['after'];actual={str(f.relative_to(C/'archive_source')):sha(f)for f in (C/'archive_source').rglob('*')if f.is_file()}
 ck('exact_single_resource_source_delta',actual==expected,{'source_count':len(actual),'changed':[d for d,h in actual.items()if h!=ep['source_resources'].get(d)]})
 ck('all_four_prior_repairs_preserved',all(actual[r['depot']]==r['after']for r in ep['prior_repairs']),ep['prior_repairs'])
 ck('actual_after_hash_matches_receipt',sha(C/'archive_source'/plan['depot'])==patch['after'],patch['after'])
 inputs=[Path(__file__),C/'repair_plan.json',R/'patch.json',R/'native.json',R/'before.json',R/'after.json',Path(plan['review']),Path(plan['proposal']),O/'source_epoch_00.json']
 report={'status':'PASS_ACTUAL_SERIALIZED_ARR12_FUTURE_EVENT_REPAIR','checks':len(tests),'tests':tests,'mutations':mutations,'before':'EXPECTED_FAIL_MISSING_NATIVE_MONITOR','after':'PASS_EXACT_REVIEWED_MONITOR_WITH_PRIVATE_FUTURE_GUARD','input_pins':{str(p):sha(p)for p in inputs},'limits':['No old already-Entered/Started adoption; native arm0/1 accepted unchanged.','NodeRef placement/engine fanout, interruption, reload and outcome execution remain live/opaque.','Exact failure/reward payload preservation is proven; source condition/dominance and scene AND-pulse proof are separately reviewed, not an engine simulation.'],'game_writes':0,'save_writes':0}
 write(out/'tests.json',report);return {'status':report['status'],'checks':len(tests),'mutations':len(mutations)}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();print(run(Path(a.output).resolve()))
