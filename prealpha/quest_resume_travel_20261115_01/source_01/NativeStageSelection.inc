constexpr auto PrefabLoaderType = 0x306F8C0U;
constexpr auto PhaseHandlerType = 0x3046748U;
constexpr auto CassiusBridgeName = "PTFR.HistorySnapshotHS1.CassiusResumeBridge";
constexpr auto RestoreLimit = std::chrono::seconds(30);
constexpr auto CollectionIndex = CassiusNodes.size() - 1;
constexpr std::array SupportPhases{std::size_t{3}, CassiusCollection.body};
constexpr auto CassiusServicePath = std::to_array<std::uint16_t>({1, 32493, 5});
constexpr auto CassiusServiceDepot = Depot(R"(towercontinued\b0_story_services\cassius.questphase)");

void (*removeConditionOriginal)(void*, std::uint32_t, void*){};
void (*notifyQuestOriginal)(void*, std::uint32_t){};
std::uint32_t (*allocateQuestSlotOriginal)(void*, std::uint64_t, const std::uint64_t*){};
void (*worldUpdateOriginal)(void*, void*){};

struct SupportBinding
{
    const void* original{};
    PrefabLeaseBinding lease{};
    std::optional<WorldPrefabSupport> observed;
};

struct LiveHandoff
{
    Boundary cutoff;
    RestorePlan plan;
    RetainedQuestRestore restore;
    std::array<SupportBinding, SupportPhases.size()> supports{};
    CassiusJournalEdit journalEdit;
    std::optional<CassiusJournal> journal;
    std::optional<SaveGuard::HandoffPermit> permit;
    CassiusPhase phase{CassiusPhase::Retiring};
    Monotonic::time_point deadline{};
    Monotonic::time_point journalSampled{};
    const void* originalListener{};
    const char* failure{};
    unsigned quietPasses{};
    unsigned rollbackPasses{};
    bool retired{};
    bool graphUndone{};
    bool notificationsArmed{};
    bool ownerReceipt{};
};

std::optional<LiveHandoff> liveHandoff;
std::atomic<const void*> watchedCollectionPhase{};
RestoreNotifications restoreNotifications;
thread_local LiveHandoff* installing{};
thread_local const RestoreNode* installingNode{};
thread_local bool enrolled{};

auto HandoffFacts(const LiveHandoff& handoff)
{
    return [facts = handoff.cutoff.facts](std::string_view name) { return FactValue(facts, name); };
}

bool SameHandoff(const LiveHandoff& handoff, const void* quests)
{
    return quests == handoff.cutoff.quests && Is(quests, QuestSystem) &&
           Is(handoff.cutoff.facts, FactsManager) && Read<const void*>(quests, 0xF8) == handoff.cutoff.facts &&
           Read<const void*>(quests, 0x100) == handoff.supports.back().lease.loader;
}

void ResetLiveHandoff()
{
    watchedCollectionPhase.store(nullptr);
    restoreNotifications.Discard();
    if (liveHandoff)
        liveHandoff->restore.Forget();
    liveHandoff.reset();
}

SaveGuard::HandoffPermit BeforeLiveTransition(void* quests)
{
    if (!liveHandoff)
        return {};
    if (!gate.Transitioning() && SameHandoff(*liveHandoff, quests))
        liveHandoff->restore.ReleaseUnadopted(quests);
    return liveHandoff->permit ? std::move(*liveHandoff->permit) : SaveGuard::HandoffPermit{};
}

void* FindQuestHandler(const void* phase, std::uint32_t node)
{
    return At<void* (*)(const void*, std::uint32_t)>(0x2B1B64)(phase, node);
}

