Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$candidate = Join-Path $PSScriptRoot 'candidate_01'
$source = Join-Path $candidate 'archive_source'
$archive = Join-Path $candidate 'package/archive/pc/mod/zzzz_PTFR_Combined.archive'
$result = Join-Path $PSScriptRoot 'archive_readback.json'
if ((Test-Path -LiteralPath $archive) -or (Test-Path -LiteralPath $result)) { throw 'Fresh archive output required' }
$inputs = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'pack_inputs.json') -Raw | ConvertFrom-Json -AsHashtable
$expected = $inputs.source_resources
$files = @(Get-ChildItem -LiteralPath $source -Recurse -File)
if ($files.Count -ne $expected.Count) { throw 'Unexpected resource inventory' }
foreach ($file in $files) {
    $depot = [IO.Path]::GetRelativePath($source, $file.FullName)
    if ($file.Attributes -band [IO.FileAttributes]::ReparsePoint -or !$expected.ContainsKey($depot) -or
        (Get-FileHash -LiteralPath $file.FullName).Hash -cne $expected[$depot]) { throw "Unexpected resource $depot" }
}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hashes = [WolvenKit.Common.Services.HashService]::new()
$hashes.Load()
$stream = [IO.File]::Open($archive, [IO.FileMode]::CreateNew)
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashes, [WolvenKit.SerilogWrapper]::new())
    if (!$writer.WriteArchive([IO.DirectoryInfo]::new($source), $stream)) { throw 'Archive pack failed' }
} finally { $stream.Dispose() }
$packed = $null
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
if ($reader.ReadArchive($archive, $hashes, [ref]$packed).ToString() -cne 'NoError' -or $packed.Files.Count -ne $expected.Count) {
    throw 'Archive readback inventory failed'
}
$keys = [Collections.Generic.HashSet[uint64]]::new()
$rows = foreach ($depot in ($expected.Keys | Sort-Object)) {
    $key = [uint64][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
    if (!$keys.Add($key) -or !$packed.Files.ContainsKey($key)) { throw "Archive key mismatch at $depot" }
    $buffer = [IO.MemoryStream]::new()
    try {
        $packed.Files[$key].Extract($buffer)
        $actual = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($buffer.ToArray()))
    } finally { $buffer.Dispose() }
    if ($actual -cne $expected[$depot]) { throw "Archived bytes differ at $depot" }
    @{ depot = $depot; sha256 = $actual; key = $key.ToString() }
}
@{
    status = 'PASS_ALL_ARCHIVE_MEMBERS'
    resources = $rows
    archive_sha256 = (Get-FileHash -LiteralPath $archive).Hash
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $result -Encoding utf8NoBOM
