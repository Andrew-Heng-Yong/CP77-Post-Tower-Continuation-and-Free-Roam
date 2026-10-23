"""Bind component proofs, inspect packed graphs, and report honest coverage."""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'runtime'))
import generate
spec = importlib.util.spec_from_file_location('native_checks', ROOT / 'prealpha/sidejobs_s22/delamain_v2/test.py')
lib = importlib.util.module_from_spec(spec); spec.loader.exec_module(lib)
read, sha, graphs = lib.read, lib.sha, lib.graphs


def main(revision):
    build = HERE / 'build' / revision
    output = build / 'tests.json'; assert not output.exists()
    m = read(build / 'build.json')
    assert m['status'] == 'BUILT_S23_LIVE_PENDING' and m['packed_readback']
    assert len(m['files']) == 3 and not any('old_sha256' in f for f in m['files'])
    assert m['official_overrides'] == []
    assert set(m['mod_overrides']) == {'towercontinued\\gig_phone_u9\\fixer_cleanup.questphase', 'towercontinued\\b0_wilson_vendor\\owner.questphase'}
    for p, h in m['source_pins'].items():
        assert sha(ROOT / p) == h, p
    for row in m['files']:
        assert sha(build / Path(row['relative']).name) == row['sha256']
    for depot, h in m['resources'].items():
        assert sha(build / 'source' / depot) == h
        assert depot.startswith('towercontinued\\')
    assert len(m['injections']) == len(m['boots']) == len(set(m['boots']))
    assert len({v['id'] for v in m['injections']}) == len(m['injections'])
    assert all(v['depot'] in m['resources'] for v in m['injections'])
    assert m['installed_xl_pins']
    for path, h in m['installed_xl_pins'].items():
        assert sha(Path(path)) == h, path
    for old in m['installed_injections']:
        witnesses = [h for p, h in m['installed_xl_pins'].items() if Path(p).name == old['source']]
        assert witnesses == [old['source_sha256']]
    native = cases = 0; proofs = []; owner_specs = []
    for c in m['components']:
        cm, test = read(ROOT / c['manifest']), read(ROOT / c['tests'])
        assert test['status'].startswith('PASS')
        assert test.get('component_sha256', test.get('build_sha256')) == sha(ROOT / c['manifest'])
        assert test['tester_sha256'] in m['source_pins'].values()
        native += test['native_payload_checks']; cases += test['policy_cases']
        for depot, h in cm['resources'].items():
            assert m['resources'][depot] == h
            original = ROOT / c['root'] / 'source' / depot
            assert sha(original) == h
            # Aggregate graph readback is normalized independently from each
            # component's raw payload; byte-equality already binds both files.
            g = graphs(build / ('readback/' + depot.replace('\\', '_') + '.json'))
            assert g and 'root' in g
            for path, graph in g.items():
                ids = {n['id'] for n in graph['nodes']}
                assert len(ids) == len(graph['nodes']), (depot, path)
                for e in graph['edges']:
                    assert e[0] in ids and e[2] in ids, (depot, path, e)
        contract = cm.get('contract')
        if contract:
            data = read(ROOT / contract)
            owner_specs += data.get('owners', data.get('contracts', [data]))
        proofs.append({'manifest': c['manifest'], 'tests': c['tests'], 'sha256': sha(ROOT / c['tests'])})
    rt = ROOT / m['runtime']; rm, rp = read(rt / 'manifest.json'), read(rt / 'tests.json')
    assert rp['status'] == 'PASS_OFFLINE_NOT_LIVE'
    assert rp['manifest_sha256'] == sha(rt / 'manifest.json')
    assert rp['test_sha256'] == sha(HERE / 'runtime/test.py')
    assert sha(build / 'SideJobsS23.reds') == rm['files']['SideJobsS23.reds']
    assert (build / 'SideJobsS23.reds').read_text(encoding='utf-8') == generate.template().replace('// GENERATED_DATA', generate.data_source(rm['rows']))
    assert len({row['tag'] for row in rm['rows']}) == len(rm['rows'])
    assert all(set(row['journals'][0]['states']) <= {1, 4} for row in rm['rows'])
    assert {s['tag'] for s in owner_specs} == {r['tag'] for r in rm['rows']}
    cases += rp['policy_cases']
    capture = read(ROOT / 'research/sidejobs_s23/live_20261016_01/capture.json')
    assert capture['repeatedReadMatched'] and capture['first']['settledBefore'] and capture['first']['settledAfter']
    jobs = capture['second']['jobs']
    assert len(jobs) == 58
    owned = {}
    for spec in owner_specs:
        for id in spec.get('ids', [spec['id']]):
            if id in owned:
                # One explicit, opt-in continuation alongside the unchanged
                # fresh Skippy owner. Never permit arbitrary overlapping owners.
                tags = {owned[id], spec['tag']}
                assert id == 'mq007_smartgun' and tags == {'PTFRS23_MQ007', 'PTFRS23_MQ007_RESUME'}
                variants = [r for r in rm['rows'] if r['id'] == id]
                assert len(variants) == 2
                left, right = [{f['name']: f for f in r['facts']} for r in variants]
                disjoint = [n for n in left.keys() & right.keys() if not n.startswith('PTFR') and
                            (left[n]['max'] < right[n]['min'] or right[n]['max'] < left[n]['min'])]
                assert disjoint, 'Fresh and progressed Skippy must have disjoint native progress'
                resume = next(r for r in variants if r['tag'] == 'PTFRS23_MQ007_RESUME')
                facts = {f['name']: f for f in resume['facts']}
                assert facts['PTFRS23_MQ007_ModeTalkConfirmed']['min'] == facts['PTFRS23_MQ007_ModeTalkConfirmed']['max'] == 1
                assert facts['PTFRS23_MQ007_Issued']['min'] == facts['PTFRS23_MQ007_Issued']['max'] == 0
                owned[id] = 'PTFRS23_MQ007 fresh / explicit confirmed-history resume'
            else:
                owned[id] = spec['tag']
    existing = {'mq005_alley': 'Existing S1 adapter, current-policy bridge',
                'mq032_sacrum': 'Existing S2 native fresh admission',
                'mq025_02_kabuki': 'Existing active boxing family',
                'mq025_03_arroyo': 'Existing active boxing family',
                'mq025_05_glen': 'Existing active boxing family',
                'mq025_07_fight_club': 'Existing active boxing family',
                'mq025_06_pacifica': 'Existing active boxing family',
                'sq025c05_scared': 'Existing active Epistrophy family',
                'sq025c04_manic': 'Existing active Epistrophy family'}
    coverage = []
    for job in jobs:
        state = job['rootState']; id = job['id']
        if state == 'Succeeded':
            status = 'Completed: preserved, no replay'
        elif state == 'Active':
            status = 'Active: existing owner preserved, no duplicate'
        elif id in owned:
            status = 'Native adapter supplied; exact stage/prerequisite guards still apply'
        elif id in existing:
            status = existing[id]
        else:
            status = 'NOT COVERED'
        coverage.append({'id': id, 'title': job['title'], 'captured_state': state, 'coverage': status})
    assert not any(c['coverage'] == 'NOT COVERED' for c in coverage), [c for c in coverage if c['coverage'] == 'NOT COVERED']
    result = {'status': 'PASS_NOT_LIVE', 'build_sha256': sha(build / 'build.json'),
              'tester_sha256': sha(Path(__file__)), 'native_payload_checks': native,
              'policy_cases': cases, 'component_tests': proofs, 'coverage': coverage,
              'coverage_limit': 'Supplied adapter is not admitted/live proof. Ambiguous progress and unmet native prerequisites remain protected; do not claim all stages restored.',
              'runtime_adapters': len(rm['rows']), 'source_pins': m['source_pins']}
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['coverage', 'source_pins']}, indent=2))


if __name__ == '__main__':
    main(sys.argv[1])
