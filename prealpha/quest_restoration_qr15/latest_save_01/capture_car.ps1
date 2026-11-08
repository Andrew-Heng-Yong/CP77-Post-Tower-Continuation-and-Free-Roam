# Read only the earlier positive fixture's community component and four bound PS keys.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = (Get-Item -LiteralPath (Join-Path $PSScriptRoot '../../..')).FullName
$output = Join-Path $PSScriptRoot 'car_capture_01'
if (Test-Path -LiteralPath $output) { throw 'Use a fresh output' }
$positivePath = Join-Path $workspace 'prealpha/quest_restoration_qr15/earlier_saves_01/capture_03/wa1backup16.json'
$positive = Get-Content -LiteralPath $positivePath -Raw | ConvertFrom-Json
$source = Join-Path $workspace 'recovery/world_combat_wa1_01/autosaves_before_test/AutoSave-16/sav.dat'
$metadata = Join-Path (Split-Path $source -Parent) 'metadata.9.json'
$sourceHash = 'E5E0C78C0604BFC5840ECBFDEF95A78554207705C190FAD5FEE1713E8E5D8F5E'
if ($positive.source -ine $source -or $positive.metadata -ine $metadata -or $positive.source_sha256 -cne $sourceHash) {
    throw 'Unexpected earlier fixture binding'
}
foreach ($path in @($source,$metadata,$PSScriptRoot)) {
    $item = Get-Item -LiteralPath $path
    while ($null -ne $item) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked input or output refused' }
        $item = if ($item -is [IO.DirectoryInfo]) { $item.Parent } else { $item.Directory }
    }
}
function Assert-Pair {
    if ((Get-FileHash -LiteralPath $source).Hash -cne $sourceHash -or (Get-FileHash -LiteralPath $metadata).Hash -cne $positive.metadata_sha256) {
        throw 'Earlier fixture changed'
    }
}
Assert-Pair
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$readerHash = 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987'
if ((Get-FileHash -LiteralPath ([WolvenKit.RED4.Save.IO.CyberpunkSaveReader].Assembly.Location)).Hash -cne $readerHash) { throw 'Unexpected reader assembly' }
$bytes = [IO.File]::ReadAllBytes($source)
if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $sourceHash) { throw 'Unstable body snapshot' }
$reader = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new([IO.MemoryStream]::new($bytes,$false))
$save = $null
try {
    if ($reader.ReadFile([ref]$save).ToString() -cne 'NoError') { throw 'Save parser failed' }
    if ($save.FileHeader.SaveVersion -ne 277 -or $save.FileHeader.GameVersion -ne 2500) { throw 'Unexpected native format' }
    $communityName = [WolvenKit.RED4.Save.CommunitySystemParser]::NodeName
    $psName = [WolvenKit.RED4.Save.PersistencySystem2Parser]::NodeName
    $communityNodes = @($save.Nodes | Where-Object Name -ceq $communityName)
    $psNodes = @($save.Nodes | Where-Object Name -ceq $psName)
    if ($communityNodes.Count -ne 1 -or $communityNodes[0].Value -isnot [WolvenKit.RED4.Save.CommunitySystem] -or
        $psNodes.Count -ne 1 -or $psNodes[0].Value -isnot [WolvenKit.RED4.Save.PersistencySystem2]) { throw 'Required save components unavailable' }
    $node = $communityNodes[0]
    $tail = $node.Value.TrailingBytes
    $outerKeys = @($node.Value.Unk_HashList | ForEach-Object { $_.ToString() })
    if ($tail.Length -gt 8388608 -or $node.TrailingSize -ne 0 -or $node.Size -ne (8 + 8 * $outerKeys.Count + $tail.Length)) {
        throw 'Unexpected community span'
    }
    $ps = $psNodes[0].Value
    $targetKeys = @('10229047','6695448052237678836','15311582179580628726','17113219195054135786')
    $targetSet = [Collections.Generic.HashSet[uint64]]::new()
    foreach ($key in $targetKeys) { [void]$targetSet.Add([uint64]$key) }
    $rows = @(
        foreach ($entry in $ps.Entries) {
            if ($targetSet.Contains($entry.Id)) {
                @{id_u64=$entry.Id.ToString(); parsed_class=if ($null -eq $entry.Data) { 'NULL' } else { $entry.Data.GetType().Name }}
            }
        }
    )
    Assert-Pair
    New-Item -ItemType Directory -Path $output | Out-Null
    $tailPath = Join-Path $output 'community_trailing.bin'
    [IO.File]::WriteAllBytes($tailPath,$tail)
    @{
        status='EARLIER_CAR_COMPONENT_CAPTURE'; source=$source; source_sha256=$sourceHash
        metadata=$metadata; metadata_sha256=$positive.metadata_sha256; reader_sha256=$readerHash
        save_version=277; game_version=2500; outer_keys=$outerKeys; node_size=$node.Size
        trailing_path=$tailPath; trailing_sha256=(Get-FileHash -LiteralPath $tailPath).Hash
        ps2_entry_count=$ps.Entries.Count; queried_keys=$targetKeys; matching_rows=$rows
        source_unchanged=$true; save_writes=0; game_calls=0
    } | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath (Join-Path $output 'capture.json') -Encoding utf8NoBOM
    @{status='CAPTURED'; ps_entries=$ps.Entries.Count; matches=$rows.Count; community_bytes=$tail.Length; output=$output} | ConvertTo-Json
} finally { $reader.Dispose() }
