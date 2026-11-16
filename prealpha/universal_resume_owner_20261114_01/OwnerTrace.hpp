#pragma once

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <optional>
#include <span>
#include <atomic>

namespace ptfr
{
struct PhaseAddress
{
    static constexpr std::size_t Capacity = 16;
    std::array<std::uint16_t, Capacity> words{};
    std::size_t size = 0;

    bool operator==(const PhaseAddress&) const = default;
};

template <class T>
T NativeField(const void* object, std::size_t offset)
{
    T value{};
    std::memcpy(&value, static_cast<const std::byte*>(object) + offset, sizeof(value));
    return value;
}

// Only call while the engine owns the phase object at a native hook boundary.
inline std::optional<PhaseAddress> CopyPhaseAddress(const void* phase)
{
    if (!phase)
        return std::nullopt;
    const auto depth = NativeField<std::uint32_t>(phase, 0x7C);
    if (depth < 2 || depth > PhaseAddress::Capacity)
        return std::nullopt;
    const auto* path = NativeField<const std::uint16_t*>(phase, 0x70);
    if (!path)
        return std::nullopt;
    PhaseAddress copy;
    copy.size = depth;
    std::copy_n(path, depth, copy.words.begin());
    return copy;
}

inline constexpr std::array<std::uint16_t, 6> HasanWorld{1, 0, 10, 5, 14, 5};
inline constexpr std::array<std::uint16_t, 10> HasanBugfix{1, 0, 10, 2, 3, 16, 5, 6, 14, 5};
inline constexpr std::array<std::uint16_t, 2> HasanS23{1, 19107};
inline constexpr std::array<std::uint16_t, 4> HasanS23World{1, 19107, 100, 5};
inline constexpr std::array<std::uint16_t, 4> HasanS23Dialog{1, 19107, 100, 9};
inline constexpr std::array<std::uint16_t, 6> HasanNativeDialog{1, 0, 10, 4, 1, 9};
inline constexpr std::array<std::uint16_t, 11> HasanBugfixStoryDialog{1, 0, 10, 2, 3, 16, 5, 6, 14, 5, 41};
inline constexpr std::array<std::uint16_t, 11> HasanBugfixWorldDialog{1, 0, 10, 2, 3, 16, 5, 6, 14, 6, 22};
inline constexpr std::array<std::uint16_t, 7> HasanStoryDialog{1, 0, 10, 5, 14, 5, 41};
inline constexpr std::array<std::uint16_t, 7> HasanWorldDialog{1, 0, 10, 5, 14, 6, 22};

// These are watch filters for one known restored quest. The lifecycle hooks and
// exact path matching work with other quest families through the same table.
struct PhaseWatch
{
    const char* name;
    std::span<const std::uint16_t> path;
    bool quest = false;
};

inline std::uint32_t PhaseHash(std::span<const std::uint16_t> path)
{
    if (path.empty() || path.front() > 1)
        return 0;
    std::uint32_t hash = path.front() == 0 ? 0x811C9DC5u : 0x01800013u;
    for (const auto node : path)
    {
        hash = (hash ^ (node & 0xFFu)) * 0x01000193u;
        hash = (hash ^ (node >> 8)) * 0x01000193u;
    }
    return hash;
}

inline constexpr PhaseWatch HasanPhases[] = {
    {"native-open-world", HasanWorld, true}, {"native-bugfix", HasanBugfix, true}, {"s23-entry", HasanS23},
    {"s23-quest", HasanS23World, true}, {"s23-dialogue", HasanS23Dialog}, {"native-default-dialogue", HasanNativeDialog},
    {"bugfix-story-dialogue", HasanBugfixStoryDialog}, {"bugfix-world-dialogue", HasanBugfixWorldDialog},
    {"native-story-dialogue", HasanStoryDialog}, {"native-world-dialogue", HasanWorldDialog},
};

inline const PhaseWatch* FindWatchedPhase(const PhaseAddress& address)
{
    if (address.size > address.words.size())
        return nullptr;
    const auto words = std::span(address.words).first(address.size);
    const auto found = std::find_if(std::begin(HasanPhases), std::end(HasanPhases), [&](const PhaseWatch& phase) {
        return std::ranges::equal(phase.path, words);
    });
    return found == std::end(HasanPhases) ? nullptr : found;
}

struct RegistrationRow
{
    std::uint64_t type;
    std::uint32_t phaseHash;
    std::uint32_t node;
};
static_assert(sizeof(RegistrationRow) == 16);

inline std::optional<RegistrationRow> CopyRegistration(const void* eventManager, std::uint32_t slot)
{
    if (!eventManager || slot >= NativeField<std::uint32_t>(eventManager, 0x14))
        return std::nullopt;
    const auto* rows = NativeField<const RegistrationRow*>(eventManager, 8);
    if (!rows || !rows[slot].type || !rows[slot].phaseHash || rows[slot].node >= 0xFFFF)
        return std::nullopt;
    return rows[slot];
}

inline bool MatchesRegistration(const void* eventManager, std::uint32_t slot, std::uint32_t phaseHash,
                                std::uint32_t node, std::uint64_t type)
{
    const auto row = CopyRegistration(eventManager, slot);
    return row && row->phaseHash == phaseHash && row->node == node && row->type == type;
}

inline std::optional<bool> HasChild(const void* parent, const void* child)
{
    if (!parent || !child)
        return std::nullopt;
    const auto count = NativeField<std::uint32_t>(parent, 0x94);
    const auto* entries = NativeField<const std::byte*>(parent, 0x88);
    if (count > 0xFFFF || (count && !entries))
        return std::nullopt;
    for (std::uint32_t index = 0; index < count; ++index)
    {
        if (NativeField<const void*>(entries, 16ull * index) == child)
            return true;
    }
    return false;
}

inline bool HandlerReady(void* handler)
{
    auto* state = reinterpret_cast<std::uint32_t*>(static_cast<std::byte*>(handler) + 0x2C);
    return std::atomic_ref(*state).load() != 0;
}
} // namespace ptfr
