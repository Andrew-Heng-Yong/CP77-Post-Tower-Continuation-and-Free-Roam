param(
 [ValidateSet('Validate','Install','Verify','ValidateRollback','Rollback')][string]$Action='Validate',
 [string]$FixtureRoot='',
 [ValidateSet('','AfterBackup','AfterFirstReplace','BeforeReceipt')][string]$TestFailPoint=''
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$c=Join-Path $PSScriptRoot 'candidate_03';$mf=Join-Path $c 'install_manifest_01.json'
function Hash([string]$p){if(!(Test-Path -LiteralPath $p -PathType Leaf)){return $null};return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function Safe([string]$root,[string]$rel){
 if([IO.Path]::IsPathRooted($rel) -or $rel.Contains(':') -or @($rel.Replace('\','/').Split('/')) -contains '..'){throw 'Unsafe relative path'}
 $base=[IO.Path]::GetFullPath($root).TrimEnd('\');$p=[IO.Path]::GetFullPath((Join-Path $base $rel))
 if(!$p.StartsWith($base+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Path escaped root'}
 $cur=$p;while($cur){if(Test-Path -LiteralPath $cur){if((Get-Item -LiteralPath $cur -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked path'}};$cur=Split-Path $cur -Parent}
 return $p
}
$fixture=$FixtureRoot -ne ''
$m=Get-Content -LiteralPath $mf -Raw|ConvertFrom-Json -Depth 20
if($m.status -cne 'PH1_STAGED_51_PATH_SUCCESSOR' -or $m.package_files.Count -ne 51 -or $m.changed_paths.Count -ne 2 -or $m.archive_members -ne 1572){throw 'Manifest scope drift'}
if((Hash $mf) -cne (Get-Content -LiteralPath ($mf+'.sha256') -Raw).Trim()){throw 'Manifest hash drift'}
$game=$m.game_root;$backup=$m.backup_root
if($fixture){
 $FixtureRoot=[IO.Path]::GetFullPath($FixtureRoot);$bound=[IO.Path]::GetFullPath((Join-Path $c 'deploy_fixtures_01')).TrimEnd('\')+'\'
 if(!$FixtureRoot.StartsWith($bound,[StringComparison]::OrdinalIgnoreCase)){throw 'Fixture outside controlled root'}
 $game=Safe $FixtureRoot 'game';$backup=Safe $FixtureRoot 'backup'
}elseif($TestFailPoint -ne ''){throw 'Failure injection only allowed in fixture'}
function Closed {if(!$fixture -and (Get-Process -Name Cyberpunk2077,REDprelauncher -ErrorAction SilentlyContinue)){throw 'Game or launcher is open'}}
function FailAt([string]$s){if($fixture -and $TestFailPoint -ceq $s){throw "Injected interruption $s"}}
Closed
$rows=@($m.package_files);$changes=@($rows|Where-Object {$_.before -cne $_.after})
$actualChanges=@($changes.path|Sort-Object) -join ','
$expectedChanges=@('archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl'|Sort-Object) -join ','
if($actualChanges -cne $expectedChanges){throw 'Unexpected changes'}
foreach($r in $rows){
 [void](Safe $game $r.path)
 $src=Safe (Join-Path $c 'package') $r.path
 if((Hash $src) -cne $r.after){throw ('Candidate changed '+$r.path)}
}
if((Hash (Join-Path $c 'verification_01.json')) -cne $m.validation_sha256 -or (Hash (Join-Path $c 'save_baseline_01.json')) -cne $m.save_baseline_sha256){throw 'Validation proof drift'}
if((Hash (Join-Path $c 'semantic_verification_01.json')) -cne $m.semantic_validation_sha256){throw 'Semantic proof drift'}
if(!$fixture -and (Hash (Safe $game 'archive/pc/mod/LizziesBDs.archive')) -cne $m.external_lizzies_archive_sha256){throw 'Lizzie add-on changed'}
function Baseline {foreach($r in $rows){if((Hash (Safe $game $r.path)) -cne $r.before){throw ('Production drift '+$r.path)}}}
function Installed {foreach($r in $rows){if((Hash (Safe $game $r.path)) -cne $r.after){throw ('Installed drift '+$r.path)}}}
$receipt=Safe $backup 'receipt.json'
function Stage($r){Safe $game ($r.path+'.PTFRPH1_STAGE')}
if($Action -in @('Verify','ValidateRollback','Rollback')){
 if(!(Test-Path -LiteralPath $receipt)){throw 'Missing recovery receipt'}
 $r=Get-Content -LiteralPath $receipt -Raw|ConvertFrom-Json
 if($r.manifest_sha256 -cne (Hash $mf)){throw 'Receipt mismatch'}
 foreach($x in $changes){if((Hash (Safe $backup ('old/'+$x.path))) -cne $x.before){throw ('Backup drift '+$x.path)}}
 if($Action -eq 'Verify'){Installed;@{status='VERIFIED';replacements=2}|ConvertTo-Json;exit}
 if($Action -eq 'ValidateRollback'){Installed;@{status='ROLLBACK_READY';replacements=2;save_undo=$false}|ConvertTo-Json;exit}
 foreach($x in $changes){
  Closed;$target=Safe $game $x.path;$stage=Stage $x
  if((Hash $target) -cne $x.after){throw ('Rollback target drift '+$x.path)}
  Copy-Item -LiteralPath (Safe $backup ('old/'+$x.path)) -Destination $stage
  if((Hash $stage) -cne $x.before){throw 'Rollback stage drift'}
  [IO.File]::Replace($stage,$target,[NullString]::Value)
 }
 Baseline;$r.status='ROLLED_BACK';$r|ConvertTo-Json|Set-Content -LiteralPath $receipt -Encoding utf8NoBOM
 @{status='ROLLED_BACK';replacements=2;save_undo=$false}|ConvertTo-Json;exit
}
if(Test-Path -LiteralPath $backup){throw 'Recovery path occupied'}
foreach($x in $changes){if(Test-Path -LiteralPath (Stage $x)){throw 'Stage path occupied'}}
Baseline
if($Action -eq 'Validate'){@{status='READY';package_files=51;replacements=2}|ConvertTo-Json;exit}
New-Item -ItemType Directory -Path $backup|Out-Null
$receiptData=[ordered]@{status='BACKING_UP';manifest_sha256=Hash $mf;created_utc=[DateTime]::UtcNow.ToString('o');replacements=2;game_launched=$false;save_writes=0;live_result='pending'}
function Receipt {$receiptData|ConvertTo-Json|Set-Content -LiteralPath $receipt -Encoding utf8NoBOM}
Receipt
try{
 foreach($x in $changes){$dest=Safe $backup ('old/'+$x.path);New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent)|Out-Null;Copy-Item -LiteralPath (Safe $game $x.path) -Destination $dest;if((Hash $dest) -cne $x.before){throw 'Backup mismatch'}}
 $receiptData.status='BACKED_UP';Receipt;FailAt 'AfterBackup'
 $i=0
 foreach($x in $changes){
  Closed;$target=Safe $game $x.path;$stage=Stage $x
  if((Hash $target) -cne $x.before){throw 'Target changed'}
  Copy-Item -LiteralPath (Safe (Join-Path $c 'package') $x.path) -Destination $stage
  if((Hash $stage) -cne $x.after){throw 'Stage mismatch'}
  [IO.File]::Replace($stage,$target,[NullString]::Value)
  if((Hash $target) -cne $x.after){throw 'Replace mismatch'}
  $i++;if($i -eq 1){FailAt 'AfterFirstReplace'}
 }
 FailAt 'BeforeReceipt';Installed;$receiptData.status='INSTALLED_VERIFIED';Receipt
 @{status='INSTALLED_VERIFIED';replacements=2;backup=$backup}|ConvertTo-Json
}catch{
 $reason=$_.Exception.Message
 foreach($x in $changes){
  $target=Safe $game $x.path;$stage=Stage $x
  if(Test-Path -LiteralPath $stage){Remove-Item -LiteralPath $stage}
  if((Hash $target) -ceq $x.after){Copy-Item -LiteralPath (Safe $backup ('old/'+$x.path)) -Destination $stage;[IO.File]::Replace($stage,$target,[NullString]::Value)}
 }
 Baseline;$receiptData.status='INTERRUPTED_ROLLED_BACK';$receiptData.error=$reason;Receipt
 throw "Install interrupted and rolled back: $reason"
}

