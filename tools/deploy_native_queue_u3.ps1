param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',[string]$AuditDirectory='',[ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall')
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\');$root=Join-Path $workspace 'research/gig_restoration/native_queue_u3';$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077';$fixture=$game.StartsWith($root+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported game root'}
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$root}
if($fixture -and (-not $AuditDirectory -or -not $audit.StartsWith((Split-Path -Parent $game)+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Fixture audit mismatch'}
if(-not $fixture -and $AuditDirectory){throw 'Actual audit must be canonical'}
R5Closed
$mp=Join-Path $root 'manifest.json';$tp=Join-Path $root 'tests.json'
$m=Get-Content $mp -Raw|ConvertFrom-Json;$t=Get-Content $tp -Raw|ConvertFrom-Json
if($t.status -ne 'PASS_U3_OFFLINE_LIVE_PENDING' -or $t.manifest_sha256 -ne (R5Hash $mp) -or -not $t.full_scc -or -not $t.compiled_readback -or -not $t.source_delta_exact){throw 'Tests stale'}
R5Match (Join-Path $workspace 'tools/test_native_queue_u3.py') $t.test_sha256
$mapping=[ordered]@{'build/NativeQueueU3/NativeReuseU1.reds'='r6/scripts/PTFR_NativeReuseU1/NativeReuseU1.reds';'build/NativeQueueU3/GigFamilyB7.reds'='r6/scripts/PTFR_GigFamilyB7/GigFamilyB7.reds'}
$old=@('F1EEAD97F5E3F24EB23C1103899AFCC2464DDF5F860A220F8AB7153E5678CC50','0FFCF6A347426018BBE0A6194DA58B912D31A5A64E142ADA64C4CBC14C3AD8AF')
if($m.files.Count -ne 2){throw 'Exactly two targets required'}
$files=@();$index=0
foreach($source in $mapping.Keys){$f=@($m.files|Where-Object {$_.source -ceq $source -and $_.relative -ceq $mapping[$source]});if($f.Count -ne 1 -or $f[0].predecessor -ne $old[$index]){throw 'Mapping mismatch'};R5Match (R5Within (Join-Path $workspace $source) $workspace) $f[0].sha256;$files+=,$f[0];$index++}
$targets=@($files|ForEach-Object {R5Within (Join-Path $game $_.relative) $game})
if(-not $fixture){
 $d=Get-Content (Join-Path $root 'deployment_tests.json') -Raw|ConvertFrom-Json
 if($d.status -ne 'PASS_U3_RECOVERABLE_FIXTURE' -or $d.installer_sha256 -ne (R5Hash $PSCommandPath) -or $d.tests_sha256 -ne (R5Hash $tp)){throw 'Fixture tests stale'}
 foreach($p in $t.dependencies.PSObject.Properties){if($p.Name -notin $targets){R5Match $p.Name $p.Value}}
}
$protected=R5Snapshot $game $targets
if(-not $fixture){foreach($folder in @('archive/pc/mod','red4ext/plugins','r6/scripts','r6/cache')){foreach($p in Get-ChildItem -LiteralPath (Join-Path $game $folder) -Recurse -File){if($p.FullName -notin $targets -and ($folder -eq 'r6/cache' -or $p.Extension -in @('.archive','.xl','.reds','.dll'))){$protected[$p.FullName]=R5Hash $p.FullName}}}}
$rp=Join-Path $audit 'install_receipt.json'
if($Mode -in @('ValidateRollback','Rollback')){
 $r=Get-Content $rp -Raw|ConvertFrom-Json
 if($r.status -ne 'INSTALLED_U3_QUEUE_REPAIR' -or $r.game_root -ne $game -or $r.manifest_sha256 -ne (R5Hash $mp) -or $r.installer_sha256 -ne (R5Hash $PSCommandPath)){throw 'Receipt mismatch'}
 foreach($f in $files){R5Match (Join-Path $game $f.relative) $f.sha256;R5Match (Join-Path $audit ('backup/'+$f.relative)) $f.predecessor}
 if(Test-Path (Join-Path $audit 'rollback_receipt.json')){throw 'Already recovered'}
}else{
 if(Test-Path $rp){throw 'Existing receipt; refuse reinstall'}
 foreach($f in $files){R5Match (Join-Path $game $f.relative) $f.predecessor;if(Test-Path (Join-Path $audit ('backup/'+$f.relative))){throw 'Backup exists'}}
}
R5Closed
if($Mode.StartsWith('Validate')){[ordered]@{status='VALIDATED';mode=$Mode;replacements=2;protected_files=$protected.Count}|ConvertTo-Json;return}
New-Item -ItemType Directory -Force $audit|Out-Null
if($Mode -eq 'Install'){
 foreach($f in $files){$backup=R5Within (Join-Path $audit ('backup/'+$f.relative)) $audit;New-Item -ItemType Directory -Force (Split-Path -Parent $backup)|Out-Null;Copy-Item -LiteralPath (Join-Path $game $f.relative) -Destination $backup;R5Match $backup $f.predecessor}
 foreach($f in $files){R5Closed;R5Match (Join-Path $game $f.relative) $f.predecessor;R5Match (Join-Path $workspace $f.source) $f.sha256;Copy-Item -LiteralPath (Join-Path $workspace $f.source) -Destination (Join-Path $game $f.relative);R5Match (Join-Path $game $f.relative) $f.sha256}
 R5Unchanged $protected
 R5Json $rp ([ordered]@{status='INSTALLED_U3_QUEUE_REPAIR';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=$files;manifest_sha256=R5Hash $mp;tests_sha256=R5Hash $tp;installer_sha256=R5Hash $PSCommandPath;protected=$protected;replacements=2;additions=0;cache_writes=0;direct_save_writes=0;engine_proof=$false})
 'INSTALLED_U3_QUEUE_REPAIR'
}else{
 $recoverable=R5Within (Join-Path $audit ('recoverable_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $audit
 foreach($f in $files){R5Closed;$target=R5Within (Join-Path $game $f.relative) $game;R5Match $target $f.sha256;$dest=R5Within (Join-Path $recoverable $f.relative) $recoverable;New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null;Move-Item -LiteralPath $target -Destination $dest;Copy-Item -LiteralPath (Join-Path $audit ('backup/'+$f.relative)) -Destination $target;R5Match $target $f.predecessor}
 R5Unchanged $protected;R5Json (Join-Path $audit 'rollback_receipt.json') ([ordered]@{status='U3_FILES_RECOVERED_NOT_WORLD';recoverable=$recoverable;warning='Restores old premature lock. Cannot rewind runtime or new saves.'});'U3_FILES_RECOVERED_NOT_WORLD'
}
