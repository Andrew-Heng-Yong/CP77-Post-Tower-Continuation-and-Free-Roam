"""Stage and compile the one-file Reed cutoff crash repair."""

from difflib import unified_diff
from hashlib import file_digest
import json
from pathlib import Path
import re
import shutil
import stat
import subprocess


HERE = Path(__file__).resolve().parent
PRE = HERE.parent
BASELINE = PRE / 'history_snapshot_cutoff/deployment_01/installed_manifest_01.json'
BASELINE_SHA = 'AF8F033C66A97CF6049FC018B923C04C3B29D799F7002E6A044898F298002931'
SCRIPT = 'r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds'
OLD_SHA = '3DFC328E20F427770AF8A097A947FCF8A12C2EBEE3335F939E1322BE754F020A'
PACKAGE = HERE / 'candidate_01/package'
OUT = HERE / 'compile_01'
CUTOFF = 'q307_point_of_no_return'


def sha(path):
    with Path(path).open('rb') as stream:
        return file_digest(stream, 'sha256').hexdigest().upper()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, data):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(data, stream, indent=2)
        stream.write('\n')


def plain(path):
    for component in (path, *path.parents):
        assert not component.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, component


def replace_once(source, old, new):
    assert source.count(old) == 1, old
    return source.replace(old, new)


def repair(data):
    old = data.decode('utf-8')
    newline = '\r\n' if '\r\n' in old else '\n'
    source = replace_once(old, newline.join([
        '      let cutoffIndex=tower ? ArrayFindFirst(SnapshotDataHS1.Facts(i),"q307_point_of_no_return") : -1;',
        '      let verified=this.rows[i].stable && this.Same(this.rows[i],this.ReadRow(i),cutoffIndex);',
    ]), newline.join([
        '      let verified=this.rows[i].stable && this.Same(this.rows[i],this.ReadRow(i),tower ? i : -1);',
    ]))
    source = replace_once(source, 'b: SnapshotRowHS1,cutoffIndex: Int32)',
                          'b: SnapshotRowHS1,towerCutoffRow: Int32)')
    source = replace_once(source, newline.join([
        '      // The native callback follows this one write. The saved value still comes from the pre-ending sample.',
        '      if a.facts[k]!=b.facts[k] && !(k==cutoffIndex && a.facts[k]==0 && b.facts[k]==1) { return false; }',
    ]), newline.join([
        '      if a.facts[k]!=b.facts[k] {',
        '        if towerCutoffRow<0 || a.facts[k]!=0 || b.facts[k]!=1 { return false; }',
        '        // Resolve only the differing fact from the same row used by ReadRow.',
        '        let names=SnapshotDataHS1.Facts(towerCutoffRow);',
        '        if k>=ArraySize(names) || NotEquals(StringToName(names[k]),n"q307_point_of_no_return") { return false; }',
        '      }',
    ]))
    assert 'ArrayFindFirst(' not in source
    old_catalogue, _, old_state = old.partition('public class SnapshotStateHS1')
    new_catalogue, _, new_state = source.partition('public class SnapshotStateHS1')
    assert old_catalogue == new_catalogue
    assert old_state.split('  public func Ready()', 1)[1] == new_state.split('  public func Ready()', 1)[1]
    persistent = r'(?m)^ *private persistent let .+$'
    assert re.findall(persistent, old) == re.findall(persistent, source)
    return source.encode('utf-8')


def check_cutoff_policy(source):
    catalogue = re.findall(r'private static func Facts(\d+)\(\) -> array<String> \{ return \[(.*?)\]; \}', source)
    assert {int(index) for index, _ in catalogue} == set(range(158))
    fields = 0
    cutoff_rows = 0
    for _, entries in catalogue:
        facts = re.findall(r'"([^"]*)"', entries)
        assert len(facts) == len(set(facts))
        old_index = facts.index(CUTOFF) if CUTOFF in facts else -1
        cutoff_rows += old_index >= 0
        for index, name in enumerate(facts):
            fields += 1
            for before, after in ((0, 0), (1, 1), (0, 1), (1, 0), (0, 2), (2, 1)):
                for tower in (False, True):
                    previous = before == after or (tower and index == old_index and (before, after) == (0, 1))
                    repaired = before == after or (tower and name == CUTOFF and (before, after) == (0, 1))
                    assert repaired == previous, (index, name, before, after, tower)
    return {'catalogue_rows': len(catalogue), 'fact_fields': fields,
            'rows_containing_tower_cutoff_fact': cutoff_rows,
            'fact_transition_comparisons': fields * 12}


