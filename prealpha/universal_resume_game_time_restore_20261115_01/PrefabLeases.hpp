#pragma once

#include "../universal_resume_owner_20261114_01/OwnerTrace.hpp"

namespace ptfr::resume
{
struct PrefabTicketIds
{
    std::uint32_t phase;
    std::uint32_t handler;

    bool Valid() const { return phase && handler && phase != handler; }
};

struct PrefabLeases
{
    PrefabTicketIds tickets;
    std::array<std::uint64_t, 2> refs;
};

// Read from the serial quest update with the loader lifetime already pinned.
// Native cancel can remove a ready ID outside the ticket-map lock on that
// worker. The try-lock excludes concurrent streaming callbacks during the copy.
// Ticket readback verifies loader ownership. Check live world support separately.
inline std::optional<PrefabLeases> ReadPrefabLeases(void* loader, const void* loaderType, PrefabTicketIds selected,
                                                   const std::optional<PrefabLeases>& retired = std::nullopt)
{
    if (!loader || !loaderType || NativeField<const void*>(loader, 0) != loaderType || !selected.Valid())
        return std::nullopt;
    if (retired && (!retired->tickets.Valid() || selected.phase == retired->tickets.phase ||
                    selected.phase == retired->tickets.handler || selected.handler == retired->tickets.phase ||
                    selected.handler == retired->tickets.handler))
        return std::nullopt;

    struct Lock
    {
        std::atomic_ref<std::uint8_t> byte;
        bool acquired;
        explicit Lock(std::uint8_t& byte) : byte(byte), acquired(Take()) {}
        ~Lock() { if (acquired) byte.store(0, std::memory_order_release); }
        bool Take()
        {
            std::uint8_t clear{};
            return byte.compare_exchange_strong(clear, 0xFF, std::memory_order_acquire);
        }
    } lock(*reinterpret_cast<std::uint8_t*>(static_cast<std::byte*>(loader) + 0x30));
    if (!lock.acquired)
        return std::nullopt;

    const auto arrayAt = []<typename T>(const void* object, std::size_t offset) -> std::optional<std::span<const T>> {
        const auto* data = NativeField<const T*>(object, offset);
        const auto capacity = NativeField<std::uint32_t>(object, offset + 8);
        const auto size = NativeField<std::uint32_t>(object, offset + 12);
        if (size > capacity || (size && !data))
            return std::nullopt;
        return std::span<const T>(data, size);
    };
    const auto ids = arrayAt.operator()<std::uint32_t>(loader, 0x38);
    const auto ready = arrayAt.operator()<std::uint32_t>(loader, 0xA0);
    const auto refs = arrayAt.operator()<std::uint64_t>(loader, 0x60);
    const auto counts = arrayAt.operator()<std::uint32_t>(loader, 0x70);
    const auto* tickets = NativeField<const std::byte*>(loader, 0x48);
    if (!ids || !ready || !refs || !counts || !tickets || refs->size() != counts->size())
        return std::nullopt;
    const auto contains = [](auto entries, auto id) { return std::ranges::find(entries, id) != entries.end(); };
    if (retired && (contains(*ids, retired->tickets.phase) || contains(*ids, retired->tickets.handler) ||
                    contains(*ready, retired->tickets.phase) || contains(*ready, retired->tickets.handler)))
        return std::nullopt;

    PrefabLeases result{selected, {}};
    for (const auto id : {selected.phase, selected.handler})
    {
        const auto found = std::ranges::find(*ids, id);
        if (found == ids->end() || std::ranges::count(*ids, id) != 1 || contains(*ready, id))
            return std::nullopt;
        const auto* ticket = tickets + 0x68 * static_cast<std::size_t>(found - ids->begin());
        const auto resolved = arrayAt.operator()<std::uint64_t>(ticket, 0x00);
        if (!resolved || resolved->size() != 2 || !(*resolved)[0] || !(*resolved)[1] ||
            (*resolved)[0] == (*resolved)[1] || NativeField<std::uint32_t>(ticket, 0x1C) ||
            NativeField<std::uint8_t>(ticket, 0x60))
            return std::nullopt;
        if (id == selected.phase)
            std::ranges::copy(*resolved, result.refs.begin());
        else if (!std::ranges::equal(*resolved, result.refs))
            return std::nullopt;
    }
    if (retired && retired->refs != result.refs)
        return std::nullopt;

    for (const auto ref : result.refs)
    {
        const auto found = std::ranges::find(*refs, ref);
        if (found == refs->end() || std::ranges::count(*refs, ref) != 1 ||
            (*counts)[static_cast<std::size_t>(found - refs->begin())] < 2)
            return std::nullopt;
    }
    return result;
}
} // namespace ptfr::resume
