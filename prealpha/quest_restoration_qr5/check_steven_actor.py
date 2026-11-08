"""Actual staged actor-helper graph, refusal, choice and preservation regression."""
from pathlib import Path
import sys,argparse,copy,collections
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk
from model import Resource,reachable

def run(out):
 assert not out.exists();C=O/'candidate_02';R=C/'repair_steven';plan=read(C/'actor_repair_plan.json');p=read(plan['proposal']);patch=read(R/'patch.json');docs={k:read(R/(k+'.json'))for k in ['before','after','template']};M={k:Resource(d).normalize()for k,d in docs.items()};tests=[];mut=[]
 def ck(n,ok,e):tests.append({'name':n,'status':'PASS'if ok else'FAIL','evidence':e});assert ok,n
 for k,m in M.items():ck('actual_decoded '+k,not m['errors'],m['errors'])
 before=M['before'];after=M['after'];tpl=M['template'];g=after['graphs']['root/50'];old=before['graphs']['root/50'];hg=after['graphs']['root/50/1302'];tg=tpl['graphs']['root/100']
 def valid_helper(m):
  if 'root/50/1302'not in m['graphs']:return False
  q=m['graphs']['root/50/1302'];return set(q['nodes'])=={'0','17','19','1303'}and all(q['nodes'][i]==tg['nodes'][i]for i in ['0','17','19'])and q['edges']==sorted([['0','Out','19','In'],['19','Out','1303','In'],['1303','Out','17','In1'],['17','Out1','19','In']])
 ck('baseline_missing_future_actor_owner',not valid_helper(before),{'expected':'FAIL_MISSING_U9_ACTOR_OWNER','before':patch['before']})
 ck('after_actor_only_exact_native_loop',valid_helper(after),'No501 message/timer subtree or unrelated native owner')
 # Socket names already strings; convert only node IDs in the JSON proposal.
 def edge(e):return (str(e[0]),e[1],str(e[2]),e[3])
 expected=collections.Counter(map(tuple,old['edges']))
 for e in p['parent_removed_edges']:expected[edge(e)]-=1
 expected+=collections.Counter(edge(e)for e in p['parent_added_edges'])
 ck('exact_ordered_parent_delta',collections.Counter(map(tuple,g['edges']))==expected,p['parent_added_edges'])
 ck('guard_before_both_original_children',[e for e in g['edges']if e[0]=='65003']==[['65003','Out','1300','In']],'No direct source→native bypass')
 for output in ['True','False']:
  found=[];todo=[e[2]for e in g['edges']if e[0]=='1300'and e[1]==output]
  while todo:
   ident=todo.pop()
   if ident in ['10','64001','1302']:found.append(ident);continue
   todo += [e[2]for e in g['edges']if e[0]==ident and e[1]=='Out']
  ck('native_continuation_once_on_'+output,collections.Counter(found)==collections.Counter(['10','64001']+(['1302']if output=='True'else[])),found)
 for gp,gr in before['graphs'].items():
  if gp=='root/50':
   for ident,n in gr['nodes'].items():ck('old_node_identity_payload_socket '+ident,g['nodes'][ident]==n,ident)
  else:ck('old_graph_preserved '+gp,after['graphs'][gp]==gr,gp)
 ck('only_new_parent_ids',set(g['nodes'])-set(old['nodes'])=={'1300','1301','1302'},list(set(g['nodes'])-set(old['nodes'])))
 ck('only_new_actor_graph',set(after['graphs'])-set(before['graphs'])=={'root/50/1302'},list(after['graphs']))
 for key in ['metadata','metadata_sha256','root_prefabs','embedded_files']:ck('root_metadata '+key,after[key]==before[key],key)
 ck('only_new_external_actor_ref',set(after['refs'])-set(before['refs'])=={p['native_actor']},sorted(set(after['refs'])-set(before['refs'])))
 ck('only_owned_new_fact_write',g['nodes']['1301']['writes']==[{'$type':'questSetVar_NodeType','factName':p['claim_fact'],'setExactValue':1,'value':1}]and not any(n['writes']for n in hg['nodes'].values()),p['claim_fact'])
 ck('no_helper_sms_reward_or_prefabs',not any(n['sms']or n['reward']or n['prefabs']for n in hg['nodes'].values()),'Original external actor body remains unchanged, including its native cleanup/reward')
 initial=g['nodes']['1300']['payload']['condition'];late=hg['nodes']['1303']['payload']['condition']
 def ev(c,f,j):
  t=c['$type']
  if t=='questLogicalCondition':
   a=[ev(x,f,j)for x in c['conditions']];return all(a)if c['operation']=='AND'else any(a)if c['operation']=='OR'else False
  if t in ['questFactsDBCondition','questJournalCondition']:return ev(c['type'],f,j)
  if t=='questVarComparison_ConditionType':
   a=f.get(c['factName'],0);b=c['value'];return {'Equal':a==b,'Greater':a>b,'GreaterOrEqual':a>=b}[c['comparisonType']]
  if t=='questJournalEntryState_ConditionType':return c['path']['realPath']in j and ((j[c['path']['realPath']]==c['state'])!=bool(c.get('inverted')))
  raise ValueError(t)
 ir=g['nodes']['1300']['reads'];lr=hg['nodes']['1303']['reads'];facts=p['initial_guard_facts'];journals={x['path']['realPath']:'Inactive'for x in p['initial_guard_journals']};lf={x['fact']:x['value']+(1 if x['comparison']=='Greater'else 0)for x in p['helper_graph_change']['late_guard_facts']};root=p['helper_graph_change']['late_guard_journal']['path']
 ck('exact_initial_fact_guard',{x['factName']:x['value']for x in ir if'factName'in x}==facts and all(x.get('comparisonType','Equal')=='Equal'for x in ir),facts)
 ck('exact_initial_journal_clauses',[x for x in ir if x['$type']=='questJournalEntryState_ConditionType']==p['initial_guard_journals'],p['initial_guard_journals'])
 expectedlate={(x['fact'],x['comparison'],x['value'])for x in p['helper_graph_change']['late_guard_facts']};ck('exact_late_fact_guard',{(x['factName'],x['comparisonType'],x['value'])for x in lr if'factName'in x}==expectedlate,sorted(expectedlate))
 ck('genuine_initial_event_fixture',ev(initial,facts,journals),facts)
 for k,v in facts.items():ck('initial_negative_'+k,not ev(initial,facts|{k:1-v},journals),v)
 for path in journals:
  for state in ['Active','Succeeded','Failed',None]:
   jj=dict(journals)
   if state is None:jj.pop(path)
   else:jj[path]=state
   ck('old_or_unknown_journal_rejected_'+path+str(state),not ev(initial,facts,jj),'Missing remains unknown; no forced Inactive')
 for ownerfinished in [0,1]:ck('late_completed_parent_allowed_'+str(ownerfinished),ev(late,lf|{'PTFRU9_sts_ep1_08_OwnerFinished':ownerfinished},{root:'Active'}),'Initial zero-state predicates not reused late')
 ck('choice_changes_after_enrollment_do_not_restore_stadium',not ev(late,lf|{'sts_ep1_08_biomonitor_ana':1},{root:'Active'}),'InitialAna0→laterAna1 is refused on every19→17 invocation')
 for state in ['Succeeded','Failed',None]:ck('late_terminal_or_unknown_root_rejected_'+str(state),not ev(late,lf,{}if state is None else{root:state}),state)
 def raw_node(doc,ids):
  r=Resource(doc);gr=r.d(r.root['graph'])
  for ident in ids:
   n=next(r.d(h)for h in gr['nodes']if r.d(h)['id']==ident)
   if'phaseGraph'in n:gr=r.d(n['phaseGraph'])
  return r,n
 bad=copy.deepcopy(docs['after']);rr,n=raw_node(bad,[50,1302,1303]);cond=rr.d(n['condition']);cond['conditions']=[h for h in cond['conditions']if not any(x.get('factName')=='sts_ep1_08_biomonitor_ana'for x in walk(rr.d(h)))];bm=Resource(bad).normalize();detected=ev(bm['graphs']['root/50/1302']['nodes']['1303']['payload']['condition'],lf|{'sts_ep1_08_biomonitor_ana':1},{root:'Active'});mut.append({'fault':'remove_actual_late_Ana_fence','detected':detected});ck('raw_mutation_late_Ana',detected,mut[-1])
 # Actual raw false edge removal, reciprocal socket lists, separate route oracle.
 bad=copy.deepcopy(docs['after']);rr,n=raw_node(bad,[50,1300]);matches=[]
 for sh in n['sockets']:
  s=rr.d(sh)
  if s['name'].get('$value')=='False':matches.extend(rr.hid(h)for h in s.get('connections',[]))
 ck('actual_refusal_edges_present',len(matches)==2,matches)
 selected=matches[0];gr=rr.d(next(rr.d(h)for h in rr.d(rr.root['graph'])['nodes']if rr.d(h)['id']==50)['phaseGraph'])
 for h in gr['nodes']:
  for sh in rr.d(h).get('sockets',[]):
   s=rr.d(sh);s['connections']=[ch for ch in s.get('connections',[])if rr.hid(ch)!=selected]
 bm=Resource(bad).normalize();detected=collections.Counter(map(tuple,bm['graphs']['root/50']['edges']))!=expected;mut.append({'fault':'remove_actual_main_refusal_path','detected':detected});ck('raw_mutation_refusal',detected,mut[-1])
 ck('actual_after_binary_hash',sha(C/'archive_source'/patch['depot'])==patch['after'],patch['after'])
 ck('existing_S23_template_unmodified',sha(plan['template']['binary'])==plan['template']['sha256'],'Old actor/message adapter preserved exactly')
 inputs=[Path(__file__),C/'actor_repair_plan.json',R/'patch.json',R/'before.json',R/'after.json',R/'template.json',Path(plan['proposal']),Path(plan['review'])]
 write(out/'tests.json',{'status':'PASS_SERIALIZED_STEVEN_FUTURE_ACTOR_ONLY_HELPER','checks':len(tests),'tests':tests,'mutations':mut,'input_pins':{str(x):sha(x)for x in inputs},'before':'EXPECTED_FAIL_MISSING_FUTURE_U9_ACTOR_OWNER','after':'PASS_EXACT_ORDERED_HELPER_WITH_LATE_CHOICE_HISTORY_FENCES','limits':['No old passed-node polling/adoption; queued saved execution and engine transition behavior not certified.','World/actor/marker/vehicle/notifier binding and journal existence remain opaque/live; missing journal fixture refuses.','Native actor resource and legitimate native default_on0 cleanup remain unchanged; no new native timer/message/reward producer.'],'game_writes':0,'save_writes':0})
 return {'status':'PASS_SERIALIZED_STEVEN_FUTURE_ACTOR_ONLY_HELPER','checks':len(tests),'raw_mutations':len(mut)}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();print(run(Path(a.output).resolve()))
