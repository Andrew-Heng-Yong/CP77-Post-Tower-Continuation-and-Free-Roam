# Post Tower Continuation and Free Roam — full consolidation v1

**Current successor:** [WA2](world_actions_wa2_20261028.md) was installed on 28 October. It retains CC1, the 30 corrective donors restored by [CR1](consolidation_repair_cr1.md), the S30 additions, and the same 51 install paths. Use WA2's rollback first. The audit correction and historical results below remain part of the record.

**Status:** Installed locally and file-verified on 25 October 2026. On 26 October, the user reported the combined mod and previous fixes working with public Codeware 1.21.1. Full restored-quest coverage remains pending.

**26 October audit correction:** The [all-sidejob entry/phone audit](sidejob_entry_phone_audit_20261026.md) found that consolidation selected superseded donors at 30 conflicting resource paths (37 overwrite events), discarding several prior repairs. Package hashes and read-back remain valid, but the earlier claim of preserved internal override winners is withdrawn. The installed S30 successor inherits these losses. No repair or installation was performed by the audit; consult its per-job findings before treating the combined package as equivalent to the previous stack.

This package combines the complete installed alpha stack and subsequent local fixes, including the installed SR1 side job repair. The local ZIP `prealpha/full_consolidation_v1/candidate_01/dist/Post-Tower-Continuation-and-Free-Roam-v1.zip` contains 51 game files, replacing 127 legacy PTFR files in the current installation. The ZIP is not in Git or a GitHub Release yet. The number of archives falls from 25 to one, ArchiveXL registration files from 23 to one, and REDscript files from 76 to 46. The two CET entry files and one TweakXL file retain their paths. Three development CET helper mods and generated runtime data are outside the package.

REDscript accepts one module declaration per file. The current code uses 45 named modules plus one global script group, so 46 REDscript files are the smallest grouping validated without changing module identities or saved script types. The old archives and scripts remain recoverable in the deployment backup; future repairs should update the combined archive, registration file, or affected module script and archive the replaced version in the workspace.

## Policy for subsequent fixes

Build each production fix into a successor of the complete consolidated package.
Replace the affected archive, ArchiveXL registration, REDscript module, CET entry,
or TweakXL file at its existing install path. Do not leave a sequence of hotfix
overlays or obsolete versions in the player's game folder. Keep old packages and
replaced source files in the workspace for debugging and rollback; they are not
part of the new install. Add a new installed path only when the engine needs a
distinct resource or module. Record that need in the change log and remove any
retired path through the installer.
The temporary Scav workspot prototype approved on 26 October is a scoped
diagnostic exception. It adds three reversible files alongside the current
51-file package. Its eventual production replacement must return to 51 files
and remove all prototype-only paths; see the
[ambient investigation](world_hostile_idle_report_20261026.md).

Before installing a successor, verify the full package manifest, native archive
resource winners, script compilation, installer replacement and rollback, and
preservation of save files. Maintain a separate rollback receipt for each
installed version. File rollback cannot undo quest or reward changes already
written into a save.

## Preservation checks

- The combined archive contains 1,153 effective resources. Every resource was read back against the builder-selected bytes from the 25 installed archives. **Superseded equivalence claim:** later review found that the builder's repeated overwrites discarded prior corrective donors at 30 distinct paths; the 37 figure counts overwrite events, not unique keys. No installed non-PTFR archive uses these resource keys.
- The combined ArchiveXL file retains 742 distinct quest phase registrations, 13 streaming block registrations and the English lipmap registration.
- The 46 REDscript files compile with the full installed script set, including EquipmentEX. Every original PTFR script body is preserved, and the decompiled output has the same 661,977 nonblank lines as the current compiled build after normalization of generated wrapper numbers.
- The two CET entry files and the TweakXL file are byte identical to the current installation. All 117 files in the last alpha release manifest and ten later installed files are accounted for.
- The ZIP contains only the 51 game-relative installation paths; its entries were read back and checked against the package manifest.

Local-only evidence under `prealpha/full_consolidation_v1/candidate_01` includes `install_manifest_01.json`, `build_archive_02.json`, `build_xl_01.json`, and `test_reds_modules_01.json`; the external collision scan is `prealpha/full_consolidation_v1/external_collisions_01.json`. The ZIP has SHA-256 `2A148EDF7D99AF9ECCE433959BD23F012E80BAAA764D2F5578C848C8B1AED86D`.

## Installation and recovery

Use [deploy_02.ps1](../prealpha/full_consolidation_v1/deploy_02.ps1) to validate, install, verify or roll back the local game installation. The installer checks all old and new hashes, then moves individual old files into `recovery/full_consolidation_v1_01/old` before copying the combined files. A receipt records an interrupted deployment so `ValidateRollback` and `Rollback` can restore the old layout. The installer passed 25 isolated actions: a complete install/verify/rollback cycle and interruptions after steps 1, 64, 127, 150 and 178. Local `Validate`, `Install`, `Verify` and `ValidateRollback` passed. Local-only `postinstall_01.json` found all 51 combined files at the expected hashes, 124 retired paths absent and all 289 baseline save files unchanged.

For a manual install, remove the 124 retired PTFR paths listed in the manifest before extracting the ZIP into the game root. Do not layer the ZIP over an older PTFR installation: duplicate owners and stale overrides can result.

The source archives, previous repair builds and recovery files remain in the workspace. Rollback restores files, not saved quest state. The package has offline equivalence checks and the user reports a successful current-fixture run; the Tower handoff on a fresh fixture, full save-upgrade behavior and restored side-job branches still need individual coverage. Keep the untouched pre-ending test save while validating this layout. The game was not launched by the installer.

The combined REDscript package also compiled with the unmodified public Codeware 1.21.1 scripts. The local machine now has all nine untouched public Codeware files; the earlier two-line script correction was archived for rollback. The user reports a successful live run with the public package. Exact quest branches and fresh-transition coverage were not itemized; see [the framework follow-up](core_updates_20261025.md).
