param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',[string]$AuditDirectory='',[ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall')
. (Join-Path $PSScriptRoot 'shark_b7_2_helpers.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\');$root=Join-Path $workspace 'research/gig_restoration/native_reuse_u1';$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077';$fixture=$game.StartsWith($root+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported game root'}
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$root}
if($fixture -and (-not $AuditDirectory -or -not $audit.StartsWith((Split-Path -Parent $game)+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Fixture audit mismatch'}
if(-not $fixture -and $AuditDirectory){throw 'Actual audit must be canonical'}
R5Closed
$mp=Join-Path $root 'manifest.json';$m=Get-Content $mp -Raw|ConvertFrom-Json;$tp=Join-Path $root 'tests.json';$t=Get-Content $tp -Raw|ConvertFrom-Json
if($t.status -ne 'PASS_U1_OFFLINE_ENGINE_PENDING' -or $t.manifest_sha256 -ne (R5Hash $mp) -or -not $t.full_scc -or -not $t.compiled_readback -or -not $t.wrapper_payload_comparison){throw 'U1 tests missing/stale'}
$mapping=[ordered]@{
 'build/NativeReuseU1/TowerContinued_NativeReuseU1.archive'='archive/pc/mod/TowerContinued_NativeReuseU1.archive'
 'build/NativeReuseU1/TowerContinued_NativeReuseU1.archive.xl'='archive/pc/mod/TowerContinued_NativeReuseU1.archive.xl'
 'redscript/PTFR_NativeReuseU1/NativeReuseU1.reds'='r6/scripts/PTFR_NativeReuseU1/NativeReuseU1.reds'
 'build/NativeReuseU1/GigFamilyB7.reds'='r6/scripts/PTFR_GigFamilyB7/GigFamilyB7.reds'
}
if($m.files.Count -ne 4 -or @($m.files.relative|Select-Object -Unique).Count -ne 4){throw 'Exactly four targets required'}
$old='9BC70799B64D4A6EB8B605CCC51ECB1FB9C6D378F060B10EF79E2B7C6A92CD51'
$files=@();foreach($source in $mapping.Keys){$f=@($m.files|Where-Object {$_.source -ceq $source -and $_.relative -ceq $mapping[$source]});if($f.Count -ne 1){throw 'Mapping mismatch'};R5Match (R5Within (Join-Path $workspace $source) $workspace) $f[0].sha256;$files+=,$f[0]}
B71Parser|Out-Null
$xl=Get-Content (Join-Path $workspace $files[1].source) -Raw
if($xl -cne (B71Render @($m.depot))){throw 'Unexpected U1 registration'};B71Parse $xl|Out-Null
if(-not $fixture){
 $d=Get-Content (Join-Path $root 'deployment_tests.json') -Raw|ConvertFrom-Json
 if($d.status -ne 'PASS_U1_RECOVERABLE_FIXTURE' -or $d.installer_sha256 -ne (R5Hash $PSCommandPath) -or $d.tests_sha256 -ne (R5Hash $tp)){throw 'Deployment fixture stale'}
 $inv=@(B72Inventory $game|Where-Object path -cne $m.depot)
 $collision=B72CollisionCheck $inv $workspace $m.depot;if($collision.new_id -ne $m.collision.new_id){throw 'Collision inventory drift'}
 foreach($p in $t.dependencies.PSObject.Properties){if($p.Name -ne (Join-Path $game $files[3].relative)){R5Match $p.Name $p.Value}}
}
$targets=@($files|ForEach-Object {R5Within (Join-Path $game $_.relative) $game});$protected=R5Snapshot $game $targets
if(-not $fixture){foreach($folder in @('archive/pc/mod','red4ext/plugins','r6/scripts','r6/cache')){foreach($p in Get-ChildItem -LiteralPath (Join-Path $game $folder) -Recurse -File){if($p.FullName -notin $targets -and ($folder -eq 'r6/cache' -or $p.Extension -in @('.archive','.xl','.reds','.dll'))){$protected[$p.FullName]=R5Hash $p.FullName}}}}
$rp=Join-Path $audit 'install_receipt.json';$backup=Join-Path $audit 'backup/GigFamilyB7.reds'
if($Mode -in @('ValidateRollback','Rollback')){
 $r=Get-Content $rp -Raw|ConvertFrom-Json
 if($r.status -ne 'INSTALLED_U1_ENGINE_PENDING' -or $r.game_root -ne $game -or $r.manifest_sha256 -ne (R5Hash $mp) -or $r.installer_sha256 -ne (R5Hash $PSCommandPath)){throw 'Receipt mismatch'}
 foreach($f in $files){R5Match (Join-Path $game $f.relative) $f.sha256};R5Match $backup $old
 if(Test-Path (Join-Path $audit 'rollback_receipt.json')){throw 'Already recovered'}
}else{
 if(Test-Path $rp){throw 'Existing receipt; refuse reinstall'}
 for($i=0;$i -lt 3;$i++){if(Test-Path $targets[$i]){throw 'Addition already exists'}};R5Match $targets[3] $old
}
R5Closed
if($Mode.StartsWith('Validate')){[ordered]@{status='VALIDATED';mode=$Mode;additions=3;replacements=1;protected_files=$protected.Count}|ConvertTo-Json;return}
New-Item -ItemType Directory -Force $audit|Out-Null
if($Mode -eq 'Install'){
 if(Test-Path $backup){throw 'Backup exists'};New-Item -ItemType Directory -Force (Split-Path -Parent $backup)|Out-Null;Copy-Item -LiteralPath $targets[3] -Destination $backup;R5Match $backup $old
 # Interlock first; game must remain closed through all four writes.
 foreach($i in @(3,0,1,2)){R5Closed;$f=$files[$i];R5Match (Join-Path $workspace $f.source) $f.sha256;if($i -eq 3){R5Match $targets[$i] $old}elseif(Test-Path $targets[$i]){throw 'Addition appeared during install'};New-Item -ItemType Directory -Force (Split-Path -Parent $targets[$i])|Out-Null;Copy-Item -LiteralPath (Join-Path $workspace $f.source) -Destination $targets[$i];R5Match $targets[$i] $f.sha256}
 R5Unchanged $protected
 R5Json $rp ([ordered]@{status='INSTALLED_U1_ENGINE_PENDING';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=$files;manifest_sha256=R5Hash $mp;tests_sha256=R5Hash $tp;installer_sha256=R5Hash $PSCommandPath;protected=$protected;additions=3;replacements=1;cache_writes=0;direct_save_writes=0;engine_proof=$false})
 'INSTALLED_U1_ENGINE_PENDING'
}else{
 $recoverable=R5Within (Join-Path $audit ('recoverable_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $audit
 foreach($i in @(2,1,0,3)){R5Closed;$f=$files[$i];R5Match $targets[$i] $f.sha256;$dest=R5Within (Join-Path $recoverable $f.relative) $recoverable;New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null;Move-Item -LiteralPath $targets[$i] -Destination $dest;if($i -eq 3){Copy-Item -LiteralPath $backup -Destination $targets[$i];R5Match $targets[$i] $old}}
 R5Unchanged $protected;R5Json (Join-Path $audit 'rollback_receipt.json') ([ordered]@{status='U1_FILES_RECOVERED_NOT_WORLD';recoverable=$recoverable;warning='Reload ORIGINAL pre-U1 snapshot after rollback; never reuse a U1-running save with copied Shark enabled.'});'U1_FILES_RECOVERED_NOT_WORLD'
}
