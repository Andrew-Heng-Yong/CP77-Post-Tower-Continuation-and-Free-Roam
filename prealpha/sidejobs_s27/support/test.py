"""Check all native contact payloads and the single appended cleanup chain."""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('native_checks', ROOT / 'prealpha/sidejobs_s22/delamain_v2/test.py')
lib = importlib.util.module_from_spec(spec); spec.loader.exec_module(lib)
read, sha, graphs, nodes, edges, evaluate = lib.read, lib.sha, lib.graphs, lib.nodes, lib.edges, lib.evaluate


def main(build):
    out = build / 'tests.json'; assert not out.exists()
    m = read(build / 'component.json')
    for p, h in m['source_pins'].items():
        assert sha(ROOT / p) == h, p
    assert len(m['resources']) == 3 and len(m['boots']) == 2
    original = graphs(ROOT / (m['init_source'].replace('/raw/', '/json/') + '.json'))['root']
    on = nodes(original)
    count = cases = 0
    for row in m['contacts']:
        contact, tag = row['contact'], row['tag']
        g = graphs(build / ('readback/' + contact['name'] + '.json'))['root']
        actual = nodes(g); init = contact['init']
        assert actual[init] == on[init]; count += 1
        assert set(actual) == {init, 1000, 1001, 1002, 1003, 1004}
        assert edges(g) == {(1000, 'Out', 1001, 'In'), (1001, 'Out', 1002, 'In'),
                            (1002, 'Out', 1003, 'In'), (1003, 'False', 1002, 'In'),
                            (1003, 'True', 1004, 'In'), (1004, 'Out', init, 'In1')}
        condition = actual[1002]['condition']
        assert contact['name'] in ('MAMA', 'CLAIRE')
        for prefix in (f"holo_v_calls_{contact['folder']}", f"holo_{contact['folder']}_calls_v"):
            assert row['idle'][prefix + '_start_activate'] == 0
            assert row['idle'][prefix + '_end_activate'] == 0
        assert condition == actual[1003]['condition']
        assert 'questVarVsVarComparison' not in json.dumps(condition), 'No historical equality admission'
        consumer = row['consumer_tags'][0]
        facts = m['common'] | row['idle'] | {tag + '_Issued': 0, consumer + '_Permit': 1,
                                           consumer + '_Issued': 0, consumer + '_Fault': 0}
        assert evaluate(condition, facts, {}); cases += 1
        for name, wanted in facts.items():
            for wrong in [-1, 0, 1, 2, 99]:
                if wrong == wanted:
                    continue
                assert not evaluate(condition, facts | {name: wrong}, {}), (contact['name'], name, wrong)
                cases += 1
        writes = [n['type']['factName'] for n in actual.values() if n['$type'] == 'questFactsDBManagerNodeDefinition']
        assert set(writes) == {tag + '_Ready', tag + '_Issued'}
    old = graphs(ROOT / m['cleanup_witness'])
    native = graphs(ROOT / (m['cleanup_source'].replace('/raw/', '/json/') + '.json'))
    new = graphs(build / 'readback/fixer_cleanup.json')
    for path, graph in old.items():
        for key, payload in nodes(graph).items():
            assert nodes(new[path])[key] == payload, (path, key)
            count += 1
        if path != 'root':
            assert edges(new[path]) == edges(graph), path
    tail = {(911, 'False', 6, 'In2'), (902, 'False', 6, 'In2'), (903, 'Out46', 6, 'In2')}
    assert tail <= edges(old['root'])
    expected = edges(old['root']) - tail
    expected |= {(a, b, 1010, 'In') for a, b, _, _ in tail}
    for i, row in enumerate(m['contacts']):
        c = row['contact']; cid, pid = 1000 + 2*i, 1001 + 2*i
        for source, target in [(c['condition'], cid), (c['cleanup'], pid)]:
            expected_node = dict(nodes(native['root'])[source]); expected_node['id'] = target
            assert nodes(new['root'])[target] == expected_node
            count += 1
        gate = 1010 + i
        gate_condition = nodes(new['root'])[gate]['condition']
        for issued in [-1, 0, 1, 2, 99]:
            assert evaluate(gate_condition, {row['tag'] + '_Issued': issued}, {}) == (issued == 1)
            cases += 1
        nxt = gate + 1 if i < 1 else 6
        inp = 'In' if i < 1 else 'In2'
        expected |= {(cid, 'True', pid, c['input']), (cid, 'False', nxt, inp), (pid, c['output'], nxt, inp)}
        expected |= {(gate, 'True', cid, 'In'), (gate, 'False', nxt, inp)}
    assert edges(new['root']) == expected
    assert set(nodes(new['root'])) == set(nodes(old['root'])) | set(range(1000, 1004)) | {1010, 1011}
    assert m['native_counter_writes'] == m['global_owner_restarts'] == m['history_equalities'] == 0
    for depot, h in m['resources'].items():
        assert sha(build / 'source' / depot) == h
    result = {'status': 'PASS_NOT_LIVE', 'component_sha256': sha(build / 'component.json'),
              'tester_sha256': sha(Path(__file__)), 'native_payload_checks': count,
              'policy_cases': cases, 'contact_count': 2, 'original_cleanup_preserved': True,
              'no_history_equality_admission': True}
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main(Path(sys.argv[1]))
