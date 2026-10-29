Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$inputFile=Join-Path $PSScriptRoot 'inputs_01.json'
$inputData=Get-Content $inputFile -Raw|ConvertFrom-Json -Depth 50
$C=Join-Path (Split-Path $PSScriptRoot -Parent) 'candidate_01'
$donor=Read-Cr2wFile (Join-Path $ws 'diagnostics/world_npc_idle_20261026_01/combat_owners/base_open_world_combat_events_pacifica_coastview_ce_pac_cvi_phase.questphase')
$cg=(Get-QuestNode (Get-QuestNode (Get-QuestNode $donor.RootChunk.Graph.Chunk 28).PhaseGraph.Chunk 14).PhaseGraph.Chunk 61).PhaseGraph.Chunk
$pause=Get-QuestNode $cg 30
function Put($g,$n){Add-RedHandle $g.Nodes $n}
function Link($g,$a,$b){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) 'Out') (Get-QuestSocket (Get-QuestNode $g $b) 'In'))}
function Fact($name,$value){return New-FactCondition $name $value ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)}
function Pause($id,$condition){$n=$pause.DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};Set-RedHandleProperty $n Condition $condition;return $n}
$proofs=@()
foreach($row in $inputData.groups){
 $id=[int]$row.id;$prefix="PTFRWA3ENV_${id}_";$support="PTFRWW2_${id}_"
 if(@($row.community_refs).Count -ne 1){throw 'Require exact single community'}
 $path=Join-Path $ws $row.native_binary
 if((Get-FileHash $path).Hash -cne $row.native_binary_sha256){throw 'Native source drift'}
 $native=Read-Cr2wFile $path;$g0=$native.RootChunk.Graph.Chunk
 foreach($v in @($row.node_path.Split('/')|Select-Object -Skip 1)){$g0=(Get-QuestNode $g0 ([int]$v)).PhaseGraph.Chunk}
 if(@($row.operations).Count -ne 1){throw 'Require one exact native event'}
 $eventId=[int]$row.operations[0].path.Split('/')[-1]
 $event=Get-QuestNode $g0 $eventId
 if($event.GetType().Name -cne 'questWorldDataManagerNodeDefinition' -or $event.Type.Chunk.GetType().Name -cne 'questTogglePrefabVariant_NodeType'){throw 'Unexpected native operation'}
 foreach($s in $event.Sockets){$s.Chunk.Connections.Clear()}
 $guard=[WolvenKit.RED4.Types.questLogicalCondition]::new();$guard.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
 $facts=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;PTFRBASE_Suspended=0;q305_johnny_scene_active=0;q115_point_of_no_return=0;q000_done=1;($support+'Claimed')=1;($support+'Entered')=1;($support+'Hold')=0;($prefix+'Claimed')=0}
 foreach($k in $facts.Keys){Add-RedHandle $guard.Conditions (Fact $k $facts[$k])}
 $ready=$pause.Condition.Chunk.DeepCopy()
 $ready.Type.Chunk.SpawnerReference=[WolvenKit.RED4.Types.NodeRef]::op_Implicit([string]$row.community_refs[0])
 Add-RedHandle $guard.Conditions $ready
 $g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 Put $g (New-InputNode 0 'In1');Put $g (New-SetFactNode 1 ($prefix+'Ready') 1);Put $g (Pause 2 $guard)
 Put $g (New-SetFactNode 3 ($prefix+'Claimed') 1);Put $g (New-SetFactNode 4 ($prefix+'Ready') 0);Put $g (New-SetFactNode 5 ($prefix+'Entered') 1)
 Put $g $event;Put $g (New-SetFactNode 7 ($prefix+'Finished') 1);Put $g (Pause 8 (Fact ($prefix+'Hold') 1))
 Link $g 0 1;Link $g 1 2;Link $g 2 3;Link $g 3 4;Link $g 4 5;Link $g 5 $eventId;Link $g $eventId 7;Link $g 7 8
 $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
 Set-RedHandleProperty $root Graph $g
 $file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
 $resource="towercontinued/world_support_wa3/environment_${id}.questphase"
 $dest=Join-Path $C ('source/'+$resource)
 if(Test-Path $dest){throw 'Preserve existing owner'}
 [void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent))
 Write-Cr2wFile $file $dest
 $back=Read-Cr2wFile $dest
 Export-Cr2wJson $back (Join-Path $PSScriptRoot "owner_${id}_readback_01.json")
 if($back.RootChunk.Graph.Chunk.Nodes.Count -ne 9 -or @(Get-GraphEdges $back.RootChunk.Graph.Chunk).Count -ne 8){throw 'Roundtrip shape'}
 $proofs+=@{id=$id;resource=$resource;path=$dest;sha256=(Get-FileHash $dest).Hash;native=$path;native_sha256=$row.native_binary_sha256;native_event=$eventId;facts=$facts;community_ref=$row.community_refs[0];edges=@(Get-GraphEdges $back.RootChunk.Graph.Chunk)}
}
@{status='FOUR_NATIVE_ENVIRONMENT_OWNERS_BUILT_NOT_DEPLOYED';owners=$proofs;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 40|Set-Content (Join-Path $PSScriptRoot 'build_proof_01.json') -Encoding utf8NoBOM
$proofs|Select-Object id,sha256|ConvertTo-Json
