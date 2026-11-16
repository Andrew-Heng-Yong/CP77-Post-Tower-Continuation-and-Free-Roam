#pragma once

#include "../../universal_resume_falco_transfer_20261115_01/FalcoRestorePlan.hpp"

#include <mutex>

namespace ptfr::resume
{
constexpr auto FalcoTimerNodeKey = (std::uint64_t{PhaseHash(FalcoMessages)} << 32) | FalcoRestoreNodes.back().node;

inline std::uint64_t RestoreNodeKey(std::size_t index)
{
    const auto& node = FalcoRestoreNodes[index];
    return (std::uint64_t{PhaseHash(FalcoPhases[node.phase].address)} << 32) | node.node;
}

template<typename ReadFact>
bool MatchingReedCutoff(std::int32_t ticket, ReadFact fact)
{
    return ticket > 0 && fact("PTFRHS3_GateTicket") == ticket && fact("PTFRHS3_GateRoute") == 1 &&
           fact("PTFRHS3_GateResult") == 1 && fact("q307_point_of_no_return") > 0 &&
           fact("q115_point_of_no_return") == 0 && fact("q307_debug_reset") == 0;
}

template<typename ReadFact>
bool GenuineTowerCompletion(std::int32_t ticket, ReadFact fact)
{
    return MatchingReedCutoff(ticket, fact) && fact("PTFRHS3_GateOpen") == 0 &&
           fact("q307_main_game_killed") == 1 && fact("q307_ep1_killed") == 1 &&
           fact("q307_done") == 1 && fact("q307_finished") == 1 && fact("q307_2079") == 1 &&
           fact("PostTowerFreeRoamActive") == 1 && fact("PTFRP0_DR13") == 1 && fact("q307_active") == 0;
}

// Native notification delivery deduplicates physical slots in first-seen
// order. Keep that order while a selected handler is still being installed.
// Registry allocation enrolls the slot before the native initializer runs.
class RestoreNotifications
{
public:
    static constexpr auto Capacity = FalcoRestoreNodes.size();

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
