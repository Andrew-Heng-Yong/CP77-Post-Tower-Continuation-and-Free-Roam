# Pack five reviewed resource changes into the exact RD5 archive baseline.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$pins = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/inputs.json') | ConvertFrom-Json -AsHashtable
$proof = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/assessment_02.json') | ConvertFrom-Json -AsHashtable
$graphPath = Join-Path $PSScriptRoot 'graph_02/readback.json'
$graph = Get-Content -Raw -LiteralPath $graphPath | ConvertFrom-Json -AsHashtable
$currentArchivePath = (Get-Item -LiteralPath (Join-Path $pins.game 'archive/pc/mod/zzzz_PTFR_Combined.archive')).FullName
$out = Join-Path $PSScriptRoot 'archive_02'
if (Test-Path -LiteralPath $out) { throw 'Fresh archive output required' }
if ($proof.status -cne 'PASS' -or (Get-FileHash -LiteralPath $graphPath).Hash -cne $proof.graph_sha256 -or
    (Get-FileHash -LiteralPath $currentArchivePath).Hash -cne $pins.archive_sha256 -or
    (Get-FileHash -LiteralPath (Join-Path $pins.game $pins.xl.path)).Hash -cne $pins.xl.sha256) { throw 'Input drift' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$names = [WolvenKit.Common.Services.HashService]::new()
$names.Load()
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
function Open-Archive([string]$Path) {
    $archive = $null
    if ($reader.ReadArchive($Path,$names,[ref]$archive).ToString() -cne 'NoError') { throw "Unreadable archive $Path" }
    $archive
}
function Key([string]$Depot) { [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($Depot) }
function Member-Hash($Entry) {
    $memory = [IO.MemoryStream]::new()
    try {
        $Entry.Extract($memory)
        $memory.Position = 0
        [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory))
    } finally { $memory.Dispose() }
}
function Plain([string]$Path) {
    for ($item=Get-Item -LiteralPath $Path -Force; $null -ne $item;) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked path $Path" }
        $item = if ($item -is [IO.FileInfo]) { $item.Directory } else { $item.Parent }
    }
}

$changes = @{}
foreach ($part in $graph.resources) { $changes[$part.depot] = @{path=$part.path; sha256=$part.sha256} }
foreach ($part in @($pins.parts.root,$pins.parts.main,$pins.phone)) {
    $changes[$part.depot] = @{path=$part.raw; sha256=$part.raw_sha256}
}
if ($changes.Count -ne 5) { throw 'Unexpected payload scope' }
$keys = @{}
foreach ($depot in $changes.Keys) {
    $key = Key $depot
    if ($keys.ContainsKey($key)) { throw 'Staged key collision' }
    $keys[$key] = $depot
}
$archives = 0
foreach ($relative in 'archive/pc','mods') {
    $root = Join-Path $pins.game $relative
    if (!(Test-Path -LiteralPath $root)) { continue }
    Plain $root
    if (@(Get-ChildItem -LiteralPath $root -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked archive tree' }
    foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.archive') {
        $stamp = @($file.Length,$file.LastWriteTimeUtc.Ticks)
        $archive = Open-Archive $file.FullName
        foreach ($key in $keys.Keys) {
            $expected = $file.FullName -ieq $currentArchivePath -and $pins.members.Contains($keys[$key])
            if ($archive.Files.ContainsKey($key) -ne $expected) {
                throw "Unexpected provider for $($keys[$key]) in $($file.FullName), expected=$expected"
            }
        }
        $file.Refresh()
        if ($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1]) { throw 'Archive changed during scan' }
        $archives++
    }
}
$source = Join-Path $out 'source'
[void][IO.Directory]::CreateDirectory($source)
$donor = $pins.archive_source
Plain $donor
if (@(Get-ChildItem -LiteralPath $donor -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked donor tree' }
$current = Open-Archive $currentArchivePath
$expectedMembers = @{}
foreach ($file in Get-ChildItem -LiteralPath $donor -Recurse -File) {
    $depot = [IO.Path]::GetRelativePath($donor,$file.FullName)
    $key = Key $depot
    if ($expectedMembers.ContainsKey($key) -or !$current.Files.ContainsKey($key) -or !$pins.members.Contains($depot)) { throw "Unexpected donor $depot" }
    $digest = (Get-FileHash -LiteralPath $file.FullName).Hash
    if ($digest -cne $pins.members[$depot] -or $digest -cne (Member-Hash $current.Files[$key])) { throw "Donor drift $depot" }
    $expectedMembers[$key] = @{depot=$depot; sha256=$digest}
    if ($changes.ContainsKey($depot)) { continue }
    $dest = Join-Path $source $depot
    [void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent))
    [IO.File]::Copy($file.FullName,$dest,$false)
}
if ($expectedMembers.Count -ne 1745 -or $current.Files.Count -ne $expectedMembers.Count) { throw 'Incomplete baseline donor' }
foreach ($depot in $changes.Keys) {
    $row = $changes[$depot]
    Plain $row.path
    if ((Get-FileHash -LiteralPath $row.path).Hash -cne $row.sha256) { throw "Staged payload drift $depot" }
    $dest = Join-Path $source $depot
    [void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent))
    [IO.File]::Copy($row.path,$dest,$false)
    $expectedMembers[(Key $depot)] = @{depot=$depot;sha256=$row.sha256}
}
$packed = Join-Path $out 'zzzz_PTFR_Combined.archive'
$stream = [IO.File]::Open($packed,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($names,[WolvenKit.SerilogWrapper]::new())
    if (!$writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)) { throw 'Packing failed' }
} finally { $stream.Dispose() }
$readback = Open-Archive $packed
if ($expectedMembers.Count -ne 1748 -or $readback.Files.Count -ne $expectedMembers.Count) { throw 'Incorrect member count' }
foreach ($key in $expectedMembers.Keys) {
    if (!$readback.Files.ContainsKey($key) -or (Member-Hash $readback.Files[$key]) -cne $expectedMembers[$key].sha256) {
        throw "Packed member drift $($expectedMembers[$key].depot)"
    }
}
@{status='MEMBERS_VERIFIED'; archive_sha256=(Get-FileHash -LiteralPath $packed).Hash; scanned_archives=$archives;
    registered_paths_changed=0; changes=@($changes.Keys | Sort-Object); members=@($expectedMembers.Values | Sort-Object depot)} |
    ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
Write-Output "Verified $($expectedMembers.Count) packed members and five changed depots."
