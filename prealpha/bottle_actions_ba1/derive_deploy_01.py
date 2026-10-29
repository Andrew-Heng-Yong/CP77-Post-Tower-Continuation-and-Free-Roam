"""Derive BA1's bounded two-file transactional deployer from tested CC1."""
from pathlib import Path
H=Path(__file__).resolve().parent
source=H.parent/'coaster_cutoff_cc1'
text=(source/'deploy_01.ps1').read_text(encoding='utf-8-sig')
for old,new in [
 ('coaster_cutoff_cc1_01','bottle_actions_ba1_01'),
 ('CC1_51_PATH_SUCCESSOR_STAGED_NOT_INSTALLED','BA1_51_PATH_SUCCESSOR_STAGED_NOT_INSTALLED'),
 ('CC1_51_PATH_INSTALLED_LIVE_PENDING','BA1_51_PATH_INSTALLED_LIVE_PENDING'),
 ('PTFRCC1_STAGE','PTFRBA1_STAGE'),
 ('$m.archive_members -ne 1185','$m.archive_members -ne 1186'),
 ("'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds'","'archive/pc/mod/zzzz_PTFR_Combined.archive.xl'")]:
    assert old in text,old
    text=text.replace(old,new)
assert 'CC1' not in text and 'SideJobsS29.reds' not in text
anchor="foreach($p in $m.proofs){if((Hash $p.path) -cne $p.sha256){throw ('Proof changed '+$p.path)}}"
assert text.count(anchor)==1
text=text.replace(anchor,anchor+"""
# New installs require the exact compiled stack and resource-winner environment.
# An unrelated mod update does not prevent restoring this package's own backup.
if(!$fixture -and $Action -in @('Validate','Install')){
 if($m.runtime_inputs.Count -ne 64 -or $m.external_archives.Count -lt 1){throw 'Runtime/winner input inventory incomplete'}
 foreach($p in @($m.runtime_inputs)+@($m.external_archives)){
  if((Hash (Safe $game $p.path)) -cne $p.sha256){throw ('Runtime/winner environment changed '+$p.path)}
 }
}
""")
target=H/'deploy_01.ps1';target.write_text(text,encoding='utf-8')
test=(source/'test_deploy_01.py').read_text(encoding='utf-8-sig')
for old,new in [('Exercise W3 replacement','Exercise BA1 replacement'),('prealpha/skippy_ambient_sc3/candidate_02/package','prealpha/coaster_cutoff_cc1/candidate_01/package')]:
    assert old in test,old
    test=test.replace(old,new)
target=H/'test_deploy_01.py';target.write_text(test,encoding='utf-8')
print('Derived BA1 two-file deployer and five-interruption fixture suite')
