"""Independently compare native and post-Tower paths after serialization."""

from collections import Counter, defaultdict
from hashlib import file_digest
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'johnny_dialogue_index_20261107_02'))
from common import scalar, walk
from graphs import PhaseSource


ARCHIVE = 'archive/pc/mod/zzzz_PTFR_Combined.archive'
PLAN = HERE / 'authored_03/plan.json'
READBACK = HERE / 'readback_02/manifest.json'
WELLSPRINGS = r'towercontinued\johnny_world\wellsprings_exposition.scene'
DAM = r'towercontinued\johnny_world\courier_dam.scene'
SCENE_ALIAS = {
    'ma_hey_spr_04_phase.questphase': {65000: (162, WELLSPRINGS), 65001: (207, WELLSPRINGS)},
    'sa_ep1_courier_outro_intro_scene.questphase': {65000: (6, DAM), 65001: (126, DAM)},
}
GUARDS = {
    'ma_bls_ina_se1_40_phase.questphase': ('root', {
        65000: [(112, 'Inactive')], 65001: [(72, 'In'), (112, 'Inactive')],
    }),
    'ma_bls_ina_se1_44_phase.questphase': ('root', {
        65000: [(92, 'Inactive')], 65001: [(48, 'In'), (92, 'Inactive')],
    }),
    'ma_wat_lch_06_phase.questphase': ('root/74', {65000: []}),
    'ma_wat_nid_03.questphase': ('root/81', {65000: []}),
    'ma_hey_spr_04_phase.questphase': ('root', {
        65002: [(65000, 'spawn_johnny_in')], 65003: [(65000, 'lookats_in')],
        65004: [(65001, 'knockback')],
    }),
    'sa_ep1_courier_outro_intro_scene.questphase': ('root', {
        65002: [(65000, 'Start 0')], 65003: [(65001, 'talk_interaction')],
    }),
}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    with Path(path).open('rb') as stream:
        return file_digest(stream, 'sha256').hexdigest().upper()


def graph_map(doc):
    return {graph['path']: graph for graph in PhaseSource(doc).graphs}


def boundary_edges(graph):
    def endpoint(data):
        return data['status'], tuple((o['graph'], o['node'], o['name'], o['type'])
                                     for o in data['owners'])
    return Counter((endpoint(edge['source']), endpoint(edge['destination']))
                   for edge in graph['connections'] if edge['classification'] != 'LOCAL_EDGE')


def node_payloads(graph):
    return {node: row['payload'] for node, row in graph['nodes'].items()}


def verify_roundtrip(authored, actual):
    expected = graph_map(authored)
    cooked = graph_map(actual)
    assert expected.keys() == cooked.keys()
    for path, before in expected.items():
        after = cooked[path]
        assert before['entries'] == after['entries'], path
        assert node_payloads(before) == node_payloads(after), path
        assert Counter(before['edges']) == Counter(after['edges']), path
        assert boundary_edges(before) == boundary_edges(after), path
    authored_source, actual_source = PhaseSource(authored), PhaseSource(actual)
    before_root = authored_source.clean(authored['Data']['RootChunk'])
    after_root = actual_source.clean(actual['Data']['RootChunk'])
    assert before_root == after_root
    return cooked