// A missing child is valid after cleanup. Ambiguous phase paths and
// unreadable trees defer both native restore and legacy permit issuance.
std::optional<const void*> FindPhase(const void* quests, std::span<const std::uint16_t> address)
{
    const auto* root = Read<const void*>(quests, 0x68);
    if (!Is(root, SyntheticRoot) || address.empty())
        return std::nullopt;
    const auto roots = ArrayAt<HandleRow>(root, 0x88, 64);
    if (!roots || address.front() >= roots->size())
        return std::nullopt;
    const void* phase = (*roots)[address.front()].instance;
    for (std::size_t count = 1; phase && count <= address.size(); ++count)
    {
        if (!Is(phase, PhaseInstance))
            return std::nullopt;
        const auto prefix = address.first(count);
        const auto actual = ArrayAt<std::uint16_t>(phase, 0x70, MaxDepth);
        if (!actual || !std::ranges::equal(*actual, prefix) || Read<std::uint32_t>(phase, 0x80) != PhaseHash(prefix))
            return std::nullopt;
        if (count == address.size())
            return phase;
        const auto children = ArrayAt<HandleRow>(phase, 0x88, MaxPhases);
        if (!children)
            return std::nullopt;
        phase = nullptr;
        const auto childHash = PhaseHash(address.first(count + 1));
        for (const auto& child : *children)
        {
            if (!Is(child.instance, PhaseInstance))
                return std::nullopt;
            if (Read<std::uint32_t>(child.instance, 0x80) == childHash)
            {
                if (phase)
                    return std::nullopt;
                phase = child.instance;
            }
        }
    }
    return nullptr;
}

bool PrivatePathsIdle(const void* quests)
{
    for (const auto path : {std::span<const std::uint16_t>(CassiusS22), std::span<const std::uint16_t>(CassiusS24)})
    {
        const auto phase = FindPhase(quests, path);
        if (!phase)
            return false;
        if (!*phase)
            continue;
        const auto children = ArrayAt<HandleRow>(*phase, 0x88, MaxPhases);
        const auto count = Read<std::uint32_t>(*phase, 0xA0);
        const auto pending = path.back() == CassiusS22.back() ? 1001U : 1002U;
        const auto* wait = FindQuestHandler(*phase, pending);
        if (!children || !children->empty() || count != (wait ? 1U : 0U) || (wait && Ready(wait)))
            return false;
    }
    return true;
}

template<typename ReadFact>
bool CassiusServiceReady(const void* quests, ReadFact fact)
{
    if (!VendorAvailable(fact))
        return false;
    const auto owner = FindPhase(quests, std::span(CassiusServicePath).first(2));
    const auto active = FindPhase(quests, CassiusServicePath);
    if (!owner || !*owner || PhaseDepot(*owner) != CassiusServiceDepot || !active || !*active)
        return false;
    return Is(FindQuestHandler(*owner, 5), PhaseHandlerType);
}

bool QueuesQuiet(void* quests, const RestorePlan& plan)
{
    const std::unique_lock lock(LockAt(quests, 0x150), std::try_to_lock);
    const auto slots = lock ? ArrayAt<std::uint32_t>(quests, 0x158, MaxQueue) : std::nullopt;
    return slots && std::ranges::none_of(plan.RetiredSlots(), [&](std::uint32_t slot) {
        return std::ranges::find(*slots, slot) != slots->end();
    });
}

std::optional<SupportBinding> ObserveOriginalSupport(void* quests, const StageSpec& stage, std::size_t index)
{
    const auto phase = FindPhase(quests, stage.phases[index].address);
    const auto parent = FindPhase(quests, stage.phases[stage.phases[index].parent].address);
    const auto* handler = parent && *parent ? FindQuestHandler(*parent, stage.phases[index].address.back()) : nullptr;
    if (!phase || !*phase || !Is(handler, PhaseHandlerType))
        return std::nullopt;
    auto* loader = Read<void*>(quests, 0x100);
    const auto lease = ReadPrefabLeaseBinding(loader, image + PrefabLoaderType,
        {Read<std::uint32_t>(*phase, 0x84), Read<std::uint32_t>(handler, 0x54)});
    return lease ? std::optional(SupportBinding{*phase, *lease, {}}) : std::nullopt;
}

