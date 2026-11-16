#include "RestoreFixture.hpp"
#include "TravelContract.hpp"
#include "TravelEvidence.hpp"

#include <cstdio>

namespace
{
using namespace ptfr::resume;
using namespace ptfr::resume::test;

unsigned failures{};
void Check(bool passed, const char* name)
{
    std::printf("%s %s\n", passed ? "PASS" : "FAIL", name);
    failures += !passed;
}

State OriginalState()
{
    State state;
    state.roots = {BaseQuest, ExpansionQuest};
    state.phases.assign(MovingHeatObservedPhases.begin(), MovingHeatObservedPhases.end());
    state.handlers.assign(MovingHeatObservedHandlers.begin(), MovingHeatObservedHandlers.end());
    return state;
}

bool MintAll(RetainedQuestRestore& restore, Fixture& native)
{
    for (std::size_t i = 0; i < native.stage.nodes.size(); ++i)
    {
        if (!restore.CreateHandler(native.quests.data(), i) ||
            restore.Handler(native.quests.data(), i) != native.handlers[i].data())
            return false;
    }
    return true;
}
} // namespace

int main()
{
    auto state = OriginalState();
    const auto bind = [&] { return BindUntimedStage(state, MovingHeatTravel); };
    const auto original = bind();
    Check(original && original->stage->kind == ResumeKind::TravelOrTalk &&
              std::ranges::equal(original->RetiredSlots(), MovingHeatObservedHandlers,
                                 {}, std::identity{}, &Handler::slot),
          "both recorded cutoffs bind the seven Moving Heat registrations and their four ancestors");

    state.handlers.pop_back();
    Check(!bind(), "a missing community trigger defers the whole travel stage");
    state = OriginalState();
    const auto branch = state.phases.back();
    state.handlers.push_back({{LogicalRegistration, branch.hash, 2}, 20, Binding::Live});
    Check(!bind(), "an extra listener inside a nested child defers");
    state = OriginalState();
    ++state.phases.back().handlers;
    Check(!bind(), "an unaccounted native handler count defers");
    state = OriginalState();
    auto extra = branch;
    extra.path[extra.size++] = 100;
    extra.hash = PhaseHash(extra.Path());
    state.phases.push_back(extra);
    Check(!bind(), "an unknown descendant phase defers");
    state = OriginalState();
    extra = state.phases[Garage];
    extra.path[extra.size - 1] = 300;
    extra.hash = PhaseHash(extra.Path());
    state.phases.push_back(extra);
    Check(bind().has_value(), "an unrelated sibling belongs to its own owner");
    state = OriginalState();
    state.instances = {{(std::uint64_t{branch.hash} << 32) | 1, 3}};
    Check(!bind(), "unqualified native state inside a nested child defers");
    state.instances.clear();
    state.resourceRequests = {branch.depot};
    Check(!bind(), "a queued resource replacement defers");
    state.resourceRequests.clear();
    state.notifications = {state.handlers.back().slot};
    Check(!bind(), "a pending nested notification defers");
    state.notifications.clear();
    state.timings = {{state.handlers.back().slot, Clock::Game, 28, 5.0, 0}};
    Check(!bind(), "a pending timer needs a separate clock contract");
    state = OriginalState();
    std::ranges::swap(state.roots[0], state.roots[1]);
    Check(!bind(), "the EP1 quest branch must belong to native root one");

    {
        State rite;
        rite.roots = {BaseQuest, ExpansionQuest};
        rite.phases.assign(RiteObservedPhases.begin(), RiteObservedPhases.end());
        rite.handlers.assign(RiteObservedHandlers.begin(), RiteObservedHandlers.end());
        const std::array stages{
            RestorePhase{std::span(RiteTravelPath).first(1), BaseQuest, 0},
            RestorePhase{std::span(RiteTravelPath).first(2), Depot(R"(base\quest\cyberpunk2077.questphase)"), 0},
            RestorePhase{std::span(RiteTravelPath).first(3), 0, 1},
            RestorePhase{std::span(RiteTravelPath).first(4), Depot(R"(base\quest\additional_game_elements.questphase)"), 2},
            RestorePhase{std::span(RiteTravelPath).first(5), Depot(R"(base\quest\persistent_content.questphase)"), 3},
            RestorePhase{std::span(RiteTravelPath).first(6), 0, 4},
            RestorePhase{std::span(RiteTravelPath).first(7), 0, 5},
            RestorePhase{std::span(RiteTravelPath).first(8), 0, 6},
            RestorePhase{std::span(RiteTravelPath).first(9), RiteMainDepot, 7}
        };
        // The absent main phase alone makes the native target ineligible.
        // Separate bug-fix registrations cannot substitute for it.
        constexpr std::array callers{RestoreNode{7, 10, PhaseRegistration}};
        const StageSpec clinic{ResumeKind::TravelOrTalk, stages, callers, 8};
        Check(!BindUntimedStage(rite, clinic), "Rite of Passage defers when only unrelated listeners survive");
    }
    {
        Fixture native(MovingHeatTravel);
        RetainedQuestRestore restore;
        auto* quests = native.quests.data();
        const bool prepared = restore.Prepare(Native(), quests, native.Plan());
        Check(prepared && !restore.CreatePhases(quests), "an original EP1 garage owner prevents a second owner");
        native.Retire(3, true);
        const auto retained = native.rows[0];
        Check(prepared && restore.CreatePhases(quests) && MintAll(restore, native) &&
                  native.phasesCreated == 7 && native.handlersCreated == 10 &&
                  native.rows[0] == retained && !restore.Minted(0),
              "the same restore transaction adopts the ten missing registrations under EP1");
        Check(restore.Commit() && native.phasePresent[GarageCommunity] &&
                  native.counts[Garage] == 1 && native.counts[LoadingArea] == 1 &&
                  native.counts[GarageCommunity] == 1 && native.contextOpened == native.contextClosed,
              "only adopted resources survive commit and contexts balance");
    }
    {
        Fixture native(MovingHeatTravel);
        RetainedQuestRestore restore;
        auto* quests = native.quests.data();
        const bool prepared = restore.Prepare(Native(), quests, native.Plan());
        native.Retire(3, true);
        native.failChild = LoadingArea;
        Check(prepared && !restore.CreatePhases(quests) && restore.Rollback(quests) &&
                  native.phasePresent[2] && !native.phasePresent[Garage] && !native.counts[Garage] &&
                  !native.counts[LoadingArea] && !native.counts[GarageCommunity],
              "a failed nested phase rolls back the EP1 additions without removing the retained parent");
    }
    return failures != 0;
}
