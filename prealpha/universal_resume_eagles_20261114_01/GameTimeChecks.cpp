#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>

#include "GameTimeWait.hpp"

#include <array>
#include <bitset>
#include <cerrno>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <memory>
#include <stdexcept>

namespace
{
constexpr auto ImageSize = 0x4000000;
std::uintptr_t fixtureBase{};

LONG ReportNativeFault(EXCEPTION_POINTERS* exception)
{
    if (exception->ExceptionRecord->ExceptionCode == EXCEPTION_ACCESS_VIOLATION)
    {
        const auto code = exception->ContextRecord->Rip;
        const auto address = exception->ExceptionRecord->ExceptionInformation[1];
        std::fprintf(stderr, "Native fixture fault. RIP %016llX, address %016llX, slice base %016llX\n",
                     code, address, fixtureBase);
    }
    return EXCEPTION_CONTINUE_SEARCH;
}

template <class T>
void Write(void* memory, std::size_t offset, T value)
{
    std::memcpy(static_cast<std::byte*>(memory) + offset, &value, sizeof(T));
}

class NativeCode
{
public:
    NativeCode() : base(static_cast<std::byte*>(VirtualAlloc(nullptr, ImageSize, MEM_RESERVE, PAGE_NOACCESS)))
    {
        if (!base)
            throw std::runtime_error("Could not reserve native fixture code");
        fixtureBase = reinterpret_cast<std::uintptr_t>(base);
    }

    NativeCode(const NativeCode&) = delete;
    NativeCode& operator=(const NativeCode&) = delete;
    ~NativeCode() { VirtualFree(base, 0, MEM_RELEASE); }

    void Load(const char* path)
    {
        std::ifstream input(path, std::ios::binary);
        const auto count = Read<std::uint32_t>(input);
        if (count != 32)
            throw std::runtime_error("Unexpected native slice count");
        for (std::uint32_t index = 0; index < count; ++index)
        {
            const auto rva = Read<std::uint32_t>(input);
            const auto length = Read<std::uint32_t>(input);
            if (rva >= ImageSize || !length || length > 0x1000 || length > ImageSize - rva)
                throw std::runtime_error("Invalid native slice");
            const auto first = rva / PageSize;
            const auto last = (rva + length - 1) / PageSize;
            for (auto page = first; page <= last; ++page)
            {
                if (pages[page])
                    continue;
                if (!VirtualAlloc(base + page * PageSize, PageSize, MEM_COMMIT, PAGE_READWRITE))
                    throw std::runtime_error("Could not commit native slice page");
                pages.set(page);
            }
            if (!input.read(reinterpret_cast<char*>(base + rva), length))
                throw std::runtime_error("Could not load native slice");
        }
        for (std::size_t page = 0; page < pages.size(); ++page)
        {
            DWORD previous{};
            if (page == 0x36A1D20 / PageSize)
                continue; // Relocated fixture callback table is read/write data.
            if (pages[page] && !VirtualProtect(base + page * PageSize, PageSize, PAGE_EXECUTE_READ, &previous))
                throw std::runtime_error("Could not seal native slice page");
        }
        if (input.peek() != std::char_traits<char>::eof() ||
            !FlushInstructionCache(GetCurrentProcess(), base, ImageSize))
            throw std::runtime_error("Invalid native fixture data");
    }

