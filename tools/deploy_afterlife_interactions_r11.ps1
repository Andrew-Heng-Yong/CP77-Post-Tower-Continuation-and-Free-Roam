param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$AuditDirectory='',
 [ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall'
)
# Three exact replacements. Safe fallback keeps retired faces/dancers and
# substitutes the R10 quarantined interaction resources, never R8 or R9.
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$sourceAudit=Join-Path $workspace 'research\afterlife_world\interactions_r11'
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$sourceAudit}
New-Item -ItemType Directory -Force $audit|Out-Null
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$archive='archive/pc/mod/TowerContinued_AfterlifeR1.archive'
$driver='r6/scripts/PTFR_Afterlife_Interactions_R8/AfterlifeInteractionsR8.reds'
$faces='r6/scripts/PTFR_Afterlife_Faces_R5/AfterlifeFacesR5.reds'
$scope=@($archive,$driver,$faces)
$safeScope=@($archive,$driver)
$rollback=$Mode -in @('ValidateRollback','Rollback')
$testsPath=Join-Path $sourceAudit 'tests.json'
$tests=Get-Content -LiteralPath $testsPath -Raw|ConvertFrom-Json
if($tests.status -ne 'PASS_R11_OFFLINE_LIVE_PENDING' -or -not $tests.packed_readback -or
 -not $tests.redscript_compile -or -not $tests.faces_retired -or -not $tests.dancers_retired){throw 'R11 offline regression pass missing'}
