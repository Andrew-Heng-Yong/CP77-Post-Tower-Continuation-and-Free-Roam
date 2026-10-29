Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$nativePath=Join-Path $ws 'diagnostics/bottle_shooting_20261027_01/native_review/current_dependencies_01/basegame_4_gamedata.archive/ce_pac_cvi_phase.questphase'
$candidatePath=Join-Path (Split-Path $PSScriptRoot -Parent) 'candidate_01/source/towercontinued/bottle_actions_ba1/bottle_action_owner.questphase'
$native=Read-Cr2wFile $nativePath;$candidate=Read-Cr2wFile $candidatePath
$n28=Get-QuestNode $native.RootChunk.Graph.Chunk 28
$n14=Get-QuestNode $n28.PhaseGraph.Chunk 14
$n61=Get-QuestNode $n14.PhaseGraph.Chunk 61
$cg=$candidate.RootChunk.Graph.Chunk
$loop=(Get-QuestNode $cg 10).PhaseGraph.Chunk
$c61=Get-QuestNode $loop 61
$ne=@(Get-GraphEdges $n61.PhaseGraph.Chunk)
$ce=@(Get-GraphEdges $c61.PhaseGraph.Chunk)
$nn=@($n61.PhaseGraph.Chunk.Nodes|ForEach-Object {"$($_.Chunk.Id):$($_.Chunk.GetType().Name)"}|Sort-Object)
$cn=@($c61.PhaseGraph.Chunk.Nodes|ForEach-Object {"$($_.Chunk.Id):$($_.Chunk.GetType().Name)"}|Sort-Object)
if(@(Compare-Object $ne $ce).Count -or @(Compare-Object $nn $cn).Count){throw 'Native controller graph differs'}
Export-Cr2wJson $native (Join-Path $PSScriptRoot 'fresh_native_01.json')
Export-Cr2wJson $candidate (Join-Path $PSScriptRoot 'fresh_candidate_01.json')
$community='$/03_night_city/c_pacifica/coastview/cvi_ce_prefabMZQN2IY/cs_goons_shooting_openworld_002_prefabPFINICQ/cs_goons_shooting_com;#ce_pac_cvi_112_com'
$result=@{status='PASS_FRESH_NATIVE_GRAPH_EQUIVALENCE';native_path=$nativePath;native_sha256=(Get-FileHash -LiteralPath $nativePath).Hash;candidate_path=$candidatePath;candidate_sha256=(Get-FileHash -LiteralPath $candidatePath).Hash;nodes=$nn.Count;edges=$ne.Count;controller_edges=$ce;root_edges=@(Get-GraphEdges $cg);loop_edges=@(Get-GraphEdges $loop);community_hash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($community).ToString();game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'fresh_graph_proof_01.json'),($result|ConvertTo-Json -Depth 20)+"`n",[Text.UTF8Encoding]::new($false))
$result|Select-Object status,nodes,edges,candidate_sha256,community_hash|ConvertTo-Json
