"""Combine the two approved files and test their guarded transaction."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess

from build import BASELINE, BASELINE_SHA, HERE, OUT, PACKAGE, PRE, SCRIPT, plain, read, replace_once, sha, write


ARCHIVE = 'archive/pc/mod/zzzz_PTFR_Combined.archive'
WORLD = PRE / 'johnny_main_world_removal_20261111_01'
WORLD_ARCHIVE = WORLD / 'candidate_02/package' / ARCHIVE
WORLD_SHA = 'EB1793D88329DB23AC9B1B6B2422662E9E2911A5C63AB63279CDEFEFFDC0DE55'
INSTALLER = HERE / 'deploy_core.ps1'
MANIFEST = HERE / 'core_manifest_01.json'
TEMPLATE = PRE / 'history_snapshot_cutoff/deploy_core.ps1'
TEMPLATE_SHA = '11E5778B7E0E18A8BECDDED6059E767AFC522303BA8043E8C3527EA0E09B07FD'
PREDECESSOR = 'QP2_SNAPSHOT_CUTOFF'
EPOCH = 'QP2_REED_CRASH_AND_JOHNNY_WORLD'
SCHEMA = 'PTFR_REED_CRASH_AND_JOHNNY_WORLD_CORE_V1'
CHANGED = {ARCHIVE, SCRIPT}
OUT_PACKAGE = HERE / 'candidate_02/package'
FIXTURES = HERE / 'fixtures/deployment_01'


def prepare():
    assert not OUT_PACKAGE.exists() and not MANIFEST.exists() and not INSTALLER.exists()
    assert sha(BASELINE) == BASELINE_SHA and sha(TEMPLATE) == TEMPLATE_SHA
    baseline = read(BASELINE)
    assert baseline['core_epoch'] == PREDECESSOR
    game = Path(baseline['game_root'])
    saves = Path(baseline['save_root'])
    current = {row['path']: row['sha256'] for row in baseline['core_files']}
    crash_proof = read(HERE / 'verification.json')
    world_proof = read(WORLD / 'verification.json')
    compiler = read(OUT / 'result.json')
    assert crash_proof['status'] == 'VERIFIED_OFFLINE' and crash_proof['before_sha256'] == current[SCRIPT]
    assert world_proof['status'] == 'VERIFIED_STATIC_CANDIDATE'
    assert Path(world_proof['baseline']).resolve() == BASELINE.resolve()
    assert world_proof['files'] == {**current, ARCHIVE: WORLD_SHA}
    assert sha(WORLD_ARCHIVE) == WORLD_SHA and world_proof['archive_members'] == 1737
    assert compiler['status'] == 'PASS' and compiler['source_count'] == 148
    assert compiler['staged_hashes'][SCRIPT] == crash_proof['after_sha256'] == sha(PACKAGE / SCRIPT)

    shutil.copytree(PACKAGE, OUT_PACKAGE)
    shutil.copyfile(WORLD_ARCHIVE, OUT_PACKAGE / ARCHIVE)
    actual = {p.relative_to(OUT_PACKAGE).as_posix(): sha(p) for p in OUT_PACKAGE.rglob('*') if p.is_file()}
    assert actual == {**current, ARCHIVE: WORLD_SHA, SCRIPT: crash_proof['after_sha256']}
    files = []
    for row in baseline['core_files']:
        relative = row['path']
        files.append({'path': relative, 'before': row['sha256'], 'before_bytes': row['bytes'],
                      'after': actual[relative], 'after_bytes': (OUT_PACKAGE / relative).stat().st_size})
    assert {row['path'] for row in files if row['before'] != row['after']} == CHANGED

    protected = []
    for name in ('metadata.9.json', 'sav.dat', 'screenshot.png'):
        path = saves / 'ManualSave-26' / name
        plain(path)
        protected.append({'path': path.relative_to(saves).as_posix(), 'sha256': sha(path),
                          'bytes': path.stat().st_size})
    evidence = read(HERE / 'crash_evidence.json')
    assert protected[1]['sha256'] == evidence['fixture_sha256']
    previous_path = TEMPLATE.parent / 'core_manifest_01.json'
    assert sha(previous_path) == '214E1955D7FDE9DE0F270EF4A263205B1634CAC7A6DF4E7327C0DF74DD645D2C'
    previous_manifest = read(previous_path)
    proofs = [BASELINE, HERE / 'verification.json', HERE / 'crash_evidence.json',
              HERE / 'source.patch', OUT / 'result.json', WORLD / 'verification.json']
    manifest = {
        'schema': SCHEMA, 'component': 'Core', 'source_epoch': EPOCH, 'predecessor_epoch': PREDECESSOR,
        'scope': 'Install the approved Reed snapshot crash repair and main-world Johnny archive.',
        'game_root': str(game), 'save_root': str(saves), 'package_root': str(OUT_PACKAGE),
        'process_names': previous_manifest['process_names'], 'files': files,
        'changing_paths': sorted(CHANGED), 'required_files': baseline['required_files'],
        'protected_saves': protected, 'working_save_files': [],
        'proofs': [{'path': str(p), 'sha256': sha(p)} for p in proofs],
        'compile_inputs': {str(game / rel): digest for rel, digest in compiler['input_pins'].items()},
        'zip': '', 'zip_sha256': None,
    }
    write(MANIFEST, manifest)
    source = TEMPLATE.read_text(encoding='utf-8-sig')
    for old, new in (
        ('# The user authorized the snapshot cutoff repair over QP2.\n# The snapshot REDscript is the only game write.',
         '# The user authorized both repairs. Only the listed archive and snapshot script can change.'),
        ("$PinnedCoreManifestSHA='214E1955D7FDE9DE0F270EF4A263205B1634CAC7A6DF4E7327C0DF74DD645D2C'",
         f"$PinnedCoreManifestSHA='{sha(MANIFEST)}'"),
        ("'PTFR_SNAPSHOT_CUTOFF_CORE_V1'", f"'{SCHEMA}'"),
        ("$manifest.source_epoch -cne 'QP2_SNAPSHOT_CUTOFF'", f"$manifest.source_epoch -cne '{EPOCH}'"),
        ("$manifest.predecessor_epoch -cne 'QP2'", f"$manifest.predecessor_epoch -cne '{PREDECESSOR}'"),
        ("'recovery/core_snapshot_cutoff_01'", "'recovery/core_reed_johnny_01'"),
        (f"$wanted=@('{SCRIPT}')", f"$wanted=@('{ARCHIVE}','{SCRIPT}')"),
        ('$changes.Count -ne 1', '$changes.Count -ne 2'),
        ('Core51/one-file snapshot scope drift', 'Core51/two-file repair scope drift'),
    ):
        source = replace_once(source, old, new)
    with INSTALLER.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(source)
    return manifest, game


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def fixture(manifest, installed, name, exact=False):
    root = FIXTURES / name
    before = root / 'game'
    after = root / 'package'
    saves = root / 'saves'
    copy = deepcopy(manifest)
    copy.update(game_root=str(before), package_root=str(after), save_root=str(saves),
                compile_inputs={}, proofs=[])
    for row in copy['files']:
        rel = row['path']
        if exact:
            for origin, target, label in ((installed, before, 'before'), (OUT_PACKAGE, after, 'after')):
                assert sha(origin / rel) == row[label]
                put(target / rel, (origin / rel).read_bytes())
        else:
            old = ('old ' + rel).encode()
            new = ('new ' + rel).encode() if rel in CHANGED else old
            put(before / rel, old)
            put(after / rel, new)
            row.update(before=sha(before / rel), before_bytes=len(old),
                       after=sha(after / rel), after_bytes=len(new))
    for rows, dest in ((copy['required_files'], before), (copy['protected_saves'], saves)):
        for row in rows:
            data = ('protected ' + row['path']).encode()
            path = dest / row['path']
            put(path, data)
            row.update(sha256=sha(path), bytes=len(data))
    put(saves / 'OtherSave/sav.dat', b'Extra save')
    put(before / 'unrelated_mod/keep.txt', b'External mod')
    write(root / 'manifest.json', copy)
    return root, copy


def check_state(root, manifest, side):
    game = root / 'game'
    assert all(sha(game / r['path']) == r[side] for r in manifest['files'])
    assert all(sha(game / r['path']) == r['sha256'] for r in manifest['required_files'])
    assert all(sha(root / 'saves' / r['path']) == r['sha256'] for r in manifest['protected_saves'])
    assert (root / 'saves/OtherSave/sav.dat').read_bytes() == b'Extra save'
    assert (game / 'unrelated_mod/keep.txt').read_bytes() == b'External mod'


def verify_transaction(manifest, game):
    assert not FIXTURES.exists()
    powershell = shutil.which('pwsh') or (
        r'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
    actions = []

    def call(root, action, expected, *flags):
        path = root / 'manifest.json'
        command = [powershell, '-NoProfile', '-File', str(INSTALLER), '-Action', action,
                   '-FixtureRoot', str(root), '-FixtureManifest', str(path),
                   '-FixtureManifestSHA', sha(path), *flags]
        proc = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace',
                              timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
        if isinstance(expected, int):
            assert proc.returncode == expected, (root, action, proc.stdout, proc.stderr)
            status = None
        else:
            assert proc.returncode == 0, (root, action, proc.stdout, proc.stderr)
            status = json.loads(proc.stdout)['status']
            assert status == expected, (root, action, status, expected)
        actions.append({'fixture': root.name, 'action': action, 'returncode': proc.returncode, 'status': status})

    root, copy = fixture(manifest, game, 'exact_Core51', exact=True)
    call(root, 'Preflight', 'PREFLIGHT_READY')
    call(root, 'Install', 'INSTALLED_VERIFIED')
    check_state(root, copy, 'after')
    for row in copy['files']:
        if row['path'] in CHANGED:
            assert sha(root / 'recovery/core/old' / row['path']) == row['before']
    call(root, 'Verify', 'VERIFIED_AFTER')
    call(root, 'ValidateRollback', 'ROLLBACK_READY')
    call(root, 'Rollback', 'ROLLED_BACK_VERIFIED')
    call(root, 'Verify', 'VERIFIED_BEFORE', '-ExpectedState', 'Before')
    check_state(root, copy, 'before')

    root, copy = fixture(manifest, game, 'crash_between_replacements')
    call(root, 'Install', 72, '-FailurePoint', 'CrashAfterFirstReplace')
    call(root, 'Recover', 'RECOVERED_BEFORE')
    call(root, 'Verify', 'VERIFIED_BEFORE', '-ExpectedState', 'Before')
    check_state(root, copy, 'before')

    root, copy = fixture(manifest, game, 'interruption_after_second_replacement')
    call(root, 'Install', 1, '-FailurePoint', 'AfterSecondReplace')
    call(root, 'Verify', 'VERIFIED_BEFORE', '-ExpectedState', 'Before')
    check_state(root, copy, 'before')

    root, copy = fixture(manifest, game, 'game_running')
    call(root, 'Install', 1, '-FixtureProcesses', 'Cyberpunk2077')
    check_state(root, copy, 'before')
    assert not (root / 'recovery').exists()
    return actions


def main():
    manifest, game = prepare()
    actions = verify_transaction(manifest, game)
    checks = HERE / 'fixture_results.json'
    scope = HERE / 'scope_review.json'
    write(checks, {'status': 'PASS', 'manifest_sha256': sha(MANIFEST),
                   'installer_sha256': sha(INSTALLER), 'actions': actions})
    write(scope, {'approved_paths': sorted(CHANGED), 'manifest_sha256': sha(MANIFEST),
                  'source_checks': [row['path'] for row in manifest['proofs']],
                  'core_paths': 51, 'save_writes': 0, 'game_launches': 0})
    write(HERE / 'readiness.json', {
        'status': 'READY_NOT_INSTALLED', 'manifest_sha256': sha(MANIFEST), 'installer_sha256': sha(INSTALLER),
        'fixture_result': checks.name, 'fixture_result_sha256': sha(checks),
        'scope_review': scope.name, 'scope_review_sha256': sha(scope),
    })
    print(f'Both files prepared and {len(actions)} transaction fixture actions verified.')


if __name__ == '__main__':
    main()
