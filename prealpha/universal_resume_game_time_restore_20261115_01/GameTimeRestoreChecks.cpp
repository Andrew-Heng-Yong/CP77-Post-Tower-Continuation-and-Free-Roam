#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>

#include "GameTimeRestore.hpp"
#include "../universal_resume_save_admission_20261115_01/SaveAdmission.hpp"
#include "fixture_input.hpp"

#include <array>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <stdexcept>
#include <vector>

namespace
{
using namespace ptfr;
using namespace ptfr::resume;
constexpr auto ImageSize = 0x4000000U;
constexpr auto FactoryRelay = 0x4000U;
constexpr auto HandlerType = 0x31C2388U;
constexpr auto RecordType = 0x30A75A8U;
constexpr auto InitialCallback = 0x36A1D50U;
constexpr auto LoadedCallback = 0x36A1D20U;
constexpr auto TimeSystemSize = 0x6EC00U;
constexpr auto NeighborKey = SavedNodeKey + 1;
constexpr auto NeighborSeconds = 900U;
constexpr auto RebuiltSlot = 1102U;

std::uintptr_t imageBase{};

LONG PrintNativeFault(EXCEPTION_POINTERS* exception)
{
    if (exception->ExceptionRecord->ExceptionCode == EXCEPTION_ACCESS_VIOLATION)
        std::fprintf(stderr, "Native fixture fault at %016llX (image %016llX), address %016llX\n",
                     exception->ContextRecord->Rip, static_cast<unsigned long long>(imageBase),
                     exception->ExceptionRecord->ExceptionInformation[1]);
    return EXCEPTION_CONTINUE_SEARCH;
}

template<typename T>
void Put(void* object, std::size_t offset, T value)
{
    std::memcpy(static_cast<std::byte*>(object) + offset, &value, sizeof(value));
}

unsigned failures{};
void Check(bool condition, const char* label)
{
    std::printf("%s %s\n", condition ? "PASS" : "FAIL", label);
    failures += !condition;
}

class NativeCode
{
public:
    explicit NativeCode(const char* input)
        : base(static_cast<std::byte*>(VirtualAlloc(nullptr, ImageSize, MEM_RESERVE | MEM_COMMIT,
                                                    PAGE_EXECUTE_READWRITE)))
    {
        if (!base)
            throw std::runtime_error("Cannot map native code in the fixture");
        imageBase = reinterpret_cast<std::uintptr_t>(base);
        std::ifstream file(input, std::ios::binary);
        const auto count = Read(file);
        if (!count || count > 32)
            throw std::runtime_error("Unexpected native slice count");
        for (std::uint32_t i = 0; i < count; ++i)
        {
            const auto address = Read(file);
            const auto size = Read(file);
            if (!size || address >= ImageSize || size > ImageSize - address ||
                !file.read(reinterpret_cast<char*>(base + address), size))
                throw std::runtime_error("Truncated native slice");
        }
        if (file.peek() != EOF)
            throw std::runtime_error("Trailing data in native fixture");
    }

    ~NativeCode() { VirtualFree(base, 0, MEM_RELEASE); }
    NativeCode(const NativeCode&) = delete;
    NativeCode& operator=(const NativeCode&) = delete;

    template<typename T>
    T At(std::uint32_t rva) const { return reinterpret_cast<T>(base + rva); }

    template<typename T>
    void Redirect(std::uint32_t rva, T destination)
    {
        std::uint8_t jump[]{0x48, 0xB8, 0, 0, 0, 0, 0, 0, 0, 0, 0xFF, 0xE0};
        Put(jump, 2, reinterpret_cast<std::uintptr_t>(destination));
        std::memcpy(base + rva, jump, sizeof(jump));
    }

    void Return(std::uint32_t rva) { base[rva] = std::byte{0xC3}; }

    void ConnectFactory()
    {
        constexpr auto Call = 0xA09C4DU;
        if (base[Call] != std::byte{0xE8})
            throw std::runtime_error("Unexpected native factory call");
        Put(base, Call + 1, static_cast<std::int32_t>(FactoryRelay) - static_cast<std::int32_t>(Call + 5));
    }

private:
    static std::uint32_t Read(std::ifstream& file)
    {
        std::uint32_t value{};
        if (!file.read(reinterpret_cast<char*>(&value), sizeof(value)))
            throw std::runtime_error("Missing native slice header");
        return value;
    }

    std::byte* const base;
};

struct TimerRun;
TimerRun* current{};
GameTimeFactory nativeFactory{};

struct TimerRun
{
    struct Allocation
    {
        alignas(16) std::array<std::byte, 0xA0> timer{};
        long count{1};
    };
    struct Enqueued
    {
        NativeGameTimerReference ref;
        std::uint32_t deadline;
    };

