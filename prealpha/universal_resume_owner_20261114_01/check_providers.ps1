# Compare only the watched chain and its dialogue providers across installed archives.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$source = Join-Path $PSScriptRoot 'source_inventory_01.json'
$out = Join-Path $PSScriptRoot 'providers_01.json'
if (Test-Path -LiteralPath $out) { throw 'Fresh provider output required' }
$sources = Get-Content -LiteralPath $source -Raw | ConvertFrom-Json
$manifestPath = Join-Path $workspace 'prealpha/resume_dispatcher_rd10_kirk_20261113_01/deployment_01/installed_manifest_01.json'
if ((Get-FileHash -LiteralPath $manifestPath).Hash -cne 'AB279745469DEE08EC9A816EE9F04C9F9750456DE26A9C6CC8940E15FAFE56D8') { throw 'RD10 manifest changed' }
$game = (Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json).game_root
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$service = [WolvenKit.Common.Services.HashService]::new()
$service.Load()
$wanted = @{}
foreach ($row in $sources) {
    $key = [UInt64]$row.key
    if ($wanted.ContainsKey($key)) { throw 'Watched depot key collision' }
    $wanted[$key] = $row.depot
}
$archiveFiles = @(foreach ($rel in 'archive/pc','red4ext/plugins','mods') {
    $root = Join-Path $game $rel
    if (Test-Path -LiteralPath $root) { Get-ChildItem -LiteralPath $root -Recurse -Force -File -Filter '*.archive' }
}) | Sort-Object FullName -Unique
$inventory = @()
$providers = @()
foreach ($file in $archiveFiles) {
    for ($parent = $file; $null -ne $parent;) {
        if ($parent.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked archive input' }
        $parent = if ($parent -is [IO.FileInfo]) { $parent.Directory } else { $parent.Parent }
    }
    $size = $file.Length
    $timestamp = $file.LastWriteTimeUtc.Ticks
    $archive = $null
    if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$service,[ref]$archive).ToString() -cne 'NoError') { throw 'Archive parse failed' }
    foreach ($key in $wanted.Keys) {
        if ($archive.Files.ContainsKey($key)) {
            $bytes = [IO.MemoryStream]::new()
            try {
                $archive.Files[$key].Extract($bytes)
                $digest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes.ToArray()))
                $providers += @{ archive = $file.FullName; depot = $wanted[$key]; sha256 = $digest }
            } finally { $bytes.Dispose() }
        }
    }
    $file.Refresh()
    if ($file.Length -ne $size -or $file.LastWriteTimeUtc.Ticks -ne $timestamp) { throw 'Input archive changed during inspection' }
    $inventory += @{ path = $file.FullName; bytes = $size; mtime_ticks = $timestamp }
}
@{ source_inventory_sha256 = (Get-FileHash -LiteralPath $source).Hash; archives = $inventory; providers = $providers } |
    ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $out -Encoding utf8NoBOM
Write-Output "Scanned $($archiveFiles.Count) archives for $($sources.Count) depots. Found $($providers.Count) providers."
