#include "source_01/NativeCheckpoint.cpp"
#include "control_input.hpp"

#include <cstdio>
#include <cstdlib>
#include <vector>

namespace
{
unsigned failures{};
unsigned passes{};
void Check(bool okay, const char* text)
{
    std::printf("%s %s\n", okay ? "PASS" : "FAIL", text);
    okay ? ++passes : ++failures;
}

template<typename T>
void Put(void* object, std::size_t offset, T value)
{
    std::memcpy(static_cast<std::byte*>(object) + offset, &value, sizeof(value));
}

struct Fixture;
Fixture* fixture{};

struct Fixture
{
    Fixture() : clockObjects(0x6EC00)
    {
        fixture = this;
        image = static_cast<std::uint8_t*>(VirtualAlloc(nullptr, 0x3800000, MEM_RESERVE | MEM_COMMIT,
                                                       PAGE_EXECUTE_READWRITE));
        if (!image)
            std::abort();
        RestoreAt(0x2B2270, &GetFact);
        RestoreAt(0x194AC4, &ReadMapping);
        RestoreAt(0x468358, &ReadClock);
        if (!FlushInstructionCache(GetCurrentProcess(), image, 0x3800000))
            std::abort();
        testLogger.WarnF = &IgnoreLog;
        testSdk.logger = &testLogger;
        sdk = &testSdk;
        enabled.store(true);
        dispatchSavesOriginal = [](void*, void*) { ++fixture->saveDispatches; };
        notifyQuestOriginal = [](void*, std::uint32_t slot) { fixture->published.push_back(slot); };
        uninitializeGameWaitOriginal = &Uninitialize;
        initializeGameWaitOriginal = &Initialize;
        allocateQuestSlotOriginal = [](void*, std::uint64_t, const std::uint64_t*) { return NewSlot; };
        makeGameTimerOriginal = &MakeTimer;
        Put(quests.data(), 0, image + QuestSystem);
        Put(quests.data(), 0xF8, factsStorage.data());
        Put(quests.data(), 0x100, loader.data());
        Put(quests.data(), 0xE8, events.data());
        Put(loader.data(), 0, image + PrefabLoaderType);
        Put(loader.data(), 0xC8, &world);
        Put(factsStorage.data(), 0, image + FactsManager);
        Put(context.data(), 0x18, quests.data());
        Put(context.data(), 0xE8, clockObjects.data());
        Put(clockObjects.data(), 0, image + TimeSystem);
        Put(session.data(), 0, image + SaveSessionVtable);
        ResetHandler(oldHandler, SavedTimer, true);
        ResetHandler(newHandler, 0, false);
        static_assert(GateTicket > 0 && CapturedSeconds < FalcoDuration);
    }

    ~Fixture()
    {
        ResetLiveHandoff();
        enabled.store(false);
        VirtualFree(const_cast<std::uint8_t*>(image), 0, MEM_RELEASE);
        image = nullptr;
        sdk = nullptr;
        fixture = nullptr;
    }

    void ResetHandler(std::array<std::byte, 0x50>& handler, std::uint32_t timerId, bool active)
    {
        Put(handler.data(), 0, image + GameTimeHandler);
        Put(handler.data(), 0x38, FalcoTimerNodeKey);
        Put(handler.data(), 0x40, timerId);
        Put(handler.data(), 0x44, FalcoDuration);
        Put(handler.data(), 0x30, active ? 1U : 0U);
    }

    LiveHandoff& Start()
    {
        auto& handoff = liveHandoff.emplace();
        handoff.cutoff = {quests.data(), factsStorage.data(), GateTicket, 1};
        handoff.oldPrefabs = {loader.data(), &world, {10, 0}, {111, 222}};
        handoff.timeSystem = clockObjects.data();
        handoff.plan.falcoWait = {SavedSlot, Clock::Game, SavedTimer, CapturedSeconds, 0};
        handoff.plan.reyesChoice = {ReyesChoiceKey, 4};
        for (std::size_t index = 0; index < handoff.plan.paths.size(); ++index)
            handoff.plan.paths[index].retiredSlot = SavedSlot + static_cast<std::uint32_t>(index);
        return handoff;
    }

    void SetQueuedOldSlot(bool queued)
    {
        Put(quests.data(), 0x158, &queuedSlot);
        Put(quests.data(), 0x160, 1U);
        Put(quests.data(), 0x164, queued ? 1U : 0U);
    }

    void SetClockTimer(bool active)
    {
        auto* list = clockObjects.data() + ptfr::GameTimerList;
        Put(list, 0x10, timerRef);
        Put(list, ptfr::GameTimerCount, active ? 1U : 0U);
    }

    static std::int32_t GetFact(const void*, std::uint32_t store, std::uint32_t key)
    {
        if (store != 1)
            return 0;
        if (key == FactId("mq049_started"))
            return 1;
        if (key == FactId("q307_main_game_killed") && fixture->preRetirement)
            return 0;
        const auto row = std::ranges::find_if(CompletionFacts, [key](const Fact& item) { return item.key == key; });
        return row == CompletionFacts.end() ? 0 : row->value;
    }

