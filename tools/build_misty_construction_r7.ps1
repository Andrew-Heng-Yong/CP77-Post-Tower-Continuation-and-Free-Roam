param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$plan=Get-Content (Join-Path $audit 'r7_construction_audit.json') -Raw|ConvertFrom-Json -Depth 100
if($plan.status -ne 'SOURCE_AUDITED_TWO_PILES_NOT_INSTALLED_OR_LIVE' -or $plan.selected_node_count -ne 6 -or $plan.visible_mesh_instances -ne 18){throw 'Construction audit changed'}
$source=Join-Path $WorkspaceRoot 'build\MistyViktorConstructionR7\source'
$sourcePath=Join-Path $WorkspaceRoot $plan.source_raw
if((Get-FileHash -LiteralPath $sourcePath).Hash -ne $plan.source_sha256){throw 'Construction source hash changed'}
$original=Read-Cr2wFile $sourcePath
$selected=@($plan.selected_rows)
$nodes=@($original.RootChunk.Nodes);$placements=@($original.RootChunk.NodeData.Data)
$shared=$nodes[[int]$selected[0].node_index].Chunk.CookedInstanceTransforms.SharedDataBuffer.DeepCopy()
$allTransforms=@($shared.Chunk.Buffer.Data.Transforms)
$shared.Chunk.Buffer.Data.Transforms.Clear()

# This source has no dependencies on ending entities; preserve native physics
# and trim its cooked transform buffer to exactly the six audited groups.
$file=Read-Cr2wFile (Join-Path $WorkspaceRoot 'build\MistyViktorRepairR6\source\towercontinued\misty_viktor_world\street_0.streamingsector')
$file.EmbeddedFiles.Clear()
$root=$file.RootChunk
$root.Nodes.Clear();$root.NodeData.Data.Clear();$root.NodeRefs.Clear();$root.LocalInplaceResource.Clear();$root.PersistentNodes.Clear()
$root.ExternInplaceResource=[Activator]::CreateInstance($root.GetType().GetProperty('ExternInplaceResource').PropertyType)
if($root.VariantIndices.Count -ne 2 -or $root.VariantIndices[0].ToString() -ne '0' -or $root.VariantIndices[1].ToString() -ne '0'){throw 'Default-empty template changed'}
$sourceRows=[Collections.Generic.List[object]]::new()
$ordinal=0
foreach($row in $selected){
 $node=$nodes[[int]$row.node_index].DeepCopy()
 $data=$placements[[int]$row.data_index].DeepCopy()
 if($node.Chunk.GetType().Name -ne 'worldInstancedDestructibleMeshNode' -or $node.Chunk.Mesh.DepotPath.ToString() -ne $row.mesh){throw 'Construction node source changed'}
 if($node.Chunk.IsDestructible.ToString() -ne 'False' -or $node.Chunk.IsWorkspot.ToString() -ne 'False'){throw 'Unexpected active node behavior'}
 $start=[int]$row.transform_start;$count=[int]$row.transform_count
 if($node.Chunk.CookedInstanceTransforms.StartIndex.ToString() -ne $start.ToString() -or $node.Chunk.CookedInstanceTransforms.NumElements.ToString() -ne $count.ToString()){throw 'Transform slice changed'}
 $newStart=$shared.Chunk.Buffer.Data.Transforms.Count
 for($i=$start;$i -lt ($start+$count);$i++){[void]$shared.Chunk.Buffer.Data.Transforms.Add($allTransforms[$i].DeepCopy())}
 $node.Chunk.CookedInstanceTransforms.SharedDataBuffer=$shared
 $node.Chunk.CookedInstanceTransforms.StartIndex=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]$newStart)
 $node.Chunk.SourcePrefabHash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit([uint64]0)
 $data.Id=[uint64](740000000007000+$ordinal)
 $data.NodeIndex=[WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]$ordinal)
 $data.QuestPrefabRefHash=[WolvenKit.RED4.Types.NodeRef]::op_Implicit('')
 $data.UkHash1=[WolvenKit.RED4.Types.NodeRef]::op_Implicit('')
 [void]$root.Nodes.Add($node);[void]$root.NodeData.Data.Add($data)
 $sourceRows.Add([pscustomobject]@{source_data=[int]$row.data_index;source_node=[int]$row.node_index;new_node=$ordinal;new_id=$data.Id.ToString();mesh=$row.mesh;old_transform_start=$start;new_transform_start=$newStart;transform_count=$count})
 $ordinal++
}
if($shared.Chunk.Buffer.Data.Transforms.Count -ne 18){throw 'Expected only eighteen transforms'}
$depot='towercontinued\misty_viktor_world\construction_r7.streamingsector'
$path=Join-Path $source $depot
Write-Cr2wFile $file $path
$readback=Read-Cr2wFile $path
if($readback.RootChunk.Nodes.Count -ne 6 -or $readback.RootChunk.NodeData.Data.Count -ne 6 -or $readback.EmbeddedFiles.Count -ne 0){throw 'Construction readback scope mismatch'}
if($readback.RootChunk.Nodes[0].Chunk.CookedInstanceTransforms.SharedDataBuffer.Chunk.Buffer.Data.Transforms.Count -ne 18){throw 'Cooked buffer trim did not survive native write'}
Export-Cr2wJson $readback (Join-Path $audit 'r7_construction_sector.json')

