#pragma once

#include <Windows.h>

#include "../universal_resume_game_time_restore_20261115_01/PrefabLeases.hpp"

namespace ptfr::resume
{
// Valid for the pinned executable. The caller verifies the engine build
// before calling these routines or attaching the world update hook.
inline constexpr std::uint32_t WorldUpdateEntry = 0x69B1FC;
inline constexpr std::uint32_t WorldStreamingType = 0x308F3E0;
inline constexpr std::uint32_t WorldStreamingUpdateType = 0x308F3B8;
inline constexpr std::uint32_t WorldPrefabIndexLookup = 0x1ADF8C;
inline constexpr std::uint32_t WorldPrefabDesired = 0x69BB3C;

struct WorldPrefabMethods
{
    const void* worldType;
    const void* updateType;
    bool (*find)(const void*, const std::uint64_t*, std::uint32_t*, const void**);
    std::uint8_t (*desired)(const void*, std::uint64_t);
};

enum class WorldPrefabStatus : std::uint8_t
{
    MissingIndex,
    AwaitingRequest,
    AwaitingStreaming,
    Ready
};

struct WorldPrefabSupport
{
    const void* world;
    std::array<std::uint64_t, 2> refs;
    std::array<WorldPrefabStatus, 2> states;

    bool Ready() const
    {
        return states[0] == WorldPrefabStatus::Ready && states[1] == WorldPrefabStatus::Ready;
    }
};

struct PrefabLeaseBinding
{
    const void* loader;
    const void* world;
    PrefabTicketIds tickets;
    std::array<std::uint64_t, 2> refs;
};

namespace prefab_detail
{
template<typename T>
inline std::optional<std::span<const T>> Array(const void* object, std::size_t offset)
{
    const auto* data = NativeField<const T*>(object, offset);
    const auto capacity = NativeField<std::uint32_t>(object, offset + 8);
    const auto size = NativeField<std::uint32_t>(object, offset + 12);
    if (size > capacity || (size && !data))
        return std::nullopt;
    return std::span<const T>{data, size};
}

template<typename T>
inline bool Has(std::span<const T> values, T value)
{
    return std::ranges::find(values, value) != values.end();
}

inline bool ValidRefs(const std::array<std::uint64_t, 2>& refs)
{
    return refs[0] && refs[1] && refs[0] != refs[1];
}

class LoaderLock
{
public:
    explicit LoaderLock(void* loader)
        : byte(*reinterpret_cast<std::uint8_t*>(static_cast<std::byte*>(loader) + 0x30))
    {
        std::uint8_t clear{};
        acquired = byte.compare_exchange_strong(clear, 0xFF, std::memory_order_acquire);
    }

    LoaderLock(const LoaderLock&) = delete;
    LoaderLock& operator=(const LoaderLock&) = delete;

    ~LoaderLock()
    {
        if (acquired)
            byte.store(0, std::memory_order_release);
    }

    explicit operator bool() const { return acquired; }

private:
    std::atomic_ref<std::uint8_t> byte;
    bool acquired{};
};

class WorldLock
{
public:
    WorldLock(void* world, std::size_t offset)
        : lock(reinterpret_cast<SRWLOCK*>(static_cast<std::byte*>(world) + offset)),
          acquired(TryAcquireSRWLockShared(lock) != FALSE)
    {
    }

    WorldLock(const WorldLock&) = delete;
    WorldLock& operator=(const WorldLock&) = delete;

    ~WorldLock()
    {
        if (acquired)
            ReleaseSRWLockShared(lock);
    }

    explicit operator bool() const { return acquired; }

private:
    SRWLOCK* lock;
    bool acquired;
};

struct LoaderIndex
{
    std::span<const std::uint32_t> ids;
    std::span<const std::uint32_t> ready;
    std::span<const std::uint64_t> refs;
    std::span<const std::uint32_t> counts;

    bool HasTicket(std::uint32_t id) const
    {
        return id && (Has(ids, id) || Has(ready, id));
    }

