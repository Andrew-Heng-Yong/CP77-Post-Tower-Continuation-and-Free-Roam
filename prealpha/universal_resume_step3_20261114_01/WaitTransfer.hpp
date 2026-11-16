#pragma once

#include "../universal_resume_checkpoint_probe_20261114_01/source_02/Checkpoint.hpp"
#include "../universal_resume_handoff_20261114_01/RealTimeHandoff.hpp"
#include "../universal_resume_retirement_20261114_01/RetiredQuestSlot.hpp"

namespace ptfr::resume
{
struct WaitAddress
{
    PhaseAddress phase;
    std::array<std::uint8_t, 32> provider;
    std::uint64_t registrationType;
    std::uint16_t node;

    bool operator==(const WaitAddress&) const = default;

    std::uint32_t Hash() const
    {
        if (phase.size < 2 || phase.size > phase.words.size() || phase.words[0] > 1)
            return 0;
        return PhaseHash(std::span(phase.words).first(phase.size));
    }

    std::uint64_t NodeKey() const { return (std::uint64_t{Hash()} << 32) | node; }

    bool Matches(const void* events, std::uint32_t slot) const
    {
        const auto hash = Hash();
        return hash && std::ranges::any_of(provider, [](auto byte) { return byte != 0; }) &&
               MatchesRegistration(events, slot, hash, node, registrationType);
    }
};

struct EndingCheckpoint
{
    std::array<char, 32> id;
    std::uint64_t session;
    std::int32_t ticket;
    std::int32_t route;

    bool operator==(const EndingCheckpoint&) const = default;

    bool Valid() const
    {
        return session && ticket > 0 && (route == 1 || route == 2) && ValidId({id.data(), id.size()});
    }
};

enum class Retirement { Unmatched, ForwardedUnreserved, Reserved };

// The scheduler and graph owners must serialize entry to this transaction and
// keep the addresses valid. This class is exercised in a stand-alone harness.
// In particular, it cannot acquire an engine save barrier or qualify a phase's
// support providers. Those proofs are required from the live caller.
class RealTimeTransfer
{
public:
    RealTimeTransfer(WaitAddress address, EndingCheckpoint ending, void* events, std::uint32_t originalSlot)
        : address(address), ending(ending), oldEvents(events), oldSlot(originalSlot) {}

    RealTimeTransfer(const RealTimeTransfer&) = delete;
    RealTimeTransfer& operator=(const RealTimeTransfer&) = delete;

    bool Hold(const RealTimeReload& native, DelayOwner owner, const void* handler, std::uint64_t timer,
              float frameSeconds, bool notificationInFlight, bool saveExcluded)
    {
        if (stage != Stage::Unchanged || !ending.Valid() || !saveExcluded || notificationInFlight ||
            !address.Matches(oldEvents, oldSlot) || !owner.callback || !handler ||
            NativeField<const void*>(owner.callback, 0) != native.callbackVtable ||
            NativeField<const void*>(owner.callback, 8) != handler ||
            !MatchesHandler(native, handler, oldEvents, oldSlot) ||
            NativeField<std::uint64_t>(handler, 0x40) != timer)
            return false;
        auto* quests = NativeField<void*>(oldEvents, 0x28);
        std::uint64_t mapping{};
        if (!quests || NativeField<const void*>(quests, 0xE8) != oldEvents ||
            !native.readMapping(quests, address.NodeKey(), &mapping) ||
            mapping != SchedulerId::FromNative(timer).NodeInstanceValue())
            return false;
        auto result = HeldDelay::Take(native.worker, owner, native.timerVtable, timer, frameSeconds);
        if (!result)
            return false;
        held.emplace(std::move(*result));
        original = owner;
        checkpoint = {address.NodeKey(), ending.ticket, held->RemainingSeconds()};
        stage = Stage::Held;
        return true;
    }

    std::optional<WaitCheckpoint> Captured() const
    {
        return stage == Stage::Held ? std::optional(checkpoint) : std::nullopt;
    }

    // Called after the quest side reads back the value in the same ending
    // session. A scheduler sample alone cannot authorize acknowledging cleanup.
    bool Commit(const EndingCheckpoint& observed, const WaitCheckpoint& saved)
    {
        if (stage != Stage::Held || observed != ending || !saved.Matches(checkpoint.node, checkpoint.ticket) ||
            saved.seconds != checkpoint.seconds || !address.Matches(oldEvents, oldSlot))
            return false;
        stage = Stage::Committed;
        return true;
    }

