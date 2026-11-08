# Independent QR11 diagnostic deployment review

Status: **approved offline installer source and bounded fixtures**. This is preparation approval, not authorization or evidence of a real deployment. Final readiness still requires the primary fixture result and exact readiness binding; this review does not launch the game or install anything.

Reviewed installer SHA256 `400438835F72415A78D6604EC9551034A2967BEB42206132FC94714E8496806E` and manifest SHA256 `8B42EAC8C161256534DB26F859A62447E8A9921104929B10ADFF83020C1B2DD0`. No blocking source defect remains in this reviewed version.

## Scope and exact bytes

The manifest names exactly the existing two diagnostic leaves under `PTFR_QR9_Diagnostics`: `init.lua` B04 `ACCE8B7E...` → D01 `1A366E10...`, and `watch.json` B04 `AEC4D492...` → D01 `A1AAB30B...`. Both before values must exist and both paths must change; arbitrary managed paths and absent-target installation are refused. Source inventory is exactly two files. The 58 required inputs comprise Core51, six external dependencies and the exact game executable. All required hashes are fresh-read; the prior hash-cache reuse was removed. Package proofs and payloads are checked before installation.

The original `ManualSave-23` three-file pins apply to every real action. `ManualSave-24` pins apply only to before-state Preflight/Install, so later legitimate play does not prevent verification or diagnostic file rollback. No save setter, save copy-back, fact setter, quest execution, input automation or game-launch action exists. Each mutating transaction snapshots then-current save names and SHA256 bytes, unmanaged game metadata and required dependency bytes. Drift is detected; unknown saves/dependencies are preserved, never restored to the preparation snapshot.

## Transaction and recovery

Install, Rollback and Recover share the existing zero-byte QR9 `worker_a/installer.lock`, held exclusively independent of recovery directory. The real path must already exist, and unexpected lock contents are refused. Real actions use the pinned manifest; fixture override roots are restricted to the QR11 fixtures tree. Containment checks reject path traversal, reparse ancestors, alternate streams and Windows device names. Recovery/source/game/save overlap and cross-volume staging are refused.

The deployment is **not a globally atomic pair**. Each known leaf replacement uses a staged verified file and per-file atomic replacement. The checksummed journal is durably staged and replaced, and records the operation/state. Recovery chooses the operation's starting side, checks all targets are known before/after bytes and requires only backups needed for actual restoration. An incomplete pre-backup journal can close without inventing missing payloads. Unknown target bytes or corrupt required recovery payloads are preserved and block restoration. Committed receipts cannot be passed to Recover; rollback requires the verified installed state. Rollback interruption restores its D01 action-start state, rather than pretending file rollback reverses a save.

Readiness checks bind the actual script and pinned manifest to the referenced fixture-result SHA before real actions. The primary agent must finish and inspect that exact result before generating readiness, and separately perform read-only real preflight. Fixture success does not exercise actual Program Files write permission or real engine behavior.

## Efficiency correction

The reviewed `NoLinks` optimization uses `.NET File.GetAttributes` for each ancestor. It catches only missing-file/missing-directory exceptions and remains fail-closed for other errors; it retains full ancestor traversal and reparse rejection. No path-check or hash-result cache was introduced. The independent broken-report-link control below passes with this implementation.

The earlier `fixtures/review_01` run overlapped the primary agent's source update and is **discovery only**. Its final unchanged-source assertion correctly failed, and it emitted no passing result. `discovery_run_01.json` preserves that boundary. The reviewer did not stop any process; an attempted CIM query restricted to the reviewer runner was denied. Final evidence is the fresh unchanged-source run below.

## Independent adversarial evidence

Ran `review/test_adversarial.py` against the exact unchanged installer above. `adversarial_results_02.json` records **8 assertions and 7 actual PowerShell fixture calls**, all passed. Diagnostic payloads are the actual pinned B04/D01 bytes; Core/dependencies and saves are synthetic within `fixtures/review_02`.

The additional cases establish:

- After fixture installation, overwrite all three working ManualSave24 fixture files to represent later human play. Verify, ValidateRollback, Rollback and Before-state Verify succeed; every later working-save byte and pinned master fixture byte remains exact.
- Rollback restores only the exact two B04 diagnostic leaves, preserving an unknown game file.
- A nonempty package-proof entry with changed bytes blocks installation before journal creation or any game/save mutation.
- A broken report symlink is refused without creating its missing target or changing game/save fixture bytes.
- The installer SHA is identical at the beginning and end of the run.

No duplicate full fixture suite was run by this reviewer. The primary agent owns the comprehensive interruption/lock/corruption suite and its final result binding.

## Manual plan limits

The working-save candidate is named `ManualSave-24` in its actual metadata: 2 November 2026 16:37:02, level51, `mq030` in finished quests, and the same playthrough ID as the user-confirmed `ManualSave-23`. This correlates the working save to the confirmed lineage; metadata alone is not independent proof of genuine Tower execution. `ManualSave-23` remains untouched and pinned. The user controls loading and gameplay.

D00 can be offered only when the existing Regina **Call** option is present; absent means NOT_TESTABLE with no history reset, contact enablement or eligibility fabrication. A sampled fact difference tests getter-difference capture only. Native callback delivery remains unsupported and unverified. Do not repeat Wilson, Bullets, Zane shop or confirmed reload acceptance tests. Exact owner activation, listener ownership, queue/acknowledgement semantics, termination and reward idempotence remain outside this deployment review.

No real game, save, Core file, QR9/QR10 evidence or installed diagnostic file was changed by the reviewer. No real Install/Rollback/Recover command, game/CET module execution, game launch or CUA was performed.
