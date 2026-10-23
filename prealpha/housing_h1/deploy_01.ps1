param(
 [ValidateSet('Validate','Install','ValidateRollback','Rollback')][string]$Mode='Validate',
 [string]$Build='',[string]$RecoveryRoot='',
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$SaveRoot='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077',
 [switch]$Fixture,[int]$FailAfterWrite=0
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')).TrimEnd('\')
$fixtureRoot=Join-Path $PSScriptRoot 'fixtures'
$replacements=@{
 'r6/scripts/PTFR_PreAlpha/PA1/PreAlphaEntry.reds'='386A6496EAF1ACB485FB2D4CF8F09BCE6AA2E85538D0598E548ABA83B9EBFAC2'
 'r6/scripts/PTFR_PreAlpha/PTFR_RestorationBaseline/RestorationBaseline.reds'='8E29C4573988049564808BDB7DFE815351793C8621300E8858AA9C827EACF3ED'
}
$lib=Join-Path $workspace 'prealpha/graphics_gd2/tools/deploy.ps1'
if((Get-FileHash -LiteralPath $lib).Hash -cne '1D1D204D792D65FF30757B455E57826787E395A1DF0C1D5352A60D0757EC3307'){throw 'Safety helper changed'}
$text=Get-Content -LiteralPath $lib -Raw
$start=$text.IndexOf('function Full(');$end=$text.IndexOf('$game=Full $GameRoot;')
if($start -lt 0 -or $end -le $start){throw 'Safety helper boundary changed'}
$defs=$text.Substring($start,$end-$start)
if([regex]::Matches($defs,[regex]::Escape('if($rel -ceq $relative)')).Count -ne 1){throw 'Snapshot helper boundary changed'}
$defs=$defs.Replace('if($rel -ceq $relative)','if($rel -cin $relatives)')
. ([scriptblock]::Create($defs))
function At($root,$rel){
 if($rel -isnot [string] -or $rel -notmatch '^[a-zA-Z0-9_./-]+$' -or $rel -match '(^|/)\.\.?(/|$)' -or [IO.Path]::IsPathRooted($rel)){throw 'Invalid relative path'}
 Bound (Join-Path $root $rel) $root
}
function Scope($files){
 if(@($files).Count -lt 5 -or @($files).Count -gt 12){throw 'Unexpected housing package size'}
 $seen=@{}
 foreach($f in $files){
  if($seen.ContainsKey($f.relative) -or $f.sha256 -cnotmatch '^[A-F0-9]{64}$'){throw 'Duplicate or invalid file'}
  $seen[$f.relative]=$true
  if($replacements.ContainsKey($f.relative)){
   if($f.action -cne 'replace' -or $f.before_sha256 -cne $replacements[$f.relative]){throw 'Replacement must match reviewed installed source'}
  }else{
   if($f.action -cne 'add' -or $f.before_sha256 -cne '' -or $f.relative -cnotmatch '^(archive/pc/mod/00000000_TowerContinued_Housing_H1\.archive(?:\.xl)?|r6/scripts/TowerContinued_Housing_H1/[A-Za-z0-9_]+\.reds)$'){throw 'Addition outside housing scope'}
  }
 }
 foreach($p in @($replacements.Keys)+@('archive/pc/mod/00000000_TowerContinued_Housing_H1.archive','archive/pc/mod/00000000_TowerContinued_Housing_H1.archive.xl','r6/scripts/TowerContinued_Housing_H1/HousingState.reds')){if(!$seen.ContainsKey($p)){throw "Required file absent: $p"}}
}
function Pins($map){
 if($null -eq $map -or @($map.PSObject.Properties).Count -lt 1){throw 'Missing input pins'}
 foreach($p in $map.PSObject.Properties){Match $p.Name $p.Value}
}
function EnsureParent($target,$root){
 $parent=Split-Path -Parent $target
 [void](Bound $parent $root)
 if(!(Test-Path -LiteralPath $parent)){New-Item -ItemType Directory -Path $parent -Force | Out-Null}
 NoLink $parent
}
function ReplaceExact($from,$target,$before,$after,$temp){
 Match $from $after;Match $target $before;NoLink $temp
 if(Test-Path -LiteralPath $temp){throw 'Pending replacement already exists'}
 [IO.File]::Copy($from,$temp,$false);Match $temp $after
 Closed;Match $target $before
 [IO.File]::Replace($temp,$target,[System.Management.Automation.Language.NullString]::Value);Match $target $after
}
$game=Full $GameRoot;$saves=Full $SaveRoot;NoLink $game;NoLink $saves
if(!(Test-Path -LiteralPath $game -PathType Container) -or !(Test-Path -LiteralPath $saves -PathType Container)){throw 'Existing roots required'}
if($Fixture){[void](Bound $game $fixtureRoot);[void](Bound $saves $fixtureRoot);$buildBound=$fixtureRoot;$recoveryBound=$fixtureRoot}
else{
 if($game -cne 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077' -or $saves -cne 'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077' -or $FailAfterWrite -ne 0){throw 'Unapproved live roots/options'}
 $buildBound=Join-Path $PSScriptRoot 'build';$recoveryBound=Join-Path $workspace 'recovery'
}
$recovery=if($RecoveryRoot){Bound $RecoveryRoot $recoveryBound}else{''}
Closed
if($Mode -in @('ValidateRollback','Rollback')){
 if(!$recovery){throw 'Exact recovery directory required'}
 if(Test-Path -LiteralPath (Join-Path $recovery 'rollback_receipt.json')){throw 'Already rolled back'}
 $txnPath=Join-Path $recovery 'transaction.json'
 Match $txnPath (Get-Content -LiteralPath (Join-Path $recovery 'transaction.sha256') -Raw)
 $txn=ReadJson $txnPath
 if($txn.status -cne 'H1_SCOPED_TRANSACTION' -or $txn.game_root -cne $game -or $txn.save_root -cne $saves -or $txn.installer_sha256 -cne (Hash $PSCommandPath)){throw 'Recovery identity mismatch'}
 Scope $txn.files;$relatives=@($txn.files.relative)
 foreach($f in $txn.files){
  Match (At (Join-Path $recovery 'new') $f.relative) $f.sha256
  $target=At $game $f.relative
  if($f.action -ceq 'replace'){
   Match (At (Join-Path $recovery 'original') $f.relative) $f.before_sha256
   if(!(Test-Path -LiteralPath $target) -or (Hash $target) -cnotin @($f.sha256,$f.before_sha256)){throw 'Replaced target changed after installation'}
  }elseif(Test-Path -LiteralPath $target){Match $target $f.sha256}
  if(Test-Path -LiteralPath ($target+'.ptfrh1.pending')){throw 'Pending file requires inspection before rollback'}
 }
 $protected=Snapshot
 if($Mode -eq 'ValidateRollback'){@{status='VALIDATED_H1_ROLLBACK';protected_files=$protected.Count;files=@($txn.files).Count}|ConvertTo-Json;return}
 foreach($f in $txn.files){
  Closed;$target=At $game $f.relative
  if($f.action -ceq 'replace'){
   $actual=Hash $target
   if($actual -cnotin @($f.sha256,$f.before_sha256)){throw 'Replacement changed during rollback'}
   if($actual -ceq $f.sha256){ReplaceExact (At (Join-Path $recovery 'original') $f.relative) $target $f.sha256 $f.before_sha256 ($target+'.ptfrh1.pending')}
  }elseif(Test-Path -LiteralPath $target){
   Match $target $f.sha256;$removed=At (Join-Path $recovery 'removed') $f.relative
   EnsureParent $removed $recovery
   if(Test-Path -LiteralPath $removed){throw 'Rollback destination exists'}
   [IO.File]::Move($target,$removed,$false);Match $removed $f.sha256
  }
 }
 foreach($f in $txn.files){
  $target=At $game $f.relative
  if($f.action -ceq 'replace'){Match $target $f.before_sha256}elseif(Test-Path -LiteralPath $target){throw 'Added file remains after rollback'}
 }
 $count=Same $protected
 WriteJson (Join-Path $recovery 'rollback_receipt.json') @{status='ROLLED_BACK_H1';utc=[DateTime]::UtcNow.ToString('o');protected_files=$count;save_changes=$false;file_rollback_is_not_save_rollback=$true}
 Write-Output "ROLLED_BACK: $recovery";return
}
if(!$Build){throw 'Build required'}
$buildRoot=Bound $Build $buildBound;$manifestPath=Join-Path $buildRoot 'build.json';$manifestDigest=Hash $manifestPath;$m=ReadJson $manifestPath
if($m.status -cne 'BUILT_H1_LIVE_PENDING' -or $m.installer_sha256 -cne (Hash $PSCommandPath)){throw 'Unreviewed build/installer'}
if(!$Fixture -and ('synthetic_fixture' -in $m.PSObject.Properties.Name)){throw 'Synthetic build cannot install live'}
Scope $m.files;$relatives=@($m.files.relative)
foreach($f in $m.files){
 Match (At (Join-Path $buildRoot 'package') $f.relative) $f.sha256
 $target=At $game $f.relative
 if($f.action -ceq 'replace'){Match $target $f.before_sha256}elseif(Test-Path -LiteralPath $target){throw 'Addition already exists'}
 if(Test-Path -LiteralPath ($target+'.ptfrh1.pending')){throw 'Pending replacement exists'}
}
if($null -eq $m.source_pins -or @($m.source_pins.PSObject.Properties).Count -lt 1){throw 'Source pins required'}
foreach($p in $m.source_pins.PSObject.Properties){Match (At $workspace $p.Name) $p.Value}
$proofHashes=@{}
foreach($proofName in @('tests.json','compile_result.json','resource_check.json','compatibility_check.json','deployment_tests.json')){
 $proofPath=Join-Path $buildRoot $proofName;$proofHashes[$proofPath]=Hash $proofPath
 $proof=ReadJson $proofPath
 if($proof.status -cnotlike 'PASS*' -or $proof.build_sha256 -cne (Hash $manifestPath)){throw "Missing matching proof: $proofName"}
}
$compiler=ReadJson (Join-Path $buildRoot 'compile_result.json')
if($compiler.full_scc -isnot [bool] -or !$compiler.full_scc -or $compiler.live_files_unchanged -isnot [bool] -or !$compiler.live_files_unchanged){throw 'Complete compilation required'}
$stagedScripts=@($m.files|Where-Object {$_.relative -clike 'r6/scripts/*.reds'})
if(@($compiler.overlay_pins.PSObject.Properties).Count -ne $stagedScripts.Count){throw 'Compiled overlay scope mismatch'}
foreach($f in $stagedScripts){
 $source=At (Join-Path $buildRoot 'package') $f.relative
 $proofPins=@($compiler.overlay_pins.PSObject.Properties|Where-Object {(Full $_.Name) -ieq $source})
 if($proofPins.Count -ne 1 -or $proofPins[0].Value -cne $f.sha256){throw 'Staged REDS is not the compiled overlay'}
}
$resource=ReadJson (Join-Path $buildRoot 'resource_check.json')
function EnvironmentUnchanged {
 Match $manifestPath $manifestDigest
 foreach($p in $proofHashes.Keys){Match $p $proofHashes[$p]}
 foreach($p in $m.source_pins.PSObject.Properties){Match (At $workspace $p.Name) $p.Value}
 foreach($f in $m.files){Match (At (Join-Path $buildRoot 'package') $f.relative) $f.sha256}
 Pins $compiler.dependencies;Pins $compiler.protected;Pins $compiler.compiler_inputs;Pins $compiler.overlay_pins
 Pins $resource.archive_pins;Pins $resource.xl_pins;Pins $resource.official_archive_pins
 $seenScripts=@(foreach($r in $compiler.script_roots){Get-ChildItem -LiteralPath $r -Filter '*.reds' -File -Recurse|ForEach-Object FullName})|Sort-Object -Unique
 if(($seenScripts -join '|') -ine (@($compiler.dependencies.PSObject.Properties.Name|Sort-Object)-join '|')){throw 'Installed script set changed since compile'}
 $seenArchives=@(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/mod') -File -Filter '*.archive'|ForEach-Object FullName|Sort-Object)
 if(($seenArchives -join '|') -ine (@($resource.archive_pins.PSObject.Properties.Name|Sort-Object)-join '|')){throw 'Installed archive set changed'}
 $seenXL=@(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/mod') -File -Filter '*.xl'|ForEach-Object FullName|Sort-Object)
 if(($seenXL -join '|') -ine (@($resource.xl_pins.PSObject.Properties.Name|Sort-Object)-join '|')){throw 'Installed XL set changed'}
}
EnvironmentUnchanged
$protected=Snapshot
if($Mode -eq 'Validate'){@{status='VALIDATED_H1';files=$relatives.Count;protected_files=$protected.Count;build_sha256=Hash $manifestPath}|ConvertTo-Json;return}
if(!$recovery -or (Test-Path -LiteralPath $recovery)){throw 'New recovery directory required'}
Closed;New-Item -ItemType Directory -Path $recovery | Out-Null
foreach($f in $m.files){
 $stage=At (Join-Path $recovery 'new') $f.relative;EnsureParent $stage $recovery
 CopyExact (At (Join-Path $buildRoot 'package') $f.relative) $stage $f.sha256
 if($f.action -ceq 'replace'){$old=At (Join-Path $recovery 'original') $f.relative;EnsureParent $old $recovery;CopyExact (At $game $f.relative) $old $f.before_sha256}
}
WriteJson (Join-Path $recovery 'transaction.json') @{status='H1_SCOPED_TRANSACTION';game_root=$game;save_root=$saves;files=$m.files;build_sha256=Hash $manifestPath;installer_sha256=Hash $PSCommandPath;protected=$protected;utc=[DateTime]::UtcNow.ToString('o')}
[IO.File]::WriteAllText((Join-Path $recovery 'transaction.sha256'),(Hash (Join-Path $recovery 'transaction.json')),[Text.UTF8Encoding]::new($false))
$written=0
try{
 EnvironmentUnchanged
 [void](Same $protected)
 foreach($f in $m.files){
  Closed;$target=At $game $f.relative;$stage=At (Join-Path $recovery 'new') $f.relative
  if($f.action -ceq 'replace'){ReplaceExact $stage $target $f.before_sha256 $f.sha256 ($target+'.ptfrh1.pending')}
  else{EnsureParent $target $game;CopyExact $stage $target $f.sha256}
  $written++;if($FailAfterWrite -gt 0 -and $written -eq $FailAfterWrite){throw 'Injected fixture interruption'}
 }
 foreach($f in $m.files){Match (At $game $f.relative) $f.sha256}
 $count=Same $protected
 WriteJson (Join-Path $recovery 'install_receipt.json') @{status='INSTALLED_H1_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');files=$m.files;build_sha256=Hash $manifestPath;protected_files=$count;protected_save_files=@($protected.Keys|Where-Object{$_ -like 'save/*'}).Count;protected_cache_files=@($protected.Keys|Where-Object{$_ -like 'game/r6/cache/*'}).Count;save_changes=$false;game_launched=$false;recovery=$recovery}
 Write-Output "INSTALLED: $recovery"
}catch{
 WriteJson (Join-Path $recovery 'failure.json') @{status='INSTALL_INTERRUPTED';message=$_.Exception.Message;written=$written;instruction='Do not launch. Inspect any pending file, then ValidateRollback/Rollback using this exact recovery directory.'}
 throw
}
