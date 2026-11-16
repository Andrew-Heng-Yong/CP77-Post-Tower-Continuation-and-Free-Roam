#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>
#include <bcrypt.h>

#include <RED4ext/RED4ext.hpp>
#include <RED4ext/Scripting/Natives/Generated/quest/QuestsSystem.hpp>

#include <atomic>
#include <cstdio>
#include <mutex>

#include "../universal_resume_handoff_20261114_01/RealTimeHandoff.hpp"
#include "OwnerTrace.hpp"

namespace
{
constexpr std::uint64_t ObservedNode = 0x1361AA1A00000005;
constexpr std::uint64_t QuestDelayTag = 0xC74E8775F65E90DD;
constexpr std::uintptr_t RealTimeHandler = 0x31267A0;
constexpr std::uintptr_t GameTimeHandler = 0x31C2388;
constexpr std::uintptr_t NewTimerCallback = 0x3695E40;
constexpr std::uintptr_t RestoredTimerCallback = 0x3695E70;
constexpr std::uintptr_t QuestSystem = 0x30BCE78;
constexpr std::uintptr_t FactsManager = 0x306FA58;
constexpr std::uintptr_t DelaySystem = 0x30A2A90;
constexpr std::uintptr_t PhaseContext = 0x3040630;
constexpr std::uintptr_t PhaseInstance = 0x308A948;

constexpr std::uint32_t FactId(const char* name)
{
    std::uint32_t hash = 0x811C9DC5;
    for (; *name; ++name)
        hash = (hash ^ static_cast<unsigned char>(*name)) * 0x01000193;
    return hash;
}

constexpr auto GateOpen = FactId("PTFRHS3_GateOpen");
constexpr auto GateTicket = FactId("PTFRHS3_GateTicket");
constexpr auto GateRoute = FactId("PTFRHS3_GateRoute");
constexpr auto GateResult = FactId("PTFRHS3_GateResult");
constexpr auto TowerPONR = FactId("q307_point_of_no_return");
constexpr auto HanakoPONR = FactId("q115_point_of_no_return");
constexpr auto Tower2079 = FactId("q307_2079");
constexpr auto TowerDebugReset = FactId("q307_debug_reset");
constexpr auto TowerBaseKilled = FactId("q307_main_game_killed");
constexpr auto TowerEp1Killed = FactId("q307_ep1_killed");
constexpr auto TowerDone = FactId("q307_done");
constexpr auto TowerFinished = FactId("q307_finished");
constexpr auto HasanPermit = FactId("PTFRS23_HASAN_Permit");
constexpr auto HasanIssued = FactId("PTFRS23_HASAN_Issued");
constexpr auto HasanEntered = FactId("PTFRS23_HASAN_Entered");
constexpr auto HasanFinished = FactId("PTFRS23_HASAN_Finished");
constexpr auto HasanFault = FactId("PTFRS23_HASAN_Fault");
constexpr auto TowerReady = FactId("PostTowerFreeRoamActive");

using HandlerMethod = void (*)(void*, void*);
using ScheduleMethod = std::uint64_t* (*)(void*, std::uint64_t*, void*, float, std::uint32_t, bool,
                                          std::uint64_t, std::uint64_t);
using AttachMethod = bool (*)(void*, std::uint64_t, void*, std::uint64_t, std::uint64_t);
using CompleteMethod = void (*)(void*);
using CollectMethod = void* (*)(void*, void*, void*);
using RemoveMethod = void (*)(void*, const std::uint64_t*, std::uintptr_t);
using EraseMethod = void (*)(void*, std::uint16_t);
using SetFactMethod = void (*)(void*, std::uint32_t, std::uint32_t, std::int32_t);
using TransformFactMethod = void (*)(void*, std::uint32_t, std::uint32_t, void*);
using GetFactMethod = std::int32_t (*)(const void*, std::uint32_t, std::uint32_t);
using DispatchDueMethod = void (*)(void*, float, const void*);
using ReadRemainingMethod = float (*)(void*, std::uint64_t);
using LoadQuestsMethod = void (*)(void*, void*, void*, void*);
using TearDownQuestsMethod = void (*)(void*, void*);
using EnqueueQuestMethod = void (*)(void*, std::uint32_t);
using PhaseFactory = void* (*)(void*, void*, void*, const void*, void*, std::uint16_t);
using EraseChildMethod = void (*)(void*, void*, const void*, std::uint8_t);
using RegisterHandlerMethod = void (*)(void*, std::uint32_t, std::uint64_t, const void*);
using RetireSlotMethod = void (*)(void*, std::uint32_t);
using RootInitMethod = void (*)(void*);
using CurrentPhaseMethod = const void* (*)(const void*);
using FindHandlerMethod = void* (*)(const void*, std::uint32_t);

const RED4ext::v1::Sdk* sdk;
RED4ext::v1::PluginHandle plugin;
const std::uint8_t* image;
HandlerMethod initializeOriginal;
HandlerMethod uninitializeOriginal;
ScheduleMethod scheduleOriginal;
AttachMethod attachOriginal;
CompleteMethod completeOriginal;
CollectMethod collectOriginal;
RemoveMethod removeOriginal;
EraseMethod eraseOriginal;
SetFactMethod setFactOriginal;
TransformFactMethod transformFactOriginal;
DispatchDueMethod dispatchDueOriginal;
LoadQuestsMethod loadQuestsOriginal;
TearDownQuestsMethod tearDownQuestsOriginal;
EnqueueQuestMethod enqueueQuestOriginal;
PhaseFactory makeChildOriginal;
EraseChildMethod eraseChildOriginal;
RegisterHandlerMethod registerHandlerOriginal;
RetireSlotMethod retireSlotOriginal;
RootInitMethod rootInitOriginal;
CurrentPhaseMethod currentPhase;
FindHandlerMethod findHandler;
GetFactMethod getFact;
ReadRemainingMethod readRemaining;
thread_local bool observingInitialization;
thread_local std::uint64_t initializedTimer;
thread_local bool erasedDelaySlot;
thread_local std::uint64_t completingTimer;
std::atomic<std::uint64_t> watchedTimer;
std::atomic<std::uint64_t> retiringTimer;
std::mutex observationMutex;
ptfr::CutoffObservation observation;
ptfr::CutoffWaitSample waitSample;
RED4ext::CGlobalFunction* cutoffReader;
std::atomic_bool hooksReady{false};

struct OwnerWait
{
    const char* owner;
    std::uint64_t node;
    ptfr::CutoffObservation observation{};
    ptfr::CutoffWaitSample sample{};
};

OwnerWait ownerWaits[] = {{"native-open-world", 0x9A66DFB600000045},
                         {"native-bugfix", 0xDE60547900000045}, {"s23-quest", 0x617629A200000045}};

struct GateWrite
{
    std::uint64_t kabuki = 0;
    std::array<std::uint64_t, std::size(ownerWaits)> owners{};
};

OwnerWait* FindOwnerWait(std::uint64_t node)
{
    const auto found = std::find_if(std::begin(ownerWaits), std::end(ownerWaits),
                                    [&](const OwnerWait& wait) { return wait.node == node; });
    return found == std::end(ownerWaits) ? nullptr : found;
}

template <class T>
T Read(const void* object, std::size_t offset)
{
    T result{};
    std::memcpy(&result, static_cast<const std::uint8_t*>(object) + offset, sizeof(result));
    return result;
}

const ptfr::PhaseWatch* WatchedPhase(const void* phase)
{
    if (!phase || Read<const void*>(phase, 0) != image + PhaseInstance)
        return nullptr;
    const auto address = ptfr::CopyPhaseAddress(phase);
    if (!address)
        return nullptr;
    const auto* watch = ptfr::FindWatchedPhase(*address);
    return watch && ptfr::PhaseHash(watch->path) == Read<std::uint32_t>(phase, 0x80) ? watch : nullptr;
}

void WatchRealWait(const void* state, void* handler, std::uint64_t node, std::uint64_t timer)
{
    if (!ptfr::SchedulerId::FromNative(timer).IsQuestDelay())
        return;
    auto* found = FindOwnerWait(node);
    if (!found)
        return;
    const auto* quests = Read<const void*>(state, 0x128);
    auto* delay = Read<void*>(state, 0x208);
    if (!quests || !delay || Read<const void*>(quests, 0) != image + QuestSystem ||
        Read<const void*>(delay, 0) != image + DelaySystem)
        return;
    const auto* facts = Read<const void*>(quests, 0xF8);
    if (!facts || Read<const void*>(facts, 0) != image + FactsManager)
        return;

    const std::lock_guard lock(observationMutex);
    if (ptfr::HandlerReady(handler) || Read<std::uint64_t>(handler, 0x38) != node)
        return;
    auto& current = found->observation;
    current.Watch({handler, delay, facts, timer}, current.BeginWatch(handler));
}

void InvalidateRealWait(OwnerWait* wait, const void* handler)
{
    if (wait)
    {
        const std::lock_guard lock(observationMutex);
        wait->observation.Invalidate(handler);
    }
}

void LogOwner(const char* event, const ptfr::PhaseWatch& phase, std::uint32_t node, std::uint32_t slot,
              std::uint64_t type, int mode = -1)
{
    char line[208];
    std::snprintf(line, sizeof(line), "hasan-%s owner=%s phase=%08X node=%u slot=%u type=%016llX mode=%d",
                  event, phase.name, ptfr::PhaseHash(phase.path), node, slot,
                  static_cast<unsigned long long>(type), mode);
    sdk->logger->Info(plugin, line);
}

void* MakeChild(void* parent, void* result, void* context, const void* resource, void* graph, std::uint16_t node)
{
    auto* handle = makeChildOriginal(parent, result, context, resource, graph, node);
    const auto* child = handle ? Read<const void*>(handle, 0) : nullptr;
    if (const auto* watch = WatchedPhase(child); watch && ptfr::HasChild(parent, child) == true)
        LogOwner("child-created", *watch, node, UINT32_MAX, 0, Read<std::uint8_t>(context, 1));
    return handle;
}

void EraseChild(void* parent, void* context, const void* child, std::uint8_t permanent)
{
    // The native call below can release the last phase reference. Keep only
    // the matched static watch and copy the mode before invoking it.
    const auto* removed = child ? Read<const void*>(child, 0) : nullptr;
    const auto* watch = WatchedPhase(removed);
    const auto mode = watch ? Read<std::uint8_t>(context, 1) : 0;
    const bool linked = watch && ptfr::HasChild(parent, removed) == true;
    eraseChildOriginal(parent, context, child, permanent);
    if (linked && ptfr::HasChild(parent, removed) == false)
        LogOwner("child-detached", *watch, watch->path.back(), UINT32_MAX, 0, mode);
}

void RegisterHandler(void* context, std::uint32_t node, std::uint64_t type, const void* ref)
{
    if (!context || Read<const void*>(context, 0) != image + PhaseContext)
    {
        registerHandlerOriginal(context, node, type, ref);
        return;
    }
    const auto* state = Read<const void*>(context, 0x220);
    const auto* phase = state ? currentPhase(state) : nullptr;
    const auto* watch = WatchedPhase(phase);
    const auto mode = watch ? Read<std::uint8_t>(state, 1) : 0;
    const auto* events = watch ? Read<const void*>(state, 0x10) : nullptr;
    // The enclosing graph operation owns these objects. Re-read the map after
    // initialization so a callback which retired itself is never logged as a
    // successful registration from only its temporary handler reference.
    registerHandlerOriginal(context, node, type, ref);
    if (!watch || currentPhase(state) != phase)
        return;
    auto* handler = findHandler(phase, node);
    if (!handler || !ref || handler != Read<const void*>(ref, 0))
        return;
    const auto slot = Read<std::uint32_t>(handler, 0x28);
    if (!ptfr::MatchesRegistration(events, slot, ptfr::PhaseHash(watch->path), node, type))
        return;
    LogOwner("handler-registered", *watch, node, slot, type, mode);
    if (!watch->quest)
        return;
    const auto* cls = Read<const void*>(handler, 0);
    if ((node == 69 && cls == image + RealTimeHandler) || (node == 47 && cls == image + GameTimeHandler))
    {
        const auto timer = node == 69 ? Read<std::uint64_t>(handler, 0x40) : Read<std::uint32_t>(handler, 0x40);
        if (node == 69)
            WatchRealWait(state, handler, (static_cast<std::uint64_t>(ptfr::PhaseHash(watch->path)) << 32) | node, timer);
        char line[188];
        std::snprintf(line, sizeof(line), "hasan-wait owner=%s phase=%08X node=%u slot=%u clock=%s timer=%016llX",
                      watch->name, ptfr::PhaseHash(watch->path), node, slot, node == 69 ? "real" : "game",
                      static_cast<unsigned long long>(timer));
        sdk->logger->Info(plugin, line);
    }
}

void RetireSlot(void* eventManager, std::uint32_t slot)
{
    const auto row = ptfr::CopyRegistration(eventManager, slot);
    retireSlotOriginal(eventManager, slot);
    if (!row || ptfr::CopyRegistration(eventManager, slot))
        return;
    for (const auto& phase : ptfr::HasanPhases)
    {
        if (ptfr::PhaseHash(phase.path) == row->phaseHash)
            LogOwner("slot-cleared", phase, row->node, slot, row->type);
    }
}

bool IsObservedHandler(const void* handler)
{
    return handler && Read<const void*>(handler, 0) == image + RealTimeHandler &&
           Read<std::uint64_t>(handler, 0x38) == ObservedNode;
}

void Log(const char* action, std::uint64_t timer, float seconds = -1)
{
    char message[160];
    std::snprintf(message, sizeof(message), "%s node=%016llX timer=%016llX seconds=%.6f", action,
                  static_cast<unsigned long long>(ObservedNode), static_cast<unsigned long long>(timer), seconds);
    sdk->logger->Info(plugin, message);
}

void Initialize(void* handler, void* context)
{
    const bool previous = observingInitialization;
    const auto previousTimer = initializedTimer;
    observingInitialization = IsObservedHandler(handler);
    initializedTimer = 0;
    std::uint64_t write = 0;
    if (observingInitialization)
    {
        const std::lock_guard lock(observationMutex);
        write = observation.BeginWatch(handler);
    }
    initializeOriginal(handler, context);
    if (write && initializedTimer && Read<std::uint64_t>(handler, 0x40) == initializedTimer)
    {
        const auto quests = Read<const void*>(context, 0x18);
        const auto delay = Read<void*>(context, 0xF8);
        if (quests && delay && Read<const void*>(quests, 0) == image + QuestSystem &&
            Read<const void*>(delay, 0) == image + DelaySystem)
        {
            const auto facts = Read<const void*>(quests, 0xF8);
            if (facts && Read<const void*>(facts, 0) == image + FactsManager)
            {
                const std::lock_guard lock(observationMutex);
                observation.Watch({handler, delay, facts, initializedTimer}, write);
            }
        }
    }
    observingInitialization = previous;
    initializedTimer = previousTimer;
}

void Uninitialize(void* handler, void* context)
{
    InvalidateRealWait(FindOwnerWait(Read<std::uint64_t>(handler, 0x38)), handler);
    if (IsObservedHandler(handler))
    {
        {
            const std::lock_guard lock(observationMutex);
            observation.Invalidate(handler);
        }
        const auto timer = Read<std::uint64_t>(handler, 0x40);
        auto expected = timer;
        if (timer && watchedTimer.compare_exchange_strong(expected, 0))
            retiringTimer.store(timer);
        Log("uninitialize", timer);
    }
    uninitializeOriginal(handler, context);
}

std::uint64_t* Schedule(void* delay, std::uint64_t* result, void* callback, float seconds, std::uint32_t group,
                        bool flag, std::uint64_t tag, std::uint64_t payload)
{
    auto* timer = scheduleOriginal(delay, result, callback, seconds, group, flag, tag, payload);
    if (observingInitialization && tag == QuestDelayTag && group == 4 && timer)
    {
        if (ptfr::SchedulerId::FromNative(*timer).IsQuestDelay())
        {
            initializedTimer = *timer;
            watchedTimer.store(*timer);
        }
        Log("schedule", *timer, seconds);
    }
    return timer;
}

bool Attach(void* delay, std::uint64_t timer, void* callback, std::uint64_t tag, std::uint64_t payload)
{
    const bool accepted = attachOriginal(delay, timer, callback, tag, payload);
    if (observingInitialization && tag == QuestDelayTag && ptfr::SchedulerId::FromNative(timer).IsQuestDelay())
    {
        if (accepted)
        {
            initializedTimer = timer;
            watchedTimer.store(timer);
        }
        Log(accepted ? "reattach-accepted" : "reattach-rejected", timer);
    }
    return accepted;
}

void Complete(void* callback)
{
    const auto previous = completingTimer;
    completingTimer = 0;
    const auto table = Read<const void*>(callback, 0);
    const void* hasanHandler = nullptr;
    OwnerWait* hasanWait = nullptr;
    if (table == image + NewTimerCallback || table == image + RestoredTimerCallback)
    {
        const auto handler = Read<const void*>(callback, 8);
        if (handler && Read<const void*>(handler, 0) == image + RealTimeHandler)
        {
            hasanHandler = handler;
            hasanWait = FindOwnerWait(Read<std::uint64_t>(handler, 0x38));
        }
        if (IsObservedHandler(handler))
        {
            {
                const std::lock_guard lock(observationMutex);
                observation.Invalidate(handler);
            }
            completingTimer = Read<std::uint64_t>(handler, 0x40);
            Log("timer-callback-entered", completingTimer);
        }
    }
    completeOriginal(callback);
    InvalidateRealWait(hasanWait, hasanHandler);
    completingTimer = previous;
}

void EnqueueQuest(void* quests, std::uint32_t slot)
{
    enqueueQuestOriginal(quests, slot);
    if (completingTimer)
    {
        char line[128];
        std::snprintf(line, sizeof(line), "timer-quest-notification timer=%016llX slot=%u",
                      static_cast<unsigned long long>(completingTimer), slot);
        sdk->logger->Info(plugin, line);
    }
}

void* Collect(void* context, void* output, void* group)
{
    auto* result = collectOriginal(context, output, group);
    const auto timer = watchedTimer.load();
    if (result && timer)
    {
        const auto data = Read<const void*>(result, 0);
        const auto count = Read<std::uint32_t>(result, 0x0C);
        const auto remaining = ptfr::FindRemainingDelay(data, count, ptfr::SchedulerId::FromNative(timer));
        if (remaining && watchedTimer.load() == timer)
            Log("saved-remaining", timer, *remaining);
    }
    return result;
}

// The delay worker also uses this removal path after expiry. The probe reports
// the actual slot erasure independently of any callback already delivered.
void Remove(void* delay, const std::uint64_t* timer, std::uintptr_t nativeArgument)
{
    auto expected = retiringTimer.load();
    if (!expected || *timer != expected)
    {
        removeOriginal(delay, timer, nativeArgument);
        return;
    }
    erasedDelaySlot = false;
    removeOriginal(delay, timer, nativeArgument);
    const bool erased = erasedDelaySlot;
    erasedDelaySlot = false;
    if (erased && retiringTimer.compare_exchange_strong(expected, 0))
        Log("scheduler-slot-erased", expected);
}

void Erase(void* group, std::uint16_t index)
{
    eraseOriginal(group, index);
    erasedDelaySlot = true;
}

bool IsGateChange(const void* facts, std::uint32_t store, std::uint32_t key)
{
    return store == 1 && (key == GateOpen || key == GateResult || key == GateRoute || key == GateTicket) &&
           Read<const void*>(facts, 0) == image + FactsManager;
}

const char* OwnerFactName(std::uint32_t key)
{
    switch (key)
    {
    case TowerEp1Killed: return "q307_ep1_killed";
    case TowerDone: return "q307_done";
    case TowerFinished: return "q307_finished";
    case TowerReady: return "PostTowerFreeRoamActive";
    case HasanPermit: return "PTFRS23_HASAN_Permit";
    case HasanIssued: return "PTFRS23_HASAN_Issued";
    case HasanEntered: return "PTFRS23_HASAN_Entered";
    case HasanFinished: return "PTFRS23_HASAN_Finished";
    case HasanFault: return "PTFRS23_HASAN_Fault";
    default: return nullptr;
    }
}

void LogOwnerFact(const void* facts, std::uint32_t store, std::uint32_t key)
{
    if (store != 1)
        return;
    const auto* name = OwnerFactName(key);
    if (!name || Read<const void*>(facts, 0) != image + FactsManager)
        return;
    char line[148];
    std::snprintf(line, sizeof(line), "hasan-fact name=%s value=%d ticket=%d", name,
                  getFact(facts, 1, key), getFact(facts, 1, GateTicket));
    sdk->logger->Info(plugin, line);
}

bool IsDirectCutoff(const void* facts, std::int32_t ticket)
{
    return ticket > 0 && getFact(facts, 1, GateTicket) == ticket && getFact(facts, 1, GateRoute) == 1 &&
           getFact(facts, 1, GateOpen) == 1 && getFact(facts, 1, GateResult) == 0 &&
           getFact(facts, 1, TowerPONR) > 0 && getFact(facts, 1, HanakoPONR) == 0 &&
           getFact(facts, 1, Tower2079) == 0 && getFact(facts, 1, TowerDebugReset) == 0 &&
           getFact(facts, 1, TowerBaseKilled) == 0 && getFact(facts, 1, TowerEp1Killed) == 0 &&
           getFact(facts, 1, TowerDone) == 0 && getFact(facts, 1, TowerFinished) == 0;
}

void ReadWaitAtCutoff(RED4ext::IScriptable*, RED4ext::CStackFrame* frame, float* out, std::int64_t)
{
    RED4ext::Handle<RED4ext::quest::QuestsSystem> quests;
    std::int32_t ticket{};
    std::uint64_t node{};
    RED4ext::GetParameter(frame, &quests);
    RED4ext::GetParameter(frame, &ticket);
    RED4ext::GetParameter(frame, &node);
    ++frame->code;
    if (!out)
        return;
    *out = 0;
    if (!hooksReady)
        return;

    if (!quests || Read<const void*>(quests.GetPtr(), 0) != image + QuestSystem)
        return;
    const auto* facts = Read<const void*>(quests.GetPtr(), 0xF8);
    if (!facts || Read<const void*>(facts, 0) != image + FactsManager || !IsDirectCutoff(facts, ticket))
        return;

    const std::lock_guard lock(observationMutex);
    const auto* owner = FindOwnerWait(node);
    if (owner)
    {
        // Keep ambiguous captures out of the save-local sample. The diagnostic
        // still logs each native owner independently for the investigation.
        for (const auto& competing : ownerWaits)
        {
            if (&competing != owner && competing.sample.Read(competing.observation, facts, competing.node, ticket))
                return;
        }
    }
    const auto saved = owner ? owner->sample.Read(owner->observation, facts, node, ticket) :
                               waitSample.Read(observation, facts, node, ticket);
    if (saved)
        *out = saved->seconds;
}

void RegisterCutoffReader()
{
    constexpr auto name = "PTFR.HistorySnapshotHS1.ReadNativeWaitAtCutoff";
    auto function = RED4ext::CGlobalFunction::Create(name, name, &ReadWaitAtCutoff);
    if (!function)
    {
        sdk->logger->Error(plugin, "Quest timer cutoff reader allocation failed");
        return;
    }
    function->flags.isNative = true;
    function->flags.isStatic = true;
    function->AddParam("handle:questQuestsSystem", "quests");
    function->AddParam("Int32", "ticket");
    function->AddParam("Uint64", "node");
    function->SetReturnType("Float");
    RED4ext::CRTTISystem::Get()->RegisterFunction(function);
    cutoffReader = function;
}

GateWrite BeginGateWrite(const void* facts, std::uint32_t store, std::uint32_t key,
                         std::optional<ptfr::GateOutcome>& previous)
{
    GateWrite write;
    if (!IsGateChange(facts, store, key))
        return write;
    const std::lock_guard lock(observationMutex);
    write.kabuki = observation.BeginGateWrite(facts, previous);
    for (std::size_t i = 0; i < std::size(ownerWaits); ++i)
    {
        std::optional<ptfr::GateOutcome> ignored;
        write.owners[i] = ownerWaits[i].observation.BeginGateWrite(facts, ignored);
    }
    return write;
}

void LogGate(const char* action, ptfr::GateTicket gate, const char* details)
{
    char line[128];
    std::snprintf(line, sizeof(line), "%s route=%d ticket=%d %s", action, gate.route, gate.ticket, details);
    sdk->logger->Info(plugin, line);
}

void ObserveGateOpen(const void* facts, const GateWrite& write)
{
    const ptfr::GateTicket ticket{facts, getFact(facts, 1, GateRoute), getFact(facts, 1, GateTicket)};
    if (getFact(facts, 1, GateOpen) != 1 || getFact(facts, 1, GateResult) != 0)
        return;
    bool opened;
    {
        const std::lock_guard lock(observationMutex);
        opened = observation.Open(ticket, write.kabuki);
        if (ticket.route == 1)
        {
            for (std::size_t i = 0; i < std::size(ownerWaits); ++i)
                ownerWaits[i].observation.Open(ticket, write.owners[i]);
        }
    }
    if (opened)
        LogGate("cutoff-open", ticket, "");
}

void SetFact(void* facts, std::uint32_t store, std::uint32_t key, std::int32_t value)
{
    std::optional<ptfr::GateOutcome> previous;
    const auto write = BeginGateWrite(facts, store, key, previous);
    setFactOriginal(facts, store, key, value);
    if (previous)
        LogGate("cutoff-finished", previous->gate, previous->sampled ? "sampled=1" : "sampled=0");
    if (write.kabuki && key == GateOpen && value == 1)
        ObserveGateOpen(facts, write);
    LogOwnerFact(facts, store, key);
}

void TransformFact(void* facts, std::uint32_t store, std::uint32_t key, void* transform)
{
    std::optional<ptfr::GateOutcome> previous;
    const auto write = BeginGateWrite(facts, store, key, previous);
    transformFactOriginal(facts, store, key, transform);
    if (previous)
        LogGate("cutoff-finished", previous->gate, previous->sampled ? "sampled=1" : "sampled=0");
    if (write.kabuki && key == GateOpen)
        ObserveGateOpen(facts, write);
    LogOwnerFact(facts, store, key);
}

void DispatchDue(void* delay, float seconds, const void* time)
{
    std::optional<ptfr::CaptureRequest> request;
    std::array<std::optional<ptfr::CaptureRequest>, std::size(ownerWaits)> ownerRequests;
    {
        const std::lock_guard lock(observationMutex);
        request = observation.Request(delay);
        for (std::size_t i = 0; i < ownerRequests.size(); ++i)
            ownerRequests[i] = ownerWaits[i].observation.Request(delay);
    }
    if (request)
    {
        // This worker owns the delay list at this point. Only the native
        // scheduler accessor runs here. Quest handler pointers are opaque.
        const auto remaining = readRemaining(delay, request->wait.timer);
        bool accepted;
        {
            const std::lock_guard lock(observationMutex);
            accepted = waitSample.Record(observation, *request, ObservedNode, remaining, seconds);
        }
        if (accepted)
        {
            char line[192];
            std::snprintf(line, sizeof(line), "cutoff-sample route=%d ticket=%d node=%016llX timer=%016llX seconds=%.9g",
                          request->gate.route, request->gate.ticket, static_cast<unsigned long long>(ObservedNode),
                          static_cast<unsigned long long>(request->wait.timer), remaining);
            sdk->logger->Info(plugin, line);
        }
    }
    std::array<float, std::size(ownerWaits)> remainingByOwner{};
    bool anyOwnerRequest = false;
    for (std::size_t i = 0; i < ownerRequests.size(); ++i)
    {
        if (ownerRequests[i])
        {
            anyOwnerRequest = true;
            remainingByOwner[i] = readRemaining(delay, ownerRequests[i]->wait.timer);
        }
    }
    if (!anyOwnerRequest)
    {
        dispatchDueOriginal(delay, seconds, time);
        return;
    }
    std::array<bool, std::size(ownerWaits)> accepted{};
    {
        const std::lock_guard lock(observationMutex);
        for (std::size_t i = 0; i < ownerRequests.size(); ++i)
        {
            auto& wait = ownerWaits[i];
            if (ownerRequests[i])
                accepted[i] = wait.sample.Record(wait.observation, *ownerRequests[i], wait.node, remainingByOwner[i], seconds);
        }
    }
    for (std::size_t i = 0; i < accepted.size(); ++i)
    {
        if (!accepted[i])
            continue;
        const auto& pending = *ownerRequests[i];
        const auto& wait = ownerWaits[i];
        char line[208];
        std::snprintf(line, sizeof(line), "hasan-cutoff owner=%s ticket=%d node=%016llX timer=%016llX seconds=%.9g",
                      wait.owner, pending.gate.ticket, static_cast<unsigned long long>(wait.node),
                      static_cast<unsigned long long>(pending.wait.timer), remainingByOwner[i]);
        sdk->logger->Info(plugin, line);
    }
    dispatchDueOriginal(delay, seconds, time);
}

void ResetObservation()
{
    const std::lock_guard lock(observationMutex);
    observation.Reset();
    for (auto& wait : ownerWaits)
    {
        wait.observation.Reset();
        wait.sample = {};
    }
    waitSample = {};
    watchedTimer.store(0);
    retiringTimer.store(0);
}

void LoadQuests(void* quests, void* context, void* status, void* reader)
{
    ResetObservation();
    sdk->logger->Info(plugin, "hasan-session quest-load");
    loadQuestsOriginal(quests, context, status, reader);
}

void InitializeRoot(void* quests)
{
    ResetObservation();
    sdk->logger->Info(plugin, "hasan-session root-initialization");
    rootInitOriginal(quests);
}

void TearDownQuests(void* quests, void* context)
{
    ResetObservation();
    sdk->logger->Info(plugin, "hasan-session quest-teardown");
    tearDownQuestsOriginal(quests, context);
}

bool VerifyExecutable()
{
    constexpr std::uint8_t expected[] = {0xD3, 0x6E, 0x74, 0xC4, 0x75, 0x92, 0xE9, 0xC6,
                                         0x56, 0xAE, 0x25, 0x00, 0x78, 0xCB, 0x40, 0xB2,
                                         0xBE, 0x63, 0xC7, 0x82, 0xAF, 0x5B, 0xFB, 0xEF,
                                         0xF2, 0x28, 0x0D, 0x43, 0xE6, 0x53, 0xFA, 0xB4};
    wchar_t path[MAX_PATH];
    const auto length = GetModuleFileNameW(nullptr, path, MAX_PATH);
    if (length == 0 || length >= MAX_PATH)
        return false;
    const auto file = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_DELETE, nullptr, OPEN_EXISTING, 0,
                                  nullptr);
    if (file == INVALID_HANDLE_VALUE)
        return false;
    BCRYPT_ALG_HANDLE algorithm = nullptr;
    BCRYPT_HASH_HANDLE hash = nullptr;
    std::uint8_t digest[32];
    bool ok = BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0) >= 0 &&
              BCryptCreateHash(algorithm, &hash, nullptr, 0, nullptr, 0, 0) >= 0;
    std::uint8_t buffer[16384];
    while (ok)
    {
        DWORD bytesRead = 0;
        ok = ReadFile(file, buffer, sizeof(buffer), &bytesRead, nullptr) != FALSE;
        if (!ok || !bytesRead)
            break;
        ok = BCryptHashData(hash, buffer, bytesRead, 0) >= 0;
    }
    ok = ok && BCryptFinishHash(hash, digest, sizeof(digest), 0) >= 0 &&
         std::memcmp(digest, expected, sizeof(expected)) == 0;
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
};

