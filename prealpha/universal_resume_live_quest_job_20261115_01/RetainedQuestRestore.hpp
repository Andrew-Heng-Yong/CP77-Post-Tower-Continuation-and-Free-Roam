#pragma once

#include "../universal_resume_falco_transfer_20261115_01/FalcoRestorePlan.hpp"

#include <atomic>
#include <type_traits>

namespace ptfr::resume
{
struct RestoreHandle
{
    void* object{};
    void* reference{};
    bool operator==(const RestoreHandle&) const = default;
};

struct NativeRestorePath
{
    std::uint16_t* words;
    std::uint32_t capacity;
    std::uint32_t size;
};
static_assert(sizeof(NativeRestorePath) == 0x10);

struct RetainedQuestMethods
{
    const void* systemType{};
    const void* cacheType{};
    const void* rootType{};
    const void* phaseType{};
    const void* definitionType{};

    RestoreHandle* (*lookup)(void*, RestoreHandle*, std::uint64_t){};
    bool (*hold)(void*, std::uint64_t, const void*){};
    void (*release)(void*, std::uint64_t){};
    void (*releaseHandle)(RestoreHandle*){};
    RestoreHandle* (*findDefinition)(const void*, RestoreHandle*, std::uint16_t){};
    RestoreHandle* (*promoteDefinition)(const RestoreHandle*, RestoreHandle*){};
    void (*releaseDefinition)(RestoreHandle*){};
    void (*bindDefinition)(void*, const RestoreHandle*){};
    void (*unbindDefinition)(void*){};

    void* (*open)(void*, void*, std::uint8_t, std::uint8_t, std::uint32_t, std::uint32_t){};
    void (*close)(void*){};
    bool (*phase)(void*, void*, NativeRestorePath*, std::uint16_t, const void*){};
    bool (*handler)(void*, void*, const NativeRestorePath*, std::uint16_t){};
    void* (*findHandler)(const void*, std::uint32_t){};
    bool (*stopChild)(void*, std::uint32_t, void*, bool){};
    void (*removeHandler)(void*, std::uint32_t){};
    void (*lockQueue)(std::uint8_t*){};

    static RetainedQuestMethods FromImage(const std::uint8_t* image)
    {
        RetainedQuestMethods result{};
        if (!image)
            return result;
        const auto bind = [image](auto& field, std::uintptr_t offset) {
            field = reinterpret_cast<std::remove_reference_t<decltype(field)>>(image + offset);
        };
        bind(result.systemType, 0x30BCE78);
        bind(result.cacheType, 0x306F758);
        bind(result.rootType, 0x3699F88);
        bind(result.phaseType, 0x308A948);
        bind(result.definitionType, 0x30470A8);
        bind(result.lookup, 0x350C30);
        bind(result.hold, 0x21F99E0);
        bind(result.release, 0x34F7C4);
        bind(result.releaseHandle, 0x195798);
        bind(result.findDefinition, 0x32D31C);
        bind(result.promoteDefinition, 0x189688);
        bind(result.releaseDefinition, 0x409774);
        bind(result.bindDefinition, 0x350BF8);
        bind(result.unbindDefinition, 0x34F330);
        bind(result.open, 0x2B30A0);
        bind(result.close, 0x2B2D50);
        bind(result.phase, 0x2B33F0);
        bind(result.handler, 0x2B25CC);
        bind(result.findHandler, 0x2B1B64);
        bind(result.stopChild, 0xBEC6D4);
        bind(result.removeHandler, 0x2FCEAC);
        bind(result.lockQueue, 0x22CA300);
        return result;
    }
};

// Every call touching game memory belongs on the graph-locked quest worker with
// a current, retained quest-system owner. Prepare borrows only resident native
// cache entries. The caller keeps the save permit across the graph transaction.
class RetainedQuestRestore
{
    static constexpr std::array<std::size_t, FalcoPhases.size()> Parents{0, 0, 1, 2, 3, 4, 5, 6, 6};
    static constexpr std::size_t FirstBody = 6;

