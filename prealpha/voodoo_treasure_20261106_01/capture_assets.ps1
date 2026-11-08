param([string]$OutputName = 'assets_01')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($OutputName -cnotmatch '^[a-z][a-z0-9_]+$') { throw 'Use a simple fresh output directory name' }
$output = Join-Path $PSScriptRoot $OutputName
if (Test-Path -LiteralPath $output) { throw 'Fresh output required' }
$workspace = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$game = 'C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077'
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$targets = @{}
foreach ($depot in @(
    'ep1\quest\main_quests\q304\entities\q304_slider_stash_loot.ent',
    'ep1\quest\main_quests\q304\entities\q304_slider_stash_door.ent',
    'ep1\quest\main_quests\q304\entities\q304_slider_stash.ent',
    'base\gameplay\devices\masters\terminals\door_terminal_1.ent',
    'ep1\quest\main_quests\q304\phases\q304_slider_stash.questphase',
    'towercontinued\sidejobs_s23\ep1\voodoo_boot.questphase',
    'ep1\quest\ep1_persistent_content.questphase',
    'base\worlds\03_night_city\_compiled\default\ep1\blocks\all.streamingblock'
)) {
    $targets[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)] = $depot
}
$service = [WolvenKit.Common.Services.HashService]::new()
$service.Load()
$archives = @(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc') -Filter '*.archive' -Recurse -File | Sort-Object FullName)
$rows = [Collections.Generic.List[object]]::new()
[IO.Directory]::CreateDirectory($output) | Out-Null
foreach ($file in $archives) {
    $meta = @($file.Length, $file.LastWriteTimeUtc.Ticks)
    $archive = $null
    if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName, $service, [ref]$archive).ToString() -ne 'NoError') {
        throw "Cannot read archive index $($file.FullName)"
    }
    foreach ($key in $targets.Keys) {
        if (-not $archive.Files.ContainsKey([uint64]$key)) { continue }
        $depot = $targets[$key]
        $raw = Join-Path $output ("asset_$($rows.Count)_" + [IO.Path]::GetFileName($depot))
        $memory = [IO.MemoryStream]::new()
        try {
            $archive.Files[[uint64]$key].Extract($memory)
            [IO.File]::WriteAllBytes($raw, $memory.ToArray())
        } finally { $memory.Dispose() }
        $row = @{depot = $depot; provider = $file.FullName; metadata = $meta; raw = $raw; sha256 = (Get-FileHash -LiteralPath $raw).Hash}
        if (-not $depot.EndsWith('.streamingblock')) {
            try {
                $row.json = $raw + '.json'
                Export-Cr2wJson (Read-Cr2wFile $raw) $row.json
                $row.json_sha256 = (Get-FileHash -LiteralPath $row.json).Hash
            } catch { $row.error = $_.Exception.Message }
        }
        $rows.Add($row)
    }
    $file.Refresh()
    if ($file.Length -ne $meta[0] -or $file.LastWriteTimeUtc.Ticks -ne $meta[1]) { throw 'Archive changed during capture' }
}
@{targets = @($targets.Values | Sort-Object); archives = @($archives.FullName); providers = $rows} |
    ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $output 'manifest.json') -Encoding utf8NoBOM
$rows | ForEach-Object { '{0} {1} {2} {3}' -f $_.depot, [IO.Path]::GetFileName($_.provider), $_.sha256, $_['error'] }
