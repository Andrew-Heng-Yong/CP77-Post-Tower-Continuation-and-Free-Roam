#include "OwnerTrace.hpp"
#include "../universal_resume_handoff_20261114_01/CutoffObservation.hpp"

#include <cstdio>
#include <string_view>

template <class T, std::size_t Size>
void Set(std::array<std::byte, Size>& object, std::size_t offset, const T& value)
{
    std::memcpy(object.data() + offset, &value, sizeof(value));
}

int main()
{
    unsigned passed = 0;
    unsigned failed = 0;
    const auto expect = [&](bool condition, const char* name) {
        std::printf("%s %s\n", condition ? "PASS" : "FAIL", name);
        condition ? ++passed : ++failed;
    };
    using namespace ptfr;

    std::array<std::byte, 0xA0> phase{};
    for (const auto& watch : HasanPhases)
    {
        Set(phase, 0x70, watch.path.data());
        Set(phase, 0x7C, static_cast<std::uint32_t>(watch.path.size()));
        const auto address = CopyPhaseAddress(phase.data());
        expect(address && FindWatchedPhase(*address) == &watch, watch.name);
    }
    expect(PhaseHash(HasanWorld) == 0x9A66DFB6 && PhaseHash(HasanBugfix) == 0xDE605479 &&
               PhaseHash(HasanS23World) == 0x617629A2, "the same quest depot has three distinct phase hashes");
    expect(PhaseHash(HasanNativeDialog) == 0xA53D960C && PhaseHash(HasanS23Dialog) == 0x2993E68E,
           "the two default-dialogue owners have different phase hashes");
    auto similar = HasanWorld;
    similar[4] = 15;
    Set(phase, 0x70, similar.data());
    Set(phase, 0x7C, static_cast<std::uint32_t>(similar.size()));
    expect(!FindWatchedPhase(*CopyPhaseAddress(phase.data())), "a different ancestor cannot match a watched phase");
    Set(phase, 0x7C, std::uint32_t{17});
    expect(!CopyPhaseAddress(phase.data()), "overlength native phase path rejected");
    Set(phase, 0x7C, std::uint32_t{2});
    Set(phase, 0x70, static_cast<const std::uint16_t*>(nullptr));
    expect(!CopyPhaseAddress(phase.data()) && !CopyPhaseAddress(nullptr), "absent native path rejected");

    RegistrationRow rows[]{{1, PhaseHash(HasanWorld), 69}, {2, PhaseHash(HasanS23World), 69}, {0, 0, 0xFFFF}};
    std::array<std::byte, 0x30> events{};
    Set(events, 8, static_cast<RegistrationRow*>(rows));
    Set(events, 0x14, std::uint32_t{3});
    expect(MatchesRegistration(events.data(), 0, PhaseHash(HasanWorld), 69, 1), "physical slot matches its logical owner");
    expect(!MatchesRegistration(events.data(), 0, PhaseHash(HasanS23World), 69, 1), "another owner of the same wait is distinct");
    expect(!MatchesRegistration(events.data(), 0, PhaseHash(HasanWorld), 69, 2), "registration type mismatch rejected");
    expect(!CopyRegistration(events.data(), 2) && !CopyRegistration(events.data(), 3), "cleared and out-of-range slots rejected");
    const auto before = CopyRegistration(events.data(), 0);
    rows[0] = rows[1];
    expect(before && before->phaseHash == PhaseHash(HasanWorld) &&
               !MatchesRegistration(events.data(), 0, PhaseHash(HasanWorld), 69, 1), "reused slot does not change the retirement sample");

    const void* children[]{phase.data(), nullptr, events.data(), nullptr};
    const auto* target = children[0];
    Set(phase, 0x88, static_cast<const void**>(children));
    Set(phase, 0x94, std::uint32_t{2});
    expect(HasChild(phase.data(), target) == true, "registered native child found");
    children[0] = children[2];
    Set(phase, 0x94, std::uint32_t{1});
    expect(HasChild(phase.data(), target) == false && HasChild(phase.data(), children[0]) == true,
           "erased child distinguished from the adjacent live owner");
    Set(phase, 0x88, static_cast<const void*>(nullptr));
    expect(!HasChild(phase.data(), target), "invalid child vector reports unknown");

    alignas(std::uint32_t) std::array<std::byte, 0x60> handler{};
    Set(handler, 0x2C, std::uint32_t{1});
    expect(HandlerReady(handler.data()), "a completed timer is ineligible for cutoff sampling");
    Set(handler, 0x2C, std::uint32_t{0});
    expect(!HandlerReady(handler.data()), "a still-pending handler can be sampled");

    int alternative{}, scheduler{}, facts{};
    CutoffObservation openWorld;
    CutoffObservation bugfix;
    constexpr std::uint64_t firstTimer = 0x0000000400000123;
    constexpr std::uint64_t secondTimer = 0x0000000400000456;
    openWorld.Watch({handler.data(), &scheduler, &facts, firstTimer}, openWorld.BeginWatch(handler.data()));
    bugfix.Watch({&alternative, &scheduler, &facts, secondTimer}, bugfix.BeginWatch(&alternative));
    std::optional<GateOutcome> previous;
    const GateTicket gate{&facts, 1, 19};
    openWorld.Open(gate, openWorld.BeginGateWrite(&facts, previous));
    bugfix.Open(gate, bugfix.BeginGateWrite(&facts, previous));
    const auto worldRequest = openWorld.Request(&scheduler);
    const auto bugfixRequest = bugfix.Request(&scheduler);
    expect(worldRequest && bugfixRequest && worldRequest->wait.timer != bugfixRequest->wait.timer,
           "overlapping owners keep independent cutoff requests");
    bugfix.Invalidate(&alternative);
    expect(worldRequest && bugfixRequest && openWorld.Accept(*worldRequest, 30.0f, 0.016f) &&
               !bugfix.Accept(*bugfixRequest, 40.0f, 0.016f), "retiring one owner revokes only its request");

    std::printf("%u passed, %u failed\n", passed, failed);
    return failed ? 1 : 0;
}
