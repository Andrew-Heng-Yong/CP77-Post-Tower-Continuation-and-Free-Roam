"""Prepare and record the requested global-latest HS4 installation; no game launch."""
import argparse
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED
from build import HERE, BASE, BASELINE, RED, LUA, ARCHIVE, baseline, read, sha, write, one, plain

EPOCH = 'HS4_GLOBAL_LATEST_HISTORY'
BEFORE = 'HS3_NATIVE_HISTORY_CAPTURE'
SCHEMA = 'PTFR_HS4_GLOBAL_LATEST_HISTORY_CORE_V1'
CHANGES = {RED, LUA}
PACKAGE = HERE / 'candidate_02/package'
MANIFEST = HERE / 'core_manifest_01.json'
INSTALLER = HERE / 'deploy_core.ps1'
DEPLOYMENT = HERE / 'deployment_01'
RECOVERY = HERE / 'recovery/core_global_latest_hs4_01'
PS = Path(r'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')


def exclusive_text(path, text):
    with path.open('x', encoding='utf-8', newline='\n') as out:
        out.write(text)


def run_fixtures(manifest):
    fixtures = HERE / 'fixtures/deployment_01'
    assert not fixtures.exists()
    cases = {
        'rollback': [('Install', 'INSTALLED_VERIFIED'), ('Verify', 'VERIFIED_AFTER'),
                     ('ValidateRollback', 'ROLLBACK_READY'), ('Rollback', 'ROLLED_BACK_VERIFIED'),
                     ('Verify', 'VERIFIED_BEFORE', '-ExpectedState', 'Before')],
        'crash_first': [('Install', 72, '-FailurePoint', 'CrashAfterFirstReplace'),
                        ('Recover', 'RECOVERED_BEFORE'), ('Verify', 'VERIFIED_BEFORE', '-ExpectedState', 'Before')],
        'crash_second': [('Install', 72, '-FailurePoint', 'CrashAfterSecondReplace'),
                         ('Recover', 'RECOVERED_BEFORE'), ('Verify', 'VERIFIED_BEFORE', '-ExpectedState', 'Before')],
        'crash_stage': [('Install', 72, '-FailurePoint', 'CrashAfterStage'),
                        ('Recover', 'RECOVERED_BEFORE'), ('Verify', 'VERIFIED_BEFORE', '-ExpectedState', 'Before')],
        'crash_receipt': [('Install', 72, '-FailurePoint', 'CrashBeforeReceipt'),
                          ('Recover', 'RECOVERED_BEFORE'), ('Verify', 'VERIFIED_BEFORE', '-ExpectedState', 'Before')],
        'game_running': [('Install', 1, '-FixtureProcesses', 'Cyberpunk2077')],
    }
    actions = []
    for case, operations in cases.items():
        root = fixtures / case
        game, saves, package = (root / p for p in ('game', 'saves', 'package'))
        data = deepcopy(manifest)
        data.update(game_root=str(game), save_root=str(saves), package_root=str(package),
                    proofs=[], compile_inputs={}, working_save_files=[], protected_saves=[], zip='', zip_sha256=None)
        for row in data['files']:
            rel = row['path']; old, new = game / rel, package / rel
            old.parent.mkdir(parents=True, exist_ok=True); new.parent.mkdir(parents=True, exist_ok=True)
            if case == 'rollback':
                shutil.copyfile(Path(manifest['game_root']) / rel, old)
                shutil.copyfile(PACKAGE / rel, new)
                assert (sha(old), sha(new)) == (row['before'], row['after'])
            else:
                old.write_text('old ' + rel, encoding='utf-8')
                new.write_text(('new ' if rel in CHANGES else 'old ') + rel, encoding='utf-8')
                row.update(before=sha(old), before_bytes=old.stat().st_size, after=sha(new), after_bytes=new.stat().st_size)
        for row in data['required_files']:
            path = game / row['path']; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(row['path'], encoding='utf-8'); row.update(sha256=sha(path), bytes=path.stat().st_size)
        saved = saves / 'FixtureSave/sav.dat'; saved.parent.mkdir(parents=True); saved.write_bytes(b'preserved save')
        external = game / 'ExternalMod/keep.dat'; external.parent.mkdir(); external.write_bytes(b'preserved external file')
        fixture = root / 'manifest.json'; write(fixture, data)
        for action, expected, *flags in operations:
            result = subprocess.run([str(PS), '-NoProfile', '-File', str(INSTALLER), '-Action', action,
                '-FixtureRoot', str(root), '-FixtureManifest', str(fixture), '-FixtureManifestSHA', sha(fixture), *flags],
                capture_output=True, encoding='utf-8', errors='replace', timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
            if isinstance(expected, int):
                assert result.returncode == expected, (case, action, result.stdout, result.stderr)
                status = None
            else:
                assert result.returncode == 0, (case, action, result.stdout, result.stderr)
                status = json.loads(result.stdout)['status']; assert status == expected
            actions.append({'fixture': case, 'action': action, 'status': status, 'returncode': result.returncode})
        assert all(sha(game / r['path']) == r['before'] for r in data['files'])
        assert all(sha(game / r['path']) == r['sha256'] for r in data['required_files'])
        assert saved.read_bytes() == b'preserved save' and external.read_bytes() == b'preserved external file'
        assert not list((root / 'recovery').rglob('*.reds')) or case != 'game_running'
        if case == 'game_running': assert not (root / 'recovery').exists()
    return actions


def prepare():
    assert not MANIFEST.exists() and not INSTALLER.exists() and not DEPLOYMENT.exists()
    previous, game = baseline()
    selected = read(HERE / 'checkpoint.json')
    assert selected['candidate'] == 'candidate_02' and selected['baseline_manifest_sha256'] == sha(BASELINE)
    for group in ('artifacts', 'sources'):
        for rel, digest in selected[group].items(): assert sha(HERE / rel) == digest, rel
    candidate = read(HERE / 'candidate_02/manifest.json')
    compiled = read(HERE / 'compile_02/result.json')
    assert compiled['status'] == 'PASS' and compiled['source_count'] == 148
    assert compiled['staged_hashes'][RED] == sha(PACKAGE / RED)
    # No archive resource, ArchiveXL registration or generated phase node changes.
    for rel in (ARCHIVE, ARCHIVE+'.xl'):
        assert sha(PACKAGE/rel)==sha(game/rel)
    write(HERE/'unchanged_resources.json', {'status':'PASS_UNCHANGED_ARCHIVE_AND_XL',
        'files':{p:sha(PACKAGE/p) for p in (ARCHIVE,ARCHIVE+'.xl')},
        'baseline_manifest_sha256':sha(BASELINE), 'resource_or_node_additions':0})
    after_by_path = {r['path']: r for r in candidate['core_files']}
    assert set(after_by_path) == {r['path'] for r in previous['core_files']}
    files = []
    for row in previous['core_files']:
        path = PACKAGE / row['path']; plain(path); staged = after_by_path[row['path']]
        assert sha(path) == staged['sha256'] and path.stat().st_size == staged['bytes']
        files.append({'path': row['path'], 'before': row['sha256'], 'before_bytes': row['bytes'],
                      'after': staged['sha256'], 'after_bytes': staged['bytes']})
    assert len(files) == 51 and {r['path'] for r in files if r['before'] != r['after']} == CHANGES
    for folder in (DEPLOYMENT, HERE / 'fixtures', HERE / 'recovery'):
        folder.mkdir(); exclusive_text(folder / '.gitignore', '*\n!.gitignore\n!REPORT.md\n!installed_manifest_01.json\n')
    zip_path = DEPLOYMENT / 'HS4_candidate_02.zip'
    with ZipFile(zip_path, 'x', compression=ZIP_DEFLATED, compresslevel=6) as z:
        for row in files: z.write(PACKAGE / row['path'], row['path'])
    with ZipFile(zip_path, 'r') as z:
        assert set(z.namelist()) == set(after_by_path) and len(z.namelist()) == 51 and z.testzip() is None
        assert all(sha256(z.read(r['path'])).hexdigest().upper() == r['after'] for r in files)
    write(DEPLOYMENT / 'zip_readback.json', {'status': 'PASS', 'files': 51, 'sha256': sha(zip_path)})
    working = []  # The transaction protects every current save by exact hash.
    template = BASE / 'deploy_core.ps1'
    assert sha(template) == 'D84D6A09FACD7BBC7B7BFBFAA7F8FD7278EB4B20F26879804A4A3195485EBBEB'
    proofs = [BASELINE, HERE / 'checkpoint.json', HERE / 'unchanged_resources.json', DEPLOYMENT / 'zip_readback.json']
    proofs += [HERE / rel for rel in selected['artifacts']]
    manifest = {'schema': SCHEMA, 'component': 'Core', 'source_epoch': EPOCH, 'predecessor_epoch': BEFORE,
        'scope': 'Ongoing user-authorized mod installation/test; follow-up instruction: bruh just use global latest. Update the two snapshot scripts to HS4 candidate_02.',
        'game_root': str(game), 'save_root': previous['save_root'], 'package_root': str(PACKAGE),
        'process_names': read(BASE / 'core_manifest_01.json')['process_names'], 'files': files,
        'changing_paths': sorted(CHANGES), 'required_files': previous['required_files'], 'protected_saves': [],
        'working_save_files': working, 'zip': str(zip_path), 'zip_sha256': sha(zip_path),
        'proofs': [{'path': str(p), 'sha256': sha(p)} for p in proofs],
        'compile_inputs': {str(game / p): h for p, h in compiled['input_pins'].items()}}
    write(MANIFEST, manifest)
    script = template.read_text(encoding='utf-8-sig')
    for old, new in (
        ('# Replace exactly the snapshot REDscript, CET exporter and combined archive.', '# Replace exactly the two snapshot scripts for global-latest loading.'),
        (sha(BASE / 'core_manifest_01.json'), sha(MANIFEST)),
        ('PTFR_HS3_NATIVE_HISTORY_CAPTURE_CORE_V1', SCHEMA),
        ("$manifest.source_epoch -cne 'HS3_NATIVE_HISTORY_CAPTURE'", f"$manifest.source_epoch -cne '{EPOCH}'"),
        ("$manifest.predecessor_epoch -cne 'QP2_QUEST_HISTORY_AUTOLOAD'", f"$manifest.predecessor_epoch -cne '{BEFORE}'"),
        ('recovery/core_history_capture_hs3_01', 'recovery/core_global_latest_hs4_01'),
        ("$wanted=@('archive/pc/mod/zzzz_PTFR_Combined.archive','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/init.lua','r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds')",
         '$wanted=@(' + ','.join("'" + p + "'" for p in sorted(CHANGES)) + ')'),
        ('$changes.Count -ne 3', '$changes.Count -ne 2'),
        ('Core51/three-file HS3 capture scope drift', 'Core51/two-file HS4 global-latest scope drift')):
        script = one(script, old, new)
    exclusive_text(INSTALLER, script)
    actions = run_fixtures(manifest)
    write(HERE / 'fixture_results.json', {'status': 'PASS', 'installer_sha256': sha(INSTALLER), 'actions': actions})
    write(HERE / 'scope_review.json', {'scope': manifest['scope'], 'changed_paths': sorted(CHANGES),
        'manifest_sha256': sha(MANIFEST), 'template_sha256': sha(template), 'gameplay': 'User will test; no game launch'})
    write(HERE / 'readiness.json', {'status': 'READY_NOT_INSTALLED', 'manifest_sha256': sha(MANIFEST),
        'installer_sha256': sha(INSTALLER), 'fixture_result': 'fixture_results.json', 'fixture_result_sha256': sha(HERE / 'fixture_results.json'),
        'scope_review': 'scope_review.json', 'scope_review_sha256': sha(HERE / 'scope_review.json')})
    print(f'Prepared candidate_02: ZIP readback and {len(actions)} deployment fixture actions passed.')


def record():
    previous, manifest, envelope = read(BASELINE), read(MANIFEST), read(RECOVERY / 'journal.json')
    text = envelope['payload_json']; assert sha256(text.encode()).hexdigest().upper() == envelope['payload_sha256']
    journal = json.loads(text)
    assert journal['manifest_sha256'] == sha(MANIFEST) and journal['state'] == 'INSTALLED_VERIFIED'
    assert set(journal['completed_paths']) == CHANGES
    assert read(DEPLOYMENT / 'verify.json')['status'] == 'VERIFIED_AFTER'
    assert read(DEPLOYMENT / 'rollback_readiness.json')['status'] == 'ROLLBACK_READY'
    before, after = journal['protection_before'], journal['protection_after']
    assert before['saves']['tree_sha256'] == after['saves']['tree_sha256']
    assert before['unmanaged']['tree_sha256'] == after['unmanaged']['tree_sha256']
    assert before['dependencies'] == after['dependencies']
    assert journal['save_writes'] == journal['game_launches'] == 0
    game = Path(manifest['game_root'])
    files = [{'path': r['path'], 'bytes': r['after_bytes'], 'sha256': r['after']} for r in manifest['files']]
    for row in files + manifest['required_files']:
        path = game / row['path']; plain(path); assert sha(path) == row['sha256'] and path.stat().st_size == row['bytes']
    count = sum(r['kind'] == 'file' for r in after['saves']['files'])
    # Use Windows' installed timezone database; this Python has no tzdata package.
    stamp = datetime.fromisoformat(journal['updated_utc']).isoformat()
    date_command = "[TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTimeOffset]::Parse('" + stamp + "'),'Eastern Standard Time').ToString('yyyy-MM-dd')"
    date_result = subprocess.run([str(PS), '-NoProfile', '-Command', date_command], capture_output=True,
        encoding='utf-8', check=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
    recorded_date = datetime.strptime(date_result.stdout.strip(), '%Y-%m-%d').date().isoformat()
    installed = {**previous, 'recorded_date': recorded_date, 'recorded_timezone': 'America/Toronto',
        'core_epoch': EPOCH, 'predecessor_epoch': BEFORE, 'authorization': manifest['scope'],
        'archive_payloads': 1740, 'archive_sha256': sha(game / ARCHIVE),
        'archive_source': previous['archive_source'], 'core_files': files, 'required_files': manifest['required_files'],
        'source_candidate': str(PACKAGE.parent), 'predecessor_manifest': str(BASELINE), 'predecessor_manifest_sha256': sha(BASELINE),
        'core_transaction': str(MANIFEST), 'core_transaction_sha256': sha(MANIFEST),
        'installed_receipt': str(RECOVERY / 'journal.json'), 'installed_receipt_sha256': sha(RECOVERY / 'journal.json'),
        'post_install_verification': str(DEPLOYMENT / 'verify.json'), 'rollback_readiness': str(DEPLOYMENT / 'rollback_readiness.json'),
        'compile_result': str(HERE / 'compile_02/result.json'), 'compile_sources': 148,
        'changed_paths': sorted(CHANGES), 'unchanged_core_paths': 49, 'save_files_preserved': count,
        'save_tree_sha256': after['saves']['tree_sha256'], 'gameplay': 'PENDING_USER_GLOBAL_LATEST_LOAD_OBSERVATION'}
    write(DEPLOYMENT / 'installed_manifest_01.json', installed)
    print(f'INSTALLED_VERIFIED: 51 Core paths, 26 dependencies, {count} save files preserved; rollback ready.')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('action', choices=('prepare', 'record')); args = ap.parse_args()
    prepare() if args.action == 'prepare' else record()
