"""Prepare, exercise and record the profile setup repair transaction."""

import argparse
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

from build import (BASELINE, BASELINE_SHA, CHANGES, EPOCH, HERE, PREVIOUS, TEMPLATE,
                   TEMPLATE_MANIFEST_SHA, TEMPLATE_SHA, one, read, sha, write)


SCHEMA = 'PTFR_TOWER_RECOVERY_PROFILE_HOLD_CORE_V1'
MANIFEST = HERE / 'core_manifest_01.json'
INSTALLER = HERE / 'deploy_core.ps1'
FIXTURES = HERE / 'fixtures/deployment_01'
DEPLOYMENT = HERE / 'deployment_01'
JOURNAL = HERE / 'recovery/core_tower_profile_hold_01/journal.json'


def prepare(attempt):
    assert not MANIFEST.exists() and not INSTALLER.exists()
    assert sha(BASELINE) == BASELINE_SHA and sha(TEMPLATE) == TEMPLATE_SHA
    predecessor = read(BASELINE)
    assert predecessor['core_epoch'] == PREVIOUS
    candidate = HERE / f'candidate_{attempt:02}'
    package = candidate / 'package'
    compile_path = HERE / f'compile_{attempt:02}/result.json'
    source_check = candidate / 'verification.json'
    compiled, checked = read(compile_path), read(source_check)
    assert compiled['status'] == checked['compile'] == 'PASS'
    assert checked['baseline_sha256'] == BASELINE_SHA
    game = Path(predecessor['game_root'])
    files = []
    for row in predecessor['core_files']:
        rel = row['path']
        src, dest = game / rel, package / rel
        assert sha(src) == row['sha256']
        after = sha(dest)
        if rel in CHANGES:
            assert after == compiled['staged_hashes'][rel] == checked['script_hashes'][rel]
        else:
            assert after == row['sha256']
        files.append({'path': rel, 'before': row['sha256'], 'before_bytes': row['bytes'],
                      'after': after, 'after_bytes': dest.stat().st_size})
    assert len(files) == 51 and {x['path'] for x in files if x['before'] != x['after']} == CHANGES
    template_manifest = TEMPLATE.parent / 'core_manifest_01.json'
    assert sha(template_manifest) == TEMPLATE_MANIFEST_SHA
    proofs = [BASELINE, compile_path, source_check, candidate / 'source.patch']
    manifest = {
        'schema': SCHEMA, 'component': 'Core', 'source_epoch': EPOCH, 'predecessor_epoch': PREVIOUS,
        'scope': 'Resolve the post-Tower profile setup hold in the two existing restriction scripts.',
        'game_root': str(game), 'save_root': predecessor['save_root'], 'package_root': str(package),
        'process_names': read(template_manifest)['process_names'], 'files': files, 'changing_paths': sorted(CHANGES),
        'required_files': predecessor['required_files'], 'protected_saves': [], 'working_save_files': [],
        'proofs': [{'path': str(p), 'sha256': sha(p)} for p in proofs],
        'compile_inputs': {str(game / rel): pin for rel, pin in compiled['input_pins'].items()},
        'zip': '', 'zip_sha256': None,
    }
    write(MANIFEST, manifest)
    script = TEMPLATE.read_text(encoding='utf-8-sig')
    for old, new in (
        ('# The Johnny presentation REDscript is the only game write for this load repair.',
         '# The two existing restriction scripts are the only game writes.'),
        (TEMPLATE_MANIFEST_SHA, sha(MANIFEST)),
        ('PTFR_JOHNNY_LOAD_REPAIR_CORE_V1', SCHEMA),
        ("$manifest.source_epoch -cne 'QP2_JOHNNY_LOAD_REPAIR'", f"$manifest.source_epoch -cne '{EPOCH}'"),
        ("$manifest.predecessor_epoch -cne 'QP2_REED_CRASH_AND_JOHNNY_WORLD'", f"$manifest.predecessor_epoch -cne '{PREVIOUS}'"),
        ('recovery/core_johnny_load_01', 'recovery/core_tower_profile_hold_01'),
        ("$wanted=@('r6/scripts/PTFR_Consolidated/PTFR_JohnnyVoiceJV1.reds')",
         '$wanted=@(' + ','.join(f"'{path}'" for path in sorted(CHANGES)) + ')'),
        ('$changes.Count -ne 1', '$changes.Count -ne 2'),
        ('Core51/one-file Johnny presentation scope drift', 'Core51/profile repair scope drift'),
    ):
        script = one(script, old, new)
    with INSTALLER.open('x', encoding='utf-8', newline='\n') as out:
        out.write(script)
    actions = run_fixtures(manifest)
    fixture_result = HERE / 'fixture_results.json'
    scope = HERE / 'scope_review.json'
    write(fixture_result, {'status': 'PASS', 'installer_sha256': sha(INSTALLER), 'actions': actions})
    write(scope, {'changed_paths': sorted(CHANGES), 'core_paths': 51,
                  'source_checks': checked['checks'], 'manifest_sha256': sha(MANIFEST)})
    write(HERE / 'readiness.json', {
        'status': 'READY_NOT_INSTALLED', 'manifest_sha256': sha(MANIFEST), 'installer_sha256': sha(INSTALLER),
        'fixture_result': fixture_result.name, 'fixture_result_sha256': sha(fixture_result),
        'scope_review': scope.name, 'scope_review_sha256': sha(scope),
    })
    print(f'Prepared the two-script repair. {len(actions)} transaction fixture actions passed.')


