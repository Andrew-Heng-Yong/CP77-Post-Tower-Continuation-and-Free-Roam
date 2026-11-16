constexpr auto PrefabLoaderType = 0x306F8C0U;
constexpr auto QuestPhaseHandlerType = 0x3046748U;
constexpr std::size_t FalcoParent = 6;
constexpr auto FalcoHandlerIndex = FalcoRestoreNodes.size() - 1;
constexpr auto FalcoAfterWaitKey = (std::uint64_t{PhaseHash(FalcoMessages)} << 32) | FalcoAfterWait.node;
constexpr auto RestoreLimit = std::chrono::seconds(25);

using GameWaitLifecycle = void (*)(void*, void*);
GameWaitLifecycle uninitializeGameWaitOriginal{};
GameWaitLifecycle initializeGameWaitOriginal{};
void (*removeConditionOriginal)(void*, std::uint32_t, void*){};
GameTimeFactory makeGameTimerOriginal{};
void (*notifyQuestOriginal)(void*, std::uint32_t){};
std::uint32_t (*allocateQuestSlotOriginal)(void*, std::uint64_t, const std::uint64_t*){};
void (*worldUpdateOriginal)(void*, void*){};

enum class HandoffStage { Retiring, NeedPermit, Phases, World, Confirm, Rollback, Cancelled };

// Holds only one retained-session handoff. All state is under boundaryMutex,
// except the small native notification ingress and the TLS of the quest job.
struct LiveHandoff
{
    Boundary cutoff;
    FalcoRestorePlan plan;
    PrefabLeaseBinding oldPrefabs;
    RetainedQuestRestore questsRestore;
    std::optional<SaveGuard::HandoffPermit> permit;
    GameTimeRestoreOwner newTimer;
    std::optional<GameTimeRestoreReceipt> timerReceipt;
    std::optional<WorldPrefabSupport> worldSupport;
    void* timeSystem{};
    const void* originalFalcoPhase{};
    const void* nextFalcoHandler{};
    std::uint32_t nextFalcoSlot{};
    std::uint32_t createdTimer{};
    HandoffStage stage{HandoffStage::Retiring};
    Monotonic::time_point deadline{};
    const char* failure{};
    std::uint8_t cleanRetirementPasses{};
    bool retired{};
    bool expired{};
    bool retiredClock{};
    bool freshClock{};
};

std::optional<LiveHandoff> liveHandoff;
std::atomic<const void*> originalFalcoHandler{};
std::atomic<const void*> watchedFalcoPhase{};
RestoreNotifications restoreNotifications;
thread_local LiveHandoff* installingHandler{};
thread_local std::optional<std::size_t> installingIndex;
thread_local bool enrolledHandler{};

void* LiveQuests(const LiveHandoff& handoff) { return const_cast<void*>(handoff.cutoff.quests); }

auto ReadHandoffFact(const LiveHandoff& handoff)
{
    return [facts = handoff.cutoff.facts](std::string_view name) { return FactValue(facts, name); };
}

bool SameHandoffOwners(const LiveHandoff& handoff, const void* quests)
{
    return quests == handoff.cutoff.quests && Is(quests, QuestSystem) && Is(handoff.cutoff.facts, FactsManager) &&
           Read<const void*>(quests, 0xF8) == handoff.cutoff.facts &&
           Read<const void*>(quests, 0x100) == handoff.oldPrefabs.loader;
}

GameTimeRestoreMethods NativeGameTimeMethods()
{
    return {image + GameTimeHandler, image + GameTimerRecord, image + NewGameTimerCallback,
            image + LoadedGameTimerCallback, At<decltype(GameTimeRestoreMethods::readMapping)>(0x194AC4)};
}

void ResetLiveHandoff()
{
    originalFalcoHandler.store(nullptr);
    watchedFalcoPhase.store(nullptr);
    restoreNotifications.Discard();
    if (liveHandoff)
    {
        liveHandoff->questsRestore.Forget();
        liveHandoff.reset();
    }
}

