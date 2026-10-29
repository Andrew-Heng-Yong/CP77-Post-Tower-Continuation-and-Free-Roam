Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$support=Join-Path $ws 'prealpha/world_actions_wa2/candidate_01/source/towercontinued/world_actions_wa2/group250_support.questphase'
$prior=Join-Path $ws 'prealpha/skippy_ambient_sc3/candidate_02/archive_source/towercontinued/world_workspots_w2/base_open_world_combat_events_pacifica_coastview_ce_pac_cvi_phase_owners.questphase'
$s=Read-Cr2wFile $support;$w=Read-Cr2wFile $prior
Export-Cr2wJson $s (Join-Path $PSScriptRoot 'fresh_support_01.json')
Export-Cr2wJson $w (Join-Path $PSScriptRoot 'fresh_W3_reference_01.json')
$sp=$s.RootChunk.Graph.Chunk;$wi=(Get-QuestNode $w.RootChunk.Graph.Chunk 215).PhaseGraph.Chunk
$out=@{status='FRESH_SUPPORT_AND_W3_REFERENCE';support_sha256=(Get-FileHash -LiteralPath $support).Hash;prior_sha256=(Get-FileHash -LiteralPath $prior).Hash;root_edges=@(Get-GraphEdges $sp);inner_edges=@(Get-GraphEdges (Get-QuestNode $sp 105).PhaseGraph.Chunk);W3_inner_edges=@(Get-GraphEdges $wi)}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'fresh_support_graph_01.json'),($out|ConvertTo-Json -Depth 12)+"`n",[Text.UTF8Encoding]::new($false))
