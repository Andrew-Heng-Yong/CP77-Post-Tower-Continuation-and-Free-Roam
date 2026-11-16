#pragma once

#include "../universal_resume_eagles_20261114_01/GameTimeWait.hpp"
#include "../universal_resume_save_guard_20261115_01/SaveGuard.hpp"

namespace ptfr::resume
{
using GameTimeFactory = NativeGameTimerReference* (*)(
    NativeGameTimerReference*, const std::uint32_t*, void*, const std::uint32_t*,
    const std::uint32_t*, const std::uint8_t*, const std::uint32_t*, const std::uint64_t*, const std::uint64_t*);

struct GameTimeRestoreOwner
{
    const void* quests;
    const void* timeSystem;
    const void* handler;
    std::uint64_t nodeKey;
    std::uint32_t retiredTimer;
    std::uint32_t authoredSeconds;
};

struct GameTimeRestoreMethods
{
    const void* handlerType;
    const void* timerType;
    const void* initialCallbackType;
    const void* loadedCallbackType;
    bool (*readMapping)(const void*, std::uint64_t, std::uint64_t*);
};

struct GameTimeRestoreReceipt
{
    std::uint32_t id;
    std::uint32_t deadline;

    // Read on the native clock job after the enqueue has been consumed. The
    // caller has revalidated the same session and pinned the replacement owner.
    bool OnClock(const GameTimeRestoreMethods& native, const GameTimeRestoreOwner& owner, std::uint32_t now) const
    {
        const auto timer = ReadOneShotGameWait(owner.timeSystem, id, now, owner.authoredSeconds,
                                              native.timerType, native.initialCallbackType,
                                              native.loadedCallbackType, owner.handler);
        return timer && deadline > now && timer->wait.seconds == deadline - now;
    }
};

// Arm during the selected handler's synchronous native initializer. The quest
// caller pins the owners, holds the save permit through verification, and has
// already drained the old timer and callbacks. The timer factory runs before
// Schedule queues the resulting object. Calls for other owners pass through.
class GameTimeRestoreScope
{
public:
    GameTimeRestoreScope(const SaveGuard::HandoffPermit& permit, GameTimeRestoreMethods native,
                         GameTimeRestoreOwner owner, const void* context, GameTimeCheckpoint checkpoint)
        : native(native), owner(owner), checkpoint(checkpoint)
    {
        if (active || !permit || !context || !owner.quests || !owner.timeSystem || !owner.handler ||
            !owner.nodeKey || !owner.retiredTimer || !checkpoint.seconds || checkpoint.seconds >= owner.authoredSeconds ||
            !native.handlerType || !native.timerType || !native.initialCallbackType ||
            !native.loadedCallbackType || !native.readMapping)
            return;
        if (ReadGameTimeField<const void*>(context, 0x18) != owner.quests ||
            ReadGameTimeField<const void*>(context, 0xE8) != owner.timeSystem ||
            ReadGameTimeField<const void*>(owner.handler, 0) != native.handlerType ||
            ReadGameTimeField<std::uint64_t>(owner.handler, 0x38) != owner.nodeKey ||
            ReadGameTimeField<std::uint32_t>(owner.handler, 0x44) != owner.authoredSeconds ||
            ReadGameTimeField<std::uint32_t>(owner.handler, 0x2C) ||
            ReadGameTimeField<std::uint32_t>(owner.handler, 0x30) ||
            ReadGameTimeField<std::uint32_t>(owner.handler, 0x40))
            return;
        std::uint64_t oldMapping{};
        if (!native.readMapping(owner.quests, owner.nodeKey, &oldMapping))
            active = this;
    }

    GameTimeRestoreScope(const GameTimeRestoreScope&) = delete;
    GameTimeRestoreScope& operator=(const GameTimeRestoreScope&) = delete;
    GameTimeRestoreScope(SaveGuard::HandoffPermit&&, GameTimeRestoreMethods, GameTimeRestoreOwner,
                         const void*, GameTimeCheckpoint) = delete;
    ~GameTimeRestoreScope()
    {
        if (active == this)
            active = nullptr;
    }

