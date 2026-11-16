#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include "WorldPrefabSupport.hpp"

#include <cstdio>
#include <fstream>

namespace
{
using namespace ptfr::resume;

int failures{};

void Check(bool condition, const char* label)
{
    std::printf("%s %s\n", condition ? "PASS" : "FAIL", label);
    failures += !condition;
}

template<typename T>
void Put(void* object, std::size_t offset, T value)
{
    std::memcpy(static_cast<std::byte*>(object) + offset, &value, sizeof(value));
}

template<typename T>
void PutArray(void* object, std::size_t offset, T* elements, std::uint32_t count)
{
    Put(object, offset, elements);
    Put(object, offset + 8, count);
    Put(object, offset + 12, count);
}

constexpr std::array<std::uint64_t, 2> Refs{0xA000000000000001ULL, 0xB000000000000002ULL};
constexpr auto Missing = UINT32_MAX;
const int worldType{};
const int updateType{};
const int loaderType{};

struct MapEntry
{
    std::uint32_t next{Missing};
    std::uint32_t lowHash;
    std::uint64_t ref;
};

struct IndexEntry
{
    MapEntry key;
    std::uint32_t* indices;
    std::uint32_t capacity;
    std::uint32_t count;
};
static_assert(sizeof(IndexEntry) == 0x20);

struct DesiredEntry
{
    MapEntry key;
    std::uint8_t value;
};
static_assert(sizeof(DesiredEntry) == 0x18);

struct Fixture
{
    Fixture()
    {
        Put(world.data(), 0x00, &worldType);
        Put(world.data(), 0x48, &updateType);
        InitializeSRWLock(reinterpret_cast<SRWLOCK*>(world.data() + 0x2A0));
        InitializeSRWLock(reinterpret_cast<SRWLOCK*>(world.data() + 0x2E8));
        ConstructWorldMap(0x128, indexed, indexBuckets);
        ConstructWorldMap(0x2A8, desired, desiredBuckets);
        PutArray(world.data(), 0x50, sectors.data(), 2);
        for (std::size_t i = 0; i < 2; ++i)
        {
            Put(sectors[i].data(), 0x28, &worldType);
            Put(sectors[i].data(), 0x80, std::uint8_t{1});
            Put(sectors[i].data(), 0x82, std::uint8_t{2});
            nodePointers[i] = nodes[i].data();
            PutArray(sectors[i].data(), 0x50, &nodePointers[i], 1);
            Put(nodes[i].data(), 0x25, std::uint8_t{0xC});
            Put(nodes[i].data(), 8, nodeData[i].data());
            Put(nodeData[i].data(), 0x8C, std::uint8_t{0x20});
            PutArray(tickets[i].data(), 0, leaseRefs[i].data(), 2);
        }
        Put(loader.data(), 0, &loaderType);
        Put(loader.data(), 0xC8, world.data());
        Put(loader.data(), 0x48, tickets.data());
        PutArray(loader.data(), 0x38, ticketIds.data(), 2);
        Put(loader.data(), 0x44, 1U);
        PutArray(loader.data(), 0x60, Refs.data(), 2);
        PutArray(loader.data(), 0x70, leaseCounts.data(), 2);
    }

    template<typename Entry>
    void ConstructWorldMap(std::size_t offset, std::array<Entry, 2>& values, std::array<std::uint32_t, 4>& buckets)
    {
        Put(world.data(), offset, buckets.data());
        Put(world.data(), offset + 8, 2U);
        Put(world.data(), offset + 0x0C, 4U);
        Put(world.data(), offset + 0x10, values.data());
        Put(world.data(), offset + 0x1C, static_cast<std::uint32_t>(sizeof(Entry)));
    }

    std::optional<WorldPrefabSupport> World(const WorldPrefabMethods& native)
    {
        return ReadWorldPrefabSupport(world.data() + 0x48, world.data(), Refs, native);
    }