template <class Function>
Hook MakeHook(std::uintptr_t rva, const char* prefix, Function detour, Function& original)
{
    return {rva, prefix, reinterpret_cast<void*>(detour), reinterpret_cast<void**>(&original)};
}

const Hook Hooks[] = {
    MakeHook(0x1948BC, "\x48\x89\x5C\x24\x20\x55\x56\x57", &Initialize, initializeOriginal),
    MakeHook(0x194828, "\x48\x89\x5C\x24\x10\x48\x89\x6C", &Uninitialize, uninitializeOriginal),
    MakeHook(0x1AA1A0, "\x48\x89\x5C\x24\x08\x48\x89\x7C", &Schedule, scheduleOriginal),
    MakeHook(0x193A1C, "\x48\x89\x5C\x24\x08\x48\x89\x7C", &Attach, attachOriginal),
    MakeHook(0x1304ED8, "\x48\x8B\x49\x08\xB2\x01\xE9\xC9", &Complete, completeOriginal),
    MakeHook(0x2AAC3D4, "\x48\x89\x5C\x24\x08\x48\x89\x74", &Collect, collectOriginal),
    MakeHook(0x1AA7D0, "\x44\x88\x44\x24\x18\x53\x48\x83", &Remove, removeOriginal),
    MakeHook(0x1AA3A8, "\x40\x53\x48\x83\xEC\x40\x0F\xB7", &Erase, eraseOriginal),
    MakeHook(0x350E50, "\x45\x8B\xD8\x8D\x42\xFF\x48\x8B", &SetFact, setFactOriginal),
    MakeHook(0x21F9A80, "\x45\x8B\xD8\x8D\x42\xFF\x48\x8B", &TransformFact, transformFactOriginal),
    MakeHook(0x1AA634, "\x48\x8B\xC4\x48\x89\x58\x10\x48", &DispatchDue, dispatchDueOriginal),
    MakeHook(0x739578, "\x48\x8B\xC4\x48\x89\x58\x08\x48", &LoadQuests, loadQuestsOriginal),
    MakeHook(0x35EAEC, "\x40\x53\x56\x57\x48\x83\xEC\x40", &TearDownQuests, tearDownQuestsOriginal),
    MakeHook(0x88BC58, "\x89\x54\x24\x10\x53\x48\x83\xEC", &EnqueueQuest, enqueueQuestOriginal),
    MakeHook(0x889C38, "\x48\x89\x5C\x24\x08\x48\x89\x74", &MakeChild, makeChildOriginal),
    MakeHook(0xBEC890, "\x48\x89\x5C\x24\x08\x57\x48\x83", &EraseChild, eraseChildOriginal),
    MakeHook(0x2B0800, "\x48\x89\x5C\x24\x18\x48\x89\x6C", &RegisterHandler, registerHandlerOriginal),
    MakeHook(0x2FCFD0, "\x89\x54\x24\x10\x53\x48\x83\xEC", &RetireSlot, retireSlotOriginal),
    MakeHook(0x35F430, "\x48\x89\x5C\x24\x10\x48\x89\x74", &InitializeRoot, rootInitOriginal),
};
std::size_t installedHooks;
std::size_t attachedMask;

