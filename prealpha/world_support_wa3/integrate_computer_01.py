"""Add the separately staged CO1 compatibility component to one WA3 transaction."""
from pathlib import Path
H=Path(__file__).resolve().parent
def edit(name, replacements):
    p=H/name;s=p.read_text(encoding='utf-8-sig')
    for before,after in replacements:
        assert before in s,(name,before)
        s=s.replace(before,after)
    p.write_text(s,encoding='utf-8',newline='\n')

edit('package_01.py',[
("# Validate the actual fresh compile and its one permitted script replacement.","""# CO1 is a separate existing-path compatibility component, not part of the Tower ZIP.
co1=W/'prealpha/computer_overlay_co1/candidate_02'
compat_rel='r6/scripts/virtual-atelier-full/SetupNewTab.reds'
compat_source=co1/'SetupNewTab.reds'
compat_original=co1/'original/SetupNewTab.reds'
assert digest(compat_original)=='14B651576CC6D1FCEDBC11A48A96D1A2AC79DD84FCCFB90097F4169057378F80'
assert digest(compat_source)=='5743CDCD6F8CD46A58F9642002F75EBCA25D84BE340856C2E6D85B15DAD973F8'
assert digest(G/compat_rel)==digest(compat_original),'CO1 installed baseline drift'
compatibility=[{'component':'CO1','path':compat_rel,'source':str(compat_source),'original':str(compat_original),'before':digest(compat_original),'after':digest(compat_source)}]
# Validate the actual fresh compile and both exact script replacements."""),
("expected=digest(P/baseline_rel) if key=='game/PTFR_Consolidated/PTFR_RestorationBaseline.reds' else h","expected=digest(P/baseline_rel) if key=='game/PTFR_Consolidated/PTFR_RestorationBaseline.reds' else digest(compat_source) if key=='game/virtual-atelier-full/SetupNewTab.reds' else h"),
("'changed_script':baseline_rel", "'changed_scripts':[baseline_rel,compat_rel]"),
("proofs.extend(Path(p).resolve() for p in args.proof)","proofs.extend([compat_source,compat_original,H/'integrate_computer_01.py'])\nproofs.extend(Path(p).resolve() for p in args.proof)"),
("'full_package_count':51,'changed_paths':3", "'full_package_count':51,'changed_paths':3,'compatibility_files':compatibility,'combined_path_count':52,'combined_changed_paths':4"),
])

edit('deploy_01.ps1',[
("'AfterThirdReplace','BeforeReceipt'", "'AfterThirdReplace','AfterFourthReplace','BeforeReceipt'"),
("$changes=@($m.package_files|Where-Object", """if($m.combined_path_count -ne 52 -or $m.combined_changed_paths -ne 4 -or @($m.compatibility_files).Count -ne 1){throw 'Combined scope changed'}
$co=$m.compatibility_files[0]
if($co.component -cne 'CO1' -or $co.path -cne 'r6/scripts/virtual-atelier-full/SetupNewTab.reds' -or $co.before -cne '14B651576CC6D1FCEDBC11A48A96D1A2AC79DD84FCCFB90097F4169057378F80' -or $co.after -cne '5743CDCD6F8CD46A58F9642002F75EBCA25D84BE340856C2E6D85B15DAD973F8'){throw 'Compatibility scope changed'}
if((Hash $co.source) -cne $co.after -or (Hash $co.original) -cne $co.before){throw 'Compatibility source changed'}
$managed=@($m.package_files)+@($m.compatibility_files)
function CandidateSource([string]$rel){if($rel -ceq $co.path){return $co.source};return Safe (Join-Path $candidate 'package') $rel}
$changes=@($m.package_files|Where-Object"""),
("if(@($m.package_files.path|Select-Object -Unique).Count -ne 51)","$changes+=@($m.compatibility_files)\nif(@($managed.path|Select-Object -Unique).Count -ne 52)"),
("foreach($f in $m.package_files)","foreach($f in $managed)"),
("(Safe (Join-Path $candidate 'package') $f.path)","(CandidateSource $f.path)"),
("$tested.interruption_points -ne 6", "$tested.interruption_points -ne 7"),
("package_files=51;replacements=3", "package_files=51;compatibility_files=1;replacements=4"),
("replacements=3", "replacements=4"),
("restored_production=51", "restored_production=52"),
("production_paths=51", "production_paths=52"),
("$n++;if($n -eq 1){FailAt 'AfterFirstReplace'};if($n -eq 2){FailAt 'AfterSecondReplace'}", "$n++;if($n -eq 1){FailAt 'AfterFirstReplace'};if($n -eq 2){FailAt 'AfterSecondReplace'};if($n -eq 3){FailAt 'AfterThirdReplace'};if($n -eq 4){FailAt 'AfterFourthReplace'}"),
(" FailAt 'AfterThirdReplace'\n", ""),
("WA3_51_PATH_INSTALLED_LIVE_PENDING", "WA3_CO1_COMBINED_INSTALLED_LIVE_PENDING"),
])

edit('test_deploy_01.py',[
("for f in M[\"package_files\"]", "for f in M[\"package_files\"]+M['compatibility_files']"),
("src = OLD / f[\"path\"]", "src = Path(f['original']) if f.get('component')=='CO1' else OLD / f[\"path\"]"),
("\"AfterThirdReplace\", \"BeforeReceipt\"", "\"AfterThirdReplace\", \"AfterFourthReplace\", \"BeforeReceipt\""),
("\"interruption_points\": 6", "\"interruption_points\": 7"),
])
edit('capture_save_baseline_01.py',[
("f['fixture_actions']==23 and f['interruption_points']==6", "f['fixture_actions']==26 and f['interruption_points']==7"),
])
print('Combined transaction tooling updated; no game files changed.')