    template <class T>
    T At(std::uint32_t rva) const { return reinterpret_cast<T>(base + rva); }

private:
    template <class T>
    static T Read(std::ifstream& input)
    {
        T value{};
        if (!input.read(reinterpret_cast<char*>(&value), sizeof(T)))
            throw std::runtime_error("Truncated native slice header");
        return value;
    }
    static constexpr std::uint32_t PageSize = 4096;
    std::byte* base;
    std::bitset<ImageSize / PageSize> pages;
};

unsigned passed{};
unsigned failed{};

void Check(bool condition, const char* name)
{
    std::printf("%s %s\n", condition ? "PASS" : "FAIL", name);
    condition ? ++passed : ++failed;
}

std::uint32_t firedSlot{};
std::uint32_t callbacks{};
unsigned notificationCount{};
using NativeReady = void (*)(void*, std::uint8_t);
NativeReady markReady{};

void ObserveNotification(void*, std::uint32_t slot)
{
    firedSlot = slot;
    ++notificationCount;
}

void CountCallback(void* callback)
{
    ++callbacks;
    auto* handler = ptfr::ReadGameTimeField<void*>(callback, 8);
    if (!handler)
        std::abort();
    markReady(handler, 1);
}

struct TimerFixture
{
    using TickMethod = std::uint8_t (*)(void*, std::uint32_t);
    explicit TimerFixture(const NativeCode& native, std::uint32_t id, std::uint32_t authored)
        : timerId(id), authoredSeconds(authored), tick(native.At<TickMethod>(0x193B00))
    {
        timerTable[0x130 / 8] = native.At<const void*>(0x193E58);
        timerTable[0x128 / 8] = native.At<const void*>(0xB79440);
        savedCallbackTable[2] = reinterpret_cast<const void*>(&CountCallback);
        savedCallbackTable[1] = native.At<const void*>(0x15702A8);
        savedCallbackTable[4] = native.At<const void*>(0x258480);
        firstCallbackTable[2] = savedCallbackTable[2];
        eventTable[1] = native.At<const void*>(0x88BC48);
        questTable[0x200 / 8] = reinterpret_cast<const void*>(&ObserveNotification);
        Write(timer.data(), 0, timerTable.data());
        Write(timer.data(), 0x44, 1U);
        Write(timer.data(), 0x80, callback.data());
        Write(timer.data(), 0x88, id);
        Write(timer.data(), 0x90, authored);
        Write(callback.data(), 0, savedCallbackTable.data());
        Write(callback.data(), 8, owner.data());
        Write(owner.data(), 0x18, eventManager.data());
        Write(owner.data(), 0x30, 1U);
        Write(eventManager.data(), 0, eventTable.data());
        Write(eventManager.data(), 0x28, quests.data());
        Write(quests.data(), 0, questTable.data());
        Write(List(), 0x10, ptfr::NativeGameTimerReference{timer.data(), &references});
        Write(List(), 0x3008, 1U);
    }

    std::optional<ptfr::NativeGameTimer> Read(std::uint32_t clock) const
    {
        return ptfr::ReadOneShotGameWait(system.data(), timerId, clock, authoredSeconds, timerTable.data(),
                                        firstCallbackTable.data(), savedCallbackTable.data(), owner.data());
    }
    std::optional<ptfr::HeldGameTimeWait> Hold(const ptfr::GameTimeWorkerMethods& native, std::uint32_t clock)
    {
        return ptfr::HeldGameTimeWait::Take(native, Owner(), timerId, clock, authoredSeconds,
                                            timerTable.data(), firstCallbackTable.data(), savedCallbackTable.data());
    }
    ptfr::GameTimeOwner Owner() { return {system.data(), owner.data(), 1}; }
    void Install(const ptfr::GameTimeWorkerMethods& native)
    {
        const auto empty = static_cast<std::uint16_t>(0xFFFF);
        Write(List(), 0, empty);
        Write(List(), 2, empty);
        Write(List(), 0x3008, 0U);
        // The fixture owns one reference in addition to the list's reference.
        references = 1;
        ptfr::NativeGameTimerReference reference{timer.data(), &references};
        native.insert(system.data(), &reference, 0);
    }
    void SetDeadline(std::uint32_t deadline) { Write(timer.data(), 0x40, deadline); }
    std::uint8_t Tick(std::uint32_t clock) { return tick(timer.data(), clock); }
    std::byte* List() { return system.data() + 0x30130; }
    void AddNeighbor(const ptfr::GameTimeWorkerMethods& native, const TimerFixture& other)
    {
        // The neighboring fixture also owns its own independent reference.
        auto timerRef = *ptfr::FindGameTimer(other.system.data(), other.timerId);
        native.insert(system.data(), &timerRef, 0);
    }
    std::uint32_t HeadTimer()
    {
        const auto head = ptfr::ReadGameTimeField<std::uint16_t>(List(), 0);
        if (head == 0xFFFF)
            return 0;
        const auto* headTimer = ptfr::ReadGameTimeField<const void*>(List(), 24 * head + 0x10);
        return ptfr::ReadGameTimeField<std::uint32_t>(headTimer, 0x88);
    }
    void Remove(const ptfr::GameTimeWorkerMethods& native, std::uint32_t id)
    {
        native.remove(system.data(), id);
    }
    std::uint32_t NativeDeadline(const NativeCode& native)
    {
        auto read = native.At<std::uint32_t* (*)(const void*, std::uint32_t*)>(0xB79440);
        std::uint32_t value{};
        read(timer.data(), &value);
        return value;
    }
    bool RebindLoadedCallback(const NativeCode& native)
    {
        auto** manager = native.At<const void**>(0x36A1D20);
        std::memcpy(manager, savedCallbackTable.data(), sizeof(savedCallbackTable));
        const ptfr::GameTimeCallbackMethods methods{
            timerTable.data(), manager,
            native.At<decltype(ptfr::GameTimeCallbackMethods::find)>(0x2179700),
            native.At<decltype(ptfr::GameTimeCallbackMethods::assign)>(0x193B54),
            predicateTable.data()};
        Write(timer.data(), 0x80, static_cast<const void*>(nullptr));
        predicateTable[0] = native.At<const void*>(0x12428A8);
        return ptfr::AttachLoadedGameTimeCallback(methods, system.data(), timerId, owner.data());
    }

