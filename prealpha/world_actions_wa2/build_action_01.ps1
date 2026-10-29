param([Parameter(Mandatory=$true)][int]$Group)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $PSScriptRoot 'candidate_01'
$contracts=Get-Content (Join-Path $PSScriptRoot 'native_review/action_contracts_02.json') -Raw|ConvertFrom-Json -Depth 100
$contract=@($contracts.contracts|Where-Object group -eq $Group)
if($contract.Count -ne 1){throw 'Expected one exact source contract'}
$contract=$contract[0]
$vehicle=$contract.kind.Contains('vehicle')
$revision=if($vehicle){'02'}else{'01'}
if($contract.kind -in @('existing_BA1_preserve','isolated_shoot_phase')){throw 'Use preserved BA1 or sibling builder'}
$record=$contract
if(@($record.community_refs).Count -ne 1){throw 'One exact community required'}
$community=[string]$record.community_refs[0]
$prefix="PTFRWA2_${Group}_";$support="PTFRWW2_${Group}_"
$resource="towercontinued/world_actions_wa2/group_${Group}_action.questphase"
$dest=Join-Path $out ('unqualified_'+$revision+'/'+$resource)
if(Test-Path -LiteralPath $dest){throw 'Preserve existing candidate'}
$nativePath=[string]$contract.native_binary
if(-not [IO.Path]::IsPathRooted($nativePath)){$nativePath=Join-Path $ws $nativePath}
$nativeHash=(Get-FileHash -LiteralPath $nativePath).Hash
if($nativeHash -cne $contract.native_binary_sha256){throw 'Native drift'}
$native=Read-Cr2wFile $nativePath
function GraphAt($path){$graph=$native.RootChunk.Graph.Chunk;foreach($id in @($path.Split('/')|Select-Object -Skip 1)){$graph=(Get-QuestNode $graph ([int]$id)).PhaseGraph.Chunk};return $graph}
$source=GraphAt $contract.graph_path
$donor=Read-Cr2wFile (Join-Path $ws 'diagnostics/world_npc_idle_20261026_01/combat_owners/base_open_world_combat_events_pacifica_coastview_ce_pac_cvi_phase.questphase')
$donorGraph=(Get-QuestNode (Get-QuestNode (Get-QuestNode $donor.RootChunk.Graph.Chunk 28).PhaseGraph.Chunk 14).PhaseGraph.Chunk 61).PhaseGraph.Chunk
$ready=(Get-QuestNode $donorGraph 30).DeepCopy()
$ready.Condition.Chunk.Type.Chunk.SpawnerReference=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($community)
foreach($s in $ready.Sockets){$s.Chunk.Connections.Clear()}
function Put($g,$n){Add-RedHandle $g.Nodes $n}
function Link($g,$a,$as,$b,$bs='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $as) (Get-QuestSocket (Get-QuestNode $g $b) $bs))}
function Fact($name,$value,$op='Equal'){return (New-FactCondition $name $value ([Enum]::Parse([WolvenKit.RED4.Types.Enums+EComparisonType],$op)))}
function Logic($op){$c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[Enum]::Parse([WolvenKit.RED4.Types.Enums+questLogicalOperation],$op);return $c}
function Pause($id,$condition){$n=$ready.DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};Set-RedHandleProperty $n Condition $condition;return $n}

