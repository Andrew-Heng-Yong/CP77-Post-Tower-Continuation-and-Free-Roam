Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$rel='towercontinued\sidejobs_s30\entries\mq006_rollercoaster.questphase'
$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($rel).ToString()
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$folder='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\mod'
$archives=@(Get-ChildItem -LiteralPath $folder -Filter '*.archive' -File)
$hits=@()
foreach($f in $archives){$a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hs,[ref]$a).ToString() -cne 'NoError'){throw ('Unreadable '+$f.Name)};foreach($e in $a.Files.Values){if($e.Key.ToString() -ceq $key){$hits+=@{archive=$f.Name;depot=$e.Name}}}}
if($hits.Count -ne 1 -or $hits[0].archive -cne 'zzzz_PTFR_Combined.archive' -or $hits[0].depot -cne $rel){throw ('Unexpected installed winner '+($hits|ConvertTo-Json -Compress))}
$result=@{status='PASS_SINGLE_EXPECTED_PTFR_WINNER';archives=$archives.Count;resource=$rel;hits=$hits;game_writes=0}
$out=Join-Path $PSScriptRoot 'candidate_01/winner_scan_01.json'
[IO.File]::WriteAllText($out,($result|ConvertTo-Json -Depth 10)+"`n",[Text.UTF8Encoding]::new($false))
$result|ConvertTo-Json -Depth 10