    std::uint32_t timerId;
    std::uint32_t authoredSeconds;
    long references = 2;
    std::uint32_t padding{};
    alignas(void*) std::array<std::byte, 0xA0> timer{};
    alignas(void*) std::array<std::byte, 0x40> callback{};
    alignas(void*) std::array<std::byte, 0x60> owner{};
    std::array<const void*, 5> firstCallbackTable{};
    std::array<const void*, 5> savedCallbackTable{};

private:
    alignas(void*) std::array<std::byte, 0x33140> system{};
    alignas(void*) std::array<std::byte, 0x40> eventManager{};
    alignas(void*) std::array<std::byte, 0x180> quests{};
    std::array<const void*, 0x138 / 8> timerTable{};
    std::array<const void*, 2> eventTable{};
    std::array<const void*, 0x208 / 8> questTable{};
    std::array<const void*, 1> predicateTable{};
    TickMethod tick;
};

void CheckWait(const NativeCode& native, std::uint32_t id, std::uint32_t clock,
               std::uint32_t deadline, std::uint32_t authored)
{
    TimerFixture original(native, id, authored);
    original.SetDeadline(deadline);
    Write(original.owner.data(), 0x28, 411U);
    const auto capture = original.Read(clock);
    Check(capture && capture->reference.timer == original.timer.data() && capture->wait.seconds == 171141,
          "read the exact Manual Save 26 duration from a bound native-layout wait");
    if (!capture)
        return;
    Check(!original.Read(deadline), "defer a callback already due on the game clock");
    Check(!original.Read(deadline - authored - 1), "reject a wait longer than its source duration");
    Write(original.callback.data(), 0, original.firstCallbackTable.data());
    Check(original.Read(clock).has_value(), "new and loaded native quest callback classes match");
    Write(original.callback.data(), 8, static_cast<void*>(nullptr));
    Check(!original.Read(clock), "reject a different callback owner");
    Write(original.callback.data(), 8, original.owner.data());
    Write(original.timer.data(), 0x44, 2U);
    Check(!original.Read(clock), "defer a repeating timer");
    Write(original.timer.data(), 0x44, 1U);
    Write(original.timer.data(), 0x94, static_cast<std::uint8_t>(1));
    Check(!original.Read(clock), "defer an unverified native timer mode");
    Write(original.timer.data(), 0x94, static_cast<std::uint8_t>(0));
    Write(original.List(), 0x10 + 24, ptfr::NativeGameTimerReference{original.timer.data(), &original.references});
    Write(original.List(), 0x3008, 2U);
    Check(!original.Read(clock), "reject duplicate timer identities");
    Write(original.List(), 0x3008, 513U);
    Check(!original.Read(clock), "reject an out-of-range timer count");
    Write(original.List(), 0x3008, 0U);
    Check(!original.Read(clock), "absence from the active list stays unknown");
    Check(!ptfr::RebaseOneShotGameWait(capture->wait, authored, ptfr::GameTimeCheckpoint::MaxClock - 1) &&
              !ptfr::RebaseOneShotGameWait({authored + 1}, authored, clock) &&
              !ptfr::RebaseOneShotGameWait({0}, authored, clock),
          "reject overflowing, longer-than-authored or empty restore durations");

    const auto postTower = deadline + 100;
    const auto restored = ptfr::RebaseOneShotGameWait(capture->wait, authored, postTower);
    Check(restored && *restored - postTower == capture->wait.seconds,
          "the remaining game time ignores elapsed Tower time");
    if (!restored)
        return;
    TimerFixture resumed(native, id + 1, authored);
    Write(resumed.owner.data(), 0x28, 412U);
    resumed.SetDeadline(*restored);
    Check(resumed.Tick(*restored - 1) == 0 && callbacks == 0,
          "the native timer cannot notify one game second early");

    // Model saved timer data with the native absolute deadline. Stock
    // reattachment supplies the callback on the new handler in a live reload.
    const auto reloadClock = postTower + 3600;
    const auto elapsed = resumed.Read(reloadClock);
    Check(elapsed && elapsed->wait.seconds == capture->wait.seconds - 3600,
          "elapsed free-roam time reduces the remaining duration");
    TimerFixture reloaded(native, id + 1, authored);
    Write(reloaded.owner.data(), 0x28, 413U);
    reloaded.SetDeadline(resumed.NativeDeadline(native));
    Check(reloaded.RebindLoadedCallback(native), "native lookup and callback assignment rebind the saved timer");
    Check(reloaded.Tick(*restored - 1) == 0 && callbacks == 0,
          "isolated reload keeps the rebased deadline");
    Check(reloaded.Tick(*restored) == 1 && callbacks == 1 && notificationCount == 1 && firedSlot == 413,
          "the native callback queues exactly one notification on the current slot");
    Check(reloaded.Tick(*restored + 1) != 0 && callbacks == 2 && notificationCount == 1 && firedSlot == 413,
          "a duplicate callback reaches native readiness twice and queues the slot only once");
    Check(ptfr::ReadGameTimeField<std::uint32_t>(original.owner.data(), 0x2C) == 0 &&
              ptfr::ReadGameTimeField<std::uint32_t>(resumed.owner.data(), 0x2C) == 0,
          "the original and pre-reload handlers remain quiet");
}

void HoldCheck(const NativeCode& native, std::uint32_t id, std::uint32_t clock,
               std::uint32_t deadline, std::uint32_t authored)
{
    const ptfr::GameTimeWorkerMethods worker{
        native.At<decltype(ptfr::GameTimeWorkerMethods::remove)>(0xB79130),
        native.At<decltype(ptfr::GameTimeWorkerMethods::insert)>(0xB79234),
        native.At<decltype(ptfr::GameTimeWorkerMethods::release)>(0x195798)};
    const auto neighborStorage = std::make_unique<TimerFixture>(native, id + 1, authored);
    const auto liveStorage = std::make_unique<TimerFixture>(native, id, authored);
    auto& neighbor = *neighborStorage;
    auto& live = *liveStorage;
    live.SetDeadline(deadline);
    live.Install(worker);
    neighbor.SetDeadline(deadline + 10);
    neighbor.Install(worker);
    live.AddNeighbor(worker, neighbor);
    Check(live.references == 2 && live.Read(clock).has_value(),
          "the native time system registers a one-shot timer");
    Check(live.HeadTimer() == id && neighbor.references == 3,
          "the later neighboring wait is registered after the selected wait");
    Check(!live.Hold(worker, deadline) && live.references == 2,
          "a due timer keeps its original registration");
    auto held = live.Hold(worker, clock);
    Check(held && held->Checkpoint().seconds == deadline - clock && !live.Read(clock) && live.references == 2,
          "native cancellation removes the pending timer and keeps an owned rollback reference");
    if (!held)
        return;
    Check(live.HeadTimer() == id + 1 && neighbor.NativeDeadline(native) == deadline + 10,
          "native unlink preserves the neighboring timer and its deadline");
    auto differentOwner = live.Owner();
    ++differentOwner.generation;
    Check(!held->Return(differentOwner, clock) && !live.Read(clock),
          "the original callback cannot be returned to a different generation");
    const auto later = deadline + 30;
    Check(held->Return(live.Owner(), later) && live.references == 2,
          "rollback uses native insertion and releases the temporary reference");
    const auto returned = live.Read(later);
    Check(returned && returned->wait.seconds == deadline - clock && !held->Return(live.Owner(), later),
          "rollback returns the exact duration only once");
    Check(live.HeadTimer() == id + 1, "native reinsertion orders the returned wait after the earlier deadline");
    live.Remove(worker, id);
    live.Remove(worker, id + 1);
    Check(live.HeadTimer() == 0 && live.references == 1 && neighbor.references == 2,
          "ordinary expiry or stop can retire both list references independently");
}

std::uint32_t Number(const char* text)
{
    char* end = nullptr;
    errno = 0;
    const auto value = std::strtoul(text, &end, 10);
    if (errno || !text[0] || *end)
        throw std::runtime_error("Invalid fixture number");
    return value;
}
} // namespace

int main(int argc, char** argv)
{
    if (argc != 6)
        return 2;
    std::setvbuf(stdout, nullptr, _IONBF, 0);
    AddVectoredExceptionHandler(1, &ReportNativeFault);
    try
    {
        NativeCode native;
        native.Load(argv[1]);
        markReady = native.At<NativeReady>(0x88B6AC);
        CheckWait(native, Number(argv[2]), Number(argv[3]), Number(argv[4]), Number(argv[5]));
        HoldCheck(native, Number(argv[2]), Number(argv[3]), Number(argv[4]), Number(argv[5]));
        std::printf("%u passed, %u failed\n", passed, failed);
        return failed ? 1 : 0;
    }
    catch (const std::exception& error)
    {
        std::fprintf(stderr, "%s\n", error.what());
        return 2;
    }
}
