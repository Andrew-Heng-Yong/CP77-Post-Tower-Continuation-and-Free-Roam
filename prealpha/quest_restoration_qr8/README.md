# QR8 evidence and reproduction

Start with completion.json, REPORT.md, HANDOFF.md and release_readiness.json. Source/packageQR8:02 is staged only; installedPH3 is unchanged. No game/runtime/collector/debugger/test execution is implied by static result files.

Fresh-output read-only validation commands from repository root:

```powershell
# Actual installed DLL byte checks:91assertions/six private byte mutants.
C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr8/worker_a/recheck_binary.py --output prealpha/quest_restoration_qr8/worker_a/reproduce_binary_01
# Complete current compile inputs:131sources/134pins/46managed, no SCC invocation.
C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr8/verify_compile_inputs.py --epoch prealpha/quest_restoration_qr8/source_epoch_02.json --output prealpha/quest_restoration_qr8/reproduce/compile_01
# Protected input/game/save metadata, no game or save writes; expect zero differences on unchanged inputs.
C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr8/verify_preservation.py --output prealpha/quest_restoration_qr8/reproduce/preservation_01
```

Prerequisites: exact pinned QR7/QR8 local evidence and candidates, current declared game/tool inputs, Python3.14 at the explicit path. Output paths must not exist. An input/version mismatch is a new boundary; do not change the old pins to turn it green. WorkerC/REPRODUCE.md and workerB/evidence_index.json name their native/proposal reproducers. WorkerA/evidence_index_04.json pins all native/namespace/inherited/final-package inputs. Inspect command parameters/top-level guards before any capture; never import a historical builder. PowerShell resource tooling loads build_phase2a.ps1 only with-HelpersOnly and explicit WolvenKit9.1 path.

The final archive/ZIP was independently fully extracted in worker_a/final_package_01. Its runner/schema is worker-owned and pinned there; reuse the recorded exact-source result rather than rerun unchanged large-stock hashes for every row. verify_archive.ps1 deliberately verifies baselineQR8:00; it is not the successor runner. Final successor source authority is source_epoch_02.json and its independent final result. Declaration of that distinction prevents a fresh baseline gate from being mistaken for final-package certification.

collect_acceptance_logs.ps1 is only a prepared read/copy collector. It was syntax-parsed, never executed against the game. It writes a fresh QR8 observation directory, records stale/concurrently changed snapshots and reads no save state. ENGINE_DIAGNOSTIC.md gives exactQR8:02 applicability to the inactive observer; original worker diagnostic text mentioningQR7is historical. Future actual run timestamps/fixture state are required. Neither document authorizes deployment, debugger attachment or launch.

Historical one-shot QR8 recipes: initialize.py, integrate_late_future.py, readback_late_future.ps1, verify_successor.py, rebuild_candidate.ps1, package_candidate.py, prepare_acceptance.py and publish_*.py. Do not rerun them over pinned outputs. Proposal filenames/NOT_FOR_INTEGRATION flags are preserved private history; coordinator promotion/epoch/readback records are the explicit later approval. Diagnostic/evidence artifacts are not bundled in the51-path ZIP.
