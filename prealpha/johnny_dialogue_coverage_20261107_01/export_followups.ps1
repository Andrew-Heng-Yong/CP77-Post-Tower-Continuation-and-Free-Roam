Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$requests=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'evidence_04/requests.json') -Raw | ConvertFrom-Json -Depth 100
$out=Join-Path $PSScriptRoot 'evidence_05'
if(Test-Path -LiteralPath $out){throw 'Use a fresh export directory'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hashService=[WolvenKit.Common.Services.HashService]::new();$hashService.Load()
New-Item -ItemType Directory -Path $out | Out-Null
$writer=[IO.StreamWriter]::new((Join-Path $out 'exports.jsonl'),$false,[Text.UTF8Encoding]::new($false))
$count=0;$errors=0
try{
    foreach($group in ($requests.resources | Group-Object archive)){
        $archiveInfo=$requests.archives | Where-Object {$_.path -ceq $group.Name}
        $file=Get-Item -LiteralPath $group.Name
        if($file.Length -ne $archiveInfo.bytes -or $file.LastWriteTimeUtc.Ticks -ne ([DateTime]$archiveInfo.mtime_utc).ToUniversalTime().Ticks){throw 'Archive changed'}
        $archive=$null
        $code=([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hashService,[ref]$archive)
        if($code.ToString() -cne 'NoError'){throw 'Archive unreadable'}
        $folder=Join-Path $out $archiveInfo.index
        New-Item -ItemType Directory -Path $folder | Out-Null
        foreach($source in $group.Group){
            $row=[ordered]@{archive=$source.archive;key=$source.key;depot=$source.depot;reasons=$source.reasons;
                raw=$source.raw;sha256=$null;json=$null;json_sha256=$null;status='PENDING';root_type=$null;error=$null}
            try{
                if(!$row.raw){
                    $entry=$archive.Files[[uint64]$source.key]
                    $memory=[IO.MemoryStream]::new()
                    try{$entry.Extract($memory);$bytes=$memory.ToArray()}finally{$memory.Dispose()}
                    $row.raw=Join-Path $folder ($source.key + '.bin')
                    [IO.File]::WriteAllBytes($row.raw,$bytes)
                }
                $row.sha256=(Get-FileHash -LiteralPath $row.raw).Hash
                if($source.sha256 -and $source.sha256 -cne $row.sha256){throw 'Source hash changed'}
                $resource=Read-Cr2wFile $row.raw
                $row.root_type=$resource.RootChunk.GetType().Name
                $text=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize(
                    [WolvenKit.Common.Conversion.RedFileDto]::new($resource,$false),
                    [WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
                $row.json=Join-Path $folder ($source.key + '.json.gz')
                $stream=[IO.File]::Create($row.json)
                try{
                    $gzip=[IO.Compression.GZipStream]::new($stream,[IO.Compression.CompressionLevel]::Fastest,$true)
                    try{
                        $textWriter=[IO.StreamWriter]::new($gzip,[Text.UTF8Encoding]::new($false))
                        try{$textWriter.Write($text)}finally{$textWriter.Dispose()}
                    }finally{$gzip.Dispose()}
                }finally{$stream.Dispose()}
                $row.json_sha256=(Get-FileHash -LiteralPath $row.json).Hash;$row.status='EXPORTED'
            }catch{$row.status='OPAQUE';$row.error=$_.Exception.Message;$row.json=$null;$errors++}
            $writer.WriteLine(($row | ConvertTo-Json -Depth 8 -Compress));$writer.Flush();$count++
            if($count % 20 -eq 0){Write-Output "Exported $count sources, $errors opaque"}
        }
    }
}finally{$writer.Dispose()}
$changes=@(foreach($info in $requests.archives){
    $file=Get-Item -LiteralPath $info.path
    if($file.Length -ne $info.bytes -or $file.LastWriteTimeUtc.Ticks -ne ([DateTime]$info.mtime_utc).ToUniversalTime().Ticks){$info.path}
})
@{count=$count;opaque=$errors;changed_archives=$changes;
manifest_sha256=(Get-FileHash -LiteralPath (Join-Path $out 'exports.jsonl')).Hash;game_writes=0;save_writes=0} |
ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $out 'summary.json') -Encoding utf8NoBOM
if($changes.Count){throw 'Archive inputs changed'}
Write-Output "Completed $count source exports with $errors opaque"
