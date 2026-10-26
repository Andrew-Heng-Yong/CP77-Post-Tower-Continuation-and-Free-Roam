# Change log

## Unreleased — after v0.1.1-alpha.20261024

These changes are in the local development installation. **No new GitHub Release has been published.** On 26 October, the user reported that the combined mod runs with untouched public Codeware 1.21.1 and that the previous fixes they tested worked. The exact quest branches exercised were not itemized; full fresh-transition and restored-quest coverage remain open.

### Restored content and repairs

- Added native entry adapters for the remaining 18 selected side jobs. The implemented entry inventory now covers 80/80 selected gigs and 78/78 selected side jobs. Follow-up trees, rewards, map timing, and save/reload need gameplay testing. See [S29 playtest notes](docs/sidejobs_s29_playtest.md).
- Repaired Judy's private apartment door lock and the missing Dennis holocall setup for *Big in Japan*. The user reports previous fixes working in the combined test; detailed Judy/Dennis route evidence was not provided. See [JD1](docs/judy_dennis_jd1.md).
- Repaired side-job scene and owner details found in the vanilla comparison: Johnny cigarette and smoke routes, English lipmap registration for 44 private scenes, Yoko's component choices, Zane's shop return, Delamain phone ownership and sequel admission, *Where Eagles Dare* completion, and one orphaned *Sinnerman* ember. The three-file SR1 repair was installed, then folded into the consolidated package. The user reports previous fixes working; exhaustive scene-by-scene coverage remains open. See [SR1](docs/sidejob_repair_sr1_production.md).
- Narrowed Coach Fred's private conversation scene admission and release range while preserving his NPC spawn lifecycle. The user reports previous fixes working; a Fred-specific cold-load trace remains pending. See [FS1](docs/fred_scene_fs1.md).
- Reproduced and repaired the enhanced Skeleton implant preservation failure during Tower setup. Both reported implants passed the local reproduction after CF1 installation. See [CF1](docs/cyberware_cf1.md).

### Housing, reload, and dependencies

- Replaced H10's automatic purchase offer with explicit native Buy/Not now choices. Repaired paid-apartment service admission and a history-snapshot JSON export crash on reload. The user's H10 purchase, interactions, and save/reload passed one fixture; broader coverage remains open. See [H5](docs/h10_h5.md) and [H6/HS2](docs/h10_h6_snapshot_reload_hs2.md).
- Updated RED4ext, Codeware, ArchiveXL, TweakXL, and Mod Settings to the checked Patch 2.5 stack. An isolated compile confirmed PTFR builds with untouched public Codeware 1.21.1, which is installed locally with all nine files matching the official ZIP. The user then reported a successful live run with that public package. See [framework follow-up](docs/core_updates_20261025.md).

### Packaging and project name

- Combined the installed alpha and later local fixes into one ZIP with 51 game files in place of 127: one archive, one ArchiveXL file, 46 REDscript files, two CET entries, and one TweakXL file. All old files are recoverable; offline equivalence, full script compilation, install/rollback fixtures, installed hashes, and 289 unchanged save files were checked. The user reports the combined mod and previous fixes working with public Codeware; full quest coverage remains pending. See [consolidation record](docs/full_consolidation_v1.md).
- Documented the production update rule: subsequent fixes replace affected files in a complete consolidated package, with previous versions kept for debugging and rollback. A new installed file requires a distinct engine resource or script module.
- Confirmed the official name **Post Tower Continuation and Free Roam** and updated the repository name and public documentation. Legacy `PTFR`, `TowerContinuation`, and `TowerContinued` identifiers remain for compatibility.

## v0.1.1-alpha.20261024 — 24 October 2026

Last published alpha test. See its [release notes](release/NOTES-v0.1.1-alpha.20261024.md) and [installation instructions](release/INSTALL-v0.1.1-alpha.20261024.md).
