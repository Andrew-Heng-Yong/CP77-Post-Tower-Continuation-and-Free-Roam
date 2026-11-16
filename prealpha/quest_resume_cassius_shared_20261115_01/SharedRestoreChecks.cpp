#include "source_01/RetainedQuestRestore.hpp"

#include <cstdio>
#include <cstdlib>

namespace
{
using namespace ptfr::resume;

template<class T, std::size_t N>
void Put(std::array<std::byte, N>& bytes, std::size_t offset, T value)
{
    std::memcpy(bytes.data() + offset, &value, sizeof(T));
}

template<class T>
T Read(const void* ptr, std::size_t offset)
{
    T value{};
    std::memcpy(&value, static_cast<const std::byte*>(ptr) + offset, sizeof(T));
    return value;
}

template<class T>
void Write(void* ptr, std::size_t offset, T value)
{
    std::memcpy(static_cast<std::byte*>(ptr) + offset, &value, sizeof(T));
}

template<class T, std::size_t N, std::size_t S>
void Array(std::array<std::byte, S>& object, std::size_t offset, std::array<T, N>& data, std::uint32_t count)
{
    Put(object, offset, data.data());
    Put(object, offset + 8, static_cast<std::uint32_t>(N));
    Put(object, offset + 12, count);
}

constexpr auto phases = CassiusPhases.size();
constexpr auto nodes = CassiusNodes.size();
char systemType, rootType, phaseType, definitionType, cacheType;

struct Fixture;
Fixture* f;

struct Fixture
{
    std::array<std::byte, 0x300> quests{};
    std::array<std::byte, 0xA0> root{};
    std::array<std::byte, 0x80> cache{};
    std::array<std::byte, 0x30> manager{};
    std::array<std::uint64_t, 2> roots{BaseQuest, ExpansionQuest};
    std::array<RestoreHandle, 2> rootChildren{};
    std::array<std::array<std::byte, 0x110>, ::phases> phases{};
    std::array<std::array<std::byte, 0x96>, ::phases> definitions{};
    std::array<std::array<std::byte, 0x48>, ::phases> resources{};
    std::array<std::array<std::uint16_t, MaxDepth>, ::phases> pathWords{};
    std::array<std::array<RestoreHandle, 3>, ::phases> children{};
    std::array<std::array<std::byte, 0x48>, nodes> handlers{};
    std::array<Registration, 32> rows{};
    std::array<std::uint32_t, 16> pending{};
    std::array<bool, ::phases> phasePresent{};
    std::array<std::uint32_t, ::phases> counts{};
    std::array<int, ::phases> references{};
    std::array<void*, 16> contextStack{};
    std::array<std::uint32_t, nodes> slots{};
    std::size_t failHold{};
    std::size_t failChild{};
    std::size_t contextOpened{};
    std::size_t contextClosed{};
    std::size_t phasesCreated{};
    std::size_t handlersCreated{};
    std::size_t phasesStopped{};
    std::size_t handlersRemoved{};
    Fixture()
    {
        f = this;
        Put(quests, 0, &systemType);
        Put(quests, 0x68, root.data());
        Put(quests, 0x198, cache.data());
        Put(quests, 0xE8, manager.data());
        Put(root, 0, &rootType);
        Put(cache, 0, &cacheType);
        Array(quests, 0xA8, roots, 2);
        Array(quests, 0x158, pending, 0);
        Array(root, 0x88, rootChildren, 2);
        Array(manager, 8, rows, static_cast<std::uint32_t>(rows.size()));
        rootChildren[0].object = phases[0].data();
        for (std::size_t i = 0; i < phases.size(); ++i)
        {
            Put(resources[i], 0x30, CassiusPhases[i].depot);
            RestoreHandle identity{};
            if (CassiusPhases[i].depot)
            {
                identity = {resources[i].data(), &references[i]};
                counts[i] = 1;
                if (i)
                {
                    Put(definitions[i], 0x48, identity);
                    Put(definitions[i], 0x58, std::uint8_t{1});
                }
            }
            Put(phases[i], 0, &phaseType);
            Put(phases[i], 0x30, identity);
            Put(phases[i], 0x40, phases[i].data());
            Put(phases[i], 0x80, PhaseHash(CassiusPhases[i].address));
            std::ranges::copy(CassiusPhases[i].address, pathWords[i].begin());
            Array(phases[i], 0x70, pathWords[i], static_cast<std::uint32_t>(CassiusPhases[i].address.size()));
            Array(phases[i], 0x88, children[i], 0);
            Put(definitions[i], 0, &definitionType);
            Put(definitions[i], 0x88, CassiusPhases[i].depot);
            phasePresent[i] = true;
            if (i)
                LinkChild(i);
        }
        for (std::size_t i = 0; i < rows.size(); ++i)
            rows[i] = {0, 0, 0xFFFF};
        for (std::size_t i = 0; i < handlers.size(); ++i)
            Install(i, static_cast<std::uint32_t>(i));
    }

