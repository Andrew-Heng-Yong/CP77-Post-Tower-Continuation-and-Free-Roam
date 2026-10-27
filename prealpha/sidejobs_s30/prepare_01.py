"""Prepare private native S30 resources without touching the game."""
import copy,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,'prealpha/sidejobs_s29')
from common import handles,deref,walk,value

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'prealpha/sidejobs_s30/prepared_01'
assert not OUT.exists();OUT.mkdir()

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def get(prefix):
 data=json.loads((ROOT/prefix/'inventory.json').read_text(encoding='utf-8'))
 rows=data['rows'] if isinstance(data,dict) else data
 for x in rows:
  dep=x.get('depot',x.get('ResourcePath'))
  raw=x.get('raw',x.get('RawOutput'));j=x.get('json',x.get('JsonOutput'))
  if not raw.startswith('research/'):raw=str(prefix/raw).replace('\\','/')
  if not j.startswith('research/'):j=str(prefix/j).replace('\\','/')
  yield dep,ROOT/raw,ROOT/j

sources={}
for dirname in ('shape_pony_native_01','career_native_01'):
 sources.update({d:(r,j) for d,r,j in get(Path('research/whitelist_outside_review_20261026')/dirname)})
for base in ('research/b0_world_interactions/extended','research/b0_world_interactions/dependencies'):
 for j in (ROOT/base/'json').rglob('*.json'):
  raw=ROOT/base/'raw'/j.relative_to(ROOT/base/'json');raw=Path(str(raw)[:-5])
  if not raw.exists():continue
  dep=str(j.relative_to(ROOT/base/'json'))[:-5].replace('/','\\')
  sources[dep]=(raw,j)
for d,r,j in get(Path('research/sidejobs_s29/s30_workspots_02')):
 if d not in sources or 'memoryresident' in str(r):sources[d]=(r,j)
for d,r,j in get(Path('research/sidejobs_s29/native_05')):
 if d.endswith('johnny__sit_bench__sit_around__01.workspot') and d not in sources:sources[d]=(r,j)

quests={
 'mq006_rollercoaster':r'base\quest\minor_quests\mq006\mq006.questphase',
 'mws_se5_07':r'base\open_world\mini_world_stories\badlands\se5\mws_se5_07\mws_se5_07.questphase',
 'mws_wat_08_trauma_drama':r'base\open_world\mini_world_stories\watson\mws_wat_08\mws_wat_08.questphase',
}
queue=list(quests.values());selected=set()
while queue:
 dep=queue.pop(0)
 if dep in selected:continue
 assert dep in sources,('missing',dep)
 selected.add(dep)
 obj=json.loads(sources[dep][1].read_text(encoding='utf-8'))
 for v in walk(obj):
  p=v.get('DepotPath')
  if not isinstance(p,dict):continue
  d=p.get('$value')
  if d in sources and d not in selected and d.endswith(('.questphase','.scene')):queue.append(d)

def private(dep):return 'towercontinued\\sidejobs_s30\\native\\'+dep
mapping={d:private(d) for d in selected}
report=[]
def add_workspot(dep):
 assert dep in sources,('missing workspot',dep)
 mapping[dep]=private(dep);selected.add(dep)

prepared={}
for dep in sorted(selected):prepared[dep]=json.loads(sources[dep][1].read_text(encoding='utf-8'))

