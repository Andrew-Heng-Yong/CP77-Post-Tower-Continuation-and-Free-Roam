param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$AuditDirectory='',
 [ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall'
)
# Exactly two backed-up replacements. No install occurs with default arguments.
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$sourceAudit=Join-Path $workspace 'research\afterlife_world\booth_r6'
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$sourceAudit}
New-Item -ItemType Directory -Force $audit|Out-Null
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$scope=@('archive/pc/mod/TowerContinued_AfterlifeIdlesR3.archive','r6/scripts/PTFR_Afterlife_Idles_R3/AfterlifeIdlesR3.reds')
$rollback=$Mode -in @('ValidateRollback','Rollback')
if($rollback){
 $receipt=Get-Content -LiteralPath (Join-Path $audit 'install_receipt.json') -Raw|ConvertFrom-Json -Depth 12
 if($receipt.status -ne 'INSTALLED_AFTERLIFE_BOOTH_R6_LIVE_PENDING'){throw 'Unexpected receipt'}
 if($game -ne $receipt.game_root){throw 'Game root differs from receipt'}
 $files=@($receipt.files)
}else{
 $tests=Get-Content -LiteralPath (Join-Path $sourceAudit 'tests.json') -Raw|ConvertFrom-Json
 if($tests.status -ne 'PASS_R6_OFFLINE_NOT_INSTALLED_NOT_LIVE' -or -not $tests.exact_source_redscript_compile_with_installed_codeware){throw 'Offline pass missing'}
 R5Match (Join-Path $sourceAudit 'manifest.json') $tests.manifest_sha256
 R5Match (Join-Path $workspace 'tools\build_afterlife_booth_r6.ps1') $tests.builder_sha256
 R5Match (Join-Path $workspace 'tools\test_afterlife_booth_r6.py') $tests.validator_sha256
 $files=@($tests.files)
}
if($files.Count -ne 2 -or @(Compare-Object $scope @($files.relative)).Count){throw 'Deployment scope mismatch'}
if(-not (Test-Path -LiteralPath (Join-Path $game 'r6\cache\final.redscripts') -PathType Leaf)){throw 'Unexpected game root'}
R5Closed
$prior=[ordered]@{}
foreach($name in @('install_receipt.json','population_r2\install_receipt.json','idles_r3\install_receipt.json','faces_r5\install_receipt.json')){
 $old=Get-Content -LiteralPath (Join-Path $workspace ('research\afterlife_world\'+$name)) -Raw|ConvertFrom-Json
 foreach($file in $old.files){$prior[$file.relative.Replace('\','/') ]=$file.sha256}
}
foreach($p in $prior.Keys){if($rollback -and $p -in $scope){continue};R5Match (R5Within (Join-Path $game $p) $game) $prior[$p]}
$payloads=@($files|ForEach-Object {
 $target=R5Within (Join-Path $game $_.relative) $game
 $source=if($rollback){R5Within $_.backup $workspace}else{R5Within (Join-Path $workspace $_.source) $workspace}
 $before=if($rollback){$_.sha256}else{$_.before_sha256}
 $after=if($rollback){$_.before_sha256}else{$_.sha256}
 R5Match $target $before;R5Match $source $after
 @{relative=$_.relative;target=$target;source=$source;before_sha256=$before;sha256=$after}
})
$protected=R5Snapshot $game @($payloads.target)
R5Unchanged $protected;R5Closed
if($Mode -like 'Validate*'){
 $result=@{status=('R6_'+$Mode.ToUpper()+'_ONLY');replacements=2;additions=0;protected_files=$protected.Count;game_unchanged=$true}
 R5Json (Join-Path $audit ($Mode+'.json')) $result;$result|ConvertTo-Json;return
}
if(-not $rollback -and (Test-Path -LiteralPath (Join-Path $audit 'install_receipt.json'))){throw 'Receipt already exists'}
$backup=R5Within (Join-Path $audit ('backup_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $workspace
# Back up both exact targets BEFORE replacing either.
foreach($file in $payloads){
 R5Closed;R5Match $file.target $file.before_sha256
 $file.backup=R5Within (Join-Path $backup $file.relative) $backup
 New-Item -ItemType Directory -Force (Split-Path $file.backup)|Out-Null
 [IO.File]::Copy($file.target,$file.backup,$false);R5Match $file.backup $file.before_sha256
}
$written=[Collections.Generic.List[object]]::new()
try{
 foreach($file in $payloads){
  R5Closed;R5Match $file.target $file.before_sha256;R5Match $file.source $file.sha256
  [IO.File]::Copy($file.source,$file.target,$true);$written.Add($file);R5Match $file.target $file.sha256
 }
 R5Closed;R5Unchanged $protected
 $result=[ordered]@{status=$(if($rollback){'ROLLED_BACK_AFTERLIFE_BOOTH_R6'}else{'INSTALLED_AFTERLIFE_BOOTH_R6_LIVE_PENDING'});utc=[DateTime]::UtcNow.ToString('o');game_root=$game;replacements=2;additions=0;protected_files=$protected.Count;protected_hashes=$protected;files=@($payloads|ForEach-Object {@{relative=$_.relative;sha256=$_.sha256;before_sha256=$_.before_sha256;backup=$_.backup}});game_closed=$true;live_tested=$false;save_writes=0;story_writes=0}
 R5Json (Join-Path $audit $(if($rollback){'rollback_receipt.json'}else{'install_receipt.json'})) $result
 [pscustomobject]$result|Select-Object status,utc,replacements,additions,protected_files|ConvertTo-Json
}catch{
 $failure=$_.Exception.Message;$recovery=[Collections.Generic.List[string]]::new()
 foreach($file in $written){try{R5Closed;R5Match $file.target $file.sha256;R5Match $file.backup $file.before_sha256;[IO.File]::Copy($file.backup,$file.target,$true);R5Match $file.target $file.before_sha256}catch{$recovery.Add($_.Exception.Message)}}
 R5Json (Join-Path $audit 'deployment_failure.json') @{failure=$failure;backups=$backup;recovery_errors=@($recovery)}
 throw $failure
}
