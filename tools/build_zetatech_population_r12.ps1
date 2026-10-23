param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$out=Join-Path $WorkspaceRoot 'build\ZetatechPopulationR12'
$source=Join-Path $out 'source'
$prefix='towercontinued\zetatech_population_r12\'
$spawner='$/03_night_city/#PTFRMV12_Population'
function ReadWorld([string]$path){
 $s=[IO.File]::OpenRead($path)
 try{$rd=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($s);$rd.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])});$f=$null;if($rd.ReadFile([ref]$f,$true).ToString() -ne 'NoError'){throw "Parse failed: $path"};return $f}finally{$s.Dispose()}
}
$cast=[WolvenKit.RED4.Types.NodeRef].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint64]}
function NodeHash([string]$ref){$n=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref);return [uint64]$script:cast.Invoke($null,[object[]]@($n.PSObject.BaseObject))}
function NewRef([string]$ref){return [WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref)}
function NewName([string]$name){return [WolvenKit.RED4.Types.CName]::op_Implicit($name)}
function CloneSector([string]$depot){
 $f=ReadWorld (Join-Path $WorkspaceRoot ('build\MistyViktorStreetR11\source\towercontinued\misty_viktor_world\'+$depot))
 $f.RootChunk.Nodes.Clear();$f.RootChunk.NodeData.Data.Clear();$f.RootChunk.NodeRefs.Clear();return $f
}
$registryPath=Join-Path $WorkspaceRoot 'research\phase2b_p4\staging_scan\ep1_1_nightcity\raw\base\worlds\03_night_city\_compiled\default\always_loaded_1.streamingsector'
$spotsPath=Join-Path $WorkspaceRoot 'research\misty_viktor_world\r6_wall_nav_sources\ep1_1_nightcity\raw\base\worlds\03_night_city\_compiled\default\ep1\quest_bb3937b6e34a251c.streamingsector'
if((Get-FileHash $registryPath).Hash -ne '48997B5E57F019C979AFCE29AAEAC147809F1C9F8C88C9B305F58EF1DB02D824' -or (Get-FileHash $spotsPath).Hash -ne '47A17525EF23E21E9E1B35CC97F207A6AABDE7D605EE933182A193538C417952'){throw 'Source hashes changed'}
$original=ReadWorld $registryPath;$originalSpots=ReadWorld $spotsPath
$registries=@($original.RootChunk.Nodes|Where-Object {$_.Chunk.GetType().Name -eq 'worldCommunityRegistryNode'})
function OriginalEntry([string]$name){
 $found=[Collections.Generic.List[object]]::new()
 foreach($reg in $script:registries){foreach($item in $reg.Chunk.CommunitiesData){foreach($entry in $item.Template.Chunk.Entries){if($entry.Chunk.EntryName.ToString() -eq $name){$found.Add(@{registry=$reg.Chunk;item=$item;entry=$entry})}}}}
 if($found.Count -ne 1){throw "Ambiguous original entry $name : $($found.Count)"};return $found[0]
}
$base=OriginalEntry 'q307_alley_extra_12'
$regFile=CloneSector 'street_people_r11_registry.streamingsector';$spotFile=CloneSector 'street_people_r11_spots.streamingsector'
$basePrivate=ReadWorld (Join-Path $WorkspaceRoot 'build\MistyViktorStreetR11\source\towercontinued\misty_viktor_world\street_people_r11_registry.streamingsector')
$registry=$basePrivate.RootChunk.Nodes[0].Chunk.DeepCopy();$area=$basePrivate.RootChunk.Nodes[1].Chunk.DeepCopy()
$item=$registry.CommunitiesData[0].DeepCopy();$registry.CommunitiesData.Clear();$registry.WorkspotsPersistentData.Clear();$item.Template.Chunk.Entries.Clear();$item.EntriesInitialState.Clear();$area.Area.Chunk.EntriesData.Clear()
$communityHash=NodeHash $spawner
$item.CommunityId.EntityId.Hash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit($communityHash)
$area.SourceObjectId.Hash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit($communityHash);$area.DebugName=NewName 'PTFRMV12_Population'
$registry.DebugName=NewName 'PTFRMV12_Registry'
$selection=[Collections.Generic.List[object]]::new()
foreach($num in 2..31){if($num -notin 12..15){$selection.Add(@{entry=('q307_alley_extra_{0:00}' -f $num);phase=$null;role='street'})}}
$selection.Add(@{entry='q307_alley_extra_04b';phase=$null;role='street'})
$selection.Add(@{entry='q307_alley_extra_01';phase='return';role='guard'})
$selection.Add(@{entry='q307_zetatech_clerk';phase='q307_ws_zetatech_clerk_return';role='clerk'})
$rows=[Collections.Generic.List[object]]::new()
# These independent source spots replace encounter/prop-dependent poses only.
$substitutions=@{
 'q307_alley_extra_03'=@{node=40;reason='Remove synchronized kicking encounter; use independent nervous idle'}
 'q307_alley_extra_07'=@{node=20;reason='Vending device is not restored by this population package; independent idle'}
 'q307_alley_extra_11'=@{node=40;reason='Avoid endlessly knocking at an unverified door; independent nervous idle'}
 'q307_alley_extra_20'=@{node=2;reason='Replace synchronized curb conversation with independent seated smoking'}
 'q307_alley_extra_28'=@{node=44;reason='Bench support not independently verified; source ground-seated idle'}
}
function AddSpot([int]$index,[string]$ref,[int]$animationIndex=-1){
 $node=$script:originalSpots.RootChunk.Nodes[$index].DeepCopy()
 $placements=@($script:originalSpots.RootChunk.NodeData.Data|Where-Object {$_.NodeIndex.ToString() -eq $index.ToString()})
 if($placements.Count -ne 1){throw 'Spot placement ambiguity'};$datum=$placements[0].DeepCopy();$originalRef=$datum.QuestPrefabRefHash.ToString()
 $hash=NodeHash $ref;$slot=$script:spotFile.RootChunk.Nodes.Count
 if($node.Chunk.GetType().Name -ne 'worldAISpotNode' -or $node.Chunk.Spot.Chunk.MasterNodeRef.ToString() -notin @('0','') -or $node.Chunk.LookAtTarget.ToString() -notin @('0','')){throw "Dependent workspot $index"}
 if($animationIndex -ge 0){$node.Chunk.Spot=$script:originalSpots.RootChunk.Nodes[$animationIndex].Chunk.Spot.DeepCopy()}
 $node.Chunk.IsWorkspotInfinite=$true;$node.Chunk.SourcePrefabHash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit([uint64]0);$node.Chunk.DebugName=NewName ('PTFRMV12_Spot'+$slot)
 $datum.Id=[uint64](750000000012000+$slot);$datum.NodeIndex=[WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]$slot);$datum.QuestPrefabRefHash=NewRef $ref;$datum.UkHash1=NewRef ''
 [void]$script:spotFile.RootChunk.Nodes.Add($node);[void]$script:spotFile.RootChunk.NodeData.Data.Add($datum);[void]$script:spotFile.RootChunk.NodeRefs.Add((NewRef $ref))
 $sourceHash=NodeHash $originalRef
 $persistent=@($script:registries|ForEach-Object {$_.Chunk.WorkspotsPersistentData}|Where-Object {$_.GlobalNodeId.Hash.ToString() -eq $sourceHash.ToString()})
 if($persistent.Count -ne 1){throw "Persistent workspot descriptor missing $originalRef"}
 $persistent=$persistent[0].DeepCopy();$persistent.GlobalNodeId.Hash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit($hash);[void]$script:registry.WorkspotsPersistentData.Add($persistent)
 return @{ref=$ref;hash=$hash;original_ref=$originalRef;original_hash=$sourceHash;index=$index;slot=$slot;animation=$node.Chunk.Spot.Chunk.Resource.DepotPath.ToString();position=@($datum.Position.X.ToString(),$datum.Position.Y.ToString(),$datum.Position.Z.ToString())}
}
foreach($choice in $selection){
 $src=OriginalEntry $choice.entry;$entry=$src.entry.DeepCopy()
 if($entry.Chunk.Initializers.Count -ne 0){throw "Entry initializers need audit $($choice.entry)"}
 $phases=@($entry.Chunk.Phases|Where-Object {$null -eq $choice.phase -or $_.Chunk.PhaseName.ToString() -eq $choice.phase})
 if($phases.Count -ne 1){throw "Phase selection failed $($choice.entry)"}
 $phase=$phases[0].DeepCopy();$phaseName=$phase.Chunk.PhaseName.ToString()
 if($phase.Chunk.TimePeriods.Count -ne 1 -or $phase.Chunk.TimePeriods[0].SpotNodeRefs.Count -ne 1 -or $phase.Chunk.TimePeriods[0].Quantity.ToString() -ne '1'){throw 'Non-singleton schedule'}
 $shortRef=$phase.Chunk.TimePeriods[0].SpotNodeRefs[0].ToString()
 $placements=@($originalSpots.RootChunk.NodeData.Data|Where-Object {$_.QuestPrefabRefHash.ToString().EndsWith('/'+$shortRef)})
 if($placements.Count -ne 1){throw "Workspot mapping failed $shortRef"}
 $sourceIndex=[int]::Parse($placements[0].NodeIndex.ToString());$ref='$/03_night_city/#PTFRMV12_'+$choice.entry
 $animationIndex=if($substitutions.ContainsKey($choice.entry)){$substitutions[$choice.entry].node}else{-1}
 $spot=AddSpot $sourceIndex $ref $animationIndex
 $phase.Chunk.TimePeriods[0].SpotNodeRefs[0]=NewRef $ref;$entry.Chunk.Phases.Clear();[void]$entry.Chunk.Phases.Add($phase)
 $initial=@($src.item.EntriesInitialState|Where-Object {$_.EntryName.ToString() -eq $choice.entry})
 if($initial.Count -ne 1){throw 'Initial state ambiguity'};$initial=$initial[0].DeepCopy();$initial.EntryActiveOnStart=$false;$initial.InitialPhaseName=NewName $phaseName
 $areas=@($original.RootChunk.Nodes|Where-Object {$_.Chunk.GetType().Name -eq 'worldCompiledCommunityAreaNode' -and $_.Chunk.SourceObjectId.Hash.ToString() -eq $src.item.CommunityId.EntityId.Hash.ToString()})
 if($areas.Count -ne 1){throw 'Area identity ambiguity'}
 $areaEntry=@($areas[0].Chunk.Area.Chunk.EntriesData|Where-Object {$_.EntryName.ToString() -eq $choice.entry})[0].DeepCopy()
 $areaPhases=@($areaEntry.PhasesData|Where-Object {$_.EntryPhaseName.ToString() -eq $phaseName})
 if($areaPhases.Count -ne 1){throw 'Compiled phase ambiguity'};$ap=$areaPhases[0].DeepCopy()
 if($ap.TimePeriodsData.Count -ne 1 -or $ap.TimePeriodsData[0].SpotNodeIds.Count -ne 1 -or $ap.TimePeriodsData[0].SpotNodeIds[0].Hash.ToString() -ne $spot.original_hash.ToString()){throw 'Compiled spot does not match original alias'}
 $ap.TimePeriodsData[0].SpotNodeIds[0].Hash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit([uint64]$spot.hash);$areaEntry.PhasesData.Clear();[void]$areaEntry.PhasesData.Add($ap)
 [void]$item.Template.Chunk.Entries.Add($entry);[void]$item.EntriesInitialState.Add($initial);[void]$area.Area.Chunk.EntriesData.Add($areaEntry)
 $rows.Add([ordered]@{entry=$choice.entry;phase=$phaseName;role=$choice.role;source_community=$src.item.CommunityId.EntityId.Hash.ToString();record=$entry.Chunk.CharacterRecordId.ToString();spot=$spot;animation_change=if($substitutions.ContainsKey($choice.entry)){$substitutions[$choice.entry].reason}else{'Original independent workspot preserved'}})
}
$terrySpot=AddSpot 12 '$/03_night_city/#PTFRMV12_TerrySmoke'
# Entry23's exact authored wheelchair, not the whole ending prop bundle.
$chair=$originalSpots.RootChunk.Nodes[203].DeepCopy();$chairData=@($originalSpots.RootChunk.NodeData.Data|Where-Object {$_.NodeIndex.ToString() -eq '203'})[0].DeepCopy()
if($chair.Chunk.GetType().Name -ne 'worldStaticMeshNode' -or $chair.Chunk.Mesh.DepotPath.ToString() -ne 'base\environment\decoration\misc\shops\int_medical_deco\wheelchair_deco.mesh'){throw 'Wheelchair source changed'}
$chair.Chunk.SourcePrefabHash=[WolvenKit.RED4.Types.CUInt64]::op_Implicit([uint64]0);$chair.Chunk.DebugName=NewName 'PTFRMV12_Wheelchair'
$chairData.Id=[uint64]750000000012030;$chairData.NodeIndex=[WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]30);$chairData.QuestPrefabRefHash=NewRef '$/03_night_city/#PTFRMV12_Wheelchair';$chairData.UkHash1=NewRef ''
[void]$spotFile.RootChunk.Nodes.Add($chair);[void]$spotFile.RootChunk.NodeData.Data.Add($chairData);[void]$spotFile.RootChunk.NodeRefs.Add($chairData.QuestPrefabRefHash)
[void]$registry.CommunitiesData.Add($item);Add-RedHandle $regFile.RootChunk.Nodes $registry;Add-RedHandle $regFile.RootChunk.Nodes $area
for($i=0;$i -lt 2;$i++){
 $d=$basePrivate.RootChunk.NodeData.Data[$i].DeepCopy();$ref=if($i -eq 0){'$/03_night_city/#PTFRMV12_Registry'}else{$spawner}
 $d.Id=[uint64](750000000012040+$i);$d.QuestPrefabRefHash=NewRef $ref;[void]$regFile.RootChunk.NodeData.Data.Add($d);[void]$regFile.RootChunk.NodeRefs.Add((NewRef $ref))
}
$resources=@(($prefix+'registry.streamingsector'),($prefix+'spots.streamingsector'),($prefix+'population.streamingblock'))
Write-Cr2wFile $regFile (Join-Path $source $resources[0]);Write-Cr2wFile $spotFile (Join-Path $source $resources[1])
$block=ReadWorld (Join-Path $WorkspaceRoot 'build\MistyViktorStreetR11\source\towercontinued\misty_viktor_world\street_people_r11.streamingblock')
for($i=0;$i -lt 2;$i++){$block.RootChunk.Descriptors[$i].Data=[Activator]::CreateInstance($block.RootChunk.Descriptors[$i].GetType().GetProperty('Data').PropertyType,[object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($resources[$i])))}
Write-Cr2wFile $block (Join-Path $source $resources[2])
foreach($depot in $resources){Export-Cr2wJson (ReadWorld (Join-Path $source $depot)) (Join-Path $audit ('r12_'+[IO.Path]::GetFileName($depot)+'.json'))}
if($rows.Count -ne 29 -or $spotFile.RootChunk.Nodes.Count -ne 31){throw 'R12 population count mismatch'}
$manifest=[ordered]@{status='BUILT_R12_POPULATION_WORLD_LIVE_PENDING';source=$source;resources=$resources;spawner=$spawner;entries=@($rows);terry_spot=$terrySpot;additional_street_npcs=27;existing_street_npcs_unchanged=4;indoor_replacements=2;private_workspots=30;wheelchairs=1;initially_active=0;ending_cast_excluded=@('Misty','Jim','new merc','three scene drones');original_resource_overrides=0;live_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'population_r12_world_manifest.json'),($manifest|ConvertTo-Json -Depth 15),[Text.UTF8Encoding]::new($false))
[pscustomobject]$manifest|Select-Object status,additional_street_npcs,indoor_replacements,private_workspots,wheelchairs|ConvertTo-Json