    ReturnToScheduler Abort(DelayOwner current)
    {
        if (stage != Stage::Held)
            return ReturnToScheduler::Empty;
        if (!address.Matches(oldEvents, oldSlot))
            return ReturnToScheduler::OwnerChanged;
        const auto result = held->Return(current);
        if (result == ReturnToScheduler::Returned)
        {
            held.reset();
            stage = Stage::Returned;
        }
        return result;
    }

    // Wrap only the verified old registration's normal retirement call. The
    // caller forwards all other native retirements through the original path.
    Retirement Retire(const QuestSlotMethods& methods, const QuestNotificationDrain& drain)
    {
        if (stage != Stage::Committed || drain.Session() != ending.session ||
            !address.Matches(oldEvents, oldSlot))
            return Retirement::Unmatched;
        auto result = RetiredQuestSlot::Retire(methods, oldEvents, oldSlot, drain);
        if (!result)
        {
            stage = Stage::RetirementFailed;
            return Retirement::ForwardedUnreserved;
        }
        reservation.emplace(std::move(*result));
        stage = Stage::Retiring;
        return Retirement::Reserved;
    }

    RetiredSlotStatus Settle(const QuestSlotMethods& methods, void* quests, const QuestNotificationDrain& drain,
                             bool producersStopped)
    {
        if (stage != Stage::Retiring)
            return RetiredSlotStatus::Deferred;
        const auto result = reservation->Settle(methods, quests, drain, producersStopped);
        if (result == RetiredSlotStatus::Released)
        {
            reservation.reset();
            stage = Stage::Drained;
        }
        return result;
    }

    // Release the old scheduler reference on its worker, after all original
    // producers and the copied notification batch are quiet.
    bool ReleaseOldTimer(const RealTimeReload& native, const EndingCheckpoint& observed)
    {
        if (stage != Stage::Drained || observed != ending)
            return false;
        auto* quests = NativeField<void*>(oldEvents, 0x28);
        std::uint64_t mapping{};
        if (!quests || NativeField<const void*>(quests, 0xE8) != oldEvents ||
            native.readMapping(quests, address.NodeKey(), &mapping))
            return false;
        held.reset();
        handoff.emplace(checkpoint);
        stage = Stage::Ready;
        return true;
    }

    ReattachResult Restore(const RealTimeReload& native, const RegisteredWait& owner, std::uint64_t freshTimer,
                           const EndingCheckpoint& observed, const WaitAddress& restoredAddress,
                           const void* newEvents, std::uint32_t newSlot, bool genuineCompletion,
                           bool soleQualifiedOwner, bool saveExcluded)
    {
        if (stage == Stage::Restored)
            return ReattachResult::AlreadyAttached;
        if ((stage != Stage::Ready && stage != Stage::Attaching) || observed != ending ||
            !genuineCompletion || !soleQualifiedOwner || !saveExcluded || restoredAddress != address ||
            owner.retiredGeneration != original.generation || owner.scheduler != original.scheduler ||
            owner.node != address.NodeKey() ||
            !owner.quests || NativeField<const void*>(owner.quests, 0xE8) != newEvents ||
            !address.Matches(newEvents, newSlot) || !MatchesHandler(native, owner.handler, newEvents, newSlot))
            return ReattachResult::Deferred;
        stage = Stage::Attaching;
        const auto result = handoff->Reattach(native, owner, freshTimer);
        if (result == ReattachResult::Attached)
            stage = Stage::Restored;
        return result;
    }

    bool SaveCoherent() const
    {
        return stage == Stage::Unchanged || stage == Stage::Returned || stage == Stage::Ready || stage == Stage::Restored;
    }

private:
    enum class Stage { Unchanged, Held, Returned, Committed, Retiring, RetirementFailed, Drained, Ready, Attaching, Restored };

    bool MatchesHandler(const RealTimeReload& native, const void* handler, const void* events, std::uint32_t slot) const
    {
        if (!handler || NativeField<const void*>(handler, 0) != native.handlerVtable ||
            NativeField<std::uint64_t>(handler, 0x38) != address.NodeKey() ||
            NativeField<std::uint32_t>(handler, 0x2C) != 0 || NativeField<std::uint32_t>(handler, 0x30) != 1)
            return false;
        const auto* parent = NativeField<const void*>(handler, 0x20);
        return parent && NativeField<const void*>(parent, 0x18) == events &&
               NativeField<std::uint32_t>(parent, 0x28) == slot;
    }

    const WaitAddress address;
    const EndingCheckpoint ending;
    void* const oldEvents;
    const std::uint32_t oldSlot;
    Stage stage{Stage::Unchanged};
    DelayOwner original{};
    WaitCheckpoint checkpoint{};
    std::optional<HeldDelay> held;
    std::optional<RetiredQuestSlot> reservation;
    std::optional<RealTimeHandoff> handoff;
};
} // namespace ptfr::resume
