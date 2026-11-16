#include "SaveGuard.hpp"

#include <barrier>
#include <cstdio>
#include <thread>

using ptfr::resume::SaveGuard;

int main()
{
    unsigned failures{};
    const auto check = [&](bool condition, const char* message) {
        std::printf("%s %s\n", condition ? "PASS" : "FAIL", message);
        if (!condition)
            ++failures;
    };

    SaveGuard guard;
    {
        const auto first = guard.TrySave();
        {
            const auto second = guard.TrySave();
            check(first && second, "ordinary save permits can overlap");
            check(!guard.TryHandoff(), "in-flight saves defer the handoff");
        }
        check(!guard.TryHandoff(), "ending one capture leaves the other protected");
    }
    {
        auto permit = guard.TryHandoff();
        check(permit && !guard.TrySave() && !guard.TryHandoff(), "handoff excludes new saves and other handoffs");
        std::thread owner([moved = std::move(permit), &guard, &check] {
            check(moved && !guard.TrySave(), "handoff remains protected after ownership moves to another worker");
        });
        owner.join();
        check(!permit && guard.TrySave(), "a save can retry after the last handoff permit is released");
    }

    std::barrier boundary(2);
    bool saveAdmitted{};
    bool handoffAdmitted{};
    constexpr unsigned runs = 128;
    std::thread saver([&] {
        for (unsigned i = 0; i < runs; ++i)
        {
            boundary.arrive_and_wait();
            const auto save = guard.TrySave();
            saveAdmitted = static_cast<bool>(save);
            boundary.arrive_and_wait();
            boundary.arrive_and_wait();
        }
    });
    bool excluded = true;
    for (unsigned i = 0; i < runs; ++i)
    {
        boundary.arrive_and_wait();
        const auto handoff = guard.TryHandoff();
        handoffAdmitted = static_cast<bool>(handoff);
        boundary.arrive_and_wait();
        excluded = excluded && saveAdmitted != handoffAdmitted;
        boundary.arrive_and_wait();
    }
    saver.join();
    check(excluded, "a simultaneous save and handoff never both enter");

    try
    {
        const auto handoff = guard.TryHandoff();
        check(static_cast<bool>(handoff), "guard is idle after racing requests");
        throw 1;
    }
    catch (int)
    {
        check(static_cast<bool>(guard.TrySave()), "unwinding releases the handoff permit");
    }
    return failures ? 1 : 0;
}
