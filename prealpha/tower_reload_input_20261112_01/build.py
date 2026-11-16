"""Stage the completed-Tower reload input repair against the installed Core."""

import argparse
from difflib import unified_diff
import importlib.util
from pathlib import Path
import shutil
import subprocess


HERE = Path(__file__).resolve().parent
PRE = HERE.parent
PREVIOUS = 'QP2_TOWER_HAND_APPEARANCE'
EPOCH = 'QP2_TOWER_RELOAD_INPUT'
BASELINE = PRE / 'tower_hand_appearance_20261112_03/deployment_01/installed_manifest_01.json'
BASELINE_SHA = 'A9946B30B826A081C40D1117AE49CD58729D5B009846733865F86BFDBA8972A0'
TEMPLATE = PRE / 'johnny_load_crash_20261111_01/deploy_core.ps1'
TEMPLATE_SHA = '8C94862FC57931194D6892B2B485C8E155F1CAC1903D1323DE6BB2E5F1E9D7C5'
TEMPLATE_MANIFEST_SHA = 'A18B646B307FE336F4D34BDFD01676322E0368C40204AA1C0CE92BF36FB79DB0'
COVER = 'r6/scripts/PTFR_Consolidated/PTFR_LoadingCoverLC1.reds'
CHANGES = {COVER}

spec = importlib.util.spec_from_file_location(
    'cyberware_build_helpers', PRE / 'cyberware_treatment_20261111_01/prepare.py'
)
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)
sha, read, write, one = common.digest, common.read_json, common.write_json, common.one


def edit(source):
    source = one(source, '''    let game=this.GetGameInstance();let profile=ProfilePolicy.Get(game);let body=BodyPolicy.Get(game);let housing=HousingState.Get(game);
    // A completed save may load in combat, with a weapon, or in a vehicle.
    // Revalidate its receipts and physical state without demanding a new respec.
    this.continuation=this.Fact(n"PTFRPA2_Finished")==1 && IsDefined(profile) && profile.PTFRPAComplete() &&
      IsDefined(body) && body.PTFRR3Complete() && IsDefined(housing) && housing.HousingReadyForReveal();''',
                 '    this.continuation=false;')
    source = one(source, '''    if this.started<0.0 { this.started=this.Now();this.engineStarted=this.EngineNow(); }
    if IsDefined(this.popup) { return; }''', '''    if this.started<0.0 {
      this.started=this.Now();this.engineStarted=this.EngineNow();
      // Classify once, when the arrival facts first become available in this
      // session. A new handoff retains its cover through final acknowledgement.
      this.continuation=this.Fact(n"PTFRPA2_Finished")==1;
      if this.continuation {
        this.SetStage("Checking restored Tower save","Setup checks are running in the background.");
      }
    }
    if this.continuation || IsDefined(this.popup) { return; }''')
    source = one(source, '''  public func Accepts(epoch:Int32) -> Bool { return this.running && epoch==this.epoch && !this.leaving && !this.released && this.Required(); }''',
                 '''  public func Accepts(epoch:Int32) -> Bool { return this.running && epoch==this.epoch && !this.leaving && !this.released && !this.continuation && this.Required(); }''')
    return one(source, '''    if !this.Required() { this.Drop();return; }this.Ensure();
    if !this.visible { return; }
    // A render opportunity before the native fade may be released. The graph
    // waits on this owned acknowledgement, never on profile or Tier1 readiness.
    if this.rendered && this.Fact(n"PTFRLC1_CoverReady")!=1 {
      GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(n"PTFRLC1_CoverReady",1);
    }
    if !this.rendered { this.SetStage("Preparing the loading cover","Waiting for the interface to draw.");this.Heartbeat();return; }
    if !this.Check() {''', '''    if !this.Required() { this.Drop();return; }
    this.Ensure();
    if !this.continuation {
      if !this.visible { return; }
      // The first arrival acknowledges a drawn cover before releasing the native fade.
      if this.rendered && this.Fact(n"PTFRLC1_CoverReady")!=1 {
        GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(n"PTFRLC1_CoverReady",1);
      }
      if !this.rendered { this.SetStage("Preparing the loading cover","Waiting for the interface to draw.");this.Heartbeat();return; }
    }
    if !this.Check() {''')


