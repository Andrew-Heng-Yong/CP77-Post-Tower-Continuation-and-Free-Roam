param(
 [ValidateSet('Validate','Install','Verify','ValidateRollback','Rollback')][string]$Action='Validate',
 [string]$FixtureRoot='',
 [ValidateSet('','AfterBackup','AfterStage','AfterFirstReplace','AfterSecondReplace','AfterThirdReplace','BeforeReceipt')][string]$TestFailPoint=''
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$candidate=Join-Path $PSScriptRoot 'candidate_01'
$manifest=Join-Path $candidate 'install_manifest_01.json'
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$backup=Join-Path $ws 'recovery/world_actions_wa2_01'
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
 $bound=[IO.Path]::GetFullPath((Join-Path $candidate 'deploy_fixtures_01')).TrimEnd('\')+'\'
 if(!$FixtureRoot.StartsWith($bound,[StringComparison]::OrdinalIgnoreCase)){throw 'Fixture outside controlled directory'}
 $game=Safe $FixtureRoot 'game';$backup=Safe $FixtureRoot 'backup'
}elseif($TestFailPoint -ne ''){throw 'Interruption injection is fixture-only'}
function Closed {if(!$fixture -and (Get-Process -Name Cyberpunk2077,REDprelauncher -ErrorAction SilentlyContinue)){throw 'Close game and launcher before deployment'}}
function FailAt([string]$step){if($fixture -and $TestFailPoint -ceq $step){throw "Injected interruption $step"}}
Closed
$manifestHash=(Get-Content -LiteralPath ($manifest+'.sha256') -Raw).Trim()
if((Hash $manifest) -cne $manifestHash){throw 'Manifest changed'}
$m=Get-Content -LiteralPath $manifest -Raw|ConvertFrom-Json -Depth 80
if($m.status -cne 'WA2_51_PATH_SUCCESSOR_STAGED_NOT_INSTALLED' -or $m.full_package_count -ne 51 -or $m.package_files.Count -ne 51 -or $m.changed_paths -ne 3 -or $m.retired.Count -ne 0 -or $m.base_archive_members -ne 1186 -or $m.archive_members -ne (1186+@($m.new_resources).Count)){throw 'Manifest scope changed'}
if(@($m.new_resources).Count -lt 1 -or @($m.new_resources.depot|Select-Object -Unique).Count -ne @($m.new_resources).Count){throw 'New resource cohort invalid'}
foreach($resource in $m.new_resources){if($resource.depot -notmatch '^towercontinued\\world_actions_wa2\\[a-zA-Z0-9_\\-]+\.questphase$' -or $resource.sha256 -cnotmatch '^[A-F0-9]{64}$'){throw 'Unexpected new controller depot/hash'}}
if(!$fixture -and ($m.game_root -cne $game -or $m.backup_root -cne $backup)){throw 'Manifest roots changed'}
$changes=@($m.package_files|Where-Object {$_.before -cne $_.after})
$expected=@('archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl','r6/scripts/PTFR_Consolidated/PTFR_RestorationBaseline.reds')
if($changes.Count -ne 3 -or @(Compare-Object ($changes.path|Sort-Object) ($expected|Sort-Object)).Count){throw 'Unexpected replacement paths'}
if(@($m.package_files.path|Select-Object -Unique).Count -ne 51){throw 'Duplicate package paths'}
foreach($f in $m.package_files){
 [void](Safe $game $f.path);[void](Safe (Join-Path $candidate 'package') $f.path)
 if((Hash (Safe (Join-Path $candidate 'package') $f.path)) -cne $f.after){throw ('Candidate file changed '+$f.path)}
}
foreach($p in $m.proofs){if((Hash $p.path) -cne $p.sha256){throw ('Proof changed '+$p.path)}}
# New installs require the exact compiled stack and resource-winner environment.
# An unrelated mod update does not prevent restoring this package's own backup.
if(!$fixture -and $Action -in @('Validate','Install')){
 if($m.runtime_inputs.Count -ne 64 -or $m.external_archives.Count -lt 1){throw 'Runtime/winner input inventory incomplete'}
 foreach($p in @($m.runtime_inputs)+@($m.external_archives)){
  if((Hash (Safe $game $p.path)) -cne $p.sha256){throw ('Runtime/winner environment changed '+$p.path)}
 }
}

if(!$fixture){
 foreach($name in @('deployment_tests_01.json','zip_proof_01.json','save_baseline_01.json')){
  $path=Join-Path $candidate $name;$pin=(Get-Content -LiteralPath ($path+'.sha256') -Raw).Trim()
  if((Hash $path) -cne $pin){throw ('Post-manifest proof changed '+$name)}
 }
 $tested=Get-Content -LiteralPath (Join-Path $candidate 'deployment_tests_01.json') -Raw|ConvertFrom-Json
 if($tested.status -cne 'PASS' -or $tested.interruption_points -ne 6 -or !$tested.normal_install_verify_rollback){throw 'Deployment fixtures incomplete'}
 $zipProof=Get-Content -LiteralPath (Join-Path $candidate 'zip_proof_01.json') -Raw|ConvertFrom-Json
 if($zipProof.status -cne 'UNRELEASED_FULL_51_PATH_ZIP_VERIFIED' -or $zipProof.members -ne 51 -or (Hash $zipProof.path) -cne $zipProof.sha256){throw 'Distribution ZIP proof invalid'}
}
$receipt=Safe $backup 'receipt.json'
function Stage([string]$rel){return Safe $game ($rel+'.PTFRWA2_STAGE')}
function VerifyUnchanged {foreach($f in $m.package_files){if($f.before -ceq $f.after -and (Hash (Safe $game $f.path)) -cne $f.before){throw ('Unchanged file drift '+$f.path)}}}
function VerifyBaseline {foreach($f in $m.package_files){if((Hash (Safe $game $f.path)) -cne $f.before){throw ('Production baseline drift '+$f.path)}}}
if($Action -in @('Verify','ValidateRollback','Rollback')){
 if(!(Test-Path -LiteralPath $receipt)){throw 'No deployment receipt'}
 $r=Get-Content -LiteralPath $receipt -Raw|ConvertFrom-Json -Depth 40
 if($r.manifest_sha256 -cne $manifestHash -or (Hash (Safe $backup 'install_manifest_01.json')) -cne $manifestHash){throw 'Receipt/backup manifest mismatch'}
 VerifyUnchanged
 foreach($f in $changes){
  $actual=Hash (Safe $game $f.path)
  if($actual -cne $f.before -and $actual -cne $f.after){throw ('Unknown production target state '+$f.path)}
  if((Hash (Safe (Join-Path $backup 'old') $f.path)) -cne $f.before){throw ('Old backup changed '+$f.path)}
 }
 if($Action -eq 'Verify'){
  foreach($f in $m.package_files){if((Hash (Safe $game $f.path)) -cne $f.after){throw ('Installed production mismatch '+$f.path)}}
  foreach($f in $changes){if(Test-Path -LiteralPath (Stage $f.path)){throw ('Install stage remains '+$f.path)}}
  @{status='VERIFIED';package_files=51;replacements=3}|ConvertTo-Json;exit
 }
 if($Action -eq 'ValidateRollback'){@{status='ROLLBACK_READY';replacements=3;save_undo=$false}|ConvertTo-Json;exit}
 foreach($f in $changes){
  Closed;$target=Safe $game $f.path;$stage=Stage $f.path
  if(Test-Path -LiteralPath $stage){
   $stageHash=Hash $stage;$held=Safe $backup ('interrupted_stage/'+$f.path+'.'+$stageHash)
   New-Item -ItemType Directory -Path (Split-Path $held -Parent) -Force|Out-Null
   if(!(Test-Path -LiteralPath $held)){Move-Item -LiteralPath $stage -Destination $held}else{if((Hash $held) -cne $stageHash){throw 'Interrupted stage conflict'};Remove-Item -LiteralPath $stage}
  }
  if((Hash $target) -ceq $f.before){continue}
  Copy-Item -LiteralPath (Safe (Join-Path $backup 'old') $f.path) -Destination $stage
  if((Hash $stage) -cne $f.before){throw ('Rollback stage mismatch '+$f.path)}
  Closed
  if((Hash $target) -cne $f.after){throw ('Target changed before rollback '+$f.path)}
  [IO.File]::Replace($stage,$target,[NullString]::Value)
  if((Hash $target) -cne $f.before){throw ('Rollback replacement mismatch '+$f.path)}
 }
 VerifyBaseline
 $r.status='ROLLED_BACK';$r|ConvertTo-Json -Depth 40|Set-Content -LiteralPath $receipt -Encoding utf8NoBOM
 @{status='ROLLED_BACK';restored_production=51;save_undo=$false}|ConvertTo-Json;exit
}
if(Test-Path -LiteralPath $backup){throw 'Recovery directory exists; inspect receipt instead'}
VerifyBaseline
foreach($f in $changes){if(Test-Path -LiteralPath (Stage $f.path)){throw ('Stage path occupied '+$f.path)}}
if($Action -eq 'Validate'){@{status='READY';production_paths=51;replacements=3}|ConvertTo-Json;exit}
New-Item -ItemType Directory -Path $backup|Out-Null
Copy-Item -LiteralPath $manifest -Destination (Safe $backup 'install_manifest_01.json')
$r=[ordered]@{status='BACKING_UP';manifest_sha256=$manifestHash;created_utc=[DateTime]::UtcNow.ToString('o');production_paths=51;replacements=3;game_launched=$false;save_edits=0;live_result='pending'}
function Receipt {$r|ConvertTo-Json -Depth 40|Set-Content -LiteralPath $receipt -Encoding utf8NoBOM}
Receipt
try{
 foreach($f in $changes){
  $held=Safe (Join-Path $backup 'old') $f.path;New-Item -ItemType Directory -Path (Split-Path $held -Parent) -Force|Out-Null
  Copy-Item -LiteralPath (Safe $game $f.path) -Destination $held
  if((Hash $held) -cne $f.before){throw ('Backup changed '+$f.path)}
 }
 $r.status='BACKED_UP';Receipt;FailAt 'AfterBackup'
 $n=0
 foreach($f in $changes){
  Closed;$target=Safe $game $f.path;$stage=Stage $f.path
  if((Hash $target) -cne $f.before){throw ('Target drift '+$f.path)}
  Copy-Item -LiteralPath (Safe (Join-Path $candidate 'package') $f.path) -Destination $stage
  if((Hash $stage) -cne $f.after){throw ('Stage mismatch '+$f.path)}
  FailAt 'AfterStage'
  Closed
  if((Hash $target) -cne $f.before){throw ('Target changed before replacement '+$f.path)}
  [IO.File]::Replace($stage,$target,[NullString]::Value)
  if((Hash $target) -cne $f.after){throw ('Replacement mismatch '+$f.path)}
  $n++;if($n -eq 1){FailAt 'AfterFirstReplace'};if($n -eq 2){FailAt 'AfterSecondReplace'}
 }
 FailAt 'AfterThirdReplace'
 FailAt 'BeforeReceipt'
 $r.status='WA2_51_PATH_INSTALLED_LIVE_PENDING';Receipt
}catch{$r.status='INTERRUPTED_REVIEW_REQUIRED';$r.error=$_.Exception.Message;Receipt;throw}
@{status=$r.status;production_paths=51;replacements=3;backup=$backup}|ConvertTo-Json
