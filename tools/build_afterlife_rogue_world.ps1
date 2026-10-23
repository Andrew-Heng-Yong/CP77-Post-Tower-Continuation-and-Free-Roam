param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\afterlife_world'
$out=Join-Path $WorkspaceRoot 'build\AfterlifeR1\rogue_source'
$prefix='towercontinued\afterlife_r1\'
$spawner='$/03_night_city/#PTFRAF1_RogueCommunity'
$spotRef='$/03_night_city/#PTFRAF1_RogueBooth'
$variantName='PTFRAF1_Rogue'
$variantOwner='$/03_night_city/c_watson/little_china/#loc_q103_afterlife/#loc_q103_afterlife_env'
$appearance='rogue_ep__q307__two_years_later'
$ending=Get-Content (Join-Path $WorkspaceRoot 'research\q307_extracted\json\ep1\quest\main_quests\q307\scenes\final_boards\q307_ending_01_rogue.scene.json') -Raw|ConvertFrom-Json -Depth 100
$endingActor=@($ending.Data.RootChunk.actors|Where-Object {$_.actorName -eq 'rogue'})
if($endingActor.Count -ne 1 -or $endingActor[0].spawnDespawnParams.appearance.'$value' -ne $appearance -or $endingActor[0].spawnDespawnParams.specRecordId.'$value' -ne 'Character.Rogue'){throw 'Tower Rogue appearance source changed'}
$registryRel='research\phase2b_p4\staging_scan\ep1_1_nightcity\raw\base\worlds\03_night_city\_compiled\default\always_loaded_1.streamingsector'
$spotRel='research\afterlife_world\rogue_world\raw\base\worlds\03_night_city\_compiled\default\quest_285aa3a99f6fad6d.streamingsector'
function ReadWorld([string]$path){
 $s=[IO.File]::OpenRead($path)
 try{$rd=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($s);$rd.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])});$f=$null;if($rd.ReadFile([ref]$f,$true).ToString() -ne 'NoError'){throw "Parse failed: $path"};return $f}finally{$s.Dispose()}
}
function NewRef([string]$ref){return [WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref)}
function NewName([string]$name){return [WolvenKit.RED4.Types.CName]::op_Implicit($name)}
$cast=[WolvenKit.RED4.Types.NodeRef].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint64]}
function NodeHash([string]$ref){$n=NewRef $ref;return [uint64]$script:cast.Invoke($null,[object[]]@($n.PSObject.BaseObject))}
function JsonObject($file){return ([WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize([WolvenKit.Common.Conversion.RedFileDto]::new($file,$false),[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())|ConvertFrom-Json -Depth 100)}
function Normalized($obj){return (($obj|ConvertTo-Json -Depth 100 -Compress) -replace '"HandleId":"[0-9]+",','')}
function NewSector([string]$name){
 $f=ReadWorld (Join-Path $WorkspaceRoot ('build\MistyViktorStreetR11\source\towercontinued\misty_viktor_world\'+$name))
 $f.RootChunk.Nodes.Clear();$f.RootChunk.NodeData.Data.Clear();$f.RootChunk.NodeRefs.Clear();return $f
}
if((Get-FileHash (Join-Path $WorkspaceRoot $registryRel)).Hash -ne '48997B5E57F019C979AFCE29AAEAC147809F1C9F8C88C9B305F58EF1DB02D824' -or (Get-FileHash (Join-Path $WorkspaceRoot $spotRel)).Hash -ne 'F9953D1D5BB5BD4BEB7E054CDE397DC548E0267311F65D0932735B5CC6F0C1D5'){throw 'Rogue original source hash changed'}
$original=ReadWorld (Join-Path $WorkspaceRoot $registryRel);$sourceSpots=ReadWorld (Join-Path $WorkspaceRoot $spotRel)
$originalRegistry=$original.RootChunk.Nodes[3256].Chunk;$originalArea=$original.RootChunk.Nodes[2946].Chunk
if($originalRegistry.GetType().Name -ne 'worldCommunityRegistryNode' -or $originalArea.SourceObjectId.Hash.ToString() -ne '5513750264196322780'){throw 'Rogue source identity changed'}
$item=$originalRegistry.CommunitiesData[96].DeepCopy()
if($item.CommunityId.EntityId.Hash.ToString() -ne '5513750264196322780' -or $item.Template.Chunk.SpawnSetReference.ToString() -ne '#rogue' -or $item.Template.Chunk.Entries.Count -ne 1){throw 'Rogue source template changed'}
$entry=$item.Template.Chunk.Entries[0].DeepCopy();$initial=$item.EntriesInitialState[0].DeepCopy()
$expectedRecord=[WolvenKit.RED4.Types.TweakDBID]::op_Implicit('Character.Rogue')
if($entry.Chunk.EntryName.ToString() -ne 'rogue' -or -not $entry.Chunk.CharacterRecordId.Equals($expectedRecord) -or $entry.Chunk.Initializers.Count -ne 0){throw 'Rogue source record changed'}
$phases=@($entry.Chunk.Phases|Where-Object {$_.Chunk.PhaseName.ToString() -eq 'default'});if($phases.Count -ne 1){throw 'Default Rogue phase ambiguous'}
$phase=$phases[0].DeepCopy()
if($phase.Chunk.TimePeriods.Count -ne 1 -or $phase.Chunk.TimePeriods[0].Quantity.ToString() -ne '1' -or $phase.Chunk.TimePeriods[0].SpotNodeRefs.Count -ne 1 -or $phase.Chunk.TimePeriods[0].SpotNodeRefs[0].ToString() -ne '#ws_rogue_default'){throw 'Rogue ordinary schedule changed'}
$entry.Chunk.Phases.Clear();[void]$entry.Chunk.Phases.Add($phase)
$item.Template.Chunk.Entries.Clear();[void]$item.Template.Chunk.Entries.Add($entry);$item.Template.Chunk.CrowdEntries.Clear()
$item.EntriesInitialState.Clear();[void]$item.EntriesInitialState.Add($initial)
$area=$originalArea.DeepCopy();$areaEntry=$area.Area.Chunk.EntriesData[0].DeepCopy()
$areaPhases=@($areaEntry.PhasesData|Where-Object {$_.EntryPhaseName.ToString() -eq 'default'});if($areaPhases.Count -ne 1){throw 'Rogue compiled default phase ambiguous'}
$areaPhase=$areaPhases[0].DeepCopy();$areaEntry.PhasesData.Clear();[void]$areaEntry.PhasesData.Add($areaPhase);$area.Area.Chunk.EntriesData.Clear();[void]$area.Area.Chunk.EntriesData.Add($areaEntry)
$node=$sourceSpots.RootChunk.Nodes[0].DeepCopy();$datum=$sourceSpots.RootChunk.NodeData.Data[0].DeepCopy();$sourceRef=$datum.QuestPrefabRefHash.ToString();$sourceHash=NodeHash $sourceRef
if($node.Chunk.GetType().Name -ne 'worldAISpotNode' -or $node.Chunk.Spot.Chunk.MasterNodeRef.ToString() -notin @('0','') -or $node.Chunk.LookAtTarget.ToString() -notin @('0','') -or $node.Chunk.Spot.Chunk.Resource.DepotPath.ToString() -ne 'base\workspots\main_characters\rogue\rogue__sit_couch_lean_back__sit_around__01.workspot'){throw 'Rogue independent booth animation changed'}
if($areaPhase.TimePeriodsData.Count -ne 1 -or $areaPhase.TimePeriodsData[0].SpotNodeIds.Count -ne 1 -or $areaPhase.TimePeriodsData[0].SpotNodeIds[0].Hash.ToString() -ne $sourceHash.ToString()){throw 'Rogue source alias mapping mismatch'}
$persistent=@($originalRegistry.WorkspotsPersistentData|Where-Object {$_.GlobalNodeId.Hash.ToString() -eq $sourceHash.ToString()});if($persistent.Count -ne 1){throw 'Rogue workspot persistent descriptor ambiguous'}
$registry=[WolvenKit.RED4.Types.worldCommunityRegistryNode]::new()
foreach($key in 'IsHostOnly','IsVisibleInGame','ProxyScale','Tag','TagExt','RepresentsCrowd'){$registry.$key=$originalRegistry.$key}
$registry.DebugName=NewName 'PTFRAF1_RogueRegistry';$registry.SourcePrefabHash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit([uint64]0)
[void]$registry.CommunitiesData.Add($item);[void]$registry.WorkspotsPersistentData.Add($persistent[0].DeepCopy())
$regFile=NewSector 'street_people_r11_registry.streamingsector';$spotFile=NewSector 'street_people_r11_spots.streamingsector'
Add-RedHandle $regFile.RootChunk.Nodes $registry;Add-RedHandle $regFile.RootChunk.Nodes $area
foreach($index in @(3256,2946)){$ds=@($original.RootChunk.NodeData.Data|Where-Object {$_.NodeIndex.ToString() -eq $index.ToString()});if($ds.Count -ne 1){throw 'Rogue source registry placement ambiguous'};[void]$regFile.RootChunk.NodeData.Data.Add($ds[0].DeepCopy())}
[void]$spotFile.RootChunk.Nodes.Add($node);[void]$spotFile.RootChunk.NodeData.Data.Add($datum)
$beforeRegistry=(JsonObject $regFile).Data.RootChunk;$beforeSpots=(JsonObject $spotFile).Data.RootChunk
$communityHash=NodeHash $spawner;$spotHash=NodeHash $spotRef
$item.CommunityId.EntityId.Hash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit($communityHash)
$item.Template.Chunk.SpawnSetReference=NewName 'None';$initial.EntryActiveOnStart=$false
$phase.Chunk.Appearances.Clear();[void]$phase.Chunk.Appearances.Add((NewName $appearance));$phase.Chunk.TimePeriods[0].SpotNodeRefs[0]=NewRef $spotRef
$area.SourceObjectId.Hash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit($communityHash);$area.SourcePrefabHash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit([uint64]0);$area.DebugName=NewName 'PTFRAF1_RogueCommunity'
$areaPhase.TimePeriodsData[0].SpotNodeIds[0].Hash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit($spotHash)
$registry.WorkspotsPersistentData[0].GlobalNodeId.Hash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit($spotHash)
$node.Chunk.DebugName=NewName 'PTFRAF1_RogueBooth';$node.Chunk.SourcePrefabHash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit([uint64]0)
$datum.Id=[uint64]750000000101101;$datum.NodeIndex=[WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]0);$datum.QuestPrefabRefHash=NewRef $spotRef;$datum.UkHash1=NewRef ''
[void]$spotFile.RootChunk.NodeRefs.Add((NewRef $spotRef))
for($i=0;$i -lt 2;$i++){$ref=if($i -eq 0){'$/03_night_city/#PTFRAF1_RogueRegistry'}else{$spawner};$d=$regFile.RootChunk.NodeData.Data[$i];$d.Id=[uint64](750000000101110+$i);$d.NodeIndex=[WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]$i);$d.QuestPrefabRefHash=NewRef $ref;$d.UkHash1=NewRef '';[void]$regFile.RootChunk.NodeRefs.Add((NewRef $ref))}
$resources=@(($prefix+'rogue_registry.streamingsector'),($prefix+'rogue_spot.streamingsector'),($prefix+'rogue.streamingblock'))
Write-Cr2wFile $regFile (Join-Path $out $resources[0]);Write-Cr2wFile $spotFile (Join-Path $out $resources[1])
$block=ReadWorld (Join-Path $WorkspaceRoot 'research\phase2b_p4\staging_scan\ep1_1_nightcity\raw\base\worlds\03_night_city\_compiled\default\blocks\all.streamingblock')
$regDescriptor=$block.RootChunk.Descriptors[24130].DeepCopy()
$sourceDescriptors=@($block.RootChunk.Descriptors|Where-Object {$_.Data.DepotPath.ToString() -eq 'base\worlds\03_night_city\_compiled\default\exterior_-23_15_0_0.streamingsector'})
if($sourceDescriptors.Count -ne 1 -or $regDescriptor.Category.ToString() -ne 'AlwaysLoaded' -or $regDescriptor.Variants.Count -ne 0){throw 'Rogue block descriptor source changed'}
$spotDescriptor=$sourceDescriptors[0].DeepCopy();$spotFile.RootChunk.Level=$spotDescriptor.Level;$spotFile.RootChunk.Category=$spotDescriptor.Category
Write-Cr2wFile $spotFile (Join-Path $out $resources[1])
$variantSource=ReadWorld (Join-Path $WorkspaceRoot 'build\MistyViktorStreetR11\source\towercontinued\misty_viktor_world\street_people_r11.streamingblock')
$variant=$variantSource.RootChunk.Descriptors[1].Variants[0].DeepCopy();$variant.Name=NewName $variantName;$variant.NodeRef=NewRef $variantOwner;$variant.VariantId=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]1826022284)
$variant.EnabledByDefault=$false;$variant.RangeIndex=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]1);$variant.ParentVariantID=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]0)
$spotDescriptor.Variants.Clear();[void]$spotDescriptor.Variants.Add($variant);$spotDescriptor.NumNodeRanges=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]2)
$regDescriptor.NumNodeRanges=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]1)
foreach($pair in @(@($regDescriptor,$resources[0]),@($spotDescriptor,$resources[1]))){$pair[0].Data=[Activator]::CreateInstance($pair[0].GetType().GetProperty('Data').PropertyType,[object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($pair[1])))}
$block.RootChunk.Descriptors.Clear();$block.EmbeddedFiles.Clear();[void]$block.RootChunk.Descriptors.Add($regDescriptor);[void]$block.RootChunk.Descriptors.Add($spotDescriptor)
Write-Cr2wFile $block (Join-Path $out $resources[2])
foreach($depot in $resources){Export-Cr2wJson (ReadWorld (Join-Path $out $depot)) (Join-Path $audit ([IO.Path]::GetFileName($depot)+'.json'))}
$blockRead=ReadWorld (Join-Path $out $resources[2]);$descs=$blockRead.RootChunk.Descriptors
if($descs.Count -ne 2 -or $descs[0].Category.ToString() -ne 'AlwaysLoaded' -or $descs[0].Variants.Count -ne 0 -or $descs[1].Variants.Count -ne 1 -or $descs[1].Variants[0].EnabledByDefault.ToString() -ne 'False' -or $descs[1].Variants[0].Name.ToString() -ne $variantName -or $descs[1].Variants[0].NodeRef.ToString() -ne $variantOwner -or $descs[1].QuestPrefabNodeRef.ToString() -notin @('0','')){throw 'Rogue block readback mismatch'}
$spotBox=(JsonObject $blockRead).Data.RootChunk.descriptors[1].streamingBox
foreach($axis in 'X','Y','Z'){$value=[double]::Parse($datum.Position.$axis.ToString(),[Globalization.CultureInfo]::InvariantCulture);if($value -lt $spotBox.Min.$axis -or $value -gt $spotBox.Max.$axis){throw 'Rogue placement outside its streaming bounds'}}
$ar=(JsonObject (ReadWorld (Join-Path $out $resources[0]))).Data.RootChunk;$asp=(JsonObject (ReadWorld (Join-Path $out $resources[1]))).Data.RootChunk
if($ar.nodes.Count -ne 2 -or $asp.nodes.Count -ne 1 -or $ar.nodes[0].Data.communitiesData.Count -ne 1 -or $ar.nodes[0].Data.workspotsPersistentData.Count -ne 1 -or $ar.nodes[0].Data.communitiesData[0].entriesInitialState[0].entryActiveOnStart -ne 0 -or $asp.variantIndices.Count -ne 2 -or $asp.variantIndices[0] -ne 0 -or $asp.variantIndices[1] -ne 0){throw 'Rogue bounded readback mismatch'}
$a=$asp.nodes[0].Data;$b=$beforeSpots.nodes[0].Data;$a.debugName=$b.debugName;$a.sourcePrefabHash=$b.sourcePrefabHash
if((Normalized $a) -cne (Normalized $b)){throw 'Unexpected Rogue workspot payload change'}
$a=$asp.nodeData.Data[0];$b=$beforeSpots.nodeData.Data[0];foreach($key in 'Id','NodeIndex','QuestPrefabRefHash','UkHash1'){$a.$key=$b.$key};if((Normalized $a) -cne (Normalized $b)){throw 'Unexpected Rogue placement change'}
$rr=$ar.nodes[0].Data;$br=$beforeRegistry.nodes[0].Data;$ra=$ar.nodes[1].Data;$ba=$beforeRegistry.nodes[1].Data
$rr.communitiesData[0].communityId=$br.communitiesData[0].communityId;$rr.communitiesData[0].template.Data.spawnSetReference=$br.communitiesData[0].template.Data.spawnSetReference
$rr.communitiesData[0].template.Data.entries[0].Data.phases[0].Data.appearances=$br.communitiesData[0].template.Data.entries[0].Data.phases[0].Data.appearances
$rr.communitiesData[0].template.Data.entries[0].Data.phases[0].Data.timePeriods[0].spotNodeRefs=$br.communitiesData[0].template.Data.entries[0].Data.phases[0].Data.timePeriods[0].spotNodeRefs
$rr.workspotsPersistentData[0].globalNodeId=$br.workspotsPersistentData[0].globalNodeId
foreach($key in 'sourceObjectId','sourcePrefabHash','debugName'){$ra.$key=$ba.$key};$ra.area.Data.entriesData[0].phasesData[0].timePeriodsData[0].spotNodeIds=$ba.area.Data.entriesData[0].phasesData[0].timePeriodsData[0].spotNodeIds
if((Normalized $rr) -cne (Normalized $br) -or (Normalized $ra) -cne (Normalized $ba)){throw 'Unexpected Rogue registry payload change'}
$manifest=[ordered]@{status='BUILT_PRIVATE_AMBIENT_ROGUE_NOT_PACKAGED_INSTALLED_OR_LIVE';source_root=$out;resources=$resources;block_depot=$resources[2];private_community_ref=$spawner;private_community_hash=$communityHash.ToString();entry='rogue';phase='default';record='Character.Rogue';appearance=$appearance;workspot_ref=$spotRef;source_workspot_ref=$sourceRef;source_workspot_hash=$sourceHash.ToString();source_registry=$registryRel;source_registry_node=3256;source_registry_item=96;source_area_node=2946;source_spots=$spotRel;source_spot_node=0;source_spot_datum=0;original_spawnset='#rogue';original_entry='rogue';original_handoff_action='Deactivate';variant_name=$variantName;variant_owner=$variantOwner;variant_id=1826022284;default_off=$true;initial_active_entries=0;registry_always_loaded=$true;private_workspots=1;private_actors=1;source_transform=$beforeSpots.nodeData.Data[0];workspot_payload=$beforeSpots.nodes[0].Data;streaming_bounds=$spotBox;exact_allowed_delta_readback_pass=$true;hashes=@($resources|ForEach-Object {[ordered]@{depot=$_;sha256=(Get-FileHash (Join-Path $out $_)).Hash}});recommended_guards=@('Full completed-Tower guard set','main_game_killed=1','rogue_default_on>0','q116_rogue_dead=0','private workspot streamed','mod-owned Rogue quest lease clear');availability_policy='Preserve rogue_default_on and all story facts; private ambient presence is independent of stopped pre-ending quest leases';default_dialogue_restored=$false;original_resources_overridden=0;live_tested=$false}
$manifest.recommended_guards=@('Full completed-Tower guard set','q307_main_game_killed=1','rogue_default_on>0','q116_rogue_dead=0','private workspot streamed','mod-owned Rogue quest lease clear')
[IO.File]::WriteAllText((Join-Path $audit 'rogue_world_manifest.json'),($manifest|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
[pscustomobject]$manifest|Select-Object status,private_community_ref,workspot_ref,private_actors,private_workspots,exact_allowed_delta_readback_pass|ConvertTo-Json
