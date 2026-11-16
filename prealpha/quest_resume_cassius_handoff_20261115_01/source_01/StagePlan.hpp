#pragma once

#include "../../universal_resume_checkpoint_probe_20261114_01/source_02/Checkpoint.hpp"

namespace ptfr::resume
{
enum class ResumeKind { EarnedCollection, TravelOrTalk, SimpleTimer, ParallelObjectives };

struct RestorePhase
{
    std::span<const std::uint16_t> address;
    std::uint64_t depot;
    std::size_t parent;
};

struct RestoreNode
{
    std::size_t phase;
    std::uint16_t node;
    std::uint64_t type;
};

struct StageSpec
{
    ResumeKind kind;
    std::span<const RestorePhase> phases;
    std::span<const RestoreNode> nodes;
    std::size_t body;

    std::uint32_t PhaseKey(std::size_t phase) const { return PhaseHash(phases[phase].address); }
};

inline constexpr auto CassiusPath = std::to_array<std::uint16_t>({0, 2, 82, 3, 17, 151, 9, 2, 5});
inline constexpr auto CassiusS22 = std::to_array<std::uint16_t>({1, 27465});
inline constexpr auto CassiusS24 = std::to_array<std::uint16_t>({1, 24609});
inline constexpr auto CassiusS22Phase = PhaseHash(CassiusS22);
inline constexpr auto CassiusS24Phase = PhaseHash(CassiusS24);
inline constexpr auto CassiusPhases = [] {
    constexpr std::array depots{
        BaseQuest,
        Depot(R"(base\quest\cyberpunk2077.questphase)"),
        std::uint64_t{},
        Depot(R"(base\quest\additional_game_elements.questphase)"),
        Depot(R"(base\quest\persistent_content.questphase)"),
        std::uint64_t{}, std::uint64_t{}, std::uint64_t{},
        Depot(R"(base\quest\main_quests\prologue\q001\phases\q101_wakako_reward.questphase)")
    };
    std::array<RestorePhase, depots.size()> phases{};
    for (std::size_t i = 0; i < phases.size(); ++i)
        phases[i] = {std::span(CassiusPath).first(i + 1), depots[i], i ? i - 1 : 0};
    return phases;
}();
inline constexpr auto PhaseRegistration = Depot("questPhaseNodeDefinition");
inline constexpr auto LogicalRegistration = Depot("questLogicalCondition");
inline constexpr std::array CassiusNodes{
    RestoreNode{0, 2, PhaseRegistration}, RestoreNode{2, 3, PhaseRegistration},
    RestoreNode{3, 17, PhaseRegistration}, RestoreNode{7, 5, PhaseRegistration},
    RestoreNode{8, 29, LogicalRegistration}
};
inline constexpr StageSpec CassiusCollection{ResumeKind::EarnedCollection, CassiusPhases, CassiusNodes, 8};
inline constexpr std::size_t MaxRestorePhases = 16;
inline constexpr std::size_t MaxRestoreNodes = 16;
static_assert(PhaseHash(CassiusPath) == 1462110622);
static_assert(LogicalRegistration == 0xa135c358ccdc56c9ULL);

struct RestorePlan
{
    const StageSpec* stage{};
    std::array<std::uint32_t, MaxRestoreNodes> slots{};

