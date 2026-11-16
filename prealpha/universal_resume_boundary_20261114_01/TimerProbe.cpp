#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>
#include <bcrypt.h>

#include <RED4ext/Common.hpp>
#include <RED4ext/Api/ApiVersion.hpp>
#include <RED4ext/Api/v1/EMainReason.hpp>
#include <RED4ext/Api/v1/PluginInfo.hpp>
#include <RED4ext/Api/v1/Runtime.hpp>
#include <RED4ext/Api/v1/Sdk.hpp>
#include <RED4ext/Api/v1/Version.hpp>

#include <atomic>
#include <cstdio>
#include <mutex>

#include "CutoffObservation.hpp"

namespace
{
// Diagnostic filter for an original 10-second wait already present in the pre-Tower fixture.
constexpr std::uint64_t ObservedNode = 0x1361AA1A00000005;
constexpr std::uint64_t QuestDelayTag = 0xC74E8775F65E90DD;
constexpr std::uintptr_t RealTimeHandler = 0x31267A0;
constexpr std::uintptr_t NewTimerCallback = 0x3695E40;
constexpr std::uintptr_t RestoredTimerCallback = 0x3695E70;
constexpr std::uintptr_t QuestSystem = 0x30BCE78;
constexpr std::uintptr_t FactsManager = 0x306FA58;
constexpr std::uintptr_t DelaySystem = 0x30A2A90;

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

template <class T>
T Read(const void* object, std::size_t offset)
{
    T result{};
    std::memcpy(&result, static_cast<const std::uint8_t*>(object) + offset, sizeof(result));
    return result;
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
    if (table == image + NewTimerCallback || table == image + RestoredTimerCallback)
    {
        const auto handler = Read<const void*>(callback, 8);
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

std::uint64_t BeginGateWrite(const void* facts, std::uint32_t store, std::uint32_t key,
                             std::optional<ptfr::GateOutcome>& previous)
{
    if (!IsGateChange(facts, store, key))
        return 0;
    const std::lock_guard lock(observationMutex);
    return observation.BeginGateWrite(facts, previous);
}

void LogGate(const char* action, ptfr::GateTicket gate, const char* details)
{
    char line[128];
    std::snprintf(line, sizeof(line), "%s route=%d ticket=%d %s", action, gate.route, gate.ticket, details);
    sdk->logger->Info(plugin, line);
}

void ObserveGateOpen(const void* facts, std::uint64_t write)
{
    const ptfr::GateTicket ticket{facts, getFact(facts, 1, GateRoute), getFact(facts, 1, GateTicket)};
    if (getFact(facts, 1, GateOpen) != 1 || getFact(facts, 1, GateResult) != 0)
        return;
    bool opened;
    {
        const std::lock_guard lock(observationMutex);
        opened = observation.Open(ticket, write);
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
    if (write && key == GateOpen && value == 1)
        ObserveGateOpen(facts, write);
}

void TransformFact(void* facts, std::uint32_t store, std::uint32_t key, void* transform)
{
    std::optional<ptfr::GateOutcome> previous;
    const auto write = BeginGateWrite(facts, store, key, previous);
    transformFactOriginal(facts, store, key, transform);
    if (previous)
        LogGate("cutoff-finished", previous->gate, previous->sampled ? "sampled=1" : "sampled=0");
    if (write && key == GateOpen)
        ObserveGateOpen(facts, write);
}

void DispatchDue(void* delay, float seconds, const void* time)
{
    std::optional<ptfr::CaptureRequest> request;
    {
        const std::lock_guard lock(observationMutex);
        request = observation.Request(delay);
    }
    if (request)
    {
        // This worker owns the delay list at this point. Only the native
        // scheduler accessor runs here. Quest handler pointers are opaque.
        const auto remaining = readRemaining(delay, request->wait.timer);
        bool accepted;
        {
            const std::lock_guard lock(observationMutex);
            accepted = observation.Accept(*request, remaining, seconds);
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
    dispatchDueOriginal(delay, seconds, time);
}

void ResetObservation()
{
    const std::lock_guard lock(observationMutex);
    observation.Reset();
    watchedTimer.store(0);
    retiringTimer.store(0);
}

void LoadQuests(void* quests, void* context, void* status, void* reader)
{
    ResetObservation();
    loadQuestsOriginal(quests, context, status, reader);
}

void TearDownQuests(void* quests, void* context)
{
    ResetObservation();
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
};
std::size_t installedHooks;
std::size_t attachedMask;

bool DetachHooks()
{
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
        return DetachHooks();
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
        Read<const void*>(image + DelaySystem, 0x290) != image + 0x111894C)
    {
        sdk->logger->Error(plugin, "Quest timer probe callback table mismatch");
        return false;
    }
    getFact = reinterpret_cast<GetFactMethod>(image + 0x2B2270);
    readRemaining = reinterpret_cast<ReadRemainingMethod>(image + 0x111894C);
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
    sdk->logger->Info(plugin, "Quest timer probe ready");
    return true;
}

RED4EXT_C_EXPORT void RED4EXT_CALL Query(RED4ext::v1::PluginInfo* info)
{
    info->name = L"PTFR Quest Timer Probe";
    info->author = L"Post Tower Continuation";
    info->version = RED4EXT_V1_SEMVER(0, 2, 0);
    info->runtime = RED4EXT_V1_RUNTIME_VERSION_2_50;
    info->sdk = RED4EXT_V1_SDK_VERSION_CURRENT;
}

RED4EXT_C_EXPORT std::uint32_t RED4EXT_CALL Supports()
{
    return RED4EXT_API_VERSION_1;
}