for dep,obj in list(prepared.items()):
 if not dep.endswith('.scene'):continue
 root=obj['Data']['RootChunk'];h=handles(root)
 actors=[a for a in root['actors'] if a['actorName'].lower() in ('johnny','silverhand')]
 if not actors:report.append(dict(depot=dep,johnny=False));continue
 ids={(a['actorId']['id']<<8)|1 for a in actors}
 names={value(a['spawnDespawnParams']['dynamicEntityUniqueName']) for a in actors};names.discard('None');names.discard(None)
 owned=set();other=set();byrefs=[]
 for v in walk(root):
  if v.get('$type')=='questUseWorkspotNodeDefinition':
   p=deref(v.get('paramsV1') or {},h) or {};w=p.get('workspotInstanceId',{}).get('id')
   if w is not None:
    ref=v['entityReference'];mine=value(ref.get('dynamicEntityUniqueName')) in names or str(value(ref.get('sceneActorContextName',''))).lower() in {a['actorName'].lower() for a in actors}
    (owned if mine else other).add(w);byrefs.append((v,p,mine))
  if v.get('$type')=='scnPlaySkAnimEvent':
   p=deref(v.get('poseBlendOutWorkspot') or {},h) or {};w=p.get('workspotId',{}).get('id')
   if w is not None:
    mine=v.get('performer',{}).get('id') in ids;(owned if mine else other).add(w);byrefs.append((v,p,mine))
 shared=owned&other
 if shared:
  max_instance=max(w['workspotInstanceId']['id'] for w in root['workspotInstances'])
  max_data=max(deref(w,h)['dataId']['id'] for w in root['workspots'])
  max_handle=max(int(v['HandleId']) for v in walk(root) if 'HandleId' in v)
  for old in sorted(shared):
   max_instance+=1;max_data+=1;max_handle+=1
   base=next(w for w in root['workspotInstances'] if w['workspotInstanceId']['id']==old)
   old_data=base['dataId']['id'];new_inst=copy.deepcopy(base);new_inst['workspotInstanceId']['id']=max_instance;new_inst['dataId']['id']=max_data;root['workspotInstances'].append(new_inst)
   wrapper=copy.deepcopy(next(w for w in root['workspots'] if deref(w,h)['dataId']['id']==old_data));wrapper['HandleId']=str(max_handle);wrapper['Data']['dataId']['id']=max_data;root['workspots'].append(wrapper)
   for v,p,mine in byrefs:
    if mine and p.get('workspotInstanceId',p.get('workspotId',{})).get('id')==old:
     p.get('workspotInstanceId',p.get('workspotId'))['id']=max_instance
   owned.remove(old);owned.add(max_instance)
  h=handles(root)
 instances={w['workspotInstanceId']['id']:w['dataId']['id'] for w in root['workspotInstances']}
 owned_data={instances[i] for i in owned if i in instances}
 work=[]
 for w in root['workspots']:
  x=deref(w,h)
  if x['dataId']['id'] not in owned_data:continue
  old=value(x['workspotResource']['DepotPath']);assert old in sources,('unavailable Johnny workspot',old)
  add_workspot(old);x['workspotResource']['DepotPath']['$value']=private(old);work.append(old)
 removed=[];muted=[]
 for w in root['sceneGraph']['Data']['graph']:
  n=deref(w,h);keep=[]
  for ew in n.get('events',[]):
   e=deref(ew,h);typ=e.get('$type');performer=e.get('performerId',{}).get('id')
   if performer in ids and typ in ('scneventsEquipItemToPerformer','scneventsUnequipItemFromPerformer','scneventsVFXEvent'):
    removed.append(e['id']['id']);continue
   if typ=='scnPlaySkAnimEvent' and e.get('performer',{}).get('id') in ids:
    assert e['muteAnimEvents'] in ('0','STANDARD');e['muteAnimEvents']='STANDARD';muted.append(e['id']['id'])
   keep.append(ew)
  if 'events' in n:n['events']=keep
 if removed:
  for sym in root['debugSymbols']['sceneEventsDebugSymbols']:
   sym['sceneEventIds']=[v for v in sym['sceneEventIds'] if v['id'] not in removed]
  root['debugSymbols']['sceneEventsDebugSymbols']=[v for v in root['debugSymbols']['sceneEventsDebugSymbols'] if v['sceneEventIds']]
 report.append(dict(depot=dep,johnny=True,actors=[a['actorName'] for a in actors],owned_instances=sorted(owned),shared_instances_split=sorted(shared),workspots=sorted(set(work)),removed_events=removed,muted_animation_events=muted))

for dep in sorted(selected):
 if dep not in prepared:prepared[dep]=json.loads(sources[dep][1].read_text(encoding='utf-8'))
 obj=prepared[dep]
 if dep.endswith('.workspot'):
  root=obj['Data']['RootChunk'];changes=0
  for v in walk(root):
   if v.get('$type')=='animAnimNode_WorkspotHub':
    assert v['eventFilterType'] in ('Default','Mute');v['eventFilterType']='Mute';changes+=1
   if v.get('$type')=='workWorkspotTree' and v.get('initialActions'):
    assert all(a['Data']['$type']=='workEquipItemToSlotAction' for a in v['initialActions']);v['initialActions']=[];changes+=1
  assert changes,dep
 for v in walk(obj):
  if isinstance(v.get('DepotPath'),dict):
   old=v['DepotPath'].get('$value')
   if old in mapping:v['DepotPath']['$value']=mapping[old]
 # A removed scene event can own the first definition of a shared handle.
 definitions={**handles(json.loads(sources[dep][1].read_text(encoding='utf-8'))),**handles(obj)};seen=set()
 def canonical(x):
  if isinstance(x,list):return [canonical(v) for v in x]
  if not isinstance(x,dict):return x
  key=x.get('HandleId',x.get('HandleRefId'))
  if key is not None and key in definitions:
   if key in seen:return {'HandleRefId':key}
   seen.add(key);return {'HandleId':key,'Data':canonical(definitions[key])}
  return {k:canonical(v) for k,v in x.items()}
 obj=canonical(obj)
 path=OUT/'json'/(private(dep)+'.json');path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

meta=dict(status='PREPARED_NOT_INSTALLED',quests=quests,mapping=mapping,presentation=report,resources=[dict(native=d,private=mapping[d],raw=str(sources[d][0].relative_to(ROOT)).replace('\\','/'),raw_sha256=sha(sources[d][0]),json_sha256=sha(sources[d][1]),prepared=str((OUT/'json'/(mapping[d]+'.json')).relative_to(ROOT)).replace('\\','/')) for d in sorted(selected)])
(OUT/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('prepared',len(selected),'resources',len(report),'scenes')
