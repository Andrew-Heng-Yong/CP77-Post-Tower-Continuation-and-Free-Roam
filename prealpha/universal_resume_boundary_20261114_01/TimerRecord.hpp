#pragma once

#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <optional>

namespace ptfr
{
struct SchedulerId
{
    std::uint32_t serial;
    std::uint32_t group;

    static SchedulerId FromNative(std::uint64_t packed)
    {
        return {static_cast<std::uint32_t>(packed), static_cast<std::uint32_t>(packed >> 32)};
    }

    std::uint64_t NodeInstanceValue() const
    {
        return (static_cast<std::uint64_t>(serial) << 32) | group;
    }

    bool IsQuestDelay() const { return serial != 0 && group == 4; }
    bool operator==(const SchedulerId&) const = default;
};

struct SavedTimer
{
    SchedulerId id;
    float remainingSeconds;
    std::uint8_t kind;
};

static_assert(sizeof(SavedTimer) == 16);
static_assert(offsetof(SavedTimer, remainingSeconds) == 8);
static_assert(offsetof(SavedTimer, kind) == 12);

inline std::optional<float> FindRemainingDelay(const void* data, std::uint32_t count, SchedulerId id)
{
    if (!data || !id.IsQuestDelay() || count > 0x800)
        return std::nullopt;

    std::optional<float> remaining;
    const auto* bytes = static_cast<const std::uint8_t*>(data);
    for (std::uint32_t index = 0; index < count; ++index)
    {
        SavedTimer row{};
        std::memcpy(&row, bytes + index * sizeof(row), sizeof(row));
        if (row.id != id)
            continue;
        if (remaining || row.kind != 1 || !std::isfinite(row.remainingSeconds) || row.remainingSeconds < 0)
            return std::nullopt;
        remaining = row.remainingSeconds;
    }
    return remaining;
}
} // namespace ptfr
