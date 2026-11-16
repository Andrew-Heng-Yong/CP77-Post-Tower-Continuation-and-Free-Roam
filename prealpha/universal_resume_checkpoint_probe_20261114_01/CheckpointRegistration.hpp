#pragma once

#include <RED4ext/RED4ext.hpp>

#include <array>
#include <cstdint>
#include <span>

namespace ptfr::resume
{
inline constexpr auto ReadCheckpointName = "PTFR.HistorySnapshotHS1.ReadExecutionCheckpoint";
inline constexpr auto DecodeCheckpointName = "PTFR.HistorySnapshotHS1.DecodeExecutionCheckpoint";

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

inline NativeType* CheckedHandle(NativeType* type, RED4ext::CName target)
{
    if (!type || type->GetType() != NativeKind::Handle ||
        type->GetSize() != sizeof(RED4ext::Handle<RED4ext::IScriptable>))
        return nullptr;
    const auto* inner = static_cast<const RED4ext::CRTTIHandleType*>(type)->GetInnerType();
    return inner && inner->GetName() == target ? type : nullptr;
}

inline NativeType* CheckedWordArray(NativeType* type, const NativeType* word)
{
    if (!word || !type || type->GetType() != NativeKind::Array ||
        type->GetSize() != sizeof(RED4ext::DynArray<std::uint64_t>))
        return nullptr;
    return static_cast<const RED4ext::CRTTIBaseArrayType*>(type)->GetInnerType() == word ? type : nullptr;
}

template<class Registry, class InternName>
CheckpointTypes ResolveCheckpointTypes(Registry& registry, InternName internName)
{
    // A miss in GetType's index can reach the engine's compound-type factory.
    // That path parses the interned spelling, so passing only a CName hash
    // cannot resolve a compound type whose spelling is absent from the pool.
    const auto find = [&](const char* name) { return registry.GetType(internName(name)); };
    const auto word = CheckedScalar(find("Uint64"), "Uint64", sizeof(std::uint64_t));
    return {
        CheckedHandle(find("handle:questQuestsSystem"), "questQuestsSystem"),
        CheckedHandle(find("handle:gameDelaySystem"), "gameDelaySystem"),
        CheckedHandle(find("handle:gameTimeSystem"), "gameTimeSystem"),
        CheckedScalar(find("Int32"), "Int32", sizeof(std::int32_t)),
        CheckedWordArray(find("array:Uint64"), word),
        CheckedScalar(find("String"), "String", sizeof(RED4ext::CString))
    };
}

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
