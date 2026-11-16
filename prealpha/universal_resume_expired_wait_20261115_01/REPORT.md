# Over the Edge after Falco’s wait expires during The Tower

For this MS31 trial the player accepts the original wait expiring naturally if Over the Edge continues. The live v0.1.8 build captured 84,710 game seconds remaining. The Tower’s time jump expired that wait ahead of base-game cleanup. The guard deferred and the player stopped the run. [Live observation](../universal_resume_live_runtime_20261115_01/observations_01/REPORT.md)

| Readback | Observed native state |
| --- | --- |
| AutoSave-7, before base-game cleanup | Original timer 125066 and its mapping were gone. In Falco’s original phase, slot 2333 advanced from wait node 28 to logical condition node 2. Both Reyes listeners were still registered. |
| AutoSave-8, after base-game cleanup | Both cleanup flags were set. Falco’s new condition and both Reyes listeners were gone. The quest’s started fact was set and the Falco completion fact was absent. The save was still inside the ending. |

The verified Falco phase has a single incoming edge to node 2, from the authored wait. Node 2 checks the side-quest content token and whether V is outside Reyes’s trigger. Its native successors handle contact and pickup progression. [AutoSave-7 readback](../universal_resume_live_runtime_20261115_01/run_08/assessment.json) · [AutoSave-8 readback](run_01/assessment.json)

Checkpoint v0.1.9 watches the original timer and the pending logical condition in the retained Reed session. It requires the native expiry, the matching live condition and its retirement during Tower cleanup. The existing post-credits guard, save permit and prefab checks still gate the restore. The expired path initializes Falco’s native condition with the original Reyes listeners and branch choice. A wait that is still pending at cleanup uses the existing timed handoff. [Native handoff](source_01/NativeHandoff.inc)

The exact build passed 87 checkpoint regressions, 28 integration checks and 21 quest restore checks. Gameplay verification requires Falco’s normal message and pickup progression after the genuine ending, plus a clean reload of a fresh manual save. [Build assessment](run_04/assessment.json) · [MS31 test card](TEST_CARD.md)

The staged installer passed 17 installation and recovery fixture actions. Closed-game preflight verified the one-DLL scope, all 52 managed files, 26 dependencies and a 403-file save snapshot that matched the original MS31 hash. The seven native providers matched across the 137 scanned archives. [Readiness](staged_05/readiness.json) · [Preflight](staged_05/preflight_01.json)

The authorized 15 November installation replaced the checkpoint DLL. Closed-game readback verified all 52 managed files and 26 dependencies. All 403 saves matched, including MS31. The v0.1.8 file rollback passed readiness verification. The live game test is pending. [Installed manifest](staged_05/deployment_01/installed_manifest_01.json) · [Rollback readiness](staged_05/rollback_readiness_01.json)

The subsequent MS31 run verified native expiry, cleanup, and phase rebuilding. The checkpoint rolled back at handler setup. [Live result](observations_01/REPORT.md)
