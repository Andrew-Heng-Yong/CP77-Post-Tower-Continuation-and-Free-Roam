"""Derive WA2's three-file transactional deployer from tested BA1."""
from pathlib import Path
H=Path(__file__).resolve().parent
source=H.parent/'bottle_actions_ba1'
text=(source/'deploy_01.ps1').read_text(encoding='utf-8-sig')
for old,new in [
 ('bottle_actions_ba1_01','world_actions_wa2_01'),
 ('BA1_51_PATH_SUCCESSOR_STAGED_NOT_INSTALLED','WA2_51_PATH_SUCCESSOR_STAGED_NOT_INSTALLED'),
 ('BA1_51_PATH_INSTALLED_LIVE_PENDING','WA2_51_PATH_INSTALLED_LIVE_PENDING'),
 ('PTFRBA1_STAGE','PTFRWA2_STAGE'),
 ('$m.changed_paths -ne 2','$m.changed_paths -ne 3'),
 ('$changes.Count -ne 2','$changes.Count -ne 3'),
 ('replacements=2','replacements=3'),
 ("$expected=@('archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl')","$expected=@('archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl','r6/scripts/PTFR_Consolidated/PTFR_RestorationBaseline.reds')"),
 ("'AfterFirstReplace','AfterSecondReplace','BeforeReceipt'","'AfterFirstReplace','AfterSecondReplace','AfterThirdReplace','BeforeReceipt'"),
 ("$n++;if($n -eq 1){FailAt 'AfterFirstReplace'}","$n++;if($n -eq 1){FailAt 'AfterFirstReplace'};if($n -eq 2){FailAt 'AfterSecondReplace'}"),
 (" FailAt 'AfterSecondReplace'\n"," FailAt 'AfterThirdReplace'\n"),
 ('$tested.interruption_points -ne 5','$tested.interruption_points -ne 6'),
 ('$m.archive_members -ne 1186','$m.base_archive_members -ne 1186 -or $m.archive_members -ne (1186+@($m.new_resources).Count)')]:
    assert old in text,old
    text=text.replace(old,new)
anchor="if(!$fixture -and ($m.game_root -cne $game -or $m.backup_root -cne $backup)){throw 'Manifest roots changed'}"
assert text.count(anchor)==1
text=text.replace(anchor,"""if(@($m.new_resources).Count -lt 1 -or @($m.new_resources.depot|Select-Object -Unique).Count -ne @($m.new_resources).Count){throw 'New resource cohort invalid'}
foreach($resource in $m.new_resources){if($resource.depot -notmatch '^towercontinued\\\\world_actions_wa2\\\\[a-zA-Z0-9_\\\\-]+\\.questphase$' -or $resource.sha256 -cnotmatch '^[A-F0-9]{64}$'){throw 'Unexpected new controller depot/hash'}}
"""+anchor)
assert 'BA1' not in text
(H/'deploy_01.ps1').write_text(text,encoding='utf-8')
test=(source/'test_deploy_01.py').read_text(encoding='utf-8-sig')
for old,new in [('Exercise BA1 replacement','Exercise WA2 replacement'),('prealpha/coaster_cutoff_cc1/candidate_01/package','prealpha/bottle_actions_ba1/candidate_01/package')]:
    assert old in test,old
    test=test.replace(old,new)
test=test.replace('"AfterFirstReplace", "AfterSecondReplace", "BeforeReceipt"','"AfterFirstReplace", "AfterSecondReplace", "AfterThirdReplace", "BeforeReceipt"')
test=test.replace('"interruption_points": 5','"interruption_points": 6')
(H/'test_deploy_01.py').write_text(test,encoding='utf-8')
print('Derived WA2 three-file deployer and six-interruption fixture suite')
