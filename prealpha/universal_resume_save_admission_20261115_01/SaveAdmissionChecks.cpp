#include "SaveAdmission.hpp"

#include <array>
#include <cstdio>

namespace
{
using ptfr::resume::SaveAdmission;
using Engine = std::array<std::uint8_t, 0x309>;
constexpr auto Flags = 0x308;
constexpr auto Busy = 0x10;
constexpr auto Preflight = 0x20;

enum class Request { None, Manual, Automatic };

struct Jobs
{
    SaveAdmission& admission;
    Engine& expectedEngine;
    Request pending{};
    Request captured{};
    int polls{};
    int submissions{};
    bool initialHandoff{};
    bool receivedEngine{};
};

void Dispatch(void* engine, void* jobs)
{
    auto& request = *static_cast<Jobs*>(jobs);
    request.receivedEngine = engine == request.expectedEngine.data();
    ++request.polls;
    request.initialHandoff = static_cast<bool>(request.admission.TryHandoff(engine));
    auto& flags = request.expectedEngine[Flags];
    if ((flags & Busy) || request.pending == Request::None)
        return;
    flags |= Busy;
    request.captured = std::exchange(request.pending, Request::None);
    ++request.submissions;
}
} // namespace

int main()
{
    SaveAdmission admission;
    Engine engine{};
    auto& flags = engine[Flags];
    Jobs jobs{admission, engine};
    const auto poll = [&] { admission.Poll(Dispatch, engine.data(), &jobs); };
    int failed{};
    const auto check = [&](bool condition, const char* name) {
        std::printf("%s %s\n", condition ? "PASS" : "FAIL", name);
        failed += !condition;
    };

    check(!admission.TryHandoff(nullptr), "missing engine declines the handoff");
    jobs.pending = Request::Manual;
    {
        auto handoff = admission.TryHandoff(engine.data());
        check(!!handoff, "idle engine grants the handoff");
        check(!admission.TryHandoff(engine.data()), "concurrent handoff is declined");
        poll();
        poll();
        check(jobs.polls == 0 && jobs.pending == Request::Manual && !flags,
              "an already queued manual request is left untouched");
    }
    poll();
    check(jobs.receivedEngine && jobs.polls == 1 && jobs.submissions == 1 &&
              jobs.captured == Request::Manual && jobs.pending == Request::None,
          "native dispatcher receives the original arguments and submits once");
    check(!jobs.initialHandoff, "dispatcher holds its permit before publishing busy");
    check(!admission.TryHandoff(engine.data()), "native save stays protected after the dispatcher returns");

    jobs.pending = Request::Automatic;
    poll();
    check(jobs.polls == 2 && jobs.submissions == 1 && jobs.pending == Request::Automatic,
          "the stock busy check governs the next queued request");
    flags = Preflight;
    {
        auto handoff = admission.TryHandoff(engine.data());
        check(!!handoff && flags == Preflight, "completion reopens handoff with the preflight bit present");
        poll();
        check(jobs.polls == 2 && jobs.pending == Request::Automatic && flags == Preflight,
              "automatic request and preflight state survive deferral");
    }
    poll();
    check(jobs.polls == 3 && jobs.submissions == 2 && jobs.captured == Request::Automatic &&
              jobs.pending == Request::None && flags == (Preflight | Busy),
          "the next native update consumes the deferred automatic request once");
    flags = Preflight;
    poll();
    check(jobs.submissions == 2 && !!admission.TryHandoff(engine.data()),
          "an empty poll releases the guard without duplicating a save");
    return failed != 0;
}
