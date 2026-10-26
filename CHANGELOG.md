# Change log

## Unreleased — after v0.1.1-alpha.20261024

These changes are in the local development installation. **No new GitHub Release has been published.** The consolidated package passes static and installation checks; a full Tower transition and restored-quest playthrough on that layout remain pending.

### Restored content and repairs

- Added native entry adapters for the remaining 18 selected side jobs. The implemented entry inventory now covers 80/80 selected gigs and 78/78 selected side jobs. Follow-up trees, rewards, map timing, and save/reload need gameplay testing. See [S29 playtest notes](docs/sidejobs_s29_playtest.md).
- Repaired Judy's private apartment door lock and the missing Dennis holocall setup for *Big in Japan*. Their live quest checks remain pending. See [JD1](docs/judy_dennis_jd1.md).
- Repaired side-job scene and owner details found in the vanilla comparison: Johnny cigarette and smoke routes, English lipmap registration for 44 private scenes, Yoko's component choices, Zane's shop return, Delamain phone ownership and sequel admission, *Where Eagles Dare* completion, and one orphaned *Sinnerman* ember. The three-file SR1 repair was installed, then folded into the consolidated package. Scene-by-scene gameplay remains pending. See [SR1](docs/sidejob_repair_sr1_production.md).
- Narrowed Coach Fred's private conversation scene admission and release range while preserving his NPC spawn lifecycle. Cold-load behavior remains pending. See [FS1](docs/fred_scene_fs1.md).
- Reproduced and repaired the enhanced Skeleton implant preservation failure during Tower setup. Both reported implants passed the local reproduction after CF1 installation. See [CF1](docs/cyberware_cf1.md).

### Housing, reload, and dependencies

- Replaced H10's automatic purchase offer with explicit native Buy/Not now choices. Repaired paid-apartment service admission and a history-snapshot JSON export crash on reload. The user's H10 purchase, interactions, and save/reload passed one fixture; broader coverage remains open. See [H5](docs/h10_h5.md) and [H6/HS2](docs/h10_h6_snapshot_reload_hs2.md).
- Updated RED4ext, Codeware, ArchiveXL, TweakXL, and Mod Settings to the checked Patch 2.5 stack, retaining the required small Codeware script correction. EquipmentEX 1.2.10 was installed separately. Restored the UV mapping and VTK head files after isolation tests. See [framework updates](docs/core_updates_20261025.md) and [UV/VTK restoration](docs/uv_vtk_restore_20261025.md).

### Packaging and project name

- Combined the installed alpha and later local fixes into one ZIP with 51 game files in place of 127: one archive, one ArchiveXL file, 46 REDscript files, two CET entries, and one TweakXL file. All old files are recoverable; offline equivalence, full script compilation, install/rollback fixtures, installed hashes, and 289 unchanged save files were checked. Gameplay acceptance of the combined layout is pending. See [consolidation record](docs/full_consolidation_v1.md).
- Confirmed the official name **Post Tower Continuation and Free Roam** and updated the repository name and public documentation. Legacy `PTFR`, `TowerContinuation`, and `TowerContinued` identifiers remain for compatibility.

## v0.1.1-alpha.20261024 — 24 October 2026

Last published alpha test. See its [release notes](release/NOTES-v0.1.1-alpha.20261024.md) and [installation instructions](release/INSTALL-v0.1.1-alpha.20261024.md).
