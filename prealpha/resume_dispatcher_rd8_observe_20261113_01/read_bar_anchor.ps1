# Resolve the installed vanilla bar marker through the registered streaming blocks.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$core = Join-Path $ws 'prealpha/resume_dispatcher_rd8_kirk_20261113_01/core_manifest_01.json'
$game = (Get-Content -Raw -LiteralPath $core | ConvertFrom-Json).game_root
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$base = 'base\worlds\03_night_city\_compiled\default'
$prefab = '$/03_night_city/#c_heywood/glen/loc_sq022_el_coyote_cojo_bar_prefabKDIAKFA/loc_sq022_el_coyote_cojo_bar_questdesign_prefabRNA3BGI/#mq017_pr_streetkid_distance_check'
$anchor = $prefab + '/#mq017_distance_check'
$prefabKey = [WolvenKit.RED4.Types.NodeRef]::CalculateHash($prefab)
$anchorKey = [WolvenKit.RED4.Types.NodeRef]::CalculateHash($anchor)
$hashes = [WolvenKit.Common.Services.HashService]::new()
$hashes.Load()
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
$archives = @{}
foreach ($rel in 'archive/pc/content/basegame_3_nightcity.archive','archive/pc/ep1/ep1_1_nightcity.archive') {
    $archive = $null
    if ($reader.ReadArchive((Join-Path $game $rel), $hashes, [ref]$archive).ToString() -cne 'NoError') { throw "Cannot read $rel" }
    $archives[$rel] = $archive
}
function Get-Part($Entry) {
    $stream = [IO.MemoryStream]::new()
    try {
        $Entry.Extract($stream)
        $stream.Position = 0
        $digest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($stream))
        $stream.Position = 0
        $parser = [WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
        $resource = $null
        if ($parser.ReadFile([ref]$resource, $true).ToString() -cne 'NoError') { throw "Cannot decode $($Entry.Name)" }
        return @{ resource = $resource; sha256 = $digest }
    } finally { $stream.Dispose() }
}
function Key([string]$Path) {
    [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($Path)
}
$blocks = @(foreach ($depot in "$base\blocks\all.streamingblock","$base\ep1\blocks\all.streamingblock") {
    foreach ($rel in $archives.Keys) {
        $archive = $archives[$rel]
        $key = Key $depot
        if (!$archive.Files.ContainsKey($key)) { continue }
        $part = Get-Part $archive.Files[$key]
        $descriptors = @(foreach ($desc in $part.resource.RootChunk.Descriptors) {
            if ($desc.QuestPrefabNodeRef.GetRedHash() -eq $prefabKey) {
                @{ sector = $desc.Data.DepotPath.ToString(); reference = $desc.QuestPrefabNodeRef.ToString();
                    variants = $desc.Variants.Count; category = $desc.Category.ToString() }
            }
        })
        @{ archive = $rel; depot = $depot; sha256 = $part.sha256; descriptors = $descriptors }
    }
})
if ($blocks.Count -lt 2) { throw 'Missing native block variants' }
$sectors = @(foreach ($depot in ($blocks.descriptors.sector | Sort-Object -Unique)) {
    foreach ($rel in $archives.Keys) {
        $key = Key $depot
        if (!$archives[$rel].Files.ContainsKey($key)) { continue }
        $part = Get-Part $archives[$rel].Files[$key]
        $root = $part.resource.RootChunk
        $buffer = $root.NodeData.Buffer.GetBytes()
        if (!$buffer.Length -or $buffer.Length % 144) { throw 'Unexpected placement stride' }
        $markers = @(for ($offset = 0; $offset -lt $buffer.Length; $offset += 144) {
            if ([BitConverter]::ToUInt64($buffer, $offset + 88) -ne $anchorKey) { continue }
            $index = [int]([BitConverter]::ToUInt64($buffer, $offset + 112) -band 0x7FFFF)
            $node = $root.Nodes[$index].Chunk
            $position = @(0,4,8 | ForEach-Object { [BitConverter]::ToSingle($buffer, $offset + $_) })
            $serialized = [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($node,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
            @{ node_index = $index; type = $node.GetType().Name; position = $position;
                streaming_distance = [BitConverter]::ToSingle($buffer, $offset + 124);
                node = ($serialized | ConvertFrom-Json -AsHashtable); setup = [Convert]::ToHexString($buffer, $offset, 144) }
        })
        @{ archive = $rel; depot = $depot; sha256 = $part.sha256; markers = $markers }
    }
})
$report = @{ prefab = $prefab; anchor = $anchor; prefab_hash = $prefabKey.ToString(); anchor_hash = $anchorKey.ToString();
    blocks = $blocks; sectors = $sectors }
$out = [IO.File]::Open((Join-Path $PSScriptRoot 'bar_anchor.json'), [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
try { $out.Write([Text.Encoding]::UTF8.GetBytes(($report | ConvertTo-Json -Depth 12))) } finally { $out.Dispose() }
