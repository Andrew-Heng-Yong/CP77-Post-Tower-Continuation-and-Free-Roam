param(
 [ValidateSet('Validate','Install','ValidateRollback','Rollback')][string]$Mode='Validate',
 [string]$Build='', [string]$RecoveryRoot='',
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$SaveRoot='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077',
 [switch]$Fixture,[switch]$FailAfterBackup,[switch]$FailAfterFirst
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')).TrimEnd('\')
$fixtureRoot=Join-Path $PSScriptRoot 'fixtures'
$relatives=@('archive/pc/mod/0000_TowerContinued_SideJobs_S23.archive','archive/pc/mod/0000_TowerContinued_SideJobs_S23.archive.xl','r6/scripts/TowerContinued_SideJobs_S23/SideJobsS23.reds')
$allowedOverrides=@('towercontinued\gig_phone_u9\fixer_cleanup.questphase','towercontinued\b0_wilson_vendor\owner.questphase')
# Definitions only, not an old installer's main or stale OriginalPackage chain.
$lib=Join-Path $workspace 'prealpha/graphics_gd2/tools/deploy.ps1'
if((Get-FileHash -LiteralPath $lib).Hash -cne '1D1D204D792D65FF30757B455E57826787E395A1DF0C1D5352A60D0757EC3307'){throw 'Safety helper changed'}
$text=Get-Content -LiteralPath $lib -Raw;$start=$text.IndexOf('function Full(');$end=$text.IndexOf('$game=Full $GameRoot;')
if($start -lt 0 -or $end -le $start){throw 'Helper boundary changed'}
$defs=$text.Substring($start,$end-$start)
if([regex]::Matches($defs,[regex]::Escape('if($rel -ceq $relative)')).Count -ne 1){throw 'Snapshot boundary changed'}
$defs=$defs.Replace('if($rel -ceq $relative)','if($rel -cin $relatives)')
. ([scriptblock]::Create($defs))
function WorkingPackage {
 if($Fixture){return 0}
 $pins=@{
  'archive/pc/mod/000_TowerContinued_SideJobs_S22.archive'='D60EBBC7346F4FFFF0C08F301FEA360D59CAB503D84CFF6039E40ACADEB40E78'
  'archive/pc/mod/000_TowerContinued_SideJobs_S22.archive.xl'='D88437FB829F76E774535D2B982D69205931A3A94BF59E2D890165205087A223'
  'r6/scripts/TowerContinued_SideJobs_S22/SideJobsS22.reds'='037BB7AE91EA09A5BB7604DC27B0B45343AC16BF6435486855527BC3FE1641D7'
  'r6/scripts/TowerContinued_SideJobs_S2/SideJobsS2.reds'='58F134FFE6CCD8DF0AF30FCCABBFD161BBBCC8AEF75E25C16D18303992134295'
 }
 foreach($p in $pins.Keys){Match (Bound (Join-Path $game $p) $game) $pins[$p]};return $pins.Count
}
function TrueFlag($v){return ($v -is [bool] -and $v)}
function PositiveCount($v){return (($v -is [int] -or $v -is [long]) -and $v -gt 0)}
function Scope($files){
 if(@($files).Count -ne 3 -or @($files|Select-Object -ExpandProperty relative -Unique).Count -ne 3){throw 'Exactly three additions required'}
 for($i=0;$i -lt 3;$i++){$f=$files[$i]
  if($f.relative -cne $relatives[$i] -or $f.sha256 -isnot [string] -or $f.sha256 -cnotmatch '^[A-F0-9]{64}$'){throw 'File scope mismatch'}
  if('old_sha256' -in $f.PSObject.Properties.Name){throw 'No replacement metadata allowed'}
 }
}
function PinMap($map,$kind){
 if($null -eq $map -or @($map.PSObject.Properties).Count -lt 1){throw "Missing $kind pins"}
 foreach($p in $map.PSObject.Properties){if($p.Value -isnot [string]){throw "Bad $kind digest"};Match $p.Name $p.Value}
}
$game=Full $GameRoot;$saves=Full $SaveRoot;NoLink $game;NoLink $saves
if(!(Test-Path -LiteralPath $game -PathType Container) -or !(Test-Path -LiteralPath $saves -PathType Container)){throw 'Existing roots required'}
if($Fixture){[void](Bound $game $fixtureRoot);[void](Bound $saves $fixtureRoot);$buildBound=$fixtureRoot;$recoveryBound=$fixtureRoot}
else{
 if($game -cne 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077' -or $saves -cne 'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077' -or $FailAfterBackup -or $FailAfterFirst){throw 'Unapproved live roots/options'}
 $buildBound=Join-Path $PSScriptRoot 'build';$recoveryBound=Join-Path $workspace 'recovery'
}
$scriptParent=Bound (Join-Path $game 'r6/scripts/TowerContinued_SideJobs_S23') $game
$recovery=if($RecoveryRoot){Bound $RecoveryRoot $recoveryBound}else{''}
Closed;$verified=WorkingPackage
if($Mode -in @('ValidateRollback','Rollback')){
 if(!$recovery){throw 'Exact recovery directory required'}
 if(Test-Path -LiteralPath (Join-Path $recovery 'rollback_receipt.json')){throw 'Already rolled back'}
 $txnPath=Join-Path $recovery 'transaction.json';NoLink (Join-Path $recovery 'transaction.sha256')
 Match $txnPath (Get-Content -LiteralPath (Join-Path $recovery 'transaction.sha256') -Raw);$txn=ReadJson $txnPath
 if($txn.status -cne 'S23_ADD_ONLY' -or $txn.game_root -cne $game -or $txn.save_root -cne $saves -or $txn.installer_sha256 -cne (Hash $PSCommandPath)){throw 'Recovery identity mismatch'}
 Scope $txn.files
 foreach($f in $txn.files){
  $name=[IO.Path]::GetFileName($f.relative);Match (Join-Path $recovery $name) $f.sha256
  $target=Bound (Join-Path $game $f.relative) $game;if(Test-Path -LiteralPath $target){Match $target $f.sha256}
  $removed=Bound (Join-Path $recovery ('removed_'+$name)) $recovery
  if(Test-Path -LiteralPath $removed){throw 'Interrupted/previous rollback requires inspection'}
 }
 $protected=Snapshot
 if($Mode -eq 'ValidateRollback'){@{status='VALIDATED_S23_ROLLBACK';protected_files=$protected.Count;working_files_verified=$verified}|ConvertTo-Json;return}
 $moved=0
 foreach($f in $txn.files){
  $target=Bound (Join-Path $game $f.relative) $game
  if(Test-Path -LiteralPath $target){Closed;Match $target $f.sha256;$removed=Bound (Join-Path $recovery ('removed_'+[IO.Path]::GetFileName($f.relative))) $recovery;[IO.File]::Move($target,$removed,$false);Match $removed $f.sha256;$moved++}
 }
 $count=Same $protected
 WriteJson (Join-Path $recovery 'rollback_receipt.json') @{status='ROLLED_BACK_S23';utc=[DateTime]::UtcNow.ToString('o');moved_recoverably=$moved;protected_files=$count;working_files_verified=(WorkingPackage);save_changes=$false;settings_changed=$false;empty_script_directory_retained=$true}
 Write-Output "ROLLED_BACK: $recovery";return
}
if(!$Build){throw 'Build required'}
$buildRoot=Bound $Build $buildBound;$manifestPath=Join-Path $buildRoot 'build.json';$m=ReadJson $manifestPath
if($m.status -cne 'BUILT_S23_LIVE_PENDING' -or !(TrueFlag $m.packed_readback) -or @($m.resources.PSObject.Properties).Count -lt 1 -or @($m.boots).Count -lt 1 -or @($m.official_overrides).Count -ne 0){throw 'Build scope mismatch'}
if((@($m.mod_overrides|Sort-Object) -join '|') -cne (@($allowedOverrides|Sort-Object) -join '|')){throw 'Only cleanup and Wilson mod-resource overrides allowed'}
foreach($p in $m.resources.PSObject.Properties){if($p.Name -cnotmatch '^towercontinued\\[a-zA-Z0-9_\\.]+$' -or $p.Name -match '\.\.' -or $p.Value -cnotmatch '^[A-F0-9]{64}$'){throw 'Unsafe/non-mod resource'}}
Scope $m.files
foreach($f in $m.files){
 Match (Bound (Join-Path $buildRoot ([IO.Path]::GetFileName($f.relative))) $buildRoot) $f.sha256
 $target=Bound (Join-Path $game $f.relative) $game;if(Test-Path -LiteralPath $target){throw 'Addition exists; refusing overwrite'}
 $parent=Split-Path -Parent $target
 if(!(Test-Path -LiteralPath $parent -PathType Container)){
  if($parent -cne $scriptParent -or (Test-Path -LiteralPath $parent) -or !(Test-Path -LiteralPath (Split-Path -Parent $parent) -PathType Container)){throw 'Only exact new script leaf may be created'}
 }
}
$tests=ReadJson (Join-Path $buildRoot 'tests.json')
if($tests.status -cne 'PASS_NOT_LIVE' -or $tests.build_sha256 -cne (Hash $manifestPath) -or !(PositiveCount $tests.policy_cases) -or !(PositiveCount $tests.native_payload_checks)){throw 'Matching native/policy tests required'}
Match (Join-Path $PSScriptRoot 'test.py') $tests.tester_sha256
$compiled=ReadJson (Join-Path $buildRoot 'compile_result.json')
if($compiled.status -cne 'PASS_NOT_LIVE' -or $compiled.build_sha256 -cne (Hash $manifestPath)){throw 'Matching compiler proof required'}
foreach($flag in @('full_scc','combined_cli','body_readback','equipmentex','live_files_unchanged')){if(!(TrueFlag $compiled.$flag)){throw "Compiler proof missing: $flag"}}
Match (Join-Path $PSScriptRoot 'compile.py') $compiled.compiler_sha256
if($compiled.script_sha256 -cne $m.files[2].sha256){throw 'Compiler script binding mismatch'}
PinMap $compiled.dependencies 'compiler dependencies';PinMap $compiled.protected 'compiler protected'
$audit=ReadJson (Join-Path $buildRoot 'resource_check.json')
if($audit.status -cne 'PASS_RESOURCE_AUDIT' -or $audit.build_sha256 -cne (Hash $manifestPath) -or !(PositiveCount $audit.official_comparisons) -or @($audit.official_overrides).Count -ne 0 -or !(TrueFlag $audit.modlist_absent) -or !(TrueFlag $audit.new_overrides_first)){throw 'Matching resource audit required'}
Match (Join-Path $PSScriptRoot 'resource_check.ps1') $audit.checker_sha256
$seen=@{};foreach($c in $audit.collisions){
 if($c.depot -cnotin $allowedOverrides){throw 'Unexpected resource collision'}
 $allowedArchives=if($c.depot -ceq $allowedOverrides[0]){@('000_TowerContinued_SideJobs_S22.archive','00_TowerContinued_Courier_C1.archive','0_TowerContinued_NCPD_N1.archive','TowerContinued_PreAlpha.archive')}else{@('TowerContinued_PreAlpha.archive')}
 if($c.archive -cnotin $allowedArchives -or $c.resource_sha256 -cnotmatch '^[A-F0-9]{64}$'){throw 'Unexpected collision donor'}
 $key=$c.depot+'|'+$c.archive;if($seen.ContainsKey($key)){throw 'Duplicate collision record'};$seen[$key]=$true
}
foreach($depot in $allowedOverrides){if(@($audit.collisions|Where-Object {$_.depot -ceq $depot}).Count -lt 1){throw 'Required mod-resource donor missing'}}
if(Test-Path -LiteralPath (Join-Path $game 'archive/pc/mod/modlist.txt')){throw 'Explicit load order appeared'}
$archives=@(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/mod') -Filter '*.archive' -File)
if($archives.Count -ne @($audit.archive_pins.PSObject.Properties).Count -or $archives.Count -lt 1){throw 'Installed archive set changed'}
$pinPaths=@()
foreach($p in $audit.archive_pins.PSObject.Properties){$ap=if([IO.Path]::IsPathFullyQualified($p.Name)){$p.Name}else{Join-Path $game ('archive/pc/mod/'+$p.Name)};$ap=Bound $ap (Join-Path $game 'archive/pc/mod');Match $ap $p.Value;$pinPaths+=,$ap.ToUpperInvariant()}
if((@($pinPaths|Sort-Object) -join '|') -cne (@($archives|ForEach-Object {$_.FullName.ToUpperInvariant()}|Sort-Object) -join '|')){throw 'Installed archive identities changed'}
$xls=@(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/mod') -Filter '*.xl' -File)
# Both build-time injection inventory and later resource audit must describe
# precisely the same current XL files, including standalone non-archive XL.
foreach($xlMap in @($m.installed_xl_pins,$audit.xl_pins)){
 if($null -eq $xlMap -or $xls.Count -ne @($xlMap.PSObject.Properties).Count -or $xls.Count -lt 1){throw 'Installed ArchiveXL set changed or missing proof'}
 $xlPaths=@()
 foreach($p in $xlMap.PSObject.Properties){$xp=if([IO.Path]::IsPathFullyQualified($p.Name)){$p.Name}else{Join-Path $game ('archive/pc/mod/'+$p.Name)};$xp=Bound $xp (Join-Path $game 'archive/pc/mod');Match $xp $p.Value;$xlPaths+=,$xp.ToUpperInvariant()}
 if((@($xlPaths|Sort-Object) -join '|') -cne (@($xls|ForEach-Object {$_.FullName.ToUpperInvariant()}|Sort-Object) -join '|')){throw 'Installed ArchiveXL identities changed'}
}
if(@($m.source_pins.PSObject.Properties).Count -lt 1){throw 'Source pins required'}
foreach($p in $m.source_pins.PSObject.Properties){
 if([IO.Path]::IsPathFullyQualified($p.Name) -or $p.Name -match '(^|[/\\])\.\.([/\\]|$)'){throw 'Unsafe source pin'}
 Match (Bound (Join-Path $workspace $p.Name) $workspace) $p.Value
}
if(!$Fixture){
 $proofs=@(Get-ChildItem -LiteralPath $fixtureRoot -Filter results.json -Recurse -File|ForEach-Object {ReadJson $_.FullName}|Where-Object {$_.status -ceq 'PASS_WORKSPACE_FIXTURES_NOT_LIVE' -and $_.build_sha256 -ceq (Hash $manifestPath) -and $_.installer_sha256 -ceq (Hash $PSCommandPath) -and $_.tester_sha256 -ceq (Hash (Join-Path $PSScriptRoot 'test_deploy.py')) -and $_.cases -ge 30 -and $_.checks -ge 40})
 if($proofs.Count -lt 1){throw 'Matching deployment fixtures required'}
}
$protected=Snapshot
if($Mode -eq 'Validate'){@{status='VALIDATED_S23_ADD_ONLY';additions=3;replacements=0;protected_files=$protected.Count;working_files_verified=$verified;build_sha256=Hash $manifestPath}|ConvertTo-Json;return}
if(!$recovery -or (Test-Path -LiteralPath $recovery)){throw 'New recovery directory required'}
Closed;New-Item -ItemType Directory -Path $recovery -ErrorAction Stop|Out-Null
foreach($f in $m.files){CopyExact (Join-Path $buildRoot ([IO.Path]::GetFileName($f.relative))) (Join-Path $recovery ([IO.Path]::GetFileName($f.relative))) $f.sha256}
WriteJson (Join-Path $recovery 'transaction.json') @{status='S23_ADD_ONLY';game_root=$game;save_root=$saves;files=$m.files;build_sha256=Hash $manifestPath;installer_sha256=Hash $PSCommandPath;protected=$protected;utc=[DateTime]::UtcNow.ToString('o')}
[IO.File]::WriteAllText((Join-Path $recovery 'transaction.sha256'),(Hash (Join-Path $recovery 'transaction.json')),[Text.UTF8Encoding]::new($false))
try{
 if($FailAfterBackup){throw 'Injected fixture failure after backup'}
 $count=0;$created=$false
 foreach($f in $m.files){
  Closed;$target=Bound (Join-Path $game $f.relative) $game
  if($f.relative -ceq $relatives[2] -and !(Test-Path -LiteralPath $scriptParent)){[void](Bound $scriptParent $game);New-Item -ItemType Directory -Path $scriptParent -ErrorAction Stop|Out-Null;$created=$true}
  CopyExact (Join-Path $recovery ([IO.Path]::GetFileName($f.relative))) $target $f.sha256;$count++
  if($FailAfterFirst -and $count -eq 1){throw 'Injected fixture failure after first copy'}
 }
 $same=Same $protected
 WriteJson (Join-Path $recovery 'install_receipt.json') @{status='INSTALLED_S23_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');additions=3;replacements=0;files=$m.files;protected_files=$same;protected_save_files=@($protected.Keys|Where-Object {$_ -like 'save/*'}).Count;protected_cache_files=@($protected.Keys|Where-Object {$_ -like 'game/r6/cache/*'}).Count;working_files_verified=(WorkingPackage);save_changes=$false;settings_changed=$false;build_sha256=Hash $manifestPath;created_script_directory=$created}
 Write-Output "INSTALLED: $recovery"
}catch{WriteJson (Join-Path $recovery 'failure.json') @{status='S23_INSTALL_FAILED';message=$_.Exception.Message;instruction='Do not launch. ValidateRollback then Rollback with this exact recovery directory.'};throw}
