"""Stage a one-script repair against the verified TP2 installation."""
from pathlib import Path
import difflib
import shutil
from capture import HERE, BASELINE, BASELINE_SHA, sha, read, write, plain

COVER = 'r6/scripts/PTFR_Consolidated/PTFR_LoadingCoverLC1.reds'

def one(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)

def main():
    candidate = HERE / 'candidate_01'
    assert not candidate.exists() and sha(BASELINE) == BASELINE_SHA
    baseline = read(BASELINE)
    game = Path(baseline['game_root'])
    for row in baseline['core_files'] + baseline['required_files']:
        path = game / row['path']
        plain(path)
        assert sha(path) == row['sha256'], row['path']
    package = candidate / 'package'
    for row in baseline['core_files']:
        dest = package / row['path']
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(game / row['path'], dest)
        assert sha(dest) == row['sha256']
    old = (package / COVER).read_text(encoding='utf-8')
    start = old.index('  // TP2: finish presentation teardown')
    end = old.index('  public func TraceUIStateTP2', start)
    repair = (HERE / 'presentation.reds').read_text(encoding='utf-8')
    new = old[:start] + repair + '\n' + old[end:]
    new = one(new, '  private let presentationStateCaptures:Int32;',
              '  private let presentationStateCaptures:Int32;\n  private let presentationUIState:CName;')
    new = one(new, '    this.presentationRepairActor=null;this.presentationStateCaptures=0;',
              '    this.presentationRepairActor=null;this.presentationStateCaptures=0;this.presentationUIState=n"";')
    new = one(new, '    if this.leaving || this.released { return; }',
              '    if this.leaving || this.released { return; }\n    this.FinishBodyReturnTP3();')
    new = one(new, '    if !this.running || !this.Required() || this.presentationStateCaptures>=24 { return; }',
              '    if !this.running || !this.Required() { return; }\n    this.presentationUIState=current;\n    if this.presentationStateCaptures>=24 { return; }')
    (package / COVER).write_bytes(new.replace('\n', '\r\n').encode('utf-8'))
    (candidate / 'cover.patch').write_text(''.join(difflib.unified_diff(
        old.splitlines(keepends=True), new.splitlines(keepends=True), fromfile='TP2', tofile='TP3')),
        encoding='utf-8', newline='\n')
    rows = [{'path': row['path'], 'sha256': sha(package / row['path'])} for row in baseline['core_files']]
    assert len(rows) == 51
    assert {a['path'] for a,b in zip(rows, baseline['core_files']) if a['sha256'] != b['sha256']} == {COVER}
    write(candidate / 'manifest.json', {'baseline_manifest_sha256': BASELINE_SHA, 'changed_paths': [COVER], 'files': rows})
    print('Staged a one-script successor from the verified TP2 installation.')

if __name__ == '__main__':
    main()
