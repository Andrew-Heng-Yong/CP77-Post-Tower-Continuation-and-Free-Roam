Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$C=Join-Path $PSScriptRoot 'candidate_02';$O=Join-Path $C 'repair_steven'
if(Test-Path -LiteralPath $O){throw 'Fresh actor evidence required'}
$plan=Get-Content -LiteralPath (Join-Path $C 'actor_repair_plan.json') -Raw|ConvertFrom-Json -Depth 100
foreach($pin in @(@{path=$plan.proposal;sha=$plan.proposal_sha256},@{path=$plan.review;sha=$plan.review_sha256},@{path=$plan.template.binary;sha=$plan.template.sha256})){
 if((Get-FileHash -LiteralPath $pin.path).Hash -cne $pin.sha){throw 'Reviewed input changed'}
}
$p=Get-Content -LiteralPath $plan.proposal -Raw|ConvertFrom-Json -Depth 100
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
function ClearActor($n){foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}}
function RemoveActorEdge($g,[int]$a,[string]$sn,[int]$b,[string]$dn){
 $s=Get-QuestSocket (Get-QuestNode $g $a) $sn;$d=Get-QuestSocket (Get-QuestNode $g $b) $dn;$found=@()
 foreach($ch in $s.Connections){if([object]::ReferenceEquals($ch.Chunk.Source.Chunk,$s) -and [object]::ReferenceEquals($ch.Chunk.Destination.Chunk,$d)){$found+=,$ch.Chunk}}
 if($found.Count -ne 1){throw 'Approved old edge missing/duplicated'};$co=$found[0]
 foreach($sock in @($s,$d)){$indices=@();for($i=0;$i -lt $sock.Connections.Count;$i++){if([object]::ReferenceEquals($sock.Connections[$i].Chunk,$co)){$indices+=,$i}};if($indices.Count -ne 1){throw 'Reciprocal old edge differs'};$sock.Connections.RemoveAt($indices[0])}
}
function GatherActorJournals($c,$list){
 if($c.GetType().Name -eq 'questJournalCondition'){$list.Add($c.DeepCopy());return}
 if($c.GetType().Name -eq 'questLogicalCondition'){foreach($h in $c.Conditions){GatherActorJournals $h.Chunk $list}}
}
function AllActor(){ $x=[WolvenKit.RED4.Types.questLogicalCondition]::new();$x.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND;return $x }
$raw=Join-Path (Join-Path $C 'archive_source') $plan.depot
if((Get-FileHash -LiteralPath $raw).Hash -cne $plan.before){throw 'Wrong carrier source'}
$file=Read-Cr2wFile $raw;$boot=Read-Cr2wFile $plan.template.binary;$template=Get-QuestNode $boot.RootChunk.Graph.Chunk 100
$g=(Get-QuestNode $file.RootChunk.Graph.Chunk 50).PhaseGraph.Chunk
foreach($id in $p.new_parent_local_ids){if(@($g.Nodes|Where-Object{[int]$_.Chunk.Id.ToString() -eq $id}).Count){throw 'New local ID collision'}}
$journals=[Collections.Generic.List[object]]::new();GatherActorJournals (Get-QuestNode $boot.RootChunk.Graph.Chunk 2).Condition.Chunk $journals
if($journals.Count -ne $p.initial_guard_journals.Count){throw 'Original journal guard shape differs'}
$initial=AllActor
foreach($f in $p.initial_guard_facts.PSObject.Properties){Add-RedHandle $initial.Conditions (New-FactCondition $f.Name ([int]$f.Value) ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
foreach($j in $journals){Add-RedHandle $initial.Conditions ($j.DeepCopy())}
$guard=New-ConditionNode 1300 $initial;$claim=New-SetFactNode 1301 $p.claim_fact 1
$helper=$template.DeepCopy();$helper.Id=[uint16]1302;ClearActor $helper
$hg=[WolvenKit.RED4.Types.questGraphDefinition]::new()
foreach($id in $p.helper_template.retain_nodes){$n=(Get-QuestNode $template.PhaseGraph.Chunk $id).DeepCopy();ClearActor $n;Add-RedHandle $hg.Nodes $n}
$lateCondition=AllActor
foreach($f in $p.helper_graph_change.late_guard_facts){$cmp=[Enum]::Parse([WolvenKit.RED4.Types.Enums+EComparisonType],$f.comparison);Add-RedHandle $lateCondition.Conditions (New-FactCondition $f.fact ([int]$f.value) $cmp)}
$rootJournal=@($journals|Where-Object{$_.Type.Chunk.Path.Chunk.RealPath.ToString() -ceq $p.helper_graph_change.late_guard_journal.path})
if($rootJournal.Count -ne 1){throw 'Root journal template ambiguous'}
$states=[WolvenKit.RED4.Types.questLogicalCondition]::new();$states.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
foreach($state in $p.helper_graph_change.late_guard_journal.states){$j=$rootJournal[0].DeepCopy();$j.Type.Chunk.State=[Enum]::Parse([WolvenKit.RED4.Types.Enums+gameJournalEntryState],$state);Add-RedHandle $states.Conditions $j}
Add-RedHandle $lateCondition.Conditions $states
$late=(Get-QuestNode $template.PhaseGraph.Chunk 19).DeepCopy();$late.Id=[uint16]1303;ClearActor $late;Set-RedHandleProperty $late Condition $lateCondition;Add-RedHandle $hg.Nodes $late
foreach($e in @(@(0,'Out',19,'In'),@(19,'Out',1303,'In'),@(1303,'Out',17,'In1'),@(17,'Out1',19,'In'))){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $hg $e[0]) $e[1]) (Get-QuestSocket (Get-QuestNode $hg $e[2]) $e[3]))}
Set-RedHandleProperty $helper PhaseGraph $hg
[IO.Directory]::CreateDirectory($O)|Out-Null
Export-Cr2wJson $file (Join-Path $O 'before.json');Export-Cr2wJson $boot (Join-Path $O 'template.json')
foreach($e in $p.parent_removed_edges){RemoveActorEdge $g $e[0] $e[1] $e[2] $e[3]}
foreach($n in @($guard,$claim,$helper)){Add-RedHandle $g.Nodes $n}
foreach($e in $p.parent_added_edges){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $e[0]) $e[1]) (Get-QuestSocket (Get-QuestNode $g $e[2]) $e[3]))}
Write-Cr2wFile $file $raw;Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $O 'after.json')
@{status='SERIALIZED_FUTURE_U9_NIGHTCITY_ACTOR_ONLY_HELPER_NOT_INSTALLED';depot=$plan.depot;before=$plan.before;after=(Get-FileHash -LiteralPath $raw).Hash;proposal=$plan.proposal;proposal_sha256=$plan.proposal_sha256;review=$plan.review;review_sha256=$plan.review_sha256;new_parent_ids=$p.new_parent_local_ids;new_child_id=1303;removed_edges=$p.parent_removed_edges;added_edges=$p.parent_added_edges;claim_fact=$p.claim_fact;template=$plan.template;no_new_native_SMS_or_reward=$true;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 100|Set-Content -LiteralPath (Join-Path $O 'patch.json') -Encoding utf8NoBOM
'SERIALIZED_FUTURE_U9_NIGHTCITY_ACTOR_ONLY_HELPER'
