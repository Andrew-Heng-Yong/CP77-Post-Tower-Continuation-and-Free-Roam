param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$AuditDirectory='',
 [ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall'
)
# Foundation only: two history scripts + thin CET bridge. No full activity rollout.
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$auditRoot=Join-Path $workspace 'research\activity_state_r3'
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$fixture=$game.StartsWith($auditRoot+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported game root'}
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$auditRoot}
if($fixture -and (-not $AuditDirectory -or -not $audit.StartsWith((Split-Path -Parent $game)+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Fixture audit path mismatch'}
if(-not $fixture -and $AuditDirectory){throw 'Actual audit directory must be canonical'}
$testsPath=Join-Path $auditRoot 'tests.json';$tests=Get-Content $testsPath -Raw|ConvertFrom-Json
if($tests.status -ne 'PASS_ACTIVITY_HISTORY_FOUNDATION_NOT_FULL_RESTORATION' -or -not $tests.equipmentex_full_compile -or
 $tests.gig_count -ne 71 -or $tests.side_job_count -ne 57 -or $tests.native_reset_writes -ne 0 -or $tests.completed_replay_adapter_count -ne 0){throw 'Current history tests missing'}
$scope=@('r6/scripts/PTFR_ActivityStateR3/ActivityDefinition.generated.reds','r6/scripts/PTFR_ActivityStateR3/ActivityStateR3.reds','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_ActivityStateR3/init.lua')
$sources=@('redscript/PTFR_ActivityStateR3/ActivityDefinition.generated.reds','redscript/PTFR_ActivityStateR3/ActivityStateR3.reds','diagnostics/PTFR_ActivityStateR3/init.lua')
if(@($tests.files).Count -ne 3 -or @($tests.files.relative|Select-Object -Unique).Count -ne 3){throw 'Unexpected deployment scope'}
for($i=0;$i -lt 3;$i++){
 $f=@($tests.files|Where-Object {$_.relative -eq $scope[$i] -and $_.source -eq $sources[$i]})
 if($f.Count -ne 1){throw 'Unexpected source mapping'}
 R5Match (R5Within (Join-Path $workspace $sources[$i]) $workspace) $f[0].sha256
}
foreach($p in $tests.tools.PSObject.Properties){R5Match (R5Within (Join-Path $workspace $p.Name) $workspace) $p.Value}
$compilePath=Join-Path $auditRoot 'compile_result.json';R5Match $compilePath $tests.compile_sha256
if(-not $fixture){
 $fixtureTests=Get-Content (Join-Path $auditRoot 'deployment_tests.json') -Raw|ConvertFrom-Json
 if($fixtureTests.status -ne 'PASS_THREE_FILE_HISTORY_FIXTURE' -or $fixtureTests.tests_sha256 -ne (R5Hash $testsPath) -or $fixtureTests.installer_sha256 -ne (R5Hash $PSCommandPath)){throw 'Current deployment fixture missing'}
}
$files=@($tests.files);$targets=@($scope|ForEach-Object {R5Within (Join-Path $game $_) $game})
$protected=R5Snapshot $game $targets
if(-not $fixture){
 $compile=Get-Content $compilePath -Raw|ConvertFrom-Json
 foreach($p in @($compile.protected.PSObject.Properties)+@($compile.dependencies.PSObject.Properties)){
  $path=R5Within $p.Name $game;R5Match $path $p.Value;$protected[$path]=$p.Value
 }
 foreach($root in @('archive/pc/mod','red4ext/plugins','r6/scripts')){
  foreach($p in Get-ChildItem -LiteralPath (Join-Path $game $root) -File -Recurse){
   if($p.FullName -notin $targets -and $p.Extension -in @('.archive','.xl','.reds','.dll')){$protected[$p.FullName]=R5Hash $p.FullName}
  }
 }
}
$receiptPath=Join-Path $audit 'install_receipt.json';$rollback=$Mode -in @('ValidateRollback','Rollback')
if($rollback){
 $receipt=Get-Content $receiptPath -Raw|ConvertFrom-Json
 if($receipt.status -ne 'INSTALLED_ACTIVITY_HISTORY_FOUNDATION_NOT_FULL_RESTORATION' -or $receipt.game_root -ne $game -or
  $receipt.tests_sha256 -ne (R5Hash $testsPath) -or $receipt.installer_sha256 -ne (R5Hash $PSCommandPath) -or @($receipt.files).Count -ne 3){throw 'Receipt mismatch'}
 foreach($f in $files){
  if(@($receipt.files|Where-Object {$_.relative -eq $f.relative -and $_.source -eq $f.source -and $_.sha256 -eq $f.sha256}).Count -ne 1){throw 'Receipt scope/hash mismatch'}
  R5Match (R5Within (Join-Path $game $f.relative) $game) $f.sha256
 }
 if(Test-Path (Join-Path $audit 'rollback_receipt.json')){throw 'Already rolled back'}
}else{
 if(Test-Path $receiptPath){throw 'Existing receipt; refuse reinstall'}
 foreach($target in $targets){if(Test-Path -LiteralPath $target){throw 'Addition exists; refuse overwrite'}}
}
R5Closed
if($Mode.StartsWith('Validate')){[ordered]@{status='VALIDATED';mode=$Mode;additions=3;replacements=0;protected_files=$protected.Count}|ConvertTo-Json;return}
New-Item -ItemType Directory -Force $audit|Out-Null
R5Closed
if($Mode -eq 'Install'){
 foreach($f in $files){
  $target=R5Within (Join-Path $game $f.relative) $game
  if(Test-Path $target){throw 'Target appeared during preflight'}
  New-Item -ItemType Directory -Force (Split-Path -Parent $target)|Out-Null
  Copy-Item -LiteralPath (R5Within (Join-Path $workspace $f.source) $workspace) -Destination $target
  R5Match $target $f.sha256
 }
 R5Unchanged $protected
 $result=[ordered]@{status='INSTALLED_ACTIVITY_HISTORY_FOUNDATION_NOT_FULL_RESTORATION';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=$files;tests_sha256=R5Hash $testsPath;installer_sha256=R5Hash $PSCommandPath;protected=$protected;additions=3;replacements=0;deployment_save_writes=0;cache_writes=0;new_restoration_adapters=0;completed_replay_adapters=0}
 R5Json $receiptPath $result
}else{
 $recoverable=R5Within (Join-Path $audit ('recoverable_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $audit
 foreach($f in $files){
  $target=R5Within (Join-Path $game $f.relative) $game;$dest=R5Within (Join-Path $recoverable $f.relative) $recoverable
  New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null
  Move-Item -LiteralPath $target -Destination $dest;R5Match $dest $f.sha256
 }
 R5Unchanged $protected
 $result=[ordered]@{status='HISTORY_FILES_RECOVERABLY_REMOVED';recoverable=$recoverable;game_root=$game;files=$files}
 R5Json (Join-Path $audit 'rollback_receipt.json') $result
}
Write-Output $result.status
