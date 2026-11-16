Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out = Join-Path $PSScriptRoot 'candidate_01/truck/area_inputs.json'
$rawSector = Join-Path (Split-Path $out -Parent) 'garage.streamingsector'
$setups = Join-Path (Split-Path $out -Parent) 'garage.setups.bin'
if ((Test-Path -LiteralPath $out) -or (Test-Path -LiteralPath $rawSector) -or (Test-Path -LiteralPath $setups)) {
    throw 'Preserve existing garage area proof'
}
$game = (Get-Content -LiteralPath (Join-Path $ws 'prealpha/johnny_batch4_jb3/deployment_01/installed_manifest_01.json') -Raw | ConvertFrom-Json).game_root
$depot = 'base\worlds\03_night_city\_compiled\default\quest_2c1c6fb4f5331fdf.streamingsector'
$blockDepot = 'base\worlds\03_night_city\_compiled\default\blocks\all.streamingblock'
$key = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
$blockKey = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($blockDepot)
$hashes = [WolvenKit.Common.Services.HashService]::new()
$hashes.Load()
$archiveReader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
$providers = @()
$blocks = @()
function ReadPacked($member) {
    $mem = [IO.MemoryStream]::new()
    try {
        $member.Extract($mem)
        $sha = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))
        $mem.Position = 0
        $reader = [WolvenKit.RED4.Archive.IO.CR2WReader]::new($mem)
        $reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{
            param($e) return $e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs]
        })
        $file = $null
        if ($reader.ReadFile([ref]$file,$true).ToString() -cne 'NoError') { throw 'Garage provider decoding failed' }
        return @{sha256=$sha;root=$file.RootChunk}
    } finally { $mem.Dispose() }
}
function CapturePackedSector($member) {
    $mem = [IO.MemoryStream]::new()
    $decoded = [IO.MemoryStream]::new()
    try {
        $member.Extract($mem)
        $mem.Position = 0
        $reader = [WolvenKit.RED4.Archive.IO.CR2WReader]::new($mem)
        $info = $null
        if ($reader.ReadFileInfo([ref]$info,$null).ToString() -cne 'NoError') { throw 'Garage CR2W table read failed' }
        $buffer = $info.BufferInfo[0]
        if ($buffer.memSize -eq 0 -or $buffer.memSize % 144 -ne 0) { throw 'Garage setup size mismatch' }
        $mem.Position = $buffer.offset
        [WolvenKit.Core.Compression.Oodle]::DecompressAndCopySegment($mem,$decoded,$buffer.diskSize,$buffer.memSize)
        if ($decoded.Length -ne $buffer.memSize) { throw 'Garage setup decompression failed' }
        [IO.File]::WriteAllBytes($rawSector,$mem.ToArray())
        [IO.File]::WriteAllBytes($setups,$decoded.ToArray())
        return @{raw=$rawSector;sha256=(Get-FileHash -LiteralPath $rawSector).Hash;buffer=$setups;
                 buffer_sha256=(Get-FileHash -LiteralPath $setups).Hash;offset=$buffer.offset;disk_size=$buffer.diskSize;size=$buffer.memSize}
    } finally { $decoded.Dispose(); $mem.Dispose() }
}
foreach ($archiveFile in Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc') -File -Recurse -Filter '*.archive') {
    $archive = $null
    if ($archiveReader.ReadArchive($archiveFile.FullName,$hashes,[ref]$archive).ToString() -cne 'NoError') { throw "Cannot index $archiveFile" }
    if ($archive.Files.ContainsKey($key)) {
        if ($providers.Count) { throw 'Multiple garage sector providers' }
        $row = CapturePackedSector $archive.Files[$key]
        $row.archive = $archiveFile.FullName
        $providers += $row
    }
    if ($archive.Files.ContainsKey($blockKey) -and $archiveFile.Name -in @('basegame_3_nightcity.archive','ep1_1_nightcity.archive')) {
        $row = ReadPacked $archive.Files[$blockKey]
        $descriptors = @($row.root.Descriptors | Where-Object { $_.Data.DepotPath.ToString() -ceq $depot })
        if ($descriptors.Count -eq 1) {
            $blocks += @{archive=$archiveFile.FullName;sha256=$row.sha256;prefab=$descriptors[0].QuestPrefabNodeRef.ToString()}
        }
    }
}
if ($providers.Count -ne 1 -or !$providers[0].archive.EndsWith('\basegame_3_nightcity.archive')) { throw 'Unexpected garage sector providers' }
if ($blocks.Count -lt 1 -or @($blocks | Where-Object { !$_.prefab.EndsWith('/#mq017_pr_van_hideout') }).Count) {
    throw 'Missing vanilla garage prefab descriptor'
}
@{status='CAPTURED_STOCK_GARAGE_SECTOR';depot=$depot;sector=$providers[0];blocks=$blocks;
  typed_decode_limit='WolvenKit 9.1 DynamicBaseClass to worldNode in garage sector'} | ConvertTo-Json -Depth 6 |
    Set-Content -LiteralPath $out -Encoding utf8NoBOM
Write-Output 'Captured the native garage sector and decompressed placement table.'
