"""Source-bound H1 housing payload/ownership tests. Not engine or payment simulation."""
import copy,hashlib,itertools,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import walk,value
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def graphs(p):
 r=SafeResource(read(p));return {g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
def nodes(g):return {n['id']:n for n in g['nodes']}
def normalized(o):
 handles={}
 def collect(x):
  if isinstance(x,dict):
   if 'HandleId' in x:
    assert x['HandleId'] not in handles or handles[x['HandleId']]==x['Data'],'duplicate handle'
    handles[x['HandleId']]=x['Data']
   for v in x.values():collect(v)
  elif isinstance(x,list):
   for v in x:collect(v)
 collect(o)
 def deref(x,active=frozenset()):
  if isinstance(x,list):return [deref(v,active) for v in x]
  if not isinstance(x,dict):return x
  if 'HandleRefId' in x:
   key=x['HandleRefId']
   if key=='-1':return None
   assert key in handles,('unresolved handle',key)
   assert key not in active,('unexpected scene handle cycle',key)
   return deref(handles[key],active|{key})
  if 'HandleId' in x:return deref(x['Data'],active|{x['HandleId']})
  return {k:deref(v,active) for k,v in x.items()}
 return deref(o)

def facts(o):return {v['factName']:(v['comparisonType'],v['value']) for v in walk(o) if v.get('$type')=='questVarComparison_ConditionType'}
def evaluate(c,fs,items=None):
 t=c['$type']
 if t=='questLogicalCondition':
  v=[evaluate(x,fs,items) for x in c['conditions']];return all(v) if c['operation']=='AND' else any(v)
 if t=='questFactsDBCondition':return evaluate(c['type'],fs,items)
 if t=='questVarComparison_ConditionType':
  a=fs.get(c['factName']);b=c['value']
  if a is None:return False
  return {'Equal':lambda:a==b,'Greater':lambda:a>b,'GreaterOrEqual':lambda:a>=b}[c['comparisonType']]()
 raise ValueError(t)
def main():
 folder=Path(sys.argv[1]).resolve();out=folder/'tests.json';assert not out.exists();c=read(folder/'component.json');checks=0;native=0;cases=0
 def check(ok,why):
  nonlocal checks
  assert ok,why;checks+=1
 for p,h in c['source_pins'].items():check(sha(ROOT/p)==h,('pin',p))
 for p,h in c['resources'].items():check(sha(folder/'source'/p)==h,('resource',p))
 check(len(c['resources'])==17 and len(c['boots'])==6,'six bounded owners, nine scenes, two same-owner overlays')
 check(set(c['override_donors'])=={r'towercontinued\b0_h10_persistent\h10_owner.questphase',r'towercontinued\relationship_mirrors\m10_owner.questphase'},'only H10 and Judy saved-owner mod overrides')
 check(c['override_donors'][c['donor']['rows'][0]['depot']]==c['donor']['rows'][0]['raw_sha256'],'actual packed donor bound')
 old=graphs(ROOT/c['donor']['rows'][0]['json']);new=graphs(folder/'readback/h10_persistent_owner.json');check(old.keys()==new.keys(),'H10 graph identities')
 for gp,g in old.items():
  check(g['edges']==new[gp]['edges'],('H10 same edges',gp));a=nodes(g);b=nodes(new[gp]);check(a.keys()==b.keys(),'H10 same node IDs')
  for ident,n in a.items():
   if gp=='root' and ident==2:
    check(b[ident]['condition']['operation']=='AND' and b[ident]['condition']['conditions'][0]==n['condition'],'H10 original wait exact first conjunct')
    add=b[ident]['condition']['conditions'][1];check(add['operation']=='OR' and facts(add)=={'PTFRH1_Ready':('Equal',0),'PTFRH1_h10_Entitled':('Equal',1)},'pre-migration unchanged, later entitlement gate')
    bb=copy.deepcopy(b[ident]);bb['condition']=n['condition'];check(bb==n,'condition-only H10 node delta')
    for ready,owned in itertools.product([None,-1,0,1,2],repeat=2):
     check(evaluate(add,{'PTFRH1_Ready':ready,'PTFRH1_h10_Entitled':owned})==(ready==0 or owned==1),'H10 availability truth table');cases+=1
   else:check(n==b[ident],('H10 unchanged payload',ident))
   native+=1
 # Judy delayed native waits both recheck the pre-existing suspension control.
 old=graphs(ROOT/c['m10_donor']['json']);new=graphs(ROOT/c['m10_override_readback']);check(old.keys()==new.keys(),'Judy graph identities');check(sha(ROOT/c['m10_override_readback'])==c['m10_override_readback_sha256'],'Judy exact readback pin')
 for gp,g in old.items():
  check(g['edges']==new[gp]['edges'],'Judy same exact edges');a=nodes(g);b=nodes(new[gp]);check(a.keys()==b.keys(),'Judy same node IDs')
  for ident,n in a.items():
   expected=copy.deepcopy(n)
   if ident in [7,13]:
    cond=b[ident]['condition'];check(cond['operation']=='AND' and cond['conditions'][0]==n['condition'],'Judy original wait retained');check(facts(cond['conditions'][1])=={'PTFRRM10_Suspended':('Equal',0)},'Judy late suspension guard');expected['condition']=cond
   check(expected==b[ident],('Judy exact payload delta',ident));native+=1
 # Every private scene is precisely the prepared bounded source; inspect actual reachable payload.
 for inp in c['presentation']['inputs']:
  rb=folder/'readback'/(inp['depot'].rsplit('\\',1)[-1]+'.json');actual=read(rb)['Data']['RootChunk'];expected=read(ROOT/inp['expected'])['Data']['RootChunk']
  check(normalized(actual)==normalized(expected),('prepared scene equality',inp['depot']))
  ns={h['Data']['nodeId']['id']:h['Data'] for h in actual['sceneGraph']['Data']['graph']};start=actual['entryPoints'][0]['nodeId']['id'];seen=set();todo=[start]
  while todo:
   n=todo.pop()
   if n in seen:continue
   check(n in ns,'all scene edges resolve');seen.add(n);todo += [d['nodeId']['id'] for s in ns[n].get('outputSockets',[]) for d in s['destinations']]
  check(seen==set(ns),'no disconnected retained scene nodes');native+=len(ns)
  check(not {'kerry','johnny_mirror'} & {value(a['actorName']) for a in actual['actors']},'no excluded acquisition')
  writes=[v for n in ns.values() for v in walk(n) if v.get('$type')=='questSetVar_NodeType']
  if inp['kind']=='purchase':
   check(len(ns)==5 and len(actual['actors'])==0 and actual['props']==[],'choice-only five-node scene')
   check([(v['factName'],v['setExactValue'],v['value']) for v in writes]==[('PTFRH1_'+inp['id']+'_PurchaseRequest',1,1)],'explicit selection writes only own request')
   check(not any(v.get('$type') in ['questPaymentBalanced_ConditionType','PaymentBalanced_ScriptConditionType','questAddRemoveItem_NodeType'] for n in ns.values() for v in walk(n)),'native choice cannot charge or grant')
   check(len([v for n in ns.values() for v in walk(n) if v.get('$type')=='questVarComparison_ConditionType' and v.get('factName')=='PTFRH1_'+inp['id']+'_PurchaseReady'])==2,'ready-only availability and cancellation')
  else:
   check(not any('purchased' in v['factName'] or 'kerry' in v['factName'] or v['factName'].startswith('mq055_') for v in writes),'no service acquisition/dating writes')
   check([value(e['name']) for e in actual['entryPoints']]==['in'],'only bounded default service entry')
 for recipe in c['recipes']:
  id=recipe['id'];src=graphs(ROOT/recipe['source']['json']);sg=src[recipe['marker']['graph']];on=nodes(sg);new=graphs(folder/'readback'/(id+'_owner.json'));ns=nodes(new['root']);edges=new['root']['edges'];own='PTFRH1_'+id+'_'
  for target in [11,26]:
   expected=copy.deepcopy(on[recipe['marker']['node']]);expected['id']=target;check(ns[target]==expected,('exact native home marker',id,target));native+=1
  check([11,'Out',12,'In'] in edges and ns[12]['type']['factName']==own+'LossApplied','loss acknowledgement after marker')
  check([26,'Out',27,'In'] in edges and ns[27]['type']['factName']==own+'AccessApplied','paid access acknowledgement after marker')
  lossfacts=facts(ns[10]['condition']);accessfacts=facts(ns[20]['condition'])
  check(lossfacts[own+'Entitled']==('Equal',0) and lossfacts[own+'LossPermit']==('Equal',1) and lossfacts[own+'LossApplied']==('Equal',0) and lossfacts[own+'ServiceActive']==('Equal',0),'bounded idle one-time loss')
  check(accessfacts[own+'Entitled']==('Equal',1) and accessfacts[own+'AccessPermit']==('Equal',1) and accessfacts[own+'AccessApplied']==('Equal',0) and accessfacts[own+'LossApplied']==('Equal',1),'paid one-time access')
  for condition in [ns[10]['condition'],ns[20]['condition']]:
   fields=facts(condition);positive={k:v for k,(op,v) in fields.items()};positive.update({k:v+1 for k,(op,v) in fields.items() if op=='Greater'});check(evaluate(condition,positive),'positive native gate');cases+=1
   for key,(op,v) in fields.items():
    for wrong in [None,-1,v+1 if op=='Equal' else v]:
     bad=positive|{key:wrong};check(not evaluate(condition,bad),('single-field contradiction',id,key,wrong));cases+=1
  check(read(folder/'readback'/(id+'_owner.json'))['Data']['RootChunk']['phasePrefabs']==[],'no root activation before ready')
  if id=='h10':
   check(lossfacts['PTFRH1_RelationshipsApplied']==('Equal',1),'relationship policy complete before H10 loss ack')
   check([109,'Out',110,'In'] in edges and ns[110]['type']['factName']=='PTFRH1_RelationshipsApplied','relationship acknowledgement after exact POIs')
   check([104,'True',106,'Inactive'] in edges and [104,'False',105,'In'] in edges,'earned Kerry never suspended by policy branch')
   check([(ns[x]['type']['factName'],ns[x]['type']['value']) for x in [101,102,103,105]]==[('PTFRRM7_Suspended',1),('PTFRRM10_Suspended',1),('PTFRRM13_Suspended',1),('PTFRRM20_Suspended',1)],'only existing mirror entry suspension controls')
   check([ns[x]['type']['path']['realPath'] for x in [106,107,108,109]]==['points_of_interest/safehouses/'+h for h in ['judys_apartment','river_trailer_park','nomad_camp_01','nomad_camp_02']],'four exact non-Kerry home POIs only')
   check(lossfacts['PTFRB0H10P_Enabled']==('Equal',0),'saved reusable H10 control revoked before loss ack');check([10,'Out',11,'Inactive'] in edges and [20,'Out',26,'Active'] in edges,'H10 marker-only migration, public transit untouched')
   check(not any(v.get('$type')=='RegisterFastTravelPointsRequest' for n in ns.values() for v in walk(n)),'H10 public transit preserved');continue
  key=recipe['key'];expected=copy.deepcopy(on[key['node']]);expected['id']=22;check(ns[22]==expected,'exact key grant only');native+=1
  inventory=[v for v in walk(ns[21]) if v.get('$type')=='questInventory_ConditionType'];check(len(inventory)==1 and inventory[0]['isPlayer']==1 and inventory[0]['quantity']==0 and inventory[0]['comparisonType']=='Equal','missing key only')
  keyhash=next(v['itemID']['hash'] for v in walk(ns[22]) if v.get('$type')=='questAddRemoveItem_NodeTypeParams');check(inventory[0]['itemID']['hash']==keyhash,'exact key query')
  has=[v for v in walk(ns[23]) if v.get('$type')=='questInventory_ConditionType'];check(len(has)==1 and has[0]['itemID']['hash']==keyhash and has[0]['quantity']==1 and has[0]['comparisonType']=='GreaterOrEqual','ack waits actual key ownership')
  for target,enabled in [(13,0),(25,1)]:
   expected=copy.deepcopy(on[key['travel_node']]);expected['id']=target;expected['event']['register']=enabled;expected['event']['fastTravelNodes'][0]['markerRef']['$value']=key['travel_registry']['path'];check(ns[target]==expected,'exact apartment fast travel registration delta');native+=1
  check([10,'Out',13,'In'] in edges and [13,'Out',11,'Inactive'] in edges,'unregister home point before loss ack')
  check([21,'True',22,'In'] in edges and [21,'False',23,'In'] in edges and [22,'Out',23,'In'] in edges and [23,'Out',25,'In'] in edges,'key check/grant/verify sequence')
  sourceRoot=read(ROOT/recipe['source']['json'])['Data']['RootChunk'];check(ns[32]['phaseInstancePrefabs']==sourceRoot['phasePrefabs'],'exact scoped native context')
  scoped=new['root/32'];sn=nodes(scoped);row=next(r for r in read(ROOT/'research/housing_h1/native/catalog_01.json')['properties'] if r['id']==id);nativeService=src[row['service_graph']];os=nodes(nativeService)
  check(sn[10]['condition']['conditions'][-1]==os[row['service_wait_node']]['condition'],'original service condition retained')
  first=next(e[2] for e in nativeService['edges'] if e[0]==0);check(sn[20]['condition']['conditions'][-2]==os[first]['condition'],'original local purchase AND/OR predicate retained')
  check(facts(sn[20]['condition'])['q101_done']==('Greater',0),'normal original global purchase prerequisite')
  check(facts(sn[20]['condition'])[own+'PurchaseRequest']==('Equal',0),'no automatic repeated purchase request')
  check([22,'out',23,'In'] in scoped['edges'] and [23,'Out',20,'In'] in scoped['edges'],'one saved purchase scene loop')
  check(facts(sn[10]['condition'])[own+'Entitled']==('Equal',1) and facts(sn[20]['condition'])[own+'Entitled']==('Equal',0),'purchase and service mutually exclusive')
  check(not any(n['$type'] in ['questSpawnManagerNodeDefinition','questDeviceManagerNodeDefinition','questCharacterManagerNodeDefinition'] for g in new.values() for n in g['nodes']),'no NPC replay/door lock/character mutation')
 k=graphs(folder/'readback/kerry_visitor_owner.json');kn=nodes(k['root']);check(facts(kn[1]['condition'])['sq028_kerry_friend']==('GreaterOrEqual',1) and facts(kn[1]['condition'])['sq028_kerry_relationship']==('GreaterOrEqual',1),'Kerry earned fact predicates')
 earned=kn[1]['condition']['conditions'][-3];check(earned['operation']=='OR','native Kerry friend/relationship OR')
 for f,r in itertools.product([None,-1,0,1,2],repeat=2):check(evaluate(earned,{'sq028_kerry_friend':f,'sq028_kerry_relationship':r})==((f is not None and f>=1) or (r is not None and r>=1)),'Kerry earned OR truth table');cases+=1
 check(not any(v.get('$type')=='questSetVar_NodeType' and not v['factName'].startswith('PTFRH1_kerry_') for g in k.values() for n in g['nodes'] for v in walk(n)),'Kerry native history untouched')
 result={'status':'PASS_HOUSING_H1_NATIVE_SOURCE_POLICY_ENGINE_PENDING','component_sha256':sha(folder/'component.json'),'tester_sha256':sha(__file__),'checks':checks,'native_payload_checks':native,'policy_cases':cases,'limitations':['Saved old H10 wait reuse, scene interruption cleanup, device/fast-travel behavior and payment require live verification.','Tests verify exact source payloads and ownership guards; they do not simulate engine execution.']};out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
