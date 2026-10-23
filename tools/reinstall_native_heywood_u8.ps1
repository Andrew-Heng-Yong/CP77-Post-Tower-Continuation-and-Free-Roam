param([ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall')
# User-requested reinstatement of the exact withdrawn build. New receipts;
# original build, tests, installation and withdrawal evidence remain pinned.
. (Join-Path $PSScriptRoot 'shark_b7_2_helpers.ps1')
$workspace=Split-Path -Parent $PSScriptRoot
$oldRoot=Join-Path $workspace 'research/gig_restoration/native_heywood_u8'
$audit=Join-Path $workspace 'research/gig_restoration/native_heywood_u8_reinstall_1'
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$manifest=Join-Path $oldRoot 'manifest.json';$tests=Join-Path $oldRoot 'tests.json'
R5Closed
R5Match $manifest '3F749754769134EB4B5E157CB9539628C0FE60DD9B5F27C432E556C6707512D1'
R5Match $tests '23B7CCECC2EBBA259E067D00DCD2E64E51EFE2FD6CA052B22FDAA65F382CDB24'
$m=Get-Content -LiteralPath $manifest -Raw|ConvertFrom-Json
$t=Get-Content -LiteralPath $tests -Raw|ConvertFrom-Json
$oldReceipt=Get-Content -LiteralPath (Join-Path $oldRoot 'install_receipt.json') -Raw|ConvertFrom-Json
$withdrawal=Get-Content -LiteralPath (Join-Path $oldRoot 'rollback_receipt.json') -Raw|ConvertFrom-Json
$quarantine=R5Within $withdrawal.recoverable $oldRoot
if($withdrawal.status -ne 'U8_FILES_RECOVERED_NOT_WORLD' -or $oldReceipt.game_root -ne $game -or $oldReceipt.manifest_sha256 -ne (R5Hash $manifest)){throw 'Original recovery chain mismatch'}
R5Match (Join-Path $PSScriptRoot 'build_native_heywood_u8.ps1') $m.builder_sha256
R5Match (Join-Path $PSScriptRoot 'test_native_heywood_u8.py') $t.test_sha256
R5Match (Join-Path $PSScriptRoot 'deploy_native_heywood_u8.ps1') $oldReceipt.installer_sha256
$allowed=@('archive/pc/mod/TowerContinued_NativeHeywoodU8.archive','archive/pc/mod/TowerContinued_NativeHeywoodU8.archive.xl','r6/scripts/PTFR_NativeHeywoodU8/NativeHeywoodU8.reds','r6/scripts/PTFR_GigFamilyB7/GigFamilyB7.reds')
if($m.files.Count -ne 4){throw 'Unexpected file count'}
$targets=@();$sources=@()
for($i=0;$i -lt 4;$i++){
 $f=$m.files[$i];if($f.relative -cne $allowed[$i]){throw 'Unexpected target'}
 $targets+=R5Within (Join-Path $game $f.relative) $game
 $sources+=R5Within (Join-Path $quarantine $f.relative) $quarantine
 R5Match $sources[$i] $f.sha256;R5Match (R5Within (Join-Path $workspace $f.source) $workspace) $f.sha256
}
$predecessor='51AD9771C8FB0F18D1BF754CD6A2F78E9BDEE78C08AB3657680E0D22E355A87F'
R5Match (Join-Path $oldRoot 'backup/GigFamilyB7.reds') $predecessor
B71Parser|Out-Null;$xl=Get-Content -LiteralPath $sources[1] -Raw
if($xl -cne (B71Render @($m.boots)) -or $m.boots.Count -ne 24){throw 'Registration mismatch'};B71Parse $xl|Out-Null
$inventory=@(B72Inventory $game|Where-Object path -cnotin $m.boots)
foreach($depot in $m.boots){$c=B72CollisionCheck $inventory $workspace $depot;if($c.new_id -in $inventory.id){throw 'Node collision'};$inventory+=@{path=$depot;id=$c.new_id;source='U8_reinstall'}}
foreach($p in $t.dependencies.PSObject.Properties){if($p.Name -notin $targets){R5Match $p.Name $p.Value}}
foreach($name in @('native_support_u7','native_jeopardy_u4')){
 $r=Get-Content -LiteralPath (Join-Path $workspace ('research/gig_restoration/'+$name+'/install_receipt.json')) -Raw|ConvertFrom-Json
 foreach($f in $r.files){$path=Join-Path $game $f.relative;if($path -notin $targets){R5Match $path $f.sha256}}
}
$protected=R5Snapshot $game $targets
foreach($folder in @('archive/pc/mod','red4ext/plugins','r6/scripts','r6/cache')){
 foreach($p in Get-ChildItem -LiteralPath (Join-Path $game $folder) -Recurse -File){if($p.FullName -notin $targets -and ($folder -eq 'r6/cache' -or $p.Extension -in @('.archive','.xl','.reds','.dll'))){$protected[$p.FullName]=R5Hash $p.FullName}}
}
$save='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077\ManualSave-21\sav.dat'
R5Match $save '2467361DEB162C0E7955FD234FAB376A38539E57523EC808E958CEB90DBC6965';$protected[$save]=R5Hash $save
foreach($p in @($manifest,$tests,(Join-Path $oldRoot 'install_receipt.json'),(Join-Path $oldRoot 'rollback_receipt.json'))){$protected[$p]=R5Hash $p}
$rp=Join-Path $audit 'install_receipt.json';$backup=Join-Path $audit 'backup/GigFamilyB7.reds';$rr=Join-Path $audit 'rollback_receipt.json'
if($Mode -in @('ValidateRollback','Rollback')){
 $r=Get-Content -LiteralPath $rp -Raw|ConvertFrom-Json
 if($r.status -ne 'U8_REINSTALLED_EXACT_USER_REQUEST' -or $r.script_sha256 -ne (R5Hash $PSCommandPath) -or (Test-Path -LiteralPath $rr)){throw 'Reinstallation receipt mismatch or already recovered'}
 for($i=0;$i -lt 4;$i++){R5Match $targets[$i] $m.files[$i].sha256};R5Match $backup $predecessor
}else{
 if((Test-Path -LiteralPath $rp) -or (Test-Path -LiteralPath $backup)){throw 'Existing reinstall receipt/backup'}
 for($i=0;$i -lt 3;$i++){if(Test-Path -LiteralPath $targets[$i]){throw 'U8 target already exists'}};R5Match $targets[3] $predecessor
}
R5Closed
if($Mode.StartsWith('Validate')){[ordered]@{status='VALIDATED';mode=$Mode;protected=$protected.Count;exact_same_build=$true}|ConvertTo-Json;return}
if($Mode -eq 'Install'){
 New-Item -ItemType Directory -Path (Split-Path -Parent $backup) -Force|Out-Null;Copy-Item -LiteralPath $targets[3] -Destination $backup;R5Match $backup $predecessor
 foreach($i in @(3,0,1,2)){
  R5Closed;R5Match $sources[$i] $m.files[$i].sha256
  if($i -eq 3){R5Match $targets[$i] $predecessor}elseif(Test-Path -LiteralPath $targets[$i]){throw 'Addition appeared'}
  New-Item -ItemType Directory -Path (Split-Path -Parent $targets[$i]) -Force|Out-Null;Copy-Item -LiteralPath $sources[$i] -Destination $targets[$i];R5Match $targets[$i] $m.files[$i].sha256
 }
 R5Unchanged $protected
 R5Json $rp ([ordered]@{status='U8_REINSTALLED_EXACT_USER_REQUEST';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;script_sha256=R5Hash $PSCommandPath;original_manifest_sha256=R5Hash $manifest;files=$m.files;protected=$protected;additions=3;backed_up_replacements=1;game_closed=$true;direct_save_writes=0;cache_writes=0;user_requested_same_build=$true;note='User attributes earlier crashes to PC memory exhaustion and explicitly requested U8 back. No independent causal resolution or new live pass claimed.'})
 'U8_REINSTALLED_EXACT_USER_REQUEST'
}else{
 $destRoot=R5Within (Join-Path $audit ('recoverable_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $audit
 foreach($i in @(2,1,0,3)){
  R5Closed;R5Match $targets[$i] $m.files[$i].sha256;$dest=R5Within (Join-Path $destRoot $m.files[$i].relative) $destRoot
  New-Item -ItemType Directory -Path (Split-Path -Parent $dest) -Force|Out-Null;Move-Item -LiteralPath $targets[$i] -Destination $dest
  if($i -eq 3){Copy-Item -LiteralPath $backup -Destination $targets[$i];R5Match $targets[$i] $predecessor}
 }
 R5Unchanged $protected;R5Json $rr ([ordered]@{status='U8_REINSTALL_FILES_RECOVERED';recoverable=$destRoot;warning='Reload pre-U8 ManualSave-21; file recovery cannot rewind new saved owners or rewards.'});'U8_REINSTALL_FILES_RECOVERED'
}