SaveGuard::HandoffPermit BeforeLiveTransition(void* quests)
{
    if (!liveHandoff)
        return {};
    if (!gate.Transitioning() && SameHandoffOwners(*liveHandoff, quests))
    {
        // The native transition owns destruction of any adopted phases. Release
        // transient prep references while the owning cache is still valid.
        liveHandoff->questsRestore.ReleaseUnadopted(quests);
    }
    return liveHandoff->permit ? std::move(*liveHandoff->permit) : SaveGuard::HandoffPermit{};
}

const void* FindCapturedPhase(const Capture& capture, std::size_t index)
{
    const auto& expected = FalcoPhases[index];
    const auto found = std::ranges::find_if(capture.phases, [&](const LivePhase& row) {
        return row.record.depot == expected.depot && std::ranges::equal(row.record.Path(), expected.address);
    });
    return found == capture.phases.end() ? nullptr : found->instance;
}

void ArmLiveHandoff(void* quests, void* timeSystem, const Capture& capture, std::int32_t ticket, std::int32_t route)
{
    if (route != 1 || !Is(timeSystem, TimeSystem))
        return;
    const auto plan = PlanFalcoRestore(capture.state);
    if (!plan)
    {
        sdk->logger->Info(plugin, "PTFR Step 3 Over the Edge: capture did not match the pending Falco stage");
        return;
    }
    const std::unique_lock lifetime(boundaryMutex, std::try_to_lock);
    if (!lifetime || liveHandoff || gate.Transitioning() || gate.Epoch() != capture.epoch ||
        !Is(quests, QuestSystem) || notificationPasses)
        return;
    const std::unique_lock graph(LockAt(quests, 0x60), std::try_to_lock);
    if (!graph)
        return;
    const Boundary cutoff{quests, Read<const void*>(quests, 0xF8), ticket, route};
    if (!gate.Matches(cutoff) || !OpenFacts(cutoff) || FactValue(cutoff.facts, "mq049_started") != 1 ||
        FactValue(cutoff.facts, "mq049_falco_done") != 0)
        return;

    Capture current(false);
    if (!ReadPhases(current, quests) || !ReadHandlers(current, quests, false))
        return;
    const auto selected = std::ranges::find_if(current.waits, [&](const Wait& w) {
        return w.slot == plan->falcoWait.slot && w.timer == plan->falcoWait.serial && w.clock == Clock::Game &&
               ((std::uint64_t{w.registration.phase} << 32) | w.registration.node) == FalcoTimerNodeKey;
    });
    const auto* phase = FindCapturedPhase(current, FalcoParent);
    const auto* owner = FindCapturedPhase(current, FalcoParent - 1);
    const auto* falcoPhase = FindCapturedPhase(current, FalcoAfterWait.phase);
    const auto* handler = owner ? At<const void* (*)(const void*, std::uint32_t)>(0x2B1B64)(owner, 64) : nullptr;
    if (selected == current.waits.end() || !phase || !falcoPhase || !Is(handler, QuestPhaseHandlerType))
        return;
    auto* loader = Read<void*>(quests, 0x100);
    const auto leases = ReadPrefabLeaseBinding(loader, image + PrefabLoaderType,
        {Read<std::uint32_t>(phase, 0x84), Read<std::uint32_t>(handler, 0x54)});
    if (!leases)
    {
        sdk->logger->Info(plugin, "PTFR Step 3 Over the Edge: original prefab lease capture deferred");
        return;
    }

    auto& handoff = liveHandoff.emplace();
    handoff.cutoff = cutoff;
    handoff.plan = *plan;
    handoff.oldPrefabs = *leases;
    handoff.timeSystem = timeSystem;
    handoff.originalFalcoPhase = falcoPhase;
    if (!handoff.questsRestore.Prepare(image, quests, *plan))
    {
        handoff.questsRestore.Rollback(quests);
        ResetLiveHandoff();
        sdk->logger->Info(plugin, "PTFR Step 3 Over the Edge: original resident resource capture deferred");
        return;
    }
    originalFalcoHandler.store(selected->handler);
    sdk->logger->InfoF(plugin, "PTFR Step 3 Over the Edge: cutoff selected ticket=%d remaining=%u original timer=%u",
                      ticket, static_cast<std::uint32_t>(plan->falcoWait.remainingSeconds),
                      static_cast<std::uint32_t>(plan->falcoWait.serial));
}

