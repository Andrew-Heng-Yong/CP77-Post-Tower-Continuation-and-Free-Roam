#pragma once

#include "DelayHold.hpp"
#include "CutoffObservation.hpp"

namespace ptfr
{
struct WaitCheckpoint
{
    std::uint64_t node = 0;
    std::int32_t ticket = 0;
    float seconds = 0;

    bool Matches(std::uint64_t expectedNode, std::int32_t endingTicket) const
    {
        return node && node == expectedNode && ticket > 0 && ticket == endingTicket &&
               std::isfinite(seconds) && seconds > 0;
    }
};

class CutoffWaitSample
{
public:
    bool Record(CutoffObservation& observation, const CaptureRequest& request,
                std::uint64_t node, float remaining, float frameSeconds)
    {
        if (request.gate.route != 1 || !node || !observation.Accept(request, remaining, frameSeconds))
            return false;
        captured = request;
        saved = {node, request.gate.ticket, remaining};
        return true;
    }

    std::optional<WaitCheckpoint> Read(const CutoffObservation& observation, const void* facts,
                                       std::uint64_t node, std::int32_t ticket) const
    {
        if (!facts || !captured || facts != captured->gate.facts || !saved.Matches(node, ticket) ||
            !observation.IsCurrentSample(*captured))
            return std::nullopt;
        return saved;
    }

private:
    std::optional<CaptureRequest> captured;
    WaitCheckpoint saved;
};

struct RealTimeReload
{
    using Construct = NativeDelayReference* (*)(NativeDelayReference*);
    using Attach = bool (*)(void*, std::uint64_t, void*, std::uint64_t, std::uint64_t);
    using ReadNodeData = bool (*)(void*, std::uint64_t, std::uint64_t*);
    using InsertNodeData = void (*)(void*, std::uint64_t, std::uint64_t);

    DelayWorker worker;
    Construct construct;
    Attach attach;
    ReadNodeData readMapping;
    InsertNodeData insertMapping;
    const void* timerVtable;
    const void* callbackVtable;
    const void* handlerVtable;
};

// The quest side supplies this record only after retiring the previous
// registration and its queued notifications and qualifying the new phase's
// complete support ownership. Timer code cannot prove those prerequisites.
struct RegisteredWait
{
    std::uint64_t node;
    std::int32_t endingTicket;
    std::uint64_t retiredGeneration;
    void* scheduler;
    std::uint64_t generation;
    void* quests;
    void* handler;
};

enum class ReattachResult
{
    Deferred,
    Retry,
    Attached,
    AlreadyAttached,
};

// Call before expiry on the delay worker, while the quest registration and
// candidate ID are reserved and the save and stop paths are held outside.
class RealTimeHandoff
{
public:
    explicit RealTimeHandoff(WaitCheckpoint saved) : saved(saved) {}
    RealTimeHandoff(const RealTimeHandoff&) = delete;
    RealTimeHandoff& operator=(const RealTimeHandoff&) = delete;

    ReattachResult Reattach(const RealTimeReload& native, const RegisteredWait& owner,
                            std::uint64_t freshTimer)
    {
        if (attached)
            return ReattachResult::AlreadyAttached;
        if (!saved.Matches(owner.node, owner.endingTicket) || !owner.handler || !owner.quests ||
            !owner.scheduler || !owner.retiredGeneration || owner.generation <= owner.retiredGeneration ||
            !SchedulerId::FromNative(freshTimer).IsQuestDelay())
            return ReattachResult::Deferred;
        if (Field<const void*>(owner.handler, 0) != native.handlerVtable ||
            Field<std::uint64_t>(owner.handler, 0x38) != owner.node ||
            Field<std::uint64_t>(owner.handler, 0x40) != InactiveTimer ||
            Field<std::uint32_t>(owner.handler, 0x2C) != 0 || Field<std::uint32_t>(owner.handler, 0x30) != 1)
            return ReattachResult::Deferred;

        std::uint64_t mapping{};
        if (native.readMapping(owner.quests, owner.node, &mapping))
            return ReattachResult::Deferred;

        auto* scheduler = owner.scheduler;
        if (native.worker.remaining(scheduler, freshTimer) != -1.0f ||
            Field<std::uint32_t>(scheduler, HeldDelay::Group4Count) >= HeldDelay::Capacity)
            return ReattachResult::Retry;

        NativeDelayReference timer{};
        native.construct(&timer);
        if (!timer.entry || !timer.count || Field<const void*>(timer.entry, 0) != native.timerVtable)
        {
            native.worker.release(&timer);
            return ReattachResult::Deferred;
        }
        Field<std::uint64_t>(timer.entry, HeldDelay::EntryTimer) = freshTimer;
        Field<float>(timer.entry, HeldDelay::EntrySeconds) = saved.seconds;
        native.worker.insert(scheduler, &timer, 0);

        RestoredCallback callback{native.callbackVtable, owner.handler, {}, nullptr};
        callback.self = &callback;
        const bool inserted = native.worker.remaining(scheduler, freshTimer) >= 0;
        const auto payload = Field<std::uint64_t>(owner.handler, 0x50);
        const bool bound = inserted && native.attach(scheduler, freshTimer, &callback, DelayTag, payload);
        const auto* stored = Field<const RestoredCallback*>(timer.entry, 0x78);
        if (!bound || static_cast<const void*>(stored) != static_cast<std::byte*>(timer.entry) + 0x40 ||
            stored->vtable != native.callbackVtable || stored->handler != owner.handler)
        {
            if (inserted)
                native.worker.remove(scheduler, &freshTimer, 0);
            native.worker.release(&timer);
            return ReattachResult::Retry;
        }

        const auto expected = SchedulerId::FromNative(freshTimer).NodeInstanceValue();
        native.insertMapping(owner.quests, owner.node, expected);
        if (!native.readMapping(owner.quests, owner.node, &mapping) || mapping != expected)
        {
            native.worker.remove(scheduler, &freshTimer, 0);
            native.worker.release(&timer);
            return ReattachResult::Retry;
        }
        Field<std::uint64_t>(owner.handler, 0x40) = freshTimer;

        native.worker.release(&timer);
        attached = true;
        return ReattachResult::Attached;
    }

    static constexpr std::uint64_t InactiveTimer = 0x8000000000000000;

private:
    struct RestoredCallback
    {
        const void* vtable;
        void* handler;
        std::byte storage[0x28];
        const RestoredCallback* self;
    };

    static_assert(offsetof(RestoredCallback, self) == 0x38);
    static constexpr std::uint64_t DelayTag = 0xC74E8775F65E90DD;

    template <class T>
    static T& Field(void* object, std::size_t offset)
    {
        return *reinterpret_cast<T*>(static_cast<std::byte*>(object) + offset);
    }

    WaitCheckpoint saved;
    bool attached = false;
};
} // namespace ptfr
