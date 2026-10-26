Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$candidate=Join-Path $PSScriptRoot 'candidate_02';$plan=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'plan_01.json') -Raw|ConvertFrom-Json
$build=Get-Content -LiteralPath (Join-Path $candidate 'build_native_02.json') -Raw|ConvertFrom-Json;$test=Get-Content -LiteralPath (Join-Path $candidate 'test_native_01.json') -Raw|ConvertFrom-Json;$compile=Get-Content -LiteralPath (Join-Path $candidate 'compile_01/result.json') -Raw|ConvertFrom-Json;$runtime=Get-Content -LiteralPath (Join-Path $candidate 'patch_runtime_01.json') -Raw|ConvertFrom-Json
if($build.status -cne 'STAGED_NATIVE_SIX_RESOURCE_PATCH_NOT_INSTALLED' -or $test.status -cne 'PASS_SIX_RESOURCE_SCOPED_SEMANTIC_READBACK_NOT_LIVE' -or $compile.status -cne 'PASS_FULL_SCC_NOT_LIVE' -or $runtime.status -cne 'STAGED_RUNTIME_PREDECESSOR_FILTER_AND_S25_PHONE_ADOPTION'){throw 'Prerequisite proofs missing'}
$game='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077';$mods=Join-Path $game 'archive/pc/mod'
if(Test-Path -LiteralPath (Join-Path $mods 'modlist.txt')){throw 'Explicit mod load order requires review'}
$name='zzzz_PTFR_SideJobs_SR1.archive';$archive=Join-Path $candidate ('package/archive/pc/mod/'+$name)
if(Test-Path -LiteralPath $archive){throw 'Package output exists'}
$keys=@{};foreach($r in $plan.installed){$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($r.depot);$keys[$key.ToString()]=$r}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$matches=[Collections.Generic.List[object]]::new()
$files=[string[]]@(Get-ChildItem -LiteralPath $mods -Filter '*.archive' -File|ForEach-Object FullName);[Array]::Sort($files,[StringComparer]::OrdinalIgnoreCase)
foreach($path in $files){$a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hs,[ref]$a).ToString() -cne 'NoError'){throw ('Archive read failed: '+$path)}
 foreach($k in $keys.Keys){$key=[uint64]::Parse($k);if(!$a.Files.ContainsKey($key)){continue};$m=[IO.MemoryStream]::new();try{$a.Files[$key].Extract($m);$h=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()))}finally{$m.Dispose()};$matches.Add(@{archive=$path;depot=$keys[$k].depot;sha256=$h})}
}
foreach($r in $plan.installed){$hits=@($matches|Where-Object {$_.depot -ceq $r.depot});if($hits.Count -ne 1 -or $hits[0].sha256 -cne $r.sha256 -or $hits[0].archive -cne $r.archive){throw ('Winning override changed: '+$r.depot)};if([string]::CompareOrdinal($name,[IO.Path]::GetFileName($r.archive)) -le 0){throw ('Patch load order insufficient: '+$r.depot)}}
$source=Join-Path $candidate 'source';foreach($r in $plan.installed){$p=Join-Path $source $r.depot;if((Get-FileHash -LiteralPath $p).Hash -cne $build.resources.($r.depot)){throw ('Built source drift: '+$r.depot)}}
New-Item -ItemType Directory -Path (Split-Path $archive -Parent) -Force|Out-Null
$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Archive writer failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -cne 'NoError' -or $packed.Files.Count -ne 6){throw 'Packed member count mismatch'}
foreach($e in $packed.Files.Values){$m=[IO.MemoryStream]::new();try{$e.Extract($m);$h=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()))}finally{$m.Dispose()};if($h -cne $build.resources.($e.Name)){throw ('Packed readback drift '+$e.Name)}}
$scriptSource=Join-Path $candidate 'source_scripts/r6/scripts/TowerContinued_SideJobs_S29/SideJobsS29.reds';$scriptPackage=Join-Path $candidate 'package/r6/scripts/TowerContinued_SideJobs_S29/SideJobsS29.reds'
New-Item -ItemType Directory -Path (Split-Path $scriptPackage -Parent) -Force|Out-Null;Copy-Item -LiteralPath $scriptSource -Destination $scriptPackage
if((Get-FileHash -LiteralPath $scriptPackage).Hash -cne $runtime.output_sha256){throw 'Runtime package drift'}
$proof=[ordered]@{status='STAGED_PACKED_READBACK_NO_INSTALL';archive=$archive;archive_sha256=(Get-FileHash -LiteralPath $archive).Hash;resources=6;script=$scriptPackage;script_sha256=(Get-FileHash -LiteralPath $scriptPackage).Hash;existing_collisions=$matches.ToArray();native_test_sha256=(Get-FileHash -LiteralPath (Join-Path $candidate 'test_native_01.json')).Hash;compile_sha256=$compile.compiled_sha256;package_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $candidate 'package_01.json'),($proof|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
$proof|Select-Object status,resources,archive_sha256,script_sha256|ConvertTo-Json
