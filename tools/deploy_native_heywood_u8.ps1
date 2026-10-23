param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',[string]$AuditDirectory='',[ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall')
. (Join-Path $PSScriptRoot 'shark_b7_2_helpers.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\');$root=Join-Path $workspace 'research/gig_restoration/native_heywood_u8';$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077';$fixture=$game.StartsWith($root+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported game root'}
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$root}
if($fixture -and (-not $AuditDirectory -or -not $audit.StartsWith((Split-Path -Parent $game)+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Fixture audit mismatch'}
if(-not $fixture -and $AuditDirectory){throw 'Actual audit must be canonical'}
R5Closed
$mp=Join-Path $root 'manifest.json';$tp=Join-Path $root 'tests.json';$m=Get-Content $mp -Raw|ConvertFrom-Json;$t=Get-Content $tp -Raw|ConvertFrom-Json
if($t.status -ne 'PASS_U8_OFFLINE_LIVE_PENDING' -or $t.manifest_sha256 -ne (R5Hash $mp) -or -not $t.full_scc -or -not $t.compiled_readback -or -not $t.exact_stock_delta){throw 'Tests stale'}
R5Match (Join-Path $workspace 'tools/test_native_heywood_u8.py') $t.test_sha256
R5Match (Join-Path $workspace 'tools/build_native_heywood_u8.ps1') $m.builder_sha256
foreach($p in $t.source_pins.PSObject.Properties){R5Match (R5Within (Join-Path $workspace $p.Name) $workspace) $p.Value}
$map=[ordered]@{
 'build/NativeHeywoodU8/TowerContinued_NativeHeywoodU8.archive'='archive/pc/mod/TowerContinued_NativeHeywoodU8.archive'
 'build/NativeHeywoodU8/TowerContinued_NativeHeywoodU8.archive.xl'='archive/pc/mod/TowerContinued_NativeHeywoodU8.archive.xl'
 'redscript/PTFR_NativeHeywoodU8/NativeHeywoodU8.reds'='r6/scripts/PTFR_NativeHeywoodU8/NativeHeywoodU8.reds'
 'build/NativeHeywoodU8/GigFamilyB7.reds'='r6/scripts/PTFR_GigFamilyB7/GigFamilyB7.reds'
}
$old='51AD9771C8FB0F18D1BF754CD6A2F78E9BDEE78C08AB3657680E0D22E355A87F'
if($m.files.Count -ne 4){throw 'Exactly four targets required'}
$files=@();foreach($source in $map.Keys){$f=@($m.files|Where-Object {$_.source -ceq $source -and $_.relative -ceq $map[$source]});if($f.Count -ne 1){throw 'Mapping mismatch'};R5Match (R5Within (Join-Path $workspace $source) $workspace) $f[0].sha256;$files+=,$f[0]}
if($files[3].predecessor -ne $old -or @($files[0..2]|Where-Object predecessor).Count){throw 'Predecessor mismatch'}
$targets=@($files|ForEach-Object {R5Within (Join-Path $game $_.relative) $game})
B71Parser|Out-Null;$xl=Get-Content (Join-Path $workspace $files[1].source) -Raw
if($m.boots.Count -ne 24 -or $xl -cne (B71Render @($m.boots))){throw 'Unexpected registrations'};B71Parse $xl|Out-Null
if(-not $fixture){
 $d=Get-Content (Join-Path $root 'deployment_tests.json') -Raw|ConvertFrom-Json
 if($d.status -ne 'PASS_U8_RECOVERABLE_FIXTURE' -or $d.installer_sha256 -ne (R5Hash $PSCommandPath) -or $d.tests_sha256 -ne (R5Hash $tp)){throw 'Fixture tests stale'}
 $inventory=@(B72Inventory $game|Where-Object path -cnotin $m.boots)
 foreach($depot in $m.boots){
  $c=B72CollisionCheck $inventory $workspace $depot;$expected=@($m.collisions|Where-Object depot -ceq $depot)
  if($expected.Count -ne 1 -or $c.new_id -ne $expected[0].node_id -or $c.new_id -in $inventory.id){throw 'Registration collision drift'}
  $inventory+=@{path=$depot;id=$c.new_id;source='U8_batch'}
 }
 foreach($p in $t.dependencies.PSObject.Properties){if($p.Name -notin $targets){R5Match $p.Name $p.Value}}
 # Pin proven phone and Jeopardy dependencies, without changing their files.
 foreach($receipt in @('native_support_u7','native_jeopardy_u4')){
  $r=Get-Content (Join-Path $workspace ('research/gig_restoration/'+$receipt+'/install_receipt.json')) -Raw|ConvertFrom-Json
  foreach($f in $r.files){$p=Join-Path $game $f.relative;if($p -notin $targets){R5Match $p $f.sha256}}
 }
}
$protected=R5Snapshot $game $targets
if(-not $fixture){
 foreach($folder in @('archive/pc/mod','red4ext/plugins','r6/scripts','r6/cache')){foreach($p in Get-ChildItem -LiteralPath (Join-Path $game $folder) -Recurse -File){if($p.FullName -notin $targets -and ($folder -eq 'r6/cache' -or $p.Extension -in @('.archive','.xl','.reds','.dll'))){$protected[$p.FullName]=R5Hash $p.FullName}}}
 $save='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077\ManualSave-20\sav.dat';R5Match $save '0E531F856D4233C9C339F45C29405E590861F40B7918CFA082F736BF64D51096';$protected[$save]=R5Hash $save
}
$rp=Join-Path $audit 'install_receipt.json';$backup=Join-Path $audit 'backup/GigFamilyB7.reds'
if($Mode -in @('ValidateRollback','Rollback')){
 $r=Get-Content $rp -Raw|ConvertFrom-Json
 if($r.status -ne 'INSTALLED_U8_ENGINE_PENDING' -or $r.game_root -ne $game -or $r.manifest_sha256 -ne (R5Hash $mp) -or $r.installer_sha256 -ne (R5Hash $PSCommandPath)){throw 'Receipt mismatch'}
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
 R5Json $rp ([ordered]@{status='INSTALLED_U8_ENGINE_PENDING';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=$files;manifest_sha256=R5Hash $mp;tests_sha256=R5Hash $tp;installer_sha256=R5Hash $PSCommandPath;protected=$protected;additions=3;replacements=1;cache_writes=0;direct_save_writes=0;engine_proof=$false})
 'INSTALLED_U8_ENGINE_PENDING'
}else{
 $recoverable=R5Within (Join-Path $audit ('recoverable_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $audit
 foreach($i in @(2,1,0,3)){R5Closed;$f=$files[$i];R5Match $targets[$i] $f.sha256;$dest=R5Within (Join-Path $recoverable $f.relative) $recoverable;New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null;Move-Item -LiteralPath $targets[$i] -Destination $dest;if($i -eq 3){Copy-Item -LiteralPath $backup -Destination $targets[$i];R5Match $targets[$i] $old}}
 R5Unchanged $protected;R5Json (Join-Path $audit 'rollback_receipt.json') ([ordered]@{status='U8_FILES_RECOVERED_NOT_WORLD';recoverable=$recoverable;warning='Reload retained PRE-U8 successful U7-completion save. Do not continue U8-running save with copied B7 requests re-enabled; file recovery cannot rewind native owners, rewards or credits.'});'U8_FILES_RECOVERED_NOT_WORLD'
}
