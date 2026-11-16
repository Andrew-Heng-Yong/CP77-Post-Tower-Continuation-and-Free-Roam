# Step 2 startup failure and rollback

On 14 November 2026, the checkpoint registration repair v0.1.1 blocked Cyberpunk at startup. All times below are Toronto time. The game’s crash report came from the same process, PID 18568. [RED4ext startup log](observations_03/red4ext-2026-11-14-20-29-20.log) · [Engine crash summary](observations_03/stacktrace.txt)

| Time | Observation |
| --- | --- |
| 20:29:23 | RED4ext loaded the v0.1.1 DLL. The plugin rejected four runtime type checks during registration. |
| 20:29:30 | REDscript compilation succeeded. RED4ext then rejected the two missing native globals `PTFR.HistorySnapshotHS1.ReadExecutionCheckpoint` and `PTFR.HistorySnapshotHS1.DecodeExecutionCheckpoint`. |
| 20:31:44 | The engine asserted `Watchdog timeout! (120 seconds)` at `engineWatchdog.cpp:224`. RED4ext logged the same assertion and Cyberpunk wrote the crash report. |
| 20:33:05 | The guarded rollback restored and verified the RD10 files. |
| 20:33:19 | An independent file and dependency check returned `VERIFIED_BEFORE`. |

The dump records assertion thread 19424 and breakpoint exception `0x80000003` in `Cyberpunk2077.exe`. Startup thread 10272 was in `win32u!NtUserWaitMessage`. That thread’s captured stack contains the RED4ext return address immediately after its call to `MessageBoxW`. This fits the watchdog firing while the startup error dialog was open. The original crash bundle is in the local REDEngine report queue under `Cyberpunk2077-20261114-203144-18568-19424`.

## Registration failure

The checkpoint registrar rejected the strong-handle descriptors borrowed from `ScriptGameInstance.GetQuestsSystem`, `GetDelaySystem` and `GetTimeSystem`, plus the `array<Uint64>` descriptor borrowed from `MultiSelectCovers.selectedCovers`. The logs identify the failed checks. Descriptor availability at the callback and the exact cause of rejection within each check remain open. The offline fixture supplied those descriptors in advance, so it missed the live failure. [Checkpoint log](observations_03/ptfr_executioncheckpoint-2026-11-14-20-29-23.log) · [Prior repair and fixture results](../universal_resume_checkpoint_rtti_20261114_01/REPORT.md)

Immersive First Person’s patch compatibility warning also appears in the successful 19:53 RD10 launch. The two unresolved checkpoint globals are the script-validation errors from this failed startup.

## Recovery and test status

RD10 `MEET_KIRK_CONTENT_LOCK` is the current file-verified baseline. Rollback restored both history files and removed the checkpoint DLL. It verified all 51 Core files, the DLL’s absence and 26 dependencies. All 379 save-file contents and the save tree matched across rollback. The rollback used zero save writes and game launches. [Rollback result](../universal_resume_checkpoint_rtti_deploy_20261114_01/deployment_01/failure_rollback.json) · [Independent verification](../universal_resume_checkpoint_rtti_deploy_20261114_01/deployment_01/failure_verify_before.json) · [RD10 manifest](../resume_dispatcher_rd10_kirk_20261113_01/deployment_01/installed_manifest_01.json)

Checkpoint capture is unavailable on the restored baseline. The next Step 2 candidate needs to pass live startup validation at the main menu before the Manual Save 26 Tower capture and reload test can run.
