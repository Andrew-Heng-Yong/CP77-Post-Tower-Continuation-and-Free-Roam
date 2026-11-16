#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>

#include <algorithm>
#include <array>
#include <bit>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <stdexcept>
#include <vector>

#include "RealTimeHandoff.hpp"

namespace
{
constexpr std::size_t ImageSize = 0x3C40000;
constexpr std::size_t DelaySize = 0x54000;
constexpr auto GroupMask = 4ULL << 32;
constexpr std::uint64_t TestedNode = 0x1361AA1A00000005;
using DispatchDue = void (*)(void*, float, const float*);
void* sliceBaseForDiagnostics;

template <class T>
T& Field(void* address, std::size_t offset)
{
    return *reinterpret_cast<T*>(static_cast<std::byte*>(address) + offset);
}

struct NativeAllocation
{
    alignas(16) std::array<std::byte, 0x80> bytes{};
    long count = 0;
};

std::array<NativeAllocation, 4> loadedTimers;
unsigned allocations;
const void* timerClass;

void* AllocateLoadedTimer(std::size_t size)
{
    if (size != 0x80 || allocations == loadedTimers.size())
        std::abort();
    return loadedTimers[allocations++].bytes.data();
}

ptfr::NativeDelayReference* MakeLoadedReference(ptfr::NativeDelayReference* out, void* entry)
{
    auto& allocation = loadedTimers[allocations - 1];
    if (allocation.bytes.data() != entry || allocation.count)
        std::abort();
    allocation.count = 2; // The fixture and the returned reference each own one.
    *out = {entry, &allocation.count};
    return out;
}

const void* QueryDelayClass(void*) { return &timerClass; }
bool ReloadContext(void*) { return true; }

void InitTimerSearch(void* predicate, const std::uint64_t* timer)
{
    Field<std::uint64_t>(predicate, 0) = *timer;
    Field<const void*>(predicate, 0x40) = static_cast<const std::byte*>(sliceBaseForDiagnostics) + 0x3950258;
}

void DiscardBorrowedPredicate(void*) {}

// Test substitutes for the native transient vector allocator. The timer
// scheduler and all reference movements under test run as copied instructions.
void ReserveExpired(void* vector, std::uint32_t count, std::uint32_t stride, unsigned, void*)
{
    auto& data = Field<void*>(vector, 0);
    data = std::realloc(Field<std::uint32_t>(vector, 8) ? data : nullptr, count * stride);
    if (!data)
        std::abort();
    Field<std::uint32_t>(vector, 8) = count;
}

void FreeExpired(void* vector, unsigned)
{
    std::free(Field<void*>(vector, 0));
    Field<std::uint32_t>(vector, 8) = 0;
}

std::uint32_t NextAllocation(std::uint32_t count)
{
    return count < 8 ? 8 : count * 2;
}

void FreeQuestBatch(void* vector)
{
    if (Field<std::uint32_t>(vector, 8))
        FreeExpired(vector, 4);
}

[[noreturn]] void UnexpectedCall()
{
    std::abort();
}

LONG LogException(EXCEPTION_POINTERS* info)
{
    if (info->ExceptionRecord->ExceptionCode == EXCEPTION_ACCESS_VIOLATION)
    {
        const auto base = reinterpret_cast<std::uintptr_t>(sliceBaseForDiagnostics);
        if (base && info->ContextRecord->Rip >= base && info->ContextRecord->Rip - base < ImageSize)
            std::fprintf(stderr, "Fixture access violation at native RVA %08llX\n",
                         static_cast<unsigned long long>(info->ContextRecord->Rip - base));
    }
    return EXCEPTION_CONTINUE_SEARCH;
}

class Slices
{
public:
    explicit Slices(const char* path)
    {
        std::ifstream file(path, std::ios::binary);
        const auto slices = Read<std::uint32_t>(file);
        timerId = Read<std::uint64_t>(file);
        remaining = Read<float>(file);
        if (slices != 73 || timerId >> 32 != 4 || !std::isfinite(remaining) || remaining <= 0)
            throw std::runtime_error("Invalid scheduler fixture");
        base = static_cast<std::byte*>(VirtualAlloc(nullptr, ImageSize, MEM_RESERVE, PAGE_NOACCESS));
        if (!base)
            throw std::runtime_error("Unable to reserve the slice cage");
        sliceBaseForDiagnostics = base;
        for (unsigned index = 0; index < slices; ++index)
        {
            const auto rva = Read<std::uint32_t>(file);
            const auto size = Read<std::uint32_t>(file);
            if (size == 0 || size > 0x1000 || rva >= ImageSize || size > ImageSize - rva)
                throw std::runtime_error("Invalid slice range");
            Allocate(rva, size);
            if (!file.read(reinterpret_cast<char*>(base + rva), size))
                throw std::runtime_error("Truncated slice");
        }
        if (file.peek() != std::char_traits<char>::eof())
            throw std::runtime_error("Unexpected slice data");
        PutJump(0x270174, &ReserveExpired);
        PutJump(0x26E178, &FreeExpired);
        PutJump(0x29B410, &NextAllocation);
        using Move = void* (*)(void*, const void*, std::size_t);
        PutJump(0x196A250, static_cast<Move>(&std::memmove));
        PutJump(0x1CEF5C, &FreeQuestBatch);
        PutJump(0x2B1BC4, &UnexpectedCall); // Tests must stop before path lookup and graph dispatch.
        PutJump(0xC52B94, &AllocateLoadedTimer);
        PutJump(0x271FA4, &MakeLoadedReference);
        using Fill = void* (*)(void*, int, std::size_t);
        PutJump(0x1969F30, static_cast<Fill>(&std::memset));
        PutJump(0xC47A50, &QueryDelayClass);
        PutJump(0x217A310, &InitTimerSearch); // Skip the game's TLS initialization for a borrowed predicate.
        PutJump(0x1FF2B0, &DiscardBorrowedPredicate);
        Allocate(0x3BF6720, sizeof(std::uint64_t));
        Field<std::uint64_t>(base, 0x3BF6720) = 0;
        Allocate(0x3C3BED2, sizeof(std::uint8_t));
        Field<std::uint8_t>(base, 0x3C3BED2) = 1; // Fixture uses the engine's initialized CName branch.
        PutPointer(0x3BC6610, &timerClass);
        PutPointer(0x3950258, At<const void*>(0x12FD7EC));
        PutPointer(0x3950258 + 0x18, At<const void*>(0x1FF2B0));
        PutPointer(0x302B0A8 + 8, At<const void*>(0xC47A50));
        PutPointer(0x302B0A8 + 0xD8, At<const void*>(0x1AAB6C));
        PutPointer(0x302B0A8 + 0xE0, At<const void*>(0x7B2AD0));
        PutPointer(0x3695E70 + 8, At<const void*>(0x153D590));
        PutPointer(0x3695E70 + 0x10, At<const void*>(0x1304ED8));
        PutPointer(0x3695E70 + 0x20, At<const void*>(0x258480));
        for (std::size_t page = 0; page < committed.size(); ++page)
        {
            DWORD oldProtection{};
            const auto protect = page == 0x3BF6720 / 4096 ? PAGE_READWRITE : PAGE_EXECUTE_READ;
            if (committed[page] && !VirtualProtect(base + page * 4096, 4096, protect, &oldProtection))
                throw std::runtime_error("Unable to seal a slice");
        }
        FlushInstructionCache(GetCurrentProcess(), base, ImageSize);
    }

