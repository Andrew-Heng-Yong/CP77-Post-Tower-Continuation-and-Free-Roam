# Packaging, deployment, verification and rollback

## P1 — Prepare an authorized consolidated successor

**Status:** recorded workflow in PH1–PH3; their literal builders/preparers are pinned historical scripts.

**Prerequisites:** authorized build/package scope, new complete candidate passing [build checks](consolidated-build.md), exact predecessor manifest, unchanged external mods and a fresh output. Preserve the stable 51 Tower paths; the approved Atelier file is an external compatibility component, not a 52nd bundled Tower path.

Inspect `prealpha/phone_studios_ph3/prepare_01.py`: it enumerates the three core folders, hashes candidate/installed files, asserts only expected replacements, records saves, writes the install manifest/checksum and full ZIP, then reads every ZIP member and checks CRC/hashes. Its source count, baseline and output paths are hardcoded. Adapt into a fresh task instead of overwriting `candidate_01`.

**Expected outputs:** 51-path candidate package, full local ZIP, install manifest plus SHA256, save/external baselines and ZIP proof. **Verify:** exact paths and member hashes, reviewed changed list, source/archive readback and current baseline. Local engineering ZIPs and the separately frozen beta are distinct artifacts.

## P2 — Final beta distribution layout

**Status:** final recorded four-folder package PASS, VD1 snapshot. **Prerequisites:** its exact recorded 51-file manifest/candidate and explicit release-packaging authorization.

`tools/package_release_020_readme.py` is the final recorded builder. It reads the VD1 candidate and `release/manifest-v0.2.0-beta.json`; it overwrites the prepared dist ZIP/manifests and removes obsolete helper entries under controlled paths. **Do not run it during documentation work or as a way to package PH3.** Its historical invocation is:

```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' tools/package_release_020_readme.py
```

**Expected outputs/checks:** 55 ZIP entries, exactly `archive/bin/r6/readme`, 51 core files and four reference documents/JSONs. No installers, scripts, release notes, persistence contract, old ZIP or backups are bundled. The required Atelier manual edit must reproduce corrected hash `5743CDCD...` in full as recorded in current-state. Read every ZIP member; verify CRC, hashes, exact folder/file set and no current-core overlap in obsolete cleanup paths.

**Blocked current test:** `tools/test_release_020.py` forwards to `test_release_020_cleanup_02.py`, which still reads `package/TowerContinuation/FILES.json`. That is the superseded layout. It also creates fixtures and writes `release/validation-v0.2.0-beta.json`. Do not call it a read-only/fresh final-layout certification. See C08; a future tooling task must reconcile it before reuse.

Consumer cleanup follows `release/AI_CLEANUP_INSTRUCTIONS.md`, `MANUAL_CLEANUP_INSTRUCTIONS.md` and the accepted-hash obsolete catalogue: delete only exact path+hash matches after containment/reparse checks, with unknown/changed files retained, no old ZIP or cleanup backup required. This is not permission to perform cleanup now.

## P3 — Validate and test a development deployment

**Status:** PH3 recorded four fixture cases PASS (clean and three interruption points); actual closed-game install/verify/rollback preflight PASS.

**Prerequisites:** installation authorization; game and launcher closed naturally; exact current before hashes; staged candidate/proofs; fresh recovery location; current save and external-file baselines. Do not auto-close or launch the game. Resolve source/layout drift before writing.

The existing transaction interface is `prealpha/phone_studios_ph3/deploy_01.ps1` with `-Action Validate|Install|Verify|ValidateRollback|Rollback`, optional bounded `-FixtureRoot`, and fixture-only failure points `AfterBackup|AfterFirstReplace|BeforeReceipt`. It verifies containment, rejects reparse paths, hashes all managed inputs, creates rollback copies, stages and hashes replacements, uses `File.Replace`, writes a receipt, and restores the original baseline on injected interruption.

For a **new** successor, adapt that script/manifest into its own task. Run its matching `test_deploy_01.py` only with fresh fixture paths and preserved before-state copies. Assert the exact expected replacements, successful clean rollback, automatic interruption recovery and no leftover stages. These tests write workspace fixtures; they are not read-only.

**Expected outputs:** fixture results, validated manifest/checksum, recovery receipt and before/after preservation reports. **Verify:** current filenames, member/source/proof hashes, changed-path allowlist, save names/bytes, unrelated mod bytes, and restoration of the full managed baseline in each fixture. Do not silently edit unsupported Atelier bytes or other mods.

## P4 — Actual deployment and installed verification

**Status:** exact historical PH3 command sequence below; not authorization or a reusable install command for its already-installed baseline.

```powershell
pwsh -NoProfile -File prealpha/phone_studios_ph3/deploy_01.ps1 -Action Validate
pwsh -NoProfile -File prealpha/phone_studios_ph3/deploy_01.ps1 -Action Install
pwsh -NoProfile -File prealpha/phone_studios_ph3/deploy_01.ps1 -Action Verify
pwsh -NoProfile -File prealpha/phone_studios_ph3/deploy_01.ps1 -Action ValidateRollback
```

`Validate`/`Install` intentionally reject occupied recovery paths and wrong before-state; do not remove backups to make a rerun succeed. For an installed successor, `Verify` and `ValidateRollback` check current manifests/receipts and remain subject to the game-closed guard. They do not launch the game or prove gameplay.

The accompanying `verify_preservation_01.py before|after` hashes the saved baseline, external Lizzie files and 51 managed paths, and requires fixture PASS. Its reports refuse overwrite. A future deployment needs a newly captured baseline, not the old task's save count.

## P5 — Safe rollback

**Status:** PH3 rollback readiness was verified; no rollback was executed by instruction maintenance.

**Prerequisites:** separately authorized rollback, game/launcher closed, current exact installed after hashes, matching immutable receipt/manifest, verified recovery old bytes. Execute only the newest applicable layer first:

```powershell
pwsh -NoProfile -File prealpha/phone_studios_ph3/deploy_01.ps1 -Action ValidateRollback
pwsh -NoProfile -File prealpha/phone_studios_ph3/deploy_01.ps1 -Action Rollback
```

**Expected output:** ROLLBACK_READY, then ROLLED_BACK with the predecessor file hashes restored. **Verify:** all managed before hashes and receipt state. PH3 precedes PH2, PH1, LR2 and LR1. Stop on any mismatch; do not blindly walk a historical chain after unrelated installs.

File rollback does not undo quest execution, rewards, saved receipts or persistent migrations. Restoring old binaries is not evidence that a newer save is compatible. Keep appropriate disposable save fixtures and preserve user/master saves. Development recovery backups are intentionally different from the beta consumer no-backup cleanup policy.
