#include "NativeCheckpoint.cpp"

#include <iostream>
#include <unordered_map>

namespace
{
template<std::size_t Size>
struct Bytes
{
    alignas(16) std::array<std::byte, Size> bytes{};
    void* Data() { return bytes.data(); }
};

template<class T>
void Put(void* object, std::size_t offset, T value)
{
    std::memcpy(static_cast<std::byte*>(object) + offset, &value, sizeof(value));
}

template<class T, std::size_t Count>
void SetArray(void* object, std::size_t offset, const std::array<T, Count>& array, std::size_t count = Count)
{
    Put(object, offset, array.data());
    Put(object, offset + 8, static_cast<std::uint32_t>(Count));
    Put(object, offset + 12, static_cast<std::uint32_t>(count));
}

// This harness calls the production reader with bounded synthetic objects.
// Native ABI dependencies use bounded stubs. No game code is loaded.
class Stubs
{
public:
    Stubs()
    {
        image = static_cast<const std::uint8_t*>(VirtualAlloc(nullptr, 0x4000000, MEM_RESERVE, PAGE_NOACCESS));
        if (!image)
            throw std::runtime_error("test address range");
        Add(0x2B2270, &Fact);
        Add(0x2B1B64, &Find);
        Add(0x2B224C, &FindPhase);
        Add(0x1B92E4, &Noop);
        Add(0x9BFC0C, &Noop);
        Add(0x111894C, &Remaining);
        Add(0x468358, &ReadClock);
        const auto executeSlot = Memory(0x30E5E68 + 0xE8);
        Put(executeSlot, 0, image + SetVarBody);
    }

    ~Stubs() { VirtualFree(const_cast<std::uint8_t*>(image), 0, MEM_RELEASE); }

    static inline std::unordered_map<std::uint32_t, std::int32_t> named;
    static inline std::uint32_t now = 3;
    static inline float remaining = 8.94622517f;
    static inline std::array<const void*, 3> owners{};
    static inline std::array<const void*, 2> phases{};
    static inline const void* currentPhase{};

private:
    static std::uint8_t* Memory(std::uintptr_t rva)
    {
        auto* page = const_cast<std::uint8_t*>(image + (rva & ~0xFFFULL));
        if (!VirtualAlloc(page, 0x1000, MEM_COMMIT, PAGE_EXECUTE_READWRITE))
            throw std::runtime_error("test trampoline");
        return const_cast<std::uint8_t*>(image + rva);
    }

    template<class Method>
    static void Add(std::uintptr_t rva, Method method)
    {
        auto* location = Memory(rva);
        const auto target = reinterpret_cast<std::uint64_t>(method);
        std::uint8_t code[]{0x48, 0xB8, 0, 0, 0, 0, 0, 0, 0, 0, 0xFF, 0xE0};
        std::memcpy(code + 2, &target, sizeof(target));
        std::memcpy(location, code, sizeof(code));
        FlushInstructionCache(GetCurrentProcess(), location, sizeof(code));
    }

    static std::int32_t Fact(const void*, std::uint32_t, std::uint32_t key)
    {
        const auto pos = named.find(key);
        return pos == named.end() ? 0 : pos->second;
    }

    static const void* Find(const void* phase, std::uint32_t node)
    {
        if (phase == phases[0] && node == 1000) return owners[0];
        if (phase == phases[1] && node == 2000) return owners[1];
        if (phase == phases[0] && node == 1001) return owners[2];
        return nullptr;
    }

