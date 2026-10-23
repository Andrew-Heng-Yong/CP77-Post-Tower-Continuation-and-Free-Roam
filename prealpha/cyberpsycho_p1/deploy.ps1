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
$relatives=@('archive/pc/mod/TowerContinued_Cyberpsycho_P1.archive','archive/pc/mod/TowerContinued_Cyberpsycho_P1.archive.xl','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_CyberpsychoP1/init.lua','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_CyberpsychoP1/data.json')
$cetRel='bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_CyberpsychoP1'
$lib=Join-Path $workspace 'prealpha/graphics_gd2/tools/deploy.ps1'
if((Get-FileHash $lib).Hash -cne '1D1D204D792D65FF30757B455E57826787E395A1DF0C1D5352A60D0757EC3307'){throw 'Safety helper changed'}
$text=Get-Content $lib -Raw;$start=$text.IndexOf('function Full(');$end=$text.IndexOf('$game=Full $GameRoot;')
if($start -lt 0 -or $end -le $start){throw 'Helper boundary changed'}
$defs=$text.Substring($start,$end-$start)
if([regex]::Matches($defs,[regex]::Escape('if($rel -ceq $relative)')).Count -ne 1){throw 'Snapshot boundary changed'}
. ([scriptblock]::Create($defs.Replace('if($rel -ceq $relative)','if($rel -cin $relatives)')))
$prior=Join-Path $workspace 'prealpha/ncpd_repair_n21/deploy.ps1';Match $prior 'BF2707160A098226BF09AEA32611D5F7B91412BFE1B4C057F0B6420F95CF49B4'
$text=Get-Content $prior -Raw;$start=$text.IndexOf('function OriginalPackage {');$end=$text.IndexOf('function Scope(')
if($start -lt 0 -or $end -le $start){throw 'Baseline helper boundary changed'}
. ([scriptblock]::Create($text.Substring($start,$end-$start).Replace('function OriginalPackage {','function PriorPackage {')))
function OriginalPackage {
 $count=PriorPackage
 if(!$Fixture){
  $files=@{
   'archive/pc/mod/TowerContinued_NCPD_N21.archive'='17DFA1342F28A88CE18C058185BB0246DD152BBC7BC1D38C5FE8A01590C93FDB'
   'archive/pc/mod/TowerContinued_NCPD_N21.archive.xl'='17A19445CEFA4CDEA031970E39896CC5C029AF3F735674C5DB5C83B827424FC6'
   'r6/scripts/TowerContinued_NCPD_N21/ScannerRepairN21.reds'='8F4DDBF69C7BA62984B6236EEF9461EF16AC4D639D1FB50CDFE0C3FCB121BEB3'
   'archive/pc/mod/TowerContinued_Airdrops_D1.archive'='74B291C8FACA6D03AFBC98D2DD9062D1CCCFE5EB9AD58B1ED47B3CB3978F2F45'
   'archive/pc/mod/TowerContinued_Airdrops_D1.archive.xl'='C30EFAF8109EC637B4F9AB7EC6191749C25483F6C4516579BF2C80FC6480ECA3'
  };foreach($p in $files.Keys){Match (Join-Path $game $p) $files[$p];$count++}
 };return $count
}
function Scope($files){
 if(@($files).Count -ne 4 -or @($files|Select-Object -ExpandProperty relative -Unique).Count -ne 4){throw 'Exactly four unique additions required'}
 for($i=0;$i -lt 4;$i++){if($files[$i].relative -cne $relatives[$i] -or $files[$i].sha256 -cnotmatch '^[A-F0-9]{64}$'){throw 'Addition scope mismatch'}}
}
$game=Full $GameRoot;$saves=Full $SaveRoot;NoLink $game;NoLink $saves
if(!(Test-Path $game -PathType Container) -or !(Test-Path $saves -PathType Container)){throw 'Existing game/save roots required'}
if($Fixture){[void](Bound $game $fixtureRoot);[void](Bound $saves $fixtureRoot);$buildBound=$fixtureRoot;$recoveryBound=$fixtureRoot}
else{if($game -cne 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077' -or $saves -cne 'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077' -or $FailAfterFirst){throw 'Unapproved roots/options'};$buildBound=Join-Path $PSScriptRoot 'build';$recoveryBound=Join-Path $workspace 'recovery'}
$recovery=if($RecoveryRoot){Bound $RecoveryRoot $recoveryBound}else{''};Closed;$original=OriginalPackage
if($Mode -in @('ValidateRollback','Rollback')){
 if(!$recovery -or (Test-Path (Join-Path $recovery 'rollback_receipt.json'))){throw 'Unused exact recovery directory required'}
 $txnPath=Join-Path $recovery 'transaction.json';Match $txnPath (Get-Content (Join-Path $recovery 'transaction.sha256') -Raw);$txn=ReadJson $txnPath
 if($txn.status -cne 'P1_ADD_ONLY' -or $txn.game_root -cne $game -or $txn.save_root -cne $saves){throw 'Recovery identity mismatch'};Scope $txn.files
 foreach($f in $txn.files){$name=[IO.Path]::GetFileName($f.relative);Match (Join-Path $recovery $name) $f.sha256;$target=Bound (Join-Path $game $f.relative) $game;$removed=Join-Path $recovery ('removed_'+$name);NoLink $removed;if(Test-Path $removed){throw 'Recovery target exists'};if(Test-Path $target){Match $target $f.sha256}}
 $protected=Snapshot
 if($Mode -eq 'ValidateRollback'){@{status='VALIDATED_P1_ROLLBACK';original_package_verified=$original;protected_files=$protected.Count}|ConvertTo-Json;return}
 $moved=0
 foreach($f in $txn.files){$target=Bound (Join-Path $game $f.relative) $game;if(Test-Path $target){Closed;Match $target $f.sha256;$removed=Join-Path $recovery ('removed_'+[IO.Path]::GetFileName($f.relative));[IO.File]::Move($target,$removed,$false);Match $removed $f.sha256;$moved++}}
 $count=Same $protected;WriteJson (Join-Path $recovery 'rollback_receipt.json') @{status='ROLLED_BACK_P1';utc=[DateTime]::UtcNow.ToString('o');moved_recoverably=$moved;protected_files=$count;original_package_verified=(OriginalPackage);save_changes=$false};Write-Output "ROLLED_BACK: $recovery";return
}
if(!$Build){throw 'Build directory required'}
$buildRoot=Bound $Build $buildBound;$manifestPath=Join-Path $buildRoot 'build.json';$m=ReadJson $manifestPath
if($m.status -cne 'BUILT_P1_LIVE_PENDING' -or @($m.resources.PSObject.Properties).Count -ne 20 -or @($m.boots).Count -ne 20 -or !$m.packed_readback -or !$m.native_scenes_unchanged -or @($m.official_overrides).Count -ne 0 -or $m.runtime_scripts_added -ne 0){throw 'Manifest scope mismatch'};Scope $m.files
foreach($f in $m.files){Match (Join-Path $buildRoot ([IO.Path]::GetFileName($f.relative))) $f.sha256;$target=Bound (Join-Path $game $f.relative) $game;if(Test-Path $target){throw 'P1 already present; refusing overwrite'}}
$cet=Bound (Join-Path $game $cetRel) $game
if(Test-Path $cet){throw 'P1 helper folder already exists; preserve it'}
foreach($p in @('archive/pc/mod','bin/x64/plugins/cyber_engine_tweaks/mods')){if(!(Test-Path (Bound (Join-Path $game $p) $game) -PathType Container)){throw 'Existing mod directories required'}}
$tests=ReadJson (Join-Path $buildRoot 'tests.json');if($tests.status -cne 'PASS_NOT_LIVE' -or $tests.build_sha256 -cne (Hash $manifestPath)){throw 'Matching tests required'};Match (Join-Path $PSScriptRoot 'test.py') $tests.tester_sha256
$audit=ReadJson (Join-Path $buildRoot 'resource_check.json')
if($audit.status -cne 'PASS_NOT_LIVE' -or $audit.build_sha256 -cne (Hash $manifestPath) -or @($audit.overrides).Count -ne 0 -or @($audit.official).Count -ne $audit.native_count -or $audit.native_count -lt 50 -or !$audit.modlist_absent -or @($audit.official_overrides).Count){throw 'Matching resource audit required'};Match (Join-Path $PSScriptRoot 'resource_check.ps1') $audit.checker_sha256
if(!$Fixture){
 if(Test-Path (Join-Path $game 'archive/pc/mod/modlist.txt')){throw 'Load order appeared'}
 $proofs=@(Get-ChildItem $fixtureRoot -Filter results.json -File -Recurse|ForEach-Object {ReadJson $_.FullName}|Where-Object {$_.status -ceq 'PASS_WORKSPACE_FIXTURES_NOT_LIVE' -and $_.build_sha256 -ceq (Hash $manifestPath) -and $_.installer_sha256 -ceq (Hash $PSCommandPath) -and $_.tester_sha256 -ceq (Hash (Join-Path $PSScriptRoot 'test_deploy.py')) -and $_.cases -ge 31 -and $_.checks -ge 41})
 if(!$proofs.Count){throw 'Matching installer fixtures required'}
 foreach($p in $m.source_pins.PSObject.Properties){Match (Bound (Join-Path $workspace $p.Name) $workspace) $p.Value}
 $actual=@(Get-ChildItem (Join-Path $game 'archive/pc/mod') -File -Filter '*.archive');if($actual.Count -ne @($audit.installed_archives).Count){throw 'Archive set changed'}
 foreach($a in $audit.installed_archives){Match (Bound (Join-Path $game ('archive/pc/mod/'+$a.name)) $game) $a.sha256}
 foreach($p in $m.installed_injections|Sort-Object source -Unique){Match (Bound (Join-Path $game ('archive/pc/mod/'+$p.source)) $game) $p.source_sha256}
}
$protected=Snapshot
if($Mode -eq 'Validate'){@{status='VALIDATED_P1_ADD_ONLY';additions=4;original_package_verified=$original;protected_files=$protected.Count;build_sha256=Hash $manifestPath}|ConvertTo-Json;return}
if(!$recovery -or (Test-Path $recovery)){throw 'New recovery directory required'};Closed
New-Item -ItemType Directory -Path $recovery -ErrorAction Stop|Out-Null
foreach($f in $m.files){$name=[IO.Path]::GetFileName($f.relative);CopyExact (Join-Path $buildRoot $name) (Join-Path $recovery $name) $f.sha256}
WriteJson (Join-Path $recovery 'transaction.json') @{status='P1_ADD_ONLY';game_root=$game;save_root=$saves;files=$m.files;build=$buildRoot;build_sha256=Hash $manifestPath;utc=[DateTime]::UtcNow.ToString('o');protected=$protected;installer_sha256=Hash $PSCommandPath}
[IO.File]::WriteAllText((Join-Path $recovery 'transaction.sha256'),(Hash (Join-Path $recovery 'transaction.json')),[Text.UTF8Encoding]::new($false))
try{
 Closed;NoLink $cet;New-Item -ItemType Directory -Path $cet -ErrorAction Stop|Out-Null
 $copied=0;foreach($f in $m.files){Closed;CopyExact (Join-Path $recovery ([IO.Path]::GetFileName($f.relative))) (Bound (Join-Path $game $f.relative) $game) $f.sha256;$copied++;if($FailAfterFirst -and $copied -eq 1){throw 'Injected failure after first addition'}}
 $count=Same $protected
 WriteJson (Join-Path $recovery 'install_receipt.json') @{status='INSTALLED_P1_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');additions=4;replacements=0;installed_files=$m.files;original_package_verified=(OriginalPackage);protected_files=$count;protected_save_files=@($protected.Keys|Where-Object{$_ -like 'save/*'}).Count;protected_cache_files=@($protected.Keys|Where-Object{$_ -like 'game/r6/cache/*'}).Count;settings_changed=$false;build_sha256=Hash $manifestPath;recovery=$recovery}
 Write-Output "INSTALLED: $recovery"
}catch{WriteJson (Join-Path $recovery 'failure.json') @{status='INSTALL_INTERRUPTED';message=$_.Exception.Message;instruction='Do not launch. ValidateRollback then Rollback with this recovery directory.'};throw}
