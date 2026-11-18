# Read-only current archive lookup. Outputs are confined to a fresh workspace capture.
param([string]$Name='sources_01',[string]$QueryFile='')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if ($Name -cnotmatch '^[a-z][a-z0-9_]+$') { throw 'Invalid output name' }
$out=Join-Path $PSScriptRoot ('work/'+$Name)
if (Test-Path -LiteralPath $out) { throw 'Fresh evidence required' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$depots = @(Get-Content -LiteralPath $(if ($QueryFile) { $QueryFile } else { Join-Path $PSScriptRoot 'queries.json' }) -Raw | ConvertFrom-Json)
function Plain([string]$path) {
    for ($item=Get-Item -LiteralPath $path -Force; $null -ne $item;) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked path refused: $path" }
        $item=if ($item -is [IO.FileInfo]) { $item.Directory } else { $item.Parent }
    }
}
Plain $PSScriptRoot
$manifestPath=Join-Path $workspace 'prealpha/misty_roof_pickup_release_20261118_01/installed_manifest.json'
$manifest=Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$identity=@(foreach ($row in @($manifest.core_files)+@($manifest.required_files)) {
    $path=Join-Path $manifest.game_root $row.path
    Plain $path
    $hash=(Get-FileHash -LiteralPath $path).Hash
    if ($hash -cne $row.sha256) { throw "Installed baseline drift: $path" }
    @{path=$row.path;sha256=$hash}
})
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$queries=@{}
foreach ($depot in $depots) {
    if ($depot.StartsWith('\') -or $depot.Contains('..') -or $depot.Contains(':')) { throw 'Unsafe depot' }
    $key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString([string]$depot)
    if ($queries.ContainsKey($key)) { throw 'Depot collision' }
    $queries[$key]=[string]$depot
}
[void](New-Item -ItemType Directory -Path $out -Force)
$hits=[Collections.Generic.List[object]]::new();$archives=[Collections.Generic.List[object]]::new()
$roots = @('archive/pc','mods' | ForEach-Object {Join-Path $manifest.game_root $_} | Where-Object {Test-Path -LiteralPath $_})
foreach ($file in Get-ChildItem -LiteralPath $roots -Filter '*.archive' -Recurse -File) {
    Plain $file.FullName
    $arc=$null
    if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$arc).ToString() -cne 'NoError') { throw 'Unreadable provider' }
    $archives.Add(@{path=$file.FullName;length=$file.Length;last_write_utc=$file.LastWriteTimeUtc.ToString('o')})
    foreach ($key in $queries.Keys) {
        if (-not $arc.Files.ContainsKey([uint64]$key)) { continue }
        $depot=$queries[$key];$raw=Join-Path $out (([string]$archives.Count)+'/'+$depot)
        [void](New-Item -ItemType Directory -Path (Split-Path $raw -Parent) -Force)
        $memory=[IO.MemoryStream]::new()
        try { $arc.Files[[uint64]$key].Extract($memory);[IO.File]::WriteAllBytes($raw,$memory.ToArray()) } finally { $memory.Dispose() }
        # Use hash-matched exports for graphs and scenes.
        $hits.Add(@{archive=$file.FullName;depot=$depot;raw=$raw;sha256=(Get-FileHash -LiteralPath $raw).Hash})
    }
}
@{status='CURRENT_PROVIDER_CAPTURE';manifest_sha256=(Get-FileHash -LiteralPath $manifestPath).Hash;identity=$identity;queries=$depots;archives=$archives.ToArray();hits=$hits.ToArray();game_writes=0;save_writes=0} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $out 'providers.json') -Encoding utf8NoBOM
Write-Output ("Verified {0} installed files; {1} providers captured across {2} archives" -f $identity.Count,$hits.Count,$archives.Count)
