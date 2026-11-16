#define WIN32_LEAN_AND_MEAN
#include <Windows.h>
#include <RED4ext/RED4ext.hpp>

namespace
{
const RED4ext::v1::Sdk* sdk{};
RED4ext::v1::PluginHandle plugin{};

void Noop(RED4ext::IScriptable*, RED4ext::CStackFrame*, RED4ext::CString*, std::int64_t) {}

void Probe()
{
    auto* rtti = RED4ext::CRTTISystem::Get();
    constexpr const char* types[] = {
        "handle:questQuestsSystem", "handle:gameDelaySystem", "handle:gameTimeSystem",
        "Int32", "Uint64", "array:Uint64", "String"
    };
    for (const char* name : types)
        sdk->logger->InfoF(plugin, "PTFR RTTI type %s: %s", name,
                          rtti->GetType(name) ? "present" : "missing");

    auto* function = RED4ext::CGlobalFunction::Create("PTFR.CheckpointRTTIProbe", "PTFR.CheckpointRTTIProbe", &Noop);
    if (!function)
    {
        sdk->logger->Error(plugin, "PTFR RTTI function allocation failed");
        return;
    }
    for (const char* name : types)
        sdk->logger->InfoF(plugin, "PTFR RTTI AddParam %s: %s", name,
                          function->AddParam(name, name) ? "accepted" : "rejected");
    sdk->logger->InfoF(plugin, "PTFR RTTI SetReturnType array:Uint64: %s",
                      function->SetReturnType("array:Uint64") ? "accepted" : "rejected");
    // This diagnostic function is never registered or called by REDscript.
}
}

RED4EXT_C_EXPORT bool RED4EXT_CALL Main(RED4ext::v1::PluginHandle handle, RED4ext::v1::EMainReason reason,
                                        const RED4ext::v1::Sdk* api)
{
    if (reason != RED4ext::v1::EMainReason::Load || !api || !api->logger)
        return true;
    sdk = api;
    plugin = handle;
    auto* rtti = RED4ext::CRTTISystem::Get();
    if (!rtti)
        return false;
    rtti->AddPostRegisterCallback(&Probe);
    return true;
}

RED4EXT_C_EXPORT void RED4EXT_CALL Query(RED4ext::v1::PluginInfo* info)
{
    info->name = L"PTFR Checkpoint RTTI Probe";
    info->author = L"Post Tower Continuation";
    info->version = RED4EXT_V1_SEMVER(0, 1, 0);
    info->runtime = RED4EXT_V1_RUNTIME_VERSION_2_50;
    info->sdk = RED4EXT_V1_SDK_VERSION_CURRENT;
}

RED4EXT_C_EXPORT std::uint32_t RED4EXT_CALL Supports()
{
    return RED4EXT_API_VERSION_1;
}
