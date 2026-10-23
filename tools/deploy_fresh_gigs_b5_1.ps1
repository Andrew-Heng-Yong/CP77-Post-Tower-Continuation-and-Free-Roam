param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$AuditDirectory='',
 [ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall'
)
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$root=Join-Path $workspace 'research\gig_restoration\fresh_b5_1'
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$fixture=$game.StartsWith($root+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported game root'}
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$root}
if($fixture -and (-not $AuditDirectory -or -not $audit.StartsWith((Split-Path -Parent $game)+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Fixture audit mismatch'}
if(-not $fixture -and $AuditDirectory){throw 'Actual audit must be canonical'}
$testPath=Join-Path $root 'tests.json'
$t=Get-Content -LiteralPath $testPath -Raw|ConvertFrom-Json
if($t.status -ne 'PASS_B5_1_OFFLINE_NATIVE_RELOAD_PENDING' -or -not $t.compiled_nested_persistence_verified -or -not $t.r3_only_nested_persistence_flags_changed -or -not $t.r3_history_not_reconstructed -or -not $t.equipmentex_full_compile -or $t.recovery_writes_native_fact_journal_owner_reward_credit -or $t.new_gig_adapters -ne 0){throw 'B5.1 checks missing'}
$expected=@(
 @{source='redscript/PTFR_FreshGigsB5/FreshGigsB5.reds';relative='r6/scripts/PTFR_FreshGigsB5/FreshGigsB5.reds';predecessor='C1D2454935E0E3A02EC8BDB915E67EEB6FE56928202F79DAAC7104A4081F641A'},
 @{source='redscript/PTFR_ActivityStateR3/ActivityStateR3.reds';relative='r6/scripts/PTFR_ActivityStateR3/ActivityStateR3.reds';predecessor='D8C3F11A4CA8276392EDA64760ABE2F7900A1266B23B5460968A2A761557AD87'},
 @{source='diagnostics/PTFR_FreshGigsB5/init.lua';relative='bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_FreshGigsB5/init.lua';predecessor='C7A6E907E6A16441E9BBCAC07ED7515668A55D2E0960278787CF23CE7D813C36'}
)
if(@($t.files).Count -ne 3 -or @($t.files.relative|Select-Object -Unique).Count -ne 3){throw 'Exactly three replacements required'}
$files=@()
foreach($e in $expected){
 $f=@($t.files|Where-Object {$_.source -eq $e.source -and $_.relative -eq $e.relative -and $_.predecessor -eq $e.predecessor})
 if($f.Count -ne 1){throw 'Replacement mapping mismatch'}
 R5Match (R5Within (Join-Path $workspace $e.source) $workspace) $f[0].sha256
 $files+=,$f[0]
}
foreach($p in $t.tools.PSObject.Properties){R5Match (R5Within (Join-Path $workspace $p.Name) $workspace) $p.Value}
$compilePath=Join-Path $root 'compile_result.json'
R5Match $compilePath $t.compile_sha256
if(-not $fixture){
 $d=Get-Content -LiteralPath (Join-Path $root 'deployment_tests.json') -Raw|ConvertFrom-Json
 if($d.status -ne 'PASS_B5_1_THREE_REPLACEMENT_FIXTURE' -or -not $d.recoverable_rollback -or $d.tests_sha256 -ne (R5Hash $testPath) -or $d.installer_sha256 -ne (R5Hash $PSCommandPath)){throw 'Current recoverable fixture checks missing'}
}
$targets=@($files|ForEach-Object {R5Within (Join-Path $game $_.relative) $game})
$protected=R5Snapshot $game $targets
if(-not $fixture){
 if($Mode -in @('ValidateInstall','Install')){
  $c=Get-Content -LiteralPath $compilePath -Raw|ConvertFrom-Json
  foreach($p in @($c.protected.PSObject.Properties)+@($c.dependencies.PSObject.Properties)){
   if($p.Name -notin $targets){R5Match (R5Within $p.Name $game) $p.Value;$protected[$p.Name]=$p.Value}
  }
 }
 # Preserve all unrelated currently installed assets, including third-party mods.
 foreach($folder in @('archive/pc/mod','red4ext/plugins','r6/scripts','r6/cache')){
  foreach($p in Get-ChildItem -LiteralPath (Join-Path $game $folder) -Recurse -File){
   if($p.FullName -notin $targets -and ($folder -eq 'r6/cache' -or $p.Extension -in @('.archive','.xl','.reds','.dll'))){$protected[$p.FullName]=R5Hash $p.FullName}
  }
 }
}
$receiptPath=Join-Path $audit 'install_receipt.json'
if($Mode -in @('ValidateRollback','Rollback')){
 $r=Get-Content -LiteralPath $receiptPath -Raw|ConvertFrom-Json
 if($r.status -ne 'INSTALLED_B5_1_PERSISTENCE_RECOVERY_LIVE_PENDING' -or $r.game_root -ne $game -or $r.tests_sha256 -ne (R5Hash $testPath) -or $r.installer_sha256 -ne (R5Hash $PSCommandPath) -or @($r.files).Count -ne 3){throw 'Receipt mismatch'}
 foreach($f in $files){
  if(@($r.files|Where-Object {$_.source -eq $f.source -and $_.relative -eq $f.relative -and $_.sha256 -eq $f.sha256 -and $_.predecessor -eq $f.predecessor}).Count -ne 1){throw 'Receipt scope mismatch'}
  R5Match (Join-Path $game $f.relative) $f.sha256
  R5Match (R5Within (Join-Path (Join-Path $audit 'backup') $f.relative) $audit) $f.predecessor
 }
 if(Test-Path -LiteralPath (Join-Path $audit 'rollback_receipt.json')){throw 'Already recovered'}
}else{
 if(Test-Path -LiteralPath $receiptPath){throw 'Existing receipt; refuse reinstall'}
 foreach($f in $files){R5Match (Join-Path $game $f.relative) $f.predecessor}
 foreach($f in $t.archive_xl_unchanged){
  if(-not $fixture){R5Match (R5Within (Join-Path $game $f.relative) $game) $f.sha256}
 }
}
R5Closed
if($Mode.StartsWith('Validate')){[ordered]@{status='VALIDATED';mode=$Mode;additions=0;replacements=3;protected_files=$protected.Count}|ConvertTo-Json;return}
New-Item -ItemType Directory -Force $audit|Out-Null
R5Closed
if($Mode -eq 'Install'){
 # Complete and verify all backups before replacing any game file.
 foreach($f in $files){
  $target=R5Within (Join-Path $game $f.relative) $game
  R5Match $target $f.predecessor
  $backup=R5Within (Join-Path (Join-Path $audit 'backup') $f.relative) $audit
  if(Test-Path -LiteralPath $backup){throw 'Backup already exists'}
  New-Item -ItemType Directory -Force (Split-Path -Parent $backup)|Out-Null
  Copy-Item -LiteralPath $target -Destination $backup
  R5Match $backup $f.predecessor
 }
 foreach($f in $files){
  R5Closed
  $target=R5Within (Join-Path $game $f.relative) $game
  R5Match $target $f.predecessor
  $source=R5Within (Join-Path $workspace $f.source) $workspace
  R5Match $source $f.sha256
  Copy-Item -LiteralPath $source -Destination $target
  R5Match $target $f.sha256
 }
 R5Unchanged $protected
 $result=[ordered]@{status='INSTALLED_B5_1_PERSISTENCE_RECOVERY_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=$files;protected=$protected;tests_sha256=R5Hash $testPath;installer_sha256=R5Hash $PSCommandPath;additions=0;replacements=3;cache_writes=0;deployment_direct_save_writes=0;native_save_reload_proof=$false}
 R5Json $receiptPath $result
}else{
 $recoverable=R5Within (Join-Path $audit ('recoverable_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $audit
 foreach($f in $files){
  R5Closed
  $target=R5Within (Join-Path $game $f.relative) $game
  R5Match $target $f.sha256
  $dest=R5Within (Join-Path $recoverable $f.relative) $recoverable
  New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null
  Move-Item -LiteralPath $target -Destination $dest
  R5Match $dest $f.sha256
  Copy-Item -LiteralPath (R5Within (Join-Path (Join-Path $audit 'backup') $f.relative) $audit) -Destination $target
  R5Match $target $f.predecessor
 }
 R5Unchanged $protected
 $result=[ordered]@{status='B5_1_FILES_RECOVERED_NOT_LOADED_OR_NEW_SAVED_WORLD';game_root=$game;recoverable=$recoverable;files=$files}
 R5Json (Join-Path $audit 'rollback_receipt.json') $result
}
$result.status
