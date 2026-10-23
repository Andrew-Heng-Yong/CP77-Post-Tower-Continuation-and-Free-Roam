param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$sourceRoot=Join-Path $WorkspaceRoot 'build\MistyViktorLightPOCWorld\source'
$sourceDepot='base\worlds\03_night_city\_compiled\default\exterior_-25_18_0_0.streamingsector'
$sourceHash='F362B1A319F4FBBC007BDDA5168933E3FA7BF89D27FB22A6F9262B513886F207'
$privateRef='$/03_night_city/#PTFRMV_LightPOC01'
$variantOwner='$/03_night_city/c_watson/little_china/wlc_02/#wlc_02_b_env'
$variantName='PTFRMV_LightPOC'
$variantId=[uint32]3980092801
$privateId=[uint64]750000000008001
$sectorDepot='towercontinued\misty_viktor_light_poc\light_poc.streamingsector'
$blockDepot='towercontinued\misty_viktor_light_poc\light_poc.streamingblock'
# User's former wall-gap standing position; wall concern was subsequently withdrawn.
# Parent approved this isolated test location, not a teleport/support guarantee.
$feetPosition=@(-1570.2421875,1210.5838623,16.9989319)
$lampPosition=@(-1570.2421875,1210.5838623,17.5439548)

function ReadWorld([string]$path){
 $stream=[IO.File]::OpenRead($path)
 try{
  $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
  $handler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])}
  $reader.add_ParsingError($handler);$file=$null
  if($reader.ReadFile([ref]$file,$true).ToString() -ne 'NoError'){throw "World parse failure: $path"}
  return $file
 }finally{$stream.Dispose()}
}

# Extract only the exact current official source into memory. No game writes.
$provenance=@(Get-Content (Join-Path $audit 'r7_lighting_sources.json') -Raw|ConvertFrom-Json|Where-Object {$_.Resource -eq $sourceDepot})
if($provenance.Count -ne 1 -or $provenance[0].Sha256 -ne $sourceHash){throw 'Lamp source provenance changed'}
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$archive=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($provenance[0].Archive,$hash,[ref]$archive).ToString() -ne 'NoError'){throw 'Cannot read official light archive'}
$entry=@($archive.Files.Values|Where-Object {$_.Name -eq $sourceDepot})
if($entry.Count -ne 1){throw 'Exact source sector absent or ambiguous'}
$memory=[IO.MemoryStream]::new()
try{
 $entry[0].Extract($memory)
 if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray())) -ne $sourceHash){throw 'Official sector hash changed'}
 $memory.Position=0
 $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($memory)
 $handler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])}
 $reader.add_ParsingError($handler);$original=$null
 if($reader.ReadFile([ref]$original,$true).ToString() -ne 'NoError'){throw 'Original lamp sector decode failed'}
}finally{$memory.Dispose()}
if($original.RootChunk.Nodes.Count -ne 3941 -or $original.RootChunk.NodeData.Data.Count -ne 4534){throw 'Original source counts changed'}
$node=$original.RootChunk.Nodes[3368].DeepCopy()
$placement=$original.RootChunk.NodeData.Data[3907].DeepCopy()
if($placement.NodeIndex.ToString() -ne '3368' -or $node.Chunk.GetType().Name -ne 'worldStaticLightNode' -or $node.Chunk.DebugName.ToString() -ne '{L_RedStreet_Exhibition_}_011'){throw 'Exact source lamp changed'}
if($node.Chunk.Type.ToString() -ne 'LT_Point' -or $node.Chunk.Radius.ToString() -ne '3' -or $node.Chunk.Intensity.ToString() -ne '25'){throw 'Exact source lighting properties changed'}
if($placement.QuestPrefabRefHash.ToString() -notin @('0','') -or $placement.UkHash1.ToString() -notin @('0','')){throw 'Source target is no longer unnamed'}

