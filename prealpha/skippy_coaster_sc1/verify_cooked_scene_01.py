"""Compare normalized binary readbacks of original and edited MQ006 scenes."""
import json
from collections import Counter
from pathlib import Path

C=Path(__file__).resolve().parent/'candidate_04'
before=json.loads((C/'scene_roundtrip_readback_01.json').read_text())['Data']['RootChunk']
after=json.loads((C/'scene_readback_01.json').read_text())['Data']['RootChunk']

def walk(x):
 if isinstance(x,dict):
  yield x
  for y in x.values():yield from walk(y)
 elif isinstance(x,list):
  for y in x:yield from walk(y)

def sections(root):
 return {x['Data']['nodeId']['id']:(x['Data']['$type'],x['Data'].get('sectionDuration'))
         for x in root['sceneGraph']['Data']['graph'] if x.get('Data')}

def events(root):
 return {str(x['id']['id']):(x['$type'],x.get('screenplayLineId',{}).get('id'),x.get('startTime'),x.get('duration'))
         for x in walk(root['sceneGraph']) if x.get('$type','').endswith('Event') and isinstance(x.get('id'),dict) and 'id' in x['id']}

lines={x['itemId']['id']:x['speaker']['id'] for x in walk(before['screenplayStore']) if x.get('$type')=='scnscreenplayDialogLine'}
b,a=events(before),events(after)
assert sections(before)==sections(after)
assert set(a)<=set(b)
removed=set(b)-set(a)
assert len(removed)==14
assert all(b[i][0]=='scnDialogLineEvent' and lines[b[i][1]]==5 for i in removed)
assert all(b[i]==a[i] for i in a)
assert sum(x[0]=='scnDialogLineEvent' for x in a.values())==60
assert all(lines[x[1]]!=5 for x in a.values() if x[0]=='scnDialogLineEvent')
type_difference=Counter(x.get('$type') for x in walk(before['sceneGraph']))-Counter(x.get('$type') for x in walk(after['sceneGraph']))
assert type_difference==Counter({'scnSceneEventId':16,None:14,'CName':14,'scnscreenplayItemId':14,'scnDialogLineEvent':14,'scnAdditionalSpeakers':14,'scnDialogLineVoParams':14})
assert str(before).count('PTFRWORLD_Coaster_QuestOwns')==str(after).count('PTFRWORLD_Coaster_QuestOwns')==5
proof={'status':'PASS_COOKED_SCENE','all_section_nodes_and_durations_preserved':True,'other_scene_events_preserved':len(a),'johnny_dialog_events_removed':14,'other_dialog_events':60,'private_quest_conditions':5,'game_writes':0,'save_writes':0}
(C/'cooked_scene_semantics_01.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof))
