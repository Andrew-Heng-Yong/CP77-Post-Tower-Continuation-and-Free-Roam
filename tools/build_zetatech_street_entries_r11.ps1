# Dot-source after build_phase2a.ps1 -HelpersOnly. Does not write or install assets.
param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))

$script:ZetatechStreetR11Root=$WorkspaceRoot
$script:ZetatechStreetR11Entries=@(
 @{id='12';record='Character.SexworkerFemale';appearance='prostitute_wa_prostitute_wa_09';node=19;x=-1558.48267;y=1193.72217;z=16.2460365;workspot='base\workspots\archetype\dirt\common\ground\dirt__stand_ground__stand_around__02.workspot'},
 @{id='13';record='Character.SexworkerFemale';appearance='prostitute_wa_prostitute_wa_04';node=20;x=-1557.85596;y=1192.89490;z=16.2539005;workspot='base\workspots\common\ground\generic__stand_ground__stand_around__10.workspot'},
 @{id='14';record='Character.SexworkerFemale';appearance='prostitute_wa_prostitute_wa_05';node=21;x=-1555.03857;y=1188.73596;z=16.2151375;workspot='base\workspots\common\ground\generic__stand_ground_cigarette__smoke__02.workspot'},
 @{id='15';record='Character.FattyMale';appearance='citizen__obese_mf_nomad_02';node=22;x=-1557.29968;y=1193.97839;z=16.2523575;workspot='base\workspots\common\ground\fat__stand_ground__stand_around__01.workspot'}
)
$script:ZetatechStreetR11RefBase='$/03_night_city/c_watson/little_china/loc_mystic_mistys_ripperdoc_prefabH2DWJJI/loc_mystic_mistys_ripperdoc_questdesign_prefabJOEMBAA/#q307_pr_misty/'

function Assert-ZetatechStreetEntriesR11Sources {
 $communityPath=Join-Path $script:ZetatechStreetR11Root 'research\misty_viktor_world\street_npc_sources\json\ep1\quest\main_quests\q307\communities\q307_com_alley.community.json'
 $sectorPath=Join-Path $script:ZetatechStreetR11Root 'research\misty_viktor_world\r6_wall_nav_sources\ep1_1_nightcity\json\base\worlds\03_night_city\_compiled\default\ep1\quest_bb3937b6e34a251c.streamingsector.json'
 if((Get-FileHash -LiteralPath $communityPath).Hash -ne '34AE9D08090D8DD96650070990C1FD3E558A082B6CB1D63D03B317583DA432AF'){throw 'Street community source changed'}
 if((Get-FileHash -LiteralPath $sectorPath).Hash -ne '6DF10E0B989F3154B8C03B5E5DE361319CDD7E4E648E16A12D47A02ADC1EC535'){throw 'Street workspot source changed'}
 $community=(Get-Content -LiteralPath $communityPath -Raw|ConvertFrom-Json).Data.RootChunk.communityTemplate.Data
 $sector=(Get-Content -LiteralPath $sectorPath -Raw|ConvertFrom-Json).Data.RootChunk
 foreach($entry in $script:ZetatechStreetR11Entries){
  $name='q307_alley_extra_'+$entry.id;$ref='#q307_ws_alley_extra_'+$entry.id
  $matches=@($community.entries|Where-Object {$_.Data.entryName.'$value' -eq $name})
  if($matches.Count -ne 1){throw "Missing unique street entry $name"}
  $e=$matches[0].Data
  if($e.characterRecordId.'$value' -ne $entry.record -or $e.initializers.Count -ne 0 -or $e.phases.Count -ne 1 -or $e.spawnInView -ne 'default__true_'){throw "Street entry contract changed: $name"}
  $phase=$e.phases[0].Data
  if($phase.phaseName.'$value' -ne $name -or $phase.alwaysSpawned -ne 'default__false_' -or $phase.appearances.Count -ne 1 -or $phase.appearances[0].'$value' -ne $entry.appearance -or $phase.timePeriods.Count -ne 1){throw "Street phase contract changed: $name"}
  $period=$phase.timePeriods[0]
  if($period.hour -ne 'Day' -or $period.quantity -ne 1 -or $period.isSequence -ne 0 -or $period.categories.Count -ne 0 -or $period.markings.Count -ne 0 -or $period.spotNodeRefs.Count -ne 1 -or $period.spotNodeRefs[0].'$value' -ne $ref){throw "Street schedule contract changed: $name"}
  $node=$sector.nodes[$entry.node].Data
  $placements=@($sector.nodeData.Data|Where-Object {$_.NodeIndex -eq $entry.node})
  if($placements.Count -ne 1){throw "Street spot placement count changed: $name"}
  $placement=$placements[0]
  if($placement.QuestPrefabRefHash.'$value' -ne ($script:ZetatechStreetR11RefBase+$ref) -or [Math]::Abs($placement.Position.X-$entry.x) -gt 0.001 -or [Math]::Abs($placement.Position.Y-$entry.y) -gt 0.001 -or [Math]::Abs($placement.Position.Z-$entry.z) -gt 0.001){throw "Street spot identity/position changed: $name"}
  if($node.'$type' -ne 'worldAISpotNode' -or $node.isWorkspotInfinite -ne 1 -or $node.spot.Data.'$type' -ne 'AIActionSpot' -or $node.spot.Data.masterNodeRef.'$value' -ne '0' -or $node.lookAtTarget.'$value' -ne '0' -or $node.spot.Data.resource.DepotPath.'$value' -ne $entry.workspot){throw "Street independent workspot contract changed: $name"}
 }
}

