"""Independent S22 EP1 native payload, transition and guard checks (not live)."""
import json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).parent
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'prealpha/ncpd_scanner_n1')]
from native_inspect import SafeResource
from audit_activity_batches_b1 import flatten
from catalog_gig_rollout_r2 import walk,value
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def graphs(p):
 r=SafeResource(read(p));return {g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
def nodes(g):return {n['id']:n for n in g['nodes']}
def edges(g):return set(map(tuple,g['edges']))
def evaluate(c,f,j,outside):
 t=c['$type']
 if t=='questLogicalCondition':
  v=[evaluate(x,f,j,outside) for x in c['conditions']]
  return all(v) if c['operation']=='AND' else any(v)
 if t=='questJournalCondition':
  typ=c['type'];return j.get((typ['path']['realPath'],value(typ['path']['className'])))==typ['state']
 if t=='questTriggerCondition':
  assert c['type']=='IsOutside' and c['isPlayerActivator']==1
  return outside.get(value(c['triggerAreaRef']),False)
 assert t=='questFactsDBCondition',t
 typ=c['type'];a=f.get(typ['factName']);b=typ['value']
 return a is not None and ({'Equal':a==b,'GreaterOrEqual':a>=b}[typ['comparisonType']])
def main():
 build=Path(sys.argv[1]);spec=read(HERE/'admission.json');m=read(build/'component.json')
 for p,h in m['source_pins'].items():assert sha(ROOT/p)==h,p
 for p,h in [(m['depot'],m['sha256']),(m['boot'],m['boot_sha256'])]:assert sha(build/'source'/p)==h
 nativepath=ROOT/'research/activity_state_r3/native_sources/json/ep1/quest/main_quests/q304/phases/q304_car_retrieval.questphase.json'
 native=graphs(nativepath);resume=graphs(build/'readback/moving_heat_resume.json');copied=0
 excluded={2,252,253};assert not native['root/2']['nodes'] and not native['root/2']['edges']
 assert set(resume)==set(native)-{'root/2'},(set(resume)-set(native),set(native)-set(resume))
 for path,g in resume.items():
  old=native[path]
  if path!='root':assert g==old,path;copied+=len(g['nodes']);continue
  nn,on=nodes(g),nodes(old);assert set(nn)==set(on)-excluded
  for i,n in nn.items():assert n==on[i],i;copied+=1
  wanted={e for e in edges(old) if e[0] not in excluded and e[2] not in excluded}
  wanted|={(0,'Out',115,'In1'),(115,'Out1',164,'In'),(115,'Out1',65,'In1'),(115,'Out1',325,'In1')}
  assert edges(g)==wanted
  assert not any(n.get('phaseResource',{}).get('DepotPath',{}).get('$value','').endswith('q304_car_retrieval_messages.questphase') for n in nn.values())
 boot=graphs(build/'readback/moving_heat_boot.json');assert set(boot)=={'root','root/10'} and not boot['root/10']['nodes'];b=nodes(boot['root']);assert set(b)==set(range(13))
 expectededges={(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'False',2,'In'),(3,'True',4,'In'),(4,'Out',5,'Active'),(5,'Out',6,'Active'),(6,'Out',7,'Active'),(7,'Out',8,'In'),(8,'Out',9,'In'),(9,'False',12,'In'),(9,'True',10,'In1'),(10,'Out1',11,'In')}
 assert edges(boot['root'])==expectededges
 assert b[2]['condition']==b[3]['condition']
 for i,suffix in [(1,'Ready'),(4,'Issued'),(11,'Finished'),(12,'Fault')]:
  assert b[i]['type']=={'$type':'questSetVar_NodeType','factName':'PTFRS22_Q304_'+suffix,'setExactValue':1,'value':1}
 assert not any(n['$type']=='questOutputNodeDefinition' for n in b.values())
 for i,j in zip(range(5,8),spec['reactivate']):
  t=b[i]['type'];assert t['$type']=='questJournalQuestEntry_NodeType'
  assert (t['path']['realPath'],value(t['path']['className']))==(j['path'],j['class']) and j['state']==4
 assert b[10]['phaseResource']['DepotPath']['$value']==m['depot']
 assert b[8]['condition']['type']=={'$type':'questRealtimeDelay_ConditionType','hours':0,'miliseconds':100,'minutes':0,'seconds':0}
 states={1:'Inactive',2:'Active',3:'Succeeded',4:'Failed'}
 pre={ (j['path'],j['class']):states[j['state']] for j in spec['journal_guards']}
 post={ k:('Active' if v=='Failed' else v) for k,v in pre.items() }
 assert sum(v=='Failed' for v in pre.values())==3 and list(pre.values()).count('Succeeded')==1
 base=spec['common_guard_equal']|spec['guard_equal']|{'PTFRS22_Q304_Issued':0,'PTFRS22_Q304_Finished':0,'PTFRS22_Q304_Fault':0,'PTFRS22_Q304_Permit':1,'q305_done':0,'q306_done':1}
 outside={x:True for x in spec['outside_triggers']};positive=negative=0
 for node,j,f in [(2,pre,base),(9,post,base|{'PTFRS22_Q304_Issued':1})]:
  c=b[node]['condition'];assert evaluate(c,f,j,outside);positive+=1
  expected=spec['common_guard_equal']|spec['guard_equal']|{'PTFRS22_Q304_Issued':int(node==9),'PTFRS22_Q304_Finished':0,'PTFRS22_Q304_Fault':0}
  if node==2:expected['PTFRS22_Q304_Permit']=1
  actual={x['type']['factName']:x['type']['value'] for x in c['conditions'] if x['$type']=='questFactsDBCondition'}
  assert expected==actual
  for k,v in expected.items():
   for wrong in [-1,0,1,2,None]:
    if wrong!=v:assert not evaluate(c,f|{k:wrong},j,outside),(node,k,wrong);negative+=1
  for k,v in j.items():
   for wrong in ['Inactive','Active','Succeeded','Failed','Invalid',None]:
    if node==2 and v=='Failed' and wrong=='Inactive':assert evaluate(c,f,j|{k:wrong},outside);positive+=1;continue
    if wrong!=v:assert not evaluate(c,f,j|{k:wrong},outside),(node,k,wrong);negative+=1
  for x in outside:assert not evaluate(c,f,j,outside|{x:False});negative+=1
  assert not evaluate(c,f|{'q305_done':0,'q306_done':0},j,outside);negative+=1
  assert evaluate(c,f|{'q305_done':1,'q306_done':0},j,outside);positive+=1
 # Permit can be withdrawn after Issued without obstructing post-write proof.
 assert evaluate(b[9]['condition'],base|{'PTFRS22_Q304_Issued':1,'PTFRS22_Q304_Permit':0},post,outside);positive+=1
 # Verify native dependencies against newly extracted installed official bytes.
 newroot=ROOT/'research/sidejobs_s22/ep1_jobs/native_02';oldroot=ROOT/'research/activity_state_r3/native_sources'
 official=0;resources={}
 for p in (newroot/'raw/ep1/quest/main_quests/q304').rglob('*.questphase'):
  rel=p.relative_to(newroot/'raw');assert p.read_bytes()==(oldroot/'raw'/rel).read_bytes(),str(rel);official+=1
  jp=newroot/'json'/str(rel.with_suffix(rel.suffix+'.json'));resources[str(rel).replace('/','\\')]=read(jp)
 assert official==8
 scenes={p.relative_to(newroot/'json').as_posix().removesuffix('.json').replace('/','\\'):read(p) for p in (newroot/'json/ep1/quest/main_quests/q304/scenes').glob('*.json')}
 assert len(scenes)==3
 refs={x['$value'] for d in resources.values() for x in walk(d) if x.get('$type')=='ResourcePath' and x.get('$storage')=='string' and x['$value'].endswith(('.questphase','.scene'))}
 assert not refs-set(resources)-set(scenes),refs-set(resources)-set(scenes)
 journal=read(ROOT/'research/sidejobs_s22/ep1_jobs/mq306_details_01.json')
 assert len(journal['journals'])==41 and len(journal['fact_names'])==108
 assert len({j['path'] for j in journal['journals']})==41
 result={'status':'PASS_COMPONENT_NOT_LIVE','component_sha256':sha(build/'component.json'),'tester_sha256':sha(Path(__file__)),'native_payload_checks':copied,'negative_guard_cases':negative,'positive_guard_cases':positive,'official_phase_byte_checks':official,'original_scene_dependencies':3,'journal_reactivations':3,'progress_journals_preserved':17,'mq306_detail_only':True,'pending':['parent S22 runtime integration, archive packing, CRC/resource audits and install','native journal state transition and real interaction test','actual completion/reward/reload','MQ306 runtime stage capture and adapter']}
 dest=build/'tests.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
