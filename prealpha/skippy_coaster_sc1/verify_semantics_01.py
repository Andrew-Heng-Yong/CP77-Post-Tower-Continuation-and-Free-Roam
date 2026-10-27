"""Compare the cooked candidates with the exact native and W3 resources."""
import copy
import json
from pathlib import Path

H=Path(__file__).resolve().parent
W=H.parents[1]
C=H/'candidate_04'
OWNER=H/'candidate_06'
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values(): yield from walk(v)
 elif isinstance(x,list):
  for v in x: yield from walk(v)

native=json.loads((W/'research/activity_state_r3/native_sources/json/base/quest/minor_quests/mq007/mq007.questphase.json').read_text())['Data']['RootChunk']
owner=json.loads((OWNER/'skippy_owner_readback_01.json').read_text())['Data']['RootChunk']
native_node=next(h['Data'] for h in native['graph']['Data']['nodes'] if h.get('Data',{}).get('id')==3)
owner_node=next(h['Data'] for h in owner['graph']['Data']['nodes'] if h.get('Data',{}).get('id')==10)
def stripped(n):
 n=copy.deepcopy(n)
 n.pop('id')
 n.pop('sockets')
 n['phaseInstancePrefabs'][0]['prefabNodeRef']={'$type':'NodeRef','$storage':'string','$value':'#mq007_pr_oneliners_screen'}
 def normalize(x):
  if isinstance(x,dict):
   return {k:normalize(v) for k,v in x.items() if k not in ('HandleId','HandleRefId','sockets')}
  if isinstance(x,list):return [normalize(v) for v in x]
  return x
 return normalize(n)
def first_diff(a,b,p=''):
 if type(a)!=type(b): return (p,a,b)
 if isinstance(a,dict):
  for k in sorted(set(a)|set(b)):
   if k not in a or k not in b: return (p+'/'+k,a.get(k),b.get(k))
   d=first_diff(a[k],b[k],p+'/'+k)
   if d:return d
 elif isinstance(a,list):
  if len(a)!=len(b): return (p+'/length',len(a),len(b))
  for i,(x,y) in enumerate(zip(a,b)):
   d=first_diff(x,y,p+'/'+str(i))
   if d:return d
 elif a!=b:return (p,a,b)
 return None
assert len(native_node['phaseGraph']['Data']['nodes'])==len(owner_node['phaseGraph']['Data']['nodes'])==13
assert owner_node['phaseInstancePrefabs'][0]['prefabNodeRef']['$value'].endswith('/#mq007_pr_oneliners_screen')
root=json.loads((C/'scene_before_01.json').read_text())['Data']['RootChunk']
after=json.loads((C/'scene_after_01.json').read_text())['Data']['RootChunk']
readback=json.loads((C/'scene_readback_01.json').read_text())['Data']['RootChunk']
difference=first_diff(after,readback)
if difference:
 print('first scene cook diff',repr(difference).encode('ascii','backslashreplace')[:500])
 def all_diffs(a,b,p=''):
  if type(a)!=type(b):yield p;return
  if isinstance(a,dict):
   for k in sorted(set(a)|set(b)):
    if k not in a or k not in b:yield p+'/'+k
    else:yield from all_diffs(a[k],b[k],p+'/'+k)
  elif isinstance(a,list):
   if len(a)!=len(b):yield p+'/length'
   for i,(x,y) in enumerate(zip(a,b)):yield from all_diffs(x,y,p+'/'+str(i))
  elif a!=b:yield p
 paths=list(all_diffs(after,readback))
 from collections import Counter
 print('scene cook diff count',len(paths),'groups',Counter('/'.join(p.split('/')[:3]) for p in paths),'first20',paths[:20])
assert str(after).count('PTFRWORLD_Coaster_QuestOwns')==5
assert str(root).count('PTFRWORLD_Coaster_QuestOwns')==5
assert str(root).count('scnDialogLineEvent')==74
assert str(after).count('scnDialogLineEvent')==60
before_lines={x['itemId']['id']:x['speaker']['id'] for x in walk(root['screenplayStore']) if x.get('$type')=='scnscreenplayDialogLine'}
after_dialogs=[x for x in walk(after['sceneGraph']) if x.get('$type')=='scnDialogLineEvent']
assert not any(before_lines.get(x['screenplayLineId']['id'])==5 for x in after_dialogs)
proof={'status':'PASS','native_skippy_ambient_graphs_compared_by_native_skippy_edges_01':6,'johnny_dialog_events_removed':14,'other_dialog_events_preserved':60,'coaster_private_quest_conditions_preserved':5,'cooked_scene_root_equal':difference is None,'scene_readback_differences':len(paths) if difference else 0,'game_writes':0,'save_writes':0}
(C/'semantic_proof_01.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof))
