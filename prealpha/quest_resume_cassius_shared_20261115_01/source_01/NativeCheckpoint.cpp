#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>
#include <bcrypt.h>

#include <RED4ext/RED4ext.hpp>
#include <RED4ext/SharedSpinLock.hpp>
#include <RED4ext/Scripting/Natives/Generated/game/DelaySystem.hpp>
#include <RED4ext/Scripting/Natives/Generated/game/TimeSystem.hpp>
#include <RED4ext/Scripting/Natives/Generated/quest/QuestsSystem.hpp>
#include <RED4ext/Scripting/Natives/Generated/quest/SetVar_NodeType.hpp>

#include "../../universal_resume_checkpoint_probe_20261114_01/source_02/Checkpoint.hpp"
#include "../../universal_resume_save_admission_20261115_01/SaveAdmission.hpp"
#include "../../universal_resume_checkpoint_probe_20261114_01/CheckpointRegistration.hpp"
#include "RetainedQuestRestore.hpp"
#include "../../universal_resume_boundary_20261114_01/TimerRecord.hpp"
#include "../../universal_resume_eagles_20261114_01/GameTimeWait.hpp"

#include <atomic>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <mutex>
#include <optional>

namespace
{
using namespace ptfr::resume;
using Monotonic = std::chrono::steady_clock;
constexpr auto QuestSystem = 0x30BCE78;
constexpr auto FactsManager = 0x306FA58;
constexpr auto PhaseInstance = 0x308A948;
constexpr auto SyntheticRoot = 0x3699F88;
constexpr auto PhaseContext = 0x3040630;
constexpr auto SetVarBody = 0x9DDCB0;
constexpr auto RealTimeHandler = 0x31267A0;
constexpr auto GameTimeHandler = 0x31C2388;
constexpr auto DelaySystem = 0x30A2A90;
constexpr auto TimeSystem = 0x30BD228;
constexpr auto GameTimerRecord = 0x30A75A8;
constexpr auto NewGameTimerCallback = 0x36A1D50;
constexpr auto LoadedGameTimerCallback = 0x36A1D20;

const std::uint8_t* image{};
const RED4ext::v1::Sdk* sdk{};
RED4ext::v1::PluginHandle plugin{};
RED4ext::CGlobalFunction* reader{};
RED4ext::CGlobalFunction* decoder{};
std::atomic<bool> enabled{};
std::atomic<bool> hooksReady{};
std::atomic<bool> saveAdmissionProbeRequested{};
std::mutex boundaryMutex;
Gate gate;
// Under boundaryMutex. Compare this address against the locked phase tree
// before reading the writer's ancestors. Never dereference the stored address.
const void* gateWriter{};
std::size_t notificationPasses{};
thread_local const char* captureReject = "not_started";
std::atomic<const char*> gateOpenStatus{"unseen"};

bool Reject(const char* reason)
{
    captureReject = reason;
    return false;
}

template<class T>
T Read(const void* object, std::size_t offset) noexcept
{
    T value{};
    std::memcpy(&value, static_cast<const std::byte*>(object) + offset, sizeof(value));
    return value;
}

template<class Method>
Method At(std::uintptr_t rva)
{
    return reinterpret_cast<Method>(image + rva);
}

bool Is(const void* object, std::uintptr_t type)
{
    return object && Read<const void*>(object, 0) == image + type;
}

auto& LockAt(void* object, std::size_t offset)
{
    return *reinterpret_cast<RED4ext::SharedSpinLock*>(static_cast<std::byte*>(object) + offset);
}

template<class T>
std::optional<std::span<const T>> ArrayAt(const void* object, std::size_t offset, std::size_t limit)
{
    const auto data = Read<const T*>(object, offset);
    const auto capacity = Read<std::uint32_t>(object, offset + 8);
    const auto size = Read<std::uint32_t>(object, offset + 12);
    if (size > capacity || size > limit || (size != 0 && !data))
        return std::nullopt;
    return std::span<const T>{data, size};
}

int FactValue(const void* facts, std::string_view name)
{
    return At<std::int32_t (*)(const void*, std::uint32_t, std::uint32_t)>(0x2B2270)(facts, 1, FactId(name));
}

bool BeforeCleanup(const void* facts)
{
    constexpr std::array closed{
        "q307_debug_reset", "q307_2079", "q307_main_game_killed", "q307_ep1_killed", "q307_done", "q307_finished"
    };
    if (!std::all_of(closed.begin(), closed.end(), [&](const auto name) { return FactValue(facts, name) == 0; }))
        return Reject("facts_cleanup_started");
    return true;
}

bool OpenFacts(Boundary b)
{
    if (b.ticket <= 0 || !Is(b.facts, FactsManager) || (b.route != 1 && b.route != 2))
        return Reject("facts_boundary");
    const auto value = [&](std::string_view name) { return FactValue(b.facts, name); };
    if (value("PTFRHS3_GateOpen") != 1 || value("PTFRHS3_GateTicket") != b.ticket ||
        value("PTFRHS3_GateRoute") != b.route || value("PTFRHS3_GateResult") != 0 ||
        value("q115_point_of_no_return") != 0 ||
        (b.route == 1 ? value("q307_point_of_no_return") <= 0 : value("q307_point_of_no_return") != 0))
        return Reject("facts_gate_values");
    return BeforeCleanup(b.facts);
}

bool ProbeFacts(const void* facts)
{
    if (!Is(facts, FactsManager))
        return Reject("facts_boundary");
    if (FactValue(facts, "PTFRHS3_GateOpen") != 0 || FactValue(facts, "q307_point_of_no_return") != 0 ||
        FactValue(facts, "q115_point_of_no_return") != 0)
        return Reject("probe_requires_pre_ending_save");
    return BeforeCleanup(facts);
}

std::uint64_t PhaseDepot(const void* phase)
{
    const auto resource = Read<const void*>(phase, 0x30);
    return resource ? Read<std::uint64_t>(resource, 0x30) : 0;
}

struct ClockSample
{
    double remaining{};
    Monotonic::time_point time{};
};

struct TimerRequest
{
    Boundary boundary;
    const void* delay{};
    const void* timeSystem{};
    std::uint64_t gateEpoch{};
    Monotonic::time_point refreshed{};
    std::array<Wait, MaxTimers> waits{};
    std::array<ClockSample, MaxTimers> samples{};
    std::size_t count{};
};
TimerRequest timerRequest;

void ClearGate()
{
    gate.Clear();
    gateWriter = nullptr;
    gateOpenStatus.store("cleared");
    timerRequest.count = 0;
    timerRequest.boundary = {};
}

// Root replacement and load can run outside the graph lock. The native call
// never holds our mutex. An attempted sample either owns the mutex before a
// transition can start or declines while the transition is in flight.
class Transition
{
public:
    Transition()
    {
        const std::lock_guard lock(boundaryMutex);
        gate.BeginTransition();
        saveAdmissionProbeRequested.store(false);
        gateWriter = nullptr;
        gateOpenStatus.store("transition");
        timerRequest.count = 0;
        timerRequest.boundary = {};
    }
    ~Transition()
    {
        const std::lock_guard lock(boundaryMutex);
        gate.EndTransition();
    }
};

void (*loadOriginal)(void*, void*, void*, void*);
void (*teardownOriginal)(void*, void*);
void (*rootOriginal)(void*);
void (*drainOriginal)(void*);
void (*restoreOriginal)(void*, void*);
void (*restoreHandlersOriginal)(void*);
std::uint8_t (*factsNodeOriginal)(const void*, const void*, const void*, void*);
void (*realTickOriginal)(void*, float, const void*);
void (*gameTickOriginal)(void*, float, const void*);

#include "NativeSaveAdmission.inc"

void Load(void* quests, void* context, void* status, void* stream)
{
    const Transition transition;
    loadOriginal(quests, context, status, stream);
}
void Teardown(void* quests, void* context)
{
    const Transition transition;
    teardownOriginal(quests, context);
}
void InitializeRoot(void* quests)
{
    const Transition transition;
    rootOriginal(quests);
}
void RestorePhases(void* request, void* job)
{
    const Transition transition;
    restoreOriginal(request, job);
}
void RestoreHandlers(void* quests)
{
    const Transition transition;
    restoreHandlersOriginal(quests);
}

void DrainNotifications(void* quests)
{
    {
        const std::lock_guard lock(boundaryMutex);
        ++notificationPasses;
    }
    drainOriginal(quests);
    {
        const std::lock_guard lock(boundaryMutex);
        --notificationPasses;
    }
}

std::uint8_t ExecuteFactsNode(const void* nodeDefinition, const void* context, const void* input, void* outputs)
{
    const auto original = [&] { return factsNodeOriginal(nodeDefinition, context, input, outputs); };
    const auto node = Read<std::uint16_t>(nodeDefinition, 0x40);
    if (!enabled.load() || (node != OpenGateNode && node != CloseGateNode) || !Is(context, PhaseContext))
        return original();
    const auto definition = Read<const RED4ext::quest::SetVar_NodeType*>(nodeDefinition, 0x48);
    if (!definition || Read<const void*>(Read<const void*>(definition, 0), 0xE8) != image + SetVarBody)
        return original();
    constexpr std::string_view gateName = "PTFRHS3_GateOpen";
    if (!definition->setExactValue || definition->factName.Length() != gateName.size() ||
        std::string_view(definition->factName.c_str(), gateName.size()) != gateName)
        return original();
    const auto questContext = Read<const void*>(context, 0x220);
    if (!questContext)
        return original();
    const auto quests = Read<const void*>(context, 0x18);
    const auto facts = Read<const void*>(context, 0x28);
    const auto phase = At<const void* (*)(const void*)>(0x2B224C)(questContext);
    auto route = 0;
    if (Is(phase, PhaseInstance) && !Read<const void*>(phase, 0x30))
    {
        if (const auto path = ArrayAt<std::uint16_t>(phase, 0x70, MaxDepth))
            route = InlineGateRoute(*path);
    }
    const bool opening = route != 0 && node == OpenGateNode && definition->value == 1;
    const bool closing = route != 0 && node == CloseGateNode && definition->value == 0;
    if (!opening && !closing)
        return original();
    std::uint64_t observedEpoch;
    {
        const std::lock_guard lock(boundaryMutex);
        ClearGate();
        observedEpoch = gate.Epoch();
    }
    const auto result = original();
    if (!opening)
        return result;
    const std::lock_guard lock(boundaryMutex);
    if (gate.Transitioning() || gate.Epoch() != observedEpoch || !Is(quests, QuestSystem) ||
        !Is(facts, FactsManager) || Read<const void*>(quests, 0xF8) != facts)
    {
        gateOpenStatus.store("post_write_context");
        return result;
    }
    const Boundary boundary{quests, facts, FactValue(facts, "PTFRHS3_GateTicket"), route};
    if (OpenFacts(boundary))
    {
        gate.Open(boundary);
        gateWriter = phase;
        gateOpenStatus.store("writer_observed");
    }
    else
        gateOpenStatus.store(captureReject);
    return result;
}

struct HandleRow
{
    const void* instance;
    const void* refCount;
};

struct LivePhase
{
    Phase record;
    const void* instance;
};

struct Capture
{
    Capture(bool final)
    {
        phases.reserve(MaxPhases);
        waits.reserve(MaxTimers);
        state.roots.reserve(64);
        if (final)
        {
            state.phases.reserve(MaxPhases);
            state.handlers.reserve(MaxSlots);
            state.notifications.reserve(MaxQueue);
            state.resourceRequests.reserve(MaxQueue);
            state.instances.reserve(MaxSlots);
            state.timings.reserve(MaxTimers);
            for (auto& table : state.facts)
                table.reserve(MaxFacts);
        }
    }
    State state;
    std::vector<LivePhase> phases;
    std::vector<Wait> waits;
    std::uint64_t epoch{};
};

bool Walk(Capture& capture, const void* instance, std::span<const std::uint16_t> ancestor, std::size_t rootCount)
{
    if (!Is(instance, PhaseInstance) || capture.phases.size() == MaxPhases)
        return Reject("phase_instance_or_limit");
    const auto path = ArrayAt<std::uint16_t>(instance, 0x70, MaxDepth);
    if (!path || path->size() != ancestor.size() + 1 || path->front() >= rootCount ||
        !std::equal(ancestor.begin(), ancestor.end(), path->begin()))
        return Reject("phase_path");
    const auto hash = Read<std::uint32_t>(instance, 0x80);
    if (hash != PhaseHash(*path))
        return Reject("phase_hash");
    Phase phase{};
    std::copy(path->begin(), path->end(), phase.path.begin());
    phase.size = path->size();
    phase.hash = hash;
    phase.depot = PhaseDepot(instance);
    phase.handlers = Read<std::uint32_t>(instance, 0xA0);
    capture.phases.push_back({phase, instance});
    const auto children = ArrayAt<HandleRow>(instance, 0x88, MaxPhases);
    if (!children)
        return Reject("phase_children");
    return std::all_of(children->begin(), children->end(), [&](HandleRow child) {
        return Walk(capture, child.instance, *path, rootCount);
    });
}

bool ReadPhases(Capture& capture, const void* quests)
{
    const auto roots = ArrayAt<std::uint64_t>(quests, 0xA8, 64);
    const auto root = Read<const void*>(quests, 0x68);
    if (!roots || roots->size() < 2 || (*roots)[0] != BaseQuest || (*roots)[1] != ExpansionQuest ||
        !Is(root, SyntheticRoot))
        return Reject("phase_roots");
    const auto children = ArrayAt<HandleRow>(root, 0x88, 64);
    if (!children || children->size() > roots->size())
        return Reject("phase_root_children");
    for (std::size_t i = 0; i < children->size(); ++i)
    {
        const auto child = (*children)[i].instance;
        if (!child)
            continue;
        if (!Walk(capture, child, {}, roots->size()))
            return false;
        const auto path = ArrayAt<std::uint16_t>(child, 0x70, MaxDepth);
        if ((*path)[0] != i)
            return Reject("phase_root_index");
    }
    capture.state.roots.assign(roots->begin(), roots->end());
    std::sort(capture.phases.begin(), capture.phases.end(), [](const LivePhase& a, const LivePhase& b) {
        return a.record.hash < b.record.hash;
    });
    return true;
}

bool VerifyGateWriter(const Capture& capture, int route)
{
    const auto& phases = capture.phases;
    const auto writer = std::ranges::find(phases, gateWriter, &LivePhase::instance);
    if (writer == phases.end() || InlineGateRoute(writer->record.Path()) != route)
        return Reject("boundary_writer_missing");

    const auto path = writer->record.Path();
    const auto ownerDepth = path.size() - (route == 1 ? 1 : 2);
    const auto expectedDepot = route == 1 ? ReedGateDepot : HanakoGateDepot;
    for (auto depth = ownerDepth; depth <= path.size(); ++depth)
    {
        const auto prefix = path.first(depth);
        const auto hash = PhaseHash(prefix);
        const auto phase = std::ranges::lower_bound(phases, hash, {}, [](const LivePhase& row) { return row.record.hash; });
        if (phase == phases.end() || phase->record.hash != hash || !std::ranges::equal(phase->record.Path(), prefix) ||
            (phase + 1 != phases.end() && (phase + 1)->record.hash == hash))
            return Reject("boundary_writer_ancestry");
        if (depth == ownerDepth ? phase->record.depot != expectedDepot : Read<const void*>(phase->instance, 0x30) != nullptr)
            return Reject("boundary_writer_provider");
    }
    return true;
}

bool Ready(const void* handler)
{
    auto word = reinterpret_cast<std::uint32_t*>(static_cast<std::byte*>(const_cast<void*>(handler)) + 0x2C);
    return std::atomic_ref(*word).load() != 0;
}

void ReadWait(Capture& capture, const void* owner, const Handler& row)
{
    const auto real = Is(owner, RealTimeHandler);
    if (!real && !Is(owner, GameTimeHandler))
        return;
    ++capture.state.waitsObserved;
    const auto key = (static_cast<std::uint64_t>(row.registration.phase) << 32) | row.registration.node;
    if (capture.waits.size() == MaxTimers || Read<std::uint64_t>(owner, 0x38) != key || Ready(owner))
        return;
    const auto timer = real ? Read<std::uint64_t>(owner, 0x40) : Read<std::uint32_t>(owner, 0x40);
    if (real ? ptfr::SchedulerId::FromNative(timer).IsQuestDelay() : timer != 0)
        capture.waits.push_back({owner, row.registration, row.slot, real ? Clock::Real : Clock::Game, timer});
}

bool ReadHandlers(Capture& capture, const void* quests, bool final)
{
    const auto manager = Read<const void*>(quests, 0xE8);
    if (!manager)
        return Reject("handlers_manager");
    const auto slots = ArrayAt<Registration>(manager, 8, MaxSlots);
    if (!slots)
        return Reject("handlers_slots");
    for (std::uint32_t i = 0; i < slots->size(); ++i)
    {
        const auto row = (*slots)[i];
        if (row.Empty())
            continue;
        Handler entry{row, i, Binding::Unresolved};
        if (row.Valid())
        {
            const auto first = std::lower_bound(capture.phases.begin(), capture.phases.end(), row.phase,
                [](const LivePhase& phase, std::uint32_t hash) { return phase.record.hash < hash; });
            if (first != capture.phases.end() && first->record.hash == row.phase)
            {
                if (first + 1 != capture.phases.end() && (first + 1)->record.hash == row.phase)
                    entry.binding = Binding::Ambiguous;
                else
                {
                    const auto owner = At<const void* (*)(const void*, std::uint32_t)>(0x2B1B64)(first->instance, row.node);
                    if (owner && Read<std::uint32_t>(owner, 0x28) == i)
                    {
                        entry.binding = Binding::Live;
                        ReadWait(capture, owner, entry);
                    }
                }
            }
        }
        if (final)
            capture.state.handlers.push_back(entry);
    }
    return true;
}

class FactsLock
{
public:
    explicit FactsLock(void* table) : table(table) { At<void (*)(void*)>(0x1B92E4)(table); }
    ~FactsLock() { At<void (*)(void*)>(0x9BFC0C)(table); }
    FactsLock(const FactsLock&) = delete;
    FactsLock& operator=(const FactsLock&) = delete;
private:
    void* table;
};

bool CopyGraphFacts(State& state, const void* facts)
{
    if (Read<std::uint32_t>(facts, 0x58) != 10)
        return Reject("graph_facts_table_count");
    for (std::size_t i = 0; i < state.facts.size(); ++i)
    {
        // 3 = disabled nodes, 4 = AND inputs, 5 = XOR latch.
        const auto table = Read<void*>(facts, 8 * (i + 3));
        if (!table)
            return Reject("graph_facts_table_missing");
        const FactsLock lock(table);
        const auto keys = ArrayAt<std::uint32_t>(table, 8, MaxFacts);
        const auto values = ArrayAt<std::int32_t>(table, 0x18, MaxFacts);
        if (!keys || !values || keys->size() != values->size())
            return Reject("graph_facts_rows");
        for (std::size_t j = 0; j < keys->size(); ++j)
            state.facts[i].push_back({(*keys)[j], (*values)[j]});
    }
    return true;
}

bool CopyQueues(State& state, void* quests)
{
    const std::unique_lock resources(LockAt(quests, 0x128), std::try_to_lock);
    if (!resources)
        return Reject("queue_resource_lock");
    const std::unique_lock notifications(LockAt(quests, 0x150), std::try_to_lock);
    if (!notifications)
        return Reject("queue_notification_lock");
    const auto pendingResources = ArrayAt<HandleRow>(quests, 0x130, MaxQueue);
    const auto pendingSlots = ArrayAt<std::uint32_t>(quests, 0x158, MaxQueue);
    if (!pendingResources || !pendingSlots)
        return Reject("queue_rows");
    for (const auto resource : *pendingResources)
    {
        if (!resource.instance)
            return Reject("queue_resource_missing");
        state.resourceRequests.push_back(Read<std::uint64_t>(resource.instance, 0x30));
    }
    state.notifications.assign(pendingSlots->begin(), pendingSlots->end());
    return true;
}

bool CopyInstances(State& state, const void* quests)
{
    // The native serializer 0x2CD3208 writes these pairs by value under
    // the manager's own lock. Capture preserves their identities without
    // invoking native save preparation, which may sort the live container.
    const auto manager = Read<void*>(quests, 0xF0);
    if (!manager)
        return Reject("instances_manager");
    {
        const std::unique_lock lock(LockAt(manager, 0), std::try_to_lock);
        if (!lock)
            return Reject("instances_lock");
        const auto rows = ArrayAt<NodeInstance>(manager, 8, MaxSlots);
        if (!rows)
            return Reject("instances_rows");
        state.instances.assign(rows->begin(), rows->end());
    }
    std::sort(state.instances.begin(), state.instances.end(), [](const NodeInstance& a, const NodeInstance& b) {
        return a.key < b.key;
    });
    if (std::adjacent_find(state.instances.begin(), state.instances.end(), [](const NodeInstance& a, const NodeInstance& b) {
        return a.key == b.key;
    }) != state.instances.end())
        return Reject("instances_duplicate");
    return true;
}

void Prime(Boundary b, const Capture& capture, const void* delay, const void* timeSystem, Monotonic::time_point now)
{
    TimerRequest fresh{};
    fresh.boundary = b;
    fresh.delay = Is(delay, DelaySystem) ? delay : nullptr;
    fresh.timeSystem = Is(timeSystem, TimeSystem) ? timeSystem : nullptr;
    fresh.gateEpoch = gate.Epoch();
    fresh.refreshed = now;
    fresh.count = capture.waits.size();
    std::copy(capture.waits.begin(), capture.waits.end(), fresh.waits.begin());
    if (timerRequest.boundary == b && timerRequest.gateEpoch == fresh.gateEpoch &&
        timerRequest.delay == fresh.delay && timerRequest.timeSystem == fresh.timeSystem)
    {
        for (std::size_t i = 0; i < fresh.count; ++i)
        {
            const auto match = std::find(timerRequest.waits.begin(), timerRequest.waits.begin() + timerRequest.count,
                                         fresh.waits[i]);
            if (match != timerRequest.waits.begin() + timerRequest.count)
                fresh.samples[i] = timerRequest.samples[static_cast<std::size_t>(match - timerRequest.waits.begin())];
        }
    }
    timerRequest = fresh;
}

void CopyTimings(Capture& capture, Boundary b, const void* delay, const void* timeSystem, Monotonic::time_point now)
{
    if (timerRequest.boundary != b || timerRequest.gateEpoch != gate.Epoch() ||
        (timerRequest.delay && timerRequest.delay != delay) ||
        (timerRequest.timeSystem && timerRequest.timeSystem != timeSystem))
        return;
    for (const auto& wait : capture.waits)
    {
        const auto key = (static_cast<std::uint64_t>(wait.registration.phase) << 32) | wait.registration.node;
        const auto instance = std::lower_bound(capture.state.instances.begin(), capture.state.instances.end(), key,
            [](const NodeInstance& row, std::uint64_t index) { return row.key < index; });
        const auto timerKey = wait.clock == Clock::Real ? ptfr::SchedulerId::FromNative(wait.timer).NodeInstanceValue() : wait.timer;
        if (instance == capture.state.instances.end() || instance->key != key || instance->value != timerKey)
            continue;
        for (std::size_t i = 0; i < timerRequest.count; ++i)
        {
            const auto& sample = timerRequest.samples[i];
            const auto age = std::chrono::duration_cast<std::chrono::milliseconds>(now - sample.time).count();
            if (UseTiming(wait, timerRequest.waits[i], sample.remaining, age, capture.state.notifications) &&
                !Ready(wait.handler))
            {
                capture.state.timings.push_back({wait.slot, wait.clock, wait.timer, sample.remaining,
                                                 static_cast<std::uint32_t>(age)});
                break;
            }
        }
    }
}

void RealTick(void* delay, float frameSeconds, const void* time)
{
    if (enabled.load())
    {
        const std::unique_lock lock(boundaryMutex, std::try_to_lock);
        if (lock && timerRequest.delay == delay && gate.Matches(timerRequest.boundary))
        {
            const auto now = Monotonic::now();
            for (std::size_t i = 0; i < timerRequest.count; ++i)
            {
                const auto& wait = timerRequest.waits[i];
                if (wait.clock != Clock::Real)
                    continue;
                const auto pending = At<float (*)(void*, std::uint64_t)>(0x111894C)(delay, wait.timer);
                timerRequest.samples[i] = {};
                if (std::isfinite(pending) && std::isfinite(frameSeconds) && frameSeconds >= 0 &&
                    pending > frameSeconds)
                    timerRequest.samples[i] = {static_cast<double>(pending), now};
            }
        }
    }
    realTickOriginal(delay, frameSeconds, time);
}

void GameTick(void* timeSystem, float frameSeconds, const void* time)
{
    gameTickOriginal(timeSystem, frameSeconds, time);
    if (!enabled.load())
        return;
    const std::unique_lock lock(boundaryMutex, std::try_to_lock);
    if (!lock)
        return;
    if (timerRequest.timeSystem != timeSystem || !gate.Matches(timerRequest.boundary))
        return;
    const auto now = Monotonic::now();
    std::uint32_t clock{};
    At<void* (*)(void*, std::uint32_t*)>(0x468358)(timeSystem, &clock);
    for (std::size_t i = 0; i < timerRequest.count; ++i)
    {
        const auto& wait = timerRequest.waits[i];
        if (wait.clock != Clock::Game)
            continue;
        timerRequest.samples[i] = {};
        const auto id = static_cast<std::uint32_t>(wait.timer);
        const auto row = ptfr::FindGameTimer(timeSystem, id);
        if (!row || !Is(row->timer, GameTimerRecord))
            continue;
        const auto duration = Read<std::uint32_t>(row->timer, 0x90);
        const auto sample = ptfr::ReadOneShotGameWait(timeSystem, id, clock, duration, image + GameTimerRecord,
                                                   image + NewGameTimerCallback, image + LoadedGameTimerCallback,
                                                   wait.handler);
        if (sample)
            timerRequest.samples[i] = {static_cast<double>(sample->wait.seconds), now};
    }
}

std::string MakeId()
{
    std::uint8_t random[16]{};
    if (BCryptGenRandom(nullptr, random, sizeof(random), BCRYPT_USE_SYSTEM_PREFERRED_RNG) < 0)
        return {};
    constexpr char hex[] = "0123456789abcdef";
    std::string id;
    id.reserve(32);
    for (const auto byte : random)
    {
        id.push_back(hex[byte >> 4]);
        id.push_back(hex[byte & 15]);
    }
    return id;
}

enum class ReadMode { Prime, Commit, Probe };

bool Copy(Capture& capture, void* quests, const void* delay, const void* timeSystem,
          std::int32_t ticket, std::int32_t route, ReadMode mode)
{
    const std::unique_lock lifetime(boundaryMutex, std::try_to_lock);
    if (!lifetime)
        return Reject("boundary_lock");
    if (gate.Transitioning())
        return Reject("boundary_transition");
    if (notificationPasses)
        return Reject("boundary_notifications");
    if (!Is(quests, QuestSystem))
        return Reject("boundary_quest_system");
    const Boundary b{quests, Read<const void*>(quests, 0xF8), ticket, route};
    const bool probe = mode == ReadMode::Probe;
    const bool final = mode != ReadMode::Prime;
    if (!probe && !gate.Matches(b))
        return Reject("boundary_gate_mismatch");
    const auto now = Monotonic::now();
    if (!final && timerRequest.boundary == b && now - timerRequest.refreshed < std::chrono::milliseconds(250))
        return Reject("prime_throttle");
    const std::unique_lock graph(LockAt(quests, 0x60), std::try_to_lock);
    if (!graph)
        return Reject("graph_lock");
    const auto allowed = [&] { return probe ? ProbeFacts(b.facts) : OpenFacts(b); };
    if (!allowed() || !ReadPhases(capture, quests) || (!probe && !VerifyGateWriter(capture, route)) ||
        !ReadHandlers(capture, quests, final))
        return false;
    if (!final)
    {
        Prime(b, capture, delay, timeSystem, now);
        return false;
    }
    if (!CopyGraphFacts(capture.state, b.facts) || !CopyInstances(capture.state, quests) ||
        !CopyQueues(capture.state, quests) || !allowed())
        return false;
    if (!probe)
        CopyTimings(capture, b, delay, timeSystem, Monotonic::now());
    for (const auto& live : capture.phases)
        capture.state.phases.push_back(live.record);
    capture.epoch = gate.Epoch();
    if (probe)
        saveAdmissionProbeRequested.store(true);
    return true;
}

bool StillOpen(void* quests, std::int32_t ticket, std::int32_t route, std::uint64_t epoch)
{
    const std::unique_lock lifetime(boundaryMutex, std::try_to_lock);
    if (!lifetime || gate.Transitioning() || gate.Epoch() != epoch)
        return Reject("final_boundary_changed");
    const std::unique_lock graph(LockAt(quests, 0x60), std::try_to_lock);
    const Boundary b{quests, Read<const void*>(quests, 0xF8), ticket, route};
    if (!graph)
        return Reject("final_graph_lock");
    if (!gate.Matches(b))
        return Reject("final_gate_mismatch");
    return OpenFacts(b);
}

#include "NativeStageSelection.inc"

using PackedState = RED4ext::DynArray<std::uint64_t>;

void ReadCheckpoint(RED4ext::IScriptable*, RED4ext::CStackFrame* frame, PackedState* out, std::int64_t)
{
    RED4ext::Handle<RED4ext::quest::QuestsSystem> quests;
    RED4ext::Handle<RED4ext::game::DelaySystem> delay;
    RED4ext::Handle<RED4ext::game::TimeSystem> timeSystem;
    std::int32_t ticket{}, route{}, historyRevision{};
    PackedState presentation;
    RED4ext::GetParameter(frame, &quests);
    RED4ext::GetParameter(frame, &delay);
    RED4ext::GetParameter(frame, &timeSystem);
    RED4ext::GetParameter(frame, &ticket);
    RED4ext::GetParameter(frame, &route);
    RED4ext::GetParameter(frame, &historyRevision);
    RED4ext::GetParameter(frame, &presentation);
    ++frame->code;
    if (!out)
        return;
    out->Clear();
    // A probe has no cutoff ticket or ending route. Only the queued developer
    // request sends this reserved tuple. It receives one status word, never a
    // packet that the checkpoint decoder or save writer can use.
    const bool probe = ticket == 0 && route == 0 && historyRevision == -1;
    if (!enabled.load() || !quests || (!probe && (ticket <= 0 || (route != 1 && route != 2) || historyRevision < 0)))
    {
        if (probe)
            sdk->logger->Warn(plugin, "PTFR checkpoint probe refused: quest system or native hooks unavailable");
        else if (historyRevision > 0)
            sdk->logger->WarnF(plugin, "PTFR checkpoint final read rejected before capture: enabled=%d quests=%d ticket=%d route=%d revision=%d",
                               enabled.load() ? 1 : 0, quests ? 1 : 0, ticket, route, historyRevision);
        return;
    }
    try
    {
        // Phase/array addresses are used only inside Copy. Formatting and
        // allocation by the script ABI take place outside the native locks.
        const auto mode = probe ? ReadMode::Probe : historyRevision > 0 ? ReadMode::Commit : ReadMode::Prime;
        captureReject = "none";
        if (mode == ReadMode::Commit)
            sdk->logger->InfoF(plugin, "PTFR checkpoint final read invoked: ticket=%d route=%d revision=%d gate=%s",
                               ticket, route, historyRevision, gateOpenStatus.load());
        Capture capture(mode != ReadMode::Prime);
        if (!Copy(capture, quests.GetPtr(), delay.GetPtr(), timeSystem.GetPtr(), ticket, route, mode))
        {
            if (probe)
                sdk->logger->WarnF(plugin, "PTFR checkpoint probe refused: stage=%s", captureReject);
            else if (mode == ReadMode::Commit)
                sdk->logger->WarnF(plugin, "PTFR checkpoint final capture rejected: stage=%s gate=%s",
                                   captureReject, gateOpenStatus.load());
            return;
        }
        if (probe)
        {
            const auto& state = capture.state;
            const auto live = std::ranges::count(state.handlers, Binding::Live, &Handler::binding);
            sdk->logger->InfoF(plugin, "PTFR checkpoint probe ready: phases=%zu live_handlers=%zu slots=%zu "
                               "AND_rows=%zu node_instances=%zu notifications=%zu resource_requests=%zu wait_handlers=%zu",
                               state.phases.size(), static_cast<std::size_t>(live), state.handlers.size(),
                               state.facts[1].size(), state.instances.size(), state.notifications.size(),
                               state.resourceRequests.size(), state.waitsObserved);
            out->Resize(1);
            (*out)[0] = 1;
            return;
        }
        capture.state.presentation = ReadPresentation({presentation.Data(), presentation.Size()});
        const auto id = MakeId();
        const auto payload = Encode(capture.state, id, ticket, route, historyRevision);
        if (payload.empty())
        {
            sdk->logger->WarnF(plugin, "PTFR checkpoint final encoding rejected: id=%d", id.empty() ? 0 : 1);
            return;
        }
        PackedState encoded;
        encoded.Resize(static_cast<std::uint32_t>(PackedWords(id.size() + payload.size())));
        if (!Pack(id, payload, {encoded.Data(), encoded.Size()}))
        {
            sdk->logger->Warn(plugin, "PTFR checkpoint final packing rejected");
            return;
        }
        if (!StillOpen(quests.GetPtr(), ticket, route, capture.epoch))
        {
            sdk->logger->WarnF(plugin, "PTFR checkpoint final publication rejected: stage=%s", captureReject);
            return;
        }
        ObserveResumeSelection(quests.GetPtr(), capture, ticket, route);
        *out = std::move(encoded);
        sdk->logger->InfoF(plugin, "PTFR checkpoint final capture ready: phases=%zu handlers=%zu timings=%zu",
                           capture.state.phases.size(), capture.state.handlers.size(), capture.state.timings.size());
    }
    catch (const std::exception& error)
    {
        sdk->logger->WarnF(plugin, "PTFR execution checkpoint could not be copied: %s", error.what());
    }
}

void DecodeCheckpoint(RED4ext::IScriptable*, RED4ext::CStackFrame* frame, RED4ext::CString* out, std::int64_t)
{
    PackedState data;
    RED4ext::GetParameter(frame, &data);
    ++frame->code;
    if (!out)
        return;
    const auto decoded = Unpack({data.Data(), data.Size()});
    *out = RED4ext::CString(decoded);
}

void RegisterCheckpointFunctions()
{
    if (!hooksReady.load() || reader || decoder)
        return;
    auto* rtti = RED4ext::CRTTISystem::Get();
    if (!rtti || rtti->GetFunction(ReadCheckpointName) || rtti->GetFunction(DecodeCheckpointName))
    {
        sdk->logger->Warn(plugin, "PTFR checkpoint runtime registry unavailable or name already in use");
        return;
    }

    const auto types = ResolveCheckpointTypes(*rtti, [](const char* name) {
        return RED4ext::CNamePool::Add(name);
    });
    const Parameter required[]{
        {"handle:questQuestsSystem", types.quests}, {"handle:gameDelaySystem", types.delay},
        {"handle:gameTimeSystem", types.clock}, {"Int32", types.int32},
        {"array:Uint64", types.words}, {"String", types.text}
    };
    bool available = true;
    for (const auto& binding : required)
    {
        if (!binding.type)
        {
            sdk->logger->WarnF(plugin, "PTFR checkpoint runtime type unavailable or invalid: %s", binding.name);
            available = false;
        }
    }
    if (!available)
        return;

    auto* capture = RED4ext::CGlobalFunction::Create(ReadCheckpointName, ReadCheckpointName, &ReadCheckpoint);
    auto* decode = RED4ext::CGlobalFunction::Create(DecodeCheckpointName, DecodeCheckpointName, &DecodeCheckpoint);
    if (!capture || !decode)
    {
        sdk->logger->Warn(plugin, "PTFR checkpoint runtime function allocation failed");
        return;
    }

    const auto readParams = types.CaptureParameters();
    const auto decodeParams = types.DecodeParameters();
    const auto* readFailure = DescribeCheckpointFunction(*capture, readParams, types.words, &Property::Create);
    const auto* decodeFailure = DescribeCheckpointFunction(*decode, decodeParams, types.text, &Property::Create);
    if (readFailure || decodeFailure)
    {
        if (readFailure)
            sdk->logger->WarnF(plugin, "PTFR checkpoint capture signature rejected at %s", readFailure);
        if (decodeFailure)
            sdk->logger->WarnF(plugin, "PTFR checkpoint decoder signature rejected at %s", decodeFailure);
        return;
    }

    rtti->RegisterFunction(capture);
    rtti->RegisterFunction(decode);
    const bool capturePublished = rtti->GetFunction(ReadCheckpointName) == capture;
    const bool decodePublished = rtti->GetFunction(DecodeCheckpointName) == decode;
    if (!capturePublished || !decodePublished)
    {
        if (capturePublished)
            rtti->UnregisterFunction(capture);
        if (decodePublished)
            rtti->UnregisterFunction(decode);
        sdk->logger->Warn(plugin, "PTFR checkpoint runtime registration did not read back both functions");
        return;
    }
    reader = capture;
    decoder = decode;
    enabled.store(true);
    sdk->logger->Info(plugin, "PTFR execution checkpoint runtime ready: capture and decode registered");
}

bool OnRunning(RED4ext::CGameApplication*)
{
    try
    {
        RegisterCheckpointFunctions();
    }
    catch (const std::exception& error)
    {
        sdk->logger->WarnF(plugin, "PTFR checkpoint runtime registration failed: %s", error.what());
    }
    return true;
}

bool VerifyFile(const std::filesystem::path& path, std::string_view expected)
{
    const auto file = CreateFileW(path.c_str(), GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_DELETE,
                                  nullptr, OPEN_EXISTING, FILE_FLAG_SEQUENTIAL_SCAN, nullptr);
    if (file == INVALID_HANDLE_VALUE)
        return false;
    BCRYPT_ALG_HANDLE algorithm{};
    BCRYPT_HASH_HANDLE hash{};
    bool ok = BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0) >= 0 &&
              BCryptCreateHash(algorithm, &hash, nullptr, 0, nullptr, 0, 0) >= 0;
    std::uint8_t buffer[65536];
    while (ok)
    {
        DWORD size{};
        ok = ReadFile(file, buffer, sizeof(buffer), &size, nullptr) != FALSE;
        if (!ok || !size)
            break;
        ok = BCryptHashData(hash, buffer, size, 0) >= 0;
    }
    std::uint8_t digest[32];
    ok = ok && BCryptFinishHash(hash, digest, sizeof(digest), 0) >= 0;
    constexpr char hex[] = "0123456789ABCDEF";
    if (ok)
    {
        for (std::size_t i = 0; i < sizeof(digest); ++i)
            ok = ok && expected[2 * i] == hex[digest[i] >> 4] && expected[2 * i + 1] == hex[digest[i] & 15];
    }
    if (hash)
        BCryptDestroyHash(hash);
    if (algorithm)
        BCryptCloseAlgorithmProvider(algorithm, 0);
    CloseHandle(file);
    return ok;
}

