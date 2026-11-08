"""Independent native-root prefab oracle and preserved saved-owner regression."""
from pathlib import Path
import sys,argparse,copy,collections
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
from model import Resource
def rawnode(d,ids):
 r=Resource(d);g=r.d(r.root['graph'])
 for i in ids:
  n=next(r.d(h)for h in g['nodes']if int(r.d(h)['id'])==i)
  if'phaseGraph'in n:g=r.d(n['phaseGraph'])
 return r,n
def run(out):
 assert not out.exists();C=O/'candidate_03';R=C/'repair_moving_heat';plan=read(C/'moving_heat_plan.json');p=read(plan['proposal']);patch=read(R/'patch.json');docs={k:read(R/(k+'.json'))for k in ['before','after','native']};models={k:Resource(v).normalize()for k,v in docs.items()};tests=[];mut=[]
 def ck(n,ok,e):tests.append({'name':n,'status':'PASS'if ok else'FAIL','evidence':e});assert ok,n
 before,after,native=(models[k]for k in ['before','after','native']);old=before['graphs']['root'];g=after['graphs']['root'];hg=after['graphs']['root/1200'];prefabs=native['root_prefabs']
 for k,m in models.items():ck('actual_readback_decodes_'+k,not m['errors'],m['errors'])
 def haslease(m):return '1200'in m['graphs']['root']['nodes']and m['graphs']['root']['nodes']['1200']['prefabs']==['#q304_pr_car_retrieval']
 ck('baseline_lacks_required_native_root_lease',prefabs and not haslease(before),{'expected_fault':'Original native root holds dedicated lease; existing private root/old10 does not'})
 ck('future_wrapper_has_native_lease',haslease(after),'Exact dedicated native prefab, no global/default/main-story root owner')
 ck('native_prefab_entry_exact',g['nodes']['1200']['payload']['phaseInstancePrefabs']==native['metadata']['phasePrefabs'],native['metadata']['phasePrefabs'])
 ck('wrapper_is_inline',g['nodes']['1200']['payload']['phaseResource']==p['new_wrapper']['phaseResource'],p['new_wrapper']['phaseResource'])
 ck('only_one_new_root_ID',set(g['nodes'])-set(old['nodes'])=={'1200'},'1200')
 ck('only_wrapper_and_exact_external_empty_graph',set(after['graphs'])-set(before['graphs'])=={'root/1200','root/1200/10'}and after['graphs']['root/1200/10']==before['graphs']['root/10'],list(after['graphs']))
 exp=collections.Counter(map(tuple,old['edges']));exp.subtract(tuple(x)for x in p['remove_edges']);exp.update(tuple(x)for x in p['add_edges'])
 ck('exact_future_edge_delta',collections.Counter(map(tuple,g['edges']))==+exp,p['add_edges'])
 ck('old_saved_phase10_unchanged',g['nodes']['10']==old['nodes']['10']and['10','Out1','11','In']in g['edges'],'Existing saved descendants remain at original root/10, without a retroactive prefab addition')
 ck('new_inner_saved_body_exact',hg['nodes']['10']==old['nodes']['10'],'Same external resource, ID, flags, sockets and save fields')
 ck('exact_inner_edges',hg['edges']==sorted(p['new_wrapper']['inner_edges']),p['new_wrapper']['inner_edges'])
 ck('inner_input_and_terminating_output',set(hg['nodes'])=={'0','10','1'}and hg['nodes']['0']['type']=='questInputNodeDefinition'and hg['nodes']['1']['type']=='questOutputNodeDefinition'and hg['nodes']['1']['payload']['type']=='Terminating','Natural phase termination owns lease release before existing11 completion receipt')
 for ident,n in old['nodes'].items():
  if ident in ['2','3','9']:
   expected=copy.deepcopy(n['payload']['condition']);assert expected['operation']=='AND';expected['conditions'].append(p['guard_updates']['append_exact_AND_atom'])
   ck('exact_old_guard_plus_S24_owner_atom_'+ident,g['nodes'][ident]['payload']['condition']==expected,'No old clause, state, threshold, AND/OR group or socket removed')
   a=copy.deepcopy(g['nodes'][ident]['payload']);b=copy.deepcopy(n['payload']);a.pop('condition');b.pop('condition');ck('guard_noncondition_fields_'+ident,a==b,ident)
  else:ck('old_node_payload_identity_'+ident,g['nodes'][ident]==n,ident)
 for gp,gr in before['graphs'].items():
  if gp!='root':ck('old_graph_'+gp,after['graphs'][gp]==gr,gp)
 for key in ['metadata','metadata_sha256','root_prefabs','embedded_files','refs']:ck('root_preserved_'+key,after[key]==before[key],key)
 ck('no_new_fact_or_journal_writer',not any(n['writes']or n['journal_paths']or n['reward']or n['sms']for n in hg['nodes'].values()),'External body remains exact; wrapper adds only lease and existing execution path')
 for ident in ['2','3','9']:
  reads=g['nodes'][ident]['reads'];atom=[r for r in reads if r.get('factName')=='PTFRS24_Q304_FRESH_Issued'];ck('one_exact_S24_fence_'+ident,len(atom)==1 and atom[0]['comparisonType']=='Equal'and atom[0]['value']==0,'Known fresh owner refuses future competing resume at all three admission/rechecks')
 # Mutate actual readback exports. Native source and original saved node are independent oracles.
 bad=copy.deepcopy(docs['after']);rr,n=rawnode(bad,[1200]);n['phaseInstancePrefabs']=[];bm=Resource(bad).normalize();det=not haslease(bm);mut.append({'fault':'delete_wrapper_native_prefab','detected':det});ck('raw_mutation_prefab',det,mut[-1])
 bad=copy.deepcopy(docs['after']);rr,n=rawnode(bad,[1200,1]);n['type']='NonTerminating';bm=Resource(bad).normalize();det=bm['graphs']['root/1200']['nodes']['1']['payload']['type']!='Terminating';mut.append({'fault':'make_output_nonterminating','detected':det});ck('raw_mutation_output_lifecycle',det,mut[-1])
 bad=copy.deepcopy(docs['after']);rr,n=rawnode(bad,[9]);co=rr.d(n['condition']);co['conditions'].pop();bm=Resource(bad).normalize();det=not any(x.get('factName')=='PTFRS24_Q304_FRESH_Issued'for x in bm['graphs']['root']['nodes']['9']['reads']);mut.append({'fault':'remove_late_fresh_owner_fence','detected':det});ck('raw_mutation_guard',det,mut[-1])
 bad=copy.deepcopy(docs['after']);rr,n=rawnode(bad,[10]);n['saveLock']=1;bm=Resource(bad).normalize();det=bm['graphs']['root']['nodes']['10']!=old['nodes']['10'];mut.append({'fault':'change_old_saved_node_payload','detected':det});ck('raw_mutation_saved_identity',det,mut[-1])
 bad=copy.deepcopy(docs['after']);rr,n=rawnode(bad,[1200]);sock=next(rr.d(s)for s in n['sockets']if rr.d(s)['name'].get('$value')=='Out1');key=rr.hid(sock['connections'][0]);rg=rr.d(rr.root['graph'])
 for nh in rg['nodes']:
  for sh in rr.d(nh).get('sockets',[]):
   ss=rr.d(sh);ss['connections']=[h for h in ss.get('connections',[])if rr.hid(h)!=key]
 bm=Resource(bad).normalize();det=collections.Counter(map(tuple,bm['graphs']['root']['edges']))!=+exp;mut.append({'fault':'remove_lease_wrapper_completion_callback','detected':det});ck('raw_mutation_completion_edge',det,mut[-1])
 ck('actual_before_pin',sha(O/'candidate_02/archive_source'/patch['depot'])==patch['before'],patch['before']);ck('actual_after_pin',sha(C/'archive_source'/patch['depot'])==patch['after'],patch['after'])
 for dep in p['preserve_resources']:ck('other_fresh_resume_body_preserved_'+dep,sha(C/'archive_source'/dep)==sha(O/'candidate_02/archive_source'/dep),dep)
 files=[Path(__file__),C/'moving_heat_plan.json',R/'before.json',R/'after.json',R/'native.json',R/'patch.json',Path(plan['proposal']),Path(plan['review'])]
 write(out/'tests.json',{'status':'PASS_SERIALIZED_FUTURE_MOVING_HEAT_PREFAB_WRAPPER','checks':len(tests),'tests':tests,'mutations':mut,'input_pins':{str(f):sha(f)for f in files},'limits':p['conditional_limits'],'game_writes':0,'save_writes':0})
 return{'status':'PASS_SERIALIZED_FUTURE_MOVING_HEAT_PREFAB_WRAPPER','checks':len(tests),'mutations':len(mut)}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();print(run(Path(a.output).resolve()))
