constexpr auto SaveSessionVtable = 0x30C3790;
SaveAdmission saveAdmission;
SaveAdmission::Dispatcher dispatchSavesOriginal;

// Use the live session supplied by the dispatcher. The caller must retain its
// lifetime and hold the permit until the quest and timers agree again.
[[nodiscard]] SaveGuard::HandoffPermit TryBeginNativeHandoff(const void* session)
{
    if (!enabled.load())
        return {};
    return saveAdmission.TryHandoff(session);
}

void ProbeSaveAdmission(const void* session)
{
    if (!saveAdmissionProbeRequested.load())
        return;
    bool idle{};
    {
        const std::unique_lock lifetime(boundaryMutex, std::try_to_lock);
        if (!lifetime || !enabled.load() || gate.Transitioning() || !saveAdmissionProbeRequested.exchange(false))
            return;
        idle = static_cast<bool>(TryBeginNativeHandoff(session));
    }
    sdk->logger->Info(plugin, idle ? "PTFR native save handoff admission: idle"
                                   : "PTFR native save handoff admission: deferred");
}

void DispatchSaves(void* session, void* jobs)
{
    ProbeSaveAdmission(session);
    OnLiveSavePoll(session);
    saveAdmission.Poll(dispatchSavesOriginal, session, jobs);
}