struct Hook
{
    std::uintptr_t rva;
    const char* prefix;
    void* detour;
    void** original;
    bool attached{};
};

template<class Method>
Hook MakeHook(std::uintptr_t rva, const char* prefix, Method detour, Method& original)
{
    return {rva, prefix, reinterpret_cast<void*>(detour), reinterpret_cast<void**>(&original), false};
}

Hook hooks[]{
    MakeHook(0x3CC488, "\x40\x55\x53\x56\x57\x41\x56\x48", &DispatchSaves, dispatchSavesOriginal),
    MakeHook(0x739578, "\x48\x8B\xC4\x48\x89\x58\x08\x48", &Load, loadOriginal),
    MakeHook(0x35EAEC, "\x40\x53\x56\x57\x48\x83\xEC\x40", &Teardown, teardownOriginal),
    MakeHook(0x35F430, "\x48\x89\x5C\x24\x10\x48\x89\x74", &InitializeRoot, rootOriginal),
    MakeHook(0x156EFD0, "\x48\x89\x5C\x24\x08\x57\x48\x83", &RestorePhases, restoreOriginal),
    MakeHook(0x2B28EC, "\x48\x89\x5C\x24\x10\x48\x89\x74", &RestoreHandlers, restoreHandlersOriginal),
    MakeHook(0x3534DC, "\x48\x89\x5C\x24\x18\x55\x56\x57", &DrainNotifications, drainOriginal),
    MakeHook(0x9DDC68, "\x40\x53\x48\x83\xEC\x30\x48\x8B", &ExecuteFactsNode, factsNodeOriginal),
    MakeHook(0x1AA634, "\x48\x8B\xC4\x48\x89\x58\x10\x48", &RealTick, realTickOriginal),
    MakeHook(0x7C0CA0, "\x48\x8B\xC4\x55\x53\x56\x57\x41", &GameTick, gameTickOriginal),
};

