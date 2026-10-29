param([Parameter(Mandatory=$true)][ValidateSet(172,173)][int]$Group)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $PSScriptRoot 'candidate_01'
$config=@{172=@{owner=7;controller=64;ready=65;alias='#ce_pac_cvi_105_com'};173=@{owner=8;controller=61;ready=62;alias='#ce_pac_cvi_106_com'}}[$Group]
$manifest=Get-Content -LiteralPath (Join-Path $ws 'prealpha/world_workspots_w2/manifest_03.json') -Raw|ConvertFrom-Json -Depth 80
$record=@($manifest.groups|Where-Object id -eq $Group)
if($record.Count -ne 1 -or $record[0].community_refs.Count -ne 1){throw 'Exact W3 identity missing'}
$prefix="PTFRWA2_${Group}_";$support="PTFRWW2_${Group}_"
$resource="towercontinued/world_actions_wa2/group_${Group}_action.questphase"
$dest=Join-Path $out ('source/'+$resource)
if(Test-Path -LiteralPath $dest){throw 'Preserve existing candidate'}
$nativePath=Join-Path $ws 'diagnostics/world_npc_idle_20261026_01/combat_owners/base_open_world_combat_events_pacifica_coastview_ce_pac_cvi_phase.questphase'
$nativeHash=(Get-FileHash -LiteralPath $nativePath).Hash
if($nativeHash -cne '2A24AAC266066F835D4B677BAC1013F86736ED8358353DE49123D99E0F9445DC'){throw 'Native drift'}
$native=Read-Cr2wFile $nativePath
$district=Get-QuestNode $native.RootChunk.Graph.Chunk 28
$original=Get-QuestNode $district.PhaseGraph.Chunk $config.owner
# Preserve direct native socket identity; DeepCopy of a graph duplicates sockets.
$controller=Get-QuestNode $original.PhaseGraph.Chunk $config.controller
$ready=(Get-QuestNode $original.PhaseGraph.Chunk $config.ready).DeepCopy()
$nativeEdges=@(Get-GraphEdges $controller.PhaseGraph.Chunk)
if($controller.PhaseGraph.Chunk.Nodes.Count -ne 32 -or $nativeEdges.Count -ne 43 -or $controller.PhaseInstancePrefabs.Count -ne 0){throw 'Native controller shape'}
foreach($s in $controller.Sockets){$s.Chunk.Connections.Clear()}
foreach($s in $ready.Sockets){$s.Chunk.Connections.Clear()}
$community=[string]$record[0].community_refs[0]
$cg=$controller.PhaseGraph.Chunk
foreach($id in @(9,10,17,18,19,20,22,23)){
 $n=Get-QuestNode $cg $id
 if($n.EntityReference.Reference.ToString() -cne $config.alias){throw "Actor ref $id"}
 $n.EntityReference.Reference=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($community)
}
foreach($id in @(30,31)){
 $n=Get-QuestNode $cg $id
 if($n.Condition.Chunk.Type.Chunk.SpawnerReference.ToString() -cne $config.alias){throw "Spawner ref $id"}
 $n.Condition.Chunk.Type.Chunk.SpawnerReference=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($community)
}
if($ready.Condition.Chunk.Type.Chunk.SpawnerReference.ToString() -cne $config.alias){throw 'Ready ref'}
$ready.Condition.Chunk.Type.Chunk.SpawnerReference=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($community)
function Put($g,$n){Add-RedHandle $g.Nodes $n}
function Link($g,$a,$as,$b,$bs='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $as) (Get-QuestSocket (Get-QuestNode $g $b) $bs))}
function Fact($name,$value,$op='Equal'){return (New-FactCondition $name $value ([Enum]::Parse([WolvenKit.RED4.Types.Enums+EComparisonType],$op)))}
function Logic($op){$c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[Enum]::Parse([WolvenKit.RED4.Types.Enums+questLogicalOperation],$op);return $c}
function Pause($id,$condition){$n=$ready.DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};Set-RedHandleProperty $n Condition $condition;return $n}
$facts=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;PTFRBASE_Suspended=0;q305_johnny_scene_active=0;q115_point_of_no_return=0;q000_done=1;($support+'Claimed')=1;($support+'Entered')=1;($support+'Hold')=0}
function Eligible { $c=Logic 'AND';foreach($key in $facts.Keys){Add-RedHandle $c.Conditions (Fact $key $facts[$key])};return $c }
$admission=Eligible
Add-RedHandle $admission.Conditions (Fact ($prefix+'Claimed') 0)
$invalid=Logic 'OR';foreach($key in $facts.Keys){Add-RedHandle $invalid.Conditions (Fact $key $facts[$key] 'NotEqual')}
$loop=[WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $loop (New-InputNode 0 'In1')
$loopGate=Eligible
Add-RedHandle $loopGate.Conditions $ready.Condition.Chunk
Put $loop (Pause 2 $loopGate)
Put $loop (New-SetFactNode 3 ($prefix+'Active') 1)
Put $loop $controller
Put $loop (New-SetFactNode 4 ($prefix+'Active') 0)
Link $loop 0 Out 2;Link $loop 2 Out 3;Link $loop 3 Out $config.controller In1;Link $loop $config.controller Out1 4;Link $loop 4 Out 2
$lifecycle=[WolvenKit.RED4.Types.questPhaseNodeDefinition]::new();$lifecycle.Id=[uint16]10
[void](New-QuestSocket $lifecycle 'In1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
[void](New-QuestSocket $lifecycle 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
Set-RedHandleProperty $lifecycle PhaseGraph $loop
$g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $g (New-InputNode 0 'In1');Put $g (New-SetFactNode 1 ($prefix+'Ready') 1)
Put $g (Pause 2 $admission);Put $g (New-SetFactNode 3 ($prefix+'Claimed') 1)
Put $g (New-SetFactNode 4 ($prefix+'Ready') 0);Put $g (New-SetFactNode 5 ($prefix+'Entered') 1)
Put $g $lifecycle;Put $g (Pause 11 $invalid)
$cut=[WolvenKit.RED4.Types.questCutControlNodeDefinition]::new();$cut.Id=[uint16]12
foreach($s in @(@('In','Input'),@('Out','Output'),@('CutSource','CutSource'))){[void](New-QuestSocket $cut $s[0] ([Enum]::Parse([WolvenKit.RED4.Types.Enums+questSocketType],$s[1])))}
Put $g $cut;Put $g (New-SetFactNode 13 ($prefix+'Active') 0);Put $g (New-SetFactNode 14 ($prefix+'Suspended') 1)
Put $g (Pause 15 (Eligible));Put $g (New-SetFactNode 16 ($prefix+'Suspended') 0)
Link $g 0 Out 1;Link $g 1 Out 2;Link $g 2 Out 3;Link $g 3 Out 4;Link $g 4 Out 5
Link $g 5 Out 10 In1;Link $g 5 Out 11;Link $g 11 Out 12;Link $g 12 CutSource 10 CutDestination
Link $g 12 Out 13;Link $g 13 Out 14;Link $g 14 Out 15;Link $g 15 Out 16;Link $g 16 Out 5
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
Set-RedHandleProperty $root Graph $g
$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
[void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent))
Write-Cr2wFile $file $dest
$read=Read-Cr2wFile $dest
$rcg=(Get-QuestNode (Get-QuestNode $read.RootChunk.Graph.Chunk 10).PhaseGraph.Chunk $config.controller).PhaseGraph.Chunk
if($rcg.Nodes.Count -ne 32 -or (@(Get-GraphEdges $rcg) -join "`n") -cne ($nativeEdges -join "`n")){throw 'Native graph readback drift'}
Export-Cr2wJson $read (Join-Path $out "owner_${Group}_readback_01.json")
if((Get-FileHash -LiteralPath $nativePath).Hash -cne $nativeHash){throw 'Native input changed'}
$proof=[ordered]@{status='WA2_OWNER_SERIALIZED';group=$Group;resource=$resource;sha256=(Get-FileHash -LiteralPath $dest).Hash;native_sha256=$nativeHash;native_nodes=32;native_edges=$nativeEdges;community_ref=$community;eligibility=$facts;root_edges=@(Get-GraphEdges $read.RootChunk.Graph.Chunk);loop_edges=@(Get-GraphEdges (Get-QuestNode $read.RootChunk.Graph.Chunk 10).PhaseGraph.Chunk);game_writes=0;save_writes=0;scope='Exact W3 sibling shooting controller; no prefab/spawn/native-fact writes'}
[IO.File]::WriteAllText((Join-Path $out "owner_${Group}_proof_01.json"),($proof|ConvertTo-Json -Depth 30)+"`n",[Text.UTF8Encoding]::new($false))
$proof|ConvertTo-Json -Depth 8
