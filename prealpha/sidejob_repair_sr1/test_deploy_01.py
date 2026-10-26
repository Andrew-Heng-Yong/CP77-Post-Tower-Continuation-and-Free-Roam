import hashlib
import json
import shutil
import subprocess
from pathlib import Path

here = Path(__file__).resolve().parent
candidate = here / 'candidate_02'
manifest = json.loads((candidate / 'install_manifest_01.json').read_text(encoding='utf-8'))
pwsh = Path('C:/Users/Ayong/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
script = here / 'deploy_01.ps1'
fixtures = candidate / 'deploy_fixtures'
fixtures.mkdir(exist_ok=True)
assert not any(fixtures.iterdir()), 'Fixture test directory already populated; use a successor test'

def hash_file(path):
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest().upper()

game = Path(manifest['game_root'])
real_before = {f['target']: hash_file(game / f['target']) for f in manifest['files']}
assert real_before == {f['target']: f['before'] for f in manifest['files']}

def run(action, root, fail_after=0, expected_ok=True):
    args = [str(pwsh), '-NoProfile', '-File', str(script), '-Action', action, '-FixtureRoot', str(root)]
    if fail_after:
        args += ['-TestFailAfter', str(fail_after)]
    result = subprocess.run(args, capture_output=True, text=True)
    assert (result.returncode == 0) == expected_ok, (action, fail_after, result.returncode, result.stdout[-800:], result.stderr[-800:])
    return {'action': action, 'fail_after': fail_after, 'exit_code': result.returncode, 'tail': (result.stdout or result.stderr).strip().splitlines()[-1:]}

def setup(label):
    root = fixtures / label
    root.mkdir()
    for f in manifest['files']:
        if f['before']:
            dest = root / 'game' / f['target']
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(game / f['target'], dest)
            assert hash_file(dest) == f['before']
    return root

def verify_state(root, stage):
    for f in manifest['files']:
        expected = f['after'] if stage == 'installed' else f['before']
        assert hash_file(root / 'game' / f['target']) == expected, (stage, f['target'])

actions = []
root = setup('normal_01')
for action in ('Validate', 'Install', 'Verify', 'ValidateRollback', 'Rollback'):
    actions.append(run(action, root))
    if action == 'Install':
        verify_state(root, 'installed')
verify_state(root, 'baseline')

for fail in (1, 3, 5):
    root = setup(f'interrupt_{fail:02d}')
    actions.append(run('Validate', root))
    actions.append(run('Install', root, fail_after=fail, expected_ok=False))
    actions.append(run('ValidateRollback', root))
    actions.append(run('Rollback', root))
    verify_state(root, 'baseline')

real_after = {f['target']: hash_file(game / f['target']) for f in manifest['files']}
assert real_after == real_before, 'Real game target changed during fixture tests'
result = {'status': 'FIXTURE_DEPLOY_AND_INTERRUPT_ROLLBACK_PASS', 'actions': actions, 'game_targets_unchanged': len(real_before), 'game_writes': 0, 'save_writes': 0}
(candidate / 'deployment_tests_01.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': result['status'], 'actions': len(actions), 'game_targets_unchanged': len(real_before)}))
