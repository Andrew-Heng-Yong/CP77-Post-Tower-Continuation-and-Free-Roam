"""Tie the reviewed component checks to exact installable bytes."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/afterlife_world'


def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


m, nix = read('manifest.json'), read('nix_manifest.json')
dancers, nt, runtime, population = (read(n) for n in
    ('dancers_tests.json', 'nix_tests.json', 'runtime_tests.json', 'population_tests.json'))
assert m['status'] == 'BUILT_AFTERLIFE_R1_OFFLINE_LIVE_PENDING'
assert m['packed_readback_pass'] and m['original_resource_overrides'] == 0
assert len(m['resources']) == len(set(m['resources'])) == 8
assert m['private_entries'] == len(m['population_branches']) == 28
assert m['holographic_dancers'] == 10 and m['population_nodes'] == 262
assert all(p.startswith('towercontinued\\afterlife_r1\\') for p in m['resources'])
assert sha(m['archive']) == m['sha256']
assert sha(m['archive'] + '.xl') == m['xl_sha256']
assert sha(nix['archive']) == nix['sha256'] == nt['archive_sha256']
assert sha(nix['script']) == nix['script_sha256'] == nt['script_sha256'] == runtime['nix_driver_sha256']
assert dancers['status'] == 'PASS_DANCERS_OFFLINE_NOT_LIVE'
assert nt['status'] == 'PASS_NIX_GUARD_DELTA_OFFLINE_LIVE_PENDING'
assert runtime['status'] == 'PASS_RUNTIME_OFFLINE_NOT_LIVE'
assert population['status'] == 'PASS_POPULATION_OFFLINE_NOT_LIVE'
assert population['archive_sha256'] == m['sha256'], 'Population tests must cover the final package'
assert population['population_phase_sha256'] == sha(Path(m['source_root']) / m['population_phase'])
assert population['patrons_manifest_sha256'] == sha(OUT / 'patrons_manifest.json')
assert population['rogue_world_manifest_sha256'] == sha(OUT / 'rogue_world_manifest.json')
for row in m['payloads']:
    assert sha(row['source']) == row['sha256']
    assert sha(Path(m['source_root']) / row['depot']) == row['sha256']
assert next(r['sha256'] for r in m['payloads'] if r['depot'].endswith('\\dancers.questphase')) == dancers['phase_sha256']
assert sha(ROOT / 'redscript/PTFR_Afterlife_R1/AfterlifeDriver.reds') == runtime['driver_sha256']
assert sha(ROOT / 'diagnostics/PTFR_Afterlife_Audit/init.lua') == runtime['diagnostic_sha256']
assert read('afterlife_save_facts.json')['unchanged'] and read('preending_save_facts.json')['unchanged']
report = {'status': 'PASS_AFTERLIFE_R1_OFFLINE_NOT_LIVE', 'archive_sha256': m['sha256'],
    'xl_sha256': m['xl_sha256'], 'nix_archive_sha256': nix['sha256'],
    'dancer_nodes': dancers['nodes'], 'population_nodes': m['population_nodes'],
    'holographic_dancers': 10, 'private_population_entries': m['private_entries'],
    'private_population_maximum_actors': m['private_actors_max'],
    'nix_native_conditions_changed': 1, 'unchanged_s4_payloads': 15,
    'runtime_compile_and_lua51': 'PASS', 'population_tests': population,
    'dancer_tests': dancers, 'nix_guard_tests': nt['negative_guard_cases'],
    'runtime_enable_guard_tests': runtime['negative_enable_guards'],
    'save_samples_unchanged': True, 'live_tested': False}
(OUT / 'tests.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k not in ('population_tests', 'dancer_tests')}, indent=2))
