param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',[string]$AuditDirectory='',[ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall')
. (Join-Path $PSScriptRoot 'shark_b7_2_helpers.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\');$root=Join-Path $workspace 'research\gig_restoration\shark_b7_2';$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077';$fixture=$game.StartsWith($root+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported game root'}
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$root}
if($fixture -and (-not $AuditDirectory -or -not $audit.StartsWith((Split-Path -Parent $game)+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Fixture audit mismatch'}
if(-not $fixture -and $AuditDirectory){throw 'Actual audit must be canonical'}
R5Closed
$testPath=Join-Path $root 'tests.json';$t=Get-Content -LiteralPath $testPath -Raw|ConvertFrom-Json
if($t.status -ne 'PASS_B7_2_SHARK_ALIAS_ENGINE_PENDING' -or -not $t.packed_alias_byte_identical -or -not $t.other_75_bindings_unchanged -or -not $t.collision.collision_free -or $t.collision.old_id -ne 1 -or $t.collision.new_id -ne 55205 -or $t.rejected_cases -ne 5){throw 'B7.2 checks missing'}
$expected=@(
 @{source='build/SharkB7_2/TowerContinued_SharkB7_2.archive';relative='archive/pc/mod/TowerContinued_SharkB7_2.archive';predecessor=$null},
 @{source='build/SharkB7_2/TowerContinued_FamilyB7.archive.xl';relative='archive/pc/mod/TowerContinued_FamilyB7.archive.xl';predecessor='76B32526DB9068D39C9D32C6FB187D4D27697F9F5B5045940388C626C4F3C623'}
)
if(@($t.files).Count -ne 2 -or @($t.files.relative|Select-Object -Unique).Count -ne 2){throw 'Exactly two targets required'}
$files=@();foreach($e in $expected){
 $f=@($t.files|Where-Object {$_.source -eq $e.source -and $_.relative -eq $e.relative -and $_.predecessor -eq $e.predecessor});if($f.Count -ne 1){throw 'Mapping mismatch'}
 R5Match (R5Within (Join-Path $workspace $e.source) $workspace) $f[0].sha256;$files+=,$f[0]
}
foreach($p in @($t.tools.PSObject.Properties)+@($t.pinned.PSObject.Properties)){R5Match (R5Within (Join-Path $workspace $p.Name) $workspace) $p.Value}
B71Parser|Out-Null
B72ValidateXl (Get-Content -LiteralPath (Join-Path $workspace $files[1].source) -Raw) $workspace
if(-not $fixture){
 $d=Get-Content -LiteralPath (Join-Path $root 'deployment_tests.json') -Raw|ConvertFrom-Json
 if($d.status -ne 'PASS_B7_2_RECOVERABLE_FIXTURE' -or -not $d.recoverable_rollback -or $d.tests_sha256 -ne (R5Hash $testPath) -or $d.installer_sha256 -ne (R5Hash $PSCommandPath)){throw 'Current fixture missing'}
 B72CollisionCheck @(B72Inventory $game) $workspace (B72NewPath)|Out-Null
 foreach($f in $t.unchanged_b7_files){R5Match (R5Within (Join-Path $game $f.relative) $game) $f.sha256}
}
$targets=@($files|ForEach-Object {R5Within (Join-Path $game $_.relative) $game});$protected=R5Snapshot $game $targets
if(-not $fixture){
 foreach($folder in @('archive/pc/mod','red4ext/plugins','r6/scripts','r6/cache')){foreach($p in Get-ChildItem -LiteralPath (Join-Path $game $folder) -Recurse -File){if($p.FullName -notin $targets -and ($folder -eq 'r6/cache' -or $p.Extension -in @('.archive','.xl','.reds','.dll'))){$protected[$p.FullName]=R5Hash $p.FullName}}}
}
$receiptPath=Join-Path $audit 'install_receipt.json'
if($Mode -in @('ValidateRollback','Rollback')){
 $r=Get-Content -LiteralPath $receiptPath -Raw|ConvertFrom-Json
 if($r.status -ne 'INSTALLED_B7_2_SHARK_ALIAS_ENGINE_PENDING' -or $r.game_root -ne $game -or $r.tests_sha256 -ne (R5Hash $testPath) -or $r.installer_sha256 -ne (R5Hash $PSCommandPath) -or @($r.files).Count -ne 2){throw 'Receipt mismatch'}
 foreach($f in $files){
  if(@($r.files|Where-Object {$_.source -eq $f.source -and $_.relative -eq $f.relative -and $_.sha256 -eq $f.sha256 -and $_.predecessor -eq $f.predecessor}).Count -ne 1){throw 'Receipt mapping mismatch'}
  R5Match (Join-Path $game $f.relative) $f.sha256;if($f.predecessor){R5Match (R5Within (Join-Path (Join-Path $audit 'backup') $f.relative) $audit) $f.predecessor}
 }
 if(Test-Path -LiteralPath (Join-Path $audit 'rollback_receipt.json')){throw 'Already recovered'}
}else{
 if(Test-Path -LiteralPath $receiptPath){throw 'Existing receipt; refuse reinstall'}
 foreach($f in $files){$p=Join-Path $game $f.relative;if($f.predecessor){R5Match $p $f.predecessor}elseif(Test-Path -LiteralPath $p){throw 'Addition already exists'}}
}
R5Closed
if($Mode.StartsWith('Validate')){[ordered]@{status='VALIDATED';mode=$Mode;additions=1;replacements=1;protected_files=$protected.Count}|ConvertTo-Json;return}
New-Item -ItemType Directory -Force $audit|Out-Null;R5Closed
if($Mode -eq 'Install'){
 foreach($f in $files){if($f.predecessor){
  $target=R5Within (Join-Path $game $f.relative) $game;R5Match $target $f.predecessor;$backup=R5Within (Join-Path (Join-Path $audit 'backup') $f.relative) $audit
  if(Test-Path -LiteralPath $backup){throw 'Backup exists'};New-Item -ItemType Directory -Force (Split-Path -Parent $backup)|Out-Null;Copy-Item -LiteralPath $target -Destination $backup;R5Match $backup $f.predecessor
 }}
 # Install the alias before switching its single registration.
 foreach($f in $files){
  R5Closed;$target=R5Within (Join-Path $game $f.relative) $game;if($f.predecessor){R5Match $target $f.predecessor}elseif(Test-Path -LiteralPath $target){throw 'Addition appeared during install'}
  $source=R5Within (Join-Path $workspace $f.source) $workspace;R5Match $source $f.sha256;New-Item -ItemType Directory -Force (Split-Path -Parent $target)|Out-Null;Copy-Item -LiteralPath $source -Destination $target;R5Match $target $f.sha256
 }
 B72ValidateXl (Get-Content -LiteralPath (Join-Path $game $files[1].relative) -Raw) $workspace
 R5Unchanged $protected
 $result=[ordered]@{status='INSTALLED_B7_2_SHARK_ALIAS_ENGINE_PENDING';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=$files;protected=$protected;tests_sha256=R5Hash $testPath;installer_sha256=R5Hash $PSCommandPath;additions=1;replacements=1;cache_writes=0;deployment_direct_save_writes=0;engine_proof=$false}
 R5Json $receiptPath $result
}else{
 $recoverable=R5Within (Join-Path $audit ('recoverable_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $audit
 # Restore the prior registration before removing the additive alias archive.
 for($i=$files.Count-1;$i -ge 0;$i--){$f=$files[$i]
  R5Closed;$target=R5Within (Join-Path $game $f.relative) $game;R5Match $target $f.sha256;$dest=R5Within (Join-Path $recoverable $f.relative) $recoverable
  New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null;Move-Item -LiteralPath $target -Destination $dest;R5Match $dest $f.sha256
  if($f.predecessor){Copy-Item -LiteralPath (R5Within (Join-Path (Join-Path $audit 'backup') $f.relative) $audit) -Destination $target;R5Match $target $f.predecessor}
 }
 R5Unchanged $protected;$result=[ordered]@{status='B7_2_FILES_RECOVERED_NOT_WORLD';game_root=$game;recoverable=$recoverable;files=$files;warning='Original Shark collision returns; file rollback cannot rewind a running/new-saved quest owner.'};R5Json (Join-Path $audit 'rollback_receipt.json') $result
}
$result.status
