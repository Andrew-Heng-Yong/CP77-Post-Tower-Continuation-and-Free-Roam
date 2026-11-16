Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$jb2 = Join-Path $workspace 'prealpha/johnny_batch3_jb2'
$checkpoint = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'checkpoint.json') -Raw | ConvertFrom-Json -AsHashtable
$previousManifest = Join-Path $jb2 'core_manifest_01.json'
if ((Get-FileHash -LiteralPath $previousManifest).Hash -cne '6F56198224824B69F5073CC95A7D7708A9F08262707C48C61CE6A61593F9F1F4') {
    throw 'Changed JB2 transaction proof'
}
$previous = Get-Content -LiteralPath $previousManifest -Raw | ConvertFrom-Json -AsHashtable
$currentProof = Join-Path $PSScriptRoot 'archive_readback_01.json'
$earlierProof = Join-Path $jb2 'archive_readback_02.json'
$earlierPin = @($previous.proofs | Where-Object path -ceq $earlierProof)
if ($earlierPin.Count -ne 1 -or (Get-FileHash -LiteralPath $earlierProof).Hash -cne $earlierPin[0].sha256 -or
    (Get-FileHash -LiteralPath $currentProof).Hash -cne $checkpoint.proofs['archive_readback_01.json']) {
    throw 'Changed archive readback proof'
}
$sourceReports = @($earlierProof, $currentProof) | ForEach-Object {
    Get-Content -LiteralPath $_ -Raw | ConvertFrom-Json -AsHashtable
}
$reportDir = Join-Path $PSScriptRoot 'deployment_01'
$output = Join-Path $reportDir 'provider_preflight.json'
if (Test-Path -LiteralPath $output) { throw 'Fresh deployment provider report required' }

. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hashes = [WolvenKit.Common.Services.HashService]::new()
$hashes.Load()
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()

function EntryDigest($entry) {
    $stream = [IO.MemoryStream]::new()
    try {
        [void]$entry.Extract($stream)
        [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($stream.ToArray()))
    } finally {
        $stream.Dispose()
    }
}

$keys = @{}
foreach ($proof in $sourceReports) {
    foreach ($row in $proof.providers) {
        $key = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($row.depot)
        if ($keys.ContainsKey($key)) {
            $prior = $keys[$key]
            if ($prior.depot -cne $row.depot -or $prior.provider -cne $row.provider -or $prior.sha256 -cne $row.sha256) {
                throw "Conflicting provider proof for $($row.depot)"
            }
            continue
        }
        $keys[$key] = @{depot=$row.depot; provider=$row.provider; sha256=$row.sha256; hits=0}
    }
}

$archiveRoot = Join-Path $previous.game_root 'archive/pc'
for ($ancestor = [IO.DirectoryInfo]::new($archiveRoot); $null -ne $ancestor; $ancestor = $ancestor.Parent) {
    if ($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked archive root refused: $ancestor" }
}
if (@(Get-ChildItem -LiteralPath $archiveRoot -Recurse -Force -Attributes ReparsePoint).Count) {
    throw 'Linked archive tree refused'
}
$paths = @(Get-ChildItem -LiteralPath $archiveRoot -Recurse -File -Force -Filter '*.archive' | Sort-Object FullName)
foreach ($path in $paths) {
    $before = @($path.Length, $path.LastWriteTimeUtc.Ticks)
    $archive = $null
    if ($reader.ReadArchive($path.FullName, $hashes, [ref]$archive).ToString() -cne 'NoError') {
        throw "Unreadable archive $($path.FullName)"
    }
    foreach ($key in $keys.Keys) {
        if (-not $archive.Files.ContainsKey([uint64]$key)) { continue }
        $row = $keys[$key]
        $row.hits++
        if ($path.FullName -cne $row.provider -or (EntryDigest $archive.Files[[uint64]$key]) -cne $row.sha256) {
            throw "Changed or colliding provider $($row.depot) in $($path.FullName)"
        }
    }
    $path.Refresh()
    if ($path.Length -ne $before[0] -or $path.LastWriteTimeUtc.Ticks -ne $before[1]) {
        throw "Archive changed during provider verification: $($path.FullName)"
    }
}
foreach ($row in $keys.Values) {
    $expected = if ($row.provider) { 1 } else { 0 }
    if ($row.hits -ne $expected) { throw "Unexpected provider count for $($row.depot)" }
}
$xl = 'archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
$installedXL = (Get-FileHash -LiteralPath (Join-Path $previous.game_root $xl)).Hash
$stagedXL = (Get-FileHash -LiteralPath (Join-Path (Join-Path $PSScriptRoot 'candidate_01/package') $xl)).Hash
if ($installedXL -cne $stagedXL -or $installedXL -cne '510C49490C4B068F6CF0562AD8505D1276AE4B167F855B7730D583250ADA3056') {
    throw 'ArchiveXL registration bytes changed'
}
New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
@{
    status='PASS_JB3_CUMULATIVE_DEPOT_PROVIDERS'
    archives=@($paths.FullName)
    keys=@($keys.Values | Sort-Object depot)
    archive_count=$paths.Count
    provider_key_count=$keys.Count
    unoccupied_alias_count=@($keys.Values | Where-Object { -not $_.provider }).Count
    archivexl_sha256=$installedXL
    new_xl_registrations=0
    game_writes=0
    save_writes=0
} | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $output -Encoding utf8NoBOM
Write-Output "Verified $($keys.Count) cumulative depot keys against $($paths.Count) installed archives."
