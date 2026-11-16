constexpr auto GameEngine = 0x30C3790;
SaveAdmission saveAdmission;
SaveAdmission::Dispatcher dispatchSavesOriginal;

void DispatchSaves(void* engine, void* jobs)
{
    saveAdmission.Poll(dispatchSavesOriginal, engine, jobs);
}

// The caller must hold the permit until the live quest and timers are coherent.
// Acquisition is on the running game, before taking any handoff locks or editing.
[[nodiscard]] SaveGuard::HandoffPermit TryBeginNativeHandoff()
{
    if (!enabled.load())
        return {};
    const auto* engine = RED4ext::CGameEngine::Get();
    if (!Is(engine, GameEngine))
        return {};
    return saveAdmission.TryHandoff(engine);
}