def verify_phase(filename, original, cooked):
    old_graphs = graph_map(original)
    assert cooked.keys() == old_graphs.keys()
    gate_path, true_outputs = GUARDS[filename]
    clones = SCENE_ALIAS.get(filename, {})
    for path, old in old_graphs.items():
        new = cooked[path]
        nodes = node_payloads(new)
        old_nodes = node_payloads(old)
        assert {node: nodes[node] for node in old_nodes} == old_nodes
        assert new['entries'] == old['entries'] and boundary_edges(new) == boundary_edges(old), path
        gates = true_outputs if path == gate_path else {}
        aliases = clones if path == gate_path else {}
        assert set(nodes) - set(old_nodes) == set(map(str, {*gates, *aliases})), path
        for clone_id, (original_id, alias) in aliases.items():
            clone = nodes[str(clone_id)]
            native = old_nodes[str(original_id)]
            assert {k: v for k, v in clone.items() if k not in ('id', 'sceneFile')} == {
                k: v for k, v in native.items() if k not in ('id', 'sceneFile')}
            assert scalar(clone['sceneFile']['DepotPath']) == alias
        edges = new['edges']
        vanilla = [(a, out, b, inp) for a, out, b, inp in edges if a in old_nodes and b in old_nodes]
        for gate_id, targets in gates.items():
            gate = str(gate_id)
            condition = nodes[gate]['condition']['type']
            assert condition == {
                '$type': 'questVarComparison_ConditionType', 'comparisonType': 'Equal',
                'factName': 'PostTowerFreeRoamActive', 'value': 1,
            }, (filename, gate, condition)
            (caller, port), = [(a, out) for a, out, b, inp in edges if b == gate and inp == 'In']
            (stock, native_input), = [(b, inp) for a, out, b, inp in edges if a == gate and out == 'False']
            vanilla.append((caller, port, stock, native_input))
            assert [(b, inp) for a, out, b, inp in edges if a == gate and out == 'True'] == [
                (str(node), port) for node, port in targets], (filename, gate)
        assert Counter(vanilla) == Counter(old['edges']), (filename, path)
    if filename == 'sa_ep1_courier_outro_intro_scene.questphase':
        assert Counter(e for e in cooked['root']['edges'] if e[0] in ('65000', '65001')) == Counter([
            ('65000', 'mummar_alldone', '65001', 'talk_interaction'),
            ('65000', 'mummar_alldone', '149', 'In'),
            ('65000', 'mummar_alldone', '174', 'In'),
            ('65000', 'police car leaves', '19', 'In'),
        ])


def scene_reachable(graph, seed):
    adjacent = defaultdict(list)
    for caller, _, dest, port in graph['edges']:
        name, index = map(int, port.split(':'))
        target = graph['nodes'][dest]['payload']
        maps = target.get('isockMappings', [])
        if name == 1026 or (index < len(maps) and scalar(maps[index]) == 'CutDestination'):
            continue
        if target['$type'] in ('scnChoiceNode', 'scnSectionNode') and port != '0:0':
            continue
        adjacent[caller].append(dest)
    seen = {seed}
    todo = [seed]
    while todo:
        for dest in adjacent[todo.pop()]:
            if dest not in seen:
                seen.add(dest)
                todo.append(dest)
    return seen


def speech(graph):
    return {event['id']['id']: (node, event) for node, row in graph['nodes'].items()
            for event in row['payload'].get('events', []) if event['$type'] == 'scnDialogLineEvent'}