    ~Slices()
    {
        sliceBaseForDiagnostics = nullptr;
        VirtualFree(base, 0, MEM_RELEASE);
    }

    template <class Target>
    Target At(std::uint32_t rva) const
    {
        return reinterpret_cast<Target>(base + rva);
    }

    std::uint64_t timerId;
    float remaining;

private:
    template <class T>
    static T Read(std::ifstream& file)
    {
        T result{};
        if (!file.read(reinterpret_cast<char*>(&result), sizeof(result)))
            throw std::runtime_error("Truncated fixture header");
        return result;
    }

    void Allocate(std::uint32_t rva, std::uint32_t size)
    {
        constexpr std::uint32_t PageSize = 4096;
        const auto first = rva & ~(PageSize - 1);
        const auto last = (rva + size - 1) & ~(PageSize - 1);
        for (auto page = first; page <= last; page += PageSize)
        {
            const auto position = page / PageSize;
            if (committed[position])
                continue;
            if (!VirtualAlloc(base + page, PageSize, MEM_COMMIT, PAGE_READWRITE))
                throw std::runtime_error("Unable to commit a slice");
            std::memset(base + page, 0xCC, PageSize);
            committed[position] = true;
        }
    }

    template <class Target>
    void PutJump(std::uint32_t rva, Target target)
    {
        // mov rax, absolute address followed by jmp rax.
        std::uint8_t jump[] = {0x48, 0xB8, 0, 0, 0, 0, 0, 0, 0, 0, 0xFF, 0xE0};
        const auto absolute = reinterpret_cast<std::uintptr_t>(target);
        std::memcpy(jump + 2, &absolute, sizeof(absolute));
        Allocate(rva, sizeof(jump));
        std::memcpy(base + rva, jump, sizeof(jump));
    }

    void PutPointer(std::uint32_t rva, const void* value)
    {
        Allocate(rva, sizeof(value));
        std::memcpy(base + rva, &value, sizeof(value));
    }

