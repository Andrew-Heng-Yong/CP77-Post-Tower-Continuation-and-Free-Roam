param([int]$MaxResources = 20000)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$output = Join-Path $PSScriptRoot 'step1_01'
$evidence = Join-Path $PSScriptRoot 'evidence_01'
if (Test-Path -LiteralPath $evidence) { throw 'Use fresh evidence output' }
$query = Get-Content -LiteralPath (Join-Path $output 'queries.json') -Raw | ConvertFrom-Json -Depth 100
$baseline = Get-Content -LiteralPath (Join-Path $output 'baseline.json') -Raw | ConvertFrom-Json -Depth 100
if ($baseline.status -cne 'VERIFIED') { throw 'A verified baseline is required' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
New-Item -ItemType Directory -Path $evidence | Out-Null

$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$graphExtensions = @('.quest', '.questphase', '.scene', '.gamedef')
$followExtensions = $graphExtensions + @('.ent', '.app', '.streamingblock', '.streamingsector')
$firstProvider = [Collections.Generic.Dictionary[uint64,int]]::new()
$extraProviders = [Collections.Generic.Dictionary[uint64,Collections.Generic.List[int]]]::new()
$archives = [Collections.Generic.List[object]]::new()
$graphs = [Collections.Generic.List[object]]::new()
$privateReadback = [Collections.Generic.List[object]]::new()
$privateByKey = [Collections.Generic.Dictionary[uint64,object]]::new()
$archiveReaders = @{}
$wanted = [Collections.Generic.Dictionary[string,uint64]]::new([StringComparer]::Ordinal)
$queue = [Collections.Generic.Queue[string]]::new()
$done = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
$resources = [Collections.Generic.List[object]]::new()
$missing = [Collections.Generic.List[object]]::new()
$opaque = [Collections.Generic.List[object]]::new()
$graphPattern = [regex]'(?:base|ep1|towercontinued|dlc|lizzies)\\[A-Za-z0-9_\\.-]+\.(?:questphase|scene|quest|gamedef)(?![A-Za-z0-9_.\\])'

function Resource-Key([string]$depot) {
    if ($depot -match '^[0-9]+$') { return [uint64]$depot }
    return [uint64][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
}

function Add-Wanted([string]$depot) {
    if (!$depot -or $depot -in @('0', 'None')) { return }
    if (!$wanted.ContainsKey($depot)) {
        $wanted.Add($depot, (Resource-Key $depot))
        $queue.Enqueue($depot)
    }
}

function Bytes-Hash([byte[]]$bytes) {
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
}

function Open-Archive([string]$path) {
    $archive = $null
    $status = ([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path, $hashService, [ref]$archive)
    if ($status.ToString() -cne 'NoError') { throw "Unreadable archive $path" }
    return $archive
}

function Extract-Bytes($entry) {
    $memory = [IO.MemoryStream]::new()
    try {
        $entry.Extract($memory)
        return ,$memory.ToArray()
    } finally { $memory.Dispose() }
}

foreach ($row in $query.private) {
    $key = Resource-Key $row.depot
    if ($privateByKey.ContainsKey($key)) { throw "Private resource key collision $($row.depot)" }
    $privateByKey.Add($key, $row)
}

$archiveFiles = @(Get-ChildItem -LiteralPath (Join-Path $query.game_root 'archive/pc') -Filter '*.archive' -Recurse -File | Sort-Object FullName)
foreach ($file in $archiveFiles) {
    $archive = Open-Archive $file.FullName
    $archiveIndex = $archives.Count
    $relative = [IO.Path]::GetRelativePath($query.game_root, $file.FullName).Replace('\', '/')
    $role = if ($relative -match '^archive/pc/(content|ep1)/') { 'STOCK' } else { 'MOD_CANDIDATE' }
    $owned = $relative -ceq 'archive/pc/mod/zzzz_PTFR_Combined.archive'
    $extensionCounts = @{}
    $unnamed = 0
    foreach ($entry in $archive.Files.Values) {
        $key = [uint64]$entry.Key
        if ($firstProvider.ContainsKey($key)) {
            if (!$extraProviders.ContainsKey($key)) {
                $extraProviders.Add($key, [Collections.Generic.List[int]]::new())
            }
            $extraProviders[$key].Add($archiveIndex)
        } else { $firstProvider.Add($key, $archiveIndex) }
        $extension = $entry.Extension
        if (!$extension) { $extension = '<unknown>' }
        if (!$extensionCounts.ContainsKey($extension)) { $extensionCounts[$extension] = 0 }
        $extensionCounts[$extension]++
        if ($entry.Name -match '^[0-9]+(?:\.[a-zA-Z0-9_]+)?$') { $unnamed++ }
        if ($extension -in $graphExtensions) {
            $graphs.Add(@{ key=$key.ToString(); depot=$entry.Name; archive_index=$archiveIndex; role=$role; extension=$extension })
        }
        if ($owned) {
            if (!$privateByKey.ContainsKey($key)) { throw "Unexpected combined-archive member $key" }
            $expected = $privateByKey[$key]
            $actual = Bytes-Hash (Extract-Bytes $entry)
            if ($actual -cne $expected.sha256) { throw "Combined archive/source mismatch $($expected.depot)" }
            $privateReadback.Add(@{ depot=$expected.depot; key=$key.ToString(); sha256=$actual })
        }
    }
    $archives.Add(@{
        index=$archiveIndex; path=$file.FullName; bytes=$file.Length;
        mtime_utc=$file.LastWriteTimeUtc.ToString('o'); members=$archive.Files.Count;
        role=$role; extension_counts=$extensionCounts; unnamed_entries=$unnamed
    })
    if ($owned) { $archiveReaders[$archiveIndex] = $archive }
    if ($archives.Count % 20 -eq 0) {
        Write-Output "Indexed $($archives.Count)/$($archiveFiles.Count) archives and $($graphs.Count) graph providers"
    }
}
if ($privateReadback.Count -ne $query.private.Count) { throw 'Incomplete combined archive readback' }

foreach ($depot in $query.wanted) { Add-Wanted $depot }
$processed = 0
while ($queue.Count -gt 0 -and $processed -lt $MaxResources) {
    # Group each frontier by archive to avoid reopening archives for each dependency.
    $frontier = [Collections.Generic.List[string]]::new()
    while ($queue.Count -gt 0) {
        $depot = $queue.Dequeue()
        if ($done.Add($depot)) { $frontier.Add($depot) }
    }
    $byArchive = @{}
    foreach ($depot in $frontier) {
        $key = $wanted[$depot]
        if (!$firstProvider.ContainsKey($key)) {
            $missing.Add(@{ depot=$depot; key=$key.ToString() })
            continue
        }
        $indices = @($firstProvider[$key])
        if ($extraProviders.ContainsKey($key)) { $indices += $extraProviders[$key].ToArray() }
        foreach ($index in $indices) {
            if (!$byArchive.ContainsKey($index)) { $byArchive[$index] = [Collections.Generic.List[string]]::new() }
            $byArchive[$index].Add($depot)
        }
    }
    foreach ($index in @($byArchive.Keys | Sort-Object)) {
        $archiveInfo = $archives[$index]
        $archive = if ($archiveReaders.ContainsKey($index)) { $archiveReaders[$index] } else { Open-Archive $archiveInfo.path }
        foreach ($depot in $byArchive[$index]) {
            $key = $wanted[$depot]
            $bytes = Extract-Bytes $archive.Files[$key]
            $hash = Bytes-Hash $bytes
            $isPrivatePayload = $archiveInfo.path -ceq (Join-Path $query.game_root 'archive/pc/mod/zzzz_PTFR_Combined.archive')
            $raw = if ($isPrivatePayload) { $privateByKey[$key].path } else {
                $directory = Join-Path $evidence ('raw/' + $index)
                New-Item -ItemType Directory -Path $directory -Force | Out-Null
                $target = Join-Path $directory ($key.ToString() + [IO.Path]::GetExtension($depot))
                if (!(Test-Path -LiteralPath $target)) { [IO.File]::WriteAllBytes($target, $bytes) }
                $target
            }
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
                $opaque.Add(@{ depot=$depot; archive=$archiveInfo.path; sha256=$hash; error=$errorText })
            }
            $binaryCandidates = @($graphPattern.Matches([Text.Encoding]::UTF8.GetString($bytes)) | ForEach-Object Value | Sort-Object -Unique)
            $attachmentOnly = $depot -in $query.attachment_only_parents
            if (!$attachmentOnly) {
                foreach ($reference in @($imports + $binaryCandidates | Sort-Object -Unique)) {
                    if ([IO.Path]::GetExtension($reference) -in $followExtensions) { Add-Wanted $reference }
                }
            }
            $resources.Add(@{
                depot=$depot; key=$key.ToString(); archive_index=$index; archive=$archiveInfo.path;
                provider_role=$archiveInfo.role; sha256=$hash; raw=$raw; status=$status;
                root_type=$rootType; imports=$imports; binary_graph_reference_candidates=$binaryCandidates;
                attachment_only=$attachmentOnly; error=$errorText
            })
        }
        if (!$archiveReaders.ContainsKey($index)) { $archive = $null }
    }
    $processed += $frontier.Count
    Write-Output "Captured $processed resource queries, $($resources.Count) providers, $($queue.Count) pending, $($opaque.Count) opaque"
}

$changedArchives = @(
    foreach ($row in $archives) {
        $current = Get-Item -LiteralPath $row.path
        if ($current.Length -ne $row.bytes -or $current.LastWriteTimeUtc.ToString('o') -cne $row.mtime_utc) {
            @{ path=$row.path; status='ARCHIVE_CHANGED_DURING_CAPTURE' }
        }
    }
)
$additionalArchives = @(
    foreach ($relativeRoot in @('mods', 'r6/cache/modded')) {
        $root = Join-Path $query.game_root $relativeRoot
        if (Test-Path -LiteralPath $root) {
            Get-ChildItem -LiteralPath $root -Filter '*.archive' -Recurse -File | ForEach-Object {
                @{ path=$_.FullName; bytes=$_.Length; mtime_utc=$_.LastWriteTimeUtc.ToString('o'); load_state='UNRESOLVED_OUTSIDE_ARCHIVE_PC' }
            }
        }
    }
)
$result = @{
    schema=1; captured_utc=[DateTime]::UtcNow.ToString('o'); archives=$archives.ToArray();
    graph_provider_census=$graphs.ToArray(); private_readback=$privateReadback.ToArray();
    resources=$resources.ToArray(); missing=$missing.ToArray(); opaque=$opaque.ToArray();
    pending=$queue.ToArray(); queried=$wanted.Count; changed_archives=$changedArchives;
    additional_archive_locations=$additionalArchives;
    limits=@(
        'Reference closure includes stored branches and does not establish post-Tower execution.',
        'Archive census order is lexical inventory order and does not establish provider precedence.',
        'Every matching provider is retained and its dependency references are followed.',
        'Graph imports, entity and appearance support, and streaming support are followed. Other asset imports remain indexed references.',
        'XL parent resources are inspected as attachment interfaces without traversing the complete parent campaign.',
        'Opaque resources, unnamed archive keys, dynamic source references and external load states require explicit follow-up.'
    );
    game_writes=0; save_writes=0
}
$result | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath (Join-Path $output 'capture.json') -Encoding utf8NoBOM
@{ status='CAPTURE_RECORDED'; archives=$archives.Count; graph_providers=$graphs.Count; private_readback=$privateReadback.Count; providers=$resources.Count; missing=$missing.Count; opaque=$opaque.Count; pending=$queue.Count } | ConvertTo-Json -Compress
