from pathlib import Path
import hashlib
import json
import shutil

here = Path(__file__).resolve().parent
candidate = here / 'candidate_01'
package = candidate / 'package'
game = Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')
probe = here / 'reds_module_probe_01'
inventory = json.loads((here / 'inventory_archives_01.json').read_text(encoding='utf-8'))
xl = json.loads((candidate / 'build_xl_01.json').read_text(encoding='utf-8'))
archive = json.loads((candidate / 'build_archive_02.json').read_text(encoding='utf-8'))
reds = json.loads((candidate / 'test_reds_modules_01.json').read_text(encoding='utf-8'))
assert (inventory['archive_count'], xl['phase_count'], archive['effective_members'], reds['merged_sources']) == (25, 742, 1153, 46)

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest().upper()

current = {}
def add_current(path):
    relative = path.relative_to(game).as_posix()
    assert relative not in current
    current[relative] = {'path': relative, 'sha256': sha(path), 'bytes': path.stat().st_size}

for row in inventory['archives']:
    add_current(Path(row['archive']))
for row in xl['sources']:
    add_current(game / 'archive/pc/mod' / row['source'])
scripts_root = game / 'r6/scripts'
scripts = [path for path in scripts_root.rglob('*.reds') if any(part.startswith(('PTFR_', 'TowerContinued_')) for part in path.relative_to(scripts_root).parts)]
assert len(scripts) == 76
for path in scripts:
    add_current(path)
for mod in ('PTFR_HistorySnapshotHS1', 'PTFR_PreAlpha'):
    add_current(game / f'bin/x64/plugins/cyber_engine_tweaks/mods/{mod}/init.lua')
add_current(game / 'r6/tweaks/TowerContinued_PreAlpha.yaml')
assert len(current) == 127

for row in json.loads((probe / 'result.json').read_text(encoding='utf-8'))['rows']:
    source = probe / 'scripts' / row['path']
    dest = package / 'r6/scripts/PTFR_Consolidated' / Path(row['path']).name
    assert not dest.exists()
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    assert sha(dest) == row['sha256']
for relative in (
    'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/init.lua',
    'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_PreAlpha/init.lua',
    'r6/tweaks/TowerContinued_PreAlpha.yaml',
):
    dest = package / relative
    assert not dest.exists()
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(game / relative, dest)
    assert sha(dest) == current[relative]['sha256']

members = []
for path in package.rglob('*'):
    if path.is_file():
        relative = path.relative_to(package).as_posix()
        members.append({'path': relative, 'sha256': sha(path), 'bytes': path.stat().st_size})
members.sort(key=lambda x: x['path'])
assert len(members) == 51
assert sum(row['path'].endswith('.archive') for row in members) == 1
assert sum(row['path'].endswith('.archive.xl') for row in members) == 1
assert sum(row['path'].endswith('.reds') for row in members) == 46
assert sum(row['path'].endswith('.lua') for row in members) == 2
assert sum(row['path'].endswith('.yaml') for row in members) == 1

report = {'status': 'FULL_PTFR_127_TO_51_STAGED_PACKAGE_NOT_INSTALLED', 'game_root': str(game), 'current_files': sorted(current.values(), key=lambda x: x['path']), 'package_files': members, 'retired_existing_paths': len(set(current) - {row['path'] for row in members}), 'unchanged_path_replacements': len(set(current) & {row['path'] for row in members}), 'archive_members': 1153, 'quest_phase_registrations': 742, 'script_modules': 46, 'excluded_development_cet_mods': ['PTFR_CyberpsychoP1', 'PTFR_SideJobsCaptureS23', 'PTFR_SideJobsCaptureS26'], 'game_writes': 0, 'save_writes': 0}
dest = candidate / 'package_manifest_01.json'
assert not dest.exists()
dest.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k not in ('current_files', 'package_files')}))
