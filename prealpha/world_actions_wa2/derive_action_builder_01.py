"""Build native action closures with the BA1 admission/suspension lifecycle."""
from pathlib import Path
here=Path(__file__).resolve().parent
base=(here/'build_nested_shooting_01.ps1').read_text()
helpers=base[base.index('function Put('):base.index('$facts=[ordered]')]
wrapper=base[base.index('$facts=[ordered]'):base.index('$read=Read-Cr2wFile $dest')]
wrapper=wrapper.replace('$loop=[WolvenKit.RED4.Types.questGraphDefinition]::new()',r'''
if($vehicle){
 $eventGateId=if($contract.kind -eq 'isolated_vehicle_radio_door_phase'){2}elseif($contract.kind -eq 'nested_vehicle_radio_event_only'){65003}else{[int]$contract.entry_gate_id}
 $eventNode=Get-QuestNode $cg $eventGateId
 $eventGuard=Eligible
 Add-RedHandle $eventGuard.Conditions $eventNode.Condition.Chunk
 Set-RedHandleProperty $eventNode Condition $eventGuard
}
$loop=[WolvenKit.RED4.Types.questGraphDefinition]::new()''')
wrapper=wrapper.replace('Put $g $lifecycle;Put $g (Pause 11 $invalid)','Put $g $lifecycle\nif(-not $vehicle){\nPut $g (Pause 11 $invalid)')
wrapper=wrapper.replace("Link $g 0 Out 1;", "}\nLink $g 0 Out 1;")
wrapper=wrapper.replace('Link $g 5 Out 10 In1;Link $g 5 Out 11;', 'Link $g 5 Out 10 In1\nif(-not $vehicle){\nLink $g 5 Out 11;')
wrapper=wrapper.replace('$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new()', '}\n$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new()')
header=r'''param([Parameter(Mandatory=$true)][int]$Group)
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
'''
closure=r'''
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
'''
tail=r'''
$read=Read-Cr2wFile $dest
$rcg=(Get-QuestNode (Get-QuestNode $read.RootChunk.Graph.Chunk 10).PhaseGraph.Chunk 60000).PhaseGraph.Chunk
if((@(Get-GraphEdges $rcg) -join "`n") -cne ($nativeEdges -join "`n")){throw 'Closure readback edge drift'}
Export-Cr2wJson $read (Join-Path $out "owner_${Group}_unqualified_${revision}.json")
if((Get-FileHash -LiteralPath $nativePath).Hash -cne $nativeHash){throw 'Native input changed'}
$proof=[ordered]@{status='WA2_UNQUALIFIED_CLOSURE_SERIALIZED';group=$Group;resource=$resource;sha256=(Get-FileHash -LiteralPath $dest).Hash;native_sha256=$nativeHash;contract_kind=$contract.kind;native_node_ids=$contract.node_ids;native_internal_edges=$contract.internal_edges;controller_edges=$nativeEdges;community_ref=$community;eligibility=$facts;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out "owner_${Group}_unqualified_proof_${revision}.json"),($proof|ConvertTo-Json -Depth 30)+"`n",[Text.UTF8Encoding]::new($false))
Write-Output "Serialized group $Group"
'''
(here/'build_action_01.ps1').write_text(header+helpers+closure+wrapper+tail)
