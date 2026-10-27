from pathlib import Path
H=Path(__file__).resolve().parent
W=H.parents[1]
src=W/'prealpha/skippy_coaster_sc1/deploy_01.ps1'
out=H/'deploy_01.ps1'
assert not out.exists()
s=src.read_text()
for old,new in {
 "'candidate_07'":"'candidate_01'",
 "'recovery/skippy_coaster_sc1_01'":"'recovery/skippy_coaster_sc2_01'",
 "SC1_51_PATH_SUCCESSOR_STAGED_NOT_INSTALLED":"SC2_51_PATH_SUCCESSOR_STAGED_NOT_INSTALLED",
 "SC1_51_PATH_INSTALLED_LIVE_PENDING":"SC2_51_PATH_INSTALLED_LIVE_PENDING",
 ".PTFRSC1_STAGE":".PTFRSC2_STAGE",
 "-ne 3":"-ne 1",
 "replacements=3":"replacements=1",
 "replacements=3":"replacements=1",
 "'archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl','r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds'":"'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds'",
}.items():
 assert old in s,old
 s=s.replace(old,new)
out.write_text(s)
print(out)
