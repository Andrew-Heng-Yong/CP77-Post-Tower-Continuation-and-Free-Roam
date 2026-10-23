param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$AuditDirectory='',
 [ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall'
)
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\');$root=Join-Path $workspace 'research\gig_restoration\fresh_b5'
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\');$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$fixture=$game.StartsWith($root+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported game root'}
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$root}
if($fixture -and (-not $AuditDirectory -or -not $audit.StartsWith((Split-Path -Parent $game)+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Fixture audit mismatch'}
if(-not $fixture -and $AuditDirectory){throw 'Actual audit must be canonical'}
$testPath=Join-Path $root 'tests.json';$t=Get-Content $testPath -Raw|ConvertFrom-Json
if($t.status -ne 'PASS_B5_OFFLINE_NOT_ENGINE_PROOF' -or -not $t.r3_persistent_definition_cutoff_unchanged -or -not $t.equipmentex_full_compile -or $t.new_gig_adapters -ne 2 -or $t.total_gig_adapters -ne 5 -or $t.pending_gig_adapters -ne 67 -or $t.completed_replay_adapters -ne 0){throw 'Current B5 checks missing'}
$expected=@(
 @{source='build/FreshGigsB5/TowerContinued_FreshB5.archive';relative='archive/pc/mod/TowerContinued_FreshB5.archive'},
 @{source='archive/fresh_b5/TowerContinued_FreshB5.archive.xl';relative='archive/pc/mod/TowerContinued_FreshB5.archive.xl'},
 @{source='redscript/PTFR_FreshGigsB5/FreshGigsB5.reds';relative='r6/scripts/PTFR_FreshGigsB5/FreshGigsB5.reds'},
 @{source='diagnostics/PTFR_FreshGigsB5/init.lua';relative='bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_FreshGigsB5/init.lua'},
 @{source='redscript/PTFR_ActivityStateR3/ActivityStateR3.reds';relative='r6/scripts/PTFR_ActivityStateR3/ActivityStateR3.reds'}
)
if(@($t.files).Count -ne 5 -or @($t.files.relative|Select-Object -Unique).Count -ne 5){throw 'Five-file scope required'}
$files=@();foreach($e in $expected){$f=@($t.files|Where-Object {$_.source -eq $e.source -and $_.relative -eq $e.relative});if($f.Count -ne 1){throw 'Mapping mismatch'};R5Match (R5Within (Join-Path $workspace $e.source) $workspace) $f[0].sha256;$files+=,$f[0]}
$old='AFB91B25C44955BD7DD624433F0221C641F2C45DE048B6D56B9BC324E72A77EA'
if(@($files|Where-Object {$_.predecessor -ne ''}).Count -ne 1 -or $files[4].predecessor -ne $old){throw 'Wrong dispatcher predecessor'}
foreach($p in $t.tools.PSObject.Properties){R5Match (R5Within (Join-Path $workspace $p.Name) $workspace) $p.Value}
foreach($p in $t.source_pins.PSObject.Properties){R5Match (R5Within (Join-Path $workspace $p.Name) $workspace) $p.Value}
$compilePath=Join-Path $root 'compile_result.json';R5Match $compilePath $t.compile_sha256;R5Match (Join-Path $root 'manifest.json') $t.manifest_sha256
if(-not $fixture){$d=Get-Content (Join-Path $root 'deployment_tests.json') -Raw|ConvertFrom-Json;if($d.status -ne 'PASS_B5_MIXED_DEPLOYMENT_FIXTURE' -or -not $d.recoverable_rollback -or $d.tests_sha256 -ne (R5Hash $testPath) -or $d.installer_sha256 -ne (R5Hash $PSCommandPath)){throw 'Current recoverable fixture checks missing'}}
$targets=@($files|ForEach-Object {R5Within (Join-Path $game $_.relative) $game});$protected=R5Snapshot $game $targets
if(-not $fixture){
 $c=Get-Content $compilePath -Raw|ConvertFrom-Json
 foreach($p in @($c.protected.PSObject.Properties)+@($c.dependencies.PSObject.Properties)){if($p.Name -notin $targets){R5Match (R5Within $p.Name $game) $p.Value;$protected[$p.Name]=$p.Value}}
 foreach($folder in @('archive/pc/mod','red4ext/plugins','r6/scripts')){foreach($p in Get-ChildItem -LiteralPath (Join-Path $game $folder) -Recurse -File){if($p.FullName -notin $targets -and $p.Extension -in @('.archive','.xl','.reds','.dll')){$protected[$p.FullName]=R5Hash $p.FullName}}}
}
$receiptPath=Join-Path $audit 'install_receipt.json'
if($Mode -in @('ValidateRollback','Rollback')){
 $r=Get-Content $receiptPath -Raw|ConvertFrom-Json
 if($r.status -ne 'INSTALLED_B5_TWO_FRESH_GIGS_LIVE_PENDING' -or $r.game_root -ne $game -or $r.tests_sha256 -ne (R5Hash $testPath) -or $r.installer_sha256 -ne (R5Hash $PSCommandPath) -or @($r.files).Count -ne 5){throw 'Receipt mismatch'}
 foreach($f in $files){if(@($r.files|Where-Object {$_.source -eq $f.source -and $_.relative -eq $f.relative -and $_.sha256 -eq $f.sha256 -and $_.predecessor -eq $f.predecessor}).Count -ne 1){throw 'Receipt scope mismatch'};R5Match (Join-Path $game $f.relative) $f.sha256;if($f.predecessor){R5Match (R5Within (Join-Path (Join-Path $audit 'backup') $f.relative) $audit) $f.predecessor}}
 if(Test-Path (Join-Path $audit 'rollback_receipt.json')){throw 'Already recovered'}
}else{
 if(Test-Path $receiptPath){throw 'Existing receipt; refuse reinstall'}
 foreach($f in $files){$target=R5Within (Join-Path $game $f.relative) $game;if($f.predecessor){R5Match $target $f.predecessor}else{if(Test-Path $target){throw 'Addition exists; no overwrite'}}}
}
R5Closed
if($Mode.StartsWith('Validate')){[ordered]@{status='VALIDATED';mode=$Mode;additions=4;replacements=1;protected_files=$protected.Count;native_new_gigs=2}|ConvertTo-Json;return}
New-Item -ItemType Directory -Force $audit|Out-Null
R5Closed
if($Mode -eq 'Install'){
 foreach($f in $files){
  R5Closed;$target=R5Within (Join-Path $game $f.relative) $game
  if($f.predecessor){R5Match $target $f.predecessor;$backup=R5Within (Join-Path (Join-Path $audit 'backup') $f.relative) $audit;if(Test-Path $backup){throw 'Backup already exists'};New-Item -ItemType Directory -Force (Split-Path -Parent $backup)|Out-Null;Copy-Item -LiteralPath $target -Destination $backup;R5Match $backup $f.predecessor}else{if(Test-Path $target){throw 'Addition appeared after preflight'}}
  New-Item -ItemType Directory -Force (Split-Path -Parent $target)|Out-Null;Copy-Item -LiteralPath (R5Within (Join-Path $workspace $f.source) $workspace) -Destination $target;R5Match $target $f.sha256
 }
 R5Unchanged $protected
 $result=[ordered]@{status='INSTALLED_B5_TWO_FRESH_GIGS_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=$files;protected=$protected;tests_sha256=R5Hash $testPath;installer_sha256=R5Hash $PSCommandPath;additions=4;replacements=1;new_native_gig_adapters=2;total_native_gig_adapters=5;pending_native_gig_adapters=67;completed_replay_adapters=0;cache_writes=0;deployment_direct_save_writes=0;live_proof=$false}
 R5Json $receiptPath $result
}else{
 $recoverable=R5Within (Join-Path $audit ('recoverable_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $audit
 foreach($f in $files){R5Closed;$target=R5Within (Join-Path $game $f.relative) $game;$dest=R5Within (Join-Path $recoverable $f.relative) $recoverable;New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null;Move-Item -LiteralPath $target -Destination $dest;R5Match $dest $f.sha256;if($f.predecessor){Copy-Item -LiteralPath (R5Within (Join-Path (Join-Path $audit 'backup') $f.relative) $audit) -Destination $target;R5Match $target $f.predecessor}}
 R5Unchanged $protected;$result=[ordered]@{status='B5_FILES_RECOVERED_NOT_LOADED_OR_NEW_SAVED_WORLD';game_root=$game;recoverable=$recoverable;files=$files};R5Json (Join-Path $audit 'rollback_receipt.json') $result
}
$result.status
