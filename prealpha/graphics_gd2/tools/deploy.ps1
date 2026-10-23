param(
 [ValidateSet('Validate','Install','ValidateRollback','Rollback')][string]$Mode='Validate',
 [string]$Build='', [string]$RecoveryRoot='',
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$SaveRoot='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077',
 [switch]$Fixture, [switch]$FailAfterCopy
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..')).TrimEnd('\')
$fixtureRoot=Join-Path $workspace 'prealpha/graphics_gd2/fixtures'
$archiveName='TowerContinued_StairsFX_GD2.archive'
$relative='archive/pc/mod/'+$archiveName
$baseline=Join-Path $workspace 'prealpha/camera_pa4/build/pa4_02/build.json'
function Full([string]$p){if(!$p -or ![IO.Path]::IsPathFullyQualified($p)){throw 'Absolute path required'};[IO.Path]::GetFullPath($p).TrimEnd('\')}
function NoLink([string]$p){
 $p=Full $p
 while($p){
  try{$a=[IO.File]::GetAttributes($p)}catch [IO.FileNotFoundException]{$a=0}catch [IO.DirectoryNotFoundException]{$a=0}
  if(($a -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw "Reparse path refused: $p"}
  $parent=[IO.Directory]::GetParent($p);if(!$parent){break};$p=$parent.FullName
 }
}
function Bound([string]$p,[string]$root){$p=Full $p;$root=Full $root;if(!$p.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){throw "Outside approved root: $p"};NoLink $p;return $p}
function Closed {if(@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Close Cyberpunk first; installer never terminates processes.'}}
function Hash([string]$p){NoLink $p;(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function Match([string]$p,[string]$sha){if($sha -cnotmatch '^[A-F0-9]{64}$' -or (Hash $p) -cne $sha){throw "Hash mismatch: $p"}}
function ReadJson([string]$p){NoLink $p;Get-Content -LiteralPath $p -Raw | ConvertFrom-Json}
function WriteJson([string]$p,$data){NoLink $p;if(Test-Path -LiteralPath $p){throw "Evidence already exists: $p"};[IO.File]::WriteAllText($p,($data|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))}
function CopyExact([string]$from,[string]$to,[string]$sha){Match $from $sha;NoLink $to;if(Test-Path -LiteralPath $to){throw "Refusing overwrite: $to"};[IO.File]::Copy($from,$to,$false);Match $to $sha}
function OriginalPackage {
 if($Fixture){return 0}
 Match $baseline '8CD6316A136BC46F5BE040C40D9886F3EED612FA9DF045C24A8D8A1A343E54FD'
 $files=@((ReadJson $baseline).package_files)
 if($files.Count -ne 53){throw 'Unexpected PA4 baseline'}
 foreach($f in $files){Match (Bound (Join-Path $game $f.relative) $game) $f.sha256}
 return $files.Count
}
function Snapshot {
 $map=@{}
 foreach($part in @('archive/pc/mod','r6/scripts','r6/tweaks','r6/cache','red4ext/plugins','bin/x64/plugins','engine/config','r6/config')){
  $scan=Bound (Join-Path $game $part) $game
  if(!(Test-Path -LiteralPath $scan)){continue}
  $todo=[Collections.Generic.Stack[string]]::new();$todo.Push($scan)
  while($todo.Count){
   $dir=$todo.Pop();NoLink $dir
   foreach($f in Get-ChildItem -LiteralPath $dir -Force){
    $rel=[IO.Path]::GetRelativePath($game,$f.FullName).Replace('\','/')
    if($rel -ceq $relative){continue}
    if(($f.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){
     if($f.PSIsContainer -or $f.LinkType -cne 'SymbolicLink' -or $rel -cnotmatch '^(red4ext/plugins|bin/x64/plugins)/.+\.[lL][oO][gG]$'){throw "Protected reparse refused: $($f.FullName)"}
     $link=[string]$f.LinkTarget
     if(!$link -or $link -match '[/\\:]' -or $link -in @('.','..')){throw 'Unexpected log link target'}
     $logTarget=Join-Path $f.DirectoryName $link;NoLink $logTarget
     if(!(Test-Path -LiteralPath $logTarget -PathType Leaf)){throw 'Broken log link'}
     $map['game/'+$rel]='LINK:'+ $link
    }elseif($f.PSIsContainer){$todo.Push($f.FullName)}else{$map['game/'+$rel]=Hash $f.FullName}
   }
  }
 }
 $todo=[Collections.Generic.Stack[string]]::new();$todo.Push($saves)
 while($todo.Count){
  $dir=$todo.Pop();NoLink $dir
  foreach($f in Get-ChildItem -LiteralPath $dir -Force){
   NoLink $f.FullName
   if($f.PSIsContainer){$todo.Push($f.FullName)}else{$map['save/'+[IO.Path]::GetRelativePath($saves,$f.FullName).Replace('\','/')]=Hash $f.FullName}
  }
 }
 if(!$Fixture){$map['settings/UserSettings.json']=Hash 'C:\Users\Ayong\AppData\Local\CD Projekt Red\Cyberpunk 2077\UserSettings.json'}
 return $map
}
function Same($before){$after=Snapshot;if($before.Count -ne $after.Count){throw 'Protected file set changed'};foreach($k in $before.Keys){if(!$after.ContainsKey($k) -or $before[$k] -cne $after[$k]){throw "Protected drift: $k"}};return $after.Count}
$game=Full $GameRoot;$saves=Full $SaveRoot;NoLink $game;NoLink $saves
if(!(Test-Path -LiteralPath $game -PathType Container) -or !(Test-Path -LiteralPath $saves -PathType Container)){throw 'Existing game/save directories required'}
if($Fixture){
 [void](Bound $game $fixtureRoot);[void](Bound $saves $fixtureRoot)
 $buildBound=$fixtureRoot;$recoveryBound=$fixtureRoot
}else{
 if($game -cne 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077' -or $saves -cne 'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077' -or $FailAfterCopy){throw 'Unapproved live roots/options'}
 $buildBound=Join-Path $workspace 'prealpha/graphics_gd2/build';$recoveryBound=Join-Path $workspace 'recovery'
}
$target=Bound (Join-Path $game $relative) $game
$recovery=if($RecoveryRoot){Bound $RecoveryRoot $recoveryBound}else{''}
Closed
$verifiedOriginal=OriginalPackage
if($Mode -in @('Validate','Install') -and (Test-Path -LiteralPath (Join-Path $game 'archive/pc/mod/TowerContinued_DizzyDiagnostic_GD1.archive'))){throw 'Withdraw the old GD1 diagnostic before GD2 installation'}
if($Mode -in @('ValidateRollback','Rollback')){
 if(!$recovery){throw 'Exact recovery directory required'}
 if(Test-Path -LiteralPath (Join-Path $recovery 'rollback_receipt.json')){throw 'Already rolled back'}
 $txnPath=Join-Path $recovery 'transaction.json';$digest=Get-Content -LiteralPath (Join-Path $recovery 'transaction.sha256') -Raw
 Match $txnPath $digest
 $txn=ReadJson $txnPath
 if($txn.status -cne 'GD2_ADD_ONLY' -or $txn.game_root -cne $game -or $txn.save_root -cne $saves -or $txn.relative -cne $relative){throw 'Recovery identity mismatch'}
 $staged=Join-Path $recovery $archiveName;Match $staged $txn.sha256
 $removed=Join-Path $recovery ('removed_'+$archiveName);NoLink $removed
 if(Test-Path -LiteralPath $removed){throw 'Recovery destination already exists'}
 if(Test-Path -LiteralPath $target){Match $target $txn.sha256}
 $protected=Snapshot
 if($Mode -eq 'ValidateRollback'){@{status='VALIDATED_GD2_ROLLBACK';target_present=(Test-Path -LiteralPath $target);original_package_verified=$verifiedOriginal;protected_files=$protected.Count}|ConvertTo-Json;return}
 $moved=$false
 if(Test-Path -LiteralPath $target){Closed;Match $target $txn.sha256;[IO.File]::Move($target,$removed,$false);Match $removed $txn.sha256;$moved=$true}
 $count=Same $protected
 WriteJson (Join-Path $recovery 'rollback_receipt.json') @{status='ROLLED_BACK_GD2';utc=[DateTime]::UtcNow.ToString('o');diagnostic_moved_recoverably=$moved;protected_files=$count;original_package_verified=(OriginalPackage);save_or_settings_changes=$false}
 Write-Output "ROLLED_BACK: $recovery";return
}
if(!$Build){throw 'Build directory required'}
$buildRoot=Bound $Build $buildBound
$manifestPath=Join-Path $buildRoot 'build.json';$manifest=ReadJson $manifestPath
if($manifest.status -cne 'BUILT_GD2_CANDIDATE' -or $manifest.resource_count -ne 1 -or $manifest.resource_depot -cne 'ep1\fx\quest\q307\q307_falling_down_stairs.effect' -or $manifest.archive -cne $archiveName){throw 'Diagnostic manifest scope mismatch'}
$source=Join-Path $buildRoot $archiveName;Match $source $manifest.archive_sha256
$tests=ReadJson (Join-Path $buildRoot 'tests.json')
if($tests.status -cne 'PASS_NOT_LIVE' -or $tests.build_sha256 -cne (Hash $manifestPath)){throw 'Matching tests/readback required'}
if(Test-Path -LiteralPath $target){throw 'Diagnostic already present; refusing overwrite'}
if(!(Test-Path -LiteralPath (Split-Path -Parent $target) -PathType Container)){throw 'Existing mod archive directory required'}
$protected=Snapshot
if($Mode -eq 'Validate'){@{status='VALIDATED_GD2_ADD_ONLY';additions=1;original_package_verified=$verifiedOriginal;protected_files=$protected.Count;build_sha256=Hash $manifestPath}|ConvertTo-Json;return}
if(!$recovery -or (Test-Path -LiteralPath $recovery)){throw 'New recovery directory required'}
Closed
New-Item -ItemType Directory -Path $recovery -ErrorAction Stop | Out-Null
$staged=Join-Path $recovery $archiveName
CopyExact $source $staged $manifest.archive_sha256
WriteJson (Join-Path $recovery 'transaction.json') @{status='GD2_ADD_ONLY';game_root=$game;save_root=$saves;relative=$relative;sha256=$manifest.archive_sha256;build=$buildRoot;build_sha256=Hash $manifestPath;utc=[DateTime]::UtcNow.ToString('o');protected=$protected}
[IO.File]::WriteAllText((Join-Path $recovery 'transaction.sha256'),(Hash (Join-Path $recovery 'transaction.json')),[Text.UTF8Encoding]::new($false))
try{
 Closed;CopyExact $staged $target $manifest.archive_sha256
 if($FailAfterCopy){throw 'Injected fixture failure after copy'}
 $count=Same $protected
 WriteJson (Join-Path $recovery 'install_receipt.json') @{status='INSTALLED_GD2_CANDIDATE_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');additions=1;replacements=0;installed_sha256=Hash $target;original_package_verified=(OriginalPackage);protected_files=$count;protected_save_files=@($protected.Keys|Where-Object{$_ -like 'save/*'}).Count;protected_cache_files=@($protected.Keys|Where-Object{$_ -like 'game/r6/cache/*'}).Count;settings_changed=$false;build_sha256=Hash $manifestPath;recovery=$recovery}
 Write-Output "INSTALLED: $recovery"
}catch{
 WriteJson (Join-Path $recovery 'failure.json') @{status='INSTALL_INTERRUPTED';message=$_.Exception.Message;instruction='Do not launch. Use ValidateRollback then Rollback with this exact recovery directory.'}
 throw
}