    RestorePlan Plan() const
    {
        RestorePlan result{&CassiusCollection, {}};
        std::ranges::copy(slots, result.slots.begin());
        return result;
    }

    void Retire(std::size_t levels, bool retainSharedHandler = false)
    {
        for (std::size_t i = retainSharedHandler ? 1 : 0; i < handlers.size(); ++i)
            EraseHandler(i);
        for (std::size_t i = phases.size(); i-- > levels;)
            Detach(i);
    }

    void LinkChild(std::size_t i)
    {
        const auto parent = CassiusPhases[i].parent;
        const auto count = Read<std::uint32_t>(phases[parent].data(), 0x94);
        children[parent][count].object = phases[i].data();
        Put(phases[parent], 0x94, count + 1);
    }

    void Detach(std::size_t i)
    {
        const auto parent = CassiusPhases[i].parent;
        auto count = Read<std::uint32_t>(phases[parent].data(), 0x94);
        auto& list = children[parent];
        const auto activeChildren = std::span(list).first(count);
        const auto item = std::ranges::find(activeChildren, phases[i].data(), &RestoreHandle::object);
        if (item == activeChildren.end())
            std::abort();
        std::ranges::move(item + 1, activeChildren.end(), item);
        Put(phases[parent], 0x94, --count);
        list[count] = {};
        phasePresent[i] = false;
        if (CassiusPhases[i].depot)
        {
            --counts[i];
            auto& d = definitions[i];
            const auto refs = Read<std::uint8_t>(d.data(), 0x58);
            if (refs != 1)
                std::abort();
            Put(d, 0x48, RestoreHandle{});
            Put(d, 0x58, std::uint8_t{});
        }
    }

    void Install(std::size_t i, std::uint32_t slot)
    {
        auto& handler = handlers[i];
        const auto& target = CassiusNodes[i];
        slots[i] = slot;
        Put(handler, 0x28, slot);
        Put(handler, 0x18, manager.data());
        rows[slot] = {target.type, PhaseHash(CassiusPhases[target.phase].address), target.node};
    }

