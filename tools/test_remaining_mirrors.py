"""Check exact vanilla payload retention and scoped automatic mirror wrappers."""
import binascii
import hashlib
import json
import re
import sys
from pathlib import Path
from audit_scene_actor_ids import audit_scene_actor_ids
from test_streetkid_scene_load_s3 import quest_edges

root=Path(__file__).resolve().parents[1]
homes='--relationship-homes' in sys.argv
family='relationship_mirrors' if homes else 'remaining_mirrors'
package='RelationshipMirrors' if homes else 'RemainingMirrors'
audit=root/f'research/b0_{family}'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
manifest=read(audit/'manifest.json')
assert {s['id'] for s in manifest['sites']}==({7,10,13,20} if homes else {4,6,12,14,15,19,24,37})
assert set(manifest['deferred_ids'])==({9} if homes else {7,9,10,13,16,17,18,20})
if homes:assert set(manifest['ending_only_excluded_ids'])=={16,17,18}
inventory={r['id']:r for r in read(root/'research/b0_remaining_mirrors/inventory.json')}
def clean(v):
    if isinstance(v,dict):return {k:clean(x) for k,x in v.items() if k not in ('HandleId','HandleRefId')}
    if isinstance(v,list):return [clean(x) for x in v]
    return v
def walk(v):
    if isinstance(v,dict):
        yield v
        for x in v.values():yield from walk(x)
    elif isinstance(v,list):
        for x in v:yield from walk(x)
def expected_transform(v,short,full,ident):
    if isinstance(v,dict):
        out={k:expected_transform(x,short,full,ident) for k,x in v.items()}
        if v.get('$type')=='NodeRef' and v.get('$value')==short:out['$value']=full
        if ident==12 and v.get('factName')=='mirror_scene_shady_ripper_exit':out['factName']='PTFRRM12_Exit'
        return out
    if isinstance(v,list):return [expected_transform(x,short,full,ident) for x in v]
    return v
all_ids={}
for f in (root/'archive').rglob('*.xl'):
    for p in re.findall(r'path:\s*([^\s#]+\.questphase)',f.read_text(encoding='utf-8-sig')):
        crc=binascii.crc_hqx((p+':1').encode(),65535)
        all_ids.setdefault(crc,set()).add(p)
