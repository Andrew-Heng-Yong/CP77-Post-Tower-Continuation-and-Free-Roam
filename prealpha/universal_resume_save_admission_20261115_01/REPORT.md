# Step 3 native save guard

15 November 2026. Checkpoint v0.1.6 uses one new RED4ext hook at `0x3CC488`, the save dispatcher for the pinned Cyberpunk 2.5 executable. The hook acquires the existing save permit before the dispatcher can consume pending requests. While a handoff holds the exclusive permit, the dispatcher defers to a later engine update. The engine retains its pending request and makes the usual eligibility decision when dispatch resumes. [Native binding](NativeSaveAdmission.inc) · [Guard](SaveAdmission.hpp)

The dispatcher polls automatic and checkpoint requests at `0x3CC4D2` and takes pending manual, quicksave and slot-overwrite requests through the ink handler at `0x3CC5D6`. Before it submits the save job, native code sets bit `0x10` at engine offset `0x308`. Native completion clears that bit. The handoff acquires its exclusive permit before testing the bit, so an already admitted save also defers the handoff after the dispatch call has returned. The engine owns the preflight bit and the save queue. [Executable instruction and vtable readback](run_01/assessment.json)

The existing queued CET probe briefly tries the same handoff permit and logs `PTFR native save handoff admission: idle` or `deferred`. It resolves the running engine through the RED4ext SDK and checks its dispatch vtable before reading the flag. The permit is released before logging. A future live handoff must hold its permit from before the first edit until the quest and timers are coherent, including recovery after a failed transfer.

**78 offline checks passed.** Twelve exercise missing engine, queued manual and automatic requests, an active dispatch, asynchronous save completion and the next stock poll. The 51 checkpoint and 15 registration checks passed against the successor build. The build verified all 78 paths in the installed manifest and recorded the exact compiler input files and hashes. A separate readback matched the installed v0.1.4 DLL and the pinned Manual Save 29 backup. [Admission checks](run_01/SaveAdmissionChecks.txt) · [Compile inputs](run_01/compile_inputs.json) · [Workspace DLL](run_01/PTFR_ExecutionCheckpoint.dll)

## Installation and MS26 smoke test

The closed-game preflight passed after 15 synthetic deployment and recovery actions. The install replaced one DLL. Post-install readback verified all 78 manifest paths and the v0.1.4 rollback copy. All 397 save files matched by name and hash. All 26 required files matched by hash, and unmanaged game metadata matched across the transaction. [Installed manifest](deployment_01/installed_manifest_01.json) · [Installer fixtures](fixture_results.json) · [Rollback readiness](deployment_01/rollback_readiness.json)

1. Load **Manual Save 26** in free roam and run this in the CET console.

   ```lua
   local s = Game.GetScriptableSystemsContainer():Get("PTFR.HistorySnapshotHS1.CaptureArchiveHS3"); print(s and s:RequestExecutionProbe() or false)
   ```

2. Expect `true` for the queued probe. Close CET and resume for a few seconds. The latest `red4ext/logs/ptfr_executioncheckpoint-*.log` should contain `PTFR checkpoint probe ready` and `PTFR native save handoff admission: idle`.
3. Make a **new manual save** and reload it once to check the normal save path.

The in-game smoke test covers attachment, idle guard admission and manual saving. Save contention during the first live timer handoff remains pending.
