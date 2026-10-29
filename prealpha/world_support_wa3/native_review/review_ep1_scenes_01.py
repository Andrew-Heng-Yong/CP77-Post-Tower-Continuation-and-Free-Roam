import json,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
checks=[];rows=[]
for h in read(R/'ep1_ambient_scenes_native_01/report_01.json')['hits']:
 j=read(h['copy']+'.json');types=collections.Counter(x.get('$type','') for x in walk(j));nodes=[x['Data']['$type'] for x in j['Data']['RootChunk']['sceneGraph']['Data']['graph']]
 ok=set(nodes)<={'scnStartNode','scnSectionNode','scnEndNode'} and not any(t.startswith('quest') for t in types) and {t for t in types if t.endswith('Event')}<={'scnDialogLineEvent'}
 checks.append({'name':h['depot']+' dialog-only no quest operation','pass':ok});rows.append({'depot':h['depot'],'binary':h['copy'],'sha256':h['sha256'],'graph_types':dict(collections.Counter(nodes)),'event_types':{t:n for t,n in types.items() if t.endswith('Event')}})
assert len(rows)==6 and all(c['pass'] for c in checks)
report={'status':'PASS','checks':checks,'scenes':rows,'scope':'Six retained HillSpa civilian speech scenes. Only dialog events; no native fact, spawn, reward, kill, status or quest operations.'}
(R/'ep1_ambient_scene_assessment_01.json').write_text(json.dumps(report,indent=2)+'\n',newline='\n');print(json.dumps(report))
