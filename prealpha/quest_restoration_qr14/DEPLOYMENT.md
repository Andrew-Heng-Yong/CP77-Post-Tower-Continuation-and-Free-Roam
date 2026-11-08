# QR14 — QR13 deployment preparation

Prepared for QR8:02 → QR13:02. **No real installation is authorized or performed by this preparation.** The installed QR10D01/D00E diagnostics and saves remain outside the write set. The candidate ZIP/package is unchanged from the final QR13 review.

## Inputs and write set

Use `core_manifest_02.json`, selected by `readiness.json`, with `deploy_core.ps1`. Manifest01/engine01 and their fixtures are preserved intermediate evidence, superseded for deployment by manifest02/the final script.

The installer checks all51 stable Core paths, replacing only:

- `archive/pc/mod/zzzz_PTFR_Combined.archive`
- `r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds`
- `r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds`

It hashes26 protected dependencies, including both diagnostic files, the Atelier correction and17 LBD script sources. Before installation it also checks151 compiler inputs and the complete148-source inventory across `r6/scripts` and `red4ext/plugins`, refusing new/deleted sources, linked sources and linked directories. Existing non-source log links are retained without following them. Offline SCC output stays in this workspace; it is never copied into the game cache.

Exact staged archive SHA256: `97D3C65BB72F4BA4F3BCB6AECDE9ABA105315D0340918F42590363F9F90A32BF`. ZIP SHA256: `B2BDC04BE7CF202047C3E7CF85F9BB3BD8F0D77B9D98ACA7C1377F5E5AD52EB8`.

## Prerequisites

Explicit user approval of this deployment; Cyberpunk2077, REDlauncher and REDprelauncher closed naturally; matching current hashes; intact candidate, fixture/review/readiness proofs; fresh default recovery directory. The script refuses unexpected states. It never closes/launches a process or repairs an unrelated mod.

ManualSave-23 is the pinned genuine Tower master. ManualSave-24 is the unchanged selected working snapshot; both exact three-file identities are checked before installation. All then-current saves are hash-snapshotted for each mutation. There is no save-writing, fact-setting or save-restore operation. New legitimate working saves are allowed before rollback; master preservation remains mandatory.

## Exact commands

Run from PowerShell. Use the full PowerShell7 executable below; Windows PowerShell5.1 is not the tested host.

```powershell
Set-Location -LiteralPath 'C:\Users\Ayong\Documents\cp77 modding\tower ws'
$ptfrPwsh = 'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
$ptfrInstaller = 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr14\deploy_core.ps1'
& $ptfrPwsh -NoProfile -File $ptfrInstaller -Action Preflight
```

Expected: exit0 and `PREFLIGHT_READY`. This reads the real game/saves and creates no game, recovery or lock files. The preparation's recorded result is `preflight_01.json`; later preflights should not overwrite it.

**Only after explicit deployment approval**, the exact installation command is:

```powershell
& $ptfrPwsh -NoProfile -File $ptfrInstaller -Action Install -ReportFile 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr14\deployment_01\install.json'
```

Expected: `INSTALLED_VERIFIED`. Immediately run:

```powershell
& $ptfrPwsh -NoProfile -File $ptfrInstaller -Action Verify -ReportFile 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr14\deployment_01\verify.json'
& $ptfrPwsh -NoProfile -File $ptfrInstaller -Action ValidateRollback -ReportFile 'C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr14\deployment_01\rollback_ready.json'
```

Expected: `VERIFIED_AFTER`, then `ROLLBACK_READY`. None launches the game. An install requires a later complete restart before human gameplay. No cache deletion, manual `.reds` copy, diagnostic update or fact command is part of deployment.

## Backups, interruptions and rollback

Default recovery directory:
`C:\Users\Ayong\Documents\cp77 modding\tower ws\prealpha\quest_restoration_qr14\recovery\core_qr13_02_01`

It contains exact verified `old/` QR8 and `new/` QR13 copies of only the three changing files, per-file staging and an integrity-checked `journal.json`. Backups are completed before replacements. Each replacement is atomic; the three-file set is journaled rather than globally atomic. Process-interruption fixtures do not establish power-loss durability.

A caught failure attempts to restore the action's starting state. A hard process interruption leaves a journal for explicit recovery. Preserve all evidence, keep the game closed and review the error before proceeding. `Recover` restores QR8 after an interrupted Install, or QR13 after an interrupted Rollback. Unknown/corrupt/linked bytes are refused; they are never overwritten to force success. Do not delete a recovery directory or stale evidence to rerun Install.

For an identified interrupted transaction only, after reviewing its journal and with the game closed:

```powershell
& $ptfrPwsh -NoProfile -File $ptfrInstaller -Action Recover
```

Verify the reported side with `-Action Verify -ExpectedState Before` or `After` as appropriate. Recover refuses an already committed receipt.

For a separately authorized file rollback of a committed install, first use `ValidateRollback`, then:

```powershell
& $ptfrPwsh -NoProfile -File $ptfrInstaller -Action Rollback
& $ptfrPwsh -NoProfile -File $ptfrInstaller -Action Verify -ExpectedState Before
```

Expected: `ROLLED_BACK_VERIFIED`, `VERIFIED_BEFORE`. Only the three managed leaves revert. **File rollback does not undo quest execution, saved private receipts, rewards or save migrations.** QR13-created persistent state is not certified for QR8 by a successful file rollback fixture. The diagnostic QR11/D00E layer remains installed throughout.

Read `REPORT.md` and `readiness.json` for current preparation results; preparation is not authorization or gameplay certification.
