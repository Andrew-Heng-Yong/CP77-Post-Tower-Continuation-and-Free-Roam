"""Bind S24 fresh-entry component proofs; no full-whitelist/live claim."""
import importlib.util
import json
import sys
import subprocess
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
    assert m['status'] == 'BUILT_S24_LIVE_PENDING' and m['packed_readback']
    assert len(m['files']) == 3 and not any('old_sha256' in f for f in m['files'])
    assert m['official_overrides'] == []
    assert m['mod_overrides'] == ['towercontinued\\gig_phone_u9\\fixer_cleanup.questphase']
    for p, h in m['source_pins'].items():
        assert sha(ROOT / p) == h, p
    for row in m['files']:
        assert sha(build / Path(row['relative']).name) == row['sha256']
    for depot, h in m['resources'].items():
        assert sha(build / 'source' / depot) == h
        assert depot.startswith('towercontinued\\sidejobs_s24\\') or depot in m['mod_overrides']
    assert len(m['injections']) == len(m['boots']) == len(set(m['boots']))
    assert len({v['id'] for v in m['injections']}) == len(m['injections'])
    assert all(v['depot'] in m['resources'] for v in m['injections'])
    assert m['installed_xl_pins']
    for path, h in m['installed_xl_pins'].items():
        assert sha(Path(path)) == h, path
    for old in m['installed_injections']:
        witnesses = [h for p, h in m['installed_xl_pins'].items() if Path(p).name == old['source']]
        assert witnesses == [old['source_sha256']]
    native = cases = 0; proofs = []; owner_specs = []; contracts = []
    for c in m['components']:
        cm, test = read(ROOT / c['manifest']), read(ROOT / c['tests'])
        assert test['status'].startswith('PASS')
        assert test.get('component_sha256', test.get('build_sha256')) == sha(ROOT / c['manifest'])
        assert test['tester_sha256'] in m['source_pins'].values()
        native += test['native_payload_checks']; cases += test['policy_cases']
        for depot, h in cm['resources'].items():
            assert m['resources'][depot] == h
            assert sha(ROOT / c['root'] / 'source' / depot) == h
            for path, graph in graphs(build / ('readback/' + depot.replace('\\', '_') + '.json')).items():
                ids = {n['id'] for n in graph['nodes']}
                assert len(ids) == len(graph['nodes']), (depot, path)
                for e in graph['edges']:
                    assert e[0] in ids and e[2] in ids, (depot, path, e)
        if cm.get('contract'):
            contracts.append(cm['contract'])
            data = read(ROOT / cm['contract'])
            owner_specs += data.get('owners', data.get('contracts', [data]))
        proofs.append({'manifest': c['manifest'], 'tests': c['tests'], 'sha256': sha(ROOT / c['tests'])})
    metadata = read(ROOT / m['journal_metadata_proof'])
    assert metadata['status'] == 'PASS_USED_JOURNAL_METADATA_ALL_VARIANTS'
    assert sorted(metadata['contracts']) == sorted(contracts)
    verifier = HERE / 'ep1/verify_journal_metadata.py'
    assert sha(verifier) == metadata['verifier_sha256']
    for p, h in metadata['source_pins'].items():
        assert m['source_pins'][p] == h == sha(ROOT / p), p
    check = build / 'journal_metadata_check.json'
    subprocess.run([sys.executable, str(verifier), '--contracts', *metadata['contracts'],
                    '--output', str(check.relative_to(ROOT))], check=True, cwd=ROOT)
    assert read(check) == metadata, 'Independent metadata proof rerun changed'
    rt = ROOT / m['runtime']; rm, rp = read(rt / 'manifest.json'), read(rt / 'tests.json')
    assert rp['status'] == 'PASS_OFFLINE_NOT_LIVE'
    assert rp['manifest_sha256'] == sha(rt / 'manifest.json')
    assert rp['test_sha256'] == sha(HERE / 'runtime/test.py')
    assert sha(build / 'SideJobsS24.reds') == rm['files']['SideJobsS24.reds']
    assert (build / 'SideJobsS24.reds').read_text(encoding='utf-8') == generate.template().replace('// GENERATED_DATA', generate.data_source(rm['rows']))
    assert len({r['tag'] for r in rm['rows']}) == len(rm['rows'])
    assert len({r['id'] for r in rm['rows']}) == len(rm['rows']), 'No duplicate fresh owner'
    assert {s['tag'] for s in owner_specs} == {r['tag'] for r in rm['rows']}
    for row in rm['rows']:
        assert row['journals'][0]['states'] == [1]
        assert all(j['states'] == [1] for j in row['journals'] if j['class'] == 'gameJournalQuest')
    cases += rp['policy_cases']
    capture = read(ROOT / 'research/sidejobs_s23/live_20261016_01/capture.json')
    assert capture['repeatedReadMatched'] and capture['first']['settledBefore'] and capture['first']['settledAfter']
    jobs = {j['id']: j for j in capture['second']['jobs']}
    controls = []
    for row in rm['rows']:
        captured = jobs[row['id']]
        state = captured['rootState']
        # This is a frozen pre-S23 protection control, NOT a current live sample.
        rejected = state != 'Inactive'
        mismatches = []
        for fact in row['facts']:
            v = captured['facts'].get(fact['name']) if isinstance(captured['facts'], dict) else None
            if isinstance(v, int) and not fact['min'] <= v <= fact['max']:
                mismatches.append(fact['name']); rejected = True
        controls.append({'id': row['id'], 'captured_root': state, 'known_progress_mismatches': mismatches,
                         'frozen_control_rejected': rejected, 'unknown_not_assumed_zero': True})
    assert all(c['frozen_control_rejected'] for c in controls), 'This captured branch has prior progress for this entire new batch'
    result = {'status': 'PASS_NOT_LIVE', 'build_sha256': sha(build / 'build.json'),
              'tester_sha256': sha(Path(__file__)), 'native_payload_checks': native,
              'policy_cases': cases, 'component_tests': proofs, 'frozen_capture_controls': controls,
              'runtime_adapters': len(rm['rows']), 'source_pins': m['source_pins'],
              'coverage_limit': 'Only the listed fresh entry routes. Native interactions/rewards/reload still require live tests. Existing restorations remain installed.'}
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ['source_pins']}, indent=2))


if __name__ == '__main__':
    main(sys.argv[1])
