void RegisterReader()
{
    constexpr auto readName = "PTFR.HistorySnapshotHS1.ReadExecutionCheckpoint";
    constexpr auto decodeName = "PTFR.HistorySnapshotHS1.DecodeExecutionCheckpoint";
    auto* rtti = RED4ext::CRTTISystem::Get();
    if (!rtti || reader || decoder)
        return;

    const auto types = ResolveCheckpointTypes(*rtti, [](RED4ext::CClass& owner, RED4ext::CName name) {
        return owner.GetProperty(name);
    });
    struct Binding
    {
        const NativeType* type;
        const char* site;
        const char* source;
    };
    const Binding required[]{
        {types.quests, "ReadExecutionCheckpoint.quests", "ScriptGameInstance.GetQuestsSystem strong handle"},
        {types.delay, "ReadExecutionCheckpoint.delay", "ScriptGameInstance.GetDelaySystem strong handle"},
        {types.clock, "ReadExecutionCheckpoint.clock", "ScriptGameInstance.GetTimeSystem strong handle"},
        {types.int32, "ReadExecutionCheckpoint ticket/route/historyRevision", "Int32"},
        {types.words, "capture presentation/result and decode data", "MultiSelectCovers.selectedCovers Uint64 array"},
        {types.text, "DecodeExecutionCheckpoint result", "String"},
    };
    bool valid = true;
    for (const auto& binding : required)
    {
        if (!binding.type)
        {
            sdk->logger->ErrorF(plugin, "PTFR checkpoint type unavailable for %s (%s)", binding.site, binding.source);
            valid = false;
        }
    }
    if (!valid)
        return;

    auto* capture = RED4ext::CGlobalFunction::Create(readName, readName, &ReadCheckpoint);
    auto* decode = RED4ext::CGlobalFunction::Create(decodeName, decodeName, &DecodeCheckpoint);
    if (!capture || !decode)
    {
        sdk->logger->ErrorF(plugin, "PTFR checkpoint function allocation failed for %s",
                            capture ? decodeName : readName);
        return;
    }

    const auto readParams = types.CaptureParameters();
    const auto decodeParams = types.DecodeParameters();
    const auto* readFailure = DescribeCheckpointFunction(*capture, readParams, types.words, &Property::Create);
    const auto* decodeFailure = DescribeCheckpointFunction(*decode, decodeParams, types.text, &Property::Create);
    if (readFailure)
        sdk->logger->ErrorF(plugin, "PTFR checkpoint registration failed at %s.%s", readName, readFailure);
    if (decodeFailure)
        sdk->logger->ErrorF(plugin, "PTFR checkpoint registration failed at %s.%s", decodeName, decodeFailure);
    if (readFailure || decodeFailure)
        return;

    rtti->RegisterFunction(capture);
    rtti->RegisterFunction(decode);
    reader = capture;
    decoder = decode;
    if (rtti->GetFunction(readName) != reader || rtti->GetFunction(decodeName) != decoder)
    {
        sdk->logger->Error(plugin, "PTFR checkpoint native registration did not read back both functions");
        return;
    }
    enabled.store(hooksReady.load());
    sdk->logger->Info(plugin, "PTFR execution checkpoint registered both native functions");
}