$manifestPath=Join-Path $sourceAudit 'manifest.json'
R5Match $manifestPath $tests.manifest_sha256
$manifest=Get-Content -LiteralPath $manifestPath -Raw|ConvertFrom-Json
if(-not $manifest.safe_rollback_preserves_dancer_retirement){throw 'Fallback dancer-retirement proof missing'}
if(-not @($tests.checked_sources.PSObject.Properties).Count){throw 'Checked source hashes missing'}
foreach($checked in $tests.checked_sources.PSObject.Properties){
 if([IO.Path]::IsPathRooted($checked.Name)){throw 'Checked source path must be workspace relative'}
 R5Match (R5Within (Join-Path $workspace $checked.Name) $workspace) $checked.Value
}
$files=@($tests.files)
if($files.Count -ne 3 -or @(Compare-Object $scope @($files.relative)).Count -or @($files|Where-Object before_sha256).Count -ne 3){throw 'R11 replacement scope mismatch'}
$safe=@($tests.safe_rollback)
if($safe.Count -ne 2 -or @(Compare-Object $safeScope @($safe.relative)).Count -or @($safe|Where-Object sha256).Count -ne 2){throw 'R11 safe fallback scope mismatch'}
$manifestSafe=@($manifest.safe_rollback)
if($manifestSafe.Count -ne 2 -or @(Compare-Object $safeScope @($manifestSafe.relative)).Count){throw 'Manifest safe fallback scope mismatch'}
foreach($file in $safe){
 $declared=@($manifestSafe|Where-Object relative -eq $file.relative)[0]
 if($declared.sha256 -ne $file.sha256 -or $declared.source -ne $file.source){throw 'Safe fallback differs from tested manifest'}
 if($file.relative -eq $archive -and ($file.sha256 -ne $manifest.safe_archive_sha256 -or $file.source -ne $manifest.safe_archive)){throw 'Safe archive manifest mismatch'}
 if($file.relative -eq $driver -and ($file.sha256 -ne $manifest.safe_driver_sha256 -or $file.source -ne $manifest.safe_driver)){throw 'Safe runtime manifest mismatch'}
 $from=R5Within $(if([IO.Path]::IsPathRooted($file.source)){$file.source}else{Join-Path $workspace $file.source}) $workspace
 R5Match $from $file.sha256
}
if(-not (Test-Path -LiteralPath (Join-Path $game 'r6\cache\final.redscripts') -PathType Leaf)){throw 'Unexpected game root'}
R5Closed
$prior=[ordered]@{}
$historicUnsafe=@()
foreach($name in @('install_receipt.json','population_r2\install_receipt.json','idles_r3\install_receipt.json','faces_r5\install_receipt.json','booth_r6\install_receipt.json','emmerick_r7\install_receipt.json','interactions_r8\install_receipt.json','interactions_r9\install_receipt.json','interactions_r10\install_receipt.json')){
 $old=Get-Content -LiteralPath (Join-Path $workspace ('research\afterlife_world\'+$name)) -Raw|ConvertFrom-Json
 foreach($file in $old.files){
  $relative=$file.relative.Replace('\','/');$prior[$relative]=$file.sha256
  if($name -in @('interactions_r8\install_receipt.json','interactions_r9\install_receipt.json') -and $relative -in $safeScope){$historicUnsafe+=@{relative=$relative;sha256=$file.sha256}}
 }
}
foreach($file in $files){if($file.before_sha256 -ne $prior[$file.relative]){throw 'R11 predecessor hash mismatch'}}
foreach($file in $safe){
 if(@($historicUnsafe|Where-Object {$_.relative -eq $file.relative -and $_.sha256 -eq $file.sha256}).Count){throw 'Unsafe R8/R9 fallback refused'}
 if($file.relative -eq $driver -and $file.sha256 -ne $prior[$driver]){throw 'Fallback runtime is not the R10 quarantine baseline'}
 if($file.relative -eq $archive -and $file.sha256 -eq $prior[$archive]){throw 'Fallback archive must preserve the new dancer retirement'}
}
if($rollback){
 $receipt=Get-Content -LiteralPath (Join-Path $audit 'install_receipt.json') -Raw|ConvertFrom-Json -Depth 20
 if($receipt.status -ne 'INSTALLED_AFTERLIFE_INTERACTIONS_R11_LIVE_PENDING' -or $receipt.game_root -ne $game){throw 'Unexpected R11 receipt/root'}
 if(@($receipt.files).Count -ne 3 -or @(Compare-Object $scope @($receipt.files.relative)).Count){throw 'Receipt scope mismatch'}
 foreach($file in $files){
  $installed=@($receipt.files|Where-Object relative -eq $file.relative)[0]
  if($installed.sha256 -ne $file.sha256 -or $installed.before_sha256 -ne $file.before_sha256){throw 'Receipt hash mismatch'}
  $prior[$file.relative]=$file.sha256
 }
 if(@($receipt.safe_rollback).Count -ne 2 -or @(Compare-Object $safeScope @($receipt.safe_rollback.relative)).Count){throw 'Receipt fallback scope mismatch'}
 foreach($file in $safe){
  $declared=@($receipt.safe_rollback|Where-Object relative -eq $file.relative)[0]
  if($declared.source -ne $file.source -or $declared.sha256 -ne $file.sha256){throw 'Receipt fallback hash/source mismatch'}
 }
}elseif(-not $AuditDirectory -and $Mode -eq 'Install'){
 $fixture=Get-Content -LiteralPath (Join-Path $sourceAudit 'deployment_tests.json') -Raw|ConvertFrom-Json
 if($fixture.status -ne 'PASS_R11_WORKSPACE_INSTALL_SAFE_ROLLBACK' -or -not $fixture.retirements_preserved){throw 'Deployment fixture missing'}
 R5Match $PSCommandPath $fixture.deployment_sha256
 R5Match (Join-Path $PSScriptRoot 'test_afterlife_interactions_r11_deployment.ps1') $fixture.fixture_sha256
 R5Match (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1') $fixture.helpers_sha256
 R5Match $testsPath $fixture.tests_sha256
}
foreach($p in $prior.Keys){R5Match (R5Within (Join-Path $game $p) $game) $prior[$p]}
$payloads=@($(if($rollback){$safe}else{$files})|ForEach-Object {
 $target=R5Within (Join-Path $game $_.relative) $game
 $source=R5Within $(if([IO.Path]::IsPathRooted($_.source)){$_.source}else{Join-Path $workspace $_.source}) $workspace
 R5Match $source $_.sha256
 @{relative=$_.relative;target=$target;source=$source;from_sha256=$prior[$_.relative];to_sha256=$_.sha256;backup=''}
})
$protected=R5Snapshot $game @($payloads.target)
R5Unchanged $protected;R5Closed
if($Mode -like 'Validate*'){
 $result=@{status=('R11_'+$Mode.ToUpper()+'_ONLY');replacements=$(if($rollback){2}else{3});additions=0;removals=0;protected_files=$protected.Count;game_unchanged=$true;rollback_baseline='R10 quarantine with dancer retirement; retain R11 face shim';retirements_preserved=$true}
 R5Json (Join-Path $audit ($Mode+'.json')) $result;$result|ConvertTo-Json;return
}
if(-not $rollback -and (Test-Path -LiteralPath (Join-Path $audit 'install_receipt.json'))){throw 'Receipt already exists'}
if($rollback -and (Test-Path -LiteralPath (Join-Path $audit 'rollback_receipt.json'))){throw 'Already rolled back'}
$backup=R5Within (Join-Path $audit ('backup_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $workspace
foreach($file in $payloads){
 R5Closed;R5Match $file.target $file.from_sha256
 $file.backup=R5Within (Join-Path $backup $file.relative) $backup
 New-Item -ItemType Directory -Force (Split-Path $file.backup)|Out-Null
 [IO.File]::Copy($file.target,$file.backup,$false);R5Match $file.backup $file.from_sha256
}
$attempted=[Collections.Generic.List[object]]::new()
try{
 foreach($file in $payloads){
  R5Closed;R5Match $file.target $file.from_sha256;R5Match $file.source $file.to_sha256
  $attempted.Add($file)
  [IO.File]::Copy($file.source,$file.target,$true);R5Match $file.target $file.to_sha256
 }
 R5Closed;R5Unchanged $protected
 $result=[ordered]@{status=$(if($rollback){'ROLLED_BACK_AFTERLIFE_INTERACTIONS_R11_RETAINING_RETIREMENTS'}else{'INSTALLED_AFTERLIFE_INTERACTIONS_R11_LIVE_PENDING'});utc=[DateTime]::UtcNow.ToString('o');game_root=$game;replacements=$(if($rollback){2}else{3});additions=0;removals=0;protected_files=$protected.Count;protected_hashes=$protected;files=@($payloads|ForEach-Object {@{relative=$_.relative;sha256=$_.to_sha256;before_sha256=$_.from_sha256;backup=$_.backup}});safe_rollback=$safe;retained_face_path=$faces;rollback_baseline='R10 quarantine with dancer retirement; keep R11 face shim. Do not restore R8/R9.';retirements_preserved=$true;game_closed=$true;live_tested=$false;save_writes=0;story_writes=0}
 R5Json (Join-Path $audit $(if($rollback){'rollback_receipt.json'}else{'install_receipt.json'})) $result
 [pscustomobject]$result|Select-Object status,utc,replacements,additions,removals,protected_files|ConvertTo-Json
}catch{
 $failure=$_.Exception.Message;$recovery=[Collections.Generic.List[string]]::new()
 foreach($file in $attempted){try{
  R5Closed;R5Match $file.backup $file.from_sha256
  [IO.File]::Copy($file.backup,$file.target,$true);R5Match $file.target $file.from_sha256
 }catch{$recovery.Add($_.Exception.Message)}}
 R5Json (Join-Path $audit 'deployment_failure.json') @{failure=$failure;backups=$backup;recovery_errors=@($recovery);warning='Do not launch after failed deployment until recovery hashes are checked'}
 throw $failure
}
