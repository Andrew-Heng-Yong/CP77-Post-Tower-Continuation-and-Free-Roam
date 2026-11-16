#include "CheckpointRegistration.hpp"

#include <algorithm>
#include <cstring>
#include <iostream>
#include <string_view>
#include <vector>

namespace
{
using namespace ptfr::resume;

// Only the virtual slots used by the resolver are present in this fixture.
struct Descriptor
{
    const std::uintptr_t* vtable = Table().data();
    RED4ext::CName name;
    std::uint32_t bytes;
    NativeKind kind;
    Descriptor* inner{};

    NativeType* Type() { return reinterpret_cast<NativeType*>(this); }

    static RED4ext::CName* Name(const Descriptor* value, RED4ext::CName* result)
    {
        *result = value->name;
        return result;
    }

    static std::uint32_t Size(const Descriptor* value) { return value->bytes; }
    static NativeKind Kind(const Descriptor* value) { return value->kind; }
    static NativeType* Inner(const Descriptor* value) { return value->inner ? value->inner->Type() : nullptr; }

    static const std::array<std::uintptr_t, 25>& Table()
    {
        static const auto table = [] {
            std::array<std::uintptr_t, 25> slots{};
            slots[0x08 / 8] = reinterpret_cast<std::uintptr_t>(&Name);
            slots[0x10 / 8] = reinterpret_cast<std::uintptr_t>(&Size);
            slots[0x20 / 8] = reinterpret_cast<std::uintptr_t>(&Kind);
            slots[0xC0 / 8] = reinterpret_cast<std::uintptr_t>(&Inner);
            return slots;
        }();
        return table;
    }
};

struct Registry
{
    Descriptor questClass{Descriptor::Table().data(), "questQuestsSystem", 0x300, NativeKind::Class};
    Descriptor delayClass{Descriptor::Table().data(), "gameDelaySystem", 0x530C0, NativeKind::Class};
    Descriptor clockClass{Descriptor::Table().data(), "gameTimeSystem", 0x6EBC0, NativeKind::Class};
    Descriptor quests{Descriptor::Table().data(), "handle:questQuestsSystem", 16, NativeKind::Handle, &questClass};
    Descriptor delay{Descriptor::Table().data(), "handle:gameDelaySystem", 16, NativeKind::Handle, &delayClass};
    Descriptor clock{Descriptor::Table().data(), "handle:gameTimeSystem", 16, NativeKind::Handle, &clockClass};
    Descriptor integer{Descriptor::Table().data(), "Int32", 4, NativeKind::Fundamental};
    Descriptor word{Descriptor::Table().data(), "Uint64", 8, NativeKind::Fundamental};
    Descriptor words{Descriptor::Table().data(), "array:Uint64", 16, NativeKind::Array, &word};
    Descriptor text{Descriptor::Table().data(), "String", 0x20, NativeKind::Simple};
    std::vector<RED4ext::CName> interned;
    RED4ext::CName unavailable;

    NativeType* GetType(RED4ext::CName name)
    {
        if (name == unavailable)
            return nullptr;
        for (auto* scalar : {&integer, &word, &text})
            if (scalar->name == name)
                return scalar->Type();
        // Model a cache miss whose compound factory needs the name's spelling.
        if (std::find(interned.begin(), interned.end(), name) == interned.end())
            return nullptr;
        for (auto* compound : {&quests, &delay, &clock, &words})
            if (compound->name == name)
                return compound->Type();
        return nullptr;
    }

    CheckpointTypes Resolve()
    {
        return ResolveCheckpointTypes(*this, [this](const char* spelling) {
            const RED4ext::CName name{spelling};
            interned.push_back(name);
            return name;
        });
    }
};

template<class T>
struct Record
{
    alignas(T) std::array<std::byte, sizeof(T)> bytes{};
    T& Get() { return *reinterpret_cast<T*>(bytes.data()); }
};

struct Function
{
    Record<RED4ext::CGlobalFunction> storage;
    std::array<Property*, 7> params{};
    std::array<Record<Property>, 8> properties;
    std::size_t used{};

