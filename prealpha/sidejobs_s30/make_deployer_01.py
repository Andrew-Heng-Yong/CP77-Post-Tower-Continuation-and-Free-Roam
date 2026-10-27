"""Derive the pinned three-file successor updater from the tested SR1 updater."""
from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parent.parent
source=(W/'prealpha/sidejob_repair_sr1/deploy_production_01.ps1').read_text(encoding='utf-8-sig')
substitutions={
 "Join-Path $PSScriptRoot 'production_01'":"Join-Path $PSScriptRoot 'candidate_01'",
 "recovery/sidejob_repair_sr1_production_01":"recovery/sidejobs_s30_01",
 "THREE_FILE_PRODUCTION_STAGED_NOT_INSTALLED":"THREE_FILE_CONSOLIDATED_SUCCESSOR_STAGED_NOT_INSTALLED",
 "archive/pc/mod/00000000_TowerContinued_SideJobs_S29.archive'":"archive/pc/mod/zzzz_PTFR_Combined.archive'",
 "archive/pc/mod/00000000_TowerContinued_SideJobs_S29.archive.xl'":"archive/pc/mod/zzzz_PTFR_Combined.archive.xl'",
 "r6/scripts/TowerContinued_SideJobs_S29/SideJobsS29.reds'":"r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds'",
 "SR1_PRODUCTION_INSTALLED_LIVE_PENDING":"S30_CONSOLIDATED_INSTALLED_LIVE_PENDING",
}
for old,new in substitutions.items():
 assert source.count(old)==1,(old,source.count(old))
 source=source.replace(old,new)
out=H/'deploy_01.ps1';assert not out.exists()
out.write_text(source,encoding='utf-8')
print(out)
