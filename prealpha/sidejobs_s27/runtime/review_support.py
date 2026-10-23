"""Independent S27 phone admission/cleanup review; never writes game state."""
import importlib.util
import itertools
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / 'prealpha/sidejobs_s22/delamain_v2/test.py'
spec = importlib.util.spec_from_file_location('s27_native_reader', MODEL)
lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)


def walk(value):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def evaluate(condition, facts):
    if condition['$type'] == 'questLogicalCondition':
        values = [evaluate(child, facts) for child in condition['conditions']]
        assert condition['operation'] in ('AND', 'OR')
        return all(values) if condition['operation'] == 'AND' else any(values)
    assert condition['$type'] == 'questFactsDBCondition'
    test = condition['type']
    if test['$type'] == 'questVarVsVarComparison_ConditionType':
        left, right = facts[test['factName1']], facts[test['factName2']]
    else:
        left, right = facts[test['factName']], test['value']
    return {'Equal': left == right, 'NotEqual': left != right,
            'Greater': left > right, 'GreaterOrEqual': left >= right,
            'Less': left < right, 'LessOrEqual': left <= right}[test['comparisonType']]


def main(revision, output_name):
    folder = ROOT / 'prealpha/sidejobs_s27/support/build' / revision
    output = ROOT / 'research/sidejobs_s27/runtime' / output_name
    assert not output.exists(), 'Immutable review receipt'
    manifest = lib.read(folder / 'component.json')
    checks = []
    def check(label, valid):
        assert valid, label
        checks.append(label)
    for path, digest in manifest['source_pins'].items():
        assert lib.sha(ROOT / path) == digest, path
    check('All source pins current', bool(manifest['source_pins']))
    runtime = lib.read(ROOT / 'prealpha/sidejobs_s27/runtime/build/runtime_04/manifest.json')
    contract_by_tag = {row['tag']: row for row in runtime['rows']}
    old = lib.graphs(ROOT / manifest['cleanup_witness'])
    native = lib.graphs(ROOT / (manifest['cleanup_source'].replace('/raw/', '/json/') + '.json'))
    actual = lib.graphs(folder / 'readback/fixer_cleanup.json')
    init = lib.nodes(lib.graphs(ROOT / (manifest['init_source'].replace('/raw/', '/json/') + '.json'))['root'])
    graph = actual['root']
    nodes, edges = lib.nodes(graph), lib.edges(graph)
    global_idle = {'holo_setup_active', 'holo_setup_started', 'holo_interrupt_call',
                   'holo_active_call_interrupted', 'holo_reset', 'holo_force_reset',
                   'holo_reset_soft', 'holo_interrupt_call_manual', 'holo_interrupt_braindance'}
    cases = 0
    for index, row in enumerate(manifest['contacts']):
        contact, tag = row['contact'], row['tag']
        original_init = init[contact['init']]
        controller = lib.nodes(lib.graphs(folder / ('readback/' + contact['name'] + '.json'))['root'])
        check(contact['name'] + ' exact original initializer payload', controller[contact['init']] == original_init)
        check(contact['name'] + ' exact one consumer', len(row['consumer_tags']) == 1)
        consumer = contract_by_tag[row['consumer_tags'][0]]
        check(contact['name'] + ' consumer identity', consumer['id'] == contact['job'])
        check(contact['name'] + ' runtime has no circular support fact',
              not any(f['name'].startswith('PTFRS27_PHONE_') for f in consumer['facts']))
        expected_idle = set(global_idle)
        for raw in contact['sources']:
            data = lib.read(ROOT / (raw.replace('/raw/', '/json/') + '.json'))
            expected_idle.update(value for value in walk(data) if isinstance(value, str) and
                                 re.fullmatch(r'(?:holo|audio)_[A-Za-z0-9_]+_(?:start_activate|end_activate|active|started)', value))
        check(contact['name'] + ' exact source-derived busy facts',
              row['idle'] == dict.fromkeys(expected_idle, 0))
        check(contact['name'] + ' repeated native preflight', controller[1002]['condition'] == controller[1003]['condition'])
        admission = controller[1002]['condition']
        check(contact['name'] + ' no history equality admission',
              all(not (isinstance(value, dict) and value.get('$type') == 'questVarVsVarComparison_ConditionType')
                  for value in walk(admission)))
        good = manifest['common'] | row['idle'] | {tag + '_Issued': 0,
               consumer['tag'] + '_Permit': 1, consumer['tag'] + '_Issued': 0, consumer['tag'] + '_Fault': 0}
        check(contact['name'] + ' valid admission', evaluate(admission, good))
        for fact, expected in good.items():
            for value in (-1, 0, 1, 2, 99):
                if value != expected:
                    assert not evaluate(admission, good | {fact: value}), (contact['name'], fact, value)
                    cases += 1
        cid, phase = 1000 + 2 * index, 1001 + 2 * index
        for source, target in ((contact['condition'], cid), (contact['cleanup'], phase)):
            payload = dict(lib.nodes(native['root'])[source]); payload['id'] = target
            check(contact['name'] + ' exact cleanup node ' + str(source), nodes[target] == payload)
        native_condition = nodes[cid]['condition']
        for start1, end1, start2, end2 in itertools.product((0, 1, 3, 7), repeat=4):
            historical = {f"holo_{contact['folder']}_calls_v_start_count": start1,
                          f"holo_{contact['folder']}_calls_v_end_count": end1,
                          f"holo_v_calls_{contact['folder']}_start_count": start2,
                          f"holo_v_calls_{contact['folder']}_end_count": end2}
            assert evaluate(native_condition, historical) == (start1 > end1 or start2 > end2)
            # Unequal historical counts never affect admission. They remain
            # inputs to the ORIGINAL cleanup, not a custom balance/reset path.
            assert evaluate(admission, good | historical)
            cases += 2
    for path, original in old.items():
        check('Original payloads preserved ' + path,
              all(lib.nodes(actual[path])[key] == value for key, value in lib.nodes(original).items()))
        if path != 'root':
            check('Original embedded edges preserved ' + path, lib.edges(actual[path]) == lib.edges(original))
    changed = lib.edges(old['root']) - edges
    check('Only three S24 cleanup exits redirected', changed == {
        (911, 'False', 6, 'In2'), (902, 'False', 6, 'In2'), (903, 'Out46', 6, 'In2')})
    check('No other old edges lost', len(changed) == 3)
    # Exercise every issued/native-cleanup decision combination through the
    # added tail; each contact runs at most once and always rejoins old output6.
    for issued0, needs0, issued1, needs1 in itertools.product((False, True), repeat=4):
        choices = {1010: issued0, 1000: needs0, 1011: issued1, 1002: needs1}
        current = 1010; visited = []
        while current != 6:
            assert current not in visited, 'Cleanup tail cycle'
            visited.append(current)
            if current in choices:
                port = 'True' if choices[current] else 'False'
            else:
                port = manifest['contacts'][0 if current == 1001 else 1]['contact']['output']
            outgoing = [edge for edge in edges if edge[:2] == (current, port)]
            assert len(outgoing) == 1
            current = outgoing[0][2]
        assert (1001 in visited) == (issued0 and needs0)
        assert (1003 in visited) == (issued1 and needs1)
        cases += 1
    check('Cleanup flow matrix reaches original output once', True)
    check('No extra cleanup-tail nodes', set(nodes) - set(lib.nodes(old['root'])) == {1000, 1001, 1002, 1003, 1010, 1011})
    check('No new custom native fact setters', all(node['$type'] != 'questFactsDBManagerNodeDefinition'
          for key, node in nodes.items() if key not in lib.nodes(old['root'])))
    proof = lib.read(folder / 'tests.json')
    check('Original support test is component-bound', proof['component_sha256'] == lib.sha(folder / 'component.json'))
    result = {'status': 'PASS_INDEPENDENT_SUPPORT_REVIEW_NOT_LIVE', 'checks': len(checks),
              'check_names': checks, 'cases': cases, 'component_sha256': lib.sha(folder / 'component.json'),
              'reviewer_sha256': lib.sha(Path(__file__)), 'graph_reader_sha256': lib.sha(MODEL),
              'runtime_manifest_sha256': lib.sha(ROOT / 'prealpha/sidejobs_s27/runtime/build/runtime_04/manifest.json'),
              'support_test_sha256': lib.sha(folder / 'tests.json'), 'game_writes': 0,
              'limits': 'Native payload/flow/admission proof only. Issued is not a live phone-call, SMS or save/reload result.'}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in result.items() if key != 'check_names'}))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