    Function()
    {
        struct ArrayHeader
        {
            Property** data;
            std::uint32_t capacity;
            std::uint32_t size;
        };
        static_assert(sizeof(ArrayHeader) == sizeof(storage.Get().params));
        const ArrayHeader header{params.data(), static_cast<std::uint32_t>(params.size()), 0};
        std::memcpy(static_cast<void*>(&storage.Get().params), &header, sizeof(header));
        storage.Get().unkAC = 8;
    }

    const char* Describe(std::span<const Parameter> arguments, NativeType* result)
    {
        return DescribeCheckpointFunction(storage.Get(), arguments, result,
            [this](NativeType* type, const char* name, RED4ext::CClass* parent, std::uint32_t offset,
                   const char*, Property::Flags flags) {
                auto& prop = properties.at(used++).Get();
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
    unsigned failures = 0;
    const auto check = [&](bool pass, const char* description) {
        std::cout << (pass ? "PASS " : "FAIL ") << description << '\n';
        if (!pass)
            ++failures;
    };
    Registry registry;
    const auto bare = ResolveCheckpointTypes(registry, [](const char* spelling) { return RED4ext::CName{spelling}; });
    check(!bare.quests && !bare.delay && !bare.clock && !bare.words && bare.int32 && bare.text,
          "a hash-only lookup misses all four unindexed compound types");

    const auto types = registry.Resolve();
    check(types.quests == registry.quests.Type() && types.delay == registry.delay.Type() &&
          types.clock == registry.clock.Type(), "interned names resolve all three strong handles");
    check(types.words == registry.words.Type() && types.int32 == registry.integer.Type() &&
          types.text == registry.text.Type(), "the interned dynamic array resolves with both scalar types");
    check(registry.interned == std::vector<RED4ext::CName>{"Uint64", "handle:questQuestsSystem", "handle:gameDelaySystem",
          "handle:gameTimeSystem", "Int32", "array:Uint64", "String"}, "every lookup interns the complete spelling");

    Function capture, decode;
    check(!capture.Describe(types.CaptureParameters(), types.words), "the capture signature binds");
    check(!decode.Describe(types.DecodeParameters(), types.text), "the decoder signature binds");
    const auto& reader = capture.storage.Get();
    const auto& decoder = decode.storage.Get();
    const bool shape = reader.params.Size() == 7 && decoder.params.Size() == 1 && reader.returnType && decoder.returnType;
    check(shape && reader.params[0]->type == types.quests && reader.params[1]->type == types.delay &&
          reader.params[2]->type == types.clock && reader.params[3]->type == types.int32 &&
          reader.params[4]->type == types.int32 && reader.params[5]->type == types.int32,
          "the native argument order matches the script bridge");
    check(shape && reader.params[6]->type == types.words && reader.returnType->type == types.words &&
          decoder.params[0]->type == types.words && decoder.returnType->type == types.text,
          "capture and decode share the unchanged packed word type");
    check(shape && reader.flags.isNative && reader.flags.isStatic && reader.flags.isPublic &&
          decoder.flags.isNative && decoder.flags.isStatic && decoder.flags.isPublic &&
          reader.returnType->flags.isReturn && decoder.returnType->flags.isReturn,
          "both native globals have the flag and return layout for reflective calls");

    registry.delay.kind = NativeKind::WeakHandle;
    check(!registry.Resolve().delay, "weak handles are rejected");
    registry.delay.kind = NativeKind::Handle;
    registry.delay.inner = &registry.clockClass;
    check(!registry.Resolve().delay, "the wrong inner class is rejected");
    registry.delay.inner = &registry.delayClass;
    registry.delay.bytes = 8;
    check(!registry.Resolve().delay, "the wrong strong-handle width is rejected");
    registry.delay.bytes = 16;
    registry.words.kind = NativeKind::StaticArray;
    check(!registry.Resolve().words, "a fixed array is rejected");
    registry.words.kind = NativeKind::Array;
    registry.words.inner = &registry.integer;
    check(!registry.Resolve().words, "an array with the wrong element type is rejected");
    registry.words.inner = &registry.word;
    registry.unavailable = "array:Uint64";
    const auto missing = registry.Resolve();
    Function unresolved;
    const auto* failure = unresolved.Describe(missing.DecodeParameters(), missing.text);
    check(!missing.words && failure && std::string_view(failure) == "data" && !unresolved.storage.Get().returnType,
          "an unavailable runtime type cannot produce a callable decoder");
    return failures ? 1 : 0;
}
