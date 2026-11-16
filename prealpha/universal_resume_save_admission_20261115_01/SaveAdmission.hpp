#pragma once

#include "../universal_resume_save_guard_20261115_01/SaveGuard.hpp"

namespace ptfr::resume
{
class SaveAdmission
{
    static constexpr auto SaveState = 0x308;
    static constexpr auto SaveInProgress = 0x10;

public:
    using Dispatcher = void (*)(void* engine, void* jobs);

    void Poll(Dispatcher original, void* engine, void* jobs)
    {
        const auto permit = guard.TrySave();
        if (permit)
            original(engine, jobs);
    }

    [[nodiscard]] SaveGuard::HandoffPermit TryHandoff(const void* engine)
    {
        if (!engine)
            return {};
        auto permit = guard.TryHandoff();
        if (!permit)
            return {};

        // The dispatcher sets this bit before it schedules capture. Native
        // completion clears it after the save job, outside the dispatch permit.
        const auto* state = static_cast<const volatile std::uint8_t*>(engine) + SaveState;
        if (*state & SaveInProgress)
            return {};
        return permit;
    }

private:
    SaveGuard guard;
};
} // namespace ptfr::resume
