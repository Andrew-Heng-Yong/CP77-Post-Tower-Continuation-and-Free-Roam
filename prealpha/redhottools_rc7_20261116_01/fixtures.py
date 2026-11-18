"""Exercise the new-file installer only inside isolated workspace fixtures."""
from pathlib import Path
import copy
import hashlib
import json
import subprocess

TASK = Path(__file__).resolve().parent
WORK = TASK / 'work'
PWSH = 'C:/Users/Ayong/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe'
INSTALLER = WORK / 'install.ps1'
RESULTS = []


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest().upper()


def write_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def fixture(name):
    root = WORK / 'fixtures' / name
    root.mkdir(parents=True, exist_ok=False)
    game, saves = root/'game', root/'saves'
    game.mkdir()
    (saves/'OtherSave').mkdir(parents=True)
    (saves/'OtherSave/sav.dat').write_bytes(b'original user save')
    (game/'external.mod').write_bytes(b'original unrelated mod')
    m = copy.deepcopy(json.loads((WORK/'tool_manifest_01.json').read_text(encoding='utf-8')))
    m.update(game_root=str(game), save_root=str(saves), compile_inputs={}, proofs=[], zip=None)
    m['required_files'] = [dict(path='external.mod', bytes=22,
        sha256=sha(game/'external.mod'), active_only=False)]
    assert (game/'external.mod').stat().st_size == 22
    path = root/'manifest.json'
    write_json(path, m)
    return root, m


def run(f, action, *args, expected=0, contains=None):
    root, m = f
    result = subprocess.run([PWSH, '-NoProfile', '-File', str(INSTALLER),
        '-Action', action, '-FixtureRoot', str(root), '-FixtureManifest', str(root/'manifest.json'),
        '-FixtureManifestSHA', sha(root/'manifest.json'), *args], capture_output=True, text=True,
        encoding='utf-8', errors='replace', timeout=90)
    record = dict(fixture=root.name, action=action, args=args, expected_exit=expected,
        exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr)
    RESULTS.append(record)
    with (root/f'action_{len(RESULTS):02d}.json').open('x', encoding='utf-8') as stream:
        json.dump(record, stream, indent=2)
    assert result.returncode == expected, record
    if contains:
        assert contains in result.stdout + result.stderr, record
    return result


def preserved(f, after=False, drift=False):
    root, m = f
    assert (root/'saves/OtherSave/sav.dat').read_bytes() == b'original user save'
    assert (root/'game/external.mod').read_bytes() == b'original unrelated mod'
    for i, row in enumerate(m['files']):
        target = root/'game'/row['path']
        if drift and i == 0:
            assert target.read_bytes() == b'FIXTURE_UNKNOWN_CHANGED_BYTES'
        elif after:
            assert sha(target) == row['after']
        else:
            assert not target.exists(), target


def main():
    assert not (WORK/'fixtures').exists(), 'Fresh fixtures required'
    clean = fixture('clean_round_trip')
    run(clean, 'Preflight', contains='PREFLIGHT_READY')
    run(clean, 'Install', contains='INSTALLED_VERIFIED')
    preserved(clean, after=True)
    run(clean, 'Verify', contains='VERIFIED_AFTER')
    run(clean, 'ValidateRollback', contains='ROLLBACK_READY')
    # Rollback must preserve new human saves and runtime-created tool preferences.
    new_save = clean[0]/'saves/NewHumanSave'
    new_save.mkdir()
    (new_save/'sav.dat').write_bytes(b'newer human save')
    preferences = clean[0]/'game/bin/x64/plugins/cyber_engine_tweaks/mods/RedHotTools/user_preferences.json'
    preferences.write_bytes(b'keep runtime preferences')
    run(clean, 'Rollback', contains='ROLLED_BACK_VERIFIED')
    run(clean, 'Verify', '-ExpectedState', 'Before', contains='VERIFIED_BEFORE')
    preserved(clean)
    assert (new_save/'sav.dat').read_bytes() == b'newer human save'
    assert preferences.read_bytes() == b'keep runtime preferences'
    for fault in ['AfterBackup', 'AfterFirstReplace', 'BeforeReceipt']:
        f = fixture('automatic_' + fault)
        run(f, 'Install', '-FailurePoint', fault, expected=1, contains='RESTORED_BEFORE_VERIFIED')
        run(f, 'Verify', '-ExpectedState', 'Before', contains='VERIFIED_BEFORE')
        preserved(f)
    for fault in ['CrashAfterStage', 'CrashAfterFirstReplace', 'CrashBeforeReceipt']:
        f = fixture('interrupted_' + fault)
        run(f, 'Install', '-FailurePoint', fault, expected=72)
        run(f, 'Recover', contains='RECOVERED_BEFORE')
        run(f, 'Verify', '-ExpectedState', 'Before', contains='VERIFIED_BEFORE')
        preserved(f)
    f = fixture('game_running')
    run(f, 'Install', '-FixtureProcesses', 'Cyberpunk2077', expected=1, contains='must be closed naturally')
    preserved(f)
    assert not (f[0]/'recovery').exists()
    f = fixture('occupied_tool_root')
    occupied = f[0]/'game/red4ext/plugins/RedHotTools/unknown.log'
    occupied.parent.mkdir(parents=True)
    occupied.write_bytes(b'preserve unknown existing file')
    run(f, 'Install', expected=1, contains='Existing RedHotTools root refused')
    preserved(f)
    assert occupied.read_bytes() == b'preserve unknown existing file'
    f = fixture('unknown_target_drift')
    run(f, 'Install', '-FailurePoint', 'TargetDriftAfterFirstReplace', expected=1, contains='RECOVERY_REQUIRED')
    run(f, 'Recover', expected=1, contains='Unknown mixed target requires manual review')
    preserved(f, drift=True)
    result_path = WORK/'fixture_results.json'
    write_json(result_path, dict(status='PASS', cases=10, actions=len(RESULTS),
        installer_sha256=sha(INSTALLER), results=RESULTS, game_writes=0, real_game_launches=0,
        actual_package_used=True, new_saves_and_runtime_preferences_preserved=True))
    write_json(WORK/'readiness.json', dict(status='READY_NOT_INSTALLED',
        manifest_sha256=sha(WORK/'tool_manifest_01.json'), installer_sha256=sha(INSTALLER),
        fixture_result='fixture_results.json', fixture_result_sha256=sha(result_path),
        scope_review='scope_review.json', scope_review_sha256=sha(WORK/'scope_review.json')))
    print(json.dumps(dict(status='PASS', cases=10, actions=len(RESULTS))))


if __name__ == '__main__':
    main()