void ArmCassiusHandoff(void* quests, const Capture& capture, std::int32_t ticket, std::int32_t route,
                       const CassiusJournal& journal)
{
    if (!handoffScriptsReady || route != 1 || !journal.WasPending())
        return;
    const std::unique_lock lifetime(boundaryMutex, std::try_to_lock);
    if (!lifetime || liveHandoff || gate.Transitioning() || notificationPasses ||
        gate.Epoch() != capture.epoch || !Is(quests, QuestSystem))
        return;
    const std::unique_lock graph(LockAt(quests, 0x60), std::try_to_lock);
    if (!graph)
        return;
    const Boundary cutoff{quests, Read<const void*>(quests, 0xF8), ticket, route};
    if (!gate.Matches(cutoff) || !OpenFacts(cutoff))
        return;
    const auto fact = [facts = cutoff.facts](std::string_view name) { return FactValue(facts, name); };
    const auto plan = SelectResumeStage(capture.state, route, fact);
    if (!plan || !CassiusMayClaim(fact) || !PrivatePathsIdle(quests) || !QueuesQuiet(quests, *plan))
        return;
    const auto body = FindPhase(quests, CassiusPath);
    const auto observed = std::ranges::find_if(capture.phases, [](const LivePhase& phase) {
        return std::ranges::equal(phase.record.Path(), CassiusPath);
    });
    if (!body || !*body || observed == capture.phases.end() || *body != observed->instance)
        return;
    const auto* listener = FindQuestHandler(*body, CassiusNodes.back().node);
    if (!listener || Ready(listener))
        return;

    std::array<SupportBinding, SupportPhases.size()> supports{};
    for (std::size_t i = 0; i < SupportPhases.size(); ++i)
    {
        const auto support = ObserveOriginalSupport(quests, *plan->stage, SupportPhases[i]);
        if (!support)
        {
            sdk->logger->Info(plugin, "PTFR Cassius handoff deferred: original prefab lease unverified");
            return;
        }
        supports[i] = *support;
    }
    auto& handoff = liveHandoff.emplace();
    handoff.cutoff = cutoff;
    handoff.plan = *plan;
    handoff.supports = supports;
    handoff.originalListener = listener;
    if (!handoff.restore.Prepare(RetainedQuestMethods::FromImage(image), quests, *plan))
    {
        handoff.failure = "original resources unavailable";
        handoff.phase = CassiusPhase::Aborting;
        return;
    }
    watchedCollectionPhase.store(*body);
    sdk->logger->InfoF(plugin, "PTFR Cassius handoff reserved at Reed cutoff ticket=%d", ticket);
}

void ObserveRemoveCondition(void* phase, std::uint32_t node, void* context)
{
    if (node != CassiusNodes.back().node || phase != watchedCollectionPhase.load())
    {
        removeConditionOriginal(phase, node, context);
        return;
    }
    const std::lock_guard lock(boundaryMutex);
    if (!liveHandoff || phase != watchedCollectionPhase.load())
    {
        removeConditionOriginal(phase, node, context);
        return;
    }
    auto& handoff = *liveHandoff;
    const auto fact = HandoffFacts(handoff);
    const auto* listener = FindQuestHandler(phase, node);
    const bool retiring = handoff.phase == CassiusPhase::Retiring && listener && listener == handoff.originalListener &&
                          !Ready(listener) && !gate.Transitioning() && context &&
                          SameHandoff(handoff, Read<const void*>(context, 0x128)) &&
                          MatchingReedCutoff(handoff.cutoff.ticket, fact) &&
                          fact("q307_main_game_killed") == 1 && CassiusMayClaim(fact);
    watchedCollectionPhase.store(nullptr);
    removeConditionOriginal(phase, node, context);
    handoff.retired = retiring && !FindQuestHandler(phase, node);
    if (!handoff.retired)
        handoff.failure = "original inventory listener changed before Tower retirement";
}

std::uint32_t AllocateRestoreSlot(void* events, std::uint64_t type, const std::uint64_t* key)
{
    const auto slot = allocateQuestSlotOriginal(events, type, key);
    if (installing && installingNode && key && events == Read<const void*>(installing->cutoff.quests, 0xE8))
    {
        const auto& node = *installingNode;
        if (static_cast<std::uint32_t>(*key) == installing->plan.stage->PhaseKey(node.phase) &&
            static_cast<std::uint32_t>(*key >> 32) == node.node && type == node.type)
            enrolled = restoreNotifications.Watch(installing->cutoff.quests, slot);
    }
    return slot;
}