for site in manifest['sites']:
    i=site['id'];info=inventory[i];short=info['triggers'][0];full=site['trigger']
    scene=read(audit/f'm{i}_scene.json')['Data']['RootChunk']
    original=read(audit/f'm{i}_original_scene.json')['Data']['RootChunk']
    assert clean(scene)==clean(expected_transform(original,short,full,i)),f'scene delta {i}'
    audit_scene_actor_ids(scene)
    assert [a['actorName'] for a in scene['actors']]==['v_tpp_mirror_male','v_tpp_mirror_female']
    assert [a['playerName'] for a in scene['playerActors']]==['V']
    before=read(audit/f'm{i}_original_owner.json')['Data']['RootChunk']
    owner=read(audit/f'm{i}_owner.json')['Data']['RootChunk']
    gate=read(audit/f'm{i}_gate.json')['Data']['RootChunk']
    try:
        oe,on=quest_edges(owner);be,bn=quest_edges(before)
    except AssertionError as e:
        raise AssertionError(f'site {i}: native graph handles/edges invalid') from e
    assert oe==be,f'vanilla edges changed {i}'
    transformed=expected_transform(before,short,full,i)
    expected_nodes={n['Data']['id']:n['Data'] for n in transformed['graph']['Data']['nodes']}
    gate_guard=next(n['Data']['condition']['Data'] for n in gate['graph']['Data']['nodes'] if n['Data']['id']==1)
    gate_facts={x['factName']:(x['comparisonType'],x['value']) for x in walk(gate_guard) if x.get('$type')=='questVarComparison_ConditionType'}
    expected_facts={f:('Equal',v) for f,v in dict(PostTowerFreeRoamActive=1,PTFRP0_DR13=1,q307_active=0,q307_done=1,q307_finished=1,q307_2079=1,q307_main_game_killed=1,q305_johnny_scene_active=0,mirror_interaction_disabled=0,q115_point_of_no_return=0,PTFRBASE_Suspended=0).items()}
    expected_facts[f'PTFRRM{i}_Suspended']=('Equal',0)
    if i==6:
        for f in ['nomad_camp_01_active_combat','sq027_camp_abandoned','sq027_camp_moved']:expected_facts[f]=('LessOrEqual',0)
    if i==37:expected_facts['sts_wbr_hil_01_mirror_enabled']=('Greater',0)
    if i==7:expected_facts['nomad_camp_02_active_default']=('Greater',0)
    assert gate_facts==expected_facts
    guards=0
    for n in on:
        expected=expected_nodes[n['id']]
        if n['$type']=='questSceneNodeDefinition':
            expected['sceneFile']['DepotPath']['$value']=f'towercontinued\\{family}\\m{i}.scene'
        if expected.get('condition',{}).get('Data',{}).get('$type')=='questTriggerCondition' and expected['condition']['Data']['type']=='IsInside':
            g=n['condition']['Data']
            assert g['operation']=='AND'
            assert clean(g['conditions'][:-1])==clean(gate_guard['conditions'])
            assert clean(g['conditions'][-1]['Data'])==clean(expected['condition']['Data'])
            expected['condition']=n['condition'];guards+=1
        assert clean(n)==clean(expected),(i,n['id'])
    assert guards==1
    assert len(owner['phasePrefabs'])==1 and owner['phasePrefabs'][0]['prefabNodeRef']['$value']==info['prefab']
    assert gate['phasePrefabs']==[]
    ge,_=quest_edges(gate)
    assert ge=={(0,'Out',1,'In'),(1,'Out',2,'In1')}
    for obj in walk([scene,owner,gate]):
        if obj.get('$type')=='questSetVar_NodeType':
            assert (i==12 and obj['factName']=='PTFRRM12_Exit') or (i==7 and obj['factName']=='dlc3_panam_mirror_in_use' and obj['setExactValue']==1 and obj['value'] in (0,1))
    if i==7:
        # Preserve the mirror/wardrobe interlock, not a romance permission.
        writers=[x for x in walk(scene) if x.get('$type')=='questSetVar_NodeType']
        assert sorted(x['value'] for x in writers)==[0,1]
        assert len(scene['props'])==1 and scene['props'][0]['propName']=='mirror'
        assert scene['props'][0]['findEntityInNodeParams']['nodeRef']['$value']=='#mirror_scene_dvc_smart_mirror_new_camp'
    depot=f'towercontinued\\{family}\\m{i}_gate.questphase'
    crc=binascii.crc_hqx((depot+':1').encode(),65535)
    assert crc==site['registration_id'] and all_ids[crc]=={depot},(i,all_ids[crc])
assert len(manifest['resources'])==(12 if homes else 24)
archive=root/f'build/{package}/TowerContinued_{package}.archive'
assert hashlib.sha256(archive.read_bytes()).hexdigest().upper()==manifest['sha256']
xl=archive.with_name(archive.name+'.xl').read_text(encoding='utf-8-sig')
assert re.findall(r'path:\s*([^\s#]+\.questphase)',xl)==[f'towercontinued\\{family}\\m{s["id"]}_gate.questphase' for s in manifest['sites']]
assert xl.count('parent: ep1\\quest\\ep1.quest')==len(manifest['sites'])
assert xl== (root/f'archive/b0_{family}/TowerContinued_{package}.archive.xl').read_text(encoding='utf-8-sig')
print(f'PASS: {len(manifest["sites"])} exact vanilla scene/leaf payloads, unchanged graph edges/cast, scoped NodeRefs/private exit handshake, repeated Tower/local guards, {len(manifest["resources"])} packed resources and registration isolation')