    static void Noop(void*) {}
    static const void* FindPhase(const void*) { return currentPhase; }
    static float Remaining(void*, std::uint64_t id) { return id == RealId ? remaining : 0; }
    static void* ReadClock(void*, std::uint32_t* time) { *time = now; return time; }

public:
    static constexpr std::uint64_t RealId = 0x0000000400000066;
};

struct Fixture
{
    Fixture()
    {
        Put(quests.Data(), 0, image + QuestSystem);
        Put(quests.Data(), 0x68, root.Data());
        Put(quests.Data(), 0xF8, facts.Data());
        Put(quests.Data(), 0xE8, registry.Data());
        Put(quests.Data(), 0xF0, nodeData.Data());
        SetArray(quests.Data(), 0xA8, depots);
        Put(root.Data(), 0, image + SyntheticRoot);
        rootChildren = {{{basePhases[0].Data(), nullptr}, {expansion.Data(), nullptr}}};
        SetArray(root.Data(), 0x88, rootChildren);
        MakePhase(expansion.Data(), expansionPath, 1, ExpansionQuest);
        const auto epistrophyDepot = Depot(R"(base\quest\side_quests\sq025\phases\sq025_04_scan.questphase)");
        for (std::size_t i = 0; i < basePhases.size(); ++i)
        {
            MakePhase(basePhases[i].Data(), epistrophy, i + 1, i + 1 == epistrophy.size() ? epistrophyDepot : 0);
            if (i + 1 < basePhases.size())
            {
                childRows[i][0] = {basePhases[i + 1].Data(), nullptr};
                SetArray(basePhases[i].Data(), 0x88, childRows[i]);
            }
        }
        Stubs::phases = {basePhases[0].Data(), expansion.Data()};
        Stubs::owners = {real.Data(), game.Data(), other.Data()};
        const auto mockType = Depot("questPauseConditionNodeDefinition");
        slots[0] = {mockType, PhaseHash(std::span{epistrophy}.first(1)), 1000};
        slots[1] = {mockType, PhaseHash(expansionPath), 2000};
        slots[2] = {mockType, slots[0].phase, 1001};
        slots[3] = {mockType, 0x12345678, 1002};
        slots[4] = {0, 0, 0xFFFF};
        SetArray(registry.Data(), 8, slots);
        MakeWait(real.Data(), RealTimeHandler, 0, Stubs::RealId);
        MakeWait(game.Data(), GameTimeHandler, 1, GameId);
        MakeWait(other.Data(), RealTimeHandler, 2, Stubs::RealId + 1);
        nodeRows[0] = {Read<std::uint64_t>(real.Data(), 0x38), ptfr::SchedulerId::FromNative(Stubs::RealId).NodeInstanceValue()};
        nodeRows[1] = {Read<std::uint64_t>(game.Data(), 0x38), GameId};
        SetArray(nodeData.Data(), 8, nodeRows);
        Put(basePhases[0].Data(), 0xA0, std::uint32_t{2});
        Put(expansion.Data(), 0xA0, std::uint32_t{1});
        SetArray(quests.Data(), 0x158, notifications, 1);
        pendingResource[0] = {resource.Data(), nullptr};
        Put(resource.Data(), 0x30, epistrophyDepot);
        SetArray(quests.Data(), 0x130, pendingResource);
        Put(facts.Data(), 0, image + FactsManager);
        Put(facts.Data(), 0x58, std::uint32_t{10});
        for (std::size_t i = 0; i < tables.size(); ++i)
            Put(facts.Data(), 8 * (i + 3), tables[i].Data());
        SetArray(tables[1].Data(), 8, andKey);
        SetArray(tables[1].Data(), 0x18, andMask);
        Put(delay.Data(), 0, image + DelaySystem);
        Put(timeSystem.data(), 0, image + TimeSystem);
        Put(timeSystem.data(), ptfr::GameTimerList + ptfr::GameTimerCount, std::uint32_t{1});
        Put(timeSystem.data(), ptfr::GameTimerList + 0x10, ptfr::NativeGameTimerReference{gameRecord.Data(), &strongCount});
        Put(gameRecord.Data(), 0, image + GameTimerRecord);
        Put(gameRecord.Data(), 0x40, std::uint32_t{10});
        Put(gameRecord.Data(), 0x44, std::uint32_t{1});
        Put(gameRecord.Data(), 0x80, gameCallback.Data());
        Put(gameRecord.Data(), 0x88, GameId);
        Put(gameRecord.Data(), 0x90, std::uint32_t{20});
        Put(gameCallback.Data(), 0, image + NewGameTimerCallback);
        Put(gameCallback.Data(), 8, game.Data());
        realTickOriginal = [](void*, float, const void*) {};
        gameTickOriginal = [](void*, float, const void*) {};
        enabled.store(true);
        SetGate(1, 11);
    }

    template<std::size_t Words>
    void MakePhase(void* phase, const std::array<std::uint16_t, Words>& path, std::size_t size,
                   std::uint64_t depot)
    {
        Put(phase, 0, image + PhaseInstance);
        Put(phase, 0x80, PhaseHash(std::span{path}.first(size)));
        SetArray(phase, 0x70, path, size);
        if (depot)
        {
            auto& source = depot == ExpansionQuest ? expansionRes : scanRes;
            Put(source.Data(), 0x30, depot);
            Put(phase, 0x30, source.Data());
        }
    }

    void MakeWait(void* owner, std::uintptr_t type, std::uint32_t slot, std::uint64_t id)
    {
        Put(owner, 0, image + type);
        Put(owner, 0x28, slot);
        Put(owner, 0x38, (static_cast<std::uint64_t>(slots[slot].phase) << 32) | slots[slot].node);
        Put(owner, 0x40, id);
    }

