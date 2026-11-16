# Checkpoint v0.1.3 diagnostic successor

Prepared and installed 14 November 2026, Toronto time with the user's explicit approval. The current installation is `RD10_EXECUTION_CHECKPOINT_DIAGNOSTICS` v0.1.3. This successor changes only `red4ext/plugins/PTFR_ExecutionCheckpoint/PTFR_ExecutionCheckpoint.dll` to identify why the genuine Manual Save 26 Reed cutoff returned an empty execution checkpoint. It does not change the saved checkpoint field identities, REDscript bridge, Lua writer, combined archive, other Core files, dependencies or saves. [Exact installed manifest](deployment_01/installed_manifest_01.json).

## Finding and change

The v0.1.2 log reports `Execution checkpoint unavailable for the current cutoff` after three empty capture attempts. Code review confirms that the script and native route-1 point-of-no-return guards agree; the log does not identify which reflection or native check returned empty. [Bounded live observation](../universal_resume_checkpoint_runtime_observe_20261114_01/REPORT.md).

The v0.1.3 DLL records whether the final reflection call reaches native code, the route and ticket, the last gate-open status, and a distinct rejection stage for boundary, graph, handler, fact, instance, queue, encoding and final publication checks. It logs no save payload or quest fact values. Diagnostic state is transient; plugin version advances from 0.1.2 to 0.1.3. The original capture guards and data structures remain in place. [Source](source_01/NativeCheckpoint.cpp) · [Pinned source hashes](source_01/receipt.json).

## Offline validation

- Fresh C++ build: RED4ext plugin exports `Main`, `Query`, `Supports`; new DLL SHA-256 `F6DF93424254DF4BA7BC1191C128EDA662E3759325C7B602440626B3DF78FB4A`. [Build inventory](build_02/build.json).
- The executable fixture passed **46 checkpoint checks** with zero failures, including five checks that distinguish diagnostic rejection stages. The registration fixture passed **15 checks** with zero failures. These are synthetic tests; they do not prove live capture. [Results](checks_01/results.json).
- Only the DLL is in the staged package. Its predecessor installed hash is `5094F3C160FFB6E6A0E0EDA4AA627F6AE7FEA7159A11F60D99A06956A6EB319B`; the new hash and exact changed path are pinned in the [candidate receipt](candidate_01/receipt.json). The installed history REDscript, Lua writer and archive match the predecessor manifest. The current registered REDscript inventory contains the same 148 sources; none are changed here.
- The guarded installer passed **13 isolated actions**: clean install and rollback, interruption after staging, interruption after replacement, game-running refusal, and unknown-target refusal. Each fixture preserved its save and unrelated mod bytes. [Fixture results](fixture_results.json) · [Readiness](readiness.json).
- The real **read-only preflight** passed with 52 managed paths, 26 dependencies, 388 save files and a fresh recovery target. It performed zero save writes and zero game launches. The game and launcher process guard found no running protected process at the time of preflight. [Preflight](deployment_01/preflight.json) · [Exact transaction manifest](core_manifest_01.json) · [Guarded installer](deploy_core.ps1).

## Deployment and next gate

The user approved the one-file install. A fresh closed-game preflight passed immediately before the guarded transaction. Install reported `INSTALLED_VERIFIED`; independent readback confirmed all 51 Core paths, the v0.1.3 DLL and 26 dependencies. The 388 save-file tree and unmanaged game-file tree matched before and after the transaction. The guard reported zero save writes and zero game launches, `VERIFIED_AFTER` and `ROLLBACK_READY`. Exact v0.1.2 DLL recovery bytes and new DLL bytes are retained under the private recovery transaction. [Authorization](deployment_01/authorization_01.json) · [Fresh preflight](deployment_01/preflight_02.json) · [Install](deployment_01/install.json) · [Verification](deployment_01/verify.json) · [Rollback readiness](deployment_01/rollback_readiness.json).

The next player test is **one Reed-cutoff attempt from Manual Save 26 at normal game speed**. Check the new RED4ext checkpoint log after the cutoff; it should either name the failing capture stage or report `final capture ready`. A registration message alone is insufficient. Do not ask the player to finish The Tower again until the cutoff actually produces the checkpoint and its save-local commit. Live startup and capture remain unverified. A file rollback cannot undo save progress.
