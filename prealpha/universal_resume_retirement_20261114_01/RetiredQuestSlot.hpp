#pragma once

#include "../universal_resume_owner_20261114_01/OwnerTrace.hpp"

#include <utility>

namespace ptfr
{
// One counter for a quest-system lifetime. Its observer advances it only after
// the serial native notification worker returns from a complete dispatch pass.
class QuestNotificationDrain
{
public:
    explicit QuestNotificationDrain(std::uint64_t session) : session(session) {}

    std::uint64_t Session() const { return session; }
    std::uint64_t Completed() const { return completed.load(); }
    void CompletePass() { ++completed; }

private:
    const std::uint64_t session;
    std::atomic<std::uint64_t> completed{0};
};

struct QuestSlotMethods
{
    using Retire = void (*)(void*, std::uint32_t);
    using Lock = void (*)(std::uint8_t*);
    using Append = void (*)(void*, const std::uint32_t*);

    Retire retire;
    Lock lock;
    Append append;
};

enum class RetiredSlotStatus
{
    Deferred,
    CallbacksPending,
    AwaitingDrain,
    Released
};

// Call from the native graph owner with competing graph changes excluded.
// Pin the quest-system lifecycle. Exclude saves until the queue is clean and
// callback producers are quiescent. The destructor does not touch native state.
class RetiredQuestSlot
{
public:
    RetiredQuestSlot(const RetiredQuestSlot&) = delete;
    RetiredQuestSlot& operator=(const RetiredQuestSlot&) = delete;
    RetiredQuestSlot(RetiredQuestSlot&& other) noexcept
        : quests(std::exchange(other.quests, nullptr)), events(other.events),
          slot(other.slot), session(other.session), previous(other.previous),
          purgedAfterPass(other.purgedAfterPass)
    {
    }

    // Preserve native retirement even if the selected registration can no
    // longer be reserved. On failure the caller defers exact continuation.
    static std::optional<RetiredQuestSlot> Retire(
        const QuestSlotMethods& native, void* events, std::uint32_t slot, const QuestNotificationDrain& drain)
    {
        const auto before = CopyRegistration(events, slot);
        native.retire(events, slot);
        if (!before || !drain.Session() || !IsCleared(events, slot))
            return std::nullopt;

        auto* quests = NativeField<void*>(events, 0x28);
        auto& free = Field<Slots>(events, 0x18);
        if (!quests || NativeField<const void*>(quests, 0xE8) != events || !free.Valid() ||
            !free.count || free.data[free.count - 1] != slot ||
            std::ranges::count(free.Values(), slot) != 1)
            return std::nullopt;

        --free.count;
        return RetiredQuestSlot(quests, events, slot, drain.Session(), *before);
    }

    // Use only after all producers for the retired slot have stopped. Removing
    // every match keeps stale physical indices out of QueuedData on save. The
    // copied worker batch is separate and must finish before slot reuse.
    RetiredSlotStatus Settle(const QuestSlotMethods& native, void* currentQuests,
                             const QuestNotificationDrain& drain, bool callbacksStopped)
    {
        if (!quests || currentQuests != quests || drain.Session() != session ||
            NativeField<const void*>(quests, 0xE8) != events || !IsCleared(events, slot))
            return RetiredSlotStatus::Deferred;
        auto& free = Field<Slots>(events, 0x18);
        if (!free.Valid() || free.Contains(slot))
            return RetiredSlotStatus::Deferred;
        if (!callbacksStopped)
        {
            purgedAfterPass.reset();
            return RetiredSlotStatus::CallbacksPending;
        }

        {
            QueueLock lock(native, Field<std::uint8_t>(quests, 0x150));
            auto& pending = Field<Slots>(quests, 0x158);
            if (!pending.Valid())
                return RetiredSlotStatus::Deferred;
            const auto kept = std::ranges::remove(pending.Values(), slot);
            if (!purgedAfterPass || !kept.empty())
            {
                // A worker could have copied an old notification before the
                // purge. Count only passes after the last observed enqueue.
                purgedAfterPass = drain.Completed();
            }
            pending.count -= static_cast<std::uint32_t>(kept.size());
        }
        if (drain.Completed() <= *purgedAfterPass)
            return RetiredSlotStatus::AwaitingDrain;

        native.append(&free, &slot);
        if (!free.Valid() || !free.count || free.data[free.count - 1] != slot)
            return RetiredSlotStatus::Deferred;
        quests = nullptr;
        return RetiredSlotStatus::Released;
    }

    const RegistrationRow& PreviousRegistration() const { return previous; }

private:
    struct Slots
    {
        std::uint32_t* data;
        std::uint32_t capacity;
        std::uint32_t count;

        bool Valid() const { return count <= capacity && (!capacity || data); }
        std::span<std::uint32_t> Values() const { return {data, count}; }
        bool Contains(std::uint32_t slot) const
        {
            const auto indices = Values();
            return std::ranges::find(indices, slot) != indices.end();
        }
    };
    static_assert(sizeof(Slots) == 0x10);

    class QueueLock
    {
    public:
        QueueLock(const QuestSlotMethods& native, std::uint8_t& lock) : lock(lock) { native.lock(&lock); }
        QueueLock(const QueueLock&) = delete;
        QueueLock& operator=(const QueueLock&) = delete;
        ~QueueLock() { std::atomic_ref(lock).store(0, std::memory_order_release); }

    private:
        std::uint8_t& lock;
    };

    RetiredQuestSlot(void* quests, void* events, std::uint32_t slot,
                     std::uint64_t session, RegistrationRow previous)
        : quests(quests), events(events), slot(slot), session(session), previous(previous)
    {
    }

    static bool IsCleared(const void* events, std::uint32_t slot)
    {
        if (slot >= NativeField<std::uint32_t>(events, 0x14))
            return false;
        const auto* rows = NativeField<const RegistrationRow*>(events, 8);
        return rows && rows[slot].type == 0 && rows[slot].phaseHash == 0 && rows[slot].node == 0xFFFF;
    }

    template <class T>
    static T& Field(void* object, std::size_t offset)
    {
        return *reinterpret_cast<T*>(static_cast<std::byte*>(object) + offset);
    }

    void* quests;
    void* events;
    std::uint32_t slot;
    std::uint64_t session;
    RegistrationRow previous;
    std::optional<std::uint64_t> purgedAfterPass;
};
} // namespace ptfr