bool Detach()
{
    bool ok = true;
    for (auto i = std::size(hooks); i > 0; --i)
    {
        auto& hook = hooks[i - 1];
        if (hook.attached)
        {
            hook.attached = !sdk->hooking->Detach(plugin, const_cast<std::uint8_t*>(image + hook.rva));
            ok = !hook.attached && ok;
        }
    }
    return ok;
}

bool Attach()
{
    wchar_t path[MAX_PATH]{};
    const auto size = GetModuleFileNameW(nullptr, path, MAX_PATH);
    if (!image || !size || size >= MAX_PATH)
        return false;
    constexpr auto executable = "D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4";
    const std::filesystem::path exe{path};
    const auto root = exe.parent_path().parent_path().parent_path();
    if (!VerifyFile(exe, executable) || !VerifyFile(root / "archive/pc/mod/zzzz_PTFR_Combined.archive", ArchiveSHA) ||
        Read<const void*>(image + FactsManager, 0x10) != image + 0x2B2270 ||
        Read<const void*>(image + DelaySystem, 0x290) != image + 0x111894C ||
        Read<const void*>(image + 0x3047250, 0x158) != image + 0x9DDC68 ||
        Read<const void*>(image + 0x30E5E68, 0xE8) != image + SetVarBody ||
        Read<const void*>(image + SaveSessionVtable, 0x140) != image + 0x3CC094 ||
        Read<const void*>(image + QuestSystem, 0x110) != image + 0x35F430 ||
        Read<const void*>(image + QuestSystem, 0x148) != image + 0x739578)
        return false;
    for (const auto& hook : hooks)
    {
        if (std::memcmp(image + hook.rva, hook.prefix, 8) != 0)
            return false;
    }
    for (auto& hook : hooks)
    {
        if (!sdk->hooking->Attach(plugin, const_cast<std::uint8_t*>(image + hook.rva), hook.detour, hook.original))
        {
            Detach();
            return false;
        }
        hook.attached = true;
    }
    return true;
}
} // namespace