    struct PhaseEntry
    {
        RestoreHandle identity{};
        void* owner{};
        bool held{};
        bool created{};
    };

    struct ActiveHandler
    {
        void* owner{};
        std::uint32_t slot{UINT32_MAX};
    };

    struct Context
    {
        alignas(16) std::array<std::byte, 0x350> bytes{};
        const RetainedQuestMethods& native;
        Context(const RetainedQuestMethods& ops, void* quests, std::uint8_t mode) : native(ops)
        {
            native.open(quests, bytes.data(), mode, 0, UINT32_MAX, UINT32_MAX);
        }
        Context(const Context&) = delete;
        Context& operator=(const Context&) = delete;
        ~Context() { native.close(bytes.data()); }

        void* Data() { return bytes.data(); }

        bool Select(void* phase)
        {
            auto** stack = Read<void**>(Data(), 0xF8);
            if (!stack || !Read<std::uint32_t>(Data(), 0x100) || Read<std::uint32_t>(Data(), 0x104))
                return false;
            *stack = phase;
            Write(Data(), 0x104, std::uint32_t{1});
            return true;
        }
    };

public:
    RetainedQuestRestore() = default;
    RetainedQuestRestore(const RetainedQuestRestore&) = delete;
    RetainedQuestRestore& operator=(const RetainedQuestRestore&) = delete;

    bool Prepare(const std::uint8_t* image, void* quests, const FalcoRestorePlan& plan)
    {
        return Prepare(RetainedQuestMethods::FromImage(image), quests, plan);
    }

    bool Prepare(const RetainedQuestMethods& ops, void* quests, const FalcoRestorePlan& plan)
    {
        if (system || !Is(quests, ops.systemType) || !ValidPlan(plan))
            return false;
        native = ops;
        system = quests;
        cache = Read<void*>(quests, 0x198);
        root = Read<void*>(quests, 0x68);
        if (!Is(cache, native.cacheType) || !Is(root, native.rootType))
        {
            Forget();
            return false;
        }

        const auto base = Observe(0);
        if (!base || !*base || ResourceDepot(*base) != BaseQuest || !MatchesRoots())
        {
            Forget();
            return false;
        }
        entries[0].owner = *base;

        // Validate the complete live selection before taking any cache holds.
        for (std::size_t i = 0; i < FalcoPhases.size(); ++i)
        {
            const auto phase = Observe(i);
            if (!phase || !*phase || ResourceDepot(*phase) != FalcoPhases[i].depot)
            {
                Forget();
                return false;
            }
            entries[i].identity = Read<RestoreHandle>(*phase, 0x30);
        }
        for (std::size_t i = 0; i < plan.paths.size(); ++i)
        {
            const auto entry = ObserveHandler(i);
            if (!entry || !entry->owner || entry->slot != plan.paths[i].retiredSlot)
            {
                Forget();
                return false;
            }
        }

        // 21F99E0 acquires on a hit. Its unloaded-path return is read-only and
        // its empty callback object cannot schedule resource work.
        alignas(16) const std::array<std::byte, 0x48> emptyCallback{};
        for (std::size_t i = 1; i < FalcoPhases.size(); ++i)
        {
            const auto depot = FalcoPhases[i].depot;
            if (!depot)
                continue;
            if (!CacheMatches(i) || !native.hold(cache, depot, emptyCallback.data()))
            {
                if (ReleaseUnadopted())
                    Forget();
                return false;
            }
            entries[i].held = true;
        }
        prepared = true;
        return true;
    }