$cg=[WolvenKit.RED4.Types.questGraphDefinition]::new()
foreach($id in $contract.node_ids){
 $node=Get-QuestNode $source ([int]$id)
 foreach($s in $node.Sockets){$s.Chunk.Connections.Clear()}
 Put $cg $node
}
foreach($e in $contract.internal_edges){Link $cg ([int]$e[0]) $e[1] ([int]$e[2]) $e[3]}
if($contract.kind -ne 'isolated_vehicle_radio_door_phase'){
 Put $cg (New-InputNode 65000 'In1')
 Put $cg (New-OutputNode 65001 'Out1')
 $notReady=(Get-QuestNode $donorGraph 31).DeepCopy()
 $notReady.Id=[uint16]65002
 foreach($s in $notReady.Sockets){$s.Chunk.Connections.Clear()}
 $notReady.Condition.Chunk.Type.Chunk.SpawnerReference=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($community)
 Put $cg $notReady
 Link $cg 65000 Out 65002;Link $cg 65002 Out 65001
 if($contract.kind -eq 'nested_vehicle_radio_event_only'){
  $parent=GraphAt $contract.owner_path
  $eventGate=(Get-QuestNode $parent ([int]$contract.outer_ready_gate_id)).DeepCopy()
  $eventGate.Id=[uint16]65003
  foreach($s in $eventGate.Sockets){$s.Chunk.Connections.Clear()}
  Put $cg $eventGate
  Link $cg 65000 Out 65003;Link $cg 65003 Out 2
 }else{Link $cg 65000 Out ([int]$contract.entry_gate_id)}
}
$controller=[WolvenKit.RED4.Types.questPhaseNodeDefinition]::new();$controller.Id=[uint16]60000
foreach($s in @(@('In1','Input'),@('Out1','Output'),@('CutDestination','CutDestination'))){[void](New-QuestSocket $controller $s[0] ([Enum]::Parse([WolvenKit.RED4.Types.Enums+questSocketType],$s[1])))}
Set-RedHandleProperty $controller PhaseGraph $cg
$config=@{controller=60000}
$nativeEdges=@(Get-GraphEdges $cg)
$facts=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;PTFRBASE_Suspended=0;q305_johnny_scene_active=0;q115_point_of_no_return=0;q000_done=1;($support+'Claimed')=1;($support+'Entered')=1;($support+'Hold')=0}
function Eligible { $c=Logic 'AND';foreach($key in $facts.Keys){Add-RedHandle $c.Conditions (Fact $key $facts[$key])};return $c }
$admission=Eligible
Add-RedHandle $admission.Conditions (Fact ($prefix+'Claimed') 0)
$invalid=Logic 'OR';foreach($key in $facts.Keys){Add-RedHandle $invalid.Conditions (Fact $key $facts[$key] 'NotEqual')}

if($vehicle){
 $eventGateId=if($contract.kind -eq 'isolated_vehicle_radio_door_phase'){2}elseif($contract.kind -eq 'nested_vehicle_radio_event_only'){65003}else{[int]$contract.entry_gate_id}
 $eventNode=Get-QuestNode $cg $eventGateId
 $eventGuard=Eligible
 Add-RedHandle $eventGuard.Conditions $eventNode.Condition.Chunk
 Set-RedHandleProperty $eventNode Condition $eventGuard
}
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
Put $g $lifecycle
if(-not $vehicle){
Put $g (Pause 11 $invalid)
$cut=[WolvenKit.RED4.Types.questCutControlNodeDefinition]::new();$cut.Id=[uint16]12
foreach($s in @(@('In','Input'),@('Out','Output'),@('CutSource','CutSource'))){[void](New-QuestSocket $cut $s[0] ([Enum]::Parse([WolvenKit.RED4.Types.Enums+questSocketType],$s[1])))}
Put $g $cut;Put $g (New-SetFactNode 13 ($prefix+'Active') 0);Put $g (New-SetFactNode 14 ($prefix+'Suspended') 1)
Put $g (Pause 15 (Eligible));Put $g (New-SetFactNode 16 ($prefix+'Suspended') 0)
}
Link $g 0 Out 1;Link $g 1 Out 2;Link $g 2 Out 3;Link $g 3 Out 4;Link $g 4 Out 5
Link $g 5 Out 10 In1
if(-not $vehicle){
Link $g 5 Out 11;Link $g 11 Out 12;Link $g 12 CutSource 10 CutDestination
Link $g 12 Out 13;Link $g 13 Out 14;Link $g 14 Out 15;Link $g 15 Out 16;Link $g 16 Out 5
}
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
Set-RedHandleProperty $root Graph $g
$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
[void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent))
Write-Cr2wFile $file $dest

$read=Read-Cr2wFile $dest
$rcg=(Get-QuestNode (Get-QuestNode $read.RootChunk.Graph.Chunk 10).PhaseGraph.Chunk 60000).PhaseGraph.Chunk
if((@(Get-GraphEdges $rcg) -join "`n") -cne ($nativeEdges -join "`n")){throw 'Closure readback edge drift'}
Export-Cr2wJson $read (Join-Path $out "owner_${Group}_unqualified_${revision}.json")
if((Get-FileHash -LiteralPath $nativePath).Hash -cne $nativeHash){throw 'Native input changed'}
$proof=[ordered]@{status='WA2_UNQUALIFIED_CLOSURE_SERIALIZED';group=$Group;resource=$resource;sha256=(Get-FileHash -LiteralPath $dest).Hash;native_sha256=$nativeHash;contract_kind=$contract.kind;native_node_ids=$contract.node_ids;native_internal_edges=$contract.internal_edges;controller_edges=$nativeEdges;community_ref=$community;eligibility=$facts;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out "owner_${Group}_unqualified_proof_${revision}.json"),($proof|ConvertTo-Json -Depth 30)+"`n",[Text.UTF8Encoding]::new($false))
Write-Output "Serialized group $Group"
