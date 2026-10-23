param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$out=Join-Path $WorkspaceRoot 'build\MistyViktorTrucksR7\source'
$sourceRel='research\phase2b_p4\variant_sectors\ep1_1_nightcity\raw\base\worlds\03_night_city\_compiled\default\ep1\exterior_-13_9_0_1.streamingsector'
$sourcePath=Join-Path $WorkspaceRoot $sourceRel
$expected='CAA6C704093CB6905C191A464F7885683872033828386807EC9AEC0BDCB03A15'
if((Get-FileHash -LiteralPath $sourcePath).Hash -ne $expected){throw 'Original truck sector provenance changed'}
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
$original=ReadWorld $sourcePath
$file=ReadWorld (Join-Path $WorkspaceRoot 'build\MistyViktorVariantsR5\source\towercontinued\misty_viktor_world\street_0.streamingsector')
$file.EmbeddedFiles.Clear()
$root=$file.RootChunk
$root.Nodes.Clear();$root.NodeData.Data.Clear();$root.NodeRefs.Clear();$root.LocalInplaceResource.Clear();$root.PersistentNodes.Clear()
$root.ExternInplaceResource=[Activator]::CreateInstance($root.GetType().GetProperty('ExternInplaceResource').PropertyType)
$root.PersisentNodeIndex=[WolvenKit.RED4.Types.CInt32]::op_Implicit([int32]-1)
$root.Level=$original.RootChunk.Level
$root.Category=$original.RootChunk.Category
if($root.VariantIndices.Count -ne 2 -or $root.VariantIndices[0].ToString() -ne '0' -or $root.VariantIndices[1].ToString() -ne '0'){throw 'Controlled template ranges changed'}
$rows=[Collections.Generic.List[object]]::new()
for($i=0;$i -lt 2;$i++){
 $ni=56+$i;$di=66+$i
 $node=$original.RootChunk.Nodes[$ni].DeepCopy();$datum=$original.RootChunk.NodeData.Data[$di].DeepCopy()
 if($node.Chunk.GetType().Name -ne 'worldPopulationSpawnerNode' -or $datum.NodeIndex.ToString() -ne $ni.ToString()){throw 'Exact truck node selection drifted'}
 $recordCast=[WolvenKit.RED4.Types.TweakDBID].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint64]}
 if([uint64]$recordCast.Invoke($null,[object[]]@($node.Chunk.ObjectRecordId.PSObject.BaseObject)) -ne [uint64]188555135153){throw 'Original truck record changed'}
 $privateName='PTFRMV_NCPDTruck'+($i+1).ToString('00');$privateRef='$/03_night_city/#'+$privateName
 $node.Chunk.DebugName=[WolvenKit.RED4.Types.CName]::op_Implicit($privateName)
 $node.Chunk.SourcePrefabHash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit([uint64]0)
 $datum.Id=[uint64](750000000007066+$i)
 $datum.NodeIndex=[WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]$i)
 $datum.QuestPrefabRefHash=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($privateRef)
 $datum.UkHash1=[WolvenKit.RED4.Types.NodeRef]::op_Implicit('')
 [void]$root.Nodes.Add($node);[void]$root.NodeData.Data.Add($datum)
 [void]$root.NodeRefs.Add([WolvenKit.RED4.Types.NodeRef]::op_Implicit($privateRef))
 $rows.Add([ordered]@{source_node=$ni;source_datum=$di;private_ref=$privateRef;private_id=$datum.Id.ToString()})
}
$depot='towercontinued\misty_viktor_world\trucks_alley_r7.streamingsector'
Write-Cr2wFile $file (Join-Path $out $depot)
$readback=ReadWorld (Join-Path $out $depot)
Export-Cr2wJson $readback (Join-Path $audit 'r7_trucks_sector.json')
$blockRel='research\phase2b_p4\staging_scan\ep1_1_nightcity\raw\base\worlds\03_night_city\_compiled\default\ep1\blocks\all.streamingblock'
$block=ReadWorld (Join-Path $WorkspaceRoot $blockRel)
$descriptor=$block.RootChunk.Descriptors[700].DeepCopy()
$variants=@($descriptor.Variants|Where-Object {$_.Name.ToString() -eq 'q307_misty_alley' -and $_.RangeIndex.ToString() -eq '1'})
if($variants.Count -ne 1){throw 'Original truck variant scope changed'}
$variant=$variants[0].DeepCopy()
$variant.Name=[WolvenKit.RED4.Types.CName]::op_Implicit('PTFRMV_TowerStreet')
$variant.VariantId=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]3917072702)
$variant.RangeIndex=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]1)
$variant.EnabledByDefault=$false
$variant.ParentVariantID=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]0)
$descriptor.Variants.Clear();[void]$descriptor.Variants.Add($variant)
$descriptor.NumNodeRanges=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]2)
$descriptor.Data=[Activator]::CreateInstance($descriptor.GetType().GetProperty('Data').PropertyType,[object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($depot)))
$block.EmbeddedFiles.Clear();$block.RootChunk.Descriptors.Clear();[void]$block.RootChunk.Descriptors.Add($descriptor)
$blockDepot='towercontinued\misty_viktor_world\trucks_alley_r7.streamingblock'
Write-Cr2wFile $block (Join-Path $out $blockDepot)
$blockReadback=ReadWorld (Join-Path $out $blockDepot)
Export-Cr2wJson $blockReadback (Join-Path $audit 'r7_trucks_block.json')

