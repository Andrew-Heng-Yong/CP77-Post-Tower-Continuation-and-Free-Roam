Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$archive='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/archive/pc/mod/00000000_TowerContinued_SideJobs_S29.archive'
$out=Join-Path $PSScriptRoot 'candidate_02/visual_discovery_01'
if(Test-Path -LiteralPath $out){throw 'Discovery exists'}
New-Item -ItemType Directory -Path $out -Force|Out-Null
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$a=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$a).ToString() -cne 'NoError'){throw 'Archive read failed'}
$paths=@('towercontinued\sidejobs_s29\native\base\workspots\main_characters\johnny\johnny__stand_ground_cigarette__idle__01.workspot','towercontinued\sidejobs_s29\native\base\workspots\main_characters\johnny\ground\johnny__walk_ground_cigarette__aggressive__01.workspot')
$rows=@()
foreach($depot in $paths){$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot);if(!$a.Files.ContainsKey($key)){throw ('Workspot missing '+$depot)}
 $raw=Join-Path $out $depot;New-Item -ItemType Directory -Path (Split-Path $raw -Parent) -Force|Out-Null;$m=[IO.MemoryStream]::new();try{$a.Files[$key].Extract($m);[IO.File]::WriteAllBytes($raw,$m.ToArray())}finally{$m.Dispose()};$json=$raw+'.json';Export-Cr2wJson (Read-Cr2wFile $raw) $json
 $rows+=@{depot=$depot;raw_sha256=(Get-FileHash -LiteralPath $raw).Hash;json_sha256=(Get-FileHash -LiteralPath $json).Hash}
}
$rows|ConvertTo-Json -Depth 20
