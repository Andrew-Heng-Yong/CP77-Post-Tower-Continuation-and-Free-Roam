#pragma once

#include <atomic>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <optional>
#include <utility>

namespace ptfr
{
template <class T>
T ReadGameTimeField(const void* object, std::size_t offset)
{
    T value{};
    std::memcpy(&value, static_cast<const std::byte*>(object) + offset, sizeof(T));
    return value;
}

struct GameTimeCheckpoint
{
    std::uint32_t seconds;

    static std::optional<GameTimeCheckpoint> Capture(
        std::uint32_t now, std::uint32_t deadline, std::uint32_t authoredSeconds)
    {
        // The observed native kind compares both absolute values as signed
        // 32-bit integers. Defer overdue, wrapped and malformed waits.
        if (now >= deadline || deadline > MaxClock || deadline - now > authoredSeconds)
            return std::nullopt;
        return GameTimeCheckpoint{deadline - now};
    }

    std::optional<std::uint32_t> DeadlineAt(std::uint32_t now) const
    {
        if (!seconds || now > MaxClock || seconds > MaxClock - now)
            return std::nullopt;
        return now + seconds;
    }

    static constexpr auto MaxClock = static_cast<std::uint32_t>(std::numeric_limits<std::int32_t>::max());
};

struct NativeGameTimerReference
{
    void* timer;
    long* count;
};
static_assert(sizeof(long) == 4 && sizeof(NativeGameTimerReference) == 16);

constexpr std::size_t GameTimerList = 0x30130;
constexpr std::size_t GameTimerCount = 0x3008;
constexpr std::uint32_t GameTimerCapacity = 512;

// An empty reference means the ID is absent from a consistent list. An
// empty optional means the list could not be qualified.
inline std::optional<NativeGameTimerReference> FindGameTimer(const void* system, std::uint32_t id)
{
    if (!system || !id)
        return std::nullopt;
    const auto* list = static_cast<const std::byte*>(system) + GameTimerList;
    const auto count = ReadGameTimeField<std::uint32_t>(list, GameTimerCount);
    if (count > GameTimerCapacity)
        return std::nullopt;
    NativeGameTimerReference match{};
    for (std::uint32_t slot = 0; slot < count; ++slot)
    {
        const auto reference = ReadGameTimeField<NativeGameTimerReference>(list, 24 * slot + 0x10);
        if (!reference.timer || !reference.count)
            return std::nullopt;
        if (ReadGameTimeField<std::uint32_t>(reference.timer, 0x88) != id)
            continue;
        if (match.timer)
            return std::nullopt;
        match = reference;
    }
    return match;
}

struct NativeGameTimer
{
    NativeGameTimerReference reference;
    GameTimeCheckpoint wait;
};

// TimeSystem's serial game-clock job owns this list. The owner must already
// resolve to the exact registered handler, and remain valid through the call.
inline std::optional<NativeGameTimer> ReadOneShotGameWait(
    const void* system, std::uint32_t id, std::uint32_t now, std::uint32_t authoredSeconds,
    const void* recordType, const void* initialCallbackType, const void* loadedCallbackType,
    const void* owner)
{
    if (!system || !id || !recordType || !initialCallbackType || !loadedCallbackType || !owner)
        return std::nullopt;
    const auto reference = FindGameTimer(system, id);
    if (!reference || !reference->timer)
        return std::nullopt;
    const auto* timer = reference->timer;
    if (ReadGameTimeField<const void*>(timer, 0) != recordType)
        return std::nullopt;
    const auto* callback = ReadGameTimeField<const void*>(timer, 0x80);
    if (!callback || ReadGameTimeField<std::uint32_t>(timer, 0x44) != 1 ||
        ReadGameTimeField<std::uint8_t>(timer, 0x94) != 0 ||
        ReadGameTimeField<std::uint32_t>(timer, 0x90) != authoredSeconds)
        return std::nullopt;
    const auto* callbackType = ReadGameTimeField<const void*>(callback, 0);
    if (callbackType != initialCallbackType && callbackType != loadedCallbackType)
        return std::nullopt;
    const auto remaining = GameTimeCheckpoint::Capture(
        now, ReadGameTimeField<std::uint32_t>(timer, 0x40), authoredSeconds);
    if (!remaining || ReadGameTimeField<const void*>(callback, 8) != owner)
        return std::nullopt;
    return NativeGameTimer{*reference, *remaining};
}

// Use only on the clock worker with a reserved layout-consistent timer list.
// A native record must be inserted/rebased in deadline order by the caller.
// Stock reload publishes its replacement callback separately.
inline std::optional<std::uint32_t> RebaseOneShotGameWait(
    GameTimeCheckpoint saved, std::uint32_t authoredSeconds, std::uint32_t postTowerClock)
{
    return saved.seconds <= authoredSeconds ? saved.DeadlineAt(postTowerClock) : std::nullopt;
}

struct GameTimeWorkerMethods
{
    void (*remove)(void* system, std::uint32_t id);
    void (*insert)(void* system, const NativeGameTimerReference* timer, std::uint32_t mode);
    void (*release)(NativeGameTimerReference* timer);
};

struct GameTimeOwner
{
    void* system;
    const void* handler;
    std::uint64_t generation;

