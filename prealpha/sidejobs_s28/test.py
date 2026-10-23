"""Bind S28 component proofs, admission data and packed-resource readbacks."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'runtime'))
import generate
sys.path.insert(0, str(ROOT / 'prealpha/sidejobs_s27'))
import raw_compare
sys.path.insert(0, str(ROOT / 'tools'))
from review_stock_shark_u2 import graph

read, sha = generate.read, generate.sha


def main(revision):
    build = HERE / 'build' / revision
    output = build / 'tests.json'; assert not output.exists()
    m = read(build / 'build.json')
    assert m['status'] == 'BUILT_S28_LIVE_PENDING' and m['packed_readback']
    assert len(m['files']) == 3 and not any('old_sha256' in f for f in m['files'])
    assert m['official_overrides'] == []
    assert m['mod_overrides'] == [] and m['override_donors'] == {}
    for p, h in m['source_pins'].items(): assert sha(ROOT / p) == h, p
    assert m['native_source_readbacks']; raw_compare.self_test()
    for r in m['native_source_readbacks']:
        assert r['payload_equal'] and sha(ROOT / r['raw']) == r['raw_sha256']
        assert sha(ROOT / r['witness']) == r['witness_sha256']
        assert sha(build / r['fresh']) == r['fresh_sha256']
        assert raw_compare.payload(ROOT / r['witness']) == raw_compare.payload(build / r['fresh'])
    for row in m['files']: assert sha(build / Path(row['relative']).name) == row['sha256']
    for depot, h in m['resources'].items():
        assert sha(build / 'source' / depot) == h
        assert depot.startswith('towercontinued\\sidejobs_s28\\')
    assert len(m['injections']) == len(m['boots']) == len(set(m['boots']))
    assert len({x['id'] for x in m['injections']}) == len(m['injections'])
    assert all(x['depot'] in m['resources'] for x in m['injections'])
    for p, h in m['installed_xl_pins'].items(): assert sha(p) == h
    for x in m['installed_injections']:
        assert [h for p, h in m['installed_xl_pins'].items() if Path(p).name == x['source']] == [x['source_sha256']]
    native = cases = 0; proofs = []; contracts = []; specs = []
    for c in m['components']:
        cm, test = read(ROOT / c['manifest']), read(ROOT / c['tests'])
        assert test['status'].startswith('PASS')
        assert test.get('component_sha256', test.get('build_sha256')) == sha(ROOT / c['manifest'])
        assert test['tester_sha256'] in m['source_pins'].values()
        native += test['native_payload_checks']; cases += test['policy_cases']
        for depot, h in cm['resources'].items():
            assert m['resources'][depot] == h == sha(ROOT / c['root'] / 'source' / depot)
            if not depot.endswith('.questphase'): continue
            witness = build / ('readback/' + depot.replace('\\', '_') + '.json')
            for path, g in graph(witness).items():
                ids = {n['id'] for n in g['nodes']}
                assert len(ids) == len(g['nodes']), (depot, path)
                for e in g['edges']: assert e[0] in ids and e[2] in ids, (depot, path, e)
        if cm.get('contract'):
            contracts.append(cm['contract']); specs.extend(read(ROOT / cm['contract'])['owners'])
        proofs.append({'manifest': c['manifest'], 'tests': c['tests'], 'sha256': sha(ROOT / c['tests'])})
    metadata = read(ROOT / m['journal_metadata_proof'])
    assert metadata['status'] == 'PASS_USED_JOURNAL_METADATA_ALL_VARIANTS'
    assert sorted(metadata['contracts']) == sorted(contracts)
    verifier = HERE / 'verify_journal_metadata.py'; assert sha(verifier) == metadata['verifier_sha256']
    for p, h in metadata['source_pins'].items(): assert m['source_pins'][p] == h == sha(ROOT / p)
    check = build / 'journal_metadata_check.json'
    subprocess.run([sys.executable, str(verifier), '--contracts', *metadata['contracts'], '--output', str(check.relative_to(ROOT))], check=True, cwd=ROOT)
    assert read(check) == metadata
    rt = ROOT / m['runtime']; rm, rp = read(rt / 'manifest.json'), read(rt / 'tests.json')
    assert rp['status'] == 'PASS_OFFLINE_NOT_LIVE' and rp['manifest_sha256'] == sha(rt / 'manifest.json')
    assert rp['test_sha256'] == sha(HERE / 'runtime/test.py')
    assert sha(build / 'SideJobsS28.reds') == rm['files']['SideJobsS28.reds']
    assert (build / 'SideJobsS28.reds').read_text(encoding='utf-8') == generate.template().replace('// GENERATED_DATA', generate.data_source(rm['rows']))
    assert len(rm['rows']) == len(specs) == 4
    assert {r['tag'] for r in rm['rows']} == {r['tag'] for r in specs}
    for row in rm['rows']: assert row['journals'][0]['states'] == [1]
    cases += rp['policy_cases']
    result = {'status': 'PASS_NOT_LIVE', 'build_sha256': sha(build / 'build.json'),
              'tester_sha256': sha(Path(__file__)), 'native_payload_checks': native,
              'policy_cases': cases, 'component_tests': proofs, 'runtime_adapters': len(rm['rows']),
              'source_pins': m['source_pins'],
              'coverage_limit': 'Four bounded native beginnings. Completed/earned progress preserved; unsupported continuation defers. No live call, reward, device or reload proof.'}
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'source_pins'}, indent=2))


if __name__ == '__main__': main(sys.argv[1])
