# CET execution checkpoint probe and inline gate repair

v0.1.4 was installed with the user's approval on 14 November 2026, Toronto time. It replaces the checkpoint DLL and adds a queued diagnostic request to `PTFR_HistorySnapshotHS1.reds`. [Exact installed manifest](deployment_01/installed_manifest_01.json)

## Reed cutoff result under v0.1.3

The plugin registered at 22:06:52. At 22:10:03, three calls from the Manual Save 26 attempt reached the native reader with ticket 1, route 1 and revision 3. Each returned `boundary_gate_mismatch`. The `gate=transition` field is the last recorded lifecycle status. Each call had already passed the guard for a transition in progress. The regular history committed and CET verified both history exports. The native checkpoint did not commit. [Plugin log](observations_01/checkpoint.log) · [CET log excerpts](observations_01/cutoff-lines.txt)

The installed archive puts Reed's gate writers in inline graph `root/10` and Hanako's in `root/3/113`. These definitions have empty phase resource references. The matching executable passes an inline child's own empty resource handle to the instance constructor while passing its graph separately. The old recognizer read the enclosing depot from the child instance itself. Its synthetic fixture had supplied that depot directly on the child. v0.1.4 records the actual writer and checks its enclosing depot and inline ancestry in the locked live phase tree. The real ticket, route, graph locks and cleanup guards still apply to publication. [Pinned graph and executable evidence](observations_01/inline-source.json) · [Native implementation](source_02/NativeCheckpoint.cpp)

## Run the probe

Load **Manual Save 26** and run this in CET while outside the ending.

```lua
local s = Game.GetScriptableSystemsContainer():Get("PTFR.HistorySnapshotHS1.CaptureArchiveHS3"); print(s and s:RequestExecutionProbe() or false)
```

`true` means the request was queued on the scriptable system. Close the overlay and resume play so the game can process the request. The RED4ext checkpoint log will print `PTFR checkpoint probe ready` with counts or a `probe refused` stage. The collector reads the current phase tree, handlers, logical inputs, node instances and pending queues. It counts timer handlers and leaves scheduler duration sampling to the genuine cutoff. The response is a single status word. The capture is transient and the checkpoint decoder rejects that status as input. The command provides a repeatable in-game collection test from MS26. Reed's cutoff, a committed save-local payload and post-Tower save/reload are separate live checks. [Queued script method](source_02/PTFR_HistorySnapshotHS1.reds)

## Offline verification

- All 148 registered REDscript sources compiled from the exact installed inventory with the additive overlay. Compiled readback matched the history field layout and native declarations. [Compile receipt](compile_02/receipt.json)
- The native build passed 51 checkpoint and probe checks and 15 registration checks. Fixtures exercise both inline gate paths, refusal of a matching path under the wrong depot, capture without a cutoff, refusal after the point of no return, and refusal to decode the one-word probe status. The Reed synthetic checkpoint still preserves mask 70 and the two sampled timers. [Native checks](checks_01/results.json) · [Build inventory](build_01/build.json)
- The guarded installer passed 16 isolated actions including interruption after either replacement and rollback of both. [Installer fixtures](fixture_results.json) · [Transaction manifest](core_manifest_01.json)

## Installed verification

Fresh closed-game preflight and the approved two-file transaction passed. Independent readback verified 51 Core paths, the checkpoint DLL and 26 dependencies. All 388 save files matched before and after the transaction, and rollback to v0.1.3 is ready. Live startup and the CET probe are pending. [Authorization](deployment_01/authorization_01.json) · [Fresh preflight](deployment_01/preflight_02.json) · [Installed verification](deployment_01/verify.json) · [Rollback readiness](deployment_01/rollback_readiness.json)
