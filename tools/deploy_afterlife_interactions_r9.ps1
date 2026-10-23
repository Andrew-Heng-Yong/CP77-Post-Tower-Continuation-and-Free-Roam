param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$AuditDirectory='',
 [ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall'
)
# Two R9 replacements. Normal rollback goes to pre-R8, NEVER the crashing R8.
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$sourceAudit=Join-Path $workspace 'research\afterlife_world\interactions_r9'
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$sourceAudit}
New-Item -ItemType Directory -Force $audit|Out-Null
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$scope=@('archive/pc/mod/TowerContinued_AfterlifeR1.archive','r6/scripts/PTFR_Afterlife_Interactions_R8/AfterlifeInteractionsR8.reds')
$safeScope=@($scope)+@('archive/pc/mod/TowerContinued_AfterlifeR1.archive.xl')
$rollback=$Mode -in @('ValidateRollback','Rollback')
$tests=Get-Content -LiteralPath (Join-Path $sourceAudit 'tests.json') -Raw|ConvertFrom-Json
if($tests.status -ne 'PASS_R9_OFFLINE_LIVE_PENDING' -or -not $tests.packed_readback -or -not $tests.redscript_compile -or -not $tests.old_crash_layout_rejected){throw 'R9 offline regression pass missing'}
R5Match (Join-Path $sourceAudit 'manifest.json') $tests.manifest_sha256
R5Match (Join-Path $workspace 'tools\build_afterlife_interactions_r9.ps1') $tests.builder_sha256
R5Match (Join-Path $workspace 'tools\test_afterlife_interactions_r9.py') $tests.validator_sha256
R5Match (Join-Path $workspace 'tools\audit_scene_actor_ids.py') $tests.actor_auditor_sha256
$files=@($tests.files)
if($files.Count -ne 2 -or @(Compare-Object $scope @($files.relative)).Count -or @($files|Where-Object before_sha256).Count -ne 2){throw 'R9 replacement scope mismatch'}
$safe=@($tests.safe_rollback)
if($safe.Count -ne 3 -or @(Compare-Object $safeScope @($safe.relative)).Count -or @($safe|Where-Object sha256).Count -ne 2){throw 'Safe rollback scope mismatch'}
if(-not (Test-Path -LiteralPath (Join-Path $game 'r6\cache\final.redscripts') -PathType Leaf)){throw 'Unexpected game root'}
R5Closed
$prior=[ordered]@{}
foreach($name in @('install_receipt.json','population_r2\install_receipt.json','idles_r3\install_receipt.json','faces_r5\install_receipt.json','booth_r6\install_receipt.json','emmerick_r7\install_receipt.json','interactions_r8\install_receipt.json')){
 $old=Get-Content -LiteralPath (Join-Path $workspace ('research\afterlife_world\'+$name)) -Raw|ConvertFrom-Json
 foreach($file in $old.files){$prior[$file.relative.Replace('\','/')]=$file.sha256}
}
$r8=Get-Content -LiteralPath (Join-Path $workspace 'research\afterlife_world\interactions_r8\install_receipt.json') -Raw|ConvertFrom-Json
foreach($file in $safe){
 $old=@($r8.files|Where-Object {$_.relative.Replace('\','/') -eq $file.relative})
 if($old.Count -ne 1 -or $file.sha256 -ne $old[0].before_sha256){throw 'Safe rollback is not the recorded pre-R8 baseline'}
 if($file.sha256){
  $from=R5Within $file.source $workspace
  if($from -ne (R5Within $old[0].backup $workspace)){throw 'Safe rollback backup source changed'}
  R5Match $from $file.sha256
 }elseif($file.relative -ne $scope[1] -or $file.source){throw 'Unexpected safe removal'}
}
foreach($file in $files){if($file.before_sha256 -ne $prior[$file.relative]){throw 'R9 predecessor hash mismatch'}}
if($rollback){
 $receipt=Get-Content -LiteralPath (Join-Path $audit 'install_receipt.json') -Raw|ConvertFrom-Json -Depth 20
 if($receipt.status -ne 'INSTALLED_AFTERLIFE_INTERACTIONS_R9_LIVE_PENDING' -or $receipt.game_root -ne $game){throw 'Unexpected R9 receipt/root'}
 if(@($receipt.files).Count -ne 2 -or @(Compare-Object $scope @($receipt.files.relative)).Count){throw 'Receipt scope mismatch'}
 foreach($file in $files){
  $installed=@($receipt.files|Where-Object relative -eq $file.relative)[0]
  if($installed.sha256 -ne $file.sha256 -or $installed.before_sha256 -ne $file.before_sha256){throw 'Receipt hash mismatch'}
  $prior[$file.relative]=$file.sha256
 }
}elseif(-not $AuditDirectory -and $Mode -eq 'Install'){
 $fixture=Get-Content -LiteralPath (Join-Path $sourceAudit 'deployment_tests.json') -Raw|ConvertFrom-Json
 if($fixture.status -ne 'PASS_R9_WORKSPACE_INSTALL_SAFE_ROLLBACK'){throw 'Deployment fixture missing'}
 R5Match $PSCommandPath $fixture.deployment_sha256
 R5Match (Join-Path $PSScriptRoot 'test_afterlife_interactions_r9_deployment.ps1') $fixture.fixture_sha256
 R5Match (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1') $fixture.helpers_sha256
 R5Match (Join-Path $sourceAudit 'tests.json') $fixture.tests_sha256
}
foreach($p in $prior.Keys){R5Match (R5Within (Join-Path $game $p) $game) $prior[$p]}
$payloads=@($(if($rollback){$safe}else{$files})|ForEach-Object {
 $target=R5Within (Join-Path $game $_.relative) $game
 $source=if($_.source){R5Within $(if([IO.Path]::IsPathRooted($_.source)){$_.source}else{Join-Path $workspace $_.source}) $workspace}else{''}
 if($source){R5Match $source $_.sha256}
 @{relative=$_.relative;target=$target;source=$source;from_sha256=$prior[$_.relative];to_sha256=$_.sha256;backup='';recovered=''}
})
$protected=R5Snapshot $game @($payloads.target)
R5Unchanged $protected;R5Closed
if($Mode -like 'Validate*'){
 $result=@{status=('R9_'+$Mode.ToUpper()+'_ONLY');replacements=2;additions=0;recoverable_removals=$(if($rollback){1}else{0});protected_files=$protected.Count;game_unchanged=$true;rollback_baseline='pre-R8 (R7 archive/R2 XL; no interaction driver)'}
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
  R5Closed;R5Match $file.target $file.from_sha256
  if($file.source){R5Match $file.source $file.to_sha256}
  # Record before copying so a partial I/O failure is also recoverable.
  $attempted.Add($file)
  if($file.to_sha256){[IO.File]::Copy($file.source,$file.target,$true);R5Match $file.target $file.to_sha256}
  else{
   $file.recovered=R5Within (Join-Path $backup ('removed\'+$file.relative)) $backup
   New-Item -ItemType Directory -Force (Split-Path $file.recovered)|Out-Null
   Move-Item -LiteralPath $file.target -Destination $file.recovered
   R5Match $file.recovered $file.from_sha256
   if(Test-Path -LiteralPath $file.target){throw 'Interaction driver remains after safe rollback'}
  }
 }
 R5Closed;R5Unchanged $protected
 $result=[ordered]@{status=$(if($rollback){'ROLLED_BACK_AFTERLIFE_INTERACTIONS_R9_TO_PRE_R8'}else{'INSTALLED_AFTERLIFE_INTERACTIONS_R9_LIVE_PENDING'});utc=[DateTime]::UtcNow.ToString('o');game_root=$game;replacements=2;additions=0;recoverable_removals=$(if($rollback){1}else{0});protected_files=$protected.Count;protected_hashes=$protected;files=@($payloads|ForEach-Object {@{relative=$_.relative;sha256=$_.to_sha256;before_sha256=$_.from_sha256;backup=$_.backup;recovered=$_.recovered}});safe_rollback=$safe;rollback_baseline='pre-R8; R8 backups are forensics only, not a normal rollback';game_closed=$true;live_tested=$false;save_writes=0;story_writes=0}
 R5Json (Join-Path $audit $(if($rollback){'rollback_receipt.json'}else{'install_receipt.json'})) $result
 [pscustomobject]$result|Select-Object status,utc,replacements,additions,recoverable_removals,protected_files|ConvertTo-Json
}catch{
 $failure=$_.Exception.Message;$recovery=[Collections.Generic.List[string]]::new()
 foreach($file in $attempted){try{
  R5Closed;R5Match $file.backup $file.from_sha256
  [IO.File]::Copy($file.backup,$file.target,$true);R5Match $file.target $file.from_sha256
 }catch{$recovery.Add($_.Exception.Message)}}
 R5Json (Join-Path $audit 'deployment_failure.json') @{failure=$failure;backups=$backup;recovery_errors=@($recovery);warning='Do not launch after failed installation; transaction recovery may leave the known-unsafe R8 predecessor'}
 throw $failure
}
