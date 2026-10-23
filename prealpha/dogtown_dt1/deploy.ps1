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
$relatives=@('archive/pc/mod/TowerContinued_Dogtown_DT1.archive','archive/pc/mod/TowerContinued_Dogtown_DT1.archive.xl')
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
 $pins=@{
  'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_SideJobsCaptureS26/init.lua'='74D08E42E1D8F8B1932A2E71321D00E8C1AC13101C7BEF2BA43AB3F5F6C23BBF'
  'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_SideJobsCaptureS26/data.json'='FCABF6AC14AB00D08739C8411A0A32E8D523DB8A71EC4EC3AB87C3DE5857E1A3'
  'archive/pc/mod/000_TowerContinued_SideJobs_S22.archive'='D60EBBC7346F4FFFF0C08F301FEA360D59CAB503D84CFF6039E40ACADEB40E78'
  'archive/pc/mod/000_TowerContinued_SideJobs_S22.archive.xl'='D88437FB829F76E774535D2B982D69205931A3A94BF59E2D890165205087A223'
  'r6/scripts/TowerContinued_SideJobs_S22/SideJobsS22.reds'='44CA2D37FAC081F60A1A88516ED0B4365645EEC4C09FBE5D4639AC2D7477EC39'
  'r6/scripts/TowerContinued_SideJobs_S2/SideJobsS2.reds'='58F134FFE6CCD8DF0AF30FCCABBFD161BBBCC8AEF75E25C16D18303992134295'
  'archive/pc/mod/000000_TowerContinued_SideJobs_S25.archive'='DDCDA37330E056342D6F0C4C4245596323809CAD4DA10ED73258113875149C33'
  'archive/pc/mod/000000_TowerContinued_SideJobs_S25.archive.xl'='1720E7A2C0DEC5894370EE346BFEB9BE71F9AB10F5597AEB129EA9776075D025'
  'r6/scripts/TowerContinued_SideJobs_S25/SideJobsS25.reds'='E72BC8E83BE13D6D2601343E9108EEF8BCF442B5A69F04D4A02C98A90CB488FA'
  'r6/scripts/TowerContinued_SideJobs_S23/SideJobsS23.reds'='8E82481B770C3FE11AE4D15CEA0B422F05DDDE4441B9134384990E07183CD6F0'
 }
 foreach($p in $pins.Keys){Match (Bound (Join-Path $game $p) $game) $pins[$p]}
 return $pins.Count
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
 if($txn.status -cne 'DT1_ADD_ONLY' -or $txn.game_root -cne $game -or $txn.save_root -cne $saves -or $txn.installer_sha256 -cne (Hash $PSCommandPath)){throw 'Recovery identity mismatch'}
 Scope $txn.files
 foreach($f in $txn.files){
  $name=[IO.Path]::GetFileName($f.relative);Match (Join-Path $recovery $name) $f.sha256
  $target=Bound (Join-Path $game $f.relative) $game
  $removed=Join-Path $recovery ('removed_'+$name);NoLink $removed
  if(Test-Path -LiteralPath $removed){throw 'Recovery destination exists'}
  if(Test-Path -LiteralPath $target){Match $target $f.sha256}
 }
 $protected=Snapshot
 if($Mode -eq 'ValidateRollback'){@{status='VALIDATED_DT1_ROLLBACK';original_package_verified=$original;protected_files=$protected.Count}|ConvertTo-Json;return}
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
 WriteJson (Join-Path $recovery 'rollback_receipt.json') @{status='ROLLED_BACK_DT1';utc=[DateTime]::UtcNow.ToString('o');moved_recoverably=$moved;protected_files=$count;original_package_verified=(OriginalPackage);save_changes=$false}
 Write-Output "ROLLED_BACK: $recovery";return
}
if(!$Build){throw 'Build directory required'}
$buildRoot=Bound $Build $buildBound
$manifestPath=Join-Path $buildRoot 'build.json';$manifest=ReadJson $manifestPath
if($manifest.game_writes -ne 0 -or $manifest.save_writes -ne 0){throw 'Build writes not allowed'}
if($manifest.status -cne 'BUILT_DT1_LIVE_PENDING' -or @($manifest.resources.PSObject.Properties).Count -lt 1 -or @($manifest.boots).Count -lt 1 -or !$manifest.packed_readback -or !$manifest.native_scenes_unchanged -or @($manifest.official_overrides).Count -ne 0 -or $manifest.runtime_scripts_added -ne 0){throw 'Manifest scope mismatch'}
Scope $manifest.files
foreach($f in $manifest.files){
 Match (Join-Path $buildRoot ([IO.Path]::GetFileName($f.relative))) $f.sha256
 $target=Bound (Join-Path $game $f.relative) $game
 if(Test-Path -LiteralPath $target){throw 'DT1 already present; refusing overwrite'}
 if(!(Test-Path -LiteralPath (Split-Path -Parent $target) -PathType Container)){throw 'Existing mod folder required'}
}
$tests=ReadJson (Join-Path $buildRoot 'tests.json')
if($tests.status -cne 'PASS_NOT_LIVE' -or $tests.build_sha256 -cne (Hash $manifestPath)){throw 'Matching tests required'}
Match (Join-Path $PSScriptRoot 'test.py') $tests.tester_sha256
$resources=ReadJson (Join-Path $buildRoot 'resource_check.json')
if($resources.status -cne 'PASS_NOT_LIVE' -or $resources.build_sha256 -cne (Hash $manifestPath) -or @($resources.overrides).Count -ne 0 -or @($resources.official).Count -lt 1 -or !$resources.modlist_absent -or @($resources.official_overrides).Count){throw 'Matching resource audit required'}
Match (Join-Path $PSScriptRoot 'resource_check.ps1') $resources.checker_sha256
if(!$Fixture){
 if(Test-Path (Join-Path $game 'archive/pc/mod/modlist.txt')){throw 'Explicit load order appeared; priority not verified'}
 $proofs=@(Get-ChildItem -LiteralPath $fixtureRoot -Filter 'results.json' -File -Recurse|ForEach-Object {ReadJson $_.FullName}|Where-Object {
  $_.status -ceq 'PASS_WORKSPACE_FIXTURES_NOT_LIVE' -and $_.build_sha256 -ceq (Hash $manifestPath) -and $_.installer_sha256 -ceq (Hash $PSCommandPath) -and $_.tester_sha256 -ceq (Hash (Join-Path $PSScriptRoot 'test_deploy.py')) -and $_.cases -ge 31 -and $_.checks -ge 41
 })
 if($proofs.Count -lt 1){throw 'Matching deployment fixture proof required'}
 foreach($p in $manifest.source_pins.PSObject.Properties){Match (Bound (Join-Path $workspace $p.Name) $workspace) $p.Value}
 $actual=@(Get-ChildItem (Join-Path $game 'archive/pc/mod') -File -Filter '*.archive')
 if($actual.Count -ne @($resources.installed_archives).Count){throw 'Installed archive set changed'}
 foreach($a in $resources.installed_archives){Match (Bound (Join-Path $game ('archive/pc/mod/'+$a.name)) $game) $a.sha256}
 $actualXL=@(Get-ChildItem (Join-Path $game 'archive/pc/mod') -File -Filter '*.xl')
 if($actualXL.Count -ne @($manifest.installed_xl).Count){throw 'Installed XL set changed'}
 foreach($p in $manifest.installed_xl){Match (Bound (Join-Path $game ('archive/pc/mod/'+$p.name)) $game) $p.sha256}
}
$protected=Snapshot
if($Mode -eq 'Validate'){@{status='VALIDATED_DT1_ADD_ONLY';additions=2;original_package_verified=$original;protected_files=$protected.Count;build_sha256=Hash $manifestPath}|ConvertTo-Json;return}
if(!$recovery -or (Test-Path -LiteralPath $recovery)){throw 'New recovery directory required'}
Closed
New-Item -ItemType Directory -Path $recovery -ErrorAction Stop | Out-Null
foreach($f in $manifest.files){$name=[IO.Path]::GetFileName($f.relative);CopyExact (Join-Path $buildRoot $name) (Join-Path $recovery $name) $f.sha256}
WriteJson (Join-Path $recovery 'transaction.json') @{status='DT1_ADD_ONLY';game_root=$game;save_root=$saves;files=$manifest.files;build=$buildRoot;build_sha256=Hash $manifestPath;utc=[DateTime]::UtcNow.ToString('o');protected=$protected;installer_sha256=Hash $PSCommandPath}
[IO.File]::WriteAllText((Join-Path $recovery 'transaction.sha256'),(Hash (Join-Path $recovery 'transaction.json')),[Text.UTF8Encoding]::new($false))
try{
 $copied=0
 foreach($f in $manifest.files){
  Closed;CopyExact (Join-Path $recovery ([IO.Path]::GetFileName($f.relative))) (Bound (Join-Path $game $f.relative) $game) $f.sha256
  $copied++;if($FailAfterFirst -and $copied -eq 1){throw 'Injected fixture failure after first addition'}
 }
 $count=Same $protected
 WriteJson (Join-Path $recovery 'install_receipt.json') @{status='INSTALLED_DT1_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');additions=2;replacements=0;installed_files=$manifest.files;original_package_verified=(OriginalPackage);protected_files=$count;protected_save_files=@($protected.Keys|Where-Object{$_ -like 'save/*'}).Count;protected_cache_files=@($protected.Keys|Where-Object{$_ -like 'game/r6/cache/*'}).Count;settings_changed=$false;build_sha256=Hash $manifestPath;recovery=$recovery}
 Write-Output "INSTALLED: $recovery"
}catch{
 WriteJson (Join-Path $recovery 'failure.json') @{status='INSTALL_INTERRUPTED';message=$_.Exception.Message;instruction='Do not launch. Use ValidateRollback then Rollback with this exact recovery directory.'}
 throw
}




