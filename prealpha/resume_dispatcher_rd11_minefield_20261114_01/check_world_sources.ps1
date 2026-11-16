# Verify the exact installed EP1 sectors used to bind community records to quests.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out = Join-Path $PSScriptRoot 'evidence_02'
if (Test-Path -LiteralPath $out) { throw 'Fresh output required' }
$inventoryPath = Join-Path $workspace 'research/sidejobs_s28/vehicles/world_03/inventory.json'
$inventory = Get-Content -LiteralPath $inventoryPath -Raw | ConvertFrom-Json -AsHashtable
$providers = @($inventory.rows | Where-Object { $_['json'] -match '/ep1_1_nightcity_always_loaded_[012]\.streamingsector\.json$' })
if ($providers.Count -ne 3 -or @($providers.archive | Sort-Object -Unique).Count -ne 1) { throw 'Expected three exact EP1 sectors' }

. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$names = [WolvenKit.Common.Services.HashService]::new()
$names.Load()
$path = $providers[0].archive
$before = Get-Item -LiteralPath $path
$archive = $null
if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$names,[ref]$archive).ToString() -cne 'NoError') {
    throw 'Cannot read installed EP1 archive'
}
$pins = @{
    '0' = '208C1912B268D7B647F18E16099A5C9A302037F54042DECC20B0F52341DE63D8'
    '1' = '2BCB4243CDD2CF5DAE17AFFAA15063B96330690146AA1821EAD071F4B4A7B9CF'
    '2' = 'A29A484E5215AAD93C2F90B955D163FBEF7932AB9B6D117E67455B2D907318ED'
}
$rows = @(foreach ($pin in $providers | Sort-Object depot) {
    if ($pin.depot -cnotmatch '^base\\worlds\\03_night_city\\_compiled\\default\\always_loaded_([012])\.streamingsector$' -or
        $pin.raw_sha256 -cne $pins[$Matches[1]]) { throw 'Unexpected world export provenance' }
    $key = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($pin.depot)
    if (!$archive.Files.ContainsKey($key)) { throw "Missing EP1 sector $($pin.depot)" }
    $memory = [IO.MemoryStream]::new()
    try {
        $archive.Files[$key].Extract($memory)
        $sha = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray()))
    } finally { $memory.Dispose() }
    if ($sha -cne $pin.raw_sha256 -or (Get-FileHash -LiteralPath (Join-Path $workspace $pin.json)).Hash -cne $pin.json_sha256) {
        throw "World source drift for $($pin.depot)"
    }
    @{ key = $key.ToString(); depot = $pin.depot; raw_sha256 = $sha; export = $pin.json; export_sha256 = $pin.json_sha256 }
})
$after = Get-Item -LiteralPath $path
if ($before.Length -ne $after.Length -or $before.LastWriteTimeUtc.Ticks -ne $after.LastWriteTimeUtc.Ticks) {
    throw 'EP1 archive changed while reading'
}
[void][IO.Directory]::CreateDirectory($out)
@{ archive = $path; rows = $rows } | ConvertTo-Json -Depth 4 |
    Set-Content -LiteralPath (Join-Path $out 'world_sources.json') -Encoding utf8NoBOM
Write-Output 'Matched the three installed EP1 world sectors to their decoded exports.'
