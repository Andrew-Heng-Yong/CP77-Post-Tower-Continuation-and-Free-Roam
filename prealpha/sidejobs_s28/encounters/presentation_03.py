"""Prepare private mq003 Johnny animation-event containment without dialogue edits."""
import sys,json,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import read,sha,walk,value
MOD='towercontinued\\sidejobs_s28\\encounters\\'
SCENE='research/omitted_jobs_audit/native_01/json/base/quest/minor_quests/mq003/scenes/mq003_03_orbital_pod.scene.json'
WORK='research/sidejobs_s28/vehicles/workspots_01/ep1_1_nightcity/json/base/workspots/main_characters/johnny/johnny__stand_ground__stand_around__01.workspot.json'
OLD='base\\workspots\\main_characters\\johnny\\johnny__stand_ground__stand_around__01.workspot'
def main():
 out=Path(sys.argv[1]);out.mkdir(parents=True);pins={}
 def pin(p):pins[p]=sha(ROOT/p)
 for p in [SCENE,WORK]:pin(p);pin(p.replace('/json/','/raw/').removesuffix('.json'))
 for p in ['prealpha/sidejobs_s28/encounters/presentation_03.py','prealpha/gigs_u10/presentation/prepare_01.py','research/sidejobs_s28/vehicles/presentation_01.json','research/sidejobs_s28/encounters/johnny_owner_01.json','redscript/PTFR_JohnnyVoiceJV1/JohnnyVoiceJV1.reds']:pin(p)
 owner=read(ROOT/'research/sidejobs_s28/encounters/johnny_owner_01.json');pin(owner['source']);pin(owner['raw'])
 scene=read(ROOT/SCENE);r=scene['Data']['RootChunk'];actor=next(a for a in r['actors'] if a['actorId']['id']==4);assert actor['acquisitionPlan']=='spawnDespawn' and value(actor['spawnDespawnParams']['specRecordId'])=='Character.Silverhand'
 name=value(actor['spawnDespawnParams']['dynamicEntityUniqueName']);instances={w['workspotInstanceId']['id']:w['dataId']['id'] for w in r['workspotInstances']};johnny=set();others=set();muted=[]
 for v in walk(r):
  if v.get('$type')=='questUseWorkspotNodeDefinition':
   inst=v.get('paramsV1',{}).get('Data',{}).get('workspotInstanceId',{}).get('id')
   if inst is not None:(johnny if value(v['entityReference']['dynamicEntityUniqueName'])==name else others).add(inst)
  if v.get('$type')=='scnPlaySkAnimEvent' and v.get('performer',{}).get('id')==1025:
   assert v['muteAnimEvents']=='0';v['muteAnimEvents']='STANDARD';muted.append(v['id']['id'])
 assert not johnny&others;assert {instances[i] for i in johnny}=={2058105102,2967810069};assert not {instances[i] for i in others}&{2058105102}
 matches=[x['Data'] for x in r['workspots'] if value(x['Data']['workspotResource']['DepotPath'])==OLD];assert len(matches)==1 and matches[0]['dataId']['id']==2058105102;matches[0]['workspotResource']['DepotPath']['$value']=MOD+'johnny_stand_muted.workspot'
 work=read(ROOT/WORK);hubs=[v for v in walk(work['Data']['RootChunk']) if v.get('$type')=='animAnimNode_WorkspotHub'];assert len(hubs)==1 and hubs[0]['eventFilterType']=='Default';hubs[0]['eventFilterType']='Mute'
 assert all(v.get('initialActions',[])==[] and v.get('globalProps',[])==[] for v in walk(work['Data']['RootChunk']))
 inputs=[]
 for name,obj,source in [('mq003_pod.scene',scene,SCENE),('johnny_stand_muted.workspot',work,WORK)]:
  target=out/(name+'.json');target.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8');inputs.append({'depot':MOD+name,'expected':str(target.relative_to(ROOT)).replace('\\','/'),'original':source,'muted_scene_events':muted if name.endswith('.scene') else [],'workspot_replacement':{'old':OLD,'new':MOD+'johnny_stand_muted.workspot'} if name.endswith('.scene') else {}})
 result={'inputs':inputs,'source_pins':pins,'johnny_actor':4,'performer':1025,'native_dialogue_unchanged':True,'muted_body_event_count':len(muted),'workspot_data_id':2058105102,'workspot_instances':sorted(i for i in johnny if instances[i]==2058105102),'limitation':'Voice and native actor acquisition retained; live invisible-body/prop behavior requires gameplay verification.'}
 (out/'prepared.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'prepared':len(inputs),'body_events':len(muted)}))
if __name__=='__main__':main()
