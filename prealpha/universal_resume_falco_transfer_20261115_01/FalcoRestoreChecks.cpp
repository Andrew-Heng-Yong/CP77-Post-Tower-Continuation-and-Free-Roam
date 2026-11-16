#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>

#include "FalcoRestorePlan.hpp"
#include "../universal_resume_save_admission_20261115_01/SaveAdmission.hpp"
#include "fixture_input.hpp"

#include <cstdio>
#include <cstring>
#include <fstream>

namespace
{
using namespace ptfr::resume;

struct NativePath
{
    std::uint16_t* words;
    std::uint32_t capacity;
    std::uint32_t size;
};
struct NativePathList
{
    NativePath* paths;
    std::uint32_t capacity;
    std::uint32_t size;
    std::uint32_t flags{};
};
struct RestoreJob
{
    void* unused{};
    void* quests{};
    NativePathList* paths{};
};
static_assert(sizeof(NativePath) == 0x10);
static_assert(offsetof(NativePathList, flags) == 0x10);
static_assert(offsetof(RestoreJob, paths) == 0x10);

int failures{};
int saves{};
int contexts{};
int releases{};
void* expectedQuests{};
const void* currentContext{};
std::array<RestorePath, FalcoRestoreNodes.size()> visited{};
std::size_t visitedCount{};
bool nativeArgumentsMatch = true;

void Check(bool condition, const char* label)
{
    std::printf("%s %s\n", condition ? "PASS" : "FAIL", label);
    failures += !condition;
}

template<class T>
void Put(void* object, std::size_t offset, T value)
{
    std::memcpy(static_cast<std::byte*>(object) + offset, &value, sizeof(value));
}

void MakeContext(void* quests, void* context, std::uint8_t mode)
{
    nativeArgumentsMatch &= quests == expectedQuests && mode == 2;
    currentContext = context;
    ++contexts;
    Put(context, 0x78, 0U);
    Put(context, 0x7C, 0U);
    Put(context, 0xD4, 0U);
}

bool RestorePathStub(void*, const void* context, const NativePath* path, std::uint16_t node, const void* argument)
{
    nativeArgumentsMatch &= context == currentContext && !argument && path->size < path->capacity;
    if (visitedCount == visited.size() || path->size >= MaxDepth)
        return false;
    auto& row = visited[visitedCount++];
    std::copy_n(path->words, path->size, row.words.begin());
    row.words[path->size] = node;
    row.size = path->size + 1;
    return true;
}

void RecordPath(void*, void*) {}
void ReleaseContext(const void* context)
{
    nativeArgumentsMatch &= context == currentContext;
    ++releases;
}

class RestoreDispatchFixture
{
public:
    explicit RestoreDispatchFixture(const char* input)
    {
        std::ifstream blob(input, std::ios::binary);
        std::array<char, 0x13F> native{};
        blob.read(native.data(), native.size());
        if (!blob || blob.peek() != EOF)
            throw std::runtime_error("Unexpected restore dispatcher bytes");
        memory = static_cast<std::byte*>(VirtualAlloc(nullptr, 0x300000, MEM_RESERVE | MEM_COMMIT,
                                                      PAGE_EXECUTE_READWRITE));
        if (!memory)
            throw std::runtime_error("Cannot map native fixture");
        std::memcpy(memory + 0x2B32B0, native.data(), native.size());
        Stub(0x2B30A0, &MakeContext);
        Stub(0x2B2EB4, &RecordPath);
        Stub(0x2B2D50, &ReleaseContext);
        FlushInstructionCache(GetCurrentProcess(), memory, 0x300000);
    }

    ~RestoreDispatchFixture() { VirtualFree(memory, 0, MEM_RELEASE); }

