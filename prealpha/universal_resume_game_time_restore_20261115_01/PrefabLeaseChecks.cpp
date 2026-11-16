#include "PrefabLeases.hpp"

#include <cstdio>

namespace
{
using namespace ptfr::resume;

template<typename T>
void Put(void* object, std::size_t offset, T value)
{
    std::memcpy(static_cast<std::byte*>(object) + offset, &value, sizeof(value));
}

struct Fixture
{
    static constexpr PrefabTicketIds First{11, 12};
    static constexpr PrefabTicketIds Second{27, 32};
    static constexpr std::array<std::uint64_t, 2> Refs{0x1234567890ULL, 0x9876543210ULL};

    explicit Fixture(PrefabTicketIds pair)
    {
        Put(loader.data(), 0, Type());
        ids = {pair.phase, pair.handler, 5};
        Put(loader.data(), 0x48, tickets.data());
        PutArray(loader.data(), 0x38, ids);
        PutArray(loader.data(), 0x60, sharedRefs);
        PutArray(loader.data(), 0x70, sharedCounts);
        Put(loader.data(), 0xA0, ready.data());
        Put(loader.data(), 0xA8, 1U);
        PutArray(tickets.data(), 0, phaseRefs);
        PutArray(tickets.data() + 0x68, 0, handlerRefs);
    }

    const void* Type() const { return &loaderType; }

    std::optional<PrefabLeases> Read(PrefabTicketIds pair, std::optional<PrefabLeases> old = std::nullopt)
    {
        return ReadPrefabLeases(loader.data(), Type(), pair, old);
    }

    alignas(void*) std::array<std::byte, 0xF0> loader{};
    alignas(void*) std::array<std::byte, 3 * 0x68> tickets{};
    std::array<std::uint32_t, 3> ids{};
    std::array<std::uint64_t, 2> phaseRefs{Refs};
    std::array<std::uint64_t, 2> handlerRefs{Refs};
    std::array<std::uint64_t, 3> sharedRefs{Refs[0], 5, Refs[1]};
    std::array<std::uint32_t, 3> sharedCounts{3, 1, 2};
    std::array<std::uint32_t, 1> ready{};

private:
    template<typename T, std::size_t Count>
    static void PutArray(void* object, std::size_t offset, std::array<T, Count>& array)
    {
        Put(object, offset, array.data());
        Put(object, offset + 8, static_cast<std::uint32_t>(Count));
        Put(object, offset + 12, static_cast<std::uint32_t>(Count));
    }
    const int loaderType{};
};

unsigned failures{};
void Check(bool success, const char* label)
{
    std::printf("%s %s\n", success ? "PASS" : "FAIL", label);
    failures += !success;
}
} // namespace

int main()
{
    Fixture before(Fixture::First);
    const auto old = before.Read(Fixture::First);
    Check(old && old->refs == Fixture::Refs, "both original tickets reference the same two resolved prefabs");
    if (!old)
        return 1;
    Fixture after(Fixture::Second);
    const auto next = after.Read(Fixture::Second, old);
    Check(next && next->refs == old->refs, "fresh tickets reacquire both matching refs with shared leases allowed");
    Check(after.loader[0x30] == std::byte{}, "the loader lock is released after readback");
    Check(!before.Read(Fixture::First, old), "old native ticket IDs cannot be adopted as the replacements");

    after.ids.back() = Fixture::First.handler;
    Check(!after.Read(Fixture::Second, old), "a still-registered old ticket defers the handoff");
    after.ids.back() = 5;
    Put(after.loader.data(), 0xAC, 1U);
    after.ready.front() = Fixture::First.phase;
    Check(!after.Read(Fixture::Second, old), "an old notification in the prefab ready queue defers the handoff");
    after.ready.front() = Fixture::Second.phase;
    Check(!after.Read(Fixture::Second, old), "a fresh prefab callback still queued defers readback");
    Put(after.loader.data(), 0xAC, 0U);
    Put(after.tickets.data(), 0x1C, 1U);
    Check(!after.Read(Fixture::Second, old), "unsettled prefab requests defer readback");
    Put(after.tickets.data(), 0x1C, 0U);
    Put(after.tickets.data(), 0x60, std::uint8_t{1});
    Check(!after.Read(Fixture::Second, old), "a failed native reference resolution defers readback");
    Put(after.tickets.data(), 0x60, std::uint8_t{});
    after.handlerRefs[1] = 4;
    Check(!after.Read(Fixture::Second, old), "mismatched resolved prefab references defer readback");
    after.handlerRefs[1] = Fixture::Refs[1];
    after.sharedCounts[2] = 1;
    Check(!after.Read(Fixture::Second, old), "a reference must carry both selected ticket leases");
    after.sharedCounts[2] = 2;
    after.loader[0x30] = std::byte{1};
    Check(!after.Read(Fixture::Second, old) && after.loader[0x30] == std::byte{1},
          "an in-progress native reader defers without taking its lock");
    return failures != 0;
}
