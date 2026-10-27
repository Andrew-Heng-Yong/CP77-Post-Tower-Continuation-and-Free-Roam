"""Exact private resource readback and bounded Johnny presentation checks."""
import copy,importlib.util,json,sys
from pathlib import Path
sys.path.insert(0,'prealpha/sidejobs_s29')
from common import handles,deref,walk,read,value,sha
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('rawcompare',ROOT/'prealpha/sidejobs_s27/raw_compare.py');rc=importlib.util.module_from_spec(spec);spec.loader.exec_module(rc)
P=ROOT/'prealpha/sidejobs_s30';m=read(P/'prepared_02/manifest.json');checks=0
def check(condition,message):
 global checks
 assert condition,message;checks+=1
def normalized(obj):
 hh=handles(obj);seen={}
 def visit(v):
  if isinstance(v,list):return [visit(x) for x in v]
  if not isinstance(v,dict):return v
  key=v.get('HandleId',v.get('HandleRefId'))
  if key is not None and key in hh:
   if key in seen:return {'ref':seen[key]}
   seen[key]=len(seen);return {'handle':seen[key],'value':visit(hh[key])}
  if v.get('$type')=='TweakDBID':return rc.canonical(v)
  return {k:visit(v[k]) for k in sorted(v)}
 return visit(obj)

for r in m['resources']:
 original=read(ROOT/r['prepared'])
 actual=read(P/'serialized_02/readback'/(r['private']+'.json'))
 check(normalized(original['Data'])==normalized(actual['Data']),('serialized payload differs',r['private']))
 check(sha(ROOT/r['raw'])==r['raw_sha256'],('native raw drift',r['native']))
 check(sha(P/'serialized_02/source'/r['private'])==next(x['sha256'] for x in read(P/'serialized_02/manifest.json')['resources'] if x['private']==r['private']),('private hash',r['private']))
 if r['native'].endswith('.questphase'):
  raw=ROOT/r['raw'];native=read(Path(str(raw).replace('\\raw\\','\\json\\').replace('/raw/','/json/')+'.json'))
  restored=copy.deepcopy(original)
  reverse={v:k for k,v in m['mapping'].items()}
  for v in walk(restored):
   if isinstance(v.get('DepotPath'),dict) and v['DepotPath'].get('$value') in reverse:v['DepotPath']['$value']=reverse[v['DepotPath']['$value']]
  check(normalized(native['Data'])==normalized(restored['Data']),('native quest graph changed beyond private references',r['native']))
 if not r['native'].endswith('.scene'):continue
 # Original scene files are located by the paired raw path's sibling JSON.
 raw=ROOT/r['raw'];old=read(Path(str(raw).replace('\\raw\\','\\json\\').replace('/raw/','/json/')+'.json'))
 oldroot=old['Data']['RootChunk'];newroot=original['Data']['RootChunk']
 for field in ('actors','playerActors','dialogLineCollection','locStore','screenplayStore'):
  if field in oldroot:check(normalized(oldroot[field])==normalized(newroot[field]),('voice/cast drift',r['native'],field))
 ids={(a['actorId']['id']<<8)|1 for a in oldroot['actors'] if a['actorName'].lower() in ('johnny','silverhand')}
 ah=handles(oldroot);bh=handles(newroot)
 an=[deref(x,ah) for x in oldroot['sceneGraph']['Data']['graph']]
 bn=[deref(x,bh) for x in newroot['sceneGraph']['Data']['graph']]
 check([x['nodeId'] for x in an]==[x['nodeId'] for x in bn],('scene graph node drift',r['native']))
 for a,b in zip(an,bn):
  ae={deref(x,ah)['id']['id']:deref(x,ah) for x in a.get('events',[])}
  be={deref(x,bh)['id']['id']:deref(x,bh) for x in b.get('events',[])}
  for ident in ae.keys()-be.keys():check(ae[ident].get('performerId',{}).get('id') in ids and ae[ident]['$type'] in ('scneventsEquipItemToPerformer','scneventsUnequipItemFromPerformer','scneventsVFXEvent'),('unauthorized event deletion',r['native'],ident))
  check(be.keys()<=ae.keys(),('new scene event',r['native']))
  for e in be.values():
   if e.get('performerId',{}).get('id') in ids:check(e['$type'] not in ('scneventsEquipItemToPerformer','scneventsUnequipItemFromPerformer','scneventsVFXEvent'),('Johnny visual event remains',r['native']))
   if e['$type']=='scnPlaySkAnimEvent' and e.get('performer',{}).get('id') in ids:check(e['muteAnimEvents']=='STANDARD',('Johnny anim unmuted',r['native'],e['id']['id']))
 for w in newroot['workspots']:
  dep=value(deref(w,bh)['workspotResource']['DepotPath'])
  if dep.startswith('towercontinued\\sidejobs_s30'):
   x=read(P/'serialized_02/readback'/(dep+'.json'))
   hubs=[v for v in walk(x) if v.get('$type')=='animAnimNode_WorkspotHub']
   check(hubs and all(v['eventFilterType']=='Mute' for v in hubs),('Johnny workspot effects',dep))

# Current JV1 applies temporary mesh hiding to the Silverhand actor on attach.
jv=(ROOT/'prealpha/full_consolidation_v1/candidate_01/package/r6/scripts/PTFR_Consolidated/PTFR_JohnnyVoiceJV1.reds').read_text(encoding='utf-8')
check('actor.GetRecordID() != t"Character.Silverhand"' in jv and 'visual.TemporaryHide(true);' in jv,'Johnny mesh policy missing')
check('mq057_motorbreath' not in str(m['mapping']),'River hold escaped')
report={'status':'PASS_STATIC_ASSET_AND_JOHNNY_PRESENTATION_NOT_LIVE','checks':checks,'resources':len(m['resources']),'scenes':sum(r['native'].endswith('.scene') for r in m['resources']),'live_rendering':'pending'}
(P/'serialized_02/test_assets_02.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
