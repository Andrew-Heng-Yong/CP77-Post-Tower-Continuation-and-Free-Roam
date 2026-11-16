#include "WaitTransfer.hpp"
#include "fixture_input.hpp"

#define main PriorFixtureMain
#include "../universal_resume_retirement_20261114_01/build_05/NativeDelayChecks.cpp"
#undef main

#define main GameClockFixtureMain
#define ImageSize GameClockImageSize
#include "../universal_resume_eagles_20261114_01/GameTimeChecks.cpp"
#undef ImageSize
#undef main

namespace
{
using ptfr::RealTimeHandoff;
using ptfr::ReattachResult;
using ptfr::resume::EndingCheckpoint;
using ptfr::resume::RealTimeTransfer;
using ptfr::resume::Retirement;
using ptfr::resume::WaitAddress;

// The two clocks run in separate native slice cages. The game clock fixture
// models the serialized timer and callback owner while both waits are held.
class ConcurrentClockFixture
{
public:
    explicit ConcurrentClockFixture(const NativeCode& native)
        : native(native), methods{native.At<decltype(ptfr::GameTimeWorkerMethods::remove)>(0xB79130),
                                 native.At<decltype(ptfr::GameTimeWorkerMethods::insert)>(0xB79234),
                                 native.At<decltype(ptfr::GameTimeWorkerMethods::release)>(0x195798)},
          original(std::make_unique<TimerFixture>(native, FixtureGameTimer, FixtureGameAuthored))
    {
        markReady = native.At<NativeReady>(0x88B6AC);
        original->SetDeadline(CutoffClock + FixtureGameRemaining);
        original->Install(methods);
    }

    bool Hold()
    {
        auto wait = original->Hold(methods, CutoffClock);
        if (!wait)
            return false;
        held.emplace(std::move(*wait));
        return held->Checkpoint().seconds == FixtureGameRemaining;
    }

    bool Quiet() const
    {
        return original->HeadTimer() == 0 && callbacks == 0 && notificationCount == 0;
    }

    void Restore(Checks& test)
    {
        constexpr auto resumedClock = CutoffClock + FixtureGameAuthored + 30;
        const auto saved = held->Checkpoint();
        held.reset();
        const auto deadline = ptfr::RebaseOneShotGameWait(saved, FixtureGameAuthored, resumedClock);
        if (!test.Expect(deadline && *deadline - resumedClock == FixtureGameRemaining && original->references == 1,
                         "the game-time wait rebases the captured duration and releases the original reference"))
            return;
        const auto freshId = FixtureGameTimer + 1;
        auto resumed = std::make_unique<TimerFixture>(native, freshId, FixtureGameAuthored);
        resumed->SetDeadline(*deadline);
        resumed->Install(methods);
        const auto elapsed = resumed->Read(resumedClock + 1);
        test.Expect(resumed->Tick(resumedClock + 1) == 0 && callbacks == 0 &&
                        elapsed && elapsed->wait.seconds == FixtureGameRemaining - 1,
                    "the game-time deadline advances independently after continuation");

        auto reloaded = std::make_unique<TimerFixture>(native, freshId, FixtureGameAuthored);
        reloaded->SetDeadline(resumed->NativeDeadline(native));
        reloaded->Install(methods);
        Write(reloaded->owner.data(), 0x28, 6U);
        if (!test.Expect(reloaded->RebindLoadedCallback(native) && reloaded->Tick(*deadline - 1) == 0 &&
                             callbacks == 0 && notificationCount == 0,
                         "the stock game-time callback binding reloads without waking early"))
            return;
        const auto expired = reloaded->Tick(*deadline);
        if (expired)
            reloaded->Remove(methods, freshId);
        test.Expect(expired == 1 && callbacks == 1 && notificationCount == 1 && firedSlot == 6 &&
                        reloaded->HeadTimer() == 0 &&
                        ptfr::ReadGameTimeField<std::uint32_t>(original->owner.data(), 0x2C) == 0,
                    "the reloaded game-time callback wakes its owner once and retires");
    }

private:
    static constexpr std::uint32_t CutoffClock = 7'200'000; // Only the remaining duration comes from Reed.
    const NativeCode& native;
    const ptfr::GameTimeWorkerMethods methods;
    std::unique_ptr<TimerFixture> original;
    std::optional<ptfr::HeldGameTimeWait> held;
};

struct CompositeHandler
{
    alignas(16) std::array<std::byte, 0x40> parent{};
    alignas(16) std::array<std::byte, 0x60> handler{};

