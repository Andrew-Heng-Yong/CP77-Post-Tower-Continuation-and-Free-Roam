# PTFR SR1 consolidated local install

25 October 2026 (Toronto local date). The user authorized the production-layout local install. This was an update for an existing PTFR installation, not a standalone full-mod release or a public upload. The later [full consolidation](full_consolidation_v1.md) now includes this repair; the original three-file layout below is retained as a historical install record.

## Footprint

The repair replaced exactly three existing files, with **zero new installed files**:

1. `archive/pc/mod/00000000_TowerContinued_SideJobs_S29.archive`
2. `archive/pc/mod/00000000_TowerContinued_SideJobs_S29.archive.xl`
3. `r6/scripts/TowerContinued_SideJobs_S29/SideJobsS29.reds`

The 194 original S29 archive members were preserved except for nine intentional replacements; five new resources were folded into the same archive, for 199 members total. The existing ArchiveXL quest registration was preserved verbatim and one English lipmap registration appended. The S29 script was replaced with the tested repair version. No separate SR1 overlay archive or script remains in the game folder.

The old three files are retained under `prealpha/sidejob_repair_sr1/production_01/archived_previous` and in the verified rollback backup `recovery/sidejob_repair_sr1_production_01`. Historical development overlays remain in `candidate_02` inside the workspace only. Future debug releases should rebuild these same three paths, preserve the prior version outside the game folder, and publish one versioned update ZIP. When only archive resources change, a future update can replace just the archive; script or ArchiveXL changes require their respective files too.

## Validation and installation

All 199 packed archive members matched the expected source bytes on readback. The ArchiveXL file was checked as the original text plus exactly one registration. The S29 script matches the previously compiled 94-source REDscript proof. A 17-action production installer fixture passed normal install/verify/rollback and interrupted rollback after each of the three replacement steps. Read-only preflight reported `READY`.

The real installer returned `SR1_PRODUCTION_INSTALLED_LIVE_PENDING`. Subsequent `Verify` returned `VERIFIED`, and `ValidateRollback` returned `ROLLBACK_READY`. The installed hashes are archive `C6E962CC336C2BA9AD93A1CC0C73B2894483657BC2C6B430CCCB1A711D2CCE41`, ArchiveXL `5926BE9AA5E5F78230507FA5483554899595B77A812CD1A4CE3ADF74B75903AB`, script `D1CDF5F27B1C2625581A6CE9A58D90965BFEF94D2E1105651B7400EA364565CB`. No game launch, save edit or manual fact write was performed. Gameplay remains live pending.

The single [update ZIP](../prealpha/sidejob_repair_sr1/production_01/dist/PTFR-SR1-existing-install-three-file-update.zip) contains exactly these three paths and passed readback. It is an **existing-install update only** and has not been published. [Build proof](../prealpha/sidejob_repair_sr1/production_01/build_01.json) · [install manifest](../prealpha/sidejob_repair_sr1/production_01/install_manifest_01.json) · [installer fixture proof](../prealpha/sidejob_repair_sr1/production_01/deployment_tests_01.json) · [real install receipt](../recovery/sidejob_repair_sr1_production_01/receipt.json).

To roll back the local files, close the game and run `prealpha/sidejob_repair_sr1/deploy_production_01.ps1 -Action Rollback`; the verified backup restores the previous three versions. File rollback does not undo changes already saved by the game.

## Full-mod packaging remains separate

This repair adds no installed files, but the wider modular alpha still has **71** TowerContinued/PTFR archive, ArchiveXL and REDscript files in this local installation. The existing alpha release manifest lists **117** files across all components. Those counts were not reduced by SR1. A full user-facing production release can still be delivered as one ZIP, but merging all older modules into one technical archive requires a separate load-order, duplicate-resource and save-resumption audit. Do not describe this SR1 update ZIP as the full mod.
