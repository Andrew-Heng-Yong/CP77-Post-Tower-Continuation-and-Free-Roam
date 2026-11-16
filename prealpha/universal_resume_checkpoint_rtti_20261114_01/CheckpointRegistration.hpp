#pragma once

#include <RED4ext/RED4ext.hpp>

#include <array>
#include <cstdint>
#include <span>

namespace ptfr::resume
{
using NativeType = RED4ext::rtti::IType;
using NativeKind = RED4ext::rtti::ERTTIType;
using Property = RED4ext::CProperty;

struct Parameter
{
    const char* name;
    NativeType* type;
};

struct CheckpointTypes
{
    NativeType* quests;
    NativeType* delay;
    NativeType* clock;
    NativeType* int32;
    NativeType* words;
    NativeType* text;

    auto CaptureParameters() const
    {
        return std::array<Parameter, 7>{
            {{"quests", quests}, {"delay", delay}, {"clock", clock}, {"ticket", int32},
             {"route", int32}, {"historyRevision", int32}, {"presentation", words}}
        };
    }

    auto DecodeParameters() const
    {
        return std::array<Parameter, 1>{{{"data", words}}};
    }
};

inline NativeType* CheckedScalar(NativeType* type, RED4ext::CName name, std::size_t bytes)
{
    return type && type->GetName() == name && type->GetSize() == bytes ? type : nullptr;
}

inline NativeType* GetterResult(const RED4ext::CClass* owner, RED4ext::CName method, RED4ext::CName target)
{
    if (!owner)
        return nullptr;

    NativeType* result = nullptr;
    for (const auto* function : owner->staticFuncs)
    {
        if (!function || function->shortName != method || !function->flags.isNative ||
            !function->returnType || !function->returnType->type)
            continue;
        auto* type = function->returnType->type;
        if (type->GetType() != NativeKind::Handle || type->GetSize() != sizeof(RED4ext::Handle<RED4ext::IScriptable>))
            continue;
        const auto* inner = static_cast<const RED4ext::CRTTIHandleType*>(type)->GetInnerType();
        if (!inner || inner->GetName() != target)
            continue;
        if (result && result != type)
            return nullptr;
        result = type;
    }
    return result;
}

inline NativeType* WordArray(const Property* property, const NativeType* word)
{
    const auto type = property ? property->type : nullptr;
    if (!word || !type || type->GetType() != NativeKind::Array ||
        type->GetSize() != sizeof(RED4ext::DynArray<std::uint64_t>))
        return nullptr;
    return static_cast<const RED4ext::CRTTIBaseArrayType*>(type)->GetInnerType() == word ? type : nullptr;
}

// A stock getter already owns the strong-handle descriptor its REDscript
// callers use. The stock cover property supplies the exact dynamic Uint64
// array descriptor. Neither lookup depends on composed RTTI names.
template<class Registry, class FindProperty>
CheckpointTypes ResolveCheckpointTypes(Registry& registry, FindProperty findProperty)
{
    const auto* game = registry.GetClass("ScriptGameInstance");
    auto* cover = registry.GetClass("MultiSelectCovers");
    const auto* stockWords = cover ? findProperty(*cover, RED4ext::CName{"selectedCovers"}) : nullptr;
    const auto word = CheckedScalar(registry.GetType("Uint64"), "Uint64", sizeof(std::uint64_t));
    return {
        GetterResult(game, "GetQuestsSystem", "questQuestsSystem"),
        GetterResult(game, "GetDelaySystem", "gameDelaySystem"),
        GetterResult(game, "GetTimeSystem", "gameTimeSystem"),
        CheckedScalar(registry.GetType("Int32"), "Int32", sizeof(std::int32_t)),
        WordArray(stockWords, word),
        CheckedScalar(registry.GetType("String"), "String", sizeof(RED4ext::CString))
    };
}

// Match the SDK's AddParam/SetReturnType property flags and offsets, using
// the descriptors resolved from stock instead of repeating a name lookup.
template<class AllocateProperty>
const char* DescribeCheckpointFunction(RED4ext::CBaseFunction& function, std::span<const Parameter> params,
                                       NativeType* result, AllocateProperty allocate)
{
    for (const auto& param : params)
    {
        if (!param.type)
            return param.name;
        auto* property = allocate(param.type, param.name, nullptr, function.unkAC, nullptr, Property::Flags{});
        if (!property)
            return param.name;
        function.params.PushBack(property);
    }

    Property::Flags flags{};
    flags.isReturn = true;
    function.returnType = result ? allocate(result, "__return", nullptr, 0, nullptr, flags) : nullptr;
    if (!function.returnType)
        return "__return";
    function.flags.isNative = true;
    function.flags.isStatic = true;
    function.flags.isPublic = true;
    return nullptr;
}
} // namespace ptfr::resume
