param(
 [ValidateSet('Validate','Install','Verify','ValidateRollback','Rollback')][string]$Action='Validate',
 [string]$FixtureRoot='',
 [ValidateSet('','AfterBackup','AfterStage','AfterFirstReplace','AfterSecondReplace','AfterThirdReplace','AfterFourthReplace','BeforeReceipt')][string]$TestFailPoint=''
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$candidate=Join-Path $PSScriptRoot 'candidate_02'
$manifest=Join-Path $candidate 'install_manifest_01.json'
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$backup=Join-Path $ws 'recovery/viktor_door_vd1_01'
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
if($m.status -cne 'VD1_FULL_51_PATH_SUCCESSOR_STAGED' -or $m.package_files.Count -ne 51 -or $m.managed_paths -ne 52 -or $m.changed_paths -ne 2 -or $m.archive_members -ne 1564){throw 'Manifest scope changed'}
if(!$fixture -and ($m.game_root -cne $game -or $m.backup_root -cne $backup)){throw 'Manifest root changed'}
$co=$m.compatibility_files[0]
if($m.compatibility_files.Count -ne 1 -or $co.path -cne 'r6/scripts/virtual-atelier-full/SetupNewTab.reds' -or $co.before -cne $co.after){throw 'Compatibility path changed'}
$managed=@($m.package_files)+@($m.compatibility_files)
$changes=@($m.package_files|Where-Object {$_.before -cne $_.after})
if($changes.Count -ne 2 -or @($changes.path | Where-Object {$_ -cnotin @('archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl')}).Count -or @($managed.path|Select-Object -Unique).Count -ne 52){throw 'Unexpected replacement set'}
function CandidateSource([string]$rel){if($rel -ceq $co.path){return $co.source};return Safe (Join-Path $candidate 'package') $rel}
foreach($f in $managed){
 [void](Safe $game $f.path);[void](CandidateSource $f.path)
 if((Hash (CandidateSource $f.path)) -cne $f.after){throw ('Candidate file changed '+$f.path)}
}
foreach($p in $m.proofs){if((Hash $p.path) -cne $p.sha256){throw ('Proof changed '+$p.path)}}
if(!$fixture -and $Action -in @('Validate','Install')){
 $sourceRoots=@('r6/scripts','red4ext/plugins/Codeware/Scripts','red4ext/plugins/ArchiveXL/Scripts','red4ext/plugins/TweakXL/Scripts','red4ext/plugins/mod_settings')
 $paths=@(foreach($root in $sourceRoots){Get-ChildItem -LiteralPath (Safe $game $root) -Filter '*.reds' -Recurse -File|ForEach-Object {[IO.Path]::GetRelativePath($game,$_.FullName).Replace('\','/')}})
 if(@(Compare-Object @($paths|Sort-Object) @($m.runtime_inputs.path|Sort-Object)).Count){throw 'Compiler source inventory changed'}
 foreach($p in $m.runtime_inputs){if((Hash (Safe $game $p.path)) -cne $p.sha256){throw ('Compiler source changed '+$p.path)}}
 $archives=@(Get-ChildItem -LiteralPath (Safe $game 'archive/pc') -Filter '*.archive' -Recurse -File|ForEach-Object {[IO.Path]::GetRelativePath($game,$_.FullName).Replace('\','/')}|Sort-Object)
 $expected=@(@($m.external_archives.path)+@('archive/pc/mod/zzzz_PTFR_Combined.archive')|Sort-Object)
 if(@(Compare-Object $archives $expected).Count){throw 'Archive inventory changed'}
 foreach($p in $m.external_archives){if((Hash (Safe $game $p.path)) -cne $p.sha256){throw ('External archive changed '+$p.path)}}
 $zip=Get-Content -LiteralPath (Join-Path $candidate 'zip_proof_01.json') -Raw|ConvertFrom-Json
 if($zip.status -cne 'FULL_51_PATH_ZIP_READBACK_PASS' -or $zip.members -ne 51 -or (Hash $zip.path) -cne $zip.sha256){throw 'Full ZIP proof invalid'}
}
$receipt=Safe $backup 'receipt.json'
function Stage([string]$rel){return Safe $game ($rel+'.PTFRVD1_STAGE')}
function VerifyUnchanged {foreach($f in $managed){if($f.before -ceq $f.after -and (Hash (Safe $game $f.path)) -cne $f.before){throw ('Unchanged file drift '+$f.path)}}}
function VerifyBaseline {foreach($f in $managed){if((Hash (Safe $game $f.path)) -cne $f.before){throw ('Production baseline drift '+$f.path)}}}
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
  foreach($f in $managed){if((Hash (Safe $game $f.path)) -cne $f.after){throw ('Installed production mismatch '+$f.path)}}
  foreach($f in $changes){if(Test-Path -LiteralPath (Stage $f.path)){throw ('Install stage remains '+$f.path)}}
  @{status='VERIFIED';package_files=51;compatibility_files=1;replacements=2}|ConvertTo-Json;exit
 }
 if($Action -eq 'ValidateRollback'){@{status='ROLLBACK_READY';replacements=2;save_undo=$false}|ConvertTo-Json;exit}
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
 @{status='ROLLED_BACK';restored_production=52;replacements=2;save_undo=$false}|ConvertTo-Json;exit
}
if(Test-Path -LiteralPath $backup){throw 'Recovery directory exists; inspect receipt instead'}
VerifyBaseline
foreach($f in $changes){if(Test-Path -LiteralPath (Stage $f.path)){throw ('Stage path occupied '+$f.path)}}
if($Action -eq 'Validate'){@{status='READY';production_paths=52;replacements=2}|ConvertTo-Json;exit}
New-Item -ItemType Directory -Path $backup|Out-Null
Copy-Item -LiteralPath $manifest -Destination (Safe $backup 'install_manifest_01.json')
$r=[ordered]@{status='BACKING_UP';manifest_sha256=$manifestHash;created_utc=[DateTime]::UtcNow.ToString('o');production_paths=52;replacements=2;game_launched=$false;save_edits=0;live_result='pending'}
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
  Copy-Item -LiteralPath (CandidateSource $f.path) -Destination $stage
  if((Hash $stage) -cne $f.after){throw ('Stage mismatch '+$f.path)}
  FailAt 'AfterStage'
  Closed
  if((Hash $target) -cne $f.before){throw ('Target changed before replacement '+$f.path)}
  [IO.File]::Replace($stage,$target,[NullString]::Value)
  if((Hash $target) -cne $f.after){throw ('Replacement mismatch '+$f.path)}
  $n++;if($n -eq 1){FailAt 'AfterFirstReplace'};if($n -eq 2){FailAt 'AfterSecondReplace'};if($n -eq 3){FailAt 'AfterThirdReplace'};if($n -eq 4){FailAt 'AfterFourthReplace'}
 }
 FailAt 'BeforeReceipt'
 $r.status='VD1_INSTALLED_LIVE_PENDING';Receipt
}catch{$r.status='INTERRUPTED_REVIEW_REQUIRED';$r.error=$_.Exception.Message;Receipt;throw}
@{status=$r.status;production_paths=52;replacements=2;backup=$backup}|ConvertTo-Json
