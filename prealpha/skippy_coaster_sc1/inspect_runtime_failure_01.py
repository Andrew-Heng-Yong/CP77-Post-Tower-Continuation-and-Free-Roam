"""Read-only summary of the native Skippy ambient and gameplay-comment gates."""
import json
from pathlib import Path

W=Path(__file__).resolve().parents[2]
BASE=W/'research/activity_state_r3/native_sources/json/base/quest/minor_quests/mq007'
FILES={'root':BASE/'mq007.questphase.json','comments':BASE/'phases/mq007_gameplay_comments.questphase.json','expressions':BASE/'phases/mq007_expression_facts_reset.questphase.json'}

def walk(v):
 if isinstance(v,dict):
  yield v
  for x in v.values():yield from walk(x)
 elif isinstance(v,list):
  for x in v:yield from walk(x)

def name(v):
 if isinstance(v,dict):return v.get('$value')
 return v

for label,path in FILES.items():
 root=json.loads(path.read_text())['Data']['RootChunk']
 graph=root['graph']['Data']
 if label=='root':graph=next(h['Data'] for h in graph['nodes'] if h.get('Data',{}).get('id')==3)['phaseGraph']['Data']
 print('\n##',label,'nodes',len(graph['nodes']))
 for h in graph['nodes']:
  d=h.get('Data',{})
  if not d:continue
  facts=[];items=[];scenes=[];conditions=[]
  for x in walk(d):
   if 'factName' in x:facts.append(str(name(x['factName'])))
   if 'itemID' in x:items.append(str(name(x['itemID'])))
   if x.get('$type','').endswith('ConditionType'):conditions.append(x['$type'])
   if 'sceneFile' in x:scenes.append(str(name(x['sceneFile'])))
   if 'phaseResource' in x and isinstance(x['phaseResource'],dict):
    p=x['phaseResource'].get('DepotPath',{}).get('$value')
    if p and p!='0':scenes.append(p)
  print(d.get('id'),d.get('$type'), 'facts=',sorted(set(facts)), 'items=',sorted(set(items)), 'refs=',sorted(set(scenes)), 'conds=',sorted(set(conditions)))
