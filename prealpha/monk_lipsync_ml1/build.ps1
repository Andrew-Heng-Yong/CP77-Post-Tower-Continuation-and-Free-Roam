Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$out = Join-Path $PSScriptRoot 'candidate_01'
$readback = Join-Path $out 'readback'
if (Test-Path -LiteralPath $readback) { throw 'Preserve the existing build' }
$prepared = Get-Content -LiteralPath (Join-Path $out 'prepared.json') -Raw | ConvertFrom-Json
$planPath = Join-Path $PSScriptRoot 'plan.json'
if ($prepared.status -cne 'VERIFIED_ML1_INPUTS' -or (Get-FileHash -LiteralPath $planPath).Hash -cne $prepared.plan_sha256) {
    throw 'Prepare and verify the inputs first'
}
$plan = Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json -Depth 100
$manifest = Get-Content -LiteralPath $plan.installed_manifest -Raw | ConvertFrom-Json
$archiveRel = 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$target = Join-Path $out ('package/' + $archiveRel)
if ((Get-FileHash -LiteralPath $target).Hash -cne $plan.archive_sha256 -or
    (Get-FileHash -LiteralPath (Join-Path $manifest.game_root $archiveRel)).Hash -cne $plan.archive_sha256) {
    throw 'Archive baseline changed'
}
$source = Join-Path $out 'archive_source'
$mapPath = Join-Path $source $plan.existing_map.depot
if ((Get-FileHash -LiteralPath $mapPath).Hash -cne $plan.existing_map.sha256 -or
    (Get-FileHash -LiteralPath $plan.native_map.raw).Hash -cne $plan.native_map.sha256) {
    throw 'Lipmap baseline changed'
}
New-Item -ItemType Directory -Path $readback | Out-Null

. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$file = Read-Cr2wFile $mapPath
$map = $file.RootChunk
$stock = (Read-Cr2wFile $plan.native_map.raw).RootChunk
if ($map.ScenePaths.Count -ne 48 -or $map.SceneEntries.Count -ne 48 -or $map.LanguageCodeName.ToString() -cne 'en-us') {
    throw 'Unexpected installed English map'
}
foreach ($row in $plan.additions) {
    $i = [int]$row.native_map_index
    if ($stock.ScenePaths[$i].ToString() -cne $row.native.key) { throw 'Native scene key changed' }
    if (@($map.ScenePaths | Where-Object { $_.ToString() -ceq $row.private.key }).Count) { throw 'Duplicate private scene key' }
    $entry = $stock.SceneEntries[$i].DeepCopy()
    if ($entry.ActorVoiceTags.Count -ne $entry.AnimSets.Count -or
        $row.monk_voice_tag -cnotin @($entry.ActorVoiceTags | ForEach-Object { $_.ToString() })) {
        throw 'Native voice bindings changed'
    }
    $map.ScenePaths.Add([WolvenKit.RED4.Types.CUInt64]::op_Implicit([uint64]$row.private.key))
    $map.SceneEntries.Add($entry)
}
if ($map.ScenePaths.Count -ne 50 -or $map.SceneEntries.Count -ne 50) { throw 'Wrong lipmap delta' }
Write-Cr2wFile $file $mapPath
$mapDigest = (Get-FileHash -LiteralPath $mapPath).Hash
if ((Get-FileHash -LiteralPath $prepared.base_package_manifest).Hash -cne $prepared.base_package_manifest_sha256) { throw 'Package manifest changed' }
$base = Get-Content -LiteralPath $prepared.base_package_manifest -Raw | ConvertFrom-Json -AsHashtable -Depth 100
$expected = @{}
foreach ($item in $base.source_resources.GetEnumerator()) {
    $key = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($item.Key)
    if ($expected.ContainsKey($key)) { throw "Duplicate packed key for $($item.Key)" }
    $digest = if ($item.Key -ceq $plan.existing_map.depot) { $mapDigest } else { $item.Value }
    $expected[$key] = @{depot=$item.Key;sha256=$digest}
}

$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$stream = [IO.File]::Create($target)
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService, [WolvenKit.SerilogWrapper]::new())
    if (!$writer.WriteArchive([IO.DirectoryInfo]::new($source), $stream)) { throw 'Archive packing failed' }
} finally { $stream.Dispose() }
$archive = $null
if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($target, $hashService, [ref]$archive).ToString() -cne 'NoError') {
    throw 'Cannot reopen cooked archive'
}
if ($archive.Files.Count -ne $expected.Count) { throw 'Cooked archive member count changed' }
$rows = [Collections.Generic.List[object]]::new()
foreach ($item in $archive.Files.GetEnumerator()) {
    $row = $expected[$item.Key]
    if (!$row) { throw "Unexpected cooked key $($item.Key)" }
    $stream = [IO.MemoryStream]::new()
    try { $item.Value.Extract($stream); $bytes = $stream.ToArray() } finally { $stream.Dispose() }
    $digest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
    if ($digest -cne $row.sha256) { throw "Cooked payload differs: $($row.depot)" }
    $rows.Add(@{depot=$row.depot;key=$item.Key.ToString();sha256=$digest})
    if ($row.depot -ceq $plan.existing_map.depot) {
        $raw = Join-Path $readback 'en-us.lipmap'
        [IO.File]::WriteAllBytes($raw, $bytes)
        Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $readback 'lipmap.json')
    }
}
$proof = [ordered]@{status='ML1_ARCHIVE_READBACK_PASS';archive_sha256=(Get-FileHash -LiteralPath $target).Hash;
    plan_sha256=$prepared.plan_sha256;map_sha256=$mapDigest;members=$rows.ToArray();game_writes=0;save_writes=0}
$proof | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $readback 'archive.json') -Encoding utf8NoBOM
[pscustomobject]@{archive_members=$rows.Count;map_sha256=$mapDigest;archive_sha256=$proof.archive_sha256} | ConvertTo-Json -Compress