    bool CreatePhases(void* quests)
    {
        if (!prepared || attempted || !MatchesOwner(quests))
            return false;
        const auto competing = Observe(FalcoPrivateQuest);
        if (!competing || *competing)
            return false;
        // Validate the retained graph and resources before the first mutation.
        for (std::size_t i = 1; i < FalcoPhases.size(); ++i)
        {
            const auto current = Observe(i);
            if (!current || (*current && (i >= FirstBody || !MatchesResource(*current, i))) ||
                (entries[i].held && !CacheMatches(i)))
                return false;
        }
        for (std::size_t i = 0; i < FalcoRestoreNodes.size(); ++i)
        {
            const auto old = ObserveHandler(i);
            if (!old || old->owner)
                return false;
        }

        attempted = true;
        for (std::size_t i = 1; i < FalcoPhases.size(); ++i)
        {
            const auto present = Observe(i);
            if (!present)
                return false;
            if (*present)
                entries[i].owner = *present;
            else if (!CreateChild(i))
                return false;
        }
        phasesReady = true;
        return true;
    }

    bool CreateHandler(void* quests, std::size_t index)
    {
        if (!phasesReady || !MatchesOwner(quests) || index != nextHandler || index >= FalcoRestoreNodes.size())
            return false;
        const auto before = ObserveHandler(index);
        const auto& target = FalcoRestoreNodes[index];
        const auto owner = Phase(quests, target.phase);
        if (!before || before->owner || !owner)
            return false;

        // Native minting uses the original phase and node key in mode 2.
        // No position in the live event-manager table is edited or dispatched in bulk.
        auto words = AddressWords(FalcoPhases[target.phase].address);
        const NativeRestorePath parent{words.data(), static_cast<std::uint32_t>(words.size()),
                                       static_cast<std::uint32_t>(FalcoPhases[target.phase].address.size())};
        Context context(native, system, 2);
        const auto dispatched = native.handler(root, context.Data(), &parent, target.node);
        const auto after = ObserveHandler(index);
        if (after && after->owner)
            installed[index] = *after;
        else if (!after)
            uncertain = true;
        if (!dispatched || !after || !after->owner)
            return false;
        ++nextHandler;
        return true;
    }

    void* Phase(void* quests, std::size_t index) const
    {
        if (index >= FalcoPhases.size() || !MatchesOwner(quests))
            return nullptr;
        const auto item = Observe(index);
        return item && *item && *item == entries[index].owner && MatchesResource(*item, index) ? *item : nullptr;
    }

    void* Handler(void* quests, std::size_t index) const
    {
        if (index >= installed.size() || !Phase(quests, FalcoRestoreNodes[index].phase))
            return nullptr;
        const auto item = ObserveHandler(index);
        return item && installed[index].owner == item->owner && installed[index].slot == item->slot
                   ? item->owner : nullptr;
    }

    bool Rollback(void* quests)
    {
        if (!system)
            return true;
        if (!SameCache(quests) || (attempted && !MatchesOwner(quests)))
            return false;

        // Stop each owner we created, deepest first. Check identity just before
        // stopping it, and use the native parent/child unlink path.
        for (std::size_t i = entries.size(); i-- > 1;)
        {
            auto& entry = entries[i];
            if (!entry.created)
                continue;
            const auto parent = Observe(Parents[i]);
            const auto child = Observe(i);
            if (!parent || !*parent || *parent != entries[Parents[i]].owner || !child || *child != entry.owner)
                return false;
            const auto children = ArrayAt<RestoreHandle>(*parent, 0x88, MaxPhases);
            if (!children)
                return false;
            const auto at = std::ranges::find(*children, *child, &RestoreHandle::object);
            if (at == children->end())
                return false;
            Context context(native, system, 1);
            if (!native.stopChild(*parent, static_cast<std::uint32_t>(at - children->begin()), context.Data(), false))
                return false;
            const auto gone = Observe(i);
            if (!gone || *gone)
                return false;
            entry.created = false;
            entry.owner = nullptr;
        }

        // StopChild removes handlers in stopped phases and its owning node.
        // Explicitly remove any selected newly installed handler on a retained phase.
        for (std::size_t i = installed.size(); i-- > 0;)
        {
            if (!installed[i].owner)
                continue;
            const auto actual = ObserveHandler(i);
            if (!actual)
                return false;
            if (!actual->owner)
                continue;
            if (actual->owner != installed[i].owner || actual->slot != installed[i].slot)
                return false;
            const auto phase = Phase(quests, FalcoRestoreNodes[i].phase);
            if (!phase)
                return false;
            Context context(native, system, 1);
            if (!context.Select(phase))
                return false;
            native.removeHandler(static_cast<std::byte*>(context.Data()) + 0x110, FalcoRestoreNodes[i].node);
            const auto gone = ObserveHandler(i);
            if (!gone || gone->owner)
                return false;
        }
        if (attempted && !DiscardNotifications())
            return false;
        if (!ReleaseUnadopted() || uncertain)
            return false;
        Forget();
        return true;
    }

