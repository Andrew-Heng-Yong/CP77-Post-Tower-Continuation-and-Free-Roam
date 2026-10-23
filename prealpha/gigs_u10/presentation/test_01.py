"""Independent readback checks of the strictly scoped U10 presentation edits."""
import copy
import importlib.util
import json
import sys
from pathlib import Path
from prepare_01 import ROOT, SCENE, PHASES, MOD, read, sha, rel, walk, write

spec = importlib.util.spec_from_file_location('raw_compare', ROOT / 'prealpha/sidejobs_s27/raw_compare.py')
rawlib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rawlib)


def canonical(obj):
    """Compare graphs including cyclic handle edges under bijective ID relabeling."""
    obj = rawlib.canonical(copy.deepcopy(obj))
    ids = {}
    for _, item in walk(obj):
        if 'HandleId' in item:
            assert item['HandleId'] not in ids, ('duplicate handle', item['HandleId'])
            ids[item['HandleId']] = str(len(ids))
    for _, item in walk(obj):
        for key in ['HandleId', 'HandleRefId']:
            if key in item:
                assert item[key] in ids, ('dangling handle', item[key])
                item[key] = ids[item[key]]
    return obj


def test(build):
    assert not (build / 'tests.json').exists()
    m = read(build / 'component.json')
    p = read(build / 'prepared.json')
    assert m['prepared_sha256'] == sha(build / 'prepared.json')
    checks = cases = 0
    for source, wanted in m['source_pins'].items():
        assert sha(ROOT / source) == wanted, source
        checks += 1
    assert not m['boots'] and not m['native_overrides']
    assert set(m['reference_replacements']) == {SCENE, *PHASES}
    for item in m['inputs']:
        depot = item['depot']
        assert depot.startswith(MOD + '\\') and '..' not in depot
        assert sha(build / 'source' / depot) == m['resources'][depot]
        expected = read(ROOT / item['expected'])['Data']['RootChunk']
        actual = read(build / 'readback' / (depot + '.json'))['Data']['RootChunk']
        assert canonical(actual) == canonical(expected), ('binary readback', depot)
        checks += 1

    # Independent selective diff against the original, without using the builder.
    scene_item = next(i for i in m['inputs'] if i['depot'].endswith('.scene'))
    native = read(ROOT / scene_item['native_json'])['Data']['RootChunk']
    actual = read(ROOT / scene_item['expected'])['Data']['RootChunk']
    assert actual['actors'] == native['actors']
    assert actual['playerActors'] == native['playerActors']
    assert actual['props'] == native['props'][:5]
    assert native['props'][5]['findEntityInEntityParams']['performerId']['id'] == 769
    assert native['props'][6]['findEntityInEntityParams']['performerId']['id'] == 769
    assert {native['props'][i]['specPropRecordId']['$value'] for i in [5,6]} == {'Items.cigarette_i_stick','Items.apparel_lighter_a'}
    assert actual['workspotInstances'] == native['workspotInstances']
    assert len(actual['sceneGraph']['Data']['graph']) == len(native['sceneGraph']['Data']['graph'])
    removed = []
    muted = []
    for old_wrap, new_wrap in zip(native['sceneGraph']['Data']['graph'], actual['sceneGraph']['Data']['graph']):
        old = old_wrap['Data']; new = new_wrap['Data']
        assert old['nodeId'] == new['nodeId']
        node_expected = copy.deepcopy({k:v for k,v in old.items() if k != 'events'})
        for _, item in walk(node_expected):
            if 'DepotPath' in item and isinstance(item['DepotPath'],dict) and item['DepotPath'].get('$value') in m['reference_replacements']:
                item['DepotPath']['$value'] = m['reference_replacements'][item['DepotPath']['$value']]
        assert node_expected == {k:v for k,v in new.items() if k != 'events'}
        new_events = {e['Data']['id']['id']: e['Data'] for e in new.get('events', [])}
        for event in old.get('events', []):
            e = event['Data']; ident = e['id']['id']
            if ident not in new_events:
                assert e['performerId']['id'] == 769
                assert e['$type'] in ('scneventsEquipItemToPerformer','scneventsUnequipItemFromPerformer','scneventsVFXEvent')
                if e['$type'] == 'scneventsEquipItemToPerformer':
                    assert e['itemId']['$value'] in ('Items.cigarette_i_stick','Items.apparel_lighter_a')
                if e['$type'] == 'scneventsVFXEvent':
                    assert e['effectEntry']['effectName']['$value'].startswith('johnny_')
                removed.append(ident)
            else:
                wanted = copy.deepcopy(e)
                if wanted['$type'] == 'scnPlaySkAnimEvent' and wanted.get('performer',{}).get('id') == 769:
                    assert wanted['muteAnimEvents'] == '0'
                    wanted['muteAnimEvents'] = 'STANDARD'
                    muted.append(ident)
                assert new_events[ident] == wanted, ('unapproved scene event delta', old['nodeId'], ident)
            checks += 1
    assert set(removed) == {e['id'] for e in p['removed_events']}
    assert set(muted) == set(p['muted_events'])
    for field in native:
        if field not in ('props','sceneGraph','debugSymbols','workspots'):
            assert actual[field] == native[field], field
            checks += 1
    assert actual['debugSymbols']['sceneNodesDebugSymbols'] == native['debugSymbols']['sceneNodesDebugSymbols']
    assert actual['debugSymbols']['workspotsDebugSymbols'] == native['debugSymbols']['workspotsDebugSymbols']
    assert actual['debugSymbols']['performersDebugSymbols'] == native['debugSymbols']['performersDebugSymbols'][:-2]
    for symbol in actual['debugSymbols']['sceneEventsDebugSymbols']:
        assert all(e['id'] not in removed for e in symbol['sceneEventIds'])

    # Main and two descendant phase clones are EXACT native graph payloads except
    # for the three intended resource-reference substitutions. Socket graphs,
    # journal outcomes, rewards, conditions and per-job optional outcomes remain.
    for item in m['inputs']:
        old = read(ROOT / item['native_json'])['Data']['RootChunk']
        new = read(ROOT / item['expected'])['Data']['RootChunk']
        if item['depot'].endswith('.questphase'):
            wanted = copy.deepcopy(old)
            n = 0
            for _, o in walk(wanted):
                if 'DepotPath' in o and isinstance(o['DepotPath'],dict) and o['DepotPath'].get('$value') in m['reference_replacements']:
                    o['DepotPath']['$value'] = m['reference_replacements'][o['DepotPath']['$value']]
                    n += 1
            assert n > 0 and wanted == new, item['depot']
            checks += sum(1 for _,o in walk(new) if o.get('$type','').endswith('NodeDefinition'))
        elif item['depot'].endswith('.workspot'):
            wanted = copy.deepcopy(old)
            for _, o in walk(wanted):
                if o.get('$type') == 'animAnimNode_WorkspotHub':
                    assert o['eventFilterType'] == 'Default'
                    o['eventFilterType'] = 'Mute'
                if o.get('$type') == 'workWorkspotTree' and o.get('initialActions'):
                    assert len(o['initialActions']) == 1
                    assert o['initialActions'][0]['Data']['$type'] == 'workEquipItemToSlotAction'
                    assert 'cigarette' in json.dumps(o['initialActions'])
                    o['initialActions'] = []
            assert new == wanted, item['depot']
            checks += 1
    # Negative witnesses: body/voice and non-Johnny equip, props and callbacks
    # must survive, and each preserved actor remains present.
    assert len(actual['props']) == 5
    assert any(e['Data']['$type'] == 'scneventsEquipItemToPerformer' and e['Data']['performerId']['id'] != 769
               for n in actual['sceneGraph']['Data']['graph'] for e in n['Data'].get('events',[]))
    for actor in actual['actors']:
        assert actor in native['actors']; cases += 1
    # Dependency IDs are inputs, not a runtime permission certificate.
    for row in p['rows']:
        assert not row['missing']; cases += 1
    result = {'status':'PASS_U10_PRESENTATION_OFFLINE_NOT_LIVE',
              'component_sha256':sha(build/'component.json'),'tester_sha256':sha(Path(__file__)),
              'native_payload_checks':checks,'policy_cases':cases,
              'resources':len(m['resources']),'scene_nodes_preserved':len(native['sceneGraph']['Data']['graph']),
              'removed_johnny_props':[5,6],'removed_johnny_presentation_events':len(removed),
              'muted_johnny_animation_events':len(muted),'official_overrides':0,
              'quest_graph_edges_changed':0,'dialog_or_choice_events_changed':0,
              'live_renderer_audio_gameplay_proof':False}
    write(build/'tests.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    test(Path(sys.argv[1]).resolve())