# Registration matches the positive vanilla static-light precedent: a placement
# QuestPrefabRefHash plus the same full alias in sector.nodeRefs; no node alias field.
$proof=Get-Content (Join-Path $audit 'r7_showworld_static_light_proof.json') -Raw|ConvertFrom-Json -Depth 100
if($proof.status -ne 'POSITIVE_VANILLA_STATIC_LIGHT_SHOWWORLD_PRECEDENT' -or $proof.target.node.'$type' -ne 'worldStaticLightNode' -or $proof.target.data_index -ne 2359 -or $proof.registration_metadata.sector_nodeRefs_indices[0] -ne 26){throw 'Named Afterlife static-light precedent changed'}
if((Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $proof.source_json)).Hash -ne $proof.source_json_sha256){throw 'Afterlife source export hash changed'}

$node.Chunk.DebugName=[WolvenKit.RED4.Types.CName]::op_Implicit('PTFRMV_LightPOC01')
$node.Chunk.SourcePrefabHash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit([uint64]0)
$placement.Id=$privateId # File handle slot only; NOT the runtime targeting identity.
$placement.NodeIndex=[WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]0)
$placement.QuestPrefabRefHash=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($privateRef)
$placement.UkHash1=[WolvenKit.RED4.Types.NodeRef]::op_Implicit('')
$originalPosition=@('X','Y','Z'|ForEach-Object {[double]$placement.Position.$_.ToString()})
$translation=for($i=0;$i -lt 3;$i++){$lampPosition[$i]-$originalPosition[$i]}
for($i=0;$i -lt 3;$i++){
 $axis=@('X','Y','Z')[$i]
 $placement.Position.$axis=[WolvenKit.RED4.Types.CFloat]::op_Implicit([single]$lampPosition[$i])
 # Preserve original relative primary/secondary streaming reference positions.
 foreach($point in @($placement.Pivot,$placement.Bounds.Min,$placement.Bounds.Max)){
  $point.$axis=[WolvenKit.RED4.Types.CFloat]::op_Implicit([single]([double]$point.$axis.ToString()+$translation[$i]))
 }
}

# Validated default-empty/private-range template; remove every unrelated payload.
$templateSector=Join-Path $WorkspaceRoot 'build\MistyViktorRepairR6\source\towercontinued\misty_viktor_world\street_0.streamingsector'
$file=ReadWorld $templateSector;$root=$file.RootChunk
$file.EmbeddedFiles.Clear()
$root.Nodes.Clear();$root.NodeData.Data.Clear();$root.NodeRefs.Clear()
$root.LocalInplaceResource.Clear();$root.PersistentNodes.Clear();$root.VariantNodes.Clear()
$root.ExternInplaceResource=[Activator]::CreateInstance($root.GetType().GetProperty('ExternInplaceResource').PropertyType)
$root.VariantIndices.Clear()
[void]$root.VariantIndices.Add([WolvenKit.RED4.Types.CInt32]::op_Implicit(0))
[void]$root.VariantIndices.Add([WolvenKit.RED4.Types.CInt32]::op_Implicit(0))
$root.PersisentNodeIndex=[WolvenKit.RED4.Types.CInt32]::op_Implicit(0)
[void]$root.Nodes.Add($node);[void]$root.NodeData.Data.Add($placement)
[void]$root.NodeRefs.Add([WolvenKit.RED4.Types.NodeRef]::op_Implicit($privateRef))
if($root.Level.ToString() -ne '0' -or $root.Category.ToString() -ne 'Exterior'){throw 'Template not exterior LOD0'}
$sectorPath=Join-Path $sourceRoot $sectorDepot
Write-Cr2wFile $file $sectorPath
$sectorReadback=ReadWorld $sectorPath
Export-Cr2wJson $sectorReadback (Join-Path $audit 'light_poc_world_sector.json')

