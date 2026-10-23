param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\afterlife_world\interactions_r8'
$out=Join-Path $WorkspaceRoot 'build\AfterlifeInteractionsR8'
$source=Join-Path $out 'source'
New-Item -ItemType Directory -Force $out,$source|Out-Null
$prefix='towercontinued\afterlife_interactions_r8\'
$eRef='$/03_night_city/#PTFRAL1_Emmerick'
$rRef='$/03_night_city/#PTFRAF1_RogueCommunity'
$startRef='$/03_night_city/#PTFRAL8_EmmerickStart'
$triggerRef='$/03_night_city/#PTFRAL8_EntranceTrigger'
$hashes=[ordered]@{}
function Ref([string]$s){[WolvenKit.RED4.Types.NodeRef]::op_Implicit($s)}
function Name([string]$s){[WolvenKit.RED4.Types.CName]::op_Implicit($s)}
function ReadWorld([string]$p){$script:hashes[$p]=(Get-FileHash -LiteralPath $p).Hash;$s=[IO.File]::OpenRead($p);try{$r=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($s);$r.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])});$f=$null;if($r.ReadFile([ref]$f,$true).ToString() -ne 'NoError'){throw "Parse failed $p"};return $f}finally{$s.Dispose()}}
function Resource($o,[string]$property,[string]$path){$t=$o.GetType().GetProperty($property).PropertyType;$o.$property=[Activator]::CreateInstance($t,[object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($path)))}
function ClearSockets($n){foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}}
function Link($g,[int]$a,[string]$s,[int]$b,[string]$dest='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $s) (Get-QuestSocket (Get-QuestNode $g $b) $dest))}
function Put($g,$n){Add-RedHandle $g.Nodes $n}
function Save($f,[string]$rel){Write-Cr2wFile $f (Join-Path $script:source $rel);Export-Cr2wJson (Read-Cr2wFile (Join-Path $script:source $rel)) (Join-Path $script:audit ([IO.Path]::GetFileName($rel)+'.json'))}
$r7=Get-Content (Join-Path $WorkspaceRoot 'research\afterlife_world\emmerick_r7\manifest.json') -Raw|ConvertFrom-Json
$resources=[Collections.Generic.List[string]]::new()
foreach($rel in $r7.resources){$p=Join-Path $r7.source_root $rel;$hashes[$p]=(Get-FileHash $p).Hash;$to=Join-Path $source $rel;New-Item -ItemType Directory -Force (Split-Path $to)|Out-Null;Copy-Item -LiteralPath $p -Destination $to;$resources.Add($rel)}
$world=ReadWorld (Join-Path $WorkspaceRoot 'research\afterlife_world\patron_world_sources\raw\base\worlds\03_night_city\_compiled\default\quest_1d80ac67f39864eb.streamingsector')
$original=ReadWorld (Join-Path $WorkspaceRoot 'research\phase2b_p4\staging_scan\ep1_1_nightcity\raw\base\worlds\03_night_city\_compiled\default\always_loaded_1.streamingsector')
$spotsRel='towercontinued\afterlife_r1\patrons_spots.streamingsector';$regRel='towercontinued\afterlife_r1\patrons_registry.streamingsector'
$spots=ReadWorld (Join-Path $r7.source_root $spotsRel);$reg=ReadWorld (Join-Path $r7.source_root $regRel)
if($spots.RootChunk.Nodes.Count -ne 79){throw 'Unexpected R7 spot count'}
foreach($spec in @(@{node=84;ref=$startRef;name='PTFRAL8_EmmerickStart'},@{node=64;ref=$triggerRef;name='PTFRAL8_EntranceTrigger'})){
 $n=$world.RootChunk.Nodes[$spec.node].Chunk.DeepCopy();$d=@($world.RootChunk.NodeData.Data|Where-Object {$_.NodeIndex.ToString() -eq $spec.node.ToString()})[0].DeepCopy();$oldHash=$d.QuestPrefabRefHash.GetRedHash().ToString()
 $n.SourcePrefabHash=[uint64]0;$n.DebugName=Name $spec.name;$idx=$spots.RootChunk.Nodes.Count
 $d.Id=[uint64](760000000008000+$idx);$d.NodeIndex=[uint16]$idx;$d.QuestPrefabRefHash=Ref $spec.ref;$d.UkHash1=Ref ''
 Add-RedHandle $spots.RootChunk.Nodes $n;[void]$spots.RootChunk.NodeData.Data.Add($d);[void]$spots.RootChunk.NodeRefs.Add($d.QuestPrefabRefHash)
 if($spec.node -eq 84){
  $pds=@($original.RootChunk.Nodes[3256].Chunk.WorkspotsPersistentData|Where-Object {$_.GlobalNodeId.Hash.ToString() -eq $oldHash});if($pds.Count -ne 1){throw 'Ambiguous entrance persistent descriptor'}
  $pd=$pds[0].DeepCopy();$pd.GlobalNodeId.Hash=(Ref $startRef).GetRedHash();[void]$reg.RootChunk.Nodes[0].Chunk.WorkspotsPersistentData.Add($pd)
 }
}
$item=$reg.RootChunk.Nodes[0].Chunk.CommunitiesData[1]
if($item.CommunityId.EntityId.Hash.ToString() -ne (Ref $eRef).GetRedHash().ToString()){throw 'Wrong private actor'}
$phase=$item.Template.Chunk.Entries[0].Chunk.Phases[0].DeepCopy();$phase.Chunk.PhaseName=Name 'PTFRAL8_Entrance';$phase.Chunk.TimePeriods[0].SpotNodeRefs[0]=Ref $startRef
[void]$item.Template.Chunk.Entries[0].Chunk.Phases.Add($phase)
$area=$reg.RootChunk.Nodes[2].Chunk.Area.Chunk.EntriesData[0]
$ap=$area.PhasesData[0].DeepCopy();$ap.EntryPhaseName=Name 'PTFRAL8_Entrance';$ap.TimePeriodsData[0].SpotNodeIds[0].Hash=(Ref $startRef).GetRedHash();[void]$area.PhasesData.Add($ap)
Save $reg $regRel;Save $spots $spotsRel

# Native source nodes; all actor actions below address existing private entries.
$routine=ReadWorld (Join-Path $audit 'sources\raw\base\quest\main_quests\part1\q103\scenes\q103_02_afterlife_intro.scene')
$eOwner=ReadWorld (Join-Path $WorkspaceRoot 'research\afterlife_world\patrons_sources\raw\base\quest\main_quests\part1\q103\phases\q103_emmerick_routine.questphase')
$eGraph=(Get-QuestNode $eOwner.RootChunk.Graph.Chunk 24).PhaseGraph.Chunk
$default=ReadWorld (Join-Path $WorkspaceRoot 'research\phase2b_p4\vendor_owner\raw\base\quest\default_dialogs.questphase')
$rGraph=(Get-QuestNode (Get-QuestNode (Get-QuestNode $default.RootChunk.Graph.Chunk 3).PhaseGraph.Chunk 14).PhaseGraph.Chunk 4).PhaseGraph.Chunk
$population=ReadWorld (Join-Path $r7.source_root 'towercontinued\afterlife_r1\population.questphase')
$communityAction=(Get-QuestNode $population.RootChunk.Graph.Chunk 622).Actions[1].DeepCopy()
function Activate([int]$id,[string]$phaseName){$n=(Get-QuestNode $script:population.RootChunk.Graph.Chunk 622).DeepCopy();$n.Id=[uint16]$id;ClearSockets $n;$n.Actions.Clear();$a=$script:communityAction.DeepCopy();$a.Type.Chunk.Action=[WolvenKit.RED4.Types.Enums+populationSpawnerObjectCtrlAction]::Activate;$a.Type.Chunk.CommunityEntryPhaseName=Name $phaseName;[void]$n.Actions.Add($a);return $n}

function SceneNode($root,[int]$id){$found=@($root.SceneGraph.Chunk.Graph|Where-Object {$_.Chunk.NodeId.Id.ToString() -eq $id.ToString()});if($found.Count -ne 1){throw "Scene node $id ambiguous"};return $found[0].Chunk}
function Redirect($root,[int]$from,[int]$old,[int]$new,[uint16]$ordinal=0){$n=SceneNode $root $from;$count=0;foreach($s in $n.OutputSockets){foreach($d in $s.Destinations){if($d.NodeId.Id.ToString() -eq $old.ToString()){$d.NodeId.Id=[uint32]$new;$d.IsockStamp.Name=[uint16]0;$d.IsockStamp.Ordinal=$ordinal;$count++}}};if($count -ne 1){throw "Redirect $from->$old matched $count"}}
function PruneScene($root,[int]$start,[int]$end){
 $seen=[Collections.Generic.HashSet[int]]::new();$queue=[Collections.Generic.Queue[int]]::new();$queue.Enqueue($start)
 while($queue.Count){$id=$queue.Dequeue();if(-not $seen.Add($id)){continue};foreach($s in (SceneNode $root $id).OutputSockets){foreach($d in $s.Destinations){$queue.Enqueue([int]$d.NodeId.Id.ToString())}}}
 for($i=$root.SceneGraph.Chunk.Graph.Count-1;$i -ge 0;$i--){if(-not $seen.Contains([int]$root.SceneGraph.Chunk.Graph[$i].Chunk.NodeId.Id.ToString())){$root.SceneGraph.Chunk.Graph.RemoveAt($i)}}
 foreach($name in @('StartNodes','EndNodes')){$list=$root.SceneGraph.Chunk.$name;for($i=$list.Count-1;$i -ge 0;$i--){if($list[$i].Id.ToString() -ne $(if($name -eq 'StartNodes'){$start.ToString()}else{$end.ToString()})){$list.RemoveAt($i)}}}
 foreach($name in @('EntryPoints','ExitPoints')){$list=$root.$name;for($i=$list.Count-1;$i -ge 0;$i--){if($list[$i].NodeId.Id.ToString() -ne $(if($name -eq 'EntryPoints'){$start.ToString()}else{$end.ToString()})){$list.RemoveAt($i)}}}
 return @($seen|Sort-Object)
}
function BindActor($actor,[string]$ref,[string]$entry){$actor.AcquisitionPlan=[WolvenKit.RED4.Types.Enums+scnEntityAcquisitionPlan]::community;$actor.CommunityParams.Reference=Ref $ref;$actor.CommunityParams.EntryName=Name $entry;$actor.SpawnSetParams.Reference=Ref '';$actor.SpawnSetParams.EntryName=Name 'None'}
$eScene=$routine;$er=$eScene.RootChunk
BindActor $er.Actors[0] $eRef 'emmerick'
(SceneNode $er 445).QuestNode.Chunk.EntityReference.Reference=Ref $eRef
Set-RedHandleProperty (SceneNode $er 447) QuestNode (Activate 447 'q005_emmerick_bouncer')
$eNodes=PruneScene $er 440 449
if($eNodes.Count -ne 5){throw 'Entrance route scope drift'}
$eDepot=$prefix+'emmerick.scene';Save $eScene $eDepot;$resources.Add($eDepot)

$rScene=ReadWorld (Join-Path $WorkspaceRoot 'research\afterlife_world\rogue_sources\raw\base\quest\secondary_characters\default_dialogues\rogue_default.scene')
$rr=$rScene.RootChunk;$rDepot=$prefix+'rogue.scene'
BindActor $rr.Actors[0] $rRef 'rogue';$rr.Actors.RemoveAt(1)
# Local-only branch selection: retain false/local routes and remove holo teardown.
Redirect $rr 4 266 268
Redirect $rr 276 271 273
Redirect $rr 4 228 2
foreach($id in @(140,142,144,147,154,157)){(SceneNode $rr $id).QuestNode.Chunk.EntityReference.Reference=Ref $rRef}
Resource (SceneNode $rr 235).QuestNode.Chunk.Type.Chunk 'SceneFile' $rDepot
$rNodes=PruneScene $rr 1 2
for($i=$rr.InterruptionScenarios.Count-1;$i -ge 0;$i--){if($rr.InterruptionScenarios[$i].Id.Id.ToString() -ne '0'){$rr.InterruptionScenarios.RemoveAt($i)}}
foreach($h in $rr.SceneGraph.Chunk.Graph){$n=$h.Chunk
 if($n.GetType().Name -eq 'scnChoiceNode'){$n.ForceAttachToScreenCondition=$null}
 if($n.GetType().Name -eq 'scnSectionNode'){
  for($i=$n.Events.Count-1;$i -ge 0;$i--){if(([uint32]$n.Events[$i].Chunk.ExecutionTagFlags.ToString() -band 1) -ne 0){$n.Events.RemoveAt($i)}}
  for($i=$n.ActorBehaviors.Count-1;$i -ge 0;$i--){if($n.ActorBehaviors[$i].ActorId.Id.ToString() -eq '1'){$n.ActorBehaviors.RemoveAt($i)}}
 }
}
$rr.ExitPoints[0].Name=Name 'local_out'
Save $rScene $rDepot;$resources.Add($rDepot)

# Guarded native owners. Terminating child phases cancel scene execution on
# guard/safety loss; runtime never directly starts scenes or changes population.
$guardSource=Get-Content (Join-Path $WorkspaceRoot 'research\afterlife_world\manifest.json') -Raw|ConvertFrom-Json
$guards=[ordered]@{};foreach($p in $guardSource.guards.psobject.Properties){$guards[$p.Name]=[int]$p.Value}
$guards['PTFRAL1_WorldApplied']=1;$guards['PTFRAL8_Suspended']=0;$guards['PTFRAL8_DriverReady']=1
function Fact([string]$n,[int]$v,[bool]$inverse=$false){New-FactCondition $n $v $(if($inverse){[WolvenKit.RED4.Types.Enums+EComparisonType]::NotEqual}else{[WolvenKit.RED4.Types.Enums+EComparisonType]::Equal})}
function Logic([string]$op,$cs){$c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::$op;foreach($x in $cs){Add-RedHandle $c.Conditions $x};return $c}
function Guard([bool]$inverse=$false){Logic $(if($inverse){'OR'}else{'AND'}) @($script:guards.Keys|ForEach-Object {Fact $_ $script:guards[$_] $inverse})}
function Loaded([string]$ref,[bool]$inverse=$false){$c=[WolvenKit.RED4.Types.questNodeLoadingCondition]::new();$c.ObjectRef=Ref $ref;$c.Inverted=$inverse;return $c}
function Trigger([bool]$inside){$c=(Get-QuestNode $script:eGraph 16).Condition.Chunk.DeepCopy();$c.TriggerAreaRef=Ref $script:triggerRef;$c.Type=if($inside){[WolvenKit.RED4.Types.Enums+questTriggerConditionType]::IsInside}else{[WolvenKit.RED4.Types.Enums+questTriggerConditionType]::IsOutside};return $c}
function Pause([int]$id,$c){$n=(Get-QuestNode $script:population.RootChunk.Graph.Chunk 620).DeepCopy();$n.Id=[uint16]$id;ClearSockets $n;Set-RedHandleProperty $n Condition $c;return $n}
function Counter([int]$id,[string]$name){$n=New-SetFactNode $id $name 1;$n.Type.Chunk.SetExactValue=$false;return $n}
function Common([string]$who,[bool]$inverse=$false){$ready=if($who -eq 'E'){'PTFRAL1_Actor26Ready'}else{'PTFRAL1_Actor27Ready'};$cs=@((Guard $inverse),(Fact $ready 1 $inverse),(Fact ('PTFRAL8_'+$who+'Continue') 1 $inverse));if($who -eq 'E'){$cs+=@((Loaded $script:startRef $inverse),(Loaded $script:triggerRef $inverse),(Loaded '$/03_night_city/#PTFRAL1_PatronSpot78' $inverse))}else{$cs+=@((Loaded '$/03_night_city/#PTFRAF1_RogueBooth' $inverse),(Fact 'q116_rogue_dead' 0 $inverse),(New-FactCondition 'rogue_default_on' 0 $(if($inverse){[WolvenKit.RED4.Types.Enums+EComparisonType]::LessOrEqual}else{[WolvenKit.RED4.Types.Enums+EComparisonType]::Greater})))};Logic $(if($inverse){'OR'}else{'AND'}) $cs}
function MakePhase([string]$who,[int]$id){
 $phase=(Get-QuestNode $script:eOwner.RootChunk.Graph.Chunk 21).DeepCopy();$phase.Id=[uint16]$id;ClearSockets $phase;$phase.PhaseInstancePrefabs.Clear()
 $g=$phase.PhaseGraph.Chunk;$g.Nodes.Clear()
 Put $g (New-InputNode 0 'In1');$output=[WolvenKit.RED4.Types.questOutputNodeDefinition]::new();$output.Id=[uint16]1;$output.SocketName=Name 'Out1';$output.Type=[WolvenKit.RED4.Types.Enums+questExitType]::Terminating;[void](New-QuestSocket $output In ([WolvenKit.RED4.Types.Enums+questSocketType]::Input));Put $g $output
 $scene=if($who -eq 'E'){(Get-QuestNode $script:eGraph 17).DeepCopy()}else{(Get-QuestNode $script:rGraph 3).DeepCopy()};$scene.Id=[uint16]4;ClearSockets $scene
 Resource $scene 'SceneFile' $(if($who -eq 'E'){$script:eDepot}else{$script:rDepot})
 # All retained scene workspots/root-motion play at actor location. Use the
 # vanilla Rogue around-player tag location, no quest prefab ownership.
 $scene.SceneLocation=(Get-QuestNode $script:rGraph 3).SceneLocation.DeepCopy()
 if($who -eq 'R'){
  $scene.Sockets.Clear();[void](New-QuestSocket $scene CutDestination ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination));[void](New-QuestSocket $scene in ([WolvenKit.RED4.Types.Enums+questSocketType]::Input));[void](New-QuestSocket $scene local_out ([WolvenKit.RED4.Types.Enums+questSocketType]::Output))
 }
 Put $g $scene
 $start=Logic 'AND' @((Common $who),(Fact ('PTFRAL8_'+$who+'Start') 1));if($who -eq 'E'){$start=Logic 'AND' @($start,(Trigger $true))}
 Put $g (Pause 2 $start);Put $g (New-ConditionNode 3 $start);Put $g (Pause 5 (Common $who $true));Put $g (New-SetFactNode 6 ('PTFRAL8_'+$who+'Active') 1);Put $g (Counter 7 ('PTFRAL8_'+$who+'Requests'))
 Link $g 0 Out 2;Link $g 0 Out 5;Link $g 2 Out 3;Link $g 3 False 2;Link $g 3 True 6;Link $g 6 Out 7;Link $g 7 Out 4 $(if($who -eq 'E'){'emmerick_entrance'}else{'in'});Link $g 5 Out 1;Link $g 4 $(if($who -eq 'E'){'emmerick_entrance_out'}else{'local_out'}) 1
 return $phase
}
$owner=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$owner.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
$g=[WolvenKit.RED4.Types.questGraphDefinition]::new();Set-RedHandleProperty $owner Graph $g
Put $g (New-InputNode 0 In1);Put $g (New-SetFactNode 1 PTFRAL8_Registered 1);Link $g 0 Out 1
foreach($spec in @(@{who='E';base=100},@{who='R';base=200})){
 $who=$spec.who;$b=$spec.base
 Put $g (New-SetFactNode $b ('PTFRAL8_'+$who+'Active') 0)
 $condition=Logic AND @((Common $who),(Fact ('PTFRAL8_'+$who+'Available') 1));if($who -eq 'E'){$condition=Logic AND @($condition,(Trigger $false))}
 Put $g (Pause ($b+1) $condition);Put $g (New-ConditionNode ($b+2) $condition)
 if($who -eq 'E'){Put $g (Activate ($b+3) 'PTFRAL8_Entrance')}else{Put $g (New-SetFactNode ($b+3) 'PTFRAL8_RBound' 1)}
 Put $g (MakePhase $who ($b+4));Put $g (New-SetFactNode ($b+5) ('PTFRAL8_'+$who+'Active') 0)
 # Completion waits for departure before another approach; invalid ownership
 # may re-arm only through the full guarded entry condition above.
 # Transient permission/scene-release changes must not replay dialogue after
 # goodbye. Require real departure, unload or policy shutdown to re-arm.
 $depart=if($who -eq 'E'){Logic OR @((Trigger $false),(Loaded $script:triggerRef $true),(Guard $true))}else{Logic OR @((Fact 'PTFRAL8_RDeparted' 1),(Loaded '$/03_night_city/#PTFRAF1_RogueBooth' $true),(Guard $true))}
 Put $g (Pause ($b+6) $depart)
 Link $g 1 Out $b;Link $g $b Out ($b+1);Link $g ($b+1) Out ($b+2);Link $g ($b+2) False ($b+1);Link $g ($b+2) True ($b+3);Link $g ($b+3) Out ($b+4) In1;Link $g ($b+4) Out1 ($b+5);Link $g ($b+5) Out ($b+6);Link $g ($b+6) Out ($b+1)
}
$f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$owner;$depot=$prefix+'owner.questphase';Save $f $depot;$resources.Add($depot)
$archive=Join-Path $out 'TowerContinued_AfterlifeR1.archive'
$xlSource=Join-Path $WorkspaceRoot 'build\AfterlifePopulationR2\TowerContinued_AfterlifeR1.archive.xl';$hashes[$xlSource]=(Get-FileHash $xlSource).Hash
$xl=[IO.File]::ReadAllText($xlSource).TrimEnd()+"`n    - path: $depot`n      parent: ep1\quest\ep1.quest`n      input:`n        node: [1]`n        socket: Out`n"
[IO.File]::WriteAllText(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError'){throw 'Archive readback failed'}
if(@(Compare-Object @($resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Unexpected packed files'}
foreach($p in $packed.Files.Values){$ms=[IO.MemoryStream]::new();try{$p.Extract($ms);$h=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($ms.ToArray()))}finally{$ms.Dispose()};if($h -ne (Get-FileHash (Join-Path $source $p.Name)).Hash){throw 'Packed byte mismatch'}}
foreach($p in $hashes.Keys){if((Get-FileHash $p).Hash -ne $hashes[$p]){throw "Source changed $p"}}
$m=@{status='BUILT_R8_NOT_INSTALLED_NOT_LIVE';source_root=$source;archive=$archive;sha256=(Get-FileHash $archive).Hash;xl_sha256=(Get-FileHash ($archive+'.xl')).Hash;resources=@($resources);emmerick_nodes=$eNodes;rogue_nodes=$rNodes;guards=$guards;source_hashes=$hashes;packed_readback=$true;unchanged_prior_payloads=8;new_actor_identities=0;story_writes=0;original_resource_overrides=0}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($m|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$m|Select-Object status,sha256,packed_readback,emmerick_nodes,rogue_nodes|ConvertTo-Json -Depth 5
