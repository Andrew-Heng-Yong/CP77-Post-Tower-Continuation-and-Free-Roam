Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out = Join-Path $PSScriptRoot 'native_01'
if (Test-Path -LiteralPath $out) { throw 'Fresh capture required' }
$archiveRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc'
$world = 'base\worlds\03_night_city\_compiled\default'
$inputs = [ordered]@{
    street = "$world\ep1\quest_e1a2ca39daf3e5ef.streamingsector"
    guard = "$world\ep1\quest_7a9b44ec65844635.streamingsector"
    block = "$world\ep1\blocks\all.streamingblock"
    club = 'ep1\openworld\community\quest_communities\heavy_hearts.questphase'
    root = 'ep1\quest\ep1.quest'
    registry0 = "$world\always_loaded_0.streamingsector"
    registry1 = "$world\always_loaded_1.streamingsector"
    registry2 = "$world\always_loaded_2.streamingsector"
    registryEP = "$world\ep1\always_loaded_0.streamingsector"
}
$nativePins = @{
    street = '0981213211DE646607CB1F774A4506219E7AC5B53887BE785E3F7E883F6D83D5'
    guard = 'D4F16B96E02B0083C5C408C8A74FEE9976D31712524A465769853051E3C7D0DC'
    block = '4F17762B48D9F5019228B1BF930558A9CC1E7C365E7002725D670A23585215B9'
    club = 'D6AAC7A4CD21820F8093BD3F3C76422A3DA5A68B39D7709DAD36F6C4C060C62C'
}
$hashes = [WolvenKit.Common.Services.HashService]::new()
$hashes.Load()
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
$keys = @{}
foreach ($item in $inputs.GetEnumerator()) {
    $keys.Add([WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($item.Value), $item.Key)
}
$selected = @{}
$providers = @()
$archives = @(Get-ChildItem -LiteralPath $archiveRoot -Filter '*.archive' -Recurse -File)
foreach ($file in $archives) {
    $archive = $null
    if ($reader.ReadArchive($file.FullName, $hashes, [ref]$archive).ToString() -cne 'NoError') { throw "Unreadable archive: $file" }
    foreach ($key in $keys.Keys) {
        if (!$archive.Files.ContainsKey([uint64]$key)) { continue }
        $name = $keys[$key]
        $providers += @{ name = $name; archive = $file.Name; depot = $inputs[$name]; key = $key.ToString() }
        if ($file.Name -ceq 'basegame_3_nightcity.archive' -and $name -in @('block','registry0','registry1','registry2')) { continue }
        $expected = if ($name -in @('club','root')) { 'ep1_2_gamedata.archive' } else { 'ep1_1_nightcity.archive' }
        if ($file.Name -cne $expected -or $selected.ContainsKey($name)) { throw "Unexpected provider for ${name}: $file" }
        $selected.Add($name, $archive.Files[[uint64]$key])
    }
}
if ($selected.Count -ne $inputs.Count) { throw 'Missing current provider' }
New-Item -ItemType Directory -Path $out | Out-Null
$pins = @{}
$refs = @{}
$registry = @()
$areas = @()
function Read-World($stream) {
    $r = [WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
    $r.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{ param($e) return $e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs] })
    $f = $null
    if ($r.ReadFile([ref]$f,$true).ToString() -cne 'NoError') { throw 'Native sector decode failed' }
    return $f
}
function Json($object) {
    return [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($object,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
}
foreach ($name in $inputs.Keys) {
    $m = [IO.MemoryStream]::new()
    try {
        $selected[$name].Extract($m)
        $hash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()))
        if ($nativePins.ContainsKey($name) -and $hash -cne $nativePins[$name]) { throw "Native donor changed: $name" }
        $pins.Add($name, $hash)
        if (!$name.StartsWith('registry')) {
            $leaf = $name+[IO.Path]::GetExtension($inputs[$name])
            [IO.File]::WriteAllBytes((Join-Path $out $leaf),$m.ToArray())
        }
        if ($name -notin @('street','guard','registry0','registry1','registry2','registryEP')) { continue }
        $m.Position = 0
        $sector = (Read-World $m).RootChunk
        foreach ($ref in $sector.NodeRefs) {
            $value = $ref.ToString()
            if ($value -match 'loc_sts_ep1_06_.*(com_crowd|com_civilians|com_fake_barghest_guard|sts_ep1_06_chat|com_fake_combat_npcs)' ) {
                $refs[[WolvenKit.RED4.Types.NodeRef]::CalculateHash($value).ToString()] = $value
            }
        }
        foreach ($node in $sector.Nodes) {
            $item = $node.Chunk
            if ($item.GetType().Name -ceq 'worldCommunityRegistryNode') { $registry += @($item.CommunitiesData) }
            if ($item.GetType().Name -like 'worldCompiledCommunityAreaNode*') { $areas += $item }
        }
        if ($name -notin @('street','guard')) { continue }
        $meta = [ordered]@{
            nodes = @(for ($i=0; $i -lt $sector.Nodes.Count; $i++) { @{ index=$i; payload=(Json $sector.Nodes[$i].Chunk | ConvertFrom-Json -Depth 100) } })
            variants = @($sector.VariantIndices | ForEach-Object { [int]$_.ToString() })
            variant_nodes = @($sector.VariantNodes | ForEach-Object { $_.Count })
            persistent_nodes = $sector.PersistentNodes.Count
            placements = @(
                $bytes = $sector.NodeData.Buffer.GetBytes()
                if ($bytes.Length -ne $sector.NodeData.Data.Count * 144) { throw 'Placement stride mismatch' }
                for ($i=0; $i -lt $sector.NodeData.Data.Count; $i++) {
                    $p = $sector.NodeData.Data[$i]
                    @{ index=$i; node=[int]([BitConverter]::ToUInt64($bytes, $i*144+112) -band 0x7FFFF);
                       xyz=@([double]$p.Position.X.ToString(),[double]$p.Position.Y.ToString(),[double]$p.Position.Z.ToString());
                       ref=$p.QuestPrefabRefHash.ToString(); id=$p.Id.ToString() }
                }
            )
        }
        $meta | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath (Join-Path $out "$name.json") -Encoding utf8NoBOM
    } finally { $m.Dispose() }
}
foreach ($name in @('club.questphase','root.quest','block.streamingblock')) {
    $path = Join-Path $out $name
    Export-Cr2wJson (Read-Cr2wFile $path) ($path+'.json')
}
$communities = @(
    foreach ($item in $registry) {
        $id = $item.CommunityId.EntityId.Hash.ToString()
        if ($refs.ContainsKey($id)) { @{ hash=$id; ref=$refs[$id]; registry=(Json $item | ConvertFrom-Json -Depth 100) } }
    }
)
$placed = @(
    foreach ($item in $areas) {
        $id = $item.SourceObjectId.Hash.ToString()
        if ($refs.ContainsKey($id)) { @{ hash=$id; ref=$refs[$id]; area=(Json $item | ConvertFrom-Json -Depth 100) } }
    }
)
@{ archives=$archives.Count; providers=$providers; pins=$pins; refs=$refs; communities=$communities; areas=$placed } |
    ConvertTo-Json -Depth 100 | Set-Content -LiteralPath (Join-Path $out 'capture.json') -Encoding utf8NoBOM
Write-Output "Captured $($communities.Count) registry and $($placed.Count) placement matches"
