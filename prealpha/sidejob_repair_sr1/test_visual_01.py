import copy
import json
from pathlib import Path

root = Path(__file__).parent / 'candidate_02'
baseline = root / 'visual_baseline_01'
patched = root / 'visual_03'

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))['Data']['RootChunk']

def canonical(x):
    if isinstance(x, dict):
        return {k: canonical(v) for k, v in x.items() if k not in ('HandleId', 'HandleRefId')}
    if isinstance(x, list):
        return [canonical(v) for v in x]
    return x

def assert_handle_references_resolve(x):
    ids, refs = set(), set()
    def walk(value):
        if isinstance(value, dict):
            if 'HandleId' in value:
                ids.add(str(value['HandleId']))
            if 'HandleRefId' in value:
                refs.add(str(value['HandleRefId']))
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(x)
    assert refs <= ids, refs - ids

def scene_node(scene, node_id):
    matches = [n['Data'] for n in scene['sceneGraph']['Data']['graph'] if n['Data'].get('nodeId', {}).get('id') == node_id]
    assert len(matches) == 1, node_id
    return matches[0]

base = read(baseline / 'sweet.json')
actual = read(patched / 'sweet_dreams_scene.json')
assert_handle_references_resolve(actual)
inst = [w for w in actual['workspotInstances'] if w['workspotInstanceId']['id'] == 3131]
assert len(inst) == 1
assert inst[0]['dataId']['id'] == 4231323113
assert inst[0]['originMarker']['nodeRef']['$value'] == '#mq036_ws_johnny_exit'
assert inst[0]['playAtActorLocation'] == 0
for node_id in (158, 1073):
    old = scene_node(base, node_id)['questNode']['Data']['paramsV1']['Data']
    new = scene_node(actual, node_id)['questNode']['Data']['paramsV1']['Data']
    assert old['$type'] == 'questUseWorkspotParamsV1'
    assert old['workspotNode']['$value'] == '#mq036_ws_johnny_exit'
    assert new['$type'] == 'scnUseSceneWorkspotParamsV1'
    assert new['workspotInstanceId']['id'] == 3131
    assert new['workspotNode']['$value'] == '0'
    assert new['playAtActorLocation'] == 0
    assert new['itemOverride']['itemOverrides'] == new['itemOverride']['propOverrides'] == []
    for key, value in old.items():
        if key in ('$type', 'workspotNode'):
            continue
        assert new[key] == value, (node_id, key)
    scene_node(actual, node_id)['questNode']['Data']['paramsV1']['Data'] = copy.deepcopy(old)
actual['workspotInstances'] = [w for w in actual['workspotInstances'] if w['workspotInstanceId']['id'] != 3131]
assert canonical(actual) == canonical(base), 'Sweet Dreams changed beyond two workspot nodes and one instance'

base = read(baseline / 'sinnerman.json')
actual = read(patched / 'sinnerman_restaurant.json')
assert_handle_references_resolve(actual)
old_events = scene_node(base, 635)['events']
matches = [e for e in old_events if str(e['Data']['id']['id']) == '2514459860119400448']
assert len(matches) == 1
assert matches[0]['Data']['$type'] == 'scneventsVFXEvent'
assert matches[0]['Data']['effectEntry']['effectName']['$value'] == 'ember'
old_events.remove(matches[0])
assert canonical(actual) == canonical(base), 'Sinnerman changed beyond dangling ember event'

proof = {
    'status': 'VISUAL_TWO_RESOURCE_SEMANTIC_PRESERVATION_PASS',
    'sweet_dreams': {'private_marker_instance': 3131, 'converted_nodes': [158, 1073], 'all_other_fields_equal_to_serialized_baseline': True},
    'sinnerman': {'section': 635, 'removed_ember_event': '2514459860119400448', 'all_other_fields_equal_to_serialized_baseline': True},
    'game_writes': 0,
    'save_writes': 0,
}
dest = root / 'test_visual_01.json'
dest.write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps(proof))
