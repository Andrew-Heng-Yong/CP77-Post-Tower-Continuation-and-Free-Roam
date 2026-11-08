"""Actual readback regressions against independently pinned native monitor bodies."""
from pathlib import Path
import sys,argparse,copy,collections
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
from model import Resource,reachable

def edge(e):return(str(e[0]),e[1],str(e[2]),e[3])
def delta(edges,removed,added):
 c=collections.Counter(map(tuple,edges));c.subtract(edge(e)for e in removed);c.update(edge(e)for e in added)
 return +c
def rawnode(doc,ids):
 r=Resource(doc);g=r.d(r.root['graph'])
 for ident in ids:
  n=next(r.d(h)for h in g['nodes']if int(r.d(h)['id'])==int(ident))
  if 'phaseGraph'in n:g=r.d(n['phaseGraph'])
 return r,n
def run(out):
 assert not out.exists();C=O/'candidate_02';results=[]
 for p in read(C/'monitor_plans.json')['plans']:
  R=C/('repair_'+p['key']);d={k:read(R/(k+'.json'))for k in ['before','after','native']};m={k:Resource(v).normalize()for k,v in d.items()};patch=read(R/'patch.json');tests=[];mut=[]
  def ck(n,ok,e):tests.append({'name':n,'status':'PASS'if ok else'FAIL','evidence':e});assert ok,p['key']+': '+n
  before,after,native=(m[k]for k in ['before','after','native']);ids=list(map(str,p['new_ids']));gid,cid,hid=ids;np='root/'+str(p['native_phase_id']);hp='root/'+hid;g=after['graphs']['root'];old=before['graphs']['root'];ng=native['graphs'][np];hg=after['graphs'][hp]
  for k,v in m.items():ck('decoded_'+k,not v['errors'],v['errors'])
  ck('expected_baseline_fault',hid not in old['nodes'] and hp not in before['graphs'],'Native fallback helper is absent before repair; normal completion can still work')
  ck('exact_parent_edge_delta',collections.Counter(map(tuple,g['edges']))==delta(old['edges'],p['parent_removed_edges'],p['parent_added_edges']),p['parent_added_edges'])
  ck('only_three_new_parent_nodes',set(g['nodes'])-set(old['nodes'])==set(ids),ids)
  for ident,n in old['nodes'].items():ck('old_parent_node_'+ident,g['nodes'][ident]==n,ident)
  for gp,gr in before['graphs'].items():
   if gp!='root':ck('old_nested_graph_'+gp,after['graphs'][gp]==gr,gp)
  ck('root_metadata_unchanged',all(after[k]==before[k]for k in ['metadata','metadata_sha256','root_prefabs','embedded_files']),'No root support or metadata changes')
  expectedgraphs={hp+k[len(np):]for k in native['graphs']if k==np or k.startswith(np+'/')}
  ck('only_native_clone_graphs',set(after['graphs'])-set(before['graphs'])==expectedgraphs,sorted(expectedgraphs))
  for gp in sorted(expectedgraphs):
   src=native['graphs'][np+gp[len(hp):]];got=after['graphs'][gp]
   ck('exact_native_nodes_'+gp,got['nodes']==src['nodes'],{'nodes':len(src['nodes'])})
   exp=delta(src['edges'],p['native_input_remove'],p['native_input_add'])if gp==hp else collections.Counter(map(tuple,src['edges']))
   ck('exact_native_edges_'+gp,collections.Counter(map(tuple,got['edges']))==exp,{'edges':len(got['edges'])})
   ck('exact_native_entry_sockets_'+gp,got['entries']==src['entries'],src['entries'])
  a=copy.deepcopy(g['nodes'][hid]);b=copy.deepcopy(native['graphs']['root']['nodes'][str(p['native_phase_id'])])
  for n in [a,b]:n.pop('id');n.pop('payload_sha256');n['payload'].pop('id')
  ck('native_phase_metadata_prefabs_and_sockets',a==b,p['expected_prefabs'])
  ck('required_native_prefab_lease',g['nodes'][hid]['prefabs']==p['expected_prefabs'],p['expected_prefabs'])
  for i,t in p['required_join_types'].items():ck('native_join_'+i,hg['nodes'][i]['type']==t,t)
  ck('arm_nodes_retained_but_unreachable',all(str(i)in hg['nodes']and str(i)not in hg['reachable']for i in p['retained_arm_ids']),p['retained_arm_ids'])
  ck('native_arm_fact_not_written_from_entry',not any(w.get('factName')==p['native_arm_fact']for i in hg['reachable']for w in hg['nodes'][i]['writes']),p['native_arm_fact'])
  guard=g['nodes'][gid];reads=guard['reads'];facts=p['guard_facts']
  ck('exact_guard_AND',guard['payload']['condition']['$type']=='questLogicalCondition'and guard['payload']['condition']['operation']=='AND','All reviewed facts required')
  ck('exact_guard_fact_predicates',len(reads)==len(facts)and{r['factName']:r['value']for r in reads}==facts and all(r['comparisonType']=='Equal'for r in reads),facts)
  ck('single_private_claim',g['nodes'][cid]['writes']==[{'$type':'questSetVar_NodeType','factName':p['claim_fact'],'setExactValue':1,'value':1}],p['claim_fact'])
  for branch in ['True','False']:
   todo=[e[2]for e in g['edges']if e[0]==gid and e[1]==branch];found=[]
   while todo:
    n=todo.pop()
    if n in [p['normal_child'],hid]:found.append(n);continue
    todo.extend(e[2]for e in g['edges']if e[0]==n and e[1]=='Out')
   ck('normal_continuation_once_'+branch,collections.Counter(found)==collections.Counter([p['normal_child']]+([hid]if branch=='True'else[])),found)
  def allows(ff):return all(ff.get(r['factName'],0)==r['value']for r in reads)
  ck('fresh_fixture',allows(facts),facts)
  for f,v in facts.items():ck('guard_reject_'+f,not allows(facts|{f:1-v}),v)
  for v in [0,1]:ck('native_arm_zero_or_prearmed_'+str(v),allows(facts|{p['native_arm_fact']:v}),'Native arm history is neither reset nor used to suppress fresh helper')
  ck('old_started_no_adoption',not allows(facts|{next(k for k in facts if k.endswith('_Started')):1}),'Already passed saved-owner routes are not polled')
  # Mutate actual readback documents; independent native payload/edge oracle detects each fault.
  bad=copy.deepcopy(d['after']);rr,n=rawnode(bad,[int(hid),int(next(iter(p['required_join_types'])))]);n['$type']='questLogicalAndNodeDefinition'if n['$type']!='questLogicalAndNodeDefinition'else'questLogicalXorNodeDefinition';bm=Resource(bad).normalize();det=bm['graphs'][hp]['nodes']!=ng['nodes'];mut.append({'fault':'native_join_changed','detected':det});ck('raw_mutation_join',det,mut[-1])
  bad=copy.deepcopy(d['after']);rr,n=rawnode(bad,[int(hid)]);n['phaseInstancePrefabs']=[]if p['expected_prefabs']else[{'HandleId':'999999','Data':{'$type':'questQuestPrefabEntry','prefabNodeRef':{'$type':'NodeRef','$storage':'string','$value':'#unapproved'}}}];bm=Resource(bad).normalize();det=bm['graphs']['root']['nodes'][hid]['prefabs']!=p['expected_prefabs'];mut.append({'fault':'native_prefab_scope_changed','detected':det});ck('raw_mutation_prefab',det,mut[-1])
  bad=copy.deepcopy(d['after']);rr,n=rawnode(bad,[int(hid),int(p['native_input_add'][0][2])]);s=next(rr.d(h)for h in n['sockets']if rr.d(h)['name'].get('$value')==p['native_input_add'][0][3]);chosen=rr.hid(s['connections'][0]);rr,owner=rawnode(bad,[int(hid)]);bg=rr.d(owner['phaseGraph'])
  for nh in bg['nodes']:
   for sh in rr.d(nh).get('sockets',[]):
    ss=rr.d(sh);ss['connections']=[ch for ch in ss.get('connections',[])if rr.hid(ch)!=chosen]
  bm=Resource(bad).normalize();det=collections.Counter(map(tuple,bm['graphs'][hp]['edges']))!=delta(ng['edges'],p['native_input_remove'],p['native_input_add']);mut.append({'fault':'monitor_input_listener_edge_removed','detected':det});ck('raw_mutation_input_edge',det,mut[-1])
  ck('binary_before_pin',sha(O/'candidate_01/archive_source'/p['depot'])==p['before'],p['before'])
  ck('binary_after_pin',sha(C/'archive_source'/p['depot'])==patch['after'],patch['after'])
  pins=[Path(__file__),C/'monitor_plans.json',R/'patch.json',R/'before.json',R/'after.json',R/'native.json',Path(p['proposal']),Path(p['review'])]
  results.append({'key':p['key'],'status':'PASS_SERIALIZED_BOUNDED_NATIVE_MONITOR','checks':len(tests),'tests':tests,'mutations':mut,'input_pins':{str(x):sha(x)for x in pins},'before':'EXPECTED_MISSING_FALLBACK_OWNER','after':'EXACT_NATIVE_MONITOR_WITH_REVIEWED_PREFIX_BYPASS','limits':['No engine-pulse, streaming, journal callback, reward or gameplay success assertion.','No adoption or retrofit of already entered/started owners.','Original world prefab lease remains opaque; Cheetah retains exact native shared lease.']})
 write(out/'tests.json',{'status':'PASS_SERIALIZED_MONITORS','checks':sum(r['checks']for r in results),'raw_mutations':sum(len(r['mutations'])for r in results),'results':results,'game_writes':0,'save_writes':0})
 return {'status':'PASS_SERIALIZED_MONITORS','checks':sum(r['checks']for r in results),'raw_mutations':sum(len(r['mutations'])for r in results)}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();print(run(Path(a.output).resolve()))