    void SetGate(std::int32_t route, std::int32_t ticket)
    {
        ClearGate();
        Stubs::named.clear();
        SetFact("PTFRHS3_GateOpen", 1);
        SetFact("PTFRHS3_GateRoute", route);
        SetFact("PTFRHS3_GateTicket", ticket);
        SetFact("q307_point_of_no_return", route == 1 ? 1 : 0);
        gate.Open({quests.Data(), facts.Data(), ticket, route});
    }

    static void SetFact(std::string_view name, int value) { Stubs::named[FactId(name)] = value; }

    bool CopyState(Capture& capture, int ticket = 11, int route = 1)
    {
        return Copy(capture, quests.Data(), delay.Data(), timeSystem.data(), ticket, route, true);
    }

    void Sample(int ticket = 11, int route = 1)
    {
        Capture prime(false);
        Copy(prime, quests.Data(), delay.Data(), timeSystem.data(), ticket, route, false);
        RealTick(delay.Data(), 0.01f, nullptr);
        GameTick(timeSystem.data(), 0.01f, nullptr);
    }

    static constexpr std::uint32_t GameId = 51;
    Bytes<0x400> quests;
    Bytes<0x110> root, expansion;
    std::array<Bytes<0x110>, 6> basePhases;
    Bytes<0x28> registry, nodeData;
    Bytes<0x60> facts;
    Bytes<0x68> real, game, other;
    Bytes<0xA0> gameRecord;
    Bytes<0x28> gameCallback;
    Bytes<0x40> delay, expansionRes, scanRes, resource;
    std::vector<std::byte> timeSystem = std::vector<std::byte>(0x70000);
    std::array<Bytes<0x28>, 3> tables;
    std::array<HandleRow, 2> rootChildren{};
    std::array<std::array<HandleRow, 1>, 5> childRows{};
    std::array<HandleRow, 1> pendingResource{};
    const std::array<std::uint16_t, 6> epistrophy{0, 2, 82, 5, 48, 79};
    const std::array<std::uint16_t, 1> expansionPath{1};
    std::array<std::uint64_t, 2> depots{BaseQuest, ExpansionQuest};
    std::array<Registration, 5> slots{};
    std::array<NodeInstance, 2> nodeRows{};
    std::array<std::uint32_t, 2> notifications{2, 0};
    const std::array<std::uint32_t, 1> andKey{3673229151U};
    const std::array<std::int32_t, 1> andMask{70};
    long strongCount = 1;
};

class Checks
{
public:
    void Expect(bool condition, const char* description)
    {
        std::cout << (condition ? "PASS " : "FAIL ") << description << '\n';
        if (!condition)
            ++failures;
    }
    unsigned failures{};
};
} // namespace

