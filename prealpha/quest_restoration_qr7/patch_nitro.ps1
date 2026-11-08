Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$C=Join-Path $PSScriptRoot 'candidate_01';$O=Join-Path $C 'repair_nitro_01'
if(Test-Path -LiteralPath $O){throw 'Fresh typed repair output required'}
$p=Get-Content -LiteralPath (Join-Path $C 'nitro_plan.json') -Raw|ConvertFrom-Json -Depth 100
foreach($pin in @(@{path=$p.proposal;sha=$p.proposal_sha256},@{path=$p.evidence;sha=$p.evidence_sha256},@{path=$p.review;sha=$p.review_sha256},@{path=$p.native.raw;sha=$p.native.raw_sha256})){if((Get-FileHash -LiteralPath $pin.path).Hash -cne $pin.sha){throw 'Approved input changed'}}
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$raw=Join-Path (Join-Path $C 'archive_source') $p.depot
if((Get-FileHash -LiteralPath $raw).Hash -cne $p.before){throw 'Wrong predecessor resource'}
$file=Read-Cr2wFile $raw;$native=Read-Cr2wFile $p.native.raw;$g=$file.RootChunk.Graph.Chunk
$nativeGraph=(Get-QuestNode $native.RootChunk.Graph.Chunk $p.native_parent_phase).PhaseGraph.Chunk
[IO.Directory]::CreateDirectory($O)|Out-Null
Export-Cr2wJson $file (Join-Path $O 'before.json');Export-Cr2wJson $native (Join-Path $O 'native.json')
foreach($guardId in $p.guard_ids){
 $condition=(Get-QuestNode $g $guardId).Condition.Chunk
 if($condition.GetType().Name -cne 'questLogicalCondition' -or $condition.Operation.ToString() -cne 'AND'){throw 'Reviewed guard conjunction differs'}
 foreach($sourceId in $p.native_condition_nodes){Add-RedHandle $condition.Conditions ((Get-QuestNode $nativeGraph $sourceId).Condition.Chunk.DeepCopy())}
}
Write-Cr2wFile $file $raw
Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $O 'after.json')
@{status='SERIALIZED_REGISTERED_NATIVE_MQ060_FUTURE_GATE_NOT_INSTALLED';depot=$p.depot;before=$p.before;after=(Get-FileHash -LiteralPath $raw).Hash;plan_sha256=(Get-FileHash -LiteralPath (Join-Path $C 'nitro_plan.json')).Hash;guard_ids=$p.guard_ids;native_condition_nodes=$p.native_condition_nodes;review=$p.review;review_sha256=$p.review_sha256;game_writes=0;save_writes=0;package_state='PREDECESSOR_ARCHIVE_AWAITING_REBUILD'}|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $O 'patch.json') -Encoding utf8NoBOM
'SERIALIZED_REGISTERED_NATIVE_MQ060_FUTURE_GATE_NOT_INSTALLED'
