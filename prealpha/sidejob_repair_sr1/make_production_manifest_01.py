import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
prod = here / 'production_01'
package = prod / 'package'
game = Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')
backup = here.parent.parent / 'recovery/sidejob_repair_sr1_production_01'
build = json.loads((prod / 'build_01.json').read_text(encoding='utf-8'))
assert build['status'] == 'THREE_FILE_PRODUCTION_CANDIDATE_READBACK_NOT_INSTALLED'

def hash_file(path):
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest().upper()

targets = [
    'archive/pc/mod/00000000_TowerContinued_SideJobs_S29.archive',
    'archive/pc/mod/00000000_TowerContinued_SideJobs_S29.archive.xl',
    'r6/scripts/TowerContinued_SideJobs_S29/SideJobsS29.reds',
]
files = []
for relative in targets:
    before = hash_file(game / relative)
    previous = hash_file(prod / 'archived_previous' / relative)
    after = hash_file(package / relative)
    assert before is not None and before == previous and after is not None, relative
    files.append({'target': relative, 'before': before, 'after': after})

xl_before = (game / targets[1]).read_text(encoding='utf-8')
xl_after = (package / targets[1]).read_text(encoding='utf-8')
lipmap_line = 'localization:\n  lipmaps:\n    en-us: towercontinued\\sidejob_repair_sr1\\en-us.lipmap\n'
assert xl_after == xl_before + lipmap_line, 'ArchiveXL diff changed beyond lipmap registration'
assert sum(1 for x in targets if x.endswith('.archive')) == 1
assert len(files) == 3

proofs = [
    here / 'candidate_02/test_native_01.json',
    here / 'candidate_02/test_visual_01.json',
    here / 'candidate_02/test_visual_02.json',
    here / 'candidate_02/test_lipmap_01.json',
    here / 'candidate_02/compile_01/result.json',
    prod / 'build_01.json',
]
manifest = {
    'status': 'THREE_FILE_PRODUCTION_STAGED_NOT_INSTALLED',
    'game_root': str(game),
    'backup_root': str(backup),
    'files': files,
    'proofs': [{'path': str(p.resolve()), 'sha256': hash_file(p)} for p in proofs],
    'archived_previous': str((prod / 'archived_previous').resolve()),
    'game_writes': 0,
    'save_writes': 0,
    'live_result': 'pending',
}
path = prod / 'install_manifest_01.json'
assert not path.exists(), 'Manifest exists; use successor'
path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
(prod / 'install_manifest_01.json.sha256').write_text(hash_file(path) + '\n', encoding='utf-8')
print(json.dumps({'status': manifest['status'], 'files': 3, 'replacements': 3, 'archive_xl_append_only': True, 'manifest_sha256': hash_file(path)}))