function New-ZetatechStreetEntryNode([int]$id,[string]$action) {
 if($action -notin @('Reactivate','Deactivate')){throw 'Only exact street Reactivate/Deactivate is supported'}
 Assert-ZetatechStreetEntriesR11Sources
 $path=Join-Path $script:ZetatechStreetR11Root 'research\q307_extracted\raw\ep1\quest\main_quests\q307\phases\q307_06_viktor.questphase'
 if((Get-FileHash -LiteralPath $path).Hash -ne '5903042B905A11BF953980856BEA9A34CDBA9A348672F9BB1C24F71D7DDB209C'){throw 'Native community action precedent changed'}
 $source=Read-Cr2wFile $path
 $node=(Get-QuestNode $source.RootChunk.Graph.Chunk 30).DeepCopy()
 $node.Id=[uint16]$id
 foreach($socket in $node.Sockets){$socket.Chunk.Connections.Clear()}
 $templates=@($node.Actions|Where-Object {$_.Type.Chunk.GetType().Name -eq 'questCommunityTemplate_NodeType' -and $_.Type.Chunk.CommunityEntryName.ToString() -eq 'q307_alley_extra_01'})
 if($templates.Count -ne 1 -or $templates[0].Type.Chunk.SpawnerReference.ToString() -ne '#q307_com_alley' -or $templates[0].Type.Chunk.Action.ToString() -ne 'Reactivate'){throw 'Native alley action precedent changed'}
 $template=$templates[0].DeepCopy();$node.Actions.Clear()
 foreach($entry in $script:ZetatechStreetR11Entries){
  $one=$template.DeepCopy();$name='q307_alley_extra_'+$entry.id
  $one.Type.Chunk.CommunityEntryName=[WolvenKit.RED4.Types.CName]::op_Implicit($name)
  $one.Type.Chunk.CommunityEntryPhaseName=[WolvenKit.RED4.Types.CName]::op_Implicit($name)
  $one.Type.Chunk.Action=[WolvenKit.RED4.Types.Enums+populationSpawnerObjectCtrlAction]::$action
  [void]$node.Actions.Add($one)
 }
 return $node
}

function New-ZetatechStreetEntriesLoadingCondition([bool]$inverted=$false) {
 $condition=[WolvenKit.RED4.Types.questLogicalCondition]::new()
 $condition.Operation=if($inverted){[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR}else{[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND}
 foreach($entry in $script:ZetatechStreetR11Entries){
  $loaded=[WolvenKit.RED4.Types.questNodeLoadingCondition]::new()
  $loaded.ObjectRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($script:ZetatechStreetR11RefBase+'#q307_ws_alley_extra_'+$entry.id)
  $loaded.Inverted=$inverted
  [void](Add-RedHandle $condition.Conditions $loaded)
 }
 return $condition
}
