Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out = Join-Path $PSScriptRoot 'candidate_01'
$plan = Get-Content -LiteralPath (Join-Path $out 'pack_inputs.json') -Raw | ConvertFrom-Json -AsHashtable
$manifest = Join-Path $out 'archive_readback.json'
if (Test-Path -LiteralPath $manifest) { throw 'Preserve existing archive readback' }
$archivePath = Join-Path $out 'package/archive/pc/mod/zzzz_PTFR_Combined.archive'
if ((Get-FileHash -LiteralPath $archivePath).Hash -cne $plan.before_archive) { throw 'Wrong archive predecessor' }

$source = Join-Path $out 'archive_source'
$expected = @{}
foreach ($item in $plan.resources.GetEnumerator()) {
    $key = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($item.Key)
    if ($expected.ContainsKey($key)) { throw "Duplicate archive key $($item.Key)" }
    $expected[$key] = @{depot=$item.Key;sha256=$item.Value}
}
$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$stream = [IO.File]::Create($archivePath)
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService,[WolvenKit.SerilogWrapper]::new())
    if (!$writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)) { throw 'Cannot pack QP1 archive' }
} finally { $stream.Dispose() }

$archive = $null
if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archivePath,$hashService,[ref]$archive).ToString() -cne 'NoError' -or
    $archive.Files.Count -ne $expected.Count) { throw 'Cannot reopen exact QP1 archive' }
$actual = @{}
foreach ($member in $archive.Files.GetEnumerator()) {
    if (!$expected.ContainsKey($member.Key)) { throw "Unexpected archive member $($member.Key)" }
    $row = $expected[$member.Key]
    $mem = [IO.MemoryStream]::new()
    try {
        $member.Value.Extract($mem)
        $digest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))
    } finally { $mem.Dispose() }
    if ($digest -cne $row.sha256) { throw "Archive readback differs: $($row.depot)" }
    $actual.Add($row.depot,$digest)
}
@{status='PASS_QP1_ARCHIVE_READBACK';members=$actual;archive_sha256=(Get-FileHash -LiteralPath $archivePath).Hash;
  inputs_sha256=(Get-FileHash -LiteralPath (Join-Path $out 'pack_inputs.json')).Hash;game_writes=0;save_writes=0} |
    ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $manifest -Encoding utf8NoBOM
Write-Output "Read back all $($actual.Count) archive payloads."
