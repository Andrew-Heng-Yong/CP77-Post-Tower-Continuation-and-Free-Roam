"""Native media-owner exact-delta audit and bounded guard truth tables."""
import binascii
import hashlib
import json
import re
from pathlib import Path
from test_streetkid_scene_load_s3 import quest_edges
root=Path(__file__).resolve().parents[1]
a=root/'research/b0_tv_media'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def walk(v):
    if isinstance(v,dict):
        yield v
        for x in v.values():yield from walk(x)
    elif isinstance(v,list):
        for x in v:yield from walk(x)
def clean(v):
    if isinstance(v,dict):return {k:clean(x) for k,x in v.items() if k not in ('HandleId','HandleRefId','sockets')}
    if isinstance(v,list):return [clean(x) for x in v]
    return v
m=read(a/'manifest.json');before=read(a/'original.json')['Data']['RootChunk'];after=read(a/'controller.json')['Data']['RootChunk']
be,bn=quest_edges(before);ae,an=quest_edges(after)
bn={n['id']:n for n in bn};an={n['id']:n for n in an}
assert set(an)=={4,11,14,15,16,17,18}
assert ae=={(4,'Out',15,'In'),(15,'Out',11,'In'),(11,'Out',16,'In'),(16,'Out',18,'In'),(18,'Out',14,'In1'),(14,'Out1',17,'In'),(17,'Out',11,'In')}
assert after['phasePrefabs']==before['phasePrefabs']
assert len(after['phasePrefabs'])==1 and after['phasePrefabs'][0]['prefabNodeRef']['$value']=='#tv_content'
expected=dict(PostTowerFreeRoamActive=1,PTFRP0_DR13=1,PTFRTV_Applied=1,q307_active=0,q307_done=1,q307_finished=1,q307_2079=1,q307_main_game_killed=1,q307_ep1_killed=1,q305_johnny_scene_active=0,q115_point_of_no_return=0,PTFRBASE_Suspended=0,PTFRTVM_Suspended=0,PTFRTVM_QuestOwns=0)
assert m['guards']==expected
g=an[11]['condition']['Data'];assert g['operation']=='AND'
assert clean(g['conditions'][-1]['Data'])==clean(bn[11]['condition']['Data'])
actual={}
for c in g['conditions'][:-1]:
    t=c['Data']['type']['Data'];assert t['comparisonType']=='Equal';actual[t['factName']]=t['value']
assert actual==expected and len(g['conditions'])==len(expected)+1
gate=read(a/'gate.json')['Data']['RootChunk'];ge,gn=quest_edges(gate);gn={n['id']:n for n in gn}
assert gate['phasePrefabs']==[] and ge=={(0,'Out',1,'In'),(1,'Out',2,'In1')}
assert clean(gn[1]['condition']['Data'])==clean(g)
assert gn[2]['phaseResource']['DepotPath']['$value']==m['resource']
assert an[4]['socketName']['$value']=='In1'
before_child={'graph':bn[14]['phaseGraph']};after_child={'graph':an[14]['phaseGraph']}
bce,bcn=quest_edges(before_child);ace,acn=quest_edges(after_child)
assert ace==bce
bcn={n['id']:n for n in bcn};acn={n['id']:n for n in acn}
stop=acn[7]['condition']['Data'];assert stop['operation']=='OR'
assert clean(stop['conditions'][0]['Data'])==clean(bcn[7]['condition']['Data'])
stop_facts={}
for c in stop['conditions'][1:]:
    t=c['Data']['type']['Data'];assert t['comparisonType']=='NotEqual';stop_facts[t['factName']]=t['value']
assert stop_facts==expected and len(stop['conditions'])==len(expected)+1
assert acn[1]['type']=='Terminating'
for i in bcn:
    b=clean(bcn[i]);n=clean(acn[i])
    if i==7:b['condition']=n['condition']
    assert b==n,('child payload',i)
for i in bn:
    b=clean(bn[i]);n=clean(an[i])
    if i==11:b['condition']=n['condition']
    if i==15:b['type']['Data']['factName']='PTFRTVM_Registered'
    if i==14:b['phaseGraph']=n['phaseGraph'] # exact nested comparison above
    assert b==n,('root payload',i)
writers=[x for x in walk(after) if x.get('$type')=='questSetVar_NodeType']
assert sorted((w['factName'],w['value'],w['setExactValue']) for w in writers)==sorted([('PTFRTVM_Registered',1,1),('PTFRTVM_Running',1,1),('PTFRTVM_Running',0,1),('PTFRTVM_Starts',1,0)])
def evaluate(c,f):
    if c['$type']=='questLogicalCondition':
        values=[evaluate(x['Data'],f) for x in c['conditions']]
        return all(values) if c['operation']=='AND' else any(values)
    t=c['type']['Data'];v=f.get(t['factName'],0);target=t['value']
    return {'Equal':v==target,'NotEqual':v!=target,'Greater':v>target}[t['comparisonType']]
