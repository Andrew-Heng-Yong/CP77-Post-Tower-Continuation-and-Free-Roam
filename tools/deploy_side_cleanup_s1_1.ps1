param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$AuditDirectory='',
 [ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall'
)
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\');$root=Join-Path $workspace 'research\side_job_cleanup_s1_1'
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\');$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$fixture=$game.StartsWith($root+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported game root'}
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$root}
if($fixture -and (-not $AuditDirectory -or -not $audit.StartsWith((Split-Path -Parent $game)+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Fixture audit path mismatch'}
if(-not $fixture -and $AuditDirectory){throw 'Actual audit path must be canonical'}
R5Closed
$testsPath=Join-Path $root 'tests.json';$tests=Get-Content $testsPath -Raw|ConvertFrom-Json
if($tests.status -ne 'PASS_S1_1_GUARDED_CLEANUP_OFFLINE_LIVE_PENDING' -or -not $tests.graph.original_conditions_retained -or -not $tests.graph.outside_trigger_retained -or -not $tests.graph.reward_and_journal_graphs_unchanged -or -not $tests.graph.other_resources_byte_identical -or -not $tests.persistent_fields_unchanged -or -not $tests.equipmentex_full_compile -or $tests.native_completion_reward_reset -or $tests.direct_owner_finished_write){throw 'Current checks missing'}
$expected=@(
 @{source='build/SideJobCleanupS1_1/TowerContinued_SideJobPilotS1.archive';relative='archive/pc/mod/TowerContinued_SideJobPilotS1.archive';predecessor='3966676F0605E398C60DBCC85A2C67BE8BE1B34B63915129AEA20CCA267238D3'},
 @{source='redscript/PTFR_SideJobPilotS1/SideJobPilotS1.reds';relative='r6/scripts/PTFR_SideJobPilotS1/SideJobPilotS1.reds';predecessor='06BEC212B5BA1A401E3E9615F3229DEB06574FE68B0194FC5996FBF1AD235CC5'},
 @{source='diagnostics/PTFR_SideJobPilotS1/init.lua';relative='bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_SideJobPilotS1/init.lua';predecessor='A8611194E9BF26260E5F02FBA8B43409C07507E4FBFB5ED5E854E09B4D18A1F6'}
)
if(@($tests.files).Count -ne 3 -or @($tests.files.relative|Select-Object -Unique).Count -ne 3){throw 'Expected three replacements'}
$files=@()
foreach($pin in $expected){
 $f=@($tests.files|Where-Object {$_.source -eq $pin.source -and $_.relative -eq $pin.relative -and $_.predecessor -eq $pin.predecessor})
 if($f.Count -ne 1){throw 'Unexpected mapping'}
 R5Match (R5Within (Join-Path $workspace $pin.source) $workspace) $f[0].sha256;$files+=,$f[0]
}
foreach($p in $tests.tools.PSObject.Properties){R5Match (R5Within (Join-Path $workspace $p.Name) $workspace) $p.Value}
$compilePath=Join-Path $root 'compile_result.json';R5Match $compilePath $tests.compile_sha256
R5Match (Join-Path $root 'manifest.json') $tests.manifest_sha256
if(-not $fixture){
 $dt=Get-Content (Join-Path $root 'deployment_tests.json') -Raw|ConvertFrom-Json
 if($dt.status -ne 'PASS_S1_1_REPLACEMENT_DEPLOYMENT_FIXTURE' -or -not $dt.recoverable_rollback -or $dt.tests_sha256 -ne (R5Hash $testsPath) -or $dt.installer_sha256 -ne (R5Hash $PSCommandPath)){throw 'Current fixture checks missing'}
}
$targets=@($files|ForEach-Object {R5Within (Join-Path $game $_.relative) $game});$protected=R5Snapshot $game $targets
if(-not $fixture){
 $compile=Get-Content $compilePath -Raw|ConvertFrom-Json
 foreach($p in @($compile.protected.PSObject.Properties)+@($compile.dependencies.PSObject.Properties)+@($compile.predecessors.PSObject.Properties)){
  $path=R5Within $p.Name $game;if($path -notin $targets){R5Match $path $p.Value;$protected[$path]=$p.Value}
 }
 foreach($folder in @('archive/pc/mod','red4ext/plugins','r6/scripts')){
  foreach($p in Get-ChildItem -LiteralPath (Join-Path $game $folder) -Recurse -File){if($p.FullName -notin $targets -and $p.Extension -in @('.archive','.xl','.reds','.dll')){$protected[$p.FullName]=R5Hash $p.FullName}}
 }
}
$receiptPath=Join-Path $audit 'install_receipt.json';$rollback=$Mode -in @('ValidateRollback','Rollback')
if($rollback){
 $receipt=Get-Content $receiptPath -Raw|ConvertFrom-Json
 if($receipt.status -ne 'INSTALLED_S1_1_CLEANUP_FALLBACK_LIVE_PENDING' -or $receipt.game_root -ne $game -or $receipt.tests_sha256 -ne (R5Hash $testsPath) -or $receipt.installer_sha256 -ne (R5Hash $PSCommandPath) -or @($receipt.files).Count -ne 3){throw 'Receipt mismatch'}
 foreach($f in $files){
  if(@($receipt.files|Where-Object {$_.source -eq $f.source -and $_.relative -eq $f.relative -and $_.sha256 -eq $f.sha256 -and $_.predecessor -eq $f.predecessor}).Count -ne 1){throw 'Receipt scope mismatch'}
  R5Match (R5Within (Join-Path $game $f.relative) $game) $f.sha256
  R5Match (R5Within (Join-Path (Join-Path $audit 'backup') $f.relative) $audit) $f.predecessor
 }
 if(Test-Path (Join-Path $audit 'rollback_receipt.json')){throw 'Already recovered'}
}else{
 if(Test-Path $receiptPath){throw 'Existing receipt; refuse reinstall'}
 foreach($f in $files){R5Match (R5Within (Join-Path $game $f.relative) $game) $f.predecessor}
}
R5Closed
if($Mode.StartsWith('Validate')){[ordered]@{status='VALIDATED';mode=$Mode;additions=0;replacements=3;protected_files=$protected.Count}|ConvertTo-Json;return}
New-Item -ItemType Directory -Force $audit|Out-Null
R5Closed
if($Mode -eq 'Install'){
 # Back up every predecessor before any replacement, checking all targets again.
 foreach($f in $files){
  $target=R5Within (Join-Path $game $f.relative) $game;R5Match $target $f.predecessor
  $backup=R5Within (Join-Path (Join-Path $audit 'backup') $f.relative) $audit
  if(Test-Path $backup){throw 'Backup already exists'}
  New-Item -ItemType Directory -Force (Split-Path -Parent $backup)|Out-Null;Copy-Item -LiteralPath $target -Destination $backup;R5Match $backup $f.predecessor
 }
 foreach($f in $files){$target=R5Within (Join-Path $game $f.relative) $game;R5Match $target $f.predecessor;Copy-Item -LiteralPath (R5Within (Join-Path $workspace $f.source) $workspace) -Destination $target;R5Match $target $f.sha256}
 R5Unchanged $protected
 $result=[ordered]@{status='INSTALLED_S1_1_CLEANUP_FALLBACK_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=$files;tests_sha256=R5Hash $testsPath;installer_sha256=R5Hash $PSCommandPath;protected=$protected;additions=0;replacements=3;deployment_save_writes=0;cache_writes=0;native_reward_or_journal_reset=$false;direct_owner_finished_write=$false}
 R5Json $receiptPath $result
}else{
 $recoverable=R5Within (Join-Path $audit ('recoverable_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $audit
 foreach($f in $files){
  $target=R5Within (Join-Path $game $f.relative) $game;$dest=R5Within (Join-Path $recoverable $f.relative) $recoverable
  New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null
  Move-Item -LiteralPath $target -Destination $dest;R5Match $dest $f.sha256
  Copy-Item -LiteralPath (R5Within (Join-Path (Join-Path $audit 'backup') $f.relative) $audit) -Destination $target;R5Match $target $f.predecessor
 }
 R5Unchanged $protected
 $result=[ordered]@{status='S1_1_FILES_RECOVERED_NOT_SAVED_EFFECTS';game_root=$game;recoverable=$recoverable;files=$files}
 R5Json (Join-Path $audit 'rollback_receipt.json') $result
}
Write-Output $result.status
