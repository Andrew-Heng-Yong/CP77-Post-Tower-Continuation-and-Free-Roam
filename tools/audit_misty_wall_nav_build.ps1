param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$out=Join-Path $WorkspaceRoot 'build\MistyViktorCrowdR6\source'
$vanillaRel='research\misty_viktor_world\r6_wall_nav_sources\ep1_1_nightcity\raw\base\worlds\03_night_city\_compiled\default\ep1\quest_bb3937b6e34a251c.streamingsector'
$vanillaPath=Join-Path $WorkspaceRoot $vanillaRel
$expected='47A17525EF23E21E9E1B35CC97F207A6AABDE7D605EE933182A193538C417952'
if((Get-FileHash -LiteralPath $vanillaPath).Hash -ne $expected){throw 'Vanilla q307 quest sector provenance changed'}
function ReadWorld($path){
 $stream=[IO.File]::OpenRead($path)
 try{
  $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
  $handler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])}
  $reader.add_ParsingError($handler);$file=$null
  if($reader.ReadFile([ref]$file,$true).ToString() -ne 'NoError'){throw "World parse failure: $path"}
  return $file
 }finally{$stream.Dispose()}
}
$vanilla=ReadWorld $vanillaPath
$node=$vanilla.RootChunk.Nodes[62].DeepCopy()
$placement=$vanilla.RootChunk.NodeData.Data[62].DeepCopy()
if($node.Chunk.GetType().Name -ne 'worldCrowdNullAreaNode' -or $node.Chunk.DebugName.ToString() -ne '{q307_cna_alley}' -or $placement.NodeIndex.ToString() -ne '62'){throw 'Exact null area source drifted'}
$privateRef='$/03_night_city/#PTFRMV_TowerStreetCrowdBlocker'
$privateId=[uint64]730000000006062
$node.Chunk.DebugName=[WolvenKit.RED4.Types.CName]::op_Implicit('PTFRMV_TowerStreetCrowdBlocker')
$node.Chunk.SourcePrefabHash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit([uint64]0)
$placement.Id=$privateId
$placement.NodeIndex=[WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]0)
$placement.QuestPrefabRefHash=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($privateRef)
$placement.UkHash1=[WolvenKit.RED4.Types.NodeRef]::op_Implicit('')

# Use an already validated exterior template, not the whole quest-sector owner.
$template=Join-Path $WorkspaceRoot 'build\MistyViktorVariantsR5\source\towercontinued\misty_viktor_world\street_0.streamingsector'
$file=ReadWorld $template
$file.EmbeddedFiles.Clear()
$root=$file.RootChunk
$root.Nodes.Clear();$root.NodeData.Data.Clear();$root.NodeRefs.Clear();$root.LocalInplaceResource.Clear();$root.PersistentNodes.Clear()
[void]$root.Nodes.Add($node);[void]$root.NodeData.Data.Add($placement)
[void]$root.NodeRefs.Add([WolvenKit.RED4.Types.NodeRef]::op_Implicit($privateRef))
if($root.VariantIndices.Count -ne 2 -or $root.VariantIndices[0].ToString() -ne '0' -or $root.VariantIndices[1].ToString() -ne '0'){throw 'Controlled template ranges changed'}
$depot='towercontinued\misty_viktor_world\crowd_alley_r6.streamingsector'
$path=Join-Path $out $depot
Write-Cr2wFile $file $path
$readback=ReadWorld $path
if($readback.RootChunk.Nodes.Count -ne 1 -or $readback.RootChunk.NodeData.Data.Count -ne 1 -or $readback.RootChunk.Nodes[0].Chunk.GetType().Name -ne 'worldCrowdNullAreaNode'){throw 'Crowd-only readback scope mismatch'}
if($readback.RootChunk.NodeData.Data[0].QuestPrefabRefHash.ToString() -ne $privateRef){throw 'Private null area ref readback failed'}
Export-Cr2wJson $readback (Join-Path $audit 'r6_wall_nav_crowd_sector.json')

$block=ReadWorld (Join-Path $WorkspaceRoot 'build\MistyViktorVariantsR5\source\towercontinued\misty_viktor_world\street.streamingblock')
$descriptor=$block.RootChunk.Descriptors[0].DeepCopy()
$block.RootChunk.Descriptors.Clear()
$descriptor.Data=[Activator]::CreateInstance($descriptor.GetType().GetProperty('Data').PropertyType,[object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($depot)))
if($descriptor.Variants.Count -ne 1 -or $descriptor.Variants[0].VariantId.ToString() -ne '3917072702' -or $descriptor.Variants[0].RangeIndex.ToString() -ne '1' -or $descriptor.Variants[0].EnabledByDefault.ToString() -ne 'False'){throw 'Shared street variant metadata changed'}
[void]$block.RootChunk.Descriptors.Add($descriptor)
$blockDepot='towercontinued\misty_viktor_world\crowd_alley_r6.streamingblock'
Write-Cr2wFile $block (Join-Path $out $blockDepot)
$blockReadback=ReadWorld (Join-Path $out $blockDepot)
Export-Cr2wJson $blockReadback (Join-Path $audit 'r6_wall_nav_crowd_block.json')
$manifest=[ordered]@{
 status='BUILT_SOURCE_ONLY_NOT_PACKED_INSTALLED_OR_LIVE'
 source=$vanillaRel;source_sha256=$expected;source_node=62;source_data_index=62
 source_owner='$/03_night_city/c_watson/little_china/loc_mystic_mistys_ripperdoc_prefabH2DWJJI/loc_mystic_mistys_ripperdoc_questdesign_prefabJOEMBAA/#q307_pr_misty/#q307_cna_alley'
 source_node_type='worldCrowdNullAreaNode';private_ref=$privateRef;private_id=$privateId
 source_permanently_enabled_by_default=$false;private_permanently_enabled_by_default=$false
 retained='Exact outline buffer, shape properties, position, rotation, scale, native flags'
 changed='Only debug name, sourcePrefabHash=0, private global ID, NodeIndex=0, private ref, UkHash1=empty'
 resources=@($depot,$blockDepot);variant_name='PTFRMV_TowerStreet';variant_owner='$/03_night_city/c_watson/little_china/wlc_02/#wlc_02_b_env';variant_id=3917072702
 default_range_node_count=0;controlled_range_index=1;nodes=1;placements=1
 node_enable_required='questCrowdManagerNodeType_EnableNullArea(private_ref,true) after node streams; false before variant teardown. Streaming alone is not activation proof.'
 activation_precedent='q307_05_alley.questphase enables #q307_cna_alley; q307_cleanup.questphase disables it.'
 reroutes_existing_pedestrians='UNVERIFIED; crowd exclusion is not a navmesh rebuild'
 sha256=(Get-FileHash -LiteralPath $path).Hash;block_sha256=(Get-FileHash -LiteralPath (Join-Path $out $blockDepot)).Hash
 live_tested=$false;packed=$false;installed=$false
}
[IO.File]::WriteAllText((Join-Path $audit 'r6_wall_nav_crowd_manifest.json'),($manifest|ConvertTo-Json -Depth 7),[Text.UTF8Encoding]::new($false))
$manifest|ConvertTo-Json -Depth 4
