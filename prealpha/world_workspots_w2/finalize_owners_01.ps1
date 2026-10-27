Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$manifestPath=Join-Path $PSScriptRoot 'manifest_02.json'
$m=Get-Content -LiteralPath $manifestPath -Raw|ConvertFrom-Json -Depth 80
$candidate=Join-Path $PSScriptRoot 'candidate_01'
$out=Join-Path $candidate 'owner_proof_01.json'
if(Test-Path -LiteralPath $out){throw 'Preserve prior proof'}
$proofs=[Collections.Generic.List[object]]::new()
$cohorts=@($m.groups|Where-Object {$_.id -ne 183}|Group-Object native_binary)
foreach($cohort in $cohorts){
 $stem=[IO.Path]::GetFileNameWithoutExtension($cohort.Name)
 $rel='towercontinued\world_workspots_w2\'+$stem+'_owners.questphase'
 $path=Join-Path (Join-Path $candidate 'source') $rel
 $file=Read-Cr2wFile $path;$graph=$file.RootChunk.Graph.Chunk
 $expected=@($cohort.Group|Sort-Object id)
 if($graph.Nodes.Count -ne 1+6*$expected.Count){throw "Node count $stem"}
 $edges=@(Get-GraphEdges $graph)
 if($edges.Count -ne 6*$expected.Count){throw "Edge count $stem $($edges.Count)"}
 $groups=[Collections.Generic.List[object]]::new();$j=0
 foreach($g in $expected){
  $id=100+$j*10+5;$j+=1;$owner=Get-QuestNode $graph $id
  if($owner.PhaseInstancePrefabs.Count -ne 1 -or $owner.PhaseInstancePrefabs[0].PrefabNodeRef.ToString() -cne $g.prefab -or $owner.PhaseGraph.Chunk.Nodes.Count -ne 3){throw "Owner mismatch $($g.id)"}
  $ready=Get-QuestNode $graph ($id-5)
  $claim=Get-QuestNode $graph ($id-3)
  $request=Get-QuestNode $graph ($id-2)
  $readyOff=Get-QuestNode $graph ($id-1)
  $inner=Get-QuestNode $owner.PhaseGraph.Chunk 1
  $names=@($ready.Type.Chunk.FactName.ToString(),$claim.Type.Chunk.FactName.ToString(),$request.Type.Chunk.FactName.ToString(),$readyOff.Type.Chunk.FactName.ToString(),$inner.Type.Chunk.FactName.ToString())
  $want=@(($g.prefix+'Ready'),($g.prefix+'Claimed'),($g.prefix+'Request'),($g.prefix+'Ready'),($g.prefix+'Entered'))
  for($k=0;$k -lt 5;$k++){if($names[$k] -cne $want[$k]){throw "Fact mapping mismatch $($g.id) slot ${k}: $($names[$k])"}}
  $groups.Add([ordered]@{id=$g.id;prefix=$g.prefix;prefab=$g.prefab;owner_node=$id})
 }
 $proofs.Add([ordered]@{source=$cohort.Name;resource=$rel;owners=$expected.Count;nodes=$graph.Nodes.Count;edges=$edges.Count;sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash;groups=@($groups)})
}
$count=($proofs|ForEach-Object {$_.owners}|Measure-Object -Sum).Sum
if($count -ne 205 -or $proofs.Count -ne 9){throw "Coverage mismatch $count / $($proofs.Count)"}
$result=[ordered]@{status='PRIVATE_PREFAB_OWNERS_READBACK_PASS_NOT_PACKED_OR_INSTALLED';manifest_sha256=(Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash;owners=$count;resources=$proofs.Count;proofs=@($proofs);game_writes=0;save_writes=0}
[IO.File]::WriteAllText($out,($result|ConvertTo-Json -Depth 60)+"`n",[Text.UTF8Encoding]::new($false))
@{status=$result.status;owners=$result.owners;resources=$result.resources}|ConvertTo-Json