    std::array<bool, ImageSize / 4096> committed{};
    std::byte* base = nullptr;
};

struct TestCallback
{
    const std::uintptr_t* vtable;
    unsigned fired = 0;
};

void RecordCallback(TestCallback* callback)
{
    ++callback->fired;
}

struct Timer
{
    ptfr::NativeDelayReference Ref() { return {entry.data(), &count}; }

    alignas(16) std::array<std::byte, 0x80> entry{};
    long count = 1; // Fixture lifetime owns one reference for each timer.
    TestCallback callback{};
};

class Checks
{
public:
    explicit Checks(const Slices& native)
        : worker{native.At<ptfr::DelayWorker::Remaining>(0x111894C),
                 native.At<ptfr::DelayWorker::Remove>(0x1AA7D0),
                 native.At<ptfr::DelayWorker::Insert>(0x1AA8B8),
                 native.At<ptfr::DelayWorker::Release>(0x195798)},
          dispatch(native.At<DispatchDue>(0x1AA634))
    {
        timerTable[0xD8 / sizeof(std::uintptr_t)] = native.At<std::uintptr_t>(0x1AAB6C);
        callbackTable[2] = reinterpret_cast<std::uintptr_t>(&RecordCallback);
    }

    void Reset()
    {
        std::fill(delay.begin(), delay.end(), std::byte{0});
        // Four real-time groups with empty head/tail indices.
        for (std::size_t index = 0; index < 4; ++index)
            Field<std::uint32_t>(delay.data(), 0x50 + index * 0xC010) = UINT32_MAX;
        Field<std::uint32_t>(delay.data(), 0x5303C) = 4;
    }

    void Add(Timer& timer, std::uint64_t id, float duration, void* callback = nullptr)
    {
        timer.callback.vtable = callbackTable.data();
        Field<void*>(timer.entry.data(), 0) = timerTable.data();
        Field<std::uint64_t>(timer.entry.data(), ptfr::HeldDelay::EntryTimer) = id;
        Field<float>(timer.entry.data(), ptfr::HeldDelay::EntrySeconds) = duration;
        Field<void*>(timer.entry.data(), 0x78) = callback ? callback : &timer.callback;
        const auto reference = timer.Ref();
        worker.insert(delay.data(), &reference, 0);
    }

    std::optional<ptfr::HeldDelay> Take(Timer& timer, std::uint64_t id, float tick = 0)
    {
        return Take(&timer.callback, id, tick);
    }

    std::optional<ptfr::HeldDelay> Take(const void* callback, std::uint64_t id, float tick = 0)
    {
        return ptfr::HeldDelay::Take(worker, Owner(callback), timerTable.data(), id, tick);
    }

    ptfr::DelayOwner Owner(const void* callback) { return {delay.data(), callback, 1}; }

    void Remove(std::uint64_t id) { worker.remove(delay.data(), &id, 0); }
    void Tick(float duration) { dispatch(delay.data(), duration, &duration); }
    float Remaining(std::uint64_t id) { return worker.remaining(delay.data(), id); }

    ptfr::RealTimeReload ReloadMethods(const Slices& native)
    {
        return {worker, native.At<ptfr::RealTimeReload::Construct>(0x1133EEC),
                native.At<ptfr::RealTimeReload::Attach>(0x193A1C),
                native.At<ptfr::RealTimeReload::ReadNodeData>(0x194AC4),
                native.At<ptfr::RealTimeReload::InsertNodeData>(0x194718),
                native.At<const void*>(0x302B0A8), native.At<const void*>(0x3695E70),
                native.At<const void*>(0x31267A0)};
    }

    float ReadSavedDelay(const Slices& native, std::uint64_t timer)
    {
        using Collect = void* (*)(void*, void*, void*);
        struct Vector { void* rows; std::uint32_t capacity; std::uint32_t count; } saved{};
        native.At<Collect>(0x2AAC3D4)(nullptr, &saved, delay.data() + ptfr::HeldDelay::Group4Head);
        const auto seconds = ptfr::FindRemainingDelay(saved.rows, saved.count, ptfr::SchedulerId::FromNative(timer));
        if (saved.capacity)
            FreeExpired(&saved, 4);
        return seconds.value_or(-1.0f);
    }

    bool LoadSavedDelay(const ptfr::RealTimeReload& reload, std::uint64_t id, float seconds)
    {
        ptfr::NativeDelayReference timer{};
        reload.construct(&timer);
        if (!timer.entry || !timer.count)
            return false;
        Field<std::uint64_t>(timer.entry, ptfr::HeldDelay::EntryTimer) = id;
        Field<float>(timer.entry, ptfr::HeldDelay::EntrySeconds) = seconds;
        worker.insert(delay.data(), &timer, 0);
        worker.release(&timer);
        return Remaining(id) == seconds;
    }

