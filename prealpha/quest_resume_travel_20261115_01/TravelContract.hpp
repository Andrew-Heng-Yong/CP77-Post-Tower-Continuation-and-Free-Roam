#pragma once

#include "source_01/StagePlan.hpp"

namespace ptfr::resume::test
{
inline constexpr auto MovingHeatPath = std::to_array<std::uint16_t>({1, 0, 10, 4, 2, 30, 6, 4, 65, 17});
inline constexpr std::size_t Garage = 7;
inline constexpr std::size_t LoadingArea = 8;
inline constexpr std::size_t GarageCommunity = 9;
inline constexpr auto MovingHeatPhases = [] {
    constexpr std::array depots{
        ExpansionQuest, Depot(R"(ep1\quest\ep1.questphase)"), std::uint64_t{},
        Depot(R"(ep1\quest\ep1_additional_game_elements.questphase)"),
        Depot(R"(ep1\quest\ep1_persistent_content.questphase)"), std::uint64_t{}, std::uint64_t{},
        Depot(R"(ep1\quest\main_quests\q304\phases\q304_car_retrieval.questphase)"),
        Depot(R"(ep1\quest\main_quests\q304\phases\subphases\q304_car_retrieval_loading_area.questphase)"),
        Depot(R"(ep1\quest\main_quests\q304\phases\combat_phases\q304_car_retrieval_cmbt_loading.questphase)")
    };
    std::array<RestorePhase, depots.size()> phases{};
    for (std::size_t i = 0; i < phases.size(); ++i)
        phases[i] = {std::span(MovingHeatPath).first(i + 1), depots[i], i ? i - 1 : 0};
    return phases;
}();
inline constexpr auto TriggerRegistration = Depot("questTriggerCondition");
inline constexpr auto DeviceRegistration = Depot("questDevice_ConditionType");
inline constexpr std::array MovingHeatNodes{
    RestoreNode{0, 0, PhaseRegistration}, RestoreNode{2, 4, PhaseRegistration},
    RestoreNode{3, 2, PhaseRegistration}, RestoreNode{6, 4, PhaseRegistration},
    RestoreNode{Garage, 65, PhaseRegistration}, RestoreNode{LoadingArea, 17, PhaseRegistration},
    RestoreNode{Garage, 147, DeviceRegistration}, RestoreNode{Garage, 148, DeviceRegistration},
    RestoreNode{Garage, 164, TriggerRegistration}, RestoreNode{LoadingArea, 2, TriggerRegistration},
    RestoreNode{GarageCommunity, 1, TriggerRegistration}
};
inline constexpr StageSpec MovingHeatTravel{ResumeKind::TravelOrTalk, MovingHeatPhases, MovingHeatNodes, Garage};
} // namespace ptfr::resume::test
