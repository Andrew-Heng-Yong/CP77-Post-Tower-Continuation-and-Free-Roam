$ErrorActionPreference='Stop'
. './tools/build_phase2a.ps1' -HelpersOnly -WolvenKitRoot './research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'
$m=Get-Content prealpha/world_support_wa3/manifest_core_01.json -Raw|ConvertFrom-Json -Depth 100
foreach($id in @(1013,1014)){$g=@($m.groups|Where-Object id -eq $id)[0];$f=Read-Cr2wFile $g.native_binary;$gr=$f.RootChunk.Graph.Chunk; $ids=$g.node_path.Split('/')[1..($g.node_path.Split('/').Count-1)];$n=$null;for($j=0;$j -lt $ids.Count;$j++){$n=Get-QuestNode $gr ([int]$ids[$j]);if($j -lt $ids.Count-1){$gr=$n.PhaseGraph.Chunk}};Write-Output ('ID '+$id+' prefab '+$g.prefab+' original '+$n.PhaseInstancePrefabs.Count);foreach($p in $n.PhaseInstancePrefabs){Write-Output $p.PrefabNodeRef.ToString()}}
