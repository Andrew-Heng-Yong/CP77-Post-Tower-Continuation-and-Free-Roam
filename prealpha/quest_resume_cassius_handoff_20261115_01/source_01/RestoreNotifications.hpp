#pragma once

#include "StagePlan.hpp"

#include <mutex>

namespace ptfr::resume
{
// Native notification delivery deduplicates physical slots in first-seen
// order. Keep that order while a selected handler is still being installed.
// Registry allocation enrolls the slot before the native initializer runs.
class RestoreNotifications
{
public:
    static constexpr auto Capacity = MaxRestoreNodes;

    struct Batch
    {
        std::array<std::uint32_t, Capacity> slots{};
        std::size_t count{};
        auto Values() const { return std::span(slots).first(count); }
    };

    bool Begin(const void* owner)
    {
        const std::lock_guard lock(mutex);
        if (!owner || quests)
            return false;
        quests = owner;
        return true;
    }

    bool Watch(const void* owner, std::uint32_t slot)
    {
        const std::lock_guard lock(mutex);
        if (!quests || owner != quests || slot >= MaxSlots || watched.count == Capacity || Contains(watched, slot))
            return false;
        watched.slots[watched.count++] = slot;
        return true;
    }

    bool Intercept(const void* owner, std::uint32_t slot)
    {
        const std::lock_guard lock(mutex);
        if (quests != owner || !Contains(watched, slot))
            return false;
        if (!Contains(pending, slot))
            pending.slots[pending.count++] = slot;
        return true;
    }

    // The receiver is called while ingress is locked so a later callback
    // for a selected slot cannot overtake the buffered native notification.
    template<typename Publish>
    bool Finish(const void* owner, Publish publish)
    {
        const std::lock_guard lock(mutex);
        if (!quests || quests != owner)
            return false;
        for (const auto slot : pending.Values())
            publish(slot);
        Reset();
        return true;
    }

    void Discard()
    {
        const std::lock_guard lock(mutex);
        Reset();
    }

private:
    static bool Contains(const Batch& batch, std::uint32_t slot)
    {
        const auto entries = batch.Values();
        return std::ranges::find(entries, slot) != entries.end();
    }

    void Reset()
    {
        quests = nullptr;
        watched.count = 0;
        pending.count = 0;
    }

    const void* quests{};
    Batch watched;
    Batch pending;
    std::mutex mutex;
};
} // namespace ptfr::resume
