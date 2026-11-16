Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$out = Join-Path $PSScriptRoot 'candidate_01'
$planFile = Join-Path $PSScriptRoot 'plan.json'
$plan = Get-Content -LiteralPath $planFile -Raw | ConvertFrom-Json -AsHashtable
$source = Join-Path $out 'archive_source'
$archiveRel = 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$target = Join-Path $out "package/$archiveRel"
$readback = Join-Path $out 'readback'
if ((Test-Path -LiteralPath $target) -or (Test-Path -LiteralPath $readback)) { throw 'Fresh archive output required' }
if ($plan.status -cne 'VERIFIED_ML1_JB4_SOURCE' -or
    (Get-FileHash -LiteralPath $plan.installed_manifest).Hash -cne $plan.installed_manifest_sha256 -or
    (Get-FileHash -LiteralPath $plan.base_package_manifest).Hash -cne $plan.base_package_manifest_sha256 -or
    (Get-FileHash -LiteralPath (Join-Path $plan.game_root $archiveRel)).Hash -cne $plan.archive_before -or
    (Get-FileHash -LiteralPath (Join-Path $source $plan.map)).Hash -cne $plan.map_after) {
    throw 'Staged or installed input drift'
}
$previous = Get-Content -LiteralPath $plan.base_package_manifest -Raw | ConvertFrom-Json -AsHashtable
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')

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
    $archive
}
function PayloadBytes($Entry) {
    $stream = [IO.MemoryStream]::new()
    try { [void]$Entry.Extract($stream); return ,$stream.ToArray() } finally { $stream.Dispose() }
}

$archiveRoot = Join-Path $plan.game_root 'archive/pc'
for ($p = [IO.DirectoryInfo]::new($archiveRoot); $null -ne $p; $p = $p.Parent) {
    if ($p.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked archive root: $p" }
}
if (@(Get-ChildItem -LiteralPath $archiveRoot -Recurse -Force -Attributes ReparsePoint).Count) {
    throw 'Linked archive tree refused'
}
$configs = @{}
foreach ($row in $plan.english_configs) { $configs[$row.config] = $row.sha256 }
foreach ($file in Get-ChildItem -LiteralPath $archiveRoot -Recurse -File -Force -Filter '*.xl') {
    if (-not (Select-String -LiteralPath $file.FullName -Pattern '^\s*lipmaps:' -Quiet)) { continue }
    if (-not $configs.ContainsKey($file.FullName) -or
        (Get-FileHash -LiteralPath $file.FullName).Hash -cne $configs[$file.FullName]) {
        throw "Localization configuration changed: $($file.FullName)"
    }
    $configs.Remove($file.FullName)
}
if ($configs.Count) { throw 'A pinned lipmap configuration is missing' }

$queries = @{}
foreach ($row in $plan.providers) {
    $key = Key $row.depot
    if ($key.ToString() -cne $row.key) { throw "Unexpected depot key: $($row.depot)" }
    if (-not $queries.ContainsKey($key)) { $queries[$key] = @{depot=$row.depot; remaining=@{}} }
    $query = $queries[$key]
    if ($query.depot -cne $row.depot -or $query.remaining.ContainsKey($row.archive)) {
        throw "Conflicting provider query: $($row.depot)"
    }
    $query.remaining[$row.archive] = $row.sha256
}
$paths = @(Get-ChildItem -LiteralPath $archiveRoot -Recurse -File -Force -Filter '*.archive')
foreach ($file in $paths) {
    $stamp = @($file.Length, $file.LastWriteTimeUtc.Ticks)
    $archive = OpenArchive $file.FullName
    foreach ($key in $queries.Keys) {
        if (-not $archive.Files.ContainsKey([uint64]$key)) { continue }
        $query = $queries[$key]
        $digest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData((PayloadBytes $archive.Files[[uint64]$key])))
        if (-not $query.remaining.ContainsKey($file.FullName) -or $digest -cne $query.remaining[$file.FullName]) {
            throw "Changed or colliding provider $($query.depot) in $($file.FullName)"
        }
        $query.remaining.Remove($file.FullName)
    }
    $file.Refresh()
    if ($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1]) { throw "Archive changed during census: $file" }
}
if (@($queries.Values | Where-Object { $_.remaining.Count }).Count) { throw 'Missing pinned provider' }

$expected = @{}
foreach ($row in $previous.source_resources.GetEnumerator()) {
    $key = Key $row.Key
    if ($expected.ContainsKey($key)) { throw "Duplicate archive depot key $($row.Key)" }
    $digest = if ($row.Key -ceq $plan.map) { $plan.map_after } else { $row.Value }
    $expected[$key] = @{depot=$row.Key;sha256=$digest}
}
$stream = [IO.File]::Open($target, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService, [WolvenKit.SerilogWrapper]::new())
    if (-not $writer.WriteArchive([IO.DirectoryInfo]::new($source), $stream)) { throw 'Archive packing failed' }
} finally { $stream.Dispose() }
$archive = OpenArchive $target
if ($archive.Files.Count -ne $expected.Count) { throw 'Packed member count drift' }
New-Item -ItemType Directory -Path $readback | Out-Null
$members = @(foreach ($item in $archive.Files.GetEnumerator()) {
    $row = $expected[$item.Key]
    $bytes = PayloadBytes $item.Value
    $digest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
    if (-not $row -or $digest -cne $row.sha256) { throw "Cooked payload mismatch at $($item.Key)" }
    if ($row.depot -ceq $plan.map) {
        $raw = Join-Path $readback 'en-us.lipmap'
        [IO.File]::WriteAllBytes($raw, $bytes)
        Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $readback 'lipmap.json')
    }
    @{depot=$row.depot;key=$item.Key.ToString();sha256=$digest}
})
@{
    status='PASS_ML1_JB4_ARCHIVE_READBACK'; plan_sha256=(Get-FileHash -LiteralPath $planFile).Hash
    archive_sha256=(Get-FileHash -LiteralPath $target).Hash; members=$members
    archive_count=$paths.Count; provider_depots=$queries.Count; provider_rows=$plan.providers.Count
    game_writes=0; save_writes=0
} | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $readback 'archive.json') -Encoding utf8NoBOM
Write-Output "Read back $($members.Count) members and verified $($queries.Count) depot keys across $($paths.Count) archives."
