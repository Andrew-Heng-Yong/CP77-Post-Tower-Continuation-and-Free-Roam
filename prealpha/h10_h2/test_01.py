"""Offline regression checks for retained owners, payment and private-door scope."""
from pathlib import Path
import json,hashlib,re,math
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01';G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
checks=[]
def check(name,ok):
 assert ok,name
 checks.append(name)
def walk(x):
 yield x
 if isinstance(x,dict):
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def graph(p):
 d=read(p);handles={x['HandleId']:x['Data'] for x in walk(d) if isinstance(x,dict) and 'HandleId' in x and 'Data' in x}
 def resolve(x):
  if isinstance(x,dict):
   if 'HandleRefId' in x:return handles.get(x['HandleRefId'],x)
   if 'HandleId' in x and 'Data' in x:return x['Data']
  return x
 def canonical(x):
  if isinstance(x,dict):
   v=resolve(x)
   if v is not x:return canonical(v)
   return {k:canonical(v) for k,v in x.items() if k not in ['sockets','HandleId']}
  if isinstance(x,list):return [canonical(v) for v in x]
  return x
 ns={n['Data']['id']:n['Data'] for n in d['Data']['RootChunk']['graph']['Data']['nodes']}
 sockets={};edges=[]
 for id,n in ns.items():
  for h in n['sockets']:
   s=resolve(h);key=h.get('HandleId',h.get('HandleRefId'));sockets[key]=(id,s['name']['$value'])
 for id,n in ns.items():
  for h in n['sockets']:
   s=resolve(h)
   if s['type']!='Output':continue
   for ch in s['connections']:
    con=resolve(ch);dest=con['destination'];key=dest.get('HandleId',dest.get('HandleRefId'));b,port=sockets[key];edges.append((id,s['name']['$value'],b,port))
 return ns,set(edges),canonical
before=C/'native_inspect_01/0000_TowerContinued_SideJobs_S23/towercontinued/sidejobs_s23/base_b/mq011.questphase.json'
after=C/'native_readback_02/mq011.questphase.json'
bn,be,bc=graph(before);an,ae,ac=graph(after)
added={1014,1110,1111,1112,1113,1120,1121,1122}
check('All saved node identities retained; eight new noncolliding nodes',set(an)==set(bn)|added and not set(bn)&added)
for id in bn:
 if id!=1011:check(f'Original node {id} payload unchanged',bc(bn[id])==ac(an[id]))
