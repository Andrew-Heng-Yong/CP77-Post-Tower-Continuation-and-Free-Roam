"""Verify serialized lifecycle payloads and bounded retirement truth table."""
import copy,hashlib,itertools,json
from pathlib import Path
H=Path(__file__).resolve().parent
C=H/'candidate_02'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
native=read(H/'native_root_01.json');current=read(C/'owner_readback_01.json')
before=read(C/'owner_prewrite_01.json');old=read(H/'cooked_root_01.json')
checks=[]
def check(ok,label):
 assert ok,label
 checks.append(label)
def index(data):
 out={}
 def walk(v):
  if isinstance(v,dict):
   if 'HandleId' in v and 'Data' in v:out[v['HandleId']]=v['Data']
   for x in v.values():walk(x)
  elif isinstance(v,list):
   for x in v:walk(x)
 walk(data);return out
def normalize(v,handles):
 if isinstance(v,dict):
  if 'HandleRefId' in v and len(v)==1:return normalize(handles[v['HandleRefId']],handles)
  if 'HandleId' in v and 'Data' in v:return normalize(v['Data'],handles)
  return {k:normalize(x,handles) for k,x in v.items() if k not in ['sockets','HandleId','HandleRefId']}
 if isinstance(v,list):return [normalize(x,handles) for x in v]
 return v
def graph(data):return data['Data']['RootChunk']['graph']['Data']
def node(g,n):return next(h['Data'] for h in g['nodes'] if h.get('Data',{}).get('id')==n)
nh=index(native);ch=index(current);oh=index(old)
ng=graph(native);cg=graph(current);og=graph(old)
loop=node(cg,10)['phaseGraph']['Data']
na=copy.deepcopy(node(ng,3));ca=node(loop,3)
na['phaseInstancePrefabs'][0]['prefabNodeRef']=copy.deepcopy(ca['phaseInstancePrefabs'][0]['prefabNodeRef'])
check(normalize(na,nh)==normalize(ca,ch),'Every native ambient payload preserved except scoped absolute prefab reference and outer connections')
check(normalize(node(ng,12),nh)==normalize(node(loop,12),ch),'Exact native equip wait node12 payload preserved')
check(normalize(before,index(before))==normalize(current,ch),'All nonconnection prepared and serialized payloads match')
check(node(og,14)['type']=='Terminating','Old root exit14 terminates wrapper; do not clear old Stopped receipt')
check(node(node(ng,3)['phaseGraph']['Data'],35)['type']=='Terminating','Native TurnOff terminates ambient child before it reaches old Stopped')
check(node(cg,14)['type']=='Terminating','New takeover exit terminates the entire new root')
check(len(loop['nodes'])==5,'Lifecycle encapsulates equip wait, ambient and Active writers')

guard=normalize(node(cg,2)['condition'],ch)
def evaluate(c,facts):
 if c['$type']=='questLogicalCondition':
  values=[evaluate(v,facts) for v in c['conditions']]
  return all(values) if c['operation']=='AND' else any(values)
 assert c['$type']=='questFactsDBCondition'
 t=c['type'];assert t['comparisonType']=='Equal'
 return facts.get(t['factName'],0)==t['value']
proof=read(C/'owner_proof_01.json');base=proof['root_guards']
oldfields=['PTFRSKIP_Ambient_Claimed','PTFRSKIP_Ambient_Entered','PTFRSKIP_Ambient_Request','PTFRSKIP_Ambient_Stop','PTFRSKIP_Ambient_Stopped']
for values in itertools.product([0,1],repeat=5):
 f={**base,**dict(zip(oldfields,values))}
 claim,entered,request,stop,stopped=values
 expected=stopped==1 or (claim==entered==request==0 and stop==1)
 check(evaluate(guard,f)==expected,'Old retirement truth table '+str(values))
valid={**base,**dict(zip(oldfields,[1,1,0,0,1]))}
for fact,value in base.items():
 f={**valid,fact:0 if value else 1}
 check(not evaluate(guard,f),'Reject changed root guard '+fact)

rootedges=proof['root_edges'];loopedges=proof['loop_edges']
check('12.CutSource -> 10.CutDestination' in rootedges,'Stop cuts entire lifecycle including waiting and active child')
check('3.TurnOff -> 14.In' in loopedges and '14.Out -> 12.In' in loopedges,'Natural unequip re-arms exact equip waiter')
check('12.Out -> 13.In' in loopedges and '13.Out -> 3.In1' in loopedges,'Re-equip dispatches native ambient after Active receipt')
check(not any(e.startswith('10.') for e in rootedges),'Lifecycle has no natural return wired to permanent stop')
check('10.TurnOff -> 13.In' in read(H/'graph_trace_01.json')['cooked_root_edges'],'Negative control catches old permanent stop wiring')
check('3.TurnOff -> 12.In' in read(H/'graph_trace_01.json')['native_root_edges'],'Expected rearm comes from native parent, not invented behavior')
check('12.Out -> 15.In' in rootedges and '15.Out -> 13.In' in rootedges and '13.Out -> 14.In' in rootedges,'Stop cut clears Active then acknowledges Stopped and terminates')
for n in cg['nodes']:
 d=n['Data']
 if d['$type']=='questFactsDBManagerNodeDefinition':
  check(d['type']['Data']['factName'].startswith('PTFRSKIP_SC3_'),'Outer writer is new owned fact: '+d['type']['Data']['factName'])
for n in loop['nodes']:
 d=n['Data']
 if d['$type']=='questFactsDBManagerNodeDefinition':
  check(d['type']['Data']['factName']=='PTFRSKIP_SC3_Active','Lifecycle writer only changes own Active receipt')
graphcheck=read(C/'native_graphs_01.json')
check((graphcheck['graphs'],graphcheck['nodes'],graphcheck['edges'])==(6,68,73),'All native six nested graphs /68 nodes /73 edges match freshly decoded source')
report={'status':'PASS_SC3_NATIVE_LIFECYCLE_STATIC_NOT_LIVE','checks':len(checks),'assertions':checks,
        'native_graphs':6,'native_nodes':68,'native_edges':73,'old_retirement_cases':32,
        'resource':proof['resource'],'sha256':proof['sha256'],'game_writes':0,'save_writes':0,
        'limits':['No live engine proof; archive packaging, installed resource winners and compilation are parent tasks.','Already-saved old termination is migrated by receipt; old and native facts are never cleared.'],
        'pins':[{'path':str(p.relative_to(H)),'sha256':sha(p)} for p in [H/'native_root_01.json',H/'cooked_root_01.json',H/'graph_trace_01.json',C/'owner_readback_01.json',C/'owner_prewrite_01.json',C/'owner_proof_01.json',C/'native_graphs_01.json']]}
dest=C/'payload_checks_01.json';assert not dest.exists()
dest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':len(checks),'resource_sha256':proof['sha256']}))
