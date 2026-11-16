#include "SaveWindow.hpp"

#include <cstdio>
#include <latch>
#include <thread>

using ptfr::resume::SaveComponent;
using ptfr::resume::SaveWindow;

int main()
{
    unsigned failures{};
    const auto check = [&](bool condition, const char* description) {
        std::printf("%s %s\n", condition ? "PASS" : "FAIL", description);
        if (!condition)
            ++failures;
    };

    SaveWindow window;
    check(window.Active() == 0 && !window.Record(SaveComponent::Quests) && window.Unscoped() == 1,
          "writer without a SaveSystems call is reported as unscoped");
    {
        const SaveWindow::Capture outer(window);
        check(window.Active() == 1 && window.Record(SaveComponent::Quests) && outer.Read().components == 1,
              "quest writer belongs to the current system save");
        {
            const SaveWindow::Capture nested(window);
            check(window.Active() == 2 && window.Record(SaveComponent::GameClock) &&
                      nested.Read().id != outer.Read().id && nested.Read().components == 4 &&
                      outer.Read().components == 1,
                  "nested writer reports to its own window");
        }
        check(window.Active() == 1 && window.Record(SaveComponent::RealClock) &&
                  window.Record(SaveComponent::GameClock) && outer.Read().components == 7,
              "outer window resumes and accounts for quests and both clocks");
        check(window.Record(SaveComponent::Quests) && outer.Read().duplicates == 1,
              "duplicate native writer remains visible");
    }
    check(window.Active() == 0, "finished native window releases its occupancy");

    std::latch started(1);
    std::latch release(1);
    std::uint64_t concurrentId{};
    unsigned concurrentWriters{};
    std::thread other([&] {
        const SaveWindow::Capture capture(window);
        window.Record(SaveComponent::RealClock);
        started.count_down();
        release.wait();
        concurrentId = capture.Read().id;
        concurrentWriters = capture.Read().components;
    });
    started.wait();
    std::uint64_t mainId{};
    {
        const SaveWindow::Capture capture(window);
        mainId = capture.Read().id;
        check(window.Active() == 2 && window.Record(SaveComponent::Quests) && capture.Read().components == 1,
              "native writers on overlapping threads keep separate scopes");
    }
    check(window.Active() == 1, "a completed save does not end the other worker's capture");
    release.count_down();
    other.join();
    check(window.Active() == 0 && concurrentId != mainId && concurrentWriters == 2 && window.Unscoped() == 1,
          "each worker publishes its own identity and writers");

    try
    {
        const SaveWindow::Capture interrupted(window);
        throw 1;
    }
    catch (int)
    {
        check(window.Active() == 0 && !window.Record(SaveComponent::GameClock) && window.Unscoped() == 2,
              "unwinding leaves no stale save window");
    }
    return failures ? 1 : 0;
}
