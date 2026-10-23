param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$sourceRoot=Join-Path $WorkspaceRoot 'build\MistyViktorDoorsR11\source'
$owner='$/03_night_city/c_watson/little_china/loc_mystic_mistys_ripperdoc_prefabH2DWJJI/#loc_mystic_mistys_ripperdoc_env'
$variantName='PTFRMV_ZetatechShell'
$variantId=[uint32]3917072701
$sectorBase='research\phase2b_p4\variant_sectors\ep1_1_nightcity\raw\base\worlds\03_night_city\_compiled\default\'
$blockBase='research\phase2b_p4\staging_scan\ep1_1_nightcity\raw\base\worlds\03_night_city\_compiled\default\'
$selections=@(
 [ordered]@{name='front';sector=($sectorBase+'exterior_-25_18_0_0.streamingsector');sha256='F362B1A319F4FBBC007BDDA5168933E3FA7BF89D27FB22A6F9262B513886F207';node=3100;datum=3529;block=($blockBase+'blocks\all.streamingblock');descriptor=4833;variant='q307_entities';range=22;appearance='doors_single_neomilitary_n_v2';ref='$/03_night_city/#PTFRMV_ZetatechFrontDoor';private_id=[uint64]750000000011001},
 [ordered]@{name='inner';sector=($sectorBase+'ep1\interior_-49_37_0_0.streamingsector');sha256='06B2460FC17E699716EEAC3F814CAA9174369E1C7AAAD557103495423CFA84EB';node=195;datum=216;block=($blockBase+'ep1\blocks\all.streamingblock');descriptor=1453;variant='q307_zetatech';range=0;appearance='doors_single_entropy_a';ref='$/03_night_city/#PTFRMV_ZetatechInnerDoor';private_id=[uint64]750000000011002}
)
function ReadWorld([string]$path){
 $stream=[IO.File]::OpenRead($path)
 try{
  $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
  $reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])})
  $file=$null;if($reader.ReadFile([ref]$file,$true).ToString() -ne 'NoError'){throw "World parse failure: $path"};return $file
 }finally{$stream.Dispose()}
}
function JsonObject($file){
 return ([WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize([WolvenKit.Common.Conversion.RedFileDto]::new($file,$false),[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())|ConvertFrom-Json -Depth 100)
}
function FindDoorPS($value){
 if($null -eq $value){return}
 if($value -is [System.Collections.IList]){foreach($child in $value){FindDoorPS $child};return}
 if($value -is [pscustomobject]){
  if($value.PSObject.Properties.Name -contains '$type' -and $value.'$type' -eq 'DoorControllerPS'){return $value}
  foreach($prop in $value.PSObject.Properties){FindDoorPS $prop.Value}
 }
}
# Read the shared template into memory. The two authored nodes have no instance
# override: their ordinary interaction/closed state must come from this template.
$templateDepot='base\gameplay\devices\doors\final\single_door.ent'
$templateArchive='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\content\basegame_3_nightcity.archive'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$arc=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($templateArchive,$hs,[ref]$arc).ToString() -ne 'NoError'){throw 'Cannot read official door template archive'}
$entry=@($arc.Files.Values|Where-Object {$_.Name -eq $templateDepot});if($entry.Count -ne 1){throw 'Door template absent or ambiguous'}
$memory=[IO.MemoryStream]::new()
try{
 $entry[0].Extract($memory);$templateSha=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray()));$memory.Position=0
 $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($memory)
 $reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])})
 $template=$null;if($reader.ReadFile([ref]$template,$true).ToString() -ne 'NoError'){throw 'Door template decoding failed'}
 $ps=@(FindDoorPS (JsonObject $template));if($ps.Count -ne 1){throw 'Door template controller ambiguity'}
 $ps=$ps[0]
 if($ps.deviceState -ne 'ON' -or $ps.isInteractive -ne 1 -or $ps.isOpened -ne 0 -or $ps.isLocked -ne 0 -or $ps.isSealed -ne 0 -or $ps.doorProperties.doorType -ne 'INTERACTIVE' -or $ps.doorProperties.initialDoorState -ne 'CLOSED' -or $ps.doorProperties.automaticallyClosesItself -ne 1){throw 'Ordinary closed interactive door template changed'}
}finally{$memory.Dispose()}

