Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$candidate=Join-Path $PSScriptRoot 'candidate_02';$build=Get-Content -LiteralPath (Join-Path $candidate 'build_lipmap_01.json') -Raw|ConvertFrom-Json -Depth 30
if($build.status -cne 'STAGED_ENGLISH_LIPMAP_44_NOT_INSTALLED' -or $build.registrations -ne 44){throw 'Lipmap build proof missing'}
$source=Join-Path $candidate 'lipmap_source';$raw=Join-Path $source $build.depot
if((Get-FileHash -LiteralPath $raw).Hash -cne $build.raw_sha256){throw 'Lipmap source drift'}
$game='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077';$mods=Join-Path $game 'archive/pc/mod';$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($build.depot);$checked=0
foreach($f in Get-ChildItem -LiteralPath $mods -Filter '*.archive' -File){$a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hs,[ref]$a).ToString() -cne 'NoError'){throw ('Cannot read '+$f.Name)};if($a.Files.ContainsKey($key)){throw ('Lipmap collision '+$f.Name)};$checked++}
$name='zzzz_PTFR_SideJobs_SR1_Lipmap.archive';$archive=Join-Path $candidate ('package/archive/pc/mod/'+$name)
if(Test-Path -LiteralPath $archive){throw 'Package exists'}
New-Item -ItemType Directory -Path (Split-Path $archive -Parent) -Force|Out-Null
$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Lipmap archive pack failed'}}finally{$stream.Dispose()}
$arc=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$arc).ToString() -cne 'NoError' -or $arc.Files.Count -ne 1 -or !$arc.Files.ContainsKey($key)){throw 'Lipmap packed member mismatch'}
$m=[IO.MemoryStream]::new();try{$arc.Files[$key].Extract($m);$packed=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()))}finally{$m.Dispose()}
if($packed -cne $build.raw_sha256){throw 'Lipmap packed bytes changed'}
$xl="localization:`n  lipmaps:`n    en-us: $($build.depot)`n";[IO.File]::WriteAllText(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$proof=[ordered]@{status='STAGED_44_LIPMAP_ARCHIVE_XL_READBACK_NO_INSTALL';archive=$archive;archive_sha256=(Get-FileHash -LiteralPath $archive).Hash;xl_sha256=(Get-FileHash -LiteralPath ($archive+'.xl')).Hash;depot=$build.depot;resource_sha256=$packed;registrations=44;installed_archives_checked=$checked;build_sha256=(Get-FileHash -LiteralPath (Join-Path $candidate 'build_lipmap_01.json')).Hash;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $candidate 'package_lipmap_01.json'),($proof|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))
@{status=$proof.status;registrations=44;archive_sha256=$proof.archive_sha256}|ConvertTo-Json