# Preserve the actual source descriptor's LOD0/grid/streaming bounds. Only the
# resource and controlled variant are private. No distant LOD copy is selected.
$sourceBlock=Join-Path $WorkspaceRoot ($plan.source_block.Replace('\json\','\raw\') -replace '\.json$','')
$block=Read-Cr2wFile $sourceBlock
$descriptor=$block.RootChunk.Descriptors[[int]$selected[0].source_descriptor_index].DeepCopy()
$block.RootChunk.Descriptors.Clear();$block.EmbeddedFiles.Clear()
$template=Read-Cr2wFile (Join-Path $WorkspaceRoot 'build\MistyViktorRepairR6\source\towercontinued\misty_viktor_world\street.streamingblock')
$variant=$template.RootChunk.Descriptors[0].Variants[0].DeepCopy()
if($variant.VariantId.ToString() -ne '3917072702' -or $variant.RangeIndex.ToString() -ne '1' -or $variant.EnabledByDefault.ToString() -ne 'False'){throw 'Private street variant changed'}
$descriptor.Variants.Clear();[void]$descriptor.Variants.Add($variant)
$descriptor.NumNodeRanges=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]2)
$descriptor.Data=[Activator]::CreateInstance($descriptor.GetType().GetProperty('Data').PropertyType,[object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($depot)))
[void]$block.RootChunk.Descriptors.Add($descriptor)
$blockDepot='towercontinued\misty_viktor_world\construction_r7.streamingblock'
$blockPath=Join-Path $source $blockDepot
Write-Cr2wFile $block $blockPath
Export-Cr2wJson (Read-Cr2wFile $blockPath) (Join-Path $audit 'r7_construction_block.json')
$manifest=[ordered]@{
 status='BUILT_R7_CONSTRUCTION_SOURCE_NOT_INSTALLED_OR_LIVE'
 source_root=$source;resources=@($depot,$blockDepot);block_depot=$blockDepot
 source_sector=$plan.source_sector;source_raw=$plan.source_raw;source_sha256=$plan.source_sha256
 source_descriptor=507;source_lod_level=0;source_ranges=@(3,5)
 sector_sha256=(Get-FileHash -LiteralPath $path).Hash;block_sha256=(Get-FileHash -LiteralPath $blockPath).Hash
 readback_sector_sha256=(Get-FileHash -LiteralPath (Join-Path $audit 'r7_construction_sector.json')).Hash
 readback_block_sha256=(Get-FileHash -LiteralPath (Join-Path $audit 'r7_construction_block.json')).Hash
 nodes=6;placements=6;mesh_instances=18;meshes=5;source_rows=@($sourceRows)
 allowed_changes=@('Node SourcePrefabHash cleared to 0','Cooked transform buffer trimmed to eighteen exact source transforms and start indices rebased','Placement NodeIndex rebased; six private Ids assigned; empty node refs retain no vanilla binding','Sector template uses empty default range0, controlled range1 and no unrelated nodes/embedded files/nodeRefs/persistentNodes/localInplaceResource/externInplaceResource','Descriptor preserves source LOD0/grid/streaming bounds; path and variant metadata replaced with existing private PTFRMV_TowerStreet, id3917072702, range1 default OFF')
 retained=@('All original mesh paths and mesh appearances','Every outer position/orientation/scale, original 18 local transforms','Native mesh physics/filter/navigation/aggregate flags and simulation settings','Source streaming descriptor spatial bounds and level0')
 note='No independent collision node needed: original native instanced mesh node preserves meshMeshParamPhysics in unchanged official mesh resources; no static-only flattening. Runtime visibility/collision and impulse behavior remain unverified.'
 actors=0;lights=0;triggers=0;scene_starts=0;story_fact_writes=0;packed=$false;installed=$false;live_tested=$false
}
[IO.File]::WriteAllText((Join-Path $audit 'r7_construction_manifest.json'),($manifest|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
[pscustomobject]$manifest|Select-Object status,nodes,placements,mesh_instances,sector_sha256,block_sha256|ConvertTo-Json
