#include "RestoreFixture.hpp"

#include <cstdio>

namespace
{
using namespace ptfr::resume;
using namespace ptfr::resume::test;

unsigned failed{};
void Check(bool pass, const char* report)
{
    std::printf("%s %s\n", pass ? "PASS" : "FAIL", report);
    failed += !pass;
}

bool CreateHandlers(RetainedQuestRestore& restore, Fixture& native)
{
    for (std::size_t i = 0; i < CassiusNodes.size(); ++i)
        if (!restore.CreateHandler(native.quests.data(), i) || restore.Handler(native.quests.data(), i) != native.handlers[i].data())
            return false;
    return true;
}
} // namespace

int main()
{
    {
        Fixture native;
        RetainedQuestRestore restore;
        const auto initial = native.counts;
        Check(restore.ValidateOriginal(Native(), native.quests.data(), native.Plan()) &&
                  native.counts == initial && native.contextOpened == 0,
              "cutoff validation leaves all original native objects untouched");
        Check(restore.Prepare(Native(), native.quests.data(), native.Plan()) &&
                  native.counts[1] == 2 && native.counts[8] == 2,
              "prepare holds the selected live phase resources");
        Check(!restore.CreatePhases(native.quests.data()), "live body blocks a second owner");
        Check(restore.Rollback(native.quests.data()) && native.counts == initial && native.phasePresent[8],
              "abort before retirement preserves the original owner");
    }
    {
        Fixture native;
        RetainedQuestRestore restore;
        auto* quests = native.quests.data();
        const auto prepared = restore.Prepare(Native(), quests, native.Plan());
        native.Retire(2, true);
        const auto ancestor = native.rows[0];
        Check(prepared && restore.CreatePhases(quests) && native.phasesCreated == 7 &&
                  CreateHandlers(restore, native) && native.handlersCreated == 4 && native.rows[0] == ancestor,
              "restoration reuses a coherent surviving ancestor and mints only missing handlers");
        const auto collection = native.rows[16];
        native.rows[16] = {};
        Check(!restore.Commit(), "commit rejects missing collection readback");
        native.rows[16] = collection;
        native.pending = {0, 16, 90, 14, 97};
        Put(native.quests, 0x164, 5U);
        Check(restore.Rollback(quests) && native.rows[0] == ancestor && native.phasePresent[1] &&
                  !native.phasePresent[8] && native.counts[1] == 1 && native.handlersRemoved == 0,
              "rollback leaves the surviving ancestor and removes adopted children");
        Check(Read<std::uint32_t>(quests, 0x164) == 3 && native.pending[0] == 0 &&
                  native.pending[1] == 90 && native.pending[2] == 97 &&
                  native.contextOpened == native.contextClosed,
              "rollback drains only minted notifications and balances native contexts");
    }
    {
        Fixture native;
        RetainedQuestRestore restore;
        auto* quests = native.quests.data();
        const auto prepared = restore.Prepare(Native(), quests, native.Plan());
        native.Retire(2);
        native.failChild = 8;
        Check(prepared && !restore.CreatePhases(quests) && restore.Rollback(quests) && native.phasePresent[1] &&
                  !native.phasePresent[8] && !native.counts[8] && native.counts[1] == 1,
              "a failed phase creation unwinds its resident holds and adopted children");
    }
    {
        Fixture native;
        RetainedQuestRestore restore;
        auto* quests = native.quests.data();
        const auto prepared = restore.Prepare(Native(), quests, native.Plan());
        native.Retire(1);
        Check(prepared && restore.CreatePhases(quests) &&
                  !restore.CreateHandler(quests, 4) && CreateHandlers(restore, native) &&
                  native.handlersCreated == 5 && restore.Commit() && native.phasePresent[8] &&
                  native.counts[1] == 1 && native.counts[8] == 1 && native.rows[16].node == 29,
              "the original inventory node and all four owner registrations can be restored and committed");
    }
    return failed != 0;
}
