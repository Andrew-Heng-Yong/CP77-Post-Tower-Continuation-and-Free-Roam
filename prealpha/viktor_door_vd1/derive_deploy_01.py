from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parents[1]
s=(W/'prealpha/credits_cover_lc4/deploy_01.ps1').read_text(encoding='utf-8-sig')
s=s.replace('recovery/credits_cover_lc4_01','recovery/viktor_door_vd1_01').replace('LC4_','VD1_').replace('PTFRLC4_STAGE','PTFRVD1_STAGE')
s=s.replace('$m.changed_paths -ne 1','$m.changed_paths -ne 2').replace('$m.archive_members -ne 1563','$m.archive_members -ne 1564')
s=s.replace("$changes.Count -ne 1 -or $changes[0].path -cne 'archive/pc/mod/zzzz_PTFR_Combined.archive'", "$changes.Count -ne 2 -or @($changes.path | Where-Object {$_ -cnotin @('archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl')}).Count")
s=s.replace('replacements=1','replacements=2')
assert 'LC4' not in s and 'changed_paths -ne 2' in s
(H/'deploy_01.ps1').write_text(s,encoding='utf-8')
t=(W/'prealpha/credits_cover_lc4/test_deploy_02.py').read_text()
t=t.replace('prealpha/credits_cover_lc4','prealpha/viktor_door_vd1')
t=t.replace("('replace','AfterFirstReplace'),","('replace','AfterFirstReplace'),('second','AfterSecondReplace'),")
t=t.replace('interrupted=4','interrupted=5')
(H/'test_deploy_01.py').write_text(t,encoding='utf-8')
print('Derived guarded two-file installer and six deployment fixtures')
