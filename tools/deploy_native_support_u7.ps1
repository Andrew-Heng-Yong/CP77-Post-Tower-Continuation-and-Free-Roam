param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',[string]$AuditDirectory='',[ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall')
. (Join-Path $PSScriptRoot 'shark_b7_2_helpers.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\');$root=Join-Path $workspace 'research/gig_restoration/native_support_u7';$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077';$fixture=$game.StartsWith($root+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported game root'}
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$root}
if($fixture -and (-not $AuditDirectory -or -not $audit.StartsWith((Split-Path -Parent $game)+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Fixture audit mismatch'}
if(-not $fixture -and $AuditDirectory){throw 'Actual audit must be canonical'}
R5Closed
$mp=Join-Path $root 'manifest.json';$tp=Join-Path $root 'tests.json';$m=Get-Content $mp -Raw|ConvertFrom-Json;$t=Get-Content $tp -Raw|ConvertFrom-Json
if($t.status -ne 'PASS_U7_OFFLINE_LIVE_PENDING' -or $t.manifest_sha256 -ne (R5Hash $mp) -or -not $t.full_scc -or -not $t.compiled_readback -or -not $t.wrapper_delta_exact){throw 'Tests stale'}
R5Match (Join-Path $workspace 'tools/test_native_support_u7.py') $t.test_sha256
R5Match (Join-Path $workspace 'tools/build_native_support_u7.ps1') $m.builder_sha256
$map=[ordered]@{
 'build/NativeSupportU7/TowerContinued_NativeSupportU7.archive'='archive/pc/mod/TowerContinued_NativeSupportU7.archive'
 'build/NativeSupportU7/TowerContinued_NativeSupportU7.archive.xl'='archive/pc/mod/TowerContinued_NativeSupportU7.archive.xl'
 'redscript/PTFR_NativeSupportU7/NativeSupportU7.reds'='r6/scripts/PTFR_NativeSupportU7/NativeSupportU7.reds'
 'build/NativeSupportU7/NativePadreU6.reds'='r6/scripts/PTFR_NativePadreU6/NativePadreU6.reds'
}
$old='64CBD55882A42C4D80A90CFA7886DF8199D4E3E045B4907A2A1BF15B0AD31F92'
if($m.files.Count -ne 4){throw 'Exactly four targets required'}
$files=@();foreach($source in $map.Keys){$f=@($m.files|Where-Object {$_.source -ceq $source -and $_.relative -ceq $map[$source]});if($f.Count -ne 1){throw 'Mapping mismatch'};R5Match (R5Within (Join-Path $workspace $source) $workspace) $f[0].sha256;$files+=,$f[0]}
if($files[3].predecessor -ne $old -or @($files[0..2]|Where-Object predecessor).Count){throw 'Predecessor mismatch'}
$targets=@($files|ForEach-Object {R5Within (Join-Path $game $_.relative) $game})
B71Parser|Out-Null;$xl=Get-Content (Join-Path $workspace $files[1].source) -Raw
if($xl -cne (B71Render @($m.depot))){throw 'Unexpected registration'};B71Parse $xl|Out-Null
if(-not $fixture){
 $d=Get-Content (Join-Path $root 'deployment_tests.json') -Raw|ConvertFrom-Json
 if($d.status -ne 'PASS_U7_RECOVERABLE_FIXTURE' -or $d.installer_sha256 -ne (R5Hash $PSCommandPath) -or $d.tests_sha256 -ne (R5Hash $tp)){throw 'Fixture tests stale'}
 $inventory=@(B72Inventory $game|Where-Object path -cne $m.depot);$collision=B72CollisionCheck $inventory $workspace $m.depot
 if($collision.new_id -ne $m.collision.new_id){throw 'Registration collision drift'}
 foreach($p in $t.dependencies.PSObject.Properties){if($p.Name -notin $targets){R5Match $p.Name $p.Value}}
}
$protected=R5Snapshot $game $targets
if(-not $fixture){foreach($folder in @('archive/pc/mod','red4ext/plugins','r6/scripts','r6/cache')){foreach($p in Get-ChildItem -LiteralPath (Join-Path $game $folder) -Recurse -File){if($p.FullName -notin $targets -and ($folder -eq 'r6/cache' -or $p.Extension -in @('.archive','.xl','.reds','.dll'))){$protected[$p.FullName]=R5Hash $p.FullName}}}}
$rp=Join-Path $audit 'install_receipt.json';$backup=Join-Path $audit 'backup/NativePadreU6.reds'
if($Mode -in @('ValidateRollback','Rollback')){
 $r=Get-Content $rp -Raw|ConvertFrom-Json
 if($r.status -ne 'INSTALLED_U7_ENGINE_PENDING' -or $r.game_root -ne $game -or $r.manifest_sha256 -ne (R5Hash $mp) -or $r.installer_sha256 -ne (R5Hash $PSCommandPath)){throw 'Receipt mismatch'}
 foreach($f in $files){R5Match (Join-Path $game $f.relative) $f.sha256};R5Match $backup $old
 if(Test-Path (Join-Path $audit 'rollback_receipt.json')){throw 'Already recovered'}
}else{
 if((Test-Path $rp) -or (Test-Path $backup)){throw 'Existing receipt/backup'}
 for($i=0;$i -lt 3;$i++){if(Test-Path $targets[$i]){throw 'Addition exists'}};R5Match $targets[3] $old
}
R5Closed
if($Mode.StartsWith('Validate')){[ordered]@{status='VALIDATED';mode=$Mode;additions=3;replacements=1;protected_files=$protected.Count}|ConvertTo-Json;return}
New-Item -ItemType Directory -Force $audit|Out-Null
if($Mode -eq 'Install'){
 New-Item -ItemType Directory -Force (Split-Path -Parent $backup)|Out-Null;Copy-Item -LiteralPath $targets[3] -Destination $backup;R5Match $backup $old
 foreach($i in @(3,0,1,2)){R5Closed;$f=$files[$i];R5Match (Join-Path $workspace $f.source) $f.sha256;if($i -eq 3){R5Match $targets[$i] $old}elseif(Test-Path $targets[$i]){throw 'Addition appeared'};New-Item -ItemType Directory -Force (Split-Path -Parent $targets[$i])|Out-Null;Copy-Item -LiteralPath (Join-Path $workspace $f.source) -Destination $targets[$i];R5Match $targets[$i] $f.sha256}
 R5Unchanged $protected
 R5Json $rp ([ordered]@{status='INSTALLED_U7_ENGINE_PENDING';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=$files;manifest_sha256=R5Hash $mp;tests_sha256=R5Hash $tp;installer_sha256=R5Hash $PSCommandPath;protected=$protected;additions=3;replacements=1;cache_writes=0;direct_save_writes=0;engine_proof=$false})
 'INSTALLED_U7_ENGINE_PENDING'
}else{
 $recoverable=R5Within (Join-Path $audit ('recoverable_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $audit
 foreach($i in @(2,1,0,3)){R5Closed;$f=$files[$i];R5Match $targets[$i] $f.sha256;$dest=R5Within (Join-Path $recoverable $f.relative) $recoverable;New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null;Move-Item -LiteralPath $targets[$i] -Destination $dest;if($i -eq 3){Copy-Item -LiteralPath $backup -Destination $targets[$i];R5Match $targets[$i] $old}}
 R5Unchanged $protected;R5Json (Join-Path $audit 'rollback_receipt.json') ([ordered]@{status='U7_FILES_RECOVERED_NOT_WORLD';recoverable=$recoverable;warning='Reload original PRE-U6/U4 snapshot. Never continue a U7-running save with standalone U6 enabled; file recovery cannot rewind graph owners or credits.'});'U7_FILES_RECOVERED_NOT_WORLD'
}
