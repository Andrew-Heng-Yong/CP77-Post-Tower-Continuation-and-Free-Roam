from pathlib import Path
import hashlib
import json

here = Path(__file__).resolve().parent
candidate = here / 'candidate_01'
package_manifest = json.loads((candidate / 'package_manifest_01.json').read_text(encoding='utf-8'))
distribution = json.loads((candidate / 'distribution_01.json').read_text(encoding='utf-8'))
assert package_manifest['status'] == 'FULL_PTFR_127_TO_51_STAGED_PACKAGE_NOT_INSTALLED'
assert distribution['status'] == 'ONE_ZIP_51_FILE_FULL_PTFR_READBACK_PASS_NOT_INSTALLED'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest().upper()

proofs = [
    here / 'inventory_archives_01.json',
    here / 'external_collisions_01.json',
    candidate / 'build_archive_02.json',
    candidate / 'build_xl_01.json',
    candidate / 'test_reds_modules_01.json',
    candidate / 'package_manifest_01.json',
    candidate / 'distribution_01.json',
]
for row in package_manifest['current_files']:
    assert sha(Path(package_manifest['game_root']) / row['path']) == row['sha256']
for row in package_manifest['package_files']:
    assert sha(candidate / 'package' / row['path']) == row['sha256']

manifest = {
    'status': 'FULL_PTFR_127_TO_51_LOCAL_DEPLOYMENT_STAGED',
    'game_root': package_manifest['game_root'],
    'backup_root': str((here.parent.parent / 'recovery/full_consolidation_v1_01').resolve()),
    'old_files': package_manifest['current_files'],
    'new_files': package_manifest['package_files'],
    'proofs': [{'path': str(path.resolve()), 'sha256': sha(path)} for path in proofs],
    'zip_sha256': distribution['zip_sha256'],
    'game_writes': 0,
    'save_writes': 0,
    'live_result': 'pending',
}
dest = candidate / 'install_manifest_01.json'
assert not dest.exists()
dest.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
(candidate / 'install_manifest_01.json.sha256').write_text(sha(dest) + '\n', encoding='utf-8')
print(json.dumps({'status': manifest['status'], 'old': len(manifest['old_files']), 'new': len(manifest['new_files']), 'manifest_sha256': sha(dest)}))
