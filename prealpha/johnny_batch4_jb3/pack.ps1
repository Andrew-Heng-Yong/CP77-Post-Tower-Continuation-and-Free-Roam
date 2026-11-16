Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$planPath = Join-Path $PSScriptRoot 'input_01/plan.json'
$plan = Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json -Depth 100
$proof = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'verification_01.json') -Raw | ConvertFrom-Json -Depth 50
if ($proof.status -cne 'PASS_JB3_COOKED_AND_BOUNDED_FLOW' -or $proof.plan_sha256 -cne (Get-FileHash -LiteralPath $planPath).Hash) {
    throw 'Unverified JB3 inputs'
}
$out = Join-Path $PSScriptRoot 'archive_readback_01.json'
$archiveRel = 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$target = Join-Path (Join-Path $plan.candidate 'package') $archiveRel
if ((Test-Path -LiteralPath $out) -or (Test-Path -LiteralPath $target)) { throw 'Fresh packing output required' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hashes = [WolvenKit.Common.Services.HashService]::new()
$hashes.Load()
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
function DepotKey([string]$depot) {
    [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
}
function OpenArchive([string]$path) {
    $archive = $null
    if ($reader.ReadArchive($path,$hashes,[ref]$archive).ToString() -cne 'NoError') {
        throw "Unreadable archive $path"
    }
    return $archive
}
function EntryDigest($entry) {
    $stream = [IO.MemoryStream]::new()
    try {
        [void]$entry.Extract($stream)
        [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($stream.ToArray()))
    } finally { $stream.Dispose() }
}

# Check source-provider uniqueness and new keys across the actual installed
# archive inventory, separately from the unchanged ArchiveXL registrations.
$query = @{}
foreach ($row in $plan.providers) {
    $key = DepotKey $row.depot
    if ($query.ContainsKey($key)) { throw "Source key collision $($row.depot)" }
    $query[$key] = @{depot=$row.depot; provider=$row.archive; sha256=$row.sha256; hits=0}
}
$aliases = @($plan.edits | Where-Object is_new)
foreach ($row in $aliases) {
    $key = DepotKey $row.depot
    if ($query.ContainsKey($key)) { throw "Alias key collision $($row.depot)" }
    $query[$key] = @{depot=$row.depot; provider=$null; sha256=$null; hits=0}
}
$gameArchives = Join-Path $plan.game_root 'archive/pc'
$paths = @(Get-ChildItem -LiteralPath $gameArchives -Recurse -File -Filter '*.archive')
foreach ($path in $paths) {
    if ($path.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked archive refused' }
    $archive = OpenArchive $path.FullName
    foreach ($key in $query.Keys) {
        if (-not $archive.Files.ContainsKey([uint64]$key)) { continue }
        $row = $query[$key]
        $row.hits++
        if ($path.FullName -cne $row.provider -or (EntryDigest $archive.Files[[uint64]$key]) -cne $row.sha256) {
            throw "Changed or colliding provider $($row.depot) in $($path.FullName)"
        }
    }
}
foreach ($row in $query.Values) {
    $hits = if ($row.provider) { 1 } else { 0 }
    if ($row.hits -ne $hits) { throw "Unexpected provider count for $($row.depot)" }
}

$source = Join-Path $plan.candidate 'archive_source'
$expected = @{}
foreach ($file in Get-ChildItem -LiteralPath $source -Recurse -File) {
    if ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked source refused' }
    $depot = [IO.Path]::GetRelativePath($source,$file.FullName).Replace('/','\')
    $key = DepotKey $depot
    if ($expected.ContainsKey($key)) { throw "Archive source collision at $depot" }
    $expected[$key] = @{depot=$depot;sha256=(Get-FileHash -LiteralPath $file.FullName).Hash}
}
if ($expected.Count -ne ($plan.old_archive_count + $aliases.Count)) { throw 'Unexpected archive member count' }
$stream = [IO.File]::Create($target)
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashes,[WolvenKit.SerilogWrapper]::new())
    if (-not $writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)) { throw 'Packing failed' }
} finally { $stream.Dispose() }
$archive = OpenArchive $target
if ($archive.Files.Count -ne $expected.Count) { throw 'Archive inventory mismatch' }
$rows = @(foreach ($entry in $archive.Files.GetEnumerator()) {
    $row = $expected[$entry.Key]
    if (-not $row -or (EntryDigest $entry.Value) -cne $row.sha256) { throw 'Archive member readback mismatch' }
    @{depot=$row.depot;key=$entry.Key.ToString();sha256=$row.sha256}
})
@{status='PASS_JB3_ARCHIVE_AND_PROVIDERS';archive_sha256=(Get-FileHash -LiteralPath $target).Hash;
  plan_sha256=(Get-FileHash -LiteralPath $planPath).Hash;resources=$rows;providers=@($query.Values);
  installed_archive_count=$paths.Count;archives=@($paths.FullName);new_xl_registrations=0;
  game_writes=0;save_writes=0} | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $out -Encoding utf8NoBOM
Write-Output "Verified $($rows.Count) packed payloads and $($query.Count) depot keys across $($paths.Count) installed archives."
