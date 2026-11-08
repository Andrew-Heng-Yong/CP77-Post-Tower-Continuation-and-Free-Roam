Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$output = Join-Path $PSScriptRoot 'root_binding_providers_01'
if (Test-Path -LiteralPath $output) { throw 'Fresh output required' }

function Assert-NoLink([string]$Path) {
    $item = Get-Item -LiteralPath $Path
    while ($null -ne $item) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked input refused: $($item.FullName)" }
        $item = if ($item -is [IO.DirectoryInfo]) { $item.Parent } else { $item.Directory }
    }
}

Assert-NoLink $PSScriptRoot
New-Item -ItemType Directory -Path $output | Out-Null
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$depots = @(
    'ep1\quest\ep1.quest',
    'ep1\quest\ep1.gamedef',
    'base\quest\cyberpunk2077.quest',
    'base\quest\cyberpunk2077.gamedef'
)
$game = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$hashes = [WolvenKit.Common.Services.HashService]::new()
$hashes.Load()
$queries = @{}
foreach ($depot in $depots) {
    $key = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
    if ($queries.ContainsKey($key)) { throw 'Query collision' }
    $queries[$key] = $depot
}
$directories = [Collections.Generic.Stack[string]]::new()
$directories.Push((Join-Path $game 'archive/pc'))
$files = [Collections.Generic.List[IO.FileInfo]]::new()
while ($directories.Count -gt 0) {
    $directory = $directories.Pop()
    Assert-NoLink $directory
    foreach ($item in Get-ChildItem -LiteralPath $directory) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Archive census link: $($item.FullName)" }
        if ($item -is [IO.DirectoryInfo]) { $directories.Push($item.FullName) }
        elseif ($item.Extension -ceq '.archive') { $files.Add($item) }
    }
}
$rows = @()
$archives = @()
$index = 0
foreach ($file in $files | Sort-Object FullName) {
    Assert-NoLink $file.FullName
    $archive = $null
    if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName, $hashes, [ref]$archive).ToString() -cne 'NoError') { throw "Unreadable archive: $($file.FullName)" }
    $archives += @{ path = $file.FullName; bytes = $file.Length; mtime_utc = $file.LastWriteTimeUtc.ToString('o'); members = $archive.Files.Count }
    $index++
    foreach ($key in $queries.Keys) {
        if (-not $archive.Files.ContainsKey([uint64]$key)) { continue }
        $depot = $queries[$key]
        $raw = Join-Path $output ('sources/' + $index.ToString('D3') + '/' + $depot)
        New-Item -ItemType Directory -Path (Split-Path $raw -Parent) -Force | Out-Null
        $memory = [IO.MemoryStream]::new()
        try {
            $archive.Files[[uint64]$key].Extract($memory)
            [IO.File]::WriteAllBytes($raw, $memory.ToArray())
        } finally { $memory.Dispose() }
        $json = $raw + '.json'
        $errorText = $null
        try { Export-Cr2wJson (Read-Cr2wFile $raw) $json } catch { $errorText = $_.Exception.Message }
        $rows += @{
            archive = $file.FullName; depot = $depot; key = $key.ToString(); raw = $raw
            sha256 = (Get-FileHash -LiteralPath $raw).Hash
            json = $(if (Test-Path -LiteralPath $json) { $json } else { $null })
            json_sha256 = $(if (Test-Path -LiteralPath $json) { (Get-FileHash -LiteralPath $json).Hash } else { $null })
            decode_error = $errorText
        }
    }
}
$missing = @($depots | Where-Object { $_ -notin $rows.depot })
@{
    status = 'READ_ONLY_TARGET_PROVIDER_CAPTURE'; queries = $depots; archives = $archives; resources = $rows; missing = $missing
    game_writes = 0; save_writes = 0
    limits = 'Only four root-binding resources extracted. Candidate root paths still require exact native setup/load proof; an ordered game definition is not a proven native root ID.'
} | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $output 'manifest.json') -Encoding utf8NoBOM
@{ archives = $archives.Count; payloads = $rows.Count; missing = $missing; decode_failures = @($rows | Where-Object { $null -ne $_.decode_error }).Count } | ConvertTo-Json -Depth 3
