param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$AuditDirectory='',
 [ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall'
)
# Two addition-only read-only CET audit files; NOT a 71-gig restoration installer.
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$auditRoot=Join-Path $workspace 'research\gig_restoration\rollout_r2'
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$fixture=$game.StartsWith($auditRoot+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported game root'}
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$auditRoot}
if($fixture -and (-not $AuditDirectory -or -not $audit.StartsWith((Split-Path -Parent $game)+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Fixture audit path mismatch'}
if(-not $fixture -and $AuditDirectory){throw 'Actual audit directory must be canonical'}
$testsPath=Join-Path $auditRoot 'tests.json'
$tests=Get-Content $testsPath -Raw|ConvertFrom-Json
if($tests.status -ne 'PASS_71_GIG_READONLY_AUDIT_NOT_RESTORATION' -or $tests.selected_count -ne 71 -or $tests.source_coverage -ne 71 -or $tests.gameplay_writes -ne 0){throw 'Audit source tests missing'}
$scope=@('bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_GigAuditR2/init.lua','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_GigAuditR2/catalogue.json')
$sources=@('diagnostics/PTFR_GigAuditR2/init.lua','research/gig_restoration/rollout_r2/catalogue.json')
if(@($tests.files).Count -ne 2 -or @($tests.files.relative|Select-Object -Unique).Count -ne 2){throw 'Unexpected scope'}
for($i=0;$i -lt 2;$i++){
 $f=@($tests.files|Where-Object {$_.relative -eq $scope[$i] -and $_.source -eq $sources[$i]})
 if($f.Count -ne 1){throw 'Unexpected source mapping'}
 R5Match (R5Within (Join-Path $workspace $sources[$i]) $workspace) $f[0].sha256
}
foreach($p in $tests.tools.PSObject.Properties){R5Match (R5Within (Join-Path $workspace $p.Name) $workspace) $p.Value}
if(-not $fixture){
 $fixtureTests=Get-Content (Join-Path $auditRoot 'deployment_tests.json') -Raw|ConvertFrom-Json
 if($fixtureTests.status -ne 'PASS_TWO_FILE_AUDIT_FIXTURE' -or $fixtureTests.tests_sha256 -ne (R5Hash $testsPath) -or $fixtureTests.installer_sha256 -ne (R5Hash $PSCommandPath)){throw 'Current deployment fixture missing'}
}
$files=@($tests.files);$targets=@($scope|ForEach-Object {R5Within (Join-Path $game $_) $game})
$protected=R5Snapshot $game $targets
$cache=Join-Path $game 'r6\cache'
if(Test-Path -LiteralPath $cache){foreach($f in Get-ChildItem -LiteralPath $cache -File){$protected[$f.FullName]=R5Hash $f.FullName}}
$receiptPath=Join-Path $audit 'audit_install_receipt.json'
$rollback=$Mode -in @('ValidateRollback','Rollback')
if($rollback){
 $receipt=Get-Content $receiptPath -Raw|ConvertFrom-Json
 if($receipt.status -ne 'INSTALLED_READONLY_71_GIG_AUDIT_NOT_RESTORATION' -or $receipt.game_root -ne $game -or
  $receipt.tests_sha256 -ne (R5Hash $testsPath) -or $receipt.installer_sha256 -ne (R5Hash $PSCommandPath) -or @($receipt.files).Count -ne 2){throw 'Receipt mismatch'}
 foreach($f in $files){
  if(@($receipt.files|Where-Object {$_.relative -eq $f.relative -and $_.source -eq $f.source -and $_.sha256 -eq $f.sha256}).Count -ne 1){throw 'Receipt scope/hash mismatch'}
  R5Match (R5Within (Join-Path $game $f.relative) $game) $f.sha256
 }
 if(Test-Path (Join-Path $audit 'audit_rollback_receipt.json')){throw 'Already rolled back'}
}else{
 if(Test-Path $receiptPath){throw 'Existing receipt; refuse reinstall'}
 foreach($target in $targets){if(Test-Path -LiteralPath $target){throw 'Addition exists; refuse overwrite'}}
}
R5Closed
if($Mode.StartsWith('Validate')){[ordered]@{status='VALIDATED';mode=$Mode;additions=2;replacements=0;protected_files=$protected.Count}|ConvertTo-Json;return}
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
 $result=[ordered]@{status='INSTALLED_READONLY_71_GIG_AUDIT_NOT_RESTORATION';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=$files;tests_sha256=R5Hash $testsPath;installer_sha256=R5Hash $PSCommandPath;protected=$protected;additions=2;replacements=0;save_writes=0;cache_writes=0;restored_gigs=0}
 R5Json $receiptPath $result
}else{
 $recoverable=R5Within (Join-Path $audit ('recoverable_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $audit
 foreach($f in $files){
  $target=R5Within (Join-Path $game $f.relative) $game;$dest=R5Within (Join-Path $recoverable $f.relative) $recoverable
  New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null
  Move-Item -LiteralPath $target -Destination $dest;R5Match $dest $f.sha256
 }
 R5Unchanged $protected
 $result=[ordered]@{status='AUDIT_FILES_RECOVERABLY_REMOVED';recoverable=$recoverable;game_root=$game;files=$files}
 R5Json (Join-Path $audit 'audit_rollback_receipt.json') $result
}
Write-Output $result.status
