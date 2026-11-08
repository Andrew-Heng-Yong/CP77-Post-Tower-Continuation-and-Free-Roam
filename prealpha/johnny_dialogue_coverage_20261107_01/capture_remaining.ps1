Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$prepared = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/prepared.json') -Raw | ConvertFrom-Json -Depth 100
$out = Join-Path $PSScriptRoot 'evidence_03'
if (Test-Path -LiteralPath $out) { throw 'Use a fresh inventory directory' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hashService=[WolvenKit.Common.Services.HashService]::new();$hashService.Load()
$prior=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($line in [IO.File]::ReadLines((Join-Path $PSScriptRoot 'evidence_02/tables.jsonl'))) {
    $row=$line | ConvertFrom-Json -Depth 30
    [void]$prior.Add($row.archive + '|' + $row.key)
}
$captured=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($row in $prepared.captured_graph_providers) { [void]$captured.Add($row.archive + '|' + $row.key) }
$frozen=[Collections.Generic.List[object]]::new()
$unknownCounts=[Collections.Generic.List[object]]::new()
$graphExtensions=@('.quest','.questphase','.scene','.gamedef','.game')
# Complete the name census before parsing any payload. CR2W table reads can resolve
# previously unknown depot names for later archive entries through HashService.
foreach ($archiveInfo in $prepared.archives) {
    $file=Get-Item -LiteralPath $archiveInfo.path
    if ($file.Length -ne $archiveInfo.bytes -or $file.LastWriteTimeUtc.Ticks -ne ([DateTime]$archiveInfo.mtime_utc).ToUniversalTime().Ticks) { throw 'Archive baseline changed' }
    $archive=$null
    $code=([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hashService,[ref]$archive)
    if ($code.ToString() -cne 'NoError') { throw 'Unreadable archive' }
    $unnamedCount=0
    foreach ($entry in $archive.Files.Values) {
        $unnamed=$entry.Name -match '^[0-9]+(?:\.[a-zA-Z0-9_]+)?$'
        if ($unnamed) { $unnamedCount++ }
        $isGraph=$entry.Extension -in $graphExtensions
        $isSpeechMetadata=$entry.Extension -in @('.voicetags','.audio_metadata','.conversations')
        if (!($unnamed -or $isGraph -or $isSpeechMetadata)) { continue }
        $id=$file.FullName + '|' + $entry.Key.ToString()
        $frozen.Add(@{
            archive=$file.FullName;archive_index=$archiveInfo.index;provider_role=$archiveInfo.role;
            key=$entry.Key.ToString();depot=$entry.Name;extension=$entry.Extension;unnamed=[bool]$unnamed;
            bytes=[long]$entry.Size;prior_table=$prior.Contains($id);prior_graph_imports=$captured.Contains($id);
            is_graph=[bool]$isGraph;speech_metadata=[bool]$isSpeechMetadata
        })
    }
    $unknownCounts.Add(@{archive=$file.FullName;expected=$archiveInfo.unnamed_entries;observed=$unnamedCount})
}
New-Item -ItemType Directory -Path $out | Out-Null
@{rows=$frozen.ToArray();unknown_counts=$unknownCounts.ToArray()} | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $out 'frozen_inventory.json') -Encoding utf8NoBOM
$writer=[IO.StreamWriter]::new((Join-Path $out 'tables.jsonl'),$false,[Text.UTF8Encoding]::new($false))
$count=0
try {
    foreach ($group in ($frozen | Where-Object { !$_.prior_table -and !$_.prior_graph_imports } | Group-Object archive_index)) {
        $archive=$null
        $archiveInfo=$prepared.archives[[int]$group.Name]
        $code=([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archiveInfo.path,$hashService,[ref]$archive)
        if ($code.ToString() -cne 'NoError') { throw 'Unreadable archive' }
        foreach ($source in $group.Group) {
            $entry=$archive.Files[[uint64]$source.key]
            $row=[ordered]@{
                archive=$source.archive;archive_index=$source.archive_index;provider_role=$source.provider_role;
                key=$source.key;depot=$source.depot;extension=$source.extension;unnamed=$source.unnamed;
                uncaptured_graph=$source.is_graph;request_reasons=@('FROZEN_NAME_CENSUS');requested_depot=$null;
                bytes=$source.bytes;status='PENDING';sha256=$null;magic=$null;root_type=$null;
                imports=@();export_classes=@();embedded_count=$null;speech_name_leads=@();error=$null
            }
            try {
                if ($entry.Size -gt 134217728) { $row.status='SIZE_BOUNDED_NOT_EXTRACTED' } else {
                    $memory=[IO.MemoryStream]::new()
                    try { $entry.Extract($memory);$bytes=$memory.ToArray() } finally { $memory.Dispose() }
                    $row.sha256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
                    $row.magic=[Convert]::ToHexString($bytes[0..([Math]::Min(15,$bytes.Length-1))])
                    if ($bytes.Length -ge 4 -and [Text.Encoding]::ASCII.GetString($bytes,0,4) -ceq 'CR2W') {
                        $memory=[IO.MemoryStream]::new($bytes,$false)
                        try {
                            $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($memory);$info=$null
                            $code=$reader.ReadFileInfo([ref]$info,$null)
                            if ($code.ToString() -cne 'NoError' -or $info.ExportInfo.Count -eq 0) { throw 'No CR2W tables' }
                            $names=@($info.NameInfo | ForEach-Object {$info.StringDict[$_.offset]})
                            $row.root_type=$names[$info.ExportInfo[0].className]
                            $row.imports=@($info.ImportInfo | ForEach-Object {$info.StringDict[$_.offset]} | Sort-Object -Unique)
                            $row.export_classes=@($info.ExportInfo | ForEach-Object {$names[$_.className]} | Sort-Object -Unique)
                            $row.embedded_count=$info.EmbeddedInfo.Count
                            $row.speech_name_leads=@($info.StringDict.Values | Where-Object { $_ -match '(?i)(johnny|silverhand|voiceset|voiceover|dialogline|playvoice|playsound|bark)' } | Sort-Object -Unique)
                            $row.status='CR2W_TABLES_READ'
                        } finally { $memory.Dispose() }
                    } else { $row.status='NON_CR2W_SIGNATURE' }
                }
            } catch { $row.status='TABLE_OPAQUE';$row.error=$_.Exception.Message }
            $writer.WriteLine(($row | ConvertTo-Json -Depth 12 -Compress));$writer.Flush();$count++
        }
        Write-Output "Recovered $count remaining table inputs"
    }
} finally { $writer.Dispose() }
$changes=@(foreach($info in $prepared.archives) {
    $file=Get-Item -LiteralPath $info.path
    if ($file.Length -ne $info.bytes -or $file.LastWriteTimeUtc.Ticks -ne ([DateTime]$info.mtime_utc).ToUniversalTime().Ticks) { $info.path }
})
@{rows=$count;changed_archives=$changes;frozen_sha256=(Get-FileHash -LiteralPath (Join-Path $out 'frozen_inventory.json')).Hash;
tables_sha256=(Get-FileHash -LiteralPath (Join-Path $out 'tables.jsonl')).Hash;game_writes=0;save_writes=0} |
    ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $out 'summary.json') -Encoding utf8NoBOM
if ($changes.Count) { throw 'Archives changed' }
Write-Output "Frozen unnamed census: $(($unknownCounts | Measure-Object -Property observed -Sum).Sum) entries; $count supplementary table reads"
