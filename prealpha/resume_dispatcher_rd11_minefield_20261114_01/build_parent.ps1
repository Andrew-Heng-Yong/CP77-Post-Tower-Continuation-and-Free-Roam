# Build the unregistered Minefield handoff against the installed RD10 providers.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out = Join-Path $PSScriptRoot 'graph_03'
if (Test-Path -LiteralPath $out) { throw 'Fresh output required' }

$manifestPath = Join-Path $ws 'prealpha/resume_dispatcher_rd10_kirk_20261113_01/deployment_01/installed_manifest_01.json'
$manifestHash = (Get-FileHash -LiteralPath $manifestPath).Hash
if ($manifestHash -cne 'AB279745469DEE08EC9A816EE9F04C9F9750456DE26A9C6CC8940E15FAFE56D8') { throw 'RD10 manifest drift' }
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
$installedArchive = Join-Path $manifest.game_root 'archive/pc/mod/zzzz_PTFR_Combined.archive'
if ((Get-FileHash -LiteralPath $installedArchive).Hash -cne $manifest.archive_sha256) { throw 'Installed archive drift' }

$bodyPath = Join-Path $ws 'prealpha/resume_dispatcher_rd6_batch50_20261113_01/minefield/graph_01/sts_bls_ina_07_body.questphase'
$bodyHash = '18E7653C49B4D12D4D3557DC34DD0D18DF5B63239456D29BCFD636FF8194912D'
if ((Get-FileHash -LiteralPath $bodyPath).Hash -cne $bodyHash) { throw 'Reviewed Minefield entrance drift' }
$prefix = 'towercontinued\native_gigs_u9\resume\'
$parentName = 'sts_bls_ina_07_parent.questphase'
$parentDepot = $prefix + $parentName
$bodyDepot = $prefix + 'sts_bls_ina_07_body.questphase'
$stage = 'ResumeFindTheCar'

. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$names = [WolvenKit.Common.Services.HashService]::new()
$names.Load()
$watch = @{}
foreach ($pin in @(
    @{depot='towercontinued\johnny_batch4\sts_bls_ina_07\sts_bls_ina_07.questphase'; archive=$installedArchive;
      sha256='08268D05B5A02868E4EEE4E97B01066C8CD63D22B17FFEC22635160AA3153C51'; filename='original.questphase'},
    @{depot='base\open_world\street_stories\badlands\inland_avenue\sts_bls_ina_07\phases\sts_bls_ina_07_gpl.questphase';
      archive=(Join-Path $manifest.game_root 'archive/pc/content/basegame_4_gamedata.archive');
      sha256='CB15A2A51E4128A2735F0E9927009B1C34BADA0871DF89C6FBAF45AF02D81783'; filename='gameplay.questphase'}
)) {
    $key = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($pin.depot)
    $watch.Add($key,$pin)
}
$privateKeys = @($parentDepot,$bodyDepot | ForEach-Object { [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($_) })
if ($privateKeys[0] -eq $privateKeys[1]) { throw 'Private depot hash collision' }

[void][IO.Directory]::CreateDirectory($out)
$seen = [Collections.Generic.HashSet[uint64]]::new()
$archiveCount = 0
foreach ($root in @((Join-Path $manifest.game_root 'archive/pc'),(Join-Path $manifest.game_root 'mods'))) {
    if (!(Test-Path -LiteralPath $root)) { continue }
    if ((Get-Item -LiteralPath $root -Force).Attributes -band [IO.FileAttributes]::ReparsePoint -or
        @(Get-ChildItem -LiteralPath $root -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked archive tree' }
    foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.archive') {
        $stamp = @($file.Length,$file.LastWriteTimeUtc.Ticks)
        $archive = $null
        if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$names,[ref]$archive).ToString() -cne 'NoError') {
            throw "Unreadable archive: $file"
        }
        foreach ($key in $privateKeys) {
            if ($archive.Files.ContainsKey($key)) { throw "Private depot already installed: $key" }
        }
        foreach ($key in $watch.Keys) {
            if (!$archive.Files.ContainsKey($key)) { continue }
            $pin = $watch[$key]
            if ($pin.archive -ine $file.FullName -or !$seen.Add($key)) {
                throw "Unexpected provider for $($pin.depot): $($file.FullName)"
            }
            $memory = [IO.MemoryStream]::new()
            try {
                $archive.Files[$key].Extract($memory)
                $bytes = $memory.ToArray()
            } finally { $memory.Dispose() }
            if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $pin.sha256) { throw "Provider drift: $($pin.depot)" }
            [IO.File]::WriteAllBytes((Join-Path $out $pin.filename), $bytes)
        }
        $file.Refresh()
        if ($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1]) { throw 'Archive changed during review' }
        $archiveCount++
    }
}
if ($seen.Count -ne $watch.Count) { throw 'Missing reviewed providers' }

$originalPath = Join-Path $out 'original.questphase'
$original = Read-Cr2wFile $originalPath
$file = Read-Cr2wFile $originalPath
$source = $original.RootChunk.Graph.Chunk
$graph = $file.RootChunk.Graph.Chunk
$graph.Nodes.Clear()
Add-RedHandle $graph.Nodes (New-InputNode 1000 $stage)
foreach ($id in @(273,282,117,118,235)) {
    $node = (Get-QuestNode $source $id).DeepCopy()
    foreach ($handle in $node.Sockets) { $handle.Chunk.Connections.Clear() }
    Add-RedHandle $graph.Nodes $node
}

$bodyCall = Get-QuestNode $graph 118
if ($null -ne $bodyCall.PhaseGraph -and $null -ne $bodyCall.PhaseGraph.Chunk) { throw 'Expected an external phase call' }
(Get-QuestSocket $bodyCall 'In1').Name = $stage
$bodyCall.PhaseResource = [WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($bodyDepot)

foreach ($edge in @(
    @(1000,'Out',273,'In'),
    @(273,'Out',282,'In'),
    @(282,'Out',117,'In1'),
    @(282,'Out',118,$stage),
    @(118,'Out1',235,'In')
)) {
    $from = Get-QuestSocket (Get-QuestNode $graph $edge[0]) $edge[1]
    $to = Get-QuestSocket (Get-QuestNode $graph $edge[2]) $edge[3]
    [void](Connect-QuestSockets $from $to)
}

$parentPath = Join-Path $out $parentName
Write-Cr2wFile $file $parentPath
foreach ($path in @($originalPath,$parentPath,(Join-Path $out 'gameplay.questphase'))) {
    Export-Cr2wJson (Read-Cr2wFile $path) ($path + '.json')
}
@{
    archive_sha256 = $manifest.archive_sha256; installed_manifest_sha256 = $manifestHash; scanned_archives = $archiveCount
    private_parent = $parentDepot; private_body = $bodyDepot; private_keys = @($privateKeys | ForEach-Object { $_.ToString() })
    parent_sha256 = (Get-FileHash -LiteralPath $parentPath).Hash; parent_export_sha256 = (Get-FileHash -LiteralPath ($parentPath+'.json')).Hash
    body_sha256 = $bodyHash; providers = @($watch.Values); runtime_admission = 0
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
Write-Output "Read back the private Minefield parent. Checked both new depot keys and both retained providers across $archiveCount archives."
