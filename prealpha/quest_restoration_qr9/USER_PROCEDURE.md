# QR9 installation and first manual test

Prepared offline only. Wait for explicit deployment authorization. Codex has not installed, launched or controlled the game. The user runs these commands and all gameplay. Use **PowerShell 7** (`pwsh`), not Windows PowerShell 5.

The canonical core remains QR8:02: 51 managed files, with only the combined archive and its `.archive.xl` changing from installed PH3. The optional diagnostic observer adds two separate CET files; it is not a rebuilt core package. Exact hashes, test results and the current preflight are linked from `READINESS.md`.

## Preflight and future installation

Close Cyberpunk and its RED launcher normally. Keep them closed throughout installation, verification and any rollback. These tools never close or launch them. Do not run two installer commands concurrently.

```powershell
$qr9 = 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr9'
$installer = Join-Path $qr9 'worker_a\deploy_qr9_guarded.ps1'
pwsh -NoProfile -File $installer -Component Core -Action Preflight -BackupMaster
pwsh -NoProfile -File $installer -Component Diagnostics -Action Preflight
```

Expected: `PREFLIGHT_READY` for each component. Core checks the pinned PH3 installation and staged QR8 package. Diagnostics checks its two absent target files and the pinned existing CET dependency; that preflight alone does not certify QR8 is installed. An occupied recovery directory, changed hash, reparse path or running game/RED launcher must refuse. Stop on any refusal and return the error; do not bypass a guard or delete recovery evidence. Preflight exercises no game write permission.

Only after explicit authorization, the user runs:

```powershell
pwsh -NoProfile -File $installer -Component Core -Action Install -BackupMaster
pwsh -NoProfile -File $installer -Component Core -Action Verify -ExpectedState After
pwsh -NoProfile -File $installer -Component Diagnostics -Action Install
pwsh -NoProfile -File $installer -Component Diagnostics -Action Verify -ExpectedState After
```

Expected: both `INSTALLED_VERIFIED` and both `VERIFIED_AFTER` results. Stop at the first error. The core transaction creates an exact three-file backup of ManualSave-23 in `worker_a\recovery\core_qr8_02_01\master_before\ManualSave-23` and backs up the two changing installed files. No command writes to Saved Games. Recovery journals are in the corresponding core/diagnostics recovery directory. Preserve them.

The tool provides per-file atomic replacement and a recovery journal, not an atomic two-file pair. Do not launch with a partial transaction. For an interrupted transaction, close the game/RED launcher naturally and return the error/journal for review. The prepared command `pwsh -NoProfile -File $installer -Component Core -Action Recover` (or `-Component Diagnostics`) restores that action's starting state; a failed rollback therefore returns toward the installed state. Unknown target/backup/journal bytes refuse. Do not invoke recovery speculatively.

## Working save — protect ManualSave-23

The user selected **ManualSave-23 — 29 October, 7:23 PM** as genuine post-Tower lineage. Metadata alone was not used to prove that lineage. Keep that original and its verified recovery backup untouched.

All installed restored controllers may initialize during a load. Avoiding quest locations does not isolate that first load; establish the verified backup before bootstrap.

1. After successful installation and backup verification, the user launches normally. Start the S00 observer at the main menu if available, then load ManualSave-23 solely to create a working branch.
2. As soon as the native menu permits it, use **Save Game → New Save**. Never overwrite ManualSave-23. If New Save is unavailable, stop; do not force saving or change facts.
3. Identify the newly created native slot by timestamp/screenshot. Record it. Codex can later match its metadata to the actual directory; a copied or renamed raw folder is not assumed to be recognized by the game.
4. Stop capture before any deliberate load. Keep this first segment identified as **bootstrap**. Initial restored owners may already have run before the new slot exists or before the observer attaches, so this segment cannot certify disposable startup or fresh registration.
5. Use only the clearly identified new native slot for the following smoke and later tests. After a normal quit, `Core Verify -ExpectedState After` checks the original master and backup again. Any master mismatch is a stop condition; there is no automatic save restoration.

Loading and immediately making a native working save is user-operated bootstrap. Subsequent reload evidence describes that retained working branch; it does not retroactively prove fresh owner activation. File rollback cannot undo changes already persisted in a working save.

## First card — S00 only

Use the reviewed working-save procedure above. Start manually in CET:

```lua
GetMod("PTFR_QR9_Diagnostics").start("S00")
```

Load the identified working slot normally, move and open/close the map for 1–2 minutes. Accept no gig. Look for a normal load, control/map response, unexpected quest restart, repeated call, duplicate actor/reward or visible error. Stop immediately on an unexpected result. Enter:

```lua
GetMod("PTFR_QR9_Diagnostics").stop()
```

Stop before every deliberate reload and start a separate segment after the normal load or from the main menu. Captures do not span saves reliably or identify the loaded save automatically. Default duration is 300 seconds; the module stops automatically at its duration/event/byte limit. A failed cleanup blocks further starts in that Lua environment.

Logs are in:

`C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_QR9_Diagnostics\QR9_capture_*.jsonl`

After stopping capture and quitting normally, collect the newest S00 segment:

```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr9\collect_observation.py' --run-id S00_01 --card S00
pwsh -NoProfile -File $installer -Component Core -Action Verify -ExpectedState After
```

Use a new run label for each bundle. To collect bootstrap separately, use `--run-id S00_bootstrap` before another capture is created, or add `--log 'EXACT_PRINTED_CAPTURE_BASENAME.jsonl'` with its actual basename. No placeholder filename should be entered literally. Output is under `observations\<run-id>`. Source logs, game files and saves are read only. Support logs are bounded candidates with explicit timestamp/alignment limits; collection does not award a gameplay PASS.

Send the bundle and one line: **S00/bootstrap or working smoke; actual slot/timestamp; loaded and map/control okay? any unexpected quest/call/error?** A screenshot is needed only for a visual problem. Do not manually inspect hundreds of facts.

Fresh CVI02, Saints and Spy entry cases are unavailable on this master's completed history. Do not reset or replay them. Other missing completion names do not prove fresh eligibility. Full later cards and JSON/CSV result templates are in `worker_c/verification_01/`.

## Future file rollback

Quit normally first. Preserve the working saves, logs and recovery files. Remove the optional observer first, then restore the core files:

```powershell
pwsh -NoProfile -File $installer -Component Diagnostics -Action ValidateRollback
pwsh -NoProfile -File $installer -Component Diagnostics -Action Rollback
pwsh -NoProfile -File $installer -Component Diagnostics -Action Verify -ExpectedState Before
pwsh -NoProfile -File $installer -Component Core -Action ValidateRollback
pwsh -NoProfile -File $installer -Component Core -Action Rollback
pwsh -NoProfile -File $installer -Component Core -Action Verify -ExpectedState Before
```

Expected: `ROLLBACK_READY`, `ROLLED_BACK_VERIFIED`, `VERIFIED_BEFORE`. The observer rollback removes only the two exact unchanged managed addon files, retaining generated logs, unknown files and directories. Core rollback restores only its two exact backed-up predecessor files and verifies all 51. This does not reverse saved quest state. Do not load a progressed test branch under older files as a claim of save rollback; retain the untouched master and return the recovery evidence for any transition review.
