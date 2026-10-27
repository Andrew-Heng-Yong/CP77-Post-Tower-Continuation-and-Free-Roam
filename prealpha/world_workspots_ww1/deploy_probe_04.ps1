param(
  [ValidateSet('Validate','Install','Verify','ValidateRollback','Rollback')][string]$Action='Validate',
  [string]$FixtureRoot='',
  [ValidateSet('','AfterBackup','AfterStage','BeforeFirstMove','AfterFirstMove','AfterAllMoves','BeforeReceipt')][string]$TestFailPoint=''
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$candidate=Join-Path $PSScriptRoot 'probe_04'
$manifestPath=Join-Path $candidate 'manifest_01.json'
$manifest=Get-Content -LiteralPath $manifestPath -Raw|ConvertFrom-Json -Depth 20
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$backup=Join-Path $ws 'recovery/world_workspots_ww1_probe_04_01'
$fixture=$FixtureRoot -ne ''
if($fixture){
  $FixtureRoot=[IO.Path]::GetFullPath($FixtureRoot)
  $bound=[IO.Path]::GetFullPath((Join-Path $candidate 'deploy_fixtures_01')).TrimEnd('\')+'\'
  if(!$FixtureRoot.StartsWith($bound,[StringComparison]::OrdinalIgnoreCase)){throw 'Fixture outside prototype fixture directory'}
  $game=Join-Path $FixtureRoot 'game';$backup=Join-Path $FixtureRoot 'backup'
}elseif($TestFailPoint -ne ''){throw 'Failure injection is fixture-only'}
function Safe([string]$root,[string]$relative){
  if([IO.Path]::IsPathRooted($relative) -or $relative.Contains(':') -or @($relative.Replace('\','/').Split('/')) -contains '..'){throw 'Unsafe relative path'}
  $base=[IO.Path]::GetFullPath($root).TrimEnd('\')
  $path=[IO.Path]::GetFullPath((Join-Path $base $relative))
  if(!$path.StartsWith($base+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Target outside intended root'}
  $cursor=$path
  while($cursor){
    if(Test-Path -LiteralPath $cursor){if((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked target path'}}
    $parent=Split-Path $cursor -Parent
    if($parent -eq $cursor){break};$cursor=$parent
  }
  return $path
}
function Hash([string]$path){
  if(!(Test-Path -LiteralPath $path -PathType Leaf)){return $null}
  return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
}
function Closed(){
  if(!$fixture -and @(Get-Process -Name Cyberpunk2077,REDprelauncher -ErrorAction SilentlyContinue).Count){throw 'Close Cyberpunk and launcher before changing files'}
}
function FailAt([string]$point){if($TestFailPoint -ceq $point){throw ('Injected '+$point)}}
Closed
$expected=@('archive/pc/mod/zzzz_PTFR_WW1_Prototype.archive','archive/pc/mod/zzzz_PTFR_WW1_Prototype.archive.xl','r6/scripts/PTFR_WW1_Prototype/WW1Probe.reds')
if($manifest.status -cne 'ADDITIVE_CVI116_PROBE_WITH_STARTUP_STAGED_NOT_INSTALLED' -or $manifest.addon_paths -ne 3 -or $manifest.files.Count -ne 3){throw 'Probe manifest mismatch'}
if(@(Compare-Object ($expected|Sort-Object) @($manifest.files.path|Sort-Object)).Count){throw 'Unexpected addon paths'}
$zip=Join-Path $candidate 'Post-Tower-Continuation-and-Free-Roam-WW1-Scav-probe-unreleased.zip'
$zipReceipt=Get-Content -LiteralPath (Join-Path $candidate 'zip_receipt_01.json') -Raw|ConvertFrom-Json
if((Hash $zip) -cne $zipReceipt.sha256 -or $zipReceipt.files.Count -ne 3){throw 'Prototype ZIP proof mismatch'}
foreach($f in $manifest.files){
  if((Hash (Safe (Join-Path $candidate 'package') $f.path)) -cne $f.sha256){throw ('Candidate changed '+$f.path)}
  [void](Safe $game $f.path)
}
$compiled=Get-Content -LiteralPath (Join-Path $candidate 'compile_01/result.json') -Raw|ConvertFrom-Json
$collisions=Get-Content -LiteralPath (Join-Path $candidate 'collisions_01.json') -Raw|ConvertFrom-Json
if($compiled.status -cne 'PASS' -or $compiled.source_count -ne 65 -or $collisions.collisions.Count -ne 0){throw 'Compile or collision proof failed'}
if(!$fixture){
  $jc1=Get-Content -LiteralPath (Join-Path $ws 'prealpha/coaster_jean_jc1/candidate_01/manifest.json') -Raw|ConvertFrom-Json -Depth 30
  if($jc1.files.Count -ne 51){throw 'JC1 baseline manifest changed'}
  foreach($f in $jc1.files){if((Hash (Safe $game $f.path)) -cne $f.sha256){throw ('JC1 file drift '+$f.path)}}
}
if($Action -eq 'Validate'){
  foreach($f in $manifest.files){if(Test-Path -LiteralPath (Safe $game $f.path)){throw ('Probe target exists '+$f.path)}}
  if(Test-Path -LiteralPath $backup){throw 'Existing prototype recovery folder'}
  @{status='READY';additive_files=3;production_files_preserved=51;installed=$false}|ConvertTo-Json;exit 0
}
$receipt=Safe $backup 'receipt.json'
if($Action -in @('Verify','ValidateRollback','Rollback')){
  if(!(Test-Path -LiteralPath $receipt)){throw 'No successful installation receipt'}
  $r=Get-Content -LiteralPath $receipt -Raw|ConvertFrom-Json
  if($r.status -cne 'INSTALLED' -or $r.zip_sha256 -cne $zipReceipt.sha256){throw 'Recovery receipt mismatch'}
  foreach($f in $manifest.files){if((Hash (Safe $game $f.path)) -cne $f.sha256){throw ('Probe file drift '+$f.path)}}
  if($Action -eq 'Verify'){@{status='VERIFIED';additive_files=3;production_files_preserved=51}|ConvertTo-Json;exit 0}
  if($Action -eq 'ValidateRollback'){@{status='ROLLBACK_READY';remove_files=3}|ConvertTo-Json;exit 0}
  foreach($f in $manifest.files){Remove-Item -LiteralPath (Safe $game $f.path) -Force}
  foreach($f in $manifest.files){if(Test-Path -LiteralPath (Safe $game $f.path)){throw ('Rollback left '+$f.path)}}
  $probeDir=Safe $game 'r6/scripts/PTFR_WW1_Prototype'
  if((Test-Path -LiteralPath $probeDir -PathType Container) -and @(Get-ChildItem -LiteralPath $probeDir -Force).Count -eq 0){Remove-Item -LiteralPath $probeDir}
  $done=[ordered]@{status='ROLLED_BACK';zip_sha256=$zipReceipt.sha256;files_removed=3}
  [IO.File]::WriteAllText((Join-Path $backup 'rollback_receipt.json'),($done|ConvertTo-Json)+"`n",[Text.UTF8Encoding]::new($false))
  $done|ConvertTo-Json;exit 0
}
if($Action -ne 'Install'){throw 'Unsupported action'}
foreach($f in $manifest.files){if(Test-Path -LiteralPath (Safe $game $f.path)){throw ('Probe target exists '+$f.path)}}
if(Test-Path -LiteralPath $backup){throw 'Existing prototype recovery folder'}
New-Item -ItemType Directory -Path $backup -Force|Out-Null
$placed=@()
$staged=@()
try{
  Copy-Item -LiteralPath $manifestPath -Destination (Safe $backup 'install_manifest.json')
  Copy-Item -LiteralPath $zip -Destination (Safe $backup 'probe.zip')
  if((Hash (Safe $backup 'probe.zip')) -cne $zipReceipt.sha256){throw 'Backup ZIP hash mismatch'}
  FailAt 'AfterBackup'
  foreach($f in $manifest.files){
    $target=Safe $game $f.path
    $stage=Safe $game ($f.path+'.ptfr-ww1-stage')
    if(Test-Path -LiteralPath $stage){throw ('Unexpected stage file '+$stage)}
    New-Item -ItemType Directory -Path (Split-Path $target -Parent) -Force|Out-Null
    Copy-Item -LiteralPath (Safe (Join-Path $candidate 'package') $f.path) -Destination $stage
    if((Hash $stage) -cne $f.sha256){throw ('Stage hash mismatch '+$f.path)}
    $staged+=@($stage)
  }
  FailAt 'AfterStage';FailAt 'BeforeFirstMove'
  $index=0
  foreach($f in $manifest.files){
    $stage=Safe $game ($f.path+'.ptfr-ww1-stage')
    $target=Safe $game $f.path
    Move-Item -LiteralPath $stage -Destination $target
    if((Hash $target) -cne $f.sha256){throw ('Placed file hash mismatch '+$f.path)}
    $placed+=@($target)
    $index+=1
    if($index -eq 1){FailAt 'AfterFirstMove'}
  }
  FailAt 'AfterAllMoves';FailAt 'BeforeReceipt'
  $receiptData=[ordered]@{status='INSTALLED';zip_sha256=$zipReceipt.sha256;manifest_sha256=(Hash $manifestPath);files=@($manifest.files)}
  [IO.File]::WriteAllText($receipt,($receiptData|ConvertTo-Json -Depth 10)+"`n",[Text.UTF8Encoding]::new($false))
  @{status='INSTALLED';additive_files=3;production_files_preserved=51;backup=$backup}|ConvertTo-Json
}catch{
  $failure=$_.Exception.Message
  foreach($stage in $staged){if(Test-Path -LiteralPath $stage){Remove-Item -LiteralPath $stage -Force}}
  foreach($f in $manifest.files){
    $target=Safe $game $f.path
    if($target -in $placed -and (Hash $target) -ceq $f.sha256){Remove-Item -LiteralPath $target -Force}
  }
  $failed=[ordered]@{status='FAILED_ROLLED_BACK';message=$failure;remaining=@($manifest.files|Where-Object {Test-Path -LiteralPath (Safe $game $_.path)}|ForEach-Object {$_.path})}
  [IO.File]::WriteAllText((Join-Path $backup 'failed_receipt.json'),($failed|ConvertTo-Json -Depth 10)+"`n",[Text.UTF8Encoding]::new($false))
  throw ('Probe installation failed and rollback attempted: '+$failure)
}
