param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$out=Join-Path $WorkspaceRoot 'build\MistyViktorStreetR11\source'
$registryRel='research\phase2b_p4\staging_scan\ep1_1_nightcity\raw\base\worlds\03_night_city\_compiled\default\always_loaded_1.streamingsector'
$spotsRel='research\misty_viktor_world\r6_wall_nav_sources\ep1_1_nightcity\raw\base\worlds\03_night_city\_compiled\default\ep1\quest_bb3937b6e34a251c.streamingsector'
$registryHash='48997B5E57F019C979AFCE29AAEAC147809F1C9F8C88C9B305F58EF1DB02D824'
$spotsHash='47A17525EF23E21E9E1B35CC97F207A6AABDE7D605EE933182A193538C417952'
$spawner='$/03_night_city/#PTFRMV_StreetCommunity'
$owner='$/03_night_city/c_watson/little_china/loc_mystic_mistys_ripperdoc_prefabH2DWJJI/#loc_mystic_mistys_ripperdoc_env'
$cast=[WolvenKit.RED4.Types.NodeRef].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint64]}
function NodeHash([string]$ref){$n=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref);return [uint64]$script:cast.Invoke($null,[object[]]@($n.PSObject.BaseObject))}
function ReadWorld([string]$path){
 $s=[IO.File]::OpenRead($path)
 try{$rd=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($s);$rd.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])});$f=$null;if($rd.ReadFile([ref]$f,$true).ToString() -ne 'NoError'){throw "World parse failed: $path"};return $f}finally{$s.Dispose()}
}
function JsonObject($file){return ([WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize([WolvenKit.Common.Conversion.RedFileDto]::new($file,$false),[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())|ConvertFrom-Json -Depth 100)}
function NewSector([bool]$controlled){
 $f=ReadWorld (Join-Path $WorkspaceRoot 'build\MistyViktorVariantsR5\source\towercontinued\misty_viktor_world\street_0.streamingsector');$r=$f.RootChunk
 $f.EmbeddedFiles.Clear();$r.Nodes.Clear();$r.NodeData.Data.Clear();$r.NodeRefs.Clear();$r.LocalInplaceResource.Clear();$r.PersistentNodes.Clear();$r.VariantNodes.Clear();$r.VariantIndices.Clear()
 $r.ExternInplaceResource=[Activator]::CreateInstance($r.GetType().GetProperty('ExternInplaceResource').PropertyType);$r.PersisentNodeIndex=[WolvenKit.RED4.Types.CInt32]::op_Implicit([int32]-1)
 [void]$r.VariantIndices.Add([WolvenKit.RED4.Types.CInt32]::op_Implicit(0));if($controlled){[void]$r.VariantIndices.Add([WolvenKit.RED4.Types.CInt32]::op_Implicit(0))};return $f
}
function Normalized($obj){
 # Handle numbers are serialization addresses, not REDengine object identities.
 return (($obj|ConvertTo-Json -Depth 100 -Compress) -replace '"HandleId":"[0-9]+",','')
}
if((Get-FileHash (Join-Path $WorkspaceRoot $registryRel)).Hash -ne $registryHash -or (Get-FileHash (Join-Path $WorkspaceRoot $spotsRel)).Hash -ne $spotsHash){throw 'Original NPC source hashes changed'}
$original=ReadWorld (Join-Path $WorkspaceRoot $registryRel);$spotsSource=ReadWorld (Join-Path $WorkspaceRoot $spotsRel)
$originalRegistry=$original.RootChunk.Nodes[3256].Chunk;$originalArea=$original.RootChunk.Nodes[5187].Chunk
if($originalRegistry.GetType().Name -ne 'worldCommunityRegistryNode' -or $originalArea.GetType().Name -ne 'worldCompiledCommunityAreaNode' -or $originalArea.DebugName.ToString() -ne '{q307_com_alley}'){throw 'Exact original community nodes changed'}
$originalCommunityId=[uint64]14820265454269095532
$sourceSpawner='$/03_night_city/c_watson/little_china/loc_mystic_mistys_ripperdoc_prefabH2DWJJI/loc_mystic_mistys_ripperdoc_questdesign_prefabJOEMBAA/#q307_pr_misty/#q307_com_alley'
if((NodeHash $sourceSpawner) -ne $originalCommunityId -or $originalArea.SourceObjectId.Hash.ToString() -ne $originalCommunityId.ToString()){throw 'Vanilla community identity mapping failed'}
$items=@($originalRegistry.CommunitiesData|Where-Object {$_.CommunityId.EntityId.Hash.ToString() -eq $originalCommunityId.ToString()});if($items.Count -ne 1){throw 'Original community registry ambiguity'}
$item=$items[0].DeepCopy();$allEntries=@($item.Template.Chunk.Entries);$allInitial=@($item.EntriesInitialState)
$item.Template.Chunk.Entries.Clear();$item.Template.Chunk.CrowdEntries.Clear();$item.EntriesInitialState.Clear()
if($item.Template.Chunk.SpawnSetReference.ToString() -ne 'None'){throw 'Selected community unexpectedly uses a spawn set'}
$registry=[WolvenKit.RED4.Types.worldCommunityRegistryNode]::new()
foreach($key in 'IsHostOnly','IsVisibleInGame','ProxyScale','Tag','TagExt','RepresentsCrowd'){$registry.$key=$originalRegistry.$key}
$registry.DebugName=[WolvenKit.RED4.Types.CName]::op_Implicit('PTFRMV_StreetCommunityRegistry')
$registry.SourcePrefabHash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit([uint64]0)
if($registry.RepresentsCrowd.ToString() -ne 'False'){throw 'Ambient character subset must not be a crowd registry'}
$area=$originalArea.DeepCopy();$allArea=@($area.Area.Chunk.EntriesData);$area.Area.Chunk.EntriesData.Clear()
$registryFile=NewSector $false;$registryFile.RootChunk.Category=$original.RootChunk.Category;$registryFile.RootChunk.Level=$original.RootChunk.Level
$spotFile=NewSector $true
$rows=[Collections.Generic.List[object]]::new();$spotReferences=[Collections.Generic.List[object]]::new()
foreach($num in 12..15){
 $entryName='q307_alley_extra_'+$num;$ref='$/03_night_city/#PTFRMV_StreetSpot'+$num;$sourceIndex=$num+7;$slot=$num-12
 $entry=@($allEntries|Where-Object {$_.Chunk.EntryName.ToString() -eq $entryName});$initial=@($allInitial|Where-Object {$_.EntryName.ToString() -eq $entryName});$areaEntry=@($allArea|Where-Object {$_.EntryName.ToString() -eq $entryName})
 if($entry.Count -ne 1 -or $initial.Count -ne 1 -or $areaEntry.Count -ne 1){throw 'Street subset entry ambiguous'}
 $entry=$entry[0];$initial=$initial[0];$areaEntry=$areaEntry[0]
 if($initial.EntryActiveOnStart.ToString() -ne 'False' -or $entry.Chunk.Initializers.Count -ne 0 -or $entry.Chunk.Phases.Count -ne 1 -or $entry.Chunk.Phases[0].Chunk.PhaseName.ToString() -ne $entryName -or $entry.Chunk.Phases[0].Chunk.TimePeriods.Count -ne 1 -or $entry.Chunk.Phases[0].Chunk.TimePeriods[0].SpotNodeRefs.Count -ne 1){throw 'Unexpected source actor lifecycle'}
 if($areaEntry.PhasesData.Count -ne 1 -or $areaEntry.PhasesData[0].TimePeriodsData.Count -ne 1 -or $areaEntry.PhasesData[0].TimePeriodsData[0].SpotNodeIds.Count -ne 1){throw 'Unexpected compiled area spot structure'}
 $node=$spotsSource.RootChunk.Nodes[$sourceIndex].DeepCopy();$datum=$spotsSource.RootChunk.NodeData.Data[$sourceIndex].DeepCopy()
 if($node.Chunk.GetType().Name -ne 'worldAISpotNode' -or $datum.NodeIndex.ToString() -ne $sourceIndex.ToString() -or -not $datum.QuestPrefabRefHash.ToString().EndsWith('/#q307_ws_alley_extra_'+$num)){throw 'Exact workspot mapping changed'}
 $sourceRef=$datum.QuestPrefabRefHash.ToString();$sourceSpotHash=NodeHash $sourceRef;$privateSpotHash=NodeHash $ref
 if($areaEntry.PhasesData[0].TimePeriodsData[0].SpotNodeIds[0].Hash.ToString() -ne $sourceSpotHash.ToString()){throw 'Original compiled workspot hash disagrees with original alias'}
 $persistent=@($originalRegistry.WorkspotsPersistentData|Where-Object {$_.GlobalNodeId.Hash.ToString() -eq $sourceSpotHash.ToString()});if($persistent.Count -ne 1){throw 'Original workspot persistent descriptor absent or ambiguous'}
 $persistent=$persistent[0].DeepCopy()
 [void]$item.Template.Chunk.Entries.Add($entry);[void]$item.EntriesInitialState.Add($initial);[void]$area.Area.Chunk.EntriesData.Add($areaEntry);[void]$registry.WorkspotsPersistentData.Add($persistent)
 [void]$spotFile.RootChunk.Nodes.Add($node);[void]$spotFile.RootChunk.NodeData.Data.Add($datum)
 $spotReferences.Add([ordered]@{source_node=$sourceIndex;source_datum=$sourceIndex;source_ref=$sourceRef;source_hash=$sourceSpotHash.ToString();private_hash=$privateSpotHash.ToString();private_ref=$ref})
 $rows.Add([ordered]@{entry=$entryName;phase=$entryName;private_workspot_ref=$ref;source_workspot_ref=$sourceRef;source_node=$sourceIndex;source_datum=$sourceIndex;record=if($num -eq 15){'Character.FattyMale'}else{'Character.SexworkerFemale'};entry_active_on_start=$false;world_x=$datum.Position.X.ToString();world_y=$datum.Position.Y.ToString();world_z=$datum.Position.Z.ToString();workspot=$node.Chunk.Spot.Chunk.Resource.DepotPath.ToString()})
}
[void]$registry.CommunitiesData.Add($item)
Add-RedHandle $registryFile.RootChunk.Nodes $registry;Add-RedHandle $registryFile.RootChunk.Nodes $area
foreach($sourceNode in @(3256,5187)){
 $ds=@($original.RootChunk.NodeData.Data|Where-Object {$_.NodeIndex.ToString() -eq $sourceNode.ToString()});if($ds.Count -ne 1){throw 'Registry/area source placement ambiguity'};[void]$registryFile.RootChunk.NodeData.Data.Add($ds[0].DeepCopy())
}
# Capture exactly the selected native payload before private identity remapping.
$beforeRegistry=(JsonObject $registryFile).Data.RootChunk;$beforeSpots=(JsonObject $spotFile).Data.RootChunk
$privateCommunityHash=NodeHash $spawner
$item.CommunityId.EntityId.Hash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit($privateCommunityHash)
$area.SourceObjectId.Hash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit($privateCommunityHash)
$area.DebugName=[WolvenKit.RED4.Types.CName]::op_Implicit('PTFRMV_StreetCommunity')
$area.SourcePrefabHash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit([uint64]0)
for($i=0;$i -lt 4;$i++){
 $selection=$spotReferences[$i];$ref=$selection.private_ref;$hash=[uint64]$selection.private_hash
 $item.Template.Chunk.Entries[$i].Chunk.Phases[0].Chunk.TimePeriods[0].SpotNodeRefs[0]=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref)
 $area.Area.Chunk.EntriesData[$i].PhasesData[0].TimePeriodsData[0].SpotNodeIds[0].Hash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit($hash)
 $registry.WorkspotsPersistentData[$i].GlobalNodeId.Hash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit($hash)
 $node=$spotFile.RootChunk.Nodes[$i].Chunk;$datum=$spotFile.RootChunk.NodeData.Data[$i]
 $node.DebugName=[WolvenKit.RED4.Types.CName]::op_Implicit('PTFRMV_StreetSpot'+($i+12));$node.SourcePrefabHash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit([uint64]0)
 $datum.Id=[uint64](750000000011100+$i);$datum.NodeIndex=[WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]$i);$datum.QuestPrefabRefHash=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref);$datum.UkHash1=[WolvenKit.RED4.Types.NodeRef]::op_Implicit('')
 [void]$spotFile.RootChunk.NodeRefs.Add([WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref))
}
for($i=0;$i -lt 2;$i++){
 $ref=if($i -eq 0){'$/03_night_city/#PTFRMV_StreetCommunityRegistry'}else{$spawner}
 $d=$registryFile.RootChunk.NodeData.Data[$i];$d.Id=[uint64](750000000011110+$i);$d.NodeIndex=[WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]$i);$d.QuestPrefabRefHash=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref);$d.UkHash1=[WolvenKit.RED4.Types.NodeRef]::op_Implicit('')
 [void]$registryFile.RootChunk.NodeRefs.Add([WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref))
}
$registryDepot='towercontinued\misty_viktor_world\street_people_r11_registry.streamingsector';$spotsDepot='towercontinued\misty_viktor_world\street_people_r11_spots.streamingsector'
Write-Cr2wFile $registryFile (Join-Path $out $registryDepot);Write-Cr2wFile $spotFile (Join-Path $out $spotsDepot)
$regRead=ReadWorld (Join-Path $out $registryDepot);$spotRead=ReadWorld (Join-Path $out $spotsDepot)
Export-Cr2wJson $regRead (Join-Path $audit 'r11_street_registry_sector.json');Export-Cr2wJson $spotRead (Join-Path $audit 'r11_street_spots_sector.json')
$actualRegistry=(JsonObject $regRead).Data.RootChunk;$actualSpots=(JsonObject $spotRead).Data.RootChunk
if($actualRegistry.nodes.Count -ne 2 -or $actualSpots.nodes.Count -ne 4 -or $actualRegistry.nodes[0].Data.communitiesData.Count -ne 1 -or $actualRegistry.nodes[0].Data.workspotsPersistentData.Count -ne 4){throw 'NPC source readback scope mismatch'}
$ar=$actualRegistry.nodes[0].Data;$br=$beforeRegistry.nodes[0].Data;$aa=$actualRegistry.nodes[1].Data;$ba=$beforeRegistry.nodes[1].Data
$ar.communitiesData[0].communityId=$br.communitiesData[0].communityId;$aa.sourceObjectId=$ba.sourceObjectId;$aa.debugName=$ba.debugName;$aa.sourcePrefabHash=$ba.sourcePrefabHash
for($i=0;$i -lt 4;$i++){
 $ar.communitiesData[0].template.Data.entries[$i].Data.phases[0].Data.timePeriods[0].spotNodeRefs=$br.communitiesData[0].template.Data.entries[$i].Data.phases[0].Data.timePeriods[0].spotNodeRefs
 $ar.workspotsPersistentData[$i].globalNodeId=$br.workspotsPersistentData[$i].globalNodeId
 $aa.area.Data.entriesData[$i].phasesData[0].timePeriodsData[0].spotNodeIds=$ba.area.Data.entriesData[$i].phasesData[0].timePeriodsData[0].spotNodeIds
 $actualSpots.nodes[$i].Data.debugName=$beforeSpots.nodes[$i].Data.debugName;$actualSpots.nodes[$i].Data.sourcePrefabHash=$beforeSpots.nodes[$i].Data.sourcePrefabHash
 foreach($field in 'Id','NodeIndex','QuestPrefabRefHash','UkHash1'){$actualSpots.nodeData.Data[$i].$field=$beforeSpots.nodeData.Data[$i].$field}
}
if((Normalized $ar) -cne (Normalized $br) -or (Normalized $aa) -cne (Normalized $ba) -or (Normalized $actualSpots.nodes) -cne (Normalized $beforeSpots.nodes) -or (Normalized $actualSpots.nodeData.Data) -cne (Normalized $beforeSpots.nodeData.Data)){throw 'Unauthorized actor/workspot payload delta'}
$baseBlockRel='research\phase2b_p4\staging_scan\ep1_1_nightcity\raw\base\worlds\03_night_city\_compiled\default\blocks\all.streamingblock'
$block=ReadWorld (Join-Path $WorkspaceRoot $baseBlockRel);$regDescriptor=$block.RootChunk.Descriptors[24130].DeepCopy();$spotDescriptor=$block.RootChunk.Descriptors[4833].DeepCopy()
if($regDescriptor.Category.ToString() -ne 'AlwaysLoaded' -or $regDescriptor.Variants.Count -ne 0){throw 'Original always-loaded descriptor changed'}
$shellBlock=ReadWorld (Join-Path $WorkspaceRoot 'build\MistyViktorDetailsR7\source\towercontinued\misty_viktor_world\shell.streamingblock');$variant=$shellBlock.RootChunk.Descriptors[0].Variants[0].DeepCopy()
if($variant.Name.ToString() -ne 'PTFRMV_ZetatechShell' -or $variant.NodeRef.ToString() -ne $owner -or $variant.EnabledByDefault.ToString() -ne 'False' -or $variant.RangeIndex.ToString() -ne '1'){throw 'Existing private shell variant changed'}
$regDescriptor.Data=[Activator]::CreateInstance($regDescriptor.GetType().GetProperty('Data').PropertyType,[object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($registryDepot)))
$regDescriptor.NumNodeRanges=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]1)
$spotDescriptor.Variants.Clear();[void]$spotDescriptor.Variants.Add($variant);$spotDescriptor.NumNodeRanges=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]2)
$spotDescriptor.Data=[Activator]::CreateInstance($spotDescriptor.GetType().GetProperty('Data').PropertyType,[object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($spotsDepot)))
$block.RootChunk.Descriptors.Clear();$block.EmbeddedFiles.Clear();[void]$block.RootChunk.Descriptors.Add($regDescriptor);[void]$block.RootChunk.Descriptors.Add($spotDescriptor)
$blockDepot='towercontinued\misty_viktor_world\street_people_r11.streamingblock';Write-Cr2wFile $block (Join-Path $out $blockDepot);Export-Cr2wJson (ReadWorld (Join-Path $out $blockDepot)) (Join-Path $audit 'r11_street_block.json')
$resources=@($registryDepot,$spotsDepot,$blockDepot)
if(@(Get-ChildItem -LiteralPath $out -File -Recurse).Count -ne 3){throw 'Unexpected NPC source file'}
$manifest=[ordered]@{status='BUILT_R11_FOUR_PRIVATE_STREET_NPCS_NOT_PACKED_INSTALLED_OR_LIVE';source_root=$out;resources=$resources;block_depot=$blockDepot;private_spawner=$spawner;private_community_hash=$privateCommunityHash.ToString();entries=@($rows);source_registry=$registryRel;source_registry_sha256=$registryHash;source_spots=$spotsRel;source_spots_sha256=$spotsHash;source_registry_node=3256;source_area_node=5187;registry_entries=4;compiled_area_entries=4;workspots=4;workspot_persistent_descriptors=4;initial_active_entries=0;registry_always_loaded=$true;spot_variant='PTFRMV_ZetatechShell';spot_default_off=$true;no_spawn_before_native_activation=$true;no_original_overrides=$true;no_original_record_or_template_resource_changes=$true;private_template_changes='Four-entry subset and remapped workspot references only';exact_payload_transform_readback_pass=$true;hashes=@($resources|ForEach-Object {[ordered]@{depot=$_;sha256=(Get-FileHash (Join-Path $out $_)).Hash}});source_spot_mapping=@($spotReferences);packed=$false;installed=$false;live_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'r11_street_world_manifest.json'),($manifest|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
[pscustomobject]$manifest|Select-Object status,source_root,private_spawner,registry_entries,workspots,initial_active_entries,exact_payload_transform_readback_pass|ConvertTo-Json