    void EraseHandler(std::size_t i)
    {
        if (slots[i] < rows.size())
            rows[slots[i]] = {0, 0, 0xFFFF};
        slots[i] = UINT32_MAX;
    }
};

std::size_t Index(const void* phase)
{
    const auto at = std::ranges::find_if(f->phases, [phase](const auto& native) { return native.data() == phase; });
    if (at == f->phases.end())
        std::abort();
    return static_cast<std::size_t>(at - f->phases.begin());
}

std::size_t DepotIndex(std::uint64_t depot)
{
    const auto at = std::ranges::find(CassiusPhases, depot, &RestorePhase::depot);
    if (!depot || at == CassiusPhases.end())
        std::abort();
    return static_cast<std::size_t>(at - CassiusPhases.begin());
}

std::size_t ChildIndex(std::size_t parent, std::uint16_t id)
{
    for (std::size_t i = 1; i < CassiusPhases.size(); ++i)
        if (CassiusPhases[i].parent == parent && CassiusPhases[i].address.back() == id)
            return i;
    std::abort();
}

std::size_t HandlerIndex(std::size_t owner, std::uint16_t id)
{
    for (std::size_t i = 0; i < CassiusNodes.size(); ++i)
        if (const auto& item = CassiusNodes[i]; owner == item.phase && id == item.node)
            return i;
    std::abort();
}

std::size_t PathIndex(const NativeRestorePath& path)
{
    const auto words = std::span(path.words, path.size);
    const auto found = std::ranges::find_if(CassiusPhases, [&](const auto& phase) { return std::ranges::equal(words, phase.address); });
    if (found == CassiusPhases.end() || path.size > path.capacity)
        std::abort();
    return static_cast<std::size_t>(found - CassiusPhases.begin());
}

RetainedQuestMethods Native()
{
    return {
        &systemType, &cacheType, &rootType, &phaseType, &definitionType,
        [](void* cache, RestoreHandle* out, std::uint64_t depot) {
            if (cache != f->cache.data()) std::abort();
            const auto i = DepotIndex(depot);
            if (f->counts[i]) { *out = {f->resources[i].data(), &f->references[i]}; ++f->references[i]; }
            return out;
        },
        [](void* cache, std::uint64_t depot, const void* callback) {
            if (cache != f->cache.data() || Read<void*>(callback, 0x40)) std::abort();
            const auto i = DepotIndex(depot);
            if (f->failHold == i || !f->counts[i]) return false;
            ++f->counts[i];
            return true;
        },
        [](void* cache, std::uint64_t depot) {
            if (cache != f->cache.data() || !f->counts[DepotIndex(depot)]) std::abort();
            --f->counts[DepotIndex(depot)];
        },
        [](RestoreHandle* handle) {
            if (handle->reference) --*static_cast<int*>(handle->reference);
        },
        [](const void* graph, RestoreHandle* out, std::uint16_t id) {
            *out = {f->definitions[ChildIndex(Index(graph), id)].data(), nullptr};
            return out;
        },
        [](const RestoreHandle* weak, RestoreHandle* out) { *out = *weak; return out; },
        [](RestoreHandle*) {},
        [](void* definition, const RestoreHandle* resource) {
            Write(definition, 0x48, *resource);
            Write(definition, 0x58, static_cast<std::uint8_t>(Read<std::uint8_t>(definition, 0x58) + 1));
        },
        [](void* definition) {
            Write(definition, 0x48, RestoreHandle{});
            Write(definition, 0x58, std::uint8_t{});
        },
        [](void* quests, void* context, std::uint8_t mode, std::uint8_t flags, std::uint32_t first, std::uint32_t second) {
            if (quests != f->quests.data() || mode < 1 || mode > 2 || flags || first != UINT32_MAX || second != UINT32_MAX)
                std::abort();
            Write(context, 0, mode);
            Write(context, 0xF8, f->contextStack.data());
            Write(context, 0x100, 16U);
            ++f->contextOpened;
            return context;
        },
        [](void*) { ++f->contextClosed; },
        [](void* root, void* ctx, NativeRestorePath* path, std::uint16_t id, const void* unused) {
            if (root != f->root.data() || Read<std::uint8_t>(ctx, 0) != 2 || unused) std::abort();
            const auto i = ChildIndex(PathIndex(*path), id);
            if (f->phasePresent[i]) std::abort();
            if (f->failChild == i) return false;
            if (CassiusPhases[i].depot && (!f->counts[i] || Read<std::uint8_t>(f->definitions[i].data(), 0x58) != 1))
                std::abort();
            f->phasePresent[i] = true;
            f->LinkChild(i);
            ++f->phasesCreated;
            return true;
        },
        [](void* root, void* ctx, const NativeRestorePath* path, std::uint16_t id) {
            if (root != f->root.data() || Read<std::uint8_t>(ctx, 0) != 2) std::abort();
            const auto i = HandlerIndex(PathIndex(*path), id);
            f->Install(i, static_cast<std::uint32_t>(i + 12));
            ++f->handlersCreated;
            return true;
        },
        [](const void* owner, std::uint32_t id) -> void* {
            const auto phase = Index(owner);
            const auto i = HandlerIndex(phase, static_cast<std::uint16_t>(id));
            return f->slots[i] != UINT32_MAX ? f->handlers[i].data() : nullptr;
        },
        [](void* owner, std::uint32_t index, void* ctx, bool dispatch) {
            if (Read<std::uint8_t>(ctx, 0) != 1 || dispatch) std::abort();
            const auto parent = Index(owner);
            const auto child = Index(f->children[parent][index].object);
            if (Read<std::uint32_t>(f->phases[child].data(), 0x94)) std::abort();
            for (std::size_t i = 0; i < CassiusNodes.size(); ++i)
            {
                const auto& target = CassiusNodes[i];
                if (target.phase == child || (target.phase == parent && target.node == CassiusPhases[child].address.back()))
                    f->EraseHandler(i);
            }
            f->Detach(child);
            ++f->phasesStopped;
            return true;
        },
        [](void* phaseContext, std::uint32_t id) {
            const auto* context = static_cast<const std::byte*>(phaseContext) - 0x110;
            if (Read<std::uint8_t>(context, 0) != 1 || Read<std::uint32_t>(context, 0x104) != 1) std::abort();
            const auto owner = Index(f->contextStack[0]);
            f->EraseHandler(HandlerIndex(owner, static_cast<std::uint16_t>(id)));
            ++f->handlersRemoved;
        },
        [](std::uint8_t* lock) {
            if (*lock) std::abort();
            *lock = 0xFF;
        },
    };
}

unsigned failed{};
void Check(bool pass, const char* report)
{
    std::printf("%s %s\n", pass ? "PASS" : "FAIL", report);
    failed += !pass;
}

bool CreateHandlers(RetainedQuestRestore& restore, Fixture& native)
{
    for (std::size_t i = 0; i < CassiusNodes.size(); ++i)
        if (!restore.CreateHandler(native.quests.data(), i) || restore.Handler(native.quests.data(), i) != native.handlers[i].data())
            return false;
    return true;
}
} // namespace

