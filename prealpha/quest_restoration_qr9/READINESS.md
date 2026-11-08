# QR9 offline readiness

**Offline preparation is complete. Await explicit deployment authorization.** No installer action, including its real Preflight, was run against the game. No game launch, CUA, gameplay, fact/save edit, real save copy, deployment or release operation occurred. Installed PH3 remains unchanged. These are preparation results, not runtime acceptance.

Use [USER_PROCEDURE.md](USER_PROCEDURE.md) for exact future preflight, installation, verification, rollback, working-save, CET and collection commands. Begin with S00 only. The user runs the installer and performs all gameplay.

## Exact baseline and tools

- Core: canonical **QR8:02**, unchanged 1,577 payloads and 51 package paths. Future installation changes only the combined archive and its `.archive.xl`. No core rebuild, compile, serialization or baseline ZIP regeneration was needed.
- QR8 archive SHA: `2AB35CC95931CD3C7BB2FB3A4C8B52746DE7847D42AE1DD3503A90A965FD2039`.
- QR8 XL SHA: `F22693981B0A10DB21B47AFAD7FC8BCAEF1F021D9EA99548BA4FF80F56D18245`.
- Final installer: `worker_a/deploy_qr9_guarded.ps1`, SHA `CE020172988081100199A35C9FAA9131444DB4DED52893480F2BA746EFFDA39E`. Its byte-identical final source, predecessor snapshots, source applicability proof and promotion receipt are preserved.
- Core manifest: `worker_a/core_manifest_02.json`; optional observer manifest: `worker_a/diagnostics_manifest_01.json`. Exact staged/installed hashes, ZIP, dependency pins and master proof are in `baseline.json` and these manifests.
- Observer: frozen **QR9B04**, exactly two separate CET files, `worker_b/addon_manifest_04.json`. No new native plugin or REDscript. It is staged only, not installed.

## Verification

| Gate | Evidence and bounded result |
| --- | --- |
| Initial baseline | All 1,577 source payloads, 51 package paths, ZIP member bytes and installed PH3 hashes verified; two core changes identified. |
| Installer original body | `worker_a/fixture_result_02.json`: 29 workspace scenarios pass, attributed to original source SHA `3D3504…`. |
| Stable-lock successor | `worker_a/final_fixture_result_01.json`: 7 affected-path/lock scenarios pass, SHA `C8EE59…`. Includes distinct recovery-root contention and post-lock dependency drift. |
| Actual payload transactions | `worker_a/exact_payload_result_01.json`: actual 51-file core and two-file observer lifecycle checks pass in workspace only, SHA `C8EE59…`. Saves are synthetic. |
| Final guards | `worker_a/receipt_guards_result_01.json`: 4 final CE020 cases pass, including committed-Recover refusal and same-process lock disposal. `evidence/source_applicability.json` documents exact reuse boundaries. |
| Independent installer review | C independently ran 84 checks across four actual synthetic scenarios, then 32 final source/applicability checks. See `worker_c/reviews/installer_final_01/review.json`; it preserves exact source-version attribution. |
| CET observer | 39 standalone LuaJIT assertions and 5 actual Lua-source mutation controls pass. Independent A review adds 16 checks. No CET DLL or actual Game API was loaded. |
| Collector | Seven root test methods pass, including malformed/stale capture controls and exact read-only collection. B's independent 20 checks include cross-validation with actual Lua-produced synthetic JSONL. |
| Independent preparation preflight | `preflight_01/result.json`: PASS at its recorded UTC; exact core/source/observer targets, dependencies, proof files, fresh recovery paths and master3 files checked. No game/RED launcher running. This checker neither imported nor invoked the installer. B reviewed it separately. |
| Preservation | `preservation_01/result.json`: all 23,828 protected SHA pins match; all 856 game and 307 save file metadata entries match; existing tracked diff/branch/HEAD unchanged. Final metadata boundary is also recorded in `readiness.json`. |

Fault examples, rejected intermediate behavior and exact script snapshots remain preserved. The original PowerShell null/empty-path failure was corrected, and final guards close the committed-recovery admission and lock-lifetime gaps. Historical test results are not relabeled as executions of the final source.

## First fixture and runtime boundaries

The user confirmed **ManualSave-23 — 29 October, 7:23 PM** as genuine Tower lineage. Its original three files remain untouched. Future authorized `Install -BackupMaster` preserves an exact offline copy. The user then uses native **Load23 → Save Game → New Save**, identifies the actual new slot, and uses that working branch. No raw-folder rename is assumed safe. All controllers may initialize during bootstrap; bootstrap cannot certify disposable startup, and later reload is retained-owner evidence.

The first card is a 1–2 minute S00 load/control/map smoke. Stop on an unexpected restart, call, actor/reward duplicate or error. Start/stop are simply `GetMod("PTFR_QR9_Diagnostics").start("S00")` and `.stop()` through that same module. Stop before every deliberate reload; start a new segment afterward. Captures are bounded to 300 seconds by default, 900 maximum, 2,048 rows and 8 MiB. No fact polling fallback or state setter is present.

The selected master already completes CVI02, Saints and Spy. Fresh-entry cases are NOT_TESTABLE there; no replay/reset is requested. Other absent completion names do not prove eligibility. The nine cards, branch rules and JSON/CSV results are in `worker_c/verification_01/`. No gameplay result is PASS or FAIL yet; unavailable selected-fixture cases are classified separately from unperformed tests.

The logger records baseline values, fact deliveries, guarded journal/phone/vehicle reads and cleanup calls. Actual graph execution, native owner/lease, numeric ArchiveXL engine receipt, native pending clock/queue and save identity remain **NOT_OBSERVED**. A fact, registration attempt or unconditional plugin receipt is not successful-owner acknowledgement. Expected header hashes are declarations; current offline hashes do not prove earlier executed bytes. Missing callbacks or notifications need prerequisite/settings/owner analysis before being called defects.

Real write permissions, actual CET API exposure/event delivery, fresh activation, save transitions and gameplay remain untested. Replacements are per-file atomic with a recovery journal, not a two-file atomic or power-loss guarantee. Rollback changes files only and never reverses saved state. QR8's held Ronald first-enrollment route, five static UNKNOWN contracts, old controller/timer boundaries and other conditional/opaque limits remain in force. This is limited controlled-test readiness, not general release approval.

Preparation stops here. After explicit authorization, the user follows the procedure, performs S00 and returns the bundle plus a short visible observation. Codex then analyzes that evidence before choosing the next card or any source-confirmed repair.