def check_source(old, new):
    def block(source, start, end):
        return source.split(start, 1)[1].split(end, 1)[0]

    for start, end in (
        ('public static func GameplayReleased(', 'private func OnAttach('),
        ('private func Check()', 'private func Schedule()'),
        ('    if !this.Check() {', '  public func Status()'),
        ('public class SetupTickLC1', '@wrapMethod(PopupsManager)'),
        ('@wrapMethod(PopupsManager)', '\x00'),
    ):
        assert block(old, start, end) == block(new, start, end), start
    assert 'persistent let' not in new
    restored = block(new, 'public func Restored()', 'protected cb func OnStarted(')
    assert 'this.Drop();this.epoch+=1;this.released=false;' in restored
    assert 'this.started=-1.0;' in restored and 'this.continuation=false;' in restored
    ensure = block(new, 'public func Ensure()', 'public func Attached(')
    assert ensure.index('!this.Required()') < ensure.index('if this.started<0.0')
    assert ensure.index('this.continuation=this.Fact(n"PTFRPA2_Finished")==1;') < ensure.index('if this.continuation || IsDefined(this.popup)') < ensure.index('SetupPopupPoolLC1.Get().Show')
    poll = block(new, 'public func Poll(epoch:Int32)', 'public func Status()')
    assert poll.index('this.Ensure()') < poll.index('if !this.continuation {') < poll.index('if !this.visible')
    assert poll.index('if this.rendered &&') < poll.index('SetFact(n"PTFRLC1_CoverReady",1)') < poll.index('    }\n    if !this.Check()')
    assert new.count('SetFact(') == old.count('SetFact(') == 1
    return {
        'completed_arrival': 'BACKGROUND_CHECKS_WITH_NO_POPUP',
        'first_arrival': 'VISIBLE_FRAME_ACK_AND_ALL_SETUP_CHECKS',
        'gameplay_release_and_activity_gates': 'MATCH',
        'saved_fields_and_popup_teardown': 'MATCH',
        'gameplay': 'UNVERIFIED',
    }


def compile_overlay(game, package, output):
    registry = game / 'r6/logs/redscript_rCURRENT.log'
    common.plain(registry, game)
    registry_hash = sha(registry)
    lines = registry.read_text(encoding='utf-8-sig').splitlines()
    registered = {(game / 'r6/scripts' / line.strip()).resolve()
                  for line in lines if line.strip().lower().endswith('.reds')}
    discovered = {p.resolve() for directory in ('r6/scripts', 'red4ext/plugins')
                  for p in (game / directory).rglob('*.reds')}
    assert registered == discovered and game / COVER in registered
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

    original = (game / COVER).read_text(encoding='utf-8')
    edited = edit(original)
    checks = check_source(original, edited)
    package = candidate / 'package'
    for row in baseline['core_files']:
        relative = row['path']
        dest = package / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if relative == COVER:
            dest.write_text(edited, encoding='utf-8', newline='\n')
            assert dest.read_text(encoding='utf-8') == edited
        else:
            shutil.copyfile(game / relative, dest)
            assert sha(dest) == row['sha256'], relative
    patch = unified_diff(original.splitlines(keepends=True), edited.splitlines(keepends=True), 'a/' + COVER, 'b/' + COVER)
    (candidate / 'source.patch').write_text(''.join(patch), encoding='utf-8', newline='\n')
    count = compile_overlay(game, package, compile_output)
    write(candidate / 'verification.json', {
        'baseline_sha256': BASELINE_SHA, 'script_hashes': {COVER: sha(package / COVER)},
        'registered_sources': count, 'checks': checks, 'compile': 'PASS', 'gameplay': 'UNVERIFIED',
    })
    print(f'Completed-Tower reload repair compiled with all {count} registered sources.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('attempt', type=int)
    build(parser.parse_args().attempt)
