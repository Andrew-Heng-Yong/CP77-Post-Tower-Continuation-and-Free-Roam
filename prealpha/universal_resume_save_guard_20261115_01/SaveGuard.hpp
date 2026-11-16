#pragma once

#include <atomic>
#include <cstdint>
#include <utility>

namespace ptfr::resume
{
// Hold a save permit from admission until capture finishes. Hold a handoff
// permit from the first edit until the quest and clocks are coherent again.
// Permits can transfer between workers. Neither acquisition waits.
class SaveGuard
{
    static constexpr std::uint32_t Handoff = UINT32_MAX;

    template<bool ForHandoff>
    class Permit
    {
    public:
        Permit() = default;
        Permit(const Permit&) = delete;
        Permit& operator=(const Permit&) = delete;
        Permit(Permit&& other) noexcept : guard(std::exchange(other.guard, nullptr)) {}
        Permit& operator=(Permit&&) = delete;
        ~Permit()
        {
            if (!guard)
                return;
            if constexpr (ForHandoff)
                guard->state.store(0);
            else
                --guard->state;
        }

        explicit operator bool() const { return guard != nullptr; }

    private:
        friend class SaveGuard;
        explicit Permit(SaveGuard& guard) : guard(&guard) {}
        SaveGuard* guard{};
    };

public:
    using SavePermit = Permit<false>;
    using HandoffPermit = Permit<true>;

    [[nodiscard]] SavePermit TrySave()
    {
        auto readers = state.load();
        while (readers < Handoff - 1)
            if (state.compare_exchange_weak(readers, readers + 1))
                return SavePermit(*this);
        return {};
    }

    [[nodiscard]] HandoffPermit TryHandoff()
    {
        std::uint32_t idle{};
        if (state.compare_exchange_strong(idle, Handoff))
            return HandoffPermit(*this);
        return {};
    }

private:
    std::atomic<std::uint32_t> state{};
};
} // namespace ptfr::resume
