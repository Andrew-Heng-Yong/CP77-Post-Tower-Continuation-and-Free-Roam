# QR9 prepared deployment tools

These tools are prepared for a later, explicitly authorized user deployment. Codex has not installed QR8, copied the selected save, started the game, or run a real rollback. Read-only Preflight does not prove that Windows will permit later writes.

The Core component verifies all 51 manifest paths and replaces only the consolidated archive and its ArchiveXL configuration. Its before state is the pinned installed PH3 build; its after state is QR8:02. The Diagnostics component is a separate optional two-file CET observer. Its dependency is the existing pinned CET ASI. Diagnostics Preflight can pass while PH3 is installed; it does not certify QR8 installation. Use a successful **Core Verify** receipt before testing QR8.

Run PowerShell 7 commands from the workspace. Close Cyberpunk 2077, REDprelauncher and REDlauncher naturally. The tool never closes or launches processes. Use the same unchanged script, manifests and recovery directory for all steps of one transaction.

```powershell
$tool = 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr9\worker_a\deploy_qr9_guarded.ps1'
pwsh -NoProfile -File $tool -Component Core -Action Preflight -BackupMaster
pwsh -NoProfile -File $tool -Component Diagnostics -Action Preflight
```

After explicit deployment authorization, the user may run:

```powershell
pwsh -NoProfile -File $tool -Component Core -Action Install -BackupMaster
pwsh -NoProfile -File $tool -Component Core -Action Verify
pwsh -NoProfile -File $tool -Component Diagnostics -Action Install
pwsh -NoProfile -File $tool -Component Diagnostics -Action Verify
```

Default recovery directories are `worker_a/recovery/core_qr8_02_01` and `worker_a/recovery/diagnostics_qr8_02_01`. An occupied recovery directory blocks a new Install; retain its journal and backups. An explicit `-RecoveryRoot` must be a fresh absolute child of `worker_a/recovery`, on the same volume as the game. A stable installer lock serializes all mutating invocations, regardless of the recovery directory.

`-BackupMaster` is an explicit Core Install option. Preflight only checks the plan. Install copies the three pinned files of the user-selected `ManualSave-23` to `recovery/core_qr8_02_01/master_before/ManualSave-23`, verifies the backup bytes, and records them in the journal. It never writes to Saved Games. The original master and offline backup must remain unchanged. To make a recognized working branch later, use the game's native **Load ManualSave-23 → Save Game → New Slot**. Never rename/copy a raw slot into Saved Games or overwrite the master. This bootstrap is not a captured startup PASS.

Before a later rollback, close the game/launchers naturally and validate first:

```powershell
pwsh -NoProfile -File $tool -Component Diagnostics -Action ValidateRollback
pwsh -NoProfile -File $tool -Component Diagnostics -Action Rollback
pwsh -NoProfile -File $tool -Component Diagnostics -Action Verify -ExpectedState Before
pwsh -NoProfile -File $tool -Component Core -Action ValidateRollback
pwsh -NoProfile -File $tool -Component Core -Action Rollback
pwsh -NoProfile -File $tool -Component Core -Action Verify -ExpectedState Before
```

Diagnostics rollback removes only the exact unchanged `init.lua` and `watch.json` bytes. It retains captured JSONL logs, unknown files and all directories. Core rollback restores the exact two PH3 files from its verified backup. Neither rollback restores saves. Each write transaction snapshots then-current saves and unmanaged game metadata before and after; legitimate working saves and logs created between transactions are allowed. The six Core external dependencies remain exact-hash requirements. If the selected original master changes, verification/rollback stops and preserves the immutable backup instead of restoring it automatically.

An interrupted transaction has not passed verification. Preserve its journal. After the game and launchers are closed, a later authorized user can run:

```powershell
pwsh -NoProfile -File $tool -Component Core -Action Recover
# Use -Component Diagnostics for an interrupted optional-addon transaction.
```

Recover returns to the state at the start of that action: interrupted Install → PH3/absent addon; interrupted Rollback → QR8/addon installed. It does not finish an interrupted installation. Unknown target bytes, damaged backups, corrupt journals, dependency drift or linked paths cause refusal. Do not delete unknown files or edit receipts to bypass refusal. A new installation after recovery needs a reviewed fresh recovery directory.

`-ReportFile` optionally writes a new report only beneath `worker_a`. Never reuse a report path. Receipts and reports contain file paths and hashes, not save bodies. File replacement is atomic per file and journaled; the two Core replacements are not a single Windows filesystem transaction. Runtime behavior, future-version saved-state compatibility and write permissions remain separate from fixture/preflight results.
