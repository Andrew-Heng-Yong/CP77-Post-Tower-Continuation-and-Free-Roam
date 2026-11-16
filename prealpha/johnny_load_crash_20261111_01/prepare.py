"""Stage the save-load fix and compile the exact installed script registry."""

from difflib import unified_diff
from pathlib import Path
import re
import shutil
import subprocess
import sys


HERE = Path(__file__).resolve().parent
PRE = HERE.parent
PREDECESSOR = PRE / 'reed_snapshot_crash_20261111_01'
sys.path.insert(0, str(PREDECESSOR))
from build import plain, read, replace_once, sha, write


BASELINE = PREDECESSOR / 'deployment_01/installed_manifest_01.json'
BASELINE_SHA = '93CF7D53DA429B668925484499FC5B642972C4B4135D3615838928F4B033ED46'
SCRIPT = 'r6/scripts/PTFR_Consolidated/PTFR_JohnnyVoiceJV1.reds'
OLD_SHA = '1338B05F41A88D222BEABCFF4F9D23D3B87B42B1A67E7019678DDA60F7917FE5'
PACKAGE = HERE / 'candidate_01/package'
COMPILE = HERE / 'compile_01'


def replace_block(source, old, new, newline):
    return replace_once(source, old.replace('\n', newline), new.replace('\n', newline))


def repair(data):
    source = data.decode('utf-8')
    newline = '\r\n' if '\r\n' in source else '\n'
    source = replace_block(source, '''  private func OnDetach() -> Void {
    this.running = false; this.epoch += 1; ArrayClear(this.actors);
  }
  public func Restored() -> Void {
    // Do not clear registrations: NPC attachment and restore callbacks may
    // arrive in either order. Poll prunes expired/detached weak references.
    this.epoch += 1;
    if this.running { this.Schedule(); }
  }''', '''  private func OnDetach() -> Void {
    this.running = false;
    this.epoch += 1;
    this.visuals = 0;
  }
  public func Restored() -> Void {
    this.QueueRequest(new JohnnyVoiceRestoreRequest());
  }
  private func OnJohnnyVoiceRestoreRequest(request: ref<JohnnyVoiceRestoreRequest>) -> Void {
    if !this.running { return; }
    // Attachment and restore requests may arrive in either order. Keep
    // registered weak references and let the poll remove detached actors.
    this.epoch += 1;
    this.Schedule();
  }''', newline)
    source = replace_block(source, '''  public func Register(actor: wref<NPCPuppet>) -> Void {
    if !IsDefined(actor) || actor.GetRecordID() != t"Character.Silverhand" { return; }
    let i = 0;''', '''  public func Register(actor: wref<NPCPuppet>) -> Void {
    if !IsDefined(actor) || actor.GetRecordID() != t"Character.Silverhand" { return; }
    // NPC attachment may run on a game worker. Only the system's request
    // handlers can change the registry or run its visibility scan.
    let request = new JohnnyVoiceRegisterRequest();
    request.actor = actor;
    this.QueueRequest(request);
  }
  private func OnJohnnyVoiceRegisterRequest(request: ref<JohnnyVoiceRegisterRequest>) -> Void {
    let actor = request.actor;
    if !this.running || !IsDefined(actor) || actor.GetRecordID() != t"Character.Silverhand" { return; }
    let i = 0;''', newline)
    source = replace_block(source, '''  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    this.Schedule();''', '''  public func Poll(epoch: Int32) -> Void {
    let request = new JohnnyVoicePollRequest();
    request.epoch = epoch;
    this.QueueRequest(request);
  }
  private func OnJohnnyVoicePollRequest(request: ref<JohnnyVoicePollRequest>) -> Void {
    if !this.running || request.epoch != this.epoch { return; }
    this.Schedule();''', newline)
    source = replace_block(source, 'public class JohnnyVoiceTick extends DelayCallback {',
                           '''public class JohnnyVoiceRestoreRequest extends ScriptableSystemRequest {}

public class JohnnyVoiceRegisterRequest extends ScriptableSystemRequest {
  public let actor: wref<NPCPuppet>;
}

public class JohnnyVoicePollRequest extends ScriptableSystemRequest {
  public let epoch: Int32;
}

public class JohnnyVoiceTick extends DelayCallback {''', newline)
    return source.encode('utf-8')


def method(source, name):
    match = re.search(r'(?m)^  (?:private|public) func ' + name + r'\([^\n]*\{', source)
    assert match, name
    end = source.index('\n  }', match.end())
    return source[match.start():end + 4]


def check_source(original, edited):
    original = original.decode('utf-8').replace('\r\n', '\n')
    edited = edited.decode('utf-8').replace('\r\n', '\n')
    for name in ('CompletedTower', 'Hide', 'GetStatus', 'Schedule'):
        assert method(original, name) == method(edited, name), name
    assert original.split('@wrapMethod(NPCPuppet)', 1)[1] == edited.split('@wrapMethod(NPCPuppet)', 1)[1]
    assert not re.search(r'\bpersistent let\b', edited)
    assert 'ArrayClear(this.actors)' not in edited
    writes = re.findall(r'Array(?:Push|Erase|Clear)\(this\.actors[^\n]*', edited)
    assert len(writes) == 2
    assert writes[0] in method(edited, 'OnJohnnyVoiceRegisterRequest')
    assert writes[1] in method(edited, 'OnJohnnyVoicePollRequest')
    for name in ('Register', 'Restored', 'Poll'):
        caller = method(edited, name)
        assert 'QueueRequest(' in caller and 'this.actors' not in caller and 'this.Hide(' not in caller
    poll = method(edited, 'OnJohnnyVoicePollRequest')
    assert poll.index('request.epoch != this.epoch') < poll.index('this.Schedule()') < poll.index(writes[1])
    restore = method(edited, 'OnJohnnyVoiceRestoreRequest')
    assert restore.index('if !this.running') < restore.index('this.epoch += 1') < restore.index('this.Schedule()')
    assert 'this.epoch += 1;' in method(edited, 'OnDetach')