void ObserveUninitializeGameWait(void* handler, void* context)
{
    if (handler != originalFalcoHandler.load())
    {
        uninitializeGameWaitOriginal(handler, context);
        return;
    }
    const std::lock_guard lifetime(boundaryMutex);
    const auto* quests = Read<const void*>(context, 0x18);
    const auto nominated = liveHandoff && handler == originalFalcoHandler.load() &&
                           SameHandoffOwners(*liveHandoff, quests);
    bool retiring{};
    bool expiring{};
    if (nominated)
    {
        auto& handoff = *liveHandoff;
        const auto fact = ReadHandoffFact(handoff);
        const bool sameWait = !gate.Transitioning() && MatchingReedCutoff(handoff.cutoff.ticket, fact) &&
                              fact("mq049_started") == 1 && fact("mq049_falco_done") == 0 &&
                              Read<std::uint64_t>(handler, 0x38) == FalcoTimerNodeKey &&
                              Read<std::uint32_t>(handler, 0x40) == handoff.plan.falcoWait.serial &&
                              Read<void*>(context, 0xE8) == handoff.timeSystem;
        const auto killed = fact("q307_main_game_killed");
        const bool ready = Ready(handler);
        retiring = sameWait && killed == 1 && !ready;
        expiring = sameWait && killed == 0 && ready;
    }
    uninitializeGameWaitOriginal(handler, context);
    if (nominated)
    {
        auto& handoff = *liveHandoff;
        originalFalcoHandler.store(nullptr);
        std::uint64_t oldMapping{};
        const bool released = Read<std::uint32_t>(handler, 0x30) == 0 &&
                              !NativeGameTimeMethods().readMapping(quests, FalcoTimerNodeKey, &oldMapping);
        handoff.retired = retiring && released;
        handoff.expired = expiring && released;
        if (!handoff.retired && !handoff.expired)
            handoff.failure = "origination changed before native cleanup";
    }
}

void* FindQuestHandler(const void* phase, std::uint32_t node)
{
    return At<void* (*)(const void*, std::uint32_t)>(0x2B1B64)(phase, node);
}

void ObserveRemoveCondition(void* phase, std::uint32_t node, void* context)
{
    if (node != FalcoAfterWait.node || phase != watchedFalcoPhase.load())
    {
        removeConditionOriginal(phase, node, context);
        return;
    }
    const std::lock_guard lifetime(boundaryMutex);
    if (!liveHandoff || phase != watchedFalcoPhase.load())
    {
        removeConditionOriginal(phase, node, context);
        return;
    }

    auto& handoff = *liveHandoff;
    const auto fact = ReadHandoffFact(handoff);
    const auto* active = FindQuestHandler(phase, node);
    const bool retiring = active && active == handoff.nextFalcoHandler && !Ready(active) &&
                          !gate.Transitioning() && MatchingReedCutoff(handoff.cutoff.ticket, fact) &&
                          SameHandoffOwners(handoff, Read<const void*>(context, 0x128)) &&
                          fact("q307_main_game_killed") == 1 && fact("mq049_falco_done") == 0;
    watchedFalcoPhase.store(nullptr);
    removeConditionOriginal(phase, node, context);
    handoff.retired = retiring && !FindQuestHandler(phase, node);
    if (!handoff.retired)
        handoff.failure = "Falco's follow-up condition changed before native cleanup";
}

std::uint32_t AllocateRestoreSlot(void* events, std::uint64_t type, const std::uint64_t* key)
{
    const auto slot = allocateQuestSlotOriginal(events, type, key);
    if (installingHandler && installingIndex && key)
    {
        const auto& node = installingHandler->questsRestore.Node(*installingIndex);
        const auto expected = (std::uint64_t{PhaseHash(FalcoPhases[node.phase].address)} << 32) | node.node;
        if (*key == expected && type == node.type && events == Read<const void*>(installingHandler->cutoff.quests, 0xE8))
            enrolledHandler = restoreNotifications.Watch(installingHandler->cutoff.quests, slot);
    }
    return slot;
}

void NotifyQuest(void* quests, std::uint32_t slot)
{
    if (!restoreNotifications.Intercept(quests, slot))
        notifyQuestOriginal(quests, slot);
}