RED4EXT_C_EXPORT bool RED4EXT_CALL Main(RED4ext::v1::PluginHandle handle, RED4ext::v1::EMainReason reason,
                                      const RED4ext::v1::Sdk* api)
{
    if (reason == RED4ext::v1::EMainReason::Unload)
    {
        enabled.store(false);
        if (reader && decoder)
        {
            if (auto* rtti = RED4ext::CRTTISystem::Get())
            {
                rtti->UnregisterFunction(reader);
                rtti->UnregisterFunction(decoder);
            }
            reader = nullptr;
            decoder = nullptr;
        }
        return Detach();
    }
    if (reason != RED4ext::v1::EMainReason::Load || !api || !api->hooking || !api->logger ||
        !api->gameStates || !api->gameStates->Add)
        return false;
    sdk = api;
    plugin = handle;
    image = reinterpret_cast<const std::uint8_t*>(GetModuleHandleW(nullptr));
    RED4ext::v1::GameState running{&OnRunning, nullptr, nullptr};
    if (!sdk->gameStates->Add(plugin, RED4ext::EGameStateType::Running, &running))
    {
        sdk->logger->Warn(plugin, "PTFR checkpoint could not register its running-state callback");
        return true;
    }
    try
    {
        hooksReady.store(Attach());
    }
    catch (const std::exception&)
    {
        Detach();
    }
    if (!hooksReady.load())
        sdk->logger->Warn(plugin, "PTFR execution capture unavailable for this runtime or archive");
    return true;
}

RED4EXT_C_EXPORT void RED4EXT_CALL Query(RED4ext::v1::PluginInfo* info)
{
    info->name = L"PTFR Quest Execution Checkpoint";
    info->author = L"Post Tower Continuation";
    info->version = RED4EXT_V1_SEMVER(0, 1, 11);
    info->runtime = RED4EXT_V1_RUNTIME_VERSION_2_50;
    info->sdk = RED4EXT_V1_SDK_VERSION_CURRENT;
}

RED4EXT_C_EXPORT std::uint32_t RED4EXT_CALL Supports()
{
    return RED4EXT_API_VERSION_1;
}
