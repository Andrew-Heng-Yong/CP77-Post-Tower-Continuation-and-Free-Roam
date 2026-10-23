param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',[string]$AuditDirectory='',[ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall')
. (Join-Path $PSScriptRoot 'shark_b7_2_helpers.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\');$root=Join-Path $workspace 'research/gig_restoration/native_padre_u6';$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077';$fixture=$game.StartsWith($root+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported game root'}
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$root}
if($fixture -and (-not $AuditDirectory -or -not $audit.StartsWith((Split-Path -Parent $game)+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Fixture audit mismatch'}
if(-not $fixture -and $AuditDirectory){throw 'Actual audit must be canonical'}
R5Closed
$mp=Join-Path $root 'manifest.json';$tp=Join-Path $root 'tests.json';$m=Get-Content $mp -Raw|ConvertFrom-Json;$t=Get-Content $tp -Raw|ConvertFrom-Json
if($t.status -ne 'PASS_U6_OFFLINE_LIVE_PENDING' -or $t.manifest_sha256 -ne (R5Hash $mp) -or -not $t.full_scc -or -not $t.compiled_readback -or -not $t.wrapper_delta_exact){throw 'Tests stale'}
R5Match (Join-Path $workspace 'tools/test_native_padre_u6.py') $t.test_sha256
R5Match (Join-Path $workspace 'tools/build_native_padre_u6.ps1') $m.builder_sha256
$map=[ordered]@{
 'build/NativePadreU6/TowerContinued_NativePadreU6.archive'='archive/pc/mod/TowerContinued_NativePadreU6.archive'
 'build/NativePadreU6/TowerContinued_NativePadreU6.archive.xl'='archive/pc/mod/TowerContinued_NativePadreU6.archive.xl'
 'redscript/PTFR_NativePadreU6/NativePadreU6.reds'='r6/scripts/PTFR_NativePadreU6/NativePadreU6.reds'
}
if($m.files.Count -ne 3){throw 'Exactly three additions required'}
$files=@();foreach($source in $map.Keys){$f=@($m.files|Where-Object {$_.source -ceq $source -and $_.relative -ceq $map[$source]});if($f.Count -ne 1){throw 'Mapping mismatch'};R5Match (R5Within (Join-Path $workspace $source) $workspace) $f[0].sha256;$files+=,$f[0]}
$targets=@($files|ForEach-Object {R5Within (Join-Path $game $_.relative) $game})
B71Parser|Out-Null;$xl=Get-Content (Join-Path $workspace $files[1].source) -Raw
if($xl -cne (B71Render @($m.depot))){throw 'Unexpected registration'};B71Parse $xl|Out-Null
if(-not $fixture){
 $d=Get-Content (Join-Path $root 'deployment_tests.json') -Raw|ConvertFrom-Json
 if($d.status -ne 'PASS_U6_RECOVERABLE_FIXTURE' -or $d.installer_sha256 -ne (R5Hash $PSCommandPath) -or $d.tests_sha256 -ne (R5Hash $tp)){throw 'Fixture tests stale'}
 if($Mode -in @('Install','ValidateInstall')){
  $inventory=@(B72Inventory $game);$collision=B72CollisionCheck $inventory $workspace $m.depot
  if($collision.new_id -ne $m.collision.new_id){throw 'Registration collision drift'}
  foreach($p in $t.dependencies.PSObject.Properties){R5Match $p.Name $p.Value}
 }
}
$protected=R5Snapshot $game $targets
if(-not $fixture){foreach($folder in @('archive/pc/mod','red4ext/plugins','r6/scripts','r6/cache')){foreach($p in Get-ChildItem -LiteralPath (Join-Path $game $folder) -Recurse -File){if($p.FullName -notin $targets -and ($folder -eq 'r6/cache' -or $p.Extension -in @('.archive','.xl','.reds','.dll'))){$protected[$p.FullName]=R5Hash $p.FullName}}}}
$rp=Join-Path $audit 'install_receipt.json'
if($Mode -in @('ValidateRollback','Rollback')){
 $r=Get-Content $rp -Raw|ConvertFrom-Json
 if($r.status -ne 'INSTALLED_U6_ENGINE_PENDING' -or $r.game_root -ne $game -or $r.manifest_sha256 -ne (R5Hash $mp) -or $r.installer_sha256 -ne (R5Hash $PSCommandPath)){throw 'Receipt mismatch'}
 foreach($f in $files){R5Match (Join-Path $game $f.relative) $f.sha256}
 if(Test-Path (Join-Path $audit 'rollback_receipt.json')){throw 'Already recovered'}
}else{
 if(Test-Path $rp){throw 'Existing receipt'}
 foreach($target in $targets){if(Test-Path -LiteralPath $target){throw 'Addition exists'}}
}
R5Closed
if($Mode.StartsWith('Validate')){[ordered]@{status='VALIDATED';mode=$Mode;additions=3;replacements=0;protected_files=$protected.Count}|ConvertTo-Json;return}
New-Item -ItemType Directory -Force $audit|Out-Null
if($Mode -eq 'Install'){
 foreach($i in @(0,1,2)){R5Closed;$f=$files[$i];R5Match (Join-Path $workspace $f.source) $f.sha256;if(Test-Path $targets[$i]){throw 'Addition appeared'};New-Item -ItemType Directory -Force (Split-Path -Parent $targets[$i])|Out-Null;Copy-Item -LiteralPath (Join-Path $workspace $f.source) -Destination $targets[$i];R5Match $targets[$i] $f.sha256}
 R5Unchanged $protected
 R5Json $rp ([ordered]@{status='INSTALLED_U6_ENGINE_PENDING';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=$files;manifest_sha256=R5Hash $mp;tests_sha256=R5Hash $tp;installer_sha256=R5Hash $PSCommandPath;protected=$protected;additions=3;replacements=0;cache_writes=0;direct_save_writes=0;engine_proof=$false})
 'INSTALLED_U6_ENGINE_PENDING'
}else{
 $recoverable=R5Within (Join-Path $audit ('recoverable_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $audit
 foreach($i in @(2,1,0)){R5Closed;$f=$files[$i];R5Match $targets[$i] $f.sha256;$dest=R5Within (Join-Path $recoverable $f.relative) $recoverable;New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null;Move-Item -LiteralPath $targets[$i] -Destination $dest;R5Match $dest $f.sha256}
 R5Unchanged $protected;R5Json (Join-Path $audit 'rollback_receipt.json') ([ordered]@{status='U6_FILES_RECOVERED_NOT_WORLD';recoverable=$recoverable;warning='Reload original PRE-U6 snapshot; file removal cannot rewind native phone owners/state in later saves.'});'U6_FILES_RECOVERED_NOT_WORLD'
}