    explicit TimerRun(const NativeCode& code)
        : native(code), timeSystem(TimeSystemSize)
    {
        current = this;
        contextVT[0x100 / 8] = reinterpret_cast<const void*>(&QueryContext);
        questVT[0x2C8 / 8] = reinterpret_cast<const void*>(&ReadMapping);
        questVT[0x2B8 / 8] = reinterpret_cast<const void*>(&WriteMapping);
        questVT[0x2D0 / 8] = reinterpret_cast<const void*>(&HasMapping);
        questVT[0x2C0 / 8] = reinterpret_cast<const void*>(&RemoveMapping);
        questVT[0x200 / 8] = reinterpret_cast<const void*>(&Notify);
        timeVT[0x240 / 8] = native.At<const void*>(0xA09BC4);
        timeVT[0x250 / 8] = native.At<const void*>(0x193674);
        clockVT[0xF8 / 8] = reinterpret_cast<const void*>(&ReadClock);
        eventVT[1] = native.At<const void*>(0x88BC48);
        Put(timeSystem.data(), 0, timeVT.data());
        Put(timeSystem.data(), 0xE8, clock.data());
        Put(timeSystem.data(), 0x118, SavedTimer + 50U);
        Put(clock.data(), 0, clockVT.data());
        Put(quests.data(), 0, questVT.data());
        Put(events.data(), 0, eventVT.data());
        Put(events.data(), 0x28, quests.data());
        Put(context.data(), 0, contextVT.data());
        Put(context.data(), 0x18, quests.data());
        Put(context.data(), 0xE8, timeSystem.data());
        SeedHandler(0, SavedNodeKey, SavedAuthoredSeconds, RebuiltSlot);
        SeedHandler(1, NeighborKey, NeighborSeconds, RebuiltSlot + 1);
    }

    ~TimerRun() { current = nullptr; }

    GameTimeRestoreMethods Methods() const
    {
        return {native.At<const void*>(HandlerType), native.At<const void*>(RecordType),
                native.At<const void*>(InitialCallback), native.At<const void*>(LoadedCallback), &ReadMapping};
    }

    GameTimeRestoreOwner Owner() const
    {
        return {quests.data(), timeSystem.data(), handlers[0].data(),
                SavedNodeKey, SavedTimer, SavedAuthoredSeconds};
    }

    void Initialize(std::size_t index)
    {
        native.At<void (*)(void*, void*)>(0x193C74)(handlers[index].data(), context.data());
    }

    void Uninitialize()
    {
        native.At<void (*)(void*, void*)>(0x1934AC)(handlers[0].data(), context.data());
    }

    std::uint32_t Ready() const { return ReadGameTimeField<std::uint32_t>(handlers[0].data(), 0x2C); }
    std::uint32_t Enabled() const { return ReadGameTimeField<std::uint32_t>(handlers[0].data(), 0x30); }

    // The real clock job would consume the queue and insert these into the
    // active list. Model that boundary separately from stock scheduling.
    void ConsumeQueue()
    {
        auto* list = timeSystem.data() + GameTimerList;
        for (std::uint32_t i = 0; i < enqueuedCount; ++i)
            Put(list, 24 * i + 0x10, enqueued[i].ref);
        Put(list, GameTimerCount, enqueuedCount);
    }

    std::uint8_t Evaluate(void* timer, std::uint32_t time) const
    {
        return native.At<std::uint8_t (*)(void*, std::uint32_t)>(0x193B00)(timer, time);
    }

    static void* Allocate()
    {
        if (current->allocated == current->allocations.size())
            std::abort();
        return current->allocations[current->allocated++].timer.data();
    }

    static void MakeRef(NativeGameTimerReference* ref, void* timer)
    {
        for (auto& allocation : current->allocations)
        {
            if (timer == allocation.timer.data())
            {
                *ref = {timer, &allocation.count};
                return;
            }
        }
        std::abort();
    }

    static void Enqueue(void* queue, const NativeGameTimerReference* ref)
    {
        if (queue != current->timeSystem.data() + 0x6BAC0 || !ref->timer ||
            current->enqueuedCount == current->enqueued.size())
            std::abort();
        const auto deadline = ReadGameTimeField<std::uint32_t>(ref->timer, 0x40);
        current->enqueued[current->enqueuedCount++] = {*ref, deadline};
    }

    static void Cancel(void* queue, const std::uint32_t* id)
    {
        if (queue != current->timeSystem.data() + 0x63200)
            std::abort();
        current->cancelled = *id;
    }

