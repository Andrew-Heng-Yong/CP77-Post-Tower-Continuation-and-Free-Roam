"""Exact adapter deltas, complete handle graphs, dense scene cast and fail-closed guards."""
import binascii
import hashlib
import json
import re
from pathlib import Path
from audit_world_interactions import walk
from audit_scene_actor_ids import audit_scene_actor_ids
from audit_interaction_routes import reachable
from test_streetkid_scene_load_s3 import quest_edges

ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'research/b0_world_interactions/batch'
def read(name): return json.loads((A/(name+'.json')).read_text(encoding='utf-8-sig'))['Data']['RootChunk']
def index(root): return {str(x['HandleId']):x['Data'] for x in walk(root) if 'HandleId' in x}
def canonical(value, handles, keep_sockets=False):
    if isinstance(value,list): return [canonical(x,handles,keep_sockets) for x in value]
    if not isinstance(value,dict): return value
    if 'HandleId' in value or 'HandleRefId' in value:
        return canonical(handles[str(value.get('HandleId',value.get('HandleRefId')))],handles,keep_sockets)
    return {k:canonical(v,handles,keep_sockets) for k,v in value.items() if keep_sockets or k!='sockets'}
def node_map(r): return {n['id']:n for n in quest_edges(r)[1]}
def graph_audit(r):
    h=index(r)
    def resolve(x):return h[str(x.get('HandleId',x.get('HandleRefId')))]
    count=0
    for g in (x for x in walk(r) if x.get('$type')=='questGraphDefinition'):
        nodes=[resolve(n) for n in g['nodes']]
        assert len({n['id'] for n in nodes})==len(nodes)
        socks={str(s.get('HandleId',s.get('HandleRefId'))) for n in nodes for s in n['sockets']}
        for sid in socks:
            for ch in h[sid]['connections']:
                c=resolve(ch); cid=str(ch.get('HandleId',ch.get('HandleRefId')))
                ends=[str(c[k].get('HandleId',c[k].get('HandleRefId'))) for k in ('source','destination')]
                assert sid in ends and set(ends)<=socks
                for end in ends:
                    assert cid in {str(x.get('HandleId',x.get('HandleRefId'))) for x in h[end]['connections']}
        count+=1
    for x in walk(r):
        if 'HandleRefId' in x:assert str(x['HandleRefId']) in h
    return count
def evaluate(c,f):
    if c['$type']=='questLogicalCondition':
        vals=[evaluate(x['Data'],f) for x in c['conditions']]
        return all(vals) if c['operation']=='AND' else any(vals)
    t=c['type']['Data'];v=f.get(t['factName'],0);target=t['value']
    return {'Equal':v==target,'NotEqual':v!=target,'GreaterOrEqual':v>=target,'Greater':v>target}[t['comparisonType']]

m=json.loads((A/'manifest.json').read_text())
assert not m['new_polling'] and not m['vanilla_replacements'] and not m['live_tested']
expected=dict(PostTowerFreeRoamActive=1,PTFRP0_DR13=1,q307_active=0,q307_done=1,q307_finished=1,q307_2079=1,q307_main_game_killed=1,q307_ep1_killed=1,q305_johnny_scene_active=0,q115_point_of_no_return=0,PTFRBASE_Suspended=0,PTFRWORLD_Suspended=0)
assert m['guards']==expected
negative=graphs=0
for row in m['adapters']:
    key=row['key'];gate=read(key+'_gate');edges,ns=quest_edges(gate);ns={n['id']:n for n in ns}
    assert edges=={(0,'Out',1,'In'),(1,'Out',2,'In1')} and gate['phasePrefabs']==[]
    assert ns[2]['phaseResource']['DepotPath']['$value']==row['owner']
    guard=ns[1]['condition']['Data'];base=expected|{f'PTFRWORLD_{key}_Suspended':0,f'PTFRWORLD_{key}_QuestOwns':0}
    if key=='Coaster':base['mq006_enable_repeatable_rollercoaster']=1
    conditions={x['Data']['type']['Data']['factName']:x['Data']['type']['Data'] for x in guard['conditions']}
    assert set(conditions)==set(base) and guard['operation']=='AND'
    assert all(t['value']==base[f] and t['comparisonType']==('GreaterOrEqual' if f=='mq006_enable_repeatable_rollercoaster' else 'Equal') for f,t in conditions.items())
    assert evaluate(guard,base)
    for fact,value in base.items():
        for bad in (-1,0,1,2):
            if bad==value or (fact=='mq006_enable_repeatable_rollercoaster' and bad>=1):continue
            assert not evaluate(guard,base|{fact:bad});negative+=1
    crc=binascii.crc_hqx((row['gate']+':1').encode(),65535);assert crc==row['registration_id']
    for p in (ROOT/'archive').rglob('*.xl'):
        for d in re.findall(r'path:\s*([^\s#]+\.questphase)',p.read_text(encoding='utf-8-sig')):
            if d!=row['gate']:assert binascii.crc_hqx((d+':1').encode(),65535)!=crc,(p,d)
    graphs+=graph_audit(gate)+graph_audit(read(key+'_owner'))