def verify_scene(original, actual, old_graph, new_graph, row):
    before, after = speech(old_graph), speech(new_graph)
    edits = row['changes']
    expected_removed = {e['id'] for e in edits['events_removed'] if e['kind'] == 'scnDialogLineEvent'}
    assert set(map(str, before.keys() - after.keys())) == expected_removed
    assert after == {event_id: data for event_id, data in before.items()
                     if str(event_id) not in expected_removed}
    assert old_graph['entries'] == new_graph['entries']
    assert original['Data']['RootChunk']['exitPoints'] == actual['Data']['RootChunk']['exitPoints']
    for node, payload in node_payloads(old_graph).items():
        if payload['$type'] == 'scnChoiceNode':
            assert payload['options'] == node_payloads(new_graph)[node]['options'], node

    root = PhaseSource(actual).clean(actual['Data']['RootChunk'])
    actor, = [a for a in root['actors'] if a['actorName'].casefold() == 'johnny']
    for key in ('alwaysSpawned', 'spawnOnStart', 'isEnabled'):
        assert actor['spawnDespawnParams'][key] == 0, key
    dynamic_name = scalar(actor['spawnDespawnParams']['dynamicEntityUniqueName'])
    for entry, start in new_graph['entries']:
        original_reachable = scene_reachable(old_graph, start)
        reachable = scene_reachable(new_graph, start)
        for kind in ('scnChoiceNode', 'scnEndNode'):
            original_endpoints = {n for n in original_reachable
                                  if old_graph['nodes'][n]['payload']['$type'] == kind}
            endpoints = {n for n in reachable if new_graph['nodes'][n]['payload']['$type'] == kind}
            assert endpoints == original_endpoints, (row['depot'], entry, kind,
                                                       original_endpoints - endpoints,
                                                       endpoints - original_endpoints)
        for node in reachable:
            payload = new_graph['nodes'][node]['payload'].get('questNode', {})
            assert not any(obj.get('$type') == 'gameEntityReference'
                           and scalar(obj.get('dynamicEntityUniqueName')) == dynamic_name
                           for _, obj in walk(payload)), (row['depot'], entry, node)
    if row['depot'] == WELLSPRINGS:
        assert ('1', '0:0', '50', '0:0') in new_graph['edges']
        assert not any(e[2] in ('6', '36') for e in new_graph['edges'] if e[0] in ('1', '34'))
    if row['depot'] == DAM:
        assert {'128', '151', '585'} == {str(e['node']) for e in edits['events_removed']
                                         if e['kind'] == 'scnDialogLineEvent'}
        assert len(expected_removed) == 5
        assert not any(e[2] == '585' for e in new_graph['edges'])
        assert ('203', '0:0', '1129', '0:0') in new_graph['edges']
    if row['depot'].endswith(r'\yoko.scene'):
        assert len(expected_removed) == 3
        assert ('584', '0:0', '526', '0:0') in new_graph['edges']
        assert ('584', '0:0', '764', '0:1') in new_graph['edges']
        assert ('526', '3:0', '698', '0:0') in new_graph['edges']
        assert ('526', '3:0', '706', '0:0') in new_graph['edges']
    return len(expected_removed)


def main():
    plan, proof = read(PLAN), read(READBACK)
    assert proof['plan_sha256'] == sha(PLAN) and proof['status'] == 'PACKED_AND_READ_BACK'
    rows = {r['depot']: r for r in proof['resources']}
    assert rows.keys() == {r['depot'] for r in plan['edits']}
    report = []
    for row in plan['edits']:
        depot = row['depot']
        pin = rows[depot]
        assert sha(pin['json']) == pin['json_sha256']
        assert sha(row['json']) == row['json_sha256']
        original, authored, actual = map(read, (row['source']['json'], row['json'], pin['json']))
        graphs = verify_roundtrip(authored, actual)
        if 'scene' in graphs:
            cut = verify_scene(original, actual, graph_map(original)['scene'], graphs['scene'], row)
        else:
            verify_phase(depot.split('\\')[-1], original, graphs)
            cut = 0
        report.append({'depot': depot, 'sha256': pin['sha256'], 'speech_events_removed': cut})

    candidate = Path(plan['candidate'])
    current = {path.relative_to(candidate / 'package').as_posix(): sha(path)
               for path in (candidate / 'package').rglob('*') if path.is_file()}
    assert len(current) == len(plan['files']) == 51 and current.keys() == plan['files'].keys()
    assert {path for path in current if current[path] != plan['files'][path]} == {ARCHIVE}
    assert current[ARCHIVE] == proof['archive_sha256']
    before, after = plan['base_members'], proof['source_resources']
    assert len(before) == 1729 and len(after) == 1737
    assert before.keys() <= after.keys()
    assert {depot for depot in after if before.get(depot) != after[depot]} == rows.keys()
    result = {
        'status': 'VERIFIED_STATIC_CANDIDATE',
        'baseline': plan['baseline'], 'candidate': str(candidate),
        'archive_sha256': current[ARCHIVE], 'archive_members': len(after),
        'changed_package_files': [ARCHIVE], 'files': current,
        'resources': report, 'provider_keys': proof['provider_keys'],
        'installed_archives_scanned': proof['installed_archives'],
        'archive_xl_configs_scanned': proof['archive_xl_configs'],
        'gameplay': 'UNVERIFIED', 'game_writes': 0, 'save_writes': 0,
    }
    with (HERE / 'verification.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(f"Verified {len(report)} resources, {len(after)} archive members and {len(current)} Core files.")


if __name__ == '__main__':
    main()
