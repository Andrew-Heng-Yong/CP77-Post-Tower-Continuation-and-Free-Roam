import copy
import json
from pathlib import Path

root = Path(__file__).parent / 'candidate_02'
proof = json.loads((root / 'visual_07/proof.json').read_text(encoding='utf-8'))
assert proof['status'] == 'WORKSPACE_VISUAL_SEVEN_RESOURCE_FINAL_NOT_INSTALLED'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))['Data']['RootChunk']

def canonical(value):
    if isinstance(value, dict):
        return {k: canonical(v) for k, v in value.items() if k not in ('HandleId', 'HandleRefId')}
    if isinstance(value, list):
        return [canonical(v) for v in value]
    return value

def node(scene, identifier):
    matches = [x['Data'] for x in scene['sceneGraph']['Data']['graph'] if x['Data'].get('nodeId', {}).get('id') == identifier]
    assert len(matches) == 1, identifier
    return matches[0]

def assert_refs(scene):
    ids, refs = set(), set()
    def walk(value):
        if isinstance(value, dict):
            if 'HandleId' in value:
                ids.add(str(value['HandleId']))
            if 'HandleRefId' in value:
                refs.add(str(value['HandleRefId']))
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)
    walk(scene)
    assert refs <= ids, refs - ids

names = {'#sq025_ws_johnny_resurgence': 'delamain', '#mq018_ws_johnny_protein_stairs': 'killing', '#loc1_Johnny_corpses': 'freedom', '#mq016_ws_johnny_at_coffin': 'kold'}
for item in proof['additional']:
    name = names[item['anchor']]
    old = read(root / f'visual_baseline_02/{name}.scene.json')
    new = read(root / 'visual_07' / (item['depot'] + '.json'))
    assert_refs(new)
    if item['kind'] == 'freedom':
        base_spot = next(x['Data'] for x in old['workspots'] if x['Data']['dataId']['id'] == 3111754765)
        edited_spot = next(x['Data'] for x in new['workspots'] if x['Data']['dataId']['id'] == 3111754765)
        assert base_spot['workspotResource']['DepotPath']['$value'] == 'base\\workspots\\main_characters\\johnny\\ground\\johnny__walk_ground_cigarette__aggressive__01.workspot'
        assert edited_spot['workspotResource']['DepotPath']['$value'] == 'towercontinued\\sidejobs_s29\\native\\base\\workspots\\main_characters\\johnny\\ground\\johnny__walk_ground_cigarette__aggressive__01.workspot'
        edited_spot['workspotResource'] = copy.deepcopy(base_spot['workspotResource'])
    else:
        instance = [x for x in new['workspotInstances'] if x['workspotInstanceId']['id'] == item['instance']]
        assert len(instance) == 1
        assert instance[0]['originMarker']['nodeRef']['$value'] == item['anchor']
        assert instance[0]['playAtActorLocation'] == 0
        new['workspotInstances'].remove(instance[0])
        data_id = 4231323113 if item['kind'] == 'ground' else 3237006318
        data = [x for x in new['workspots'] if x['Data']['dataId']['id'] == data_id]
        assert len(data) == 1
        assert data[0]['Data']['workspotResource']['DepotPath']['$value'] == ('towercontinued\\sidejobs_s29\\native\\base\\workspots\\main_characters\\johnny\\johnny__stand_ground_cigarette__idle__01.workspot' if item['kind'] == 'ground' else proof['new_private_kold']['depot'])
        new['workspots'].remove(data[0])
        for identifier in item['nodes']:
            old_params = node(old, identifier)['questNode']['Data']['paramsV1']['Data']
            new_params = node(new, identifier)['questNode']['Data']['paramsV1']['Data']
            assert old_params['$type'] == 'questUseWorkspotParamsV1'
            assert old_params['workspotNode']['$value'] == item['anchor']
            assert new_params['$type'] == 'scnUseSceneWorkspotParamsV1'
            assert new_params['workspotInstanceId']['id'] == item['instance']
            assert new_params['workspotNode']['$value'] == '0'
            assert new_params['playAtActorLocation'] == 0
            assert new_params['itemOverride']['itemOverrides'] == new_params['itemOverride']['propOverrides'] == []
            for key, value in old_params.items():
                if key not in ('$type', 'workspotNode'):
                    assert new_params[key] == value, (name, identifier, key)
            node(new, identifier)['questNode']['Data']['paramsV1']['Data'] = copy.deepcopy(old_params)
    assert canonical(old) == canonical(new), name

base = read(root / 'visual_baseline_02/kold.workspot.json')
edited = read(root / 'visual_07' / (proof['new_private_kold']['depot'] + '.json'))
assert_refs(edited)
old_filter = base['nodesToInit'][0]['Data']['nodes'][0]['Data']['node']['node']['Data']
new_filter = edited['nodesToInit'][0]['Data']['nodes'][0]['Data']['node']['node']['Data']
assert old_filter['eventFilterType'] == 'Default'
assert new_filter['eventFilterType'] == 'Mute'
new_filter['eventFilterType'] = 'Default'
assert canonical(base) == canonical(edited), 'KOLD resource changed beyond event filter'

result = {'status': 'VISUAL_FOUR_ADDITIONAL_SCENES_AND_EXACT_KOLD_WORKSPOT_SEMANTIC_PASS', 'additional_scenes': 4, 'patched_world_calls': 11, 'new_private_workspots': 1, 'all_other_fields_equal_to_serialized_baseline': True, 'game_writes': 0, 'save_writes': 0}
(root / 'test_visual_02.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result))
