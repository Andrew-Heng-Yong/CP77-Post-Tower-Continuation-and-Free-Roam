import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
ws = here.parent.parent
candidate = here / 'candidate_02'
game = Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')
backup = ws / 'recovery/sidejob_repair_sr1_01'
package = candidate / 'package'

targets = [
    'archive/pc/mod/zzzz_PTFR_SideJobs_SR1.archive',
    'archive/pc/mod/zzzz_PTFR_SideJobs_SR1_Visual2.archive',
    'archive/pc/mod/zzzz_PTFR_SideJobs_SR1_Lipmap.archive',
    'archive/pc/mod/zzzz_PTFR_SideJobs_SR1_Lipmap.archive.xl',
    'r6/scripts/TowerContinued_SideJobs_S29/SideJobsS29.reds',
]

def hash_file(path):
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest().upper()

proofs = [
    ('package_01.json', 'STAGED_PACKED_READBACK_NO_INSTALL'),
    ('package_visual_02.json', 'STAGED_VISUAL_SEVEN_RESOURCE_ARCHIVE_READBACK_NO_INSTALL'),
    ('package_lipmap_01.json', 'STAGED_44_LIPMAP_ARCHIVE_XL_READBACK_NO_INSTALL'),
    ('test_native_01.json', 'PASS_SIX_RESOURCE_SCOPED_SEMANTIC_READBACK_NOT_LIVE'),
    ('test_visual_01.json', 'VISUAL_TWO_RESOURCE_SEMANTIC_PRESERVATION_PASS'),
    ('test_visual_02.json', 'VISUAL_FOUR_ADDITIONAL_SCENES_AND_EXACT_KOLD_WORKSPOT_SEMANTIC_PASS'),
]
for relative, expected in proofs:
    value = json.loads((candidate / relative).read_text(encoding='utf-8'))
    assert value['status'] == expected, relative

files = []
for relative in targets:
    before = hash_file(game / relative)
    after = hash_file(package / relative)
    assert after is not None, relative
    assert (before is not None) == relative.endswith('.reds'), (relative, before)
    files.append({'target': relative, 'before': before, 'after': after})

manifest = {
    'status': 'STAGED_NOT_INSTALLED',
    'game_root': str(game),
    'backup_root': str(backup),
    'files': files,
    'proofs': [{'path': str(candidate / relative), 'sha256': hash_file(candidate / relative)} for relative, _ in proofs],
    'compiled_script_sha256': json.loads((candidate / 'compile_01/result.json').read_text(encoding='utf-8'))['compiled_sha256'],
    'live_result': 'pending',
    'game_writes': 0,
    'save_writes': 0,
}
path = candidate / 'install_manifest_01.json'
assert not path.exists(), 'Manifest exists; create a successor'
path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
(candidate / 'install_manifest_01.json.sha256').write_text(hash_file(path) + '\n', encoding='utf-8')
print(json.dumps({'status': manifest['status'], 'files': len(files), 'replacements': sum(x['before'] is not None for x in files), 'additions': sum(x['before'] is None for x in files), 'manifest_sha256': hash_file(path)}))
