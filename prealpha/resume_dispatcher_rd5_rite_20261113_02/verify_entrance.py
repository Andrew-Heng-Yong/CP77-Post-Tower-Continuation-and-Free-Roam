"""Independently compare serialized entrance resources with the approved stock inputs."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BATCH = HERE.parent / 'resume_dispatcher_rd5_gigs_20261113_01'
sys.path.insert(0, str(BATCH))
from verify_batch import baseline, graph, load_export, normalize, read, reachable, sha, value, write


def emitted_edges(spec):
    return {(a, name, 'Output', b, socket, 'Input') for a, name, b, socket in spec.get('edges', [])}


def check_body(name, spec, original, current, plan):
    assert original['support'] == current['support'], name
    assert [g['path'] for g in original['graphs']] == [g['path'] for g in current['graphs']]
    for source, emitted in zip(original['graphs'], current['graphs'], strict=True):
        path = source['path']
        edit = spec['graphs'].get(path)
        if not edit:
            assert source == emitted, (name, path)
            continue
        old, old_edges = graph(original, path)
        new, new_edges = graph(current, path)
        assert set(new_edges) == set(old_edges) | emitted_edges(edit), (name, path)
        extras = {edit['entry'], *(dest for _, dest in edit.get('clones', []))}
        if 'exit' in edit:
            extras.add(edit['exit'][0])
            assert new[edit['exit'][0]]['type'] == 'Terminating'
            assert value(new[edit['exit'][0]]['socketName']) == edit['exit'][1]
        assert new.keys() - old.keys() == extras
        assert new[edit['entry']]['$type'] == 'questInputNodeDefinition'
        assert value(new[edit['entry']]['socketName']) == plan['socket']
        for source_id, new_id in edit.get('clones', []):
            assert new[new_id] == old[source_id] | {'id': new_id}
        redirected = dict(edit.get('calls', []))
        for i, old_params in old.items():
            assert i in new
            if i in redirected:
                assert value(new[i]['phaseResource']['DepotPath']) == plan['private_prefix'] + redirected[i] + '.questphase'
                assert new[i]['phaseResource']['Flags'] == old_params['phaseResource']['Flags']
                assert new[i] | {'phaseResource': old_params['phaseResource']} == old_params
            else:
                assert new[i] == old_params, (name, path, i)


def from_socket(src, scope, entry):
    _, edges = graph(src, scope)
    return reachable([entry], [(a, b) for a, _, x, b, _, y in edges if x == 'Output' and y == 'Input'])


def main():
    baseline()
    build = HERE / 'graph_01'
    plan = read(HERE / 'entrance.json')
    review = read(BATCH / 'evidence_02/rite_route.json')
    pin = {row['rid']: row for row in review['providers']}
    source = {}
    for row in read(build / 'readback.json')['resources']:
        name = row['name']
        spec = plan['resources'][name]
        p = pin[spec['rid']]
        assert sha(p['export_path']) == p['export_sha256']
        assert sha(build / f'{name}.stock.questphase') == p['sha256'] == row['original_sha256']
        assert sha(build / f'{name}.questphase') == row['raw_sha256']
        source[name] = normalize(load_export(build / f'{name}.questphase.json'))
        check_body(name, spec, normalize(load_export(p['export_path'])), source[name], plan)
    assert source.keys() == plan['resources'].keys()
    assert from_socket(source['streetstory'], 'root', 1000) == {1000, 3, 5, 1}
    reachable_stage = from_socket(source['streetstory'], 'root/3', 1000)
    assert not reachable_stage & {74, 105, 130, 134, 135, 136, 137, 146}
    assert {42, 43, 69, 73, 77, 102, 145, 1} <= reachable_stage
    combat = source['combat']
    assert from_socket(combat, 'root/2', 1000) == {1000, 1001, 1002, 1003}
    n, _ = graph(combat, 'root/2')
    assert n[1001]['actions'][0]['type']['action'] == 'Activate'
    assert value(n[1001]['actions'][0]['type']['spawnerReference']) == '#nid_05_com'
    assert 17 not in from_socket(combat, 'root/3', 1000)
    assert {6, 7, 11} <= from_socket(combat, 'root/2', 0)
    assert 17 in from_socket(combat, 'root/3', 0)
    assert 2 in from_socket(source['streetstory'], 'root', 0)
    assert {74, 105, 130} <= from_socket(source['streetstory'], 'root/3', 0)
    keycard = read(HERE / 'evidence_01/keycard.json')
    assert all(r['matching_items'] == [{'structure': 'None', 'inventory': '1', 'flags': '0', 'quantity': 1}]
               for r in keycard['saves'])
    world = read(HERE / 'evidence_01/world.json')
    assert len(world['providers']) == 1
    sector = world['providers'][0]
    assert sha(sector['raw']) == sector['sha256']
    data = read(sector['export'])['Data']['RootChunk']
    assert data['nodes'][31]['Data']['$type'] == 'worldTriggerAreaNode'
    assert value(data['nodeData']['Data'][31]['QuestPrefabRefHash']).endswith('/#sts_wat_nid_05_steetstory/#nid_05_tr_escape_001')
    guards = [data['nodes'][i]['Data']['communityEntries'][0] for i in (41, 42)]
    assert all(value(g['communityArea']['reference']) == '#nid_05_com' for g in guards)
    write(HERE / 'evidence_01/entrance_assessment.json', {
        'status': 'PASS_PRIVATE_PHASE_READBACK', 'entrance_sha256': sha(HERE / 'entrance.json'),
        'readback_sha256': sha(build / 'readback.json'), 'three_retained_keycards': True,
        'world_sector_sha256': sector['sha256'], 'checked_graphs': sum(len(s['graphs']) for s in source.values()),
        'limits': 'Unregistered private phase bodies. Engine streaming, device state, gameplay and reload are pending.',
    })
    print('Verified the private phase readback, retained keycards and native clinic sector binding.')


if __name__ == '__main__':
    main()
