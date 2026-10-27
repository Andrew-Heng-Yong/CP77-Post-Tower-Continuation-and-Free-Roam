"""Adapt the tested W3 transactional 51-file installer for SC1."""
from pathlib import Path
H=Path(__file__).resolve().parent
W=H.parents[1]
src=W/'prealpha/world_workspots_w2/deploy_w3_01.ps1'
out=H/'deploy_01.ps1'
assert not out.exists()
s=src.read_text()
replacements={
 "'candidate_04'":"'candidate_07'",
 "'recovery/world_workspots_w3_01'":"'recovery/skippy_coaster_sc1_01'",
 "'W3_51_PATH_SUCCESSOR_STAGED_NOT_INSTALLED'":"'SC1_51_PATH_SUCCESSOR_STAGED_NOT_INSTALLED'",
 "'W3_51_PATH_INSTALLED_LIVE_PENDING'":"'SC1_51_PATH_INSTALLED_LIVE_PENDING'",
 "'r6/scripts/PTFR_Consolidated/PTFR_RestorationBaseline.reds'":"'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds'",
 "'.PTFRW3_STAGE'":"'.PTFRSC1_STAGE'",
 " $m.retired_probe_paths -ne 0 -or":"",
 " -or $m.private_owners -ne 237 -or $m.spawner_ids -ne 245":"",
 " -ne 1183":" -ne 1184",
}
for old,new in replacements.items():
 assert s.count(old)==1,(old,s.count(old))
 s=s.replace(old,new)
out.write_text(s,encoding='utf-8')
print(out)
