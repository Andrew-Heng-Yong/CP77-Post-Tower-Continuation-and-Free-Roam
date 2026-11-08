Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$C=Join-Path $PSScriptRoot 'candidate_03';$O=Join-Path $C 'repair_moving_heat'
if(Test-Path -LiteralPath $O){throw 'Fresh repair output required'}
$plan=Get-Content -LiteralPath (Join-Path $C 'moving_heat_plan.json') -Raw|ConvertFrom-Json -Depth 100
foreach($pin in @(@{path=$plan.proposal;sha=$plan.proposal_sha256},@{path=$plan.review;sha=$plan.review_sha256},@{path=$plan.native.raw;sha=$plan.native.raw_sha256})){if((Get-FileHash -LiteralPath $pin.path).Hash -cne $pin.sha){throw 'Reviewed source changed'}}
$p=Get-Content -LiteralPath $plan.proposal -Raw|ConvertFrom-Json -Depth 100
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$helper=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'patch_arr12.ps1') -Raw
$start=$helper.IndexOf('function ClearLocal(');$end=$helper.IndexOf('$raw=Join-Path')
if($start -lt 0 -or $end -le $start){throw 'Pure graph helper boundary differs'}
. ([scriptblock]::Create($helper.Substring($start,$end-$start)))
$raw=Join-Path (Join-Path $C 'archive_source') $p.resource
if((Get-FileHash -LiteralPath $raw).Hash -cne $plan.before){throw 'Wrong predecessor boot'}
$file=Read-Cr2wFile $raw;$native=Read-Cr2wFile $plan.native.raw;$g=$file.RootChunk.Graph.Chunk;$old=Get-QuestNode $g 10
if(@($g.Nodes|Where-Object{[int]$_.Chunk.Id.ToString() -eq 1200}).Count){throw 'Local wrapper ID collision'}
if($native.RootChunk.PhasePrefabs.Count -ne 1 -or $native.RootChunk.PhasePrefabs[0].PrefabNodeRef.ToString() -cne '#q304_pr_car_retrieval'){throw 'Native dedicated root prefab scope differs'}
if($old.PhaseInstancePrefabs.Count -ne 0){throw 'Existing saved phase prefab must stay exact'}
[IO.Directory]::CreateDirectory($O)|Out-Null
Export-Cr2wJson $file (Join-Path $O 'before.json');Export-Cr2wJson $native (Join-Path $O 'native.json')
foreach($id in $p.guard_updates.node_ids){
 $cond=(Get-QuestNode $g $id).Condition.Chunk
 if($cond.GetType().Name -ne 'questLogicalCondition' -or $cond.Operation.ToString() -cne 'AND'){throw 'Reviewed guard conjunction differs'}
 Add-RedHandle $cond.Conditions (New-FactCondition 'PTFRS24_Q304_FRESH_Issued' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
}
$wrapper=$old.DeepCopy();$wrapper.Id=[uint16]1200;ClearLocal $wrapper
$wrapper.PhaseResource=[Activator]::CreateInstance($old.PhaseResource.GetType())
$wrapper.PhaseInstancePrefabs.Add($native.RootChunk.PhasePrefabs[0].DeepCopy())
$inner=[WolvenKit.RED4.Types.questGraphDefinition]::new()
$child=$old.DeepCopy();ClearLocal $child
foreach($n in @((New-InputNode 0 'In1'),$child,(New-OutputNode 1 'Out1'))){Add-RedHandle $inner.Nodes $n}
foreach($edge in $p.new_wrapper.inner_edges){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $inner $edge[0]) $edge[1]) (Get-QuestSocket (Get-QuestNode $inner $edge[2]) $edge[3]))}
Set-RedHandleProperty $wrapper PhaseGraph $inner
foreach($edge in $p.remove_edges){RemoveLocal $g $edge[0] $edge[1] $edge[2] $edge[3]}
Add-RedHandle $g.Nodes $wrapper
foreach($edge in $p.add_edges){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $edge[0]) $edge[1]) (Get-QuestSocket (Get-QuestNode $g $edge[2]) $edge[3]))}
Write-Cr2wFile $file $raw;Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $O 'after.json')
@{status='SERIALIZED_FUTURE_ACCEPTED_MOVING_HEAT_PREFAB_WRAPPER_NOT_INSTALLED';depot=$p.resource;before=$plan.before;after=(Get-FileHash -LiteralPath $raw).Hash;proposal=$plan.proposal;proposal_sha256=$plan.proposal_sha256;review=$plan.review;review_sha256=$plan.review_sha256;native=$plan.native;new_local_id=1200;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 100|Set-Content -LiteralPath (Join-Path $O 'patch.json') -Encoding utf8NoBOM
'SERIALIZED_FUTURE_ACCEPTED_MOVING_HEAT_PREFAB_WRAPPER'