    bool Expect(bool ok, const char* name)
    {
        std::printf("%s %s\n", ok ? "PASS" : "FAIL", name);
        if (ok)
            ++passed;
        else
            ++failed;
        return ok;
    }

    unsigned passed = 0;
    unsigned failed = 0;
    std::vector<std::byte> delay = std::vector<std::byte>(DelaySize);

private:
    ptfr::DelayWorker worker;
    DispatchDue dispatch;
    std::array<std::uintptr_t, 28> timerTable{};
    std::array<std::uintptr_t, 3> callbackTable{};
};

void MiddleWait(Checks& test, std::uint64_t id, float duration)
{
    using Status = ptfr::ReturnToScheduler;
    Timer earlier, selected, later;
    const auto earlierId = id - 1;
    const auto laterId = id + 1;
    test.Reset();
    test.Add(earlier, earlierId, 3.0f);
    test.Add(selected, id, duration);
    test.Add(later, laterId, 20.0f);
    test.Expect(std::bit_cast<std::uint32_t>(test.Remaining(id)) == std::bit_cast<std::uint32_t>(duration),
                "native lookup recovers the exact saved duration");
    test.Expect(!test.Take(selected, id, duration), "due this tick leaves native entry intact");
    test.Expect(!test.Take(earlier, id), "mismatching callback leaves native entry intact");
    auto held = test.Take(selected, id, 0.02f);
    if (!test.Expect(held.has_value(), "native removal holds the selected wait"))
        return;
    test.Expect(held->RemainingSeconds() == duration && selected.count == 2 && test.Remaining(id) == -1.0f,
                "hold owns the same reference with the full remaining duration");
    test.Expect(test.Remaining(earlierId) == 3.0f && test.Remaining(laterId) == 20.0f,
                "native unlink preserves both neighboring deadlines");
    test.Tick(6.0f);
    test.Expect(earlier.callback.fired == 1 && selected.callback.fired == 0 && later.callback.fired == 0 &&
                    test.Remaining(laterId) == 14.0f,
                "elapsed time fires unrelated callback and consumes no held time");
    auto owner = test.Owner(&selected.callback);
    auto recycledOwner = owner;
    ++recycledOwner.generation;
    test.Expect(held->Return(recycledOwner) == Status::OwnerChanged && test.Remaining(id) == -1.0f,
                "same pointers in a new owner generation cannot restore a stale callback");
    test.Expect(held->Return(owner) == Status::Returned && selected.count == 2 &&
                    test.Remaining(id) == duration && test.Remaining(laterId) == 14.0f,
                "native reinsertion keeps remaining time and the following deadline");
    test.Expect(held->Return(owner) == Status::Empty, "second release cannot reinsert the wait");
    test.Tick(4.0f);
    test.Expect(selected.callback.fired == 0, "original callback stays pending until restored deadline");
    test.Tick(5.0f);
    test.Expect(selected.callback.fired == 1 && selected.count == 1 && test.Remaining(id) == -1.0f,
                "original callback fires once and native expiry removes the slot");
    test.Tick(5.0f);
    test.Expect(selected.callback.fired == 1 && later.callback.fired == 1,
                "following wait fires once with no replay of restored callback");
}

void FailureControls(Checks& test, std::uint64_t id)
{
    using Status = ptfr::ReturnToScheduler;
    Timer selected, other, duplicate;
    test.Reset();
    test.Expect(!test.Take(selected, id), "absent timer leaves scheduler alone");
    test.Add(selected, id, 4.0f);
    Field<std::uint8_t>(selected.entry.data(), ptfr::HeldDelay::EntryCancelled) = 1;
    test.Expect(!test.Take(selected, id), "cancelled native entry cannot be held");
    Field<std::uint8_t>(selected.entry.data(), ptfr::HeldDelay::EntryCancelled) = 0;
    test.Add(duplicate, id, 5.0f);
    test.Expect(!test.Take(selected, id), "duplicate live scheduler identity rejected");
    test.Remove(id);
    test.Remove(id);
    const auto owner = test.Owner(&selected.callback);
    {
        test.Add(selected, id, 4.0f);
        auto held = test.Take(selected, id);
        if (!test.Expect(held.has_value(), "only timer can be held"))
            return;
        auto& count = Field<std::uint32_t>(test.delay.data(), ptfr::HeldDelay::Group4Count);
        count = ptfr::HeldDelay::Capacity;
        test.Expect(held->Return(owner) == Status::Retry && selected.count == 2, "capacity failure keeps the held reference");
        count = 0;
        test.Add(other, id, 1.0f);
        test.Expect(held->Return(owner) == Status::Occupied && test.Remaining(id) == 1.0f,
                    "ID reuse leaves the new owner untouched");
    }
    test.Tick(1.0f);
    test.Expect(selected.count == 1 && selected.callback.fired == 0 && other.callback.fired == 1,
                "discard releases only the held reference and never fires its callback");
    test.Add(selected, id, 4.0f);
    auto held = test.Take(selected, id);
    if (!test.Expect(held.has_value(), "hold after prior rollback test"))
        return;
    test.Expect(held->Return(owner) == Status::Returned && test.Remaining(id) == 4.0f,
                "native reinsertion into empty group");
    test.Tick(4.0f);
    test.Expect(selected.callback.fired == 1 && selected.count == 1, "empty-group return keeps original callback");
}

void QuestNotification(Checks& test, const Slices& native)
{
    using Status = ptfr::ReturnToScheduler;
    test.Reset();
    struct Vector
    {
        void* data;
        std::uint32_t capacity;
        std::uint32_t count;
    };
    Timer selected;
    std::array<std::uint32_t, 8> notifications{};
    std::array<std::uint32_t, 8> alreadyDispatched{};
    std::array<std::uint32_t, 8> retired{};
    std::array<std::uint64_t, 16> registration{};
    std::array<std::uintptr_t, 0x2B8 / 8> questTable{};
    std::array<std::uintptr_t, 2> eventTable{};
    std::array<std::uintptr_t, 3> callbackTable{};
    alignas(16) std::array<std::byte, 0x180> quests{};
    alignas(16) std::array<std::byte, 0x40> eventManager{};
    alignas(16) std::array<std::byte, 0x60> handler{};
    alignas(16) std::array<std::byte, 0x40> parent{};
    alignas(16) std::array<std::byte, 0x10> callback{};
    auto& pending = Field<Vector>(quests.data(), 0x158);
    auto& freedSlots = Field<Vector>(eventManager.data(), 0x18);
    const auto slot = 3U;
    notifications[0] = 9;
    pending = {notifications.data(), static_cast<std::uint32_t>(notifications.size()), 1};
    freedSlots = {retired.data(), static_cast<std::uint32_t>(retired.size()), 0};
    Field<void*>(quests.data(), 0) = questTable.data();
    Field<void*>(eventManager.data(), 0) = eventTable.data();
    Field<void*>(eventManager.data(), 8) = registration.data();
    Field<void*>(eventManager.data(), 0x28) = quests.data();
    Field<void*>(parent.data(), 0x18) = eventManager.data();
    Field<std::uint32_t>(parent.data(), 0x28) = slot;
    Field<void*>(handler.data(), 0x20) = parent.data();
    Field<std::uint32_t>(handler.data(), 0x30) = 1;
    Field<void*>(callback.data(), 0) = callbackTable.data();
    Field<void*>(callback.data(), 8) = handler.data();
    questTable[0x200 / 8] = native.At<std::uintptr_t>(0x88BC58);
    questTable[0x2B0 / 8] = native.At<std::uintptr_t>(0x2FD1BC);
    eventTable[1] = native.At<std::uintptr_t>(0x88BC48);
    callbackTable[2] = native.At<std::uintptr_t>(0x1304ED8);

    test.Add(selected, native.timerId, native.remaining, callback.data());
    auto held = test.Take(callback.data(), native.timerId);
    if (!test.Expect(held.has_value(), "hold the native quest callback chain"))
        return;
    test.Tick(12.0f);
    test.Expect(pending.count == 1 && Field<std::uint32_t>(handler.data(), 0x2C) == 0,
                "no native quest readiness or notification while held");
    test.Expect(held->Return(test.Owner(callback.data())) == Status::Returned, "native quest callback restored to scheduler");
    test.Tick(native.remaining - 0.25f);
    test.Expect(pending.count == 1, "native quest slot stays quiet until the exact deadline");
    test.Tick(0.25f);
    test.Expect(pending.count == 2 && notifications[1] == slot &&
                    Field<std::uint32_t>(handler.data(), 0x2C) == 1,
                "stock callback queues the original composite parent's slot once");
    test.Tick(30.0f);
    test.Expect(pending.count == 2 && notifications[0] == 9,
                "no duplicate quest notification or interference with another slot");

    // Model a separate already copied work list. Native retirement only scans the
    // current queue. Deliberately place two matching slots in that shared queue.
    alreadyDispatched[0] = slot;
    notifications[2] = slot;
    pending.count = 3;
    registration[slot * 2] = 0x12345678;
    registration[slot * 2 + 1] = native.timerId;
    native.At<void (*)(void*, std::uint32_t)>(0x2FCFD0)(eventManager.data(), slot);
    test.Expect(registration[slot * 2] == 0 && registration[slot * 2 + 1] == 0xFFFF00000000ULL &&
                    freedSlots.count == 1 && retired[0] == slot,
                "native retirement clears and releases the physical registration");
    test.Expect(pending.count == 2 && notifications[1] == slot && alreadyDispatched[0] == slot,
                "retirement removes one queued match and leaves a copied work list untouched");

    // In the actual worker, drain deduplicates, clears the shared list and then
    // checks retirement / registration under the graph lock before dispatch.
    Field<void*>(quests.data(), 0xE8) = eventManager.data();
    const auto drain = native.At<void (*)(void*)>(0x3534DC);
    notifications[0] = slot;
    notifications[1] = slot;
    auto& deferredRetired = Field<Vector>(quests.data(), 0x168);
    alreadyDispatched[0] = slot;
    deferredRetired = {alreadyDispatched.data(), static_cast<std::uint32_t>(alreadyDispatched.size()), 1};
    drain(quests.data());
    test.Expect(pending.count == 0 && deferredRetired.count == 0,
                "native worker drains duplicate retired slots and clears older deferred markers");
}

void CutoffAndRebuiltHandler(Checks& test, const Slices& native)
{
    using Result = ptfr::ReattachResult;
    test.Reset();
    Timer oldTimer;
    test.Add(oldTimer, native.timerId, native.remaining);
    ptfr::CutoffObservation observation;
    ptfr::CutoffWaitSample capture;
    const auto watch = observation.BeginWatch(&oldTimer.callback);
    int facts{};
    const auto scheduler = test.delay.data();
    const ptfr::GateTicket gate{&facts, 1, 19};
    observation.Watch({&oldTimer.callback, scheduler, &facts, native.timerId}, watch);
    std::optional<ptfr::GateOutcome> previous;
    const auto gateChange = observation.BeginGateWrite(&facts, previous);
    const auto otherRoute = ptfr::GateTicket{&facts, 2, gate.ticket};
    observation.Open(otherRoute, gateChange);
    test.Expect(!capture.Record(observation, *observation.Request(scheduler), TestedNode,
                                native.remaining, 0.016f), "defer q115 while its ending is unconfirmed");
    observation.Open(gate, observation.BeginGateWrite(&facts, previous));
    const auto request = observation.Request(scheduler);
    if (!test.Expect(request.has_value(), "only the matching direct Tower gate exposes the wait"))
        return;
    test.Expect(!capture.Record(observation, *request, TestedNode, 0.010f, 0.016f),
                "defer a wait due this frame");
    auto oldOwner = test.Owner(&oldTimer.callback);
    auto held = test.Take(oldTimer, native.timerId, 0.016f);
    if (!test.Expect(held.has_value(), "the delay worker holds the live pre-cleanup wait"))
        return;
    const bool recorded = capture.Record(observation, *request, TestedNode, held->RemainingSeconds(), 0.016f);
    const auto checkpoint = capture.Read(observation, &facts, TestedNode, gate.ticket);
    if (!test.Expect(recorded && checkpoint && checkpoint->Matches(TestedNode, gate.ticket),
                     "the open cutoff records the duration and ending ticket"))
        return;
    int foreignFacts = 0;
    test.Expect(!capture.Read(observation, &foreignFacts, TestedNode, gate.ticket) &&
                    !capture.Read(observation, &facts, TestedNode, gate.ticket + 1),
                "the cutoff sample belongs to one fact manager and one ending ticket");
    observation.BeginGateWrite(&facts, previous);
    test.Expect(previous && previous->sampled && !observation.Request(scheduler) &&
                    !capture.Read(observation, &facts, TestedNode, gate.ticket),
                "the completed cutoff will not sample the same wait again");
    test.Tick(85.0f);
    test.Expect(test.Remaining(native.timerId) == -1.0f && oldTimer.callback.fired == 0,
                "the held callback stays quiet during simulated Tower time");

    struct Vector
    {
        void* data;
        std::uint32_t capacity;
        std::uint32_t count;
    };
    std::array<std::uint32_t, 8> notifications{};
    std::array<std::array<std::uint64_t, 2>, 8> nodeData{};
    std::array<std::uintptr_t, 0x2D0 / 8> questTable{};
    std::array<std::uintptr_t, 2> eventTable{};
    std::array<std::uintptr_t, 0x1E0 / 8> schedulerTable{};
    std::array<std::uintptr_t, 0x108 / 8> contextTable{};
    std::array<std::uintptr_t, 6> handlerTable{};
    alignas(16) std::array<std::byte, 0x180> quests{};
    alignas(16) std::array<std::byte, 0x20> nodeManager{};
    alignas(16) std::array<std::byte, 0x40> eventManager{};
    alignas(16) std::array<std::byte, 0x60> newHandler{};
    alignas(16) std::array<std::byte, 0x40> newParent{};
    alignas(16) std::array<std::byte, 0x100> context{};
    constexpr std::uint32_t newSlot = 5;
    auto& pending = Field<Vector>(quests.data(), 0x158);
    pending = {notifications.data(), static_cast<std::uint32_t>(notifications.size()), 0};
    Field<void*>(quests.data(), 0) = questTable.data();
    Field<void*>(eventManager.data(), 0) = eventTable.data();
    Field<void*>(eventManager.data(), 0x28) = quests.data();
    Field<void*>(newParent.data(), 0x18) = eventManager.data();
    Field<std::uint32_t>(newParent.data(), 0x28) = newSlot;
    Field<void*>(newHandler.data(), 0x20) = newParent.data();
    Field<std::uint32_t>(newHandler.data(), 0x30) = 1;
    questTable[0x200 / 8] = native.At<std::uintptr_t>(0x88BC58);
    eventTable[1] = native.At<std::uintptr_t>(0x88BC48);

    ptfr::RealTimeHandoff resume(*checkpoint);
    const auto reload = test.ReloadMethods(native);
    Field<void*>(quests.data(), 0xF0) = nodeManager.data();
    Field<Vector>(nodeManager.data(), 8) = {nodeData.data(), static_cast<std::uint32_t>(nodeData.size()), 0};
    Field<const void*>(newHandler.data(), 0) = reload.handlerVtable;
    Field<std::uint64_t>(newHandler.data(), 0x38) = TestedNode;
    Field<std::uint64_t>(newHandler.data(), 0x40) = ptfr::RealTimeHandoff::InactiveTimer;
    ptfr::RegisteredWait owner{TestedNode, gate.ticket, oldOwner.generation, scheduler, oldOwner.generation + 1,
                               quests.data(), newHandler.data()};
    const auto freshId = GroupMask | 0x6e1;
    auto unproved = owner;
    unproved.generation = oldOwner.generation;
    test.Expect(resume.Reattach(reload, unproved, freshId) == Result::Deferred,
                "reattachment defers while the previous registration can still own the wait");
    unproved = owner;
    unproved.node += 1;
    test.Expect(resume.Reattach(reload, unproved, freshId) == Result::Deferred,
                "a different logical node cannot use the checkpoint");
    unproved = owner;
    unproved.endingTicket += 1;
    test.Expect(resume.Reattach(reload, unproved, freshId) == Result::Deferred,
                "a different ending ticket cannot use the checkpoint");
    Field<const void*>(newHandler.data(), 0) = nullptr;
    test.Expect(resume.Reattach(reload, owner, freshId) == Result::Deferred,
                "a different handler class cannot receive the real-time callback");
    Field<const void*>(newHandler.data(), 0) = reload.handlerVtable;
    test.Expect(held->Return({owner.scheduler, newHandler.data(), owner.generation}) == ptfr::ReturnToScheduler::OwnerChanged,
                "the old callback cannot be returned to a rebuilt registration");
    held.reset();
    const auto clearMapping = native.At<void (*)(void*, std::uint64_t)>(0x194C24);
    reload.insertMapping(quests.data(), TestedNode, ptfr::SchedulerId::FromNative(native.timerId).NodeInstanceValue());
    test.Expect(resume.Reattach(reload, owner, freshId) == Result::Deferred,
                "the saved native owner mapping has to be absent before replacement");
    clearMapping(quests.data(), TestedNode);

    Timer other;
    test.Add(other, freshId, 42.0f);
    test.Expect(resume.Reattach(reload, owner, freshId) == Result::Retry && test.Remaining(freshId) == 42.0f,
                "an occupied fresh ID defers without touching another timer");
    test.Remove(freshId);
    auto rejected = reload;
    rejected.attach = [](void*, std::uint64_t, void*, std::uint64_t, std::uint64_t) { return false; };
    test.Expect(resume.Reattach(rejected, owner, freshId) == Result::Retry && test.Remaining(freshId) == -1.0f &&
                    Field<std::uint32_t>(newHandler.data(), 0x2C) == 0,
                "failed attachment removes its own entry and leaves the handler waiting");
    rejected = reload;
    rejected.insertMapping = [](void*, std::uint64_t, std::uint64_t) {};
    test.Expect(resume.Reattach(rejected, owner, freshId) == Result::Retry && test.Remaining(freshId) == -1.0f &&
                    Field<std::uint64_t>(newHandler.data(), 0x40) == ptfr::RealTimeHandoff::InactiveTimer,
                "failed saved mapping removes the new entry and leaves the handler waiting");
    test.Expect(resume.Reattach(reload, owner, freshId) == Result::Attached && test.Remaining(freshId) == native.remaining,
                "native construction and attachment recreate exactly the saved duration");
    std::uint64_t mapping{};
    test.Expect(reload.readMapping(quests.data(), TestedNode, &mapping) &&
                    mapping == ptfr::SchedulerId::FromNative(freshId).NodeInstanceValue() &&
                    Field<std::uint64_t>(newHandler.data(), 0x40) == freshId,
                "the handler and native save map bind to the same new scheduler ID");
    test.Expect(resume.Reattach(reload, owner, freshId) == Result::AlreadyAttached &&
                    test.Remaining(native.timerId) == -1.0f,
                "a repeated resume consumes the checkpoint only once");
    test.Tick(1.5f);
    const auto savedSeconds = test.ReadSavedDelay(native, freshId);
    test.Expect(savedSeconds == native.remaining - 1.5f,
                "the native save collector writes the elapsed replacement wait");
    test.Remove(freshId);
    if (!test.Expect(test.LoadSavedDelay(reload, freshId, savedSeconds),
                     "reload starts with the saved scheduler entry and matching node mapping"))
        return;

    // Model a fresh context and rebuilt object while retaining the serialized
    // mapping. Run the stock initializer so its real attach path is exercised.
    constexpr std::uint32_t reloadedSlot = 6;
    alignas(16) std::array<std::byte, 0x60> reloadedHandler{};
    alignas(16) std::array<std::byte, 0x40> reloadedParent{};
    Field<void*>(reloadedParent.data(), 0x18) = eventManager.data();
    Field<std::uint32_t>(reloadedParent.data(), 0x28) = reloadedSlot;
    Field<void*>(reloadedHandler.data(), 0) = handlerTable.data();
    Field<void*>(reloadedHandler.data(), 0x20) = reloadedParent.data();
    Field<std::uint64_t>(reloadedHandler.data(), 0x38) = TestedNode;
    Field<std::uint64_t>(reloadedHandler.data(), 0x40) = ptfr::RealTimeHandoff::InactiveTimer;
    Field<void*>(scheduler, 0) = schedulerTable.data();
    Field<void*>(context.data(), 0) = contextTable.data();
    Field<void*>(context.data(), 0x18) = quests.data();
    Field<void*>(context.data(), 0xF8) = scheduler;
    questTable[0x2C8 / 8] = native.At<std::uintptr_t>(0x194AC4);
    schedulerTable[0x1D8 / 8] = native.At<std::uintptr_t>(0x193A1C);
    schedulerTable[0x1C8 / 8] = reinterpret_cast<std::uintptr_t>(&UnexpectedCall);
    handlerTable[0x28 / 8] = native.At<std::uintptr_t>(0x664F00);
    contextTable[0x100 / 8] = reinterpret_cast<std::uintptr_t>(&ReloadContext);
    native.At<void (*)(void*, void*)>(0x1948BC)(reloadedHandler.data(), context.data());
    test.Expect(Field<std::uint64_t>(reloadedHandler.data(), 0x40) == freshId && pending.count == 0,
                "stock quest initialization reattaches the saved ID without firing early");
    test.Tick(savedSeconds - 0.25f);
    test.Expect(pending.count == 0, "the replacement handler stays quiet before the saved deadline");
    test.Tick(0.25f);
    test.Expect(pending.count == 1 && notifications[0] == reloadedSlot &&
                    Field<std::uint32_t>(reloadedHandler.data(), 0x2C) == 1 &&
                    Field<std::uint32_t>(newHandler.data(), 0x2C) == 0 && oldTimer.callback.fired == 0,
                "the stock callback wakes only the rebuilt composite parent's new slot");
    test.Tick(30.0f);
    test.Expect(pending.count == 1 && test.Remaining(freshId) == -1.0f,
                "expiry retires the new timer without a duplicate notification");
    clearMapping(quests.data(), TestedNode);
    test.Expect(!reload.readMapping(quests.data(), TestedNode, &mapping),
                "normal native node-data removal clears the replacement mapping");

    observation.Reset();
    test.Expect(!capture.Read(observation, &facts, TestedNode, gate.ticket),
                "a session reset revokes the previously sampled wait");
}
} // namespace

int main(int argc, char** argv)
{
    std::setvbuf(stdout, nullptr, _IONBF, 0);
    AddVectoredExceptionHandler(1, &LogException);
    if (argc != 2)
        return 2;
    try
    {
        const Slices native(argv[1]);
        Checks checks(native);
        MiddleWait(checks, native.timerId, native.remaining);
        FailureControls(checks, native.timerId);
        QuestNotification(checks, native);
        CutoffAndRebuiltHandler(checks, native);
        std::printf("%u passed, %u failed\n", checks.passed, checks.failed);
        return checks.failed == 0 ? 0 : 1;
    }
    catch (const std::exception& error)
    {
        std::fprintf(stderr, "%s\n", error.what());
        return 2;
    }
}
