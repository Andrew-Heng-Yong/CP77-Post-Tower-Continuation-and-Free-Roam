#pragma once

#include <atomic>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <utility>

namespace ptfr
{
struct NativeDelayReference
{
    void* entry;
    long* count;
};

static_assert(sizeof(NativeDelayReference) == 16);
static_assert(sizeof(long) == 4);

struct DelayWorker
{
    using Remaining = float (*)(void*, std::uint64_t);
    using Remove = void (*)(void*, const std::uint64_t*, std::uint8_t);
    using Insert = void (*)(void*, const NativeDelayReference*, std::uint8_t);
    using Release = void (*)(NativeDelayReference*);

    Remaining remaining;
    Remove remove;
    Insert insert;
    Release release;
};

enum class ReturnToScheduler
{
    Retry,
    Returned,
    Occupied,
    OwnerChanged,
    Empty,
};

struct DelayOwner
{
    void* scheduler;
    const void* callback;
    std::uint64_t generation;

    bool operator==(const DelayOwner&) const = default;
};

// Lives on the delay worker. The owning quest must separately be barred from
// retiring or recycling its callback while a return to the old owner is allowed.
class HeldDelay
{
public:
    static constexpr std::size_t EntryTimer = 0x30;
    static constexpr std::size_t EntrySeconds = 0x38;
    static constexpr std::size_t EntryCancelled = 0x3C;
    static constexpr std::size_t Group4Head = 0x18070;
    static constexpr std::size_t SlotStride = 0x18;
    static constexpr std::size_t SlotNext = 0x0A;
    static constexpr std::size_t SlotReference = 0x10;
    static constexpr std::size_t Group4Count = 0x24078;
    static constexpr std::uint32_t Capacity = 0x800;

    HeldDelay() = default;
    HeldDelay(const HeldDelay&) = delete;
    HeldDelay& operator=(const HeldDelay&) = delete;
    HeldDelay& operator=(HeldDelay&&) = delete;
    HeldDelay(HeldDelay&& other) noexcept
        : reference(std::exchange(other.reference, {})), owner(other.owner),
          worker(other.worker), timerId(other.timerId), seconds(other.seconds)
    {
    }

    ~HeldDelay()
    {
        if (reference.entry)
            worker.release(&reference);
    }

    static std::optional<HeldDelay> Take(const DelayWorker& worker, DelayOwner owner,
                                        const void* entryVtable,
                                        std::uint64_t timerId, float frameSeconds)
    {
        if (!owner.scheduler || !entryVtable || !owner.callback || !owner.generation || (timerId >> 32) != 4 ||
            !static_cast<std::uint32_t>(timerId) || !std::isfinite(frameSeconds) || frameSeconds < 0)
            return std::nullopt;
        const auto entry = FindUniqueEntry(owner.scheduler, timerId);
        if (!entry.count || field<const void*>(entry.entry, 0) != entryVtable ||
            field<const void*>(entry.entry, 0x78) != owner.callback ||
            field<std::uint8_t>(entry.entry, EntryCancelled) != 0)
            return std::nullopt;
        const float seconds = worker.remaining(owner.scheduler, timerId);
        if (!std::isfinite(seconds) || seconds <= frameSeconds)
            return std::nullopt;

        HeldDelay held(entry, owner, worker, timerId, seconds);
        worker.remove(owner.scheduler, &timerId, 0);
        if (worker.remaining(owner.scheduler, timerId) != -1.0f)
            return std::nullopt;
        return held;
    }

    float RemainingSeconds() const { return seconds; }

    ReturnToScheduler Return(DelayOwner current)
    {
        if (!reference.entry)
            return ReturnToScheduler::Empty;
        if (current != owner)
            return ReturnToScheduler::OwnerChanged;
        // A fresh scheduler registration can claim this ID after a save load.
        if (worker.remaining(owner.scheduler, timerId) != -1.0f)
            return ReturnToScheduler::Occupied;
        if (field<std::uint32_t>(owner.scheduler, Group4Count) >= Capacity)
            return ReturnToScheduler::Retry;

        // Native insertion changes this value to a delta against its neighbor.
        // Keep the captured absolute duration in 'seconds' until insertion is confirmed.
        field<float>(reference.entry, EntrySeconds) = seconds;
        worker.insert(owner.scheduler, &reference, 0);
        if (FindUniqueEntry(owner.scheduler, timerId).entry != reference.entry)
            return ReturnToScheduler::Retry;
        worker.release(&reference);
        reference = {};
        return ReturnToScheduler::Returned;
    }

private:
    template <class T>
    static T& field(void* object, std::size_t offset)
    {
        return *reinterpret_cast<T*>(static_cast<std::byte*>(object) + offset);
    }

    HeldDelay(NativeDelayReference entry, DelayOwner liveOwner, const DelayWorker& methods,
              std::uint64_t id, float remaining)
        : reference(entry), owner(liveOwner), worker(methods), timerId(id), seconds(remaining)
    {
        // The caller supplies an existing native strong reference from the slot.
        // The copied reference must stay alive while native erase releases that slot.
        ++std::atomic_ref(*entry.count);
    }

    static NativeDelayReference FindUniqueEntry(void* scheduler, std::uint64_t timerId)
    {
        const auto count = field<std::uint32_t>(scheduler, Group4Count);
        if (!count || count > Capacity)
            return {};
        auto index = field<std::uint16_t>(scheduler, Group4Head);
        NativeDelayReference match{};
        for (std::uint32_t visited = 0; visited < count; ++visited)
        {
            if (index >= count)
                return {};
            const auto slot = Group4Head + index * SlotStride;
            const auto entry = field<NativeDelayReference>(scheduler, slot + SlotReference);
            if (!entry.entry)
                return {};
            if (field<std::uint64_t>(entry.entry, EntryTimer) == timerId)
            {
                if (match.entry)
                    return {};
                match = entry;
            }
            index = field<std::uint16_t>(scheduler, slot + SlotNext);
        }
        return index == UINT16_MAX ? match : NativeDelayReference{};
    }

    NativeDelayReference reference;
    DelayOwner owner;
    DelayWorker worker;
    std::uint64_t timerId;
    float seconds;
};
} // namespace ptfr