    static void IgnoreLog(RED4ext::v1::PluginHandle, const char*, ...) {}

    static bool ReadMapping(const void*, std::uint64_t key, std::uint64_t* found)
    {
        if (key != FalcoTimerNodeKey || !fixture->mapping)
            return false;
        *found = fixture->mapping;
        return true;
    }

    static void* ReadClock(void*, std::uint32_t* out)
    {
        *out = ClockNow;
        return out;
    }

    static void Uninitialize(void* handler, void*)
    {
        ++fixture->stops;
        fixture->mapping = 0;
        Put(handler, 0x30, 0U);
    }

    static void Initialize(void* handler, void*)
    {
        ++fixture->starts;
        alignas(void*) std::array<std::byte, 0x40> callback{};
        Put(callback.data(), 0, image + NewGameTimerCallback);
        Put(callback.data(), 8, handler);
        Put(callback.data(), 0x38, callback.data());
        constexpr std::uint32_t fullDeadline = ClockNow + FalcoDuration;
        constexpr std::uint32_t repeats = 1;
        constexpr std::uint8_t mode = 0;
        constexpr std::uint64_t empty = 0;
        MakeRestoredGameTimer(&fixture->timerRef, &NewTimer, callback.data(), &fullDeadline,
                              &repeats, &mode, &FalcoDuration, &empty, &empty);
        fixture->mapping = NewTimer;
        Put(handler, 0x40, NewTimer);
        Put(handler, 0x30, 1U);
    }

    static ptfr::NativeGameTimerReference* MakeTimer(ptfr::NativeGameTimerReference* out, const std::uint32_t* id,
        void* callback, const std::uint32_t* deadline, const std::uint32_t* repeats, const std::uint8_t* mode,
        const std::uint32_t* seconds, const std::uint64_t*, const std::uint64_t*)
    {
        auto* timer = fixture->timer.data();
        auto* owned = timer + 0x48;
        Put(timer, 0, image + GameTimerRecord);
        Put(timer, 0x40, *deadline);
        Put(timer, 0x44, *repeats);
        Put(timer, 0x80, owned);
        Put(timer, 0x88, *id);
        Put(timer, 0x90, *seconds);
        Put(timer, 0x94, *mode);
        std::memcpy(owned, callback, 0x10);
        *out = {timer, &fixture->timerCount};
        return out;
    }

    template<class Method>
    void RestoreAt(std::uint32_t rva, Method fn)
    {
        std::uint8_t jump[]{0x48, 0xB8, 0, 0, 0, 0, 0, 0, 0, 0, 0xFF, 0xE0};
        Put(jump, 2, reinterpret_cast<std::uintptr_t>(fn));
        std::memcpy(const_cast<std::uint8_t*>(image) + rva, jump, sizeof(jump));
    }