    explicit operator bool() const { return active == this; }

    // The caller aborts the unpublished graph through native uninitialization
    // if readback fails. It must not commit solely on the factory returning.
    std::optional<GameTimeRestoreReceipt> Mapped() const
    {
        std::uint64_t id{};
        if (active != this || mismatch || !receipt ||
            ReadGameTimeField<std::uint32_t>(owner.handler, 0x2C) != 0 ||
            ReadGameTimeField<std::uint32_t>(owner.handler, 0x30) != 1 ||
            ReadGameTimeField<std::uint32_t>(owner.handler, 0x40) != receipt->id ||
            !native.readMapping(owner.quests, owner.nodeKey, &id) || id != receipt->id)
            return std::nullopt;
        return receipt;
    }

    static NativeGameTimerReference* MakeTimer(GameTimeFactory original, NativeGameTimerReference* out,
                                              const std::uint32_t* id, void* callback, const std::uint32_t* deadline,
                                              const std::uint32_t* repeats, const std::uint8_t* mode,
                                              const std::uint32_t* authored, const std::uint64_t* label,
                                              const std::uint64_t* source)
    {
        auto* scope = active;
        if (!scope || !callback || ReadGameTimeField<const void*>(callback, 0) != scope->native.initialCallbackType ||
            ReadGameTimeField<const void*>(callback, 8) != scope->owner.handler)
            return original(out, id, callback, deadline, repeats, mode, authored, label, source);

        const auto rebased = scope->Deadline(callback, *id, *deadline, *repeats, *mode, *authored);
        if (!rebased)
        {
            scope->mismatch = true;
            return original(out, id, callback, deadline, repeats, mode, authored, label, source);
        }
        auto* result = original(out, id, callback, &*rebased, repeats, mode, authored, label, source);
        if (result == out && out->timer && out->count && scope->MatchesTimer(out->timer, *id, *rebased))
            scope->receipt = GameTimeRestoreReceipt{*id, *rebased};
        else
            scope->mismatch = true;
        return result;
    }

private:
    std::optional<std::uint32_t> Deadline(const void* callback, std::uint32_t id, std::uint32_t stock,
                                         std::uint32_t repeats, std::uint8_t mode, std::uint32_t authored) const
    {
        if (receipt || mismatch || !id || id == owner.retiredTimer || repeats != 1 || mode != 0 ||
            authored != owner.authoredSeconds || stock < authored ||
            ReadGameTimeField<const void*>(callback, 0x38) != callback)
            return std::nullopt;
        return checkpoint.DeadlineAt(stock - authored);
    }

    bool MatchesTimer(const void* timer, std::uint32_t id, std::uint32_t deadline) const
    {
        const auto* callback = ReadGameTimeField<const void*>(timer, 0x80);
        return ReadGameTimeField<const void*>(timer, 0) == native.timerType &&
               ReadGameTimeField<std::uint32_t>(timer, 0x40) == deadline &&
               ReadGameTimeField<std::uint32_t>(timer, 0x44) == 1 &&
               ReadGameTimeField<std::uint32_t>(timer, 0x88) == id &&
               ReadGameTimeField<std::uint32_t>(timer, 0x90) == owner.authoredSeconds &&
               ReadGameTimeField<std::uint8_t>(timer, 0x94) == 0 &&
               callback == static_cast<const std::byte*>(timer) + 0x48 &&
               ReadGameTimeField<const void*>(callback, 0) == native.initialCallbackType &&
               ReadGameTimeField<const void*>(callback, 8) == owner.handler;
    }

    static inline thread_local GameTimeRestoreScope* active{};
    const GameTimeRestoreMethods native;
    const GameTimeRestoreOwner owner;
    const GameTimeCheckpoint checkpoint;
    std::optional<GameTimeRestoreReceipt> receipt;
    bool mismatch{};
};
} // namespace ptfr::resume
