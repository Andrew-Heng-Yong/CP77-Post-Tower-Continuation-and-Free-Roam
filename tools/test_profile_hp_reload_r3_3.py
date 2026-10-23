"""R3.3 HP-only reload repair: exact delta, models and staged native compilers.

Never execute predecessor builders/tests or write the game's caches/saves.
Models and compiler success are not an in-game death/checkpoint test.
"""
import hashlib
import itertools
import json
import math
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from test_restrictions_r1 import function
from test_restrictions_profile_r3 import source_checks

ROOT = Path(__file__).resolve().parents[1]
GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
OUT = ROOT / 'research/restriction_profiles/profile_hp_reload_r3_3'
SOURCE = 'build/ProfileHpReloadR3_3/ProfilePhysical.reds'
TARGET = 'r6/scripts/PTFR_Restrictions_R3/ProfilePhysical.reds'
OLD = '40EE422B1134BE27783E427767FDD2024C6D83FA72D86CE19C7EA230A616DF84'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def read(p):
    return Path(p).read_text(encoding='utf-8-sig')


def check_delta(candidate, old):
    helper = '  // R3.3: a restored, already-approved HP policy must work in combat too.'
    start, end = candidate.index(helper), candidate.index('  private func CorrectPending()')
    normalized = candidate[:start] + candidate[end:]
    normalized = normalized.replace('this.pendingClamp <= 0 || !ProfilePhysical.HealthRuntimeReady(this.player)',
                                    'this.pendingClamp <= 0 || !IsDefined(this.player) || this.player.IsDead()', 1)
    normalized = normalized.replace('    if !ProfilePhysical.HealthRuntimeReady(player) { this.ready = false; this.detail = "Waiting for live player and Health pool registration"; return; }',
                                    '    if player.IsDead() || player.IsReplacer() { return; }', 1)
    normalized = normalized.replace('      // Reapply after restore without a combat/holster gate. The caller retains\n      // saved opt-in/profile/stage checks; reconcile only our owned factor.',
                                    '      // Initial activation waits for safe gameplay. Subsequent buff changes\n      // reconcile the owned factor from readback, never from a stacked penalty.\n      if !IsDefined(this.health) && !BodyPolicy.Safe(player) { this.detail = "Waiting to activate HP in safe gameplay"; return; }', 1)
    normalized = normalized.replace('return "HP R3.3 | " + this.detail;', 'return this.detail;', 1)
    assert normalized == old, 'Unreviewed physical module delta'
    ready = function(candidate, 'HealthRuntimeReady')
    for guard in ('!IsDefined(player)', '!player.IsAttached()', 'player.IsDead()', 'player.IsReplacer()',
                  'GetLocalPlayerMainGameObject() != player', '!IsDefined(stats)', '!IsDefined(pools)',
                  'maximum > 0.00', 'maximum < 1000000.00', 'poolMaximum > 0.00', 'poolMaximum < 1000000.00'):
        assert guard in ready, guard
    for forbidden in ('IsInCombat', 'IsSlotEmpty', 'IsTokensActivationBlocked', 'BodyPolicy.Safe', 'Request', 'AddModifier', 'RemoveModifier'):
        assert forbidden not in ready
    update = function(candidate, 'Update')
    assert update.index('if !useHealth') < update.index('if !ProfilePhysical.HealthRuntimeReady(player)')
    assert update.index('if !ProfilePhysical.HealthRuntimeReady(player)') < update.index('this.BeginClamp()')
    assert 'BodyPolicy.Safe' not in update
    clamp = function(candidate, 'CorrectPending')
    assert clamp.index('!ProfilePhysical.HealthRuntimeReady(this.player)') < clamp.index('RequestChangingStatPoolValue')
    assert clamp.index('!ProfilePhysical.HealthRuntimeReady(this.player)') < clamp.index('this.pendingClamp -= 1')
    return True


