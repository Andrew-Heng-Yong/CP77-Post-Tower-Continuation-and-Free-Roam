"""Compile the combined candidate's registered REDscript sources offline."""

from pathlib import Path
import shutil
import subprocess

from baseline import HERE, OUT, plain, read, sha, write


def main():
    plan = read(HERE / 'baseline.json')
    game = Path(plan['game_root'])
    out = HERE / 'compile_01'
    assert not out.exists()
    log = game / 'r6/logs/redscript_rCURRENT.log'
    plain(log)
    log_digest = sha(log)
    registered = set()
    for line in log.read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if line.lower().endswith('.reds'):
            path = game / 'r6/scripts' / line
            plain(path)
            assert path.resolve().is_relative_to(game), path
            registered.add(path.resolve())
    discovered = {p.resolve() for rel in ('r6/scripts', 'red4ext/plugins')
                  for p in (game / rel).rglob('*.reds')}
    assert registered == discovered, (registered - discovered, discovered - registered)
    assert len(registered) == 148
    cache = out / 'cache'
    cache.mkdir(parents=True)
    exe = game / 'engine/tools/scc.exe'
    cache_inputs = [game / 'r6/cache' / n for n in ('final.redscripts', 'final.redscripts.ts')]
    for path in [exe, *cache_inputs]:
        plain(path)
    pins = {str(p): sha(p) for p in sorted(registered | {exe, *cache_inputs})}
    for path in cache_inputs:
        shutil.copyfile(path, cache / path.name)
        assert sha(cache / path.name) == pins[str(path)]
    overlay = {game / row['path']: row for row in plan['scripts']}
    assert overlay.keys() <= registered
    staged = {}
    scripts = out / 'scripts'
    for path in sorted(registered):
        rel = path.relative_to(game)
        candidate = OUT / 'package' / rel
        source = candidate if candidate.is_file() else path
        expected = overlay[path]['after'] if path in overlay else pins[str(path)]
        assert sha(source) == expected, path
        dest = scripts / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        assert sha(dest) == expected
        staged[str(path)] = {'staged': str(dest), 'sha256': expected}
    paths = out / 'compile_paths.txt'
    paths.write_bytes(b'')
    compiled = cache / 'compiled.redscripts'
    command = list(map(str, [exe, '-compile', scripts, '-compilePathsFile', paths,
                            '-customCacheDir', cache, '-outputCacheFile', compiled, cache / 'final.redscripts']))
    run = subprocess.run(command, capture_output=True, text=True, timeout=180,
                         creationflags=subprocess.CREATE_NO_WINDOW)
    output = run.stdout + run.stderr
    (out / 'scc.log').write_text(output, encoding='utf-8')
    assert all(sha(path) == digest for path, digest in pins.items()) and sha(log) == log_digest
    good = run.returncode == 0 and 'Compilation complete' in output and compiled.is_file()
    write(out / 'result.json', {
        'status': 'PASS_JB4_COMPLETE_SOURCE_COMPILE' if good else 'FAIL_COMPILE',
        'exit_code': run.returncode, 'source_count': len(staged), 'input_pins': pins,
        'registry_sha256': log_digest, 'sources': staged, 'overlays': plan['scripts'],
        'compiled_sha256': sha(compiled) if good else None,
    })
    assert good, output[-4500:]
    print(f'Compiled {len(staged)} registered REDscript sources offline.')


if __name__ == '__main__':
    main()
