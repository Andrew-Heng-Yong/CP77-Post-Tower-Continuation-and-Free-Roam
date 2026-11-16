#include "RetiredQuestSlot.hpp"

#include <array>
#include <cstddef>

namespace
{
using Status = ptfr::RetiredSlotStatus;
constexpr auto OldSlot = 3U;
constexpr std::uint64_t OldType = 0x1122334455667788;
constexpr std::uint64_t NewType = 0x8877665544332211;
constexpr std::uint64_t OldKey = 0x000000051361AA1A;
constexpr std::uint64_t NewKey = 0x000000245B784885;

struct Vector
{
    std::uint32_t* data;
    std::uint32_t capacity;
    std::uint32_t count;
};

using SpinLock = ptfr::QuestSlotMethods::Lock;
SpinLock lockQuestByte;
std::uint8_t* beforeGraphLock;
void (*beforeGraphAcquire)();

std::uint8_t** ObserveQuestLock(std::uint8_t** observed, std::uint8_t* lock)
{
    // The original wrapper only stores the byte address and calls the native
    // lock. Insert one deterministic interleaving before graph-lock acquire.
    if (beforeGraphLock == lock)
    {
        beforeGraphLock = nullptr;
        beforeGraphAcquire();
    }
    *observed = lock;
    lockQuestByte(lock);
    return observed;
}

class GraphFixture
{
public:
    explicit GraphFixture(const Slices& native)
        : methods{native.At<ptfr::QuestSlotMethods::Retire>(0x2FCFD0),
                  native.At<ptfr::QuestSlotMethods::Lock>(0x22CA300),
                  native.At<ptfr::QuestSlotMethods::Append>(0x1E07BC)},
          appendRegistration(native.At<std::uint32_t (*)(void*, std::uint64_t, const std::uint64_t*)>(0xEB6B3C)),
          nativeDrain(native.At<void (*)(void*)>(0x3534DC)),
          enqueue(native.At<void (*)(void*, std::uint32_t)>(0x88BC58))
    {
        questMethods[0x2B0 / 8] = native.At<std::uintptr_t>(0x2FD1BC);
        Field<void*>(quests.data(), 0) = questMethods.data();
        Field<void*>(quests.data(), 0xE8) = events.data();
        Field<void*>(events.data(), 8) = rows.data();
        Field<std::uint32_t>(events.data(), 0x10) = static_cast<std::uint32_t>(rows.size());
        Field<std::uint32_t>(events.data(), 0x14) = OldSlot + 1;
        Field<void*>(events.data(), 0x28) = quests.data();
        Pending() = {notifications.data(), static_cast<std::uint32_t>(notifications.size()), 0};
        Free() = {freeSlots.data(), static_cast<std::uint32_t>(freeSlots.size()), 0};
        Field<Vector>(quests.data(), 0x168) = {markers.data(), static_cast<std::uint32_t>(markers.size()), 0};
        rows[OldSlot] = {OldType, static_cast<std::uint32_t>(OldKey), static_cast<std::uint32_t>(OldKey >> 32)};
    }

    void Queue(std::uint32_t slot) { enqueue(quests.data(), slot); }
    std::uint32_t Register() { return appendRegistration(events.data(), NewType, &NewKey); }
    std::optional<ptfr::RetiredQuestSlot> Retire()
    {
        return ptfr::RetiredQuestSlot::Retire(methods, events.data(), OldSlot, drain);
    }
    Status Settle(ptfr::RetiredQuestSlot& reservation, bool stopped)
    {
        return reservation.Settle(methods, quests.data(), drain, stopped);
    }
    void RunDrain()
    {
        nativeDrain(quests.data());
        drain.CompletePass();
    }
    void ReloadFreeSlots(const Slices& native)
    {
        Free().count = 0;
        native.At<void (*)(void*)>(0xCC5844)(events.data());
    }
    Vector& Pending() { return Field<Vector>(quests.data(), 0x158); }
    Vector& Free() { return Field<Vector>(events.data(), 0x18); }

