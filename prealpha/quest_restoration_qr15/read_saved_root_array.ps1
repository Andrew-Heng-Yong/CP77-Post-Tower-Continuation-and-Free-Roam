# Targeted read of one already-pinned save. Never serializes or writes a save.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$output = Join-Path $PSScriptRoot 'root_saved_resource_array_01'
if (Test-Path -LiteralPath $output) { throw 'Fresh output required' }
$source = 'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077\AutoSave-8\sav.dat'
$metadata = Join-Path (Split-Path $source -Parent) 'metadata.9.json'
$expectedSource = 'AE7331494F242FDCFA9008D86588F9C431B9ABA6092B7E9C845EE78D3D30CE9E'
$expectedMetadata = 'BF3131F582656050F4CAE2A860C93548C1CC4B506B6649B6C8B93D78A24A7D5E'
foreach ($path in @($source, $metadata, $PSScriptRoot)) {
    $item = Get-Item -LiteralPath $path
    while ($null -ne $item) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked input refused' }
        $item = if ($item -is [IO.DirectoryInfo]) { $item.Parent } else { $item.Directory }
    }
}
if ((Get-FileHash -LiteralPath $source).Hash -cne $expectedSource -or (Get-FileHash -LiteralPath $metadata).Hash -cne $expectedMetadata) { throw 'Targeted historical save body changed; do not substitute another save silently' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$data = [IO.File]::ReadAllBytes($source)
if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($data)) -cne $expectedSource) { throw 'Unstable source snapshot' }
$inputMemory = [IO.MemoryStream]::new($data, $false)
$saveReader = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($inputMemory)
$save = $null
try {
    if ($saveReader.ReadFile([ref]$save).ToString() -cne 'NoError') { throw 'Validated save reader failed' }
    $quests = @($save.Nodes | Where-Object Name -ceq 'questSystem')
    if ($quests.Count -ne 1) { throw 'Ambiguous questSystem node' }
    $quest = $quests[0]
    $facts = @($quest.Children | Where-Object Name -ceq 'FactsDB')
    $custom = @($quest.Children | Where-Object Name -ceq 'customArray')
    if ($facts.Count -ne 1 -or $custom.Count -ne 1) { throw 'Required exact inter-child boundary unavailable' }
    $factsNode = $facts[0]
    $customNode = $custom[0]
    if (@($factsNode.Children).Count -ne 10) { throw 'Unexpected fact-store shape' }
    $start = [long]$factsNode.Offset + $factsNode.Size
    $end = [long]$customNode.Offset
    if ($start -ge $end -or $end - $start -gt 65536) { throw 'Unexpected parent gap; no guessed offset search permitted' }

    # ReadFile uses this exact decompression overload for LoadFromStream. Its
    # in-memory layout reconstruction writes only a private MemoryStream.
    # The returned complete decompressed stream is never persisted.
    $compressed = [IO.MemoryStream]::new($data, $false)
    $binary = [IO.BinaryReader]::new($compressed)
    $settings = $null
    $decompressed = $null
    try {
        $decompressed = [WolvenKit.RED4.Save.Compression]::Decompress($binary, [ref]$settings)
        if ($decompressed.Length -lt $end + 4) { throw 'Decompressed span unavailable' }
        $view = [IO.BinaryReader]::new($decompressed, [Text.Encoding]::UTF8, $true)
        try {
            # Positive offset controls: parent, adjacent siblings and all ten
            # physical fact-table IDs must match their parsed node metadata.
            foreach ($node in @($quest, $factsNode, $customNode) + @($factsNode.Children)) {
                $decompressed.Position = $node.Offset
                if ($view.ReadInt32() -ne $node.Id) { throw 'Native-node offset/ID control failed' }
            }
            $decompressed.Position = $start
            $gap = $view.ReadBytes([int]($end - $start))
            if ($gap.Length -ne $end - $start) { throw 'Short parent-gap read' }
        } finally { $view.Dispose() }
    } finally {
        if ($null -ne $decompressed) { $decompressed.Dispose() }
        $binary.Dispose()
    }
    if ((Get-FileHash -LiteralPath $source).Hash -cne $expectedSource -or (Get-FileHash -LiteralPath $metadata).Hash -cne $expectedMetadata) { throw 'Source changed during read' }
    New-Item -ItemType Directory -Path $output | Out-Null
    $gapPath = Join-Path $output 'facts_to_custom_array.bin'
    [IO.File]::WriteAllBytes($gapPath, $gap)
    $boundaries = @($quest) + @($quest.Children) + @($factsNode.Children) | ForEach-Object {
        @{ name = $_.Name; id = $_.Id; offset = $_.Offset; size = $_.Size; data_size = $_.DataSize; trailing_size = $_.TrailingSize; next_id = $_.NextId; child_id = $_.ChildId }
    }
    @{
        status = 'READ_ONLY_EXACT_QUEST_PARENT_GAP'; source = $source; source_sha256 = $expectedSource; metadata = $metadata; metadata_sha256 = $expectedMetadata
        parser = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader].Assembly.Location
        parser_sha256 = (Get-FileHash -LiteralPath ([WolvenKit.RED4.Save.IO.CyberpunkSaveReader].Assembly.Location)).Hash
        start = $start; end = $end; bytes = $gap.Length; gap_path = $gapPath; gap_sha256 = (Get-FileHash -LiteralPath $gapPath).Hash
        boundaries = @($boundaries); offset_id_controls = 13; source_unchanged = $true; save_writes = 0; game_calls = 0
        limits = 'Only the exact FactsDB-end to customArray-start parent gap is persisted. Native resource-array interpretation needs independent decoder and native schema proof. This historical body is not bound to the JF01 loaded session.'
    } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $output 'extraction.json') -Encoding utf8NoBOM
    @{ status = 'EXTRACTED'; bytes = $gap.Length; output = $output } | ConvertTo-Json
} finally { $saveReader.Dispose() }
