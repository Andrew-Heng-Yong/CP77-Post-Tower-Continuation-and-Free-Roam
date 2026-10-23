param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$AuditDirectory='',
 [ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall'
)
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\');$root=Join-Path $workspace 'research\gig_restoration\rite_g2'
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\');$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$fixture=$game.StartsWith($root+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported game root'}
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$root}
if($fixture -and (-not $AuditDirectory -or -not $audit.StartsWith((Split-Path -Parent $game)+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Fixture audit path mismatch'}
if(-not $fixture -and $AuditDirectory){throw 'Actual audit path must be canonical'}
$testsPath=Join-Path $root 'tests.json';$tests=Get-Content $testsPath -Raw|ConvertFrom-Json
if($tests.status -ne 'PASS_RITE_G2_EXACT_RESUME_OFFLINE_LIVE_PENDING' -or -not $tests.graph.exact_edge_deltas -or -not $tests.graph.prefab_behind_optin -or
 -not $tests.equipmentex_full_compile -or -not $tests.logger.getter_only -or $tests.completed_replay_adapters -ne 0){throw 'Current checks missing'}
$expected=@(
 @{source='build/RiteG2/TowerContinued_RiteG2.archive';relative='archive/pc/mod/TowerContinued_RiteG2.archive'},
 @{source='archive/rite_g2/TowerContinued_RiteG2.archive.xl';relative='archive/pc/mod/TowerContinued_RiteG2.archive.xl'},
 @{source='redscript/PTFR_RiteG2/RiteG2.reds';relative='r6/scripts/PTFR_RiteG2/RiteG2.reds'},
 @{source='diagnostics/PTFR_RiteG2/init.lua';relative='bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_RiteG2/init.lua'},
 @{source='redscript/PTFR_ActivityStateR3/ActivityStateR3.reds';relative='r6/scripts/PTFR_ActivityStateR3/ActivityStateR3.reds'}
)
if(@($tests.files).Count -ne 5 -or @($tests.files.relative|Select-Object -Unique).Count -ne 5){throw 'Expected five-file scope'}
$files=@()
foreach($pin in $expected){
 $f=@($tests.files|Where-Object {$_.source -eq $pin.source -and $_.relative -eq $pin.relative})
 if($f.Count -ne 1){throw 'Unexpected mapping'}
 R5Match (R5Within (Join-Path $workspace $pin.source) $workspace) $f[0].sha256;$files+=,$f[0]
}
if(@($files|Where-Object {$_.predecessor -ne ''}).Count -ne 1 -or $files[4].predecessor -ne '1B4AA7B0FC242E2152ED370483712B2A598D6706E2EF6A1473D74A5686F52E18'){throw 'Wrong predecessor scope'}
foreach($p in $tests.tools.PSObject.Properties){R5Match (R5Within (Join-Path $workspace $p.Name) $workspace) $p.Value}
$compilePath=Join-Path $root 'compile_result.json';R5Match $compilePath $tests.compile_sha256
R5Match (Join-Path $root 'manifest.json') $tests.manifest_sha256
if(-not $fixture){
 $dt=Get-Content (Join-Path $root 'deployment_tests.json') -Raw|ConvertFrom-Json
 if($dt.status -ne 'PASS_G2_MIXED_DEPLOYMENT_FIXTURE' -or -not $dt.recoverable_rollback -or $dt.tests_sha256 -ne (R5Hash $testsPath) -or $dt.installer_sha256 -ne (R5Hash $PSCommandPath)){throw 'Current fixture checks missing'}
}
$targets=@($files|ForEach-Object {R5Within (Join-Path $game $_.relative) $game});$protected=R5Snapshot $game $targets
if(-not $fixture){
 $compile=Get-Content $compilePath -Raw|ConvertFrom-Json
 foreach($p in @($compile.protected.PSObject.Properties)+@($compile.dependencies.PSObject.Properties)+@($compile.predecessors.PSObject.Properties)){
  $path=R5Within $p.Name $game
  if($path -notin $targets){R5Match $path $p.Value;$protected[$path]=$p.Value}
 }
 foreach($folder in @('archive/pc/mod','red4ext/plugins','r6/scripts')){
  foreach($p in Get-ChildItem -LiteralPath (Join-Path $game $folder) -Recurse -File){if($p.FullName -notin $targets -and $p.Extension -in @('.archive','.xl','.reds','.dll')){$protected[$p.FullName]=R5Hash $p.FullName}}
 }
}
$receiptPath=Join-Path $audit 'install_receipt.json';$rollback=$Mode -in @('ValidateRollback','Rollback')
if($rollback){
 $receipt=Get-Content $receiptPath -Raw|ConvertFrom-Json
 if($receipt.status -ne 'INSTALLED_RITE_G2_EXACT_RESUME_LIVE_PENDING' -or $receipt.game_root -ne $game -or $receipt.tests_sha256 -ne (R5Hash $testsPath) -or
  $receipt.installer_sha256 -ne (R5Hash $PSCommandPath) -or @($receipt.files).Count -ne 5){throw 'Receipt mismatch'}
 foreach($f in $files){
  if(@($receipt.files|Where-Object {$_.source -eq $f.source -and $_.relative -eq $f.relative -and $_.sha256 -eq $f.sha256 -and $_.predecessor -eq $f.predecessor}).Count -ne 1){throw 'Receipt scope mismatch'}
  R5Match (R5Within (Join-Path $game $f.relative) $game) $f.sha256
  if($f.predecessor){R5Match (R5Within (Join-Path (Join-Path $audit 'backup') $f.relative) $audit) $f.predecessor}
 }
 if(Test-Path (Join-Path $audit 'rollback_receipt.json')){throw 'Already recovered'}
}else{
 if(Test-Path $receiptPath){throw 'Existing receipt; refuse reinstall'}
 foreach($f in $files){$target=R5Within (Join-Path $game $f.relative) $game;if($f.predecessor){R5Match $target $f.predecessor}else{if(Test-Path $target){throw 'Addition exists; refuse overwrite'}}}
}
R5Closed
if($Mode.StartsWith('Validate')){[ordered]@{status='VALIDATED';mode=$Mode;additions=4;replacements=1;protected_files=$protected.Count}|ConvertTo-Json;return}
New-Item -ItemType Directory -Force $audit|Out-Null
R5Closed
if($Mode -eq 'Install'){
 foreach($f in $files){
  $target=R5Within (Join-Path $game $f.relative) $game
  if($f.predecessor){
   R5Match $target $f.predecessor;$backup=R5Within (Join-Path (Join-Path $audit 'backup') $f.relative) $audit
   if(Test-Path $backup){throw 'Backup already exists'}
   New-Item -ItemType Directory -Force (Split-Path -Parent $backup)|Out-Null;Copy-Item -LiteralPath $target -Destination $backup;R5Match $backup $f.predecessor
  }else{if(Test-Path $target){throw 'Addition appeared during preflight'}}
  New-Item -ItemType Directory -Force (Split-Path -Parent $target)|Out-Null
  Copy-Item -LiteralPath (R5Within (Join-Path $workspace $f.source) $workspace) -Destination $target;R5Match $target $f.sha256
 }
 R5Unchanged $protected
 $result=[ordered]@{status='INSTALLED_RITE_G2_EXACT_RESUME_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=$files;tests_sha256=R5Hash $testsPath;installer_sha256=R5Hash $PSCommandPath;protected=$protected;additions=4;replacements=1;deployment_save_writes=0;cache_writes=0;new_gig_adapters=1;completed_replay_adapters=0}
 R5Json $receiptPath $result
}else{
 $recoverable=R5Within (Join-Path $audit ('recoverable_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $audit
 foreach($f in $files){
  $target=R5Within (Join-Path $game $f.relative) $game;$dest=R5Within (Join-Path $recoverable $f.relative) $recoverable
  New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null
  Move-Item -LiteralPath $target -Destination $dest;R5Match $dest $f.sha256
  if($f.predecessor){Copy-Item -LiteralPath (R5Within (Join-Path (Join-Path $audit 'backup') $f.relative) $audit) -Destination $target;R5Match $target $f.predecessor}
 }
 R5Unchanged $protected
 $result=[ordered]@{status='G2_FILES_RECOVERED_NOT_SAVED_EFFECTS';game_root=$game;recoverable=$recoverable;files=$files}
 R5Json (Join-Path $audit 'rollback_receipt.json') $result
}
Write-Output $result.status


