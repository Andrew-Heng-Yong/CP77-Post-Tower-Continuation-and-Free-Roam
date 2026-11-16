"""Stage the 11:55 recovery day counter against the installed Core."""

import argparse
from difflib import unified_diff
import importlib.util
from pathlib import Path
import shutil

from check_clock import check_clock


HERE = Path(__file__).resolve().parent
PRE = HERE.parent
PREVIOUS = 'QP2_TOWER_RELOAD_INPUT'
EPOCH = 'QP2_TOWER_RECOVERY_FACT'
BASELINE = PRE / 'tower_reload_input_20261112_01/deployment_01/installed_manifest_01.json'
BASELINE_SHA = '4EF19C369BC0AF8E6E1F888B6560C4DCB7FCD6243C74A65F6E662429C91E2B37'
TEMPLATE = PRE / 'johnny_load_crash_20261111_01/deploy_core.ps1'
TEMPLATE_SHA = '8C94862FC57931194D6892B2B485C8E155F1CAC1903D1323DE6BB2E5F1E9D7C5'
TEMPLATE_MANIFEST_SHA = 'A18B646B307FE336F4D34BDFD01676322E0368C40204AA1C0CE92BF36FB79DB0'

spec = importlib.util.spec_from_file_location(
    'cyberware_build_helpers', PRE / 'cyberware_treatment_20261111_01/prepare.py'
)
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)
R3 = common.R3
CHANGES = {R3}
sha, read, write, one = common.digest, common.read_json, common.write_json, common.one


def edit(source):
    source = one(source, '''  private persistent let recoveryDays: Int32;''', '''  private persistent let recoveryDays: Int32;
  private persistent let recoveryDailyClockInitialized: Bool;
  private persistent let recoveryLastCheckpointDay: Int32;''')
    source = one(source, '''    if !this.recoveryClockStarted {
      this.recoveryStartSeconds = seconds;
      this.recoveryDays = 0;
      this.recoveryClockStarted = true;
      ModLog(n"PTFR_Restrictions_R3", "Recovery clock started at game second " + ToString(seconds));
    }
    let days = RecoverySettings.ElapsedDays(this.recoveryStartSeconds, seconds, this.recoveryDays);
    if days > this.recoveryDays { this.recoveryDays = days; }''',
                 '    let days = this.SyncRecoveryDay(quests, seconds);')
    source = one(source, '  public func RecoveryStatus() -> String {', '''  private func SyncRecoveryDay(quests: ref<QuestsSystem>, seconds: Int32) -> Int32 {
    let fact = n"PTFRRecovery_Day";
    let factValue = quests.GetFact(fact);
    let maximum = RecoverySettings.DurationDays();
    let days = Clamp(Max(this.recoveryDays, factValue), 0, maximum);
    let checkpoint = RecoverySettings.CheckpointDay(seconds);
    let initializing = !this.recoveryDailyClockInitialized;
    if initializing {
      // Import elapsed recovery once for saves from before the daily counter.
      if this.recoveryClockStarted {
        days = Clamp(RecoverySettings.ElapsedDays(this.recoveryStartSeconds, seconds, days), 0, maximum);
      } else {
        this.recoveryStartSeconds = seconds;
        this.recoveryClockStarted = true;
      }
      this.recoveryLastCheckpointDay = checkpoint;
      this.recoveryDailyClockInitialized = true;
    } else if checkpoint > this.recoveryLastCheckpointDay {
      days += Min(maximum - days, checkpoint - this.recoveryLastCheckpointDay);
      this.recoveryLastCheckpointDay = checkpoint;
    }

    let previousDays = this.recoveryDays;
    // Keep the credited day and checkpoint together so a fact write can be retried.
    this.recoveryDays = days;
    if initializing || factValue != days { quests.SetFact(fact, days); }
    if initializing || previousDays != days {
      ModLog(n"PTFR_Restrictions_R3", "PTFRRecovery_Day=" + ToString(days) + " checkpoint day=" + ToString(this.recoveryLastCheckpointDay));
    }
    return days;
  }
  public func RecoveryStatus() -> String {''')
    return one(source, '  public static func ElapsedDays(startSeconds: Int32, nowSeconds: Int32, savedDays: Int32) -> Int32 {', '''  // Index of the latest 11:55 checkpoint, including the previous day before 11:55.
  public static func CheckpointDay(seconds: Int32) -> Int32 {
    let secondsPerDay = 86400;
    let checkpointTime = 11 * 3600 + 55 * 60;
    let day = seconds / secondsPerDay;
    return seconds % secondsPerDay < checkpointTime ? day - 1 : day;
  }

  public static func ElapsedDays(startSeconds: Int32, nowSeconds: Int32, savedDays: Int32) -> Int32 {''')


def check_source(old, new):
    def block(source, start, end):
        return source.split(start, 1)[1].split(end, 1)[0]

    for start, end in (
        ('private func OnProfilePulse(', 'private func AdvanceRecovery('),
        ('private func AdvanceRecovery(', '    if !this.recoveryClockStarted {'),
        ('    // The private native phase owns the appearance change and its acknowledgement.', '    return true;\n  }'),
        ('  public func RecoveryStatus()', 'public abstract class RecoverySettings'),
        ('  public static func ElapsedDays(', '\x00'),
    ):
        if start == 'private func AdvanceRecovery(':
            assert block(old, start, end) == block(new, start, '    let days = this.SyncRecoveryDay('), start
        else:
            assert block(old, start, end) == block(new, start, end), start
    old_fields = [line for line in old.splitlines() if 'persistent let' in line]
    new_fields = [line for line in new.splitlines() if 'persistent let' in line]
    added = [line for line in new_fields if line not in old_fields]
    assert added == ['  private persistent let recoveryDailyClockInitialized: Bool;',
                     '  private persistent let recoveryLastCheckpointDay: Int32;']
    assert [line for line in new_fields if line not in added] == old_fields
    return {
        'tower_admission_and_bruise_dispatch': 'MATCH',
        'vitals_curve_and_pool_updates': 'MATCH',
        'persistent_schema': 'TWO_ADDITIVE_CHECKPOINT_FIELDS; LEGACY_FIELDS_RETAINED',
        'clock_transition_fixtures': check_clock(new),
        'gameplay': 'UNVERIFIED',
    }


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

    original = (game / R3).read_text(encoding='utf-8')
    edited = edit(original)
    checks = check_source(original, edited)
    package = candidate / 'package'
    for row in baseline['core_files']:
        relative = row['path']
        dest = package / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if relative == R3:
            dest.write_text(edited, encoding='utf-8', newline='\n')
            assert dest.read_text(encoding='utf-8') == edited
        else:
            shutil.copyfile(game / relative, dest)
            assert sha(dest) == row['sha256'], relative
    patch = unified_diff(original.splitlines(keepends=True), edited.splitlines(keepends=True), 'a/' + R3, 'b/' + R3)
    (candidate / 'source.patch').write_text(''.join(patch), encoding='utf-8', newline='\n')
    count = common.compile_overlay(game, package, compile_output)
    write(candidate / 'verification.json', {
        'baseline_sha256': BASELINE_SHA, 'script_hashes': {R3: sha(package / R3)},
        'registered_sources': count, 'checks': checks, 'compile': 'PASS', 'gameplay': 'UNVERIFIED',
    })
    print(f'Recovery day counter compiled with all {count} registered sources.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('attempt', type=int)
    build(parser.parse_args().attempt)