before=read('Radio_original');after=read('Radio_owner');b=node_map(before);n=node_map(after)
assert set(n)==set(b)|{20,21,22}
assert quest_edges(after)[0]=={(0,'Out',20,'In'),(20,'True',19,'In'),(20,'False',18,'In'),(19,'Out',21,'In'),(21,'Out',18,'In'),(18,'Out',22,'In'),(22,'Out',17,'In1'),(17,'Out1',18,'In')}
assert n[20]['condition']['Data']['type']['Data']['factName']=='PTFRWORLD_Radio_Applied'
assert n[21]['type']['Data']['factName']=='PTFRWORLD_Radio_Applied'
bc=canonical(b[17]['phaseGraph'],index(before));ac=canonical(n[17]['phaseGraph'],index(after))
bc12=next(x for x in bc['nodes'] if x['id']==12);ac12=next(x for x in ac['nodes'] if x['id']==12)
assert ac12['condition']['operation']=='OR' and ac12['condition']['conditions'][0]==bc12['condition']
bc12['condition']=ac12['condition'];assert bc==ac # all schedulers/selection/earned outcome state preserved
for i in (0,19):assert canonical(b[i],index(before))==canonical(n[i],index(after))
assert n[19]['type']['Data']=={'$type':'questSetVar_NodeType','factName':'radio_on','setExactValue':1,'value':1}
assert all(o.get('phaseResource',{}).get('DepotPath',{}).get('$value')=='0' for o in walk(after) if o.get('$type')=='questPhaseNodeDefinition')
assert not after['phasePrefabs']

before=read('Memorial_original');after=read('Memorial_owner');b=node_map(before);n=node_map(after)
assert set(n)==set(b)|{65}
assert quest_edges(after)[0]=={(0,'Out',65,'In')}|{(65,'Out',i,'In1') for i in (61,62,63,64)}
for i in (61,62,63,64):
    bg={'graph':b[i]['phaseGraph']};ag={'graph':n[i]['phaseGraph']};bm=node_map(bg);am=node_map(ag)
    assert set(am)==set(bm)-({59,61} if i==61 else set())
    assert quest_edges(ag)[0]==quest_edges(bg)[0]-({(11,'Out',59,'In'),(59,'Out',61,'In')} if i==61 else set())
    for j in am:
        bn=canonical(bm[j],index(before));an=canonical(am[j],index(after))
        if bn['$type']=='questPauseConditionNodeDefinition':
            assert an['condition']['operation']=='AND' and an['condition']['conditions'][-1]==bn['condition']
            bn['condition']=an['condition']
        assert bn==an
assert not any(x.get('$type')=='questSpawnManagerNodeDefinition' for x in walk(after))
assert [x for x in walk(after) if x.get('$type')=='questTogglePrefabVariant_NodeTypeParams']==[x for x in walk(before) if x.get('$type')=='questTogglePrefabVariant_NodeTypeParams']
assert {x['factName'] for x in walk(after) if x.get('$type')=='questSetVar_NodeType'}=={'PTFRWORLD_Memorial_Registered'}

owner=read('Coaster_owner');ns=node_map(owner);assert set(ns)=={0,28,29,30,31,32,33,34,35,36,37}
assert quest_edges(owner)[0]=={(0,'Out',35,'In'),(35,'Out',36,'In'),(36,'Out',37,'In'),(37,'Out',31,'In'),(31,'Out',32,'In'),(32,'Out',33,'In'),(33,'Out',29,'mq006_02_ride_standalone_in'),(29,'StartRollecoasterStandalone',28,'In1'),(29,'mq006_02_ride_standalone_out',34,'In'),(34,'Out',30,'In'),(30,'Out',32,'In')}
vanilla_quest=json.loads((ROOT/'research/b0_world_interactions/extended/json/base/quest/minor_quests/mq006/mq006.questphase.json').read_text())['Data']['RootChunk']
original_setup=node_map({'graph':node_map(vanilla_quest)[50]['phaseGraph']})
vh=index(vanilla_quest);oh=index(owner)
for new,old in ((35,50),(36,51)):
    expected_node=canonical(original_setup[old],vh);actual_node=canonical(ns[new],oh)
    expected_node['id']=new
    if new==35:
        expected_node['actions'][0]['type']['spawnerReference']=actual_node['actions'][0]['type']['spawnerReference']
        assert actual_node['actions'][0]['type']['spawnerReference']['$value'].endswith('/#mq006_pr_rollercoaster_ride/#mq006_rollercoaster_cart_001')
    else:
        expected_node['type']['objectRef']=actual_node['type']['objectRef']
        assert actual_node['type']['objectRef']['$value']=='$/03_night_city/c_pacifica/coastview/#loc_q110_pacifica_mall/#loc_q110_pacifica_mall_gameplay/#loc_q110_pacifica_mall_devices/mq006_rollercoaster_devices_prefabMDXXVMQ/#mq006_dvc_rollercoaster_cart_clue'
    assert expected_node==actual_node