void InitializeRestoredGameWait(void* handler, void* context)
{
    if (!installingHandler || installingIndex != FalcoHandlerIndex ||
        Read<std::uint64_t>(handler, 0x38) != FalcoTimerNodeKey)
    {
        initializeGameWaitOriginal(handler, context);
        return;
    }
    auto& handoff = *installingHandler;
    handoff.newTimer = {handoff.cutoff.quests, handoff.timeSystem, handler, FalcoTimerNodeKey,
                        static_cast<std::uint32_t>(handoff.plan.falcoWait.serial), FalcoDuration};
    if (!enrolledHandler || !handoff.permit)
        return;
    GameTimeRestoreScope restore(*handoff.permit, NativeGameTimeMethods(), handoff.newTimer, context,
                                 {static_cast<std::uint32_t>(handoff.plan.falcoWait.remainingSeconds)});
    if (!restore)
        return;
    initializeGameWaitOriginal(handler, context);
    handoff.createdTimer = Read<std::uint32_t>(handler, 0x40);
    handoff.timerReceipt = restore.Mapped();
}

ptfr::NativeGameTimerReference* MakeRestoredGameTimer(ptfr::NativeGameTimerReference* out, const std::uint32_t* id,
    void* callback, const std::uint32_t* deadline, const std::uint32_t* repeats, const std::uint8_t* mode,
    const std::uint32_t* authored, const std::uint64_t* label, const std::uint64_t* source)
{
    return GameTimeRestoreScope::MakeTimer(makeGameTimerOriginal, out, id, callback, deadline,
                                          repeats, mode, authored, label, source);
}

void OnLiveSavePoll(const void* session)
{
    const std::unique_lock lifetime(boundaryMutex, std::try_to_lock);
    if (!lifetime || !liveHandoff || gate.Transitioning() || !Is(session, SaveSessionVtable) ||
        liveHandoff->stage != HandoffStage::NeedPermit || liveHandoff->permit)
        return;
    auto permit = TryBeginNativeHandoff(session);
    if (permit)
        liveHandoff->permit.emplace(std::move(permit));
}

void OnLiveClockLocked(void* timeSystem)
{
    if (!liveHandoff || gate.Transitioning() || liveHandoff->timeSystem != timeSystem)
        return;
    auto& handoff = *liveHandoff;
    if (handoff.stage == HandoffStage::Retiring && (handoff.retired || handoff.expired) && !handoff.retiredClock)
    {
        const auto old = ptfr::FindGameTimer(timeSystem, static_cast<std::uint32_t>(handoff.plan.falcoWait.serial));
        handoff.retiredClock = old && !old->timer;
    }
    if (handoff.stage == HandoffStage::Confirm && handoff.timerReceipt)
    {
        std::uint32_t clock{};
        At<void* (*)(void*, std::uint32_t*)>(0x468358)(timeSystem, &clock);
        handoff.freshClock = handoff.timerReceipt->OnClock(NativeGameTimeMethods(), handoff.newTimer, clock);
    }
    if (handoff.stage == HandoffStage::Cancelled && handoff.createdTimer)
    {
        const auto timer = ptfr::FindGameTimer(timeSystem, handoff.createdTimer);
        if (timer && !timer->timer)
            handoff.createdTimer = 0;
    }
}

void ObserveWorldUpdate(void* receiver, void* job)
{
    worldUpdateOriginal(receiver, job);
    const std::unique_lock lifetime(boundaryMutex, std::try_to_lock);
    if (!lifetime || !liveHandoff || gate.Transitioning() ||
        (liveHandoff->stage != HandoffStage::World && liveHandoff->stage != HandoffStage::Confirm))
        return;
    auto& handoff = *liveHandoff;
    const WorldPrefabMethods methods{image + WorldStreamingType, image + WorldStreamingUpdateType,
        At<decltype(WorldPrefabMethods::find)>(WorldPrefabIndexLookup),
        At<decltype(WorldPrefabMethods::desired)>(WorldPrefabDesired)};
    handoff.worldSupport = ReadWorldPrefabSupport(receiver, handoff.oldPrefabs.world, handoff.oldPrefabs.refs, methods);
}

