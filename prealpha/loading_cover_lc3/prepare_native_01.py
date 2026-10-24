"""Pure world-attached purchase choices do not need to acquire a player actor."""
from pathlib import Path
import copy,json,hashlib
H=Path(__file__).resolve().parent;C=H/'candidate_01';out=C/'prepared_native_01';out.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
rows=[]
for name in ['northside','japantown','glen','corpo']:
 depot='towercontinued\\housing_h1\\native\\'+name+'_purchase.scene';raw=C/'native_source_01'/depot;src=C/'native_before_01'/(name+'_purchase.scene.json')
 original=json.loads(src.read_text(encoding='utf-8-sig'));data=copy.deepcopy(original);r=data['Data']['RootChunk']
 assert r['actors']==[] and len(r['playerActors'])==1 and r['playerActors'][0]['actorId']['id']==0
 graph=r['sceneGraph']['Data']['graph'];assert len(graph)==5
 assert {h['Data']['$type'] for h in graph}=={'scnStartNode','scnEndNode','scnChoiceNode','scnQuestNode'}
 choice=next(h['Data'] for h in graph if h['Data']['$type']=='scnChoiceNode');assert choice['mode']=='attachToWorld'
 # Fail if any retained executable payload requires a defined actor/performer.
 for v in walk(graph):
  assert not(v.get('$type')=='scnActorId' and v['id']!=0xffffffff)
  assert not(v.get('$type')=='scnPerformerId' and v['id']&255==1)
 removed_player=r['playerActors'];r['playerActors']=[]
 symbols=r['debugSymbols']['performersDebugSymbols'];removed_symbols=[{'index':i,'value':v} for i,v in enumerate(symbols) if v['performerId']['id']&255==1]
 assert len(removed_symbols)==1 and removed_symbols[0]['value']['performerId']['id']==1
 r['debugSymbols']['performersDebugSymbols']=[s for s in symbols if s['performerId']['id']&255!=1]
 for v in walk(r):
  assert not(v.get('$type')=='scnActorId' and v['id']!=0xffffffff)
  assert not(v.get('$type')=='scnPerformerId' and v['id']&255==1)
 p=out/(name+'_purchase.scene.json');p.write_text(json.dumps(data,indent=2)+'\n')
 rows.append({'depot':depot,'raw_sha256':sha(raw),'source':str(src),'source_sha256':sha(src),'prepared':str(p),'prepared_sha256':sha(p),'removed_player':removed_player,'removed_debug_symbols':removed_symbols})
(C/'prepared_native_01.json').write_text(json.dumps({'resources':rows},indent=2)+'\n')
print('Prepared four actor-free world purchase choices.')
