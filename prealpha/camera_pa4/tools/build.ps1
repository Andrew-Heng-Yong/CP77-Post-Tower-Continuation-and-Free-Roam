param([Parameter(Mandatory)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$out=[IO.Path]::GetFullPath($Output)
if(!$out.StartsWith($ws+'\prealpha\camera_pa4\build\',[StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $out)){throw 'Fresh PA4 build directory required'}
function NoReparse([string]$p){$cursor=[IO.Path]::GetFullPath($p);while($cursor){if(Test-Path -LiteralPath $cursor){if(((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'Reparse path refused'}};$parent=[IO.Directory]::GetParent($cursor);if($null -eq $parent){break};$cursor=$parent.FullName}}
function Hash([string]$p){NoReparse $p;(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function Json([string]$p,$v){[IO.File]::WriteAllText($p,($v|ConvertTo-Json -Depth 35),[Text.UTF8Encoding]::new($false))}
NoReparse $out
$base=Join-Path $ws 'prealpha/handoff_pa3/build/pa3_01'
$baselineHash='AAC05EBBED94A72B8B7AAD03CE9EC8033483691E574EE80D681287B9899228AC'
if((Hash (Join-Path $base 'build.json')) -cne $baselineHash){throw 'Pinned PA3 report drift'}
$old=Get-Content -LiteralPath (Join-Path $base 'build.json') -Raw|ConvertFrom-Json
$scriptRel='r6/scripts/PTFR_PreAlpha/PA1/PreAlphaArrivalPA1.reds'
$cetRel='bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_PreAlpha/init.lua'
$archiveRel='archive/pc/mod/TowerContinued_PreAlpha.archive'
$allowed=@($scriptRel,$cetRel)
$expected=@($old.package_files|ForEach-Object {$_.relative})
if($expected.Count -ne 53 -or @($expected|Sort-Object -Unique).Count -ne 53){throw 'Pinned package file count drift'}
$actual=@(Get-ChildItem -LiteralPath $old.package_root -Recurse -Force -File|ForEach-Object {NoReparse $_.FullName;[IO.Path]::GetRelativePath($old.package_root,$_.FullName).Replace('\','/')})
if(@(Compare-Object $actual $expected -CaseSensitive).Count){throw 'Pinned package file set drift'}
foreach($f in $old.package_files){if((Hash (Join-Path $old.package_root $f.relative)) -cne $f.sha256){throw ('Pinned PA3 package drift: '+$f.relative)}}
foreach($source in @('scripts/PreAlphaArrivalPA1.reds','cet/init.lua')){[void](Hash (Join-Path $ws ('prealpha/camera_pa4/'+$source)))}
New-Item -ItemType Directory -Path $out|Out-Null
$package=Join-Path $out 'package'
Copy-Item -LiteralPath $old.package_root -Destination $package -Recurse
Copy-Item -LiteralPath (Join-Path $ws 'prealpha/camera_pa4/scripts/PreAlphaArrivalPA1.reds') -Destination (Join-Path $package $scriptRel)
Copy-Item -LiteralPath (Join-Path $ws 'prealpha/camera_pa4/cet/init.lua') -Destination (Join-Path $package $cetRel)
$files=@(Get-ChildItem -LiteralPath $package -Recurse -File|ForEach-Object {@{relative=[IO.Path]::GetRelativePath($package,$_.FullName).Replace('\','/');sha256=Hash $_.FullName;bytes=$_.Length}})
$changes=@()
foreach($f in $files){$prior=@($old.package_files|Where-Object {$_.relative -ceq $f.relative});if($prior.Count -ne 1){throw 'File set changed'};if($prior[0].sha256 -cne $f.sha256){$changes+=@{relative=$f.relative;old_sha256=$prior[0].sha256;new_sha256=$f.sha256}}}
if($files.Count -ne 53 -or $changes.Count -ne 2 -or @($changes|Where-Object {$_.relative -cnotin $allowed}).Count){throw 'Unexpected package delta'}
if((Hash (Join-Path $package $archiveRel)) -cne (Hash (Join-Path $old.package_root $archiveRel))){throw 'Archive must remain byte-identical'}
Json (Join-Path $out 'build.json') @{status='BUILT_BASELINE_IDENTICAL_COMPILE_PENDING';output=$out;package_root=$package;package_files=$files;changes=$changes;resources=616;archive_unchanged=$true;unchanged_files=51;prior_build=$base;prior_build_sha256=$baselineHash;members=$old.members;game_save_cache_writes=$false}
Write-Output ('BUILD_PASS='+$out)