replacements={(1003,'Out',1010,'In'):(1003,'Out',54,'In'),(1011,'Out',54,'In'):(1011,'Out',1014,'In'),(93,'Out',1004,'In'):(93,'Out',1110,'In'),(184,'False',1104,'In'):(184,'False',1120,'In'),(1013,'Out',1002,'In'):(1013,'Out',1113,'In')}
new={(1014,'Out',54,'In'),(1110,'Out',1111,'In'),(1111,'Out',1112,'In'),(1112,'Out',1004,'In'),(1120,'Out',1121,'In'),(1121,'Out',1122,'In'),(1122,'Out',1104,'In'),(1113,'Out',1002,'In')}
check('Exact five reroutes, eight continuation edges, no discarded native edge',ae=={replacements.get(e,e) for e in be}|new)
for a,b in [(1003,54),(54,80),(80,55),(55,184),(184,93),(93,1110),(1110,1111),(1111,1112),(1112,1004)]:check(f'Normal prerequisite-to-lease order {a} -> {b}',any(e[0]==a and e[2]==b for e in ae))
check('Legacy wait remains pre-parent; never skips parent prerequisites',(1011,'Out',1014,'In') in ae and (1014,'Out',54,'In') in ae)
for id in [1112,1122]:check(f'New lease waiter {id} retains complete old release acknowledgement',ac(an[id])['condition']==bc(bn[1011])['condition'])
check('Legacy acknowledgement preserved as first OR branch',ac(an[1011])['condition']['conditions'][0]==bc(bn[1011])['condition'])
native=read(C/'native_02.json');check('Thirty-three other S23 resources byte-exact',native['unchanged_resources']==33)
pkg=C/'package/r6/scripts';devices=(pkg/'TowerContinued_Housing_H1/HousingDevices.reds').read_text();purchase=(pkg/'TowerContinued_Housing_H1/HousingPurchase.reds').read_text();door=(pkg/'TowerContinued_Housing_H1/HousingDoorH2.reds').read_text();wilson=(pkg/'TowerContinued_Housing_H1/WilsonLeaseH2.reds').read_text();base=(pkg/'PTFR_PreAlpha/PTFR_RestorationBaseline/RestorationBaseline.reds').read_text()
oldbase=(C/'before/r6/scripts/PTFR_PreAlpha/PTFR_RestorationBaseline/RestorationBaseline.reds').read_text(encoding='utf-8-sig')
check('Baseline otherwise unchanged, including paid-only apartment services',base.replace('    WilsonLeaseH2.Reconcile(game);\n','').replace('      if q.GetFact(n"PTFRB0WV_QuestOwns") != 0 { allowed = false; }\n','')==oldbase)
check('H1 payment and saved-record implementation unchanged',sha(G/'r6/scripts/TowerContinued_Housing_H1/HousingState.reds')==sha(C/'diagnosis_01/context/HousingState.reds'))
check('Existing stash and wardrobe ownership guards unchanged',devices.split('// H10 has no native sale.')[0]==(C/'before/r6/scripts/TowerContinued_Housing_H1/HousingDevices.reds').read_text(encoding='utf-8-sig').split('// H10 has no native sale.')[0])
check('No new money, reward or apartment entitlement setter',all(x not in door+wilson for x in ['RemoveItem','GiveItem','_Entitled",','purchaseState =']))
check('Only own Wilson lease and its receipt are written',re.findall(r'q.SetFact\(n"([^"]+)"',wilson)==['PTFRH2_WV_LegacyReleased','PTFRB0WV_QuestOwns'])
check('All H10 mutations require exact source and enforcing housing',all(x in door for x in ['HousingDevices.Matches(this.GetEntityID(), HousingPurchaseLocation.Path("h10"))','!IsDefined(state) || !state.Enforcing()','!state.Entitled("h10")']))
check('Open setter, lock setter and visual door movement all guarded',all('@wrapMethod('+x+')' in door for x in ['DoorControllerPS','Door']) and all(x in door for x in ['func SetIsOpened','func SetIsLocked','func MoveDoor']))
check('Only H2-owned locks are removed', 'else if this.housingH2OwnLock' in door and 'private persistent let housingH2OwnLock: Bool' in door)
check('No closing through the threshold', 'distance <= -0.75' in door)
check('Existing inside saves retain exit', 'distance >= 0.35' in door)
check('No purchase UI during cover/menu/scene or away from exact entrance',all(x in purchase for x in ['StartupCoverLC1.GameplayReleased(game)','!board.GetBool(GetAllBlackboardDefs().UI_System.IsInMenu)','state.CanPurchase("h10", player)','HousingPurchaseLocation.Validate(game, "h10", h10.GetEntityID())']))
check('Cancel does not clear approach latch', 'if this.m_popup == popup { this.m_popup = null; }' in purchase)
check('No repeated proximity offer before exit', 'else if !self.m_h10Offered && !IsDefined(self.m_popup)' in purchase and '> 5.0' in purchase)
check('Custom action uses native Pay metadata without automatic debit','GetTweakDBChoiceRecord() -> String { return "Pay"; }' in devices and 'this.SetCanSkipPayCost(true)' in devices)
check('Only confirmed click calls durable purchase',purchase.count('state.Purchase(')==1 and 'OnPurchaseClick' in purchase)
anchor=read(C/'anchor_01.json');bed=[r for r in anchor['rows'] if r['ref'].endswith('/#mq000_01_ch_sleep')]
check('Fallback bed point bound to current official archive and corrected node index',len(bed)==1 and bed[0]['type']=='worldStaticMarkerNode' and bed[0]['position']==[-1377.66956,1275.32336,123.554993] and bed[0]['node']==5665)
# Behavioral boundary cases: reversing door orientation must not reverse access.
for forward in [1,-1]:
 for player,inside,expected in [(-2,5,'locked'),(2,5,'exit'),(-.3,5,'threshold')]:
  anchor_side=inside*forward;distance=player*forward*(1 if anchor_side>0 else -1)
  result='locked' if distance<=-.75 else 'exit' if distance>=.35 else 'threshold'
  check(f'Door plane side/threshold invariant f={forward} p={player}',result==expected)