    CompositeHandler(const void* vtable, void* events, std::uint32_t slot, std::uint64_t key, bool waiting)
    {
        Field<void*>(parent.data(), 0x18) = events;
        Field<std::uint32_t>(parent.data(), 0x28) = slot;
        Field<const void*>(handler.data(), 0) = vtable;
        Field<void*>(handler.data(), 0x20) = parent.data();
        Field<std::uint32_t>(handler.data(), 0x30) = waiting;
        Field<std::uint64_t>(handler.data(), 0x38) = key;
        Field<std::uint64_t>(handler.data(), 0x40) = RealTimeHandoff::InactiveTimer;
    }

    std::uint32_t Ready() { return Field<std::uint32_t>(handler.data(), 0x2C); }
};

struct CopyInterleave
{
    Checks& test;
    GraphFixture& graph;
    RealTimeTransfer& transfer;
};

CopyInterleave* interleave;

void RetireDuringCopy()
{
    auto& [test, graph, transfer] = *interleave;
    test.Expect(graph.Pending().count == 0 && Field<std::uint8_t>(graph.quests.data(), 0x60) == 0,
                "notification worker has copied the old slot and has not acquired the graph lock");
    graph.Queue(OldSlot);
    graph.Queue(OldSlot);

    auto* lock = &Field<std::uint8_t>(graph.quests.data(), 0x60);
    graph.methods.lock(lock);
    test.Expect(transfer.Retire(graph.methods, graph.drain) == Retirement::Reserved,
                "native retirement reserves the former slot");
    test.Expect(transfer.Settle(graph.methods, graph.quests.data(), graph.drain, false) ==
                    Status::CallbacksPending,
                "retired slot cannot be released while old producers are still active");
    test.Expect(transfer.Settle(graph.methods, graph.quests.data(), graph.drain, true) ==
                    Status::AwaitingDrain &&
                    graph.Pending().count == 0 && Field<Vector>(graph.quests.data(), 0x168).count == 0,
                "late duplicates are cleared and the copied batch must still drain");
    test.Expect(graph.Register() == OldSlot + 1 && graph.Free().count == 0,
                "native allocation cannot recycle a slot in the copied batch");
    std::atomic_ref(*lock).store(0, std::memory_order_release);
}

void RunTransfer(Checks& test, const Slices& native, const NativeCode& clockCode,
                 const WaitAddress& address, const EndingCheckpoint& ending)
{
    test.Reset();
    GraphFixture graph(native);
    const auto reload = test.ReloadMethods(native);
    auto* quests = graph.quests.data();
    auto* events = graph.events.data();
    auto* scheduler = test.delay.data();
    const auto node = address.NodeKey();
    graph.rows[OldSlot] = {address.registrationType, address.Hash(), address.node};

    std::array<std::uintptr_t, 0x2D0 / 8> questTable{};
    const auto* nativeQuestTable = Field<const std::uintptr_t*>(quests, 0);
    std::copy_n(nativeQuestTable, 0x2B8 / 8, questTable.begin());
    questTable[0x200 / 8] = native.At<std::uintptr_t>(0x88BC58);
    questTable[0x2C8 / 8] = native.At<std::uintptr_t>(0x194AC4);
    Field<void*>(quests, 0) = questTable.data();
    std::array<std::uintptr_t, 2> eventTable{};
    eventTable[1] = native.At<std::uintptr_t>(0x88BC48);
    Field<void*>(events, 0) = eventTable.data();
    alignas(16) std::array<std::byte, 0x20> nodeManager{};
    std::array<std::array<std::uint64_t, 2>, 8> rows{};
    struct NodeData { void* data; std::uint32_t capacity; std::uint32_t count; };
    Field<NodeData>(nodeManager.data(), 8) = {rows.data(), static_cast<std::uint32_t>(rows.size()), 0};
    Field<void*>(quests, 0xF0) = nodeManager.data();
    const auto clearMapping = native.At<void (*)(void*, std::uint64_t)>(0x194C24);

    CompositeHandler old(reload.handlerVtable, events, OldSlot, node, true);
    Field<std::uint64_t>(old.handler.data(), 0x40) = native.timerId;
    struct Callback
    {
        const void* vtable;
        void* handler;
        std::byte storage[0x28]{};
        const Callback* self{};
    } callback{reload.callbackVtable, old.handler.data()};
    static_assert(offsetof(Callback, self) == 0x38);
    callback.self = &callback;
    ptfr::NativeDelayReference timer{};
    reload.construct(&timer);
    if (!test.Expect(timer.entry && timer.count, "stock real-time timer was constructed"))
        return;
    Field<std::uint64_t>(timer.entry, ptfr::HeldDelay::EntryTimer) = native.timerId;
    Field<float>(timer.entry, ptfr::HeldDelay::EntrySeconds) = native.remaining;
    reload.worker.insert(scheduler, &timer, 0);
    const bool attached = reload.attach(scheduler, native.timerId, &callback, 0xC74E8775F65E90DD, 0);
    const auto oldOwner = test.Owner(Field<const void*>(timer.entry, 0x78));
    reload.worker.release(&timer);
    if (!test.Expect(attached && test.Remaining(native.timerId) == native.remaining,
                     "original native handler owns the observed remaining time"))
        return;
    reload.insertMapping(quests, node, ptfr::SchedulerId::FromNative(native.timerId).NodeInstanceValue());

    RealTimeTransfer abandoned(address, ending, events, OldSlot);
    test.Expect(!abandoned.Hold(reload, oldOwner, old.handler.data(), native.timerId, 0.016f, true, true) &&
                    !abandoned.Hold(reload, oldOwner, old.handler.data(), native.timerId, 0.016f, false, false) &&
                    !abandoned.Hold(reload, oldOwner, old.handler.data(), native.timerId, native.remaining, false, true) &&
                    test.Remaining(native.timerId) == native.remaining,
                "pending notifications, a save window and a due timer leave the stock owner untouched");
    if (!test.Expect(abandoned.Hold(reload, oldOwner, old.handler.data(), native.timerId, 0.016f, false, true),
                     "hold can pin the original timer before acknowledging cleanup"))
        return;
    auto recycled = oldOwner;
    ++recycled.generation;
    test.Expect(abandoned.Abort(recycled) == ptfr::ReturnToScheduler::OwnerChanged &&
                    !abandoned.SaveCoherent() && test.Remaining(native.timerId) == -1.0f,
                "an abort cannot reinsert the callback into another generation");
    if (!test.Expect(abandoned.Abort(oldOwner) == ptfr::ReturnToScheduler::Returned &&
                         abandoned.SaveCoherent() && test.Remaining(native.timerId) == native.remaining,
                     "aborting before cleanup restores the original timer and remaining time"))
        return;

    RealTimeTransfer transfer(address, ending, events, OldSlot);
    if (!test.Expect(transfer.Hold(reload, oldOwner, old.handler.data(), native.timerId, 0.016f, false, true),
                     "selected timer is removed from the native scheduler"))
        return;
    const auto checkpoint = transfer.Captured().value();
    test.Expect(checkpoint.node == node && checkpoint.seconds == native.remaining && !transfer.SaveCoherent(),
                "checkpoint captures the exact float at the original logical node");
    auto foreign = ending;
    ++foreign.ticket;
    auto changed = checkpoint;
    changed.seconds += 1;
    test.Expect(!transfer.Commit(foreign, checkpoint) && !transfer.Commit(ending, changed),
                "another ending ticket or duration cannot acknowledge the transfer");
    if (!test.Expect(transfer.Commit(ending, checkpoint), "readback of the same checkpoint authorizes native retirement"))
        return;

    ConcurrentClockFixture gameClock(clockCode);
    if (!test.Expect(gameClock.Hold() && test.Remaining(native.timerId) == -1.0f,
                     "real-time and game-time waits are simultaneously held"))
        return;
    Timer unrelated;
    const auto otherId = GroupMask | 0x6e2;
    test.Add(unrelated, otherId, 1);
    test.Tick(900);
    test.Expect(test.Remaining(native.timerId) == -1.0f && old.Ready() == 0 && graph.Pending().count == 0 &&
                    unrelated.callback.fired == 1 && gameClock.Quiet(),
                "both selected waits stay quiet and the unselected timer expires");

    CopyInterleave copied{test, graph, transfer};
    interleave = &copied;
    beforeGraphLock = &Field<std::uint8_t>(quests, 0x60);
    beforeGraphAcquire = &RetireDuringCopy;
    graph.Queue(OldSlot);
    graph.RunDrain();
    interleave = nullptr;
    test.Expect(!transfer.ReleaseOldTimer(reload, ending) && !transfer.SaveCoherent(),
                "a drained batch still needs graph-side release before timer disposal");
    if (!test.Expect(transfer.Settle(graph.methods, quests, graph.drain, true) == Status::Released &&
                         !transfer.ReleaseOldTimer(reload, ending),
                     "a finished drain releases the slot and the old node mapping still bars timer disposal"))
        return;
    clearMapping(quests, node); // Model native Uninitialize removing the original node-data row.
    if (!test.Expect(transfer.ReleaseOldTimer(reload, ending), "native node-data cleanup makes the old wait disposable"))
        return;
    test.Expect(transfer.SaveCoherent() && graph.Free().count == 1,
                "the detached wait is represented by the committed checkpoint");

    const auto registerSlot = native.At<std::uint32_t (*)(void*, std::uint64_t, const std::uint64_t*)>(0xEB6B3C);
    const auto registrationKey = (std::uint64_t{address.node} << 32) | address.Hash();
    const auto slot = registerSlot(events, address.registrationType, &registrationKey);
    CompositeHandler replacement(reload.handlerVtable, events, slot, node, true);
    ptfr::RegisteredWait owner{node, ending.ticket, oldOwner.generation, scheduler, oldOwner.generation + 1,
                               quests, replacement.handler.data()};
    const auto freshId = GroupMask | 0x6e1;
    auto wrongAddress = address;
    wrongAddress.provider[0] ^= 1;
    test.Expect(slot == OldSlot && address.Matches(events, slot),
                "the original logical address can reuse its physical slot after the copied batch ends");
    test.Expect(transfer.Restore(reload, owner, freshId, ending, address, events, slot, false, true, true) ==
                        ReattachResult::Deferred &&
                    transfer.Restore(reload, owner, freshId, foreign, address, events, slot, true, true, true) ==
                        ReattachResult::Deferred &&
                    transfer.Restore(reload, owner, freshId, ending, wrongAddress, events, slot, true, true, true) ==
                        ReattachResult::Deferred &&
                    transfer.Restore(reload, owner, freshId, ending, address, events, slot, true, false, true) ==
                        ReattachResult::Deferred,
                "incomplete ending, different ticket, wrong provider and competing owner all defer");
    reload.insertMapping(quests, node, ptfr::SchedulerId::FromNative(native.timerId).NodeInstanceValue());
    test.Expect(transfer.Restore(reload, owner, freshId, ending, address, events, slot, true, true, true) ==
                    ReattachResult::Deferred &&
                    test.Remaining(freshId) == -1.0f,
                "another mapping still blocks competing native ownership");
    clearMapping(quests, node);
    if (!test.Expect(transfer.Restore(reload, owner, freshId, ending, address, events, slot, true, true, true) ==
                         ReattachResult::Attached &&
                         test.Remaining(freshId) == native.remaining && transfer.SaveCoherent(),
                     "the replacement attaches at the same node with the original remaining time"))
        return;
    test.Expect(transfer.Restore(reload, owner, freshId, ending, address, events, slot, true, true, true) ==
                    ReattachResult::AlreadyAttached,
                "one checkpoint installs a single replacement timer");

    test.Tick(1.5f);
    const auto remaining = test.ReadSavedDelay(native, freshId);
    std::uint64_t savedMapping{};
    test.Expect(remaining == native.remaining - 1.5f && reload.readMapping(quests, node, &savedMapping) &&
                    savedMapping == ptfr::SchedulerId::FromNative(freshId).NodeInstanceValue(),
                "native save collector and node-map lookup agree after elapsed play");
    test.Remove(freshId);
    if (!test.Expect(test.LoadSavedDelay(reload, freshId, remaining), "the saved scheduler record reloads"))
        return;

    // Model a freshly loaded parent with the same logical address, a changed
    // physical slot and the saved node mapping from the prior instance.
    GraphFixture loaded(native);
    auto* loadedQuests = loaded.quests.data();
    auto* loadedEvents = loaded.events.data();
    Field<void*>(loadedQuests, 0) = questTable.data();
    Field<void*>(loadedEvents, 0) = eventTable.data();
    Field<void*>(loadedQuests, 0xF0) = nodeManager.data();
    const auto loadedSlot = registerSlot(loadedEvents, address.registrationType, &registrationKey);
    std::array<std::uintptr_t, 6> handlerTable{};
    std::array<std::uintptr_t, 0x1E0 / 8> schedulerTable{};
    std::array<std::uintptr_t, 0x108 / 8> contextTable{};
    alignas(16) std::array<std::byte, 0x100> context{};
    CompositeHandler rebuilt(handlerTable.data(), loadedEvents, loadedSlot, node, false);
    handlerTable[0x28 / 8] = native.At<std::uintptr_t>(0x664F00);
    Field<void*>(scheduler, 0) = schedulerTable.data();
    schedulerTable[0x1D8 / 8] = native.At<std::uintptr_t>(0x193A1C);
    schedulerTable[0x1C8 / 8] = reinterpret_cast<std::uintptr_t>(&UnexpectedCall);
    Field<void*>(context.data(), 0) = contextTable.data();
    Field<void*>(context.data(), 0x18) = loadedQuests;
    Field<void*>(context.data(), 0xF8) = scheduler;
    contextTable[0x100 / 8] = reinterpret_cast<std::uintptr_t>(&ReloadContext);
    native.At<void (*)(void*, void*)>(0x1948BC)(rebuilt.handler.data(), context.data());
    test.Expect(address.Matches(loadedEvents, loadedSlot) && loadedSlot != slot &&
                    Field<std::uint64_t>(rebuilt.handler.data(), 0x40) == freshId && loaded.Pending().count == 0,
                "stock reload binds the saved timer to the reloaded composite registration");
    test.Tick(remaining - 0.25f);
    test.Expect(rebuilt.Ready() == 0 && loaded.Pending().count == 0,
                "there is no callback before the remaining deadline");
    test.Tick(0.25f);
    test.Tick(30);
    test.Expect(rebuilt.Ready() == 1 && loaded.Pending().count == 1 && loaded.Pending().data[0] == loadedSlot &&
                    replacement.Ready() == 0 && old.Ready() == 0 && test.Remaining(freshId) == -1.0f,
                "expiry wakes the reloaded parent once and both prior handlers stay quiet");
    gameClock.Restore(test);
}
} // namespace

int main(int argc, char** argv)
{
    std::setvbuf(stdout, nullptr, _IONBF, 0);
    AddVectoredExceptionHandler(1, &LogException);
    if (argc != 3)
        return 2;
    try
    {
        const Slices native(argv[1]);
        InitQuestLockObserver(native);
        NativeCode clock;
        clock.Load(argv[2]);
        Checks test(native);
        RunTransfer(test, native, clock, FixtureAddress, FixtureEnding);
        std::printf("%u passed, %u failed\n", test.passed, test.failed);
        return test.failed == 0 ? 0 : 1;
    }
    catch (const std::exception& error)
    {
        std::fprintf(stderr, "%s\n", error.what());
        return 2;
    }
}
