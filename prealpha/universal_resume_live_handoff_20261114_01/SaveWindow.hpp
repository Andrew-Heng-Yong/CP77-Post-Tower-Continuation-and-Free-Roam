#pragma once

#include <atomic>
#include <cstdint>

namespace ptfr::resume
{
enum class SaveComponent : unsigned { Quests = 1, RealClock = 2, GameClock = 4 };

// A worker-local envelope ties each serialized subsystem to the exact
// SaveSystems invocation that called it. Across workers, keep an active count
// so one completion cannot make a concurrent writer look idle.
class SaveWindow
{
public:
    struct Result
    {
        std::uint64_t id;
        unsigned components;
        unsigned duplicates;
    };

    class Capture
    {
    public:
        explicit Capture(SaveWindow& owner)
            : owner(owner), enclosing(current), id(++owner.sequence)
        {
            ++owner.active;
            current = this;
        }

        Capture(const Capture&) = delete;
        Capture& operator=(const Capture&) = delete;
        ~Capture()
        {
            current = enclosing;
            --owner.active;
        }

        Result Read() const { return {id, components, duplicates}; }

    private:
        friend class SaveWindow;
        SaveWindow& owner;
        Capture* const enclosing;
        const std::uint64_t id;
        unsigned components{};
        unsigned duplicates{};
    };

    bool Record(SaveComponent component)
    {
        if (!current || &current->owner != this)
        {
            ++unscoped;
            return false;
        }
        const auto bit = static_cast<unsigned>(component);
        current->duplicates |= current->components & bit;
        current->components |= bit;
        return true;
    }

    unsigned Active() const { return active.load(); }
    std::uint64_t Unscoped() const { return unscoped.load(); }

private:
    inline static thread_local Capture* current{};
    std::atomic<unsigned> active{};
    std::atomic<std::uint64_t> unscoped{};
    std::atomic<std::uint64_t> sequence{};
};
} // namespace ptfr::resume