int main()
{
    const Stubs stubs;
    Fixture state;
    Checks check;
    constexpr std::array<std::uint16_t, 4> reed{1, 0, 19, 10};
    constexpr std::array<std::uint16_t, 5> hanako{0, 2, 77, 3, 113};
    constexpr auto pickup = Depot(R"(ep1\quest\main_quests\q307\phases\q307_01_pickup.questphase)");
    constexpr auto parade = Depot(R"(base\quest\main_quests\part1\q115\phases\q115_00_hanako.questphase)");
    check.Expect(GateRoute(pickup, reed) == 1 && GateRoute(parade, hanako) == 2, "both source gates");
    check.Expect(GateRoute(pickup, hanako) == 0 && GateRoute(pickup ^ 1, reed) == 0, "wrong depot or ancestry");
    {
        Bytes<0x230> phaseContext;
        Bytes<0x40> questContext, depot;
        Bytes<0x110> phase;
        Bytes<0x58> definition, operation;
        Put(phaseContext.Data(), 0, image + PhaseContext);
        Put(phaseContext.Data(), 0x18, state.quests.Data());
        Put(phaseContext.Data(), 0x28, state.facts.Data());
        Put(phaseContext.Data(), 0x220, questContext.Data());
        Put(phase.Data(), 0, image + PhaseInstance);
        Put(phase.Data(), 0x30, depot.Data());
        SetArray(phase.Data(), 0x70, reed);
        Put(depot.Data(), 0x30, pickup);
        Stubs::currentPhase = phase.Data();
        Put(definition.Data(), 0x48, operation.Data());
        Put(operation.Data(), 0, image + 0x30E5E68);
        Put(operation.Data(), 0x30, std::to_array("PTFRHS3_GateOpen"));
        Put(operation.Data(), 0x44, std::uint32_t{16});
        Put(operation.Data(), 0x50, std::int32_t{1});
        Put(operation.Data(), 0x54, true);
        factsNodeOriginal = [](const void* node, const void*, const void*, void*) -> std::uint8_t {
            Fixture::SetFact("PTFRHS3_GateOpen", Read<std::int32_t>(Read<const void*>(node, 0x48), 0x50));
            return 0xAF;
        };
        const Boundary boundary{state.quests.Data(), state.facts.Data(), 11, 1};
        ClearGate();
        Put(definition.Data(), 0x40, std::uint16_t{60004});
        check.Expect(ExecuteFactsNode(definition.Data(), phaseContext.Data(), nullptr, nullptr) == 0xAF &&
                     !gate.Matches(boundary), "native writer at wrong node cannot arm checkpoint");
        Put(definition.Data(), 0x40, OpenGateNode);
        check.Expect(ExecuteFactsNode(definition.Data(), phaseContext.Data(), nullptr, nullptr) == 0xAF &&
                     gate.Matches(boundary), "native opening arms current route and ticket");
        Put(definition.Data(), 0x40, CloseGateNode);
        Put(operation.Data(), 0x50, std::int32_t{0});
        check.Expect(ExecuteFactsNode(definition.Data(), phaseContext.Data(), nullptr, nullptr) == 0xAF &&
                     !gate.Matches(boundary), "native closing retires observation");
    }
    state.SetGate(1, 11);
    Capture sample(true);
    state.Sample();
    check.Expect(state.CopyState(sample), "read matching Reed gate");
    check.Expect(sample.state.roots == std::vector{BaseQuest, ExpansionQuest}, "native resource indices");
    check.Expect(sample.state.phases.size() == 7 && sample.state.handlers.size() == 4, "registered graph and physical slots");
    check.Expect(sample.state.handlers[0].binding == Binding::Live &&
                 sample.state.handlers[3].binding == Binding::Unresolved, "active and unresolved registrations remain distinct");
    check.Expect(sample.state.facts[1].size() == 1 && sample.state.facts[1][0].key == state.andKey[0] &&
                 sample.state.facts[1][0].value == 70, "pinned Epistrophy partial inputs");
    check.Expect(sample.state.notifications == std::vector<std::uint32_t>{2} &&
                 sample.state.resourceRequests.size() == 1, "pending native queues");
    check.Expect(sample.state.instances.size() == 2 && sample.state.instances[0].key == state.nodeRows[0].key &&
                 sample.state.instances[0].value == state.nodeRows[0].value, "native save node instance pair read intact");
    check.Expect(sample.state.waitsObserved == 3 && sample.state.timings.size() == 2, "concurrent clock samples, absent timer stays unknown");
    check.Expect(sample.state.timings.size() == 2 && sample.state.timings[0].clock == Clock::Real &&
                 sample.state.timings[0].remainingSeconds == static_cast<double>(Stubs::remaining) &&
                 sample.state.timings[1].clock == Clock::Game && sample.state.timings[1].remainingSeconds == 7,
                 "both durations copied with original slots");
    constexpr auto id = "7afcbb7b241f41086736680671f8adc7";
    std::array<std::uint64_t, 15> presentation{0x3456, 3, 1, 1, 0, 1, 1, 1, 1, 0xAD123456, 2, 1, 19, 0, 3};
    sample.state.presentation = ReadPresentation(presentation);
    check.Expect(sample.state.presentation && sample.state.presentation->inScene && sample.state.presentation->phoneActive &&
                 sample.state.presentation->phase == 2 && sample.state.presentation->talkingState == 2,
                 "player and phone observations remain separate from native graph state");
    presentation[10] = 99;
    check.Expect(!ReadPresentation(presentation), "unsupported observation shape stays unknown");
    const auto json = Encode(sample.state, id, 11, 1, 5);
    check.Expect(!json.empty() && json.find("histor") != std::string::npos, "serializable checkpoint");
    std::vector<std::uint64_t> packed(PackedWords(std::strlen(id) + json.size()));
    check.Expect(Pack(id, json, packed) && Unpack(packed) == id + json, "persistent words round-trip exact bytes");
    check.Expect(Unpack(std::span{packed}.first(packed.size() - 1)).empty(), "truncated checkpoint refused");
    packed[0] = MaxBytes + 33;
    check.Expect(Unpack(packed).empty(), "oversize checkpoint refused");
    check.Expect(Encode(sample.state, "foreign/123", 11, 1, 5).empty(), "unsafe export identity rejected");
    check.Expect(Encode(sample.state, id, 11, 1, 0).empty(), "missing original history revision rejected");
    check.Expect(!state.CopyState(sample, 12) && !state.CopyState(sample, 11, 2), "wrong ticket and route blocked");
    check.Expect(std::string_view(captureReject) == "boundary_gate_mismatch", "wrong route reports gate mismatch");
    {
        const std::lock_guard lock(LockAt(state.quests.Data(), 0x60));
        check.Expect(!state.CopyState(sample), "graph contention defers without waiting");
        check.Expect(std::string_view(captureReject) == "graph_lock", "graph contention has a distinct diagnostic");
    }
    {
        const std::lock_guard lock(LockAt(state.quests.Data(), 0x150));
        Capture busy(true);
        check.Expect(!state.CopyState(busy), "queue contention defers without waiting");
        check.Expect(std::string_view(captureReject) == "queue_notification_lock", "queue contention identifies its lock");
    }
    check.Expect(LockAt(state.quests.Data(), 0x60).TryLock(), "early return released graph lock");
    LockAt(state.quests.Data(), 0x60).Unlock();
    ++notificationPasses;
    check.Expect(!state.CopyState(sample), "notification copy in flight defers");
    --notificationPasses;
    Fixture::SetFact("q307_ep1_killed", 1);
    check.Expect(!state.CopyState(sample), "native destructive update closes capture");
    check.Expect(std::string_view(captureReject) == "facts_cleanup_started", "cleanup rejection names its stage");
    Fixture::SetFact("q307_ep1_killed", 0);
    Fixture::SetFact("PTFRHS3_GateResult", 1);
    check.Expect(!state.CopyState(sample), "native acknowledgement closes capture");
    Fixture::SetFact("PTFRHS3_GateResult", 0);
    state.nodeRows[0].value ^= 1;
    Capture wrongInstance(true);
    check.Expect(state.CopyState(wrongInstance) && wrongInstance.state.timings.size() == 1 &&
                 wrongInstance.state.timings[0].clock == Clock::Game, "duration requires matching saved node instance ID");
    state.nodeRows[0].value ^= 1;
    state.depots[1] ^= 1;
    check.Expect(!state.CopyState(sample), "unknown root ordering defers");
    check.Expect(std::string_view(captureReject) == "phase_roots", "root rejection names its stage");
    state.depots[1] ^= 1;
    Put(state.quests.Data(), 0x164, std::uint32_t{2});
    Capture queued(true);
    check.Expect(state.CopyState(queued) && queued.state.timings.size() == 1 &&
                 queued.state.timings[0].clock == Clock::Game, "already queued handler has no sampled wait");
    Put(state.quests.Data(), 0x164, std::uint32_t{1});
    timerRequest.samples[0].time -= std::chrono::seconds(1);
    Capture stale(true);
    check.Expect(state.CopyState(stale) && stale.state.timings.size() == 1 &&
                 stale.state.timings[0].clock == Clock::Game, "stale duration cannot qualify");
    state.Sample();
    Put(state.gameCallback.Data(), 8, state.real.Data());
    state.Sample();
    Capture foreign(true);
    check.Expect(state.CopyState(foreign) && foreign.state.timings.size() == 1 &&
                 foreign.state.timings[0].clock == Clock::Real, "game clock callback bound to original owner");
    Put(state.gameCallback.Data(), 8, state.game.Data());
    Stubs::remaining = 0.005f;
    state.Sample();
    Capture due(true);
    check.Expect(state.CopyState(due) && due.state.timings.size() == 1 && due.state.timings[0].clock == Clock::Game,
                 "real timer due this tick stays unknown");
    Stubs::remaining = 8.94622517f;
    {
        const Transition outer;
        {
            const Transition inner;
            check.Expect(!state.CopyState(sample), "nested root load blocks snapshot");
        }
        check.Expect(!state.CopyState(sample), "outer load blocks snapshot after inner return");
    }
    check.Expect(!StillOpen(state.quests.Data(), 11, 1, sample.epoch), "earlier epoch invalid after load");
    check.Expect(!state.CopyState(sample), "old gate cannot survive root replacement");
    state.SetGate(2, 11);
    Capture second(true);
    check.Expect(state.CopyState(second, 11, 2) && second.state.timings.empty(), "Hanako is captured without earlier session's waits");
    Fixture::SetFact("q115_point_of_no_return", 1);
    check.Expect(!state.CopyState(sample, 11, 2), "Hanako already at point of no return defers");
    if (check.failures)
        return 1;
    std::cout << "PAYLOAD " << json << '\n';
    return 0;
}
