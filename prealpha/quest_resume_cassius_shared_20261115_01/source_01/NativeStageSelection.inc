void ObserveResumeSelection(void* quests, const Capture& capture, std::int32_t ticket, std::int32_t route)
{
    if (route != 1)
        return;
    const std::unique_lock lifetime(boundaryMutex, std::try_to_lock);
    if (!lifetime || gate.Transitioning() || gate.Epoch() != capture.epoch ||
        notificationPasses || !Is(quests, QuestSystem))
        return;
    const std::unique_lock graph(LockAt(quests, 0x60), std::try_to_lock);
    if (!graph)
        return;
    const Boundary cutoff{quests, Read<const void*>(quests, 0xF8), ticket, route};
    if (!gate.Matches(cutoff) || !OpenFacts(cutoff))
        return;

    const auto fact = [&](std::string_view name) { return FactValue(cutoff.facts, name); };
    const auto plan = SelectResumeStage(capture.state, route, fact);
    if (!plan)
        return;

    RetainedQuestRestore original;
    if (!original.ValidateOriginal(RetainedQuestMethods::FromImage(image), quests, *plan))
        return;

    const auto& node = plan->stage->nodes.back();
    const auto& phase = plan->stage->phases[node.phase];
    const auto observed = std::ranges::find_if(capture.phases, [&](const LivePhase& row) {
        return row.record.depot == phase.depot && std::ranges::equal(row.record.Path(), phase.address);
    });
    if (observed == capture.phases.end())
        return;
    // A same-address replacement must not be read through a captured pointer.
    // Bind the live tree again and compare the body identity before any read.
    Capture current(false);
    if (!ReadPhases(current, quests))
        return;
    const auto live = std::ranges::find_if(current.phases, [&](const LivePhase& row) {
        return row.instance == observed->instance && row.record.depot == phase.depot &&
               std::ranges::equal(row.record.Path(), phase.address);
    });
    if (live == current.phases.end())
        return;
    const auto* listener = At<const void* (*)(const void*, std::uint32_t)>(0x2B1B64)(live->instance, node.node);
    if (!listener || Ready(listener))
        return;
    State queues;
    if (!CopyQueues(queues, quests) || std::ranges::any_of(plan->RetiredSlots(), [&](std::uint32_t slot) {
        return std::ranges::find(queues.notifications, slot) != queues.notifications.end();
    }) || std::ranges::any_of(plan->stage->phases, [&](const RestorePhase& ref) {
        return ref.depot && std::ranges::find(queues.resourceRequests, ref.depot) != queues.resourceRequests.end();
    }))
        return;

    // The successor's selection is diagnostic until the journal, lease and
    // adapter ownership transaction can authorize native restoration.
    sdk->logger->InfoF(plugin, "PTFR resume selected The Gig / Cassius collection (ticket=%d, original slot=%u)",
                       ticket, plan->RetiredSlots().back());
}
