# Independent fresh native/candidate graph comparison; no game mutation.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$native=Read-Cr2wFile (Join-Path $ws 'research/activity_state_r3/native_sources/raw/base/quest/minor_quests/mq007/mq007.questphase')
$candidate=Read-Cr2wFile (Join-Path $PSScriptRoot 'candidate_01/source/towercontinued/skippy_ambient_sc3/skippy_ambient_owner.questphase')
$script:rows=@()
function CompareGraph($a,$b,[string]$scope){
 $ae=@(Get-GraphEdges $a|Sort-Object);$be=@(Get-GraphEdges $b|Sort-Object)
 $an=@($a.Nodes|ForEach-Object {"$($_.Chunk.Id):$($_.Chunk.GetType().Name)"}|Sort-Object)
 $bn=@($b.Nodes|ForEach-Object {"$($_.Chunk.Id):$($_.Chunk.GetType().Name)"}|Sort-Object)
 if(@(Compare-Object $ae $be).Count -or @($an|Compare-Object $bn).Count){throw ('Native graph differs '+$scope)}
 $script:rows+=@{scope=$scope;nodes=$an.Count;edges=$ae.Count;expected_edges=$ae}
 foreach($h in $a.Nodes){$n=$h.Chunk;if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){CompareGraph $n.PhaseGraph.Chunk (Get-QuestNode $b ([int]$n.Id.ToString())).PhaseGraph.Chunk ($scope+'/'+$n.Id)}}
}
$nativeAmbient=Get-QuestNode $native.RootChunk.Graph.Chunk 3
$loop=(Get-QuestNode $candidate.RootChunk.Graph.Chunk 10).PhaseGraph.Chunk
$candidateAmbient=Get-QuestNode $loop 3
CompareGraph $nativeAmbient.PhaseGraph.Chunk $candidateAmbient.PhaseGraph.Chunk 'ambient'
$result=@{status='PASS_NATIVE_GRAPHS';graphs=$script:rows.Count;nodes=($script:rows|Measure-Object -Property nodes -Sum).Sum;edges=($script:rows|Measure-Object -Property edges -Sum).Sum;rows=$script:rows}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'candidate_01/native_graphs_01.json'),($result|ConvertTo-Json -Depth 12)+"`n",[Text.UTF8Encoding]::new($false))
$result|Select-Object status,graphs,nodes,edges|ConvertTo-Json
