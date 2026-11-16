#pragma once

#include "../universal_resume_checkpoint_probe_20261114_01/source_02/Checkpoint.hpp"

namespace ptfr::resume
{
inline constexpr auto FalcoQuest = std::to_array<std::uint16_t>({0, 2, 82, 4, 9, 3, 64});
inline constexpr auto ReyesMessages = std::to_array<std::uint16_t>({0, 2, 82, 4, 9, 3, 64, 11});
inline constexpr auto FalcoMessages = std::to_array<std::uint16_t>({0, 2, 82, 4, 9, 3, 64, 12});
inline constexpr auto FalcoPrivateQuest = std::to_array<std::uint16_t>({1, 35238, 64});
inline constexpr auto FalcoDuration = 86'400U;
inline constexpr auto ReyesChoiceKey = 2'093'558'463U;
inline constexpr auto FalcoJoinKey = 2'301'140'172U;

struct RestorePhase
{
    std::span<const std::uint16_t> address;
    std::uint64_t depot;
};

inline constexpr std::array FalcoPhases{
    RestorePhase{std::span(FalcoQuest).first(1), BaseQuest},
    RestorePhase{std::span(FalcoQuest).first(2), Depot(R"(base\quest\cyberpunk2077.questphase)")},
    RestorePhase{std::span(FalcoQuest).first(3), 0},
    RestorePhase{std::span(FalcoQuest).first(4), Depot(R"(base\quest\bugfixing.questphase)")},
    RestorePhase{std::span(FalcoQuest).first(5), Depot(R"(base\quest\bugfixing\quest_bugfixing.questphase)")},
    RestorePhase{std::span(FalcoQuest).first(6), 0},
    RestorePhase{FalcoQuest, Depot(R"(base\quest\minor_quests\mq049\mq049.questphase)")},
    RestorePhase{ReyesMessages, Depot(R"(base\quest\minor_quests\mq049\phases\mq049_messages_reyes.questphase)")},
    RestorePhase{FalcoMessages, Depot(R"(base\quest\minor_quests\mq049\phases\mq049_messages_falco.questphase)")},
};

struct RestoreNode
{
    std::size_t phase;
    std::uint16_t node;
    std::uint64_t type;
};

inline constexpr auto PhaseRegistration = Depot("questPhaseNodeDefinition");
inline constexpr std::array FalcoRestoreNodes{
    RestoreNode{0, 2, PhaseRegistration},
    RestoreNode{2, 4, PhaseRegistration},
    RestoreNode{3, 9, PhaseRegistration},
    RestoreNode{5, 64, PhaseRegistration},
    RestoreNode{6, 11, PhaseRegistration},
    RestoreNode{6, 12, PhaseRegistration},
    RestoreNode{7, 18, Depot("questJournalEntryState_ConditionType")},
    RestoreNode{7, 23, Depot("questVarComparison_ConditionType")},
    RestoreNode{8, 28, Depot("questGameTimeDelay_ConditionType")},
};

struct RestorePath
{
    std::array<std::uint16_t, MaxDepth> words{};
    std::uint32_t size{};
    std::uint32_t retiredSlot{};
};

struct FalcoRestorePlan
{
    std::array<RestorePath, FalcoRestoreNodes.size()> paths;
    Fact reyesChoice{};
    Timing falcoWait{};
};

// Called with the genuine cutoff's verified, current capture. The paths are
// values for the restore job. Slot and timer numbers identify only the old
// owner and may not be reused to identify the replacement.
inline std::optional<FalcoRestorePlan> PlanFalcoRestore(const State& state)
{
    if (state.roots.size() < 2 || state.roots[0] != BaseQuest || state.roots[1] != ExpansionQuest)
        return std::nullopt;
    if (std::ranges::any_of(state.phases, [](const Phase& phase) {
            if (phase.size > MaxDepth)
                return true;
            const auto address = phase.Path();
            const bool privateOwner = address.size() >= FalcoPrivateQuest.size() &&
                                      std::ranges::equal(address.first(FalcoPrivateQuest.size()), FalcoPrivateQuest);
            const bool originalChild = address.size() > FalcoQuest.size() &&
                                       std::ranges::equal(address.first(FalcoQuest.size()), FalcoQuest);
            return privateOwner || (originalChild && !std::ranges::equal(address, ReyesMessages) &&
                                    !std::ranges::equal(address, FalcoMessages));
        }))
        return std::nullopt;

    std::array<std::uint32_t, FalcoPhases.size()> phaseHashes{};
    for (std::size_t i = 0; i < FalcoPhases.size(); ++i)
    {
        const auto& target = FalcoPhases[i];
        const auto hash = PhaseHash(target.address);
        const auto sameHash = [hash](const Phase& phase) { return phase.hash == hash; };
        const auto phase = std::ranges::find_if(state.phases, sameHash);
        if (phase == state.phases.end() || !std::ranges::equal(phase->Path(), target.address) ||
            phase->depot != target.depot || std::ranges::count_if(state.phases, sameHash) != 1 ||
            (target.depot && std::ranges::find(state.resourceRequests, target.depot) != state.resourceRequests.end()))
            return std::nullopt;
        phaseHashes[i] = hash;
    }

    FalcoRestorePlan result{};
    constexpr std::ptrdiff_t BodyRegistrationCount = 5;
    for (std::size_t i = 0; i < FalcoRestoreNodes.size(); ++i)
    {
        const auto& node = FalcoRestoreNodes[i];
        const auto key = [hash = phaseHashes[node.phase], id = node.node](const Handler& handler) {
            return handler.registration.phase == hash && handler.registration.node == id;
        };
        const auto row = std::ranges::find_if(state.handlers, key);
        if (row == state.handlers.end() || row->registration.type != node.type || row->binding != Binding::Live ||
            row->slot >= MaxSlots || std::ranges::count_if(state.handlers, key) != 1 ||
            std::ranges::find(state.notifications, row->slot) != state.notifications.end())
            return std::nullopt;
        if (std::ranges::any_of(std::span(result.paths).first(i), [&](const RestorePath& path) {
                return path.retiredSlot == row->slot;
            }))
            return std::nullopt;
        auto& path = result.paths[i];
        const auto address = FalcoPhases[node.phase].address;
        std::ranges::copy(address, path.words.begin());
        path.words[address.size()] = node.node;
        path.size = static_cast<std::uint32_t>(address.size() + 1);
        path.retiredSlot = row->slot;
    }
    const auto bodyPhases = std::span(phaseHashes).last(3);
    const auto inBody = [&](std::uint32_t hash) { return std::ranges::find(bodyPhases, hash) != bodyPhases.end(); };
    if (std::ranges::count_if(state.handlers, [&](const Handler& row) { return inBody(row.registration.phase); }) !=
        BodyRegistrationCount)
        return std::nullopt;

    const auto slot = result.paths.back().retiredSlot;
    const auto timing = std::ranges::find(state.timings, slot, &Timing::slot);
    if (timing == state.timings.end() || std::ranges::count(state.timings, slot, &Timing::slot) != 1 ||
        timing->clock != Clock::Game || !timing->serial || timing->serial > UINT32_MAX ||
        !std::isfinite(timing->remainingSeconds) || timing->remainingSeconds < 1.0 ||
        timing->remainingSeconds >= FalcoDuration || std::floor(timing->remainingSeconds) != timing->remainingSeconds ||
        timing->ageMilliseconds > 250)
        return std::nullopt;
    const auto timerKey = (std::uint64_t{phaseHashes.back()} << 32) | FalcoRestoreNodes.back().node;
    const auto timer = std::ranges::find(state.instances, timerKey, &NodeInstance::key);
    if (timer == state.instances.end() || timer->value != timing->serial ||
        std::ranges::count_if(state.instances, [&](const NodeInstance& item) {
            return inBody(static_cast<std::uint32_t>(item.key >> 32));
        }) != 1)
        return std::nullopt;

    const auto choice = std::ranges::find(state.facts[2], ReyesChoiceKey, &Fact::key);
    if (choice == state.facts[2].end() || choice->value != 4 ||
        std::ranges::count(state.facts[2], ReyesChoiceKey, &Fact::key) != 1 ||
        std::ranges::any_of(state.facts[1], [](const Fact& fact) { return fact.key == FalcoJoinKey && fact.value; }))
        return std::nullopt;
    result.reyesChoice = *choice;
    result.falcoWait = *timing;
    return result;
}
} // namespace ptfr::resume
