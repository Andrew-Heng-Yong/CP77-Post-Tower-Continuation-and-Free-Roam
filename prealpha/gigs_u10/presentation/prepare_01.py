"""U10 Psychofan presentation adapter. No official resource is overridden.

Keep the native Johnny actor, dialog, choices, events' timing and quest graph.
Remove only his independently rendered smoking props and visual effects.
Native workspots used only by Johnny get private copies with animation events
muted (dialog remains scene events); NPC workspots and props stay untouched.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
EVIDENCE = ROOT / 'research/gigs_u10/presentation'
IDS = 'sts_hey_gle_03 sts_hey_gle_05 sts_hey_rey_01 sts_hey_rey_02 sts_std_arr_03 sts_wat_nid_07 sts_wbr_hil_06 sts_wbr_jpn_12'.split()
PREFIX = r'base\open_world\street_stories\heywood\glenn\sts_hey_gle_03'
MOD = r'towercontinued\gigs_u10\presentation'
SCENE = PREFIX + r'\scenes\sts_hey_gle_03_scene.scene'
PHASES = [PREFIX + '\\phases\\sts_hey_gle_03_' + s + '.questphase' for s in ('gameplay', 'ow', 'phase')]
INDEX_INPUTS = ['research/omitted_jobs_audit/native_screen_03.json',
                'research/omitted_jobs_audit/review_02/native_audit_02.json']


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def rel(path):
    return str(Path(path).relative_to(ROOT)).replace('\\', '/')


def walk(obj, path='$'):
    if isinstance(obj, dict):
        yield path, obj
        for key, value in obj.items():
            yield from walk(value, path + '/' + key)
    elif isinstance(obj, list):
        for key, value in enumerate(obj):
            yield from walk(value, path + '/' + str(key))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def prepare(out):
    assert not out.exists(), 'Immutable build exists'
    out.mkdir(parents=True)
    index = {}
    for f in INDEX_INPUTS:
        index.update(read(ROOT / f)['resources'])
    pins = {f: sha(ROOT / f) for f in INDEX_INPUTS}
    for f in ['prealpha/gigs_u10/presentation/prepare_01.py',
              'prealpha/gigs_u10/presentation/build_01.ps1',
              'prealpha/gigs_u10/presentation/test_01.py',
              'prealpha/sidejobs_s27/raw_compare.py',
              'tools/build_phase2a.ps1',
              'research/gigs_u10/presentation/native_01/inventory.json',
              'research/gig_restoration/lore_whitelists_v6_1_dependencies.json',
              'redscript/PTFR_JohnnyVoiceJV1/JohnnyVoiceJV1.reds']:
        pins[f] = sha(ROOT / f)

    def native(dep):
        p = ROOT / index[dep]['source']
        raw = Path(str(p).replace('\\json\\', '\\raw\\')[:-5])
        assert raw.exists(), raw
        assert sha(p) == index[dep]['sha256']
        pins[rel(p)] = sha(p)
        pins[rel(raw)] = sha(raw)
        return read(p)

    originals = {dep: native(dep) for dep in [SCENE] + PHASES}
    original = originals[SCENE]['Data']['RootChunk']
    scene = copy.deepcopy(originals[SCENE])
    root = scene['Data']['RootChunk']
    johnny = next(a for a in root['actors'] if a['actorName'] == 'silverhand')
    assert johnny['actorId']['id'] == 3 and johnny['acquisitionPlan'] == 'spawnDespawn'
    assert johnny['spawnDespawnParams']['specRecordId']['$value'] == 'Character.Silverhand'
    name = johnny['spawnDespawnParams']['dynamicEntityUniqueName']['$value']
    performer = 769
    propids = {5, 6}
    assert len(root['props']) == 7
    for prop in root['props'][5:]:
        assert prop['entityAcquisitionPlan'] == 'findInEntity'
        assert prop['findEntityInEntityParams']['performerId']['id'] == performer
    # The two end-of-array props have no actual prop references, only debug IDs.
    references = [(p, o) for p, o in walk(root) if o.get('$type') == 'scnPropId' and o.get('id') in propids]
    assert {p for p, _ in references} == {'$/props/5/propId', '$/props/6/propId'}
    root['props'] = root['props'][:5]
    root['debugSymbols']['performersDebugSymbols'] = [d for d in root['debugSymbols']['performersDebugSymbols']
                                                      if d['performerId']['id'] not in (1282, 1538)]
    removed_events = []
    muted_events = []
    johnny_instances = set()
    other_instances = set()
    for node in root['sceneGraph']['Data']['graph']:
        node = node['Data']
        quest = node.get('questNode', {}).get('Data', {})
        if quest.get('$type') == 'questUseWorkspotNodeDefinition':
            instance = quest.get('paramsV1', {}).get('Data', {}).get('workspotInstanceId', {}).get('id')
            if instance is not None:
                is_johnny = quest['entityReference']['dynamicEntityUniqueName']['$value'] == name
                (johnny_instances if is_johnny else other_instances).add(instance)
        retained = []
        for event in node.get('events', []):
            e = event['Data']
            typ = e['$type']
            if e.get('performerId', {}).get('id') == performer and typ in (
                    'scneventsEquipItemToPerformer', 'scneventsUnequipItemFromPerformer', 'scneventsVFXEvent'):
                removed_events.append({'node': node['nodeId']['id'], 'id': e['id']['id'], 'type': typ,
                                       'event': copy.deepcopy(e)})
                continue
            is_johnny = e.get('performer', {}).get('id') == performer
            if typ == 'scnPlaySkAnimEvent' and is_johnny:
                assert e['muteAnimEvents'] == '0'
                e['muteAnimEvents'] = 'STANDARD'
                muted_events.append(e['id']['id'])
            instance = e.get('poseBlendOutWorkspot', {}).get('Data', {}).get('workspotId', {}).get('id') if e.get('poseBlendOutWorkspot') else None
            if instance is not None:
                (johnny_instances if is_johnny else other_instances).add(instance)
            retained.append(event)
        if 'events' in node:
            node['events'] = retained
    assert not johnny_instances & other_instances
    removed_ids = {e['id'] for e in removed_events}
    # Remove only debug entries for removed presentation events.
    symbols = root['debugSymbols']['sceneEventsDebugSymbols']
    for symbol in symbols:
        symbol['sceneEventIds'] = [e for e in symbol['sceneEventIds'] if e['id'] not in removed_ids]
    root['debugSymbols']['sceneEventsDebugSymbols'] = [e for e in symbols if e['sceneEventIds']]
    instances = {w['workspotInstanceId']['id']: w['dataId']['id'] for w in root['workspotInstances']}
    johnny_dataids = {instances[i] for i in johnny_instances}
    assert not johnny_dataids & {instances[i] for i in other_instances}, 'Shared workspot must have a separate scene data binding'

    resources = []
    mappings = {dep: MOD + '\\' + dep.rsplit('\\', 1)[-1] for dep in [SCENE] + PHASES}
    workspot_changes = []
    for workspot in root['workspots']:
        w = workspot['Data']
        if w['dataId']['id'] not in johnny_dataids:
            continue
        dep = w['workspotResource']['DepotPath']['$value']
        source = EVIDENCE / 'native_01/json' / (dep + '.json')
        raw = EVIDENCE / 'native_01/raw' / dep
        pins[rel(source)] = sha(source)
        pins[rel(raw)] = sha(raw)
        obj = read(source)
        changes = []
        for path, value in walk(obj['Data']['RootChunk']):
            if value.get('$type') == 'animAnimNode_WorkspotHub':
                assert value['eventFilterType'] == 'Default'
                value['eventFilterType'] = 'Mute'
                changes.append(path + '/eventFilterType')
            if value.get('$type') == 'workWorkspotTree':
                actions = value.get('initialActions', [])
                assert all(a['Data']['$type'] == 'workEquipItemToSlotAction' for a in actions)
                if actions:
                    assert len(actions) == 1 and 'cigarette' in json.dumps(actions)
                    value['initialActions'] = []
                    changes.append(path + '/initialActions')
        assert changes
        target = MOD + '\\workspots\\' + dep.rsplit('\\', 1)[-1]
        w['workspotResource']['DepotPath']['$value'] = target
        file = out / 'expected' / (target + '.json')
        write(file, obj)
        resources.append({'depot': target, 'expected': rel(file), 'native_json': rel(source), 'native_raw': rel(raw)})
        workspot_changes.append({'depot': dep, 'target': target, 'paths': changes, 'data_id': w['dataId']['id']})

    for dep in [SCENE] + PHASES:
        obj = scene if dep == SCENE else copy.deepcopy(originals[dep])
        for _, item in walk(obj):
            if 'DepotPath' in item and isinstance(item['DepotPath'], dict):
                old = item['DepotPath'].get('$value')
                if old in mappings:
                    item['DepotPath']['$value'] = mappings[old]
        file = out / 'expected' / (mappings[dep] + '.json')
        write(file, obj)
        source = ROOT / index[dep]['source']
        raw = Path(str(source).replace('\\json\\', '\\raw\\')[:-5])
        resources.append({'depot': mappings[dep], 'expected': rel(file), 'native_json': rel(source), 'native_raw': rel(raw)})

    # Resolve all eight full quest/scene closures and preserve their witnesses.
    rows = {}
    for f in INDEX_INPUTS:
        for row in read(ROOT / f)['rows']:
            if row['id'] in IDS:
                rows[row['id']] = row
    for row in rows.values():
        assert not row['missing'], (row['id'], row['missing'])
        for dep in row['resources']:
            native(dep)

    manifest = {'status': 'PREPARED_U10_PRESENTATION_NOT_INSTALLED', 'inputs': resources,
                'source_pins': pins, 'reference_replacements': mappings,
                'main_replacement': {PHASES[-1]: mappings[PHASES[-1]]},
                'removed_props': [5, 6], 'removed_events': removed_events, 'muted_events': muted_events,
                'johnny_instances': sorted(johnny_instances), 'workspot_changes': workspot_changes,
                'rows': list(rows.values()), 'native_overrides': [], 'boots': [],
                'limitations': ['Offline payload validation is not renderer/audio/gameplay proof.',
                                'Dan uses the original local hil_06_client_com community; no parallel B0 service is created.',
                                'Generic unfinished-job reconstruction is not provided by presentation adapters.']}
    write(out / 'prepared.json', manifest)
    print(json.dumps({'prepared': rel(out), 'resources': len(resources), 'removed_events': len(removed_events),
                      'muted_events': len(muted_events), 'workspots': len(workspot_changes)}))


if __name__ == '__main__':
    prepare(Path(sys.argv[1]).resolve())
