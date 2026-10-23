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
$relatives=@('archive/pc/mod/TowerContinued_SideJobs_S2.archive','archive/pc/mod/TowerContinued_SideJobs_S2.archive.xl','r6/scripts/TowerContinued_SideJobs_S2/SideJobsS2.reds')
# Import only hash-pinned helper definitions, never an older installer's main.
$lib=Join-Path $workspace 'prealpha/graphics_gd2/tools/deploy.ps1'
if((Get-FileHash -LiteralPath $lib).Hash -cne '1D1D204D792D65FF30757B455E57826787E395A1DF0C1D5352A60D0757EC3307'){throw 'Safety helper changed'}
$text=Get-Content -LiteralPath $lib -Raw
$start=$text.IndexOf('function Full(');$end=$text.IndexOf('$game=Full $GameRoot;')
if($start -lt 0 -or $end -le $start){throw 'Helper boundary changed'}
$defs=$text.Substring($start,$end-$start)
if([regex]::Matches($defs,[regex]::Escape('if($rel -ceq $relative)')).Count -ne 1){throw 'Snapshot boundary changed'}
$defs=$defs.Replace('if($rel -ceq $relative)','if($rel -cin $relatives)')
. ([scriptblock]::Create($defs))
$prior=Join-Path $workspace 'prealpha/ncpd_repair_n21/deploy.ps1'
Match $prior 'BF2707160A098226BF09AEA32611D5F7B91412BFE1B4C057F0B6420F95CF49B4'
$text=Get-Content -LiteralPath $prior -Raw;$start=$text.IndexOf('function OriginalPackage {');$end=$text.IndexOf('function Scope(',[Math]::Max(0,$start))
if($start -lt 0 -or $end -le $start){throw 'Baseline helper boundary changed'}
. ([scriptblock]::Create($text.Substring($start,$end-$start).Replace('function OriginalPackage {','function PriorPackage {')))
$prior=Join-Path $workspace 'prealpha/races_r1/deploy.ps1'
Match $prior 'AB38881AFE99AF3EDB05993441EDB84FFAF703A2F2F39F976AB9321F16FD51C3'
$text=Get-Content -LiteralPath $prior -Raw;$start=$text.IndexOf('function N22Package {');$end=$text.IndexOf('function Scope(',[Math]::Max(0,$start))
if($start -lt 0 -or $end -le $start){throw 'R1 baseline helper boundary changed'}
. ([scriptblock]::Create($text.Substring($start,$end-$start).Replace('function OriginalPackage {','function BeforeR1Package {')))
function OriginalPackage {
 $count=BeforeR1Package
 if(!$Fixture){
  Match (Join-Path $game 'archive/pc/mod/TowerContinued_Races_R1.archive') '76028F158A7E4CB91C041B6DFBF09CEFB91E8F86BE0D9835ADC95D18CF5F9885'
  Match (Join-Path $game 'archive/pc/mod/TowerContinued_Races_R1.archive.xl') '145837A7D00ECA9E2A3D88F3C0EB6B6A92144E5571287A552AF199137CC4C752'
  $count+=2
 }
 return $count
}
function Scope($files){
 if(@($files).Count -ne 3 -or @($files|Select-Object -ExpandProperty relative -Unique).Count -ne 3){throw 'Exactly three unique additions required'}
 for($i=0;$i -lt 3;$i++){
  if($files[$i].relative -cne $relatives[$i] -or $files[$i].sha256 -cnotmatch '^[A-F0-9]{64}$'){throw 'Addition scope mismatch'}
 }
}
function TrueFlag($value){return ($value -is [bool] -and $value)}
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
 $txnPath=Join-Path $recovery 'transaction.json';NoLink (Join-Path $recovery 'transaction.sha256')
 $digest=Get-Content -LiteralPath (Join-Path $recovery 'transaction.sha256') -Raw
 Match $txnPath $digest;$txn=ReadJson $txnPath
 if($txn.status -cne 'S2_ADD_ONLY' -or $txn.game_root -cne $game -or $txn.save_root -cne $saves){throw 'Recovery identity mismatch'}
 Scope $txn.files
 foreach($f in $txn.files){
  $name=[IO.Path]::GetFileName($f.relative);Match (Join-Path $recovery $name) $f.sha256
  $target=Bound (Join-Path $game $f.relative) $game
  $removed=Join-Path $recovery ('removed_'+$name);NoLink $removed
  if(Test-Path -LiteralPath $removed){throw 'Recovery destination exists'}
  if(Test-Path -LiteralPath $target){Match $target $f.sha256}
 }
 $protected=Snapshot
 if($Mode -eq 'ValidateRollback'){@{status='VALIDATED_S2_ROLLBACK';original_package_verified=$original;protected_files=$protected.Count}|ConvertTo-Json;return}
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
 WriteJson (Join-Path $recovery 'rollback_receipt.json') @{status='ROLLED_BACK_S2';utc=[DateTime]::UtcNow.ToString('o');moved_recoverably=$moved;protected_files=$count;original_package_verified=(OriginalPackage);save_changes=$false;empty_owned_script_directory_retained=$true}
 Write-Output "ROLLED_BACK: $recovery";return
}
if(!$Build){throw 'Build directory required'}
$buildRoot=Bound $Build $buildBound
$manifestPath=Join-Path $buildRoot 'build.json';$manifest=ReadJson $manifestPath
if($manifest.status -cne 'BUILT_S2_LIVE_PENDING' -or @($manifest.resources.PSObject.Properties).Count -ne 2 -or @($manifest.boots).Count -ne 2 -or !(TrueFlag $manifest.packed_readback) -or !(TrueFlag $manifest.native_scenes_unchanged) -or @($manifest.official_overrides).Count -ne 0 -or $manifest.runtime_scripts_added -ne 1 -or $manifest.official_resource_count -lt 1){throw 'Manifest scope mismatch'}
Scope $manifest.files
$scriptParent=Bound (Join-Path $game 'r6/scripts/TowerContinued_SideJobs_S2') $game
foreach($f in $manifest.files){
 Match (Join-Path $buildRoot ([IO.Path]::GetFileName($f.relative))) $f.sha256
 $target=Bound (Join-Path $game $f.relative) $game
 if(Test-Path -LiteralPath $target){throw 'S2 already present; refusing overwrite'}
 $parent=Split-Path -Parent $target
 if(!(Test-Path -LiteralPath $parent -PathType Container)){
  if($parent -cne $scriptParent -or (Test-Path -LiteralPath $parent) -or !(Test-Path -LiteralPath (Split-Path -Parent $parent) -PathType Container)){throw 'Existing mod/scripts roots required; only exact S2 leaf may be created'}
 }
}
$tests=ReadJson (Join-Path $buildRoot 'tests.json')
if($tests.status -cne 'PASS_NOT_LIVE' -or $tests.build_sha256 -cne (Hash $manifestPath)){throw 'Matching tests required'}
Match (Join-Path $PSScriptRoot 'test.py') $tests.tester_sha256
$resources=ReadJson (Join-Path $buildRoot 'resource_check.json')
if($resources.status -cne 'PASS_NOT_LIVE' -or $resources.build_sha256 -cne (Hash $manifestPath) -or @($resources.overrides).Count -ne 0 -or @($resources.official).Count -ne $manifest.official_resource_count -or @($resources.official|Select-Object -ExpandProperty depot -Unique).Count -ne $manifest.official_resource_count -or !(TrueFlag $resources.modlist_absent) -or @($resources.official_overrides).Count){throw 'Matching resource audit required'}
Match (Join-Path $PSScriptRoot 'resource_check.ps1') $resources.checker_sha256
$compiled=ReadJson (Join-Path $buildRoot 'compiler.json')
if($compiled.status -cne 'PASS_NOT_LIVE' -or $compiled.build_sha256 -cne (Hash $manifestPath) -or $compiled.script_sha256 -cne $manifest.files[2].sha256){throw 'Matching compiler proof required'}
foreach($flag in @('full_scc','combined_cli','body_readback','equipmentex','live_files_unchanged')){if(!(TrueFlag $compiled.$flag)){throw "Compiler proof missing: $flag"}}
Match (Join-Path $PSScriptRoot 'compile.py') $compiled.compiler_sha256
if(@($manifest.source_pins.PSObject.Properties).Count -lt 1){throw 'Bound source pins required'}
foreach($p in $manifest.source_pins.PSObject.Properties){Match (Bound (Join-Path $workspace $p.Name) $workspace) $p.Value}
if(!$Fixture){
 if(Test-Path -LiteralPath (Join-Path $game 'archive/pc/mod/modlist.txt')){throw 'Explicit load order appeared; priority not verified'}
 $proofs=@(Get-ChildItem -LiteralPath $fixtureRoot -Filter 'results.json' -File -Recurse|ForEach-Object {ReadJson $_.FullName}|Where-Object {
  $_.status -ceq 'PASS_WORKSPACE_FIXTURES_NOT_LIVE' -and $_.build_sha256 -ceq (Hash $manifestPath) -and $_.installer_sha256 -ceq (Hash $PSCommandPath) -and $_.tester_sha256 -ceq (Hash (Join-Path $PSScriptRoot 'test_deploy.py')) -and $_.cases -ge 45 -and $_.checks -ge 60
 })
 if($proofs.Count -lt 1){throw 'Matching deployment fixture proof required'}
 foreach($map in @($compiled.dependencies,$compiled.protected)){foreach($p in $map.PSObject.Properties){Match $p.Name $p.Value}}
 $actual=@(Get-ChildItem (Join-Path $game 'archive/pc/mod') -File -Filter '*.archive')
 if($actual.Count -ne @($resources.installed_archives).Count){throw 'Installed archive set changed'}
 foreach($a in $resources.installed_archives){Match (Bound (Join-Path $game ('archive/pc/mod/'+$a.name)) $game) $a.sha256}
 foreach($p in $manifest.installed_injections|Sort-Object source -Unique){Match (Bound (Join-Path $game ('archive/pc/mod/'+$p.source)) $game) $p.source_sha256}
}
$protected=Snapshot
if($Mode -eq 'Validate'){@{status='VALIDATED_S2_ADD_ONLY';additions=3;original_package_verified=$original;protected_files=$protected.Count;build_sha256=Hash $manifestPath}|ConvertTo-Json;return}
if(!$recovery -or (Test-Path -LiteralPath $recovery)){throw 'New recovery directory required'}
Closed
New-Item -ItemType Directory -Path $recovery -ErrorAction Stop | Out-Null
foreach($f in $manifest.files){$name=[IO.Path]::GetFileName($f.relative);CopyExact (Join-Path $buildRoot $name) (Join-Path $recovery $name) $f.sha256}
WriteJson (Join-Path $recovery 'transaction.json') @{status='S2_ADD_ONLY';game_root=$game;save_root=$saves;files=$manifest.files;build=$buildRoot;build_sha256=Hash $manifestPath;utc=[DateTime]::UtcNow.ToString('o');protected=$protected;installer_sha256=Hash $PSCommandPath;script_parent=$scriptParent}
[IO.File]::WriteAllText((Join-Path $recovery 'transaction.sha256'),(Hash (Join-Path $recovery 'transaction.json')),[Text.UTF8Encoding]::new($false))
try{
 $copied=0;$createdScriptDirectory=$false
 foreach($f in $manifest.files){
  Closed;$target=Bound (Join-Path $game $f.relative) $game
  if($f.relative -ceq $relatives[2] -and !(Test-Path -LiteralPath $scriptParent)){
   [void](Bound $scriptParent $game);New-Item -ItemType Directory -Path $scriptParent -ErrorAction Stop | Out-Null;$createdScriptDirectory=$true
  }
  CopyExact (Join-Path $recovery ([IO.Path]::GetFileName($f.relative))) $target $f.sha256
  $copied++;if($FailAfterFirst -and $copied -eq 1){throw 'Injected fixture failure after first addition'}
 }
 $count=Same $protected
 WriteJson (Join-Path $recovery 'install_receipt.json') @{status='INSTALLED_S2_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');additions=3;replacements=0;installed_files=$manifest.files;original_package_verified=(OriginalPackage);protected_files=$count;protected_save_files=@($protected.Keys|Where-Object{$_ -like 'save/*'}).Count;protected_cache_files=@($protected.Keys|Where-Object{$_ -like 'game/r6/cache/*'}).Count;settings_changed=$false;build_sha256=Hash $manifestPath;recovery=$recovery;created_script_directory=$createdScriptDirectory}
 Write-Output "INSTALLED: $recovery"
}catch{
 WriteJson (Join-Path $recovery 'failure.json') @{status='INSTALL_INTERRUPTED';message=$_.Exception.Message;instruction='Do not launch. Use ValidateRollback then Rollback with this exact recovery directory.'}
 throw
}
