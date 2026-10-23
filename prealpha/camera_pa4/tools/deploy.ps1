param(
 [ValidateSet('Validate','Install','ValidateRollback','Rollback')][string]$Mode='Validate',
 [string]$Build='',
 [string]$RecoveryRoot='',
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$SaveRoot='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077',
 [switch]$Fixture,
 [string]$BaselineBuild='',
 [int]$FailAfterBackup=0,
 [int]$FailAfterReplace=0
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..')).TrimEnd('\')
$fixtureRoot=Join-Path $workspace 'research/pre_alpha_camera_pa4/fixtures'
$allowed=@(
 'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_PreAlpha/init.lua',
 'r6/scripts/PTFR_PreAlpha/PA1/PreAlphaArrivalPA1.reds'
)
function Full([string]$path){if(!$path -or ![IO.Path]::IsPathFullyQualified($path)){throw 'Absolute path required'};[IO.Path]::GetFullPath($path).TrimEnd('\')}
function NoReparse([string]$path){
 $cursor=Full $path
 while($cursor){
  try{$attributes=[IO.File]::GetAttributes($cursor)}
  catch [IO.FileNotFoundException] {$attributes=[IO.FileAttributes]::Normal}
  catch [IO.DirectoryNotFoundException] {$attributes=[IO.FileAttributes]::Normal}
  if(($attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw "Reparse path refused: $cursor"}
  $parent=[IO.Directory]::GetParent($cursor);if($null -eq $parent){break};$cursor=$parent.FullName
 }
}
function Bound([string]$path,[string]$root){
 $resolved=Full $path;$root=Full $root
 if(!$resolved.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){throw "Path outside scope: $resolved"}
 NoReparse $resolved;return $resolved
}
function Relative([string]$path){
 if(!$path -or $path.Contains('\') -or [IO.Path]::IsPathRooted($path) -or $path -match '[:*?"<>|\x00-\x1f]'){throw "Invalid relative path: $path"}
 foreach($part in $path.Split('/')){if(!$part -or $part -in @('.','..') -or $part -match '[. ]$' -or $part -match '^(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)'){throw "Invalid path segment: $path"}}
}
function At([string]$root,[string]$relative){Relative $relative;Bound (Join-Path $root $relative) $root}
function Hash([string]$path){NoReparse $path;(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash}
function SHA([string]$value){if($value -cnotmatch '^[A-F0-9]{64}$'){throw 'Invalid SHA256'}}
function Match([string]$path,[string]$expected){SHA $expected;if(!(Test-Path -LiteralPath $path -PathType Leaf) -or (Hash $path) -cne $expected){throw "File drift or missing file: $path"}}
function ReadJson([string]$path){NoReparse $path;Get-Content -LiteralPath $path -Raw|ConvertFrom-Json}
function WriteJson([string]$path,$value){NoReparse $path;[IO.File]::WriteAllText($path,($value|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))}
function Closed {if(@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Cyberpunk 2077 must be closed; no process will be terminated.'}}
function PackagePath([string]$relative){
 Relative $relative
 if($relative -cnotmatch '^(archive/pc/mod/TowerContinued_PreAlpha\.archive(?:\.xl)?|r6/scripts/PTFR_PreAlpha/.+\.reds|r6/tweaks/TowerContinued_PreAlpha\.yaml|bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_PreAlpha/.+\.lua)$'){throw 'Package path outside approved scope'}
}
function FileMap($files){
 $map=@{};if(@($files).Count -ne 53){throw 'Expected exactly 53 package files'}
 foreach($f in $files){PackagePath $f.relative;SHA $f.sha256;if($map.ContainsKey($f.relative)){throw 'Duplicate package path'};$map[$f.relative]=$f.sha256}
 return $map
}
function Files([string]$root){
 NoReparse $root
 if(!(Test-Path -LiteralPath $root)){return}
 $pending=[Collections.Generic.Stack[string]]::new();$pending.Push($root)
 while($pending.Count){
  $current=$pending.Pop();NoReparse $current;$item=Get-Item -LiteralPath $current -Force
  if(!$item.PSIsContainer){$item;continue}
  foreach($child in Get-ChildItem -LiteralPath $current -Force){NoReparse $child.FullName;if($child.PSIsContainer){$pending.Push($child.FullName)}else{$child}}
 }
}
function ProtectedFiles([string]$root,[string]$kind,[string]$inventoryRoot){
 NoReparse $root
 if(!(Test-Path -LiteralPath $root)){return}
 $pending=[Collections.Generic.Stack[string]]::new();$pending.Push($root)
 while($pending.Count){
  $current=$pending.Pop();NoReparse $current
  foreach($child in Get-ChildItem -LiteralPath $current -Force){
   $relative=[IO.Path]::GetRelativePath($inventoryRoot,$child.FullName).Replace('\','/')
   if(($child.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){
    # Framework rolling logs use same-directory file symlinks. Preserve their
    # metadata without following them; the regular log target is hashed by its
    # own directory entry. No other link, especially a directory link, is allowed.
    if($kind -cne 'game' -or $child.PSIsContainer -or $child.LinkType -cne 'SymbolicLink' -or
       $relative -cnotmatch '^(red4ext/plugins|bin/x64/plugins)/.+\.[lL][oO][gG]$'){throw "Reparse path refused: $($child.FullName)"}
    $linkTarget=[string]$child.LinkTarget
    Relative $linkTarget
    if($linkTarget.Contains('/') -or $linkTarget.Contains('\')){throw 'Framework log link target must be a single relative filename'}
    $target=Join-Path $child.DirectoryName $linkTarget;NoReparse $target
    if(!(Test-Path -LiteralPath $target -PathType Leaf) -or ([IO.File]::GetAttributes($target) -band [IO.FileAttributes]::Directory) -ne 0){throw 'Framework log link target must be an existing regular file'}
    [pscustomobject]@{FullName=$child.FullName;LinkMetadata=('SYMBOLIC_LINK_FILE|'+$linkTarget)}
   }elseif($child.PSIsContainer){$pending.Push($child.FullName)}
   else{[pscustomobject]@{FullName=$child.FullName;LinkMetadata=$null}}
  }
 }
}
function ProtectedSnapshot {
 $result=@{}
 foreach($entry in @(
  @{kind='game';root=$game;part='archive/pc/mod'},@{kind='game';root=$game;part='r6/scripts'},
  @{kind='game';root=$game;part='r6/tweaks'},@{kind='game';root=$game;part='r6/cache'},@{kind='game';root=$game;part='red4ext/plugins'},
  @{kind='game';root=$game;part='bin/x64/plugins'},@{kind='save';root=$saves;part=''}
 )){
  $scan=if($entry.part){At $entry.root $entry.part}else{$entry.root}
  foreach($file in ProtectedFiles $scan $entry.kind $entry.root){
   $relative=[IO.Path]::GetRelativePath($entry.root,$file.FullName).Replace('\','/')
   if($entry.kind -eq 'game' -and $relative -cin $allowed){continue}
   $key=$entry.kind+'/'+$relative
   $result[$key]=if($null -ne $file.LinkMetadata){$file.LinkMetadata}else{Hash $file.FullName}
  }
 }
 return $result
}
function CompareSnapshot($expected){
 $actual=ProtectedSnapshot
 if($actual.Count -ne $expected.Count){throw 'Protected file set changed'}
 foreach($key in $expected.Keys){if(!$actual.ContainsKey($key) -or $actual[$key] -cne $expected[$key]){throw "Protected file drift: $key"}}
 return $actual.Count
}
function CopyExact([string]$from,[string]$to,[string]$expected){
 Match $from $expected;NoReparse $to
 if(Test-Path -LiteralPath $to){throw "Copy destination exists: $to"}
 New-Item -ItemType Directory -Force (Split-Path -Parent $to)|Out-Null
 [IO.File]::Copy($from,$to,$false);Match $to $expected
}
function MoveExact([string]$from,[string]$to,[string]$expected){
 Closed;Match $from $expected;NoReparse $to
 if(Test-Path -LiteralPath $to){throw "Move destination exists: $to"}
 New-Item -ItemType Directory -Force (Split-Path -Parent $to)|Out-Null
 [IO.File]::Move($from,$to,$false);Match $to $expected
}
$game=Full $GameRoot;$saves=Full $SaveRoot;NoReparse $game;NoReparse $saves
if(!(Test-Path -LiteralPath $game -PathType Container) -or !(Test-Path -LiteralPath $saves -PathType Container)){throw 'Game and save roots must already exist'}
if($Fixture){
 [void](Bound $game $fixtureRoot);[void](Bound $saves $fixtureRoot)
 if(!$BaselineBuild){throw 'Fixture baseline required'}
 $baselinePath=Bound $BaselineBuild $fixtureRoot
 if($RecoveryRoot){$recovery=Bound $RecoveryRoot $fixtureRoot}
 if($Build){$buildRoot=Bound $Build $fixtureRoot}
}else{
 if($game -cne 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077' -or $saves -cne 'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077' -or $BaselineBuild -or $FailAfterBackup -or $FailAfterReplace){throw 'Unexpected live roots/options'}
 $baselinePath=Join-Path $workspace 'prealpha/handoff_pa3/build/pa3_01/build.json'
 Match $baselinePath 'AAC05EBBED94A72B8B7AAD03CE9EC8033483691E574EE80D681287B9899228AC'
 if($RecoveryRoot){$recovery=Bound $RecoveryRoot (Join-Path $workspace 'recovery')}
 if($Build){$buildRoot=Bound $Build (Join-Path $workspace 'prealpha/camera_pa4/build')}
}
if($FailAfterBackup -lt 0 -or $FailAfterBackup -gt 2 -or $FailAfterReplace -lt 0 -or $FailAfterReplace -gt 2){throw 'Invalid failure-injection count'}
Closed
$baseline=ReadJson $baselinePath;$oldMap=FileMap $baseline.package_files
foreach($relative in $allowed){if(!$oldMap.ContainsKey($relative)){throw 'Baseline missing approved target'}}
if($Mode -in @('ValidateRollback','Rollback')){
 if(!$RecoveryRoot){throw 'Exact RecoveryRoot required'}
 if(Test-Path -LiteralPath (Join-Path $recovery 'rollback_receipt.json')){throw 'This recovery transaction has already been rolled back'}
 $txnPath=At $recovery 'transaction.json'
 Match $txnPath (Get-Content -LiteralPath (At $recovery 'transaction.sha256') -Raw).Trim()
 $txn=ReadJson $txnPath
 if($txn.status -cne 'PA4_TWO_FILE_TRANSACTION' -or $txn.game_root -cne $game -or $txn.save_root -cne $saves -or $txn.baseline_sha256 -cne (Hash $baselinePath)){throw 'Recovery transaction identity mismatch'}
 $newMap=FileMap $txn.package_files
 foreach($relative in $oldMap.Keys){if(!$newMap.ContainsKey($relative) -or ($relative -cnotin $allowed -and $newMap[$relative] -cne $oldMap[$relative])){throw 'Recovery package differs outside approved targets'}}
 foreach($relative in $oldMap.Keys){
  $target=At $game $relative
  if($relative -cnotin $allowed){Match $target $oldMap[$relative];continue}
  if($newMap[$relative] -ceq $oldMap[$relative]){throw 'Recovery target lacks a real change'}
  $backup=At $recovery ('original/'+$relative);$removed=At $recovery ('rolled_back/'+$relative)
  if(Test-Path -LiteralPath $backup){Match $backup $oldMap[$relative]}
  if(Test-Path -LiteralPath $removed){Match $removed $newMap[$relative]}
  if(Test-Path -LiteralPath $target){
   $actual=Hash $target
   if($actual -cne $oldMap[$relative] -and $actual -cne $newMap[$relative]){throw "Installed target drift: $relative"}
   if($actual -ceq $newMap[$relative] -and (!(Test-Path -LiteralPath $backup) -or (Test-Path -LiteralPath $removed))){throw 'Missing backup or rollback destination conflict'}
  }elseif(!(Test-Path -LiteralPath $backup)){throw "Missing target and backup: $relative"}
 }
 $protected=ProtectedSnapshot
 if($Mode -eq 'ValidateRollback'){@{status='VALIDATED_PA4_ROLLBACK';protected_files=$protected.Count}|ConvertTo-Json;return}
 foreach($relative in $allowed){
  $target=At $game $relative;$backup=At $recovery ('original/'+$relative)
  if((Test-Path -LiteralPath $target) -and (Hash $target) -ceq $newMap[$relative]){MoveExact $target (At $recovery ('rolled_back/'+$relative)) $newMap[$relative]}
  if(!(Test-Path -LiteralPath $target)){Closed;CopyExact $backup $target $oldMap[$relative]}
  Match $target $oldMap[$relative]
 }
 foreach($relative in $oldMap.Keys){Match (At $game $relative) $oldMap[$relative]}
 $count=CompareSnapshot $protected
 WriteJson (At $recovery 'rollback_receipt.json') @{status='ROLLED_BACK_PA4_TO_PA3_FILES';utc=[DateTime]::UtcNow.ToString('o');protected_files=$count;save_bytes_changed=$false;cache_changed=$false;retained_original_backups=$true}
 Write-Output ('ROLLED_BACK '+$recovery);return
}
if(!$Build){throw 'Absolute Build directory required'}
$report=ReadJson (At $buildRoot 'build.json')
if(!$Fixture -and ($report.status -cne 'BUILT_BASELINE_IDENTICAL_COMPILE_PENDING' -or !$report.archive_unchanged -or $report.unchanged_files -ne 51 -or $report.prior_build_sha256 -cne (Hash $baselinePath))){throw 'PA4 immutable baseline identity mismatch'}
$compile=ReadJson (At $buildRoot 'compile.json');$tests=ReadJson (At $buildRoot 'tests.json')
if($compile.status -cne 'PASS_COMPILE_AND_READBACK_NOT_LIVE' -or $tests.status -cne 'PASS_NOT_LIVE'){throw 'Compile/readback and test PASS reports required'}
$reportHash=Hash (At $buildRoot 'build.json')
if($compile.build_sha256 -cne $reportHash -or $tests.build_sha256 -cne $reportHash){throw 'Verification reports do not match build'}
$packageRoot=Bound $report.package_root $buildRoot
$newMap=FileMap $report.package_files
if(@($report.changes).Count -ne 2){throw 'Exactly two approved changes required'}
$changes=@{}
foreach($change in $report.changes){
 if($change.relative -cnotin $allowed -or $changes.ContainsKey($change.relative)){throw 'Change outside approved scope or duplicate'}
 SHA $change.old_sha256;SHA $change.new_sha256
 if($change.old_sha256 -cne $oldMap[$change.relative] -or $change.new_sha256 -cne $newMap[$change.relative] -or $change.old_sha256 -ceq $change.new_sha256){throw 'Change hash mismatch'}
 $changes[$change.relative]=$true
}
foreach($relative in $oldMap.Keys){
 if(!$newMap.ContainsKey($relative)){throw 'Package path set changed'}
 if($relative -cnotin $allowed -and $newMap[$relative] -cne $oldMap[$relative]){throw 'Out-of-scope package modification'}
 Match (At $packageRoot $relative) $newMap[$relative]
 Match (At $game $relative) $oldMap[$relative]
}
$actualPackage=@(Files $packageRoot)
if($actualPackage.Count -ne 53){throw 'Package contains unexpected files'}
foreach($file in $actualPackage){$relative=[IO.Path]::GetRelativePath($packageRoot,$file.FullName).Replace('\','/');if(!$newMap.ContainsKey($relative)){throw 'Unlisted package file'}}
$protected=ProtectedSnapshot
if($Mode -eq 'Validate'){@{status='VALIDATED_PA4_TWO_FILE_UPGRADE';baseline_files=53;replacements=2;protected_files=$protected.Count}|ConvertTo-Json;return}
if(!$RecoveryRoot){throw 'Install requires a new explicit RecoveryRoot'}
if(Test-Path -LiteralPath $recovery){throw 'RecoveryRoot already exists'}
Closed;New-Item -ItemType Directory -Path $recovery|Out-Null
$txn=[ordered]@{status='PA4_TWO_FILE_TRANSACTION';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;save_root=$saves;baseline_sha256=Hash $baselinePath;build=$buildRoot;build_sha256=Hash (At $buildRoot 'build.json');package_files=$report.package_files;changes=$report.changes;protected=$protected}
WriteJson (At $recovery 'transaction.json') $txn
[IO.File]::WriteAllText((At $recovery 'transaction.sha256'),(Hash (At $recovery 'transaction.json')),[Text.UTF8Encoding]::new($false))
$backedUp=0;$replaced=0
try{
 foreach($relative in $allowed){CopyExact (At $packageRoot $relative) (At $recovery ('staged/'+$relative)) $newMap[$relative]}
 foreach($relative in $allowed){
  CopyExact (At $game $relative) (At $recovery ('original/'+$relative)) $oldMap[$relative]
  $backedUp++;if($FailAfterBackup -eq $backedUp){throw 'Injected fixture backup failure'}
 }
 foreach($relative in $allowed){
  MoveExact (At $game $relative) (At $recovery ('displaced/'+$relative)) $oldMap[$relative]
  MoveExact (At $recovery ('staged/'+$relative)) (At $game $relative) $newMap[$relative]
  $replaced++;if($FailAfterReplace -eq $replaced){throw 'Injected fixture replacement failure'}
 }
 foreach($relative in $newMap.Keys){Match (At $game $relative) $newMap[$relative]}
 $count=CompareSnapshot $protected
 WriteJson (At $recovery 'install_receipt.json') @{status='INSTALLED_PA4_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');replacements=$replaced;package_verified=53;protected_files=$count;save_bytes_changed=$false;cache_changed=$false;recovery=$recovery;build_sha256=$txn.build_sha256}
 Write-Output ('INSTALLED '+$recovery)
}catch{
 WriteJson (At $recovery 'failure.json') @{status='PA4_INSTALL_INTERRUPTED';error=$_.Exception.Message;backed_up=$backedUp;replaced=$replaced;instruction='Do not launch. Use this PA4 installer ValidateRollback then Rollback with this exact RecoveryRoot.'}
 throw
}