    const NativeCode& native;
    std::vector<std::byte> timeSystem;
    alignas(void*) std::array<std::byte, 0xF0> context{};
    std::array<std::optional<std::uint64_t>, 2> mappings{};
    std::array<Enqueued, 3> enqueued{};
    std::uint32_t clockNow{FixtureClock};
    std::uint32_t enqueuedCount{};
    std::uint32_t cancelled{};
    std::uint32_t notifiedSlot{};
    unsigned notifications{};

private:
    void SeedHandler(std::size_t index, std::uint64_t nodeKey, std::uint32_t authored, std::uint32_t slot)
    {
        auto* handler = handlers[index].data();
        Put(handler, 0, native.At<const void*>(HandlerType));
        Put(handler, 0x18, events.data());
        Put(handler, 0x28, slot);
        Put(handler, 0x38, nodeKey);
        Put(handler, 0x44, authored);
    }

    static std::size_t MappingIndex(std::uint64_t key)
    {
        if (key == SavedNodeKey)
            return 0;
        if (key == NeighborKey)
            return 1;
        std::abort();
    }

    static bool QueryContext(const void*) { return false; }
    static bool ReadMapping(const void* quests, std::uint64_t key, std::uint64_t* value)
    {
        if (quests != current->quests.data())
            std::abort();
        const auto match = current->mappings[MappingIndex(key)];
        if (match)
            *value = *match;
        return match.has_value();
    }
    static void WriteMapping(void*, std::uint64_t key, std::uint64_t value)
    {
        current->mappings[MappingIndex(key)] = value;
    }
    static bool HasMapping(const void*, std::uint64_t key)
    {
        return current->mappings[MappingIndex(key)].has_value();
    }
    static void RemoveMapping(void*, std::uint64_t key) { current->mappings[MappingIndex(key)].reset(); }
    static std::uint32_t* ReadClock(void*, std::uint32_t* value)
    {
        *value = current->clockNow;
        return value;
    }
    static void Notify(void*, std::uint32_t slot)
    {
        current->notifiedSlot = slot;
        ++current->notifications;
    }

