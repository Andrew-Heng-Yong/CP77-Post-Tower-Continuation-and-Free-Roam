Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$native=Read-Cr2wFile (Join-Path $ws 'research/activity_state_r3/native_sources/raw/base/quest/minor_quests/mq007/mq007.questphase')
$n=Get-QuestNode $native.RootChunk.Graph.Chunk 3
$cooked=Read-Cr2wFile (Join-Path $PSScriptRoot 'candidate_06/source/towercontinued/skippy_ambient_sc1/skippy_ambient_owner.questphase')
$c=Get-QuestNode $cooked.RootChunk.Graph.Chunk 10
$script:graphs=0;$script:nodes=0;$script:edges=0
function Compare-Graph($ng,$cg,[string]$where){
 $a=@(Get-GraphEdges $ng|Sort-Object);$b=@(Get-GraphEdges $cg|Sort-Object)
 if(@(Compare-Object $a $b).Count){throw ('Skippy ambient edge drift at '+$where)}
 $an=@($ng.Nodes|ForEach-Object {"$($_.Chunk.Id):$($_.Chunk.GetType().Name)"}|Sort-Object)
 $bn=@($cg.Nodes|ForEach-Object {"$($_.Chunk.Id):$($_.Chunk.GetType().Name)"}|Sort-Object)
 if(@(Compare-Object $an $bn).Count){throw ('Skippy ambient node drift at '+$where)}
 $script:graphs++;$script:nodes+=$an.Count;$script:edges+=$a.Count
 foreach($h in $ng.Nodes){
  $nn=$h.Chunk;$cc=Get-QuestNode $cg ([int]$nn.Id.ToString())
  if($nn -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $nn.PhaseGraph -and $null -ne $nn.PhaseGraph.Chunk){
   Compare-Graph $nn.PhaseGraph.Chunk $cc.PhaseGraph.Chunk ($where+'/'+$nn.Id)
  }
 }
}
Compare-Graph $n.PhaseGraph.Chunk $c.PhaseGraph.Chunk 'ambient'
@{status='NATIVE_AMBIENT_GRAPHS_MATCH';graphs=$script:graphs;nodes=$script:nodes;edges=$script:edges}|ConvertTo-Json