    auto RetiredSlots() const { return std::span(slots).first(stage->nodes.size()); }
};

inline bool IsPrefix(std::span<const std::uint16_t> prefix, std::span<const std::uint16_t> path)
{
    return path.size() >= prefix.size() && std::ranges::equal(prefix, path.first(prefix.size()));
}

// Registration classes are shared by other quests, including the excluded phone
// pilot. Only a mapped original phase and node can admit a pending state.
inline std::optional<RestorePlan> BindCollection(const State& state, const StageSpec& stage)
{
    if (stage.kind != ResumeKind::EarnedCollection || stage.phases.empty() || stage.nodes.empty() ||
        stage.phases.size() > MaxRestorePhases || stage.nodes.size() > MaxRestoreNodes ||
        stage.body >= stage.phases.size() ||
        state.roots.size() < 2 || state.roots[0] != BaseQuest || state.roots[1] != ExpansionQuest)
        return std::nullopt;

    const auto body = stage.phases[stage.body].address;
    if (std::ranges::any_of(state.phases, [&](const Phase& row) {
        return row.size > MaxDepth || (row.size > body.size() && IsPrefix(body, row.Path()));
    }))
        return std::nullopt;
    for (const auto& phase : stage.phases)
    {
        const auto hash = PhaseHash(phase.address);
        const auto hasHash = [hash](const Phase& value) { return value.hash == hash; };
        const auto observed = std::ranges::find_if(state.phases, hasHash);
        if (observed == state.phases.end() || std::ranges::count_if(state.phases, hasHash) != 1 ||
            !std::ranges::equal(phase.address, observed->Path()) || observed->depot != phase.depot ||
            (phase.depot && std::ranges::find(state.resourceRequests, phase.depot) != state.resourceRequests.end()))
            return std::nullopt;
    }

    RestorePlan plan{&stage, {}};
    for (std::size_t i = 0; i < stage.nodes.size(); ++i)
    {
        const auto& node = stage.nodes[i];
        if (node.phase >= stage.phases.size())
            return std::nullopt;
        const Registration expected{node.type, stage.PhaseKey(node.phase), node.node};
        const auto matches = [&](const Handler& row) {
            return row.registration.phase == expected.phase && row.registration.node == expected.node;
        };
        const auto found = std::ranges::find_if(state.handlers, matches);
        if (found == state.handlers.end() || std::ranges::count_if(state.handlers, matches) != 1 ||
            found->registration != expected || found->binding != Binding::Live || found->slot >= MaxSlots ||
            std::ranges::count(state.handlers, found->slot, &Handler::slot) != 1 ||
            std::ranges::find(state.notifications, found->slot) != state.notifications.end() ||
            std::ranges::find(state.timings, found->slot, &Timing::slot) != state.timings.end())
            return std::nullopt;
        plan.slots[i] = found->slot;
    }

    const auto hash = stage.PhaseKey(stage.body);
    if (std::ranges::count_if(state.handlers, [&](const Handler& row) { return row.registration.phase == hash; }) != 1 ||
        std::ranges::any_of(state.instances, [&](const NodeInstance& row) { return (row.key >> 32) == hash; }))
        return std::nullopt;
    return plan;
}

template<typename ReadFact>
bool CassiusEarned(ReadFact fact)
{
    return fact("sq_q001_active") == 1 && fact("sq_q001_done") == 0 &&
           fact("q001_wakako_reward_given") == 1 && fact("sq_q001_add_reward") == 1 &&
           fact("q001_done") == 1 && fact("q101_enable_side_content") == 1 &&
           fact("wat_nid_ripperdoc_01_default_on") == 1;
}

template<typename ReadFact>
bool CassiusUnclaimed(ReadFact fact)
{
    constexpr std::array receipts{
        "PTFRS22_SQ_Q001_Issued", "PTFRS22_SQ_Q001_Finished", "PTFRS22_SQ_Q001_Fault", "PTFRS22_SQ_Q001_Refused",
        "PTFRS24_THEGIG_Issued", "PTFRS24_THEGIG_Entered", "PTFRS24_THEGIG_Finished", "PTFRS24_THEGIG_Fault"
    };
    return std::ranges::all_of(receipts, [&](const auto name) { return fact(name) == 0; });
}

template<typename ReadFact>
std::optional<RestorePlan> SelectResumeStage(const State& state, int route, ReadFact fact)
{
    if (route != 1 || !CassiusEarned(fact) || !CassiusUnclaimed(fact))
        return std::nullopt;
    // These roots can be present at cutoff with only their pre-claim waits.
    // Any other handler or a child phase means the private path is occupied.
    if (std::ranges::any_of(state.phases, [](const Phase& phase) {
        if (phase.size <= CassiusS22.size() || phase.size > MaxDepth)
            return false;
        return IsPrefix(CassiusS22, phase.Path()) || IsPrefix(CassiusS24, phase.Path());
    }) || std::ranges::any_of(state.handlers, [](const Handler& handler) {
        const auto& entry = handler.registration;
        const auto pending = entry.phase == CassiusS22Phase ? 1001U : entry.phase == CassiusS24Phase ? 1002U : 0;
        return pending && (entry.node != pending || entry.type != LogicalRegistration || handler.binding != Binding::Live);
    }))
        return std::nullopt;
    return BindCollection(state, CassiusCollection);
}
} // namespace ptfr::resume
