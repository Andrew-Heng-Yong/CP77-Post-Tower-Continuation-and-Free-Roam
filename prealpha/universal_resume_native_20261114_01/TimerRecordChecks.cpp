#include <array>
#include <bit>
#include <cstdio>
#include <fstream>
#include <limits>

#include "TimerRecord.hpp"

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
    std::printf("%u passed, %u failed\n", passed, failed);
    return failed == 0 ? 0 : 1;
}