    bool Commit()
    {
        if (nextHandler != installed.size() || !MatchesOwner(system))
            return false;
        for (std::size_t i = 0; i < installed.size(); ++i)
            if (!Handler(system, i))
                return false;
        if (!ReleaseUnadopted())
            return false;
        Forget();
        return true;
    }

    // The transition owns the still-valid quest-system lifetime and will stop
    // the adopted children. This path touches only the native cache, which
    // serializes lookup and release with its own lock.
    bool ReleaseUnadopted(void* quests)
    {
        return !system || (SameCache(quests) && ReleaseUnadopted());
    }

    // Drop identity-only bookkeeping once the native cache and graph were torn
    // down. With a still-live cache, Rollback performs the matching release.
    void Forget()
    {
        system = cache = root = nullptr;
        entries = {};
        installed = {};
        attempted = phasesReady = prepared = uncertain = false;
        nextHandler = 0;
    }

private:
    template<class T>
    static T Read(const void* object, std::size_t offset)
    {
        T result{};
        std::memcpy(&result, static_cast<const std::byte*>(object) + offset, sizeof(T));
        return result;
    }

    template<class T>
    static void Write(void* object, std::size_t offset, T value)
    {
        std::memcpy(static_cast<std::byte*>(object) + offset, &value, sizeof(T));
    }

    static bool Is(const void* object, const void* type)
    {
        return object && type && Read<const void*>(object, 0) == type;
    }

    template<class T>
    static std::optional<std::span<const T>> ArrayAt(const void* object, std::size_t offset, std::size_t limit)
    {
        const auto count = Read<std::uint32_t>(object, offset + 12);
        const auto capacity = Read<std::uint32_t>(object, offset + 8);
        const auto* data = Read<const T*>(object, offset);
        if (count > capacity || count > limit || (count && !data))
            return std::nullopt;
        return std::span<const T>(data, count);
    }

    static std::array<std::uint16_t, MaxDepth> AddressWords(std::span<const std::uint16_t> address)
    {
        std::array<std::uint16_t, MaxDepth> words{};
        std::ranges::copy(address, words.begin());
        return words;
    }

    static bool ValidPlan(const FalcoRestorePlan& plan)
    {
        for (std::size_t i = 0; i < plan.paths.size(); ++i)
        {
            const auto& target = FalcoRestoreNodes[i];
            const auto address = FalcoPhases[target.phase].address;
            const auto& path = plan.paths[i];
            if (path.size != address.size() + 1 || path.retiredSlot >= MaxSlots ||
                path.words[address.size()] != target.node || !std::ranges::equal(std::span(path.words).first(address.size()), address))
                return false;
        }
        return true;
    }

    bool SameCache(const void* quests) const
    {
        return quests && quests == system && Is(quests, native.systemType) &&
               Read<const void*>(quests, 0x198) == cache && Is(cache, native.cacheType);
    }

    bool MatchesRoots() const
    {
        const auto roots = ArrayAt<std::uint64_t>(system, 0xA8, 64);
        return roots && roots->size() >= 2 && (*roots)[0] == BaseQuest && (*roots)[1] == ExpansionQuest;
    }

