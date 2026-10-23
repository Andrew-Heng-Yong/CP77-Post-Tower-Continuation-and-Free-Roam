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
$relative='r6/scripts/TowerContinued_SideJobs_S2/SideJobsS2.reds'
$oldSHA='5C687B1356584D17204CA342332E4273D8B18CB1ECDFF6C27CA260397052883E'
# Import definitions only, not either prior installer's main body.
$lib=Join-Path $workspace 'prealpha/graphics_gd2/tools/deploy.ps1'
if((Get-FileHash -LiteralPath $lib).Hash -cne '1D1D204D792D65FF30757B455E57826787E395A1DF0C1D5352A60D0757EC3307'){throw 'Safety helper changed'}
$text=Get-Content -LiteralPath $lib -Raw;$start=$text.IndexOf('function Full(');$end=$text.IndexOf('$game=Full $GameRoot;')
if($start -lt 0 -or $end -le $start){throw 'Helper boundary changed'}
. ([scriptblock]::Create($text.Substring($start,$end-$start)))
$prior=Join-Path $workspace 'prealpha/sidejobs_s2/deploy.ps1'
Match $prior 'B3D60C84D5A681EBC629AB15DC29ACA37926E5D7195CCEED1D821B0FCFF6BDE1'
$text=Get-Content -LiteralPath $prior -Raw
$start=$text.IndexOf('$prior=Join-Path $workspace ''prealpha/ncpd_repair_n21/deploy.ps1''')
$scopeMatches=[regex]::Matches($text,'(?m)^function Scope\(')
if($scopeMatches.Count -ne 1){throw 'S2 scope boundary changed'}
$end=$scopeMatches[0].Index
if($start -lt 0 -or $end -le $start){throw 'S2 baseline helper boundary changed'}
$defs=[regex]::Replace($text.Substring($start,$end-$start),'(?m)^function OriginalPackage \{','function BeforeS2Package {')
. ([scriptblock]::Create($defs))
function OriginalPackage {
 $count=BeforeS2Package
 if(!$Fixture){
  Match (Join-Path $game 'archive/pc/mod/TowerContinued_SideJobs_S2.archive') '236FF68656A9BD37025406BDA1C0AF439891FC4735DD1C13E1634C27C8315A8A'
  Match (Join-Path $game 'archive/pc/mod/TowerContinued_SideJobs_S2.archive.xl') '271BAB2AE5E8A1E02F83FAA3631FEF0BE23EA3A704F537278B4F96BF55C1B0D7'
  $count+=2
 }
 return $count
}
function ReplaceExact([string]$from,[string]$expectedCurrent,[string]$newHash,[string]$backupName){
 Closed;Match $target $expectedCurrent;Match $from $newHash;NoLink $target
 $displaced=Bound (Join-Path $recovery $backupName) $recovery
 if(Test-Path -LiteralPath $displaced){throw 'Displaced-file backup already exists'}
 # Same-volume atomic replacement; the verified original is retained twice:
 # immutable before.reds plus the displaced file produced by File.Replace.
 [IO.File]::Replace($from,$target,$displaced,$false)
 Match $target $newHash;Match $displaced $expectedCurrent
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
 if(!$recovery){throw 'Exact recovery root required'}
 if(Test-Path -LiteralPath (Join-Path $recovery 'rollback_receipt.json')){throw 'Already rolled back'}
 $txnPath=Join-Path $recovery 'transaction.json';Match $txnPath (Get-Content -LiteralPath (Join-Path $recovery 'transaction.sha256') -Raw)
 $txn=ReadJson $txnPath
 if($txn.status -cne 'S21_SINGLE_SCRIPT_REPLACEMENT' -or $txn.game_root -cne $game -or $txn.save_root -cne $saves -or $txn.relative -cne $relative -or $txn.old_sha256 -cne $oldSHA -or $txn.sha256 -ceq $oldSHA){throw 'Recovery scope mismatch'}
 Match (Join-Path $recovery 'before.reds') $oldSHA;Match (Join-Path $recovery 'after.reds') $txn.sha256
 $actual=Hash $target;if($actual -cne $oldSHA -and $actual -cne $txn.sha256){throw 'Target drift; refusing to overwrite user changes'}
 foreach($name in @('rollback_candidate.reds','rollback_displaced.reds')){NoLink (Join-Path $recovery $name);if(Test-Path -LiteralPath (Join-Path $recovery $name)){throw 'Interrupted rollback requires inspection'}}
 $protected=Snapshot
 if($Mode -eq 'ValidateRollback'){@{status='VALIDATED_S21_ROLLBACK';protected_files=$protected.Count;original_package_verified=$original;replacement_present=($actual -ceq $txn.sha256)}|ConvertTo-Json;return}
 $replaced=$false
 if($actual -ceq $txn.sha256){
  $candidate=Join-Path $recovery 'rollback_candidate.reds';CopyExact (Join-Path $recovery 'before.reds') $candidate $oldSHA
  ReplaceExact $candidate $txn.sha256 $oldSHA 'rollback_displaced.reds';$replaced=$true
 }
 $count=Same $protected
 WriteJson (Join-Path $recovery 'rollback_receipt.json') @{status='ROLLED_BACK_S21';utc=[DateTime]::UtcNow.ToString('o');restored_original=$replaced;protected_files=$count;original_package_verified=(OriginalPackage);save_changes=$false}
 Write-Output "ROLLED_BACK: $recovery";return
}
if(!$Build){throw 'Build required'}
$buildRoot=Bound $Build $buildBound;$manifestPath=Join-Path $buildRoot 'build.json';$m=ReadJson $manifestPath
if($m.status -cne 'BUILT_S21_SCRIPT_REPAIR_LIVE_PENDING' -or $m.relative -cne $relative -or $m.old_sha256 -cne $oldSHA -or $m.sha256 -ceq $oldSHA -or $m.runtime_replacements -ne 1 -or $m.additions -ne 0 -or $m.archives_changed -ne 0 -or $m.owners_changed -ne 0 -or $m.native_guards_unchanged -ne $true -or $m.generated_table_unchanged -ne $true -or @($m.dataset).Count -ne 2){throw 'Build scope mismatch'}
$source=Join-Path $buildRoot 'SideJobsS2.reds';Match $source $m.sha256;Match $target $oldSHA
$tests=ReadJson (Join-Path $buildRoot 'tests.json')
if($tests.status -cne 'PASS_NOT_LIVE' -or $tests.build_sha256 -cne (Hash $manifestPath) -or $tests.policy_cases -lt 855 -or !$tests.generated_table_unchanged -or !$tests.owners_unchanged){throw 'Matching policy tests required'}
Match (Join-Path $PSScriptRoot 'test.py') $tests.tester_sha256
Match (Join-Path $PSScriptRoot 'test_policy.py') $tests.policy_tester_sha256
$compiled=ReadJson (Join-Path $buildRoot 'compile_result.json')
if($compiled.status -cne 'PASS_NOT_LIVE' -or $compiled.build_sha256 -cne (Hash $manifestPath) -or !$compiled.full_scc -or !$compiled.combined_cli -or !$compiled.body_readback -or !$compiled.live_files_unchanged -or $compiled.script_sha256 -cne $m.sha256 -or !$compiled.equipmentex){throw 'Matching full compile required'}
Match (Join-Path $PSScriptRoot 'compile.py') $compiled.compiler_sha256
if(!$Fixture){
 $proofs=@(Get-ChildItem -LiteralPath $fixtureRoot -Filter 'results.json' -File -Recurse|ForEach-Object {ReadJson $_.FullName}|Where-Object {$_.status -ceq 'PASS_WORKSPACE_FIXTURES_NOT_LIVE' -and $_.build_sha256 -ceq (Hash $manifestPath) -and $_.installer_sha256 -ceq (Hash $PSCommandPath) -and $_.tester_sha256 -ceq (Hash (Join-Path $PSScriptRoot 'test_deploy.py')) -and $_.cases -ge 30 -and $_.checks -ge 40})
 if($proofs.Count -lt 1){throw 'Matching installer fixtures required'}
 foreach($p in $compiled.dependencies.PSObject.Properties){Match $p.Name $p.Value}
 foreach($p in $compiled.protected.PSObject.Properties){Match $p.Name $p.Value}
 foreach($p in $m.source_pins.PSObject.Properties){Match (Bound (Join-Path $workspace $p.Name) $workspace) $p.Value}
}
$protected=Snapshot
if($Mode -eq 'Validate'){@{status='VALIDATED_S21_SINGLE_SCRIPT';replacements=1;additions=0;original_package_verified=$original;protected_files=$protected.Count;build_sha256=Hash $manifestPath}|ConvertTo-Json;return}
if(!$recovery -or (Test-Path -LiteralPath $recovery)){throw 'New recovery directory required'}
Closed;New-Item -ItemType Directory -Path $recovery -ErrorAction Stop|Out-Null
CopyExact $target (Join-Path $recovery 'before.reds') $oldSHA
CopyExact $source (Join-Path $recovery 'after.reds') $m.sha256
WriteJson (Join-Path $recovery 'transaction.json') @{status='S21_SINGLE_SCRIPT_REPLACEMENT';game_root=$game;save_root=$saves;relative=$relative;old_sha256=$oldSHA;sha256=$m.sha256;build_sha256=Hash $manifestPath;protected=$protected;installer_sha256=Hash $PSCommandPath;utc=[DateTime]::UtcNow.ToString('o')}
[IO.File]::WriteAllText((Join-Path $recovery 'transaction.sha256'),(Hash (Join-Path $recovery 'transaction.json')),[Text.UTF8Encoding]::new($false))
try{
 if($FailAfterBackup){throw 'Injected fixture failure after backup'}
 $candidate=Join-Path $recovery 'install_candidate.reds';CopyExact (Join-Path $recovery 'after.reds') $candidate $m.sha256
 ReplaceExact $candidate $oldSHA $m.sha256 'displaced.reds'
 if($FailAfterReplace){throw 'Injected fixture failure after replacement'}
 $count=Same $protected
 WriteJson (Join-Path $recovery 'install_receipt.json') @{status='INSTALLED_S21_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');replacements=1;additions=0;installed_sha256=Hash $target;original_package_verified=(OriginalPackage);protected_files=$count;protected_save_files=@($protected.Keys|Where-Object {$_ -like 'save/*'}).Count;protected_cache_files=@($protected.Keys|Where-Object {$_ -like 'game/r6/cache/*'}).Count;settings_changed=$false;build_sha256=Hash $manifestPath;recovery=$recovery}
 Write-Output "INSTALLED: $recovery"
}catch{
 WriteJson (Join-Path $recovery 'failure.json') @{status='INSTALL_INTERRUPTED';message=$_.Exception.Message;instruction='Do not launch. ValidateRollback then Rollback with this exact recovery directory.'}
 throw
}
