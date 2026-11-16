Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$planFile = Join-Path $PSScriptRoot 'authored_03/plan.json'
$plan = Get-Content -LiteralPath $planFile -Raw | ConvertFrom-Json -AsHashtable
$readback = Join-Path $PSScriptRoot 'readback_02'
$archiveRel = 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$installedArchive = Join-Path $plan.game_root $archiveRel
$candidateArchive = Join-Path $plan.candidate "package/$archiveRel"
if ((Test-Path -LiteralPath $readback) -or (Test-Path -LiteralPath $candidateArchive)) {
    throw 'Fresh pack and readback outputs required'
}
if ($plan.files[$archiveRel] -cne (Get-FileHash -LiteralPath $installedArchive).Hash) {
    throw 'Installed archive differs from the authored baseline'
}
if ($plan.edits.Count -ne 9 -or $plan.base_members.Count -ne 1729) {
    throw 'Unexpected resource plan'
}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()

function Key([string]$Depot) {
    [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($Depot)
}

function Open-Archive([string]$Path) {
    $archive = $null
    if ($reader.ReadArchive($Path, $hashService, [ref]$archive).ToString() -cne 'NoError') {
        throw "Unreadable archive $Path"
    }
    return $archive
}

function Entry-Hash($Entry) {
    $stream = [IO.MemoryStream]::new()
    try {
        [void]$Entry.Extract($stream)
        return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($stream.ToArray()))
    } finally {
        $stream.Dispose()
    }
}

$queries = @{}
foreach ($edit in $plan.edits) {
    $sourceKey = Key $edit.source.depot
    if ($sourceKey.ToString() -cne $edit.source.key -or $queries.ContainsKey($sourceKey)) {
        throw "Unexpected source key $($edit.source.depot)"
    }
    $queries[$sourceKey] = @{ depot=$edit.source.depot; archive=$edit.source.archive; sha256=$edit.source.sha256; count=0 }
    if ($edit.depot -cne $edit.source.depot) {
        $aliasKey = Key $edit.depot
        if ($queries.ContainsKey($aliasKey)) { throw "Alias collision $($edit.depot)" }
        $queries[$aliasKey] = @{ depot=$edit.depot; archive=$null; sha256=$null; count=0 }
    }
}
$archiveRoot = Join-Path $plan.game_root 'archive/pc'
if (@(Get-ChildItem -LiteralPath $archiveRoot -Recurse -Force -Attributes ReparsePoint).Count) {
    throw 'Linked game archive path'
}
$installed = @(Get-ChildItem -LiteralPath $archiveRoot -Recurse -File -Force -Filter '*.archive')
foreach ($file in $installed) {
    $stamp = @($file.Length, $file.LastWriteTimeUtc.Ticks)
    $archive = Open-Archive $file.FullName
    foreach ($key in $queries.Keys) {
        if (-not $archive.Files.ContainsKey($key)) { continue }
        $query = $queries[$key]
        if ($query.archive -cne $file.Name -or $query.sha256 -cne (Entry-Hash $archive.Files[$key])) {
            throw "Unexpected provider for $($query.depot) in $($file.FullName)"
        }
        $query.count++
    }
    $file.Refresh()
    if ($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1]) {
        throw "Archive changed while reading $($file.FullName)"
    }
}
foreach ($query in $queries.Values) {
    if (($null -ne $query.archive -and $query.count -ne 1) -or ($null -eq $query.archive -and $query.count -ne 0)) {
        throw "Provider count mismatch for $($query.depot)"
    }
}

$nativePhases = @($plan.edits | Where-Object { $_.depot -match '^(base|ep1)\\.*\.questphase$' })
$archiveXL = @(Get-ChildItem -LiteralPath $archiveRoot -Recurse -File -Force -Filter '*.xl')
foreach ($xl in $archiveXL) {
    $content = [IO.File]::ReadAllText($xl.FullName)
    foreach ($phase in $nativePhases) {
        if ($content.Contains($phase.depot, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Review ArchiveXL registration for $($phase.depot) in $($xl.FullName)"
        }
    }
}

New-Item -ItemType Directory -Path $readback | Out-Null
$sourceRoot = Join-Path $plan.candidate 'archive_source'
$members = @{}
foreach ($item in $plan.base_members.GetEnumerator()) { $members.Add($item.Key, $item.Value) }
$resources = @(foreach ($edit in $plan.edits) {
    if ($edit.depot -notmatch '^(base|ep1|towercontinued)\\[a-z0-9_\\]+\.(scene|questphase)$' -or
        $edit.json_sha256 -cne (Get-FileHash -LiteralPath $edit.json).Hash) {
        throw "Invalid authored input $($edit.depot)"
    }
    $target = Join-Path $sourceRoot $edit.depot
    if ($members.ContainsKey($edit.depot)) {
        if ($members[$edit.depot] -cne $edit.source.sha256 -or
            (Get-FileHash -LiteralPath $target).Hash -cne $edit.source.sha256) {
            throw "Changed candidate predecessor $($edit.depot)"
        }
    } elseif (Test-Path -LiteralPath $target) {
        throw "Unexpected source file $target"
    }
    $dto = [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize(
        [WolvenKit.Common.Conversion.RedFileDto], [IO.File]::ReadAllText($edit.json),
        [WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
    Write-Cr2wFile $dto.Data $target
    $rawHash = (Get-FileHash -LiteralPath $target).Hash
    $key = Key $edit.depot
    $json = Join-Path $readback ($key.ToString() + '.json')
    Export-Cr2wJson (Read-Cr2wFile $target) $json
    $members[$edit.depot] = $rawHash
    @{ depot=$edit.depot; sha256=$rawHash; json=$json; json_sha256=(Get-FileHash -LiteralPath $json).Hash }
})

$expected = @{}
foreach ($item in $members.GetEnumerator()) {
    $key = Key $item.Key
    if ($expected.ContainsKey($key)) { throw "Packed depot collision $($item.Key)" }
    $expected[$key] = @{ depot=$item.Key; sha256=$item.Value }
}
$stream = [IO.File]::Open($candidateArchive, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService, [WolvenKit.SerilogWrapper]::new())
    if (-not $writer.WriteArchive([IO.DirectoryInfo]::new($sourceRoot), $stream)) {
        throw 'Archive packing failed'
    }
} finally {
    $stream.Dispose()
}
$archive = Open-Archive $candidateArchive
if ($archive.Files.Count -ne $expected.Count) { throw 'Packed member count drift' }
foreach ($item in $archive.Files.GetEnumerator()) {
    if (-not $expected.ContainsKey($item.Key) -or
        (Entry-Hash $item.Value) -cne $expected[$item.Key].sha256) {
        throw "Packed member verification failed at $($item.Key)"
    }
}
@{
    status='PACKED_AND_READ_BACK'; plan_sha256=(Get-FileHash -LiteralPath $planFile).Hash
    archive_sha256=(Get-FileHash -LiteralPath $candidateArchive).Hash
    installed_archives=$installed.Count; archive_xl_configs=$archiveXL.Count
    provider_keys=$queries.Count; resources=$resources; source_resources=$members
    game_writes=0; save_writes=0
} | ConvertTo-Json -Depth 14 | Set-Content -LiteralPath (Join-Path $readback 'manifest.json') -Encoding utf8NoBOM
Write-Output "Packed and verified $($archive.Files.Count) members and $($queries.Count) provider keys."