$block=ReadWorld (Join-Path $WorkspaceRoot ($blockBase+'blocks\all.streamingblock'))
$block.EmbeddedFiles.Clear();$block.RootChunk.Descriptors.Clear()
$rows=[Collections.Generic.List[object]]::new();$resources=[Collections.Generic.List[string]]::new()
foreach($selection in $selections){
 $srcPath=Join-Path $WorkspaceRoot $selection.sector
 if((Get-FileHash -LiteralPath $srcPath).Hash -ne $selection.sha256){throw 'Original door sector hash changed'}
 $original=ReadWorld $srcPath;$srcRoot=$original.RootChunk
 $node=$srcRoot.Nodes[$selection.node].DeepCopy();$datum=$srcRoot.NodeData.Data[$selection.datum].DeepCopy()
 if($datum.NodeIndex.ToString() -ne $selection.node.ToString() -or $node.Chunk.GetType().Name -ne 'worldEntityNode' -or $node.Chunk.EntityTemplate.DepotPath.ToString() -ne $templateDepot -or $node.Chunk.AppearanceName.ToString() -ne $selection.appearance -or $null -ne $node.Chunk.InstanceData){throw 'Exact door node payload changed'}
 $sourceRef=$datum.QuestPrefabRefHash.ToString()
 $node.Chunk.DebugName=[WolvenKit.RED4.Types.CName]::op_Implicit('PTFRMV_Zetatech_'+$selection.name+'_r11')
 $node.Chunk.SourcePrefabHash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit([uint64]0)
 $datum.Id=$selection.private_id;$datum.NodeIndex=[WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]0)
 $datum.QuestPrefabRefHash=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($selection.ref)
 $datum.UkHash1=[WolvenKit.RED4.Types.NodeRef]::op_Implicit('')
 $file=ReadWorld (Join-Path $WorkspaceRoot 'build\MistyViktorVariantsR5\source\towercontinued\misty_viktor_world\street_0.streamingsector')
 $file.EmbeddedFiles.Clear();$root=$file.RootChunk
 $root.Nodes.Clear();$root.NodeData.Data.Clear();$root.NodeRefs.Clear();$root.LocalInplaceResource.Clear();$root.PersistentNodes.Clear();$root.VariantNodes.Clear()
 $root.ExternInplaceResource=[Activator]::CreateInstance($root.GetType().GetProperty('ExternInplaceResource').PropertyType)
 $root.PersisentNodeIndex=[WolvenKit.RED4.Types.CInt32]::op_Implicit([int32]-1)
 $root.Level=$srcRoot.Level;$root.Category=$srcRoot.Category
 $root.VariantIndices.Clear();[void]$root.VariantIndices.Add([WolvenKit.RED4.Types.CInt32]::op_Implicit(0));[void]$root.VariantIndices.Add([WolvenKit.RED4.Types.CInt32]::op_Implicit(0))
 [void]$root.Nodes.Add($node);[void]$root.NodeData.Data.Add($datum);[void]$root.NodeRefs.Add([WolvenKit.RED4.Types.NodeRef]::op_Implicit($selection.ref))
 $depot='towercontinued\misty_viktor_world\doors_r11_'+$selection.name+'.streamingsector'
 Write-Cr2wFile $file (Join-Path $sourceRoot $depot);$readback=ReadWorld (Join-Path $sourceRoot $depot)
 Export-Cr2wJson $readback (Join-Path $audit ('r11_doors_'+$selection.name+'_sector.json'))
 $before=(JsonObject $original).Data.RootChunk;$after=(JsonObject $readback).Data.RootChunk
 if($after.nodes.Count -ne 1 -or $after.nodeData.Data.Count -ne 1 -or $after.nodeRefs.Count -ne 1 -or $after.nodeRefs[0].'$value' -ne $selection.ref -or @($after.persistentNodes|Where-Object {$null -ne $_}).Count -ne 0 -or $after.localInplaceResource.Count -ne 0 -or $after.variantIndices.Count -ne 2 -or $after.variantIndices[0] -ne 0 -or $after.variantIndices[1] -ne 0){throw 'Door sector scope/readiness alias mismatch'}
 $actual=$after.nodes[0].Data;$expected=$before.nodes[$selection.node].Data
 $actual.debugName=$expected.debugName;$actual.sourcePrefabHash=$expected.sourcePrefabHash
 if(($actual|ConvertTo-Json -Depth 100 -Compress) -cne ($expected|ConvertTo-Json -Depth 100 -Compress)){throw 'Door node payload changed beyond private ownership'}
 $actual=$after.nodeData.Data[0];$expected=$before.nodeData.Data[$selection.datum]
 foreach($key in 'Id','NodeIndex','QuestPrefabRefHash','UkHash1'){$actual.$key=$expected.$key}
 if(($actual|ConvertTo-Json -Depth 100 -Compress) -cne ($expected|ConvertTo-Json -Depth 100 -Compress)){throw 'Door transform/placement changed beyond private ownership'}
 $sourceBlock=ReadWorld (Join-Path $WorkspaceRoot $selection.block)
 $descriptor=$sourceBlock.RootChunk.Descriptors[$selection.descriptor].DeepCopy()
 $variants=@($descriptor.Variants|Where-Object {$_.Name.ToString() -eq $selection.variant -and $_.RangeIndex.ToString() -eq $selection.range.ToString()})
 if($variants.Count -ne 1){throw 'Original door range descriptor changed'}
 $variant=$variants[0].DeepCopy();$variant.Name=[WolvenKit.RED4.Types.CName]::op_Implicit($variantName);$variant.NodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($owner)
 $variant.EnabledByDefault=$false;$variant.RangeIndex=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]1);$variant.ParentVariantID=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]0);$variant.VariantId=[WolvenKit.RED4.Types.CUInt32]::op_Implicit($variantId)
 $descriptor.Variants.Clear();[void]$descriptor.Variants.Add($variant);$descriptor.NumNodeRanges=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]2)
 $descriptor.Data=[Activator]::CreateInstance($descriptor.GetType().GetProperty('Data').PropertyType,[object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($depot)))
 [void]$block.RootChunk.Descriptors.Add($descriptor);$resources.Add($depot)
 $rows.Add([ordered]@{name=$selection.name;source=$selection.sector;source_sha256=$selection.sha256;source_node=$selection.node;source_datum=$selection.datum;source_ref=$sourceRef;source_block=$selection.block;source_descriptor=$selection.descriptor;source_variant=$selection.variant;source_range=$selection.range;depot=$depot;private_ref=$selection.ref;private_id=$selection.private_id.ToString();appearance=$selection.appearance;category=$root.Category.ToString();position=$before.nodeData.Data[$selection.datum].Position;sha256=(Get-FileHash (Join-Path $sourceRoot $depot)).Hash;exact_payload_transform_readback_pass=$true})
}
$blockDepot='towercontinued\misty_viktor_world\doors_r11.streamingblock'
Write-Cr2wFile $block (Join-Path $sourceRoot $blockDepot);$readback=ReadWorld (Join-Path $sourceRoot $blockDepot)
Export-Cr2wJson $readback (Join-Path $audit 'r11_doors_block.json');$resources.Add($blockDepot)
if($readback.RootChunk.Descriptors.Count -ne 2){throw 'Door block scope changed'}
foreach($descriptor in $readback.RootChunk.Descriptors){if($descriptor.Variants.Count -ne 1 -or $descriptor.Variants[0].Name.ToString() -ne $variantName -or $descriptor.Variants[0].NodeRef.ToString() -ne $owner -or $descriptor.Variants[0].EnabledByDefault.ToString() -ne 'False' -or $descriptor.Variants[0].RangeIndex.ToString() -ne '1'){throw 'Private shell door range changed'}}
if(@(Get-ChildItem -LiteralPath $sourceRoot -File -Recurse).Count -ne 3){throw 'Unexpected door payload file'}
$manifest=[ordered]@{
 status='BUILT_R11_TWO_PRIVATE_DOORS_NOT_PACKED_INSTALLED_OR_LIVE';source_root=$sourceRoot;resources=@($resources);block_depot=$blockDepot;block_sha256=(Get-FileHash (Join-Path $sourceRoot $blockDepot)).Hash
 template=@{depot=$templateDepot;archive=$templateArchive;sha256=$templateSha;device_state=$ps.deviceState;interactive=$ps.isInteractive;opened=$ps.isOpened;locked=$ps.isLocked;sealed=$ps.isSealed;door_properties=$ps.doorProperties};selections=@($rows)
 variant_owner=$owner;variant_name=$variantName;variant_id=$variantId;controlled_range=1;default_range_count=0;door_entities=2;scene_cast=0;original_world_overrides=0;original_templates_changed=0;phase_changes=0
 static_geometry_preserved=$true;entity_proxies_cloned=0;exact_payload_transform_readback_pass=$true;fresh_aliases_and_identities=$true
 cause='q307 cleanup turns off original front q307_entities and inner q307_zetatech owners; prior private shell/street omitted worldEntityNode doors'
 visual_audit='Source static frame/surround meshes coexist with functional vanilla entities: retain shop_u_door, door_frame_single_l, backwall_c_door_double_a_gf_l400 and inner door_single_sliding_a_frame_a. No original door entity or entity proxy was copied into the private shell/street.'
 packed=$false;installed=$false;live_tested=$false
}
[IO.File]::WriteAllText((Join-Path $audit 'r11_doors_manifest.json'),($manifest|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
[pscustomobject]$manifest|Select-Object status,source_root,resources,block_sha256,door_entities,exact_payload_transform_readback_pass|ConvertTo-Json -Depth 5