def run_fixtures(manifest):
    assert not FIXTURES.exists()
    powershell = shutil.which('pwsh')
    assert powershell
    cases = {
        'rollback': [('Install', 'INSTALLED_VERIFIED'), ('Verify', 'VERIFIED_AFTER'),
                     ('ValidateRollback', 'ROLLBACK_READY'), ('Rollback', 'ROLLED_BACK_VERIFIED'),
                     ('Verify', 'VERIFIED_BEFORE', '-ExpectedState', 'Before')],
        'interrupted': [('Install', 72, '-FailurePoint', 'CrashAfterFirstReplace'), ('Recover', 'RECOVERED_BEFORE'),
                        ('Verify', 'VERIFIED_BEFORE', '-ExpectedState', 'Before')],
        'game_running': [('Install', 1, '-FixtureProcesses', 'Cyberpunk2077')],
    }
    actions = []
    for case, operations in cases.items():
        root = FIXTURES / case
        game, saves, package = (root / p for p in ('game', 'saves', 'package'))
        data = deepcopy(manifest)
        data.update(game_root=str(game), save_root=str(saves), package_root=str(package),
                    proofs=[], compile_inputs={})
        for row in data['files']:
            rel = row['path']
            before, after = game / rel, package / rel
            before.parent.mkdir(parents=True, exist_ok=True)
            after.parent.mkdir(parents=True, exist_ok=True)
            if case == 'rollback':
                shutil.copyfile(Path(manifest['game_root']) / rel, before)
                shutil.copyfile(Path(manifest['package_root']) / rel, after)
                assert (sha(before), sha(after)) == (row['before'], row['after'])
            else:
                before.write_text('old ' + rel, encoding='utf-8')
                after.write_text(('new ' if rel in CHANGES else 'old ') + rel, encoding='utf-8')
                row.update(before=sha(before), before_bytes=before.stat().st_size,
                           after=sha(after), after_bytes=after.stat().st_size)
        for row in data['required_files']:
            path = game / row['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(row['path'], encoding='utf-8')
            row.update(sha256=sha(path), bytes=path.stat().st_size)
        save = saves / 'FixtureSave/sav.dat'
        save.parent.mkdir(parents=True)
        save.write_bytes(b'preserved save')
        external = game / 'ExternalMod/keep.dat'
        external.parent.mkdir()
        external.write_bytes(b'preserved external file')
        fixture = root / 'manifest.json'
        write(fixture, data)
        for action, expected, *flags in operations:
            result = subprocess.run(
                [powershell, '-NoProfile', '-File', str(INSTALLER), '-Action', action,
                 '-FixtureRoot', str(root), '-FixtureManifest', str(fixture),
                 '-FixtureManifestSHA', sha(fixture), *flags],
                capture_output=True, encoding='utf-8', errors='replace', timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if isinstance(expected, int):
                assert result.returncode == expected, (case, action, result.stdout, result.stderr)
                status = None
            else:
                assert result.returncode == 0, (case, action, result.stdout, result.stderr)
                status = json.loads(result.stdout)['status']
                assert status == expected, (case, action, status)
            actions.append({'fixture': case, 'action': action, 'status': status, 'returncode': result.returncode})
        assert all(sha(game / row['path']) == row['before'] for row in data['files'])
        assert all(sha(game / row['path']) == row['sha256'] for row in data['required_files'])
        assert save.read_bytes() == b'preserved save' and external.read_bytes() == b'preserved external file'
        if case == 'game_running':
            assert not (root / 'recovery').exists()
    return actions


def record(attempt):
    previous, manifest, receipt = read(BASELINE), read(MANIFEST), read(JOURNAL)
    journal_text = receipt['payload_json']
    assert sha256(journal_text.encode()).hexdigest().upper() == receipt['payload_sha256']
    journal = json.loads(journal_text)
    assert journal['manifest_sha256'] == sha(MANIFEST) and journal['state'] == 'INSTALLED_VERIFIED'
    assert set(journal['completed_paths']) == CHANGES
    assert read(DEPLOYMENT / 'verify.json')['status'] == 'VERIFIED_AFTER'
    assert read(DEPLOYMENT / 'rollback_readiness.json')['status'] == 'ROLLBACK_READY'
    before, after = journal['protection_before'], journal['protection_after']
    assert before['saves']['tree_sha256'] == after['saves']['tree_sha256']
    assert before['unmanaged']['tree_sha256'] == after['unmanaged']['tree_sha256']
    assert before['dependencies'] == after['dependencies']
    assert journal['save_writes'] == journal['game_launches'] == 0
    files = [{'path': row['path'], 'bytes': row['after_bytes'], 'sha256': row['after']} for row in manifest['files']]
    game = Path(manifest['game_root'])
    assert all(sha(game / row['path']) == row['sha256'] for row in files + manifest['required_files'])
    compile_path = HERE / f'compile_{attempt:02}/result.json'
    path = DEPLOYMENT / 'installed_manifest_01.json'
    assert not path.exists()
    write(path, {
        'schema': 1, 'recorded_date': datetime.fromisoformat(journal['updated_utc']).astimezone().date().isoformat(),
        'core_epoch': EPOCH, 'predecessor_epoch': PREVIOUS,
        'authorization': 'Correct the live profile setup stall in the requested Tower recovery installation.',
        'archive_payloads': previous['archive_payloads'], 'archive_sha256': previous['archive_sha256'],
        'core_files': files, 'required_files': manifest['required_files'],
        'game_root': manifest['game_root'], 'save_root': manifest['save_root'],
        'source_candidate': str(Path(manifest['package_root']).parent), 'archive_source': previous['archive_source'],
        'predecessor_manifest': str(BASELINE), 'predecessor_manifest_sha256': BASELINE_SHA,
        'core_transaction': str(MANIFEST), 'core_transaction_sha256': sha(MANIFEST),
        'installed_receipt': str(JOURNAL), 'installed_receipt_sha256': sha(JOURNAL),
        'post_install_verification': str(DEPLOYMENT / 'verify.json'),
        'rollback_readiness': str(DEPLOYMENT / 'rollback_readiness.json'),
        'compile_result': str(compile_path), 'compile_sources': read(compile_path)['source_count'],
        'changed_paths': sorted(CHANGES), 'unchanged_core_paths': 49,
        'save_files_preserved': sum(x['kind'] == 'file' for x in after['saves']['files']),
        'save_tree_sha256': after['saves']['tree_sha256'], 'gameplay': 'UNVERIFIED',
    })
    print(f"Verified installed repair and {read(path)['save_files_preserved']} preserved save files.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'record'))
    parser.add_argument('--attempt', default=1, type=int)
    args = parser.parse_args()
    (prepare if args.action == 'prepare' else record)(args.attempt)
