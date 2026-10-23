param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$AuditDirectory='',
 [ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall'
)
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$root=Join-Path $workspace 'research\gig_restoration\markers_m6_1'
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$fixture=$game.StartsWith($root+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported game root'}
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$root}
if($fixture -and (-not $AuditDirectory -or -not $audit.StartsWith((Split-Path -Parent $game)+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Fixture audit mismatch'}
if(-not $fixture -and $AuditDirectory){throw 'Actual audit must be canonical'}
$testPath=Join-Path $root 'tests.json'
$t=Get-Content -LiteralPath $testPath -Raw|ConvertFrom-Json
if($t.status -ne 'PASS_M6_1_SOURCE_REGRESSION_RENDERER_PENDING' -or -not $t.presentation_only -or -not $t.source_contracts -or @($t.files).Count -ne 1){throw 'M6.1 checks missing'}
$f=$t.files[0]
if($f.source -ne 'redscript/PTFR_GigMarkersM6/GigMarkersM6.reds' -or $f.relative -ne 'r6/scripts/PTFR_GigMarkersM6/GigMarkersM6.reds' -or $f.predecessor -ne 'E1B5E4323DD4B72A95EF9B293B31C624EA87067FD26C15EA0B41541D03A09DD9'){throw 'Mapping mismatch'}
$target=R5Within (Join-Path $game $f.relative) $game
$source=R5Within (Join-Path $workspace $f.source) $workspace
R5Match $source $f.sha256
foreach($p in @($t.tools.PSObject.Properties)+@($t.pinned_predecessor_evidence.PSObject.Properties)){R5Match (R5Within (Join-Path $workspace $p.Name) $workspace) $p.Value}
$compilePath=Join-Path $root 'compile_result.json';R5Match $compilePath $t.compile_sha256
$protected=R5Snapshot $game @($target)
if(-not $fixture){
 $d=Get-Content -LiteralPath (Join-Path $root 'deployment_tests.json') -Raw|ConvertFrom-Json
 if($d.status -ne 'PASS_M6_1_RECOVERABLE_FIXTURE' -or -not $d.recoverable_rollback -or $d.tests_sha256 -ne (R5Hash $testPath) -or $d.installer_sha256 -ne (R5Hash $PSCommandPath)){throw 'Current fixture missing'}
 if($Mode -in @('ValidateInstall','Install')){
  $c=Get-Content -LiteralPath $compilePath -Raw|ConvertFrom-Json
  foreach($p in @($c.protected.PSObject.Properties)+@($c.dependencies.PSObject.Properties)){if($p.Name -ne $target){R5Match (R5Within $p.Name $game) $p.Value;$protected[$p.Name]=$p.Value}}
 }
 foreach($folder in @('archive/pc/mod','red4ext/plugins','r6/scripts','r6/cache')){
  foreach($p in Get-ChildItem -LiteralPath (Join-Path $game $folder) -Recurse -File){if($p.FullName -ne $target -and ($folder -eq 'r6/cache' -or $p.Extension -in @('.archive','.xl','.reds','.dll'))){$protected[$p.FullName]=R5Hash $p.FullName}}
 }
}
$receiptPath=Join-Path $audit 'install_receipt.json'
$backup=R5Within (Join-Path (Join-Path $audit 'backup') $f.relative) $audit
if($Mode -in @('ValidateRollback','Rollback')){
 $r=Get-Content -LiteralPath $receiptPath -Raw|ConvertFrom-Json
 if($r.status -ne 'INSTALLED_M6_1_RENDERER_PENDING' -or $r.game_root -ne $game -or $r.tests_sha256 -ne (R5Hash $testPath) -or $r.installer_sha256 -ne (R5Hash $PSCommandPath) -or @($r.files).Count -ne 1){throw 'Receipt mismatch'}
 $rf=$r.files[0]
 if($rf.source -ne $f.source -or $rf.relative -ne $f.relative -or $rf.sha256 -ne $f.sha256 -or $rf.predecessor -ne $f.predecessor){throw 'Receipt mapping mismatch'}
 R5Match $target $f.sha256;R5Match $backup $f.predecessor
 if(Test-Path -LiteralPath (Join-Path $audit 'rollback_receipt.json')){throw 'Already recovered'}
}else{
 if(Test-Path -LiteralPath $receiptPath){throw 'Existing receipt; refuse reinstall'}
 R5Match $target $f.predecessor
}
R5Closed
if($Mode.StartsWith('Validate')){[ordered]@{status='VALIDATED';mode=$Mode;replacements=1;protected_files=$protected.Count}|ConvertTo-Json;return}
New-Item -ItemType Directory -Force $audit|Out-Null;R5Closed
if($Mode -eq 'Install'){
 if(Test-Path -LiteralPath $backup){throw 'Backup exists'}
 New-Item -ItemType Directory -Force (Split-Path -Parent $backup)|Out-Null
 Copy-Item -LiteralPath $target -Destination $backup;R5Match $backup $f.predecessor
 R5Closed;R5Match $target $f.predecessor;R5Match $source $f.sha256
 Copy-Item -LiteralPath $source -Destination $target;R5Match $target $f.sha256
 R5Unchanged $protected
 $result=[ordered]@{status='INSTALLED_M6_1_RENDERER_PENDING';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=@($f);protected=$protected;tests_sha256=R5Hash $testPath;installer_sha256=R5Hash $PSCommandPath;replacements=1;cache_writes=0;direct_save_writes=0;engine_proof=$false}
 R5Json $receiptPath $result
}else{
 $recoverable=R5Within (Join-Path $audit ('recoverable_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $audit
 $dest=R5Within (Join-Path $recoverable $f.relative) $recoverable
 New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null
 R5Closed;R5Match $target $f.sha256;Move-Item -LiteralPath $target -Destination $dest;R5Match $dest $f.sha256
 Copy-Item -LiteralPath $backup -Destination $target;R5Match $target $f.predecessor
 R5Unchanged $protected
 $result=[ordered]@{status='M6_1_FILE_RECOVERED';game_root=$game;recoverable=$recoverable;files=@($f)}
 R5Json (Join-Path $audit 'rollback_receipt.json') $result
}
$result.status