bool OldRowsQuiet(void* quests, const LiveHandoff& handoff)
{
    const auto* events = Read<const void*>(quests, 0xE8);
    if (!events)
        return false;
    const auto slots = ArrayAt<Registration>(events, 8, MaxSlots);
    if (!slots || std::ranges::any_of(*slots, [](const Registration& entry) {
        const auto key = (std::uint64_t{entry.phase} << 32) | entry.node;
        if (key == FalcoAfterWaitKey)
            return true;
        for (std::size_t i = 0; i < FalcoRestoreNodes.size(); ++i)
        {
            if (key == RestoreNodeKey(i))
                return true;
        }
        return false;
    }))
        return false;
    const std::unique_lock queue(LockAt(quests, 0x150), std::try_to_lock);
    if (!queue)
        return false;
    const auto slotsPending = ArrayAt<std::uint32_t>(quests, 0x158, MaxQueue);
    return slotsPending && (!handoff.nextFalcoHandler ||
           std::ranges::find(*slotsPending, handoff.nextFalcoSlot) == slotsPending->end()) &&
           std::ranges::none_of(handoff.plan.paths, [&](const RestorePath& path) {
        return std::ranges::find(*slotsPending, path.retiredSlot) != slotsPending->end();
    });
}

void FinishRollback(void* quests, LiveHandoff& handoff)
{
    if (handoff.stage != HandoffStage::Cancelled)
    {
        if (!handoff.questsRestore.Rollback(quests))
            return;
        handoff.stage = HandoffStage::Cancelled;
        if (handoff.createdTimer)
            return;
    }
    if (handoff.createdTimer)
        return;
    sdk->logger->WarnF(plugin, "PTFR Step 3 Over the Edge: restore deferred (%s)", handoff.failure);
    ResetLiveHandoff();
}

bool InstallSelectedHandlers(void* quests, LiveHandoff& handoff)
{
    if (!restoreNotifications.Begin(quests))
        return false;
    installingHandler = &handoff;
    bool installedAll = true;
    for (std::size_t i = 0; i < FalcoRestoreNodes.size(); ++i)
    {
        installingIndex = i;
        enrolledHandler = false;
        if (!handoff.questsRestore.CreateHandler(quests, i) || !enrolledHandler)
        {
            installedAll = false;
            break;
        }
    }
    installingIndex.reset();
    installingHandler = nullptr;
    return installedAll && (handoff.expired ? !handoff.timerReceipt && !handoff.createdTimer :
               handoff.timerReceipt && handoff.timerReceipt->id != handoff.plan.falcoWait.serial);
}

void WatchPendingFalcoCondition(void* quests, LiveHandoff& handoff)
{
    Capture capture(false);
    if (!ReadPhases(capture, quests) || !ReadHandlers(capture, quests, true) ||
        !CopyQueues(capture.state, quests) || !CopyInstances(capture.state, quests))
        return;
    const auto& state = capture.state;
    const auto body = std::span(FalcoPhases).subspan(FalcoParent);
    const auto inBody = [body](std::uint32_t hash) {
        return std::ranges::any_of(body, [hash](const RestorePhase& phase) { return PhaseHash(phase.address) == hash; });
    };
    if (std::ranges::count_if(state.handlers, [&](const Handler& row) { return inBody(row.registration.phase); }) != 5 ||
        std::ranges::any_of(state.instances, [&](const NodeInstance& row) {
            return inBody(static_cast<std::uint32_t>(row.key >> 32));
        }) ||
        std::ranges::any_of(state.resourceRequests, [body](std::uint64_t depot) {
            return std::ranges::find(body, depot, &RestorePhase::depot) != body.end();
        }))
        return;

    const auto* phase = FindCapturedPhase(capture, FalcoAfterWait.phase);
    if (!phase || phase != handoff.originalFalcoPhase)
        return;
    const auto* active = FindQuestHandler(phase, FalcoAfterWait.node);
    if (!active || Ready(active))
        return;
    const auto slot = Read<std::uint32_t>(active, 0x28);
    for (std::size_t i = 0; i < handoff.plan.paths.size(); ++i)
    {
        const bool followUp = i == FalcoHandlerIndex;
        const auto& node = followUp ? FalcoAfterWait : FalcoRestoreNodes[i];
        const auto key = followUp ? FalcoAfterWaitKey : RestoreNodeKey(i);
        const auto physicalSlot = followUp ? slot : handoff.plan.paths[i].retiredSlot;
        const auto hasKey = [key](const Handler& row) {
            return ((std::uint64_t{row.registration.phase} << 32) | row.registration.node) == key;
        };
        const auto row = std::ranges::find_if(state.handlers, hasKey);
        if (row == state.handlers.end() || row->registration.type != node.type || row->binding != Binding::Live ||
            row->slot != physicalSlot || std::ranges::count_if(state.handlers, hasKey) != 1 ||
            std::ranges::find(state.notifications, physicalSlot) != state.notifications.end())
            return;
    }

    const auto get = At<std::int32_t (*)(const void*, std::uint32_t, std::uint32_t)>(0x2B2270);
    if (get(handoff.cutoff.facts, 4, FalcoJoinKey) != 0 ||
        get(handoff.cutoff.facts, 5, ReyesChoiceKey) != handoff.plan.reyesChoice.value ||
        !handoff.questsRestore.SelectElapsedWait(quests, phase, active, slot))
        return;

    handoff.nextFalcoHandler = active;
    handoff.nextFalcoSlot = slot;
    watchedFalcoPhase.store(phase);
    sdk->logger->Info(plugin, "PTFR Step 3 Over the Edge: stock wait elapsed, following the pending Falco condition");
}

