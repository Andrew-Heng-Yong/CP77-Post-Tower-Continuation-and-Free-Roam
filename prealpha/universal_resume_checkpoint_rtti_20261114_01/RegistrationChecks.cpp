#include "CheckpointRegistration.hpp"

#include <array>
#include <cstddef>
#include <cstring>
#include <iostream>
#include <string_view>
#include <vector>

namespace
{
using namespace ptfr::resume;

// These synthetic records supply the reflected slots that the production
// code reads. The fixture uses the SDK layout without loading RED4ext or the game.
template<class T>
struct Record
{
    alignas(T) std::array<std::byte, sizeof(T)> bytes{};
    T& Get() { return *reinterpret_cast<T*>(bytes.data()); }
};

template<class T, std::size_t Count>
void SetArray(RED4ext::DynArray<T>& array, std::array<T, Count>& entries, std::uint32_t count)
{
    struct Header
    {
        T* data;
        std::uint32_t capacity;
        std::uint32_t size;
    };
    static_assert(sizeof(Header) == sizeof(array));
    const Header header{entries.data(), static_cast<std::uint32_t>(Count), count};
    std::memcpy(static_cast<void*>(&array), &header, sizeof(header));
}

struct Descriptor
{
    const std::uintptr_t* vtable;
    RED4ext::CName name;
    std::uint32_t bytes;
    NativeKind kind;
    Descriptor* inner;

    // The MSVC member-call ABI puts this in RCX and the CName result
    // address in RDX for the SDK's GetName virtual.
    static RED4ext::CName* Name(const Descriptor* type, RED4ext::CName* result)
    {
        *result = type->name;
        return result;
    }
    static std::uint32_t Size(const Descriptor* type) { return type->bytes; }
    static NativeKind Kind(const Descriptor* type) { return type->kind; }
    static NativeType* Inner(const Descriptor* type) { return AsType(type->inner); }

    static NativeType* AsType(Descriptor* descriptor) { return reinterpret_cast<NativeType*>(descriptor); }
    static const std::array<std::uintptr_t, 25>& Table()
    {
        static const auto methods = [] {
            std::array<std::uintptr_t, 25> t{};
            t[0x08 / 8] = reinterpret_cast<std::uintptr_t>(&Name);
            t[0x10 / 8] = reinterpret_cast<std::uintptr_t>(&Size);
            t[0x20 / 8] = reinterpret_cast<std::uintptr_t>(&Kind);
            t[0xC0 / 8] = reinterpret_cast<std::uintptr_t>(&Inner);
            return t;
        }();
        return methods;
    }

    Descriptor(const char* label, std::uint32_t width, NativeKind category, Descriptor* element = nullptr)
        : vtable(Table().data()), name(label), bytes(width), kind(category), inner(element) {}

    NativeType* Type() { return AsType(this); }
};

struct Registry
{
    Descriptor questsClass{"questQuestsSystem", 0x300, NativeKind::Class};
    Descriptor delayClass{"gameDelaySystem", 0x530C0, NativeKind::Class};
    Descriptor clockClass{"gameTimeSystem", 0x6EBC0, NativeKind::Class};
    Descriptor quests{"unindexed strong quest handle", 16, NativeKind::Handle, &questsClass};
    Descriptor delay{"unindexed strong delay handle", 16, NativeKind::Handle, &delayClass};
    Descriptor clock{"unindexed strong clock handle", 16, NativeKind::Handle, &clockClass};
    Descriptor integer{"Int32", 4, NativeKind::Fundamental};
    Descriptor word{"Uint64", 8, NativeKind::Fundamental};
    Descriptor words{"unindexed dynamic word array", 16, NativeKind::Array, &word};
    Descriptor text{"String", 0x20, NativeKind::Simple};
    std::array<Record<RED4ext::CClassStaticFunction>, 4> getters;
    std::array<Record<Property>, 4> getterResults;
    std::array<RED4ext::CClassStaticFunction*, 4> getterList{};
    Record<Property> stockWords;
    Record<RED4ext::CClass> game;
    Record<RED4ext::CClass> covers;
    std::vector<RED4ext::CName> typeRequests;
    bool haveGame = true;
    bool haveCovers = true;