void NotifyQuest(void* quests, std::uint32_t slot)
{
    if (!restoreNotifications.Intercept(quests, slot))
        notifyQuestOriginal(quests, slot);
}

void ObserveWorldUpdate(void* receiver, void* job)
{
    worldUpdateOriginal(receiver, job);
    const std::unique_lock lock(boundaryMutex, std::try_to_lock);
    if (!lock || !liveHandoff || gate.Transitioning() ||
        (liveHandoff->phase != CassiusPhase::Streaming && liveHandoff->phase != CassiusPhase::AwaitingJournal))
        return;
    const WorldPrefabMethods methods{image + WorldStreamingType, image + WorldStreamingUpdateType,
        At<decltype(WorldPrefabMethods::find)>(WorldPrefabIndexLookup),
        At<decltype(WorldPrefabMethods::desired)>(WorldPrefabDesired)};
    for (auto& support : liveHandoff->supports)
        support.observed = ReadWorldPrefabSupport(receiver, support.lease.world, support.lease.refs, methods);
}

bool SupportsRetired(void* quests, const LiveHandoff& handoff)
{
    auto* loader = Read<void*>(quests, 0x100);
    for (std::size_t i = 0; i < SupportPhases.size(); ++i)
    {
        const auto& support = handoff.supports[i];
        const auto phase = FindPhase(quests, handoff.plan.stage->phases[SupportPhases[i]].address);
        if (!phase)
            return false;
        if (*phase && *phase == support.original && SupportPhases[i] != CassiusCollection.body)
            continue;
        if (!ReadPrefabRetirement(loader, image + PrefabLoaderType, support.lease))
            return false;
    }
    return true;
}

bool SupportsReady(void* quests, const LiveHandoff& handoff)
{
    auto* loader = Read<void*>(quests, 0x100);
    for (std::size_t i = 0; i < SupportPhases.size(); ++i)
    {
        const auto& support = handoff.supports[i];
        const auto* phase = handoff.restore.Phase(quests, SupportPhases[i]);
        if (!phase || !support.observed || !support.observed->Ready())
            return false;
        const auto id = Read<std::uint32_t>(phase, 0x84);
        if (phase == support.original && id == support.lease.tickets.phase && SupportPhases[i] != CassiusCollection.body)
        {
            const auto active = ReadPrefabLeaseBinding(loader, image + PrefabLoaderType, support.lease.tickets);
            if (!active || active->refs != support.lease.refs)
                return false;
        }
        else if (!ReadPrefabLeaseBinding(loader, image + PrefabLoaderType, {id, 0}, support.lease))
            return false;
    }
    return true;
}

bool InstallCollectionHandlers(void* quests, LiveHandoff& handoff)
{
    if (!restoreNotifications.Begin(quests))
        return false;
    handoff.notificationsArmed = true;
    installing = &handoff;
    bool ok = true;
    for (std::size_t i = 0; i < handoff.plan.stage->nodes.size(); ++i)
    {
        installingNode = &handoff.restore.Node(i);
        enrolled = false;
        if (!handoff.restore.CreateHandler(quests, i) || (handoff.restore.Minted(i) && !enrolled))
        {
            ok = false;
            break;
        }
    }
    installingNode = nullptr;
    installing = nullptr;
    return ok;
}

void SetOwnerReceipt(const LiveHandoff& handoff, int value)
{
    At<void (*)(const void*, std::uint32_t, std::uint32_t, std::int32_t)>(0x350E50)(
        handoff.cutoff.facts, 1, FactId(CassiusOwnerFact), value);
}

