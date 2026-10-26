param(
 [ValidateSet('Validate','Install','Verify','ValidateRollback','Rollback')][string]$Action='Validate',
 [string]$FixtureRoot='',
 [int]$TestFailAfter=0
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$candidate=Join-Path $PSScriptRoot 'candidate_01'
$manifest=Join-Path $candidate 'install_manifest_01.json'
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$backup=Join-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) 'recovery/full_consolidation_v1_01'
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
 $bound=[IO.Path]::GetFullPath((Join-Path $candidate 'deploy_fixtures_02')).TrimEnd('\')+'\'
 if(!$FixtureRoot.StartsWith($bound,[StringComparison]::OrdinalIgnoreCase)){throw 'Fixture outside workspace test directory'}
 $game=Safe $FixtureRoot 'game';$backup=Safe $FixtureRoot 'backup'
}elseif($TestFailAfter -ne 0){throw 'Failure injection is fixture-only'}
$expected=(Get-Content -LiteralPath ($manifest+'.sha256') -Raw).Trim()
if((Hash $manifest) -cne $expected){throw 'Manifest changed'}
$m=Get-Content -LiteralPath $manifest -Raw|ConvertFrom-Json
if($m.status -cne 'FULL_PTFR_127_TO_51_LOCAL_DEPLOYMENT_STAGED' -or $m.old_files.Count -ne 127 -or $m.new_files.Count -ne 51 -or (!$fixture -and ($m.game_root -cne $game -or $m.backup_root -cne $backup))){throw 'Manifest root/count mismatch'}
$old=@{};$new=@{}
foreach($f in $m.old_files){
 if($old.ContainsKey($f.path)){throw 'Duplicate old target'}
 $old[$f.path]=$f
 [void](Safe $game $f.path);[void](Safe (Join-Path $backup 'old') $f.path)
}
foreach($f in $m.new_files){
 if($new.ContainsKey($f.path)){throw 'Duplicate new target'}
 $new[$f.path]=$f
 [void](Safe $game $f.path);[void](Safe (Join-Path $candidate 'package') $f.path)
 if((Hash (Safe (Join-Path $candidate 'package') $f.path)) -cne $f.sha256){throw ('Package changed '+$f.path)}
}
if(@($new.Keys|Where-Object {$old.ContainsKey($_)}).Count -ne 3){throw 'Expected three retained paths'}
foreach($p in $m.proofs){if((Hash $p.path) -cne $p.sha256){throw ('Proof changed '+$p.path)}}
if(!$fixture -and (Get-Process -Name Cyberpunk2077,REDprelauncher -ErrorAction SilentlyContinue)){throw 'Close the game and launcher before deployment'}
$receipt=Safe $backup 'receipt.json'
function Receipt {$r|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $receipt -Encoding utf8}
function ValidateCurrent {
 foreach($f in $m.old_files){if((Hash (Safe $game $f.path)) -cne $f.sha256){throw ('Old baseline changed '+$f.path)}}
 foreach($f in $m.new_files){if(!$old.ContainsKey($f.path) -and (Test-Path -LiteralPath (Safe $game $f.path))){throw ('New destination occupied '+$f.path)}}
}
if($Action -in @('Verify','ValidateRollback','Rollback')){
 if(!(Test-Path -LiteralPath $receipt)){throw 'No deployment receipt'}
 foreach($f in $m.old_files){
  $actual=Hash (Safe $game $f.path);$held=Hash (Safe (Join-Path $backup 'old') $f.path)
  if($actual -cne $f.sha256 -and $held -cne $f.sha256){throw ('Prior file not recoverable '+$f.path)}
  if($held -ne $null -and $held -cne $f.sha256){throw ('Backup hash mismatch '+$f.path)}
  if($actual -ne $null -and $actual -cne $f.sha256 -and (!$new.ContainsKey($f.path) -or $actual -cne $new[$f.path].sha256)){throw ('Unexpected old target state '+$f.path)}
 }
 foreach($f in $m.new_files){
  $actual=Hash (Safe $game $f.path)
  if($Action -eq 'Verify' -and $actual -cne $f.sha256){throw ('Installed hash mismatch '+$f.path)}
  if($Action -ne 'Verify' -and $actual -ne $null -and $actual -cne $f.sha256 -and (!$old.ContainsKey($f.path) -or $actual -cne $old[$f.path].sha256)){throw ('Unexpected new target state '+$f.path)}
 }
 if($Action -eq 'Verify'){
  foreach($f in $m.old_files){if(!$new.ContainsKey($f.path) -and (Test-Path -LiteralPath (Safe $game $f.path))){throw ('Retired file remains '+$f.path)}}
  @{status='VERIFIED';old=127;new=51}|ConvertTo-Json;exit
 }
 if($Action -eq 'ValidateRollback'){@{status='ROLLBACK_READY';old=127;new=51}|ConvertTo-Json;exit}
 foreach($f in $m.new_files){
  $dest=Safe $game $f.path
  if((Hash $dest) -cne $f.sha256){continue}
  if($old.ContainsKey($f.path) -and $old[$f.path].sha256 -ceq $f.sha256 -and !(Test-Path -LiteralPath (Safe (Join-Path $backup 'old') $f.path))){continue}
  $held=Safe (Join-Path $backup 'new_removed') $f.path
  if(Test-Path -LiteralPath $held){throw ('Rollback holding target already exists '+$f.path)}
  New-Item -ItemType Directory -Path (Split-Path $held -Parent) -Force|Out-Null
  Move-Item -LiteralPath $dest -Destination $held
  if((Hash $held) -cne $f.sha256){throw ('Rollback new-file hold failed '+$f.path)}
 }
 foreach($f in $m.old_files){
  $dest=Safe $game $f.path
  if((Hash $dest) -ceq $f.sha256){continue}
  if(Test-Path -LiteralPath $dest){throw ('Rollback destination occupied '+$f.path)}
  $held=Safe (Join-Path $backup 'old') $f.path
  if((Hash $held) -cne $f.sha256){throw ('Rollback source unavailable '+$f.path)}
  New-Item -ItemType Directory -Path (Split-Path $dest -Parent) -Force|Out-Null
  Move-Item -LiteralPath $held -Destination $dest
  if((Hash $dest) -cne $f.sha256){throw ('Rollback restoration failed '+$f.path)}
 }
 $r=Get-Content -LiteralPath $receipt -Raw|ConvertFrom-Json;$r.status='ROLLED_BACK';$r|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $receipt -Encoding utf8
 @{status='ROLLED_BACK';old=127;new=51;save_undo=$false}|ConvertTo-Json;exit
}
if(Test-Path -LiteralPath $backup){throw 'Backup directory already exists'}
ValidateCurrent
if($Action -eq 'Validate'){@{status='READY';old=127;new=51;retired=124;retained_paths=3}|ConvertTo-Json;exit}
New-Item -ItemType Directory -Path $backup|Out-Null
Copy-Item -LiteralPath $manifest -Destination (Safe $backup 'install_manifest_01.json')
$r=[ordered]@{status='MOVING_OLD_FILES';created_utc=[DateTime]::UtcNow.ToString('o');manifest_sha256=$expected;old=127;new=51;game_launched=$false;save_edits=0;live_result='pending'}
Receipt
try{
 $step=0
 foreach($f in $m.old_files){
  $src=Safe $game $f.path;$held=Safe (Join-Path $backup 'old') $f.path
  if((Hash $src) -cne $f.sha256){throw ('Old file changed before move '+$f.path)}
  New-Item -ItemType Directory -Path (Split-Path $held -Parent) -Force|Out-Null
  Move-Item -LiteralPath $src -Destination $held
  if((Hash $held) -cne $f.sha256 -or (Test-Path -LiteralPath $src)){throw ('Old-file move failed '+$f.path)}
  $step++;if($TestFailAfter -eq $step){throw 'Injected interrupted deployment'}
 }
 $r.status='COPYING_NEW_FILES';Receipt
 foreach($f in $m.new_files){
  $dest=Safe $game $f.path
  if(Test-Path -LiteralPath $dest){throw ('New destination occupied during copy '+$f.path)}
  New-Item -ItemType Directory -Path (Split-Path $dest -Parent) -Force|Out-Null
  Copy-Item -LiteralPath (Safe (Join-Path $candidate 'package') $f.path) -Destination $dest
  if((Hash $dest) -cne $f.sha256){throw ('Installed hash mismatch '+$f.path)}
  $step++;if($TestFailAfter -eq $step){throw 'Injected interrupted deployment'}
 }
 $r.status='FULL_PTFR_CONSOLIDATED_INSTALLED_LIVE_PENDING';Receipt
}catch{$r.status='INTERRUPTED_REVIEW_REQUIRED';$r.error=$_.Exception.Message;Receipt;throw}
@{status=$r.status;old=127;new=51;backup=$backup}|ConvertTo-Json
