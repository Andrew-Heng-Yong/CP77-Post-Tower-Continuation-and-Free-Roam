from pathlib import Path
import collections
import hashlib
import json
import re
import shutil
import subprocess

here = Path(__file__).resolve().parent
ws = here.parent.parent
game = Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')
out = here / 'reds_module_probe_01'
assert not out.exists()
sources = out / 'scripts'
cache = out / 'cache'
cache.mkdir(parents=True)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

groups = collections.defaultdict(list)
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
            text = path.read_text(encoding='utf-8-sig')
            modules = re.findall(r'(?m)^module\s+([^\s]+)\s*$', text)
            assert len(modules) <= 1, path
            groups[modules[0] if modules else '__global__'].append((path, text))
            continue
        dest = sources / label / relative
        if 'EquipmentEx' in path.parts:
            deferred.append((path, dest))
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
assert sum(len(v) for v in groups.values()) == 76
combined_rows = []
for module, items in sorted(groups.items()):
    if len(items) == 1:
        text = items[0][1]
    else:
        imports = []
        bodies = []
        for path, source in sorted(items, key=lambda x: str(x[0]).lower()):
            lines = []
            for line in source.splitlines():
                if re.match(r'^module\s+', line):
                    continue
                if re.match(r'^import\s+', line):
                    if line not in imports:
                        imports.append(line)
                    continue
                lines.append(line)
            bodies.append('// ORIGINAL: ' + str(path.relative_to(game)).replace('\\', '/') + '\n' + '\n'.join(lines).strip() + '\n')
        text = ('' if module == '__global__' else 'module ' + module + '\n') + '\n'.join(imports) + '\n\n' + '\n'.join(bodies)
    filename = ('PTFR_Global' if module == '__global__' else module.replace('.', '_')) + '.reds'
    dest = sources / 'game/PTFR_Consolidated' / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding='utf-8')
    combined_rows.append({'module': module, 'sources': [str(path.relative_to(game)).replace('\\', '/') for path, _ in items], 'path': str(dest.relative_to(sources)), 'sha256': sha(dest)})
for name in ('final.redscripts', 'final.redscripts.ts'):
    shutil.copyfile(game / 'r6/cache' / name, cache / name)
cli = ws / 'diagnostics/mod_updates_20261023_01/downloads/redscript-cli.exe'
r = subprocess.run([str(cli), 'compile', '-s', str(sources), '-b', str(cache / 'final.redscripts'), '-o', str(cache / 'cli.redscripts')], capture_output=True, text=True, timeout=240)
log = r.stdout + r.stderr
(out / 'cli.log').write_text(log, encoding='utf-8')
status = 'CLI_MODULE_MERGE_PASS' if r.returncode == 0 and 'Output successfully saved' in log and 'ERROR [' not in log else 'CLI_MODULE_MERGE_FAILED'
report = {'status': status, 'original_sources': 76, 'module_groups': len(groups), 'merged_sources': len(combined_rows), 'rows': combined_rows, 'cli_exit_code': r.returncode, 'cli_tail': log[-3000:], 'game_writes': 0, 'save_writes': 0}
if status == 'CLI_MODULE_MERGE_PASS':
    for src, dest in deferred:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
    paths = out / 'compile_paths.txt'
    paths.write_text('', encoding='utf-8')
    scc = game / 'engine/tools/scc.exe'
    r = subprocess.run([str(scc), '-compile', str(sources), '-compilePathsFile', str(paths), '-customCacheDir', str(cache), '-outputCacheFile', str(cache / 'compiled.redscripts'), str(cache / 'final.redscripts')], capture_output=True, text=True, timeout=240)
    log = r.stdout + r.stderr
    (out / 'scc.log').write_text(log, encoding='utf-8')
    report['scc_exit_code'] = r.returncode
    report['scc_tail'] = log[-3000:]
    if r.returncode == 0 and 'Compilation complete' in log:
        report['status'] = 'FULL_SCC_MODULE_MERGE_PASS'
        report['compiled_sha256'] = sha(cache / 'compiled.redscripts')
    else:
        report['status'] = 'SCC_MODULE_MERGE_FAILED'
(out / 'result.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k not in ('rows', 'cli_tail', 'scc_tail')}))
