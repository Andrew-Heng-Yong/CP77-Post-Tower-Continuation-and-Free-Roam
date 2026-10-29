"""Read-only installed package/save verification; retain the assessment locally."""
from pathlib import Path
from hashlib import sha256
import json

H = Path(__file__).resolve().parent
C = H / 'candidate_01'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
digest = lambda p: sha256(p.read_bytes()).hexdigest().upper()
m = read(C / 'install_manifest_01.json')
g = Path(m['game_root'])
s = Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
baseline = read(C / 'save_baseline_01.json')['files']
assert read(C / 'deployment_tests_01.json')['status'] == 'PASS'
assert digest(C / 'install_manifest_01.json') == Path(str(C / 'install_manifest_01.json') + '.sha256').read_text().strip()
assert all(digest(g / r['path']) == r['after'] for r in m['package_files'])
assert {str(p.relative_to(s)) for p in s.rglob('*') if p.is_file()} == {r['path'] for r in baseline}
assert all(digest(s / r['path']) == r['sha256'] for r in baseline)
assert all(digest(Path(r['path'])) == r['sha256'] for r in m['proofs'])
result = {'status': 'PASS_WA2_INSTALLED_FILES_AND_SAVE_PRESERVATION',
          'installed_paths': len(m['package_files']), 'changed_paths': m['changed_paths'],
          'archive_members': m['archive_members'], 'save_files_unchanged': len(baseline),
          'manifest_sha256': digest(C / 'install_manifest_01.json'),
          'zip': read(C / 'zip_proof_01.json'),
          'fixture_actions': read(C / 'deployment_tests_01.json')['fixture_actions'],
          'preserved_BA1_live_report': 'User confirmed prototype works', 'expanded_live_shooting': 'UNVERIFIED', 'live_speech': 'UNVERIFIED',
          'live_save_reload': 'UNVERIFIED', 'game_launched': False,
          'save_writes': 0, 'native_fact_writes': 0, 'public_release': False}
p = C / 'installed_assessment_01.json'
assert not p.exists(), 'Preserve previous installed assessment'
p.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
Path(str(p) + '.sha256').write_text(digest(p) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
