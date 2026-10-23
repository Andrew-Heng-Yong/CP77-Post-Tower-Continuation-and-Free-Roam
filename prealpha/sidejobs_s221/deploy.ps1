param(
 [ValidateSet('Validate','Install','ValidateRollback','Rollback')][string]$Mode='Validate',
 [string]$Build='', [string]$RecoveryRoot='',
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$SaveRoot='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077',
 [switch]$Fixture,[switch]$FailAfterBackup,[switch]$FailAfterReplace
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$fixtureRoot=Join-Path $PSScriptRoot 'fixtures'
$relative='archive/pc/mod/000_TowerContinued_SideJobs_S22.archive'
$oldSHA='9DE5ABC89AC73C81A381BA258118630FC195DE3580DABF776749FFD35E53D5A2'
$lib=Join-Path $workspace 'prealpha/graphics_gd2/tools/deploy.ps1'
if((Get-FileHash -LiteralPath $lib).Hash -cne '1D1D204D792D65FF30757B455E57826787E395A1DF0C1D5352A60D0757EC3307'){throw 'Safety helper changed'}
$text=Get-Content -LiteralPath $lib -Raw;$start=$text.IndexOf('function Full(');$end=$text.IndexOf('$game=Full $GameRoot;')
if($start -lt 0 -or $end -le $start){throw 'Helper boundary changed'}
. ([scriptblock]::Create($text.Substring($start,$end-$start)))
# Import only the established baseline definitions, never prior installer mains.
$prior=Join-Path $workspace 'prealpha/sidejobs_s21/deploy.ps1'
Match $prior 'C76BF68821E51B1239590E67227FB53CBDCAEC8C3EBF28C40AA0715433EB5554'
$text=Get-Content -LiteralPath $prior -Raw
$start=$text.IndexOf('$prior=Join-Path $workspace ''prealpha/sidejobs_s2/deploy.ps1''')
$ends=[regex]::Matches($text,'(?m)^function ReplaceExact\(')
if($start -lt 0 -or $ends.Count -ne 1 -or $ends[0].Index -le $start){throw 'Baseline boundary changed'}
$defs=[regex]::Replace($text.Substring($start,$ends[0].Index-$start),'(?m)^function OriginalPackage \{','function BeforeS22Package {')
. ([scriptblock]::Create($defs))
function OriginalPackage {
 $count=BeforeS22Package
 if(!$Fixture){
  Match (Join-Path $game 'archive/pc/mod/000_TowerContinued_SideJobs_S22.archive.xl') 'D88437FB829F76E774535D2B982D69205931A3A94BF59E2D890165205087A223'
  Match (Join-Path $game 'r6/scripts/TowerContinued_SideJobs_S22/SideJobsS22.reds') '037BB7AE91EA09A5BB7604DC27B0B45343AC16BF6435486855527BC3FE1641D7'
  Match (Join-Path $game 'r6/scripts/TowerContinued_SideJobs_S2/SideJobsS2.reds') '58F134FFE6CCD8DF0AF30FCCABBFD161BBBCC8AEF75E25C16D18303992134295'
  $count+=3
 }
 return $count
}
function TrueFlag($x){return ($x -is [bool] -and $x)}
function ReplaceExact([string]$from,[string]$expected,[string]$next,[string]$backup){
 Closed;Match $target $expected;Match $from $next;NoLink $target
 $displaced=Bound (Join-Path $recovery $backup) $recovery
 if(Test-Path -LiteralPath $displaced){throw 'Displaced backup exists'}
 [IO.File]::Replace($from,$target,$displaced,$false)
 Match $target $next;Match $displaced $expected
}
$game=Full $GameRoot;$saves=Full $SaveRoot;NoLink $game;NoLink $saves
if(!(Test-Path -LiteralPath $game -PathType Container) -or !(Test-Path -LiteralPath $saves -PathType Container)){throw 'Existing roots required'}
if($Fixture){
 [void](Bound $game $fixtureRoot);[void](Bound $saves $fixtureRoot);$buildBound=$fixtureRoot;$recoveryBound=$fixtureRoot
}else{
 if($game -cne 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077' -or $saves -cne 'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077' -or $FailAfterBackup -or $FailAfterReplace){throw 'Unapproved live roots/options'}
 $buildBound=Join-Path $PSScriptRoot 'build';$recoveryBound=Join-Path $workspace 'recovery'
}
$target=Bound (Join-Path $game $relative) $game
$recovery=if($RecoveryRoot){Bound $RecoveryRoot $recoveryBound}else{''}
Closed;$original=OriginalPackage
if($Mode -in @('ValidateRollback','Rollback')){
 if(!$recovery){throw 'Exact recovery required'}
 if(Test-Path -LiteralPath (Join-Path $recovery 'rollback_receipt.json')){throw 'Already rolled back'}
 $txnPath=Join-Path $recovery 'transaction.json';NoLink (Join-Path $recovery 'transaction.sha256')
 Match $txnPath (Get-Content -LiteralPath (Join-Path $recovery 'transaction.sha256') -Raw);$txn=ReadJson $txnPath
 if($txn.status -cne 'S221_SINGLE_ARCHIVE_REPLACEMENT' -or $txn.game_root -cne $game -or $txn.save_root -cne $saves -or $txn.relative -cne $relative -or $txn.old_sha256 -cne $oldSHA -or $txn.sha256 -ceq $oldSHA -or $txn.installer_sha256 -cne (Hash $PSCommandPath)){throw 'Recovery identity mismatch'}
 Match (Join-Path $recovery 'before.archive') $oldSHA;Match (Join-Path $recovery 'after.archive') $txn.sha256
 $actual=Hash $target;if($actual -cne $oldSHA -and $actual -cne $txn.sha256){throw 'Target drift; refusing overwrite'}
 foreach($name in @('rollback_candidate.archive','rollback_displaced.archive')){NoLink (Join-Path $recovery $name);if(Test-Path -LiteralPath (Join-Path $recovery $name)){throw 'Interrupted rollback requires inspection'}}
 $protected=Snapshot
 if($Mode -eq 'ValidateRollback'){@{status='VALIDATED_S221_ROLLBACK';protected_files=$protected.Count;original_package_verified=$original;replacement_present=($actual -ceq $txn.sha256)}|ConvertTo-Json;return}
 $replaced=$false
 if($actual -ceq $txn.sha256){
  $candidate=Join-Path $recovery 'rollback_candidate.archive';CopyExact (Join-Path $recovery 'before.archive') $candidate $oldSHA
  ReplaceExact $candidate $txn.sha256 $oldSHA 'rollback_displaced.archive';$replaced=$true
 }
 $count=Same $protected
 WriteJson (Join-Path $recovery 'rollback_receipt.json') @{status='ROLLED_BACK_S221';utc=[DateTime]::UtcNow.ToString('o');restored_original=$replaced;protected_files=$count;original_package_verified=(OriginalPackage);save_changes=$false}
 Write-Output "ROLLED_BACK: $recovery";return
}
if(!$Build){throw 'Build required'}
$buildRoot=Bound $Build $buildBound;$manifestPath=Join-Path $buildRoot 'build.json';$m=ReadJson $manifestPath
if($m.status -cne 'BUILT_S221_PHONE_GATE_LIVE_PENDING' -or $m.relative -cne $relative -or $m.old_sha256 -cne $oldSHA -or $m.sha256 -ceq $oldSHA -or $m.archive_replacements -ne 1 -or $m.additions -ne 0 -or $m.scripts_changed -ne 0 -or $m.native_counter_writes -ne 0 -or !(TrueFlag $m.native_cleanup_unchanged) -or !(TrueFlag $m.owner_ids_unchanged) -or !(TrueFlag $m.packed_readback) -or @($m.resources.PSObject.Properties).Count -ne 8 -or @($m.changes).Count -ne 4){throw 'Build scope mismatch'}
$source=Join-Path $buildRoot '000_TowerContinued_SideJobs_S22.archive';Match $source $m.sha256;Match $target $oldSHA
$tests=ReadJson (Join-Path $buildRoot 'tests.json')
if($tests.status -cne 'PASS_NOT_LIVE' -or $tests.build_sha256 -cne (Hash $manifestPath) -or $tests.policy_cases -lt 5464 -or $tests.user_regressions -ne 4 -or $tests.unchanged_nodes -ne 1145 -or $tests.unchanged_resources -ne 6 -or $tests.removed_equalities -ne 64 -or !(TrueFlag $tests.all_edges_unchanged) -or !(TrueFlag $tests.no_new_writes) -or !(TrueFlag $tests.native_cleanup_unchanged) -or !(TrueFlag $tests.owner_ids_unchanged)){throw 'Matching regression proof required'}
Match (Join-Path $PSScriptRoot 'test.py') $tests.tester_sha256
$audit=ReadJson (Join-Path $buildRoot 'resource_check.json')
if($audit.status -cne 'PASS_RESOURCE_AUDIT' -or $audit.build_sha256 -cne (Hash $manifestPath) -or $audit.official_comparisons -ne 57 -or $audit.installed_readbacks -ne 8 -or !(TrueFlag $audit.new_cleanup_first) -or !(TrueFlag $audit.modlist_absent) -or @($audit.official_overrides).Count -ne 0){throw 'Matching resource audit required'}
Match (Join-Path $PSScriptRoot 'resource_check.ps1') $audit.checker_sha256
if(!$Fixture){
 $proofs=@(Get-ChildItem -LiteralPath $fixtureRoot -Filter results.json -File -Recurse|ForEach-Object {ReadJson $_.FullName}|Where-Object {$_.status -ceq 'PASS_WORKSPACE_FIXTURES_NOT_LIVE' -and $_.build_sha256 -ceq (Hash $manifestPath) -and $_.installer_sha256 -ceq (Hash $PSCommandPath) -and $_.tester_sha256 -ceq (Hash (Join-Path $PSScriptRoot 'test_deploy.py')) -and $_.cases -ge 30 -and $_.checks -ge 40})
 if($proofs.Count -lt 1){throw 'Matching deployment fixtures required'}
 foreach($p in $m.source_pins.PSObject.Properties){Match (Bound (Join-Path $workspace $p.Name) $workspace) $p.Value}
 foreach($p in $audit.archive_pins.PSObject.Properties){Match (Bound $p.Name $game) $p.Value}
 $actualMods=@(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/mod') -File -Filter '*.archive'|ForEach-Object FullName)
 if(@(Compare-Object $actualMods @($audit.archive_pins.PSObject.Properties.Name)).Count){throw 'Installed archive set drift'}
 if(Test-Path -LiteralPath (Join-Path $game 'archive/pc/mod/modlist.txt')){throw 'Load order changed'}
}
$protected=Snapshot
if($Mode -eq 'Validate'){@{status='VALIDATED_S221_SINGLE_ARCHIVE';replacements=1;additions=0;original_package_verified=$original;protected_files=$protected.Count;build_sha256=Hash $manifestPath}|ConvertTo-Json;return}
if(!$recovery -or (Test-Path -LiteralPath $recovery)){throw 'New recovery directory required'}
Closed;New-Item -ItemType Directory -Path $recovery -ErrorAction Stop|Out-Null
CopyExact $target (Join-Path $recovery 'before.archive') $oldSHA
CopyExact $source (Join-Path $recovery 'after.archive') $m.sha256
WriteJson (Join-Path $recovery 'transaction.json') @{status='S221_SINGLE_ARCHIVE_REPLACEMENT';game_root=$game;save_root=$saves;relative=$relative;old_sha256=$oldSHA;sha256=$m.sha256;build_sha256=Hash $manifestPath;protected=$protected;installer_sha256=Hash $PSCommandPath;utc=[DateTime]::UtcNow.ToString('o')}
[IO.File]::WriteAllText((Join-Path $recovery 'transaction.sha256'),(Hash (Join-Path $recovery 'transaction.json')),[Text.UTF8Encoding]::new($false))
try{
 if($FailAfterBackup){throw 'Injected fixture failure after backup'}
 $candidate=Join-Path $recovery 'install_candidate.archive';CopyExact (Join-Path $recovery 'after.archive') $candidate $m.sha256
 ReplaceExact $candidate $oldSHA $m.sha256 'displaced.archive'
 if($FailAfterReplace){throw 'Injected fixture failure after replacement'}
 $count=Same $protected
 WriteJson (Join-Path $recovery 'install_receipt.json') @{status='INSTALLED_S221_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');replacements=1;additions=0;installed_sha256=Hash $target;original_package_verified=(OriginalPackage);protected_files=$count;protected_save_files=@($protected.Keys|Where-Object {$_ -like 'save/*'}).Count;protected_cache_files=@($protected.Keys|Where-Object {$_ -like 'game/r6/cache/*'}).Count;settings_changed=$false;build_sha256=Hash $manifestPath;recovery=$recovery}
 Write-Output "INSTALLED: $recovery"
}catch{
 WriteJson (Join-Path $recovery 'failure.json') @{status='INSTALL_INTERRUPTED';message=$_.Exception.Message;instruction='Do not launch. ValidateRollback then Rollback with this exact recovery directory.'}
 throw
}
