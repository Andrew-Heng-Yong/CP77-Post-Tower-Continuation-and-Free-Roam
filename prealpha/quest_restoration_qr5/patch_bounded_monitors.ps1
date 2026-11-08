Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$C=Join-Path $PSScriptRoot 'candidate_02';$plans=Get-Content -LiteralPath (Join-Path $C 'monitor_plans.json') -Raw|ConvertFrom-Json -Depth 100
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
# Import only inspected pure graph helpers, never execute the historical patch.
$helper=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'patch_arr12.ps1') -Raw
$start=$helper.IndexOf('function ClearLocal(');$end=$helper.IndexOf('$raw=Join-Path')
if($start -lt 0 -or $end -le $start){throw 'Pure helper boundary differs'}
. ([scriptblock]::Create($helper.Substring($start,$end-$start)))
foreach($p in $plans.plans){
 $O=Join-Path $C ('repair_'+$p.key);if(Test-Path -LiteralPath $O){throw 'Fresh monitor evidence required'}
 foreach($pin in @(@{path=$p.proposal;sha=$p.proposal_sha256},@{path=$p.review;sha=$p.review_sha256})) {if((Get-FileHash -LiteralPath $pin.path).Hash -cne $pin.sha){throw 'Source approval changed'}}
 $nativeSha=if($null -ne $p.native.PSObject.Properties['sha256']){$p.native.sha256}else{$p.native.resource_sha256}
 if((Get-FileHash -LiteralPath $p.native.binary).Hash -cne $nativeSha){throw 'Native source changed'}
 $raw=Join-Path (Join-Path $C 'archive_source') $p.depot;if((Get-FileHash -LiteralPath $raw).Hash -cne $p.before){throw 'Wrong predecessor resource'}
 $file=Read-Cr2wFile $raw;$native=Read-Cr2wFile $p.native.binary;$g=$file.RootChunk.Graph.Chunk;$template=Get-QuestNode $native.RootChunk.Graph.Chunk $p.native_phase_id
 foreach($id in $p.new_ids){if(@($g.Nodes|Where-Object{[int]$_.Chunk.Id.ToString() -eq $id}).Count){throw 'Local ID collision'}}
 $actualPrefabs=@($template.PhaseInstancePrefabs|ForEach-Object{$_.PrefabNodeRef.ToString()})
 if(($actualPrefabs -join '|') -cne (@($p.expected_prefabs) -join '|')){throw 'Native prefab obligation differs'}
 [IO.Directory]::CreateDirectory($O)|Out-Null
 Export-Cr2wJson $file (Join-Path $O 'before.json');Export-Cr2wJson $native (Join-Path $O 'native.json')
 $condition=[WolvenKit.RED4.Types.questLogicalCondition]::new();$condition.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
 foreach($f in $p.guard_facts.PSObject.Properties){Add-RedHandle $condition.Conditions (New-FactCondition $f.Name ([int]$f.Value) ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
 $guard=New-ConditionNode $p.new_ids[0] $condition;$claim=New-SetFactNode $p.new_ids[1] $p.claim_fact 1
 $monitor=$template.DeepCopy();$monitor.Id=[uint16]$p.new_ids[2];ClearLocal $monitor;RewireLocal $monitor.PhaseGraph.Chunk $template.PhaseGraph.Chunk
 foreach($e in $p.native_input_remove){RemoveLocal $monitor.PhaseGraph.Chunk $e[0] $e[1] $e[2] $e[3]}
 foreach($e in $p.native_input_add){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $monitor.PhaseGraph.Chunk $e[0]) $e[1]) (Get-QuestSocket (Get-QuestNode $monitor.PhaseGraph.Chunk $e[2]) $e[3]))}
 foreach($e in $p.parent_removed_edges){RemoveLocal $g $e[0] $e[1] $e[2] $e[3]}
 foreach($n in @($guard,$claim,$monitor)){Add-RedHandle $g.Nodes $n}
 foreach($e in $p.parent_added_edges){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $e[0]) $e[1]) (Get-QuestSocket (Get-QuestNode $g $e[2]) $e[3]))}
 Write-Cr2wFile $file $raw;Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $O 'after.json')
 @{status='SERIALIZED_BOUNDED_FUTURE_MONITOR_NOT_INSTALLED';key=$p.key;depot=$p.depot;before=$p.before;after=(Get-FileHash -LiteralPath $raw).Hash;plan=$p;native_sha256=$nativeSha;game_writes=0;save_writes=0;prefab_lease_preserved=$actualPrefabs}|ConvertTo-Json -Depth 100|Set-Content -LiteralPath (Join-Path $O 'patch.json') -Encoding utf8NoBOM
 'SERIALIZED_'+$p.key
}