assert ns[37]['type']['Data']['factName']=='PTFRWORLD_Coaster_CartSetupRequested'
assert {p['prefabNodeRef']['$value'] for p in owner['phasePrefabs']}=={'#mq006_pr_rollercoaster','#mq006_pr_rollercoaster_ride'}
scene=read('Coaster_scene');audit_scene_actor_ids(scene)
assert [a['actorName'] for a in scene['actors']]==['rollercoaster_cart'] and scene['playerActors'][0]['actorId']['id']==1
nodes,seen=reachable(scene,509);assert set(nodes)==seen==set(json.loads((A/'coaster_scene_delta.json').read_text())['nodes'])|{1160,1161}
for node in nodes.values():
    if node['$type']=='scnQuestNode':
        expected_stamps={(0,i) for i in range(len(node['osockMappings']))}
        actual_stamps=[(s['stamp']['name'],s['stamp']['ordinal']) for s in node['outputSockets']]
        assert len(actual_stamps)==len(expected_stamps) and set(actual_stamps)==expected_stamps,('Missing native callback',node['nodeId'])
assert {x['nodeId']['id'] for x in scene['entryPoints']}=={509} and {x['nodeId']['id'] for x in scene['exitPoints']}=={520,538}
assert {o['caption']['$value'] for i in seen for o in nodes[i].get('options',[])}=={'Exit','Handsup','GetIn'}
assert scene['screenplayStore']['lines']==[] and not any(x.get('$type')=='questSpawnManagerNodeDefinition' for x in walk(scene))
assert all(x.get('factName','').startswith('PTFRWORLD_') for x in walk(scene) if x.get('$type')=='questSetVar_NodeType')
assert 'mq006_ride_finished' not in json.dumps(scene) and 'air_traffic_start_space_shuttle' not in json.dumps(scene)
assert nodes[647]['questNode']['Data']['paramsV1']['Data']['function']=='StopWorkspot'
assert nodes[557]['outputSockets'][0]['destinations'][0]['nodeId']['id']==1160
assert nodes[557]['outputSockets'][0]['destinations'][0]['isockStamp']['ordinal']==1
assert nodes[1160]['outputSockets'][0]['destinations'][0]['nodeId']['id']==561
assert nodes[1160]['outputSockets'][0]['destinations'][0]['isockStamp']['ordinal']==0
for s in nodes[561]['outputSockets']:
    for d in s['destinations']:
        assert d['nodeId']['id'] in (558,559)
        assert d['isockStamp']['ordinal']==1
        assert nodes[d['nodeId']['id']]['isockMappings'][d['isockStamp']['ordinal']]['$value']=='In'
