import hashlib
import json
import shutil
import subprocess
from pathlib import Path

here = Path(__file__).resolve().parent
candidate = here / 'candidate_01'
manifest = json.loads((candidate / 'install_manifest_01.json').read_text(encoding='utf-8'))
pwsh = Path('C:/Users/Ayong/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
script = here / 'deploy_01.ps1'
fixtures = candidate / 'deploy_fixtures'
assert not fixtures.exists(), 'Fixture directory exists; use a successor test'
fixtures.mkdir()
game = Path(manifest['game_root'])

def sha(path):
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest().upper()

old = {row['path']: row['sha256'] for row in manifest['old_files']}
new = {row['path']: row['sha256'] for row in manifest['new_files']}
assert len(old) == 127 and len(new) == 51
real_before = {path: sha(game / path) for path in old}
assert real_before == old

def setup(name):
    root = fixtures / name
    root.mkdir()
    for relative, expected in old.items():
        target = root / 'game' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(game / relative, target)
        assert sha(target) == expected
    return root

def run(action, root, fail_after=0, ok=True):
    args = [str(pwsh), '-NoProfile', '-File', str(script), '-Action', action, '-FixtureRoot', str(root)]
    if fail_after:
        args += ['-TestFailAfter', str(fail_after)]
    process = subprocess.run(args, capture_output=True, text=True, timeout=180)
    assert (process.returncode == 0) == ok, (action, fail_after, process.returncode, process.stdout[-800:], process.stderr[-800:])
    return {'action': action, 'fail_after': fail_after, 'exit_code': process.returncode, 'tail': (process.stdout or process.stderr).strip().splitlines()[-1:]}

def check(root, installed):
    for relative, expected in old.items():
        actual = sha(root / 'game' / relative)
        assert actual == (new.get(relative) if installed else expected), (relative, actual)
    for relative, expected in new.items():
        assert sha(root / 'game' / relative) == (expected if installed else old.get(relative)), relative

actions = []
root = setup('normal_01')
for action in ('Validate', 'Install', 'Verify', 'ValidateRollback', 'Rollback'):
    actions.append(run(action, root))
    if action == 'Install':
        check(root, True)
check(root, False)

for stage in (1, 64, 127, 150, 178):
    root = setup(f'interrupt_{stage:03d}')
    actions.append(run('Validate', root))
    actions.append(run('Install', root, fail_after=stage, ok=False))
    actions.append(run('ValidateRollback', root))
    actions.append(run('Rollback', root))
    check(root, False)

assert {path: sha(game / path) for path in old} == real_before
proof = {'status': 'FULL_CONSOLIDATION_DEPLOY_FIXTURE_AND_INTERRUPTION_ROLLBACK_PASS', 'actions': actions, 'old_files': 127, 'new_files': 51, 'real_game_targets_unchanged': True, 'game_writes': 0, 'save_writes': 0}
(candidate / 'deployment_tests_01.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': proof['status'], 'actions': len(actions), 'old': 127, 'new': 51}))
