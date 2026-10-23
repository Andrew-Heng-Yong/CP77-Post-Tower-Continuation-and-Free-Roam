"""Independent native payload, dispatch ordering, and fail-closed guard tests."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).parent
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'prealpha/ncpd_scanner_n1')]
from native_inspect import SafeResource
from audit_activity_batches_b1 import flatten
from catalog_gig_rollout_r2 import value,walk
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
cache={}
def graphs(p):
 p=str(p)
 if p not in cache:
  r=SafeResource(read(Path(p)));cache[p]={g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
 return cache[p]
def nodes(g):return {n['id']:n for n in g['nodes']}
def edges(g):return set(map(tuple,g['edges']))
def evaluate(c,f,j,extra):
 t=c['$type']
 if t=='questLogicalCondition':
  v=[evaluate(x,f,j,extra) for x in c['conditions']]
  return {'AND':all(v),'OR':any(v),'NOR':not any(v)}[c['operation']]
 if t=='questJournalCondition':
  v=c['type'];return j.get((v['path']['realPath'],value(v['path']['className'])))==v['state']
 if t=='questFactsDBCondition':
  v=c['type'];a=f.get(v['factName']);b=v['value']
  if a is None:return False
  return {'Equal':a==b,'GreaterOrEqual':a>=b,'LessOrEqual':a<=b}[v['comparisonType']]
 if t=='questNodeLoadingCondition':return extra['loaded']
 if t=='questObjectCondition':
  assert c['type']['$type']=='questDevice_ConditionType'
  assert value(c['type']['deviceConditionFunction'])=='IsOpen'
  return extra['open']
 if t=='questVehicleCondition':
  assert c['type']['$type']=='questVehicleAvailable_ConditionType'
  assert c['type']['vehicleType']=='SpecificVehicle'
  return extra['owned']
 raise AssertionError(t)
def main():
 build=Path(sys.argv[1]);m=read(build/'component.json');contract=read(HERE/'contract.json')
 checks=0;positive=0;negative=0
 for p,h in m['source_pins'].items():assert sha(ROOT/p)==h,p;checks+=1
 for r in m['resource_details']:
  assert sha(build/r['relative'])==r['sha256'];assert sha(build/r['readback'])==r['readback_sha256'];checks+=2
 for c in m['native_copies']:
  source=Path(str(ROOT/c['source']).replace('/raw/','/json/').replace('\\raw\\','\\json\\')+'.json')
  old=nodes(graphs(source)[c['source_graph']])[c['source_id']]
  file,sub=c['target_graph'].split('/',1)
  new=nodes(graphs(build/'readback'/f'{file}.json')[sub])[c['target_id']]
  if file=='mq306_owner' and c['target_id']==7:
   expected=json.loads(json.dumps(old));expected['phaseResource']['DepotPath']['$value']='towercontinued\\sidejobs_s23\\ep1\\mq306_aaron.questphase'
  else:expected=old
  assert new==expected,(file,sub,c['target_id'])
  checks+=1
 # The complete original parent final cleanup, including final reward, is kept.
 mqsource=graphs(ROOT/'research/sidejobs_s23/ep1/native_01/json/ep1/quest/minor_quests/mq306/mq306.questphase.json')
 mqout=graphs(build/'readback/mq306_owner.json')
 for p,g in mqout.items():
  if p.startswith('root/9'):assert g==mqsource[p],p;checks+=len(g['nodes'])+len(g['edges'])
 assert edges(mqout['root'])=={(0,'Out',7,'In1'),(7,'Out1',9,'In1'),(9,'Out1',32,'In'),(32,'Out',31,'In'),(31,'Out',33,'In'),(33,'Out',1,'In')};checks+=1
 ar=graphs(build/'readback/mq306_aaron.json')
 arSource=graphs(ROOT/'research/sidejobs_s23/ep1/native_01/json/ep1/quest/minor_quests/mq306/phases/mq306_04a_aaron_meeting.questphase.json')
 sms=ar['root/25'];assert set(nodes(sms))=={0,24,26,54,46,28,58,19}
 assert edges(sms)=={(0,'Out',24,'In'),(24,'Out',26,'Active'),(26,'Out',54,'In'),(54,'Out',46,'Active'),(46,'Out',28,'Succeeded'),(28,'Out',58,'In'),(58,'Out',19,'In')};checks+=2
 ids=set(nodes(ar['root']));assert ids=={0,25,37,49,80,42,56,43,45,46,2}
 assert edges(ar['root'])=={e for e in edges(arSource['root']) if e[0] in ids and e[2] in ids};checks+=2
 # No clinic, combat, old waiting timer, delivered invitation or accepted reply reset.
 assert not any('mq306_03' in str(n) or 'mq306_01' in str(n) for n in ar['root']['nodes']);checks+=1
 state={1:'Inactive',2:'Active',3:'Succeeded',4:'Failed'}
 for o in contract['owners']:
  gg=graphs(build/'readback'/f"{o['key'].lower()}_boot.json");g=gg['root'];nn=nodes(g);ee=edges(g)
  assert nn[2]['condition']==nn[3]['condition'];checks+=1
  for i,suffix in [(1,'Ready'),(4,'Issued'),(91,'Fault'),(92,'Entered'),(101,'Finished')]:
   assert nn[i]['type']=={'$type':'questSetVar_NodeType','factName':o['tag']+'_'+suffix,'setExactValue':1,'value':1};checks+=1
  assert not any(n['$type']=='questOutputNodeDefinition' for n in g['nodes']);checks+=1
  assert {(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'False',2,'In'),(3,'True',4,'In'),(89,'Out',90,'In'),(90,'False',91,'In'),(90,'True',92,'In'),(92,'Out',100,'In1')}<=ee;checks+=1
  writes=[n['type']['path']['realPath'] for n in g['nodes'] if n['$type']=='questJournalNodeDefinition']
  assert writes==o['reactivate_paths'];checks+=1
  expected_j={(j['path'],j['class']):state[j['states'][0]] for j in o['journals']}
  f=contract['common_equal']|o['facts_equal']|{o['tag']+'_Issued':0,o['tag']+'_Fault':0,o['tag']+'_Finished':0,o['tag']+'_Permit':1}
  f|={k:v['min'] for k,v in o['fact_ranges'].items()}
  extra={'loaded':True,'open':False,'owned':False}
  for post,node in [(False,2),(True,90)]:
   ff=f|{o['tag']+'_Issued':int(post)}
   if post:ff|=o.get('lease_facts',{})
   jj={k:('Active' if post and k[0] in writes else v) for k,v in expected_j.items()}
   cond=nn[node]['condition'];assert evaluate(cond,ff,jj,extra),(o['key'],node);positive+=1
   for sub in walk(cond):
    if sub.get('$type')=='gameJournalPath' and '/contacts/' in sub['realPath']:
     assert sub['fileEntryIndex']==1;checks+=1
   # Fact and journal mutations independently fail closed, including unknown.
   expected=contract['common_equal']|o['facts_equal']|{o['tag']+'_Issued':int(post),o['tag']+'_Fault':0,o['tag']+'_Finished':0}
   if post:expected|=o.get('lease_facts',{})
   else:expected[o['tag']+'_Permit']=1
   for name,v in expected.items():
    for wrong in {-1,0,1,2,None}-{v}:
     assert not evaluate(cond,ff|{name:wrong},jj,extra),(o['key'],node,name,wrong);negative+=1
   for name,r in o['fact_ranges'].items():
    for wrong in [r['min']-1,r['max']+1,None]:assert not evaluate(cond,ff|{name:wrong},jj,extra);negative+=1
   for j in o['journals']:
    k=(j['path'],j['class']);allowed=['Active'] if post and k[0] in writes else [state[s] for s in j['states']]
    for wrong in ['Inactive','Active','Succeeded','Failed','Invalid',None]:
     result=evaluate(cond,ff,jj|{k:wrong},extra)
     assert result==(wrong in allowed),(o['key'],node,k,wrong,result)
     if result:positive+=1
     else:negative+=1
   if o['key']=='VOODOO':
    for ex in [extra|{'loaded':False},extra|{'open':True}]:assert not evaluate(cond,ff,jj,ex);negative+=1
   if o['key'] in ['MQ046','MQ047']:assert not evaluate(cond,ff,jj,extra|{'owned':True});negative+=1
  if o['key']=='BILL':
   assert nn[10]['type']['factName']=='PTFRB0S4BILL_QuestOwns' and nn[10]['type']['value']==1
   assert (4,'Out',10,'In') in ee and (10,'Out',89,'In') in ee
   assert not any(x.get('factName')=='PTFRB0S4BILL_QuestOwns' and x.get('value')==0 for n in g['nodes'] if n['$type']=='questFactsDBManagerNodeDefinition' for x in walk(n));checks+=3
  if o['key'] not in ['MQ306','VOODOO']:
   assert (92,'Out',102,'In') in ee and (102,'Out',101,'In') in ee
   assert not any(n['$type']=='questOutputNodeDefinition' for n in gg['root/100']['nodes']);checks+=2
 # No direct native fact writes in boot; only owned flags and the existing Bill lease.
 for o in contract['owners']:
  for n in graphs(build/'readback'/f"{o['key'].lower()}_boot.json")['root']['nodes']:
   if n['$type']=='questFactsDBManagerNodeDefinition':assert n['type']['factName'].startswith(o['tag']+'_') or n['type']['factName']=='PTFRB0S4BILL_QuestOwns';checks+=1
 proof=read(ROOT/m['official_comparison']);assert proof['status']=='PASS_OFFICIAL_BYTES'
 for dep,c in proof['comparisons'].items():assert sha(ROOT/c['source'])==sha(ROOT/c['official_witness'])==c['sha256'];checks+=1
 result={'status':'PASS_COMPONENT_NOT_LIVE','component_sha256':sha(build/'component.json'),'contract_sha256':sha(HERE/'contract.json'),'tester_sha256':sha(Path(__file__)),'native_payload_checks':checks,'native_payload_and_structure_checks':checks,'policy_cases':positive+negative,'positive_policy_cases':positive,'negative_policy_cases':negative,'official_byte_comparisons':len(proof['comparisons']),'owners':8,'resources':10,'journal_reactivation_count':3,'native_progress_resets':False,'game_writes':False,'pending':['Parent integration/resource audit and deployment','MQ306 exact phone journal guards are additional live reads; not captured','Gameplay/rewards/Johnny voice-hidden-body/reload and alternate progress states']}
 p=build/'tests.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