    Registry()
    {
        SetGetter(0, "GetQuestsSystem", quests.Type());
        SetGetter(1, "GetDelaySystem", delay.Type());
        SetGetter(2, "GetTimeSystem", clock.Type());
        SetArray(game.Get().staticFuncs, getterList, 3);
        stockWords.Get().name = "selectedCovers";
        stockWords.Get().type = words.Type();
    }

    void SetGetter(std::size_t index, RED4ext::CName name, NativeType* type)
    {
        auto& getter = getters[index].Get();
        getter.shortName = name;
        getter.flags.isNative = true;
        getterResults[index].Get().type = type;
        getter.returnType = &getterResults[index].Get();
        getterList[index] = &getter;
    }

    NativeType* GetType(RED4ext::CName name)
    {
        typeRequests.push_back(name);
        for (auto* type : {&integer, &word, &text})
            if (name == type->name)
                return type->Type();
        return nullptr;
    }

    RED4ext::CClass* GetClass(RED4ext::CName name)
    {
        if (name == RED4ext::CName{"ScriptGameInstance"} && haveGame)
            return &game.Get();
        return name == RED4ext::CName{"MultiSelectCovers"} && haveCovers ? &covers.Get() : nullptr;
    }

    CheckpointTypes Resolve()
    {
        return ResolveCheckpointTypes(*this, [this](RED4ext::CClass& owner, RED4ext::CName name) -> Property* {
            if (&owner == &covers.Get() && name == stockWords.Get().name)
                return &stockWords.Get();
            return nullptr;
        });
    }
};

struct Check
{
    unsigned failures = 0;
    void Expect(bool pass, const char* what)
    {
        std::cout << (pass ? "PASS " : "FAIL ") << what << '\n';
        if (!pass)
            ++failures;
    }
};

struct BoundFunction
{
    Record<RED4ext::CGlobalFunction> function;
    std::array<Property*, 7> params{};
    std::array<Record<Property>, 8> properties;
    std::size_t allocated = 0;
    std::string_view failOn;

    BoundFunction()
    {
        SetArray(function.Get().params, params, 0);
        function.Get().unkAC = 8;
    }

    const char* Describe(std::span<const Parameter> arguments, NativeType* result)
    {
        return DescribeCheckpointFunction(function.Get(), arguments, result,
            [this](NativeType* type, const char* name, RED4ext::CClass* parent, std::uint32_t offset,
                   const char*, Property::Flags flags) -> Property* {
                if (failOn == name || allocated == properties.size())
                    return nullptr;
                auto& prop = properties[allocated++].Get();
                prop.type = type;
                prop.name = name;
                prop.parent = parent;
                prop.valueOffset = offset;
                prop.flags = flags;
                return &prop;
            });
    }
};
} // namespace

