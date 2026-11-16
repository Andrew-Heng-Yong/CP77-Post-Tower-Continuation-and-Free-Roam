#pragma once

#include "StagePlan.hpp"

namespace ptfr::resume
{
// The five keys are the quest, phase, two settled objectives and collection.
inline constexpr std::array<std::uint8_t, 5> CassiusBefore{2, 2, 3, 3, 2};
inline constexpr std::array<std::uint8_t, 5> CassiusInterrupted{4, 4, 3, 3, 4};
inline constexpr std::string_view CassiusOwnerFact = "PTFRSharedCassiusOwner";
inline constexpr std::size_t CassiusSampleWords = 8;
inline constexpr std::size_t PresentationWords = 15;

enum class CassiusCommand : std::int32_t { Idle, Observe, RestoreJournal, UndoJournal, AdapterBlocked };
enum class CassiusPhase { Retiring, AwaitingSavePermit, Streaming, AwaitingJournal, Aborting };

struct CassiusJournal
{
    std::array<std::uint8_t, 5> states{};
    bool emptyInventory{};
    bool safe{};

    static std::optional<CassiusJournal> Read(std::span<const std::uint64_t> values)
    {
        if (values.size() != CassiusSampleWords || values[7] > 1)
            return std::nullopt;
        if (std::ranges::any_of(values.first<5>(), [](auto state) { return state < 1 || state > 4; }) ||
            values[5] > INT32_MAX || values[6] > INT32_MAX)
            return std::nullopt;
        CassiusJournal out;
        for (std::size_t i = 0; i < out.states.size(); ++i)
            out.states[i] = static_cast<std::uint8_t>(values[i]);
        out.emptyInventory = values[5] == 0 && values[6] == 0;
        out.safe = values[7] == 1;
        return out;
    }

    bool WasPending() const { return states == CassiusBefore && emptyInventory; }
    bool PendingAfterCleanup() const { return states == CassiusInterrupted && emptyInventory && safe; }
    bool RestoreSettled() const { return states == CassiusBefore; }
    bool IsOwnPartialWrite() const
    {
        for (std::size_t i = 0; i < states.size(); ++i)
            if (states[i] != CassiusBefore[i] && states[i] != CassiusInterrupted[i])
                return false;
        return true;
    }
};

template<typename ReadFact>
bool MatchingReedCutoff(std::int32_t ticket, ReadFact fact)
{
    return ticket > 0 && fact("PTFRHS3_GateTicket") == ticket && fact("PTFRHS3_GateRoute") == 1 &&
           fact("PTFRHS3_GateResult") == 1 && fact("q307_point_of_no_return") > 0 &&
           fact("q115_point_of_no_return") == 0 && fact("q307_debug_reset") == 0;
}

template<typename ReadFact>
bool GenuineTowerCompletion(std::int32_t ticket, ReadFact fact)
{
    return MatchingReedCutoff(ticket, fact) && fact("PTFRHS3_GateOpen") == 0 &&
           fact("q307_main_game_killed") == 1 && fact("q307_ep1_killed") == 1 &&
           fact("q307_done") == 1 && fact("q307_finished") == 1 && fact("q307_2079") == 1 &&
           fact("PostTowerFreeRoamActive") == 1 && fact("PTFRP0_DR13") == 1 && fact("q307_active") == 0;
}

template<typename ReadFact>
bool CassiusMayClaim(ReadFact fact)
{
    return CassiusEarned(fact) && CassiusUnclaimed(fact) && fact(CassiusOwnerFact) == 0 &&
           fact("PTFRS22_SQ_Q001_Permit") == 0 && fact("PTFRS24_THEGIG_Permit") == 0;
}

template<typename ReadFact>
bool VendorAvailable(ReadFact fact)
{
    return fact("PTFRB0STCASSIUS_Ready") == 1 && fact("PTFRB0STCASSIUS_Enabled") == 1 &&
           fact("PTFRB0STCASSIUS_OwnerActive") == 1 && fact("PTFRB0STCASSIUS_Excluded") == 0 &&
           fact("PTFRB0ST_Suspended") == 0 && fact("PTFRBASE_Suspended") == 0;
}

// This state owns only the journal operation issued to the script worker.
// Ticket, graph, save guard and callbacks remain under the native transaction.
class CassiusJournalEdit
{
public:
    CassiusCommand Request(const CassiusJournal& current)
    {
        if (issued || !current.PendingAfterCleanup())
            return CassiusCommand::Idle;
        issued = true;
        return CassiusCommand::RestoreJournal;
    }

    bool Applied(const CassiusJournal& current) const { return issued && current.RestoreSettled(); }

    bool Clean(const CassiusJournal& current) const { return !issued || current.states == CassiusInterrupted; }

    CassiusCommand Undo(const CassiusJournal& current) const
    {
        return !Clean(current) && current.IsOwnPartialWrite() ? CassiusCommand::UndoJournal : CassiusCommand::Idle;
    }

    bool Issued() const { return issued; }

private:
    bool issued{};
};
} // namespace ptfr::resume