    bool MatchesOwner(const void* quests) const
    {
        if (!SameCache(quests) || Read<const void*>(quests, 0x68) != root || !Is(root, native.rootType) || !MatchesRoots())
            return false;
        const auto base = Observe(0);
        return base && *base && *base == entries[0].owner && MatchesResource(*base, 0);
    }

    static std::uint64_t ResourceDepot(const void* phase)
    {
        const auto* resource = Read<const void*>(phase, 0x30);
        return resource ? Read<std::uint64_t>(resource, 0x30) : 0;
    }

    bool MatchesResource(const void* phase, std::size_t index) const
    {
        return ResourceDepot(phase) == FalcoPhases[index].depot &&
               Read<RestoreHandle>(phase, 0x30) == entries[index].identity;
    }

    std::optional<void*> Observe(std::size_t index) const { return Observe(FalcoPhases[index].address); }

    std::optional<void*> Observe(std::span<const std::uint16_t> address) const
    {
        const auto roots = ArrayAt<RestoreHandle>(root, 0x88, 64);
        if (!roots || address.empty())
            return std::nullopt;
        if (address.front() >= roots->size() || !(*roots)[address.front()].object)
            return nullptr;
        auto* phase = (*roots)[address.front()].object;
        for (std::size_t i = 1; i <= address.size(); ++i)
        {
            const auto expected = address.first(i);
            const auto hash = PhaseHash(expected);
            if (!Is(phase, native.phaseType) || Read<std::uint32_t>(phase, 0x80) != hash)
                return std::nullopt;
            const auto path = ArrayAt<std::uint16_t>(phase, 0x70, MaxDepth);
            if (!path || !std::ranges::equal(*path, expected))
                return std::nullopt;
            if (i == address.size())
                return phase;

            const auto children = ArrayAt<RestoreHandle>(phase, 0x88, MaxPhases);
            if (!children)
                return std::nullopt;
            const auto childHash = PhaseHash(address.first(i + 1));
            phase = nullptr;
            for (const auto& child : *children)
            {
                if (!Is(child.object, native.phaseType))
                    return std::nullopt;
                if (Read<std::uint32_t>(child.object, 0x80) != childHash)
                    continue;
                if (phase)
                    return std::nullopt;
                phase = child.object;
            }
            if (!phase)
                return nullptr;
        }
        return std::nullopt;
    }

    std::optional<ActiveHandler> ObserveHandler(std::size_t index) const
    {
        const auto& target = FalcoRestoreNodes[index];
        const auto phase = Observe(target.phase);
        const auto manager = Read<const void*>(system, 0xE8);
        if (!phase || !manager)
            return std::nullopt;
        const auto rows = ArrayAt<Registration>(manager, 8, MaxSlots);
        if (!rows)
            return std::nullopt;
        const auto hash = PhaseHash(FalcoPhases[target.phase].address);
        const auto hasKey = [&](const Registration& row) { return row.phase == hash && row.node == target.node; };
        const auto row = std::ranges::find_if(*rows, hasKey);
        const auto handler = *phase ? native.findHandler(*phase, target.node) : nullptr;
        if (!handler && row == rows->end())
            return ActiveHandler{};
        if (!handler || row == rows->end() || row->type != target.type || std::ranges::count_if(*rows, hasKey) != 1)
            return std::nullopt;
        const auto slot = static_cast<std::uint32_t>(row - rows->begin());
        if (Read<std::uint32_t>(handler, 0x28) != slot || Read<const void*>(handler, 0x18) != manager)
            return std::nullopt;
        return ActiveHandler{handler, slot};
    }

    bool CacheMatches(std::size_t index) const
    {
        RestoreHandle current{};
        native.lookup(cache, &current, FalcoPhases[index].depot);
        const auto exact = current.object && current.reference && current == entries[index].identity;
        native.releaseHandle(&current);
        return exact;
    }

