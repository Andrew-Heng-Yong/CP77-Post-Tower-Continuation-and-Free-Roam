Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$evidence = Join-Path $PSScriptRoot 'evidence_01'
$exports = Join-Path $PSScriptRoot 'exports_01'
if (Test-Path -LiteralPath $exports) { throw 'Use a fresh export directory' }
$prepared = Get-Content -LiteralPath (Join-Path $evidence 'prepared.json') -Raw | ConvertFrom-Json -Depth 100
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
New-Item -ItemType Directory -Path $exports | Out-Null
$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$byArchive = @{}
foreach ($scene in $prepared.scenes) {
    $index = [int]$scene.archive_index
    if (!$byArchive.ContainsKey($index)) { $byArchive[$index] = [Collections.Generic.Dictionary[uint64,object]]::new() }
    $byArchive[$index].Add([uint64]$scene.key, $scene)
}
$manifestPath = Join-Path $evidence 'exports.jsonl'
$writer = [IO.StreamWriter]::new($manifestPath, $false, [Text.UTF8Encoding]::new($false))
$count = 0
$cacheCount = 0
$errors = 0
$kindCounts = @{}
$metadata = [Collections.Generic.List[object]]::new()

function Write-CompressedJson($resource, [string]$path) {
    $dto = [WolvenKit.Common.Conversion.RedFileDto]::new($resource, $false)
    $options = [WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
    $text = [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($dto, $options)
    $stream = [IO.File]::Create($path)
    try {
        $gzip = [IO.Compression.GZipStream]::new($stream, [IO.Compression.CompressionLevel]::Fastest, $true)
        try {
            $textWriter = [IO.StreamWriter]::new($gzip, [Text.UTF8Encoding]::new($false))
            try { $textWriter.Write($text) } finally { $textWriter.Dispose() }
        } finally { $gzip.Dispose() }
    } finally { $stream.Dispose() }
}

try {
    foreach ($archiveInfo in $prepared.archives) {
        $file = Get-Item -LiteralPath $archiveInfo.path
        $expectedTime = ([DateTime]$archiveInfo.mtime_utc).ToUniversalTime()
        if ($file.Length -ne $archiveInfo.bytes -or $file.LastWriteTimeUtc.Ticks -ne $expectedTime.Ticks) {
            throw "Archive baseline changed $($file.FullName)"
        }
        $archive = $null
        $result = ([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName, $hashService, [ref]$archive)
        if ($result.ToString() -cne 'NoError') { throw "Unreadable archive $($file.FullName)" }
        $selected = if ($byArchive.ContainsKey([int]$archiveInfo.index)) { $byArchive[[int]$archiveInfo.index] } else {
            [Collections.Generic.Dictionary[uint64,object]]::new()
        }
        foreach ($entry in $archive.Files.Values) {
            $kind = $null
            $source = $null
            if ($selected.ContainsKey([uint64]$entry.Key)) {
                $kind = 'SCENE'
                $source = $selected[[uint64]$entry.Key]
            } elseif ($entry.Extension -ceq '.conversations') {
                $kind = 'CONVERSATIONS'
            } elseif ($entry.Name -match '\\localization\\en-us\\subtitles\\.*\.json$') {
                $kind = 'ENGLISH_SUBTITLES'
            } else { continue }
            $row = [ordered]@{
                kind=$kind; depot=$entry.Name; key=$entry.Key.ToString(); archive=$file.FullName;
                archive_index=$archiveInfo.index; provider_role=$archiveInfo.role; scope='AUXILIARY_SOURCE';
                resource_id=$null; raw=$null; sha256=$null; json=$null; json_sha256=$null;
                status='PENDING'; root_type=$null; error=$null
            }
            if ($null -ne $source) {
                $row.depot = $source.depot
                $row.resource_id = $source.resource_id
                $row.scope = $source.scope
            } else {
                $identity = $file.FullName.ToLowerInvariant() + '|' + $entry.Key.ToString()
                $row.resource_id = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($identity))).Substring(0, 24).ToLowerInvariant()
            }
            try {
                $directory = Join-Path $exports $archiveInfo.index
                New-Item -ItemType Directory -Path $directory -Force | Out-Null
                if ($null -ne $source -and $source.raw) {
                    $row.raw = $source.raw
                    $row.sha256 = (Get-FileHash -LiteralPath $row.raw).Hash
                    if ($row.sha256 -cne $source.sha256) { throw 'Pinned raw payload changed' }
                } else {
                    $memory = [IO.MemoryStream]::new()
                    try {
                        $entry.Extract($memory)
                        $bytes = $memory.ToArray()
                    } finally { $memory.Dispose() }
                    $row.sha256 = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
                    $row.raw = Join-Path $directory ($entry.Key.ToString() + $entry.Extension)
                    [IO.File]::WriteAllBytes($row.raw, $bytes)
                }
                if ($null -ne $source -and $null -ne $source.cached_json) {
                    $cachedPath = $source.cached_json.path
                    if ((Get-FileHash -LiteralPath $cachedPath).Hash -cne $source.cached_json.sha256) { throw 'Verified JSON cache changed' }
                    $row.json = $cachedPath
                    $row.json_sha256 = $source.cached_json.sha256
                    $row.status = 'VERIFIED_CACHE'
                    $cacheCount++
                } else {
                    $resource = Read-Cr2wFile $row.raw
                    $row.root_type = $resource.RootChunk.GetType().Name
                    $row.json = Join-Path $directory ($entry.Key.ToString() + $entry.Extension + '.json.gz')
                    Write-CompressedJson $resource $row.json
                    $row.json_sha256 = (Get-FileHash -LiteralPath $row.json).Hash
                    $row.status = 'EXPORTED'
                }
            } catch {
                $row.status = 'OPAQUE'
                $row.error = $_.Exception.Message
                $row.json = $null
                $errors++
            }
            $writer.WriteLine(($row | ConvertTo-Json -Depth 10 -Compress))
            $writer.Flush()
            $count++
            if (!$kindCounts.ContainsKey($kind)) { $kindCounts[$kind] = 0 }
            $kindCounts[$kind]++
            if ($count % 100 -eq 0) {
                Write-Output "Exported $count provider inputs, $cacheCount verified caches, $errors opaque"
            }
        }
        $metadata.Add(@{
            path=$file.FullName; bytes=$file.Length; mtime_ticks=$file.LastWriteTimeUtc.Ticks;
            indexed_members=$archive.Files.Count
        })
    }
} finally { $writer.Dispose() }
$changed = @(
    foreach ($row in $metadata) {
        $file = Get-Item -LiteralPath $row.path
        if ($file.Length -ne $row.bytes -or $file.LastWriteTimeUtc.Ticks -ne $row.mtime_ticks) { $row.path }
    }
)
@{
    schema=1; provider_inputs=$count; verified_caches=$cacheCount; opaque=$errors; kind_counts=$kindCounts;
    changed_archives=$changed; archives=$metadata.ToArray();
    manifest_sha256=(Get-FileHash -LiteralPath $manifestPath).Hash;
    captured_utc=[DateTime]::UtcNow.ToString('o'); game_writes=0; save_writes=0
} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $evidence 'capture_summary.json') -Encoding utf8NoBOM
Write-Output "Capture finished with $count provider inputs, $cacheCount verified caches and $errors opaque"