    ptfr::QuestSlotMethods methods;
    ptfr::QuestNotificationDrain drain{1};
    std::array<ptfr::RegistrationRow, 8> rows{};
    alignas(8) std::array<std::byte, 0x180> quests{};
    alignas(8) std::array<std::byte, 0x40> events{};

private:
    std::array<std::uintptr_t, 0x2B8 / 8> questMethods{};
    std::array<std::uint32_t, 8> notifications{};
    std::array<std::uint32_t, 8> freeSlots{};
    std::array<std::uint32_t, 8> markers{};
    std::uint32_t (*appendRegistration)(void*, std::uint64_t, const std::uint64_t*);
    void (*nativeDrain)(void*);
    void (*enqueue)(void*, std::uint32_t);
};

struct CopiedNotification
{
    Checks& test;
    GraphFixture& graph;
    std::optional<ptfr::RetiredQuestSlot> reservation;
};

CopiedNotification* copiedNotification;

void RetireAfterCopy()
{
    auto& [test, graph, reservation] = *copiedNotification;
    test.Expect(graph.Pending().count == 0 && Field<std::uint8_t>(graph.quests.data(), 0x150) == 0 &&
                    Field<std::uint8_t>(graph.quests.data(), 0x60) == 0,
                "native worker copied the old notification and released its queue lock before graph dispatch");
    // Repeat the notification in the shared queue after copying. The native
    // removal finds a match and therefore adds no deferred retirement marker.
    graph.Queue(OldSlot);
    graph.Queue(OldSlot);
    const auto graphLock = &Field<std::uint8_t>(graph.quests.data(), 0x60);
    graph.methods.lock(graphLock);
    auto retired = graph.Retire();
    if (retired)
        reservation.emplace(std::move(*retired));
    if (test.Expect(reservation && graph.Settle(*reservation, true) == Status::AwaitingDrain &&
                        graph.Free().count == 0 && graph.Pending().count == 0 &&
                        Field<Vector>(graph.quests.data(), 0x168).count == 0,
                    "retirement purges live duplicates and reserves the copied slot without a native marker"))
    {
        // Force the native registration path before allowing the worker to
        // resolve its copied work. Any reuse here would resolve to NewKey.
        test.Expect(graph.Register() == OldSlot + 1,
                    "replacement registration cannot claim a slot in the copied batch");
    }
    std::atomic_ref(*graphLock).store(0, std::memory_order_release);
}

void CheckRetiredSlots(Checks& test, const Slices& native)
{
    GraphFixture stock(native);
    stock.Queue(OldSlot);
    stock.Queue(OldSlot);
    stock.methods.retire(stock.events.data(), OldSlot);
    test.Expect(stock.Pending().count == 1 && stock.Pending().data[0] == OldSlot,
                "stock retirement leaves a second physical notification in the shared queue");
    const auto reused = stock.Register();
    test.Expect(reused == OldSlot && stock.rows[OldSlot].type == NewType &&
                    stock.Pending().data[0] == reused,
                "stock registration can immediately give that physical slot to another owner");

    GraphFixture graph(native);
    graph.Queue(OldSlot);
    graph.Queue(OldSlot);
    graph.Queue(1);
    auto reservation = graph.Retire();
    if (!test.Expect(reservation && graph.Free().count == 0 &&
                    !ptfr::CopyRegistration(graph.events.data(), OldSlot),
                    "selected retirement keeps native row removal and reserves the detached slot"))
        return;
    const auto& previous = reservation->PreviousRegistration();
    test.Expect(previous.type == OldType && previous.phaseHash == static_cast<std::uint32_t>(OldKey) &&
                    previous.node == static_cast<std::uint32_t>(OldKey >> 32),
                "the handoff keeps the original registration identity");
    const auto unrelated = graph.Register();
    test.Expect(unrelated == OldSlot + 1 && graph.rows[unrelated].type == NewType,
                "an unrelated native registration gets a distinct slot during the hold");

    test.Expect(graph.Settle(*reservation, false) == Status::CallbacksPending &&
                    graph.Pending().count == 2 && graph.Free().count == 0,
                "native unregistration alone does not certify that callbacks are quiet");
    graph.Queue(OldSlot);
    graph.Queue(2);
    graph.drain.CompletePass(); // An earlier completed pass cannot cover a later purge.
    const ptfr::QuestNotificationDrain previousSession(2);
    test.Expect(reservation->Settle(graph.methods, graph.quests.data(), previousSession, true) == Status::Deferred &&
                    graph.Pending().count == 4,
                "a reused quest-system address in a different session does not qualify");

    test.Expect(graph.Settle(*reservation, true) == Status::AwaitingDrain && graph.Free().count == 0,
                "even an earlier drain cannot release the slot until one finishes after the purge");
    test.Expect(graph.Pending().count == 2 && graph.Pending().data[0] == 1 && graph.Pending().data[1] == 2 &&
                    Field<std::uint8_t>(graph.quests.data(), 0x150) == 0,
                "the locked purge leaves unrelated notifications in order and releases the lock");
    test.Expect(graph.Settle(*reservation, true) == Status::AwaitingDrain && graph.Free().count == 0,
                "a retry in the same worker pass leaves the slot reserved");
    graph.RunDrain();
    test.Expect(graph.Settle(*reservation, true) == Status::Released &&
                    graph.Free().count == 1 && graph.Free().data[0] == OldSlot,
                "the completed native worker pass releases the slot once");
    test.Expect(graph.Settle(*reservation, true) == Status::Deferred && graph.Free().count == 1,
                "a repeated handoff cannot add the free index twice");
    test.Expect(graph.Register() == OldSlot && graph.rows[OldSlot].phaseHash == static_cast<std::uint32_t>(NewKey) &&
                    graph.Pending().count == 0,
                "native registration safely reuses the released slot with no retired notification");

    GraphFixture copied(native);
    CopiedNotification interleave{test, copied, {}};
    copied.Queue(OldSlot);
    copiedNotification = &interleave;
    beforeGraphAcquire = &RetireAfterCopy;
    beforeGraphLock = &Field<std::uint8_t>(copied.quests.data(), 0x60);
    copied.RunDrain();
    copiedNotification = nullptr;
    test.Expect(!beforeGraphLock && interleave.reservation &&
                    copied.Settle(*interleave.reservation, true) == Status::Released &&
                    copied.Register() == OldSlot,
                "the worker skips the retired row and releases its copied slot before reuse");

    GraphFixture revoked(native);
    auto revokedReservation = revoked.Retire();
    if (!test.Expect(revokedReservation &&
                    revoked.Settle(*revokedReservation, true) == Status::AwaitingDrain,
                    "reserve another registration before its first drain"))
        return;
    revoked.drain.CompletePass();
    revoked.Queue(OldSlot);
    test.Expect(revoked.Settle(*revokedReservation, false) == Status::CallbacksPending &&
                    revoked.Pending().count == 1,
                "withdrawn callback proof revokes the previous purge");
    test.Expect(revoked.Settle(*revokedReservation, true) == Status::AwaitingDrain &&
                    revoked.Pending().count == 0 && revoked.Free().count == 0,
                "a renewed quiet owner requires a new purge and worker pass");
    revoked.RunDrain();
    test.Expect(revoked.Settle(*revokedReservation, true) == Status::Released,
                "the slot can still be returned after a renewed proof and drain");

    GraphFixture late(native);
    auto lateReservation = late.Retire();
    if (!test.Expect(lateReservation && late.Settle(*lateReservation, true) == Status::AwaitingDrain,
                     "the late-enqueue control has a completed initial purge"))
        return;
    late.RunDrain();
    late.Queue(OldSlot);
    test.Expect(late.Settle(*lateReservation, true) == Status::AwaitingDrain &&
                    late.Pending().count == 0 && late.Free().count == 0,
                "an observed late enqueue requires another worker pass before reuse");
    late.RunDrain();
    test.Expect(late.Settle(*lateReservation, true) == Status::Released,
                "the slot can release after the later enqueue has been drained");

    GraphFixture reload(native);
    auto reloadReservation = reload.Retire();
    if (!test.Expect(reloadReservation && reload.Settle(*reloadReservation, true) == Status::AwaitingDrain,
                     "the save boundary can see a cleared row before the slot is released"))
        return;
    // Model reading the cleared row into a new EventManager. Empty intervening
    // rows in this synthetic fixture are occupied in a normal registration table.
    for (std::uint32_t index = 0; index < OldSlot; ++index)
        reload.rows[index] = {NewType, static_cast<std::uint32_t>(NewKey), index};
    reload.ReloadFreeSlots(native);
    test.Expect(reload.Free().count == 1 && reload.Register() == OldSlot &&
                    reload.Pending().count == 0,
                "the native reload can reuse an invalid row once its saved notifications are clean");
}
void InitQuestLockObserver(const Slices& native)
{
    lockQuestByte = native.At<SpinLock>(0x22CA300);
}
} // namespace
