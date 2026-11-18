# Read-only current-provider lookup for unresolved leaves and follow-up activation writers.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $PSScriptRoot 'native_sources_01'
if (Test-Path -LiteralPath $out) { throw 'Fresh evidence required' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$depots=@(
 'base\quest\minor_quests\mq029\phases\mq029_james.questphase',
 'base\quest\minor_quests\mq029\phases\mq029_stolen_bike.questphase',
 'ep1\openworld\street_stories\sts_ep1_07\phases\sts_ep1_07_cleanup.questphase',
 'ep1\openworld\street_stories\sts_ep1_07\phases\sts_ep1_07_bugfixing.questphase',
 'ep1\openworld\street_stories\sts_ep1_12\phases\sts_ep1_12_cleanup.questphase',
 'ep1\openworld\street_stories\sts_ep1_12\phases\sts_ep1_12_bugfixing.questphase',
 'ep1\quest\main_quests\q305\phases\q305_12_haunted_weapon.questphase',
 'ep1\openworld\world_stories\ep1_world_stories.questphase'
)
$hs=[WolvenKit.Common.Services.HashService]::new(); $hs.Load()
$queries=@{}
foreach ($depot in $depots) { $queries[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)]=$depot }
function Plain([string]$path) {
    for ($item=Get-Item -LiteralPath $path -Force; $null -ne $item;) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked input/output: $path" }
        $item=if ($item -is [IO.FileInfo]) { $item.Directory } else { $item.Parent }
    }
}
Plain $PSScriptRoot
[void](New-Item -ItemType Directory -Path $out)
$hits=[Collections.Generic.List[object]]::new()
$archives=[Collections.Generic.List[object]]::new()
foreach ($file in Get-ChildItem -LiteralPath 'C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/archive/pc' -Filter '*.archive' -Recurse -File) {
    Plain $file.FullName
    $arc=$null
    if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$arc).ToString() -cne 'NoError') { throw 'Unreadable provider' }
    $archives.Add(@{path=$file.FullName; length=$file.Length; last_write_utc=$file.LastWriteTimeUtc.ToString('o')})
    foreach ($key in $queries.Keys) {
        if (-not $arc.Files.ContainsKey([uint64]$key)) { continue }
        $depot=$queries[$key]
        $raw=Join-Path $out (([string]$archives.Count)+'/'+$depot)
        [void](New-Item -ItemType Directory -Path (Split-Path $raw -Parent) -Force)
        $memory=[IO.MemoryStream]::new()
        try { $arc.Files[[uint64]$key].Extract($memory); [IO.File]::WriteAllBytes($raw,$memory.ToArray()) } finally { $memory.Dispose() }
        Export-Cr2wJson (Read-Cr2wFile $raw) ($raw+'.json')
        $hits.Add(@{archive=$file.FullName; depot=$depot; raw=$raw; json=($raw+'.json'); sha256=(Get-FileHash -LiteralPath $raw).Hash; json_sha256=(Get-FileHash -LiteralPath ($raw+'.json')).Hash})
    }
}
@{status='CURRENT_PROVIDER_LOOKUP'; queries=$depots; archives=$archives.ToArray(); hits=$hits.ToArray(); game_writes=0; save_writes=0} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $out 'providers.json') -Encoding utf8NoBOM
Write-Output ("Scanned {0} archives; captured {1} providers for {2} depots" -f $archives.Count,$hits.Count,$depots.Count)
