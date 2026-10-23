"""Private Johnny workspots anchored to their original world nodes; no world override."""
import copy, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import read,sha,walk,value
MOD='towercontinued\\sidejobs_s28\\vehicles\\'
INV='research/sidejobs_s28/vehicles/official_02/inventory.json'
DONOR=r'base\open_world\street_stories\heywood\glenn\sts_hey_gle_03\scenes\sts_hey_gle_03_scene.scene'
SPECS=[
 ('mq029_01a_garage',r'base\quest\minor_quests\mq029\scenes\mq029_01a_garage.scene','#mq029_ws_johhny_josie_garage','johnny__stand_chair_lean_front_gun__stand_around__01',28),
 ('mq029_01b_josie_body',r'base\quest\minor_quests\mq029\scenes\mq029_01b_josie_body.scene','#mq029_ws_johnny_find_josie','johnny__stand_wall_lean_back_cigarette__stand_around__01',19),
 ('mq050_johnny_start',r'base\quest\minor_quests\mq050\scenes\mq050_johnny_start.scene','#mq050_ws_johnny','johnny__stand_ground_glasses__stand_around__01',4)]

def main():
 out=Path(sys.argv[1]);out.mkdir(parents=True);pins={};inputs=[];mapping={};changes=[]
 def pin(p):pins[p]=sha(ROOT/p)
 for p in [INV,'prealpha/sidejobs_s28/vehicles/presentation_02.py','research/sidejobs_s28/vehicles/presentation_01.json','redscript/PTFR_JohnnyVoiceJV1/JohnnyVoiceJV1.reds']:
  pin(p)
 official={r['depot']:r for r in read(ROOT/INV)['rows']}
 def source(dep):
  r=official[dep]
  for p in [r['raw'],r['json']]:pin(p)
  return r['json'],read(ROOT/r['json'])
 donorpath,donor=source(DONOR);dr=donor['Data']['RootChunk']
 inst=next(x for x in dr['workspotInstances'] if x['workspotInstanceId']['id']==712)
 assert inst['originMarker']['type']=='Global' and value(inst['originMarker']['nodeRef'])=='#sts_sm_hey_gle_03_scene'
 param=next(n for n in walk(dr) if n.get('$type')=='scnUseSceneWorkspotParamsV1')
 external=next(n for n in walk(dr) if n.get('$type')=='scnWorkspotData_ExternalWorkspotResource')
 def emit(name,obj,original,kind,details):
  p=out/(name+'.json');p.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')
  inputs.append({'depot':MOD+name,'expected':str(p.relative_to(ROOT)).replace('\\','/'),'original':original,'kind':kind,**details})
 for name,dep,anchor,workname,nodeid in SPECS:
  original,scene=source(dep);r=scene['Data']['RootChunk'];assert not r['workspots'] and not r['workspotInstances']
  actor=next(a for a in r['actors'] if a['actorId']['id']==0)
  assert actor['acquisitionPlan']=='spawnDespawn' and value(actor['spawnDespawnParams']['specRecordId'])=='Character.Silverhand'
  actorname=value(actor['spawnDespawnParams']['dynamicEntityUniqueName'])
  targets=[n for n in walk(r) if n.get('$type')=='questUseWorkspotNodeDefinition' and n['id']==nodeid]
  assert len(targets)==1;target=targets[0];assert value(target['entityReference']['dynamicEntityUniqueName'])==actorname
  old=target['paramsV1']['Data'];assert old['$type']=='questUseWorkspotParamsV1' and old['function']=='UseWorkspot' and value(old['workspotNode'])==anchor
  dataid=4282800001;instanceid=65000
  new=copy.deepcopy(old);new['$type']='scnUseSceneWorkspotParamsV1'
  for k in ['itemOverride','playAtActorLocation','workspotInstanceId']:new[k]=copy.deepcopy(param[k])
  new['workspotInstanceId']['id']=instanceid;new['workspotNode']={'$type':'NodeRef','$storage':'uint64','$value':'0'};target['paramsV1']['Data']=new
  instance=copy.deepcopy(inst);instance['dataId']['id']=dataid;instance['workspotInstanceId']['id']=instanceid
  instance['originMarker']['nodeRef']['$value']=anchor
  instance['localTransform']=copy.deepcopy(actor['spawnDespawnParams']['spawnOffset'])
  assert instance['localTransform']=={'$type':'Transform','orientation':{'$type':'Quaternion','i':0,'j':0,'k':0,'r':1},'position':{'$type':'Vector4','W':0,'X':0,'Y':0,'Z':0}}
  r['workspotInstances']=[instance]
  workdep=MOD+name+'_muted.workspot'
  data=copy.deepcopy(external);data['dataId']['id']=dataid;data['workspotResource']['DepotPath']={'$type':'ResourcePath','$storage':'string','$value':workdep}
  hid=max(int(n['HandleId']) for n in walk(scene) if 'HandleId' in n)+1
  r['workspots']=[{'HandleId':str(hid),'Data':data}]
  muted=[]
  for n in walk(r):
   if n.get('$type')=='scnPlaySkAnimEvent' and n.get('performer',{}).get('id')==1:
    assert n['muteAnimEvents']=='0';n['muteAnimEvents']='STANDARD';muted.append(n['id']['id'])
  wp='research/sidejobs_s28/vehicles/workspots_01/ep1_1_nightcity/json/base/workspots/main_characters/johnny/'+workname+'.workspot.json'
  pin(wp);pin(wp.replace('/json/','/raw/').removesuffix('.json'));work=read(ROOT/wp)
  hubs=[n for n in walk(work['Data']['RootChunk']) if n.get('$type')=='animAnimNode_WorkspotHub'];assert len(hubs)==1 and hubs[0]['eventFilterType']=='Default';hubs[0]['eventFilterType']='Mute'
  assert all(n.get('initialActions',[])==[] and n.get('globalProps',[])==[] for n in walk(work['Data']['RootChunk']))
  emit(name+'.scene',scene,original,'scene',{'anchor':anchor,'node':nodeid,'actor':0,'performer':1,'muted_events':muted,'workspot':workdep,'data_id':dataid,'instance_id':instanceid,'donor':donorpath})
  emit(name+'_muted.workspot',work,wp,'workspot',{'event_filter':'Mute'})
  mapping[dep]=MOD+name+'.scene';changes.append({'scene':dep,'node':nodeid,'anchor':anchor,'body_events':len(muted)})
 # Clone only ancestors which directly reference a replaced child, retaining complete resource metadata.
 phases={d:r for d,r in official.items() if d.endswith('.questphase') and ('\\mq029\\' in d or '\\mq050\\' in d)}
 pending=set(phases);clones=[]
 while True:
  progress=False
  for dep in sorted(pending):
   p,obj=source(dep);refs=[]
   for n in walk(obj['Data']):
    if 'DepotPath' in n and value(n['DepotPath']) in mapping:
     old=value(n['DepotPath']);n['DepotPath']['$value']=mapping[old];refs.append({'old':old,'new':mapping[old]})
   if refs:
    name=dep.split('\\')[-1];emit(name,obj,p,'phase',{'replacements':refs});mapping[dep]=MOD+name;pending.remove(dep);clones.append(dep);progress=True
  if not progress:break
 assert r'base\quest\minor_quests\mq029\mq029_tourist.questphase' in mapping
 assert r'base\quest\minor_quests\mq050\mq050.questphase' in mapping
 result={'inputs':inputs,'source_pins':pins,'mapping':mapping,'changes':changes,'global_marker_donor':donorpath,'notes':['Global marker anchored to the original world AISpot NodeRef with identity local transform.','Only Johnny body animation events muted; all dialogue, scene edges, player clue props and StopWorkspot commands preserved.','Live playback remains unverified.']}
 (out/'prepared.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'resources':len(inputs),'changes':changes,'ancestors':clones}))

if __name__=='__main__':main()
