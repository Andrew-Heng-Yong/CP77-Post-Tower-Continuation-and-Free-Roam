#define main PriorGameTimeFixtureMain
#include "../universal_resume_eagles_20261114_01/GameTimeChecks.cpp"
#undef main

#include "paired_input.hpp"

namespace
{
void PairedWaits(const NativeCode& native)
{
    const ptfr::GameTimeWorkerMethods methods{
        native.At<decltype(ptfr::GameTimeWorkerMethods::remove)>(0xB79130),
        native.At<decltype(ptfr::GameTimeWorkerMethods::insert)>(0xB79234),
        native.At<decltype(ptfr::GameTimeWorkerMethods::release)>(0x195798)};
    auto direct = std::make_unique<TimerFixture>(native, DirectId, DirectAuthored);
    auto child = std::make_unique<TimerFixture>(native, ChildId, ChildAuthored);
    direct->SetDeadline(DirectDeadline);
    child->SetDeadline(ChildDeadline);
    direct->Install(methods);
    child->Install(methods);
    direct->AddNeighbor(methods, *child);
    child->Remove(methods, ChildId);
    // Both live records now share one system's active queue.
    auto childOwner = child->Owner();
    childOwner.system = direct->Owner().system;
    const auto childType = ptfr::ReadGameTimeField<const void*>(child->timer.data(), 0);
    const auto childHold = [&] (std::uint32_t clock) {
        return ptfr::HeldGameTimeWait::Take(methods, childOwner, ChildId, clock, ChildAuthored, childType,
                                            child->firstCallbackTable.data(), child->savedCallbackTable.data());
    };
    Check(direct->HeadTimer() == ChildId, "the runtime list orders the two saved game-time waits by deadline");

    // Reject a split hold if the earlier subhandler has reached its deadline.
    auto provisional = direct->Hold(methods, ChildDeadline);
    Check(provisional && !childHold(ChildDeadline) &&
              provisional->Return(direct->Owner(), ChildDeadline) && direct->HeadTimer() == ChildId &&
              direct->NativeDeadline(native) == DirectDeadline,
          "a due companion causes the provisional hold to roll back without a timer reset");
    if (!provisional || !direct->Read(SavedClock))
        return;
    auto oldDirect = direct->Hold(methods, SavedClock);
    Check(oldDirect && direct->HeadTimer() == ChildId && child->NativeDeadline(native) == ChildDeadline,
          "holding the direct timer preserves the still-queued logical child");
    auto oldChild = childHold(SavedClock);
    Check(oldDirect && oldChild && direct->HeadTimer() == 0 && callbacks == 0,
          "both original callbacks are absent from the active queue during the hold");
    if (!oldDirect || !oldChild)
        return;
    const auto savedDirect = oldDirect->Checkpoint();
    const auto savedChild = oldChild->Checkpoint();
    Check(savedDirect.seconds == DirectDeadline - SavedClock && savedChild.seconds == ChildDeadline - SavedClock,
          "the direct timer and the logical child preserve distinct saved durations");
    oldDirect.reset();
    oldChild.reset();

    // Model the stock save records after a large clock jump, then run native
    // list insertion and loaded-ID callback binding on a fresh set of owners.
    constexpr auto resumedClock = DirectDeadline + 7'200;
    const auto later = ptfr::RebaseOneShotGameWait(savedDirect, DirectAuthored, resumedClock);
    const auto earlier = ptfr::RebaseOneShotGameWait(savedChild, ChildAuthored, resumedClock);
    Check(later && earlier && *later - *earlier == DirectDeadline - ChildDeadline,
          "rebased deadlines keep the original one-hour separation");
    if (!later || !earlier)
        return;

    auto rebuiltDirect = std::make_unique<TimerFixture>(native, DirectId + 100, DirectAuthored);
    auto rebuiltChild = std::make_unique<TimerFixture>(native, ChildId + 100, ChildAuthored);
    rebuiltDirect->SetDeadline(*later);
    rebuiltChild->SetDeadline(*earlier);
    rebuiltDirect->Install(methods);
    rebuiltChild->Install(methods);
    Write(rebuiltDirect->owner.data(), 0x28, 4U);
    Write(rebuiltChild->owner.data(), 0x28, 5U);
    const bool directBound = rebuiltDirect->RebindLoadedCallback(native);
    const bool childBound = rebuiltChild->RebindLoadedCallback(native);
    Check(directBound && childBound, "the native saved-ID lookup binds each clock to its rebuilt owner");
    if (!directBound || !childBound)
        return;
    rebuiltDirect->AddNeighbor(methods, *rebuiltChild);
    rebuiltChild->Remove(methods, ChildId + 100);
    Check(rebuiltDirect->HeadTimer() == ChildId + 100 && rebuiltChild->Tick(*earlier - 1) == 0 &&
              callbacks == 0,
          "rebuilt timers wait in deadline order without firing early");
    const auto childDue = rebuiltChild->Tick(*earlier);
    if (childDue)
        rebuiltDirect->Remove(methods, ChildId + 100);
    Check(childDue && firedSlot == 5 && notificationCount == 1 && rebuiltDirect->HeadTimer() == DirectId + 100 &&
              rebuiltDirect->Tick(*later - 1) == 0,
          "the logical child fires once and the later direct timer remains pending");
    const auto directDue = rebuiltDirect->Tick(*later);
    if (directDue)
        rebuiltDirect->Remove(methods, DirectId + 100);
    Check(directDue && firedSlot == 4 && notificationCount == 2 && callbacks == 2 &&
              rebuiltDirect->HeadTimer() == 0 &&
              ptfr::ReadGameTimeField<std::uint32_t>(direct->owner.data(), 0x2C) == 0 &&
              ptfr::ReadGameTimeField<std::uint32_t>(child->owner.data(), 0x2C) == 0,
          "the later callback fires once with the prior owners still quiet");
}
} // namespace

int main(int argc, char** argv)
{
    if (argc != 2)
        return 2;
    std::setvbuf(stdout, nullptr, _IONBF, 0);
    AddVectoredExceptionHandler(1, &ReportNativeFault);
    try
    {
        NativeCode code;
        code.Load(argv[1]);
        markReady = code.At<NativeReady>(0x88B6AC);
        PairedWaits(code);
        return failed ? 1 : 0;
    }
    catch (const std::exception& error)
    {
        std::fprintf(stderr, "%s\n", error.what());
        return 2;
    }
}
