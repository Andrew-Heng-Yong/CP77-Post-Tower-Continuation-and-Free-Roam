"""Stage the evening recovery and fast-travel cover update."""

import argparse
from difflib import unified_diff
import importlib.util
from pathlib import Path
import shutil
import subprocess

from edits import edit_cover, edit_recovery
from verify_changes import check_source


HERE = Path(__file__).resolve().parent
PRE = HERE.parent
PREVIOUS = 'QP2_TOWER_RECOVERY_FACT'
EPOCH = 'QP2_TOWER_EVENING_RECOVERY'
BASELINE = PRE / 'tower_recovery_fact_20261112_01/deployment_01/installed_manifest_01.json'
BASELINE_SHA = 'DA54FEBAED047BA09B865E704DB040BB7958AC3BE4DCB40CE5BF82C3113E415E'
TEMPLATE = PRE / 'johnny_load_crash_20261111_01/deploy_core.ps1'
TEMPLATE_SHA = '8C94862FC57931194D6892B2B485C8E155F1CAC1903D1323DE6BB2E5F1E9D7C5'
TEMPLATE_MANIFEST_SHA = 'A18B646B307FE336F4D34BDFD01676322E0368C40204AA1C0CE92BF36FB79DB0'
COVER = 'r6/scripts/PTFR_Consolidated/PTFR_LoadingCoverLC1.reds'
R3 = 'r6/scripts/PTFR_Consolidated/PTFR_RestrictionsR3.reds'
CHANGES = {COVER, R3}

spec = importlib.util.spec_from_file_location(
    'cyberware_build_helpers', PRE / 'cyberware_treatment_20261111_01/prepare.py'
)
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)
sha, read, write, one = common.digest, common.read_json, common.write_json, common.one


def compile_overlay(game, package, output):
    registry = game / 'r6/logs/redscript_rCURRENT.log'
    common.plain(registry, game)
    registry_hash = sha(registry)
    lines = registry.read_text(encoding='utf-8-sig').splitlines()
    registered = {(game / 'r6/scripts' / line.strip()).resolve()
                  for line in lines if line.strip().lower().endswith('.reds')}
    discovered = {p.resolve() for directory in ('r6/scripts', 'red4ext/plugins')
                  for p in (game / directory).rglob('*.reds')}
    assert registered == discovered and all(game / relative in registered for relative in CHANGES)
    compiler = game / 'engine/tools/scc.exe'
    caches = [game / 'r6/cache' / name for name in ('final.redscripts', 'final.redscripts.ts')]
    pins = {}
    for path in sorted(registered | {compiler, *caches}):
        common.plain(path, game)
        pins[path.relative_to(game).as_posix()] = sha(path)
    cache = output / 'cache'
    cache.mkdir(parents=True)
    for path in caches:
        staged_cache = cache / path.name
        shutil.copyfile(path, staged_cache)
        assert sha(staged_cache) == pins[path.relative_to(game).as_posix()]
    scripts = output / 'scripts'
    staged = {}
    for path in sorted(registered):
        relative = path.relative_to(game).as_posix()
        source = package / relative if relative in CHANGES else path
        destination = scripts / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        staged[relative] = sha(destination)
        assert staged[relative] == (sha(source) if relative in CHANGES else pins[relative])
    paths = output / 'compile_paths.txt'
    paths.write_bytes(b'')
    compiled = cache / 'compiled.redscripts'
    command = [compiler, '-compile', scripts, '-compilePathsFile', paths, '-customCacheDir',
               cache, '-outputCacheFile', compiled, cache / 'final.redscripts']
    result = subprocess.run(list(map(str, command)), capture_output=True, encoding='utf-8',
                            errors='replace', timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
    log = result.stdout + result.stderr
    (output / 'scc.log').write_text(log, encoding='utf-8')
    assert sha(registry) == registry_hash
    assert all(sha(game / relative) == pin for relative, pin in pins.items())
    passed = result.returncode == 0 and 'Compilation complete' in log and compiled.is_file()
    write(output / 'result.json', {
        'status': 'PASS' if passed else 'FAIL', 'source_count': len(staged),
        'registry_sha256': registry_hash, 'input_pins': pins, 'staged_hashes': staged,
        'compiled_sha256': sha(compiled) if passed else None,
    })
    if not passed:
        raise RuntimeError(log[-8500:])
    return len(staged)


def build(attempt):
    candidate = HERE / f'candidate_{attempt:02}'
    compile_output = HERE / f'compile_{attempt:02}'
    assert not candidate.exists() and not compile_output.exists()
    assert sha(BASELINE) == BASELINE_SHA
    baseline = read(BASELINE)
    assert baseline['core_epoch'] == PREVIOUS
    game = Path(baseline['game_root'])
    assert len(baseline['core_files']) == 51 and len(baseline['required_files']) == 26
    for row in baseline['core_files'] + baseline['required_files']:
        path = game / row['path']
        common.plain(path, game)
        assert sha(path) == row['sha256'] and path.stat().st_size == row['bytes'], path

    originals = {relative: (game / relative).read_text(encoding='utf-8') for relative in CHANGES}
    edited = {COVER: edit_cover(originals[COVER]), R3: edit_recovery(originals[R3])}
    checks = check_source(originals[R3], edited[R3], originals[COVER], edited[COVER])
    package = candidate / 'package'
    for row in baseline['core_files']:
        relative = row['path']
        dest = package / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if relative in CHANGES:
            dest.write_text(edited[relative], encoding='utf-8', newline='\n')
            assert dest.read_text(encoding='utf-8') == edited[relative]
        else:
            shutil.copyfile(game / relative, dest)
            assert sha(dest) == row['sha256'], relative
    patch = []
    for relative in sorted(CHANGES):
        patch.extend(unified_diff(originals[relative].splitlines(keepends=True),
                                  edited[relative].splitlines(keepends=True), 'a/' + relative, 'b/' + relative))
    (candidate / 'source.patch').write_text(''.join(patch), encoding='utf-8', newline='\n')
    count = compile_overlay(game, package, compile_output)
    write(candidate / 'verification.json', {
        'baseline_sha256': BASELINE_SHA, 'script_hashes': {relative: sha(package / relative) for relative in sorted(CHANGES)},
        'registered_sources': count, 'checks': checks, 'compile': 'PASS', 'gameplay': 'UNVERIFIED',
    })
    print(f'Evening recovery and cover update compiled with all {count} registered sources.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('attempt', type=int)
    build(parser.parse_args().attempt)