    alignas(16) std::array<Allocation, 3> allocations{};
    std::size_t allocated{};
    alignas(void*) std::array<std::array<std::byte, 0x50>, 2> handlers{};
    alignas(void*) std::array<std::byte, 0x40> quests{};
    alignas(void*) std::array<std::byte, 0x30> events{};
    alignas(void*) std::array<std::byte, 8> clock{};
    std::array<const void*, 0x108 / 8> contextVT{};
    std::array<const void*, 0x2D8 / 8> questVT{};
    std::array<const void*, 0x258 / 8> timeVT{};
    std::array<const void*, 0x100 / 8> clockVT{};
    std::array<const void*, 2> eventVT{};
};

void* EmptyLabel(void* out)
{
    Put(out, 0, std::uint64_t{});
    Put(out, 8, std::uint32_t{});
    return out;
}
void* ContextLabel(const void*, void* out) { return EmptyLabel(out); }
std::uint64_t* EmptyName(std::uint64_t* out) { *out = 0; return out; }

NativeGameTimerReference* BuildTimer(NativeGameTimerReference* out, const std::uint32_t* id,
                                    void* callback, const std::uint32_t* deadline, const std::uint32_t* repeats,
                                    const std::uint8_t* mode, const std::uint32_t* authored,
                                    const std::uint64_t* label, const std::uint64_t* source)
{
    return GameTimeRestoreScope::MakeTimer(nativeFactory, out, id, callback, deadline, repeats,
                                           mode, authored, label, source);
}

void BindFixture(NativeCode& code)
{
    nativeFactory = code.At<GameTimeFactory>(0xA0A84C);
    code.Redirect(FactoryRelay, &BuildTimer);
    code.ConnectFactory();
    code.Redirect(0x19447C, &ContextLabel);
    code.Redirect(0x3E6444, &EmptyLabel);
    code.Redirect(0x1F52D8, &EmptyName);
    code.Redirect(0x194A1C, &EmptyName);
    code.Redirect(0x260B390, &TimerRun::Allocate);
    code.Redirect(0x1A62A0, &TimerRun::MakeRef);
    code.Redirect(0x2179B80, &TimerRun::Enqueue);
    code.Redirect(0x2179420, &TimerRun::Cancel);
    for (const auto stub : {0x277CECU, 0x27C728U, 0x195798U, 0x189184U})
        code.Return(stub);
    for (const auto offset : {0x00U, 0x08U})
        Put(code.At<void*>(InitialCallback), offset, code.At<const void*>(0x18F2540));
    Put(code.At<void*>(InitialCallback), 0x10, code.At<const void*>(0x1304ED8));
    Put(code.At<void*>(InitialCallback), 0x20, code.At<const void*>(0x258480));
    Put(code.At<void*>(RecordType), 0x130, code.At<const void*>(0x193E58));
    if (!FlushInstructionCache(GetCurrentProcess(), code.At<void*>(0), ImageSize))
        throw std::runtime_error("Could not flush fixture instructions");
}

void CheckRestored(const NativeCode& code, const SaveGuard::HandoffPermit& permit)
{
    TimerRun run(code);
    const auto target = run.Owner();
    const auto native = run.Methods();
    GameTimeRestoreScope restore(permit, native, target, run.context.data(), {SavedRemainingSeconds});
    Check(static_cast<bool>(restore) && !restore.Mapped(), "the selected handler arms before any mapping is published");
    if (!restore)
        return;
    run.Initialize(1);
    Check(run.enqueuedCount == 1 && run.enqueued[0].deadline == FixtureClock + NeighborSeconds,
          "the stock scheduler receives an unrelated wait at its normal deadline");
    run.Initialize(0);
    const auto mapping = restore.Mapped();
    Check(mapping && mapping->id != SavedTimer && run.mappings[0] == mapping->id,
          "the native initializer publishes a new timer ID at the original Falco node key");
    if (!mapping || run.enqueuedCount != 2)
        return;
    const auto& record = run.enqueued[1];
    Check(record.deadline == FixtureClock + SavedRemainingSeconds && mapping->deadline == record.deadline,
          "the shortened deadline is present when the stock scheduler enqueues the timer");
    Check(ReadGameTimeField<std::uint32_t>(record.ref.timer, 0x90) == SavedAuthoredSeconds &&
              run.Ready() == 0 && run.notifications == 0,
          "the authored delay and native one-shot callback remain selected and pending");
    Check(!mapping->OnClock(native, target, FixtureClock), "a queued timer is not yet on the clock's active list");
    run.ConsumeQueue();
    Check(mapping->OnClock(native, target, FixtureClock + 5), "the clock reads the exact deadline and new callback owner");
    Check(run.Evaluate(record.ref.timer, mapping->deadline - 1) == 0 && run.notifications == 0,
          "the native evaluator stays quiet before the restored deadline");
    Check(run.Evaluate(record.ref.timer, mapping->deadline) == 1 && run.notifications == 1 &&
              run.notifiedSlot == RebuiltSlot && run.Ready() == 1,
          "the native callback notifies the rebuilt slot once when the restored wait expires");
}

void CheckDeferred(const NativeCode& code, const SaveGuard::HandoffPermit& permit)
{
    TimerRun run(code);
    run.mappings[0] = SavedTimer;
    GameTimeRestoreScope restore(permit, run.Methods(), run.Owner(), run.context.data(), {SavedRemainingSeconds});
    Check(!restore && run.enqueuedCount == 0 && run.Ready() == 0,
          "an old mapping defers before the native initializer can use its ready fallback");
}

void CheckCancelled(const NativeCode& code, const SaveGuard::HandoffPermit& permit)
{
    TimerRun run(code);
    Put(run.timeSystem.data(), 0x118, SavedTimer - 1);
    GameTimeRestoreScope restore(permit, run.Methods(), run.Owner(), run.context.data(), {SavedRemainingSeconds});
    if (!restore)
        throw std::runtime_error("Could not set up the timer-ID reuse control");
    run.Initialize(0);
    Check(!restore.Mapped() && run.enqueuedCount == 1 && run.enqueued[0].deadline == FixtureClock + SavedAuthoredSeconds,
          "reusing the retired ID cannot commit the rebased timer");
    run.Uninitialize();
    Check(!run.mappings[0] && run.cancelled == SavedTimer && run.Enabled() == 0 && run.notifications == 0,
          "native uninitialization clears the failed mapping and queues its cancellation");
}
} // namespace

int main(int argc, char** argv)
{
    if (argc != 2)
        return 2;
    AddVectoredExceptionHandler(1, &PrintNativeFault);
    try
    {
        NativeCode native(argv[1]);
        BindFixture(native);
        SaveAdmission admission;
        std::array<std::uint8_t, 0x309> session{};
        session[0x308] = 0x10;
        {
            TimerRun run(native);
            const auto saveInProgress = admission.TryHandoff(session.data());
            GameTimeRestoreScope blocked(saveInProgress, run.Methods(), run.Owner(),
                                         run.context.data(), {SavedRemainingSeconds});
            Check(!blocked, "an active save keeps the selected native factory unarmed");
        }
        session[0x308] = 0;
        const auto permit = admission.TryHandoff(session.data());
        if (!permit)
            return 1;
        CheckRestored(native, permit);
        CheckDeferred(native, permit);
        CheckCancelled(native, permit);
        return failures != 0;
    }
    catch (const std::exception& error)
    {
        std::fprintf(stderr, "%s\n", error.what());
        return 2;
    }
}