base=expected|{'tv_on':1}
assert evaluate(g,base) and not evaluate(stop,base)
negative=0
for f,v in expected.items():
    for bad in (-1,0,1,2):
        if bad==v:continue
        state=base|{f:bad};assert not evaluate(g,state) and evaluate(stop,state);negative+=1
assert not evaluate(g,base|{'tv_on':0}) and evaluate(stop,base|{'tv_on':0})
# All channels remain external, original resource references, to preserve their
# current story/news selection and compatibility overrides. Audit extracted
# originals: only media scheduler state writes, no story/actor/quest starts.
rows=[]
expected_channels=[]
for index,p in enumerate(sorted((root/'research/b0_tv_restore/channels/json/base/media/tv/phases').glob('*.json')),1):
    channel=read(p)['Data']['RootChunk'];objects=list(walk(channel))
    ws=[x for x in objects if x.get('$type')=='questSetVar_NodeType']
    stem=p.name.removesuffix('.questphase.json');allowed=stem.replace('entertainment','ent')+'_ad'
    assert all(w['factName']==allowed for w in ws)
    assert {(w['value'],w['setExactValue']) for w in ws}==({(1,0),(0,1)} if index<6 else set())
    types={x['$type'] for x in objects if x.get('$type','').endswith('NodeDefinition')}
    assert types <= {'questConditionNodeDefinition','questDeletionMarkerNodeDefinition','questFactsDBManagerNodeDefinition','questInputNodeDefinition','questLogicalHubNodeDefinition','questOutputNodeDefinition','questPhaseNodeDefinition','questRandomizerNodeDefinition','questSwitchNodeDefinition','questUIManagerNodeDefinition'}
    assert not channel['phasePrefabs']
    assert all(x['phaseResource']['DepotPath']['$value']=='0' for x in objects if x.get('$type')=='questPhaseNodeDefinition')
    assert {x['type']['Data']['$type'] for x in objects if x.get('$type')=='questUIManagerNodeDefinition'}=={'questGlobalTvScheduler_NodeType'}
    scheduler=[x for x in objects if x.get('$type')=='questGlobalTvScheduler_NodeType']
    assert scheduler and {x['channelId']['$value'] for x in scheduler}=={f'Channels.CH{index}'}
    expected_channels.append('base\\media\\tv\\phases\\'+p.name.removesuffix('.json'))
    rows.append(dict(channel=index,schedulers=len(scheduler),writers=ws))
assert len(rows)==6 and m['channels']==expected_channels
sector=read(a/'dependencies/json/base/worlds/03_night_city/_compiled/default/quest_62aeb778651a0605.streamingsector.json')['Data']['RootChunk']
assert len(sector['nodes'])==8 and all(x['Data']['$type']=='worldEntityNode' for x in sector['nodes'])
templates=[x['Data']['entityTemplate']['DepotPath']['$value'] for x in sector['nodes']]
assert templates.count('base\\media\\tv\\entities\\virtual_tv_audio.ent')==5
assert set(templates)=={'base\\media\\tv\\entities\\virtual_tv_audio.ent','base\\media\\tv\\entities\\device.ent','base\\media\\tv\\entities\\virtual_camera.ent','base\\media\\tv\\entities\\streaming_cameras\\streaming_camera_device.ent'}
path=m['gate'];crc=binascii.crc_hqx((path+':1').encode(),65535);assert crc==m['registration_id']
for p in (root/'archive').rglob('*.xl'):
    for d in re.findall(r'path:\s*([^\s#]+\.questphase)',p.read_text(encoding='utf-8-sig')):
        if d!=path:assert binascii.crc_hqx((d+':1').encode(),65535)!=crc,(p,d)
archive=root/'build/TVMedia/TowerContinued_TVMedia.archive';xl=Path(str(archive)+'.xl')
assert hashlib.sha256(archive.read_bytes()).hexdigest().upper()==m['sha256']
assert hashlib.sha256(xl.read_bytes()).hexdigest().upper()==m['xl_sha256']
assert re.findall(r'path:\s*([^\s#]+\.questphase)',xl.read_text())==[path]
print(f'PASS: exact original media-child edges/payloads; 6 channel audits; {negative} entry/stop negative guards; no tv_on/story writes, registration/hash checks')
