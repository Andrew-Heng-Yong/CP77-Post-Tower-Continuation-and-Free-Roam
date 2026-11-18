# Repack the installed archive with only the verified private root replacement.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$pins = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'work/inputs.json') | ConvertFrom-Json -AsHashtable
$proof = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'work/assessment.json') | ConvertFrom-Json -AsHashtable
$receipt = Join-Path $PSScriptRoot 'work/graph_01/readback.json'
$root = Get-Content -Raw -LiteralPath $receipt | ConvertFrom-Json -AsHashtable
$installed = (Get-Item -LiteralPath (Join-Path $pins.game 'archive/pc/mod/zzzz_PTFR_Combined.archive')).FullName
$out = Join-Path $PSScriptRoot 'work/archive_01'
if (Test-Path -LiteralPath $out) { throw 'Fresh output required' }
if ($proof.status -cne 'PASS' -or (Get-FileHash -LiteralPath $receipt).Hash -cne $proof.readback_sha256 -or
    (Get-FileHash -LiteralPath $installed).Hash -cne $pins.archive_sha256 -or
    (Get-FileHash -LiteralPath $root.path).Hash -cne $root.sha256) { throw 'Input drift' }
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
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

$depot = $pins.root.depot
$key = Key $depot
$scanned = 0
foreach ($relative in 'archive/pc','mods') {
    $folder = Join-Path $pins.game $relative
    if (!(Test-Path -LiteralPath $folder)) { continue }
    Plain $folder
    if (@(Get-ChildItem -LiteralPath $folder -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked archive tree' }
    foreach ($file in Get-ChildItem -LiteralPath $folder -Recurse -File -Filter '*.archive') {
        $stamp = @($file.Length, $file.LastWriteTimeUtc.Ticks)
        $archive = Open-Archive $file.FullName
        if ($archive.Files.ContainsKey($key) -ne ($file.FullName -ieq $installed)) {
            throw "Unexpected provider for $depot in $($file.FullName)"
        }
        $file.Refresh()
        if ($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1]) { throw 'Archive changed during scan' }
        $scanned++
    }
}
$donor = $pins.archive_source
Plain $donor
if (@(Get-ChildItem -LiteralPath $donor -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked donor tree' }
$source = Join-Path $out 'source'
[void][IO.Directory]::CreateDirectory($source)
$current = Open-Archive $installed
$expected = @{}
foreach ($file in Get-ChildItem -LiteralPath $donor -Recurse -File) {
    $member = [IO.Path]::GetRelativePath($donor, $file.FullName)
    $memberKey = Key $member
    if ($expected.ContainsKey($memberKey) -or !$pins.members.Contains($member) -or !$current.Files.ContainsKey($memberKey)) {
        throw "Unexpected donor $member"
    }
    $digest = (Get-FileHash -LiteralPath $file.FullName).Hash
    if ($digest -cne $pins.members[$member] -or $digest -cne (Member-Hash $current.Files[$memberKey])) { throw "Donor drift $member" }
    $dest = Join-Path $source $member
    [void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent))
    $original = $file.FullName
    if ($member -ceq $depot) {
        $original = $root.path
        $digest = $root.sha256
    }
    [IO.File]::Copy($original, $dest, $false)
    $expected[$memberKey] = @{ depot = $member; sha256 = $digest }
}
if ($expected.Count -ne 1748 -or $current.Files.Count -ne $expected.Count -or $expected[$key].sha256 -cne $root.sha256) {
    throw 'Incomplete archive source'
}
$packed = Join-Path $out 'zzzz_PTFR_Combined.archive'
$stream = [IO.File]::Open($packed, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($names, [WolvenKit.SerilogWrapper]::new())
    if (!$writer.WriteArchive([IO.DirectoryInfo]::new($source), $stream)) { throw 'Packing failed' }
} finally { $stream.Dispose() }
$readback = Open-Archive $packed
if ($readback.Files.Count -ne $expected.Count) { throw 'Incorrect packed member count' }
foreach ($memberKey in $expected.Keys) {
    if (!$readback.Files.ContainsKey($memberKey) -or (Member-Hash $readback.Files[$memberKey]) -cne $expected[$memberKey].sha256) {
        throw "Packed member drift $($expected[$memberKey].depot)"
    }
}
if ((Get-FileHash -LiteralPath $installed).Hash -cne $pins.archive_sha256) { throw 'Installed archive changed during check' }
@{ status = 'MEMBERS_VERIFIED'; archive_sha256 = (Get-FileHash -LiteralPath $packed).Hash; scanned_archives = $scanned;
    changed_depot = $depot; members = @($expected.Values | Sort-Object depot) } |
    ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
Write-Output "Verified $($expected.Count) packed members and one replacement."
