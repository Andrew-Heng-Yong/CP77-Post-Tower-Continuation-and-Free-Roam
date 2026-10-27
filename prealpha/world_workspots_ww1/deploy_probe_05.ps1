param(
  [ValidateSet('Validate','Install','Verify','ValidateRollback','Rollback')][string]$Action='Validate',
  [string]$FixtureRoot='',
  [ValidateSet('','AfterBackup','AfterStage','AfterReplace','BeforeReceipt')][string]$TestFailPoint=''
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$old=Join-Path $PSScriptRoot 'probe_04'
$candidate=Join-Path $PSScriptRoot 'probe_05'
$manifestPath=Join-Path $candidate 'manifest_01.json'
$m=Get-Content -LiteralPath $manifestPath -Raw|ConvertFrom-Json -Depth 15
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$backup=Join-Path $ws 'recovery/world_workspots_ww1_probe_05_01'
$fixture=$FixtureRoot -ne ''
if($fixture){
  $FixtureRoot=[IO.Path]::GetFullPath($FixtureRoot)
  $bound=[IO.Path]::GetFullPath((Join-Path $candidate 'deploy_fixtures_01')).TrimEnd('\')+'\'
  if(!$FixtureRoot.StartsWith($bound,[StringComparison]::OrdinalIgnoreCase)){throw 'Fixture outside probe05 test directory'}
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
function Hash([string]$path){if(!(Test-Path -LiteralPath $path -PathType Leaf)){return $null};return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash}
function FailAt([string]$point){if($TestFailPoint -ceq $point){throw ('Injected '+$point)}}
if(!$fixture -and @(Get-Process -Name Cyberpunk2077,REDprelauncher -ErrorAction SilentlyContinue).Count){throw 'Close Cyberpunk and launcher before updating probe'}
$expected=@('archive/pc/mod/zzzz_PTFR_WW1_Prototype.archive','archive/pc/mod/zzzz_PTFR_WW1_Prototype.archive.xl','r6/scripts/PTFR_WW1_Prototype/WW1Probe.reds')
if($m.status -cne 'WW1_PROBE05_ONE_SCRIPT_SUCCESSOR_STAGED_NOT_INSTALLED' -or $m.files.Count -ne 3 -or $m.changed_paths -ne 1){throw 'Probe05 manifest mismatch'}
if(@(Compare-Object ($expected|Sort-Object) @($m.files.path|Sort-Object)).Count){throw 'Unexpected probe05 paths'}
$manifestHash=(Get-Content -LiteralPath ($manifestPath+'.sha256') -Raw).Trim()
if((Hash $manifestPath) -cne $manifestHash){throw 'Manifest hash changed'}
$zip=Join-Path $candidate 'Post-Tower-Continuation-and-Free-Roam-WW1-Scav-probe05-unreleased.zip'
if((Hash $zip) -cne $m.zip_sha256){throw 'ZIP hash changed'}
$compiled=Get-Content -LiteralPath (Join-Path $candidate 'compile_02/result.json') -Raw|ConvertFrom-Json
if($compiled.status -cne 'PASS' -or $compiled.source_count -ne 65 -or $compiled.compiled_sha256 -cne $m.compiled_sha256){throw 'Compilation proof changed'}
$scriptRow=@($m.files|Where-Object {$_.path -ceq 'r6/scripts/PTFR_WW1_Prototype/WW1Probe.reds'})
if($scriptRow.Count -ne 1){throw 'Script row not unique'}
$row=$scriptRow[0]
$target=Safe $game $row.path
$source=Safe (Join-Path $candidate 'package') $row.path
if((Hash $source) -cne $row.after){throw 'Candidate script drift'}
foreach($f in $m.files){
  if((Hash (Safe (Join-Path $candidate 'package') $f.path)) -cne $f.after){throw ('Candidate file drift '+$f.path)}
  if($f.path -cne $row.path -and $f.before -cne $f.after){throw 'Only script may change'}
}
if(!$fixture){
  $prior=Get-Content -LiteralPath (Join-Path $ws 'recovery/world_workspots_ww1_probe_04_01/receipt.json') -Raw|ConvertFrom-Json
  if($prior.status -cne 'INSTALLED'){throw 'Probe04 install receipt missing'}
  $jc1=Get-Content -LiteralPath (Join-Path $ws 'prealpha/coaster_jean_jc1/candidate_01/manifest.json') -Raw|ConvertFrom-Json -Depth 30
  if($jc1.files.Count -ne 51){throw 'JC1 manifest changed'}
  foreach($f in $jc1.files){if((Hash (Safe $game $f.path)) -cne $f.sha256){throw ('JC1 file drift '+$f.path)}}
}
foreach($f in $m.files){
  $expectedHash=if($Action -in @('Verify','ValidateRollback','Rollback')){$f.after}else{$f.before}
  if((Hash (Safe $game $f.path)) -cne $expectedHash){throw ('Installed probe state differs '+$f.path)}
}
if($Action -eq 'Validate'){
  if(Test-Path -LiteralPath $backup){throw 'Probe05 recovery directory exists'}
  @{status='READY';replace_file=$row.path;existing_production_files=51}|ConvertTo-Json;exit 0
}
$oldScript=Safe $backup $row.path
$receipt=Safe $backup 'receipt.json'
if($Action -in @('Verify','ValidateRollback','Rollback')){
  if(!(Test-Path -LiteralPath $receipt)){throw 'No successful probe05 receipt'}
  $r=Get-Content -LiteralPath $receipt -Raw|ConvertFrom-Json
  if($r.status -cne 'INSTALLED' -or $r.manifest_sha256 -cne $manifestHash -or (Hash $oldScript) -cne $row.before){throw 'Probe05 recovery data changed'}
  if($Action -eq 'Verify'){@{status='VERIFIED';changed_file=1;production_files_preserved=51}|ConvertTo-Json;exit 0}
  if($Action -eq 'ValidateRollback'){@{status='ROLLBACK_READY';restore_script=$row.path}|ConvertTo-Json;exit 0}
  Copy-Item -LiteralPath $oldScript -Destination $target -Force
  if((Hash $target) -cne $row.before){throw 'Rollback restore failed'}
  $done=[ordered]@{status='ROLLED_BACK';restored=$row.path;hash=$row.before}
  [IO.File]::WriteAllText((Join-Path $backup 'rollback_receipt.json'),($done|ConvertTo-Json)+"`n",[Text.UTF8Encoding]::new($false))
  $done|ConvertTo-Json;exit 0
}
if($Action -ne 'Install'){throw 'Unsupported action'}
if(Test-Path -LiteralPath $backup){throw 'Probe05 recovery directory exists'}
New-Item -ItemType Directory -Path (Split-Path $oldScript -Parent) -Force|Out-Null
$stage=Safe $game ($row.path+'.ptfr-ww1-stage')
if(Test-Path -LiteralPath $stage){throw 'Unexpected stage file'}
try{
  Copy-Item -LiteralPath $target -Destination $oldScript
  if((Hash $oldScript) -cne $row.before){throw 'Old script backup mismatch'}
  Copy-Item -LiteralPath $manifestPath -Destination (Safe $backup 'install_manifest.json')
  FailAt 'AfterBackup'
  Copy-Item -LiteralPath $source -Destination $stage
  if((Hash $stage) -cne $row.after){throw 'Stage file hash mismatch'}
  FailAt 'AfterStage'
  Copy-Item -LiteralPath $stage -Destination $target -Force
  if((Hash $target) -cne $row.after){throw 'Installed script hash mismatch'}
  FailAt 'AfterReplace';FailAt 'BeforeReceipt'
  Remove-Item -LiteralPath $stage -Force
  $r=[ordered]@{status='INSTALLED';manifest_sha256=$manifestHash;before=$row.before;after=$row.after;script=$row.path}
  [IO.File]::WriteAllText($receipt,($r|ConvertTo-Json)+"`n",[Text.UTF8Encoding]::new($false))
  @{status='INSTALLED';changed_file=1;production_files_preserved=51;backup=$backup}|ConvertTo-Json
}catch{
  $failure=$_.Exception.Message
  if(Test-Path -LiteralPath $stage){Remove-Item -LiteralPath $stage -Force}
  if((Hash $oldScript) -ceq $row.before -and (Hash $target) -cne $row.before){Copy-Item -LiteralPath $oldScript -Destination $target -Force}
  $rolled=(Hash $target) -ceq $row.before
  $failed=[ordered]@{status=if($rolled){'FAILED_ROLLED_BACK'}else{'FAILED_REQUIRES_MANUAL_RECOVERY'};message=$failure;old_script_restored=$rolled}
  [IO.File]::WriteAllText((Join-Path $backup 'failed_receipt.json'),($failed|ConvertTo-Json)+"`n",[Text.UTF8Encoding]::new($false))
  throw ('Probe05 installation failed; script restored='+$rolled+'; '+$failure)
}