    static constexpr auto NewSlot = 1400U;
    static constexpr auto NewTimer = SavedTimer + 30;
    static constexpr std::uint32_t ClockNow = 7'430'843;
    RED4ext::v1::Sdk testSdk{};
    RED4ext::v1::Logger testLogger{};
    std::vector<std::byte> clockObjects;
    std::vector<std::uint32_t> published;
    alignas(void*) std::array<std::byte, 0x2B0> quests{};
    alignas(void*) std::array<std::byte, 0x80> factsStorage{};
    alignas(void*) std::array<std::byte, 0xF0> loader{};
    alignas(void*) std::array<std::byte, 0x40> events{};
    alignas(void*) std::array<std::byte, 0xF0> context{};
    alignas(void*) std::array<std::byte, 0x50> oldHandler{}, newHandler{};
    alignas(void*) std::array<std::byte, 0xA0> timer{};
    alignas(void*) std::array<std::uint8_t, 0x309> session{};
    ptfr::NativeGameTimerReference timerRef{};
    std::uint64_t mapping{SavedTimer};
    std::uint32_t queuedSlot{SavedSlot};
    int world{};
    long timerCount{1};
    unsigned saveDispatches{}, starts{}, stops{};
    bool preRetirement{};
};

void CheckRetirementAndSaveGate()
{
    Fixture f;
    auto& handoff = f.Start();
    const auto facts = ReadHandoffFact(handoff);
    Check(GenuineTowerCompletion(GateTicket, facts) && !GenuineTowerCompletion(GateTicket + 1, facts),
          "the native post-credits gate matches the exact committed Reed ticket from the control");
    originalFalcoHandler.store(f.oldHandler.data());
    ObserveUninitializeGameWait(f.oldHandler.data(), f.context.data());
    Check(handoff.retired && f.stops == 1 && !f.mapping,
          "stock uninitialization releases the observed original timer and native mapping");
    OnLiveClockLocked(f.clockObjects.data());
    Check(handoff.retiredClock, "the clock independently confirms the old timer is absent");
    f.SetQueuedOldSlot(true);
    OnLiveQuestDrain(f.quests.data());
    Check(handoff.stage == HandoffStage::Retiring && handoff.cleanRetirementPasses == 0,
          "a stale selected slot in the native queue delays the handoff");
    f.SetQueuedOldSlot(false);
    OnLiveQuestDrain(f.quests.data());
    Check(handoff.stage == HandoffStage::Retiring && handoff.cleanRetirementPasses == 1,
          "the first quiet notification pass awaits the next native drain");
    OnLiveQuestDrain(f.quests.data());
    Check(handoff.stage == HandoffStage::NeedPermit, "two stock drain completions establish a clean retirement boundary");
    f.session[0x308] = 0x10;
    DispatchSaves(f.session.data(), nullptr);
    Check(!handoff.permit && f.saveDispatches == 1, "an in-progress save prevents handoff mutation");
    f.session[0x308] = 0;
    DispatchSaves(f.session.data(), nullptr);
    Check(handoff.permit && f.saveDispatches == 1, "the idle live session grants the permit before native save dispatch");
    {
        const Transition transition(f.quests.data());
        DispatchSaves(f.session.data(), nullptr);
        Check(!liveHandoff && gate.Transitioning() && f.saveDispatches == 1,
              "native load invalidates captured ownership while retaining save exclusion through the transition");
    }
    DispatchSaves(f.session.data(), nullptr);
    Check(f.saveDispatches == 2, "native saving resumes after the transition releases its permit");
}

void CheckTimerAndNotificationHooks()
{
    Fixture f;
    auto& handoff = f.Start();
    handoff.stage = HandoffStage::NeedPermit;
    DispatchSaves(f.session.data(), nullptr);
    handoff.stage = HandoffStage::Clock;
    f.mapping = 0;
    Check(restoreNotifications.Begin(f.quests.data()), "the selected native notification transaction opens once");
    installingHandler = &handoff;
    installingIndex = FalcoHandlerIndex;
    enrolledHandler = false;
    const auto key = FalcoTimerNodeKey;
    const auto slot = AllocateRestoreSlot(f.events.data(), FalcoRestoreNodes.back().type, &key);
    NotifyQuest(f.quests.data(), slot);
    NotifyQuest(f.quests.data(), slot);
    NotifyQuest(f.quests.data(), slot + 1);
    InitializeRestoredGameWait(f.newHandler.data(), f.context.data());
    installingIndex.reset();
    installingHandler = nullptr;
    Check(enrolledHandler && slot == Fixture::NewSlot && f.published == std::vector<std::uint32_t>{slot + 1},
          "the in-process slot hook enrolls only the selected callback and leaves unrelated delivery active");
    Check(f.starts == 1 && handoff.timerReceipt && handoff.createdTimer == Fixture::NewTimer &&
              handoff.timerReceipt->deadline == Fixture::ClockNow + CapturedSeconds,
          "the live initializer and factory detours produce precisely the selected remaining time and a new mapping");
    OnLiveClockLocked(f.clockObjects.data());
    Check(!handoff.freshClock, "a mapping without the live clock record remains pending");
    f.SetClockTimer(true);
    OnLiveClockLocked(f.clockObjects.data());
    Check(handoff.freshClock, "the clock hook verifies the replacement callback and deadline together");
    restoreNotifications.Finish(f.quests.data(), [&](std::uint32_t index) { notifyQuestOriginal(f.quests.data(), index); });
    Check(f.published == std::vector<std::uint32_t>{slot + 1, slot}, "release publishes a buffered native notification once");

    handoff.stage = HandoffStage::Rollback;
    handoff.failure = "fixture cancellation";
    OnLiveQuestDrain(f.quests.data());
    Check(liveHandoff && handoff.stage == HandoffStage::Cancelled && handoff.permit,
          "rollback retains the save permit while the newly created timer still awaits native cancellation");
    f.SetClockTimer(false);
    OnLiveClockLocked(f.clockObjects.data());
    OnLiveQuestDrain(f.quests.data());
    Check(!liveHandoff, "rollback completes only after the cancelled timer disappears from the clock");
}

void CheckRejectEarlyRetirement()
{
    Fixture f;
    auto& handoff = f.Start();
    f.preRetirement = true;
    originalFalcoHandler.store(f.oldHandler.data());
    ObserveUninitializeGameWait(f.oldHandler.data(), f.context.data());
    Check(!handoff.retired && handoff.failure && f.stops == 1,
          "a timer removed by ordinary quest progression still retires natively and cannot start a handoff");
    OnLiveQuestDrain(f.quests.data());
    Check(!liveHandoff, "an unqualified cutoff releases staged resources and clears the handoff");
}
} // namespace

int main()
{
    CheckRetirementAndSaveGate();
    CheckTimerAndNotificationHooks();
    CheckRejectEarlyRetirement();
    std::printf("%u passed\n", passes);
    return failures ? 1 : 0;
}
