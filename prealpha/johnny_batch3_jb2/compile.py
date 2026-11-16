"""Compile the two admission gates against the complete installed source set."""

from pathlib import Path
import shutil
import stat
import subprocess

from prepare import BASE, HERE, INPUT, OUT
from resources import read, sha, write


def safe(path):
    for p in (path, *path.parents):
        info = p.lstat()
        assert not stat.S_ISLNK(info.st_mode) and not info.st_file_attributes & 0x400, p


def main():
    plan = read(INPUT / 'plan.json')
    game = Path(plan['game_root'])
    out = HERE / 'compile_01'
    assert not out.exists()
    prior = read(BASE.parent / 'compile_inventory_04.json')
    pins = {Path(p): digest for p, digest in prior['input_pins'].items()}
    log = game / 'r6/logs/redscript_rCURRENT.log'
    safe(log)
    log_sha = sha(log)
    registered = set()
    for line in log.read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if line.lower().endswith('.reds'):
            p = game / 'r6/scripts' / line
            safe(p)
            p = p.resolve()
            assert p.is_relative_to(game)
            registered.add(p)
    discovered = {p.resolve() for root in ('r6/scripts', 'red4ext/plugins')
                  for p in (game / root).rglob('*.reds')}
    assert registered == discovered == {p for p in pins if p.suffix == '.reds'}, (
        registered - discovered, discovered - registered)
    assert len(registered) == prior['source_count'] == 148
    exe = game / 'engine/tools/scc.exe'
    cache_names = ['final.redscripts', 'final.redscripts.ts']
    for p in (exe, *(game / 'r6/cache' / n for n in cache_names)):
        safe(p)
        digest = sha(p)
        if p.name != 'final.redscripts.ts':
            assert digest == pins[p], p
        elif digest != pins[p]:
            assert p.stat().st_size == 16, p
        pins[p] = digest
    scripts = out / 'scripts'
    cache = out / 'cache'
    cache.mkdir(parents=True)
    for name in cache_names:
        shutil.copyfile(game / 'r6/cache' / name, cache / name)
    edits = {game / row['path']: row for row in plan['scripts']}
    staged = {}
    for p in sorted(registered):
        safe(p)
        assert sha(p) == pins[p], p
        overlay = edits.get(p)
        source = OUT / 'package' / overlay['path'] if overlay else p
        expected = overlay['after'] if overlay else pins[p]
        dest = scripts / p.relative_to(game)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        assert sha(dest) == expected, dest
        staged[str(p)] = {'staged': str(dest), 'sha256': expected}
    paths = out / 'compile_paths.txt'
    paths.write_bytes(b'')
    compiled = cache / 'compiled.redscripts'
    command = list(map(str, [exe, '-compile', scripts, '-compilePathsFile', paths,
                            '-customCacheDir', cache, '-outputCacheFile', compiled,
                            cache / 'final.redscripts']))
    run = subprocess.run(command, capture_output=True, text=True, timeout=180,
                         creationflags=subprocess.CREATE_NO_WINDOW)
    output = run.stdout + run.stderr
    (out / 'scc.log').write_text(output, encoding='utf-8')
    assert all(sha(p) == digest for p, digest in pins.items())
    assert sha(log) == log_sha
    good = run.returncode == 0 and 'Compilation complete' in output and compiled.is_file()
    write(out / 'result.json', {'status': 'PASS_JB2_COMPLETE_SOURCE_COMPILE' if good else 'FAIL_COMPILE',
          'command': command, 'exit_code': run.returncode, 'source_count': len(staged),
          'input_pins': {str(p): digest for p, digest in pins.items()}, 'registry_sha256': log_sha,
          'sources': staged, 'compiled_sha256': sha(compiled) if good else None,
          'overlays': plan['scripts'], 'game_writes': 0, 'save_writes': 0})
    assert good, output[-4000:]
    print(f"Compiled {len(staged)} registered REDscript sources in isolation.")


if __name__ == '__main__':
    main()
