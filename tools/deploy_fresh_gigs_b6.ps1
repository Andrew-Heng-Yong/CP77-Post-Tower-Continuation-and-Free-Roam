param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$AuditDirectory='',
 [ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall'
)
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\');$root=Join-Path $workspace 'research\gig_restoration\fresh_b6'
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\');$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$fixture=$game.StartsWith($root+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported game root'}
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$root}
if($fixture -and (-not $AuditDirectory -or -not $audit.StartsWith((Split-Path -Parent $game)+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Fixture audit mismatch'}
if(-not $fixture -and $AuditDirectory){throw 'Actual audit must be canonical'}
$testPath=Join-Path $root 'tests.json';$t=Get-Content -LiteralPath $testPath -Raw|ConvertFrom-Json
if($t.status -ne 'PASS_B6_M6_OFFLINE_LIVE_PENDING' -or -not $t.exact_edges -or -not $t.persistence_verified -or -not $t.r3_history_capture_schema_unchanged -or -not $t.marker_presentation_only -or $t.new_gig_adapters -ne 1){throw 'B6/M6 checks missing'}
$expected=@(
 @{source='build/FreshGigsB6/TowerContinued_FreshB6.archive';relative='archive/pc/mod/TowerContinued_FreshB6.archive';predecessor=$null},
 @{source='build/FreshGigsB6/TowerContinued_FreshB6.archive.xl';relative='archive/pc/mod/TowerContinued_FreshB6.archive.xl';predecessor=$null},
 @{source='redscript/PTFR_FreshGigsB6/FreshGigsB6.reds';relative='r6/scripts/PTFR_FreshGigsB6/FreshGigsB6.reds';predecessor=$null},
 @{source='redscript/PTFR_GigMarkersM6/GigMarkersM6.reds';relative='r6/scripts/PTFR_GigMarkersM6/GigMarkersM6.reds';predecessor=$null},
 @{source='diagnostics/PTFR_FreshGigsB6/init.lua';relative='bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_FreshGigsB6/init.lua';predecessor=$null},
 @{source='redscript/PTFR_FreshGigsB5/FreshGigsB5.reds';relative='r6/scripts/PTFR_FreshGigsB5/FreshGigsB5.reds';predecessor='B171430B760F99902A2815139D31BBDA3EF0865F557608B52582AC502ECC7418'},
 @{source='redscript/PTFR_ActivityStateR3/ActivityStateR3.reds';relative='r6/scripts/PTFR_ActivityStateR3/ActivityStateR3.reds';predecessor='6B3D48216763BA4BD2FD61B4A3E1D6948733B606B850A5694F801B30198ECCE9'}
)
if(@($t.files).Count -ne 7 -or @($t.files.relative|Select-Object -Unique).Count -ne 7){throw 'Exactly seven targets required'}
$files=@()
foreach($e in $expected){
 $f=@($t.files|Where-Object {$_.source -eq $e.source -and $_.relative -eq $e.relative -and $_.predecessor -eq $e.predecessor})
 if($f.Count -ne 1){throw 'Mapping mismatch'}
 R5Match (R5Within (Join-Path $workspace $e.source) $workspace) $f[0].sha256;$files+=,$f[0]
}
foreach($p in $t.tools.PSObject.Properties){R5Match (R5Within (Join-Path $workspace $p.Name) $workspace) $p.Value}
$compilePath=Join-Path $root 'compile_result.json';R5Match $compilePath $t.compile_sha256
R5Match (Join-Path $root 'manifest.json') $t.manifest_sha256
if(-not $fixture){
 $d=Get-Content -LiteralPath (Join-Path $root 'deployment_tests.json') -Raw|ConvertFrom-Json
 if($d.status -ne 'PASS_B6_M6_MIXED_RECOVERABLE_FIXTURE' -or -not $d.recoverable_rollback -or $d.tests_sha256 -ne (R5Hash $testPath) -or $d.installer_sha256 -ne (R5Hash $PSCommandPath)){throw 'Current fixture missing'}
}
$targets=@($files|ForEach-Object {R5Within (Join-Path $game $_.relative) $game});$protected=R5Snapshot $game $targets
if(-not $fixture){
 if($Mode -in @('ValidateInstall','Install')){
  $c=Get-Content -LiteralPath $compilePath -Raw|ConvertFrom-Json
  foreach($p in @($c.protected.PSObject.Properties)+@($c.dependencies.PSObject.Properties)){if($p.Name -notin $targets){R5Match (R5Within $p.Name $game) $p.Value;$protected[$p.Name]=$p.Value}}
 }
 foreach($folder in @('archive/pc/mod','red4ext/plugins','r6/scripts','r6/cache')){
  foreach($p in Get-ChildItem -LiteralPath (Join-Path $game $folder) -Recurse -File){if($p.FullName -notin $targets -and ($folder -eq 'r6/cache' -or $p.Extension -in @('.archive','.xl','.reds','.dll'))){$protected[$p.FullName]=R5Hash $p.FullName}}
 }
}
$receiptPath=Join-Path $audit 'install_receipt.json'
if($Mode -in @('ValidateRollback','Rollback')){
 $r=Get-Content -LiteralPath $receiptPath -Raw|ConvertFrom-Json
 if($r.status -ne 'INSTALLED_B6_M6_NATIVE_AND_VISUAL_LIVE_PENDING' -or $r.game_root -ne $game -or $r.tests_sha256 -ne (R5Hash $testPath) -or $r.installer_sha256 -ne (R5Hash $PSCommandPath) -or @($r.files).Count -ne 7){throw 'Receipt mismatch'}
 foreach($f in $files){
  if(@($r.files|Where-Object {$_.source -eq $f.source -and $_.relative -eq $f.relative -and $_.sha256 -eq $f.sha256 -and $_.predecessor -eq $f.predecessor}).Count -ne 1){throw 'Receipt mapping mismatch'}
  R5Match (Join-Path $game $f.relative) $f.sha256
  if($f.predecessor){R5Match (R5Within (Join-Path (Join-Path $audit 'backup') $f.relative) $audit) $f.predecessor}
 }
 if(Test-Path -LiteralPath (Join-Path $audit 'rollback_receipt.json')){throw 'Already recovered'}
}else{
 if(Test-Path -LiteralPath $receiptPath){throw 'Existing receipt; refuse reinstall'}
 foreach($f in $files){$p=Join-Path $game $f.relative;if($f.predecessor){R5Match $p $f.predecessor}elseif(Test-Path -LiteralPath $p){throw 'Addition already exists'}}
}
R5Closed
if($Mode.StartsWith('Validate')){[ordered]@{status='VALIDATED';mode=$Mode;additions=5;replacements=2;protected_files=$protected.Count}|ConvertTo-Json;return}
New-Item -ItemType Directory -Force $audit|Out-Null;R5Closed
if($Mode -eq 'Install'){
 foreach($f in $files){if($f.predecessor){
  $target=R5Within (Join-Path $game $f.relative) $game;R5Match $target $f.predecessor
  $backup=R5Within (Join-Path (Join-Path $audit 'backup') $f.relative) $audit
  if(Test-Path -LiteralPath $backup){throw 'Backup exists'}
  New-Item -ItemType Directory -Force (Split-Path -Parent $backup)|Out-Null;Copy-Item -LiteralPath $target -Destination $backup;R5Match $backup $f.predecessor
 }}
 foreach($f in $files){
  R5Closed;$target=R5Within (Join-Path $game $f.relative) $game
  if($f.predecessor){R5Match $target $f.predecessor}elseif(Test-Path -LiteralPath $target){throw 'Addition appeared during install'}
  $source=R5Within (Join-Path $workspace $f.source) $workspace;R5Match $source $f.sha256
  New-Item -ItemType Directory -Force (Split-Path -Parent $target)|Out-Null;Copy-Item -LiteralPath $source -Destination $target;R5Match $target $f.sha256
 }
 R5Unchanged $protected
 $result=[ordered]@{status='INSTALLED_B6_M6_NATIVE_AND_VISUAL_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=$files;protected=$protected;tests_sha256=R5Hash $testPath;installer_sha256=R5Hash $PSCommandPath;additions=5;replacements=2;cache_writes=0;deployment_direct_save_writes=0;engine_proof=$false}
 R5Json $receiptPath $result
}else{
 $recoverable=R5Within (Join-Path $audit ('recoverable_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $audit
 foreach($f in $files){
  R5Closed;$target=R5Within (Join-Path $game $f.relative) $game;R5Match $target $f.sha256
  $dest=R5Within (Join-Path $recoverable $f.relative) $recoverable;New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null
  Move-Item -LiteralPath $target -Destination $dest;R5Match $dest $f.sha256
  if($f.predecessor){Copy-Item -LiteralPath (R5Within (Join-Path (Join-Path $audit 'backup') $f.relative) $audit) -Destination $target;R5Match $target $f.predecessor}
 }
 R5Unchanged $protected
 $result=[ordered]@{status='B6_M6_FILES_RECOVERED_NOT_LOADED_OR_NEW_SAVED_WORLD';game_root=$game;recoverable=$recoverable;files=$files};R5Json (Join-Path $audit 'rollback_receipt.json') $result
}
$result.status