    std::array<std::uint32_t, 2> indices{0, 1};
    std::array<std::uint32_t, 4> indexBuckets{Missing, 0, 1, Missing};
    std::array<std::uint32_t, 4> desiredBuckets{Missing, 0, 1, Missing};
    std::array<IndexEntry, 2> indexed{
        IndexEntry{{Missing, 1, Refs[0]}, &indices[0], 1, 1},
        IndexEntry{{Missing, 2, Refs[1]}, &indices[1], 1, 1},
    };
    std::array<DesiredEntry, 2> desired{{{{Missing, 1, Refs[0]}, 1}, {{Missing, 2, Refs[1]}, 1}}};
    alignas(8) std::array<std::byte, 0x3E0> world{};
    alignas(8) std::array<std::array<std::byte, 0x90>, 2> sectors{};
    alignas(8) std::array<std::array<std::byte, 0x28>, 2> nodes{};
    alignas(8) std::array<std::array<std::byte, 0x90>, 2> nodeData{};
    std::array<const void*, 2> nodePointers{};
    alignas(8) std::array<std::byte, 0xF0> loader{};
    std::array<std::array<std::uint64_t, 2>, 2> leaseRefs{Refs, Refs};
    alignas(8) std::array<std::array<std::byte, 0x68>, 2> tickets{};
    std::array<std::uint32_t, 2> ticketIds{10, 11};
    std::array<std::uint32_t, 2> leaseCounts{1, 1};
};

void CheckWorld(const WorldPrefabMethods& native)
{
    Fixture f;
    const auto get = [&] { return f.World(native); };
    const auto ready = [&] {
        const auto observation = get();
        return observation && observation->Ready();
    };
    const auto state = [&](std::size_t i, WorldPrefabStatus expected) {
        const auto observation = get();
        return observation && observation->states[i] == expected;
    };
    Check(ready(), "both indexed and desired groups have mounted support");
    Check(!ReadWorldPrefabSupport(f.world.data() + 0x48, &worldType, Refs, native),
          "the update receiver must be the bound retained world");
    f.indexBuckets[2] = Missing;
    Check(state(1, WorldPrefabStatus::MissingIndex), "a missing index cannot pass as a ready prefab");
    f.indexBuckets[2] = 1;
    f.indexed[1].count = 0;
    Check(state(1, WorldPrefabStatus::MissingIndex), "an empty sector list cannot pass as a replacement");
    f.indexed[1].count = 1;
    f.desired[0].value = 0;
    Check(state(0, WorldPrefabStatus::AwaitingRequest), "indexed but unrequested support defers");
    f.desired[0].value = 1;
    prefab_detail::WorldRequest request{Refs[0], 0};
    PutArray(f.world.data(), 0x2D8, &request, 1);
    Check(state(0, WorldPrefabStatus::AwaitingRequest), "a pending native disable prevents stale readiness");
    request.ref = 9;
    Check(ready(), "unrelated queued world work stays independent");
    Put(f.world.data(), 0x2E4, 0U);
    Put(f.sectors[0].data(), 0x82, std::uint8_t{1});
    Check(state(0, WorldPrefabStatus::AwaitingStreaming), "a native pending sector defers");
    Put(f.sectors[0].data(), 0x82, std::uint8_t{2});
    Put(f.nodes[0].data(), 0x25, std::uint8_t{4});
    Check(state(0, WorldPrefabStatus::AwaitingStreaming), "a settled fallback without a requested node defers");
    Put(f.nodes[0].data(), 0x25, std::uint8_t{0xC});
    Put(f.nodeData[0].data(), 0x8C, std::uint8_t{0});
    Check(state(0, WorldPrefabStatus::AwaitingStreaming), "a requested node may still lack ready native data");
    Put(f.nodeData[0].data(), 0x8C, std::uint8_t{0x20});
    f.indices[1] = 2;
    Check(!get(), "an out-of-range physical sector is rejected");
    f.indices[1] = 1;
    auto* queueLock = reinterpret_cast<SRWLOCK*>(f.world.data() + 0x2E8);
    AcquireSRWLockExclusive(queueLock);
    Check(!get(), "the readback defers while native request publication owns the lock");
    ReleaseSRWLockExclusive(queueLock);
    Check(ready(), "readback releases both locks and observes a later ready result");
}

void CheckLeases()
{
    Fixture f;
    const auto one = ReadPrefabLeaseBinding(f.loader.data(), &loaderType, {10, 0});
    Check(one && one->world == f.world.data() && one->refs == Refs, "ordinary load can bind one native child ticket");
    if (!one)
        return;
    Check(!ReadPrefabRetirement(f.loader.data(), &loaderType, *one), "a live old child ticket prevents retirement");
    Put(f.loader.data(), 0x44, 2U);
    f.leaseCounts = {2, 3};
    const auto two = ReadPrefabLeaseBinding(f.loader.data(), &loaderType, {10, 11});
    Check(two && two->refs == Refs, "a stock fresh phase can bind both native tickets");
    if (!two)
        return;
    Put(f.loader.data(), 0x44, 0U);
    Put(f.loader.data(), 0x6C, 1U);
    Put(f.loader.data(), 0x7C, 1U);
    f.leaseCounts = {1, 0};
    auto retired = ReadPrefabRetirement(f.loader.data(), &loaderType, *two);
    Check(retired && (*retired)[0] == 1 && (*retired)[1] == 0, "old lease release preserves an unrelated shared hold");
    PutArray(f.loader.data(), 0xA0, &f.ticketIds[1], 1);
    Check(!ReadPrefabRetirement(f.loader.data(), &loaderType, *two), "an old queued ready callback prevents retirement");
    Put(f.loader.data(), 0xAC, 0U);
    f.ticketIds[0] = 20;
    Put(f.loader.data(), 0x44, 1U);
    Put(f.loader.data(), 0x6C, 2U);
    Put(f.loader.data(), 0x7C, 2U);
    f.leaseCounts = {2, 1};
    const auto next = ReadPrefabLeaseBinding(f.loader.data(), &loaderType, {20, 0}, two);
    Check(next && next->refs == Refs, "mode 2 restores one child lease after both old tickets drain");
    Put(f.tickets[0].data(), 0x1C, 1U);
    Check(!ReadPrefabLeaseBinding(f.loader.data(), &loaderType, {20, 0}, two), "replacement callbacks still pending defer");
    Put(f.tickets[0].data(), 0x1C, 0U);
    Put(f.loader.data(), 0xC8, &updateType);
    Check(!ReadPrefabLeaseBinding(f.loader.data(), &loaderType, {20, 0}, two), "a world identity change defers replacement");
}
} // namespace

int main(int argc, char** argv)
{
    if (argc != 2)
        return 2;
    std::ifstream file(argv[1], std::ios::binary);
    if (!file)
        return 2;
    constexpr auto N = 0x76 + 0x5C;
    auto* code = static_cast<std::byte*>(VirtualAlloc(nullptr, N, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE));
    if (!code)
        return 2;
    DWORD old{};
    if (!file.read(reinterpret_cast<char*>(code), N) || file.peek() != std::ifstream::traits_type::eof() ||
        !VirtualProtect(code, N, PAGE_EXECUTE_READ, &old) || !FlushInstructionCache(GetCurrentProcess(), code, N))
    {
        VirtualFree(code, 0, MEM_RELEASE);
        return 2;
    }
    const WorldPrefabMethods native{
        &worldType, &updateType,
        reinterpret_cast<decltype(WorldPrefabMethods::find)>(code),
        reinterpret_cast<decltype(WorldPrefabMethods::desired)>(code + 0x76),
    };
    CheckWorld(native);
    CheckLeases();
    VirtualFree(code, 0, MEM_RELEASE);
    return failures != 0;
}
