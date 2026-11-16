#include "source_01/NativeCheckpoint.cpp"
#include "RestoreFixture.hpp"

#include <cstdio>

namespace
{
using ptfr::resume::test::Array;
using ptfr::resume::test::Native;
using ptfr::resume::test::Put;
using ptfr::resume::test::Write;

constexpr std::array<std::uint64_t, 8> Interrupted{4, 4, 3, 3, 4, 0, 0, 1};
constexpr std::array<std::uint64_t, 8> Reactivated{2, 2, 3, 3, 2, 0, 0, 1};
constexpr std::array<std::uint64_t, 8> Partial{2, 4, 3, 3, 4, 0, 0, 1};
constexpr std::uint32_t Missing = UINT32_MAX;
unsigned failures{};

void Check(bool ok, const char* description)
{
    std::printf("%s %s\n", ok ? "PASS" : "FAIL", description);
    failures += !ok;
}

struct Host;
Host* host{};

struct Host
{
    ptfr::resume::test::Fixture native;
    alignas(16) std::array<std::byte, 0x180> loader{};
    alignas(16) std::array<std::byte, 0x60> factsObject{};
    alignas(16) std::array<std::byte, 0x310> session{};
    alignas(16) std::array<std::byte, 0x150> callContext{};
    std::array<std::array<std::byte, 0x110>, 3> servicePhases{};
    std::array<std::array<std::uint16_t, 3>, 3> servicePaths{};
    std::array<std::array<RestoreHandle, 1>, 2> serviceChildren{};
    std::array<std::byte, 0x58> serviceHandler{};
    std::array<std::byte, 0x48> serviceResource{};
    std::array<std::array<std::byte, 0x68>, 2> tickets{};
    std::array<std::uint32_t, 2> ids{21, 22};
    std::array<std::uint32_t, 2> ready{};
    std::array<std::uint64_t, 2> refs{601, 602};
    std::array<std::uint32_t, 2> counts{1, 1};
    int world{};
    std::uint32_t nextSlot{Missing};
    std::vector<Fact> facts;
    std::vector<std::uint32_t> published;
    RED4ext::v1::Logger logger{};
    RED4ext::v1::Sdk testSdk{};

    Host()
    {
        host = this;
        image = static_cast<std::uint8_t*>(VirtualAlloc(nullptr, 0x3800000, MEM_RESERVE | MEM_COMMIT,
                                                       PAGE_EXECUTE_READWRITE));
        if (!image)
            std::abort();
        HookPointer(0x2B2270, &GetFact);
        HookPointer(0x350E50, &PutFact);
        HookPointer(0x2B1B64, &GetHandler);
        if (!FlushInstructionCache(GetCurrentProcess(), image, 0x3800000))
            std::abort();
        logger.WarnF = &IgnoreLog;
        logger.InfoF = &IgnoreLog;
        testSdk.logger = &logger;
        sdk = &testSdk;
        Put(native.quests, 0, image + QuestSystem);
        Put(native.quests, 0xF8, factsObject.data());
        Put(native.quests, 0x100, loader.data());
        Put(native.root, 0, image + SyntheticRoot);
        for (auto& phase : native.phases)
            Put(phase, 0, image + PhaseInstance);
        for (std::size_t i = 0; i < servicePhases.size(); ++i)
        {
            const auto prefix = std::span(CassiusServicePath).first(i + 1);
            auto& phase = servicePhases[i];
            std::ranges::copy(prefix, servicePaths[i].begin());
            Put(phase, 0, image + PhaseInstance);
            Put(phase, 0x80, PhaseHash(prefix));
            Array(phase, 0x70, servicePaths[i], static_cast<std::uint32_t>(i + 1));
            if (i < serviceChildren.size())
            {
                serviceChildren[i][0].object = servicePhases[i + 1].data();
                Array(phase, 0x88, serviceChildren[i], 1);
            }
        }
        native.rootChildren[1].object = servicePhases[0].data();
        Put(serviceResource, 0x30, CassiusServiceDepot);
        Put(servicePhases[1], 0x30, serviceResource.data());
        Put(serviceHandler, 0, image + PhaseHandlerType);
        Put(loader, 0, image + PrefabLoaderType);
        Put(loader, 0xC8, &world);
        Put(factsObject, 0, image + FactsManager);
        Put(session, 0, image + SaveSessionVtable);
        Put(callContext, 0x128, native.quests.data());

        for (auto name : {"sq_q001_active", "q001_wakako_reward_given", "sq_q001_add_reward", "q001_done",
                          "q101_enable_side_content", "wat_nid_ripperdoc_01_default_on",
                          "PTFRHS3_GateTicket", "PTFRHS3_GateRoute", "PTFRHS3_GateResult",
                          "q307_point_of_no_return", "PTFRB0STCASSIUS_Ready", "PTFRB0STCASSIUS_Enabled",
                          "PTFRB0STCASSIUS_OwnerActive"})
            Set(name, 1);
        for (std::size_t i = 0; i < tickets.size(); ++i)
        {
            Put(tickets[i], 0, &refs[i]);
            Put(tickets[i], 8, 1U);
            Put(tickets[i], 12, 1U);
        }
        Array(loader, 0x38, ids, 0);
        Put(loader, 0x48, tickets.data());
        Array(loader, 0x60, refs, 2);
        Array(loader, 0x70, counts, 2);
        Array(loader, 0xA0, ready, 0);

        removeConditionOriginal = [](void*, std::uint32_t, void*) { host->native.EraseHandler(CollectionIndex); };
        allocateQuestSlotOriginal = [](void*, std::uint64_t, const std::uint64_t*) { return host->nextSlot; };
        notifyQuestOriginal = [](void*, std::uint32_t slot) { host->published.push_back(slot); };
        loadOriginal = [](void*, void*, void*, void*) {};
        native.onPhaseCreated = [](std::size_t index) {
            const auto pos = std::ranges::find(SupportPhases, index);
            if (pos != SupportPhases.end())
                Put(host->native.phases[index], 0x84, host->ids[static_cast<std::size_t>(pos - SupportPhases.begin())]);
        };
        native.onAllocate = [](std::size_t index, std::uint32_t slot) {
            const auto& node = CassiusNodes[index];
            const auto key = (std::uint64_t{node.node} << 32) | CassiusCollection.PhaseKey(node.phase);
            host->nextSlot = slot;
            return AllocateRestoreSlot(host->native.manager.data(), node.type, &key);
        };
        native.onRegister = [](std::uint32_t slot) {
            NotifyQuest(host->native.quests.data(), slot);
            NotifyQuest(host->native.quests.data(), slot);
        };
        enabled.store(true);
    }

