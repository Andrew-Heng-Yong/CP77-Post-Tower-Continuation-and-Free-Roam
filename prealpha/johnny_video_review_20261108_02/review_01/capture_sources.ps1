Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$queryPath = Join-Path $PSScriptRoot 'source_queries.json'
$batchReviewRequest = Get-Content -LiteralPath $queryPath -Raw | ConvertFrom-Json -Depth 20
$output = Join-Path $PSScriptRoot 'source_01'
if (Test-Path -LiteralPath $output) { throw 'Fresh capture required' }
foreach ($pin in $batchReviewRequest.pins) {
    if ((Get-FileHash -LiteralPath $pin.path).Hash -cne $pin.sha256) { throw "Source pin changed: $($pin.path)" }
}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
New-Item -ItemType Directory -Path $output | Out-Null
$hashes = [WolvenKit.Common.Services.HashService]::new()
$hashes.Load()
$lookup = @{}
foreach ($query in $batchReviewRequest.queries) {
    $key = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($query.depot).ToString()
    if ($lookup.ContainsKey($key)) { throw 'Duplicate query depot key' }
    $lookup[$key] = $query
}
$resources = [Collections.Generic.List[object]]::new()
$archives = [Collections.Generic.List[object]]::new()
foreach ($file in Get-ChildItem -LiteralPath (Join-Path $batchReviewRequest.game_root 'archive/pc') -Recurse -File -Filter '*.archive') {
    if ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked archive refused' }
    $archive = $null
    $result = ([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hashes,[ref]$archive)
    if ($result.ToString() -cne 'NoError') { throw "Unreadable archive: $($file.FullName)" }
    $archives.Add(@{ path=$file.FullName; bytes=$file.Length; mtime_utc=$file.LastWriteTimeUtc.ToString('o') })
    foreach ($key in $lookup.Keys) {
        if (-not $archive.Files.ContainsKey([uint64]$key)) { continue }
        $query = $lookup[$key]
        $memory = [IO.MemoryStream]::new()
        try {
            [void]$archive.Files[[uint64]$key].Extract($memory)
            $bytes = $memory.ToArray()
        } finally { $memory.Dispose() }
        $provider = '{0:D3}_{1}' -f $archives.Count,$file.BaseName
        $raw = Join-Path $output ($provider + '/' + $key + [IO.Path]::GetExtension($query.depot))
        New-Item -ItemType Directory -Force -Path (Split-Path $raw -Parent) | Out-Null
        [IO.File]::WriteAllBytes($raw,$bytes)
        $row = @{ depot=$query.depot; scope=$query.scope; archive=$file.FullName; key=$key; raw=$raw; sha256=(Get-FileHash -LiteralPath $raw).Hash; json=$null; json_sha256=$null; decode_error=$null }
        try {
            Export-Cr2wJson (Read-Cr2wFile $raw) ($raw+'.json')
            $row.json = $raw+'.json'
            $row.json_sha256 = (Get-FileHash -LiteralPath $row.json).Hash
        } catch { $row.decode_error = $_.Exception.Message }
        $resources.Add($row)
    }
}
$issues = @(foreach ($query in $batchReviewRequest.queries) {
    $found = @($resources | Where-Object { $_.depot -ceq $query.depot })
    if ($found.Count -ne 1 -or @($found | Where-Object {
        $_.archive -ine $query.expected_archive -or $_.sha256 -cne $query.expected_sha256 -or $_.decode_error
    }).Count) {
        @{ depot=$query.depot; expected=$query.expected_sha256; expected_archive=$query.expected_archive; found=$found }
    }
})
$status = if ($issues.Count) { 'SOURCE_REVIEW_REQUIRED' } else { 'PASS_BATCH3_CURRENT_PROVIDER_PINS' }
@{ status=$status; query_sha256=(Get-FileHash -LiteralPath $queryPath).Hash; archives=@($archives); resources=@($resources); issues=$issues; game_writes=0; save_writes=0 } |
    ConvertTo-Json -Depth 15 | Set-Content -LiteralPath (Join-Path $output 'manifest.json') -Encoding utf8NoBOM
Write-Output "$status. $($resources.Count) resources, $($archives.Count) archive indices, $($issues.Count) issues."
