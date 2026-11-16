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

constexpr std::array<std::size_t, 9> parents{0, 0, 1, 2, 3, 4, 5, 6, 6};
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
    std::array<std::array<std::byte, 0x110>, 9> phases{};
    std::array<std::array<std::byte, 0x96>, 9> definitions{};
    std::array<std::array<std::byte, 0x48>, 9> resources{};
    std::array<std::array<std::uint16_t, MaxDepth>, 9> pathWords{};
    std::array<std::array<RestoreHandle, 3>, 9> children{};
    std::array<std::array<std::byte, 0x48>, 9> handlers{};
    std::array<Registration, 32> rows{};
    std::array<std::uint32_t, 16> pending{};
    std::array<bool, 9> phasePresent{};
    std::array<std::uint32_t, 9> counts{};
    std::array<int, 9> references{};
    std::array<void*, 16> contextStack{};
    std::array<std::uint32_t, 9> slots{};
    std::size_t failHold{};
    std::size_t failChild{};
    std::size_t contextOpened{};
    std::size_t contextClosed{};
    std::size_t phasesCreated{};
    std::size_t handlersCreated{};
    std::size_t phasesStopped{};
    std::size_t handlersRemoved{};
    bool elapsedWait{};

    const RestoreNode& ExpectedNode(std::size_t i) const
    {
        return elapsedWait && i == handlers.size() - 1 ? FalcoAfterWait : FalcoRestoreNodes[i];
    }

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
            Put(resources[i], 0x30, FalcoPhases[i].depot);
            RestoreHandle identity{};
            if (FalcoPhases[i].depot)
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
            Put(phases[i], 0x80, PhaseHash(FalcoPhases[i].address));
            std::ranges::copy(FalcoPhases[i].address, pathWords[i].begin());
            Array(phases[i], 0x70, pathWords[i], static_cast<std::uint32_t>(FalcoPhases[i].address.size()));
            Array(phases[i], 0x88, children[i], 0);
            Put(definitions[i], 0, &definitionType);
            Put(definitions[i], 0x88, FalcoPhases[i].depot);
            phasePresent[i] = true;
            if (i)
                LinkChild(i);
        }
        for (std::size_t i = 0; i < rows.size(); ++i)
            rows[i] = {0, 0, 0xFFFF};
        for (std::size_t i = 0; i < handlers.size(); ++i)
            Install(i, static_cast<std::uint32_t>(i));
    }

    FalcoRestorePlan Plan() const
    {
        FalcoRestorePlan result{};
        for (std::size_t i = 0; i < handlers.size(); ++i)
        {
            const auto& target = FalcoRestoreNodes[i];
            const auto address = FalcoPhases[target.phase].address;
            auto& path = result.paths[i];
            std::ranges::copy(address, path.words.begin());
            path.words[address.size()] = target.node;
            path.size = static_cast<std::uint32_t>(address.size() + 1);
            path.retiredSlot = slots[i];
        }
        return result;
    }

    void Retire(std::size_t levels)
    {
        for (std::size_t i = 0; i < handlers.size(); ++i)
            EraseHandler(i);
        for (std::size_t i = phases.size(); i-- > levels;)
            Detach(i);
    }

    void LinkChild(std::size_t i)
    {
        const auto parent = parents[i];
        const auto count = Read<std::uint32_t>(phases[parent].data(), 0x94);
        children[parent][count].object = phases[i].data();
        Put(phases[parent], 0x94, count + 1);
    }

    void Detach(std::size_t i)
    {
        const auto parent = parents[i];
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
        if (FalcoPhases[i].depot)
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
        const auto& target = ExpectedNode(i);
        slots[i] = slot;
        Put(handler, 0x28, slot);
        Put(handler, 0x18, manager.data());
        rows[slot] = {target.type, PhaseHash(FalcoPhases[target.phase].address), target.node};
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
    const auto at = std::ranges::find(FalcoPhases, depot, &RestorePhase::depot);
    if (!depot || at == FalcoPhases.end())
        std::abort();
    return static_cast<std::size_t>(at - FalcoPhases.begin());
}

std::size_t ChildIndex(std::size_t parent, std::uint16_t id)
{
    for (std::size_t i = 1; i < parents.size(); ++i)
        if (parents[i] == parent && FalcoPhases[i].address.back() == id)
            return i;
    std::abort();
}