def compile_overlay(game, package):
    log = game / 'r6/logs/redscript_rCURRENT.log'
    plain(log)
    log_hash = sha(log)
    registered = {(game / 'r6/scripts' / line.strip()).resolve()
                  for line in log.read_text(encoding='utf-8-sig').splitlines()
                  if line.strip().lower().endswith('.reds')}
    discovered = {p.resolve() for parent in ('r6/scripts', 'red4ext/plugins')
                  for p in (game / parent).rglob('*.reds')}
    assert len(registered) == 148 and registered == discovered and game / SCRIPT in registered
    scc = game / 'engine/tools/scc.exe'
    caches = [game / 'r6/cache' / n for n in ('final.redscripts', 'final.redscripts.ts')]
    pins = {}
    for file in sorted(registered | {scc, *caches}):
        plain(file)
        pins[file.relative_to(game).as_posix()] = sha(file)
    cache = COMPILE / 'cache'
    cache.mkdir(parents=True)
    for file in caches:
        shutil.copyfile(file, cache / file.name)
        assert sha(cache / file.name) == pins[file.relative_to(game).as_posix()]
    scripts = COMPILE / 'scripts'
    staged = {}
    for file in sorted(registered):
        relative = file.relative_to(game).as_posix()
        source = package / relative if relative == SCRIPT else file
        dest = scripts / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        expected = sha(source) if relative == SCRIPT else pins[relative]
        assert sha(dest) == expected, relative
        staged[relative] = expected
    inputs = COMPILE / 'compile_paths.txt'
    inputs.write_bytes(b'')
    compiled = cache / 'compiled.redscripts'
    cmd = [scc, '-compile', scripts, '-compilePathsFile', inputs, '-customCacheDir',
           cache, '-outputCacheFile', compiled, cache / 'final.redscripts']
    process = subprocess.run(list(map(str, cmd)), capture_output=True, text=True,
                             encoding='utf-8', errors='replace', timeout=180,
                             creationflags=subprocess.CREATE_NO_WINDOW)
    output = process.stdout + process.stderr
    (COMPILE / 'scc.log').write_text(output, encoding='utf-8')
    assert sha(log) == log_hash and all(sha(game / rel) == pin for rel, pin in pins.items())
    passed = process.returncode == 0 and 'Compilation complete' in output and compiled.is_file()
    write(COMPILE / 'result.json', {
        'status': 'PASS' if passed else 'FAIL', 'source_count': len(staged), 'registry_sha256': log_hash,
        'input_pins': pins, 'staged_hashes': staged, 'compiled_sha256': sha(compiled) if passed else None,
    })
    assert passed, output[-4500:]


def main():
    assert not PACKAGE.exists() and not COMPILE.exists()
    assert sha(BASELINE) == BASELINE_SHA
    baseline = read(BASELINE)
    assert baseline['core_epoch'] == 'QP2_REED_CRASH_AND_JOHNNY_WORLD'
    game = Path(baseline['game_root'])
    files = {row['path']: row['sha256'] for row in baseline['core_files']}
    assert len(files) == 51 and files[SCRIPT] == OLD_SHA
    for row in baseline['core_files'] + baseline['required_files']:
        path = game / row['path']
        plain(path)
        assert path.resolve().is_relative_to(game) and sha(path) == row['sha256'], path
        assert path.stat().st_size == row['bytes'], path
    old = (game / SCRIPT).read_bytes()
    edited = repair(old)
    check_source(old, edited)
    for rel, digest in files.items():
        dest = PACKAGE / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if rel == SCRIPT:
            dest.write_bytes(edited)
        else:
            shutil.copyfile(game / rel, dest)
            assert sha(dest) == digest, rel
    patch = unified_diff(old.decode('utf-8').splitlines(keepends=True),
                         edited.decode('utf-8').splitlines(keepends=True), 'a/' + SCRIPT, 'b/' + SCRIPT)
    (HERE / 'source.patch').write_text(''.join(patch), encoding='utf-8', newline='\n')
    compile_overlay(game, PACKAGE)
    write(HERE / 'verification.json', {
        'status': 'VERIFIED_OFFLINE', 'baseline': str(BASELINE), 'before_sha256': OLD_SHA,
        'after_sha256': sha(PACKAGE / SCRIPT), 'changed_paths': [SCRIPT], 'package': str(PACKAGE),
        'registered_sources': 148, 'script_hooks_and_tower_gate': 'UNCHANGED', 'gameplay': 'UNVERIFIED',
    })
    print('Prepared the one-file load repair and compiled all 148 registered sources.')


if __name__ == '__main__':
    main()
