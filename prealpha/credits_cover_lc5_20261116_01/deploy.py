"""Prepare, test and record the guarded one-file credits cover deployment."""
import argparse
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from stage_and_compile import HERE, WORKSPACE, PREDECESSOR, PREDECESSOR_SHA, RELATIVE_SCRIPT
from stage_and_compile import check_plain, file_record, inventory, sha256, verify_rows, write_json


WORK = HERE / 'work'
DEPLOYMENT = WORK / 'deployment_01'
INSTALLER = WORK / 'deploy_core.ps1'
MANIFEST = WORK / 'core_manifest_01.json'
RECOVERY = WORK / 'recovery/credits_cover_01'
CANDIDATE = HERE / 'candidate_01'
CANDIDATE_MANIFEST = CANDIDATE / 'core_manifest_01.json'
CANDIDATE_SHA = '3195CA9A49E1D0C6DDCC08DE5868C59EBE47DCD9E5D5C73D07B3736EA6D33AAA'
PACKAGE = CANDIDATE / 'package'
COMPILE = CANDIDATE / 'compile_01/assessment.json'
COMPILED = CANDIDATE / 'compile_01/cache/compiled.redscripts'
REVIEW = WORKSPACE / 'diagnostics/credits_flash_20261116_03/compiled_review_01/assessment.json'
REVIEW_SHA = '0F13B92CCF7F4988C54A01CC6D1F15BCC721423EADC6970B7089DA8996ADF6A6'
OLD_WORK = PREDECESSOR.parents[1]
TEMPLATE = OLD_WORK / 'deploy_core.ps1'
TEMPLATE_SHA = '5D3CBB145F66E50279292EC659251A09E969E2CBCDB06C0C92623ABADCF3744C'
PS = Path('C:/Users/Ayong/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
EPOCH = 'LC5_CREDITS_COVER'
PREVIOUS_EPOCH = 'WO1_STREET_OVERLAP_CLEANUP'
SCHEMA = f'PTFR_{EPOCH}_CORE_V1'
BINDINGS = 'bin/x64/plugins/cyber_engine_tweaks/bindings.json'
PROCESS_NAMES = ['Cyberpunk2077', 'REDlauncher', 'REDprelauncher']
SCOPE = 'Install the staged Tower credits cover by replacing the existing consolidated loading-cover script.'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def pin(path, digest):
    check_plain(path)
    assert sha256(path) == digest, path
    return {'path': str(path), 'sha256': digest}


def prepare():
    proofs = [pin(PREDECESSOR, PREDECESSOR_SHA), pin(CANDIDATE_MANIFEST, CANDIDATE_SHA), pin(REVIEW, REVIEW_SHA)]
    baseline, candidate, review = map(read, (PREDECESSOR, CANDIDATE_MANIFEST, REVIEW))
    assert baseline['core_epoch'] == PREVIOUS_EPOCH
    assert candidate['predecessor_sha256'] == PREDECESSOR_SHA and candidate['status'] == 'STAGED_OFFLINE'
    assert review['candidate_manifest_sha256'] == CANDIDATE_SHA and review['status'] == 'PASS'
    assert len(review['checks']) == 8 and all(review['checks'].values())
    proofs.append(pin(COMPILE, candidate['compile_assessment_sha256']))
    compiled = read(COMPILE)
    assert compiled['status'] == 'PASS' and compiled['compiled_sha256'] == review['compiled_sha256']
    proofs.append(pin(COMPILED, compiled['compiled_sha256']))
    game = Path(baseline['game_root'])
    assert set(inventory(game)) == {Path(p) for p in compiled['installed_inputs'] if p.lower().endswith('.reds')}
    for path, digest in compiled['installed_inputs'].items():
        pin(Path(path), digest)
    assert compiled['source_count'] == len(compiled['staged_sources']) == 149
    assert compiled['changed_sources'] == candidate['changed_paths'] == [RELATIVE_SCRIPT]

    before = {row['path']: row for row in baseline['core_files']}
    after = {row['path']: row for row in candidate['core_files']}
    assert len(before) == len(after) == 51 and before.keys() == after.keys()
    assert list(p for p in before if before[p] != after[p]) == [RELATIVE_SCRIPT]
    verify_rows(game, baseline['core_files'])
    verify_rows(PACKAGE, candidate['core_files'])
    assert compiled['staged_sources'][RELATIVE_SCRIPT] == after[RELATIVE_SCRIPT]['sha256']
    required = candidate['required_files'] + [file_record(game, BINDINGS) | {'active_only': False}]
    assert len({r['path'] for r in required}) == len(required)
    verify_rows(game, required)
    files = [
        {
            'path': path,
            'before': before[path]['sha256'],
            'before_bytes': before[path]['bytes'],
            'after': after[path]['sha256'],
            'after_bytes': after[path]['bytes'],
        }
        for path in before
    ]
    authorization = DEPLOYMENT / 'authorization_01.json'
    check_plain(WORK)
    WORK.mkdir(exist_ok=False)
    DEPLOYMENT.mkdir()
    write_json(authorization, {'user_request': 'install pls', 'scope': SCOPE, 'candidate_manifest_sha256': CANDIDATE_SHA})
    proofs.append(pin(authorization, sha256(authorization)))
    write_json(MANIFEST, {
        'schema': SCHEMA,
        'component': 'Core',
        'source_epoch': EPOCH,
        'predecessor_epoch': PREVIOUS_EPOCH,
        'scope': SCOPE,
        'game_root': baseline['game_root'],
        'save_root': baseline['save_root'],
        'package_root': str(PACKAGE),
        'process_names': PROCESS_NAMES,
        'files': files,
        'changing_paths': [RELATIVE_SCRIPT],
        'required_files': required,
        'protected_saves': [],
        'working_save_files': [],
        'zip': '',
        'zip_sha256': None,
        'proofs': proofs,
        'compile_inputs': compiled['installed_inputs'],
    })
    pin(TEMPLATE, TEMPLATE_SHA)
    script = TEMPLATE.read_text(encoding='utf-8-sig')
    replacements = [
        ('D702386BF785130F80AE8ACEAD97DF9A92D253A5D2DBEC35098AADCA2AEC5CC1', sha256(MANIFEST)),
        ('PTFR_WO1_STREET_OVERLAP_CLEANUP_CORE_V1', SCHEMA),
        ("source_epoch -cne 'WO1_STREET_OVERLAP_CLEANUP'", f"source_epoch -cne '{EPOCH}'"),
        ("predecessor_epoch -cne 'KM3_KOLD_PREPARED_ENTRY'", f"predecessor_epoch -cne '{PREVIOUS_EPOCH}'"),
        ('recovery/street_overlap_01', 'recovery/credits_cover_01'),
        ("$wanted=@('archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl','r6/scripts/PTFR_Consolidated/PTFR_MistyViktorAuto.reds')",
         f"$wanted=@('{RELATIVE_SCRIPT}')"),
        ('$changes.Count -ne 3 -or', '$changes.Count -ne 1 -or'),
        ('Street cleanup three-file scope drift', 'Credits cover one-file scope drift'),
        ('# Install the qualified street-cleanup archive, XL entry and existing driver update.',
         '# Install the qualified credits cover script after an exact baseline check.'),
    ]
    for old, new in replacements:
        assert script.count(old) == 1, old
        script = script.replace(old, new, 1)
    with INSTALLER.open('x', encoding='utf-8', newline='\r\n') as file:
        file.write(script)
    write_json(WORK / 'installer_adaptation.json', {
        'template': str(TEMPLATE),
        'template_sha256': TEMPLATE_SHA,
        'installer_sha256': sha256(INSTALLER),
        'replacements': replacements,
    })
    print(f'Prepared the verified one-file update with {len(required)} protected files.')


def fixtures():
    manifest = read(MANIFEST)
    roots = WORK / 'fixtures/deployment_01'
    roots.mkdir(parents=True, exist_ok=False)
    cases = {
        'rollback': [
            ('Install', 'INSTALLED_VERIFIED'), ('Verify', 'VERIFIED_AFTER'),
            ('ValidateRollback', 'ROLLBACK_READY'), ('Rollback', 'ROLLED_BACK_VERIFIED'),
            ('Verify', 'VERIFIED_BEFORE', '-ExpectedState', 'Before'),
        ],
        'crash_after_stage': [
            ('Install', 72, '-FailurePoint', 'CrashAfterStage'),
            ('Recover', 'RECOVERED_BEFORE'), ('Verify', 'VERIFIED_BEFORE', '-ExpectedState', 'Before'),
        ],
        'crash_after_replace': [
            ('Install', 72, '-FailurePoint', 'CrashAfterFirstReplace'),
            ('Recover', 'RECOVERED_BEFORE'), ('Verify', 'VERIFIED_BEFORE', '-ExpectedState', 'Before'),
        ],
        'game_running': [('Install', 1, '-FixtureProcesses', 'Cyberpunk2077')],
    }
    results = []
    for case, operations in cases.items():
        root = roots / case
        game, saves, package = (root / name for name in ('game', 'saves', 'package'))
        data = deepcopy(manifest)
        data.update(game_root=str(game), save_root=str(saves), package_root=str(package), proofs=[], compile_inputs={})
        for row in data['files']:
            relative = row['path']
            old, new = game / relative, package / relative
            old.parent.mkdir(parents=True, exist_ok=True)
            new.parent.mkdir(parents=True, exist_ok=True)
            if case == 'rollback':
                shutil.copyfile(Path(manifest['game_root']) / relative, old)
                shutil.copyfile(PACKAGE / relative, new)
                assert (sha256(old), sha256(new)) == (row['before'], row['after'])
            else:
                old.write_text('before ' + relative, encoding='utf-8')
                new.write_text(('after ' if relative == RELATIVE_SCRIPT else 'before ') + relative, encoding='utf-8')
                row.update(before=sha256(old), before_bytes=old.stat().st_size,
                           after=sha256(new), after_bytes=new.stat().st_size)
        for row in data['required_files']:
            path = game / row['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(row['path'], encoding='utf-8')
            row.update(bytes=path.stat().st_size, sha256=sha256(path))
        saved = saves / 'FixtureSave/sav.dat'
        saved.parent.mkdir(parents=True)
        saved.write_bytes(b'preserved save')
        external = game / 'other_mod.dat'
        external.write_bytes(b'preserved external file')
        fixture = root / 'manifest.json'
        write_json(fixture, data)
        for action, expected, *options in operations:
            result = subprocess.run(
                [str(PS), '-NoProfile', '-File', str(INSTALLER), '-Action', action,
                 '-FixtureRoot', str(root), '-FixtureManifest', str(fixture),
                 '-FixtureManifestSHA', sha256(fixture), *options],
                capture_output=True, encoding='utf-8', errors='replace', timeout=55,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if isinstance(expected, int):
                assert result.returncode == expected, (case, action, result.stdout, result.stderr)
                if case == 'game_running':
                    assert 'Game or REDlauncher must be closed naturally' in result.stderr
                status = None
            else:
                assert result.returncode == 0, (case, action, result.stdout, result.stderr)
                status = json.loads(result.stdout)['status']
                assert status == expected, (case, action, status)
            results.append({'case': case, 'action': action, 'status': status, 'exit_code': result.returncode})
        assert all(sha256(game / row['path']) == row['before'] for row in data['files'])
        verify_rows(game, data['required_files'])
        assert saved.read_bytes() == b'preserved save' and external.read_bytes() == b'preserved external file'
        assert not any((root / 'recovery/core/stage').rglob('*.reds'))
        if case == 'game_running':
            assert not (root / 'recovery').exists()
        print(f'{case} passed', flush=True)
    fixture_result = WORK / 'fixture_results.json'
    scope_review = WORK / 'scope_review.json'
    write_json(fixture_result, {'status': 'PASS', 'installer_sha256': sha256(INSTALLER), 'actions': results})
    write_json(scope_review, {'scope': SCOPE, 'changed_paths': [RELATIVE_SCRIPT], 'manifest_sha256': sha256(MANIFEST)})
    write_json(WORK / 'readiness.json', {
        'status': 'READY_NOT_INSTALLED',
        'manifest_sha256': sha256(MANIFEST),
        'installer_sha256': sha256(INSTALLER),
        'fixture_result': fixture_result.name,
        'fixture_result_sha256': sha256(fixture_result),
        'scope_review': scope_review.name,
        'scope_review_sha256': sha256(scope_review),
    })
    print(f'{len(cases)} fixture cases and {len(results)} fixture actions passed.')


def record():
    baseline, manifest = read(PREDECESSOR), read(MANIFEST)
    receipt = RECOVERY / 'journal.json'
    envelope = read(receipt)
    body = envelope['payload_json']
    assert hashlib.sha256(body.encode('utf-8')).hexdigest().upper() == envelope['payload_sha256']
    journal = json.loads(body)
    assert journal['manifest_sha256'] == sha256(MANIFEST) and journal['state'] == 'INSTALLED_VERIFIED'
    assert journal['completed_paths'] == [RELATIVE_SCRIPT]
    assert read(DEPLOYMENT / 'verify.json')['status'] == 'VERIFIED_AFTER'
    assert read(DEPLOYMENT / 'rollback_readiness.json')['status'] == 'ROLLBACK_READY'
    before, after = journal['protection_before'], journal['protection_after']
    assert before['saves']['tree_sha256'] == after['saves']['tree_sha256']
    assert before['unmanaged']['tree_sha256'] == after['unmanaged']['tree_sha256']
    assert before['dependencies'] == after['dependencies']
    assert journal['save_writes'] == journal['game_launches'] == 0
    saves = sum(row['kind'] == 'file' for row in after['saves']['files'])
    game = Path(manifest['game_root'])
    files = [{'path': row['path'], 'bytes': row['after_bytes'], 'sha256': row['after']} for row in manifest['files']]
    verify_rows(game, files + manifest['required_files'])
    verify_rows(RECOVERY / 'old', [row for row in baseline['core_files'] if row['path'] == RELATIVE_SCRIPT])
    authorization = DEPLOYMENT / 'authorization_01.json'
    installed = {
        'schema': 'PTFR_INSTALLED_CONSOLIDATED_LC5_V1',
        'game_root': manifest['game_root'],
        'save_root': manifest['save_root'],
        'recorded_utc': journal['updated_utc'],
        'recorded_date': datetime.fromisoformat(journal['updated_utc']).astimezone().date().isoformat(),
        'recorded_timezone': 'America/Toronto',
        'live_restore_enabled': baseline['live_restore_enabled'],
        'exact_resume_status': baseline['exact_resume_status'],
        'legacy_resume_admission': baseline['legacy_resume_admission'],
        'core_epoch': EPOCH,
        'predecessor_epoch': PREVIOUS_EPOCH,
        'authorization': SCOPE,
        'authorization_record': str(authorization),
        'authorization_record_sha256': sha256(authorization),
        'archive_payloads': baseline['archive_payloads'],
        'archive_sha256': baseline['archive_sha256'],
        'archive_source': baseline['archive_source'],
        'core_files': files,
        'required_files': [row for row in manifest['required_files'] if row['path'] != BINDINGS],
        'transaction_only_preserved': [row for row in manifest['required_files'] if row['path'] == BINDINGS],
        'source_candidate': str(CANDIDATE),
        'candidate_manifest_sha256': CANDIDATE_SHA,
        'predecessor_manifest': str(PREDECESSOR),
        'predecessor_manifest_sha256': PREDECESSOR_SHA,
        'core_transaction': str(MANIFEST),
        'core_transaction_sha256': sha256(MANIFEST),
        'installed_receipt': str(receipt),
        'installed_receipt_sha256': sha256(receipt),
        'installation_report': str(DEPLOYMENT / 'install.json'),
        'installation_report_sha256': sha256(DEPLOYMENT / 'install.json'),
        'post_install_verification': str(DEPLOYMENT / 'verify.json'),
        'rollback_readiness': str(DEPLOYMENT / 'rollback_readiness.json'),
        'compile_result': str(COMPILE),
        'compile_sources': read(COMPILE)['source_count'],
        'changed_paths': [RELATIVE_SCRIPT],
        'unchanged_core_paths': len(files) - 1,
        'save_files_preserved': saves,
        'save_tree_sha256': after['saves']['tree_sha256'],
        'unmanaged_tree_sha256': after['unmanaged']['tree_sha256'],
        'gameplay': 'PENDING_CREDITS_RENDERED_HANDOFF_RETEST',
    }
    write_json(DEPLOYMENT / 'installed_manifest_01.json', installed)
    print(f'Installed and verified {len(files)} Core paths, {len(manifest["required_files"])} protected files, '
          f'and {saves} preserved save files. Rollback ready.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'fixtures', 'record'))
    actions = {'prepare': prepare, 'fixtures': fixtures, 'record': record}
    actions[parser.parse_args().action]()