std::size_t HandlerIndex(std::size_t owner, std::uint16_t id)
{
    for (std::size_t i = 0; i < FalcoRestoreNodes.size(); ++i)
        if (const auto& item = f->ExpectedNode(i); owner == item.phase && id == item.node)
            return i;
    std::abort();
}

std::size_t PathIndex(const NativeRestorePath& path)
{
    const auto words = std::span(path.words, path.size);
    const auto found = std::ranges::find_if(FalcoPhases, [&](const auto& phase) { return std::ranges::equal(words, phase.address); });
    if (found == FalcoPhases.end() || path.size > path.capacity)
        std::abort();
    return static_cast<std::size_t>(found - FalcoPhases.begin());
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
            if (FalcoPhases[i].depot && (!f->counts[i] || Read<std::uint8_t>(f->definitions[i].data(), 0x58) != 1))
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
            if (phase == FalcoAfterWait.phase && id != f->ExpectedNode(FalcoRestoreNodes.size() - 1).node)
                return nullptr;
            const auto i = HandlerIndex(phase, static_cast<std::uint16_t>(id));
            return f->slots[i] != UINT32_MAX ? f->handlers[i].data() : nullptr;
        },
        [](void* owner, std::uint32_t index, void* ctx, bool dispatch) {
            if (Read<std::uint8_t>(ctx, 0) != 1 || dispatch) std::abort();
            const auto parent = Index(owner);
            const auto child = Index(f->children[parent][index].object);
            if (Read<std::uint32_t>(f->phases[child].data(), 0x94)) std::abort();
            for (std::size_t i = 0; i < FalcoRestoreNodes.size(); ++i)
            {
                const auto& target = f->ExpectedNode(i);
                if (target.phase == child || (target.phase == parent && target.node == FalcoPhases[child].address.back()))
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
    for (std::size_t i = 0; i < FalcoRestoreNodes.size(); ++i)
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
        auto* quests = native.quests.data();
        auto* phase = native.phases[8].data();
        auto* pending = native.handlers[8].data();
        Check(restore.Prepare(Native(), quests, native.Plan()) &&
                  !restore.SelectElapsedWait(quests, phase, pending, 8),
              "the original running timer does not qualify as an elapsed wait");
        native.EraseHandler(8);
        native.elapsedWait = true;
        native.Install(8, 10);
        const auto correct = native.rows[10];
        native.rows[10].type = FalcoRestoreNodes.back().type;
        Check(!restore.SelectElapsedWait(quests, phase, pending, 10),
              "the post-wait path rejects a successor of the wrong condition type");
        native.rows[10] = correct;
        Check(!restore.SelectElapsedWait(quests, phase, pending, 8) &&
                  restore.SelectElapsedWait(quests, phase, pending, 10) && !restore.CreatePhases(quests),
              "the verified native successor on its live slot still requires stock cleanup");
        native.Retire(2);
        Check(restore.CreatePhases(quests) && CreateHandlers(restore, native) && native.rows[20].node == 2 &&
                  std::ranges::none_of(native.rows, [](const Registration& row) {
                      return row.phase == PhaseHash(FalcoMessages) && row.node == FalcoRestoreNodes.back().node;
                  }) && restore.Commit(),
              "the native restore creates the follow-up condition without resetting the completed wait");
    }
    {
        Fixture native;
        const auto initial = native.counts;
        RetainedQuestRestore restore;
        Check(restore.Prepare(Native(), native.quests.data(), native.Plan()) && native.counts[1] == 2 && native.counts[8] == 2,
              "resident preparation takes one exact native cache hold per external child");
        Check(std::ranges::all_of(native.references, [](int count) { return !count; }), "cache lookup balances transient strong references");
        Check(!restore.CreatePhases(native.quests.data()), "an original body that is still live defers mutation");
        Check(restore.Rollback(native.quests.data()) && native.counts == initial && native.phasePresent[8],
              "abort before cleanup releases only our pins and leaves the entire original graph active");
    }
    {
        Fixture native;
        const auto initial = native.counts;
        native.failHold = 4;
        RetainedQuestRestore restore;
        Check(!restore.Prepare(Native(), native.quests.data(), native.Plan()) && native.counts == initial && native.phasePresent[8],
              "a failed cache hit leaves every resident owner and count unchanged");
    }
    {
        Fixture native;
        RetainedQuestRestore restore;
        const auto setup = restore.Prepare(Native(), native.quests.data(), native.Plan());
        native.Retire(1);
        Check(setup && native.counts[6] == 1 && native.counts[8] == 1,
              "native retirement leaves the pending transaction's resident pins intact");
        Check(restore.CreatePhases(native.quests.data()) && native.phasesCreated == 8 && !native.handlersCreated &&
                  restore.Phase(native.quests.data(), 6) == native.phases[6].data(),
              "mode 2 creates only the requested branches before any selected handler");
        Check(!restore.CreateHandler(native.quests.data(), 8) && !native.handlersCreated, "out of sequence initialization defers");
        Check(CreateHandlers(restore, native) && native.handlersCreated == 9 && native.rows[20].node == 28,
              "only the nine original rows return with verified native replacement slots");
        native.pending = {20, 90, 12, 97};
        Put(native.quests, 0x164, 4U);
        Check(restore.Rollback(native.quests.data()) && native.phasesStopped == 8 && native.counts[6] == 0 && !native.phasePresent[8],
              "rollback stops only its created subtree and native release consumes each adopted pin");
        Check(Read<std::uint32_t>(native.quests.data(), 0x164) == 2 && native.pending[0] == 90 && native.pending[1] == 97,
              "rollback purges only its reclaimed notification slots in native order");
        Check(native.contextOpened == native.contextClosed, "all native contexts are released");
    }
    {
        Fixture native;
        RetainedQuestRestore restore;
        const auto setup = restore.Prepare(Native(), native.quests.data(), native.Plan());
        native.Retire(2);
        native.failChild = 7;
        Check(setup && !restore.CreatePhases(native.quests.data()) && restore.Rollback(native.quests.data()) &&
                  native.phasePresent[1] && native.counts[1] == 1 && !native.phasePresent[6] && !native.counts[7] &&
                  !Read<std::uint8_t>(native.definitions[7].data(), 0x58),
              "a later child creation failure unbinds its prepared definition and unwinds only new children");
    }
    {
        Fixture native;
        RetainedQuestRestore restore;
        const auto setup = restore.Prepare(Native(), native.quests.data(), native.Plan());
        native.Retire(2);
        Check(setup && restore.CreatePhases(native.quests.data()) && CreateHandlers(restore, native) && restore.Commit() &&
                  native.phasePresent[1] && native.phasePresent[8] && native.counts[1] == 1 && native.counts[8] == 1,
              "commit releases the extra hold for a retained ancestor and transfers the fresh body holds");
    }
    {
        Fixture native;
        RetainedQuestRestore restore;
        const auto setup = restore.Prepare(Native(), native.quests.data(), native.Plan());
        native.Retire(2);
        const auto restored = setup && restore.CreatePhases(native.quests.data()) && CreateHandlers(restore, native);
        auto replacement = native.phases[6];
        auto& child = native.children[5][0];
        const auto live = child.object;
        child.object = replacement.data();
        const auto rejectsDifferentOwner = restored && !restore.Phase(native.quests.data(), 6) && !restore.Commit();
        child.object = live;
        const auto slot = native.slots[8];
        const auto row = native.rows[slot];
        native.rows[slot] = {};
        const auto rejectsChangedRow = rejectsDifferentOwner && !restore.Commit();
        native.rows[slot] = row;
        Check(rejectsChangedRow && restore.Commit(), "commit verifies the exact phase owners and live handler rows");
    }
    {
        Fixture native;
        RetainedQuestRestore restore;
        const auto setup = restore.Prepare(Native(), native.quests.data(), native.Plan());
        native.Retire(2);
        Check(setup && restore.CreatePhases(native.quests.data()) && restore.ReleaseUnadopted(native.quests.data()) &&
                  restore.ReleaseUnadopted(native.quests.data()) && native.counts[1] == 1 && native.counts[8] == 1 &&
                  native.phasePresent[8] && restore.Rollback(native.quests.data()) && !native.counts[8],
              "transition release consumes its transient holds once and leaves adopted children to their native lifetime");
    }
    {
        Fixture native;
        RetainedQuestRestore restore;
        const auto setup = restore.Prepare(Native(), native.quests.data(), native.Plan());
        native.Retire(2);
        Check(setup && restore.CreatePhases(native.quests.data()) && CreateHandlers(restore, native) &&
                  restore.Rollback(native.quests.data()) && native.phasePresent[1] && native.handlersRemoved == 1,
              "rollback explicitly removes a replacement on a retained ancestor without stopping the ancestor");
    }
    return failed != 0;
}
