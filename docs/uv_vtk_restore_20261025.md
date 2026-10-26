# UV and VTK restoration — 25 October 2026

Restored the original `!!!_UV4.xl` mapping file and `vtk_VanillaHD_Head_xBaebsae.archive` at the user's request. This reverses the temporary female-head/body UV exclusions and the VTK head-geometry isolation test. The existing cosmetic rollback chain ran in order 03, 02, 01.

The restored files match the retained original download ZIPs. The installed packages are UV Framework 4.1, VTK Vanilla HD Body 3.4, VTK Vanilla HD Head 3.1 and VTK Extra Textures 1.0. All eleven corresponding installed package files matched their original ZIP entries.

Validate, three ValidateRollback/Rollback pairs, Verify and ValidateUndo passed. All 770 other protected files, including 289 save files, remained unchanged. The newly installed RED4ext, Codeware, ArchiveXL, TweakXL, Mod Settings and EquipmentEX are retained, as is PTFR. Current cache/save files changed after the earlier EquipmentEX install; this restoration protects the newer closed-game baseline.

No game launch, save modification or runtime fact write was performed. Appearance with the restored originals and the new official framework stack needs a live test; previous cosmetic passes applied to the temporary workaround configuration.

The two workaround files were backed up under `recovery/uv_vtk_restore_20261025_01`. To reinstate them with the game closed, run `diagnostics/uv_vtk_restore_20261025_01/restore_01.ps1 -Action ValidateUndo`, then `-Action Undo`. This changes only those two cosmetic files and does not undo saves. The original 03/02/01 receipts now record rollback; the new restoration receipt is authoritative for this transition.

Evidence: `diagnostics/uv_vtk_restore_20261025_01/assessment_01.json`, `manifest_01.json` and `installed_packages_01.json`. The separate online update check initially encountered Nexus's adult-content preference gate. No newer cosmetic package has been installed by this restoration.
