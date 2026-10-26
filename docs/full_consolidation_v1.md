# Post Tower Continuation and Free Roam — full consolidation v1

**Status:** Installed locally and file-verified on 25 October 2026. Gameplay acceptance is pending.

This package combines the complete installed alpha stack and subsequent local fixes, including the installed SR1 side job repair. The local ZIP `prealpha/full_consolidation_v1/candidate_01/dist/Post-Tower-Continuation-and-Free-Roam-v1.zip` contains 51 game files, replacing 127 legacy PTFR files in the current installation. The ZIP is not in Git or a GitHub Release yet. The number of archives falls from 25 to one, ArchiveXL registration files from 23 to one, and REDscript files from 76 to 46. The two CET entry files and one TweakXL file retain their paths. Three development CET helper mods and generated runtime data are outside the package.

REDscript accepts one module declaration per file. The current code uses 45 named modules plus one global script group, so 46 REDscript files are the smallest grouping validated without changing module identities or saved script types. The old archives and scripts remain recoverable in the deployment backup; future repairs should update the combined archive, registration file, or affected module script and archive the replaced version in the workspace.

## Preservation checks

- The combined archive contains 1,153 effective resources. Every resource was read back and checked against the last winning bytes from the 25 installed archives. The 37 internal override keys resolve to the same bytes. No installed non-PTFR archive uses any of these resource keys.
- The combined ArchiveXL file retains 742 distinct quest phase registrations, 13 streaming block registrations and the English lipmap registration.
- The 46 REDscript files compile with the full installed script set, including EquipmentEX. Every original PTFR script body is preserved, and the decompiled output has the same 661,977 nonblank lines as the current compiled build after normalization of generated wrapper numbers.
- The two CET entry files and the TweakXL file are byte identical to the current installation. All 117 files in the last alpha release manifest and ten later installed files are accounted for.
- The ZIP contains only the 51 game-relative installation paths; its entries were read back and checked against the package manifest.

Local-only evidence under `prealpha/full_consolidation_v1/candidate_01` includes `install_manifest_01.json`, `build_archive_02.json`, `build_xl_01.json`, and `test_reds_modules_01.json`; the external collision scan is `prealpha/full_consolidation_v1/external_collisions_01.json`. The ZIP has SHA-256 `2A148EDF7D99AF9ECCE433959BD23F012E80BAAA764D2F5578C848C8B1AED86D`.

## Installation and recovery

Use [deploy_02.ps1](../prealpha/full_consolidation_v1/deploy_02.ps1) to validate, install, verify or roll back the local game installation. The installer checks all old and new hashes, then moves individual old files into `recovery/full_consolidation_v1_01/old` before copying the combined files. A receipt records an interrupted deployment so `ValidateRollback` and `Rollback` can restore the old layout. The installer passed 25 isolated actions: a complete install/verify/rollback cycle and interruptions after steps 1, 64, 127, 150 and 178. Local `Validate`, `Install`, `Verify` and `ValidateRollback` passed. Local-only `postinstall_01.json` found all 51 combined files at the expected hashes, 124 retired paths absent and all 289 baseline save files unchanged.

For a manual install, remove the 124 retired PTFR paths listed in the manifest before extracting the ZIP into the game root. Do not layer the ZIP over an older PTFR installation: duplicate owners and stale overrides can result.

The source archives, previous repair builds and recovery files remain in the workspace. Rollback restores files, not saved quest state. The package has offline equivalence checks; game startup, the Tower handoff, save/reload and side job behavior still require live acceptance. Keep the untouched pre-ending test save while validating this layout. The game was not launched by the installer.
