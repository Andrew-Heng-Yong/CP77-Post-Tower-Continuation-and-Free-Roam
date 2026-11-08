# QR11 diagnostic transaction

The practical installation and D00 instructions are self-contained in **MANUAL_TEST_PLAN.md**. This file contains recovery details. No real Install, Rollback or Recover was executed during QR11 preparation.

## Reviewed inputs

- Installer `deploy_diagnostics.ps1`: SHA256 `400438835F72415A78D6604EC9551034A2967BEB42206132FC94714E8496806E`.
- `diagnostics_manifest_01.json`: SHA256 `8B42EAC8C161256534DB26F859A62447E8A9921104929B10ADFF83020C1B2DD0`.
- Payload: unchanged QR10D01 candidate_02, exact two B04-before/D01-after hashes from QR10 manifest_02.
- Readiness binds that exact installer/manifest and final fixture-result hash. Real Preflight passed; this checks inputs but does not prove Program Files write permission.
- Protected requirements:51Core files +6 external dependencies + gameEXE; original master3files; working24 exact before installation; current all-save byte/name snapshots during each transaction. Subsequent normal working/autosave changes are preserved during verification/rollback, rather than compared with a historic snapshot.

The shared existing QR9 `worker_a/installer.lock` is held exclusively for real mutation, released even on process death, and never removed. Fixture locks are separate. Old QR9/QR10 evidence remains immutable. A normal install stores both old and new payloads with exact hashes before replacing anything. Each existing file uses Windows `File.Replace`; the pair is **not globally atomic**. The flushed hashed journal defines interrupted recovery. No save backup/restore action or Core component selector is exposed.

## Common command setup

Run from `C:\Users\Ayong\Documents\cp77 modding\tower ws`, game/RED launcher closed naturally:

```powershell
Set-Location -LiteralPath 'C:\Users\Ayong\Documents\cp77 modding\tower ws'
$ps7 = 'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
$installer = 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr11\deploy_diagnostics.ps1'
```

Read-only preflight:

```powershell
& $ps7 -NoProfile -File $installer -Action Preflight
```

Expected `PREFLIGHT_READY`. **Only after separate deployment authorization or the user's decision to run it:**

```powershell
& $ps7 -NoProfile -File $installer -Action Install
& $ps7 -NoProfile -File $installer -Action Verify
& $ps7 -NoProfile -File $installer -Action ValidateRollback
```

Require exit0 after every command and statuses `INSTALLED_VERIFIED`, `VERIFIED_AFTER`, `ROLLBACK_READY`. Stop on a nonzero exit; never continue a command sequence blindly. Do not invoke the old QR9 installer or remove an occupied QR11 recovery folder to rerun installation.

## Optional diagnostic rollback — not part of D00

Quit game/RED launcher, preserve logs and obtain rollback authorization or choose rollback yourself. Use the common setup, then:

```powershell
& $ps7 -NoProfile -File $installer -Action ValidateRollback
& $ps7 -NoProfile -File $installer -Action Rollback
& $ps7 -NoProfile -File $installer -Action Verify -ExpectedState Before
```

Require `ROLLBACK_READY`, `ROLLED_BACK_VERIFIED`, `VERIFIED_BEFORE`, with exit0 after each. Rollback requires a committed installed receipt, exact current D01 leaves and verified old/new recovery payloads. It restores only `init.lua`/`watch.json` to B04. Keep all captures, unknown files, directories and saved progress. File rollback is not save rollback. B04's callback observation defect is still present after rollback; do not use it to validate D00.

## Interruption recovery

If installation/rollback failed or was interrupted: **do not launch the game**. Preserve the console error and:

`C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr11\recovery\diagnostics_qr10d01_01\journal.json`

A caught install error attempts to restore B04 immediately. A caught rollback error attempts to restore the D01 state from before that rollback. An unfinished journal needs the explicit recovery action, with game/launcher closed and the exact source/manifest/readiness intact:

```powershell
& $ps7 -NoProfile -File $installer -Action Recover
```

Only run recovery for a reported interrupted transaction, not an ordinary committed receipt. It returns installation to B04 (`RECOVERED_BEFORE`) or an interrupted rollback to D01 (`RECOVERED_AFTER`). Verify using `-ExpectedState Before` or default After accordingly. An already restored caught install failure can be checked with `-Action Verify -ExpectedState Before`.

Unknown target/backup/dependency bytes, broken source proofs, a changed protected master or corrupt journal are refusal conditions. Preserve them for analysis; never replace unknown files, restore saves or delete the receipt to make the tool proceed. A successful before recovery does not authorize a new install; an occupied receipt deliberately prevents blind retries.

## Reproducing offline fixtures

Prerequisites: exact unchanged installer/manifest, current Python3.14 and bundled PowerShell7, fresh fixture run label. Only QR11/fixtures is writable by fixture mutation; game/Core/save contents there are synthetic except actual two-file diagnostic payloads.

```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B prealpha/quest_restoration_qr11/test_deployment.py --run run_NEXT
```

Expected 48checks/86actions and `PASS_DEPLOYMENT_FIXTURES`; fresh `run_NEXT_results.json`. Independent review adds8checks/7actions. Existing completed results should be reused; do not rerun the suite to test unchanged Core. No hardware power-loss or real Program Files permissions are certified. Initial interrupted discovery runs and original source drafts are retained under attempts/fixtures; only run_02 and review_02 qualify the frozen source.