# Retain the proven local descriptor's spatial/grid metadata; only private path
# and its distinct, default-OFF variant identity change.
$templateBlock=Join-Path $WorkspaceRoot 'build\MistyViktorRepairR6\source\towercontinued\misty_viktor_world\street.streamingblock'
$block=ReadWorld $templateBlock
$descriptor=$block.RootChunk.Descriptors[0].DeepCopy()
$block.RootChunk.Descriptors.Clear();$block.EmbeddedFiles.Clear()
if($descriptor.Variants.Count -ne 1){throw 'Template descriptor must have one variant'}
$variant=$descriptor.Variants[0]
$variant.Name=[WolvenKit.RED4.Types.CName]::op_Implicit($variantName)
$variant.NodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($variantOwner)
$variant.VariantId=[WolvenKit.RED4.Types.CUInt32]::op_Implicit($variantId)
$variant.ParentVariantID=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]0)
$variant.RangeIndex=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]1)
$variant.EnabledByDefault=$false
$descriptor.NumNodeRanges=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]2)
$descriptor.Data=[Activator]::CreateInstance($descriptor.GetType().GetProperty('Data').PropertyType,[object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($sectorDepot)))
for($i=0;$i -lt 3;$i++){
 $axis=@('X','Y','Z')[$i]
 if($lampPosition[$i] -lt [double]$descriptor.StreamingBox.Min.$axis.ToString() -or $lampPosition[$i] -gt [double]$descriptor.StreamingBox.Max.$axis.ToString()){throw 'Approved lamp outside existing descriptor bounds'}
}
[void]$block.RootChunk.Descriptors.Add($descriptor)
$blockPath=Join-Path $sourceRoot $blockDepot
Write-Cr2wFile $block $blockPath
$blockReadback=ReadWorld $blockPath
Export-Cr2wJson $blockReadback (Join-Path $audit 'light_poc_world_block.json')

# Audit literal leaf changes against the untouched original JSON source.
function CompareLeaves($before,$after,[string]$path,$changes){
 if($before -is [pscustomobject] -and $after -is [pscustomobject]){
  $keys=@(@($before.PSObject.Properties.Name)+@($after.PSObject.Properties.Name)|Sort-Object -Unique)
  foreach($key in $keys){
   $bp=$before.PSObject.Properties[$key];$ap=$after.PSObject.Properties[$key]
   if($null -eq $bp -or $null -eq $ap){throw "Unexpected property schema change at $path.$key"}
   CompareLeaves $bp.Value $ap.Value "$path.$key" $changes
  }
 }elseif($before -is [array] -and $after -is [array]){
  if($before.Count -ne $after.Count){throw "Unexpected array size change at $path"}
  for($i=0;$i -lt $before.Count;$i++){CompareLeaves $before[$i] $after[$i] "$path[$i]" $changes}
 }elseif(($before|ConvertTo-Json -Compress -Depth 100) -cne ($after|ConvertTo-Json -Compress -Depth 100)){
  $changes.Add([pscustomobject]@{path=$path;before=$before;after=$after})
 }
}
$sourceJson=Get-Content $provenance[0].Json -Raw|ConvertFrom-Json -Depth 100
$sectorJson=Get-Content (Join-Path $audit 'light_poc_world_sector.json') -Raw|ConvertFrom-Json -Depth 100
$output=$sectorJson.Data.RootChunk
$nodeChanges=[Collections.Generic.List[object]]::new();$placementChanges=[Collections.Generic.List[object]]::new()
CompareLeaves $sourceJson.Data.RootChunk.nodes[3368].Data $output.nodes[0].Data '$' $nodeChanges
CompareLeaves $sourceJson.Data.RootChunk.nodeData.Data[3907] $output.nodeData.Data[0] '$' $placementChanges
$nodeAllowed=@('$.debugName.$value','$.sourcePrefabHash')
$placementAllowed=@('$.Id','$.NodeIndex','$.QuestPrefabRefHash.$storage','$.QuestPrefabRefHash.$value')
foreach($group in @('Position','Pivot','Bounds.Min','Bounds.Max')){foreach($axis in @('X','Y','Z')){$placementAllowed+="`$.$group.$axis"}}
foreach($change in $nodeChanges){if($change.path -notin $nodeAllowed){throw "Unapproved light-property delta: $($change.path)"}}
foreach($change in $placementChanges){if($change.path -notin $placementAllowed){throw "Unapproved placement delta: $($change.path)"}}
if($nodeChanges.Count -ne 2){throw 'Expected exactly two non-light node metadata changes'}
if($output.nodes.Count -ne 1 -or $output.nodeData.Data.Count -ne 1 -or $output.nodeRefs.Count -ne 1 -or $output.nodeRefs[0].'$value' -ne $privateRef){throw 'Single light readback scope failed'}
if($output.variantIndices.Count -ne 2 -or $output.variantIndices[0] -ne 0 -or $output.variantIndices[1] -ne 0 -or $output.persistentNodes.Count -ne 0 -or $output.localInplaceResource.Count -ne 0 -or $sectorJson.Data.EmbeddedFiles.Count -ne 0){throw 'Default-empty/no auxiliary payload readback failed'}
if($blockReadback.RootChunk.Descriptors.Count -ne 1 -or $blockReadback.RootChunk.Descriptors[0].Variants[0].Name.ToString() -ne $variantName -or $blockReadback.RootChunk.Descriptors[0].Variants[0].EnabledByDefault.ToString() -ne 'False'){throw 'Private default-off block readback failed'}
if(@(Get-ChildItem -LiteralPath $sourceRoot -File -Recurse).Count -ne 2){throw 'Asset source root contains unexpected files'}

