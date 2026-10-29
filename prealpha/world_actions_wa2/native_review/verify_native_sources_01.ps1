Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$raw=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'census_raw_01.json') -Raw|ConvertFrom-Json
$files=@{};$pins=@();$checks=@()
$freshDir=Join-Path $PSScriptRoot 'fresh_sources_01'
[void][IO.Directory]::CreateDirectory($freshDir)
foreach($owner in $raw.owners){
 $path=$owner.native_binary
 if(!$files.ContainsKey($path)){
  if((Get-FileHash -LiteralPath $path).Hash -cne $owner.native_binary_sha256){throw ('Native binary drift '+$path)}
  $file=Read-Cr2wFile $path;$files[$path]=$file
  $dest=Join-Path $freshDir ([IO.Path]::GetFileName($path)+'.json')
  Export-Cr2wJson $file $dest
  $pins+=@{native_binary=$path;sha256=$owner.native_binary_sha256;fresh_json=$dest;fresh_json_sha256=(Get-FileHash -LiteralPath $dest).Hash;old_json=$owner.source}
 }
 foreach($phase in $owner.phases){
  $graph=$files[$path].RootChunk.Graph.Chunk;$node=$null
  foreach($part in ($phase.path.Split('/')|Select-Object -Skip 1)){
   $node=Get-QuestNode $graph ([int]$part)
   $graph=$null
   if($null -ne $node.PhaseGraph){$graph=$node.PhaseGraph.Chunk}
  }
  $actualEdges=@();$actualNodes=@()
  if($null -ne $graph){
   $actualEdges=@(Get-GraphEdges $graph)
   $actualNodes=@($graph.Nodes|ForEach-Object {"$($_.Chunk.Id):$($_.Chunk.GetType().Name)"}|Sort-Object)
  }
  $expectedEdges=@($phase.edges|ForEach-Object {"$($_[0]).$($_[1]) -> $($_[2]).$($_[3])"}|Sort-Object)
  $expectedNodes=@()
  if($phase.node_count -gt 0){$expectedNodes=@($phase.payload.phaseGraph.nodes|ForEach-Object {"$($_.id):$($_.'$type')"}|Sort-Object)}
  if(($actualEdges -join "`n") -cne ($expectedEdges -join "`n")){throw ('Edge mismatch '+$owner.id+' '+$phase.path)}
  if(($actualNodes -join "`n") -cne ($expectedNodes -join "`n")){throw ('Node mismatch '+$owner.id+' '+$phase.path)}
  $checks+=@{group=$owner.id;path=$phase.path;nodes=$actualNodes.Count;edges=$actualEdges.Count}
 }
}
$result=@{status='PASS_FRESH_BINARY_ALL_237_OWNERS_ALL_257_PHASES';owners=237;phases=$checks.Count;sources=$files.Count;source_pins=$pins;graph_checks=$checks;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'fresh_source_proof_01.json'),($result|ConvertTo-Json -Depth 15)+"`n",[Text.UTF8Encoding]::new($false))
$result|Select-Object status,owners,phases,sources|ConvertTo-Json
