#include <array>
#include <bit>
#include <cstdio>
#include <fstream>
#include <limits>

#include "CutoffObservation.hpp"

int main(int argc, char** argv)
{
    if (argc != 2)
        return 2;
    constexpr std::uint32_t rowCount = 9;
    std::array<ptfr::SavedTimer, rowCount> rows{};
    std::ifstream input(argv[1], std::ios::binary);
    if (!input.read(reinterpret_cast<char*>(rows.data()), sizeof(rows)) ||
        input.peek() != std::char_traits<char>::eof())
        return 2;

    unsigned passed = 0;
    unsigned failed = 0;
    const auto expect = [&](bool result, const char* description) {
        std::printf("%s %s\n", result ? "PASS" : "FAIL", description);
        if (result)
            ++passed;
        else
            ++failed;
    };
    constexpr auto nativeId = 0x0000000402488C23ull;
    const auto id = ptfr::SchedulerId::FromNative(nativeId);
    const auto remaining = ptfr::FindRemainingDelay(rows.data(), rowCount, id);
    expect(id.IsQuestDelay() && id.NodeInstanceValue() == 0x02488C2300000004ull, "scheduler and node ID ordering");
    expect(remaining && std::bit_cast<std::uint32_t>(*remaining) == 0x410F23BD, "exact saved seconds");
    expect(!ptfr::FindRemainingDelay(rows.data(), rowCount, {0, 4}), "invalid serial");
    expect(!ptfr::FindRemainingDelay(rows.data(), rowCount, {id.serial, 5}), "wrong group");
    expect(!ptfr::FindRemainingDelay(rows.data(), rowCount, {id.serial + 1, 4}), "missing timer");
    expect(!ptfr::FindRemainingDelay(nullptr, rowCount, id), "null vector");
    expect(!ptfr::FindRemainingDelay(rows.data(), 0, id), "empty vector");
    expect(!ptfr::FindRemainingDelay(rows.data(), 0x801, id), "over-capacity vector");

    auto* target = &rows[3];
    expect(target->id == id, "fixture row identity");
    rows[8] = *target;
    expect(!ptfr::FindRemainingDelay(rows.data(), rowCount, id), "duplicate timer");
    rows[8] = {};
    target->kind = 2;
    expect(!ptfr::FindRemainingDelay(rows.data(), rowCount, id), "wrong native timer type");
    target->kind = 1;
    target->remainingSeconds = std::numeric_limits<float>::quiet_NaN();
    expect(!ptfr::FindRemainingDelay(rows.data(), rowCount, id), "NaN remaining");
    target->remainingSeconds = std::numeric_limits<float>::infinity();
    expect(!ptfr::FindRemainingDelay(rows.data(), rowCount, id), "infinite remaining");
    target->remainingSeconds = -1;
    expect(!ptfr::FindRemainingDelay(rows.data(), rowCount, id), "negative remaining");
    target->remainingSeconds = 0;
    expect(ptfr::FindRemainingDelay(rows.data(), rowCount, id) == 0, "zero remaining is an observed value");

    int questHandler, otherHandler, delay, otherDelay, facts, otherFacts;
    const ptfr::LiveWait wait{&questHandler, &delay, &facts, nativeId};
    const ptfr::GateTicket direct{&facts, 1, 1};
    const ptfr::GateTicket hanako{&facts, 2, 2};
    ptfr::CutoffObservation capture;
    std::optional<ptfr::GateOutcome> previous;
    const auto begin = [&](const void* manager) { return capture.BeginGateWrite(manager, previous); };
    const auto open = [&](ptfr::GateTicket gate) {
        return capture.Open(gate, begin(gate.facts));
    };
    const auto watch = [&] {
        return capture.Watch(wait, capture.BeginWatch(wait.handler));
    };
    expect(watch(), "finished initialization publishes matching timer");
    expect(!capture.Request(&delay), "native wait alone does not arm capture");
    expect(!open({&facts, 0, 1}) && !open({&facts, 1, 0}), "invalid route and ticket");
    expect(open(direct), "direct Tower capture ticket");
    expect(!capture.Request(&otherDelay), "foreign scheduler");
    const auto first = capture.Request(&delay);
    if (!first || !remaining)
        return 2;
    expect(!capture.Accept(*first, 0, 0) && !capture.Accept(*first, -1, 0) &&
           !capture.Accept(*first, std::numeric_limits<float>::quiet_NaN(), 0), "expired or invalid duration");
    expect(!capture.Accept(*first, *remaining, *remaining) &&
           !capture.Accept(*first, *remaining, *remaining + 1), "due in this worker tick");
    expect(!capture.Accept(*first, *remaining, -1) &&
           !capture.Accept(*first, *remaining, std::numeric_limits<float>::infinity()), "invalid worker tick");
    capture.Invalidate(&otherHandler);
    expect(capture.Accept(*first, *remaining, 0.02f), "exact observed duration with matching live owner");
    expect(!capture.Accept(*first, *remaining, 0) && !capture.Request(&delay), "same ticket cannot sample twice");
    expect(!open(direct), "duplicate open after close");
    expect(previous && previous->gate == direct && previous->sampled, "closing ticket reports observed sample");
    expect(open(hanako), "separate Hanako cutoff ticket");
    const auto second = capture.Request(&delay);
    if (!second)
        return 2;
    capture.Invalidate(&questHandler);
    expect(!capture.Accept(*second, *remaining, 0) && !capture.Request(&delay), "callback or uninitialization invalidates lease");
    const auto racingWatch = capture.BeginWatch(wait.handler);
    capture.Invalidate(wait.handler);
    expect(!capture.Watch(wait, racingWatch) && !capture.Request(&delay), "expiry during initialization rejects late publication");
    watch();
    const auto beforeClose = capture.Request(&delay);
    if (!beforeClose)
        return 2;
    const auto openingWrite = begin(&facts);
    expect(previous && previous->gate == hanako && !previous->sampled, "closing ticket reports missed sample");
    const auto closingWrite = begin(&facts);
    expect(!capture.Open({&facts, 1, 3}, openingWrite), "late opener cannot overtake closing write");
    expect(!capture.Accept(*beforeClose, *remaining, 0), "gate acknowledgement invalidates pending read");
    expect(capture.Open({&otherFacts, 1, 3}, closingWrite) && !capture.Request(&delay), "another save facts manager");
    const auto pendingWrite = begin(&facts);
    const auto pendingWatch = capture.BeginWatch(wait.handler);
    capture.Reset();
    expect(!capture.Open(direct, pendingWrite) && !capture.Request(&delay), "reload invalidates outstanding gate write");
    expect(!capture.Watch(wait, pendingWatch), "reload invalidates outstanding timer initialization");
    expect(open(direct) && !capture.Request(&delay), "reused numeric ticket does not inherit old live wait");
    watch();
    expect(!capture.Accept(*first, *remaining, 0), "reused identities after reload reject an older request");
    std::printf("%u passed, %u failed\n", passed, failed);
    return failed == 0 ? 0 : 1;
}
