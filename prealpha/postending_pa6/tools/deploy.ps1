param(
 [ValidateSet('Validate','Install','ValidateRollback','Rollback')][string]$Mode='Validate',
 [string]$Build='', [string]$RecoveryRoot='',
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$SaveRoot='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077',
 [switch]$Fixture,[string]$BaselineBuild='',
 [int]$FailAfterBackup=0,[int]$FailAfterReplace=0
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..')).TrimEnd('\')
$fixtureRoot=Join-Path $workspace 'research/postending_pa6/fixtures'
. (Join-Path $PSScriptRoot 'scope.ps1')
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
 if($relative -cnotmatch '^(archive/pc/mod/(?:TowerContinued_(?:PreAlpha|Optics_PA5)\.archive(?:\.xl)?|0_TowerContinued_RogueLipsync_PA6\.archive)|r6/scripts/PTFR_PreAlpha/.+\.reds|r6/tweaks/TowerContinued_PreAlpha\.yaml|bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_PreAlpha/.+\.lua)$'){throw 'Package path outside approved scope'}
}
function FileMap($files,[int]$count=59){
 $map=@{};if(@($files).Count -ne $count){throw 'Unexpected package file count'}
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
  @{kind='game';root=$game;part='bin/x64/plugins'},@{kind='game';root=$game;part='engine/config'},@{kind='game';root=$game;part='r6/config'},@{kind='save';root=$saves;part=''}
 )){
  $scan=if($entry.part){At $entry.root $entry.part}else{$entry.root}
  foreach($file in ProtectedFiles $scan $entry.kind $entry.root){
   $relative=[IO.Path]::GetRelativePath($entry.root,$file.FullName).Replace('\','/')
   if($entry.kind -eq 'game' -and $relative -cin $allowed){continue}
   $key=$entry.kind+'/'+$relative
   $result[$key]=if($null -ne $file.LinkMetadata){$file.LinkMetadata}else{Hash $file.FullName}
  }
 }
 if(!$Fixture){$result['settings/UserSettings.json']=Hash 'C:\Users\Ayong\AppData\Local\CD Projekt Red\Cyberpunk 2077\UserSettings.json'}
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
 [void](Bound $to $recovery)
 New-Item -ItemType Directory -Force (Split-Path -Parent $to)|Out-Null
 # Copies occur only within this transaction's recovery tree. Preserve an
 # interrupted temporary copy, then verify a new copy before atomic publication.
 $partial=$to+'.pa6-copying';NoReparse $partial
 if(Test-Path -LiteralPath $partial){
  $held=$partial+'.interrupted-'+[Guid]::NewGuid().ToString('N')
  MoveExact $partial $held (Hash $partial)
 }
 Closed;[IO.File]::Copy($from,$partial,$false);Match $partial $expected
 MoveExact $partial $to $expected
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
 $baselinePath=Join-Path $workspace 'prealpha/postending_pa5/build/pa5_03/build.json';Match $baselinePath $baselineSHA
 if($RecoveryRoot){$recovery=Bound $RecoveryRoot (Join-Path $workspace 'recovery')}
 if($Build){$buildRoot=Bound $Build (Join-Path $workspace 'prealpha/postending_pa6/build')}
 Match (At $game $gd2Relative) $gd2SHA
}
if($FailAfterBackup -lt 0 -or $FailAfterBackup -gt 3 -or $FailAfterReplace -lt 0 -or $FailAfterReplace -gt 4){throw 'Invalid failure-injection count'}
Closed
$baseline=ReadJson $baselinePath;$oldMap=FileMap $baseline.package_files 58
foreach($rel in $replacePaths){if(!$oldMap.ContainsKey($rel)){throw 'Baseline missing approved replacement'}}
foreach($rel in $addPaths){if($oldMap.ContainsKey($rel)){throw 'Addition already in baseline'}}
function ValidateMaps($newMap){
 foreach($rel in $oldMap.Keys){if(!$newMap.ContainsKey($rel)){throw 'Baseline file removed'};if($rel -cnotin $replacePaths -and $oldMap[$rel] -cne $newMap[$rel]){throw 'Out-of-scope package modification'}}
 foreach($rel in $replacePaths){if($oldMap[$rel] -ceq $newMap[$rel]){throw 'Replacement lacks a real change'}}
 foreach($rel in $newMap.Keys){if(!$oldMap.ContainsKey($rel) -and $rel -cnotin $addPaths){throw 'Out-of-scope package addition'}}
 foreach($rel in $addPaths){if(!$newMap.ContainsKey($rel)){throw 'Missing required addition'}}
}
if($Mode -in @('ValidateRollback','Rollback')){
 if(!$RecoveryRoot){throw 'Exact RecoveryRoot required'}
 if(Test-Path -LiteralPath (Join-Path $recovery 'rollback_receipt.json')){throw 'This recovery transaction has already been rolled back'}
 $txnPath=At $recovery 'transaction.json';Match $txnPath (Get-Content -LiteralPath (At $recovery 'transaction.sha256') -Raw).Trim()
 $txn=ReadJson $txnPath
 if($txn.status -cne 'PA6_SCOPED_TRANSACTION' -or $txn.game_root -cne $game -or $txn.save_root -cne $saves -or $txn.baseline_sha256 -cne (Hash $baselinePath)){throw 'Recovery transaction identity mismatch'}
 $newMap=FileMap $txn.package_files;ValidateMaps $newMap
 foreach($rel in $oldMap.Keys){
  $target=At $game $rel
  if($rel -cnotin $replacePaths){Match $target $oldMap[$rel];continue}
  $backup=At $recovery ('original/'+$rel);$removed=At $recovery ('rolled_back/'+$rel)
  if(Test-Path -LiteralPath $backup){Match $backup $oldMap[$rel]}
  if(Test-Path -LiteralPath $removed){Match $removed $newMap[$rel]}
  if(Test-Path -LiteralPath $target){
   $hash=Hash $target
   if($hash -cne $oldMap[$rel] -and $hash -cne $newMap[$rel]){throw "Installed target drift: $rel"}
   if($hash -ceq $newMap[$rel] -and (!(Test-Path -LiteralPath $backup) -or (Test-Path -LiteralPath $removed))){throw 'Missing backup or rollback destination conflict'}
  }elseif(!(Test-Path -LiteralPath $backup)){throw "Missing target and backup: $rel"}
 }
 foreach($rel in $addPaths){
  $target=At $game $rel;$removed=At $recovery ('rolled_back/'+$rel)
  if(Test-Path -LiteralPath $target){Match $target $newMap[$rel];if(Test-Path -LiteralPath $removed){throw 'Rollback destination conflict'}}
  if(Test-Path -LiteralPath $removed){Match $removed $newMap[$rel]}
 }
 $protected=ProtectedSnapshot
 if($Mode -eq 'ValidateRollback'){@{status='VALIDATED_PA6_ROLLBACK';protected_files=$protected.Count}|ConvertTo-Json;return}
 foreach($rel in $allowed){
  $target=At $game $rel
  if((Test-Path -LiteralPath $target) -and (Hash $target) -ceq $newMap[$rel]){MoveExact $target (At $recovery ('rolled_back/'+$rel)) $newMap[$rel]}
  if($rel -cin $replacePaths -and !(Test-Path -LiteralPath $target)){
   $restore=At $recovery ('restoring/'+$rel)
   if(Test-Path -LiteralPath $restore){Match $restore $oldMap[$rel]}
   else{CopyExact (At $recovery ('original/'+$rel)) $restore $oldMap[$rel]}
   MoveExact $restore $target $oldMap[$rel]
  }
 }
 foreach($rel in $oldMap.Keys){Match (At $game $rel) $oldMap[$rel]}
 foreach($rel in $addPaths){if(Test-Path -LiteralPath (At $game $rel)){throw 'Added file not recovered'}}
 $count=CompareSnapshot $protected
 WriteJson (At $recovery 'rollback_receipt.json') @{status='ROLLED_BACK_PA6_TO_PA5_PLUS_GD2';utc=[DateTime]::UtcNow.ToString('o');protected_files=$count;save_bytes_changed=$false;cache_changed=$false;recovered_additions=1;restored_originals=3}
 Write-Output ('ROLLED_BACK '+$recovery);return
}
if(!$Build){throw 'Absolute Build directory required'}
$report=ReadJson (At $buildRoot 'build.json')
if(!$Fixture -and ($report.status -cne 'BUILT_BASELINE_IDENTICAL_COMPILE_PENDING' -or !$report.archive_unchanged -or $report.unchanged_files -ne 55 -or $report.prior_build_sha256 -cne (Hash $baselinePath))){throw 'PA6 immutable baseline identity mismatch'}
$compile=ReadJson (At $buildRoot 'compile.json');$tests=ReadJson (At $buildRoot 'tests.json')
if($compile.status -cne 'PASS_COMPILE_AND_READBACK_NOT_LIVE' -or $tests.status -cne 'PASS_NOT_LIVE'){throw 'Compile/readback and test PASS reports required'}
$reportHash=Hash (At $buildRoot 'build.json')
if($compile.build_sha256 -cne $reportHash -or $tests.build_sha256 -cne $reportHash){throw 'Verification reports do not match build'}
if($tests.compile_sha256 -cne (Hash (At $buildRoot 'compile.json'))){throw 'Tests do not match compile report'}
$packageRoot=Bound $report.package_root $buildRoot
$newMap=FileMap $report.package_files;ValidateMaps $newMap
if(@($report.changes).Count -ne 4){throw 'Exactly four approved changes required'}
$changes=@{}
foreach($change in $report.changes){
 $rel=$change.relative
 if($rel -cnotin $allowed -or $changes.ContainsKey($rel)){throw 'Change outside approved scope or duplicate'}
 SHA $change.new_sha256
 if($change.new_sha256 -cne $newMap[$rel]){throw 'Change hash mismatch'}
 if($rel -cin $replacePaths){SHA $change.old_sha256;if($change.old_sha256 -cne $oldMap[$rel] -or $change.kind -cne 'replace'){throw 'Change hash mismatch'}}
 elseif($null -ne $change.old_sha256 -or $change.kind -cne 'add'){throw 'Invalid addition metadata'}
 $changes[$rel]=$true
}
foreach($rel in $newMap.Keys){Match (At $packageRoot $rel) $newMap[$rel]}
foreach($rel in $oldMap.Keys){Match (At $game $rel) $oldMap[$rel]}
foreach($rel in $addPaths){if(Test-Path -LiteralPath (At $game $rel)){throw "Addition target already exists: $rel"}}
$actualPackage=@(Files $packageRoot)
if($actualPackage.Count -ne 59){throw 'Package contains unexpected files'}
foreach($file in $actualPackage){$rel=[IO.Path]::GetRelativePath($packageRoot,$file.FullName).Replace('\','/');if(!$newMap.ContainsKey($rel)){throw 'Unlisted package file'}}
# Match the component's audited archive inputs immediately before deployment.
# This admission check is intentionally absent from rollback: later user mods
# must not prevent restoring our known files, and are protected by snapshot.
$archiveRoot=At $game 'archive/pc/mod'
if(Test-Path -LiteralPath (Join-Path $archiveRoot 'modlist.txt')){throw 'Custom archive load order requires separate review'}
$archiveInputs=@{}
foreach($entry in $report.archive_inventory){
 Relative $entry.archive;SHA $entry.sha256
 if($entry.archive.Contains('/') -or $entry.archive -cnotmatch '\.archive$' -or $archiveInputs.ContainsKey($entry.archive)){throw 'Invalid archive inventory'}
 $archiveInputs[$entry.archive]=$entry.sha256
}
$actualArchives=@(Get-ChildItem -LiteralPath $archiveRoot -Filter '*.archive' -File)
if(!$archiveInputs.Count -or $actualArchives.Count -ne $archiveInputs.Count){throw 'Audited archive inventory changed'}
foreach($file in $actualArchives){if(!$archiveInputs.ContainsKey($file.Name)){throw 'Audited archive inventory changed'};Match $file.FullName $archiveInputs[$file.Name]}
$protected=ProtectedSnapshot
if($Mode -eq 'Validate'){@{status='VALIDATED_PA6_UPGRADE';baseline_files=58;replacements=3;additions=1;protected_files=$protected.Count}|ConvertTo-Json;return}
if(!$RecoveryRoot){throw 'Install requires a new explicit RecoveryRoot'}
if(Test-Path -LiteralPath $recovery){throw 'RecoveryRoot already exists'}
Closed;New-Item -ItemType Directory -Path $recovery|Out-Null
$txn=[ordered]@{status='PA6_SCOPED_TRANSACTION';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;save_root=$saves;baseline_sha256=Hash $baselinePath;build=$buildRoot;build_sha256=$reportHash;package_files=$report.package_files;changes=$report.changes;protected=$protected;preserve_gd2=$true}
WriteJson (At $recovery 'transaction.json') $txn
[IO.File]::WriteAllText((At $recovery 'transaction.sha256'),(Hash (At $recovery 'transaction.json')),[Text.UTF8Encoding]::new($false))
$backedUp=0;$replaced=0
try{
 foreach($rel in $allowed){CopyExact (At $packageRoot $rel) (At $recovery ('staged/'+$rel)) $newMap[$rel]}
 foreach($rel in $replacePaths){CopyExact (At $game $rel) (At $recovery ('original/'+$rel)) $oldMap[$rel];$backedUp++;if($FailAfterBackup -eq $backedUp){throw 'Injected fixture backup failure'}}
 foreach($rel in $allowed){
  if($rel -cin $replacePaths){MoveExact (At $game $rel) (At $recovery ('displaced/'+$rel)) $oldMap[$rel]}
  MoveExact (At $recovery ('staged/'+$rel)) (At $game $rel) $newMap[$rel]
  $replaced++;if($FailAfterReplace -eq $replaced){throw 'Injected fixture replacement failure'}
 }
 foreach($rel in $newMap.Keys){Match (At $game $rel) $newMap[$rel]}
 $count=CompareSnapshot $protected
 WriteJson (At $recovery 'install_receipt.json') @{status='INSTALLED_PA6_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');replacements=3;additions=1;package_verified=59;protected_files=$count;save_bytes_changed=$false;cache_changed=$false;gd2_preserved=$true;recovery=$recovery;build_sha256=$txn.build_sha256}
 Write-Output ('INSTALLED '+$recovery)
}catch{
 WriteJson (At $recovery 'failure.json') @{status='PA6_INSTALL_INTERRUPTED';error=$_.Exception.Message;backed_up=$backedUp;applied=$replaced;instruction='Do not launch. Use this PA6 installer ValidateRollback then Rollback with this exact RecoveryRoot.'}
 throw
}
