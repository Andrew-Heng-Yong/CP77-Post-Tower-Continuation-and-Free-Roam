param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$AuditDirectory='',
 [ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall'
)
# Exactly two backed-up replacements plus one reversible addition.
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$sourceAudit=Join-Path $workspace 'research\afterlife_world\interactions_r8'
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$sourceAudit}
New-Item -ItemType Directory -Force $audit|Out-Null
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$scope=@('archive/pc/mod/TowerContinued_AfterlifeR1.archive','archive/pc/mod/TowerContinued_AfterlifeR1.archive.xl','r6/scripts/PTFR_Afterlife_Interactions_R8/AfterlifeInteractionsR8.reds')
$rollback=$Mode -in @('ValidateRollback','Rollback')
if($rollback){
 $receipt=Get-Content -LiteralPath (Join-Path $audit 'install_receipt.json') -Raw|ConvertFrom-Json -Depth 15
 if($receipt.status -ne 'INSTALLED_AFTERLIFE_INTERACTIONS_R8_LIVE_PENDING'){throw 'Unexpected receipt'}
 if($game -ne $receipt.game_root){throw 'Game root differs from receipt'}
 $files=@($receipt.files)
}else{
 $tests=Get-Content -LiteralPath (Join-Path $sourceAudit 'tests.json') -Raw|ConvertFrom-Json
 if($tests.status -ne 'PASS_R8_OFFLINE_NOT_INSTALLED_NOT_LIVE' -or -not $tests.packed_readback -or -not $tests.redscript_compile){throw 'Offline pass missing'}
 R5Match (Join-Path $sourceAudit 'manifest.json') $tests.manifest_sha256
 R5Match (Join-Path $workspace 'tools\build_afterlife_interactions_r8.ps1') $tests.builder_sha256
 R5Match (Join-Path $workspace 'tools\test_afterlife_interactions_r8.py') $tests.validator_sha256
 if(-not $AuditDirectory -and $Mode -eq 'Install'){
  $fixture=Get-Content -LiteralPath (Join-Path $sourceAudit 'deployment_tests.json') -Raw|ConvertFrom-Json
  if($fixture.status -ne 'PASS_R8_WORKSPACE_INSTALL_ROLLBACK'){throw 'Deployment fixture missing'}
  R5Match $PSCommandPath $fixture.deployment_sha256
  R5Match (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1') $fixture.helpers_sha256
  R5Match (Join-Path $sourceAudit 'tests.json') $fixture.tests_sha256
 }
 $files=@($tests.files)
}
if($files.Count -ne 3 -or @(Compare-Object $scope @($files.relative)).Count){throw 'Deployment scope mismatch'}
if(@($files|Where-Object before_sha256).Count -ne 2){throw 'Expected two replacements and one addition'}
if(-not (Test-Path -LiteralPath (Join-Path $game 'r6\cache\final.redscripts') -PathType Leaf)){throw 'Unexpected game root'}
R5Closed
$prior=[ordered]@{}
foreach($name in @('install_receipt.json','population_r2\install_receipt.json','idles_r3\install_receipt.json','faces_r5\install_receipt.json','booth_r6\install_receipt.json','emmerick_r7\install_receipt.json')){
 $old=Get-Content -LiteralPath (Join-Path $workspace ('research\afterlife_world\'+$name)) -Raw|ConvertFrom-Json
 foreach($file in $old.files){$prior[$file.relative.Replace('\','/')]=$file.sha256}
}
foreach($p in $prior.Keys){if($rollback -and $p -in $scope){continue};R5Match (R5Within (Join-Path $game $p) $game) $prior[$p]}
$payloads=@($files|ForEach-Object {
 $target=R5Within (Join-Path $game $_.relative) $game
 if($rollback){
  R5Match $target $_.sha256
  $source=if($_.before_sha256){R5Within $_.backup $workspace}else{''}
  if($source){R5Match $source $_.before_sha256}
 }else{
  $source=R5Within (Join-Path $workspace $_.source) $workspace;R5Match $source $_.sha256
  if($_.before_sha256){R5Match $target $_.before_sha256}elseif(Test-Path -LiteralPath $target){throw "Addition already exists: $target"}
 }
 @{relative=$_.relative;target=$target;source=$source;before_sha256=$_.before_sha256;sha256=$_.sha256;backup=''}
})
$protected=R5Snapshot $game @($payloads.target)
R5Unchanged $protected;R5Closed
if($Mode -like 'Validate*'){
 $result=@{status=('R8_'+$Mode.ToUpper()+'_ONLY');replacements=2;additions=1;protected_files=$protected.Count;game_unchanged=$true}
 R5Json (Join-Path $audit ($Mode+'.json')) $result;$result|ConvertTo-Json;return
}
if(-not $rollback -and (Test-Path -LiteralPath (Join-Path $audit 'install_receipt.json'))){throw 'Receipt already exists'}
if($rollback -and (Test-Path -LiteralPath (Join-Path $audit 'rollback_receipt.json'))){throw 'Already rolled back'}
$backup=R5Within (Join-Path $audit ('backup_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $workspace
# Back up every existing target before the first mutation. Rollback also keeps
# the R8 payloads, so the added script is recoverable rather than deleted.
foreach($file in $payloads){
 if(-not $rollback -and -not $file.before_sha256){continue}
 R5Closed;R5Match $file.target $(if($rollback){$file.sha256}else{$file.before_sha256})
 $file.backup=R5Within (Join-Path $backup $file.relative) $backup
 New-Item -ItemType Directory -Force (Split-Path $file.backup)|Out-Null
 [IO.File]::Copy($file.target,$file.backup,$false)
 R5Match $file.backup $(if($rollback){$file.sha256}else{$file.before_sha256})
}
$written=[Collections.Generic.List[object]]::new()
try{
 foreach($file in $payloads){
  R5Closed
  if($rollback){
   R5Match $file.target $file.sha256
   if($file.before_sha256){R5Match $file.source $file.before_sha256;[IO.File]::Copy($file.source,$file.target,$true)}
   else {
    # One validated leaf only; preserve it under the rollback directory.
    $file.recovered=R5Within (Join-Path $backup ('removed\'+$file.relative)) $backup
    New-Item -ItemType Directory -Force (Split-Path $file.recovered)|Out-Null
    Move-Item -LiteralPath $file.target -Destination $file.recovered
   }
  }else{
   if($file.before_sha256){R5Match $file.target $file.before_sha256}elseif(Test-Path -LiteralPath $file.target){throw 'Addition appeared during deployment'}
   R5Match $file.source $file.sha256
   New-Item -ItemType Directory -Force (Split-Path $file.target)|Out-Null
   [IO.File]::Copy($file.source,$file.target,[bool]$file.before_sha256)
  }
  $written.Add($file)
  if($rollback -and -not $file.before_sha256){if(Test-Path -LiteralPath $file.target){throw 'Addition remains after rollback'}}
  else{R5Match $file.target $(if($rollback){$file.before_sha256}else{$file.sha256})}
 }
 R5Closed;R5Unchanged $protected
 $result=[ordered]@{status=$(if($rollback){'ROLLED_BACK_AFTERLIFE_INTERACTIONS_R8'}else{'INSTALLED_AFTERLIFE_INTERACTIONS_R8_LIVE_PENDING'});utc=[DateTime]::UtcNow.ToString('o');game_root=$game;replacements=2;additions=1;protected_files=$protected.Count;protected_hashes=$protected;files=@($payloads|ForEach-Object {@{relative=$_.relative;sha256=$_.sha256;before_sha256=$_.before_sha256;backup=$_.backup}});game_closed=$true;live_tested=$false;save_writes=0;story_writes=0}
 R5Json (Join-Path $audit $(if($rollback){'rollback_receipt.json'}else{'install_receipt.json'})) $result
 [pscustomobject]$result|Select-Object status,utc,replacements,additions,protected_files|ConvertTo-Json
}catch{
 $failure=$_.Exception.Message;$recovery=[Collections.Generic.List[string]]::new()
 foreach($file in $written){try{
  R5Closed
  if($rollback){R5Match $file.backup $file.sha256;[IO.File]::Copy($file.backup,$file.target,$true);R5Match $file.target $file.sha256}
  elseif($file.before_sha256){R5Match $file.target $file.sha256;R5Match $file.backup $file.before_sha256;[IO.File]::Copy($file.backup,$file.target,$true);R5Match $file.target $file.before_sha256}
  else{R5Match $file.target $file.sha256;$dest=R5Within (Join-Path $backup ('failed_addition\'+$file.relative)) $backup;New-Item -ItemType Directory -Force (Split-Path $dest)|Out-Null;Move-Item -LiteralPath $file.target -Destination $dest}
 }catch{$recovery.Add($_.Exception.Message)}}
 R5Json (Join-Path $audit 'deployment_failure.json') @{failure=$failure;backups=$backup;recovery_errors=@($recovery)}
 throw $failure
}
