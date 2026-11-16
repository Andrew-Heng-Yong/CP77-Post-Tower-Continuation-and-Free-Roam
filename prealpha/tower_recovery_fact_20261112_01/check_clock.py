"""Check recovery checkpoint arithmetic and save transitions in a model."""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class SavedClock:
    start: int | None = None
    days: int = 0
    checkpoint: int | None = None


def check_clock(source):
    duration = int(re.search(r'func DurationDays\(\) -> Int32 \{ return (\d+); \}', source)[1])
    checkpoint_code = source.split('func CheckpointDay(seconds: Int32) -> Int32 {', 1)[1].split('}', 1)[0]
    seconds_per_day = int(re.search(r'let secondsPerDay = (\d+);', checkpoint_code)[1])
    hour, minute = map(int, re.search(r'let checkpointTime = (\d+) \* 3600 \+ (\d+) \* 60;', checkpoint_code).groups())
    assert (duration, seconds_per_day, hour, minute) == (30, 86400, 11, 55)
    assert 'return seconds % secondsPerDay < checkpointTime ? day - 1 : day;' in checkpoint_code
    sync = source.split('private func SyncRecoveryDay(', 1)[1].split('public func RecoveryStatus()', 1)[0]
    assert 'let fact = n"PTFRRecovery_Day";' in sync
    assert 'let days = Clamp(Max(this.recoveryDays, factValue), 0, maximum);' in sync
    assert 'let initializing = !this.recoveryDailyClockInitialized;' in sync
    assert '} else if checkpoint > this.recoveryLastCheckpointDay {' in sync
    assert 'days += Min(maximum - days, checkpoint - this.recoveryLastCheckpointDay);' in sync
    assert sync.index('this.recoveryDays = days;') < sync.index('quests.SetFact(fact, days);')
    assert 'if initializing || factValue != days { quests.SetFact(fact, days); }' in sync

    def stamp(day, hour, minute, second=0):
        return day * seconds_per_day + hour * 3600 + minute * 60 + second

    def update(state, fact, seconds):
        today, seconds_today = divmod(seconds, seconds_per_day)
        checkpoint = today - (seconds_today < hour * 3600 + minute * 60)
        days = min(duration, max(0, state.days, fact))
        if state.checkpoint is None:
            if state.start is not None and seconds >= state.start:
                days = min(duration, max(days, (seconds - state.start) // seconds_per_day))
            start = seconds if state.start is None else state.start
            return SavedClock(start, days, checkpoint), True
        if checkpoint > state.checkpoint:
            days = min(duration, days + checkpoint - state.checkpoint)
        return SavedClock(state.start, days, max(checkpoint, state.checkpoint)), fact != days

    before, _ = update(SavedClock(), 0, stamp(12, 11, 54, 59))
    exact, publish = update(before, 0, stamp(12, 11, 55))
    assert (before.days, exact.days, publish) == (0, 1, True)
    assert update(exact, 1, stamp(12, 12, 0)) == (exact, False)
    assert update(exact, 1, stamp(13, 0, 0)) == (exact, False)

    assert update(before, 0, stamp(12, 18, 30))[0].days == 1
    jumped, _ = update(before, 0, stamp(16, 11, 54, 59))
    assert jumped.days == 4
    assert update(jumped, 4, stamp(16, 11, 55))[0].days == 5
    assert update(jumped, 4, stamp(10, 18, 0)) == (jumped, False)
    assert update(jumped, 4, stamp(16, 11, 54, 59)) == (jumped, False)
    assert update(exact, 0, stamp(12, 12, 0)) == (exact, True)

    completed, _ = update(jumped, 30, stamp(16, 11, 54, 59))
    assert completed.days == 30
    capped, publish = update(completed, 30, stamp(58, 12, 0))
    assert capped.days == 30 and not publish
    assert update(jumped, 4, stamp(58, 12, 0))[0].days == 30
    assert update(jumped, 2147483647, stamp(16, 11, 54, 59))[0].days == 30

    legacy = SavedClock(start=stamp(10, 10, 0), days=5)
    migrated, publish = update(legacy, 0, stamp(17, 11, 54, 59))
    assert (migrated.days, migrated.start, publish) == (7, legacy.start, True)
    assert update(migrated, 7, stamp(17, 11, 55))[0].days == 8
    assert update(SavedClock(start=legacy.start, days=19), 0, stamp(17, 12, 0))[0].days == 19
    assert update(legacy, 30, stamp(17, 11, 54, 59))[0].days == 30
    assert update(SavedClock(start=legacy.start, days=58), 0, stamp(17, 12, 0))[0].days == 30

    initialized_on_checkpoint, _ = update(SavedClock(), 0, stamp(0, 11, 55))
    assert initialized_on_checkpoint.days == 0
    assert update(initialized_on_checkpoint, 0, stamp(1, 11, 55))[0].days == 1
    return {
        'scope': 'SOURCE_CHECKS_AND_CLOCK_MODEL',
        'exact_checkpoint_and_midnight': 'PASS',
        'single_and_multiple_forward_skips': 'PASS',
        'rewind_and_reload_without_repeat_credit': 'PASS',
        'recoverable_fact_publication': 'PASS',
        'cap_and_external_override': 'PASS',
        'legacy_migration_and_next_checkpoint': 'PASS',
    }
