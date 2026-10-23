"""Native payload, cooked embedded helper and fail-closed admission regression."""
import copy
import json
import sys
from pathlib import Path
from prepare import ROOT, read, sha, graphs, value, walk


def nodes(g):
    return {n['id']: n for n in g['nodes']}


def evaluate(c, facts, journals):
    kind = c['$type']
    if kind == 'questLogicalCondition':
        answers = [evaluate(x, facts, journals) for x in c['conditions']]
        return {'AND': all(answers), 'OR': any(answers), 'NOR': not any(answers)}[c['operation']]
    if kind == 'questFactsDBCondition':
        t = c['type']
        a = facts.get(t['factName'])
        if a is None:
            return False
        b = t['value']
        return {'Equal': a == b, 'GreaterOrEqual': a >= b, 'LessOrEqual': a <= b}[t['comparisonType']]
    if kind == 'questJournalCondition':
        t = c['type']
        p = t['path']
        return journals.get((p['realPath'], value(p['className']))) == t['state']
    raise AssertionError(kind)


def main():
    build = Path(sys.argv[1])
    m = read(build / 'component.json')
    spec = read(ROOT / m['contract'])
    o = spec['owners'][0]
    checks = cases = 0
    for p, h in m['source_pins'].items():
        assert sha(ROOT / p) == h, p
        checks += 1
    for r in m['resource_details']:
        assert sha(build / r['relative']) == r['sha256']
        assert sha(build / r['readback']) == r['readback_sha256']
        checks += 2
    gg = graphs(build / 'readback/sq024_fresh.json')
    assert set(gg) == {'root'}
    g = gg['root']
    nn = nodes(g)
    for c in m['native_copies']:
        original = nodes(graphs(ROOT / (c['source'].replace('/raw/', '/json/') + '.json'))[c['source_graph']])[c['source_id']]
        expected = copy.deepcopy(original)
        expected['id'] = c['target_id']
        assert nn[c['target_id']] == expected, c
        checks += 1
    expected_edges = {(0, 'Out', 1, 'In'), (1, 'Out', 2, 'In'), (2, 'Out', 3, 'In'),
                      (3, 'False', 2, 'In'), (3, 'True', 4, 'In'), (4, 'Out', 89, 'In'),
                      (89, 'Out', 90, 'In'), (90, 'False', 91, 'In'), (90, 'True', 92, 'In'),
                      (92, 'Out', 93, 'In'), (93, 'Out', 100, 'sq024_in'), (100, 'sq024_out', 101, 'In')}
    assert set(map(tuple, g['edges'])) == expected_edges
    assert nn[89]['condition']['type']['tickCount'] == 2
    assert value(nn[100]['phaseResource']['DepotPath']) == o['native_depot']
    assert nn[93]['type']['params'][0]['contact']['realPath'] == 'contacts/marianne'
    assert nn[93]['type']['params'][0]['addContact'] == 1
    assert nn[93]['type']['params'][0]['sendNotification'] == 1
    checks += 6
    for n in g['nodes']:
        assert n['$type'] != 'questJournalNodeDefinition'
        if n['$type'] == 'questFactsDBManagerNodeDefinition':
            assert n['type']['factName'].startswith(o['tag'] + '_')
            assert n['type']['value'] == 1 and n['type']['setExactValue'] == 1
        checks += 1
    facts = spec['common_equal'] | o['facts_equal'] | {k: v['min'] for k, v in o['fact_ranges'].items()}
    facts |= {o['tag'] + '_Permit': 1, o['tag'] + '_Issued': 0, o['tag'] + '_Fault': 0,
              o['tag'] + '_Finished': 0, spec['phone']['support_fact']: 1}
    journals = {(j['path'], j['class']): 'Inactive' for j in o['journals']}
    roots = [j for j in o['journals'] if j['class'] == 'gameJournalQuest']
    assert len(roots) == 5 and len(o['ids']) == 5 and o['id'] == '07_nc_underground'
    assert spec['phone']['support_fact'] not in o['facts_equal'], 'Circular runtime Permit'
    checks += 2
    for ident in (2, 3, 90):
        f = facts | {o['tag'] + '_Issued': int(ident == 90)}
        condition = nn[ident]['condition']
        assert evaluate(condition, f, journals)
        cases += 1
        for name, num in f.items():
            if ident == 90 and name.endswith('_Permit'):
                continue
            bounds = o['fact_ranges'].get(name)
            bad = [bounds['min'] - 1, bounds['max'] + 1] if bounds else [num - 1, num + 1]
            for changed in bad:
                assert not evaluate(condition, f | {name: changed}, journals), (ident, name, changed)
                cases += 1
            absent = f.copy()
            del absent[name]
            assert not evaluate(condition, absent, journals), (ident, name)
            cases += 1
        for key in journals:
            for state in ('Active', 'Succeeded', 'Failed', None):
                assert not evaluate(condition, f, journals | {key: state}), (ident, key, state)
                cases += 1
        for name in o['fact_ranges']:
            assert evaluate(condition, f | {name: 1}, journals)
            cases += 1
        historic = {f'holo_{direction}_{suffix}': value for direction in ('claire_calls_v', 'v_calls_claire')
                    for suffix, value in (('start_count', 7), ('end_count', 2), ('start_done', 3), ('end_done', 1))}
        assert evaluate(condition, f | historic, journals), 'Historical phone counts must not gate startup'
        cases += 1
    # Exact embedded native implementation resolves the old false dependency.
    native = graphs(ROOT / o['native_source'])
    helper = native['root/53/55']
    hn = nodes(helper)
    assert len(hn) == 20 and len(helper['edges']) == 28
    assert (0, 'Out', 55, 'make_hackable_in') in set(map(tuple, native['root/53']['edges']))
    assert value(hn[27]['socketName']) == 'make_hackable_in'
    assert value(hn[29]['socketName']) == 'un_hackable_in'
    assert all(hn[i]['type']['val'] == 1 for i in range(34, 40))
    assert all(hn[i]['type']['val'] == 0 for i in range(41, 47))
    assert nn[100]['$type'] == 'questPhaseNodeDefinition' and not m['override_donors']
    checks += 7
    # Stock beginning retains earned unlock, content token and offsite wait.
    opening = nodes(native['root/92'])
    assert opening[6]['condition']['type']['factName'] == 'q105_done'
    assert opening[6]['condition']['type']['comparisonType'] == 'Greater'
    assert opening[6]['condition']['type']['value'] == 0
    assert opening[7]['condition']['operation'] == 'AND'
    checks += 4
    parent = graphs(ROOT / 'research/sidejobs_s27/heroes/native_04/json/base/quest/side_quests/sidequests.questphase.json')['root']
    pn = nodes(parent)
    assert (31, 'Out', 50, 'sq024_in') in set(map(tuple, parent['edges']))
    assert pn[31]['condition']['type'] == {'$type': 'questVarComparison_ConditionType', 'comparisonType': 'Greater', 'factName': 'q101_enable_side_content', 'value': 0}
    assert o['fact_ranges']['q101_enable_side_content'] == {'min': 1, 'max': 2147483647}
    normal_phase = copy.deepcopy(pn[50]); normal_phase['id'] = 100
    assert normal_phase == nn[100], 'Normal-parent phase payload differs'
    checks += 4
    # Native service ordering: Reactivate quest-role before default_on=0.
    garage_depot = 'base\\quest\\side_quests\\sq024\\phases\\sq024_01_garage.questphase'
    garage_graphs = graphs(ROOT / m['native_resources'][garage_depot]['json'])
    garage = nodes(garage_graphs['root/54'])
    assert garage[96]['$type'] == 'questSpawnManagerNodeDefinition'
    assert garage[111]['type']['factName'] == 'claire_default_on' and garage[111]['type']['value'] == 0
    assert (96, 'Out', 111, 'In') in set(map(tuple, garage_graphs['root/54']['edges']))
    checks += 3
    for depot, row in m['native_resources'].items():
        assert sha(ROOT / row['raw']) == row['raw_sha256']
        assert sha(ROOT / row['json']) == row['json_sha256']
        checks += 2
    # All current captured progressed/completed states are negative controls.
    capture = read(ROOT / 'research/sidejobs_s23/live_20261016_01/capture.json')['second']['jobs']
    ff, jj = facts.copy(), journals.copy()
    for row in capture:
        if row['id'] in o['ids']:
            ff.update(row['facts'])
            jj.update({(j['path'], j['class']): j['state'] for j in row['journals']})
    assert not evaluate(nn[3]['condition'], ff, jj)
    cases += 1
    result = {'status': 'PASS_COMPONENT_NOT_LIVE', 'component_sha256': sha(build / 'component.json'),
              'contract_sha256': sha(ROOT / m['contract']), 'tester_sha256': sha(Path(__file__)),
              'native_payload_checks': checks, 'policy_cases': cases, 'owners': 1, 'roots': 5,
              'resources': 1, 'official_overrides': 0, 'native_progress_resets': False,
              'direct_new_journal_writes': 0, 'game_writes': False,
              'limits': ['Fresh family only; no unfinished replay implementation', 'Engine phase-resource precedence not independently proven',
                         'Original stock bytes and embedded helper retained unchanged, not an external-helper replacement',
                         'Live story calls/races/rewards/Johnny/service handoff/reload remain pending']}
    out = build / 'tests.json'
    assert not out.exists()
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
