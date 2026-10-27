Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$m=Get-Content (Join-Path $PSScriptRoot 'candidate_01/manifest.json') -Raw|ConvertFrom-Json -Depth 100
$paths=@($m.overlays.PSObject.Properties.Name | Where-Object {$_ -cne 'towercontinued\sidejob_repair_sr1\en-us.lipmap'})
if($paths.Count -ne 18){throw 'Expected 18 new resource paths'}
$keys=@{};foreach($p in $paths){$keys[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($p).ToString()]=$p}
$mod='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/archive/pc/mod'
$archives=@(Get-ChildItem -LiteralPath $mod -Filter '*.archive' -File|Where-Object {$_.Name -cne 'zzzz_PTFR_Combined.archive'})
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$hits=[Collections.Generic.List[object]]::new()
foreach($f in $archives){$a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hs,[ref]$a).ToString() -cne 'NoError'){throw ('Unreadable archive '+$f.FullName)}
 foreach($e in $a.Files.Values){if($keys.ContainsKey($e.Key.ToString())){$hits.Add(@{archive=$f.FullName;name=$e.Name;depot=$keys[$e.Key.ToString()]})}}
}
$result=@{status='READ_ONLY_COLLISION_SCAN';archives=$archives.Count;new_paths=$paths.Count;collisions=$hits.ToArray()}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'candidate_01/collisions_01.json'),($result|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
@{archives=$archives.Count;new_paths=$paths.Count;collisions=$hits.Count}|ConvertTo-Json
if($hits.Count){throw 'New resource path collision'}