bool LogicalStateCanRestore(const LiveHandoff& handoff)
{
    const auto get = At<std::int32_t (*)(const void*, std::uint32_t, std::uint32_t)>(0x2B2270);
    const auto readyChoice = get(handoff.cutoff.facts, 5, handoff.plan.reyesChoice.key);
    return get(handoff.cutoff.facts, 4, FalcoJoinKey) == 0 &&
           (readyChoice == 0 || readyChoice == handoff.plan.reyesChoice.value);
}

bool LivePrefabsReady(void* quests, const LiveHandoff& handoff)
{
    if (!handoff.worldSupport || !handoff.worldSupport->Ready())
        return false;
    const auto* phase = handoff.questsRestore.Phase(quests, FalcoParent);
    return phase && ReadPrefabLeaseBinding(Read<void*>(quests, 0x100), image + PrefabLoaderType,
        {Read<std::uint32_t>(phase, 0x84), 0}, handoff.oldPrefabs).has_value();
}

void OnLiveQuestDrain(void* quests)
{
    const std::unique_lock lifetime(boundaryMutex, std::try_to_lock);
    if (!lifetime || !liveHandoff || gate.Transitioning() || notificationPasses || !SameHandoffOwners(*liveHandoff, quests))
        return;
    const std::unique_lock graph(LockAt(quests, 0x60), std::try_to_lock);
    if (!graph)
        return;
    auto& handoff = *liveHandoff;
    const auto fact = ReadHandoffFact(handoff);
    const auto now = Monotonic::now();
    if (handoff.stage == HandoffStage::Retiring)
    {
        const bool completion = GenuineTowerCompletion(handoff.cutoff.ticket, fact);
        if (fact("PTFRHS3_GateOpen") == 0 && !MatchingReedCutoff(handoff.cutoff.ticket, fact))
            handoff.failure = "the native cutoff did not commit";
        if (!handoff.failure && handoff.expired && !handoff.nextFalcoHandler && fact("q307_main_game_killed") == 0)
            WatchPendingFalcoCondition(quests, handoff);
        if (completion && handoff.expired && !handoff.retired)
            handoff.failure = "the pending Falco condition did not retire at native cleanup";
        if (completion && handoff.deadline == Monotonic::time_point{})
            handoff.deadline = now + RestoreLimit;
        if (completion && handoff.retired && handoff.retiredClock && OldRowsQuiet(quests, handoff) &&
            ReadPrefabRetirement(Read<void*>(quests, 0x100), image + PrefabLoaderType, handoff.oldPrefabs))
        {
            // The end of the next stock pass clears any batch copied before
            // the retirement observations, including old physical slot IDs.
            if (++handoff.cleanRetirementPasses >= 2)
                handoff.stage = HandoffStage::NeedPermit;
        }
        else
            handoff.cleanRetirementPasses = 0;
    }

    if (handoff.stage >= HandoffStage::NeedPermit && handoff.stage < HandoffStage::Rollback &&
        (!GenuineTowerCompletion(handoff.cutoff.ticket, fact) || fact("mq049_started") != 1 ||
         fact("mq049_falco_done") != 0 || !LogicalStateCanRestore(handoff)))
        handoff.failure = "the retained quest or ending state changed";
    if (!handoff.failure && handoff.stage < HandoffStage::Rollback &&
        handoff.deadline != Monotonic::time_point{} && now >= handoff.deadline)
        handoff.failure = handoff.stage == HandoffStage::World ? "streamed supports did not settle" :
                          handoff.stage == HandoffStage::Confirm ? "the replacement owner did not settle" :
                          "retired ownership or save admission did not settle";

    if (handoff.failure || handoff.stage >= HandoffStage::Rollback)
    {
        if (handoff.stage != HandoffStage::Cancelled)
            handoff.stage = HandoffStage::Rollback;
        FinishRollback(quests, handoff);
        return;
    }

    if (handoff.stage == HandoffStage::NeedPermit && handoff.permit)
    {
        handoff.stage = HandoffStage::Phases;
        if (!OldRowsQuiet(quests, handoff) || !handoff.questsRestore.CreatePhases(quests))
            handoff.failure = "the native phase creation did not qualify";
        else
        {
            handoff.stage = HandoffStage::World;
            handoff.deadline = now + RestoreLimit;
            sdk->logger->Info(plugin, "PTFR Step 3 Over the Edge: original phases rebuilt, waiting for the streamed prefabs");
        }
    }

    if (handoff.stage == HandoffStage::World && LivePrefabsReady(quests, handoff))
    {
        if (!InstallSelectedHandlers(quests, handoff))
            handoff.failure = "the selected native handler initialization did not qualify";
        else
        {
            handoff.stage = HandoffStage::Confirm;
            handoff.worldSupport.reset();
            handoff.deadline = now + RestoreLimit;
        }
    }

    if (handoff.stage == HandoffStage::Confirm &&
        (handoff.expired || (handoff.freshClock && handoff.timerReceipt)) && LivePrefabsReady(quests, handoff))
    {
        std::uint64_t mapped{};
        const auto* handler = handoff.questsRestore.Handler(quests, FalcoHandlerIndex);
        const bool hasTimer = NativeGameTimeMethods().readMapping(quests, FalcoTimerNodeKey, &mapped);
        if (!handler || (handoff.expired ? hasTimer : handler != handoff.newTimer.handler || Ready(handler) ||
                         !hasTimer || mapped != handoff.timerReceipt->id))
        {
            handoff.failure = "the replacement owner changed before commit";
            return;
        }
        const auto get = At<std::int32_t (*)(const void*, std::uint32_t, std::uint32_t)>(0x2B2270);
        const auto set = At<void (*)(const void*, std::uint32_t, std::uint32_t, std::int32_t)>(0x350E50);
        const auto key = handoff.plan.reyesChoice.key;
        const auto previousChoice = get(handoff.cutoff.facts, 5, key);
        if (previousChoice == 0)
            set(handoff.cutoff.facts, 5, key, handoff.plan.reyesChoice.value);
        if (get(handoff.cutoff.facts, 5, key) != handoff.plan.reyesChoice.value || !handoff.questsRestore.Commit())
        {
            if (previousChoice == 0)
                set(handoff.cutoff.facts, 5, key, previousChoice);
            handoff.failure = "native branch selection or resource commit did not verify";
            return;
        }
        restoreNotifications.Finish(quests, [quests](std::uint32_t slot) { notifyQuestOriginal(quests, slot); });
        if (handoff.expired)
            sdk->logger->InfoF(plugin, "PTFR Step 3 Over the Edge: handoff committed ticket=%d after natural wait expiry",
                              handoff.cutoff.ticket);
        else
            sdk->logger->InfoF(plugin, "PTFR Step 3 Over the Edge: handoff committed ticket=%d remaining=%u native timer=%u deadline=%u",
                              handoff.cutoff.ticket, static_cast<std::uint32_t>(handoff.plan.falcoWait.remainingSeconds),
                              handoff.timerReceipt->id, handoff.timerReceipt->deadline);
        ResetLiveHandoff();
    }
}