int main()
{
    {
        Fixture native;
        RetainedQuestRestore restore;
        const auto initial = native.counts;
        Check(restore.ValidateOriginal(Native(), native.quests.data(), native.Plan()) &&
                  native.counts == initial && native.contextOpened == 0,
              "cutoff validation leaves all original native objects untouched");
        Check(restore.Prepare(Native(), native.quests.data(), native.Plan()) &&
                  native.counts[1] == 2 && native.counts[8] == 2,
              "prepare holds the selected live phase resources");
        Check(!restore.CreatePhases(native.quests.data()), "live body blocks a second owner");
        Check(restore.Rollback(native.quests.data()) && native.counts == initial && native.phasePresent[8],
              "abort before retirement preserves the original owner");
    }
    {
        Fixture native;
        RetainedQuestRestore restore;
        auto* quests = native.quests.data();
        const auto prepared = restore.Prepare(Native(), quests, native.Plan());
        native.Retire(2, true);
        const auto ancestor = native.rows[0];
        Check(prepared && restore.CreatePhases(quests) && native.phasesCreated == 7 &&
                  CreateHandlers(restore, native) && native.handlersCreated == 4 && native.rows[0] == ancestor,
              "restoration reuses a coherent surviving ancestor and mints only missing handlers");
        const auto collection = native.rows[16];
        native.rows[16] = {};
        Check(!restore.Commit(), "commit rejects missing collection readback");
        native.rows[16] = collection;
        native.pending = {0, 16, 90, 14, 97};
        Put(native.quests, 0x164, 5U);
        Check(restore.Rollback(quests) && native.rows[0] == ancestor && native.phasePresent[1] &&
                  !native.phasePresent[8] && native.counts[1] == 1 && native.handlersRemoved == 0,
              "rollback leaves the surviving ancestor and removes adopted children");
        Check(Read<std::uint32_t>(quests, 0x164) == 3 && native.pending[0] == 0 &&
                  native.pending[1] == 90 && native.pending[2] == 97 &&
                  native.contextOpened == native.contextClosed,
              "rollback drains only minted notifications and balances native contexts");
    }
    {
        Fixture native;
        RetainedQuestRestore restore;
        auto* quests = native.quests.data();
        const auto prepared = restore.Prepare(Native(), quests, native.Plan());
        native.Retire(2);
        native.failChild = 8;
        Check(prepared && !restore.CreatePhases(quests) && restore.Rollback(quests) && native.phasePresent[1] &&
                  !native.phasePresent[8] && !native.counts[8] && native.counts[1] == 1,
              "a failed phase creation unwinds its resident holds and adopted children");
    }
    {
        Fixture native;
        RetainedQuestRestore restore;
        auto* quests = native.quests.data();
        const auto prepared = restore.Prepare(Native(), quests, native.Plan());
        native.Retire(1);
        Check(prepared && restore.CreatePhases(quests) &&
                  !restore.CreateHandler(quests, 4) && CreateHandlers(restore, native) &&
                  native.handlersCreated == 5 && restore.Commit() && native.phasePresent[8] &&
                  native.counts[1] == 1 && native.counts[8] == 1 && native.rows[16].node == 29,
              "the original inventory node and all four owner registrations can be restored and committed");
    }
    return failed != 0;
}