bool DetachHooks()
{
    hooksReady = false;
    bool ok = true;
    for (auto index = installedHooks; index > 0; --index)
    {
        const auto bit = std::size_t{1} << (index - 1);
        if (!(attachedMask & bit))
            continue;
        if (sdk->hooking->Detach(plugin, const_cast<std::uint8_t*>(image + Hooks[index - 1].rva)))
            attachedMask &= ~bit;
        else
            ok = false;
    }
    return ok;
}
} // namespace

RED4EXT_C_EXPORT bool RED4EXT_CALL Main(RED4ext::v1::PluginHandle handle, RED4ext::v1::EMainReason reason,
                                      const RED4ext::v1::Sdk* api)
{
    if (reason == RED4ext::v1::EMainReason::Unload)
    {
        if (cutoffReader)
        {
            if (auto* const rtti = RED4ext::CRTTISystem::Get())
                rtti->UnregisterFunction(cutoffReader);
            cutoffReader = nullptr;
        }
        return DetachHooks();
    }
    if (reason != RED4ext::v1::EMainReason::Load || !api || !api->hooking || !api->logger)
        return false;

    sdk = api;
    plugin = handle;
    image = reinterpret_cast<const std::uint8_t*>(GetModuleHandleW(nullptr));
    if (!image || !VerifyExecutable())
    {
        sdk->logger->Error(plugin, "Quest timer probe executable hash mismatch");
        return false;
    }
    for (const auto& hook : Hooks)
    {
        if (std::memcmp(image + hook.rva, hook.prefix, 8) != 0)
        {
            sdk->logger->Error(plugin, "Quest timer probe native entry point mismatch");
            return false;
        }
    }
    if (Read<const void*>(image + NewTimerCallback, 0x10) != image + 0x1304ED8 ||
        Read<const void*>(image + RestoredTimerCallback, 0x10) != image + 0x1304ED8 ||
        Read<const void*>(image + FactsManager, 0x10) != image + 0x2B2270 ||
        Read<const void*>(image + DelaySystem, 0x290) != image + 0x111894C ||
        Read<const void*>(image + PhaseContext, 0x60) != image + 0x2B0800 ||
        Read<const void*>(image + QuestSystem, 0x110) != image + 0x35F430)
    {
        sdk->logger->Error(plugin, "Quest timer probe callback table mismatch");
        return false;
    }
    getFact = reinterpret_cast<GetFactMethod>(image + 0x2B2270);
    readRemaining = reinterpret_cast<ReadRemainingMethod>(image + 0x111894C);
    currentPhase = reinterpret_cast<CurrentPhaseMethod>(image + 0x2B224C);
    findHandler = reinterpret_cast<FindHandlerMethod>(image + 0x2B1B64);
    for (const auto& hook : Hooks)
    {
        if (!sdk->hooking->Attach(plugin, const_cast<std::uint8_t*>(image + hook.rva), hook.detour, hook.original))
        {
            sdk->logger->Error(plugin, "Quest timer probe hook attachment failed");
            // Keep the module loaded if the loader could not detach an earlier hook.
            return !DetachHooks();
        }
        attachedMask |= std::size_t{1} << installedHooks++;
    }
    auto* const rtti = RED4ext::CRTTISystem::Get();
    if (!rtti)
        return !DetachHooks();
    rtti->AddPostRegisterCallback(&RegisterCutoffReader);
    hooksReady = true;
    sdk->logger->Info(plugin, "Quest timer cutoff and owner trace ready");
    return true;
}

RED4EXT_C_EXPORT void RED4EXT_CALL Query(RED4ext::v1::PluginInfo* info)
{
    info->name = L"PTFR Quest Timer Owner Trace";
    info->author = L"Post Tower Continuation";
    info->version = RED4EXT_V1_SEMVER(0, 4, 0);
    info->runtime = RED4EXT_V1_RUNTIME_VERSION_2_50;
    info->sdk = RED4EXT_V1_SDK_VERSION_CURRENT;
}

RED4EXT_C_EXPORT std::uint32_t RED4EXT_CALL Supports()
{
    return RED4EXT_API_VERSION_1;
}
