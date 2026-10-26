"""Check packed native structure and exercise its decoded distance/cut lifecycle.

The small scheduler checks graph contracts; it does not emulate engine actor
acquisition or prove saved quest-node resumption. Those remain live checks.
"""
from pathlib import Path
import copy, hashlib, json, sys
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_02'
sys.path.insert(0,str(W/'tools'))
from test_b0_ordinary_vendor_batch import canonical, handles
from audit_wilson_vendor_owner import walk
from plan_b0_ordinary_vendor_batch import graph_at, nm, edge_set
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def check(value, label):
 assert value,label
 checks.append(label)
checks=[]
a=read(C/'fred_before.questphase.json')['Data']['RootChunk'];b=read(C/'fred_after.questphase.json')['Data']['RootChunk']
ah,bh=handles(a),handles(b)
def payload(n,h):return canonical({k:v for k,v in n.items() if k not in ('phaseGraph','sockets')},h)
for route in ('root','root/node5','root/node5/node14'):
 ga,gb=graph_at(a,route),graph_at(b,route);na,nb=nm(ga),nm(gb)
 inner=route.endswith('/node14')
 check(set(nb)==set(na)|({400,401,402,403} if inner else set()),route+' IDs')
 for i,n in na.items():
  pa,pb=payload(n,ah),payload(nb[i],bh)
  if inner and i in (4,5):pa.pop('condition');pb.pop('condition')
  check(pa==pb,f'{route}/{i} preserved payload/type')
 ea,eb=set(edge_set(ga,ah)),set(edge_set(gb,bh))
 if inner:
  expected=ea-{(5,'Out',6,'In')}|{(5,'Out',400,'In'),(400,'True',6,'In'),(400,'False',401,'In'),(401,'CutSource',3,'CutDestination'),(401,'CutSource',4,'CutDestination'),(401,'Out',402,'In'),(402,'Out',403,'In'),(403,'True',6,'In'),(403,'False',4,'In'),(403,'False',5,'In')}
  check(eb==expected,'Only enumerated private scene lifecycle edges')
 else:check(ea==eb,route+' edges preserved')
check(canonical({k:v for k,v in a.items() if k!='graph'},ah)==canonical({k:v for k,v in b.items() if k!='graph'},bh),'Root prefab/metadata preserved')
g=graph_at(b,'root/node5/node14');nodes=nm(g);edges=set(edge_set(g,bh))
normalized={i:payload(n,bh) for i,n in nodes.items()}
def condition(i):return normalized[i]['condition']
def evaluate(c,near,far,issued,fault):
 if c['$type']=='questLogicalCondition':
  v=[evaluate(x,near,far,issued,fault) for x in c['conditions']]
  return all(v) if c['operation']=='AND' else any(v)
 t=c['type'];op=t['comparisonType']
 if c['$type']=='questFactsDBCondition':
  actual={'PTFRS25_MQ025_FRESH_Issued':issued,'PTFRS25_MQ025_FRESH_Fault':fault}[t['factName']];wanted=t['value']
 elif c['$type']=='questDistanceCondition':
  ref=t['distanceDefinition1']['nodeRef2']['reference']['$value']
  assert ref in ('#wat_lch_melee_01','#loading_conditions_ent_wat_lch_melee_01')
  actual=near if ref=='#wat_lch_melee_01' else far;wanted=t['distanceDefinition2']['distanceValue']
 else:raise AssertionError(c['$type'])
 return {'Equal':actual==wanted,'NotEqual':actual!=wanted,'Less':actual<wanted,'Greater':actual>wanted}[op]
matrix=0
for issued in (0,1,2):
 for fault in (0,1):
  fresh=issued==1 and fault==0
  for near in (0,7.99,8,10,12,12.01,49.9,50,80):
   for far in (99,100,100.01):
    e=lambda i:evaluate(condition(i),near,far,issued,fault)
    check(e(4)==(near<(50 if fresh else 8)),'Admission boundary')
    check(e(5)==(far>100 or (not fresh and near>12)),'Departure boundary')
    check(e(402)==(e(4) or far>100),'Rearm or full departure boundary')
    check(e(400)==e(403)==(far>100),'Full departure branch')
    matrix+=1
