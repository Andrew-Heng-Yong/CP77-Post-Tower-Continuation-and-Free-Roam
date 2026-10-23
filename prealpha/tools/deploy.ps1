param(
 [string]$ManifestPath,
 [ValidateSet('Validate','Install','Restore')][string]$Mode='Validate',
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$SaveRoot='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077',
 [string]$RecoveryRoot='',
 [switch]$Fixture,
 [int]$FailAfterMove=0,
 [int]$FailAfterPackage=0
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')).TrimEnd('\')
function Full([string]$p){[IO.Path]::GetFullPath($p).TrimEnd('\')}
function Bound([string]$p,[string]$root){
 $p=Full $p;$root=Full $root
 if(-not $p.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){throw "Path outside scope: $p"}
 $cursor=$p
 while($cursor){
  if(Test-Path -LiteralPath $cursor){if(((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw "Reparse path: $cursor"}}
  $parent=Split-Path -Parent $cursor;if($parent -eq $cursor){break};$cursor=$parent
 }
 return $p
}
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function Match([string]$p,[string]$h){if(!(Test-Path -LiteralPath $p -PathType Leaf) -or (Hash $p) -cne $h){throw "File drift: $p"}}
function Closed {if(@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Close Cyberpunk 2077 before deployment; no process will be killed.'}}
function Json([string]$p,$v){[IO.File]::WriteAllText($p,($v|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))}
function Relative([string]$p){
 if(!$p -or $p.Contains('\') -or [IO.Path]::IsPathRooted($p) -or $p -match '[:*?"<>|]' -or $p -match '[\x00-\x1f]'){throw "Invalid relative path: $p"}
 foreach($part in $p.Split('/')){if(!$part -or $part -in @('.','..') -or $part -match '[. ]$'){throw "Invalid path segment: $p"}}
 return $p
}
function At([string]$root,[string]$relative){[void](Relative $relative);return Bound (Join-Path $root $relative) $root}
function UnitFiles([string]$p){
 $item=Get-Item -LiteralPath $p -Force
 if(($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw "Reparse path: $p"}
 if(!$item.PSIsContainer){return ,$item}
 $all=@(Get-ChildItem -LiteralPath $p -Recurse -Force)
 if(@($all|Where-Object {($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0}).Count){throw "Nested reparse path: $p"}
 return @($all|Where-Object {!$_.PSIsContainer})
}
function ExactUnit([string]$target,$files){
 if(!(Test-Path -LiteralPath $target)){throw "Unit missing: $target"}
 $actual=@(UnitFiles $target);$expected=@($files);$seenFiles=@{}
 if($actual.Count -ne $expected.Count){throw "Unit contents changed: $target"}
 $leaf=Test-Path -LiteralPath $target -PathType Leaf
 foreach($f in $expected){
  if($leaf){if($f.path -cne '.'){throw 'Leaf marker invalid'};$p=$target}
  else{$p=At $target $f.path}
  $key=$p.ToLowerInvariant();if($seenFiles.ContainsKey($key)){throw "Duplicate unit file: $p"};$seenFiles[$key]=$true;Match $p $f.sha256
 }
 foreach($f in $actual){if(!$seenFiles.ContainsKey($f.FullName.ToLowerInvariant())){throw "Unlisted unit file: $($f.FullName)"}}
}
function PackagePath([string]$relative){
 [void](Relative $relative)
 if($relative -cnotmatch '^(archive/pc/mod/TowerContinued_PreAlpha\.archive(\.xl)?|r6/scripts/PTFR_PreAlpha/.+\.reds|r6/tweaks/TowerContinued_PreAlpha\.yaml|bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_PreAlpha/.+\.lua)$'){throw 'Package target outside scope'}
}
function UnitPath($u,[string]$keep){
 if($u.kind -notin @('game','save')){throw 'Unknown move kind'}
 [void](Relative $u.relative)
 if($u.kind -eq 'game' -and $u.relative -cnotmatch '^(archive/pc/mod/TowerContinued[^/]+\.(archive|xl)|r6/scripts/PTFR_[^/]+|r6/tweaks/TowerContinued[^/]+\.yaml|bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_[^/]+)$'){throw 'Cleanup outside project files'}
 if($u.kind -eq 'save' -and ($u.relative -cnotmatch '^(ManualSave|AutoSave|EndGameSave|PointOfNoReturnSave|QuickSave)-\d+$' -or $u.relative -eq $keep)){throw 'Invalid save cleanup target'}
}
function MoveExact([string]$source,[string]$dest){
 if(Test-Path -LiteralPath $dest){throw "Move destination exists: $dest"}
 New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null;Closed
 if(Test-Path -LiteralPath $source -PathType Container){[IO.Directory]::Move($source,$dest)}else{[IO.File]::Move($source,$dest,$false)}
}
$game=Full $GameRoot;$saves=Full $SaveRoot
if($Fixture){
 [void](Bound $game (Join-Path $workspace 'research/pre_alpha_clean/deploy_fixtures'))
 [void](Bound $saves (Join-Path $workspace 'research/pre_alpha_clean/deploy_fixtures'))
 if(!$RecoveryRoot){throw 'Fixture recovery required'}
 [void](Bound $RecoveryRoot (Join-Path $workspace 'research/pre_alpha_clean/deploy_fixtures'))
}elseif($game -cne 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077' -or $saves -cne 'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077' -or $FailAfterMove -or $FailAfterPackage){throw 'Unexpected deployment roots/options'}
Closed
if($Mode -eq 'Restore'){
 if(!$RecoveryRoot){throw 'Exact recovery directory is required'}
 $recovery=Bound $RecoveryRoot $workspace
 $receiptPath=Join-Path $recovery 'transaction.json'
 Match $receiptPath (Get-Content -LiteralPath (Join-Path $recovery 'transaction.sha256') -Raw).Trim()
 $txn=Get-Content -LiteralPath $receiptPath -Raw|ConvertFrom-Json
 if($txn.status -cne 'PREALPHA_INSTALL_TRANSACTION' -or $txn.keep_save -cne 'ManualSave-10'){throw 'Unrecognized recovery transaction'}
 if($txn.game_root -cne $game -or $txn.save_root -cne $saves){throw 'Recovery root mismatch'}
 if(Test-Path -LiteralPath (Join-Path $recovery 'restored.json')){throw 'Already restored'}
 # Validate every destination BEFORE any move. Newly created saves are never overwritten.
 foreach($u in $txn.units){
  UnitPath $u $txn.keep_save
  $root=if($u.kind -eq 'save'){$saves}else{$game}
  $target=At $root $u.relative
  $backup=At $recovery ($u.kind+'/'+$u.relative)
  if(Test-Path -LiteralPath $backup){
   if(Test-Path -LiteralPath $target){throw "Recovery conflict; preserve both and review: $target"}
   ExactUnit $backup $u.files
  }elseif(!(Test-Path -LiteralPath $target)){throw "Missing original and backup: $target"}
  else{ExactUnit $target $u.files}
 }
 foreach($f in $txn.package){
  PackagePath $f.relative;$target=At $game $f.relative;$dest=At $recovery ('removed_package/'+$f.relative)
  if(Test-Path -LiteralPath $target){Match $target $f.sha256;if(Test-Path -LiteralPath $dest){throw "Recovery package destination conflict: $dest"}}
  elseif(Test-Path -LiteralPath $dest){Match $dest $f.sha256}
 }
 foreach($f in $txn.package){
  $target=Bound (Join-Path $game $f.relative) $game
  if(Test-Path -LiteralPath $target){$dest=At $recovery ('removed_package/'+$f.relative);Match $target $f.sha256;MoveExact $target $dest}
 }
 foreach($u in $txn.units){
  $root=if($u.kind -eq 'save'){$saves}else{$game};$target=Bound (Join-Path $root $u.relative) $root;$backup=Bound (Join-Path $recovery ($u.kind+'/'+$u.relative)) $recovery
  if(Test-Path -LiteralPath $backup){ExactUnit $backup $u.files;MoveExact $backup $target;ExactUnit $target $u.files}
 }
 Json (Join-Path $recovery 'restored.json') @{status='RESTORED_ORIGINAL_FILES';utc=[DateTime]::UtcNow.ToString('o')}
 Write-Output ('RESTORED '+$recovery);return
}
if(!$ManifestPath){throw 'Manifest required'}
$manifest=Bound $ManifestPath $workspace;$m=Get-Content -LiteralPath $manifest -Raw|ConvertFrom-Json
if($m.status -cne 'PREALPHA_PACKAGE_VERIFIED' -or $m.keep_save -cne 'ManualSave-10'){throw 'Unverified/wrong package'}
$packageRoot=Bound $m.package_root $workspace
$packageSeen=@{}
foreach($f in $m.package){
 PackagePath $f.relative;$source=At $packageRoot $f.relative;Match $source $f.sha256
 $target=At $game $f.relative;$key=$target.ToLowerInvariant()
 if($packageSeen.ContainsKey($key)){throw 'Duplicate package target'};$packageSeen[$key]=$true
 if(Test-Path -LiteralPath $target){throw "Package already exists: $target"}
}
$seen=@{}
foreach($u in $m.units){
 UnitPath $u $m.keep_save
 $root=if($u.kind -eq 'save'){$saves}else{$game};$target=At $root $u.relative
 if($seen.ContainsKey($target.ToLowerInvariant())){throw 'Duplicate cleanup target'};$seen[$target.ToLowerInvariant()]=$true
 if($u.kind -eq 'game'){foreach($p in $packageSeen.Keys){if($p -eq $target -or $p.StartsWith($target+'\',[StringComparison]::OrdinalIgnoreCase)){throw "Package cleanup overlap: $target"}}}
 ExactUnit $target $u.files
}
foreach($f in $m.protected){
 if($f.kind -notin @('game','save')){throw 'Unknown protected kind'}
 $root=if($f.kind -eq 'save'){$saves}else{$game};$p=At $root $f.relative;Match $p $f.sha256
 foreach($target in $seen.Keys){if($p -eq $target -or $p.StartsWith($target+'\',[StringComparison]::OrdinalIgnoreCase)){throw "Protected cleanup overlap: $p"}}
}
$keep=Bound (Join-Path $saves $m.keep_save) $saves
if(!(Test-Path -LiteralPath $keep -PathType Container)){throw 'Selected ending fixture missing'}
$keepFiles=@(UnitFiles $keep|ForEach-Object {[ordered]@{path=[IO.Path]::GetRelativePath($keep,$_.FullName).Replace('\','/');sha256=Hash $_.FullName}})
$saveNames=@(Get-ChildItem -LiteralPath $saves -Directory -Force |Where-Object {$_.Name -match '^(ManualSave|AutoSave|EndGameSave|PointOfNoReturnSave|QuickSave)-\d+$'}|ForEach-Object {$_.Name})
$expectedSaveNames=@($m.keep_save)+@($m.units|Where-Object kind -eq 'save'|ForEach-Object {$_.relative})
if(@(Compare-Object ($saveNames|Sort-Object) ($expectedSaveNames|Sort-Object)).Count){throw 'Active save set differs from cleanup plan'}
if($Mode -eq 'Validate'){@{status='VALIDATED';moves=@($m.units).Count;package_files=@($m.package).Count;keep=$keep}|ConvertTo-Json;return}
$recovery=if($RecoveryRoot){Bound $RecoveryRoot $workspace}else{Bound (Join-Path $workspace ('recovery/pre_alpha_clean_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $workspace}
if(Test-Path -LiteralPath $recovery){throw 'Recovery destination exists'}
New-Item -ItemType Directory -Path $recovery|Out-Null
$txn=[ordered]@{status='PREALPHA_INSTALL_TRANSACTION';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;save_root=$saves;manifest=$manifest;manifest_sha256=Hash $manifest;units=$m.units;package=$m.package;keep_save=$m.keep_save;keep_files=$keepFiles}
Json (Join-Path $recovery 'transaction.json') $txn
[IO.File]::WriteAllText((Join-Path $recovery 'transaction.sha256'),(Hash (Join-Path $recovery 'transaction.json')),[Text.UTF8Encoding]::new($false))
# Preserve even the retained source save before any cleanup.
$keepBackup=Bound (Join-Path $recovery ('retained_source/'+$m.keep_save)) $recovery
New-Item -ItemType Directory -Force (Split-Path -Parent $keepBackup)|Out-Null
Copy-Item -LiteralPath $keep -Destination $keepBackup -Recurse
ExactUnit $keepBackup $keepFiles;ExactUnit $keep $keepFiles
$count=0
try{
 # Stage and verify package bytes before moving any installed file or save.
 foreach($f in $m.package){$source=At $packageRoot $f.relative;$stage=At $recovery ('staged_package/'+$f.relative);New-Item -ItemType Directory -Force (Split-Path -Parent $stage)|Out-Null;[IO.File]::Copy($source,$stage,$false);Match $stage $f.sha256}
 foreach($u in $m.units){
  $root=if($u.kind -eq 'save'){$saves}else{$game};$target=Bound (Join-Path $root $u.relative) $root;$dest=Bound (Join-Path $recovery ($u.kind+'/'+$u.relative)) $recovery
  ExactUnit $target $u.files;MoveExact $target $dest;ExactUnit $dest $u.files
  $count++;if($FailAfterMove -gt 0 -and $count -eq $FailAfterMove){throw 'Injected fixture failure'}
 }
 $packageCount=0
 foreach($f in $m.package){$stage=At $recovery ('staged_package/'+$f.relative);$target=At $game $f.relative;Match $stage $f.sha256;MoveExact $stage $target;Match $target $f.sha256;$packageCount++;if($FailAfterPackage -gt 0 -and $packageCount -eq $FailAfterPackage){throw 'Injected fixture package failure'}}
 foreach($f in $m.protected){$root=if($f.kind -eq 'save'){$saves}else{$game};Match (Bound (Join-Path $root $f.relative) $root) $f.sha256}
 $remaining=@(Get-ChildItem -LiteralPath $saves -Directory|Where-Object {$_.Name -match '^(ManualSave|AutoSave|EndGameSave|PointOfNoReturnSave|QuickSave)-\d+$'})
 if($remaining.Count -ne 1 -or $remaining[0].Name -cne $m.keep_save){throw 'Active save set differs from plan'}
 Json (Join-Path $recovery 'install_receipt.json') @{status='INSTALLED_PREALPHA_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');manifest_sha256=Hash $manifest;moved_units=$count;package_files=@($m.package).Count;kept_save=$m.keep_save;protected_verified=@($m.protected).Count;save_contents_modified=$false;cache_modified=$false;recovery=$recovery}
 Write-Output ('INSTALLED '+$recovery)
}catch{
 Json (Join-Path $recovery 'failure.json') @{error=$_.Exception.Message;moved_units=$count;instruction='Do not launch. Restore with this script and the exact RecoveryRoot.'}
 throw
}
