"""Combine the pinned cyberware candidate with the Tower recovery scripts."""

import argparse
from difflib import unified_diff
import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
CYBERWARE = HERE.parent / 'cyberware_treatment_20261111_01'
DONOR = CYBERWARE / 'candidate_06'
EXPECTED_DONORS = {
    'r6/scripts/PTFR_Consolidated/PTFR_RestrictionsR1.reds':
        'C6BA8A5674792648643C988331080E4BBD107ED10214987ACEFF1E14AE9A7700',
    'r6/scripts/PTFR_Consolidated/PTFR_RestrictionsR3.reds':
        '291C7A8252DCA6EF32765CFE874F6A7E1F48045755F9C0D8AD2C7C0FFC0BBA4F',
}

# The donor module has no top-level filesystem effects. Reuse its exact-input
# compiler and hashing helpers without running its candidate builder.
spec = importlib.util.spec_from_file_location('cyberware_build_helpers', CYBERWARE / 'prepare.py')
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)
R1, R3 = common.R1, common.R3


def edit_r3(source):
    one = common.one
    section = common.replace_section
    source = one(source, '''  private let health: ref<gameStatModifierData>;
  private let healthFactor: Float;''', '''  private let health: ref<RecoveryVital>;
  private let stamina: ref<RecoveryVital>;''')
    source = one(source, '''  private let ready: Bool;
  private let fault: Bool;
  private let detail: String;
  private let ceiling: Float;
  private let pendingClamp: Int32;
  private let clampSent: Bool;''', '''  private let configurationFault: Bool;
  private let detail: String;''')
    source = section(source, '  private func DropHealth()', '    if !CyberwarePolicy.Active(player) {\n      this.ClearWeapon();', '''  private func DropVitals() -> Void {
    if IsDefined(this.health) { this.health.Disable(this.player); }
    if IsDefined(this.stamina) { this.stamina.Disable(this.player); }
  }
  public func Release() -> Void {
    this.ClearWeapon();
    if IsDefined(this.health) { this.health.Release(this.player); }
    if IsDefined(this.stamina) { this.stamina.Release(this.player); }
    if IsDefined(this.player) && IsDefined(this.smart) {
      GameInstance.GetStatsSystem(this.player.GetGame()).RemoveModifier(Cast<StatsObjectID>(this.player.GetEntityID()), this.smart);
    }
    this.health = null; this.stamina = null; this.smart = null; this.player = null;
    this.configurationFault = false;
  }
  public func Update(player: ref<PlayerPuppet>, useVitals: Bool, days: Int32) -> Void {
    if this.player != player { this.Release(); this.player = player; }
''')
    source = one(source, 'this.ClearWeapon(); this.DropHealth();', 'this.ClearWeapon(); this.DropVitals();')
    source = section(source, '    if !useHealth { this.DropHealth();', '  private func AddWeaponZero(', '''    if !useVitals {
      this.DropVitals();
      this.detail = "Recovery vitals off";
      return;
    }
    if !RecoverySettings.VitalsValid() {
      this.configurationFault = true;
      this.detail = "Invalid recovery vitals settings";
      return;
    }
    if days < 0 { this.detail = "Waiting for the retained Tower handoff clock"; return; }
    if !IsDefined(this.health) {
      this.health = RecoveryVital.Create(gamedataStatType.Health, gamedataStatPoolType.Health);
      this.stamina = RecoveryVital.Create(gamedataStatType.Stamina, gamedataStatPoolType.Stamina);
    }
    if !this.health.PoolReady(player) || !this.stamina.PoolReady(player) {
      this.detail = "Waiting for Health and Stamina pools";
      return;
    }
    this.health.Update(player, RecoverySettings.Health(days));
    this.stamina.Update(player, RecoverySettings.Stamina(days));
    this.detail = "Day " + ToString(days) + " | " + this.health.Status() + " | " + this.stamina.Status();
  }
''')
    source = section(source, '  private func Stop(message: String)', '\n// ORIGINAL: r6/scripts/PTFR_PreAlpha/PTFR_Restrictions_R3/ProfilePolicy.reds', '''  public func VitalsReady() -> Bool {
    return !this.configurationFault && IsDefined(this.health) && this.health.Ready() &&
      IsDefined(this.stamina) && this.stamina.Ready();
  }
  public func Faulted() -> Bool {
    return this.configurationFault || (IsDefined(this.health) && this.health.Faulted()) ||
      (IsDefined(this.stamina) && this.stamina.Faulted());
  }
  public func Status() -> String { return this.detail; }
}
''')
    source = one(source, '  private persistent let handAttempted: Bool;', '''  private persistent let handAttempted: Bool;
  private persistent let recoveryClockStarted: Bool;
  private persistent let recoveryStartSeconds: Int32;
  private persistent let recoveryDays: Int32;
  private let recoveryWarmup: Int32;''')
    source = one(source, '  private persistent let healthTarget: Float;',
                 '  private persistent let healthTarget: Float; // Legacy profile identity check')
    source = one(source, '''    this.running = true;
    this.Restored();
  }
  private func OnDetach()''', '''    this.running = true;
    this.ResetRuntime();
  }
  private func OnDetach()''')
    source = one(source, '''  public func Restored() -> Void {
    this.epoch += 1; this.queued = false; this.mutation = false;''', '''  public func Restored() -> Void { this.QueueRequest(new ProfileRestored()); }
  private func OnProfileRestored(request: ref<ProfileRestored>) -> Void {
    if this.running { this.ResetRuntime(); }
  }
  private func ResetRuntime() -> Void {
    this.epoch += 1; this.queued = false; this.mutation = false;
    this.recoveryWarmup = 4;''')
    source = one(source, '''  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    this.Schedule();''', '''  public func Poll(epoch: Int32) -> Void {
    let request = new ProfilePulse();
    request.epoch = epoch;
    this.QueueRequest(request);
  }
  private func OnProfilePulse(request: ref<ProfilePulse>) -> Void {
    if !this.running || request.epoch != this.epoch { return; }
    this.Schedule();''')
    source = one(source, 'this.physical = new ProfilePhysical(); this.actor = player; this.warmup = 4;',
                 'this.physical = new ProfilePhysical(); this.actor = player; this.warmup = 4; this.recoveryWarmup = 4;')
    source = one(source, '''    // Smart targeting is a Cyberware Only rule, not contingent on spending perks.
    this.physical.Update(player, this.enabled && this.vitalsRequested && this.stage >= 3 && this.stage <= 4 &&
      this.MatchesDefinition() && ProfilePolicy.Active(player), this.healthTarget);''', '''    let recoveryEligible = this.AdvanceRecovery(player);
    // Smart targeting is a Cyberware Only rule, independent of the vitals opt-in.
    this.physical.Update(player, this.enabled && this.vitalsRequested && this.stage >= 3 && this.stage <= 4 &&
      this.MatchesDefinition() && ProfilePolicy.Active(player), recoveryEligible ? this.recoveryDays : -1);''')
    source = one(source, '  private func OnProfileStep(step: ref<ProfileStep>) -> Void {', '''  private func AdvanceRecovery(player: ref<PlayerPuppet>) -> Bool {
    if !RecoveryVital.ActorReady(player) || !CyberwarePolicy.Completed(player.GetGame()) { return false; }
    let game = player.GetGame();
    let quests = GameInstance.GetQuestsSystem(game);
    if quests.GetFact(n"PTFRPA2_ControlReady") != 1 || quests.GetFact(n"PTFRPA2_Fault") != 0 { return false; }
    if this.recoveryWarmup > 0 {
      this.recoveryWarmup -= 1;
      return this.recoveryClockStarted;
    }
    let time = GameInstance.GetTimeSystem(game);
    if !IsDefined(time) { return this.recoveryClockStarted; }
    let seconds = GameTime.GetSeconds(time.GetGameTime());
    if seconds < 0 { return this.recoveryClockStarted; }
    if !this.recoveryClockStarted {
      this.recoveryStartSeconds = seconds;
      this.recoveryDays = 0;
      this.recoveryClockStarted = true;
      ModLog(n"PTFR_Restrictions_R3", "Recovery clock started at game second " + ToString(seconds));
    }
    let days = RecoverySettings.ElapsedDays(this.recoveryStartSeconds, seconds, this.recoveryDays);
    if days > this.recoveryDays { this.recoveryDays = days; }
    // The private native phase owns the appearance change and its acknowledgement.
    if RecoverySettings.BruiseDays() >= 0 && days >= RecoverySettings.BruiseDays() &&
      quests.GetFact(n"PTFRRecovery_BruiseApplied") == 0 && quests.GetFact(n"PTFRRecovery_BruiseReady") == 0 &&
      CyberwarePolicy.Safe(player) {
      quests.SetFact(n"PTFRRecovery_BruiseReady", 1);
    }
    return true;
  }
  public func RecoveryStatus() -> String {
    if !this.recoveryClockStarted { return "Recovery clock waiting for Tower handoff"; }
    let q = GameInstance.GetQuestsSystem(this.GetGameInstance());
    return "Recovery day " + ToString(this.recoveryDays) + " / " + ToString(RecoverySettings.DurationDays()) +
      " | bruise ready/applied=" + ToString(q.GetFact(n"PTFRRecovery_BruiseReady")) + "/" + ToString(q.GetFact(n"PTFRRecovery_BruiseApplied"));
  }
  private func OnProfileStep(step: ref<ProfileStep>) -> Void {''')
    source = one(source, 'this.detail = "HP module STOPPED; progression is not replayed. "',
                 'this.detail = "Recovery vitals stopped. "')
    source = one(source, 'this.detail = "Waiting for HP readback: "', 'this.detail = "Waiting for vitals readback: "')
    source = source.replace('this.physical.HealthReady()', 'this.physical.VitalsReady()')
    source = one(source, 'HP module enabled on completed migration; no refunds replayed.',
                 'Recovery vitals enabled on the completed migration.')
    source = one(source, 'Wait until the no-vitals migration completes before enabling HP.',
                 'Wait until the no-vitals migration completes before enabling recovery vitals.')
    source = one(source, 'this.Note("Profile queued; Body/Relic preserved. HP requested=" + ToString(vitals) + "; stamina untouched.");',
                 'this.Note("Profile queued; Body/Relic preserved. Recovery vitals requested=" + ToString(vitals));')
    source = one(source, '''  public func LC1PhysicalReady() -> Bool { return this.PTFRPAComplete() && IsDefined(this.physical) && this.physical.VitalsReady() && !this.physical.Faulted(); }''', '''  public func LC1PhysicalReady() -> Bool {
    return this.PTFRPAComplete() && (!this.vitalsRequested || (IsDefined(this.physical) && this.physical.VitalsReady()));
  }''')
    source = one(source, 'return this.enabled && this.vitalsRequested && this.MatchesDefinition() && this.stage >= 1 && this.stage <= 4;',
                 'return this.enabled && this.MatchesDefinition() && this.stage >= 1 && this.stage <= 4;')
    source = one(source, '''      " HP requested=" + ToString(this.vitalsRequested) + " | " + this.detail +''',
                 '''      " recovery vitals requested=" + ToString(this.vitalsRequested) + " | " + this.RecoveryStatus() + " | " + this.detail +''')
    source = one(source, '''    return BodyPolicy.Get(this.GetGameInstance()).PTFRR3MeasureNative() + " | R3 HP requested=" + ToString(this.vitalsRequested) +
      " target=" + ToString(this.healthTarget) + " | " + (IsDefined(this.physical) ? this.physical.Status() : "Physical module not attached");''', '''    return BodyPolicy.Get(this.GetGameInstance()).PTFRR3MeasureNative() + " | Recovery vitals requested=" + ToString(this.vitalsRequested) +
      " | " + this.RecoveryStatus() + " | " + (IsDefined(this.physical) ? this.physical.Status() : "Physical module not attached");''')
    source += '''

public class ProfilePulse extends ScriptableSystemRequest { public let epoch: Int32; }
public class ProfileRestored extends ScriptableSystemRequest {}

@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void {
  wrappedMethod(gameInstance);
  let profile = ProfilePolicy.Get(gameInstance);
  if IsDefined(profile) { profile.Restored(); }
}

'''
    return source + (HERE / 'RecoveryVitals.reds').read_text(encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('attempt', type=int)
    attempt = parser.parse_args().attempt
    assert attempt > 0
    candidate = HERE / f'candidate_{attempt:02}'
    overlay = candidate / 'overlay'
    compile_output = HERE / f'compile_{attempt:02}'
    assert not candidate.exists() and not compile_output.exists()
    assert common.digest(common.BASELINE) == common.BASELINE_HASH
    baseline = common.read_json(common.BASELINE)
    assert baseline['core_epoch'] == 'QP2_JOHNNY_LOAD_REPAIR'
    game = Path(baseline['game_root']).resolve()
    assert len(baseline['core_files']) == 51 and len(baseline['required_files']) == 26
    for row in baseline['core_files'] + baseline['required_files']:
        path = game / row['path']
        common.plain(path, game)
        assert common.digest(path) == row['sha256'] and path.stat().st_size == row['bytes'], path
    donor_evidence = common.read_json(DONOR / 'verification.json')
    assert donor_evidence['compile'] == 'PASS' and donor_evidence['baseline_sha256'] == common.BASELINE_HASH
    for rel, pin in EXPECTED_DONORS.items():
        path = DONOR / 'overlay' / rel
        assert common.digest(path) == pin == donor_evidence['changed_sources'][rel]['after']
        assert common.digest(game / rel) == donor_evidence['changed_sources'][rel]['before']
    r3 = (DONOR / 'overlay' / R3).read_text(encoding='utf-8')
    recovered = edit_r3(r3)
    (overlay / R1).parent.mkdir(parents=True)
    (overlay / R1).write_bytes((DONOR / 'overlay' / R1).read_bytes())
    (overlay / R3).write_text(recovered, encoding='utf-8', newline='\n')
    delta = unified_diff(r3.splitlines(keepends=True), recovered.splitlines(keepends=True),
                         'cyberware/' + R3, 'recovery/' + R3)
    (candidate / 'recovery.patch').write_text(''.join(delta), encoding='utf-8', newline='\n')
    assert common.digest(overlay / R1) == EXPECTED_DONORS[R1]
    assert (overlay / R3).read_text(encoding='utf-8') == recovered and recovered != r3
    source_count = common.compile_overlay(game, overlay, compile_output)
    common.write_json(candidate / 'verification.json', {
        'baseline_sha256': common.BASELINE_HASH, 'donor': str(DONOR),
        'script_hashes': {rel: common.digest(overlay / rel) for rel in EXPECTED_DONORS},
        'registered_sources': source_count, 'compile': 'PASS', 'gameplay': 'UNVERIFIED',
    })
    print(f'Compiled cyberware and recovery with all {source_count} registered inputs.')


if __name__ == '__main__':
    main()
