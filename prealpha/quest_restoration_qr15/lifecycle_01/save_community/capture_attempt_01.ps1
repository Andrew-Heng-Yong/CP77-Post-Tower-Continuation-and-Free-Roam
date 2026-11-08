# Read one already-pinned save's community component only. Never write a save.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = (Get-Item -LiteralPath (Join-Path $PSScriptRoot '../../../..')).FullName
$output = Join-Path $PSScriptRoot 'capture_01'
if (Test-Path -LiteralPath $output) { throw 'Fresh output required' }
$source = 'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077\AutoSave-8\sav.dat'
$metadata = Join-Path (Split-Path $source -Parent) 'metadata.9.json'
$sourceHash = 'AE7331494F242FDCFA9008D86588F9C431B9ABA6092B7E9C845EE78D3D30CE9E'
$metadataHash = 'BF3131F582656050F4CAE2A860C93548C1CC4B506B6649B6C8B93D78A24A7D5E'
foreach ($path in @($source, $metadata, $PSScriptRoot)) {
    $item = Get-Item -LiteralPath $path
    while ($null -ne $item) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked input/output refused' }
        $item = if ($item -is [IO.DirectoryInfo]) { $item.Parent } else { $item.Directory }
    }
}
if ((Get-FileHash -LiteralPath $source).Hash -cne $sourceHash -or (Get-FileHash -LiteralPath $metadata).Hash -cne $metadataHash) { throw 'Historical body changed; no silent substitute' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$assembly = [WolvenKit.RED4.Save.CommunitySystem].Assembly
if ((Get-FileHash -LiteralPath $assembly.Location).Hash -cne 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987') { throw 'Reader assembly drift' }
$bytes = [IO.File]::ReadAllBytes($source)
if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $sourceHash) { throw 'Unstable source snapshot' }
$memory = [IO.MemoryStream]::new($bytes, $false)
$reader = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($memory)
$save = $null
try {
    if ($reader.ReadFile([ref]$save).ToString() -cne 'NoError') { throw 'Save parser failed' }
    $parser = [WolvenKit.RED4.Save.CommunitySystemParser]::new()
    $nodes = @($save.Nodes | Where-Object Name -ceq $parser.NodeName)
    if ($nodes.Count -ne 1 -or $nodes[0].Value -isnot [WolvenKit.RED4.Save.CommunitySystem]) { throw 'Exact community component unavailable' }
    $node = $nodes[0]
    $tail = $node.Value.TrailingBytes
    if ($tail.Length -gt 8388608) { throw 'Component capture exceeds8MiB bound' }
    $hashList = @($node.Value.Unk_HashList | ForEach-Object { $_.ToString() })
    $id = [uint64]17433794865907239043
    $needle = [BitConverter]::GetBytes($id)
    $hits = [Collections.Generic.List[int]]::new()
    for ($index = 0; $index -le $tail.Length - 8; $index++) {
        if ($tail[$index] -ne $needle[0]) { continue }
        $same = $true
        for ($part = 1; $part -lt 8; $part++) { if ($tail[$index + $part] -ne $needle[$part]) { $same = $false; break } }
        if ($same) { $hits.Add($index) }
        if ($hits.Count -gt 32) { throw 'Target signature not sufficiently bounded; do not infer a schema' }
    }
    if ((Get-FileHash -LiteralPath $source).Hash -cne $sourceHash -or (Get-FileHash -LiteralPath $metadata).Hash -cne $metadataHash) { throw 'Source changed during capture' }
    New-Item -ItemType Directory -Path $output | Out-Null
    $tailPath = Join-Path $output 'community_trailing.bin'
    [IO.File]::WriteAllBytes($tailPath, $tail)
    $readMethod = [WolvenKit.RED4.Save.CommunitySystemParser].GetMethod('Read')
    @{
        status = 'READ_ONLY_PINNED_COMPONENT_UNINTERPRETED'; source = $source; source_sha256 = $sourceHash; metadata = $metadata; metadata_sha256 = $metadataHash
        save_version = $save.FileHeader.SaveVersion; game_version = $save.FileHeader.GameVersion
        reader = $assembly.Location; reader_sha256 = (Get-FileHash -LiteralPath $assembly.Location).Hash
        parser_read_il = [Convert]::ToHexString($readMethod.GetMethodBody().GetILAsByteArray())
        node = @{ name = $node.Name; offset = $node.Offset; size = $node.Size; data_size = $node.DataSize; trailing_size = $node.TrailingSize }
        unknown_hash_list = $hashList; unknown_hash_list_count = $hashList.Count
        trailing_path = $tailPath; trailing_sha256 = (Get-FileHash -LiteralPath $tailPath).Hash; trailing_bytes = $tail.Length
        target_node_id_u64 = $id.ToString(); target_little_endian_hex = [Convert]::ToHexString($needle)
        target_in_unknown_hash_list = $hashList.Contains($id.ToString()); target_uninterpreted_byte_offsets = @($hits)
        limits = 'Only a candidate64bit signature lookup in an otherwise opaque component. Neither a hit nor a miss proves saved spawner state, absence, lifecycle or loaded-body identity. Requires native serializer/reader schema before interpretation.'
        game_calls = 0; source_unchanged = $true; save_writes = 0
    } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $output 'capture.json') -Encoding utf8NoBOM
    @{ status = 'CAPTURED_UNINTERPRETED'; component = $node.Name; unknown_hashes = $hashList.Count; trailing_bytes = $tail.Length; candidate_offsets = @($hits) } | ConvertTo-Json -Depth 3
} finally { $reader.Dispose() }