def model_checks():
    # Explicit regression: old initial-modifier gate fails when a checkpoint
    # resumes combat, a drawn weapon, or a phone-content blocker. The new gate
    # admits all these when the actor/pools are ready and the saved policy opts in.
    admissions = 0
    for combat, drawn, phone, opted_in, active, stage, matches in itertools.product(
            (False, True), (False, True), (False, True), (False, True), (False, True), range(6), (False, True)):
        use = opted_in and active and 3 <= stage <= 4 and matches
        old_applies = use and not (combat or drawn or phone)
        new_applies = use
        if use and (combat or drawn or phone):
            assert not old_applies and new_applies
        if not use:
            assert not new_applies
        admissions += 1
    readiness = 0
    for defined, attached, dead, replacer, local, stats, pools in itertools.product((False, True), repeat=7):
        for maximum, pool in ((368., 368.), (0., 0.), (368., 0.), (-1., 10.), (float('nan'), 10.), (10., float('inf'))):
            ready = (defined and attached and not dead and not replacer and local and stats and pools
                     and 0 < maximum < 1e6 and 0 < pool < 1e6)
            pending = 12
            if ready:
                pending -= 1
            else:
                assert pending == 12  # loading/death cannot exhaust the budget
            readiness += 1
    feedback = 0
    for raw, foreign, current in itertools.product((80., 150., 368., 5000.), (.5, 1., 1.5, 3.), (1., 45., 100., 150.)):
        # Fresh physical module after each restore owns no saved multiplier.
        for reload in range(3):
            factor = 1.
            maximum = raw * foreign
            factor *= 150. / maximum
            maximum = raw * foreign * factor
            assert math.isclose(maximum, 150.)
            for tick in range(10):
                assert math.isclose(maximum, 150.)  # no second modifier needed
            scaled = current * 1.5
            correction = -max(0., scaled - current)
            assert correction <= 0 and math.isclose(scaled + correction, current)
        feedback += 1
    return dict(admission_cases=admissions, readiness_cases=readiness, feedback_reload_cases=feedback,
                engine_execution=False)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT / 'install_receipt.json').exists(), 'Installed evidence pinned'
    assert sha(GAME / TARGET) == OLD
    assert sha(ROOT / 'redscript/PTFR_Restrictions_R3/ProfilePhysical.reds') == OLD
    old, candidate = read(GAME / TARGET), read(ROOT / SOURCE)
    assert check_delta(candidate, old)
    # Run predecessor invariant functions only, never their main/build/report paths.
    sources = {p.name: read(p) for i in (1, 2, 3) for p in (GAME / f'r6/scripts/PTFR_Restrictions_R{i}').glob('*.reds')}
    sources['ProfilePhysical.reds'] = candidate
    assert source_checks(sources)
    policy = sources['ProfilePolicy.reds']
    for guard in ('this.enabled && this.vitalsRequested && this.stage >= 3 && this.stage <= 4',
                  'this.MatchesDefinition() && ProfilePolicy.Active(player)',
                  'if !CyberwarePolicy.Completed(game) || !BodyPolicy.Safe(player)',
                  'this.physical = new ProfilePhysical()', 'if !this.running || epoch != this.epoch'):
        assert guard in policy
    assert 'profile.Restored()' in sources['DevelopmentHooks.reds']
    assert 'return 150.000000;' in sources['ProfileDefinition.generated.reds']
    mutants = []
    for guard in ('!player.IsAttached()', 'player.IsDead()', 'player.IsReplacer()',
                  'GetLocalPlayerMainGameObject() != player', 'poolMaximum > 0.00'):
        try:
            check_delta(candidate.replace(guard, 'REMOVED', 1), old)
        except AssertionError:
            mutants.append(guard)
        else:
            raise AssertionError('Readiness mutant escaped: ' + guard)
    models = model_checks()
    pinned = {}
    for name in ('profile_r3', 'profile_hp_r3_1', 'profile_implant_r3_2'):
        folder = ROOT / 'research/restriction_profiles' / name
        for filename in ('tests.json', 'install_receipt.json', 'deployment_tests.json'):
            p = folder / filename
            pinned[str(p)] = sha(p)
    u7 = ROOT / 'research/gig_restoration/native_support_u7'
    for filename in ('manifest.json', 'tests.json', 'deployment_tests.json', 'install_receipt.json', 'assessment.json'):
        p = u7 / filename
        pinned[str(p)] = sha(p)
    save = Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077\ManualSave-20\sav.dat')
    pinned[str(save)] = sha(save)
    assert pinned[str(save)] == '0E531F856D4233C9C339F45C29405E590861F40B7918CFA082F736BF64D51096'
    for p in (ROOT / 'profiles').rglob('*.json'):
        pinned[str(p)] = sha(p)
    for name in ('test_restrictions_r1.py', 'test_restrictions_profile_r3.py'):
        p = ROOT / 'tools' / name
        pinned[str(p)] = sha(p)
    stage = Path(tempfile.mkdtemp(prefix='compile_', dir=OUT))
    cache = stage / 'cache'
    cache.mkdir()
    protected = {str(p): sha(p) for p in (GAME / 'r6/cache').iterdir() if p.is_file()}
    for name in ('final.redscripts', 'final.redscripts.ts'):
        shutil.copy2(GAME / 'r6/cache' / name, cache / name)
    dependencies = {}
    for p in (GAME / 'r6/scripts').rglob('*.reds'):
        destination = stage / 'scripts' / p.relative_to(GAME / 'r6/scripts')
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, destination)
        dependencies[str(p)] = sha(p)
    shutil.copy2(ROOT / SOURCE, stage / 'scripts/PTFR_Restrictions_R3/ProfilePhysical.reds')
    plugins = read(ROOT / 'research/restriction_profiles/implementation_r1/compile_paths.txt').splitlines()[2:]
    for folder in plugins:
        for p in Path(folder).rglob('*.reds'):
            dependencies[str(p)] = sha(p)
    cli = ROOT / 'research/finalboards_dismissal/tooling/redscript-cli.exe'
    args = [str(cli), 'compile']
    for name in ('PTFR_Restrictions_R1', 'PTFR_Restrictions_R2', 'PTFR_Restrictions_R3'):
        args += ['-s', str(stage / 'scripts' / name)]
    args += ['-s', str(GAME / 'red4ext/plugins/Codeware/Scripts'), '-b', str(cache / 'final.redscripts'), '-o', str(stage / 'headless.redscripts')]
    run = subprocess.run(args, capture_output=True, text=True, timeout=90)
    log = run.stdout + run.stderr
    (OUT / 'headless_compile.log').write_text(log, encoding='utf-8')
    assert run.returncode == 0 and 'Output successfully saved' in log and '[ERROR' not in log, log[-8000:]
    paths = stage / 'compile_paths.txt'
    paths.write_text('\n'.join(plugins) + '\n', encoding='utf-8')
    compiled = cache / 'compiled.redscripts'
    args = [str(GAME / 'engine/tools/scc.exe'), '-compile', str(stage / 'scripts'), '-compilePathsFile', str(paths),
            '-customCacheDir', str(cache), '-outputCacheFile', str(compiled), str(cache / 'final.redscripts')]
    run = subprocess.run(args, capture_output=True, text=True, timeout=120)
    log = run.stdout + run.stderr
    (OUT / 'compile.log').write_text(log, encoding='utf-8')
    assert run.returncode == 0 and 'Compilation complete' in log and 'Output successfully saved' in log and '[ERROR' not in log, log[-8000:]
    assert 'EquipmentEx.reds' in log
    flat = OUT / 'compiled_flat.script'
    run = subprocess.run([str(cli), 'decompile', '-i', str(compiled), '-o', str(flat)], capture_output=True, text=True, timeout=90)
    assert run.returncode == 0
    text = read(flat)
    for symbol in ('HealthRuntimeReady', 'HP R3.3 | ', 'PTFR.RestrictionsR3.ProfilePhysical', 'class PTFR.ActivityStateR3.NativeSupportU7', 'EquipmentEx.OutfitSystem'):
        assert symbol in text, symbol
    for p, digest in {**protected, **dependencies, **pinned}.items():
        assert sha(p) == digest, p
    result = dict(status='PASS_HP_RELOAD_R3_3_OFFLINE_LIVE_PENDING', utc=datetime.now(timezone.utc).isoformat(),
                  file=dict(source=SOURCE, relative=TARGET, predecessor=OLD, sha256=sha(ROOT / SOURCE)),
                  exact_delta=True, inherited_invariants=True, models=models, negative_variants=len(mutants),
                  cli=True, full_scc=True, equipmentex=True, compiled_readback=True, compiled_sha256=sha(compiled),
                  dependencies=dependencies, dependency_roots=[str(GAME / 'r6/scripts')] + plugins,
                  protected=protected, pinned=pinned, test_sha256=sha(__file__),
                  runtime_proof=False, game_writes=0, direct_save_writes=0)
    (OUT / 'tests.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('status', 'models', 'negative_variants', 'compiled_sha256')}, indent=2))


if __name__ == '__main__':
    main()