    void Dispatch(const FalcoRestorePlan& plan)
    {
        auto words = plan.paths;
        std::array<NativePath, FalcoRestoreNodes.size()> paths{};
        for (std::size_t i = 0; i < paths.size(); ++i)
            paths[i] = {words[i].words.data(), words[i].size, words[i].size};
        NativePathList list{paths.data(), static_cast<std::uint32_t>(paths.size()),
                            static_cast<std::uint32_t>(paths.size())};
        std::array<void*, 0x138 / sizeof(void*)> vtable{};
        vtable[0x130 / sizeof(void*)] = reinterpret_cast<void*>(&RestorePathStub);
        void* table = vtable.data();
        alignas(8) std::array<std::byte, 0x270> quests{};
        Put(quests.data(), 0x68, &table);
        expectedQuests = quests.data();
        RestoreJob job{nullptr, quests.data(), &list};
        const auto next = reinterpret_cast<void (*)(RestoreJob*, void*)>(memory + 0x2B32B0);
        next(&job, nullptr);
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

State SavedState()
{
    State state;
    state.roots = {BaseQuest, ExpansionQuest};
    for (const auto& target : FalcoPhases)
    {
        Phase phase{};
        std::ranges::copy(target.address, phase.path.begin());
        phase.size = target.address.size();
        phase.hash = PhaseHash(target.address);
        phase.depot = target.depot;
        state.phases.push_back(phase);
    }
    state.handlers.assign(SavedHandlers.begin(), SavedHandlers.end());
    state.instances.assign(SavedInstances.begin(), SavedInstances.end());
    state.facts[2].push_back(SavedChoice);
    state.timings.push_back(SavedWait);
    return state;
}
} // namespace

int main(int argc, char** argv)
{
    if (argc != 2)
        return 2;
    try
    {
        const auto state = SavedState();
        const auto plan = PlanFalcoRestore(state);
        Check(plan && plan->paths.size() == 9 && plan->reyesChoice.value == 4 &&
                  plan->falcoWait.remainingSeconds == 86'388, "MS31 selects nine original paths and the exact branch and wait");
        const auto reject = [&](auto change, const char* label) {
            auto modified = state;
            change(modified);
            Check(!PlanFalcoRestore(modified), label);
        };
        reject([](State& altered) { altered.handlers.erase(altered.handlers.end() - 2); },
               "a missing Reyes listener defers the whole restore");
        reject([](State& altered) { altered.handlers.back().registration.type ^= 1; },
               "an unrecognized handler type defers restore");
        reject([](State& altered) { altered.phases.back().depot ^= 1; },
               "a different provider defers restore");
        reject([](State& altered) {
            Phase competing{};
            std::ranges::copy(FalcoPrivateQuest, competing.path.begin());
            competing.size = FalcoPrivateQuest.size();
            altered.phases.push_back(competing);
        }, "a competing quest owner defers restore");
        reject([](State& altered) {
            Phase additional{};
            std::ranges::copy(FalcoQuest, additional.path.begin());
            additional.path[FalcoQuest.size()] = 6;
            additional.size = FalcoQuest.size() + 1;
            additional.hash = PhaseHash(additional.Path());
            altered.phases.push_back(additional);
        }, "another live branch in the same quest defers restore");
        reject([](State& altered) { altered.notifications.push_back(altered.handlers.front().slot); },
               "a pending callback on the affected ancestor defers restore");
        reject([](State& altered) { altered.timings.front().serial ^= 1; }, "a changed timer identity defers restore");
        reject([](State& altered) { altered.timings.front().remainingSeconds = 0; }, "a due timer defers restore");
        reject([](State& altered) { altered.timings.front().ageMilliseconds = 251; },
               "a stale scheduler sample defers restore");
        reject([](State& altered) { altered.facts[2].front().value = 2; }, "a changed original choice defers restore");
        reject([](State& altered) { altered.handlers.push_back(altered.handlers.back()); },
               "duplicate native registrations defer restore");
        reject([](State& altered) { altered.facts[1].push_back({FalcoJoinKey, 1}); },
               "a signaled parent join defers this stage");

        if (!plan)
            return 1;
        RestoreDispatchFixture native(argv[1]);
        SaveAdmission admission;
        std::array<std::uint8_t, 0x309> session{};
        session[0x308] = 0x10;
        Check(!admission.TryHandoff(session.data()), "a native save defers the restoration window");
        session[0x308] = 0;
        const auto save = [](void*, void*) { ++saves; };
        {
            const auto permit = admission.TryHandoff(session.data());
            if (!permit)
                return 1;
            native.Dispatch(*plan);
            admission.Poll(save, session.data(), nullptr);
            Check(saves == 0, "save dispatch stays deferred across native context dispatch");
        }
        admission.Poll(save, session.data(), nullptr);
        Check(saves == 1, "save dispatch resumes after the window");
        Check(nativeArgumentsMatch && contexts == 9 && releases == 9 && visitedCount == 9,
              "the native dispatcher opens and releases one mode 2 context per requested path");
        bool same = true;
        for (std::size_t i = 0; i < plan->paths.size(); ++i)
            same &= visited[i].words == plan->paths[i].words && visited[i].size == plan->paths[i].size;
        Check(same, "the engine visits exactly the prepared ancestors and listeners with original node addresses");
        return failures != 0;
    }
    catch (const std::exception& error)
    {
        std::fprintf(stderr, "%s\n", error.what());
        return 2;
    }
}
