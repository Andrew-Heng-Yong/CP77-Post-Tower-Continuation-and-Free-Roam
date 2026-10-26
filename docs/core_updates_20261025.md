# Essential mod updates — 25 October 2026

The user requested installation after the update check. EquipmentEX is excluded because the user chose to update it themselves after Chrome access was declined.

| Component | Previous installation | Installed |
| --- | --- | --- |
| RED4ext | 1.30.0 | Official 1.31.0, including winmm loader |
| Codeware | Local PR63 build + PR65 script fix | Official 1.21.1 binary and scripts, retaining the two-line PR65 fallback-return fix |
| ArchiveXL | Local PR31 + SDK229/230 + PR32 guard | Official 1.28.0 |
| TweakXL | Local PR22 build | Official 1.12.0 |
| Mod Settings | Local PR33 + PR34 build | Official 0.2.22 for game 2.50 |

CET 1.38.0, redscript 0.5.32, Deceptious Quest Core 3.3.1 and EquipmentEX 1.2.9 are retained. RedHotTools stays outside the game. The existing PTFR S29, CF1 and housing fixes are preserved.

## Package and compatibility checks

All five ZIPs came from their authors' GitHub releases and match the published SHA256 digests. The current game executable reports patch 2.5. Mod Settings's required versions are satisfied together by this update.

The ArchiveXL 1.28.0 tag uses SDK commit `5246e659d783e5834cc08a90e56c8932c9ed3449`. Its sources retain the corrected FindSlotData offset 0x450, MatchVisualTag offset 0x4E0, CMesh size 0x220, StatIDType int8 representation, and the empty partsOverrides guard. These are the relevant equivalents of the previously installed local fixes.

Codeware 1.21.1 still omits an explicit fallback return in Reflection.Call. The staged global script adds only `let result: Variant;` and `return result;` to preserve the already installed PR65 correction. Its DLL and all other changed files match the official packages. The install is therefore an official Codeware binary with a small retained local script patch, not an entirely untouched release.

**Public-package compatibility follow-up:** The official [Codeware 1.21.1 release](https://github.com/psiberx/cp2077-codeware/releases/tag/v1.21.1) is the latest public release checked on 25 October. Its [unmodified Reflection source](https://github.com/psiberx/cp2077-codeware/blob/v1.21.1/scripts/Reflection/Reflection.reds) lacks those two fallback lines. An isolated full REDscript compile replaced the local patched `Codeware.Global.reds` with the byte-exact file from the official release ZIP; all 64 combined PTFR and dependency script files compiled successfully. PTFR does not call `Reflection.Call`. The two-line patch is therefore **not required for PTFR compilation**. The local installation still carries it, and a cold load using the untouched public script has not been run. Evidence: local-only `prealpha/full_consolidation_v1/public_codeware_probe_01/result.json`; repeatable source `prealpha/full_consolidation_v1/test_public_codeware_01.py`.

The full current stack of 93 redscript sources compiled successfully with EquipmentEX 1.2.9 included. Compiled comparison verifies all 146 PTFR classes unchanged, all 212 existing classes containing persistent fields retain those fields, and all 51 Codeware namespace class names remain present. The official update removes the unused native InkGameSystem declaration and adds two native declarations. Compilation does not prove live engine behavior.

The installation candidate is `diagnostics/core_updates_20261025_01/candidate_02`. The initial workspace preparation stopped at a Reflection declaration assertion before any installation; candidate_02 corrects the assertion and retains the missing fallback. Final package, compile and proof artifacts are pinned; use successors for changes.

## Recovery and testing

Installer: `diagnostics/core_updates_20261025_01/install_01.ps1`.
Backup: `recovery/core_updates_20261025_01`.

After installation, close the game and use `-Action ValidateRollback`, then `-Action Rollback`, to restore the exact previous framework stack. Roll back this package before the older Oct 24 framework patches. Later modifications to targeted files make rollback refuse rather than overwrite them. The two new ArchiveXL files are moved into recovery on rollback. Saves and user settings are not reverted.

After updating EquipmentEX separately, cold-start the game and load a retained save. Check Mod Settings opens, PTFR setup finishes, and the outfit/body display works; then continue the S29 follow-up quest tests. No game launch or gameplay validation is performed by this installation task.

Installation completed: 23 replacements and two additions. Validate, Install, Verify and ValidateRollback passed, as did 14 installer fixture actions. All 740 protected files, including 283 save files, remained byte-identical. Game testing is pending. The authoritative outcome and hashes are in `diagnostics/core_updates_20261025_01/assessment_01.json`.


## EquipmentEX follow-up installation

The user subsequently downloaded EquipmentEX 1.2.10 and requested installation. It is now installed from that ZIP. This replaces the earlier plan for the user to install it themselves.

Only its two scripts and dependency-hints TOML changed; the archive, XL and license are identical. The full 93-source stack compiled successfully. Compiled comparison found only the version string and three minimum-framework version constants changed, with all saved fields retained. All 14 installer fixture actions and installation/readback/rollback checks passed. The other 762 protected files, including 283 saves, were unchanged.

Evidence: `diagnostics/equipmentex_20261025_01/assessment_01.json`. Backup: `recovery/equipmentex_20261025_01`. Use `diagnostics/equipmentex_20261025_01/install_01.ps1 -Action ValidateRollback`, then `-Action Rollback`, to restore the three previous files. Roll back EquipmentEX before downgrading its required Oct 25 frameworks. EquipmentEX remains optional for PTFR. No game launch occurred; Wardrobe/outfit and new-framework gameplay checks remain pending.
