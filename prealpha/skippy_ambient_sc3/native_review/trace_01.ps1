Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$nativePath=Join-Path $ws 'research/activity_state_r3/native_sources/raw/base/quest/minor_quests/mq007/mq007.questphase'
$cookedPath=Join-Path $ws 'prealpha/skippy_coaster_sc1/candidate_07/archive_source/towercontinued/skippy_ambient_sc1/skippy_ambient_owner.questphase'
if(!(Test-Path -LiteralPath $cookedPath)){$cookedPath=Join-Path $ws 'prealpha/skippy_coaster_sc1/candidate_06/source/towercontinued/skippy_ambient_sc1/skippy_ambient_owner.questphase'}
$native=Read-Cr2wFile $nativePath
$cooked=Read-Cr2wFile $cookedPath
Export-Cr2wJson $native (Join-Path $PSScriptRoot 'native_root_01.json')
Export-Cr2wJson $cooked (Join-Path $PSScriptRoot 'cooked_root_01.json')
function Rows($g){return @($g.Nodes|ForEach-Object {[ordered]@{id=$_.Chunk.Id.ToString();type=$_.Chunk.GetType().Name}})}
$n=Get-QuestNode $native.RootChunk.Graph.Chunk 3
$c=Get-QuestNode $cooked.RootChunk.Graph.Chunk 10
$proof=[ordered]@{
 status='NATIVE_AND_COOKED_LIFECYCLE_TRACE';
 native_source=$nativePath;native_sha256=(Get-FileHash -LiteralPath $nativePath).Hash;
 cooked_source=$cookedPath;cooked_sha256=(Get-FileHash -LiteralPath $cookedPath).Hash;
 native_root_nodes=(Rows $native.RootChunk.Graph.Chunk);
 native_root_edges=@(Get-GraphEdges $native.RootChunk.Graph.Chunk);
 native_ambient_nodes=(Rows $n.PhaseGraph.Chunk);
 native_ambient_edges=@(Get-GraphEdges $n.PhaseGraph.Chunk);
 cooked_root_edges=@(Get-GraphEdges $cooked.RootChunk.Graph.Chunk);
 cooked_ambient_edges=@(Get-GraphEdges $c.PhaseGraph.Chunk);
}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'graph_trace_01.json'),($proof|ConvertTo-Json -Depth 20)+"`n",[Text.UTF8Encoding]::new($false))
$proof|ConvertTo-Json -Depth 20
