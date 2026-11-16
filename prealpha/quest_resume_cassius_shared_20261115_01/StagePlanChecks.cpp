#include "source_01/StagePlan.hpp"
#include "source_01/RestoreNotifications.hpp"
#include "CassiusEvidence.hpp"

#include <cstdio>

namespace
{
using namespace ptfr::resume;
unsigned failures{};

void Check(bool ok, const char* description)
{
    std::printf("%s %s\n", ok ? "PASS" : "FAIL", description);
    failures += !ok;
}

State OriginalState()
{
    State result;
    result.roots = {BaseQuest, ExpansionQuest};
    for (const auto& phase : OriginalPhases)
        result.phases.push_back(phase);
    for (const auto& handler : OriginalHandlers)
        result.handlers.push_back(handler);
    return result;
}
} // namespace

int main()
{
    auto state = OriginalState();
    constexpr std::array<std::string_view, 6> setFacts{
        "sq_q001_active", "q001_wakako_reward_given", "sq_q001_add_reward",
        "q001_done", "q101_enable_side_content", "wat_nid_ripperdoc_01_default_on"
    };
    std::string_view overridden;
    int overrideValue{};
    const auto fact = [&](std::string_view name) {
        return name == overridden ? overrideValue : (std::ranges::find(setFacts, name) != setFacts.end() ? 1 : 0);
    };
    const auto select = [&](int route = 1) { return SelectResumeStage(state, route, fact); };
    const auto selected = select();
    Check(selected && selected->stage == &CassiusCollection &&
              std::ranges::equal(selected->RetiredSlots(), OriginalHandlers, {}, std::identity{}, &Handler::slot),
          "source-bound cutoff selects the five original Cassius registrations");
    Check(!select(2), "unqualified ending route defers");

    for (const auto name : {"PTFRS22_SQ_Q001_Issued", "PTFRS24_THEGIG_Issued", "sq_q001_done"})
    {
        overridden = name;
        overrideValue = 1;
        Check(!select(), name);
    }
    overridden = "q001_wakako_reward_given";
    overrideValue = 0;
    Check(!select(), "unsettled payment defers");
    overridden = {};

    state.handlers.push_back({{LogicalRegistration, CassiusS22Phase, 1001}, 9032, Binding::Live});
    Check(select().has_value(), "the observed S22 pre-claim wait can coexist with the original");
    state.handlers.back().registration.node = 29;
    Check(!select(), "private collection listener blocks selection even without an issued receipt");
    state.handlers.pop_back();
    state.handlers.back() = ExcludedMessageHandler;
    Check(!select(), "the excluded message pilot cannot qualify as collection");
    state = OriginalState();
    state.notifications = {state.handlers.back().slot};
    Check(!select(), "an outstanding collection notification defers");
    state.notifications = {40U};
    Check(select().has_value(), "an unrelated notification does not block the collection plan");
    state.notifications.clear();
    state.handlers.push_back(state.handlers.back());
    Check(!select(), "a duplicate native listener defers");
    state.handlers.pop_back();
    state.handlers.back().binding = Binding::Ambiguous;
    Check(!select(), "an ambiguous native listener defers");
    state = OriginalState();
    state.instances = {{(std::uint64_t{PhaseHash(CassiusPath)} << 32) | 29, 17}};
    Check(!select(), "an unqualified collection node instance defers");
    state.instances.clear();
    state.resourceRequests = {CassiusPhases.back().depot};
    Check(!select(), "a queued replacement of the original resource defers");
    state.resourceRequests.clear();
    state.phases.back().depot ^= 1;
    Check(!select(), "a different native resource defers");

    RestoreNotifications notify;
    int owner{};
    int unrelatedOwner{};
    std::vector<std::uint32_t> published;
    Check(notify.Begin(&owner) && notify.Watch(&owner, 8) && notify.Watch(&owner, 9) &&
              !notify.Intercept(&unrelatedOwner, 8) && !notify.Intercept(&owner, 7),
          "notification reservation covers only selected slots in the owning session");
    Check(notify.Intercept(&owner, 9) && notify.Intercept(&owner, 8) && notify.Intercept(&owner, 9) &&
              notify.Finish(&owner, [&](std::uint32_t slot) { published.push_back(slot); }) &&
              published == std::vector<std::uint32_t>{9, 8},
          "notification commit preserves first delivery order and deduplicates callbacks");
    Check(notify.Begin(&owner) && notify.Watch(&owner, 8) && notify.Intercept(&owner, 8),
          "a later transfer starts with a clean notification reservation");
    notify.Discard();
    Check(!notify.Intercept(&owner, 8), "rollback releases only this transfer's notification reservation");
    return failures != 0;
}
