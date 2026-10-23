"""Validate the eight bounded native-parent components and refusal policy."""
import json,sys,copy,itertools
from pathlib import Path
from audit import ROOT,graphs,sha,load,walk,capture
from prepare import contract
HERE=Path(__file__).resolve().parent
STATES={1:'Inactive',2:'Active',3:'Succeeded',4:'Failed'}

def ev(c,f,j,inventory=0):
 if c['$type']=='questLogicalCondition':
  parts=[ev(v,f,j,inventory) for v in c['conditions']]
  return all(parts) if c['operation']=='AND' else any(parts)
 t=c['type']
 if c['$type']=='questJournalCondition':return j.get(t['path']['realPath'])==t['state']
 if c['$type']=='questObjectCondition':
  assert t['$type']=='questInventory_ConditionType' and t['isPlayer']==1 and t['itemID']['hash']==81386061912
  assert t['quantity']==0 and t['comparisonType']=='Equal';return inventory==0
 assert c['$type']=='questFactsDBCondition'
 a=f.get(t['factName']);b=t['value']
 if a is None:return False
 return {'Equal':lambda:a==b,'GreaterOrEqual':lambda:a>=b,'LessOrEqual':lambda:a<=b}[t['comparisonType']]()

def verify(out):
 spec=load(HERE/'contract.json');assert spec==contract()
 m=load(out/'manifest.json');checks=cases=0;limits=[]
 for p,h in m['source_pins'].items():assert sha(ROOT/p)==h,p;checks+=1
 original={g['path']:g for g in graphs(ROOT/(spec['owners'][0]['native_source'].replace('/raw/','/json/')+'.json'))};on={n['id']:n for n in original['root']['nodes']}
 for s,r in zip(spec['owners'],m['rows']):
  assert r['id']==s['id'] and sha(Path(r['raw']))==r['sha256']
  actual={g['path']:g for g in graphs(Path(r['json']))};n={v['id']:v for v in actual['root']['nodes']};ids=s['selected_nodes'];es={tuple(e) for e in actual['root']['edges']}
  assert set(n)==set(ids)|set(range(1000,1012))|set(range(1100,1100+2*len(s['target_nodes'])))
  for i in ids:assert n[i]==on[i],(s['id'],'native node drift',i);checks+=1
  for path,g in original.items():
   if path!='root' and int(path.split('/')[1]) in ids:assert actual[path]==g,(s['id'],path);checks+=len(g['nodes'])
  assert set(actual)=={'root'}|{p for p in original if p!='root' and int(p.split('/')[1]) in ids}
  expected={tuple(e) for e in s['native_edges'] if e[0]!=0 and e[2] not in s['target_nodes']}
  expected|={(0,'Out',1000,'In'),(1000,'Out',1001,'In'),(1001,'Out',1002,'In'),(1002,'True',1003,'In'),(1002,'False',1009,'In'),(1003,'Out',1004,'In'),(1004,'True',1005,'Active'),(1005,'Out',1006,'In'),(1006,'Out',1007,'In'),(1004,'False',1007,'In'),(1007,'Out',1008,'In'),(1008,'False',1009,'In'),(1010,'Out',1011,'In')}
  expected|={(1008,'True',e[2],e[3]) for e in s['native_edges'] if e[0]==0}
  for k,target in enumerate(s['target_nodes']):
   gate=1100+2*k;expected|={(e[0],e[1],gate,'In') for e in s['native_edges'] if e[2]==target};expected|={(gate+1,'Out',target,e[3]) for e in s['native_edges'] if e[2]==target}
   expected|={(gate,'True',gate+1,'In'),(gate,'False',1009,'In'),(gate+1,'Out',1010,'In')}
   assert n[gate]['condition']==n[1007]['condition'];checks+=1
  assert es==expected,(s['id'],'edge mismatch',es^expected)
  assert n[1001]['condition']==n[1002]['condition'] and n[1007]['condition']==n[1008]['condition']
  # Root-only conditional write, no recursive child-state operation.
  jt=n[1005]['type'];assert jt['path']['realPath']==s['root'] and jt['sendNotification']==0 and jt['trackQuest']==0
  assert set(jt)=={'$type','optional','path','sendNotification','trackQuest','version'}
  assert n[1004]['condition']['type']['state']=='Failed'
  for i,v in n.items():
   if i not in ids and v['$type']=='questFactsDBManagerNodeDefinition':assert v['type']['factName'].startswith(s['tag']+'_') and v['type']['value']==1 and v['type']['setExactValue']==1;checks+=1
  f=dict(m['common'])|s['facts_equal']|{s['tag']+'_Permit':1,s['tag']+'_Issued':0,s['tag']+'_Finished':0,s['tag']+'_Fault':0,s['tag']+'_RootReactivated':0}
  for key,v in s['fact_ranges'].items():f[key]=v['min']
  if s['phone_dependency']:f[s['phone_dependency']]=1
  js={v['path']:STATES[v['states'][0]] for v in s['journals']};g=n[1001]['condition'];ack=n[1007]['condition'];assert ev(g,f,js);cases+=1
  for key,val in f.items():
   if key.endswith('_RootReactivated'):continue
   for wrong in [None,-1,0,1,2,999]:
    if key in s['fact_ranges']:
     expect=wrong is not None and s['fact_ranges'][key]['min']<=wrong<=s['fact_ranges'][key]['max']
    else:expect=wrong==val
    assert ev(g,f|{key:wrong},js)==expect,(s['id'],key,wrong);cases+=1
  for row in s['journals']:
   for state in [None,'Inactive','Active','Succeeded','Failed','Unknown']:
    assert ev(g,f,js|{row['path']:state})==(state in [STATES[i] for i in row['states']]);cases+=1
  af=f|{s['tag']+'_Issued':1,s['tag']+'_Permit':0};assert ev(ack,af,js);cases+=1
  assert not ev(ack,af,js|{s['root']:'Failed'});cases+=1
  assert not ev(ack,af,js|{s['root']:'Active'});cases+=1
  assert ev(ack,af|{s['tag']+'_RootReactivated':1},js|{s['root']:'Active'});cases+=1
  assert not ev(ack,af|{s['tag']+'_RootReactivated':1},js);cases+=1
  for key in s['facts_equal']:
   assert not ev(ack,af|{key:1},js);cases+=1
  for state in ['Succeeded','Active',None,'Unknown']:
   assert not ev(g,f,js|{s['root']:state});cases+=1
  if s['key']=='MQ007':assert not ev(g,f,js,1);cases+=1
  captured=capture()[s['id']];cf=f|captured['facts'];cj={j['path']:j['state'] for j in captured['journals']}
  assert ev(g,cf,cj)==s['capture_progress_match'];cases+=1
  limits.append({'id':s['id'],'captured_progress_matches_bounded_guard':s['capture_progress_match'],'native_unlock_gates_retained':True,'live_verified':False})
 # Passive flags are genuinely before player interaction, not assumed fresh.
 stud=ROOT/'research/activity_state_r3/native_sources/json/base/quest/minor_quests/mq012/mq012.questphase.json'
 sg=next(g for g in graphs(stud) if g['path']=='root/12');sn={n['id']:n for n in sg['nodes']};assert sn[2]['type']['factName']=='mq012_active' and sn[2]['type']['setExactValue']==1
 vets=ROOT/'research/activity_state_r3/native_sources/json/base/quest/minor_quests/mq002/phases/mq002_beginning.questphase.json'
 vg=next(g for g in graphs(vets) if g['path']=='root');vn={n['id']:n for n in vg['nodes']};assert {(0,'Out',9,'In'),(9,'Out',8,'In')}<={tuple(e) for e in vg['edges']};assert vn[9]['type']['factName']=='mq002_active' and vn[8]['condition']['$type']=='questTriggerCondition';checks+=4
 # Original Sex on Wheels delay and prerequisite, Sandra data/main single owner.
 assert on[148]['condition']['type']['factName']=='gle_06_finished' and on[150]['condition']['type']['days']==3
 assert spec['owners'][0]['target_nodes']==[9,128];checks+=2
 return {'status':'PASS_BOUNDED_NATIVE_COMPONENTS_LIVE_PENDING','component_sha256':sha(out/'manifest.json'),'tester_sha256':sha(Path(__file__)),'native_payload_checks':checks,'policy_cases':cases,'limits':limits}

if __name__=='__main__':print(json.dumps(verify(Path(sys.argv[1])),indent=2))