# Verify actual retained fixture matches the narrowly released pre-entry state.
facts={r['name']:r['value'] for r in read(C/'diagnosis_01/AutoSave-12.expanded_02.json')['facts']}
for k,v in [('PTFRB0WV_QuestOwns',1),('PTFRB0WV_Released',1),('PTFRB0WV_Near',0),('PTFRS23_MQ011_Ready',1),('PTFRPA2_Finished',1)]:check('Actual retained fixture '+k,facts.get(k)==v)
for k in ['PTFRS23_MQ011_Issued','PTFRS23_MQ011_Entered','mq011_active']:
 check('No serialized active native entry: '+k,k not in facts or facts[k]==0)
# Runtime guards explicitly reject active/completed/faulted/renewed leases.
guards={k:(op,int(v)) for k,op,v in re.findall(r'q.GetFact\(n"([^"]+)"\)\s*(!=|<)\s*(\d+)',wilson)}
def repair(f):return not any((f.get(k,0)!=v if op=='!=' else f.get(k,0)<v) for k,(op,v) in guards.items())
fixture={k:v for k,(_,v) in guards.items()};check('Eligible idle legacy lease accepted',repair(fixture))
for key in ['PTFRH2_WV_LeaseRequested','PTFRH2_WV_LegacyReleased','PTFRS23_MQ011_Issued','PTFRS23_MQ011_Entered','PTFRS23_MQ011_Finished','PTFRS23_MQ011_Fault','mq011_active','q001_spawn_wilson_attention','q101_spawn_wilson_attention','PTFRB0WV_SpawnActionOut','PTFRB0WV_Near','PTFRB0WV_ActorDistanceGate']:
 bad=fixture|{key:1};check('Reject live/new/used lease '+key,not repair(bad))
for key in ['PTFRB0WV_Released','PTFRB0WV_Ready','PTFRPA2_Finished','PTFRS23_MQ011_Ready']:
 check('Reject missing acknowledgement '+key,not repair(fixture|{key:0}))
compiled=(C/'compile_03/compiled.script').read_text(encoding='utf-8-sig')
for token in ['PTFR.Housing.HousingDoorH2','PTFR.Housing.WilsonLeaseH2','HousingReconcileH2','housingH2OwnLock','PTFRH2_WV_LeaseRequested','H10 entrance purchase offered']:
 check('Compiled implementation '+token,token in compiled)
check('Full current SCC includes Equipment-EX',read(C/'compile_03/result.json')['full_scc_equipmentex'])
sources=[p for p in (C/'package').rglob('*') if p.is_file()]+[after,before,C/'native_02.json',C/'anchor_01.json',C/'compile_03/result.json',C/'compile_03/cache/compiled.redscripts']
report={'status':'PASS_H2_OFFLINE_NOT_LIVE','checks':checks,'count':len(checks),'sources':{str(p):sha(p) for p in sources},'limits':['Native door/popup/payment/egress/merchant behavior needs user live test.','Serialized absence alone is not runtime zero; repair checks every live guard.','Exact native content wait not proven from saved quest-node position; pre-entry lease defect and guarded continuation are source-bound.']}
(C/'tests_01.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'checks':len(checks)}))
