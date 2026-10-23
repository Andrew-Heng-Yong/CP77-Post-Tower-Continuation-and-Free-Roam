param(
 [ValidateSet('Validate','Install','ValidateRollback','Rollback')][string]$Mode='Validate',
 [string]$Build='', [string]$RecoveryRoot='',
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$SaveRoot='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077',
 [switch]$Fixture,[switch]$FailAfterBackup,[switch]$FailAfterFirst,[switch]$FailAfterFirstReplace,[switch]$FailAfterSecondReplace
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')).TrimEnd('\')
$fixtureRoot=Join-Path $PSScriptRoot 'fixtures'
$relatives=@('archive/pc/mod/000000_TowerContinued_SideJobs_S25.archive','archive/pc/mod/000000_TowerContinued_SideJobs_S25.archive.xl','r6/scripts/TowerContinued_SideJobs_S25/SideJobsS25.reds','r6/scripts/TowerContinued_SideJobs_S22/SideJobsS22.reds','r6/scripts/TowerContinued_SideJobs_S23/SideJobsS23.reds')
$oldHashes=@('037BB7AE91EA09A5BB7604DC27B0B45343AC16BF6435486855527BC3FE1641D7','4634CF2C37243E59BF7CD3879441BFB47E1B8BCE1195FDC48B37C1DAA6AB8CB9')
$allowedOverrides=@('towercontinued\sidejobs_s22\mq025_progress.questphase','towercontinued\sidejobs_s22\the_gig_reward_resume.questphase','towercontinued\sidejobs_s22\delamain\support.questphase','towercontinued\sidejobs_s22\delamain\owner.questphase','towercontinued\sidejobs_s22\moving_heat_boot.questphase','towercontinued\sidejobs_s23\base_a\mq024_sandra.questphase','towercontinued\sidejobs_s23\base_a\mq007_smartgun.questphase','towercontinued\sidejobs_s23\base_a\mq035_ozob.questphase','towercontinued\sidejobs_s23\base_a\mq012_stud.questphase','towercontinued\sidejobs_s23\base_a\mq002_veterans.questphase','towercontinued\sidejobs_s23\base_a\mq021_guide.questphase','towercontinued\sidejobs_s23\base_a\mq041_corpo.questphase','towercontinued\sidejobs_s23\base_a\mq044_jakes_vehicle.questphase','towercontinued\sidejobs_s23\base_a_v2\mq007_resume_boot.questphase','towercontinued\sidejobs_s23\base_b\mq026.questphase','towercontinued\sidejobs_s23\ep1\mq306_boot.questphase','towercontinued\side_job_pilot_s1\owner.questphase')
$allowedOverrides+=@('towercontinued\b0_story_services\fred.questphase')
$allowedOverrides+=@('towercontinued\b0_story_eight\viktor.scene','towercontinued\b0_wilson_vendor\body.questphase')
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
  'archive/pc/mod/0000_TowerContinued_SideJobs_S23.archive'='A24A4BEF165833F38E04F7BF20698E45F9E516C150358518C981C768DFDBD1CB'
  'archive/pc/mod/0000_TowerContinued_SideJobs_S23.archive.xl'='C4C231F332266181E1D8DD1455CD6DD751E5924AFBF792119414D331D915DFB5'
  'archive/pc/mod/000_TowerContinued_SideJobs_S22.archive'='D60EBBC7346F4FFFF0C08F301FEA360D59CAB503D84CFF6039E40ACADEB40E78'
  'archive/pc/mod/000_TowerContinued_SideJobs_S22.archive.xl'='D88437FB829F76E774535D2B982D69205931A3A94BF59E2D890165205087A223'
  'r6/scripts/TowerContinued_SideJobs_S2/SideJobsS2.reds'='58F134FFE6CCD8DF0AF30FCCABBFD161BBBCC8AEF75E25C16D18303992134295'
  'archive/pc/mod/00000_TowerContinued_SideJobs_S24.archive'='15A7CDE8A4E7780E41B4AF8A1979F1154EECB95B9CCF380A0777342DBD750417'
  'archive/pc/mod/00000_TowerContinued_SideJobs_S24.archive.xl'='31140F99FADBCCA43FAB1429A2545BDF9CCD8625D296B7516D3CAEF0B2CD1B3E'
  'r6/scripts/TowerContinued_SideJobs_S24/SideJobsS24.reds'='BB7371BC8C7266BD51D65E87EFBCAC07624555E8C3A9878F56E6FC82120D2CDC'
 }
 foreach($p in $pins.Keys){Match (Bound (Join-Path $game $p) $game) $pins[$p]};return $pins.Count
}
function TrueFlag($v){return ($v -is [bool] -and $v)}
function PositiveCount($v){return (($v -is [int] -or $v -is [long]) -and $v -gt 0)}
function Scope($files){
 if(@($files).Count -ne 5 -or @($files|Select-Object -ExpandProperty relative -Unique).Count -ne 5){throw 'Exactly three additions and two replacements required'}
 for($i=0;$i -lt 5;$i++){$f=$files[$i]
  if($f.relative -cne $relatives[$i] -or $f.sha256 -isnot [string] -or $f.sha256 -cnotmatch '^[A-F0-9]{64}$'){throw 'File scope mismatch'}
  if($i -lt 3){if($f.action -cne 'add' -or 'before_sha256' -in $f.PSObject.Properties.Name -or 'old_sha256' -in $f.PSObject.Properties.Name){throw 'Addition cannot replace anything'}}
  else{if($f.action -cne 'replace' -or $f.before_sha256 -cne $oldHashes[$i-3] -or $f.sha256 -ceq $oldHashes[$i-3]){throw 'Replacement identity mismatch'}}
 }
}
function ReplaceExact($from,$target,$before,$after,$backupName){
 Closed;Match $from $after;Match $target $before;NoLink $target
 $displaced=Bound (Join-Path $recovery $backupName) $recovery
 if(Test-Path -LiteralPath $displaced){throw 'Displaced backup already exists'}
 [IO.File]::Replace($from,$target,$displaced,$false)
 Match $target $after;Match $displaced $before
}
function PinMap($map,$kind){
 if($null -eq $map -or @($map.PSObject.Properties).Count -lt 1){throw "Missing $kind pins"}
 foreach($p in $map.PSObject.Properties){if($p.Value -isnot [string]){throw "Bad $kind digest"};Match $p.Name $p.Value}
}
$game=Full $GameRoot;$saves=Full $SaveRoot;NoLink $game;NoLink $saves
if(!(Test-Path -LiteralPath $game -PathType Container) -or !(Test-Path -LiteralPath $saves -PathType Container)){throw 'Existing roots required'}
if($Fixture){[void](Bound $game $fixtureRoot);[void](Bound $saves $fixtureRoot);$buildBound=$fixtureRoot;$recoveryBound=$fixtureRoot}
else{
 if($game -cne 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077' -or $saves -cne 'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077' -or $FailAfterBackup -or $FailAfterFirst -or $FailAfterFirstReplace -or $FailAfterSecondReplace){throw 'Unapproved live roots/options'}
 $buildBound=Join-Path $PSScriptRoot 'build';$recoveryBound=Join-Path $workspace 'recovery'
}
$scriptParent=Bound (Join-Path $game 'r6/scripts/TowerContinued_SideJobs_S25') $game
$recovery=if($RecoveryRoot){Bound $RecoveryRoot $recoveryBound}else{''}
Closed;$verified=WorkingPackage
if($Mode -in @('ValidateRollback','Rollback')){
 if(!$recovery){throw 'Exact recovery directory required'}
 if(Test-Path -LiteralPath (Join-Path $recovery 'rollback_receipt.json')){throw 'Already rolled back'}
 $txnPath=Join-Path $recovery 'transaction.json';NoLink (Join-Path $recovery 'transaction.sha256')
 Match $txnPath (Get-Content -LiteralPath (Join-Path $recovery 'transaction.sha256') -Raw);$txn=ReadJson $txnPath
 if($txn.status -cne 'S25_THREE_ADD_TWO_REPLACE' -or $txn.game_root -cne $game -or $txn.save_root -cne $saves -or $txn.installer_sha256 -cne (Hash $PSCommandPath)){throw 'Recovery identity mismatch'}
 Scope $txn.files
 foreach($f in $txn.files){
  $name=[IO.Path]::GetFileName($f.relative);Match (Join-Path $recovery $name) $f.sha256
  $target=Bound (Join-Path $game $f.relative) $game
  if($f.action -ceq 'replace'){
   Match (Join-Path $recovery ('before_'+$name)) $f.before_sha256
   $actual=Hash $target;if($actual -cne $f.before_sha256 -and $actual -cne $f.sha256){throw 'Replacement drift; refusing to overwrite user changes'}
   foreach($prefix in @('rollback_candidate_','rollback_displaced_')){$p=Bound (Join-Path $recovery ($prefix+$name)) $recovery;if(Test-Path -LiteralPath $p){throw 'Interrupted rollback requires inspection'}}
  }elseif(Test-Path -LiteralPath $target){Match $target $f.sha256}
  $removed=Bound (Join-Path $recovery ('removed_'+$name)) $recovery
  if(Test-Path -LiteralPath $removed){throw 'Interrupted/previous rollback requires inspection'}
 }
 $protected=Snapshot
 if($Mode -eq 'ValidateRollback'){@{status='VALIDATED_S25_ROLLBACK';protected_files=$protected.Count;working_files_verified=$verified}|ConvertTo-Json;return}
 $moved=0;$restored=0
 foreach($f in $txn.files[3..4]){
  $target=Bound (Join-Path $game $f.relative) $game;$name=[IO.Path]::GetFileName($f.relative)
  if((Hash $target) -ceq $f.sha256){
   $candidate=Join-Path $recovery ('rollback_candidate_'+$name);CopyExact (Join-Path $recovery ('before_'+$name)) $candidate $f.before_sha256
   ReplaceExact $candidate $target $f.sha256 $f.before_sha256 ('rollback_displaced_'+$name);$restored++
  }
 }
 foreach($f in $txn.files[0..2]){
  $target=Bound (Join-Path $game $f.relative) $game
  if(Test-Path -LiteralPath $target){Closed;Match $target $f.sha256;$removed=Bound (Join-Path $recovery ('removed_'+[IO.Path]::GetFileName($f.relative))) $recovery;[IO.File]::Move($target,$removed,$false);Match $removed $f.sha256;$moved++}
 }
 $count=Same $protected
 foreach($f in $txn.files[3..4]){Match (Join-Path $game $f.relative) $f.before_sha256}
 WriteJson (Join-Path $recovery 'rollback_receipt.json') @{status='ROLLED_BACK_S25';utc=[DateTime]::UtcNow.ToString('o');restored_original=$restored;moved_recoverably=$moved;protected_files=$count;working_files_verified=(WorkingPackage);save_changes=$false;settings_changed=$false;empty_script_directory_retained=$true}
 Write-Output "ROLLED_BACK: $recovery";return
}
if(!$Build){throw 'Build required'}
$buildRoot=Bound $Build $buildBound;$manifestPath=Join-Path $buildRoot 'build.json';$m=ReadJson $manifestPath
if($m.status -cne 'BUILT_S25_LIVE_PENDING' -or !(TrueFlag $m.packed_readback) -or @($m.resources.PSObject.Properties).Count -lt 1 -or @($m.boots).Count -lt 1 -or @($m.official_overrides).Count -ne 0){throw 'Build scope mismatch'}
if((@($m.mod_overrides|Sort-Object) -join '|') -cne (@($allowedOverrides|Sort-Object) -join '|')){throw 'Only reviewed policy/service MOD overrides allowed'}
foreach($p in $m.resources.PSObject.Properties){if($p.Name -cnotmatch '^towercontinued\\[a-zA-Z0-9_\\.]+$' -or $p.Name -match '\.\.' -or $p.Value -cnotmatch '^[A-F0-9]{64}$'){throw 'Unsafe/non-mod resource'}}
Scope $m.files
foreach($f in $m.files){
 Match (Bound (Join-Path $buildRoot ([IO.Path]::GetFileName($f.relative))) $buildRoot) $f.sha256
 $target=Bound (Join-Path $game $f.relative) $game
 if($f.action -ceq 'replace'){Match $target $f.before_sha256}else{if(Test-Path -LiteralPath $target){throw 'Addition exists; refusing overwrite'}}
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
foreach($flag in @('full_scc','combined_cli','body_readback','equipmentex','live_files_unchanged','script_environment_complete')){if(!(TrueFlag $compiled.$flag)){throw "Compiler proof missing: $flag"}}
Match (Join-Path $PSScriptRoot 'compile.py') $compiled.compiler_sha256
if($compiled.script_sha256 -cne $m.files[2].sha256){throw 'Compiler script binding mismatch'}
if(@($compiled.replacement_scripts.PSObject.Properties).Count -ne 2 -or @($compiled.replacement_body_checks.PSObject.Properties).Count -ne 2){throw 'Complete replacement compiler proof required'}
if(!(TrueFlag $compiled.replacement_body_checks.s22.owned_permit_only) -or !(TrueFlag $compiled.replacement_body_checks.s23.owned_permit_only) -or $compiled.replacement_body_checks.s22.s22_arrays -ne 24 -or $compiled.replacement_body_checks.s23.arrays -ne 168){throw 'Replacement body/data proof incomplete'}
foreach($f in $m.files[3..4]){if($compiled.replacement_scripts.($f.relative) -cne $f.sha256){throw 'Replacement compiler script binding mismatch'}}
PinMap $compiled.dependencies 'compiler dependencies';PinMap $compiled.protected 'compiler protected'
# A matching digest for old files is insufficient: newly added uncompiled
# scripts or changed include roots must invalidate the compiler proof as well.
$config=if($Fixture){Join-Path $buildRoot 'compile_paths.txt'}else{Join-Path $workspace 'research/restriction_profiles/implementation_r1/compile_paths.txt'}
$cli=if($Fixture){Join-Path $buildRoot 'toolchain/redscript-cli.exe'}else{Join-Path $workspace 'research/finalboards_dismissal/tooling/redscript-cli.exe'}
$scc=if($Fixture){Join-Path $buildRoot 'toolchain/scc.exe'}else{Join-Path $game 'engine/tools/scc.exe'}
$toolPaths=@($config,$cli,$scc,(Join-Path $workspace 'prealpha/sidejobs_s23/compile.py'),(Join-Path $workspace 'prealpha/sidejobs_s22b/compile.py'))|ForEach-Object {[IO.Path]::GetFullPath($_).ToUpperInvariant()}|Sort-Object
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
Match (Join-Path $PSScriptRoot 'resource_check.ps1') $audit.checker_sha256
$metadataRel='research/sidejobs_s25/journal_metadata_02.json'
if($m.journal_metadata_proof -cne $metadataRel -or $audit.metadata_variant_proof -cne $metadataRel){throw 'Journal metadata proof identity missing or changed'}
$metadataPath=Bound (Join-Path $workspace $metadataRel) $workspace
Match $metadataPath $audit.metadata_variant_proof_sha256
if($m.source_pins.($metadataRel) -cne $audit.metadata_variant_proof_sha256){throw 'Journal metadata proof not build-bound'}
$metadata=ReadJson $metadataPath
if($metadata.status -cne 'PASS_USED_JOURNAL_METADATA_ALL_VARIANTS' -or $metadata.metadata_only_depot -cne 'base\journal\cooked_journal.journal' -or @($metadata.variants).Count -ne 2){throw 'Invalid narrow journal variant proof'}
Match (Join-Path $PSScriptRoot 'verify_journal_metadata.py') $metadata.verifier_sha256
if(@($audit.metadata_variants.PSObject.Properties).Count -ne 2 -or $audit.exact_byte_resources -ne ($audit.official_comparisons-1) -or $audit.official_comparisons -ne @($audit.official_resources.PSObject.Properties).Count){throw 'Incomplete exact-byte/metadata resource audit'}
foreach($v in $metadata.variants){if($audit.metadata_variants.($v.archive) -cne $v.sha256){throw 'Audited journal variant mismatch'}}
if(@($m.override_donors.PSObject.Properties).Count -ne $allowedOverrides.Count -or @($audit.winning_donors.PSObject.Properties).Count -ne $allowedOverrides.Count){throw 'Complete winning donor proof required'}
foreach($depot in $allowedOverrides){
 $expected=$m.override_donors.$depot;$actual=$audit.winning_donors.$depot
 if($expected.source -isnot [string] -or $expected.source -match '(^|[/\\])\.\.([/\\]|$)' -or [IO.Path]::IsPathFullyQualified($expected.source)){throw 'Unsafe winning donor source'}
 if($expected.sha256 -cnotmatch '^[A-F0-9]{64}$' -or $expected.archive -cnotmatch '^([0]+_)?TowerContinued_[a-zA-Z0-9_]+\.archive$'){throw 'Invalid winning donor identity'}
 Match (Bound (Join-Path $workspace $expected.source) $workspace) $expected.sha256
 if($m.source_pins.($expected.source) -cne $expected.sha256){throw 'Winning donor not build-pinned'}
 foreach($k in @('source','sha256','archive')){if($actual.$k -cne $expected.$k){throw 'Winning donor proof mismatch'}}
}
$seen=@{};foreach($c in $audit.collisions){
 if($c.depot -cnotin $allowedOverrides){throw 'Unexpected resource collision'}
 $allowedArchives=if($c.depot -ceq 'towercontinued\gig_phone_u9\fixer_cleanup.questphase'){@('00000_TowerContinued_SideJobs_S24.archive','0000_TowerContinued_SideJobs_S23.archive','000_TowerContinued_SideJobs_S22.archive','00_TowerContinued_Courier_C1.archive','0_TowerContinued_NCPD_N1.archive','TowerContinued_PreAlpha.archive')}else{@($m.override_donors.($c.depot).archive)}
 if($c.archive -cnotin $allowedArchives -or $c.resource_sha256 -cnotmatch '^[A-F0-9]{64}$'){throw 'Unexpected collision donor'}
 $key=$c.depot+'|'+$c.archive;if($seen.ContainsKey($key)){throw 'Duplicate collision record'};$seen[$key]=$true
}
foreach($depot in $allowedOverrides){
 $donor=$m.override_donors.$depot
 if(@($audit.collisions|Where-Object {$_.depot -ceq $depot -and $_.archive -ceq $donor.archive -and $_.resource_sha256 -ceq $donor.sha256}).Count -ne 1){throw 'Required winning mod-resource donor missing'}
}
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
if($Mode -eq 'Validate'){@{status='VALIDATED_S25_MIXED';additions=3;replacements=2;protected_files=$protected.Count;working_files_verified=$verified;build_sha256=Hash $manifestPath}|ConvertTo-Json;return}
if(!$recovery -or (Test-Path -LiteralPath $recovery)){throw 'New recovery directory required'}
Closed;New-Item -ItemType Directory -Path $recovery -ErrorAction Stop|Out-Null
foreach($f in $m.files){CopyExact (Join-Path $buildRoot ([IO.Path]::GetFileName($f.relative))) (Join-Path $recovery ([IO.Path]::GetFileName($f.relative))) $f.sha256}
foreach($f in $m.files[3..4]){CopyExact (Join-Path $game $f.relative) (Join-Path $recovery ('before_'+[IO.Path]::GetFileName($f.relative))) $f.before_sha256}
WriteJson (Join-Path $recovery 'transaction.json') @{status='S25_THREE_ADD_TWO_REPLACE';game_root=$game;save_root=$saves;files=$m.files;build_sha256=Hash $manifestPath;installer_sha256=Hash $PSCommandPath;protected=$protected;utc=[DateTime]::UtcNow.ToString('o')}
[IO.File]::WriteAllText((Join-Path $recovery 'transaction.sha256'),(Hash (Join-Path $recovery 'transaction.json')),[Text.UTF8Encoding]::new($false))
try{
 if($FailAfterBackup){throw 'Injected fixture failure after backup'}
 $count=0;$created=$false
 foreach($f in $m.files[0..2]){
  Closed;$target=Bound (Join-Path $game $f.relative) $game
  if($f.relative -ceq $relatives[2] -and !(Test-Path -LiteralPath $scriptParent)){[void](Bound $scriptParent $game);New-Item -ItemType Directory -Path $scriptParent -ErrorAction Stop|Out-Null;$created=$true}
  CopyExact (Join-Path $recovery ([IO.Path]::GetFileName($f.relative))) $target $f.sha256;$count++
  if($FailAfterFirst -and $count -eq 1){throw 'Injected fixture failure after first copy'}
 }
 $replaced=0
 foreach($f in $m.files[3..4]){
  $target=Bound (Join-Path $game $f.relative) $game;$name=[IO.Path]::GetFileName($f.relative)
  $candidate=Join-Path $recovery ('install_candidate_'+$name);CopyExact (Join-Path $recovery $name) $candidate $f.sha256
  ReplaceExact $candidate $target $f.before_sha256 $f.sha256 ('displaced_'+$name);$replaced++
  if(($FailAfterFirstReplace -and $replaced -eq 1) -or ($FailAfterSecondReplace -and $replaced -eq 2)){throw 'Injected fixture failure after replacement'}
 }
 foreach($f in $m.files){Match (Join-Path $game $f.relative) $f.sha256}
 $same=Same $protected
 WriteJson (Join-Path $recovery 'install_receipt.json') @{status='INSTALLED_S25_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');additions=3;replacements=2;files=$m.files;protected_files=$same;protected_save_files=@($protected.Keys|Where-Object {$_ -like 'save/*'}).Count;protected_cache_files=@($protected.Keys|Where-Object {$_ -like 'game/r6/cache/*'}).Count;working_files_verified=(WorkingPackage);save_changes=$false;settings_changed=$false;build_sha256=Hash $manifestPath;created_script_directory=$created}
 Write-Output "INSTALLED: $recovery"
}catch{WriteJson (Join-Path $recovery 'failure.json') @{status='S25_INSTALL_FAILED';message=$_.Exception.Message;instruction='Do not launch. ValidateRollback then Rollback with this exact recovery directory.'};throw}

