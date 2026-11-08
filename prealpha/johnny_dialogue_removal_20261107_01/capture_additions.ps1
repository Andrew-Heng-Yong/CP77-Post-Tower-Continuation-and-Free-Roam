param([int]$MaxRounds = 12)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$output = Join-Path $PSScriptRoot 'step1_01'
$evidence = Join-Path $PSScriptRoot 'evidence_03'
if (Test-Path -LiteralPath $evidence) { throw 'Use a fresh supplemental output' }
$capture = Get-Content -LiteralPath (Join-Path $output 'capture.json') -Raw | ConvertFrom-Json -Depth 100
$refinement = Get-Content -LiteralPath (Join-Path $output 'refinement.json') -Raw | ConvertFrom-Json -Depth 100
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
New-Item -ItemType Directory -Path $evidence | Out-Null
$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$done = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
$wanted = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
$resources = [Collections.Generic.List[object]]::new()
$missing = [Collections.Generic.List[object]]::new()
$opaque = [Collections.Generic.List[object]]::new()
$follow = @('.quest', '.questphase', '.scene', '.gamedef', '.ent', '.app', '.streamingblock', '.streamingsector')
$graphPattern = [regex]'(?:[A-Za-z0-9_.-]+\\)+[A-Za-z0-9_.-]+\.(?:questphase|scene|quest|gamedef)(?![A-Za-z0-9_.\\-])'
foreach ($row in $capture.resources) { [void]$done.Add($row.depot) }
foreach ($row in $capture.missing) { [void]$done.Add($row.depot) }
foreach ($depot in @($refinement.wanted) + @($capture.pending)) { [void]$wanted.Add($depot) }
$initialQueries = @($wanted | Where-Object { !$done.Contains($_) })
$archivesChanged = @()
for ($round = 0; $round -lt $MaxRounds; $round++) {
    $pending = @($wanted | Where-Object { !$done.Contains($_) })
    if (!$pending.Count) { break }
    $keys = @{}
    $hits = @{}
    foreach ($depot in $pending) {
        $key = if ($depot -match '^[0-9]+$') { [uint64]$depot } else {
            [uint64][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
        }
        $keys[$key] = $depot
        $hits[$depot] = 0
    }
    foreach ($archiveInfo in $capture.archives) {
        $file = Get-Item -LiteralPath $archiveInfo.path
        $expectedTime = ([DateTime]$archiveInfo.mtime_utc).ToUniversalTime()
        if ($file.Length -ne $archiveInfo.bytes -or $file.LastWriteTimeUtc.Ticks -ne $expectedTime.Ticks) {
            throw "Archive changed since initial capture $($file.FullName)"
        }
        $archive = $null
        if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName, $hashService, [ref]$archive).ToString() -cne 'NoError') {
            throw "Unreadable archive $($file.FullName)"
        }
        foreach ($key in $keys.Keys) {
            if (!$archive.Files.ContainsKey([uint64]$key)) { continue }
            $depot = $keys[$key]
            $hits[$depot]++
            $directory = Join-Path $evidence ('raw/' + $archiveInfo.index)
            New-Item -ItemType Directory -Path $directory -Force | Out-Null
            $raw = Join-Path $directory ($key.ToString() + [IO.Path]::GetExtension($depot))
            $memory = [IO.MemoryStream]::new()
            try {
                $archive.Files[[uint64]$key].Extract($memory)
                $bytes = $memory.ToArray()
            } finally { $memory.Dispose() }
            [IO.File]::WriteAllBytes($raw, $bytes)
            $hash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
            $imports = @()
            $rootType = $null
            $errorText = $null
            $status = 'IMPORTS_DECODED'
            try {
                $resource = Read-Cr2wFile $raw
                $rootType = $resource.RootChunk.GetType().Name
                $imports = @($resource.GetImports() | ForEach-Object ToString | Sort-Object -Unique)
            } catch {
                $status = 'OPAQUE'
                $errorText = $_.Exception.Message
                $opaque.Add(@{ depot=$depot; archive=$file.FullName; sha256=$hash; error=$errorText })
            }
            $binaryCandidates = @($graphPattern.Matches([Text.Encoding]::UTF8.GetString($bytes)) | ForEach-Object Value | Sort-Object -Unique)
            $attachmentOnly = $depot -in $refinement.attachment_only_parents
            if (!$attachmentOnly) {
                foreach ($reference in @($imports + $binaryCandidates | Sort-Object -Unique)) {
                    if ([IO.Path]::GetExtension($reference) -in $follow) { [void]$wanted.Add($reference) }
                }
            }
            $resources.Add(@{
                depot=$depot; key=$key.ToString(); archive_index=$archiveInfo.index; archive=$file.FullName;
                provider_role=$archiveInfo.role; sha256=$hash; raw=$raw; status=$status; root_type=$rootType;
                imports=$imports; binary_graph_reference_candidates=$binaryCandidates; attachment_only=$attachmentOnly; error=$errorText
            })
        }
    }
    foreach ($depot in $pending) {
        [void]$done.Add($depot)
        if (!$hits[$depot]) { $missing.Add(@{ depot=$depot; key=''; origin='SUPPLEMENTAL_QUERY' }) }
    }
    Write-Output "Supplement round $round captured $($resources.Count) providers, $($missing.Count) missing, $(@($wanted | Where-Object { !$done.Contains($_) }).Count) pending"
}
$result = @{
    schema=1; initial_capture_sha256=(Get-FileHash -LiteralPath (Join-Path $output 'capture.json')).Hash;
    refinement_sha256=(Get-FileHash -LiteralPath (Join-Path $output 'refinement.json')).Hash;
    initial_queries=$initialQueries; resources=$resources.ToArray(); missing=$missing.ToArray(); opaque=$opaque.ToArray();
    pending=@($wanted | Where-Object { !$done.Contains($_) }); changed_archives=$archivesChanged;
    game_writes=0; save_writes=0
}
$result | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath (Join-Path $output 'capture_additions.json') -Encoding utf8NoBOM
@{ status='SUPPLEMENT_RECORDED'; providers=$resources.Count; missing=$missing.Count; opaque=$opaque.Count; pending=$result.pending.Count } | ConvertTo-Json -Compress
