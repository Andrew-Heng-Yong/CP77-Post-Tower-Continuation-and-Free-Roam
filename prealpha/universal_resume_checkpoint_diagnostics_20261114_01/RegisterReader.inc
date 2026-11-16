void RegisterCheckpointFunctions()
{
    if (!hooksReady.load() || reader || decoder)
        return;
    auto* rtti = RED4ext::CRTTISystem::Get();
    if (!rtti || rtti->GetFunction(ReadCheckpointName) || rtti->GetFunction(DecodeCheckpointName))
    {
        sdk->logger->Warn(plugin, "PTFR checkpoint runtime registry unavailable or name already in use");
        return;
    }

    const auto types = ResolveCheckpointTypes(*rtti, [](const char* name) {
        return RED4ext::CNamePool::Add(name);
    });
    const Parameter required[]{
        {"handle:questQuestsSystem", types.quests}, {"handle:gameDelaySystem", types.delay},
        {"handle:gameTimeSystem", types.clock}, {"Int32", types.int32},
        {"array:Uint64", types.words}, {"String", types.text}
    };
    bool available = true;
    for (const auto& binding : required)
    {
        if (!binding.type)
        {
            sdk->logger->WarnF(plugin, "PTFR checkpoint runtime type unavailable or invalid: %s", binding.name);
            available = false;
        }
    }
    if (!available)
        return;

    auto* capture = RED4ext::CGlobalFunction::Create(ReadCheckpointName, ReadCheckpointName, &ReadCheckpoint);
    auto* decode = RED4ext::CGlobalFunction::Create(DecodeCheckpointName, DecodeCheckpointName, &DecodeCheckpoint);
    if (!capture || !decode)
    {
        sdk->logger->Warn(plugin, "PTFR checkpoint runtime function allocation failed");
        return;
    }

    const auto readParams = types.CaptureParameters();
    const auto decodeParams = types.DecodeParameters();
    const auto* readFailure = DescribeCheckpointFunction(*capture, readParams, types.words, &Property::Create);
    const auto* decodeFailure = DescribeCheckpointFunction(*decode, decodeParams, types.text, &Property::Create);
    if (readFailure || decodeFailure)
    {
        if (readFailure)
            sdk->logger->WarnF(plugin, "PTFR checkpoint capture signature rejected at %s", readFailure);
        if (decodeFailure)
            sdk->logger->WarnF(plugin, "PTFR checkpoint decoder signature rejected at %s", decodeFailure);
        return;
    }

    rtti->RegisterFunction(capture);
    rtti->RegisterFunction(decode);
    const bool capturePublished = rtti->GetFunction(ReadCheckpointName) == capture;
    const bool decodePublished = rtti->GetFunction(DecodeCheckpointName) == decode;
    if (!capturePublished || !decodePublished)
    {
        if (capturePublished)
            rtti->UnregisterFunction(capture);
        if (decodePublished)
            rtti->UnregisterFunction(decode);
        sdk->logger->Warn(plugin, "PTFR checkpoint runtime registration did not read back both functions");
        return;
    }
    reader = capture;
    decoder = decode;
    enabled.store(true);
    sdk->logger->Info(plugin, "PTFR execution checkpoint runtime ready: capture and decode registered");
}

bool OnRunning(RED4ext::CGameApplication*)
{
    try
    {
        RegisterCheckpointFunctions();
    }
    catch (const std::exception& error)
    {
        sdk->logger->WarnF(plugin, "PTFR checkpoint runtime registration failed: %s", error.what());
    }
    return true;
}
