param(
 [ValidateSet('Validate','Install','Verify','ValidateRollback','Rollback')][string]$Action='Validate',
 [string]$FixtureRoot='',
 [ValidateSet('','AfterBackup','AfterStage','BeforeReplace','AfterReplace','BeforeReceipt','AfterReceipt')][string]$TestFailPoint=''
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$candidate=Join-Path $PSScriptRoot 'candidate_01'
$manifest=Join-Path $candidate 'install_manifest_02.json'
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$backup=Join-Path $ws 'recovery/consolidation_repair_cr1_01'
function Safe([string]$root,[string]$relative){
 if([IO.Path]::IsPathRooted($relative) -or $relative.Contains(':') -or @($relative.Replace('\','/').Split('/')) -contains '..'){throw 'Unsafe relative path'}
 $base=[IO.Path]::GetFullPath($root).TrimEnd('\');$path=[IO.Path]::GetFullPath((Join-Path $base $relative))
 if(!$path.StartsWith($base+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Target escapes intended directory'}
 $cursor=$path
 while($cursor){if(Test-Path -LiteralPath $cursor){if((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked target path'}};$cursor=Split-Path $cursor -Parent}
 return $path
}
function Hash([string]$p){if(!(Test-Path -LiteralPath $p -PathType Leaf)){return $null};return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
$fixture=$FixtureRoot -ne ''
if($fixture){
 $FixtureRoot=[IO.Path]::GetFullPath($FixtureRoot)
 $bound=[IO.Path]::GetFullPath((Join-Path $candidate 'deploy_fixtures_02')).TrimEnd('\')+'\'
 if(!$FixtureRoot.StartsWith($bound,[StringComparison]::OrdinalIgnoreCase)){throw 'Fixture outside test directory'}
 $game=Safe $FixtureRoot 'game';$backup=Safe $FixtureRoot 'backup'
}elseif($TestFailPoint -ne ''){throw 'Failure injection is fixture-only'}
function Closed {
 if(!$fixture -and (Get-Process -Name Cyberpunk2077,REDprelauncher -ErrorAction SilentlyContinue)){throw 'Close game and launcher before deployment'}
}
Closed
$manifestHash=(Get-Content -LiteralPath ($manifest+'.sha256') -Raw).Trim()
if((Hash $manifest) -cne $manifestHash){throw 'Manifest changed'}
$m=Get-Content -LiteralPath $manifest -Raw|ConvertFrom-Json -Depth 40
if($m.status -cne 'CR1_CONSOLIDATED_SUCCESSOR_STAGED' -or $m.files.Count -lt 1 -or $m.files.Count -gt 3 -or $m.package_files.Count -ne 51){throw 'Manifest status/count mismatch'}
if(!$fixture -and ($m.game_root -cne $game -or $m.backup_root -cne $backup)){throw 'Manifest root mismatch'}
$allowed=@('archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl','r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds')
if(@($m.files.target|Select-Object -Unique).Count -ne $m.files.Count -or @($m.package_files.path|Select-Object -Unique).Count -ne 51){throw 'Duplicate manifest path'}
foreach($f in $m.files){
 if($f.target -cnotin $allowed -or !$f.before -or !$f.after -or $f.before -ceq $f.after){throw 'Unexpected replacement'}
 [void](Safe $game $f.target);[void](Safe $backup $f.target)
 $full=@($m.package_files|Where-Object {$_.path -ceq $f.target})
 if($full.Count -ne 1 -or $full[0].before -cne $f.before -or $full[0].after -cne $f.after){throw 'Replacement/full manifest disagreement'}
}
foreach($f in $m.package_files){
 if((Hash (Safe (Join-Path $candidate 'package') $f.path)) -cne $f.after){throw ('Candidate changed '+$f.path)}
 if($f.before -cne $f.after -and $f.path -cnotin @($m.files.target)){throw 'Unlisted package change'}
}
foreach($p in $m.proofs){if((Hash $p.path) -cne $p.sha256){throw ('Proof changed '+$p.path)}}
if(!$fixture){
 $tests=Join-Path $candidate 'deployment_tests_02.json'
 $testHash=(Get-Content -LiteralPath ($tests+'.sha256') -Raw).Trim()
 if((Hash $tests) -cne $testHash){throw 'Deployment fixture proof changed'}
 $tested=Get-Content -LiteralPath $tests -Raw|ConvertFrom-Json -Depth 30
 if($tested.status -cne 'PASS' -or $tested.interruption_points -ne 6 -or !$tested.partial_stage_recovered -or !$tested.path_escape_refused){throw 'Deployment fixtures did not pass'}
}
function PackageState([string]$state){
 foreach($f in $m.package_files){if((Hash (Safe $game $f.path)) -cne $f.$state){throw ('Full package mismatch '+$f.path)}}
}
function FailAt([string]$point){if($TestFailPoint -ceq $point){throw ('Injected '+$point)}}
function StagePath([string]$rel){return Safe $game ($rel+'.ptfr-cr1-stage')}
function CheckOtherFiles {
 foreach($f in $m.package_files){if($f.path -cnotin @($m.files.target) -and (Hash (Safe $game $f.path)) -cne $f.before){throw ('Unchanged installed path drift '+$f.path)}}
}
$receipt=Safe $backup 'receipt.json'
if($Action -in @('Verify','ValidateRollback','Rollback')){
 if(!(Test-Path -LiteralPath $receipt)){throw 'No deployment receipt'}
 $r=Get-Content -LiteralPath $receipt -Raw|ConvertFrom-Json -Depth 40
 if($r.manifest_sha256 -cne $manifestHash -or (Hash (Safe $backup 'install_manifest_02.json')) -cne $manifestHash){throw 'Receipt/backup manifest mismatch'}
 CheckOtherFiles
 foreach($f in $m.files){
  $actual=Hash (Safe $game $f.target)
  if($actual -cne $f.after -and $actual -cne $f.before){throw ('Later modification prevents rollback '+$f.target)}
  if((Hash (Safe $backup $f.target)) -cne $f.before){throw ('Backup changed '+$f.target)}
  $stage=StagePath $f.target
  if((Test-Path -LiteralPath $stage) -and !(Test-Path -LiteralPath $stage -PathType Leaf)){throw ('Staging target is not a file '+$stage)}
 }
 if($Action -eq 'Verify'){
  PackageState 'after'
  foreach($f in $m.files){if(Test-Path -LiteralPath (StagePath $f.target)){throw 'Staging residue after install'}}
  @{status='VERIFIED';package_files=51;replaced_files=$m.files.Count}|ConvertTo-Json;exit
 }
 if($Action -eq 'ValidateRollback'){@{status='ROLLBACK_READY';files=$m.files.Count;save_undo=$false}|ConvertTo-Json;exit}
 foreach($f in $m.files){
  Closed
  $target=Safe $game $f.target;$stage=StagePath $f.target
  # Preserve even a partial interrupted copy; never infer that it is installable.
  if(Test-Path -LiteralPath $stage){
   $stageHash=Hash $stage
   $held=Safe $backup ('interrupted_stage/'+$f.target+'.'+$stageHash)
   New-Item -ItemType Directory -Path (Split-Path $held -Parent) -Force|Out-Null
   if(Test-Path -LiteralPath $held){
    if((Hash $held) -cne $stageHash){throw 'Held stage hash disagreement'}
    Remove-Item -LiteralPath $stage
   }else{Move-Item -LiteralPath $stage -Destination $held}
  }
  if((Hash $target) -ceq $f.before){continue}
  Copy-Item -LiteralPath (Safe $backup $f.target) -Destination $stage
  if((Hash $stage) -cne $f.before){throw 'Rollback stage mismatch'}
  Closed
  [IO.File]::Replace($stage,$target,[NullString]::Value)
  if((Hash $target) -cne $f.before){throw 'Rollback replacement mismatch'}
 }
 PackageState 'before'
 $r.status='ROLLED_BACK';$r|ConvertTo-Json -Depth 40|Set-Content -LiteralPath $receipt -Encoding utf8NoBOM
 @{status='ROLLED_BACK';files=$m.files.Count;save_undo=$false}|ConvertTo-Json;exit
}
if(Test-Path -LiteralPath $backup){throw 'Recovery directory exists; inspect receipt rather than reinstalling'}
PackageState 'before'
foreach($f in $m.files){if(Test-Path -LiteralPath (StagePath $f.target)){throw 'Staging target already exists'}}
if($Action -eq 'Validate'){@{status='READY';replacements=$m.files.Count;added_install_paths=0;full_package_files=51}|ConvertTo-Json;exit}
New-Item -ItemType Directory -Path $backup|Out-Null
Copy-Item -LiteralPath $manifest -Destination (Safe $backup 'install_manifest_02.json')
foreach($f in $m.files){
 $dest=Safe $backup $f.target;New-Item -ItemType Directory -Path (Split-Path $dest -Parent) -Force|Out-Null
 Copy-Item -LiteralPath (Safe $game $f.target) -Destination $dest
 if((Hash $dest) -cne $f.before){throw 'Backup verification failed'}
}
$r=[ordered]@{status='BACKED_UP';created_utc=[DateTime]::UtcNow.ToString('o');manifest_sha256=$manifestHash;files=$m.files;game_launched=$false;save_edits=0;live_result='pending'}
function Receipt {$r|ConvertTo-Json -Depth 40|Set-Content -LiteralPath $receipt -Encoding utf8NoBOM}
Receipt
try{
 FailAt 'AfterBackup'
 foreach($f in $m.files){
  $target=Safe $game $f.target;$stage=StagePath $f.target
  if((Hash $target) -cne $f.before){throw ('Target drift before staging '+$f.target)}
  Copy-Item -LiteralPath (Safe (Join-Path $candidate 'package') $f.target) -Destination $stage
  if((Hash $stage) -cne $f.after){throw 'Stage verification failed'}
  FailAt 'AfterStage'
  Closed
  if((Hash $target) -cne $f.before){throw 'Target changed before atomic replacement'}
  FailAt 'BeforeReplace'
  [IO.File]::Replace($stage,$target,[NullString]::Value)
  FailAt 'AfterReplace'
  if((Hash $target) -cne $f.after){throw 'Installed replacement mismatch'}
 }
 PackageState 'after'
 FailAt 'BeforeReceipt'
 $r.status='CR1_CONSOLIDATED_INSTALLED_LIVE_PENDING';Receipt
 FailAt 'AfterReceipt'
}catch{$r.status='INTERRUPTED_REVIEW_REQUIRED';$r.error=$_.Exception.Message;Receipt;throw}
@{status=$r.status;files=$m.files.Count;full_package_files=51;backup=$backup}|ConvertTo-Json
