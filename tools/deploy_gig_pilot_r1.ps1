param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$AuditDirectory='',
 [ValidateSet('ValidateInstall','Install','ValidateRollback','Rollback')][string]$Mode='ValidateInstall'
)
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$sourceAudit=Join-Path $workspace 'research\gig_restoration\pilot_r1'
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$actual='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$fixture=$game.StartsWith($sourceAudit+'\fixture_',[StringComparison]::OrdinalIgnoreCase)
if($game -ne $actual -and -not $fixture){throw 'Unsupported game root'}
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$sourceAudit}
if($fixture -and (-not $AuditDirectory -or -not $audit.StartsWith((Split-Path -Parent $game)+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'Fixture audit must be inside its fixture directory'}
if(-not $fixture -and $AuditDirectory){throw 'Actual deployment requires canonical audit directory'}
$expected=@(
 @{source='build/GigPilotR1/TowerContinued_GigPilotR1.archive';relative='archive/pc/mod/TowerContinued_GigPilotR1.archive'},
 @{source='archive/gig_pilot_r1/TowerContinued_GigPilotR1.archive.xl';relative='archive/pc/mod/TowerContinued_GigPilotR1.archive.xl'},
 @{source='redscript/PTFR_GigPilotR1/GigPilotR1.reds';relative='r6/scripts/PTFR_GigPilotR1/GigPilotR1.reds'},
 @{source='diagnostics/PTFR_GigPilotR1/init.lua';relative='bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_GigPilotR1/init.lua'}
)
$testsPath=Join-Path $sourceAudit 'tests.json'
$tests=Get-Content -LiteralPath $testsPath -Raw|ConvertFrom-Json
if($tests.status -ne 'PASS_GIG_PILOT_R1_OFFLINE_LIVE_PENDING' -or -not $tests.equipmentex_full_compile -or
 -not $tests.graph.exact_edge_deltas -or -not $tests.graph.prefab_behind_optin -or -not $tests.logger.no_gameplay_writes){throw 'Offline checks missing'}
if(-not $fixture){
 $deployment=Get-Content -LiteralPath (Join-Path $sourceAudit 'deployment_tests.json') -Raw|ConvertFrom-Json
 if($deployment.status -ne 'PASS_SCOPED_DEPLOYMENT_FIXTURE' -or -not $deployment.recoverable_rollback -or
  $deployment.installer_sha256 -ne (R5Hash $PSCommandPath) -or $deployment.tests_sha256 -ne (R5Hash $testsPath)){throw 'Current deployment fixture checks missing'}
}
if(@($tests.files).Count -ne 4 -or @($tests.files.relative|Select-Object -Unique).Count -ne 4){throw 'Four unique additions required'}
$files=@()
foreach($pin in $expected){
 $match=@($tests.files|Where-Object {$_.relative -eq $pin.relative -and $_.source -eq $pin.source})
 if($match.Count -ne 1){throw 'Unexpected deployment mapping'}
 $f=$match[0];R5Match (R5Within (Join-Path $workspace $f.source) $workspace) $f.sha256;$files+=,$f
}
foreach($p in $tests.tools.PSObject.Properties){R5Match (R5Within (Join-Path $workspace $p.Name) $workspace) $p.Value}
$targets=@($files|ForEach-Object {R5Within (Join-Path $game $_.relative) $game})
$protected=R5Snapshot $game $targets
if(-not $fixture){
 foreach($p in @($tests.protected.PSObject.Properties)+@($tests.dependencies.PSObject.Properties)){
  $path=R5Within $p.Name $game;R5Match $path $p.Value;$protected[$path]=$p.Value
 }
 foreach($root in @('archive/pc/mod','red4ext/plugins','r6/scripts')){
  foreach($p in Get-ChildItem -LiteralPath (Join-Path $game $root) -File -Recurse){
   if($p.FullName -notin $targets -and $p.Extension -in @('.archive','.xl','.reds','.dll')){$protected[$p.FullName]=R5Hash $p.FullName}
  }
 }
}
$receiptPath=Join-Path $audit 'install_receipt.json'
$rollback=$Mode -in @('ValidateRollback','Rollback')
if($rollback){
 $receipt=Get-Content -LiteralPath $receiptPath -Raw|ConvertFrom-Json
 if($receipt.status -ne 'INSTALLED_GIG_PILOT_R1_LIVE_PENDING' -or $receipt.game_root -ne $game -or
  $receipt.tests_sha256 -ne (R5Hash $testsPath) -or $receipt.installer_sha256 -ne (R5Hash $PSCommandPath) -or @($receipt.files).Count -ne 4){throw 'Receipt mismatch'}
 foreach($f in $files){
  $entry=@($receipt.files|Where-Object {$_.relative -eq $f.relative -and $_.sha256 -eq $f.sha256 -and $_.source -eq $f.source})
  if($entry.Count -ne 1){throw 'Receipt file mismatch'}
  R5Match (R5Within (Join-Path $game $f.relative) $game) $f.sha256
 }
 if(Test-Path -LiteralPath (Join-Path $audit 'rollback_receipt.json')){throw 'Already rolled back'}
}else{
 if(Test-Path -LiteralPath $receiptPath){throw 'Receipt already exists; refuse reinstall'}
 foreach($target in $targets){if(Test-Path -LiteralPath $target){throw "Addition target exists; refuse overwrite: $target"}}
}
R5Closed
if($Mode.StartsWith('Validate')){
 [ordered]@{status='VALIDATED';mode=$Mode;additions=4;replacements=0;protected_files=$protected.Count;game_root=$game}|ConvertTo-Json
 return
}
New-Item -ItemType Directory -Force $audit|Out-Null
R5Closed
if($Mode -eq 'Install'){
 foreach($f in $files){
  $target=R5Within (Join-Path $game $f.relative) $game
  if(Test-Path -LiteralPath $target){throw 'Target appeared during preflight'}
  New-Item -ItemType Directory -Force (Split-Path -Parent $target)|Out-Null
  Copy-Item -LiteralPath (R5Within (Join-Path $workspace $f.source) $workspace) -Destination $target -ErrorAction Stop
  R5Match $target $f.sha256
 }
 R5Unchanged $protected
 $result=[ordered]@{status='INSTALLED_GIG_PILOT_R1_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;files=$files;tests_sha256=R5Hash $testsPath;installer_sha256=R5Hash $PSCommandPath;protected=$protected;additions=4;replacements=0;save_writes=0;cache_writes=0;live_tested=$false}
 R5Json $receiptPath $result
}else{
 # Recoverable file rollback only. It cannot reverse saved quest/world effects.
 $recoverable=R5Within (Join-Path $audit ('recoverable_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $audit
 foreach($f in $files){
  $target=R5Within (Join-Path $game $f.relative) $game
  $dest=R5Within (Join-Path $recoverable $f.relative) $recoverable
  New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null
  Move-Item -LiteralPath $target -Destination $dest -ErrorAction Stop
  R5Match $dest $f.sha256
 }
 R5Unchanged $protected
 $result=[ordered]@{status='ROLLED_BACK_GIG_PILOT_R1_FILES_ONLY';recoverable=$recoverable;files=$files;game_root=$game;save_writes=0;cache_writes=0}
 R5Json (Join-Path $audit 'rollback_receipt.json') $result
}
$result|Select-Object status,additions,replacements,save_writes,cache_writes|ConvertTo-Json
