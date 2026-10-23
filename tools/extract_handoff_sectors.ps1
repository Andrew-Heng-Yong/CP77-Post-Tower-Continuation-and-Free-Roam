param(
    [Parameter(Mandatory=$true)][string[]]$ResourcePaths,
    [string]$OutputRoot='research/phase2b_p4/normal_candidates'
)
$ErrorActionPreference='Stop'
$wkHandoff='C:\Users\Ayong\Documents\WolvenKit-8.20.0'
foreach($assembly in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')) {
    [void][Reflection.Assembly]::LoadFrom((Join-Path $wkHandoff $assembly))
}
$hsHandoff=[WolvenKit.Common.Services.HashService]::new();$hsHandoff.Load()
$wantHandoff=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach($path in $ResourcePaths){[void]$wantHandoff.Add($path)}
$gameArchiveRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc'
$rowsHandoff=[Collections.Generic.List[object]]::new()
foreach($relative in @('content/basegame_3_nightcity.archive','ep1/ep1_1_nightcity.archive')) {
    $arcPath=Join-Path $gameArchiveRoot $relative
    $arcKey=[IO.Path]::GetFileNameWithoutExtension($arcPath)
    $archive=$null
    $result=([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($arcPath,$hsHandoff,[ref]$archive)
    if($result.ToString() -ne 'NoError'){throw "Archive read failed: $result"}
    foreach($entry in $archive.Files.Values) {
        if(-not $wantHandoff.Contains($entry.Name)){continue}
        $raw=Join-Path $OutputRoot (Join-Path $arcKey (Join-Path 'raw' $entry.Name))
        $json=Join-Path $OutputRoot (Join-Path $arcKey (Join-Path 'json' ($entry.Name+'.json')))
        New-Item -ItemType Directory -Force -Path (Split-Path $raw) | Out-Null
        $memory=[IO.MemoryStream]::new()
        try{$entry.Extract($memory);[IO.File]::WriteAllBytes($raw,$memory.ToArray())}finally{$memory.Dispose()}
        & (Join-Path $PSScriptRoot 'export_handoff_raw.ps1') -InputRaw $raw -JsonOutput $json
        $rowsHandoff.Add([pscustomobject]@{Resource=$entry.Name;Archive=$arcPath;RawOutput=$raw;JsonOutput=$json;RawSha256=(Get-FileHash -LiteralPath $raw).Hash})
    }
}
$missing=@($ResourcePaths | Where-Object {$_ -notin $rowsHandoff.Resource})
if($missing.Count){throw "Requested resources absent: $($missing -join ', ')"}
$rowsHandoff | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $OutputRoot 'inventory.json') -Encoding utf8NoBOM
$rowsHandoff | Select-Object Resource,Archive | Format-List
