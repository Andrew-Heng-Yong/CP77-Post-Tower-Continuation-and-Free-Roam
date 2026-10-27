"""Derive the audited SC3 transactional deployer for CC1's two replacements."""
from pathlib import Path

H=Path(__file__).resolve().parent
SC3=H.parent/'skippy_ambient_sc3'
source=(SC3/'deploy_02.ps1').read_text(encoding='utf-8-sig')
replacements=[
 ('candidate_02','candidate_01'),
 ('skippy_ambient_sc3_01','coaster_cutoff_cc1_01'),
 ('SC3_51_PATH_SUCCESSOR_STAGED_NOT_INSTALLED','CC1_51_PATH_SUCCESSOR_STAGED_NOT_INSTALLED'),
 ('SC3_51_PATH_INSTALLED_LIVE_PENDING','CC1_51_PATH_INSTALLED_LIVE_PENDING'),
 ('PTFRSC3_STAGE','PTFRCC1_STAGE'),
 ("$m.changed_paths -ne 3","$m.changed_paths -ne 2"),
 ("$changes.Count -ne 3","$changes.Count -ne 2"),
 ("'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds'","'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds'"),
 ("'archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl','r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds'","'archive/pc/mod/zzzz_PTFR_Combined.archive','r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds'"),
 ("'deployment_tests_01.json','zip_proof_01.json','save_baseline_01.json'","'deployment_tests_01.json','zip_proof_01.json','save_baseline_01.json'"),
 ("$tested.interruption_points -ne 5","$tested.interruption_points -ne 5"),
 ('AfterThirdReplace','AfterSecondReplace'),
 ('replacements=3','replacements=2'),
 ('$n -eq 1','$n -eq 1'),
]
for old,new in replacements:
    if old!=new:
        assert old in source,old
        source=source.replace(old,new)
assert 'SideJobsS23.reds' not in source
assert 'zzzz_PTFR_Combined.archive.xl' not in source
assert 'AfterThirdReplace' not in source
(H/'deploy_01.ps1').write_text(source,encoding='utf-8')
test=(SC3/'test_deploy_02.py').read_text(encoding='utf-8-sig')
for old,new in [('candidate_02','candidate_01'),('prealpha/skippy_coaster_sc2/candidate_01/package','prealpha/skippy_ambient_sc3/candidate_02/package'),('deploy_02.ps1','deploy_01.ps1'),('AfterThirdReplace','AfterSecondReplace')]:
    assert old in test,old
    test=test.replace(old,new)
(H/'test_deploy_01.py').write_text(test,encoding='utf-8')
print('Derived CC1 deployer and fixture script')