    ~Host()
    {
        ResetLiveHandoff();
        enabled.store(false);
        sdk = nullptr;
        VirtualFree(const_cast<std::uint8_t*>(image), 0, MEM_RELEASE);
        image = nullptr;
        host = nullptr;
    }

    void* Quests() { return native.quests.data(); }
    void Set(std::string_view name, int value) { PutFact(factsObject.data(), 1, FactId(name), value); }
    auto Command(int operation, std::span<const std::uint64_t> values = {})
    {
        return DispatchCassiusBridge(Quests(), operation, values);
    }

    bool Reserve()
    {
        auto methods = Native();
        methods.systemType = image + QuestSystem;
        methods.rootType = image + SyntheticRoot;
        methods.phaseType = image + PhaseInstance;
        auto& h = liveHandoff.emplace();
        h.cutoff = {Quests(), factsObject.data(), 1, 1};
        h.plan = native.Plan();
        for (std::size_t i = 0; i < h.supports.size(); ++i)
            h.supports[i] = {native.phases[SupportPhases[i]].data(), {loader.data(), &world, {11U + static_cast<unsigned>(i), 0},
                             {refs[i]}}, {}};
        h.originalListener = native.handlers[CollectionIndex].data();
        watchedCollectionPhase.store(native.phases[CassiusCollection.body].data());
        return h.restore.Prepare(methods, Quests(), h.plan);
    }

    void Retire(bool genuine)
    {
        if (genuine)
            Set("q307_main_game_killed", 1);
        ObserveRemoveCondition(native.phases[CassiusCollection.body].data(), 29, callContext.data());
        native.Retire(2, true);
    }

    bool AdvanceToStreaming()
    {
        Retire(true);
        for (auto name : {"q307_ep1_killed", "q307_done", "q307_finished", "q307_2079",
                          "PostTowerFreeRoamActive", "PTFRP0_DR13"})
            Set(name, 1);
        Command(2, Interrupted);
        OnLiveQuestDrain(Quests());
        OnLiveSavePoll(session.data());
        if (!liveHandoff || liveHandoff->permit)
            return false;
        OnLiveQuestDrain(Quests());
        OnLiveSavePoll(session.data());
        if (!liveHandoff || !liveHandoff->permit)
            return false;
        OnLiveQuestDrain(Quests());
        return liveHandoff && liveHandoff->phase == CassiusPhase::Streaming && published.empty();
    }

    void SetStreaming(bool available)
    {
        Put(loader, 0x44, 2U);
        for (std::size_t i = 0; i < SupportPhases.size(); ++i)
            liveHandoff->supports[i].observed = WorldPrefabSupport{&world, {refs[i]},
                {available ? WorldPrefabStatus::Ready : WorldPrefabStatus::AwaitingStreaming}};
    }

    template<typename F>
    void HookPointer(std::uint32_t rva, F func)
    {
        // Microsoft x64 tail-jump stub used only by the isolated fixture.
        std::array<std::uint8_t, 12> code{0x48, 0xB8, 0, 0, 0, 0, 0, 0, 0, 0, 0xFF, 0xE0};
        const auto address = reinterpret_cast<std::uintptr_t>(func);
        std::memcpy(code.data() + 2, &address, sizeof(address));
        std::memcpy(const_cast<std::uint8_t*>(image) + rva, code.data(), code.size());
    }

