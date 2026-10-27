import sys,json
from pathlib import Path
sys.path.insert(0,'prealpha/sidejobs_s29')
from common import handles,deref,walk,value
from inspect_native_01 import ROOT
from inspect_scenes_01 import files

for path in files:
 root=json.loads(path.read_text(encoding='utf-8'))['Data']['RootChunk'];h=handles(root)
 actors=[a for a in root['actors'] if a['actorName'].lower() in ('johnny','silverhand')]
 ids={(a['actorId']['id']<<8)|1 for a in actors}
 names={value(a['spawnDespawnParams']['dynamicEntityUniqueName']) for a in actors};names.discard('None')
 owned=set();others=set()
 for v in walk(root):
  if v.get('$type')=='questUseWorkspotNodeDefinition':
   w=(deref(v.get('paramsV1') or {},h) or {}).get('workspotInstanceId',{}).get('id')
   if w is not None:
    ref=v['entityReference'];actor_names={a['actorName'].lower() for a in actors}
    mine=value(ref.get('dynamicEntityUniqueName')) in names or str(value(ref.get('sceneActorContextName',''))).lower() in actor_names or any(str(value(n)).lower() in actor_names for n in ref.get('names',[])) or str(value(ref.get('reference'))).lower() in {'#'+n for n in actor_names}
    (owned if mine else others).add(w)
  if v.get('$type')=='scnPlaySkAnimEvent':
   w=(deref(v.get('poseBlendOutWorkspot') or {},h) or {}).get('workspotId',{}).get('id')
   if w is not None:(owned if v.get('performer',{}).get('id') in ids else others).add(w)
 instances={w['workspotInstanceId']['id']:w['dataId']['id'] for w in root['workspotInstances']}
 bydata={deref(w,h)['dataId']['id']:value(deref(w,h)['workspotResource']['DepotPath']) for w in root['workspots']}
 print(path.name,'JOHNNY',ids,'OWNED',owned,'SHARED',owned&others)
 for i in owned:print(i,bydata.get(instances.get(i)))
