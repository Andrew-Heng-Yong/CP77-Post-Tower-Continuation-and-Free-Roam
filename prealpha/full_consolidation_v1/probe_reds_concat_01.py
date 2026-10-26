from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess

here = Path(__file__).resolve().parent
ws = here.parent.parent
game = Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')
out = here / 'reds_concat_probe_01'
assert not out.exists()
sources = out / 'scripts'
cache = out / 'cache'
cache.mkdir(parents=True)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

ptfr = []
deferred = []
for label, root in [
    ('game', game / 'r6/scripts'),
    ('Codeware', game / 'red4ext/plugins/Codeware/Scripts'),
    ('ArchiveXL', game / 'red4ext/plugins/ArchiveXL/Scripts'),
    ('TweakXL', game / 'red4ext/plugins/TweakXL/Scripts'),
    ('mod_settings', game / 'red4ext/plugins/mod_settings'),
]:
    for path in root.rglob('*.reds'):
        relative = path.relative_to(root)
        if label == 'game' and any(x.startswith(('PTFR_', 'TowerContinued_')) for x in relative.parts):
            ptfr.append(path)
            continue
        dest = sources / label / relative
        if 'EquipmentEx' in path.parts:
            deferred.append((path, dest))
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
assert len(ptfr) == 76
sections = []
for path in sorted(ptfr, key=lambda p: str(p.relative_to(game)).lower()):
    text = path.read_text(encoding='utf-8-sig')
    sections.append('// PTFR SOURCE: ' + str(path.relative_to(game)).replace('\\', '/') + '\n' + text.rstrip() + '\n')
combined = '\n'.join(sections)
dest = sources / 'game/r6/scripts/PTFR_Consolidated/PTFR_All.reds'
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(combined, encoding='utf-8')
for name in ('final.redscripts', 'final.redscripts.ts'):
    shutil.copyfile(game / 'r6/cache' / name, cache / name)
cli = ws / 'diagnostics/mod_updates_20261023_01/downloads/redscript-cli.exe'
r = subprocess.run([str(cli), 'compile', '-s', str(sources), '-b', str(cache / 'final.redscripts'), '-o', str(cache / 'cli.redscripts')], capture_output=True, text=True, timeout=240)
log = r.stdout + r.stderr
(out / 'cli.log').write_text(log, encoding='utf-8')
status = 'CLI_CONCAT_PASS' if r.returncode == 0 and 'Output successfully saved' in log and not re.search(r'(?m)^\[?ERROR\b', log) else 'CLI_CONCAT_FAILED'
report = {'status': status, 'original_ptfr_sources': len(ptfr), 'combined_sha256': sha(dest), 'combined_bytes': dest.stat().st_size, 'cli_exit_code': r.returncode, 'cli_tail': log[-3000:], 'game_writes': 0, 'save_writes': 0}
if status == 'CLI_CONCAT_PASS':
    for src, dst in deferred:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    paths = out / 'compile_paths.txt'
    paths.write_text('', encoding='utf-8')
    scc = game / 'engine/tools/scc.exe'
    r = subprocess.run([str(scc), '-compile', str(sources), '-compilePathsFile', str(paths), '-customCacheDir', str(cache), '-outputCacheFile', str(cache / 'compiled.redscripts'), str(cache / 'final.redscripts')], capture_output=True, text=True, timeout=240)
    log = r.stdout + r.stderr
    (out / 'scc.log').write_text(log, encoding='utf-8')
    report['scc_exit_code'] = r.returncode
    report['scc_tail'] = log[-3000:]
    if r.returncode == 0 and 'Compilation complete' in log:
        report['status'] = 'FULL_SCC_CONCAT_PASS'
        report['compiled_sha256'] = sha(cache / 'compiled.redscripts')
    else:
        report['status'] = 'SCC_CONCAT_FAILED'
(out / 'result.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if not k.endswith('_tail')}))
