"""Check the exact changed scopes and the evening checkpoint transitions."""

from check_clock import check_clock


def block(source, start, end):
    return source.split(start, 1)[1].split(end, 1)[0]


def check_source(old_recovery, recovery, old_cover, cover):
    for start, end in (
        ('private func AdvanceRecovery(', 'public abstract class RecoverySettings'),
        ('public static func ElapsedDays(', 'public class RecoveryVital'),
    ):
        assert block(old_recovery, start, end) == block(recovery, start, end), start
    assert [line for line in old_recovery.splitlines() if 'persistent let' in line] == [
        line for line in recovery.splitlines() if 'persistent let' in line
    ]
    update = block(recovery, 'public func Update(player: ref<PlayerPuppet>, target:', 'public func Ready()')
    assert update.index('if AbsF(maximum - target)') < update.index('this.ReadBack(')
    assert 'pending > 0' not in update
    readback = block(recovery, 'private func ReadBack(', 'private func RemoveOwned(')
    assert 'this.Stop(' not in readback and 'if this.pending <= 0 { return; }' in readback
    assert readback.index('this.pending = 0;') < readback.index('if excess > 0.01')
    assert readback.count('RequestChangingStatPoolValue(') == 1 and 'this.pool, -excess' in readback
    assert 'clampSent' not in recovery

    for start, end in (
        ('public static func GameplayReleased(', 'private func OnAttach('),
        ('public func Ensure()', 'private func SetStage('),
        ('private func Check()', 'private func Schedule()'),
        ('    if this.leaving || this.released { return; }', '  public func TraceFastTravel('),
    ):
        after_end = '  public func Status()' if start.startswith('    if this.leaving') else end
        if start.startswith('    if this.leaving'):
            assert block(old_cover, start, after_end) == block(cover, start, end)
        else:
            assert block(old_cover, start, end) == block(cover, start, end), start
    show = block(cover, 'protected cb func OnShow() -> Void {', 'protected cb func OnCoverFrame(')
    assert show.index('if !this.ActiveCover()') < show.index('root.SetVisible(false)') < show.index('root.SetVisible(true)')
    dismiss = block(cover, 'public func Dismiss()', 'public class SetupPopupCloseLC1')
    assert dismiss.index('SetVisible(false)') < dismiss.index('this.Detach()')
    input_handler = block(cover, 'protected cb func OnGlobalReleaseInput(', 'public func UpdateText(')
    assert input_handler.index('!this.ActiveCover()') < input_handler.index('evt.Handle()')
    trace = block(cover, 'public func TraceFastTravel(', 'public func Status()')
    assert all(key in trace for key in ('PTFRPA2_Finished', 'FastTravelLoadingScreenStarted',
                                       'FastTravelLoadingScreenFinished', 'HasPopup()', 'GetWorldPosition()'))
    assert all(call not in trace for call in ('SetFact(', 'SetBool(', 'TeleportTo', 'NotifyFastTravelStart'))
    native_start = block(cover, '@wrapMethod(FastTravelSystem)', 'protected cb func OnLoadingScreenFinished(')
    assert native_start.count('wrappedMethod();') == 1
    native_finish = block(cover, 'protected cb func OnLoadingScreenFinished(', '\x00')
    assert native_finish.count('wrappedMethod(value)') == 1 and 'return result;' in native_finish
    assert cover.count('SetFact(') == old_cover.count('SetFact(') == 1
    return {
        'clock': check_clock(recovery),
        'pool': 'LATEST_CAP_APPLIED_BEFORE_READBACK; ONE_DOWNWARD_CORRECTION; NO_TIMEOUT_FAULT',
        'persistent_schema_and_profile_admission': 'MATCH',
        'cover': 'STALE_ROOT_HIDDEN_BEFORE_DETACH; LIVE_INPUT_HANDLER_REQUIRES_OWNER',
        'fast_travel': 'NATIVE_CALLS_PRESERVED; READ_ONLY_TRACE',
        'gameplay': 'UNVERIFIED',
    }
