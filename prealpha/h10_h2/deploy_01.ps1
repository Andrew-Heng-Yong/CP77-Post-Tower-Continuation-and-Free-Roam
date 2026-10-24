param(
 [ValidateSet('Validate','Install','Verify','ValidateRollback','Rollback')][string]$Action='Validate',
 [string]$FixtureRoot='',
 [int]$TestFailAfter=0
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$candidate=Join-Path $PSScriptRoot 'candidate_01'
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$backup=Join-Path $ws 'recovery/h10_h2_01'
$manifest=Join-Path $candidate 'install_manifest_01.json'
function Safe([string]$root,[string]$relative){
 if([IO.Path]::IsPathRooted($relative) -or $relative.Contains(':') -or $relative -match '(^|[/\\])\.\.([/\\]|$)'){throw 'Unsafe relative path'}
 $base=[IO.Path]::GetFullPath($root).TrimEnd('\');$path=[IO.Path]::GetFullPath((Join-Path $base $relative))
 if(!$path.StartsWith($base+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Target escapes intended directory'}
 $cursor=$path
 while($cursor){if(Test-Path -LiteralPath $cursor){if((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked target path'}};$cursor=Split-Path $cursor -Parent}
 return $path
}
function Hash($p){if(!(Test-Path -LiteralPath $p -PathType Leaf)){return $null};(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
if($FixtureRoot){
 $FixtureRoot=[IO.Path]::GetFullPath($FixtureRoot)
 $bound=[IO.Path]::GetFullPath((Join-Path $candidate 'deploy_fixtures')).TrimEnd('\')+'\'
 if(!$FixtureRoot.StartsWith($bound,[StringComparison]::OrdinalIgnoreCase)){throw 'Fixture outside workspace test directory'}
 $game=Safe $FixtureRoot 'game';$backup=Safe $FixtureRoot 'backup';$manifest=Safe $FixtureRoot 'install_manifest_01.json'
}elseif($TestFailAfter -ne 0){throw 'Failure injection is fixture-only'}
$expected=(Get-Content -LiteralPath ($manifest+'.sha256') -Raw).Trim()
if((Hash $manifest) -cne $expected){throw 'Manifest changed'}
$m=Get-Content -LiteralPath $manifest -Raw|ConvertFrom-Json
if($m.game_root -cne $game -or $m.backup_root -cne $backup -or $m.files.Count -ne 6){throw 'Unexpected deployment roots/count'}
$targets=@($m.files.target|Select-Object -Unique)
if($targets.Count -ne 6){throw 'Duplicate target'}
foreach($f in $m.files){
 if($f.target -cnotin @('r6/scripts/TowerContinued_Housing_H1/HousingDevices.reds','r6/scripts/TowerContinued_Housing_H1/HousingPurchase.reds','r6/scripts/TowerContinued_Housing_H1/HousingDoorH2.reds','r6/scripts/PTFR_PreAlpha/PTFR_RestorationBaseline/RestorationBaseline.reds','r6/scripts/TowerContinued_Housing_H1/WilsonLeaseH2.reds','archive/pc/mod/0000_TowerContinued_SideJobs_S23.archive')){throw 'Unexpected target scope'}
 [void](Safe $game $f.target);[void](Safe $backup $f.target)
 if((Hash (Safe (Join-Path $candidate 'package') $f.target)) -cne $f.after){throw 'Candidate changed'}
}
function Closed {if(Get-Process -Name Cyberpunk2077,REDprelauncher -ErrorAction SilentlyContinue){throw 'Close the game and launcher before deployment.'}}
function Protected {foreach($p in $m.protected){if((Hash $p.path) -cne $p.sha256){throw "Protected file changed: $($p.path)"}}}
Closed
foreach($p in $m.proofs){if((Hash $p.path) -cne $p.sha256){throw "Proof changed: $($p.path)"}}
$receipt=Safe $backup 'receipt.json'
if($Action -in @('Verify','ValidateRollback','Rollback')){
 if(!(Test-Path -LiteralPath $receipt)){throw 'No deployment receipt'}
 foreach($f in $m.files){
  $actual=Hash (Safe $game $f.target)
  if($Action -eq 'Verify' -and $actual -cne $f.after){throw 'Installed hash mismatch'}
  if($actual -cne $f.after -and $actual -cne $f.before){throw "Later modification prevents rollback: $($f.target)"}
  if($null -ne $f.before -and (Hash (Safe $backup $f.target)) -cne $f.before){throw 'Backup hash mismatch'}
 }
 if($Action -eq 'Verify'){Protected;@{status='VERIFIED';files=6;protected=$m.protected.Count}|ConvertTo-Json;exit}
 if($Action -eq 'ValidateRollback'){@{status='ROLLBACK_READY';files=6}|ConvertTo-Json;exit}
 # All targets and resolved paths were validated before any move or replacement.
 foreach($f in $m.files){
  $dest=Safe $game $f.target
  if((Hash $dest) -ceq $f.before){continue}
  if($null -eq $f.before){
   $held=Safe $backup ('removed/'+$f.target)
   if(Test-Path -LiteralPath $held){throw 'Rollback holding target already exists'}
   New-Item -ItemType Directory -Path (Split-Path $held -Parent) -Force|Out-Null
   Move-Item -LiteralPath $dest -Destination $held
  }else{Copy-Item -LiteralPath (Safe $backup $f.target) -Destination $dest}
  if((Hash $dest) -cne $f.before){throw 'Rollback verification failed'}
 }
 $r=Get-Content -LiteralPath $receipt -Raw|ConvertFrom-Json;$r.status='ROLLED_BACK';$r|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $receipt -Encoding utf8
 @{status='ROLLED_BACK';files=6;save_undo=$false}|ConvertTo-Json;exit
}
if(Test-Path -LiteralPath $backup){throw 'Backup directory already exists'}
foreach($f in $m.files){if((Hash (Safe $game $f.target)) -cne $f.before){throw "Unexpected installed baseline: $($f.target)"}}
Protected
if($Action -eq 'Validate'){@{status='READY';replacements=4;additions=2;protected=$m.protected.Count}|ConvertTo-Json;exit}
New-Item -ItemType Directory -Path $backup|Out-Null
Copy-Item -LiteralPath $manifest -Destination (Safe $backup 'install_manifest_01.json')
foreach($f in $m.files){if($null -ne $f.before){$dest=Safe $backup $f.target;New-Item -ItemType Directory -Path (Split-Path $dest -Parent) -Force|Out-Null;Copy-Item -LiteralPath (Safe $game $f.target) -Destination $dest;if((Hash $dest) -cne $f.before){throw 'Backup verification failed'}}}
$r=[ordered]@{status='BACKED_UP';created_utc=[DateTime]::UtcNow.ToString('o');manifest_sha256=$expected;files=$m.files;game_launched=$false;save_edits=0;native_story_fact_writes=0;live_result='pending'}
function Receipt {$r|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $receipt -Encoding utf8}
Receipt
try{
 Closed;$copied=0
 foreach($f in $m.files){
  $dest=Safe $game $f.target
  if((Hash $dest) -cne $f.before){throw 'Target changed immediately before write'}
  New-Item -ItemType Directory -Path (Split-Path $dest -Parent) -Force|Out-Null
  Copy-Item -LiteralPath (Safe (Join-Path $candidate 'package') $f.target) -Destination $dest
  if((Hash $dest) -cne $f.after){throw 'Installed verification failed'}
  $copied+=1;if($TestFailAfter -gt 0 -and $copied -eq $TestFailAfter){throw 'Injected interrupted deployment'}
 }
 Protected;$r.status='H2_INSTALLED_LIVE_PENDING';Receipt
}catch{$r.status='INTERRUPTED_REVIEW_REQUIRED';$r.error=$_.Exception.Message;Receipt;throw}
@{status=$r.status;files=6;protected=$m.protected.Count;backup=$backup}|ConvertTo-Json
