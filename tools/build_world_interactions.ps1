param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\b0_world_interactions\batch'
$source=Join-Path $WorkspaceRoot 'archive\b0_world_interactions\source'
$build=Join-Path $WorkspaceRoot 'build\WorldInteractions'
New-Item -ItemType Directory -Force -Path $audit,$source,$build|Out-Null
$python='C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $python (Join-Path $PSScriptRoot 'prepare_world_interaction_scenes.py');if($LASTEXITCODE -ne 0){throw 'Scene preparation failed'}
$options=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
$foundation=Read-Cr2wFile (Join-Path $WorkspaceRoot 'archive\b0_ordinary_mirrors_c5_red_dirt\source\towercontinued\ordinary_mirrors_c5_red_dirt\m42_gate.questphase')
$facts=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q305_johnny_scene_active=0;q115_point_of_no_return=0;PTFRBASE_Suspended=0;PTFRWORLD_Suspended=0}
function CloneFile($f){$j=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize([WolvenKit.Common.Conversion.RedFileDto]::new($f,$false),$script:options);return [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],$j,$script:options).Data}
function Guard($key){
 $g=[WolvenKit.RED4.Types.questLogicalCondition]::new();$g.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
 foreach($f in $script:facts.Keys){Add-RedHandle $g.Conditions (New-FactCondition $f $script:facts[$f] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
 foreach($suffix in 'Suspended','QuestOwns'){Add-RedHandle $g.Conditions (New-FactCondition ("PTFRWORLD_${key}_$suffix") 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
 if($key -eq 'Coaster'){Add-RedHandle $g.Conditions (New-FactCondition 'mq006_enable_repeatable_rollercoaster' 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::GreaterOrEqual))}
 return $g
}
function Link($g,$a,$socket,$b,$inputName='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $socket) (Get-QuestSocket (Get-QuestNode $g $b) $inputName))}
function Unlink($g,$a,$socket,$b,$inputName='In'){
 $s=Get-QuestSocket (Get-QuestNode $g $a) $socket;$d=Get-QuestSocket (Get-QuestNode $g $b) $inputName
 $m=@($s.Connections|Where-Object {[object]::ReferenceEquals($_.Chunk.Destination.Chunk,$d)});if($m.Count -ne 1){throw "Missing unique edge $a->$b"};$c=$m[0].Chunk
 foreach($sock in @($s,$d)){for($i=$sock.Connections.Count-1;$i -ge 0;$i--){if([object]::ReferenceEquals($sock.Connections[$i].Chunk,$c)){$sock.Connections.RemoveAt($i)}}}
}
function RemoveNodes($g,$ids){
 foreach($id in $ids){$n=Get-QuestNode $g $id
  foreach($s in $n.Sockets){foreach($handle in @($s.Chunk.Connections)){$c=$handle.Chunk;foreach($end in @($c.Source.Chunk,$c.Destination.Chunk)){for($i=$end.Connections.Count-1;$i -ge 0;$i--){if([object]::ReferenceEquals($end.Connections[$i].Chunk,$c)){$end.Connections.RemoveAt($i)}}}}}
  for($i=$g.Nodes.Count-1;$i -ge 0;$i--){if($g.Nodes[$i].Chunk.Id.ToString() -eq "$id"){$g.Nodes.RemoveAt($i)}}
 }
}
function Pause($id,$condition){$n=(Get-QuestNode $script:foundation.RootChunk.Graph.Chunk 1).DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};Set-RedHandleProperty $n Condition $condition;return $n}
function Resource($node,$property,$path){$rp=[WolvenKit.RED4.Types.ResourcePath]::op_Implicit($path);$node.$property=[Activator]::CreateInstance($node.GetType().GetProperty($property).PropertyType,[object[]]@($rp))}
function Counter($id,$name){$n=New-SetFactNode $id $name 1;$n.Type.Chunk.SetExactValue=$false;return $n}
$resources=[Collections.Generic.List[string]]::new();$records=[Collections.Generic.List[object]]::new()
$xl=[Collections.Generic.List[string]]::new();$xl.Add('# Audited post-Tower media, ride and memorial adapters.');$xl.Add('quest:');$xl.Add('  phases:')
function Save($f,$depot,$label){Write-Cr2wFile $f (Join-Path $script:source $depot);Export-Cr2wJson (Read-Cr2wFile (Join-Path $script:source $depot)) (Join-Path $script:audit ($label+'.json'));$script:resources.Add($depot)}
function Register($key,$owner){
 $gate=CloneFile $script:foundation;$g=$gate.RootChunk.Graph.Chunk
 if($gate.RootChunk.PhasePrefabs.Count -ne 0){throw 'Outer gate acquired prefab'}
 Set-RedHandleProperty (Get-QuestNode $g 1) Condition (Guard $key)
 Resource (Get-QuestNode $g 2) PhaseResource $owner
 $depot=("towercontinued\world_interactions\${key}_gate.questphase").ToLowerInvariant();Save $gate $depot ($key+'_gate')
 $crc=65535;foreach($b in [Text.Encoding]::UTF8.GetBytes($depot+':1')){$x=($crc -shr 8) -bxor $b;$x=$x -bxor ($x -shr 4);$crc=(($crc -shl 8) -bxor ($x -shl 12) -bxor ($x -shl 5) -bxor $x) -band 65535}
 $script:xl.Add("    - path: $depot");$script:xl.Add('      parent: ep1\quest\ep1.quest');$script:xl.Add('      input:');$script:xl.Add('        node: [1]');$script:xl.Add('        socket: Out')
 $script:records.Add(@{key=$key;gate=$depot;owner=$owner;registration_id=$crc})
}
# Radio: preserve every native scheduler/selection/outcome node. The ending
# board explicitly wrote radio_on=0; restore it once, not on every reload or
# every later quest-controlled shutdown. All later entries still respect it.
$radio=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\b0_world_interactions\extracted\raw\base\media\radio\radio_content.questphase')
Export-Cr2wJson $radio (Join-Path $audit 'Radio_original.json');$g=$radio.RootChunk.Graph.Chunk
Write-Host 'Radio: adding bounded bootstrap nodes'
Add-RedHandle $g.Nodes (New-ConditionNode 20 (New-FactCondition 'PTFRWORLD_Radio_Applied' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)))
Add-RedHandle $g.Nodes (New-SetFactNode 21 'PTFRWORLD_Radio_Applied' 1)
Add-RedHandle $g.Nodes (Counter 22 'PTFRWORLD_Radio_Starts')
Write-Host 'Radio: rewiring initial entry'
Unlink $g 0 Out 19;Unlink $g 19 Out 17 In1;Unlink $g 18 Out 17 In1
Link $g 0 Out 20;Link $g 20 True 19;Link $g 20 False 18;Link $g 19 Out 21;Link $g 21 Out 18;Link $g 18 Out 22;Link $g 22 Out 17 In1
Write-Host 'Radio: entry and termination guards'
$guard=Guard 'Radio';Add-RedHandle $guard.Conditions (Get-QuestNode $g 18).Condition.Chunk.DeepCopy();Set-RedHandleProperty (Get-QuestNode $g 18) Condition $guard
$child=(Get-QuestNode $g 17).PhaseGraph.Chunk;$stop=[WolvenKit.RED4.Types.questLogicalCondition]::new();$stop.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
Add-RedHandle $stop.Conditions (Get-QuestNode $child 12).Condition.Chunk.DeepCopy()
foreach($f in $facts.Keys){Add-RedHandle $stop.Conditions (New-FactCondition $f $facts[$f] ([WolvenKit.RED4.Types.Enums+EComparisonType]::NotEqual))}
foreach($suffix in 'Suspended','QuestOwns'){Add-RedHandle $stop.Conditions (New-FactCondition ("PTFRWORLD_Radio_$suffix") 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::NotEqual))}
Set-RedHandleProperty (Get-QuestNode $child 12) Condition $stop
Write-Host 'Radio: serializing controller'
$depot='towercontinued\world_interactions\radio_owner.questphase';Save $radio $depot 'Radio_owner';Register 'Radio' $depot
# Memorials: only outcome-driven display variants. Delete the scanner-triggered
# Johnny activation edge and both nodes, preserve every earned death reader.
$memorial=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\b0_world_interactions\extracted\raw\base\quest\main_quests\epilogue\q204\phases\q204_columbarium_holograms.questphase')
Export-Cr2wJson $memorial (Join-Path $audit 'Memorial_original.json');$g=$memorial.RootChunk.Graph.Chunk
RemoveNodes (Get-QuestNode $g 61).PhaseGraph.Chunk @(59,61)
Add-RedHandle $g.Nodes (New-SetFactNode 65 'PTFRWORLD_Memorial_Registered' 1)
foreach($id in 61,62,63,64){Unlink $g 0 Out $id In1;Link $g 65 Out $id In1
 $leaf=(Get-QuestNode $g $id).PhaseGraph.Chunk
 foreach($n in $leaf.Nodes){if($n.Chunk.GetType().Name -eq 'questPauseConditionNodeDefinition'){$guard=Guard 'Memorial';Add-RedHandle $guard.Conditions $n.Chunk.Condition.Chunk.DeepCopy();Set-RedHandleProperty $n.Chunk Condition $guard}}
}
Link $g 0 Out 65
$depot='towercontinued\world_interactions\memorial_owner.questphase';Save $memorial $depot 'Memorial_owner';Register 'Memorial' $depot
# Coaster: exact vanilla standalone action chain, no Jean introduction or NPC
# acquisition. Keep earned mq006_enable_repeatable_rollercoaster untouched.
$owner=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\b0_world_interactions\extracted\raw\base\quest\minor_quests\mq006\phases\mq006_repeatable_rollercoaster_controller.questphase')
Export-Cr2wJson $owner (Join-Path $audit 'Coaster_original.json');$g=$owner.RootChunk.Graph.Chunk
RemoveNodes $g @(19,20,21,22,23,24,26)
Unlink $g 0 Out 29 mq006_02_ride_standalone_in;Unlink $g 30 Out 29 mq006_02_ride_standalone_in
Add-RedHandle $g.Nodes (New-SetFactNode 31 'PTFRWORLD_Coaster_Registered' 1)
Add-RedHandle $g.Nodes (Pause 32 (Guard 'Coaster'))
Add-RedHandle $g.Nodes (Counter 33 'PTFRWORLD_Coaster_Requests')
Add-RedHandle $g.Nodes (Counter 34 'PTFRWORLD_Coaster_Returns')
Link $g 0 Out 31;Link $g 31 Out 32;Link $g 32 Out 33;Link $g 33 Out 29 mq006_02_ride_standalone_in
Unlink $g 29 mq006_02_ride_standalone_out 30;Link $g 29 mq006_02_ride_standalone_out 34;Link $g 34 Out 30;Link $g 30 Out 32
$ride=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\b0_world_interactions\dependencies\raw\base\quest\minor_quests\mq006\phases\mq006_rollercoaster_ride_controller.questphase')
Export-Cr2wJson $ride (Join-Path $audit 'Coaster_ride_original.json')
$refs=Get-Content (Join-Path $audit 'coaster_refs.json') -Raw|ConvertFrom-Json -AsHashtable
$j=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize([WolvenKit.Common.Conversion.RedFileDto]::new($ride,$false),$options)
$j=$j.Replace('mq006_ride_finished','PTFRWORLD_Coaster_Finished')
foreach($ref in $refs.Keys){$j=$j.Replace('"$value": "'+$ref+'"','"$value": "'+$refs[$ref]+'"')}
$ride=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],$j,$options).Data
$rideDepot='towercontinued\world_interactions\coaster_ride.questphase';Save $ride $rideDepot 'Coaster_ride';Resource (Get-QuestNode $g 28) PhaseResource $rideDepot
$j=Get-Content (Join-Path $audit 'coaster_scene_prepared.json') -Raw
$scene=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],$j,$options).Data
foreach($variant in 1,2){
 $wpj=Get-Content (Join-Path $audit "coaster_hands_${variant}_prepared.json") -Raw
 $wp=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],$wpj,$options).Data
 Save $wp "towercontinued\world_interactions\coaster_hands_${variant}.workspot" "Coaster_hands_$variant"
}
# Readable private acknowledgements isolate selection from native workspot start.
$sg=$scene.RootChunk.SceneGraph.Chunk
function SceneNode($id){return @($script:sg.Graph|Where-Object {$_.Chunk.NodeId.Id.ToString() -eq "$id"})[0].Chunk}
function SceneDest($id){$d=(SceneNode 593).OutputSockets[0].Destinations[0].DeepCopy();$d.NodeId.Id=[uint32]$id;$d.IsockStamp.Ordinal=[uint16]$(if($id -eq 561){0}else{1});return $d}
foreach($spec in @(@(1160,'PTFRWORLD_Coaster_HandsRequests'),@(1161,'PTFRWORLD_Coaster_HandsStarted'))){
 $sn=(SceneNode 593).DeepCopy();$sn.NodeId.Id=[uint32]$spec[0]
 Set-RedHandleProperty $sn QuestNode (Counter $spec[0] $spec[1]);$sn.OutputSockets[0].Destinations.Clear()
 if($spec[0] -eq 1160){$sn.OutputSockets[0].Destinations.Add((SceneDest 561))}
 Add-RedHandle $sg.Graph $sn
}
(SceneNode 557).OutputSockets[0].Destinations[0].NodeId.Id=[uint32]1160
(SceneNode 557).OutputSockets[0].Destinations[0].IsockStamp.Ordinal=[uint16]1
foreach($id in 558,559){
 $started=@((SceneNode $id).OutputSockets|Where-Object {$_.Stamp.Name.ToString() -eq '0' -and $_.Stamp.Ordinal.ToString() -eq '1'})
 if($started.Count -ne 1){throw 'Missing unique Work Started socket'}
 $started[0].Destinations.Add((SceneDest 1161))
}
$sceneDepot='towercontinued\world_interactions\coaster.scene';Save $scene $sceneDepot 'Coaster_scene';Resource (Get-QuestNode $g 29) SceneFile $sceneDepot
# Shared original main trigger prefab is required for track-end notifications;
# its only extra population spawner has spawnOnStart=0 and is never activated.
$originalQuest=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\b0_world_interactions\extended\raw\base\quest\minor_quests\mq006\mq006.questphase')
$owner.RootChunk.PhasePrefabs.Clear();foreach($p in $originalQuest.RootChunk.PhasePrefabs){$owner.RootChunk.PhasePrefabs.Add($p.DeepCopy())}
# The repeatable scene assumes mq006 already activated the real cart and hid
# the colocated broken-cart clue. A raw gate write does neither. Copy ONLY
# those original leaf actions, once per owner acquisition, not once per ride.
$setup=(Get-QuestNode $originalQuest.RootChunk.Graph.Chunk 50).PhaseGraph.Chunk
$spawn=(Get-QuestNode $setup 50).DeepCopy();$spawn.Id=[uint16]35
foreach($s in $spawn.Sockets){$s.Chunk.Connections.Clear()}
if($spawn.Actions.Count -ne 1 -or $spawn.Actions[0].Type.Chunk.GetType().Name -ne 'questSpawner_NodeType' -or $spawn.Actions[0].Type.Chunk.Action.ToString() -ne 'Activate'){throw 'Unexpected vanilla cart activation'}
$spawn.Actions[0].Type.Chunk.SpawnerReference=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($refs['#mq006_rollercoaster_cart_001'])
$hide=(Get-QuestNode $setup 51).DeepCopy();$hide.Id=[uint16]36
foreach($s in $hide.Sockets){$s.Chunk.Connections.Clear()}
$clueSector=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\b0_world_interactions\coaster_fix\raw\base\worlds\03_night_city\_compiled\default\exterior_-38_-31_0_0.streamingsector')
$clues=@($clueSector.RootChunk.NodeData.Data|Where-Object {$_.QuestPrefabRefHash.ToString().EndsWith('/#mq006_dvc_rollercoaster_cart_clue')})
if($clues.Count -ne 1 -or $hide.Type.Chunk.GetType().Name -ne 'questShowWorldNode_NodeType' -or $hide.Type.Chunk.Show.ToString() -notin @('False','0')){throw 'Unexpected vanilla clue hide action'}
$hide.Type.Chunk.ObjectRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($clues[0].QuestPrefabRefHash.ToString())
Add-RedHandle $g.Nodes $spawn;Add-RedHandle $g.Nodes $hide
Add-RedHandle $g.Nodes (New-SetFactNode 37 'PTFRWORLD_Coaster_CartSetupRequested' 1)
Unlink $g 0 Out 31;Link $g 0 Out 35;Link $g 35 Out 36;Link $g 36 Out 37;Link $g 37 Out 31
$depot='towercontinued\world_interactions\coaster_owner.questphase';Save $owner $depot 'Coaster_owner';Register 'Coaster' $depot
$ep1=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\ep1.quest');foreach($r in $records){if(@($ep1.RootChunk.Graph.Chunk.Nodes|Where-Object {$_.Chunk.Id.ToString() -eq "$($r.registration_id)"}).Count){throw 'Parent ID collision'}}
$xlPath=Join-Path $WorkspaceRoot 'archive\b0_world_interactions\TowerContinued_WorldInteractions.archive.xl';[IO.File]::WriteAllLines($xlPath,$xl,[Text.UTF8Encoding]::new($false))
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load();$archive=Join-Path $build 'TowerContinued_WorldInteractions.archive';$stream=[IO.File]::Create($archive)
try{$writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new());if(-not $writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hash,[ref]$packed).ToString() -ne 'NoError'){throw 'Reopen failed'}
if(@(Compare-Object @($resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Packed manifest differs'}
Copy-Item $xlPath ($archive+'.xl') -Force
$manifest=@{status='BUILT_AUTOMATIC_CANDIDATES';adapters=@($records);resources=@($resources);guards=$facts;sha256=(Get-FileHash $archive).Hash;xl_sha256=(Get-FileHash ($archive+'.xl')).Hash;vanilla_replacements=@();new_polling=$false;pending=@('gig-radio coordination','shooting range activation','paid fortune device binding','housing entitlement','relationship-home non-mirror services','altar world action');live_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($manifest|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false));$manifest|ConvertTo-Json -Depth 4
