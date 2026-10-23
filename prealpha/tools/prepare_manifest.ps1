param([Parameter(Mandatory)][string]$Build)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$saves='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077'
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function Rel([string]$root,[string]$p){[IO.Path]::GetRelativePath($root,$p).Replace('\','/')}
$built=Get-Content (Join-Path $Build 'build.json') -Raw|ConvertFrom-Json
$compiled=Get-Content (Join-Path $Build 'compile.json') -Raw|ConvertFrom-Json
if($built.status -cne 'BUILT_PACKED_READBACK_PASS_COMPILE_PENDING' -or $compiled.status -cne 'PASS_COMPILE_AND_READBACK_NOT_LIVE'){throw 'Package verification absent'}
if($built.package_root -cne [IO.Path]::GetFullPath((Join-Path $Build 'package')) -or (Hash (Join-Path $Build 'build.json')) -cne $compiled.build_sha256){throw 'Compiled build/package identity changed'}
$actualPackage=@(Get-ChildItem -LiteralPath $built.package_root -File -Recurse|ForEach-Object {Rel $built.package_root $_.FullName})
$expectedPackage=@($built.package_files|ForEach-Object {$_.relative})
if($actualPackage.Count -eq 0 -or @($expectedPackage|Sort-Object -Unique).Count -ne $expectedPackage.Count -or @(Compare-Object ($actualPackage|Sort-Object) ($expectedPackage|Sort-Object) -CaseSensitive).Count){throw 'Readback-verified package file set changed'}
foreach($f in $built.package_files){if((Hash (Join-Path $built.package_root $f.relative)) -cne $f.sha256){throw "Readback-verified package bytes changed: $($f.relative)"}}
foreach($f in $compiled.package_scripts){if((Hash $f.path) -cne $f.sha256){throw 'Compiled package source changed'}}
foreach($f in $built.inputs){if((Hash $f.path) -cne $f.sha256){throw 'Source input changed during build'}}
if((Hash (Join-Path $saves 'ManualSave-10/sav.dat')) -cne '62742BF7E77451D5498AB724EEECD10CD2E35AFEF3442361D67A29BBDD486B3B'){throw 'Selected original fixture changed'}
$units=[Collections.Generic.List[object]]::new()
function AddUnit([string]$kind,[string]$root,$item){
 $files=if($item.PSIsContainer){@(Get-ChildItem -LiteralPath $item.FullName -File -Recurse -Force|ForEach-Object {@{path=(Rel $item.FullName $_.FullName);sha256=(Hash $_.FullName)}})}else{@(@{path='.';sha256=(Hash $item.FullName)})}
 $units.Add(@{kind=$kind;relative=(Rel $root $item.FullName);files=@($files)})
}
foreach($f in Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/mod') -File|Where-Object {$_.Name -like 'TowerContinued*' -and $_.Name -match '\.(archive|xl)$'}){AddUnit 'game' $game $f}
foreach($path in @('r6/scripts','bin/x64/plugins/cyber_engine_tweaks/mods')){
 foreach($d in Get-ChildItem -LiteralPath (Join-Path $game $path) -Directory|Where-Object {$_.Name -like 'PTFR_*'}){AddUnit 'game' $game $d}
}
foreach($f in Get-ChildItem -LiteralPath (Join-Path $game 'r6/tweaks') -File|Where-Object {$_.Name -like 'TowerContinued*.yaml'}){AddUnit 'game' $game $f}
foreach($d in Get-ChildItem -LiteralPath $saves -Directory -Force){
 if($d.Name -ceq 'ManualSave-10'){continue}
 if($d.Name -cnotmatch '^(ManualSave|AutoSave|EndGameSave|PointOfNoReturnSave|QuickSave)-\d+$'){throw "Unknown save directory; review before cleanup $($d.Name)"}
 AddUnit 'save' $saves $d
}
$protected=[Collections.Generic.List[object]]::new()
$inv=Get-Content (Join-Path $ws 'research/pre_alpha_clean/inventory/files.json') -Raw|ConvertFrom-Json
foreach($f in $inv.files|Where-Object category -eq 'preserve_third_party'){
 if((Hash (Join-Path $game $f.relative)) -cne $f.sha256){throw "Third-party drift $($f.relative)"}
 $protected.Add(@{kind='game';relative=$f.relative;sha256=$f.sha256})
}
foreach($path in @('r6/cache','red4ext/plugins')){
 foreach($f in Get-ChildItem -LiteralPath (Join-Path $game $path) -File -Recurse -Force|Where-Object {$_.Extension -notin @('.log')}){
  $rel=Rel $game $f.FullName
  if(!@($protected|Where-Object relative -ceq $rel).Count){$protected.Add(@{kind='game';relative=$rel;sha256=(Hash $f.FullName)})}
 }
}
foreach($f in Get-ChildItem -LiteralPath (Join-Path $saves 'ManualSave-10') -File -Recurse -Force){$protected.Add(@{kind='save';relative=(Rel $saves $f.FullName);sha256=(Hash $f.FullName)})}
$package=@(Get-ChildItem -LiteralPath $built.package_root -File -Recurse|ForEach-Object {@{relative=(Rel $built.package_root $_.FullName);sha256=(Hash $_.FullName)}})
$m=[ordered]@{status='PREALPHA_PACKAGE_VERIFIED';utc=[DateTime]::UtcNow.ToString('o');package_root=$built.package_root;keep_save='ManualSave-10';package=$package;units=$units;protected=$protected;build_sha256=(Hash (Join-Path $Build 'build.json'));compile_sha256=(Hash (Join-Path $Build 'compile.json'));runtime_testing='PENDING';save_byte_edits=$false;cleanup_is_recoverable=$true}
$manifest=Join-Path $Build 'deployment_manifest.json'
[IO.File]::WriteAllText($manifest,($m|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))
@{manifest=$manifest;package_files=$package.Count;game_moves=@($units|Where-Object kind -eq 'game').Count;save_moves=@($units|Where-Object kind -eq 'save').Count;protected=$protected.Count}|ConvertTo-Json
