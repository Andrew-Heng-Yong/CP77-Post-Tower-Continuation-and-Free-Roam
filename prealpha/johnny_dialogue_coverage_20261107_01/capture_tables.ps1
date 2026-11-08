param([long]$MaximumMemberBytes = 134217728)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$preparedPath = Join-Path $PSScriptRoot 'evidence_01/prepared.json'
$prepared = Get-Content -LiteralPath $preparedPath -Raw | ConvertFrom-Json -Depth 100
$evidence = Join-Path $PSScriptRoot 'evidence_02'
if (Test-Path -LiteralPath $evidence) { throw 'Use a fresh table capture directory' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$requests = [Collections.Generic.Dictionary[uint64,object]]::new()
foreach ($row in $prepared.table_requests) {
    $key = [uint64][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($row.depot)
    if ($requests.ContainsKey($key)) { throw "Request key collision $($row.depot)" }
    $requests.Add($key, $row)
}
$capturedGraphs = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($row in $prepared.captured_graph_providers) {
    [void]$capturedGraphs.Add($row.archive + '|' + $row.key)
}
$foundRequests = [Collections.Generic.HashSet[uint64]]::new()
$graphs = @('.scene', '.quest', '.questphase', '.gamedef')
$metadata = [Collections.Generic.List[object]]::new()
New-Item -ItemType Directory -Path $evidence | Out-Null
$writer = [IO.StreamWriter]::new((Join-Path $evidence 'tables.jsonl'), $false, [Text.UTF8Encoding]::new($false))
$count = 0
$opaqueCount = 0
$unknownCount = 0

function Table-Info([byte[]]$bytes) {
    $memory = [IO.MemoryStream]::new($bytes, $false)
    try {
        $reader = [WolvenKit.RED4.Archive.IO.CR2WReader]::new($memory)
        $info = $null
        $code = $reader.ReadFileInfo([ref]$info, $null)
        if ($code.ToString() -cne 'NoError') { throw "ReadFileInfo: $code" }
        if ($info.ExportInfo.Count -eq 0) { throw 'CR2W has no exports' }
        $names = @($info.NameInfo | ForEach-Object { $info.StringDict[$_.offset] })
        $imports = @($info.ImportInfo | ForEach-Object { $info.StringDict[$_.offset] } | Sort-Object -Unique)
        $classes = @($info.ExportInfo | ForEach-Object { $names[$_.className] } | Sort-Object -Unique)
        return @{
            root_type=$names[$info.ExportInfo[0].className]; imports=$imports;
            export_classes=$classes; embedded_count=$info.EmbeddedInfo.Count;
            speech_name_leads=@($info.StringDict.Values | Where-Object {
                $_ -match '(?i)(johnny|silverhand|voiceset|voiceover|dialogline|playvoice|playsound|bark)' } | Sort-Object -Unique)
        }
    } finally { $memory.Dispose() }
}

try {
    foreach ($archiveInfo in $prepared.archives) {
        $file = Get-Item -LiteralPath $archiveInfo.path
        $expectedTime = ([DateTime]$archiveInfo.mtime_utc).ToUniversalTime()
        if ($file.Length -ne $archiveInfo.bytes -or $file.LastWriteTimeUtc.Ticks -ne $expectedTime.Ticks) {
            throw "Archive baseline changed $($file.FullName)"
        }
        $archive = $null
        $code = ([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName, $hashService, [ref]$archive)
        if ($code.ToString() -cne 'NoError') { throw "Unreadable archive $($file.FullName)" }
        $selected = 0
        foreach ($entry in $archive.Files.Values) {
            $key = [uint64]$entry.Key
            $unnamed = $entry.Name -match '^[0-9]+(?:\.[a-zA-Z0-9_]+)?$'
            $uncapturedGraph = $entry.Extension -in $graphs -and !$capturedGraphs.Contains($file.FullName + '|' + $key.ToString())
            $requested = $requests.ContainsKey($key)
            if (!($unnamed -or $uncapturedGraph -or $requested)) { continue }
            if ($requested) { [void]$foundRequests.Add($key) }
            $row = [ordered]@{
                archive=$file.FullName; archive_index=$archiveInfo.index; provider_role=$archiveInfo.role;
                key=$key.ToString(); depot=$entry.Name; extension=$entry.Extension;
                unnamed=[bool]$unnamed; uncaptured_graph=[bool]$uncapturedGraph;
                request_reasons=@(); requested_depot=$null;
                bytes=[long]$entry.Size; compressed_bytes=[long]$entry.ZSize;
                status='PENDING'; sha256=$null; magic=$null; root_type=$null;
                imports=@(); export_classes=@(); embedded_count=$null; speech_name_leads=@(); error=$null
            }
            if ($requested) {
                $row.request_reasons = $requests[$key].reasons
                $row.requested_depot = $requests[$key].depot
            }
            try {
                if ([long]$entry.Size -gt $MaximumMemberBytes) {
                    $row.status = 'SIZE_BOUNDED_NOT_EXTRACTED'
                } else {
                    $memory = [IO.MemoryStream]::new()
                    try { $entry.Extract($memory); $bytes=$memory.ToArray() } finally { $memory.Dispose() }
                    $row.bytes = $bytes.LongLength
                    $row.sha256 = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
                    $row.magic = [Convert]::ToHexString($bytes[0..([Math]::Min(15,$bytes.Length-1))])
                    if ($bytes.Length -ge 4 -and [Text.Encoding]::ASCII.GetString($bytes,0,4) -ceq 'CR2W') {
                        $table = Table-Info $bytes
                        foreach ($prop in $table.Keys) { $row[$prop] = $table[$prop] }
                        $row.status = 'CR2W_TABLES_READ'
                    } else { $row.status = 'NON_CR2W_SIGNATURE' }
                }
            } catch { $row.status='TABLE_OPAQUE'; $row.error=$_.Exception.Message; $opaqueCount++ }
            $writer.WriteLine(($row | ConvertTo-Json -Depth 12 -Compress))
            $writer.Flush()
            $count++; $selected++
            if ($unnamed) { $unknownCount++ }
        }
        $metadata.Add(@{path=$file.FullName;bytes=$file.Length;mtime_ticks=$file.LastWriteTimeUtc.Ticks;members=$archive.Files.Count})
        Write-Output "Archive $($archiveInfo.index): $selected table inputs; total $count, unnamed $unknownCount, errors $opaqueCount"
    }
    # Table-only recovery preserves opaque graph/world imports without decoding their objects.
    foreach ($source in $prepared.opaque_resources) {
        $bytes = [IO.File]::ReadAllBytes($source.raw)
        $hash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
        if ($hash -cne $source.sha256) { throw "Opaque source changed $($source.raw)" }
        $row = [ordered]@{
            archive=$source.archive; archive_index=$source.archive_index; provider_role=$source.provider_role;
            key=$source.key; depot=$source.depot; extension=[IO.Path]::GetExtension($source.depot);
            unnamed=$false; uncaptured_graph=$false; request_reasons=@('ORIGINAL_OPAQUE_PAYLOAD'); requested_depot=$source.depot;
            bytes=$bytes.LongLength; compressed_bytes=$null; status='PENDING'; sha256=$hash;
            magic=[Convert]::ToHexString($bytes[0..15]); root_type=$null; imports=@(); export_classes=@();
            embedded_count=$null; speech_name_leads=@(); error=$null
        }
        try {
            $table = Table-Info $bytes
            foreach ($prop in $table.Keys) { $row[$prop] = $table[$prop] }
            $row.status='CR2W_TABLES_READ'
        } catch { $row.status='TABLE_OPAQUE';$row.error=$_.Exception.Message;$opaqueCount++ }
        $writer.WriteLine(($row | ConvertTo-Json -Depth 12 -Compress)); $writer.Flush(); $count++
    }
} finally { $writer.Dispose() }

$changes = @(
    foreach ($row in $metadata) {
        $file=Get-Item -LiteralPath $row.path
        if ($file.Length -ne $row.bytes -or $file.LastWriteTimeUtc.Ticks -ne $row.mtime_ticks) { $row.path }
    }
)
$missing = @(
    foreach ($pair in $requests.GetEnumerator()) {
        if (!$foundRequests.Contains($pair.Key)) { @{key=$pair.Key.ToString();depot=$pair.Value.depot;reasons=$pair.Value.reasons} }
    }
)
@{
    schema=1; prepared_sha256=(Get-FileHash -LiteralPath $preparedPath).Hash;
    tables_sha256=(Get-FileHash -LiteralPath (Join-Path $evidence 'tables.jsonl')).Hash;
    total_rows=$count;unnamed_entries=$unknownCount;table_errors=$opaqueCount;maximum_member_bytes=$MaximumMemberBytes;
    missing_requests=$missing;archives=$metadata.ToArray();changed_archives=$changes;
    game_writes=0;save_writes=0
} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $evidence 'summary.json') -Encoding utf8NoBOM
if ($changes.Count -gt 0) { throw 'Archive inputs changed during table capture' }
Write-Output "Completed $count table rows and $($missing.Count) absent requests"
