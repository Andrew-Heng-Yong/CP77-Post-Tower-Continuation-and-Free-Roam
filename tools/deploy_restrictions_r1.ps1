param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$AuditDirectory='',
 [ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall'
)
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$sourceAudit=Join-Path $workspace 'research\restriction_profiles\implementation_r1'
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$sourceAudit}
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$fixture=$game.StartsWith($sourceAudit+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported deployment root'}
if($fixture -and -not $AuditDirectory){throw 'Fixture needs its own audit directory'}
New-Item -ItemType Directory -Force $audit | Out-Null
$testsPath=Join-Path $sourceAudit 'tests.json'
$tests=Get-Content -LiteralPath $testsPath -Raw | ConvertFrom-Json
if($tests.status -ne 'PASS_RESTRICTIONS_R1_OFFLINE_LIVE_PENDING' -or -not $tests.equipmentex_full_compile -or -not $tests.source_audit){throw 'Offline checks missing'}
foreach($p in $tests.checked_sources.PSObject.Properties){R5Match (R5Within (Join-Path $workspace $p.Name) $workspace) $p.Value}
$scope=@('r6/scripts/PTFR_Restrictions_R1/CyberwarePolicy.reds','r6/scripts/PTFR_Restrictions_R1/EquipmentHooks.reds','r6/scripts/PTFR_Restrictions_R1/RipperdocHooks.reds')
$files=@($tests.files)
if($files.Count -ne 3 -or @(Compare-Object $scope @($files.relative)).Count){throw 'Unexpected install scope'}
foreach($f in $files){R5Match (R5Within (Join-Path $workspace $f.source) $workspace) $f.sha256}
R5Match (Join-Path $game 'r6/cache/final.redscripts') $tests.base_sha256
if(-not $fixture){
 foreach($p in $tests.dependency_hashes.PSObject.Properties){R5Match $p.Name $p.Value}
 $r11=Get-Content -LiteralPath (Join-Path $workspace 'research/afterlife_world/interactions_r11/install_receipt.json') -Raw | ConvertFrom-Json
 foreach($f in $r11.files){R5Match (R5Within (Join-Path $game $f.relative) $game) $f.sha256}
}
$rollback=$Mode -in @('ValidateRollback','Rollback')
if($rollback){
 $receipt=Get-Content -LiteralPath (Join-Path $audit 'install_receipt.json') -Raw | ConvertFrom-Json
 if($receipt.status -ne 'INSTALLED_RESTRICTIONS_R1_LIVE_PENDING' -or $receipt.game_root -ne $game){throw 'Receipt/root mismatch'}
 if(@($receipt.files).Count -ne 3 -or @(Compare-Object $scope @($receipt.files.relative)).Count){throw 'Receipt scope mismatch'}
 foreach($f in $files){
  $entry=@($receipt.files | Where-Object relative -eq $f.relative)[0]
  if($entry.sha256 -ne $f.sha256){throw 'Receipt/source mismatch'}
  R5Match (R5Within (Join-Path $game $f.relative) $game) $entry.sha256
 }
}else{
 foreach($f in $files){if(Test-Path -LiteralPath (R5Within (Join-Path $game $f.relative) $game)){throw 'Target exists; refusing overwrite'}}
 if(Test-Path -LiteralPath (Join-Path $audit 'install_receipt.json')){throw 'Install receipt already exists'}
}
if($Mode -eq 'Install' -and -not $fixture){
 $deployment=Get-Content -LiteralPath (Join-Path $sourceAudit 'deployment_tests.json') -Raw | ConvertFrom-Json
 if($deployment.status -ne 'PASS_RESTRICTIONS_R1_INSTALL_ROLLBACK_FIXTURE'){throw 'Fixture pass missing'}
 R5Match $PSCommandPath $deployment.installer_sha256
 R5Match $testsPath $deployment.tests_sha256
 R5Match (Join-Path $PSScriptRoot 'test_restrictions_r1_deployment.ps1') $deployment.fixture_sha256
 R5Match (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1') $deployment.helpers_sha256
}
R5Closed
$targets=@($files | ForEach-Object {R5Within (Join-Path $game $_.relative) $game})
$protected=R5Snapshot $game $targets
$cacheHashes=[ordered]@{}
foreach($name in @('final.redscripts','final.redscripts.modded','final.redscripts.ts','tweakdb.bin','tweakdb_ep1.bin')){
 $path=Join-Path $game ('r6/cache/'+$name)
 if(Test-Path -LiteralPath $path){$cacheHashes[$path]=R5Hash $path}
}
R5Unchanged $protected; R5Unchanged $cacheHashes
if($Mode -like 'Validate*'){
 $result=@{status=('RESTRICTIONS_R1_'+$Mode.ToUpper());game_root=$game;additions=$(if($rollback){0}else{3});removals=$(if($rollback){3}else{0});replacements=0;protected_files=$protected.Count;game_unchanged=$true}
 R5Json (Join-Path $audit ($Mode+'.json')) $result
 $result | ConvertTo-Json; return
}
$recovery=R5Within (Join-Path $audit ('recoverable_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $workspace
$completed=[Collections.Generic.List[object]]::new()
try {
 foreach($f in $files){
  R5Closed
  $target=R5Within (Join-Path $game $f.relative) $game
  if($rollback){
   R5Match $target $f.sha256
   $destination=R5Within (Join-Path $recovery $f.relative) $recovery
   New-Item -ItemType Directory -Force (Split-Path $destination) | Out-Null
   Move-Item -LiteralPath $target -Destination $destination
   R5Match $destination $f.sha256
  }else{
   $source=R5Within (Join-Path $workspace $f.source) $workspace
   R5Match $source $f.sha256
   New-Item -ItemType Directory -Force (Split-Path $target) | Out-Null
   [IO.File]::Copy($source,$target,$false)
   R5Match $target $f.sha256
  }
  $completed.Add($f)
 }
 R5Closed; R5Unchanged $protected; R5Unchanged $cacheHashes
 $result=[ordered]@{status=$(if($rollback){'ROLLED_BACK_RESTRICTIONS_R1_RECOVERABLY'}else{'INSTALLED_RESTRICTIONS_R1_LIVE_PENDING'});utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=$files;additions=$(if($rollback){0}else{3});removals=$(if($rollback){3}else{0});replacements=0;protected_files=$protected.Count;protected_hashes=$protected;cache_hashes=$cacheHashes;game_closed=$true;live_tested=$false;save_writes=0;story_writes=0;recovery=$recovery}
 R5Json (Join-Path $audit $(if($rollback){'rollback_receipt.json'}else{'install_receipt.json'})) $result
 [pscustomobject]$result | Select-Object status,utc,additions,removals,replacements,protected_files | ConvertTo-Json
}catch{
 $reason=$_.Exception.Message
 # Only move exact known additions; never remove unknown or pre-existing files.
 foreach($f in $completed){
  R5Closed
  $target=R5Within (Join-Path $game $f.relative) $game
  $backup=R5Within (Join-Path $recovery $f.relative) $recovery
  if($rollback){R5Match $backup $f.sha256;Move-Item -LiteralPath $backup -Destination $target}
  else{R5Match $target $f.sha256;New-Item -ItemType Directory -Force (Split-Path $backup)|Out-Null;Move-Item -LiteralPath $target -Destination $backup}
 }
 R5Json (Join-Path $audit 'deployment_failure.json') @{error=$reason;recoverable=$recovery}
 throw $reason
}
