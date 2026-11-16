$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$workspace = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$donor = Join-Path $workspace 'prealpha/resume_dispatcher_rd10_kirk_20261113_01/archive_01'
$readback = Join-Path $donor 'readback.json'
$baseline = Join-Path $workspace 'prealpha/mid_quest_resume_archive_20261115_01/stage_02/deployment_01/installed_manifest_01.json'
if ((Get-FileHash -LiteralPath $readback).Hash -cne '5BBD9BB8F04AA5CC235B9845BDE691E2D6105B70E98083B36D7A8F54A3B29B81' -or
    (Get-FileHash -LiteralPath $baseline).Hash -cne '35B2CE7B75DBACD202E902A9969F002042B151127FD13BAA636851180747F9CF') { throw 'Baseline proof drift' }
$before = Get-Content -Raw -LiteralPath $readback | ConvertFrom-Json -AsHashtable
$game = (Get-Content -Raw -LiteralPath $baseline | ConvertFrom-Json -AsHashtable).game_root
$installed = (Get-Item -LiteralPath (Join-Path $game 'archive/pc/mod/zzzz_PTFR_Combined.archive')).FullName
if ((Get-FileHash -LiteralPath $installed).Hash -cne $before.archive_sha256) { throw 'Installed archive drift' }
$gatePath = Join-Path $PSScriptRoot 'stage_03/gates.json'
$revisions = Get-Content -Raw -LiteralPath $gatePath | ConvertFrom-Json -AsHashtable
$proof = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'stage_03/gate_checks.json') | ConvertFrom-Json -AsHashtable
if ($proof.status -cne 'PASS' -or $revisions.Count -ne 10 -or $proof.gates_sha256 -cne (Get-FileHash -LiteralPath $gatePath).Hash) { throw 'Missing independent graph verification' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$names = [WolvenKit.Common.Services.HashService]::new()
$names.Load()
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
function Open-Archive([string]$Path) {
    $archive = $null
    if ($reader.ReadArchive($Path, $names, [ref]$archive).ToString() -cne 'NoError') { throw "Unreadable archive $Path" }
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
    for ($item = Get-Item -LiteralPath $Path -Force; $null -ne $item;) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked path $Path" }
        $item = if ($item -is [IO.FileInfo]) { $item.Directory } else { $item.Parent }
    }
}
$changed = @{}
foreach ($row in $revisions) {
    if ($changed.ContainsKey($row.depot) -or (Get-FileHash -LiteralPath $row.path).Hash -cne $row.sha256) { throw 'Revised resource drift' }
    $changed[$row.depot] = $row
}
$changedKeys = @($changed.Keys | ForEach-Object {Key $_})
$scanned = 0
foreach ($relative in 'archive/pc','mods') {
    $folder = Join-Path $game $relative
    if (!(Test-Path -LiteralPath $folder)) { continue }
    Plain $folder
    if (@(Get-ChildItem -LiteralPath $folder -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked archive tree' }
    foreach ($file in Get-ChildItem -LiteralPath $folder -Recurse -File -Filter '*.archive') {
        $stamp = @($file.Length, $file.LastWriteTimeUtc.Ticks)
        $archive = Open-Archive $file.FullName
        foreach ($key in $changedKeys) {
            if ($archive.Files.ContainsKey($key) -ne ($file.FullName -ieq $installed)) {
                throw "Unexpected provider for $key in $($file.FullName)"
            }
        }
        $file.Refresh()
        if ($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1]) { throw 'Archive changed during scan' }
        $scanned++
    }
}
$out = Join-Path $PSScriptRoot 'stage_03/pack'
if (Test-Path -LiteralPath $out) { throw 'Fresh output required' }
$source = Join-Path $out 'source'
[void][IO.Directory]::CreateDirectory($source)
$stock = Join-Path $donor 'source'
Plain $stock
if (@(Get-ChildItem -LiteralPath $stock -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked donor tree' }
$expected = @{}
$current = Open-Archive $installed
foreach ($row in $before.members) {
    $depot = $row.depot
    $key = Key $depot
    $bytes = Join-Path $stock $depot
    if ($expected.ContainsKey($key) -or !$current.Files.ContainsKey($key) -or
        (Get-FileHash -LiteralPath $bytes).Hash -cne $row.sha256 -or (Member-Hash $current.Files[$key]) -cne $row.sha256) { throw "Donor mismatch $depot" }
    $sha = $row.sha256
    if ($changed.ContainsKey($depot)) { $bytes = $changed[$depot].path; $sha = $changed[$depot].sha256 }
    $target = Join-Path $source $depot
    [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target))
    [IO.File]::Copy($bytes, $target, $false)
    $expected[$key] = @{depot=$depot; sha256=$sha; before=$row.sha256}
}
if ($expected.Count -ne 1748 -or $current.Files.Count -ne $expected.Count) { throw 'Incomplete archive source' }
$packed = Join-Path $out 'zzzz_PTFR_Combined.archive'
$stream = [IO.File]::Open($packed, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($names, [WolvenKit.SerilogWrapper]::new())
    if (!$writer.WriteArchive([IO.DirectoryInfo]::new($source), $stream)) { throw 'Packing failed' }
} finally { $stream.Dispose() }
$roundTrip = Open-Archive $packed
if ($roundTrip.Files.Count -ne $expected.Count) { throw 'Incorrect packed member count' }
foreach ($key in $expected.Keys) {
    if (!$roundTrip.Files.ContainsKey($key) -or (Member-Hash $roundTrip.Files[$key]) -cne $expected[$key].sha256) {
        throw "Packed member drift $($expected[$key].depot)"
    }
}
if ((Get-FileHash -LiteralPath $installed).Hash -cne $before.archive_sha256) { throw 'Installed archive changed during check' }
@{status='PASS'; archive_sha256=(Get-FileHash -LiteralPath $packed).Hash; scanned_archives=$scanned;
    members=@($expected.Values | Sort-Object depot); changed_depots=@($changed.Keys | Sort-Object)} |
    ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
Write-Output "Read back $($expected.Count) members and checked $scanned installed archives."