    static std::int32_t GetFact(const void*, std::uint32_t store, std::uint32_t key)
    {
        const auto row = std::ranges::find(host->facts, key, &Fact::key);
        return store == 1 && row != host->facts.end() ? row->value : 0;
    }

    static void PutFact(const void*, std::uint32_t store, std::uint32_t key, std::int32_t value)
    {
        if (store != 1)
            std::abort();
        const auto row = std::ranges::find(host->facts, key, &Fact::key);
        if (row == host->facts.end())
            host->facts.push_back({key, value});
        else
            row->value = value;
    }

    static void* GetHandler(const void* phase, std::uint32_t node)
    {
        if (phase == host->servicePhases[1].data())
            return node == 5 ? host->serviceHandler.data() : nullptr;
        return Native().findHandler(phase, node);
    }

    static void IgnoreLog(RED4ext::v1::PluginHandle, const char*, ...) {}
};
} // namespace

int main()
{
    {
        Host h;
        Check(h.Reserve() && h.Command(0) == CassiusCommand::AdapterBlocked &&
                  h.Command(1) == CassiusCommand::Observe,
              "the same-session reservation blocks both adapter permits and accepts journal observation");
        Check(h.AdvanceToStreaming() && !saveAdmission.TryHandoff(h.session.data()),
              "stock removal and two quiet passes precede creation under the save guard");
        h.SetStreaming(false);
        OnLiveQuestDrain(h.Quests());
        Check(h.Command(2, Interrupted) == CassiusCommand::Idle && !h.native.handlersCreated,
              "unready streamed world support prevents listener creation and journal writes");
        h.SetStreaming(true);
        h.refs[1] = 999;
        OnLiveQuestDrain(h.Quests());
        Check(!h.native.handlersCreated, "an incorrect prefab identity defers despite a ready world sample");
        h.refs[1] = 602;
        OnLiveQuestDrain(h.Quests());
        Check(h.native.handlersCreated == 4 && h.published.empty() &&
                  h.Command(2, Interrupted) == CassiusCommand::RestoreJournal &&
                  h.Command(2, Interrupted) == CassiusCommand::Idle,
              "minted callbacks wait for one authorized journal request");
        h.Command(2, Partial);
        OnLiveQuestDrain(h.Quests());
        Check(liveHandoff.has_value() && h.published.empty(), "an incomplete journal change cannot commit");
        h.Command(2, Reactivated);
        OnLiveQuestDrain(h.Quests());
        Check(!liveHandoff && h.native.phasePresent[CassiusCollection.body] &&
                  h.published == std::vector<std::uint32_t>({13, 14, 15, 16}) &&
                  Host::GetFact(nullptr, 1, FactId(CassiusOwnerFact)) == 1 &&
                  static_cast<bool>(saveAdmission.TryHandoff(h.session.data())),
              "commit verifies journal readback, publishes selected callbacks once and releases saving");
        Load(h.Quests(), nullptr, nullptr, nullptr);
        Check(h.Command(0) == CassiusCommand::AdapterBlocked, "an installed native owner blocks adapters after a load transition");
    }
    {
        Host h;
        const auto started = h.Reserve() && h.AdvanceToStreaming();
        h.SetStreaming(true);
        OnLiveQuestDrain(h.Quests());
        const auto edited = h.Command(2, Interrupted) == CassiusCommand::RestoreJournal;
        liveHandoff->failure = "injected failure after journal change";
        OnLiveQuestDrain(h.Quests());
        Check(started && edited && liveHandoff && !h.native.phasePresent[CassiusCollection.body] && h.published.empty() &&
                  h.Command(2, Partial) == CassiusCommand::UndoJournal && h.Command(0) == CassiusCommand::AdapterBlocked,
              "rollback removes replacement listeners while a partial journal update still blocks adapters");
        h.Command(2, Interrupted);
        OnLiveQuestDrain(h.Quests());
        NotifyQuest(h.Quests(), 16);
        Check(liveHandoff.has_value() && h.published.empty() &&
                  h.Command(0) == CassiusCommand::AdapterBlocked,
              "late callbacks are fenced through the post-rollback stock passes");
        OnLiveQuestDrain(h.Quests());
        Check(!liveHandoff && h.Command(0) == CassiusCommand::Idle &&
                  static_cast<bool>(saveAdmission.TryHandoff(h.session.data())) && h.native.rows[0].node == 2,
              "rollback releases fallback only after the journal unwinds and preserves the retained ancestor");
    }
    {
        Host h;
        const auto prepared = h.Reserve();
        h.Retire(false);
        OnLiveQuestDrain(h.Quests());
        Check(prepared && !liveHandoff && h.native.phasesCreated == 0 && h.published.empty(),
              "ordinary early listener removal cannot qualify as Tower retirement");
    }
    {
        Host h;
        const auto prepared = h.Reserve();
        h.Set("PTFRS22_SQ_Q001_Issued", 1);
        OnLiveQuestDrain(h.Quests());
        Check(prepared && !liveHandoff && h.native.phasesCreated == 0 && h.native.phasePresent[CassiusCollection.body],
              "a competing issued receipt cancels the reservation before graph mutation");
    }
    return failures != 0;
}