void FinishCassiusRollback(void* quests, LiveHandoff& handoff)
{
    if (!handoff.graphUndone)
    {
        if (!handoff.restore.Rollback(quests))
            return;
        handoff.graphUndone = true;
        if (handoff.notificationsArmed)
            return;
    }
    // Keep intercepted replacement slots fenced until the stock worker has
    // passed the removed listeners and any notification copy made before undo.
    if (handoff.notificationsArmed && handoff.rollbackPasses < 2 && ++handoff.rollbackPasses < 2)
        return;
    if (handoff.journalEdit.Issued() && (!handoff.journal || !handoff.journalEdit.Clean(*handoff.journal)))
        return;
    if (handoff.ownerReceipt)
    {
        SetOwnerReceipt(handoff, 0);
        if (HandoffFacts(handoff)(CassiusOwnerFact) != 0)
            return;
    }
    sdk->logger->WarnF(plugin, "PTFR Cassius restore deferred: %s", handoff.failure);
    ResetLiveHandoff();
}

void OnLiveSavePoll(const void* session)
{
    const std::unique_lock lock(boundaryMutex, std::try_to_lock);
    if (!lock || !liveHandoff || gate.Transitioning() || !Is(session, SaveSessionVtable) ||
        liveHandoff->phase != CassiusPhase::AwaitingSavePermit || liveHandoff->permit)
        return;
    auto permit = TryBeginNativeHandoff(session);
    if (permit)
        liveHandoff->permit.emplace(std::move(permit));
}

void OnLiveQuestDrain(void* quests)
{
    const std::unique_lock lifetime(boundaryMutex, std::try_to_lock);
    if (!lifetime || !liveHandoff || gate.Transitioning() || notificationPasses || !SameHandoff(*liveHandoff, quests))
        return;
    const std::unique_lock graph(LockAt(quests, 0x60), std::try_to_lock);
    if (!graph)
        return;
    auto& handoff = *liveHandoff;
    const auto fact = HandoffFacts(handoff);
    const auto now = Monotonic::now();
    const bool freshJournal = handoff.journal && now - handoff.journalSampled <= std::chrono::seconds(1);
    const bool completion = GenuineTowerCompletion(handoff.cutoff.ticket, fact);
    if (!handoff.failure && (!CassiusMayClaim(fact) || !PrivatePathsIdle(quests)))
        handoff.failure = "original progress or an adapter claim changed";
    if (!handoff.failure && fact("PTFRHS3_GateOpen") == 0 && !MatchingReedCutoff(handoff.cutoff.ticket, fact))
        handoff.failure = "Reed cutoff did not commit";
    if (completion && handoff.deadline == Monotonic::time_point{})
        handoff.deadline = now + RestoreLimit;
    if (!handoff.failure && handoff.deadline != Monotonic::time_point{} && now >= handoff.deadline)
        handoff.failure = "retirement, journal or world readiness timed out";
    if (!handoff.failure && completion && !handoff.retired)
        handoff.failure = "original inventory listener retirement was not observed";
    if (handoff.failure)
    {
        handoff.phase = CassiusPhase::Aborting;
        FinishCassiusRollback(quests, handoff);
        return;
    }
    if (!completion)
        return;

    if (handoff.phase == CassiusPhase::Retiring)
    {
        const auto body = FindPhase(quests, CassiusPath);
        if (body && !*body && QueuesQuiet(quests, handoff.plan) && SupportsRetired(quests, handoff))
        {
            // Drain a full additional stock pass after observing producer
            // removal, including a previously copied notification batch.
            if (++handoff.quietPasses == 2 && freshJournal &&
                handoff.journal->PendingAfterCleanup() && CassiusServiceReady(quests, fact))
                handoff.phase = CassiusPhase::AwaitingSavePermit;
            else if (handoff.quietPasses >= 2)
                handoff.quietPasses = 1;
        }
        else
            handoff.quietPasses = 0;
    }
    if (handoff.phase == CassiusPhase::AwaitingSavePermit && handoff.permit)
    {
        if (!freshJournal || !handoff.journal->PendingAfterCleanup() || !CassiusServiceReady(quests, fact) ||
            !QueuesQuiet(quests, handoff.plan) || !SupportsRetired(quests, handoff) || !handoff.restore.CreatePhases(quests))
        {
            handoff.failure = "native phase restoration did not qualify";
            return;
        }
        handoff.phase = CassiusPhase::Streaming;
        handoff.deadline = now + RestoreLimit;
    }
    if (handoff.phase == CassiusPhase::Streaming && freshJournal &&
        handoff.journal->PendingAfterCleanup() && CassiusServiceReady(quests, fact) && SupportsReady(quests, handoff))
    {
        if (!InstallCollectionHandlers(quests, handoff))
        {
            handoff.failure = "native inventory listener did not enroll";
            return;
        }
        handoff.phase = CassiusPhase::AwaitingJournal;
        handoff.deadline = now + RestoreLimit;
    }
    if (handoff.phase == CassiusPhase::AwaitingJournal && freshJournal &&
        handoff.journalEdit.Applied(*handoff.journal) && handoff.journal->safe &&
        CassiusServiceReady(quests, fact) && SupportsReady(quests, handoff))
    {
        if (!handoff.restore.Handler(quests, CollectionIndex))
        {
            handoff.failure = "replacement listener disappeared before commit";
            return;
        }
        SetOwnerReceipt(handoff, 1);
        handoff.ownerReceipt = fact(CassiusOwnerFact) == 1;
        if (!handoff.ownerReceipt || !handoff.restore.Commit())
        {
            handoff.failure = "native owner receipt or resource commit did not verify";
            return;
        }
        restoreNotifications.Finish(quests, [quests](std::uint32_t slot) { notifyQuestOriginal(quests, slot); });
        sdk->logger->InfoF(plugin, "PTFR Cassius native handoff committed ticket=%d", handoff.cutoff.ticket);
        ResetLiveHandoff();
    }
}

