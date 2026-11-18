"""Stage the credits cover successor and compile with current runtime inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import stat
import subprocess


HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[1]
PREDECESSOR = WORKSPACE / 'prealpha/world_overlap_20261116_01/work/deployment_01/installed_manifest_01.json'
PREDECESSOR_SHA = 'F9AA02A1C70BE28CB1C0B343C542FD5B204CAAE9048EDF94C8AD281FBED63A05'
RELATIVE_SCRIPT = 'r6/scripts/PTFR_Consolidated/PTFR_LoadingCoverLC1.reds'
SOURCE = HERE / Path(RELATIVE_SCRIPT).name
LIZZIES_PLUGIN = 'red4ext/plugins/LizziesBDs'
LIZZIES_ARCHIVE = 'archive/pc/mod/LizziesBDs.archive'
NEW_LIZZIES_SOURCE = f'{LIZZIES_PLUGIN}/Scripts/LizziesBDs.WorkspotBD.reds'


def sha256(path):
    with path.open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest().upper()


def check_plain(path):
    for item in (path, *path.parents):
        if item.exists() and item.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise RuntimeError(f'Linked path refused: {item}')


def write_json(path, data):
    with path.open('x', encoding='utf-8', newline='\n') as file:
        json.dump(data, file, indent=2)
        file.write('\n')


def inventory(game):
    return {
        path
        for relative in ('r6/scripts', 'red4ext/plugins')
        for path in (game / relative).rglob('*.reds')
    }


def verify_rows(root, rows):
    for row in rows:
        path = root / row['path']
        check_plain(path)
        if path.stat().st_size != row['bytes'] or sha256(path) != row['sha256']:
            raise RuntimeError(f'File identity changed: {path}')


def file_record(root, relative):
    path = root / relative
    check_plain(path)
    return {'path': relative, 'bytes': path.stat().st_size, 'sha256': sha256(path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('revision', type=int)
    revision = parser.parse_args().revision
    if revision < 1:
        parser.error('revision must be positive')
    output = HERE / f'candidate_{revision:02d}'
    check_plain(output)
    check_plain(PREDECESSOR)
    check_plain(SOURCE)
    assert sha256(PREDECESSOR) == PREDECESSOR_SHA
    baseline = json.loads(PREDECESSOR.read_text(encoding='utf-8-sig'))
    game = Path(baseline['game_root'])
    core = baseline['core_files']
    required = baseline['required_files']
    assert len(core) == 51
    verify_rows(game, core)

    # Lizzie's Braindances was updated after the last recorded startup.
    live_required = [row | file_record(game, row['path']) for row in required]
    dependency_changes = [
        {'before': before, 'current': current}
        for before, current in zip(required, live_required)
        if before != current
    ]
    for item in dependency_changes:
        relative = item['current']['path']
        if relative != LIZZIES_ARCHIVE and not relative.startswith(LIZZIES_PLUGIN + '/'):
            raise RuntimeError(f'Unreviewed dependency drift: {relative}')
    live_required += [
        {'active_only': False} | file_record(game, relative)
        for relative in (NEW_LIZZIES_SOURCE, f'{LIZZIES_PLUGIN}/LizziesBDs.dll')
        if relative not in {row['path'] for row in live_required}
    ]

    runtime_log = game / 'r6/logs/redscript_rCURRENT.log'
    log_bytes = runtime_log.read_bytes()
    log_text = log_bytes.decode('utf-8-sig', errors='replace')
    assert 'Compilation complete' in log_text
    registered = {
        (game / 'r6/scripts' / line.strip()).resolve(strict=True)
        for line in log_text.splitlines()
        if line.strip().lower().endswith('.reds')
    }
    installed = inventory(game)
    added = installed - registered
    if registered - installed or added - {game / NEW_LIZZIES_SOURCE}:
        raise RuntimeError(
            f'Runtime source inventory differs. '
            f'Unregistered: {sorted(added)}. Missing: {sorted(registered - installed)}'
        )
    assert game / RELATIVE_SCRIPT in installed
    compiler = game / 'engine/tools/scc.exe'
    caches = [game / 'r6/cache' / name for name in ('final.redscripts', 'final.redscripts.ts')]
    pins = {}
    for path in sorted(installed | set(caches) | {compiler}):
        check_plain(path)
        pins[path] = sha256(path)
    source_hash = sha256(SOURCE)
    assert source_hash != pins[game / RELATIVE_SCRIPT]

    output.mkdir(exist_ok=False)
    package = output / 'package'
    candidate_rows = []
    for row in core:
        relative = row['path']
        source = SOURCE if relative == RELATIVE_SCRIPT else game / relative
        staged = package / relative
        staged.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, staged)
        candidate_rows.append({'path': relative, 'bytes': staged.stat().st_size, 'sha256': sha256(staged)})
    changed = [after['path'] for before, after in zip(core, candidate_rows) if before != after]
    assert changed == [RELATIVE_SCRIPT], changed
    assert next(row['sha256'] for row in candidate_rows if row['path'] == RELATIVE_SCRIPT) == source_hash
    assert {p.relative_to(package).as_posix() for p in package.rglob('*') if p.is_file()} == {
        row['path'] for row in core
    }

    proof = output / 'compile_01'
    cache = proof / 'cache'
    cache.mkdir(parents=True)
    (proof / 'runtime_redscript.log').write_bytes(log_bytes)
    for path in caches:
        staged_cache = cache / path.name
        shutil.copyfile(path, staged_cache)
        assert sha256(staged_cache) == pins[path]
    sources = proof / 'scripts'
    staged_hashes = {}
    for path in sorted(installed):
        relative = path.relative_to(game).as_posix()
        source = package / relative if relative == RELATIVE_SCRIPT else path
        staged = sources / relative
        staged.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, staged)
        staged_hashes[relative] = sha256(staged)
        assert staged_hashes[relative] == (source_hash if relative == RELATIVE_SCRIPT else pins[path])
    paths = proof / 'compile_paths.txt'
    paths.write_bytes(b'')
    compiled = cache / 'compiled.redscripts'
    command = [
        compiler, '-compile', sources, '-compilePathsFile', paths,
        '-customCacheDir', cache, '-outputCacheFile', compiled, cache / 'final.redscripts',
    ]
    result = subprocess.run(
        [str(arg) for arg in command], cwd=proof, capture_output=True,
        encoding='utf-8', errors='replace', timeout=140, creationflags=subprocess.CREATE_NO_WINDOW,
    )
    compiler_log = result.stdout + result.stderr
    (proof / 'scc.log').write_text(compiler_log, encoding='utf-8')

    verify_rows(game, core + live_required)
    verify_rows(package, candidate_rows)
    assert inventory(game) == installed
    assert runtime_log.read_bytes() == log_bytes
    assert all(sha256(path) == expected for path, expected in pins.items())
    assert sha256(SOURCE) == source_hash
    assert result.returncode == 0 and 'Compilation complete' in compiler_log and compiled.is_file(), compiler_log[-8000:]

    assessment = proof / 'assessment.json'
    write_json(assessment, {
        'status': 'PASS',
        'runtime_log_sha256': hashlib.sha256(log_bytes).hexdigest().upper(),
        'last_startup_source_count': len(registered),
        'present_since_last_startup': [p.relative_to(game).as_posix() for p in sorted(added)],
        'source_count': len(staged_hashes),
        'staged_sources': staged_hashes,
        'installed_inputs': {str(path): expected for path, expected in pins.items()},
        'compiled_sha256': sha256(compiled),
        'changed_sources': changed,
        'game_writes': 0,
    })
    write_json(output / 'core_manifest_01.json', {
        'status': 'STAGED_OFFLINE',
        'predecessor': str(PREDECESSOR),
        'predecessor_sha256': PREDECESSOR_SHA,
        'core_files': candidate_rows,
        'changed_paths': changed,
        'required_files': live_required,
        'dependency_changes_since_predecessor': dependency_changes,
        'compile_assessment': str(assessment),
        'compile_assessment_sha256': sha256(assessment),
        'rendered_handoff': 'PENDING',
    })
    print(f'Compiled {len(staged_hashes)} current scripts. Staged {len(core)} Core files with one replacement.')


if __name__ == '__main__':
    main()
