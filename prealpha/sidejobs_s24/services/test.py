"""S24 fresh The Gig: native payload, one-shot, no S22 overlap and policy checks."""
import copy,importlib.util,itertools,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('s22_native_test',ROOT/'prealpha/sidejobs_s22/delamain_v2/test.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
read,sha,graphs,nodes,edges,evaluate=m.read,m.sha,m.graphs,m.nodes,m.edges,m.evaluate
def verify(build):
 manifest=read(build/'build.json');c=read(HERE/'contract.json')['owners'][0]
 for p,h in manifest['source_pins'].items():assert sha(ROOT/p)==h,p
 for p,h in manifest['resources'].items():assert sha(build/'source'/p)==h,p
 assert len(manifest['resources'])==len(manifest['boots'])==1 and not manifest['mod_overrides']
 source=graphs(ROOT/(c['native_source'].replace('/raw/','/json/')+'.json'))
 actual=graphs(build/'readback/the_gig.json');assert set(source)==set(actual)=={'root'}
 ng=source['root'];ag=actual['root'];ns=nodes(ng);an=nodes(ag)
 for i,n in ns.items():assert an[i]==n,('native payload changed',i)
 assert len(manifest['native_copies'])==len(ns)==24
 expected=edges(ng)-{(0,'Out',25,'In'),(27,'Out',1,'In')}
 expected|={(0,'Out',1001,'In'),(1001,'Out',1002,'In'),(1002,'Out',1003,'In'),(1003,'False',1002,'In'),(1003,'True',1004,'In'),(1004,'Out',1006,'In'),(1006,'Out',1005,'In'),(1005,'Out',25,'In'),(27,'Out',1007,'In'),(1007,'Out',1,'In')}
 assert edges(ag)==expected
 original=nodes(graphs(ROOT/(c['contact_source'].replace('/raw/','/json/')+'.json'))['root'])[168]
 derived=copy.deepcopy(original);derived['id']=1006;derived['type']['params'][0]['contact']['realPath']='contacts/wakako_okada'
 assert an[1006]==derived
 # This exact target contact identity/class/index is present in stock Wakako's owner.
 native_wakako=read(ROOT/'research/fixer_offices_fo1/parents/json/base/open_world/fixers/wakako/phases/wakako.questphase.json')
 p=derived['type']['params'][0]['contact']
 refs=[x for x in m.walk(native_wakako) if x.get('$type')=='gameJournalPath' and x.get('realPath')==p['realPath']]
 assert refs and all(x['fileEntryIndex']==1 and m.value(x['className'])=='gameJournalContact' for x in refs)
 # Every new native operation is this sole contact addition. No native progress
 # writes, rewards, inventory actions or other contact/owner changes in wrapper.
 for i in set(an)-set(ns)-{1006}:
  n=an[i]
  if n['$type']=='questFactsDBManagerNodeDefinition':assert n['type']['factName'].startswith(c['tag']+'_')
  else:assert n['$type'] in ('questConditionNodeDefinition','questPauseConditionNodeDefinition')
 assert an[1002]['condition']==an[1003]['condition']
 good=manifest['common_equal']|c['facts_equal']|{k:v['min'] for k,v in c['fact_ranges'].items()}|{c['tag']+'_Permit':1,c['tag']+'_Issued':0,c['tag']+'_Finished':0,c['tag']+'_Fault':0}
 j={x['path']:'Inactive' for x in c['journals']};condition=an[1002]['condition']
 assert evaluate(condition,good,j)
 cases=1
 for k,v in good.items():
  bounds=c['fact_ranges'].get(k,{'min':v,'max':v})
  for alt in {-1,0,1,2,3,99,2147483647,bounds['min']-1,bounds['max']+1}:
   f=good|{k:alt};expected_policy=bounds['min']<=alt<=bounds['max']
   assert evaluate(condition,f,j)==expected_policy,(k,alt);cases+=1
 for path in j:
  for state in (None,'Active','Succeeded','Failed'):
   assert not evaluate(condition,good,j|{path:state}),(path,state);cases+=1
 capture=read(ROOT/'research/sidejobs_s23/live_20261016_01/capture.json')
 cur=next(x for x in capture['second']['jobs'] if x['id']==c['id'])
 assert cur['rootState']=='Active'
 assert not evaluate(condition,good,j|{x['path']:x['state'] for x in cur['journals']})
 cases+=1
 # S22 tail (unchanged) cannot start at any reachable native state. No root
 # failure/inactivation branch exists here, and no S22 Issued lock is forged.
 old=read(ROOT/'prealpha/sidejobs_s22/the_gig/contract.json')
 def old_admits(f,js):
  return all(f.get(k,0)==v for k,v in old['facts_equal'].items()) and all(js.get(x['path']) in {1:'Inactive',2:'Active',3:'Succeeded',4:'Failed'}.values() and js.get(x['path']) in [{1:'Inactive',2:'Active',3:'Succeeded',4:'Failed'}[v] for v in x['states']] for x in old['journals'])
 f=good.copy();js=j.copy();current=0;trace=[];reward_calls=0
 assert not old_admits(f,js)
 while current!=1:
  assert len(trace)<100;trace.append(current);n=an[current];out='Out'
  if n['$type']=='questConditionNodeDefinition':out='True' if evaluate(n['condition'],f,js) else 'False'
  elif n['$type']=='questFactsDBManagerNodeDefinition':
   t=n['type'];f[t['factName']]=t['value'] if t['setExactValue'] else f.get(t['factName'],0)+t['value']
  elif current==3:f['q001_wakako_reward_given']=1 # native conversation performs this only upon player collection
  elif current==11:reward_calls+=1
  e=[e for e in expected if e[0]==current and e[1]==out];assert len(e)==1,(current,e)
  edge=e[0];target=an[edge[2]]
  if target['$type']=='questJournalNodeDefinition':
   assert edge[3] in ('Active','Succeeded'),edge
   js[target['type']['path']['realPath']]=edge[3]
  assert not old_admits(f,js),(current,js)
  current=edge[2]
 assert reward_calls==1 and f[c['tag']+'_Finished']==1 and f['sq_q001_done']==1
 assert js['quests/side_quest/sq_q001_wakako']=='Succeeded'
 assert not evaluate(condition,f,js)
 cases+=len(trace)+1
 return {'status':'PASS_NOT_LIVE_PROOF','native_payloads_exact':len(ns),'native_payload_checks':len(ns)+1,'contact_path_only_transform':1,'guard_cases':cases,'policy_cases':cases,'tester_sha256':sha(Path(__file__)),'component_sha256':sha(build/'build.json'),'native_trace_nodes':trace,'old_S22_overlap':False,'current_active_branch_protected':True,'build_manifest_sha256':sha(build/'build.json'),'contract_sha256':sha(HERE/'contract.json')}
if __name__=='__main__':
 build=HERE/'build'/sys.argv[1];out=build/'tests.json'
 if out.exists():raise RuntimeError('Immutable test result exists')
 result=verify(build);out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