CassiusCommand DispatchCassiusBridge(void* quests, std::int32_t operation, std::span<const std::uint64_t> values)
{
    const auto conservative = operation == 0 ? CassiusCommand::AdapterBlocked : CassiusCommand::Idle;
    const std::unique_lock lifetime(boundaryMutex, std::try_to_lock);
    if (!lifetime || !enabled.load() || gate.Transitioning() || notificationPasses || !Is(quests, QuestSystem))
        return conservative;
    if (operation == 0 && liveHandoff && liveHandoff->cutoff.quests == quests)
        return CassiusCommand::AdapterBlocked;
    if (operation != 0 && (!liveHandoff || !SameHandoff(*liveHandoff, quests)))
        return CassiusCommand::Idle;
    const std::unique_lock graph(LockAt(quests, 0x60), std::try_to_lock);
    if (!graph)
        return conservative;
    if (operation == 0)
    {
        const auto* facts = Read<const void*>(quests, 0xF8);
        const auto phase = FindPhase(quests, CassiusPath);
        return !Is(facts, FactsManager) || FactValue(facts, CassiusOwnerFact) != 0 || !phase || *phase
                   ? CassiusCommand::AdapterBlocked : CassiusCommand::Idle;
    }

    auto& handoff = *liveHandoff;
    if (operation == 1)
        return CassiusCommand::Observe;
    if (operation != 2)
        return CassiusCommand::Idle;
    handoff.journal = CassiusJournal::Read(values);
    if (!handoff.journal)
        return CassiusCommand::Idle;
    handoff.journalSampled = Monotonic::now();
    const auto fact = HandoffFacts(handoff);
    CassiusCommand command = CassiusCommand::Idle;
    if (handoff.phase == CassiusPhase::Aborting && handoff.graphUndone &&
        CassiusUnclaimed(fact) && fact("sq_q001_done") == 0)
        command = handoff.journalEdit.Undo(*handoff.journal);
    if (handoff.phase == CassiusPhase::AwaitingJournal && !handoff.failure &&
        GenuineTowerCompletion(handoff.cutoff.ticket, fact) && CassiusMayClaim(fact) &&
        PrivatePathsIdle(quests) && CassiusServiceReady(quests, fact) && SupportsReady(quests, handoff) &&
        handoff.restore.Handler(quests, CollectionIndex))
        command = handoff.journalEdit.Request(*handoff.journal);
    // The script is about to change the journal. Its pre-write sample cannot
    // serve as the acknowledgement of a later undo or commit.
    if (command != CassiusCommand::Idle)
        handoff.journal.reset();
    return command;
}
