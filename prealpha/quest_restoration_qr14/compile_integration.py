"""One justified integration compile: include17 actual LBD runtime inputs missed by QR13.
Copies sources/caches to a fresh workspace. Never writes installed inputs or rebuilds Core.
"""
from pathlib import Path
import shutil, stat, subprocess
from prepare import H, read, sha, write

def safe(p):
    for q in (p, *p.parents):
        s = q.lstat()
        assert not stat.S_ISLNK(s.st_mode) and not s.st_file_attributes & 0x400, q

def main():
    m = read(H / 'core_manifest_01.json'); game = Path(m['game_root'])
    out = H / 'verification/compile_01'
    assert not out.exists(), 'Fresh output only'
    log = game / 'r6/logs/redscript_rCURRENT.log'; safe(log)
    raw = log.read_bytes(); log_sha = sha(log)
    registered = set()
    for line in raw.decode('utf-8-sig').splitlines():
        line = line.strip()
        if line.lower().endswith('.reds'):
            p = Path(line) if Path(line).is_absolute() else game / 'r6/scripts' / line
            safe(p); assert p.is_relative_to(game)
            registered.add(p)
    roots = [('game', game / 'r6/scripts'), ('Codeware', game / 'red4ext/plugins/Codeware/Scripts'),
        ('ArchiveXL', game / 'red4ext/plugins/ArchiveXL/Scripts'), ('TweakXL', game / 'red4ext/plugins/TweakXL/Scripts'),
        ('mod_settings', game / 'red4ext/plugins/mod_settings'), ('LizziesBDs', game / 'red4ext/plugins/LizziesBDs/Scripts')]
    found = {p for _, root in roots for p in root.rglob('*.reds')}
    all_sources = set((game / 'r6/scripts').rglob('*.reds')) | set((game / 'red4ext/plugins').rglob('*.reds'))
    assert found == registered == all_sources, {'not_registered': list(map(str, found-registered)), 'unknown_roots': list(map(str, all_sources-found))}
    out.mkdir(parents=True); (out / 'runtime_redscript.log').write_bytes(raw)
    scripts = out / 'scripts'; cache = out / 'cache'; cache.mkdir()
    pins = {}; origin = {}
    for group, root in roots:
        safe(root)
        for p in sorted(root.rglob('*.reds')):
            safe(p); pins[str(p)] = sha(p)
            dest = scripts / group / p.relative_to(root); dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, dest); assert sha(dest) == pins[str(p)]; origin[str(p)] = str(dest)
    for r in m['files']:
        if r['path'].endswith('.reds'):
            src = Path(m['package_root']) / r['path']; safe(src)
            dest = scripts / 'game' / Path(r['path']).relative_to('r6/scripts')
            assert dest.exists() and sha(src) == r['after']; shutil.copyfile(src, dest)
    for name in ['final.redscripts', 'final.redscripts.ts']:
        p = game / 'r6/cache' / name; safe(p); pins[str(p)] = sha(p); shutil.copyfile(p, cache / name)
    exe = game / 'engine/tools/scc.exe'; safe(exe); pins[str(exe)] = sha(exe)
    paths = out / 'compile_paths.txt'; paths.write_text('', encoding='utf-8')
    command = list(map(str, [exe, '-compile', scripts, '-compilePathsFile', paths,
        '-customCacheDir', cache, '-outputCacheFile', cache / 'compiled.redscripts', cache / 'final.redscripts']))
    r = subprocess.run(command, capture_output=True, text=True, timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
    (out / 'scc.log').write_text(r.stdout + r.stderr, encoding='utf-8')
    assert all(sha(p) == s for p,s in pins.items()), 'Installed compiler inputs changed'
    assert sha(log) == log_sha, 'Runtime evidence changed'
    staged = {str(p): sha(p) for p in scripts.rglob('*.reds')}
    good = r.returncode == 0 and 'Compilation complete' in r.stdout+r.stderr and (cache / 'compiled.redscripts').is_file()
    result = {'status': 'PASS_RUNTIME_REGISTERED148_INTEGRATION_COMPILE' if good else 'FAIL_INTEGRATION_COMPILE',
        'command': command, 'exit_code': r.returncode, 'source_count': len(staged), 'input_pins': pins,
        'runtime_log': {'path': str(log), 'sha256': log_sha, 'copy': str(out / 'runtime_redscript.log')},
        'runtime_registered_sources': sorted(map(str, registered)), 'source_origins': origin, 'staged_sources': staged,
        'roots': [str(root) for _, root in roots], 'additional_sources_vs_QR13': sorted(set(pins)-set(m['compile_inputs'])),
        'compiled_sha256': sha(cache / 'compiled.redscripts') if good else None,
        'installed_inputs_unchanged': True, 'game_writes': 0, 'save_writes': 0,
        'limits': 'Current runtime-log/source inventory only. Offline compilation is not executing-owner or gameplay proof. Does not replace or rewrite immutable QR13 result.'}
    write(out / 'result.json', result)
    print({'status': result['status'], 'sources': len(staged), 'additional': len(result['additional_sources_vs_QR13']),
        'compiled_sha256': result['compiled_sha256']})
    assert good, (r.stdout + r.stderr)[-4500:]

if __name__ == '__main__':
    main()
