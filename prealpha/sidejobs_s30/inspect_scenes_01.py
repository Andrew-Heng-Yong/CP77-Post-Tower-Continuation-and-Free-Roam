import json
from pathlib import Path
from inspect_native_01 import ROOT,walk

files=[
 ROOT/'research/b0_world_interactions/dependencies/json/base/quest/minor_quests/mq006/scenes/mq006_01_intro.scene.json',
 ROOT/'research/b0_world_interactions/dependencies/json/base/quest/minor_quests/mq006/scenes/mq006_02_finale.scene.json',
 *sorted((ROOT/'research/whitelist_outside_review_20261026/shape_pony_native_01/json').rglob('*.scene.json')),
 *sorted((ROOT/'research/whitelist_outside_review_20261026/career_native_01/json').rglob('*.scene.json')),
]
if __name__=='__main__':
 for path in files:
  root=json.loads(path.read_text(encoding='utf-8'))['Data']['RootChunk']
  refs={x['HandleId']:x['Data'] for x in walk(root) if 'HandleId' in x and 'Data' in x}
  def deref(x):return refs.get(x.get('HandleId',x.get('HandleRefId')),x) if isinstance(x,dict) else x
  actors=[{'id':a['actorId']['id'],'name':a['actorName'],'plan':a['acquisitionPlan']} for a in root['actors']]
  johnny={a['id']*256+1 for a in actors if a['name'].lower() in ('johnny','silverhand')}
  evs=[]
  for x in walk(root):
   if '$type' in x and ('Event' in x['$type'] or 'VFX' in x['$type']):
    aid=x.get('performerId',x.get('performer',{})).get('id')
    if aid in johnny:evs.append((x['$type'],x.get('id',{}).get('id'),str(x.get('effectName',x.get('itemID','')))[:70]))
  spots=[]
  for w in root.get('workspots',[]):
   d=deref(w)
   spots.append((d['dataId']['id'],deref(d['workspotResource']).get('DepotPath',{}).get('$value')))
  props=[(p['propId']['id'],p['propName'],p.get('findEntityInEntityParams',{}).get('performerId',{}).get('id')) for p in root.get('props',[])]
  print('\n',path.name,'ACTORS',actors,'JOHNNY_EVENTS',len(evs),'WORKSPOTS',spots,'PROPS',props)
  for e in evs:print(e)
