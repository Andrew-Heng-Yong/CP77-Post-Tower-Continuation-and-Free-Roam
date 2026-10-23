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
$relatives=@('archive/pc/mod/TowerContinued_SideJobs_S28.archive','archive/pc/mod/TowerContinued_SideJobs_S28.archive.xl','r6/scripts/TowerContinued_SideJobs_S28/SideJobsS28.reds')
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
  'archive/pc/mod/TowerContinued_Gigs_U10.archive'='2DD9DEC6814817086D88CD4DD9B6979E49FDEC02D15864779EE36A8CE276C64B'
  'archive/pc/mod/TowerContinued_Gigs_U10.archive.xl'='E771B6A2B6F07E196DE0AC2FD9F16B3C85D8FEA4B33870D3CD9D79D4161A832B'
  'r6/scripts/TowerContinued_Gigs_U10/GigsU10.reds'='9E14ED7A8ED92EA8F35470D2A6010F78C189139562A83DA1C31B4EB2470019A7'
  'archive/pc/mod/TowerContinued_PreAlpha.archive'='6B9AAE7DAE4AD9613A7F8ABA7FB3CB2B05D7CD85DAAA3A5FE82B198324316DE9'
  'r6/scripts/PTFR_PreAlpha/PTFR_GigPhoneU9/GigPhoneU9.reds'='0B8B576F8F033808288F1C5176C3622BF55E850575660FC6CBB15C485DB5DCA5'
  'archive/pc/mod/0000000_TowerContinued_SideJobs_S27.archive'='FC33D4CBFDA8AC881AEA80D0D1CBAE0E0398F42E93BC9D00F50CD73BBCA16C6F'
  'archive/pc/mod/0000000_TowerContinued_SideJobs_S27.archive.xl'='634191653DDCD5955A55311922065843FAD23780B62BCF2FD0A7A12E1F50F433'
  'r6/scripts/TowerContinued_SideJobs_S27/SideJobsS27.reds'='9CFF174B1EF7D0FBE0660E792DE89BDF56730123398969FCEAB0A80AB2856ED1'
  'archive/pc/mod/0000_TowerContinued_SideJobs_S23.archive'='A24A4BEF165833F38E04F7BF20698E45F9E516C150358518C981C768DFDBD1CB'
  'archive/pc/mod/0000_TowerContinued_SideJobs_S23.archive.xl'='C4C231F332266181E1D8DD1455CD6DD751E5924AFBF792119414D331D915DFB5'
  'r6/scripts/TowerContinued_SideJobs_S23/SideJobsS23.reds'='8E82481B770C3FE11AE4D15CEA0B422F05DDDE4441B9134384990E07183CD6F0'
  'archive/pc/mod/000_TowerContinued_SideJobs_S22.archive'='D60EBBC7346F4FFFF0C08F301FEA360D59CAB503D84CFF6039E40ACADEB40E78'
  'archive/pc/mod/000_TowerContinued_SideJobs_S22.archive.xl'='D88437FB829F76E774535D2B982D69205931A3A94BF59E2D890165205087A223'
  'r6/scripts/TowerContinued_SideJobs_S22/SideJobsS22.reds'='44CA2D37FAC081F60A1A88516ED0B4365645EEC4C09FBE5D4639AC2D7477EC39'
  'r6/scripts/TowerContinued_SideJobs_S2/SideJobsS2.reds'='58F134FFE6CCD8DF0AF30FCCABBFD161BBBCC8AEF75E25C16D18303992134295'
  'archive/pc/mod/000000_TowerContinued_SideJobs_S25.archive'='DDCDA37330E056342D6F0C4C4245596323809CAD4DA10ED73258113875149C33'
  'archive/pc/mod/000000_TowerContinued_SideJobs_S25.archive.xl'='1720E7A2C0DEC5894370EE346BFEB9BE71F9AB10F5597AEB129EA9776075D025'
  'r6/scripts/TowerContinued_SideJobs_S25/SideJobsS25.reds'='E72BC8E83BE13D6D2601343E9108EEF8BCF442B5A69F04D4A02C98A90CB488FA'
  'archive/pc/mod/00000_TowerContinued_SideJobs_S24.archive'='15A7CDE8A4E7780E41B4AF8A1979F1154EECB95B9CCF380A0777342DBD750417'
  'archive/pc/mod/00000_TowerContinued_SideJobs_S24.archive.xl'='31140F99FADBCCA43FAB1429A2545BDF9CCD8625D296B7516D3CAEF0B2CD1B3E'
  'r6/scripts/TowerContinued_SideJobs_S24/SideJobsS24.reds'='BB7371BC8C7266BD51D65E87EFBCAC07624555E8C3A9878F56E6FC82120D2CDC'
  'archive/pc/mod/TowerContinued_Dogtown_DT1.archive'='B04F110320C566652D9DE5B3E4ED85279F7AF8576496F48897887DF6800D07EF'
  'archive/pc/mod/TowerContinued_Dogtown_DT1.archive.xl'='D2FA13E6142D3E0B0A2135F636E61F6CCF840EF64A55433182831DC34C7A923C'
  'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_SideJobsCaptureS26/init.lua'='74D08E42E1D8F8B1932A2E71321D00E8C1AC13101C7BEF2BA43AB3F5F6C23BBF'
  'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_SideJobsCaptureS26/data.json'='FCABF6AC14AB00D08739C8411A0A32E8D523DB8A71EC4EC3AB87C3DE5857E1A3'
 }
 foreach($p in $pins.Keys){Match (Bound (Join-Path $game $p) $game) $pins[$p]};return $pins.Count
}
function TrueFlag($v){return ($v -is [bool] -and $v)}
function PositiveCount($v){return (($v -is [int] -or $v -is [long]) -and $v -gt 0)}
function Scope($files){
 if(@($files).Count -ne 3 -or @($files|Select-Object -ExpandProperty relative -Unique).Count -ne 3){throw 'Exactly three additions required'}
 for($i=0;$i -lt 3;$i++){$f=$files[$i]
  if($f.relative -cne $relatives[$i] -or $f.sha256 -isnot [string] -or $f.sha256 -cnotmatch '^[A-F0-9]{64}$'){throw 'File scope mismatch'}
  if('old_sha256' -in $f.PSObject.Properties.Name -or 'before_sha256' -in $f.PSObject.Properties.Name -or ('action' -in $f.PSObject.Properties.Name -and $f.action -cne 'add')){throw 'No replacement metadata allowed'}
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
$scriptParent=Bound (Join-Path $game 'r6/scripts/TowerContinued_SideJobs_S28') $game
$recovery=if($RecoveryRoot){Bound $RecoveryRoot $recoveryBound}else{''}
Closed;$verified=WorkingPackage
if($Mode -in @('ValidateRollback','Rollback')){
 if(!$recovery){throw 'Exact recovery directory required'}
 if(Test-Path -LiteralPath (Join-Path $recovery 'rollback_receipt.json')){throw 'Already rolled back'}
 $txnPath=Join-Path $recovery 'transaction.json';NoLink (Join-Path $recovery 'transaction.sha256')
 Match $txnPath (Get-Content -LiteralPath (Join-Path $recovery 'transaction.sha256') -Raw);$txn=ReadJson $txnPath
 if($txn.status -cne 'S28_ADD_ONLY' -or $txn.game_root -cne $game -or $txn.save_root -cne $saves -or $txn.installer_sha256 -cne (Hash $PSCommandPath)){throw 'Recovery identity mismatch'}
 Scope $txn.files
 foreach($f in $txn.files){
  $name=[IO.Path]::GetFileName($f.relative);Match (Join-Path $recovery $name) $f.sha256
  $target=Bound (Join-Path $game $f.relative) $game;if(Test-Path -LiteralPath $target){Match $target $f.sha256}
  $removed=Bound (Join-Path $recovery ('removed_'+$name)) $recovery
  if(Test-Path -LiteralPath $removed){throw 'Interrupted/previous rollback requires inspection'}
 }
 $protected=Snapshot
 if($Mode -eq 'ValidateRollback'){@{status='VALIDATED_S28_ROLLBACK';protected_files=$protected.Count;working_files_verified=$verified}|ConvertTo-Json;return}
 $moved=0
 foreach($f in $txn.files){
  $target=Bound (Join-Path $game $f.relative) $game
  if(Test-Path -LiteralPath $target){Closed;Match $target $f.sha256;$removed=Bound (Join-Path $recovery ('removed_'+[IO.Path]::GetFileName($f.relative))) $recovery;[IO.File]::Move($target,$removed,$false);Match $removed $f.sha256;$moved++}
 }
 $count=Same $protected
 WriteJson (Join-Path $recovery 'rollback_receipt.json') @{status='ROLLED_BACK_S28';utc=[DateTime]::UtcNow.ToString('o');moved_recoverably=$moved;protected_files=$count;working_files_verified=(WorkingPackage);save_changes=$false;settings_changed=$false;empty_script_directory_retained=$true}
 Write-Output "ROLLED_BACK: $recovery";return
}
if(!$Build){throw 'Build required'}
$buildRoot=Bound $Build $buildBound;$manifestPath=Join-Path $buildRoot 'build.json';$m=ReadJson $manifestPath
if(!$Fixture -and 'synthetic_fixture' -in $m.PSObject.Properties.Name){throw 'Synthetic inputs cannot validate or install a live build'}
if($m.status -cne 'BUILT_S28_LIVE_PENDING' -or !(TrueFlag $m.packed_readback) -or @($m.resources.PSObject.Properties).Count -lt 1 -or @($m.boots).Count -lt 1 -or @($m.official_overrides).Count -ne 0){throw 'Build scope mismatch'}
if(@($m.mod_overrides).Count -ne 0){throw 'No existing mod resource override allowed'}
foreach($p in $m.resources.PSObject.Properties){if($p.Name -cnotmatch '^towercontinued\\sidejobs_s28\\[a-zA-Z0-9_\\.]+$' -or $p.Name -match '\.\.' -or $p.Value -cnotmatch '^[A-F0-9]{64}$'){throw 'Unsafe/non-S28 resource'}}
if('override_donors' -in $m.PSObject.Properties.Name -and @($m.override_donors.PSObject.Properties).Count -ne 0){throw 'No override donor allowed'}
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
Match (Join-Path $PSScriptRoot 'test_02.py') $tests.tester_sha256
$compiled=ReadJson (Join-Path $buildRoot 'compile_result.json')
if($compiled.status -cne 'PASS_NOT_LIVE' -or $compiled.build_sha256 -cne (Hash $manifestPath)){throw 'Matching compiler proof required'}
foreach($flag in @('full_scc','combined_cli','body_readback','equipmentex','live_files_unchanged','script_environment_complete')){if(!(TrueFlag $compiled.$flag)){throw "Compiler proof missing: $flag"}}
Match (Join-Path $PSScriptRoot 'compile_02.py') $compiled.compiler_sha256
$nativePrereqs=@('PTFR.SideJobsS28.PTFRS28HighwaymanVehicleUnownedPrereq','PTFR.SideJobsS28.PTFRS28HoonVehicleUnownedPrereq','PTFR.SideJobsS28.PTFRS28HoonWorldKeyAbsentPrereq')
if(!(PositiveCount $compiled.body_checks.arrays) -or $compiled.body_checks.arrays -ne 36 -or !(PositiveCount $compiled.body_checks.adapters) -or $compiled.body_checks.adapters -ne 4){throw 'S28 compiled adapter scope mismatch'}
if(!(TrueFlag $compiled.body_checks.complete_native_predicate_body_readback) -or (@($compiled.body_checks.native_prereq_classes)-join '|') -cne ($nativePrereqs-join '|')){throw 'Native prerequisite body readback required'}

if($compiled.script_sha256 -cne $m.files[2].sha256){throw 'Compiler script binding mismatch'}
PinMap $compiled.dependencies 'compiler dependencies';PinMap $compiled.protected 'compiler protected'
# A matching digest for old files is insufficient: newly added uncompiled
# scripts or changed include roots must invalidate the compiler proof as well.
$config=if($Fixture){Join-Path $buildRoot 'compile_paths.txt'}else{Join-Path $workspace 'research/restriction_profiles/implementation_r1/compile_paths.txt'}
$cli=if($Fixture){Join-Path $buildRoot 'toolchain/redscript-cli.exe'}else{Join-Path $workspace 'research/framework_pr63_01/redscript-cli.exe'}
$scc=if($Fixture){Join-Path $buildRoot 'toolchain/scc.exe'}else{Join-Path $game 'engine/tools/scc.exe'}
$sccLibrary=if($Fixture){Join-Path $buildRoot 'toolchain/scc_lib.dll'}else{Join-Path $game 'engine/tools/scc_lib.dll'}
$toolPaths=@($config,$cli,$scc,$sccLibrary)|ForEach-Object {[IO.Path]::GetFullPath($_).ToUpperInvariant()}|Sort-Object
PinMap $compiled.compiler_inputs 'compiler binaries and include configuration'
if((@($compiled.compiler_inputs.PSObject.Properties.Name|ForEach-Object {[IO.Path]::GetFullPath($_).ToUpperInvariant()}|Sort-Object)-join '|') -cne ($toolPaths-join '|')){throw 'Compiler input identity mismatch'}
$roots=@((Join-Path $game 'r6/scripts'))+@(Get-Content -LiteralPath $config|Select-Object -Skip 2|Where-Object {$_.Trim()}|ForEach-Object {$_.Trim()})
$roots=@($roots|ForEach-Object {Full $_}|Sort-Object -Unique)
if((@($roots|ForEach-Object {$_.ToUpperInvariant()}|Sort-Object)-join '|') -cne (@($compiled.script_roots|ForEach-Object {(Full $_).ToUpperInvariant()}|Sort-Object)-join '|')){throw 'Compiler include roots changed'}
$liveScripts=@(foreach($root in $roots){NoLink $root;if(!(Test-Path -LiteralPath $root -PathType Container)){throw 'Compiler source root missing'};Get-ChildItem -LiteralPath $root -Filter '*.reds' -File -Recurse|ForEach-Object {NoLink $_.FullName;$_.FullName.ToUpperInvariant()}})|Sort-Object -Unique
$compiledScripts=@($compiled.dependencies.PSObject.Properties.Name|ForEach-Object {[IO.Path]::GetFullPath($_).ToUpperInvariant()}|Sort-Object -Unique)
if(($liveScripts-join '|') -cne ($compiledScripts-join '|')){throw 'Installed script identity set changed since compilation'}
$audit=ReadJson (Join-Path $buildRoot 'resource_check.json')
if($audit.status -cne 'PASS_RESOURCE_AUDIT' -or $audit.build_sha256 -cne (Hash $manifestPath) -or !(PositiveCount $audit.official_comparisons) -or @($audit.official_overrides).Count -ne 0 -or !(TrueFlag $audit.modlist_absent) -or !(TrueFlag $audit.new_overrides_first)){throw 'Matching resource audit required'}
Match (Join-Path $PSScriptRoot 'resource_check_02.ps1') $audit.checker_sha256
$metadataRel='research/sidejobs_s28/journal_metadata_02.json'
if($m.journal_metadata_proof -cne $metadataRel -or $audit.metadata_variant_proof -cne $metadataRel){throw 'Journal metadata proof identity missing or changed'}
$metadataPath=Bound (Join-Path $workspace $metadataRel) $workspace
Match $metadataPath $audit.metadata_variant_proof_sha256
if($m.source_pins.($metadataRel) -cne $audit.metadata_variant_proof_sha256){throw 'Journal metadata proof not build-bound'}
$metadata=ReadJson $metadataPath
if($metadata.status -cne 'PASS_USED_JOURNAL_METADATA_ALL_VARIANTS' -or $metadata.metadata_only_depot -cne 'base\journal\cooked_journal.journal' -or @($metadata.variants).Count -ne 2){throw 'Invalid narrow journal variant proof'}
Match (Join-Path $PSScriptRoot 'verify_journal_metadata_02.py') $metadata.verifier_sha256
if(@($audit.metadata_variants.PSObject.Properties).Count -ne 2 -or $audit.exact_byte_resources -ne ($audit.official_comparisons-1) -or $audit.official_comparisons -ne @($audit.official_resources.PSObject.Properties).Count){throw 'Incomplete exact-byte/metadata resource audit'}
foreach($v in $metadata.variants){if($audit.metadata_variants.($v.archive) -cne $v.sha256){throw 'Audited journal variant mismatch'}}
if(@($audit.collisions).Count -ne 0){throw 'Existing resource collision forbidden'}
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
 $proofs=@(Get-ChildItem -LiteralPath $fixtureRoot -Filter results.json -Recurse -File|ForEach-Object {ReadJson $_.FullName}|Where-Object {$_.status -ceq 'PASS_WORKSPACE_FIXTURES_NOT_LIVE' -and $_.build_sha256 -ceq (Hash $manifestPath) -and $_.installer_sha256 -ceq (Hash $PSCommandPath) -and $_.tester_sha256 -ceq (Hash (Join-Path $PSScriptRoot 'test_deploy_02.py')) -and $_.cases -ge 30 -and $_.checks -ge 40})
 if($proofs.Count -lt 1){throw 'Matching deployment fixtures required'}
}
$protected=Snapshot
if($Mode -eq 'Validate'){@{status='VALIDATED_S28_ADD_ONLY';additions=3;replacements=0;protected_files=$protected.Count;working_files_verified=$verified;build_sha256=Hash $manifestPath}|ConvertTo-Json;return}
if(!$recovery -or (Test-Path -LiteralPath $recovery)){throw 'New recovery directory required'}
Closed;New-Item -ItemType Directory -Path $recovery -ErrorAction Stop|Out-Null
foreach($f in $m.files){CopyExact (Join-Path $buildRoot ([IO.Path]::GetFileName($f.relative))) (Join-Path $recovery ([IO.Path]::GetFileName($f.relative))) $f.sha256}
WriteJson (Join-Path $recovery 'transaction.json') @{status='S28_ADD_ONLY';game_root=$game;save_root=$saves;files=$m.files;build_sha256=Hash $manifestPath;installer_sha256=Hash $PSCommandPath;protected=$protected;utc=[DateTime]::UtcNow.ToString('o')}
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
 WriteJson (Join-Path $recovery 'install_receipt.json') @{status='INSTALLED_S28_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');additions=3;replacements=0;files=$m.files;protected_files=$same;protected_save_files=@($protected.Keys|Where-Object {$_ -like 'save/*'}).Count;protected_cache_files=@($protected.Keys|Where-Object {$_ -like 'game/r6/cache/*'}).Count;working_files_verified=(WorkingPackage);save_changes=$false;settings_changed=$false;build_sha256=Hash $manifestPath;created_script_directory=$created}
 Write-Output "INSTALLED: $recovery"
}catch{WriteJson (Join-Path $recovery 'failure.json') @{status='S28_INSTALL_FAILED';message=$_.Exception.Message;instruction='Do not launch. ValidateRollback then Rollback with this exact recovery directory.'};throw}
