"""Compare emitted body graphs and the two quest families' ownership boundaries."""
from pin_inputs import HERE, BATCH, RD5, baseline, read, sha, write
from verify_batch import graph, load_export, normalize, reachable, value, walk, readonly


def typed_edges(edges):
    return {(a, b, 'Output', c, d, 'Input') for a, b, c, d in edges}


def load_source(pin):
    assert sha(pin['export_path']) == pin['export_sha256']
    return normalize(load_export(pin['export_path']))


def check_stage(spec, body, initial):
    assert initial['support'] == body['support']
    for old, new in zip(initial['graphs'], body['graphs'], strict=True):
        scope = old['path']
        assert new['path'] == scope
        if scope not in spec['graphs']:
            assert old == new, scope
            continue
        edit = spec['graphs'][scope]
        before, before_edges = graph(initial, scope)
        after, after_edges = graph(body, scope)
        assert all(after[k] == v for k, v in before.items())
        assert set(after)-set(before) == ({edit['input']} if 'input' in edit else set())
        if 'input' in edit:
            node = after[edit['input']]
            assert node['$type'] == 'questInputNodeDefinition' and value(node['socketName']) == spec['socket']
        removed = typed_edges(edit.get('remove_edges', []))
        assert removed <= set(before_edges)
        assert set(after_edges) == (set(before_edges)-removed) | typed_edges(edit['edges']), scope
    _, edges = graph(body, spec['stage_graph'])
    address = spec['graphs'][spec['stage_graph']]['input']
    active = reachable([address], [(a, b) for a, _, x, b, _, y in edges if x == 'Output' and y == 'Input'])
    assert set(spec['preserve']) <= active
    assert not set(spec['bypass']) & active
    scope, node, reward = spec['reward']
    nodes, _ = graph(body, scope)
    assert [value(x) for x in nodes[node]['type']['rewards']] == [reward]
    return sorted(active)


def fact_writers(source, scope):
    nodes, _ = graph(source, scope)
    return {row['factName'] for node in nodes.values() for row in walk(node)
            if row.get('$type') == 'questSetVar_NodeType'}


def main():
    installed = baseline()
    evidence = HERE/'evidence_02'
    specs = read(HERE/'entrances.json')['quests']
    pins = read(evidence/'inputs.json')
    assert sha(HERE/'entrances.json') == pins['plan_sha256']
    out = HERE/'graph_02'
    readback = read(out/'readback.json')
    assert readback['status'] == 'UNREGISTERED_BODY_READBACK'
    assert readback['pinned_providers'] == len(pins['resources'])
    resources = {p['rid']: load_source(p) for p in pins['resources']}
    source_pins = {p['rid']: p for p in pins['resources']}
    reports = {}
    states = {r['id']: r for r in read(BATCH/'evidence_01/batch_assessment.json')['stages']}
    for spec in specs:
        quest = spec['id']
        file = out/(quest+'_body.questphase')
        row = next(r for r in readback['bodies'] if r['id'] == quest)
        assert sha(file) == row['sha256'] and sha(str(file)+'.json') == row['export_sha256']
        body = normalize(load_export(str(file)+'.json'))
        reached = check_stage(spec, body, resources[spec['body']])
        guard = states[quest]['fixture_guard']
        root = guard['journals'][0]
        assert root['history'] == 2 and root['live'] == 4
        assert all(quest in f for f in guard['zero_receipts'])
        reports[quest] = {'body_sha256': row['sha256'], 'reachable_stage_nodes': reached,
                          'stage_guard': guard, 'claim_and_credit_receipts': guard['zero_receipts']}

    many, minefield = (reports[q['id']] for q in specs)
    assert set(many['claim_and_credit_receipts']).isdisjoint(minefield['claim_and_credit_receipts'])
    rd5_members = {r['depot']: r['sha256'] for r in read(RD5/'archive_01/readback.json')['members']}
    credits = {}
    with readonly('registry_02/registry.sqlite3') as db:
        for rid in (14677, 15667):
            row = dict(db.execute('SELECT * FROM resources WHERE rid=?', (rid,)).fetchone())
            assert rd5_members[row['depot']] == row['sha256']
            credits[row['depot']] = sorted(fact_writers(load_source(row), 'root'))
    many_credit, minefield_credit = map(set, credits.values())
    assert 'wat_sts_counter' in many_credit and 'bls_sts_counter' in minefield_credit
    assert many_credit.isdisjoint(minefield_credit)

    monitor, edges = graph(resources[14725], 'root')
    conditions = {row['factName']: row['value'] for row in walk(monitor[1300]) if 'factName' in row}
    assert conditions['nid_02_start'] == 0 and many['stage_guard']['facts']['nid_02_start'] == 1
    assert (1300, 'True', 'Output', 1301, 'In', 'Input') in edges
    assert (1301, 'Out', 'Output', 1302, 'In1', 'Input') in edges
    assert 'sts_wat_nid_02_fail' in fact_writers(resources[14725], 'root/1302')
    combat, _ = graph(resources[10705], 'root/2')
    spawn = [row for node in combat.values() for row in walk(node) if row.get('$type') == 'questCommunityTemplate_NodeType']
    assert len(spawn) == 11 and all(a['action'] == 'Activate' for a in spawn)
    assert {value(a['communityEntryPhaseName']) for a in spawn} == {'A'}
    chase, _ = graph(resources[8663], 'root/4/138')
    assert '/sts_pac_cvi_02/' in chase[92]['type']['path']['realPath']
    many['pending'] = {'failure_monitor_fresh_start_condition': conditions['nid_02_start'],
                      'encounter_phase_writes': len(spawn), 'foreign_journal_node': 92}

    parent, _ = graph(resources[15733], 'root')
    assert parent[264]['event']['accumulate'] == 1
    assert value(parent[254]['actions'][0]['type']['communityEntryPhaseName']) == 'spawn'
    scene, _ = graph(resources[14737], 'root/11')
    assert not {590, 591} & set(minefield['reachable_stage_nodes'])
    foreign = scene[591]['actions'][0]['type']
    assert foreign['action'] == 'Deactivate' and value(foreign['spawnerReference']) == '#ina_04_com_outpost_crew'
    minefield['pending'] = {'accumulating_damage_node': 264, 'car_community_phase': 'spawn',
                           'foreign_garage_cleanup': [590, 591]}
    write(evidence/'assessment.json', {
        'status': 'PASS_TWO_UNREGISTERED_BODY_GRAPHS', 'baseline_archive_sha256': installed['archive_sha256'],
        'graph_readback_sha256': sha(out/'readback.json'), 'routes': reports,
        'credit_writers': credits, 'native_support_resources': [source_pins[n]['depot'] for n in (6800, 10705, 4013, 3756, 6572)],
        'runtime_admission': 0, 'game_writes': 0, 'save_writes': 0,
    })
    print('Verified two serialized entrances, separate Watson and Badlands credit, and the remaining owner boundaries.')


if __name__ == '__main__':
    main()