$manifest=[ordered]@{
 status='BUILT_SINGLE_LIGHT_POC_SOURCE_ONLY_NOT_PACKED_INSTALLED_OR_LIVE'
 source_root=$sourceRoot;resources=@($sectorDepot,$blockDepot);block_depot=$blockDepot
 source_archive=$provenance[0].Archive;source_depot=$sourceDepot;source_sha256=$sourceHash
 source_data_index=3907;source_node_index=3368;source_node_type='worldStaticLightNode';source_light_type='LT_Point'
 private_ref=$privateRef;private_file_handle_slot=$privateId;file_handle_is_not_global_id=$true
 variant_name=$variantName;variant_owner=$variantOwner;variant_id=$variantId;variant_parent_id=0
 ranges=@(@{index=0;start=0;count=0},@{index=1;start=0;count=1});variant_enabled_by_default=$false
 nodes=1;placements=1;static_lights=1;entities=0;meshes=0;collisions=0;triggers=0;scene_starts=0
 known_user_feet_position=$feetPosition;approved_lamp_position=$lampPosition;original_lamp_position=$originalPosition
 translation=$translation;actual_float32_position=@($output.nodeData.Data[0].Position.X,$output.nodeData.Data[0].Position.Y,$output.nodeData.Data[0].Position.Z)
 site_note='Parent-approved isolated pavement test, approximately42.4m from original3907; prior user standing location is not a teleport/support guarantee. No collision or geometry added.'
 node_changes=@($nodeChanges);placement_changes=@($placementChanges)
 registration_precedent='mq016_02_afterlife.scene790/792; placement2359/node1862, matching full placement NodeRef and sector.nodeRefs26; no original scene copied or started'
 afterlife_proof_source_sha256=$proof.source_raw_sha256
 retained='All original light properties including LT_Point, color255/249/43, intensity25, EV1.5, radius3, orientation, scale, lighting channels and native flags; all placement streaming distances/flags retained.'
 translated_fields=@('Position.xyz','Pivot.xyz','Bounds.Min.xyz','Bounds.Max.xyz')
 sector_auxiliary_payloads=0;sector_node_refs=@($privateRef);persistent_node_index=0
 descriptor_retained='Existing tested local Exterior/LOD0 descriptor grid/streamingBox; only path and distinct private variant metadata differ.'
 sector_template=$templateSector;block_template=$templateBlock
 sector_sha256=(Get-FileHash -LiteralPath $sectorPath).Hash;block_sha256=(Get-FileHash -LiteralPath $blockPath).Hash
 original_resource_overrides=0;gameplay_commands_executed=0;packed=$false;installed=$false;live_tested=$false
}
[IO.File]::WriteAllText((Join-Path $audit 'light_poc_world_manifest.json'),($manifest|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
[pscustomobject]$manifest|Select-Object status,private_ref,variant_name,variant_owner,variant_id,static_lights,sector_sha256,block_sha256|ConvertTo-Json