for variant,i in ((1,558),(2,559)):
    assert nodes[i]['$type']=='scnQuestNode' and nodes[i]['questNode']['Data']['$type']=='questUseWorkspotNodeDefinition'
    params=nodes[i]['questNode']['Data']['paramsV1']['Data']
    assert params['function']=='UseWorkspot' and params['workspotInstanceId']['id']==i
    assert params['enableIdleMode']==0
    assert params['entryId']['id']==5 and params['jumpToEntry']==1
    outputs={s['stamp']['ordinal']:s for s in nodes[i]['outputSockets']}
    assert outputs[0]['destinations']==[] # native Success can fire on replacement/stop
    assert outputs[1]['destinations'][0]['nodeId']['id']==1161 # Work Started
    assert outputs[1]['destinations'][0]['isockStamp']['ordinal']==1
    instance=next(w for w in scene['workspotInstances'] if w['workspotInstanceId']['id']==i)
    assert instance['originMarker']['slotName']['$value']=='seat_front_right' and instance['originMarker']['isMounted']==1
    wp=read(f'Coaster_hands_{variant}')
    wh=index(wp);tree=wp['workspotTree']['Data'];seq=tree['rootEntry']['Data']['list'][0]['Data']
    clip=seq['list'][0]['Data'];idle=seq['list'][1]['Data']
    assert clip['$type']=='workAnimClip' and clip['animName']['$value']==f'sit_rollercoaster__2h_on_chest__01__cheer__0{variant}'
    assert seq['id']['id']==2 and clip['id']['id']==params['entryId']['id']
    assert clip['flags']==2 and clip['blendOutTime']==0.5
    assert idle['loopInfinitely']==1 and idle['idleAnim']['$value']=='sit_rollercoaster__2h_on_chest__calm__01'
    ids=[o['id']['id'] for o in walk(tree['rootEntry']) if isinstance(o.get('id'),dict) and o['id'].get('$type')=='workWorkEntryId']
    assert len(ids)==len(set(ids)) and set(ids)=={1,2,5,6,7}
    for o in walk(wp):
        if 'HandleRefId' in o:assert str(o['HandleRefId']) in wh
    original_wp=json.loads((ROOT/'research/b0_world_interactions/coaster_crash/json/base/workspots/quest/minor_quests/mq006/player__sit_rollercoaster_train_lean_back__sit_around__02.workspot.json').read_text())['Data']['RootChunk']
    original_wp_canonical=canonical(original_wp,index(original_wp));wp_canonical=canonical(wp,wh)
    original_wp_canonical['workspotTree']['rootEntry']=wp_canonical['workspotTree']['rootEntry']
    original_wp_canonical['workspotTree']['idCounter']=7
    assert original_wp_canonical==wp_canonical # rig bindings/loading/other native resource fields unchanged
assert not {1022,1024,1026,1028}&seen # optional cinematic-yell tail not retained
assert {o['factName'] for i in (1160,1161) for o in walk(nodes[i]) if o.get('$type')=='questSetVar_NodeType'}=={'PTFRWORLD_Coaster_HandsRequests','PTFRWORLD_Coaster_HandsStarted'}
previous_scene=json.loads((ROOT/'research/b0_world_interactions/coaster_crash/rollback_revision2/Coaster_scene.json').read_text())['Data']['RootChunk']
previous_nodes={n['Data']['nodeId']['id']:n['Data'] for n in previous_scene['sceneGraph']['Data']['graph']}
assert set(nodes)==(set(previous_nodes)-{1022,1024,1026,1028})|{1160,1161}
for i in set(previous_nodes)&set(nodes)-{558,559}:
    previous=canonical(previous_nodes[i],index(previous_scene));current=canonical(nodes[i],index(scene))
    if i==557:
        previous['outputSockets'][0]['destinations'][0]['nodeId']['id']=1160
        previous['outputSockets'][0]['destinations'][0]['isockStamp']['ordinal']=1
    if i==561:
        for s in previous['outputSockets']:
            for d in s['destinations']:d['isockStamp']['ordinal']=1
    assert previous==current,('Unexpected scene-node change',i)
for variant,i in ((1,558),(2,559)):
    expected_params=canonical(previous_nodes[643]['questNode']['Data']['paramsV1'],index(previous_scene))
    expected_params['workspotInstanceId']['id']=i
    expected_params['enableIdleMode']=0
    expected_params['entryId']['id']=5
    assert expected_params==canonical(nodes[i]['questNode']['Data']['paramsV1'],index(scene))
assert scene['workspotInstances'][:len(previous_scene['workspotInstances'])]==previous_scene['workspotInstances']
assert canonical(scene['workspots'][:len(previous_scene['workspots'])],index(scene))==canonical(previous_scene['workspots'],index(previous_scene))
revision3=json.loads((ROOT/'research/b0_world_interactions/coaster_hands_binding/rollback_revision3/Coaster_scene.json').read_text())['Data']['RootChunk']
revision3_canonical=canonical(revision3,index(revision3))
current_canonical=canonical(scene,index(scene))
randomizer=next(n for n in revision3_canonical['sceneGraph']['graph'] if n['nodeId']['id']==561)
for s in randomizer['outputSockets']:
    for d in s['destinations']:d['isockStamp']['ordinal']=1
old_lips=revision3_canonical['resouresReferences']['lipsyncAnimSets']
assert len(old_lips)==7 and revision3_canonical['playerActors'][0]['lipsyncAnimSet']['id']==6
revision3_canonical['resouresReferences']['lipsyncAnimSets']=[old_lips[6]]
revision3_canonical['playerActors'][0]['lipsyncAnimSet']['id']=0
for i in (558,559):
    n=next(n for n in revision3_canonical['sceneGraph']['graph'] if n['nodeId']['id']==i)
    n['questNode']['paramsV1']['enableIdleMode']=0
    n['questNode']['paramsV1']['entryId']['id']=5
    n['outputSockets'].insert(0,{'$type':'scnOutputSocket','destinations':[],
                               'stamp':{'$type':'scnOutputSocketStamp','name':0,'ordinal':0}})
