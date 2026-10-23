"""Integration and bounded The Gig tests; never operates on live saves."""
import importlib.util,itertools,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('delamain_test',HERE/'delamain/test.py')
lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)
sha,read,graphs,nodes,edges,evaluate=lib.sha,lib.read,lib.graphs,lib.nodes,lib.edges,lib.evaluate

def main(revision):
 b=HERE/'build'/revision;dest=b/'tests.json';assert not dest.exists()
 m=read(b/'build.json');assert m['status']=='BUILT_S22_LIVE_PENDING'
 for p,h in m['source_pins'].items():assert sha(ROOT/p)==h,p
 assert len(m['files'])==4 and len(m['resources'])==8 and len(m['boots'])==5
 assert len(set(m['boots']))==5 and len({x['id'] for x in m['injections']})==5
 assert sum('old_sha256' in x for x in m['files'])==1 and m['packed_readback']
 assert m['official_overrides']==[] and m['mod_overrides']==['towercontinued\\gig_phone_u9\\fixer_cleanup.questphase']
 for row in m['files']:assert sha(b/Path(row['relative']).name)==row['sha256']
 for p,h in m['resources'].items():assert sha(b/'source'/p)==h,p
 native_checks=0;cases=0;component_proofs=[]
 for item in m['components']:
  t=read(ROOT/item['tests']);component_proofs.append({'name':item['name'],'path':item['tests'],'sha256':sha(ROOT/item['tests'])})
  assert t['status'].startswith('PASS'),item
  if item['name']=='delamain':
   cm=read(ROOT/item['manifest']);assert t['build_sha256']==sha(ROOT/item['manifest'])
   assert t['tester_sha256']==sha(HERE/'delamain/test.py')
   for p,h in cm['resources'].items():assert m['resources'][p]==h
   native_checks+=t['copied_native_nodes'];cases+=t['negative_admissions']+t['positive_admissions']+t['completion_masks']
  elif item['name']=='moving_heat':
   cm=read(ROOT/item['manifest']);assert t['component_sha256']==sha(ROOT/item['manifest'])
   assert t['tester_sha256']==sha(HERE/'ep1_jobs/test_component.py')
   assert m['resources'][cm['depot']]==cm['sha256'] and m['resources'][cm['boot']]==cm['boot_sha256']
   native_checks+=t['native_payload_checks'];cases+=t['negative_guard_cases']+t['positive_guard_cases']
  else:
   assert t['test_sha256']==sha(HERE/'boxing/test.py')
   actual=graphs(b/'readback/towercontinued_sidejobs_s22_mq025_progress.questphase.json')
   expected=graphs(ROOT/'research/sidejobs_s22/boxing/audit_02/mq025_progress.json')
   assert actual==expected,'boxing packed integration differs'
   native_checks+=t['native_payloads_checked'];cases+=t['policy_cases']
 s=read(HERE/'the_gig/contract.json');source=graphs(ROOT/(s['native_source'].replace('/raw/','/json/')+'.json'))['root']
 actual=graphs(b/('readback/'+s['depot'].replace('\\','_')+'.json'))['root']
 on,an=nodes(source),nodes(actual)
 for i in s['selected_nodes']:assert on[i]==an[i],('native reward tail payload',i);native_checks+=1
 assert set(an)==set(s['selected_nodes'])|set(range(1000,1009))
 assert not any(i in an for i in [11,12,13]),'paid reward or old SMS replay'
 expected={e for e in edges(source) if e[0] in s['selected_nodes'] and e[2] in s['selected_nodes'] and e[0] not in [0,15] and e!=(27,'Out',1,'In')}
 expected|={(0,'Out',1000,'In'),(1000,'Out',1001,'In'),(1001,'Out',1002,'In'),(1002,'True',1003,'In'),(1002,'False',1005,'In'),(1003,'Out',25,'In'),(2,'Out',1006,'Active'),(1006,'Out',15,'Active'),(15,'Out',1007,'In'),(1007,'Out',1008,'In'),(1008,'True',30,'In'),(1008,'False',1005,'In'),(27,'Out',1004,'In'),(1004,'Out',1,'In')}
 assert edges(actual)==expected
 c=an[1001]['condition'];assert c==an[1002]['condition']
 states={1:'Inactive',2:'Active',3:'Succeeded',4:'Failed'}
 f=m['common']|s['facts_equal']|{s['tag']+'_Permit':1,s['tag']+'_Issued':0,s['tag']+'_Finished':0,s['tag']+'_Fault':0}
 j={x['path']:states[x['states'][0]] for x in s['journals']}
 assert evaluate(c,f,j);cases+=1
 for k,v in f.items():
  for wrong in [-1,0,1,2,9]:
   if wrong==v:continue
   assert not evaluate(c,f|{k:wrong},j),(k,wrong);cases+=1
 for x in s['journals']:
  for v in [None,'Inactive','Active','Succeeded','Failed','Unknown']:
   assert evaluate(c,f,j|{x['path']:v})==(v in [states[n] for n in x['states']]);cases+=1
 post=an[1007]['condition'];assert post==an[1008]['condition']
 pj=j|{p:'Active' for p in s['reactivate_paths']}
 pf=f|{s['tag']+'_Issued':1,s['tag']+'_Permit':0}
 assert evaluate(post,pf,pj);cases+=1
 for p in [x['path'] for x in s['journals'] if x['states']==[3]]:
  for v in [None,'Inactive','Active','Failed']:assert not evaluate(post,pf,pj|{p:v});cases+=1
 # Only journal reactivation + original tail facts are reachable. No player
 # inventory mutation or new payout node is introduced by this adapter.
 assert all('RewardManager' not in n['$type'] for n in an.values())
 writes=[n['type']['factName'] for n in an.values() if n['$type']=='questFactsDBManagerNodeDefinition']
 assert {x for x in writes if not x.startswith('PTFRS22_')}=={'sq_q001_active','sq_q001_add_reward','sq_q001_done'}
 runtime=read(HERE/'runtime/manifest.json')
 assert len(runtime['rows'])==4
 for name in ['SideJobsS2.reds','SideJobsS22.reds']:assert sha(b/name)==sha(HERE/'runtime'/name)
 assert all(row['journals'][0]['states'] in [[1,4],[4,1]] for row in runtime['rows'])
 r={'status':'PASS_NOT_LIVE','build_sha256':sha(b/'build.json'),'tester_sha256':sha(Path(__file__)),'native_payload_checks':native_checks,'policy_cases':cases,'component_tests':component_proofs,'the_gig_native_tail_checked':True,'no_generic_native_reset':True,'not_proven':['actual runtime journal activation/objects/prompts','all58 whitelist entries','No Easy Way Out resume','all possible partial quest stages','reward/reload lifecycle']}
 dest.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':main(sys.argv[1])