# Roundtrip scope checks compare the full original node/placement except private ownership fields.
Export-Cr2wJson $original (Join-Path $audit 'r7_trucks_source_sector.json')
$originalJson=Get-Content -Raw (Join-Path $audit 'r7_trucks_source_sector.json')|ConvertFrom-Json -Depth 100
$actual=Get-Content -Raw (Join-Path $audit 'r7_trucks_sector.json')|ConvertFrom-Json -Depth 100
$actualRoot=$actual.Data.RootChunk;$sourceRoot=$originalJson.Data.RootChunk
if($actualRoot.nodes.Count -ne 2 -or $actualRoot.nodeData.Data.Count -ne 2 -or $actualRoot.nodeRefs.Count -ne 2){throw 'Truck output scope mismatch'}
for($i=0;$i -lt 2;$i++){
 $node=$actualRoot.nodes[$i].Data;$reference=$sourceRoot.nodes[56+$i].Data
 $node.debugName=$reference.debugName;$node.sourcePrefabHash=$reference.sourcePrefabHash
 if(($node|ConvertTo-Json -Depth 100 -Compress) -ne ($reference|ConvertTo-Json -Depth 100 -Compress)){throw 'Unauthorized truck node payload change'}
 $datum=$actualRoot.nodeData.Data[$i];$reference=$sourceRoot.nodeData.Data[66+$i]
 foreach($field in 'Id','NodeIndex','QuestPrefabRefHash','UkHash1'){$datum.$field=$reference.$field}
 if(($datum|ConvertTo-Json -Depth 100 -Compress) -ne ($reference|ConvertTo-Json -Depth 100 -Compress)){throw 'Unauthorized truck placement change'}
}
$manifest=[ordered]@{
 status='BUILT_R7_TRUCK_SOURCE_NOT_INSTALLED_OR_LIVE';source_root=$out
 source=$sourceRel;source_sha256=$expected;source_block=$blockRel;source_block_sha256=(Get-FileHash (Join-Path $WorkspaceRoot $blockRel)).Hash;source_descriptor=700
 source_variant='q307_misty_alley';source_range_index=1;source_range_start=1;source_range_end_exclusive=68
 nodes=2;placements=2;default_range_node_count=0;controlled_range_index=1;variant_id=3917072702;variant_name='PTFRMV_TowerStreet';variant_owner='$/03_night_city/c_watson/little_china/wlc_02/#wlc_02_b_env'
 selections=@($rows);record='Vehicle.v_utility4_militech_behemoth_police';template='ep1\vehicles\utility\v_utilty4_militech_behemoth_police_01.ent'
 resources=@($depot,$blockDepot);block_depot=$blockDepot
 sha256=(Get-FileHash (Join-Path $out $depot)).Hash;sector_sha256=(Get-FileHash (Join-Path $out $depot)).Hash;block_sha256=(Get-FileHash (Join-Path $out $blockDepot)).Hash
 exact_node_placement_readback_pass=$true;retained='All original population settings, record, appearances, full transform, bounds, streaming distances; no template or record edits'
 changed='Only debugName, sourcePrefabHash=0, unique IDs, private NodeRefs, empty UkHash1, compact NodeIndex; original descriptor retargeted to existing private street variant'
 explicit_npc_community_scene_commands=0;story_fact_writes=0;private_phase_changes=0;record_mutations=0;global_ai_changes=0
 classification='Full standard vehicle objects, NOT inert mesh props. No explicit crew or drive commands in source spawners; record supports random passengers and native vehicle behavior.'
 live_pending=@('Exactly two correct parked trucks','No unexpected crew or movement','No duplication on leave/return','Controlled Stop removes owned trucks','Cold load after approved save')
 packed=$false;installed=$false;live_tested=$false
}
[IO.File]::WriteAllText((Join-Path $audit 'r7_trucks_manifest.json'),($manifest|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
$manifest|ConvertTo-Json -Depth 6
