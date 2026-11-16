"""Generate the v0.1.8 translation unit from the exact installed v0.1.7 source."""

from hashlib import sha256
from pathlib import Path


HERE = Path(__file__).resolve().parent
PREDECESSOR = HERE.parent / "universal_resume_save_session_20261115_01/run_01"
SOURCE = HERE / "source_01"


def read(path, expected):
    raw = path.read_bytes()
    if sha256(raw).hexdigest().upper() != expected:
        raise ValueError(f"Changed predecessor input {path}")
    return raw.decode("utf-8-sig").replace("\r\n", "\n")


def substitute(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"Unexpected predecessor anchor {old}")
    return source.replace(old, new, 1)


def main():
    native = read(PREDECESSOR / "NativeCheckpoint.cpp",
                  "D92A1BF8F65E0636002ED93ABE9E1EF93D38267F09902D84CC7A0B226624106F")
    admission = read(PREDECESSOR / "NativeSaveAdmission.inc",
                     "D4CEC2CA11EDEAA3ED2F91108C12B52C25D5890D67A63B50260889C83E5260B2")
    replacements = (
        ('#include "Checkpoint.hpp"\n#include "SaveAdmission.hpp"\n#include "../CheckpointRegistration.hpp"',
         '#include "../../universal_resume_checkpoint_probe_20261114_01/source_02/Checkpoint.hpp"\n'
         '#include "../../universal_resume_save_admission_20261115_01/SaveAdmission.hpp"\n'
         '#include "../../universal_resume_checkpoint_probe_20261114_01/CheckpointRegistration.hpp"\n'
         '#include "../../universal_resume_game_time_restore_20261115_01/GameTimeRestore.hpp"\n'
         '#include "../../universal_resume_live_quest_job_20261115_01/RetainedQuestRestore.hpp"\n'
         '#include "../../universal_resume_live_world_20261115_01/WorldPrefabSupport.hpp"\n'
         '#include "HandoffControl.hpp"'),
        ('class Transition\n{', 'void ResetLiveHandoff();\nSaveGuard::HandoffPermit BeforeLiveTransition(void* quests);\n'
         'void OnLiveSavePoll(const void* session);\nvoid OnLiveQuestDrain(void* quests);\n'
         'void OnLiveClockLocked(void* timeSystem);\n\nclass Transition\n{'),
        ('    Transition()\n    {\n        const std::lock_guard lock(boundaryMutex);\n        gate.BeginTransition();',
         '    explicit Transition(void* quests = nullptr)\n    {\n        const std::lock_guard lock(boundaryMutex);\n'
         '        transitionPermit.emplace(BeforeLiveTransition(quests));\n        gate.BeginTransition();\n        ResetLiveHandoff();'),
        ('        gate.EndTransition();\n    }\n};', '        gate.EndTransition();\n    }\n\nprivate:\n'
         '    std::optional<SaveGuard::HandoffPermit> transitionPermit;\n};'),
        ('    const Transition transition;\n    loadOriginal', '    const Transition transition(quests);\n    loadOriginal'),
        ('    const Transition transition;\n    teardownOriginal', '    const Transition transition(quests);\n    teardownOriginal'),
        ('    const Transition transition;\n    rootOriginal', '    const Transition transition(quests);\n    rootOriginal'),
        ('    const Transition transition;\n    restoreOriginal',
         '    const Transition transition(request ? Read<void*>(request, 8) : nullptr);\n    restoreOriginal'),
        ('    const Transition transition;\n    restoreHandlersOriginal',
         '    const Transition transition(quests);\n    restoreHandlersOriginal'),
        ('        --notificationPasses;\n    }\n}',
         '        --notificationPasses;\n    }\n    if (enabled.load())\n        OnLiveQuestDrain(quests);\n}'),
        ('    if (!lock || timerRequest.timeSystem != timeSystem || !gate.Matches(timerRequest.boundary))',
         '    if (!lock)\n        return;\n    OnLiveClockLocked(timeSystem);\n'
         '    if (timerRequest.timeSystem != timeSystem || !gate.Matches(timerRequest.boundary))'),
        ('using PackedState = RED4ext::DynArray<std::uint64_t>;',
         '#include "NativeHandoff.inc"\n\nusing PackedState = RED4ext::DynArray<std::uint64_t>;'),
        ('        *out = std::move(encoded);',
         '        ArmLiveHandoff(quests.GetPtr(), timeSystem.GetPtr(), capture, ticket, route);\n'
         '        *out = std::move(encoded);'),
        ('Hook hooks[]{\n', r'''Hook hooks[]{
    MakeHook(0x1934AC, "\x48\x89\x5C\x24\x08\x48\x89\x74", &ObserveUninitializeGameWait, uninitializeGameWaitOriginal),
    MakeHook(0x193C74, "\x48\x89\x5C\x24\x20\x55\x56\x57", &InitializeRestoredGameWait, initializeGameWaitOriginal),
    MakeHook(0xA0A84C, "\x48\x89\x5C\x24\x18\x48\x89\x4C", &MakeRestoredGameTimer, makeGameTimerOriginal),
    MakeHook(0x88BC58, "\x89\x54\x24\x10\x53\x48\x83\xEC", &NotifyQuest, notifyQuestOriginal),
    MakeHook(0xEB6B3C, "\x40\x53\x48\x83\xEC\x30\x83\x79", &AllocateRestoreSlot, allocateQuestSlotOriginal),
    MakeHook(WorldUpdateEntry, "\x48\x8B\xC4\x48\x89\x58\x08\x48", &ObserveWorldUpdate, worldUpdateOriginal),
'''),
        ('        Read<const void*>(image + FactsManager, 0x10) != image + 0x2B2270 ||',
         '        Read<const void*>(image + FactsManager, 0x10) != image + 0x2B2270 ||\n'
         '        Read<const void*>(image + FactsManager, 0x18) != image + 0x350E50 ||\n'
         '        Read<const void*>(image + QuestSystem, 0x200) != image + 0x88BC58 ||\n'
         '        Read<const void*>(image + QuestSystem, 0x2C8) != image + 0x194AC4 ||\n'
         '        Read<const void*>(image + WorldStreamingUpdateType, 0x18) != image + WorldUpdateEntry ||\n'
         '        Read<const void*>(image + GameTimeHandler, 0x10) != image + 0x193C74 ||\n'
         '        Read<const void*>(image + GameTimeHandler, 0x20) != image + 0x1934AC ||'),
        ('RED4EXT_V1_SEMVER(0, 1, 7)', 'RED4EXT_V1_SEMVER(0, 1, 8)'),
    )
    for before, after in replacements:
        native = substitute(native, before, after)
    admission = substitute(admission, "    ProbeSaveAdmission(session);",
                           "    ProbeSaveAdmission(session);\n    OnLiveSavePoll(session);")
    for name, body in (("NativeCheckpoint.cpp", native), ("NativeSaveAdmission.inc", admission)):
        path = SOURCE / name
        path.write_bytes(body.encode("utf-8"))
        print(f"{name} {sha256(path.read_bytes()).hexdigest().upper()}")


if __name__ == "__main__":
    main()
