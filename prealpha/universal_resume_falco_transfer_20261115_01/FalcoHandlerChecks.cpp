#define main PriorPhaseFixture
#include "FalcoRestoreChecks.cpp"
#undef main

namespace
{
struct NativeRegistrationTable
{
    void* unused{};
    const Registration* rows;
    std::uint32_t capacity;
    std::uint32_t size;
};
static_assert(offsetof(NativeRegistrationTable, rows) == 8);
static_assert(offsetof(NativeRegistrationTable, size) == 0x14);

struct HandlerFixture
{
    std::array<std::uint32_t, FalcoRestoreNodes.size()> hashes{};
    std::array<NativePath, FalcoRestoreNodes.size()> paths{};
    const NativePath* preparedPath{};
    std::uint16_t preparedNode{};
    std::size_t preparedCount{};
};
HandlerFixture* handlerFixture{};

const NativePath* FindHandlerPath(const void*, const std::uint32_t* hash)
{
    const auto match = std::ranges::find(handlerFixture->hashes, *hash);
    if (match == handlerFixture->hashes.end())
    {
        nativeArgumentsMatch = false;
        return nullptr;
    }
    return &handlerFixture->paths[static_cast<std::size_t>(match - handlerFixture->hashes.begin())];
}

void MakeHandlerContext(void* quests, void* context, std::uint8_t mode)
{
    MakeContext(quests, context, mode);
    Put(context, 1, mode);
    Put(context, 0xB8, 0U);
}

void PrepareHandler(std::uint8_t mode, const NativePath* path, std::uint16_t node)
{
    nativeArgumentsMatch &= mode == 2;
    handlerFixture->preparedPath = path;
    handlerFixture->preparedNode = node;
    ++handlerFixture->preparedCount;
}

void RestoreHandler(void* root, const void* context, const NativePath* path, std::uint16_t node)
{
    nativeArgumentsMatch &= path == handlerFixture->preparedPath && node == handlerFixture->preparedNode;
    RestorePathStub(root, context, path, node, nullptr);
}

void* FormatResult(void* value) { return value; }
void Ignore(void*, void*) {}

class HandlerDispatchFixture
{
public:
    explicit HandlerDispatchFixture(const char* input)
    {
        std::ifstream blob(input, std::ios::binary);
        std::array<char, 0x185> native{};
        blob.read(native.data(), native.size());
        if (!blob || blob.peek() != EOF)
            throw std::runtime_error("Unexpected handler dispatcher bytes");
        memory = static_cast<std::byte*>(VirtualAlloc(nullptr, 0x4000000, MEM_RESERVE | MEM_COMMIT,
                                                      PAGE_EXECUTE_READWRITE));
        if (!memory)
            throw std::runtime_error("Cannot map native fixture");
        std::memcpy(memory + 0x2B28EC, native.data(), native.size());
        Stub(0x2B1BC4, &FindHandlerPath);
        Stub(0x2B30A0, &MakeHandlerContext);
        Stub(0x2B2F08, &PrepareHandler);
        Stub(0x2B2EB4, &RecordPath);
        Stub(0x2B2D50, &ReleaseContext);
        Stub(0x3E65F0, &FormatResult);
        Stub(0x275C58, &Ignore);
        Stub(0x277CEC, &Ignore);
        FlushInstructionCache(GetCurrentProcess(), memory, 0x4000000);
    }

    ~HandlerDispatchFixture() { VirtualFree(memory, 0, MEM_RELEASE); }

    bool Dispatch(const FalcoRestorePlan& plan)
    {
        auto words = plan.paths;
        HandlerFixture fixture{};
        // The extra cleared row exercises the stock skip path without
        // changing the selected occupation or the phase address.
        std::array<Registration, FalcoRestoreNodes.size() + 1> rows{};
        rows.front() = {0, 0, 0xFFFF};
        for (std::size_t i = 0; i < words.size(); ++i)
        {
            const auto& target = FalcoRestoreNodes[i];
            const auto hash = PhaseHash(FalcoPhases[target.phase].address);
            rows[i + 1] = {target.type, hash, target.node};
            fixture.hashes[i] = hash;
            fixture.paths[i] = {words[i].words.data(), words[i].size, words[i].size - 1};
        }
        handlerFixture = &fixture;
        NativeRegistrationTable registry{nullptr, rows.data(), static_cast<std::uint32_t>(rows.size()),
                                         static_cast<std::uint32_t>(rows.size())};
        std::array<void*, 0x140 / sizeof(void*)> vtable{};
        vtable[0x138 / sizeof(void*)] = reinterpret_cast<void*>(&RestoreHandler);
        void* table = vtable.data();
        alignas(8) std::array<std::byte, 0x300> quests{};
        Put(quests.data(), 0x68, &table);
        Put(quests.data(), 0xE8, &registry);
        Put(quests.data(), 0x258, 6U);
        expectedQuests = quests.data();
        const auto next = reinterpret_cast<bool (*)(void*)>(memory + 0x2B28EC);
        const auto result = next(quests.data());
        handlerFixture = nullptr;
        return result && fixture.preparedCount == plan.paths.size();
    }

private:
    template<class Function>
    void Stub(std::uintptr_t rva, Function call)
    {
        std::uint8_t jump[]{0x48, 0xB8, 0, 0, 0, 0, 0, 0, 0, 0, 0xFF, 0xE0};
        const auto absolute = reinterpret_cast<std::uintptr_t>(call);
        std::memcpy(jump + 2, &absolute, sizeof(absolute));
        std::memcpy(memory + rva, jump, sizeof(jump));
    }
    std::byte* memory{};
};
} // namespace

int main(int argc, char** argv)
{
    if (argc != 3)
        return 2;
    try
    {
        const auto plan = PlanFalcoRestore(SavedState());
        if (!plan)
            return 1;
        RestoreDispatchFixture phases(argv[1]);
        HandlerDispatchFixture handlers(argv[2]);
        SaveAdmission admission;
        std::array<std::uint8_t, 0x309> session{};
        {
            const auto permit = admission.TryHandoff(session.data());
            if (!permit)
                return 1;
            phases.Dispatch(*plan);
            Check(nativeArgumentsMatch && visitedCount == 9 && releases == 9,
                  "the phase pass prepares the original paths in mode 2");
            visitedCount = 0;
            Check(handlers.Dispatch(*plan), "the native handler pass skips the cleared row and prepares the selected rows");
            admission.Poll([](void*, void*) { ++saves; }, session.data(), nullptr);
            Check(saves == 0, "the save guard covers both restore passes");
        }
        Check(nativeArgumentsMatch && contexts == 18 && releases == 18 && visitedCount == 9,
              "both native passes use the expected context and release it for each row");
        bool same = true;
        for (std::size_t i = 0; i < plan->paths.size(); ++i)
            same &= visited[i].words == plan->paths[i].words && visited[i].size == plan->paths[i].size;
        Check(same, "the handler pass resolves both Reyes listeners and Falco on their original paths");
        return failures != 0;
    }
    catch (const std::exception& error)
    {
        std::fprintf(stderr, "%s\n", error.what());
        return 2;
    }
}
