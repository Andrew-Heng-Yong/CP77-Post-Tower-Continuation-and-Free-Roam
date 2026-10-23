param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$prior=Get-Content (Join-Path $audit 'variants_r5_manifest.json') -Raw|ConvertFrom-Json
$crowd=Get-Content (Join-Path $audit 'r6_wall_nav_crowd_manifest.json') -Raw|ConvertFrom-Json
$out=Join-Path $WorkspaceRoot 'build\MistyViktorRepairR6'
$source=Join-Path $out 'source'
New-Item -ItemType Directory -Force $source|Out-Null
$resources=[Collections.Generic.List[string]]::new()
foreach($depot in $prior.resources){
 $src=Join-Path $WorkspaceRoot ('build\MistyViktorVariantsR5\source\'+$depot)
 $dst=Join-Path $source $depot
 New-Item -ItemType Directory -Force (Split-Path -Parent $dst)|Out-Null
 Copy-Item -LiteralPath $src -Destination $dst -Force
 $resources.Add($depot)
}
$crowdResources=@('towercontinued\misty_viktor_world\crowd_alley_r6.streamingsector','towercontinued\misty_viktor_world\crowd_alley_r6.streamingblock')
foreach($depot in $crowdResources){
 $src=Join-Path $WorkspaceRoot ('build\MistyViktorCrowdR6\source\'+$depot)
 Copy-Item -LiteralPath $src -Destination (Join-Path $source $depot) -Force
 $resources.Add($depot)
}
$phaseDepot='towercontinued\misty_viktor_world\shell_optin.questphase'
$phase=Read-Cr2wFile (Join-Path $source $phaseDepot)
$graph=$phase.RootChunk.Graph.Chunk
if($graph.Nodes.Count -ne 22){throw 'R5 native graph drifted'}
foreach($node in $graph.Nodes){foreach($socket in $node.Chunk.Sockets){$socket.Chunk.Connections.Clear()}}
$revision=(Get-QuestNode $graph 18).Type.Chunk
if($revision.FactName.ToString() -ne 'PTFRMV_Revision' -or $revision.Value.ToString() -ne '5'){throw 'R5 revision drifted'}
$revision.Value=[int32]6
# One original ordinary DataTerm and its proxy, hidden only for final-cutscene
# composition. Leave the terminal restored on opt-out; do not clone it or write
# fast-travel registration/discovery or device power state.
$terminal=(Get-QuestNode $graph 21).DeepCopy();$terminal.Id=[uint16]22
$terminal.Type.Chunk.Params[0].PrefabNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit('$/03_night_city/c_watson/little_china/#little_china_data_terminals')
$terminal.Type.Chunk.Params[0].VariantStates[0].Name=[WolvenKit.RED4.Types.CName]::op_Implicit('q307_fast_travel_terminal_cutscene_hide')
$terminal.Type.Chunk.Params[0].VariantStates[0].Show=$true
Add-RedHandle $graph.Nodes $terminal
# Native local crowd-null enable/disable precedent, never global crowd control.
$cleanup=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\main_quests\q307\phases\q307_cleanup.questphase')
$policeOwner='$/03_night_city/c_watson/little_china/loc_mystic_mistys_ripperdoc_prefabH2DWJJI/#loc_mystic_mistys_ripperdoc_gameplay'
# Cleanup authors both OFF and then ON for the old police dressing. Suppress
# only its 19 reviewed placements while our overlay is owned; restore ON with
# the existing guarded manual opt-out. Do not disable its separate quest prefab.
foreach($spec in @(@(21,$false),@(16,$true))){
 $candidates=@((Get-QuestNode $cleanup.RootChunk.Graph.Chunk 22).Type.Chunk.Params|Where-Object {$_.PrefabNodeRef.ToString() -eq '#loc_mystic_mistys_ripperdoc_gameplay'})
 $match=@($candidates|Where-Object {@($_.VariantStates|Where-Object {$_.Name.ToString() -eq 'q001_holo_scene' -and (($_.Show.ToString() -in @('True','1')) -eq [bool]$spec[1])}).Count -eq 1})
 if($match.Count -ne 1){throw 'Ambiguous police dressing precedent'}
 $param=$match[0].DeepCopy()
 $state=@($param.VariantStates|Where-Object {$_.Name.ToString() -eq 'q001_holo_scene'})[0].DeepCopy()
 $param.VariantStates.Clear();[void]$param.VariantStates.Add($state)
 $param.PrefabNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($policeOwner)
 [void](Get-QuestNode $graph $spec[0]).Type.Chunk.Params.Add($param)
}
$lightingOwner='$/03_night_city/c_watson/little_china/loc_mystic_mistys_ripperdoc_prefabH2DWJJI/#loc_mystic_mistys_ripperdoc_lightning'
$lighting=@((Get-QuestNode $cleanup.RootChunk.Graph.Chunk 22).Type.Chunk.Params|Where-Object {$_.PrefabNodeRef.ToString() -eq '#loc_mystic_mistys_ripperdoc_lightning'})
if($lighting.Count -ne 1 -or $lighting[0].VariantStates.Count -ne 2 -or $lighting[0].VariantStates[0].Name.ToString() -ne 'Q307_VV' -or $lighting[0].VariantStates[1].Name.ToString() -ne 'V_Default'){throw 'Original clinic lighting pair drifted'}
# The visible candles also belong to V_Default exterior lighting. Switch the
# authored local pair together so removal does not leave the clinic unlit.
foreach($spec in @(@(21,$true),@(16,$false))){
 $param=$lighting[0].DeepCopy()
 $param.PrefabNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($lightingOwner)
 $param.VariantStates[0].Show=[bool]$spec[1]
 $param.VariantStates[1].Show=-not [bool]$spec[1]
 [void](Get-QuestNode $graph $spec[0]).Type.Chunk.Params.Add($param)
}
$crowdRef='$/03_night_city/#PTFRMV_TowerStreetCrowdBlocker'
foreach($spec in @(@(23,$true),@(24,$false))){
 $node=(Get-QuestNode $cleanup.RootChunk.Graph.Chunk 26).DeepCopy()
 if($node.Type.Chunk.GetType().Name -ne 'questCrowdManagerNodeType_EnableNullArea' -or $node.Type.Chunk.AreaReference.ToString() -ne '#q307_cna_alley'){throw 'Vanilla crowd precedent drifted'}
 $node.Id=[uint16]$spec[0]
 foreach($socket in $node.Sockets){$socket.Chunk.Connections.Clear()}
 $node.Type.Chunk.AreaReference=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($crowdRef)
 $node.Type.Chunk.Enable=[bool]$spec[1]
 Add-RedHandle $graph.Nodes $node
}
# Independent event-driven crowd branch: the node must be resident, not merely
# requested by the streaming variant. Ownership loss cancels both waits.
# Re-arm on actual unload/reload; no timer, polling or blind repeated inserts.
function Loaded([bool]$inverted){
 $c=[WolvenKit.RED4.Types.questNodeLoadingCondition]::new()
 $c.ObjectRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($script:crowdRef)
 $c.Inverted=$inverted
 return $c
}
function Logic($operation,$conditions){
 $c=[WolvenKit.RED4.Types.questLogicalCondition]::new()
 $c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::$operation
 foreach($child in $conditions){Add-RedHandle $c.Conditions $child}
 return $c
}
function EntryGuard{return (Get-QuestNode $script:graph 2).Condition.Chunk.DeepCopy()}
function StopGuard{return (Get-QuestNode $script:graph 5).Condition.Chunk.DeepCopy()}
function Ready{return Logic 'AND' @((Loaded $false),(EntryGuard))}
function Pause($id,$condition){
 $n=(Get-QuestNode $script:graph 2).DeepCopy();$n.Id=[uint16]$id
 foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}
 Set-RedHandleProperty $n Condition $condition
 return $n
}
Add-RedHandle $graph.Nodes (Pause 25 (Logic 'OR' @((Ready),(StopGuard))))
Add-RedHandle $graph.Nodes (New-ConditionNode 26 (Ready))
Add-RedHandle $graph.Nodes (Pause 27 (Logic 'OR' @((Loaded $true),(StopGuard))))
Add-RedHandle $graph.Nodes (New-ConditionNode 28 (EntryGuard))
$request=New-SetFactNode 29 'PTFRMV_CrowdRequests' 1
$request.Type.Chunk.SetExactValue=$false
Add-RedHandle $graph.Nodes $request
$edges=@(@(0,'Out',1),@(1,'Out',18),@(18,'Out',2),@(2,'Out',3),@(3,'Out',21),@(21,'Out',10),@(10,'Out',19),@(19,'Out',22),@(22,'Out',11),@(11,'Out',12),@(12,'Out',8),@(8,'Out',4),@(4,'Out',5),@(5,'Out',24),@(24,'Out',20),@(20,'Out',13),@(13,'True',14),@(14,'Out',15),@(15,'Out',16),@(16,'Out',17),@(17,'Out',6),@(13,'False',6),@(6,'Out',9),@(9,'Out',7),@(7,'Out',2),@(19,'Out',25),@(25,'Out',26),@(26,'True',23),@(23,'Out',29),@(29,'Out',27),@(27,'Out',28),@(28,'True',25))
foreach($e in $edges){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $e[0]) $e[1]) (Get-QuestSocket (Get-QuestNode $graph $e[2]) 'In'))}
Write-Cr2wFile $phase (Join-Path $source $phaseDepot)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $phaseDepot)) (Join-Path $audit 'repair_r6_phase.json')
Copy-Item -LiteralPath (Join-Path $audit 'r6_wall_nav_crowd_sector.json') -Destination (Join-Path $audit 'repair_r6_crowd.json') -Force
Copy-Item -LiteralPath (Join-Path $audit 'r6_wall_nav_crowd_block.json') -Destination (Join-Path $audit 'repair_r6_crowd_block.json') -Force
$xl=Get-Content ($prior.archive+'.xl')
$expected='    - towercontinued\misty_viktor_world\street.streamingblock'
if(@($xl|Where-Object {$_ -eq $expected}).Count -ne 1){throw 'R5 XL drifted'}
$xl=@($xl|ForEach-Object {$_;if($_ -eq $expected){'    - towercontinued\misty_viktor_world\crowd_alley_r6.streamingblock'}})
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$archive=Join-Path $out 'TowerContinued_MistyViktorShellOptIn.archive'
$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'R6 pack failed'}}finally{$stream.Dispose()}
[IO.File]::WriteAllLines(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hash,[ref]$packed).ToString() -ne 'NoError'){throw 'R6 reopen failed'}
if(@(Compare-Object @($resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'R6 resource scope mismatch'}
$manifest=[ordered]@{status='BUILT_R6_LOCAL_REPAIR_NOT_INSTALLED_OR_LIVE';archive=$archive;sha256=(Get-FileHash $archive).Hash;xl_sha256=(Get-FileHash ($archive+'.xl')).Hash;resources=@($resources);guards=$prior.guards;edges=$edges;crowd_ref=$crowdRef;crowd_source_node=62;crowd_enabled_by_default=$false;crowd_readiness='questNodeLoadingCondition';crowd_rearm='native node unload/load event conditions';crowd_request_counter='PTFRMV_CrowdRequests';terminal_owner='$/03_night_city/c_watson/little_china/#little_china_data_terminals';terminal_variant='q307_fast_travel_terminal_cutscene_hide';terminal_retained_on_stop=$true;police_owner=$policeOwner;police_variant='q001_holo_scene';police_restore_on_guarded_stop=$true;police_member_count=19;lighting_owner=$lightingOwner;lighting_default_members=267;lighting_tower_members=270;lighting_restore_on_guarded_stop=$true;private_sector_count=15;private_block_count=3;actors=0;native_scene_starts=0;story_fact_writes=0;live_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'repair_r6_manifest.json'),($manifest|ConvertTo-Json -Depth 7))
[pscustomobject]@{status=$manifest.status;sha256=$manifest.sha256;resources=$resources.Count}|ConvertTo-Json
