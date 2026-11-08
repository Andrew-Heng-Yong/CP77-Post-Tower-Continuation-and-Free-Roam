"""Failing-before/passing-after checks for the excluded-Dumpster admission leak."""
from pathlib import Path
import sys,copy
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;C=O/'candidate_01'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk
from model import Resource,compare_graph,reachable
target=C/'repair/verification_01';assert not target.exists(),'Fresh verification output required'
a=Resource(read(C/'repair/before.json')).normalize();b=Resource(read(C/'repair/after.json')).normalize()
ag=a['graphs']['root'];bg=b['graphs']['root'];tests=[]
def check(name,ok,evidence):
 tests.append({'name':name,'status':'PASS' if ok else 'FAIL','evidence':evidence});assert ok,name
def reach(g,seeds):return reachable(g['nodes'],g['edges'],seeds)
def policy_ok(g):return '34' not in reach(g,[g['entries']['In1']]) and '1005' not in reach(g,[g['entries']['In1']])
check('defective_baseline_fails_scope_safety',not policy_ok(ag),'Current PH3 new input reaches Issued1005 and nativefullIn1 node34')
check('serialized_repair_passes_scope_safety',policy_ok(bg),'New input cannot claim Issued or enter full native chain')
check('existing_refused_receipt_reachable','1008' in reach(bg,[bg['entries']['In1']]),bg['nodes']['1008']['writes'])
check('only_exact_preclaim_edge_removed',set(map(tuple,ag['edges']))-set(map(tuple,bg['edges']))=={('1004','True','1005','In')},'1004.True ->1005.In')
check('only_exact_refusal_edge_added',set(map(tuple,bg['edges']))-set(map(tuple,ag['edges']))=={('1004','True','1008','In')},'1004.True ->1008.In')
check('all_saved_node_payloads_and_socket_identities_unchanged',ag['nodes']==bg['nodes'],sorted(ag['nodes']))
check('root_metadata_prefabs_and_references_unchanged',a['metadata']==b['metadata'] and a['refs']==b['refs'] and a['root_prefabs']==b['root_prefabs'],'No resource/node/field/prefab identifier renamed')
check('no_serialized_graph_errors',not a['errors'] and not b['errors'],[a['errors'],b['errors']])
for i in ['1005','1006','34']:
 check('saved_descendant_reachability_preserved_'+i,reach(ag,[i])==reach(bg,[i]),sorted(reach(bg,[i])))
# Actual serialized preclaim condition is still the same native/history seam;
# the quarantine does not forge a new eligibility predicate or completion.
def evaluate(x,fs,js):
 t=x.get('$type')
 if t=='questLogicalCondition':
  vs=[evaluate(y,fs,js) for y in x['conditions']]
  return all(vs) if x['operation']=='AND' else any(vs) if x['operation']=='OR' else not any(vs) if x['operation']=='NOR' else False
 if t in ('questFactsDBCondition','questJournalCondition'):return evaluate(x['type'],fs,js)
 if t=='questVarComparison_ConditionType':
  if x['factName'] not in fs:return False
  n=fs[x['factName']];v=x['value'];return {'Equal':n==v,'NotEqual':n!=v,'Greater':n>v,'Less':n<v,'GreaterOrEqual':n>=v,'LessOrEqual':n<=v}[x['comparisonType']]
 if t=='questJournalEntryState_ConditionType':
  p=x['path']['realPath']
  return p in js and ((js[p]==x['state'])!=bool(x.get('inverted',0)))
 raise ValueError('Unsupported condition '+str(t))
cond=ag['nodes']['1004']['payload']['condition']
fs={x['factName']:x['value'] for x in walk(cond) if x.get('$type')=='questVarComparison_ConditionType'}
js={x['path']['realPath']:'Inactive' for x in walk(cond) if x.get('$type')=='questJournalEntryState_ConditionType'}
check('baseline_guard_accepts_excluded_fresh_seam',evaluate(cond,fs,js),{'journal_entries':len(js),'state':'Inactive','predicate':'actual serialized condition'})
dumpster='quests/minor_quest/mq037_brendan_dumpster'
check('earned_dumpster_is_already_unsupported_by_original_guard',not evaluate(cond,fs,js|{dumpster:'Succeeded'}),'Do not label this containment as removal of a proven valid earned-history adapter')
policy=read(W/'research/gig_restoration/lore_whitelists_v6_2_sidejobs.json')
matches=[r for r in walk(policy) if r.get('id')=='mq037_brendan_dumpster']
check('current_selection_explicitly_excludes_fresh_dumpster',len(matches)==1 and matches[0]['decision']=='EXCLUDE' and matches[0]['new_runtime_admission'] is False,matches)
for name,edge in [('restore_leaking_edge',['1004','True','1005','In']),('also_connect_native_owner',['1008','Out','34','In1'])]:
 bad=copy.deepcopy(bg)
 if name=='restore_leaking_edge':bad['edges'].remove(['1004','True','1008','In'])
 bad['edges'].append(edge)
 check('mutation_detected_'+name,not policy_ok(bad),'Actual repaired graph mutated in memory; source files untouched')
patch=read(C/'repair/patch.json');diff=compare_graph(a,b)
write(target/'tests.json',{'status':'PASS_FAILING_BEFORE_PASSING_AFTER_SERIALIZED_REPAIR','checks':tests,'count':len(tests),'baseline_scope_check':'FAIL_REPRODUCED','repaired_scope_check':'PASS','mutations':2,'semantic_diff':diff,'source_before_sha256':patch['before'],'source_after_sha256':patch['after'],'policy_sha256':sha(W/'research/gig_restoration/lore_whitelists_v6_2_sidejobs.json'),'live_limits':['Already-issued or already-passed preclaim saved execution is not reversed','Fact-node branch ending, mid-node save transitions and actor behavior require engine fixtures','Later earned-history sequel adapter remains unsupported; no native history is invented']})
write(O/'approved_changes_01.json',{'resources':[{'depot':patch['depot'],'before':patch['before'],'after':patch['after'],'evidence':str(O/'agents/agent_c/verification_02/defects.json'),'tests':str(target/'tests.json'),'independent_review':str(O/'agents/agent_b/reviews/brendan_quarantine.json'),'intent':'Contain invalid fresh excluded activation; preserve saved descendants, not a claim of restored sequels'}]})
print({'status':'PASS','checks':len(tests),'defective_baseline':'FAIL_REPRODUCED','serialized_repair':'PASS','changed_resources':1})
