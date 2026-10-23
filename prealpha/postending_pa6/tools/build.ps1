param([Parameter(Mandatory)][string]$Output,[Parameter(Mandatory)][string]$RogueBuild)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
. (Join-Path $PSScriptRoot 'scope.ps1')
function NoLink([string]$p){$cursor=[IO.Path]::GetFullPath($p);while($cursor){if(Test-Path -LiteralPath $cursor){if(((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'Reparse path refused'}};$parent=[IO.Directory]::GetParent($cursor);if(!$parent){break};$cursor=$parent.FullName}}
function Bound([string]$p,[string]$base){if(![IO.Path]::IsPathFullyQualified($p)){throw 'Absolute build path required'};$p=[IO.Path]::GetFullPath($p);$base=[IO.Path]::GetFullPath($base);if(!$p.StartsWith($base+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Outside build scope'};NoLink $p;$p}
function Hash([string]$p){NoLink $p;(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function ReadJson([string]$p){NoLink $p;Get-Content -LiteralPath $p -Raw|ConvertFrom-Json}
function Json([string]$p,$v){if(Test-Path -LiteralPath $p){throw 'Pinned output exists'};[IO.File]::WriteAllText($p,($v|ConvertTo-Json -Depth 35),[Text.UTF8Encoding]::new($false))}
$out=Bound $Output (Join-Path $ws 'prealpha/postending_pa6/build')
if(Test-Path -LiteralPath $out){throw 'Fresh PA6 build directory required'}
$rogue=Bound $RogueBuild (Join-Path $ws 'prealpha/postending_pa6/rogue/build')
$rr=ReadJson (Join-Path $rogue 'build.json');$rt=ReadJson (Join-Path $rogue 'tests.json')
$rh=Hash (Join-Path $rogue 'build.json')
if($rr.status -cne 'BUILT_PA6_ROGUE_CANDIDATE_NOT_LIVE' -or $rt.status -cne 'PASS_EXACT_FAULT_REPAIR_OFFLINE_NOT_LIVE' -or $rt.build_sha256 -cne $rh -or
 $rr.archive -cne '0_TowerContinued_RogueLipsync_PA6.archive' -or $rr.resource_count -ne 1 -or $rr.depot -cne 'towercontinued\afterlife_interactions_r8\rogue.scene' -or
 !$rr.explicit_modlist_absent -or !$rr.patch_name_ascii_before_baseline -or $rr.expected_baseline_hits -ne 1){throw 'Unverified native Rogue component'}
if((Hash (Join-Path $rogue $rr.archive)) -cne $rr.archive_sha256){throw 'Rogue tested archive drift'}
$inventory=@(ReadJson (Join-Path $rogue 'collision_audit.json'))
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$mods=Join-Path $game 'archive/pc/mod'
if(Test-Path -LiteralPath (Join-Path $mods 'modlist.txt')){throw 'Custom archive order needs review'}
$actualArchives=@(Get-ChildItem -LiteralPath $mods -File -Filter '*.archive')
if($inventory.Count -ne $rr.installed_archives_scanned -or $inventory.Count -ne $actualArchives.Count -or @($inventory.archive|Sort-Object -Unique).Count -ne $inventory.Count){throw 'Archive inventory changed'}
$hits=0
foreach($row in $inventory){
 if($row.archive -cnotmatch '^[^/\\:]+\.archive$' -or $row.sha256 -cnotmatch '^[A-F0-9]{64}$'){throw 'Invalid audit row'}
 if((Hash (Join-Path $mods $row.archive)) -cne $row.sha256){throw 'Audited archive changed'}
 $hits+=$row.target_hits
 if($row.target_hits -ne 0 -and ($row.archive -cne 'TowerContinued_PreAlpha.archive' -or $row.target_hits -ne 1 -or $row.sha256 -cne $rr.baseline_archive_sha256)){throw 'Unexpected target collision'}
}
if($hits -ne 1){throw 'Expected one original scene'}
$base=Join-Path $ws 'prealpha/postending_pa5/build/pa5_03'
if((Hash (Join-Path $base 'build.json')) -cne $baselineSHA){throw 'Pinned PA5 report drift'}
$old=ReadJson (Join-Path $base 'build.json')
$expected=@($old.package_files|ForEach-Object relative)
if($expected.Count -ne 58 -or @($expected|Sort-Object -Unique).Count -ne 58){throw 'Pinned baseline count drift'}
$actual=@(Get-ChildItem -LiteralPath $old.package_root -Recurse -Force -File|ForEach-Object {NoLink $_.FullName;[IO.Path]::GetRelativePath($old.package_root,$_.FullName).Replace('\','/')})
if(@(Compare-Object $actual $expected -CaseSensitive).Count){throw 'Pinned baseline set drift'}
foreach($f in $old.package_files){if((Hash (Join-Path $old.package_root $f.relative)) -cne $f.sha256){throw 'Pinned baseline bytes drift'}}
$sources=@{
 'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_PreAlpha/init.lua'=(Join-Path $ws 'prealpha/postending_pa6/logging/init.lua');
 'r6/scripts/PTFR_PreAlpha/PA1/PreAlphaEntry.reds'=(Join-Path $ws 'prealpha/postending_pa6/scripts/PreAlphaEntry.reds');
 'r6/scripts/PTFR_PreAlpha/PTFR_RestorationBaseline/RestorationBaseline.reds'=(Join-Path $ws 'prealpha/postending_pa6/h10/source/RestorationBaseline.reds');
 'archive/pc/mod/0_TowerContinued_RogueLipsync_PA6.archive'=(Join-Path $rogue $rr.archive)
}
if($sources.Count -ne 4){throw 'Expected exact four-change package'}
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
if($files.Count -ne 59 -or $changes.Count -ne 4){throw 'Unexpected package delta'}
foreach($r in @('archive/pc/mod/TowerContinued_PreAlpha.archive','archive/pc/mod/TowerContinued_PreAlpha.archive.xl','archive/pc/mod/TowerContinued_Optics_PA5.archive')){if((Hash (Join-Path $package $r)) -cne (Hash (Join-Path $old.package_root $r))){throw 'Existing archives must remain unchanged'}}
Json (Join-Path $out 'build.json') @{status='BUILT_BASELINE_IDENTICAL_COMPILE_PENDING';output=$out;package_root=$package;package_files=$files;changes=$changes;archive_unchanged=$true;unchanged_files=55;prior_build=$base;prior_build_sha256=$baselineSHA;rogue_build=$rogue;rogue_evidence=@{build_sha256=$rh;tests_sha256=Hash (Join-Path $rogue 'tests.json');collision_audit_sha256=Hash (Join-Path $rogue 'collision_audit.json')};archive_inventory=$inventory;source_files=@($sources.Keys|ForEach-Object {@{relative=$_;source=$sources[$_];sha256=Hash $sources[$_]}});preserved_gd2=@{relative=$gd2Relative;sha256=$gd2SHA};game_save_cache_writes=$false}
Write-Output ('BUILD_PASS='+$out)