check({d for s,o,d,t in edges if s==401 and o=='CutSource'}=={3,4},'Cut targets private scene and pending admission only')
check(normalized[300]==payload(nm(graph_at(a,'root/node5/node14'))[300],ah),'Original boxing scene unchanged')
check([v for n in normalized.values() for v in walk(n) if v.get('$type')=='questSetVar_NodeType']==[v for n in nm(graph_at(a,'root/node5/node14')).values() for v in walk(payload(n,ah)) if v.get('$type')=='questSetVar_NodeType'],'No new fact writer or counter reset')
class Model:
 def __init__(self,issued=0,fault=0):
  self.issued,self.fault=issued,fault;self.near=60;self.far=60;self.wait=set();self.scenes=set();self.spawn=False;self.requests=0;self.spawns=0;self.exits=0;self.queue=[];self.operations=0
 def send(self,i,s='Out'):
  self.queue.extend(d for a,o,d,t in edges if a==i and o==s)
 def advance(self,near,far=None):
  self.near=near;self.far=near if far is None else far
  start=self.operations
  while True:
   ready=[i for i in self.wait if evaluate(condition(i),self.near,self.far,self.issued,self.fault)]
   for i in ready:self.wait.remove(i);self.send(i)
   if not self.queue:return
   i=self.queue.pop(0);self.operations+=1
   assert self.operations-start<100,'Unbounded immediate loop'
   n=normalized[i];typ=n['$type']
   if typ=='questPauseConditionNodeDefinition':self.wait.add(i)
   elif typ=='questConditionNodeDefinition':self.send(i,'True' if evaluate(n['condition'],self.near,self.far,self.issued,self.fault) else 'False')
   elif typ=='questCutControlNodeDefinition':
    for a,s,d,t in edges:
     if a==i and s=='CutSource':self.wait.discard(d);self.scenes.discard(d)
    self.send(i)
   elif typ=='questSceneNodeDefinition':
    assert i not in self.scenes,'Duplicate scene request';self.scenes.add(i)
   elif typ=='questSpawnManagerNodeDefinition':
    if i==2:self.spawn=True;self.spawns+=1
    elif i==6:self.spawn=False
    else:raise AssertionError(i)
    self.send(i)
   elif typ=='questOutputNodeDefinition':self.wait.clear();self.scenes.clear();self.queue.clear()
   else:
    if i==202:self.requests+=1
    if i==201:self.exits+=1
    self.send(i)
# Start at ordinary 60m: spawn remains, scene waits without spinning.
m=Model();m.queue=[0];m.advance(60)
check(m.spawn and not m.scenes and m.wait=={402},'Distant service keeps NPC, no V scene')
ops=m.operations
for _ in range(200):m.advance(60)
check(m.operations==ops and m.spawns==1,'No distant spawn/retry churn')
m.advance(7);check(m.scenes=={3} and m.requests==1 and m.wait=={5},'Approach enters private scene once')
m.advance(10);check(m.scenes=={3} and m.requests==1,'Hysteresis holds current scene')
m.advance(13);check(not m.scenes and m.spawn and m.wait=={402} and m.exits==0,'Leave releases private scene only')
m.advance(10);check(not m.scenes,'No premature restart in dead band')
m.advance(7);check(m.scenes=={3} and m.requests==2 and m.spawns==1,'Revisit one scene, no duplicate NPC')
m.advance(110);check(not m.scenes and not m.spawn and not m.wait and m.exits==1,'Original far cleanup remains')
# A saved legacy active scene has its existing departure node5 pending.
m=Model();m.spawn=True;m.scenes={3};m.wait={5};m.advance(67)
check(m.spawn and not m.scenes and m.wait=={402} and m.requests==0 and m.spawns==0,'Legacy active branch releases without owner restart')
m=Model();m.spawn=True;m.wait={4,5};m.advance(67);m.advance(7)
check(m.scenes=={3} and m.requests==1 and m.wait=={5},'Legacy pending entry cannot double-request on return')
m=Model();m.spawn=True;m.wait={402};m.advance(67)
check(m.wait=={402} and m.requests==0 and m.spawns==0,'Saved new rearm wait has no replay')
m=Model(1,0);m.queue=[0];m.advance(49)
check(m.scenes=={300} and m.requests==1,'Fresh boxing retains 50m native scene admission')
m.advance(60);check(m.scenes=={300} and m.spawn and m.wait=={5},'Fresh boxing not cut by service range')
m.advance(110);check(not m.scenes and not m.spawn and m.exits==1,'Fresh boxing retains original departure')
build=read(C/'build_01.json')
check(build['resources']==26 and build['unchanged_resources']==25,'25 unrelated packed resources byte-identical')
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
check(sha(G/build['target'])==build['before']==sha(C/'before'/build['target']),'Installed baseline remains unchanged')
check(sha(C/'package'/build['target'])==build['after'],'Candidate archive pinned')
inputs=read(W/'diagnostics/scene_membership_20261025_01/inputs_01/receipt.json')
S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
check({str(p.relative_to(S)):sha(p) for p in S.rglob('*') if p.is_file()}==inputs['save_hashes'],'All 265 saved files unchanged')
out={'status':'PASS_FS1_OFFLINE_LIVE_PENDING','checks':len(checks),'condition_cases':matrix,'checks_detail':checks,'saved_files':len(inputs['save_hashes']),'sources':{str(p):sha(p) for p in (H/'build_02.ps1',Path(__file__),C/'build_01.json',C/'fred_before.questphase.json',C/'fred_after.questphase.json')},'limits':['Native graph model is not a game-engine execution test.','Resumed saved wait5 and scene ownership release need a cold-load check.','No REDscript change; no new compilation required.']}
p=C/'tests_01.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('sources','checks_detail')}))
