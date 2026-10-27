import json,sys
sys.path.insert(0,'prealpha/sidejobs_s29')
from common import handles,deref,walk
from inspect_scenes_01 import files
for path in files:
 root=json.loads(path.read_text(encoding='utf-8'))['Data']['RootChunk'];h=handles(root)
 ids={(a['actorId']['id']<<8)|1 for a in root['actors'] if a['actorName'].lower() in ('johnny','silverhand')}
 if not ids:continue
 print('\n',path.name)
 for w in root['sceneGraph']['Data']['graph']:
  n=deref(w,h)
  for ew in n.get('events',[]):
   e=deref(ew,h);aid=e.get('performerId',e.get('performer',{})).get('id')
   if aid in ids:print(e)
