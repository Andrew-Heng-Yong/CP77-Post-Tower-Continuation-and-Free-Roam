param(
 [ValidateSet('Validate','Install','ValidateRollback','Rollback')][string]$Mode='Validate',
 [string]$Build='', [string]$RecoveryRoot='',
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$SaveRoot='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077',
 [switch]$Fixture,[switch]$FailAfterFirst
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..')).TrimEnd('\')
$fixtureRoot=Join-Path $PSScriptRoot 'fixtures'
$modRelative='bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_SideJobsCaptureS23'
$relatives=@(($modRelative+'/init.lua'),($modRelative+'/data.json'))
$lib=Join-Path $workspace 'prealpha/graphics_gd2/tools/deploy.ps1'
if((Get-FileHash -LiteralPath $lib).Hash -cne '1D1D204D792D65FF30757B455E57826787E395A1DF0C1D5352A60D0757EC3307'){throw 'Safety helper changed'}
$text=Get-Content -LiteralPath $lib -Raw
$start=$text.IndexOf('function Full(');$end=$text.IndexOf('$game=Full $GameRoot;')
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
 foreach($p in $pins.Keys){Match (Bound (Join-Path $game $p) $game) $pins[$p]}
 return $pins.Count
}
function Scope($files){
 $names=@($files.PSObject.Properties.Name|Sort-Object)
 if(($names -join '|') -cne 'data.json|init.lua'){throw 'Exactly two diagnostic files required'}
 foreach($p in $files.PSObject.Properties){if($p.Value -isnot [string] -or $p.Value -cnotmatch '^[A-F0-9]{64}$'){throw 'Invalid digest'}}
}
$game=Full $GameRoot;$saves=Full $SaveRoot;NoLink $game;NoLink $saves
if(!(Test-Path -LiteralPath $game -PathType Container) -or !(Test-Path -LiteralPath $saves -PathType Container)){throw 'Existing roots required'}
if($Fixture){
 [void](Bound $game $fixtureRoot);[void](Bound $saves $fixtureRoot);$buildBound=$fixtureRoot;$recoveryBound=$fixtureRoot
}else{
 if($game -cne 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077' -or $saves -cne 'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077' -or $FailAfterFirst){throw 'Unapproved live roots/options'}
 $buildBound=Join-Path $PSScriptRoot 'build';$recoveryBound=Join-Path $workspace 'recovery'
}
$targetDir=Bound (Join-Path $game $modRelative) $game
$recovery=if($RecoveryRoot){Bound $RecoveryRoot $recoveryBound}else{''}
Closed;$verified=WorkingPackage
if($Mode -in @('ValidateRollback','Rollback')){
 if(!$recovery){throw 'Exact recovery directory required'}
 if(Test-Path -LiteralPath (Join-Path $recovery 'rollback_receipt.json')){throw 'Already rolled back'}
 $txnPath=Join-Path $recovery 'transaction.json'
 Match $txnPath (Get-Content -LiteralPath (Join-Path $recovery 'transaction.sha256') -Raw)
 $txn=ReadJson $txnPath
 if($txn.status -cne 'S23_CAPTURE_ADD_ONLY' -or $txn.game_root -cne $game -or $txn.save_root -cne $saves -or $txn.mod_relative -cne $modRelative -or $txn.installer_sha256 -cne (Hash $PSCommandPath)){throw 'Recovery identity mismatch'}
 Scope $txn.files
 foreach($p in $txn.files.PSObject.Properties){
  Match (Join-Path $recovery $p.Name) $p.Value
  $target=Bound (Join-Path $targetDir $p.Name) $game
  if(Test-Path -LiteralPath $target){Match $target $p.Value}
  $removed=Bound (Join-Path $recovery ('removed_'+$p.Name)) $recovery
  if(Test-Path -LiteralPath $removed){throw 'Interrupted/previous rollback requires inspection'}
 }
 $protected=Snapshot
 if($Mode -eq 'ValidateRollback'){@{status='VALIDATED_S23_CAPTURE_ROLLBACK';protected_files=$protected.Count;working_files_verified=$verified}|ConvertTo-Json;return}
 $moved=0
 foreach($p in $txn.files.PSObject.Properties){
  $target=Bound (Join-Path $targetDir $p.Name) $game
  if(Test-Path -LiteralPath $target){
   Closed;Match $target $p.Value
   $removed=Bound (Join-Path $recovery ('removed_'+$p.Name)) $recovery
   [IO.File]::Move($target,$removed,$false);Match $removed $p.Value;$moved++
  }
 }
 $count=Same $protected
 WriteJson (Join-Path $recovery 'rollback_receipt.json') @{status='ROLLED_BACK_S23_CAPTURE';moved_recoverably=$moved;protected_files=$count;capture_reports_preserved=$true;save_changes=$false}
 Write-Output "ROLLED_BACK: $recovery";return
}
if(!$Build){throw 'Build required'}
$buildRoot=Bound $Build $buildBound;$manifestPath=Join-Path $buildRoot 'build.json';$m=ReadJson $manifestPath
if($m.status -cne 'BUILT_READ_ONLY_CAPTURE_NOT_RESTORATION' -or $m.jobs -ne 58 -or $m.journals -ne 740 -or $m.facts -ne 2932 -or @($m.root_only).Count -ne 0 -or $m.native_writes -ne 0 -or $m.save_writes -ne 0 -or $m.automatic_callbacks -ne 0){throw 'Capture-only scope mismatch'}
Scope $m.files
if(Test-Path -LiteralPath $targetDir){throw 'Diagnostic directory already exists; refusing overwrite'}
if(!(Test-Path -LiteralPath (Split-Path -Parent $targetDir) -PathType Container)){throw 'Existing CET mods folder required'}
foreach($p in $m.files.PSObject.Properties){Match (Bound (Join-Path $buildRoot $p.Name) $buildRoot) $p.Value}
$tests=ReadJson (Join-Path $buildRoot 'tests.json')
if($tests.status -cne 'PASS_LUAJIT_NOT_LIVE' -or $tests.build_sha256 -cne (Hash $manifestPath) -or $tests.cases -lt 19 -or $tests.native_writes -ne 0 -or $tests.automatic_callbacks -ne 0){throw 'Matching LuaJIT tests required'}
Match (Join-Path $PSScriptRoot 'test.py') $tests.tester_sha256
if(!$Fixture){
 foreach($p in $m.source_pins.PSObject.Properties){Match (Bound (Join-Path $workspace $p.Name) $workspace) $p.Value}
 $proofs=@(Get-ChildItem -LiteralPath $fixtureRoot -Filter results.json -Recurse -File|ForEach-Object {ReadJson $_.FullName}|Where-Object {$_.status -ceq 'PASS_WORKSPACE_FIXTURES_NOT_LIVE' -and $_.build_sha256 -ceq (Hash $manifestPath) -and $_.installer_sha256 -ceq (Hash $PSCommandPath) -and $_.tester_sha256 -ceq (Hash (Join-Path $PSScriptRoot 'test_deploy.py')) -and $_.cases -ge 12})
 if($proofs.Count -lt 1){throw 'Matching deployment fixtures required'}
}
$protected=Snapshot
if($Mode -eq 'Validate'){@{status='VALIDATED_S23_CAPTURE';additions=2;replacements=0;protected_files=$protected.Count;working_files_verified=$verified;build_sha256=Hash $manifestPath}|ConvertTo-Json;return}
if(!$recovery -or (Test-Path -LiteralPath $recovery)){throw 'New recovery directory required'}
Closed;New-Item -ItemType Directory -Path $recovery -ErrorAction Stop|Out-Null
foreach($p in $m.files.PSObject.Properties){CopyExact (Join-Path $buildRoot $p.Name) (Join-Path $recovery $p.Name) $p.Value}
WriteJson (Join-Path $recovery 'transaction.json') @{status='S23_CAPTURE_ADD_ONLY';game_root=$game;save_root=$saves;mod_relative=$modRelative;files=$m.files;build_sha256=Hash $manifestPath;installer_sha256=Hash $PSCommandPath;protected=$protected;utc=[DateTime]::UtcNow.ToString('o')}
[IO.File]::WriteAllText((Join-Path $recovery 'transaction.sha256'),(Hash (Join-Path $recovery 'transaction.json')),[Text.UTF8Encoding]::new($false))
try{
 Closed;NoLink $targetDir;New-Item -ItemType Directory -Path $targetDir -ErrorAction Stop|Out-Null
 $count=0
 foreach($p in $m.files.PSObject.Properties){
  Closed;CopyExact (Join-Path $recovery $p.Name) (Bound (Join-Path $targetDir $p.Name) $game) $p.Value;$count++
  if($FailAfterFirst -and $count -eq 1){throw 'Injected fixture failure after first copy'}
 }
 $same=Same $protected
 WriteJson (Join-Path $recovery 'install_receipt.json') @{status='INSTALLED_S23_READ_ONLY_CAPTURE';utc=[DateTime]::UtcNow.ToString('o');additions=2;replacements=0;files=$m.files;protected_files=$same;protected_save_files=@($protected.Keys|Where-Object {$_ -like 'save/*'}).Count;protected_cache_files=@($protected.Keys|Where-Object {$_ -like 'game/r6/cache/*'}).Count;working_files_verified=(WorkingPackage);save_changes=$false;build_sha256=Hash $manifestPath}
 Write-Output "INSTALLED read-only capture: $recovery"
}catch{
 $errorText=$_.Exception.Message
 WriteJson (Join-Path $recovery 'failure.json') @{status='S23_CAPTURE_INSTALL_FAILED';error=$errorText;recover_with='ValidateRollback, then Rollback using this exact transaction.'}
 throw $errorText
}
