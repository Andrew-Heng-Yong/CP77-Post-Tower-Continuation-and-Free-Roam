# Step 3 save-session binding repair

15 November 2026. Both v0.1.6 game probes logged `deferred`. The installed probe took the `CGameEngine` singleton from the SDK, then checked it against the vtable of `gsmState_Session`. The pinned 2.5 address table resolves the singleton to `0x3BBFB38`. The native type readers and their registration sites identify the `CGameEngine` and `gsmState_Session` vtables separately. The session update at `0x3CC094` calls into the save dispatcher, and the pre-game session update also delegates to it. [Live retry](../universal_resume_save_admission_20261115_01/observations_02/REPORT.md) · [Provider and dispatcher readback](run_01/assessment.json)

Checkpoint v0.1.7 queues admission after the existing CET checkpoint probe succeeds. The next native save poll tests the guard against its own session object. It releases the permit before logging and calls the stock dispatcher with the original arguments. Load and teardown clear pending diagnostics. The handoff interface accepts the verified live session and scopes its permit to the caller's transfer. [Native binding](NativeSaveAdmission.inc)

**87 offline checks passed.** Nine new checks exercise the actual detour wrapper, live-session argument forwarding, idle and busy results, handoff contention and load cancellation. The existing 51 checkpoint, 15 registration and 12 save-admission checks passed. The build verified the 78 installed baseline paths and recorded the exact C++ compile inventory. [Checkpoint and detour checks](run_01/CheckpointChecks.txt) · [Compile inputs](run_01/compile_inputs.json) · [Workspace DLL](run_01/PTFR_ExecutionCheckpoint.dll)

## Installation and live retest

The closed-game transaction replaced the checkpoint DLL on 15 November. All 15 deployment and recovery fixture actions passed. Post-install readback verified all 78 installed paths and the v0.1.6 rollback copy. All 400 save files matched by name and hash, all 26 required files matched by hash, and unmanaged game metadata matched. [Installed manifest](deployment_01/installed_manifest_01.json) · [Installer fixtures](fixture_results.json) · [Rollback readiness](deployment_01/rollback_readiness.json)

Load **Manual Save 30** in free roam. Once the save indicator clears, run the same CET probe once.

```lua
local s = Game.GetScriptableSystemsContainer():Get("PTFR.HistorySnapshotHS1.CaptureArchiveHS3"); print(s and s:RequestExecutionProbe() or false)
```

`true` means the probe queued. Close CET and resume for a few seconds. The expected log line is `PTFR native save handoff admission: idle`. The first live timer transfer remains pending.
