Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$source=Join-Path $ws 'diagnostics/world_npc_idle_20261026_01/combat_owners/base_open_world_combat_events_pacifica_coastview_ce_pac_cvi_phase.questphase'
$native=Read-Cr2wFile $source;$results=@()
foreach($group in @(172,173)){
 $ownerId=@{172=7;173=8}[$group];$controllerId=@{172=64;173=61}[$group]
 $candidate=Join-Path $ws "prealpha/world_actions_wa2/candidate_01/source/towercontinued/world_actions_wa2/group_${group}_action.questphase"
 $c=Read-Cr2wFile $candidate
 $n=(Get-QuestNode (Get-QuestNode (Get-QuestNode $native.RootChunk.Graph.Chunk 28).PhaseGraph.Chunk $ownerId).PhaseGraph.Chunk $controllerId)
 $cg=$c.RootChunk.Graph.Chunk;$loop=(Get-QuestNode $cg 10).PhaseGraph.Chunk;$cn=Get-QuestNode $loop $controllerId
 $ne=@(Get-GraphEdges $n.PhaseGraph.Chunk);$ce=@(Get-GraphEdges $cn.PhaseGraph.Chunk)
 if(($ne -join "`n") -cne ($ce -join "`n") -or $ce.Count -ne 43 -or $cn.PhaseGraph.Chunk.Nodes.Count -ne 32){throw 'Fresh graph mismatch'}
 Export-Cr2wJson $c (Join-Path $PSScriptRoot "fresh_candidate_${group}_01.json")
 $results+=@{group=$group;sha256=(Get-FileHash -LiteralPath $candidate).Hash;nodes=32;edges=43;root_edges=@(Get-GraphEdges $cg);loop_edges=@(Get-GraphEdges $loop);controller_edges=$ce}
}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'candidate_172173_graph_proof_01.json'),(@{status='PASS_FRESH_NATIVE_AND_CANDIDATE_GRAPHS';groups=$results;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 15)+"`n",[Text.UTF8Encoding]::new($false))
$results|Select-Object group,sha256,nodes,edges|ConvertTo-Json