    bool ReleaseUnadopted()
    {
        bool complete = true;
        for (std::size_t i = 1; i < entries.size(); ++i)
        {
            if (!entries[i].held)
                continue;
            if (!CacheMatches(i))
            {
                complete = false;
                continue;
            }
            native.release(cache, FalcoPhases[i].depot);
            entries[i].held = false;
        }
        return complete;
    }

    bool CreateChild(std::size_t index)
    {
        const auto parent = Phase(system, Parents[index]);
        const auto graph = parent ? Read<const void*>(parent, 0x40) : nullptr;
        if (!graph)
            return false;
        const auto childId = FalcoPhases[index].address.back();
        RestoreHandle weak{};
        native.findDefinition(graph, &weak, childId);
        RestoreHandle strong{};
        native.promoteDefinition(&weak, &strong);
        native.releaseDefinition(&weak);
        struct DropHandle
        {
            const RetainedQuestMethods& native;
            RestoreHandle& handle;
            ~DropHandle() { native.releaseHandle(&handle); }
        } drop{native, strong};
        auto* definition = strong.object;
        if (!Is(definition, native.definitionType) || Read<std::uint64_t>(definition, 0x88) != FalcoPhases[index].depot)
            return false;

        // The native preload walker binds one definition reference for each
        // newly created external phase. Existing coherent references can be shared.
        const auto depot = FalcoPhases[index].depot;
        if (depot)
        {
            const auto count = Read<std::uint8_t>(definition, 0x58);
            if (!entries[index].held || count == UINT8_MAX ||
                (count && Read<RestoreHandle>(definition, 0x48) != entries[index].identity) || !CacheMatches(index))
                return false;
            native.bindDefinition(definition, &entries[index].identity);
        }

        const auto parentAddress = FalcoPhases[Parents[index]].address;
        auto words = AddressWords(parentAddress);
        NativeRestorePath path{words.data(), static_cast<std::uint32_t>(words.size()),
                              static_cast<std::uint32_t>(parentAddress.size())};
        Context context(native, system, 2);
        const auto dispatched = native.phase(root, context.Data(), &path, childId, nullptr);
        const auto child = Observe(index);
        if (!child)
        {
            uncertain = true;
            return false;
        }
        if (*child)
        {
            entries[index].owner = *child;
            entries[index].created = true;
            // 2B1D30 releases this cache hold when the new phase stops.
            entries[index].held = false;
            return dispatched && MatchesResource(*child, index);
        }
        if (depot)
            native.unbindDefinition(definition);
        return false;
    }

    bool DiscardNotifications() const
    {
        auto* lock = reinterpret_cast<std::uint8_t*>(static_cast<std::byte*>(system) + 0x150);
        native.lockQueue(lock);
        struct Unlock
        {
            std::uint8_t& byte;
            ~Unlock() { std::atomic_ref(byte).store(0, std::memory_order_release); }
        } unlock{*lock};
        const auto pending = ArrayAt<std::uint32_t>(system, 0x158, MaxQueue);
        if (!pending)
            return false;
        auto* data = const_cast<std::uint32_t*>(pending->data());
        std::uint32_t kept{};
        for (const auto slot : *pending)
        {
            if (std::ranges::none_of(installed, [slot](const auto& entry) { return entry.owner && entry.slot == slot; }))
                data[kept++] = slot;
        }
        Write(system, 0x164, kept);
        return true;
    }

    RetainedQuestMethods native{};
    void* system{};
    void* cache{};
    void* root{};
    std::array<PhaseEntry, FalcoPhases.size()> entries{};
    std::array<ActiveHandler, FalcoRestoreNodes.size()> installed{};
    std::size_t nextHandler{};
    bool prepared{};
    bool attempted{};
    bool phasesReady{};
    bool uncertain{};
};
} // namespace ptfr::resume
