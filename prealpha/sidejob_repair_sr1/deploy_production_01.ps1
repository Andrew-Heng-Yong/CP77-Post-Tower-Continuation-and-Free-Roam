param(
 [ValidateSet('Validate','Install','Verify','ValidateRollback','Rollback')][string]$Action='Validate',
 [string]$FixtureRoot='',
 [int]$TestFailAfter=0
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$candidate=Join-Path $PSScriptRoot 'production_01'
$manifest=Join-Path $candidate 'install_manifest_01.json'
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$backup=Join-Path $ws 'recovery/sidejob_repair_sr1_production_01'
function Safe([string]$root,[string]$relative){
 if([IO.Path]::IsPathRooted($relative) -or $relative.Contains(':') -or @($relative.Replace('\','/').Split('/')) -contains '..'){throw 'Unsafe relative path'}
 $base=[IO.Path]::GetFullPath($root).TrimEnd('\');$path=[IO.Path]::GetFullPath((Join-Path $base $relative))
 if(!$path.StartsWith($base+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Target escapes intended directory'}
 $cursor=$path
 while($cursor){if(Test-Path -LiteralPath $cursor){if((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked target path'}};$cursor=Split-Path $cursor -Parent}
 return $path
}
function Hash([string]$path){if(!(Test-Path -LiteralPath $path -PathType Leaf)){return $null};return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash}
$fixture=$FixtureRoot -ne ''
if($fixture){
 $FixtureRoot=[IO.Path]::GetFullPath($FixtureRoot)
 $bound=[IO.Path]::GetFullPath((Join-Path $candidate 'deploy_fixtures')).TrimEnd('\')+'\'
 if(!$FixtureRoot.StartsWith($bound,[StringComparison]::OrdinalIgnoreCase)){throw 'Fixture outside workspace test directory'}
 $game=Safe $FixtureRoot 'game';$backup=Safe $FixtureRoot 'backup'
}elseif($TestFailAfter -ne 0){throw 'Failure injection is fixture-only'}
$expected=(Get-Content -LiteralPath ($manifest+'.sha256') -Raw).Trim()
if((Hash $manifest) -cne $expected){throw 'Manifest changed'}
$m=Get-Content -LiteralPath $manifest -Raw|ConvertFrom-Json
if($m.status -cne 'THREE_FILE_PRODUCTION_STAGED_NOT_INSTALLED' -or $m.files.Count -ne 3 -or (!$fixture -and ($m.game_root -cne $game -or $m.backup_root -cne $backup))){throw 'Manifest root/count mismatch'}
$allowed=@('archive/pc/mod/00000000_TowerContinued_SideJobs_S29.archive','archive/pc/mod/00000000_TowerContinued_SideJobs_S29.archive.xl','r6/scripts/TowerContinued_SideJobs_S29/SideJobsS29.reds')
if(@($m.files.target|Select-Object -Unique).Count -ne 3){throw 'Duplicate deployment target'}
foreach($f in $m.files){
 if($f.target -cnotin $allowed){throw 'Unexpected target scope'}
 [void](Safe $game $f.target);[void](Safe $backup $f.target)
 if((Hash (Safe (Join-Path $candidate 'package') $f.target)) -cne $f.after){throw ('Candidate changed '+$f.target)}
}
foreach($p in $m.proofs){if((Hash $p.path) -cne $p.sha256){throw ('Proof changed '+$p.path)}}
if(!$fixture -and (Get-Process -Name Cyberpunk2077,REDprelauncher -ErrorAction SilentlyContinue)){throw 'Close the game and launcher before deployment'}
$receipt=Safe $backup 'receipt.json'
if($Action -in @('Verify','ValidateRollback','Rollback')){
 if(!(Test-Path -LiteralPath $receipt)){throw 'No deployment receipt'}
 foreach($f in $m.files){
  $actual=Hash (Safe $game $f.target)
  if($Action -eq 'Verify' -and $actual -cne $f.after){throw ('Installed hash mismatch '+$f.target)}
  if($actual -cne $f.after -and $actual -cne $f.before){throw ('Later modification prevents rollback '+$f.target)}
  if($null -ne $f.before -and (Hash (Safe $backup $f.target)) -cne $f.before){throw ('Backup hash mismatch '+$f.target)}
 }
 if($Action -eq 'Verify'){@{status='VERIFIED';files=3}|ConvertTo-Json;exit}
 if($Action -eq 'ValidateRollback'){@{status='ROLLBACK_READY';files=3}|ConvertTo-Json;exit}
 foreach($f in $m.files){
  $dest=Safe $game $f.target
  if((Hash $dest) -ceq $f.before){continue}
  if($null -eq $f.before){
   $held=Safe $backup ('removed/'+$f.target)
   if(Test-Path -LiteralPath $held){throw 'Rollback holding target already exists'}
   New-Item -ItemType Directory -Path (Split-Path $held -Parent) -Force|Out-Null
   Move-Item -LiteralPath $dest -Destination $held
  }else{Copy-Item -LiteralPath (Safe $backup $f.target) -Destination $dest}
  if((Hash $dest) -cne $f.before){throw ('Rollback verification failed '+$f.target)}
 }
 $r=Get-Content -LiteralPath $receipt -Raw|ConvertFrom-Json;$r.status='ROLLED_BACK';$r|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $receipt -Encoding utf8
 @{status='ROLLED_BACK';files=3;save_undo=$false}|ConvertTo-Json;exit
}
if(Test-Path -LiteralPath $backup){throw 'Backup directory already exists'}
foreach($f in $m.files){if((Hash (Safe $game $f.target)) -cne $f.before){throw ('Unexpected installed baseline '+$f.target)}}
if($Action -eq 'Validate'){@{status='READY';replacements=3;additions=0}|ConvertTo-Json;exit}
New-Item -ItemType Directory -Path $backup|Out-Null
Copy-Item -LiteralPath $manifest -Destination (Safe $backup 'install_manifest_01.json')
foreach($f in $m.files){if($null -ne $f.before){$dest=Safe $backup $f.target;New-Item -ItemType Directory -Path (Split-Path $dest -Parent) -Force|Out-Null;Copy-Item -LiteralPath (Safe $game $f.target) -Destination $dest;if((Hash $dest) -cne $f.before){throw 'Backup verification failed'}}}
$r=[ordered]@{status='BACKED_UP';created_utc=[DateTime]::UtcNow.ToString('o');manifest_sha256=$expected;files=$m.files;game_launched=$false;save_edits=0;live_result='pending'}
function Receipt {$r|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $receipt -Encoding utf8}
Receipt
try{
 $copied=0
 foreach($f in $m.files){
  $dest=Safe $game $f.target
  if((Hash $dest) -cne $f.before){throw ('Target changed immediately before write '+$f.target)}
  New-Item -ItemType Directory -Path (Split-Path $dest -Parent) -Force|Out-Null
  Copy-Item -LiteralPath (Safe (Join-Path $candidate 'package') $f.target) -Destination $dest
  if((Hash $dest) -cne $f.after){throw ('Installed verification failed '+$f.target)}
  $copied++;if($TestFailAfter -gt 0 -and $copied -eq $TestFailAfter){throw 'Injected interrupted deployment'}
 }
 $r.status='SR1_PRODUCTION_INSTALLED_LIVE_PENDING';Receipt
}catch{$r.status='INTERRUPTED_REVIEW_REQUIRED';$r.error=$_.Exception.Message;Receipt;throw}
@{status=$r.status;files=3;backup=$backup}|ConvertTo-Json
