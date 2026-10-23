"""Compile a candidate housing overlay against the complete installed environment.

All outputs and copied caches remain in this workspace. This checks the mod,
not the experimental framework toolchain's own test suites.
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def compile_overlay(overlay, output):
    overlay, output = Path(overlay).resolve(), Path(output).resolve()
    assert overlay.is_relative_to(ROOT) and output.is_relative_to(ROOT)
    output.mkdir(parents=True, exist_ok=False)
    scripts = output / 'scripts'
    shutil.copytree(GAME / 'r6/scripts', scripts)
    dependencies = {str(p): sha(p) for p in (GAME / 'r6/scripts').rglob('*.reds')}
    additions = {}
    for p in sorted((overlay / 'r6/scripts').rglob('*.reds')):
        additions[str(p)] = sha(p)
        target = scripts / p.relative_to(overlay / 'r6/scripts')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)
    assert additions, 'No overlay scripts'
    config = ROOT / 'research/restriction_profiles/implementation_r1/compile_paths.txt'
    plugins = [v.strip() for v in config.read_text(encoding='utf-8-sig').splitlines()[2:] if v.strip()]
    roots = sorted({str(GAME / 'r6/scripts'), *plugins})
    for root in plugins:
        assert Path(root).is_dir()
        for p in Path(root).rglob('*.reds'):
            dependencies[str(p)] = sha(p)
    cache = output / 'cache'
    cache.mkdir()
    protected = {str(p): sha(p) for p in (GAME / 'r6/cache').iterdir() if p.is_file()}
    for name in ['final.redscripts', 'final.redscripts.ts']:
        shutil.copy2(GAME / 'r6/cache' / name, cache / name)
    paths = output / 'compile_paths.txt'
    paths.write_text('\n'.join(plugins) + '\n', encoding='utf-8')
    cli = ROOT / 'research/framework_pr63_01/redscript-cli.exe'
    tool_inputs = {str(p): sha(p) for p in [config, cli, GAME / 'engine/tools/scc.exe', GAME / 'engine/tools/scc_lib.dll']}

    def run(args, log_name):
        result = subprocess.run([str(a) for a in args], capture_output=True, text=True, timeout=240)
        log = result.stdout + result.stderr
        (output / log_name).write_text(log, encoding='utf-8')
        assert result.returncode == 0 and 'Output successfully saved' in log and not re.search(r'(?m)^\[?ERROR\b', log), log[-16000:]
        return log

    compiled = cache / 'compiled.redscripts'
    log = run([GAME / 'engine/tools/scc.exe', '-compile', scripts, '-compilePathsFile', paths,
               '-customCacheDir', cache, '-outputCacheFile', compiled, cache / 'final.redscripts'], 'scc.log')
    assert 'Compilation complete' in log and 'EquipmentEx.reds' in log
    decompiled = output / 'compiled.script'
    run([cli, 'decompile', '-i', compiled, '-o', decompiled], 'decompile.log')
    text = decompiled.read_text(encoding='utf-8-sig')
    assert 'EquipmentEx.OutfitSystem.GetInstance' in text
    classes = []
    for filename in additions:
        source = Path(filename).read_text(encoding='utf-8-sig')
        module = re.search(r'(?m)^module ([\w.]+)', source)
        for name in re.findall(r'(?m)^public (?:abstract )?class (\w+)', source):
            qualified = (module.group(1) + '.' if module else '') + name
            assert re.search(r'\bclass ' + re.escape(qualified) + r'\b', text), qualified
            classes.append(qualified)
    for path, digest in {**dependencies, **protected, **tool_inputs, **additions}.items():
        assert sha(path) == digest, 'Input changed: ' + path
    assert sorted({str(p) for root in roots for p in Path(root).rglob('*.reds')}) == sorted(dependencies)
    report = dict(status='PASS_FULL_SCC_NOT_LIVE', overlay=str(overlay), stage=str(output),
                  full_scc=True, equipmentex=True, decompiled_classes=classes,
                  compiled_sha256=sha(compiled), decompiled_sha256=sha(decompiled),
                  compiler_sha256=sha(__file__), script_roots=roots, dependencies=dependencies,
                  compiler_inputs=tool_inputs, protected=protected, overlay_pins=additions,
                  live_files_unchanged=True)
    (output / 'compile_result.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ['status', 'stage', 'decompiled_classes', 'live_files_unchanged']}, indent=2))
    return report


if __name__ == '__main__':
    compile_overlay(sys.argv[1], sys.argv[2])
