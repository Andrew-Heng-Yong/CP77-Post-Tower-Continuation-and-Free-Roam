"""Prepare a fresh one-file deployment and check its recovery path."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess

from prepare import BASELINE, BASELINE_SHA, COMPILE, HERE, PACKAGE, PRE, SCRIPT, read, replace_once, sha, write


PREVIOUS = 'QP2_REED_CRASH_AND_JOHNNY_WORLD'
EPOCH = 'QP2_JOHNNY_LOAD_REPAIR'
SCHEMA = 'PTFR_JOHNNY_LOAD_REPAIR_CORE_V1'
MANIFEST = HERE / 'core_manifest_01.json'
INSTALLER = HERE / 'deploy_core.ps1'
TEMPLATE = PRE / 'history_snapshot_cutoff/deploy_core.ps1'
FIXTURES = HERE / 'fixtures/deployment_01'


def prepare():
    assert not MANIFEST.exists() and not INSTALLER.exists()
    assert sha(BASELINE) == BASELINE_SHA
    assert sha(TEMPLATE) == '11E5778B7E0E18A8BECDDED6059E767AFC522303BA8043E8C3527EA0E09B07FD'
    old_manifest = TEMPLATE.parent / 'core_manifest_01.json'
    assert sha(old_manifest) == '214E1955D7FDE9DE0F270EF4A263205B1634CAC7A6DF4E7327C0DF74DD645D2C'
    baseline = read(BASELINE)
    assert baseline['core_epoch'] == PREVIOUS
    game = Path(baseline['game_root'])
    saves = Path(baseline['save_root'])
    compiler = read(COMPILE / 'result.json')
    verification = read(HERE / 'verification.json')
    assert compiler['status'] == 'PASS' and compiler['source_count'] == 148
    assert compiler['staged_hashes'][SCRIPT] == verification['after_sha256'] == sha(PACKAGE / SCRIPT)
    before = {r['path']: r['sha256'] for r in baseline['core_files']}
    after = {f.relative_to(PACKAGE).as_posix(): sha(f) for f in PACKAGE.rglob('*') if f.is_file()}
    assert len(after) == 51 and after == {**before, SCRIPT: verification['after_sha256']}
    assert {p for p in before if before[p] != after[p]} == {SCRIPT}
    files = [{'path': r['path'], 'before': r['sha256'], 'before_bytes': r['bytes'],
              'after': after[r['path']], 'after_bytes': (PACKAGE / r['path']).stat().st_size}
             for r in baseline['core_files']]
    protected = []
    for name in ('metadata.9.json', 'sav.dat', 'screenshot.png'):
        p = saves / 'ManualSave-26' / name
        protected.append({'path': p.relative_to(saves).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)})
    crash = HERE / 'crash_evidence.json'
    assert protected[1]['sha256'] == read(crash)['fixture_sha256']
    proofs = [BASELINE, crash, HERE / 'source.patch', HERE / 'verification.json', COMPILE / 'result.json']
    manifest = {
        'schema': SCHEMA, 'component': 'Core', 'source_epoch': EPOCH, 'predecessor_epoch': PREVIOUS,
        'scope': 'Replace the Johnny presentation script for the Manual Save 26 load crash.',
        'game_root': str(game), 'save_root': str(saves), 'package_root': str(PACKAGE),
        'process_names': read(old_manifest)['process_names'], 'files': files, 'changing_paths': [SCRIPT],
        'required_files': baseline['required_files'], 'protected_saves': protected, 'working_save_files': [],
        'proofs': [{'path': str(p), 'sha256': sha(p)} for p in proofs],
        'compile_inputs': {str(game / rel): digest for rel, digest in compiler['input_pins'].items()},
        'zip': '', 'zip_sha256': None,
    }
    write(MANIFEST, manifest)
    script = TEMPLATE.read_text(encoding='utf-8-sig')
    for old, new in (
        ('# The user authorized the snapshot cutoff repair over QP2.\n# The snapshot REDscript is the only game write.',
         '# The Johnny presentation REDscript is the only game write for this load repair.'),
        ("$PinnedCoreManifestSHA='214E1955D7FDE9DE0F270EF4A263205B1634CAC7A6DF4E7327C0DF74DD645D2C'",
         f"$PinnedCoreManifestSHA='{sha(MANIFEST)}'"),
        ("'PTFR_SNAPSHOT_CUTOFF_CORE_V1'", f"'{SCHEMA}'"),
        ("$manifest.source_epoch -cne 'QP2_SNAPSHOT_CUTOFF'", f"$manifest.source_epoch -cne '{EPOCH}'"),
        ("$manifest.predecessor_epoch -cne 'QP2'", f"$manifest.predecessor_epoch -cne '{PREVIOUS}'"),
        ("'recovery/core_snapshot_cutoff_01'", "'recovery/core_johnny_load_01'"),
        ("$wanted=@('r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds')", f"$wanted=@('{SCRIPT}')"),
        ('Core51/one-file snapshot scope drift', 'Core51/one-file Johnny presentation scope drift'),
    ):
        script = replace_once(script, old, new)
    with INSTALLER.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(script)
    return manifest


def write_bytes(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def test(manifest):
    assert not FIXTURES.exists()
    powershell = shutil.which('pwsh') or (
        r'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
    cases = [
        ('exact_core', True, [
            ('Preflight', 'PREFLIGHT_READY', []), ('Install', 'INSTALLED_VERIFIED', []),
            ('Verify', 'VERIFIED_AFTER', []), ('ValidateRollback', 'ROLLBACK_READY', []),
            ('Rollback', 'ROLLED_BACK_VERIFIED', []), ('Verify', 'VERIFIED_BEFORE', ['-ExpectedState', 'Before']),
        ]),
        ('interrupted', False, [
            ('Install', 72, ['-FailurePoint', 'CrashAfterFirstReplace']),
            ('Recover', 'RECOVERED_BEFORE', []), ('Verify', 'VERIFIED_BEFORE', ['-ExpectedState', 'Before']),
        ]),
        ('game_running', False, [('Install', 1, ['-FixtureProcesses', 'Cyberpunk2077'])]),
    ]
    actions = []
    for case, exact, operations in cases:
        root = FIXTURES / case
        game, saves, package = (root / d for d in ('game', 'saves', 'package'))
        data = deepcopy(manifest)
        data.update(game_root=str(game), save_root=str(saves), package_root=str(package),
                    proofs=[], compile_inputs={})
        for row in data['files']:
            rel = row['path']
            if exact:
                old = (Path(manifest['game_root']) / rel).read_bytes()
                new = (PACKAGE / rel).read_bytes()
            else:
                old = ('old ' + rel).encode()
                new = ('new ' + rel).encode() if rel == SCRIPT else old
            write_bytes(game / rel, old)
            write_bytes(package / rel, new)
            if exact:
                assert (sha(game / rel), sha(package / rel)) == (row['before'], row['after'])
            else:
                row.update(before=sha(game / rel), after=sha(package / rel), before_bytes=len(old), after_bytes=len(new))
        for rows, target in ((data['required_files'], game), (data['protected_saves'], saves)):
            for row in rows:
                content = row['path'].encode()
                path = target / row['path']
                write_bytes(path, content)
                row.update(sha256=sha(path), bytes=len(content))
        write_bytes(saves / 'OtherSave/sav.dat', b'Other save')
        write_bytes(game / 'ExternalMod/keep.txt', b'External file')
        path = root / 'manifest.json'
        write(path, data)
        for action, expected, flags in operations:
            cmd = [powershell, '-NoProfile', '-File', str(INSTALLER), '-Action', action,
                   '-FixtureRoot', str(root), '-FixtureManifest', str(path), '-FixtureManifestSHA', sha(path), *flags]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace',
                                    timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
            if isinstance(expected, int):
                assert result.returncode == expected, (action, result.stdout, result.stderr)
                status = None
            else:
                assert result.returncode == 0, (action, result.stdout, result.stderr)
                status = json.loads(result.stdout)['status']
                assert status == expected, (action, status, expected)
            actions.append({'fixture': case, 'action': action, 'status': status, 'returncode': result.returncode})
        assert all(sha(game / r['path']) == r['before'] for r in data['files'])
        assert all(sha(game / r['path']) == r['sha256'] for r in data['required_files'])
        assert all(sha(saves / r['path']) == r['sha256'] for r in data['protected_saves'])
        assert (saves / 'OtherSave/sav.dat').read_bytes() == b'Other save'
        assert (game / 'ExternalMod/keep.txt').read_bytes() == b'External file'
        if case == 'game_running':
            assert not (root / 'recovery').exists()
    return actions


def main():
    manifest = prepare()
    actions = test(manifest)
    results = HERE / 'fixture_results.json'
    scope = HERE / 'scope_review.json'
    write(results, {'status': 'PASS', 'manifest_sha256': sha(MANIFEST),
                    'installer_sha256': sha(INSTALLER), 'actions': actions})
    write(scope, {'changing_paths': [SCRIPT], 'core_paths': 51,
                  'manifest_sha256': sha(MANIFEST), 'save_writes': 0, 'game_launches': 0})
    write(HERE / 'readiness.json', {
        'status': 'READY_NOT_INSTALLED', 'manifest_sha256': sha(MANIFEST), 'installer_sha256': sha(INSTALLER),
        'fixture_result': results.name, 'fixture_result_sha256': sha(results),
        'scope_review': scope.name, 'scope_review_sha256': sha(scope),
    })
    print(f'One-file package ready. {len(actions)} transaction fixture actions verified.')


if __name__ == '__main__':
    main()