    std::optional<std::uint32_t> RefCount(std::uint64_t ref) const
    {
        const auto found = std::ranges::find(refs, ref);
        if (found == refs.end())
            return 0;
        if (std::ranges::count(refs, ref) != 1)
            return std::nullopt;
        const auto count = counts[static_cast<std::size_t>(found - refs.begin())];
        return count ? std::optional(count) : std::nullopt;
    }
};

inline std::optional<LoaderIndex> ReadIndex(const void* loader)
{
    const auto ids = Array<std::uint32_t>(loader, 0x38);
    const auto ready = Array<std::uint32_t>(loader, 0xA0);
    const auto refs = Array<std::uint64_t>(loader, 0x60);
    const auto counts = Array<std::uint32_t>(loader, 0x70);
    if (!ids || !ready || !refs || !counts || refs->size() != counts->size())
        return std::nullopt;
    return LoaderIndex{*ids, *ready, *refs, *counts};
}

inline bool ValidLoader(const void* loader, const void* loaderType)
{
    return loader && loaderType && NativeField<const void*>(loader, 0) == loaderType;
}

inline bool SameOwner(const PrefabLeaseBinding& binding, const void* loader, const void* world)
{
    return binding.loader == loader && binding.world == world && binding.tickets.phase &&
           binding.tickets.phase != binding.tickets.handler && ValidRefs(binding.refs);
}

struct WorldRequest
{
    std::uint64_t ref;
    std::uint8_t desired;
};
static_assert(sizeof(WorldRequest) == 16);

inline std::optional<WorldPrefabStatus> ObserveRef(const void* world, const WorldPrefabMethods& native,
                                                   std::uint64_t ref, const std::byte* sectors,
                                                   std::uint32_t sectorCount,
                                                   std::span<const WorldRequest> requests)
{
    const void* record{};
    std::uint32_t bucket{};
    const auto* index = static_cast<const std::byte*>(world) + 0x128;
    if (!native.find(index, &ref, &bucket, &record))
        return WorldPrefabStatus::MissingIndex;
    if (!record || NativeField<std::uint64_t>(record, 8) != ref)
        return std::nullopt;
    const auto indices = Array<std::uint32_t>(record, 0x10);
    if (!indices || indices->empty())
        return WorldPrefabStatus::MissingIndex;
    if (std::ranges::any_of(requests, [ref](const WorldRequest& request) { return request.ref == ref; }) ||
        native.desired(world, ref) != 1)
        return WorldPrefabStatus::AwaitingRequest;

    bool fulfilledNode = false;
    for (const auto sectorIndex : *indices)
    {
        if (sectorIndex >= sectorCount)
            return std::nullopt;
        const auto* sector = sectors + static_cast<std::size_t>(sectorIndex) * 0x90;
        if (!NativeField<const void*>(sector, 0x28) || NativeField<std::uint8_t>(sector, 0x80) != 1 ||
            NativeField<std::uint8_t>(sector, 0x82) != 2)
            return WorldPrefabStatus::AwaitingStreaming;

        const auto nodes = Array<const void*>(sector, 0x50);
        if (!nodes)
            return std::nullopt;
        for (const auto* node : *nodes)
        {
            if (!node || !(NativeField<std::uint8_t>(node, 0x25) & 8))
                continue;
            if (!(NativeField<std::uint8_t>(node, 0x25) & 4))
                return WorldPrefabStatus::AwaitingStreaming;
            const auto* data = NativeField<const void*>(node, 8);
            if (data && !(NativeField<std::uint8_t>(data, 0x8C) & 0x20))
                return WorldPrefabStatus::AwaitingStreaming;
            fulfilledNode |= data != nullptr;
        }
    }
    return fulfilledNode ? WorldPrefabStatus::Ready : WorldPrefabStatus::AwaitingStreaming;
}
} // namespace prefab_detail

// Both lease functions run after the stock quest notification pass, or on
// its serial graph worker. They copy resolved identities under the loader's
// own lock. The restorer verifies the phase and handler before reading their
// ticket numbers. A stock mode-2 handler contributes zero to tickets.handler.
inline std::optional<PrefabLeaseBinding> ReadPrefabLeaseBinding(
    void* loader, const void* loaderType, PrefabTicketIds tickets,
    const std::optional<PrefabLeaseBinding>& retired = std::nullopt)
{
    using namespace prefab_detail;
    if (!ValidLoader(loader, loaderType) || !tickets.phase || tickets.phase == tickets.handler)
        return std::nullopt;
    const LoaderLock lock(loader);
    if (!lock)
        return std::nullopt;
    const auto* world = NativeField<const void*>(loader, 0xC8);
    const auto index = ReadIndex(loader);
    const auto* rows = NativeField<const std::byte*>(loader, 0x48);
    if (!world || !index || !rows)
        return std::nullopt;
    if (retired && (!SameOwner(*retired, loader, world) || index->HasTicket(retired->tickets.phase) ||
                    index->HasTicket(retired->tickets.handler)))
        return std::nullopt;

    PrefabLeaseBinding binding{loader, world, tickets, {}};
    for (const auto id : {tickets.phase, tickets.handler})
    {
        if (!id)
            continue;
        const auto found = std::ranges::find(index->ids, id);
        if (found == index->ids.end() || std::ranges::count(index->ids, id) != 1 || Has(index->ready, id))
            return std::nullopt;
        const auto* row = rows + 0x68 * static_cast<std::size_t>(found - index->ids.begin());
        const auto resolved = Array<std::uint64_t>(row, 0);
        if (!resolved || resolved->size() != binding.refs.size() || NativeField<std::uint32_t>(row, 0x1C) ||
            NativeField<std::uint8_t>(row, 0x60))
            return std::nullopt;
        if (id == tickets.phase)
            std::ranges::copy(*resolved, binding.refs.begin());
        else if (!std::ranges::equal(*resolved, binding.refs))
            return std::nullopt;
    }
    if (!ValidRefs(binding.refs) || (retired && retired->refs != binding.refs))
        return std::nullopt;
    for (const auto ref : binding.refs)
    {
        const auto count = index->RefCount(ref);
        if (!count || *count < (tickets.handler ? 2U : 1U))
            return std::nullopt;
    }
    return binding;
}

// Positive shared counts may belong to unrelated owners. Old ticket IDs and
// ready IDs must be absent even when existing leases keep the sectors present.
inline std::optional<std::array<std::uint32_t, 2>> ReadPrefabRetirement(
    void* loader, const void* loaderType, const PrefabLeaseBinding& retired)
{
    using namespace prefab_detail;
    if (!ValidLoader(loader, loaderType))
        return std::nullopt;
    const LoaderLock lock(loader);
    if (!lock || !SameOwner(retired, loader, NativeField<const void*>(loader, 0xC8)))
        return std::nullopt;
    const auto index = ReadIndex(loader);
    if (!index || index->HasTicket(retired.tickets.phase) || index->HasTicket(retired.tickets.handler))
        return std::nullopt;
    const auto main = index->RefCount(retired.refs[0]);
    const auto reyes = index->RefCount(retired.refs[1]);
    if (!main || !reyes)
        return std::nullopt;
    return std::array{*main, *reyes};
}

// Call on the native world worker after the stock update returns. The caller
// compares world and refs with the retained quest session, then publishes
// only this value snapshot. No native world pointers cross the worker boundary
// for dereference. A later world update can change streaming state normally.
inline std::optional<WorldPrefabSupport> ReadWorldPrefabSupport(
    void* update, const void* expectedWorld, const std::array<std::uint64_t, 2>& refs,
    const WorldPrefabMethods& native)
{
    using namespace prefab_detail;
    if (!update || !expectedWorld || !ValidRefs(refs) || !native.worldType || !native.updateType ||
        !native.find || !native.desired || NativeField<const void*>(update, 0) != native.updateType)
        return std::nullopt;
    auto* world = static_cast<std::byte*>(update) - 0x48;
    if (world != expectedWorld || NativeField<const void*>(world, 0) != native.worldType)
        return std::nullopt;
    const WorldLock indexLock(world, 0x2A0);
    if (!indexLock)
        return std::nullopt;
    const WorldLock queueLock(world, 0x2E8);
    if (!queueLock)
        return std::nullopt;
    const auto requests = Array<WorldRequest>(world, 0x2D8);
    const auto* sectors = NativeField<const std::byte*>(world, 0x50);
    const auto size = NativeField<std::uint32_t>(world, 0x5C);
    const auto capacity = NativeField<std::uint32_t>(world, 0x58);
    if (!requests || size > capacity || (size && !sectors))
        return std::nullopt;
    WorldPrefabSupport support{world, refs, {}};
    for (std::size_t i = 0; i < refs.size(); ++i)
    {
        const auto state = ObserveRef(world, native, refs[i], sectors, size, *requests);
        if (!state)
            return std::nullopt;
        support.states[i] = *state;
    }
    return support;
}
} // namespace ptfr::resume
