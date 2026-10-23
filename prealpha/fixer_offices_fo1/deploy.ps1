param(
 [ValidateSet('Validate','Install','ValidateRollback','Rollback')][string]$Mode='Validate',
 [string]$Build='', [string]$RecoveryRoot='',
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$SaveRoot='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077',
 [switch]$Fixture, [switch]$FailAfterFirst
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$fixtureRoot=Join-Path $PSScriptRoot 'fixtures'
$relatives=@('archive/pc/mod/TowerContinued_FixerOffices_FO1.archive','archive/pc/mod/TowerContinued_FixerOffices_FO1.archive.xl')
# Import only the pinned filesystem safety and snapshot definitions. Never run
# the older diagnostic installer's main body or mutate its historical evidence.
$lib=Join-Path $workspace 'prealpha/graphics_gd2/tools/deploy.ps1'
if((Get-FileHash -LiteralPath $lib).Hash -cne '1D1D204D792D65FF30757B455E57826787E395A1DF0C1D5352A60D0757EC3307'){throw 'Safety helper changed'}
$text=Get-Content -LiteralPath $lib -Raw
$start=$text.IndexOf('function Full(');$end=$text.IndexOf('$game=Full $GameRoot;')
if($start -lt 0 -or $end -le $start){throw 'Helper boundary changed'}
$defs=$text.Substring($start,$end-$start)
if([regex]::Matches($defs,[regex]::Escape('if($rel -ceq $relative)')).Count -ne 1){throw 'Snapshot boundary changed'}
$defs=$defs.Replace('if($rel -ceq $relative)','if($rel -cin $relatives)')
. ([scriptblock]::Create($defs))
function OriginalPackage {
 if($Fixture){return 0}
 $base=Join-Path $workspace 'prealpha/postending_pa6/build/pa6_02/build.json'
 Match $base 'BE71C5AC4D2F9267AFD97DE65B85136033427A2EEAEB42B505A833853004A299'
 $files=@((ReadJson $base).package_files);if($files.Count -ne 59){throw 'Unexpected PA6 baseline'}
 foreach($f in $files){Match (Bound (Join-Path $game $f.relative) $game) $f.sha256}
 Match (Join-Path $game 'archive/pc/mod/TowerContinued_StairsFX_GD2.archive') '03851DAA463B50FD78E2049C8A1ACDF04041E13C78B0538DCCC1955734768BDD'
 return $files.Count
}
function Scope($files){
 if(@($files).Count -ne 2 -or @($files|Select-Object -ExpandProperty relative -Unique).Count -ne 2){throw 'Exactly two unique additions required'}
 for($i=0;$i -lt 2;$i++){
  if($files[$i].relative -cne $relatives[$i] -or $files[$i].sha256 -cnotmatch '^[A-F0-9]{64}$'){throw 'Addition scope mismatch'}
 }
}
$game=Full $GameRoot;$saves=Full $SaveRoot;NoLink $game;NoLink $saves
if(!(Test-Path -LiteralPath $game -PathType Container) -or !(Test-Path -LiteralPath $saves -PathType Container)){throw 'Existing game/save directories required'}
if($Fixture){
 [void](Bound $game $fixtureRoot);[void](Bound $saves $fixtureRoot)
 $buildBound=$fixtureRoot;$recoveryBound=$fixtureRoot
}else{
 if($game -cne 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077' -or $saves -cne 'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077' -or $FailAfterFirst){throw 'Unapproved live roots/options'}
 $buildBound=Join-Path $PSScriptRoot 'build';$recoveryBound=Join-Path $workspace 'recovery'
}
$recovery=if($RecoveryRoot){Bound $RecoveryRoot $recoveryBound}else{''}
Closed
$original=OriginalPackage
if($Mode -in @('ValidateRollback','Rollback')){
 if(!$recovery){throw 'Exact recovery directory required'}
 if(Test-Path -LiteralPath (Join-Path $recovery 'rollback_receipt.json')){throw 'Already rolled back'}
 $txnPath=Join-Path $recovery 'transaction.json';$digest=Get-Content -LiteralPath (Join-Path $recovery 'transaction.sha256') -Raw
 Match $txnPath $digest;$txn=ReadJson $txnPath
 if($txn.status -cne 'FO1_ADD_ONLY' -or $txn.game_root -cne $game -or $txn.save_root -cne $saves){throw 'Recovery identity mismatch'}
 Scope $txn.files
 foreach($f in $txn.files){
  $name=[IO.Path]::GetFileName($f.relative);Match (Join-Path $recovery $name) $f.sha256
  $target=Bound (Join-Path $game $f.relative) $game
  $removed=Join-Path $recovery ('removed_'+$name);NoLink $removed
  if(Test-Path -LiteralPath $removed){throw 'Recovery destination exists'}
  if(Test-Path -LiteralPath $target){Match $target $f.sha256}
 }
 $protected=Snapshot
 if($Mode -eq 'ValidateRollback'){@{status='VALIDATED_FO1_ROLLBACK';original_package_verified=$original;protected_files=$protected.Count}|ConvertTo-Json;return}
 $moved=0
 foreach($f in $txn.files){
  $target=Bound (Join-Path $game $f.relative) $game
  if(Test-Path -LiteralPath $target){
   Closed;Match $target $f.sha256
   $removed=Join-Path $recovery ('removed_'+[IO.Path]::GetFileName($f.relative))
   [IO.File]::Move($target,$removed,$false);Match $removed $f.sha256;$moved++
  }
 }
 $count=Same $protected
 WriteJson (Join-Path $recovery 'rollback_receipt.json') @{status='ROLLED_BACK_FO1';utc=[DateTime]::UtcNow.ToString('o');moved_recoverably=$moved;protected_files=$count;original_package_verified=(OriginalPackage);save_changes=$false}
 Write-Output "ROLLED_BACK: $recovery";return
}
if(!$Build){throw 'Build directory required'}
$buildRoot=Bound $Build $buildBound
$manifestPath=Join-Path $buildRoot 'build.json';$manifest=ReadJson $manifestPath
if($manifest.status -cne 'BUILT_FO1_LIVE_PENDING' -or @($manifest.resources.PSObject.Properties).Count -ne 7 -or @($manifest.offices).Count -ne 7 -or !$manifest.packed_readback -or !$manifest.native_scenes_unchanged -or @($manifest.official_overrides).Count -ne 0 -or $manifest.runtime_scripts_added -ne 0){throw 'Manifest scope mismatch'}
Scope $manifest.files
foreach($f in $manifest.files){
 Match (Join-Path $buildRoot ([IO.Path]::GetFileName($f.relative))) $f.sha256
 $target=Bound (Join-Path $game $f.relative) $game
 if(Test-Path -LiteralPath $target){throw 'FO1 already present; refusing overwrite'}
 if(!(Test-Path -LiteralPath (Split-Path -Parent $target) -PathType Container)){throw 'Existing mod folder required'}
}
$tests=ReadJson (Join-Path $buildRoot 'tests.json')
if($tests.status -cne 'PASS_NOT_LIVE' -or $tests.build_sha256 -cne (Hash $manifestPath)){throw 'Matching tests required'}
Match (Join-Path $PSScriptRoot 'test.py') $tests.tester_sha256
$resources=ReadJson (Join-Path $buildRoot 'resource_check.json')
if($resources.status -cne 'PASS_NOT_LIVE' -or $resources.build_sha256 -cne (Hash $manifestPath) -or @($resources.overrides).Count){throw 'Matching resource audit required'}
Match (Join-Path $PSScriptRoot 'resource_check.ps1') $resources.checker_sha256
if(!$Fixture){
 foreach($p in $manifest.source_pins.PSObject.Properties){Match (Bound (Join-Path $workspace $p.Name) $workspace) $p.Value}
 $actual=@(Get-ChildItem (Join-Path $game 'archive/pc/mod') -File -Filter '*.archive')
 if($actual.Count -ne @($resources.installed_archives).Count){throw 'Installed archive set changed'}
 foreach($a in $resources.installed_archives){Match (Bound (Join-Path $game ('archive/pc/mod/'+$a.name)) $game) $a.sha256}
 foreach($p in $manifest.installed_injections|Sort-Object source -Unique){Match (Bound (Join-Path $game ('archive/pc/mod/'+$p.source)) $game) $p.source_sha256}
}
$protected=Snapshot
if($Mode -eq 'Validate'){@{status='VALIDATED_FO1_ADD_ONLY';additions=2;original_package_verified=$original;protected_files=$protected.Count;build_sha256=Hash $manifestPath}|ConvertTo-Json;return}
if(!$recovery -or (Test-Path -LiteralPath $recovery)){throw 'New recovery directory required'}
Closed
New-Item -ItemType Directory -Path $recovery -ErrorAction Stop | Out-Null
foreach($f in $manifest.files){$name=[IO.Path]::GetFileName($f.relative);CopyExact (Join-Path $buildRoot $name) (Join-Path $recovery $name) $f.sha256}
WriteJson (Join-Path $recovery 'transaction.json') @{status='FO1_ADD_ONLY';game_root=$game;save_root=$saves;files=$manifest.files;build=$buildRoot;build_sha256=Hash $manifestPath;utc=[DateTime]::UtcNow.ToString('o');protected=$protected;installer_sha256=Hash $PSCommandPath}
[IO.File]::WriteAllText((Join-Path $recovery 'transaction.sha256'),(Hash (Join-Path $recovery 'transaction.json')),[Text.UTF8Encoding]::new($false))
try{
 $copied=0
 foreach($f in $manifest.files){
  Closed;CopyExact (Join-Path $recovery ([IO.Path]::GetFileName($f.relative))) (Bound (Join-Path $game $f.relative) $game) $f.sha256
  $copied++;if($FailAfterFirst -and $copied -eq 1){throw 'Injected fixture failure after first addition'}
 }
 $count=Same $protected
 WriteJson (Join-Path $recovery 'install_receipt.json') @{status='INSTALLED_FO1_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');additions=2;replacements=0;installed_files=$manifest.files;original_package_verified=(OriginalPackage);protected_files=$count;protected_save_files=@($protected.Keys|Where-Object{$_ -like 'save/*'}).Count;protected_cache_files=@($protected.Keys|Where-Object{$_ -like 'game/r6/cache/*'}).Count;settings_changed=$false;build_sha256=Hash $manifestPath;recovery=$recovery}
 Write-Output "INSTALLED: $recovery"
}catch{
 WriteJson (Join-Path $recovery 'failure.json') @{status='INSTALL_INTERRUPTED';message=$_.Exception.Message;instruction='Do not launch. Use ValidateRollback then Rollback with this exact recovery directory.'}
 throw
}
