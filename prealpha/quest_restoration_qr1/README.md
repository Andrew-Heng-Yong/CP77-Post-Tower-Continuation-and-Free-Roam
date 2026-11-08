# QR1 — Incomplete whitelist-restoration implementation checkpoint

This working batch implements verification/build tooling and a complete persistent work queue. **It is not a completed quest-repair release. No gameplay patch was justified or applied in this batch. No quest is marked STATIC_VERIFIED.** Installation remains PH3.

Start with `REQUEST.md`, `checkpoint.json`, `quest_status_matrix.csv`, `queue.json` and `HANDOFF.md`. `candidate_01/` is a **source-equivalent reproduction of PH3**, not a fix for the remaining quest uncertainties. Its ZIP preserves the 51-path consolidated layout. Do not install it expecting repaired quest behavior.

Verified work:

- Every included catalogue ID has an identity correlation to current resource/contract/dispatch/journal evidence. The original 32 mapping gaps and five generic bindings are corroborated. Different evidence strengths remain visible; identity does not prove lifecycle correctness.
- 880 actual admission predicates were checked for bounded integer fact and journal-state contradictions, including AND/OR/NOR. No known contradiction was found; unsupported conditions remain unconstrained.
- Fresh full-current SCC compilation passed with 131 sources. Source/cache inputs remained unchanged. The old 112-source result was not reused as current proof.
- Complete consolidated archive rebuilt and all 1,574 payloads read back. Every payload equals PH3; 50 non-archive package files remain identical. Compression/index metadata can change archive-level hashes.
- Fresh lookup across 134 archives found no unexpected additional provider for any PTFR payload. Existing native counterparts of recorded overrides remain explicit. Other asset/provider uncertainties are not certified.
- 24 existing regression/mutation controls and 14 new tooling/identity/guard controls pass.
- The existing auditor was improved to retain all competing providers in ambiguity evidence and to accept a separate source-pinned identity registry without broadening the whitelist.

The proposed Delamain admission edit was **rejected before writing**: actual current guards require `PTFRS25_SQ025_FRESH_Issued == 0`, already excluding that takeover. Keep `rejected_delamain_patch_01.ps1` as rejected evidence; do not run it as a repair. The eight Sandra/Delamain counter-name warnings are inherited from native resources and do not justify artificial resets.

## Reproduction and continuation

The scripts are task-scoped and preserve completed outputs. Do not blindly rerun them against `candidate_01`. For a fresh engineering batch, adapt the output root and baseline deliberately, preserving this checkpoint.

```powershell
& 'C:/Users/Ayong/.local/bin/python3.14.exe' -B prealpha/quest_restoration_qr1/start.py
& 'C:/Users/Ayong/.local/bin/python3.14.exe' -B prealpha/quest_restoration_qr1/resolve_identities.py
& 'C:/Users/Ayong/.local/bin/python3.14.exe' -B prealpha/quest_restoration_qr1/identity_layers_02.py
& 'C:/Users/Ayong/.local/bin/python3.14.exe' -B prealpha/quest_restoration_qr1/guard_checks.py
pwsh -NoProfile -File prealpha/quest_restoration_qr1/rebuild_01.ps1
& 'C:/Users/Ayong/.local/bin/python3.14.exe' -B prealpha/quest_restoration_qr1/compile_01.py
pwsh -NoProfile -File prealpha/quest_restoration_qr1/providers_01.ps1
& 'C:/Users/Ayong/.local/bin/python3.14.exe' -B prealpha/quest_restoration_qr1/tests_01.py
pwsh -NoProfile -File prealpha/quest_restoration_qr1/adversarial_01.ps1
```

Run existing `tools/parity_audit/run_tests.py` only with a **fresh** regression output containing copies of the current `prepared.json`, `catalogues.json`, and an absolute accepted `capture_pointer.json`. Do not overwrite the original PH3 audit outputs. The identity importer is used by:

```powershell
& 'C:/Users/Ayong/.local/bin/python3.14.exe' -B tools/parity_audit/reconcile.py TASK_ROOT FRESH_RECONCILIATION_DIR QUEST_IDENTITY_REGISTRY
```

The fresh reconciliation directory requires the six pinned inventory inputs listed in this batch's `candidate_01/reconcile_01/`. Its registry checks resource hashes and selected IDs; it never approves gameplay differences or admissions.

`finalize_01.py` creates the 51-path ZIP, file manifest, 161-row quest matrix, 1,610-row contract matrix and exact remaining queue. It refuses to replace the ZIP. Protection and adversarial results are separate checks. No deployer is included or invoked.

## Remaining work

All ten quest contracts still need deep per-family verification and justified implementation where actual defects are found. Original/saved owner liveness, interrupted states, reward uniqueness, SMS paths and opaque actor/prefab/workspot/camera semantics remain unproved. The earlier static audit's unknown differences are not automatically defects. `queue.json` records exact roots, dependencies, evidence, batch assignments, completed checks and remaining acceptance criteria for every included quest.
