import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
candidate = here / 'candidate_01'
manifest = json.loads((candidate / 'install_manifest_01.json').read_text(encoding='utf-8'))
save_baseline = json.loads((candidate / 'save_baseline_01.json').read_text(encoding='utf-8'))
game = Path(manifest['game_root'])


def sha(path):
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest().upper()


old = {row['path']: row['sha256'] for row in manifest['old_files']}
new = {row['path']: row['sha256'] for row in manifest['new_files']}
assert len(old) == 127 and len(new) == 51
for relative, expected in new.items():
    assert sha(game / relative) == expected, relative
for relative in old.keys() - new.keys():
    assert not (game / relative).exists(), relative
for row in save_baseline['files']:
    assert sha(Path(row['path'])) == row['sha256'], row['path']

proof = {
    'status': 'FULL_PTFR_LOCAL_INSTALL_AND_SAVE_HASHES_PASS',
    'retired_files_absent': len(old.keys() - new.keys()),
    'combined_files_verified': len(new),
    'save_files_unchanged': len(save_baseline['files']),
    'game_launched': False,
    'gameplay_live_result': 'pending',
    'save_writes': 0,
}
(candidate / 'postinstall_01.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps(proof))
