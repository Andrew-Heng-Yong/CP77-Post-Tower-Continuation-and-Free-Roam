param([Parameter(Mandatory)][string]$Output,[Parameter(Mandatory)][string]$CameraBuild)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
. (Join-Path $PSScriptRoot 'scope.ps1')
function NoLink([string]$p){$cursor=[IO.Path]::GetFullPath($p);while($cursor){if(Test-Path -LiteralPath $cursor){if(((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'Reparse path refused'}};$parent=[IO.Directory]::GetParent($cursor);if(!$parent){break};$cursor=$parent.FullName}}
function Bound([string]$p,[string]$base){$p=[IO.Path]::GetFullPath($p);$base=[IO.Path]::GetFullPath($base);if(!$p.StartsWith($base+'\',[StringComparison]::OrdinalIgnoreCase)){throw "Outside build scope: $p"};NoLink $p;$p}
function Hash([string]$p){NoLink $p;(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function Json([string]$p,$v){if(Test-Path -LiteralPath $p){throw 'Pinned output exists'};[IO.File]::WriteAllText($p,($v|ConvertTo-Json -Depth 35),[Text.UTF8Encoding]::new($false))}
$out=Bound $Output (Join-Path $ws 'prealpha/postending_pa5/build')
if(Test-Path -LiteralPath $out){throw 'Fresh PA5 build directory required'}
$camera=Bound $CameraBuild (Join-Path $ws 'prealpha/postending_pa5/camera/build')
$cameraReport=Get-Content -LiteralPath (Join-Path $camera 'build.json') -Raw|ConvertFrom-Json
$cameraTests=Get-Content -LiteralPath (Join-Path $camera 'tests.json') -Raw|ConvertFrom-Json
$cameraCompile=Get-Content -LiteralPath (Join-Path $camera 'compile.json') -Raw|ConvertFrom-Json
$cameraHash=Hash (Join-Path $camera 'build.json');$cameraCompileHash=Hash (Join-Path $camera 'compile.json')
if($cameraReport.status -cne 'CAMERA_PA5_BUILT_NOT_LIVE' -or $cameraTests.status -cne 'PASS_OFFLINE_NOT_LIVE' -or $cameraCompile.status -cne 'PASS_COMPONENT_FULL_COMPILE_AND_READBACK_NOT_LIVE' -or
 $cameraTests.build_sha256 -cne $cameraHash -or $cameraCompile.build_sha256 -cne $cameraHash -or $cameraTests.compile_sha256 -cne $cameraCompileHash -or !$cameraReport.native_event_exact){throw 'Unverified native camera component'}
$cameraExpected=@($addPaths|Where-Object {$_ -notmatch 'GigDiagnostics'})
if(@($cameraReport.package_files).Count -ne 3 -or @(Compare-Object $cameraExpected @($cameraReport.package_files|ForEach-Object relative) -CaseSensitive).Count){throw 'Unexpected camera component file set'}
foreach($f in $cameraReport.package_files){if((Hash (Join-Path $camera ('package/'+$f.relative))) -cne $f.sha256){throw 'Camera tested package drift'}}
$base=Join-Path $ws 'prealpha/camera_pa4/build/pa4_02'
if((Hash (Join-Path $base 'build.json')) -cne $baselineSHA){throw 'Pinned PA4 report drift'}
$old=Get-Content -LiteralPath (Join-Path $base 'build.json') -Raw|ConvertFrom-Json
$expected=@($old.package_files|ForEach-Object {$_.relative})
if($expected.Count -ne 53 -or @($expected|Sort-Object -Unique).Count -ne 53){throw 'Pinned baseline count drift'}
$actual=@(Get-ChildItem -LiteralPath $old.package_root -Recurse -Force -File|ForEach-Object {NoLink $_.FullName;[IO.Path]::GetRelativePath($old.package_root,$_.FullName).Replace('\','/')})
if(@(Compare-Object $actual $expected -CaseSensitive).Count){throw 'Pinned baseline file set drift'}
foreach($f in $old.package_files){if((Hash (Join-Path $old.package_root $f.relative)) -cne $f.sha256){throw "Pinned baseline bytes drift: $($f.relative)"}}
# The consolidated XL has a deliberately uniform EP1-root injection interface.
# Refuse unfamiliar shapes instead of guessing a CRC for an arbitrary parent.
$xl=Get-Content -LiteralPath (Join-Path $old.package_root 'archive/pc/mod/TowerContinued_PreAlpha.archive.xl') -Raw
$rows=[regex]::Matches($xl,'(?m)^  - path: ([^\r\n]+)\r?\n    parent: ep1\\quest\\ep1\.quest\r?\n    input:\r?\n      node: \[1\]\r?\n      socket: Out\r?$')
if($rows.Count -ne 427 -or [regex]::Matches($xl,'(?m)^\s*parent:').Count -ne 427){throw 'Unfamiliar existing XL injection shape'}
function InjectionID([string]$path){$crc=65535;foreach($b in [Text.Encoding]::UTF8.GetBytes($path+':1')){$x=($crc -shr 8) -bxor $b;$x=$x -bxor ($x -shr 4);$crc=(($crc -shl 8) -bxor ($x -shl 12) -bxor ($x -shl 5) -bxor $x) -band 65535};return $crc}
$newID=InjectionID 'towercontinued\postending_pa5\camera\owner.questphase'
if($newID -ne $cameraReport.registration_id){throw 'Camera injection ID drift'}
foreach($row in $rows){if((InjectionID $row.Groups[1].Value) -eq $newID){throw 'Camera injection collision with existing package'}}
$liveXLRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\mod'
foreach($f in Get-ChildItem -LiteralPath $liveXLRoot -Filter '*.xl' -File){if($f.Name -cne 'TowerContinued_PreAlpha.archive.xl' -and (Get-Content -LiteralPath $f.FullName -Raw) -match '(?m)^\s*parent:\s*ep1\\quest\\ep1\.quest\s*$'){throw 'Additional live EP1-root injection needs collision audit'}}
$sources=@{
 'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_PreAlpha/init.lua'=(Join-Path $ws 'prealpha/postending_pa5/cet/init.lua');
 'r6/scripts/PTFR_PreAlpha/PA1/PreAlphaArrivalPA1.reds'=(Join-Path $ws 'prealpha/postending_pa5/scripts/PreAlphaArrivalPA1.reds');
 'r6/scripts/PTFR_PreAlpha/PA1/PreAlphaEntry.reds'=(Join-Path $ws 'prealpha/postending_pa5/scripts/PreAlphaEntry.reds');
 'r6/scripts/PTFR_PreAlpha/PTFR_RestorationBaseline/RestorationBaseline.reds'=(Join-Path $ws 'prealpha/postending_pa5/h10/source/RestorationBaseline.reds');
 'r6/scripts/PTFR_PreAlpha/PA5/GigDiagnosticsPA5.reds'=(Join-Path $ws 'prealpha/postending_pa5/gigs/GigDiagnosticsPA5.reds');
 'r6/scripts/PTFR_PreAlpha/PA5/GigDiagnosticsDataPA5.generated.reds'=(Join-Path $ws 'prealpha/postending_pa5/gigs/GigDiagnosticsDataPA5.generated.reds')
}
foreach($rel in $addPaths|Where-Object {$_ -notmatch 'GigDiagnostics'}){$sources[$rel]=Join-Path $camera ('package/'+$rel)}
if($sources.Count -ne 9){throw 'Expected exact nine-change package'}
foreach($rel in $allowed){[void](Hash $sources[$rel])}
New-Item -ItemType Directory -Path $out|Out-Null
$package=Join-Path $out 'package'
Copy-Item -LiteralPath $old.package_root -Destination $package -Recurse
foreach($rel in $allowed){$dest=Join-Path $package $rel;New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null;Copy-Item -LiteralPath $sources[$rel] -Destination $dest}
$files=@(Get-ChildItem -LiteralPath $package -Recurse -File|ForEach-Object {@{relative=[IO.Path]::GetRelativePath($package,$_.FullName).Replace('\','/');sha256=Hash $_.FullName;bytes=$_.Length}})
$changes=@()
foreach($f in $files){
 $prior=@($old.package_files|Where-Object {$_.relative -ceq $f.relative})
 if($prior.Count -eq 0){if($f.relative -cnotin $addPaths){throw 'Unexpected addition'};$changes+=@{relative=$f.relative;old_sha256=$null;new_sha256=$f.sha256;kind='add'}}
 elseif($prior.Count -eq 1 -and $prior[0].sha256 -cne $f.sha256){if($f.relative -cnotin $replacePaths){throw 'Out-of-scope change'};$changes+=@{relative=$f.relative;old_sha256=$prior[0].sha256;new_sha256=$f.sha256;kind='replace'}}
}
if($files.Count -ne 58 -or $changes.Count -ne 9){throw 'Unexpected package delta'}
foreach($r in @('archive/pc/mod/TowerContinued_PreAlpha.archive','archive/pc/mod/TowerContinued_PreAlpha.archive.xl')){if((Hash (Join-Path $package $r)) -cne (Hash (Join-Path $old.package_root $r))){throw 'Main archive/XL must remain unchanged'}}
Json (Join-Path $out 'build.json') @{status='BUILT_BASELINE_IDENTICAL_COMPILE_PENDING';output=$out;package_root=$package;package_files=$files;changes=$changes;archive_unchanged=$true;unchanged_files=49;prior_build=$base;prior_build_sha256=$baselineSHA;camera_build=$camera;camera_evidence=@{build_sha256=$cameraHash;tests_sha256=Hash (Join-Path $camera 'tests.json');compile_sha256=$cameraCompileHash;existing_injections_checked=427;new_registration_id=$newID;collision_free=$true};source_files=@($sources.Keys|ForEach-Object {@{relative=$_;source=$sources[$_];sha256=Hash $sources[$_]}});preserved_gd2=@{relative=$gd2Relative;sha256=$gd2SHA};game_save_cache_writes=$false}
Write-Output ('BUILD_PASS='+$out)
