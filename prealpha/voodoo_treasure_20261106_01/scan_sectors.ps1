param([string]$OutputName = 'sectors_01')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($OutputName -cnotmatch '^[a-z][a-z0-9_]+$') { throw 'Use a simple fresh output directory name' }
$output = Join-Path $PSScriptRoot $OutputName
if (Test-Path -LiteralPath $output) { throw 'Fresh output required' }
$workspace = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$game = 'C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077'
$qr8 = Join-Path $workspace 'prealpha/quest_restoration_qr8/worker_c'
$block = Join-Path $qr8 'reviews/enrollment_01/current_providers/resource_4.streamingblock.json'
$trigger = Join-Path $qr8 'capture_01/resource_7.nodes.bin'
$blockHash = (Get-FileHash -LiteralPath $block).Hash
$triggerHash = (Get-FileHash -LiteralPath $trigger).Hash
$blockJson = Get-Content -Raw -LiteralPath $block | ConvertFrom-Json -Depth 80
$triggerBytes = [IO.File]::ReadAllBytes($trigger)
if ($triggerBytes.Length -ne 144) { throw 'Expected the single native stash trigger setup' }
$x = [BitConverter]::ToSingle($triggerBytes, 0)
$y = [BitConverter]::ToSingle($triggerBytes, 4)
$targets = @{}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$descriptors = $blockJson.Data.RootChunk.descriptors
for ($i = 0; $i -lt $descriptors.Count; $i++) {
    $d = $descriptors[$i]
    $depot = $d.data.DepotPath.'$value'
    $prefab = $d.questPrefabNodeRef.'$value'
    $box = $d.streamingBox
    $reason = if ($prefab -is [string] -and $prefab.Contains('/monument_av_prefab')) {
        'Monument Avenue prefab'
    } elseif ($d.category -ne 'Quest' -and $box.Min.X -le $x + 256 -and $box.Max.X -ge $x - 256 -and $box.Min.Y -le $y + 256 -and $box.Max.Y -ge $y - 256) {
        'non-quest descriptor intersects 256m XY box'
    }
    if ($reason) {
        $key = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
        if ($targets.ContainsKey($key)) { throw "Duplicate target depot $depot" }
        $targets[$key] = @{depot = $depot; descriptor = $i; selection = $reason; prefab = $prefab}
    }
}
$needles = @(
    '#q304_dvc_slider_stash_door', '#q304_dvc_slider_stash_terminal',
    '#q304_dvc_slider_stash', '#q304_slider_stash_loot', '#q304_mp_slider_stash_area'
)
$shortHashes = @{}
foreach ($needle in $needles) { $shortHashes[$needle] = [WolvenKit.RED4.Types.NodeRef]::CalculateHash($needle) }
$service = [WolvenKit.Common.Services.HashService]::new()
$service.Load()
$archivePaths = @(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc') -Filter '*.archive' -Recurse -File | Sort-Object FullName)
$rows = [Collections.Generic.List[object]]::new()
$indexes = [Collections.Generic.List[object]]::new()
[IO.Directory]::CreateDirectory($output) | Out-Null
foreach ($file in $archivePaths) {
    $meta = @($file.Length, $file.LastWriteTimeUtc.Ticks)
    $archive = $null
    if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName, $service, [ref]$archive).ToString() -ne 'NoError') {
        throw "Cannot read archive index $($file.FullName)"
    }
    $count = 0
    foreach ($key in $targets.Keys) {
        if (-not $archive.Files.ContainsKey([uint64]$key)) { continue }
        $memory = [IO.MemoryStream]::new()
        try {
            $archive.Files[[uint64]$key].Extract($memory)
            $bytes = $memory.ToArray()
        } finally { $memory.Dispose() }
        $ascii = [Text.Encoding]::ASCII.GetString($bytes)
        $names = @([regex]::Matches($ascii, '(?i)[\x21-\x7e]{0,400}slider_stash[\x21-\x7e]{0,150}') | ForEach-Object Value | Sort-Object -Unique)
        $hex = [Text.Encoding]::Latin1.GetString($bytes)
        $shortMatches = @($needles | Where-Object { $hex.Contains([Text.Encoding]::Latin1.GetString([BitConverter]::GetBytes([uint64]$shortHashes[$_]))) })
        $sha = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
        $raw = $null
        if ($names.Count -gt 0 -or $shortMatches.Count -gt 0) {
            $raw = Join-Path $output ('sector_' + $rows.Count + '.streamingsector')
            [IO.File]::WriteAllBytes($raw, $bytes)
        }
        $rows.Add(@{target = $targets[$key]; provider = $file.FullName; sha256 = $sha; byte_count = $bytes.Length; string_matches = $names; short_hash_matches = $shortMatches; captured = $raw})
        $count++
    }
    $file.Refresh()
    if ($file.Length -ne $meta[0] -or $file.LastWriteTimeUtc.Ticks -ne $meta[1]) { throw 'Archive changed during scan' }
    $indexes.Add(@{path = $file.FullName; metadata = $meta; candidate_count = $count})
}
if ((Get-FileHash -LiteralPath $block).Hash -cne $blockHash -or (Get-FileHash -LiteralPath $trigger).Hash -cne $triggerHash) {
    throw 'Selection input changed during scan'
}
$report = @{
    block = @{path = $block; sha256 = $blockHash}
    trigger = @{path = $trigger; sha256 = $triggerHash; x = $x; y = $y}
    targets = @($targets.Values | Sort-Object descriptor)
    short_hashes = $shortHashes
    archives = $indexes
    providers = $rows
}
$report | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath (Join-Path $output 'manifest.json') -Encoding utf8NoBOM
$hits = @($rows | Where-Object captured)
@{candidates = $targets.Count; providers = $rows.Count; archives = $indexes.Count; hits = $hits} | ConvertTo-Json -Depth 12
