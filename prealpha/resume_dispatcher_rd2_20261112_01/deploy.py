"""RD2 fixture runner and installation recorder; no game launch."""
import argparse
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
from capture import HERE, BASELINE, plain, read, sha, write
from prepare_deployment import EPOCH, BEFORE, CHANGES, ARCHIVE, PACKAGE, MANIFEST, INSTALLER, DEPLOYMENT, PS
RECOVERY=HERE/'recovery/core_resume_rd2_01'

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
        'archive_payloads': 1742, 'archive_sha256': sha(game / ARCHIVE),
        'archive_source': str(HERE/'archive_01/archive_source'), 'core_files': files, 'required_files': manifest['required_files'],
        'source_candidate': str(PACKAGE.parent), 'predecessor_manifest': str(BASELINE), 'predecessor_manifest_sha256': sha(BASELINE),
        'core_transaction': str(MANIFEST), 'core_transaction_sha256': sha(MANIFEST),
        'installed_receipt': str(RECOVERY / 'journal.json'), 'installed_receipt_sha256': sha(RECOVERY / 'journal.json'),
        'post_install_verification': str(DEPLOYMENT / 'verify.json'), 'rollback_readiness': str(DEPLOYMENT / 'rollback_readiness.json'),
        'compile_result': str(HERE / 'compile_01/result.json'), 'compile_sources': 148,
        'changed_paths': sorted(CHANGES), 'unchanged_core_paths': 48, 'save_files_preserved': count,
        'save_tree_sha256': after['saves']['tree_sha256'], 'gameplay': 'PENDING_THE_GIG_EARNED_REWARD_PLAYTEST'}
    write(DEPLOYMENT / 'installed_manifest_01.json', installed)
    print(f'INSTALLED_VERIFIED: 51 Core paths, 26 dependencies, {count} save files preserved; rollback ready.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('fixtures','record'));args=parser.parse_args()
    if args.action=='record':record()
    else:
        actions=run_fixtures(read(MANIFEST))
        write(HERE/'fixture_results.json',{'status':'PASS','installer_sha256':sha(INSTALLER),'actions':actions})
        write(HERE/'scope_review.json',{'scope':read(MANIFEST)['scope'],'changed_paths':sorted(CHANGES),
            'manifest_sha256':sha(MANIFEST),'gameplay':'User will test; no game launch'})
        write(HERE/'readiness.json',{'status':'READY_NOT_INSTALLED','manifest_sha256':sha(MANIFEST),
            'installer_sha256':sha(INSTALLER),'fixture_result':'fixture_results.json','fixture_result_sha256':sha(HERE/'fixture_results.json'),
            'scope_review':'scope_review.json','scope_review_sha256':sha(HERE/'scope_review.json')})
        print(f'PASS: {len(actions)} deployment/recovery fixture actions; real installation not started.')
