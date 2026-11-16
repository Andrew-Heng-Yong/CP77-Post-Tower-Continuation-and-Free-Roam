"""Record the authorized TP1 install only after verification and preservation checks."""
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import json,subprocess
from capture import HERE,BASELINE,plain,read,sha,write
from prepare_deployment import EPOCH,BEFORE,CHANGES,ARCHIVE,PACKAGE,MANIFEST,INSTALLER,DEPLOYMENT,PS
RECOVERY=HERE/'recovery/core_presentation_tp1_01'
AUTH=DEPLOYMENT/'authorization_01.json'

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
        'core_epoch': EPOCH, 'predecessor_epoch': BEFORE, 'authorization': read(AUTH)['authorized_scope'], 'authorization_record': str(AUTH), 'authorization_record_sha256': sha(AUTH),
        'archive_payloads': 1742, 'archive_sha256': sha(game / ARCHIVE),
        'archive_source': previous['archive_source'], 'core_files': files, 'required_files': manifest['required_files'],
        'source_candidate': str(PACKAGE.parent), 'predecessor_manifest': str(BASELINE), 'predecessor_manifest_sha256': sha(BASELINE),
        'core_transaction': str(MANIFEST), 'core_transaction_sha256': sha(MANIFEST),
        'installed_receipt': str(RECOVERY / 'journal.json'), 'installed_receipt_sha256': sha(RECOVERY / 'journal.json'),
        'post_install_verification': str(DEPLOYMENT / 'verify.json'), 'rollback_readiness': str(DEPLOYMENT / 'rollback_readiness.json'),
        'compile_result': str(HERE / 'compile_02/result.json'), 'compile_sources': 148,
        'changed_paths': sorted(CHANGES), 'unchanged_core_paths': 49, 'save_files_preserved': count,
        'save_tree_sha256': after['saves']['tree_sha256'], 'gameplay': 'PENDING_FPP_HANDBACK_AND_BLACKOUT_OBSERVATION'}
    write(DEPLOYMENT / 'installed_manifest_01.json', installed)
    print(f'INSTALLED_VERIFIED: 51 Core paths, 26 dependencies, {count} save files preserved; rollback ready.')

if __name__=='__main__':
    assert sha(AUTH)=='E02DFB9A73A0D57DDBA225D18C40E8CB8E3E7C199E49CE99DF1A8E76FD671D26'
    assert read(AUTH)['manifest_sha256']==sha(MANIFEST)
    record()