    bool operator==(const GameTimeOwner&) const = default;
};

// The caller pins the native time-system lifetime and excludes graph/save
// changes during acquisition and rollback. Only value data crosses an owner
// retirement or save boundary. Never return the old callback to a new owner.
class HeldGameTimeWait
{
public:
    HeldGameTimeWait(const HeldGameTimeWait&) = delete;
    HeldGameTimeWait& operator=(const HeldGameTimeWait&) = delete;
    HeldGameTimeWait(HeldGameTimeWait&& other) noexcept
        : timer(std::exchange(other.timer, {})), owner(other.owner), native(other.native),
          id(other.id), wait(other.wait)
    {
    }

    ~HeldGameTimeWait()
    {
        if (timer.timer)
            native.release(&timer);
    }

    static std::optional<HeldGameTimeWait> Take(const GameTimeWorkerMethods& native,
                                               GameTimeOwner owner, std::uint32_t id, std::uint32_t now,
                                               std::uint32_t authoredSeconds, const void* recordType,
                                               const void* initialCallbackType, const void* loadedCallbackType)
    {
        if (!owner.generation)
            return std::nullopt;
        const auto matched = ReadOneShotGameWait(owner.system, id, now, authoredSeconds,
                                                 recordType, initialCallbackType, loadedCallbackType, owner.handler);
        if (!matched)
            return std::nullopt;
        HeldGameTimeWait held(*matched, native, owner, id);
        native.remove(owner.system, id);
        const auto after = FindGameTimer(owner.system, id);
        if (!after || after->timer)
            return std::nullopt;
        return held;
    }

    GameTimeCheckpoint Checkpoint() const { return wait; }

    bool Return(GameTimeOwner current, std::uint32_t clock)
    {
        if (!timer.timer || current != owner)
            return false;
        const auto present = FindGameTimer(owner.system, id);
        const auto deadline = wait.DeadlineAt(clock);
        if (!present || present->timer || !deadline ||
            ReadGameTimeField<std::uint32_t>(owner.system, GameTimerList + GameTimerCount) >= GameTimerCapacity)
            return false;
        std::memcpy(static_cast<std::byte*>(timer.timer) + 0x40, &*deadline, sizeof(*deadline));
        native.insert(owner.system, &timer, 0);
        const auto inserted = FindGameTimer(owner.system, id);
        if (!inserted || inserted->timer != timer.timer)
            return false;
        native.release(&timer);
        timer = {};
        return true;
    }

private:
    HeldGameTimeWait(NativeGameTimer matched, const GameTimeWorkerMethods& methods,
                     GameTimeOwner owner, std::uint32_t id)
        : timer(matched.reference), owner(owner), native(methods), id(id), wait(matched.wait)
    {
        ++std::atomic_ref(*timer.count);
    }

    NativeGameTimerReference timer;
    GameTimeOwner owner;
    GameTimeWorkerMethods native;
    std::uint32_t id;
    GameTimeCheckpoint wait;
};

struct GameTimeCallbackMethods
{
    const void* timerType;
    const void* restoredCallbackType;
    void* (*find)(void* activeList, void* predicate);
    void (*assign)(void* target, void* incoming);
    const void* predicateType;
};

// Stock TimeSystem reload looks up the saved timer by ID and assigns this
// callback to the rebuilt owner. The caller owns that registration and its
// surrounding saved mapping. This routine only binds the native timer.
inline bool AttachLoadedGameTimeCallback(const GameTimeCallbackMethods& native, void* system,
                                         std::uint32_t id, void* handler)
{
    if (!system || !handler || !native.restoredCallbackType || !native.predicateType)
        return false;
    const auto existing = FindGameTimer(system, id);
    if (!existing || !existing->timer ||
        ReadGameTimeField<const void*>(existing->timer, 0) != native.timerType ||
        ReadGameTimeField<const void*>(existing->timer, 0x80))
        return false;

    struct SlotPredicate
    {
        std::uint32_t id;
        std::byte storage[0x3C]{};
        const void* vtable;
    };
    struct QuestCallback
    {
        const void* vtable;
        void* handler;
        std::byte storage[0x28]{};
        const QuestCallback* self;
    };
    static_assert(offsetof(SlotPredicate, vtable) == 0x40);
    static_assert(offsetof(QuestCallback, self) == 0x38);
    SlotPredicate predicate{id, {}, native.predicateType};
    const auto* reference = native.find(static_cast<std::byte*>(system) + GameTimerList, &predicate);
    if (!reference || ReadGameTimeField<void*>(reference, 0) != existing->timer)
        return false;
    QuestCallback callback{native.restoredCallbackType, handler, {}, nullptr};
    callback.self = &callback;
    auto* embedded = static_cast<std::byte*>(existing->timer) + 0x48;
    native.assign(embedded, &callback);
    const auto* stored = ReadGameTimeField<const void*>(existing->timer, 0x80);
    return stored == embedded && ReadGameTimeField<const void*>(stored, 0) == native.restoredCallbackType &&
           ReadGameTimeField<const void*>(stored, 8) == handler;
}
} // namespace ptfr