assert revision3_canonical==current_canonical # ONLY input/lipsync/callback repairs, idle flags and direct cheer entries
revision4=json.loads((ROOT/'research/b0_world_interactions/coaster_repeat_gesture/rollback_revision4/Coaster_scene.json').read_text())['Data']['RootChunk']
revision4_canonical=canonical(revision4,index(revision4))
for i in (558,559):
    n=next(n for n in revision4_canonical['sceneGraph']['graph'] if n['nodeId']['id']==i)
    assert n['questNode']['paramsV1']['enableIdleMode']==1
    n['questNode']['paramsV1']['enableIdleMode']=0
    n['questNode']['paramsV1']['entryId']['id']=5
    n['outputSockets'].insert(0,{'$type':'scnOutputSocket','destinations':[],
                               'stamp':{'$type':'scnOutputSocketStamp','name':0,'ordinal':0}})
assert revision4_canonical==current_canonical # all other scene data, workspots and exit behavior preserved
revision5_root=ROOT/'research/b0_world_interactions/coaster_direct_entry/rollback_revision5'
revision5_receipt=json.loads((revision5_root/'install_receipt.json').read_text())
assert revision5_receipt['status']=='INSTALLED_COASTER_REPAIR_CANDIDATE_REVISION5'
assert hashlib.sha256((revision5_root/'TowerContinued_WorldInteractions.archive').read_bytes()).hexdigest().upper()==revision5_receipt['sha256'][0]
revision5=json.loads((revision5_root/'Coaster_scene.json').read_text())['Data']['RootChunk']
# Include embedded quest socket definitions as well as all other scene fields.
# Only the two cheer entry targets may differ from the preserved revision5.
revision5_exact=canonical(revision5,index(revision5),keep_sockets=True)
current_exact=canonical(scene,index(scene),keep_sockets=True)
for i in (558,559):
    n=next(n for n in revision5_exact['sceneGraph']['graph'] if n['nodeId']['id']==i)
    params=n['questNode']['paramsV1']
    assert params['entryId']['id']==2 and params['enableIdleMode']==0 and params['jumpToEntry']==1
    params['entryId']['id']=5
assert revision5_exact==current_exact, 'Revision6 must change only entryId2->5 on cheer nodes558/559'
assert len(scene['resouresReferences']['lipsyncAnimSets'])==1
assert scene['playerActors'][0]['lipsyncAnimSet']['id']==0
assert scene['resouresReferences']['lipsyncAnimSets'][0]['asyncRefLipsyncAnimSet']['DepotPath']['$value'].endswith('\\v.anims')
assert nodes[530]['$type']=='scnSectionNode' # retain the authored exit animation and every exit edge
refs=json.loads((A/'coaster_refs.json').read_text())
ride=read('Coaster_ride');original=read('Coaster_ride_original');graphs+=graph_audit(ride)
assert quest_edges(ride)[0]==quest_edges(original)[0]
br=canonical(original,index(original));ar=canonical(ride,index(ride))
expected_ride=json.dumps(br).replace('mq006_ride_finished','PTFRWORLD_Coaster_Finished')
for short,full in refs.items():expected_ride=expected_ride.replace(json.dumps(short),json.dumps(full))
assert json.loads(expected_ride)==ar
assert {x['factName'] for x in walk(ride) if x.get('$type')=='questSetVar_NodeType'}=={'PTFRWORLD_Coaster_Finished'}
for stem,node in (('quest_dc94c198a1cbdae9',38),('quest_f816da004b0f9f78',8)):
    sector=json.loads((ROOT/f'research/b0_world_interactions/extended/json/base/worlds/03_night_city/_compiled/default/{stem}.streamingsector.json').read_text())['Data']['RootChunk']
    assert sector['nodes'][node]['Data']['spawnOnStart']==0
archive=ROOT/'build/WorldInteractions/TowerContinued_WorldInteractions.archive'
assert hashlib.sha256(archive.read_bytes()).hexdigest().upper()==m['sha256']
assert hashlib.sha256(Path(str(archive)+'.xl').read_bytes()).hexdigest().upper()==m['xl_sha256']
print(f'PASS: {graphs} reciprocal graphs, {negative} negative guards; exact media/memorial/ride deltas; dense V/cart cast; no Johnny/story roots, replacements or new polling')
