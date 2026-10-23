param(
 [ValidateSet('Validate','Install','ValidateRollback','Rollback')][string]$Mode='Validate',
 [string]$Build='', [string]$RecoveryRoot='',
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$SaveRoot='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077',
 [switch]$Fixture,[switch]$FailAfterBackup,[switch]$FailAfterFirst,[switch]$FailAfterReplace
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$fixtureRoot=Join-Path $PSScriptRoot 'fixtures'
$relatives=@('archive/pc/mod/000_TowerContinued_SideJobs_S22.archive','archive/pc/mod/000_TowerContinued_SideJobs_S22.archive.xl','r6/scripts/TowerContinued_SideJobs_S22/SideJobsS22.reds','r6/scripts/TowerContinued_SideJobs_S2/SideJobsS2.reds')
$oldSHA='68947EA168C7F3A3AD589BB8E568AF6EF4E1B54F62EB8ACE8190E339F8582C1F'
# Hash-pinned definitions only. Neither imported installer's main is executed.
$lib=Join-Path $workspace 'prealpha/graphics_gd2/tools/deploy.ps1'
if((Get-FileHash -LiteralPath $lib).Hash -cne '1D1D204D792D65FF30757B455E57826787E395A1DF0C1D5352A60D0757EC3307'){throw 'Safety helper changed'}
$text=Get-Content -LiteralPath $lib -Raw;$start=$text.IndexOf('function Full(');$end=$text.IndexOf('$game=Full $GameRoot;')
if($start -lt 0 -or $end -le $start){throw 'Helper boundary changed'}
$defs=$text.Substring($start,$end-$start)
if([regex]::Matches($defs,[regex]::Escape('if($rel -ceq $relative)')).Count -ne 1){throw 'Snapshot boundary changed'}
$defs=$defs.Replace('if($rel -ceq $relative)','if($rel -cin $relatives)')
. ([scriptblock]::Create($defs))
$prior=Join-Path $workspace 'prealpha/sidejobs_s21/deploy.ps1'
Match $prior 'C76BF68821E51B1239590E67227FB53CBDCAEC8C3EBF28C40AA0715433EB5554'
$text=Get-Content -LiteralPath $prior -Raw
$start=$text.IndexOf('$prior=Join-Path $workspace ''prealpha/sidejobs_s2/deploy.ps1''')
$ends=[regex]::Matches($text,'(?m)^function ReplaceExact\(')
if($start -lt 0 -or $ends.Count -ne 1 -or $ends[0].Index -le $start){throw 'S21 baseline helper boundary changed'}
. ([scriptblock]::Create($text.Substring($start,$ends[0].Index-$start)))
function Scope($files){
 if(@($files).Count -ne 4 -or @($files|Select-Object -ExpandProperty relative -Unique).Count -ne 4){throw 'Exactly three additions and one replacement required'}
 for($i=0;$i -lt 4;$i++){
  $f=$files[$i]
  if($f.relative -cne $relatives[$i] -or $f.sha256 -cnotmatch '^[A-F0-9]{64}$'){throw 'File scope mismatch'}
  if($i -eq 3){if($f.old_sha256 -cne $oldSHA -or $f.sha256 -ceq $oldSHA){throw 'Replacement identity mismatch'}}
  elseif('old_sha256' -in $f.PSObject.Properties.Name -and $f.old_sha256){throw 'Addition may not replace anything'}
 }
}
function TrueFlag($value){return ($value -is [bool] -and $value)}
function ReplaceExact([string]$from,[string]$expectedCurrent,[string]$newHash,[string]$backupName){
 Closed;Match $replacement $expectedCurrent;Match $from $newHash;NoLink $replacement
 $displaced=Bound (Join-Path $recovery $backupName) $recovery
 if(Test-Path -LiteralPath $displaced){throw 'Displaced backup exists'}
 [IO.File]::Replace($from,$replacement,$displaced,$false)
 Match $replacement $newHash;Match $displaced $expectedCurrent
}
$game=Full $GameRoot;$saves=Full $SaveRoot;NoLink $game;NoLink $saves
if(!(Test-Path -LiteralPath $game -PathType Container) -or !(Test-Path -LiteralPath $saves -PathType Container)){throw 'Existing game/save roots required'}
if($Fixture){
 [void](Bound $game $fixtureRoot);[void](Bound $saves $fixtureRoot);$buildBound=$fixtureRoot;$recoveryBound=$fixtureRoot
}else{
 if($game -cne 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077' -or $saves -cne 'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077' -or $FailAfterBackup -or $FailAfterFirst -or $FailAfterReplace){throw 'Unapproved live roots/options'}
 $buildBound=Join-Path $PSScriptRoot 'build';$recoveryBound=Join-Path $workspace 'recovery'
}
$replacement=Bound (Join-Path $game $relatives[3]) $game
$scriptParent=Bound (Join-Path $game 'r6/scripts/TowerContinued_SideJobs_S22') $game
$recovery=if($RecoveryRoot){Bound $RecoveryRoot $recoveryBound}else{''}
Closed;$original=OriginalPackage
if($Mode -in @('ValidateRollback','Rollback')){
 if(!$recovery){throw 'Exact recovery directory required'}
 if(Test-Path -LiteralPath (Join-Path $recovery 'rollback_receipt.json')){throw 'Already rolled back'}
 $txnPath=Join-Path $recovery 'transaction.json';NoLink (Join-Path $recovery 'transaction.sha256')
 Match $txnPath (Get-Content -LiteralPath (Join-Path $recovery 'transaction.sha256') -Raw);$txn=ReadJson $txnPath
 if($txn.status -cne 'S22_THREE_ADD_ONE_REPLACE' -or $txn.game_root -cne $game -or $txn.save_root -cne $saves){throw 'Recovery identity mismatch'}
 Scope $txn.files;Match (Join-Path $recovery 'before_SideJobsS2.reds') $oldSHA
 foreach($f in $txn.files){Match (Join-Path $recovery ([IO.Path]::GetFileName($f.relative))) $f.sha256}
 $actual=Hash $replacement
 if($actual -cne $oldSHA -and $actual -cne $txn.files[3].sha256){throw 'Replacement drift; refusing to overwrite user changes'}
 foreach($f in $txn.files[0..2]){
  $target=Bound (Join-Path $game $f.relative) $game
  $removed=Join-Path $recovery ('removed_'+[IO.Path]::GetFileName($f.relative));NoLink $removed
  if(Test-Path -LiteralPath $removed){throw 'Interrupted rollback requires inspection'}
  if(Test-Path -LiteralPath $target){Match $target $f.sha256}
 }
 foreach($name in @('rollback_candidate.reds','rollback_displaced.reds')){NoLink (Join-Path $recovery $name);if(Test-Path -LiteralPath (Join-Path $recovery $name)){throw 'Interrupted rollback requires inspection'}}
 $protected=Snapshot
 if($Mode -eq 'ValidateRollback'){@{status='VALIDATED_S22_ROLLBACK';original_package_verified=$original;protected_files=$protected.Count;replacement_present=($actual -ceq $txn.files[3].sha256)}|ConvertTo-Json;return}
 $restored=$false;$moved=0
 if($actual -ceq $txn.files[3].sha256){
  $candidate=Join-Path $recovery 'rollback_candidate.reds';CopyExact (Join-Path $recovery 'before_SideJobsS2.reds') $candidate $oldSHA
  ReplaceExact $candidate $txn.files[3].sha256 $oldSHA 'rollback_displaced.reds';$restored=$true
 }
 foreach($f in $txn.files[0..2]){
  $target=Bound (Join-Path $game $f.relative) $game
  if(Test-Path -LiteralPath $target){
   Closed;Match $target $f.sha256;$removed=Join-Path $recovery ('removed_'+[IO.Path]::GetFileName($f.relative))
   [IO.File]::Move($target,$removed,$false);Match $removed $f.sha256;$moved++
  }
 }
 $count=Same $protected
 WriteJson (Join-Path $recovery 'rollback_receipt.json') @{status='ROLLED_BACK_S22';utc=[DateTime]::UtcNow.ToString('o');restored_original=$restored;moved_recoverably=$moved;protected_files=$count;original_package_verified=(OriginalPackage);save_changes=$false;empty_owned_script_directory_retained=$true}
 Write-Output "ROLLED_BACK: $recovery";return
}
if(!$Build){throw 'Build directory required'}
$buildRoot=Bound $Build $buildBound;$manifestPath=Join-Path $buildRoot 'build.json';$m=ReadJson $manifestPath
if($m.status -cne 'BUILT_S22_LIVE_PENDING' -or !(TrueFlag $m.packed_readback) -or @($m.resources.PSObject.Properties).Count -lt 1 -or @($m.boots).Count -lt 1){throw 'Build scope mismatch'}
Scope $m.files
foreach($f in $m.files){
 Match (Join-Path $buildRoot ([IO.Path]::GetFileName($f.relative))) $f.sha256
 $target=Bound (Join-Path $game $f.relative) $game
 if($f.relative -ceq $relatives[3]){Match $target $oldSHA}else{if(Test-Path -LiteralPath $target){throw 'Addition already exists; refusing overwrite'}}
 $parent=Split-Path -Parent $target
 if(!(Test-Path -LiteralPath $parent -PathType Container)){
  if($parent -cne $scriptParent -or (Test-Path -LiteralPath $parent) -or !(Test-Path -LiteralPath (Split-Path -Parent $parent) -PathType Container)){throw 'Only exact new S22 script leaf may be created'}
 }
}
$tests=ReadJson (Join-Path $buildRoot 'tests.json')
if($tests.status -cne 'PASS_NOT_LIVE' -or $tests.build_sha256 -cne (Hash $manifestPath) -or $tests.policy_cases -lt 1 -or $tests.native_payload_checks -lt 1){throw 'Matching policy/native tests required'}
Match (Join-Path $PSScriptRoot 'test.py') $tests.tester_sha256
$compiled=ReadJson (Join-Path $buildRoot 'compile_result.json')
if($compiled.status -cne 'PASS_NOT_LIVE' -or $compiled.build_sha256 -cne (Hash $manifestPath)){throw 'Matching full compiler proof required'}
foreach($flag in @('full_scc','combined_cli','body_readback','live_files_unchanged','equipmentex')){if(!(TrueFlag $compiled.$flag)){throw "Compiler proof missing: $flag"}}
Match (Join-Path $PSScriptRoot 'compile.py') $compiled.compiler_sha256
$resources=ReadJson (Join-Path $buildRoot 'resource_check.json')
if($resources.status -cne 'PASS_RESOURCE_AUDIT' -or $resources.build_sha256 -cne (Hash $manifestPath) -or $resources.official_comparisons -lt 1 -or @($resources.official_overrides).Count -ne 0 -or !(TrueFlag $resources.modlist_absent)){throw 'Matching official resource audit required'}
Match (Join-Path $PSScriptRoot 'resource_check.ps1') $resources.checker_sha256
foreach($c in $resources.collisions){if($c.depot -cne 'towercontinued\gig_phone_u9\fixer_cleanup.questphase'){throw 'Unexpected resource collision'}}
if(@($m.source_pins.PSObject.Properties).Count -lt 1){throw 'Source pins required'}
foreach($p in $m.source_pins.PSObject.Properties){Match (Bound (Join-Path $workspace $p.Name) $workspace) $p.Value}
if(!$Fixture){
 if(Test-Path -LiteralPath (Join-Path $game 'archive/pc/mod/modlist.txt')){throw 'Explicit load order appeared; priority not verified'}
 $proofs=@(Get-ChildItem -LiteralPath $fixtureRoot -Filter 'results.json' -File -Recurse|ForEach-Object {ReadJson $_.FullName}|Where-Object {$_.status -ceq 'PASS_WORKSPACE_FIXTURES_NOT_LIVE' -and $_.build_sha256 -ceq (Hash $manifestPath) -and $_.installer_sha256 -ceq (Hash $PSCommandPath) -and $_.tester_sha256 -ceq (Hash (Join-Path $PSScriptRoot 'test_deploy.py')) -and $_.cases -ge 30 -and $_.checks -ge 40})
 if($proofs.Count -lt 1){throw 'Matching deployment fixtures required'}
 foreach($map in @($compiled.dependencies,$compiled.protected)){foreach($p in $map.PSObject.Properties){Match $p.Name $p.Value}}
 $archives=@(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/mod') -Filter '*.archive' -File)
 if($archives.Count -ne @($resources.archive_pins.PSObject.Properties).Count){throw 'Installed archive set changed'}
 foreach($p in $resources.archive_pins.PSObject.Properties){
  $ap=if([IO.Path]::IsPathFullyQualified($p.Name)){$p.Name}else{Join-Path $game ('archive/pc/mod/'+$p.Name)}
  Match (Bound $ap (Join-Path $game 'archive/pc/mod')) $p.Value
 }
}
$protected=Snapshot
if($Mode -eq 'Validate'){@{status='VALIDATED_S22_MIXED';replacements=1;additions=3;original_package_verified=$original;protected_files=$protected.Count;build_sha256=Hash $manifestPath}|ConvertTo-Json;return}
if(!$recovery -or (Test-Path -LiteralPath $recovery)){throw 'New recovery directory required'}
Closed;New-Item -ItemType Directory -Path $recovery -ErrorAction Stop|Out-Null
CopyExact $replacement (Join-Path $recovery 'before_SideJobsS2.reds') $oldSHA
foreach($f in $m.files){CopyExact (Join-Path $buildRoot ([IO.Path]::GetFileName($f.relative))) (Join-Path $recovery ([IO.Path]::GetFileName($f.relative))) $f.sha256}
WriteJson (Join-Path $recovery 'transaction.json') @{status='S22_THREE_ADD_ONE_REPLACE';game_root=$game;save_root=$saves;files=$m.files;build_sha256=Hash $manifestPath;protected=$protected;installer_sha256=Hash $PSCommandPath;utc=[DateTime]::UtcNow.ToString('o')}
[IO.File]::WriteAllText((Join-Path $recovery 'transaction.sha256'),(Hash (Join-Path $recovery 'transaction.json')),[Text.UTF8Encoding]::new($false))
try{
 if($FailAfterBackup){throw 'Injected fixture failure after backup'}
 $copied=0;$createdScriptDirectory=$false
 foreach($f in $m.files[0..2]){
  Closed;$target=Bound (Join-Path $game $f.relative) $game
  if($f.relative -ceq $relatives[2] -and !(Test-Path -LiteralPath $scriptParent)){
   [void](Bound $scriptParent $game);New-Item -ItemType Directory -Path $scriptParent -ErrorAction Stop|Out-Null;$createdScriptDirectory=$true
  }
  CopyExact (Join-Path $recovery ([IO.Path]::GetFileName($f.relative))) $target $f.sha256
  $copied++;if($FailAfterFirst -and $copied -eq 1){throw 'Injected fixture failure after first addition'}
 }
 $candidate=Join-Path $recovery 'install_candidate.reds';CopyExact (Join-Path $recovery 'SideJobsS2.reds') $candidate $m.files[3].sha256
 ReplaceExact $candidate $oldSHA $m.files[3].sha256 'displaced.reds'
 if($FailAfterReplace){throw 'Injected fixture failure after replacement'}
 $count=Same $protected
 WriteJson (Join-Path $recovery 'install_receipt.json') @{status='INSTALLED_S22_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');replacements=1;additions=3;installed_files=$m.files;original_package_verified=(OriginalPackage);protected_files=$count;protected_save_files=@($protected.Keys|Where-Object {$_ -like 'save/*'}).Count;protected_cache_files=@($protected.Keys|Where-Object {$_ -like 'game/r6/cache/*'}).Count;settings_changed=$false;build_sha256=Hash $manifestPath;recovery=$recovery;created_script_directory=$createdScriptDirectory}
 Write-Output "INSTALLED: $recovery"
}catch{
 WriteJson (Join-Path $recovery 'failure.json') @{status='INSTALL_INTERRUPTED';message=$_.Exception.Message;instruction='Do not launch. ValidateRollback then Rollback with this exact recovery directory.'}
 throw
}