def compile_registered(game, overlay):
    log = game / 'r6/logs/redscript_rCURRENT.log'
    plain(log)
    log_pin = sha(log)
    registered = {(game / 'r6/scripts' / line.strip()).resolve()
                  for line in log.read_text(encoding='utf-8-sig').splitlines()
                  if line.strip().lower().endswith('.reds')}
    discovered = {p.resolve() for root in ('r6/scripts', 'red4ext/plugins')
                  for p in (game / root).rglob('*.reds')}
    assert registered == discovered, (registered - discovered, discovered - registered)
    assert len(registered) == 148 and game / SCRIPT in registered
    scc = game / 'engine/tools/scc.exe'
    base_inputs = [game / 'r6/cache' / name for name in ('final.redscripts', 'final.redscripts.ts')]
    pins = {}
    for path in sorted(registered | {scc, *base_inputs}):
        plain(path)
        pins[str(path.relative_to(game).as_posix())] = sha(path)
    cache = OUT / 'cache'
    cache.mkdir(parents=True)
    for path in base_inputs:
        shutil.copyfile(path, cache / path.name)
    staged = {}
    for path in sorted(registered):
        rel = path.relative_to(game).as_posix()
        source = overlay if rel == SCRIPT else path
        digest = sha(source)
        assert rel == SCRIPT or digest == pins[rel]
        dest = OUT / 'scripts' / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        assert sha(dest) == digest
        staged[rel] = digest
    paths = OUT / 'compile_paths.txt'
    paths.write_bytes(b'')
    compiled = cache / 'compiled.redscripts'
    command = [scc, '-compile', OUT / 'scripts', '-compilePathsFile', paths,
               '-customCacheDir', cache, '-outputCacheFile', compiled, cache / 'final.redscripts']
    process = subprocess.run(list(map(str, command)), capture_output=True, text=True,
                             encoding='utf-8', errors='replace', timeout=180,
                             creationflags=subprocess.CREATE_NO_WINDOW)
    output = process.stdout + process.stderr
    (OUT / 'scc.log').write_text(output, encoding='utf-8')
    assert sha(log) == log_pin and all(sha(game / path) == digest for path, digest in pins.items())
    passed = process.returncode == 0 and 'Compilation complete' in output and compiled.is_file()
    write(OUT / 'result.json', {
        'status': 'PASS' if passed else 'FAIL', 'exit_code': process.returncode,
        'registry_sha256': log_pin, 'source_count': len(registered), 'input_pins': pins,
        'staged_hashes': staged, 'compiled_sha256': sha(compiled) if passed else None,
    })
    assert passed, output[-5000:]
    return len(staged)


def main():
    assert not PACKAGE.exists() and not OUT.exists()
    assert sha(BASELINE) == BASELINE_SHA
    baseline = read(BASELINE)
    assert baseline['core_epoch'] == 'QP2_SNAPSHOT_CUTOFF'
    game = Path(baseline['game_root'])
    expected = {row['path']: row['sha256'] for row in baseline['core_files']}
    assert len(expected) == 51 and expected[SCRIPT] == OLD_SHA
    for row in baseline['core_files'] + baseline['required_files']:
        path = game / row['path']
        plain(path)
        assert path.resolve().is_relative_to(game) and sha(path) == row['sha256'], path
        assert path.stat().st_size == row['bytes'], path
    installed = game / SCRIPT
    old = installed.read_bytes()
    new = repair(old)
    check = check_cutoff_policy(new.decode('utf-8'))
    for rel in expected:
        dest = PACKAGE / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if rel == SCRIPT:
            dest.write_bytes(new)
        else:
            shutil.copyfile(game / rel, dest)
            assert sha(dest) == expected[rel], rel
    diff = unified_diff(old.decode('utf-8').splitlines(keepends=True),
                        new.decode('utf-8').splitlines(keepends=True),
                        'a/' + SCRIPT, 'b/' + SCRIPT)
    (HERE / 'source.patch').write_text(''.join(diff), encoding='utf-8', newline='\n')
    source_count = compile_registered(game, PACKAGE / SCRIPT)
    assert sha(installed) == OLD_SHA
    write(HERE / 'verification.json', {
        'status': 'VERIFIED_OFFLINE', 'baseline': str(BASELINE), 'before_sha256': OLD_SHA,
        'after_sha256': sha(PACKAGE / SCRIPT), 'changed_paths': [SCRIPT],
        'compile_sources': source_count, 'semantic_checks': check,
        'package': str(PACKAGE), 'gameplay': 'UNVERIFIED',
    })
    print(f'Prepared one REDscript replacement and compiled all {source_count} registered sources.')


if __name__ == '__main__':
    main()
