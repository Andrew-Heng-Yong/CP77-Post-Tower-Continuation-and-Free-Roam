from pathlib import Path
W=Path(__file__).resolve().parents[2]
R=W/'prealpha/credits_cover_lc4'
s=(W/'prealpha/world_support_wa3/deploy_02.ps1').read_text(encoding='utf-8-sig')
s=s.replace("$backup=Join-Path $ws 'recovery/world_support_wa3_02'","$backup=Join-Path $ws 'recovery/credits_cover_lc4_01'")
s=s.replace('.PTFRWA3_STAGE','.PTFRLC4_STAGE')
start=s.index('$manifestHash=')
end=s.index("$receipt=Safe $backup 'receipt.json'")
generic=r'''$manifestHash=(Get-Content -LiteralPath ($manifest+'.sha256') -Raw).Trim()
if((Hash $manifest) -cne $manifestHash){throw 'Manifest changed'}
$m=Get-Content -LiteralPath $manifest -Raw|ConvertFrom-Json -Depth 80
if($m.status -cne 'LC4_FULL_51_PATH_SUCCESSOR_STAGED' -or $m.package_files.Count -ne 51 -or $m.managed_paths -ne 52 -or $m.changed_paths -ne 1 -or $m.archive_members -ne 1563){throw 'Manifest scope changed'}
if(!$fixture -and ($m.game_root -cne $game -or $m.backup_root -cne $backup)){throw 'Manifest root changed'}
$co=$m.compatibility_files[0]
if($m.compatibility_files.Count -ne 1 -or $co.path -cne 'r6/scripts/virtual-atelier-full/SetupNewTab.reds' -or $co.before -cne $co.after){throw 'Compatibility path changed'}
$managed=@($m.package_files)+@($m.compatibility_files)
$changes=@($m.package_files|Where-Object {$_.before -cne $_.after})
if($changes.Count -ne 1 -or $changes[0].path -cne 'archive/pc/mod/zzzz_PTFR_Combined.archive' -or @($managed.path|Select-Object -Unique).Count -ne 52){throw 'Unexpected replacement set'}
function CandidateSource([string]$rel){if($rel -ceq $co.path){return $co.source};return Safe (Join-Path $candidate 'package') $rel}
foreach($f in $managed){
 [void](Safe $game $f.path);[void](CandidateSource $f.path)
 if((Hash (CandidateSource $f.path)) -cne $f.after){throw ('Candidate file changed '+$f.path)}
}
foreach($p in $m.proofs){if((Hash $p.path) -cne $p.sha256){throw ('Proof changed '+$p.path)}}
if(!$fixture -and $Action -in @('Validate','Install')){
 $sourceRoots=@('r6/scripts','red4ext/plugins/Codeware/Scripts','red4ext/plugins/ArchiveXL/Scripts','red4ext/plugins/TweakXL/Scripts','red4ext/plugins/mod_settings')
 $paths=@(foreach($root in $sourceRoots){Get-ChildItem -LiteralPath (Safe $game $root) -Filter '*.reds' -Recurse -File|ForEach-Object {[IO.Path]::GetRelativePath($game,$_.FullName).Replace('\','/')}})
 if(@(Compare-Object @($paths|Sort-Object) @($m.runtime_inputs.path|Sort-Object)).Count){throw 'Compiler source inventory changed'}
 foreach($p in $m.runtime_inputs){if((Hash (Safe $game $p.path)) -cne $p.sha256){throw ('Compiler source changed '+$p.path)}}
 $archives=@(Get-ChildItem -LiteralPath (Safe $game 'archive/pc') -Filter '*.archive' -Recurse -File|ForEach-Object {[IO.Path]::GetRelativePath($game,$_.FullName).Replace('\','/')}|Sort-Object)
 $expected=@(@($m.external_archives.path)+@('archive/pc/mod/zzzz_PTFR_Combined.archive')|Sort-Object)
 if(@(Compare-Object $archives $expected).Count){throw 'Archive inventory changed'}
 foreach($p in $m.external_archives){if((Hash (Safe $game $p.path)) -cne $p.sha256){throw ('External archive changed '+$p.path)}}
 $zip=Get-Content -LiteralPath (Join-Path $candidate 'zip_proof_01.json') -Raw|ConvertFrom-Json
 if($zip.status -cne 'FULL_51_PATH_ZIP_READBACK_PASS' -or $zip.members -ne 51 -or (Hash $zip.path) -cne $zip.sha256){throw 'Full ZIP proof invalid'}
}
'''
s=s[:start]+generic+s[end:]
s=s.replace("@{status='VERIFIED';package_files=51;compatibility_files=1;replacements=4}","@{status='VERIFIED';package_files=51;compatibility_files=1;replacements=1}")
s=s.replace("@{status='ROLLBACK_READY';replacements=4;save_undo=$false}","@{status='ROLLBACK_READY';replacements=1;save_undo=$false}")
s=s.replace("@{status='READY';production_paths=52;replacements=4}","@{status='READY';production_paths=52;replacements=1}")
s=s.replace("replacements=4;game_launched", "replacements=1;game_launched")
s=s.replace("$r.status='WA3_CO1_COMBINED_INSTALLED_LIVE_PENDING'", "$r.status='LC4_INSTALLED_LIVE_PENDING'")
s=s.replace("@{status=$r.status;production_paths=52;replacements=4;backup=$backup}","@{status=$r.status;production_paths=52;replacements=1;backup=$backup}")
s=s.replace("@{status='ROLLED_BACK';restored_production=52;save_undo=$false}","@{status='ROLLED_BACK';restored_production=52;replacements=1;save_undo=$false}")
assert "WA3_CO1_COMBINED_INSTALLED" not in s
(R/'deploy_01.ps1').write_text(s,encoding='utf-8')
print('Generated guarded one-replacement installer',len(s.splitlines()),'lines')
