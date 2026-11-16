Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$planFile = Join-Path $PSScriptRoot 'pack_inputs_02.json'
$proofFile = Join-Path $PSScriptRoot 'verification.json'
$plan = Get-Content -LiteralPath $planFile -Raw | ConvertFrom-Json -AsHashtable
$proof = Get-Content -LiteralPath $proofFile -Raw | ConvertFrom-Json -AsHashtable
$archiveRel = 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$target = Join-Path $plan.candidate "package/$archiveRel"
$archiveProof = Join-Path $PSScriptRoot 'archive_readback.json'
if ((Test-Path -LiteralPath $target) -or (Test-Path -LiteralPath $archiveProof)) { throw 'Fresh archive output required' }
if ($proof.status -cne 'PASS_QP2_MERGED_RESOURCES_AND_SCRIPTS' -or
    $plan.verification_sha256 -cne (Get-FileHash -LiteralPath $proofFile).Hash -or
    $plan.original_pack_plan_sha256 -cne (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'pack_inputs.json')).Hash -or
    $plan.before_archive -cne (Get-FileHash -LiteralPath (Join-Path $plan.game_root $archiveRel)).Hash) {
    throw 'Unverified archive input'
}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
function Key([string]$Depot) {
    [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($Depot)
}
function OpenArchive([string]$Path) {
    $archive = $null
    if ($reader.ReadArchive($Path, $hashService, [ref]$archive).ToString() -cne 'NoError') {
        throw "Unreadable archive: $Path"
    }
    return $archive
}
function EntryHash($Entry) {
    $stream = [IO.MemoryStream]::new()
    try {
        [void]$Entry.Extract($stream)
        return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($stream.ToArray()))
    } finally { $stream.Dispose() }
}

$queries = @{}
foreach ($row in $plan.providers) {
    $key = Key $row.depot
    if ($queries.ContainsKey($key)) { throw "Provider key collision at $($row.depot)" }
    $paths = @{}
    foreach ($p in $row.archives.GetEnumerator()) { $paths.Add($p.Key, $p.Value) }
    $queries[$key] = @{depot=$row.depot;remaining=$paths}
}
$archiveRoot = Join-Path $plan.game_root 'archive/pc'
for ($p = [IO.DirectoryInfo]::new($archiveRoot); $null -ne $p; $p = $p.Parent) {
    if ($p.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked archive path: $p" }
}
if (@(Get-ChildItem -LiteralPath $archiveRoot -Recurse -Force -Attributes ReparsePoint).Count) {
    throw 'Linked archive tree refused'
}
$paths = @(Get-ChildItem -LiteralPath $archiveRoot -Recurse -File -Force -Filter '*.archive')
foreach ($file in $paths) {
    $stamp = @($file.Length, $file.LastWriteTimeUtc.Ticks)
    $archive = OpenArchive $file.FullName
    foreach ($key in $queries.Keys) {
        if (-not $archive.Files.ContainsKey([uint64]$key)) { continue }
        $query = $queries[$key]
        if (-not $query.remaining.ContainsKey($file.FullName) -or
            (EntryHash $archive.Files[[uint64]$key]) -cne $query.remaining[$file.FullName]) {
            throw "Changed or colliding provider $($query.depot) in $($file.FullName)"
        }
        $query.remaining.Remove($file.FullName)
    }
    $file.Refresh()
    if ($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1]) { throw "Archive changed: $file" }
}
if (@($queries.Values | Where-Object { $_.remaining.Count }).Count) { throw 'Missing pinned resource provider' }

$expected = @{}
foreach ($row in $plan.members.GetEnumerator()) {
    $key = Key $row.Key
    if ($expected.ContainsKey($key)) { throw "Packed key collision at $($row.Key)" }
    $expected[$key] = @{depot=$row.Key;sha256=$row.Value}
}
$source = Join-Path $plan.candidate 'archive_source'
$stream = [IO.File]::Open($target, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService, [WolvenKit.SerilogWrapper]::new())
    if (-not $writer.WriteArchive([IO.DirectoryInfo]::new($source), $stream)) { throw 'Archive packing failed' }
} finally { $stream.Dispose() }
$archive = OpenArchive $target
if ($archive.Files.Count -ne $expected.Count) { throw 'Packed member count drift' }
$rows = @(foreach ($item in $archive.Files.GetEnumerator()) {
    $row = $expected[$item.Key]
    if (-not $row -or (EntryHash $item.Value) -cne $row.sha256) { throw "Cooked payload drift at $($item.Key)" }
    @{depot=$row.depot; key=$item.Key.ToString(); sha256=$row.sha256}
})
@{
    status='PASS_QP2_ARCHIVE_AND_PROVIDERS'; archive_sha256=(Get-FileHash -LiteralPath $target).Hash
    plan_sha256=(Get-FileHash -LiteralPath $planFile).Hash; resources=$rows
    archive_count=$paths.Count; provider_depots=$queries.Count; game_writes=0; save_writes=0
} | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $archiveProof -Encoding utf8NoBOM
Write-Output "Verified $($rows.Count) archive members and $($queries.Count) depot keys across $($paths.Count) installed archives."
