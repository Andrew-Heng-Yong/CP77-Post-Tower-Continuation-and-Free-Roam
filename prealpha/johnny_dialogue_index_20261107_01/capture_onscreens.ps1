Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$output = Join-Path $PSScriptRoot 'evidence_02'
$exports = Join-Path $PSScriptRoot 'exports_onscreens_01'
if ((Test-Path -LiteralPath $output) -or (Test-Path -LiteralPath $exports)) { throw 'Use fresh onscreen outputs' }
$prepared = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/prepared.json') -Raw | ConvertFrom-Json -Depth 100
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
New-Item -ItemType Directory -Path $output,$exports | Out-Null
$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$rows = [Collections.Generic.List[object]]::new()
foreach ($archiveInfo in $prepared.archives) {
    $file = Get-Item -LiteralPath $archiveInfo.path
    $time = ([DateTime]$archiveInfo.mtime_utc).ToUniversalTime()
    if ($file.Length -ne $archiveInfo.bytes -or $file.LastWriteTimeUtc.Ticks -ne $time.Ticks) { throw 'Archive baseline changed' }
    if ($archiveInfo.role -ceq 'STOCK' -and $file.Name -cne 'lang_en_text.archive') { continue }
    $archive = $null
    if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hashService,[ref]$archive).ToString() -cne 'NoError') {
        throw "Unreadable archive $($file.FullName)"
    }
    foreach ($entry in $archive.Files.Values) {
        if ($entry.Name -notmatch '\\localization\\en-us\\onscreens\\.*\.json$') { continue }
        $directory = Join-Path $exports $archiveInfo.index
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
        $raw = Join-Path $directory ($entry.Key.ToString()+'.json')
        $memory = [IO.MemoryStream]::new()
        try { $entry.Extract($memory);$bytes=$memory.ToArray() } finally { $memory.Dispose() }
        [IO.File]::WriteAllBytes($raw,$bytes)
        $rawHash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
        $json = $raw+'.export.json'
        $errorText = $null
        $status = 'EXPORTED'
        try { Export-Cr2wJson (Read-Cr2wFile $raw) $json } catch { $status='OPAQUE';$errorText=$_.Exception.Message;$json=$null }
        $identity = $file.FullName.ToLowerInvariant()+'|'+$entry.Key.ToString()
        $id = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($identity))).Substring(0,24).ToLowerInvariant()
        $rows.Add(@{
            resource_id=$id;kind='ENGLISH_ONSCREENS';depot=$entry.Name;key=$entry.Key.ToString();
            archive=$file.FullName;archive_index=$archiveInfo.index;provider_role=$archiveInfo.role;
            scope='AUXILIARY_SOURCE';raw=$raw;sha256=$rawHash;json=$json;
            json_sha256=$(if($json){(Get-FileHash -LiteralPath $json).Hash}else{$null});
            status=$status;root_type='JsonResource';error=$errorText
        })
    }
}
$manifest = Join-Path $output 'onscreens.jsonl'
$rows | ForEach-Object { $_ | ConvertTo-Json -Depth 10 -Compress } | Set-Content -LiteralPath $manifest -Encoding utf8NoBOM
@{schema=1;resources=$rows.Count;manifest_sha256=(Get-FileHash -LiteralPath $manifest).Hash;game_writes=0;save_writes=0} |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $output 'capture_summary.json') -Encoding utf8NoBOM
Write-Output "Captured $($rows.Count) onscreen providers"