int main()
{
    std::cout << std::unitbuf;
    Check check;
    Registry registry;
    check.Expect(!registry.GetType("handle:questQuestsSystem") && !registry.GetType("handle:gameDelaySystem") &&
                 !registry.GetType("handle:gameTimeSystem") && !registry.GetType("array:Uint64"),
                 "registry hides every composed lookup used by the broken build");
    registry.typeRequests.clear();
    const auto types = registry.Resolve();
    check.Expect(types.quests == registry.quests.Type(), "capture reuses the stock GameInstance quest handle");
    check.Expect(types.delay == registry.delay.Type(), "capture reuses the stock GameInstance delay handle");
    check.Expect(types.clock == registry.clock.Type(), "capture reuses the stock GameInstance time handle");
    check.Expect(types.words == registry.words.Type(), "both natives use the stock dynamic Uint64 array");
    check.Expect(registry.typeRequests == std::vector<RED4ext::CName>{"Uint64", "Int32", "String"},
                 "the resolver only uses simple type names in the registry");

    BoundFunction reader, decoder;
    check.Expect(!reader.Describe(types.CaptureParameters(), types.words), "all seven capture parameters and return bind");
    check.Expect(!decoder.Describe(types.DecodeParameters(), types.text), "decode data and return bind independently");
    auto& read = reader.function.Get();
    auto& decode = decoder.function.Get();
    const bool shape = read.params.Size() == 7 && decode.params.Size() == 1 && read.returnType && decode.returnType;
    check.Expect(shape, "both native arities match REDscript");
    check.Expect(read.flags.isNative && read.flags.isStatic && read.flags.isPublic &&
                 decode.flags.isNative && decode.flags.isStatic && decode.flags.isPublic,
                 "both native global definitions carry the expected flags");
    check.Expect(shape && read.params[6]->type == read.returnType->type && read.returnType->type == decode.params[0]->type,
                 "capture input, return and decode input share the same array descriptor");
    check.Expect(shape && read.params[0]->name == RED4ext::CName{"quests"} && read.params[0]->valueOffset == 8 &&
                 !read.params[0]->flags.isReturn && read.returnType->flags.isReturn && read.returnType->valueOffset == 0,
                 "descriptor properties retain SDK parameter and result layout");

    registry.delay.kind = NativeKind::WeakHandle;
    check.Expect(!registry.Resolve().delay, "wrong handle kind fails the specific delay binding");
    registry.delay.kind = NativeKind::Handle;
    registry.delay.inner = &registry.clockClass;
    check.Expect(!registry.Resolve().delay, "wrong handle class fails the specific delay binding");
    registry.delay.inner = &registry.delayClass;
    registry.delay.bytes = 8;
    check.Expect(!registry.Resolve().delay, "wrong handle width fails the specific delay binding");
    registry.delay.bytes = 16;
    registry.words.inner = &registry.integer;
    check.Expect(!registry.Resolve().words, "wrong array element type fails the shared array binding");
    registry.words.inner = &registry.word;
    registry.words.kind = NativeKind::StaticArray;
    check.Expect(!registry.Resolve().words, "fixed array fails the dynamic array binding");
    registry.words.kind = NativeKind::Array;
    registry.haveCovers = false;
    check.Expect(!registry.Resolve().words, "absent stock array property is reported as unavailable");
    registry.haveCovers = true;
    registry.haveGame = false;
    const auto missing = registry.Resolve();
    check.Expect(!missing.quests && !missing.delay && !missing.clock && missing.words,
                 "missing GameInstance class is distinct from the array binding");
    registry.haveGame = true;
    Descriptor competing{"other quest handle", 16, NativeKind::Handle, &registry.questsClass};
    registry.SetGetter(3, "GetQuestsSystem", competing.Type());
    SetArray(registry.game.Get().staticFuncs, registry.getterList, 4);
    check.Expect(!registry.Resolve().quests, "two distinct matching handle descriptors are ambiguous");
    registry.SetGetter(3, "GetQuestsSystem", registry.quests.Type());
    check.Expect(registry.Resolve().quests == registry.quests.Type(), "repeated identical getter descriptors bind consistently");

    BoundFunction failedParam, failedReturn;
    failedParam.failOn = "presentation";
    failedReturn.failOn = "__return";
    const auto* rejectedParam = failedParam.Describe(types.CaptureParameters(), types.words);
    const auto* rejectedReturn = failedReturn.Describe(types.DecodeParameters(), types.text);
    check.Expect(rejectedParam && std::string_view{rejectedParam} == "presentation",
                 "allocation failure identifies the exact capture argument");
    check.Expect(rejectedReturn && std::string_view{rejectedReturn} == "__return",
                 "allocation failure identifies the decode result");
    return check.failures ? 1 : 0;
}
