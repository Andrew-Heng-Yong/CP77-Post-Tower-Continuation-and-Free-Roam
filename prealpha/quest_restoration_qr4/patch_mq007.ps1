Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$C=Join-Path $PSScriptRoot 'candidate_01';$O=Join-Path $C 'repair_mq007'
if(Test-Path -LiteralPath $O){throw 'Fresh repair output required'}
$plan=Get-Content -LiteralPath (Join-Path $C 'repair_plan.json') -Raw|ConvertFrom-Json -Depth 40
$proposal=Get-Content -LiteralPath $plan.proposal -Raw|ConvertFrom-Json -Depth 100
if((Get-FileHash -LiteralPath $plan.review).Hash -cne $plan.review_sha256 -or (Get-FileHash -LiteralPath $plan.proposal).Hash -cne $plan.proposal_sha256){throw 'Review/proposal changed'}
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
function ClearLocal($n){foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}}
function EdgesLocal($g){
 $owners=@{};foreach($h in $g.Nodes){foreach($s in $h.Chunk.Sockets){$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($s.Chunk)]=[int]$h.Chunk.Id.ToString()}}
 $rows=[Collections.Generic.List[object]]::new()
 foreach($h in $g.Nodes){foreach($s in $h.Chunk.Sockets){foreach($c in $s.Chunk.Connections){if([object]::ReferenceEquals($c.Chunk.Source.Chunk,$s.Chunk)){$rows.Add(@($owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($s.Chunk)],$s.Chunk.Name.ToString(),$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($c.Chunk.Destination.Chunk)],$c.Chunk.Destination.Chunk.Name.ToString()))}}}}
 return ,$rows.ToArray()
}
function RewireLocal($g,$original){
 $edges=@(EdgesLocal $original|ForEach-Object{$_})
 foreach($h in $g.Nodes){ClearLocal $h.Chunk}
 foreach($e in $edges){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $e[0]) $e[1]) (Get-QuestSocket (Get-QuestNode $g $e[2]) $e[3]))}
 foreach($h in $g.Nodes){$n=$h.Chunk;if($n.GetType().Name -eq 'questPhaseNodeDefinition' -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireLocal $n.PhaseGraph.Chunk (Get-QuestNode $original ([int]$n.Id.ToString())).PhaseGraph.Chunk}}
}
$nativePath=[IO.Path]::GetFullPath($proposal.native_source.binary)
if((Get-FileHash -LiteralPath $nativePath).Hash -cne $proposal.native_source.sha256){throw 'Native source changed'}
$native=Read-Cr2wFile $nativePath;$template=Get-QuestNode $native.RootChunk.Graph.Chunk 14
if($template.PhaseInstancePrefabs.Count -ne 0){throw 'Unexpected outer prefab lease'}
$inner=Get-QuestNode $template.PhaseGraph.Chunk 3
if($inner.PhaseInstancePrefabs.Count -ne 1 -or $inner.PhaseInstancePrefabs[0].PrefabNodeRef.ToString() -cne '#mq007_pr_gun_re_acquiring'){throw 'Native helper lease unexpected'}
[IO.Directory]::CreateDirectory($O)|Out-Null
Export-Cr2wJson $native (Join-Path $O 'native_bugfix.json')
$changes=@();$index=0
foreach($r in $proposal.resources){
 $index++;$raw=Join-Path (Join-Path $C 'archive_source') $r.resource
 if((Get-FileHash -LiteralPath $raw).Hash -cne $r.source_pin.sha256){throw 'Wrong predecessor'}
 $file=Read-Cr2wFile $raw;$g=$file.RootChunk.Graph.Chunk
 $prefix=if($index -eq 1){'fresh'}else{'resume'}
 Export-Cr2wJson $file (Join-Path $O ($prefix+'_before.json'))
 foreach($id in $plan.node_ids){if(@($g.Nodes|Where-Object{[int]$_.Chunk.Id.ToString() -eq $id}).Count){throw 'Local node ID collision'}}
 if(@($g.Nodes|Where-Object{$_.Chunk.GetType().Name -eq 'questOutputNodeDefinition'}).Count){throw 'Caller root may terminate continuation'}
 $condition=[WolvenKit.RED4.Types.questLogicalCondition]::new();$condition.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
 foreach($f in $r.enrollment_guard.facts_equal.PSObject.Properties){Add-RedHandle $condition.Conditions (New-FactCondition $f.Name ([int]$f.Value) ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
 $guard=(Get-QuestNode $g 1100).DeepCopy();$guard.Id=[uint16]1200;ClearLocal $guard;Set-RedHandleProperty $guard Condition $condition
 $claim=New-SetFactNode -Id 1201 -FactName $plan.shared_claim -Value 1
 $continuation=$template.DeepCopy();$continuation.Id=[uint16]1202;ClearLocal $continuation
 RewireLocal $continuation.PhaseGraph.Chunk $template.PhaseGraph.Chunk
 $finish=New-SetFactNode -Id 1203 -FactName $plan.owned_finish -Value 1
 foreach($node in @($guard,$claim,$continuation,$finish)){Add-RedHandle $g.Nodes $node}
 [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g 1101) 'Out') (Get-QuestSocket $guard 'In'))
 [void](Connect-QuestSockets (Get-QuestSocket $guard 'True') (Get-QuestSocket $claim 'In'))
 [void](Connect-QuestSockets (Get-QuestSocket $claim 'Out') (Get-QuestSocket $continuation 'In1'))
 [void](Connect-QuestSockets (Get-QuestSocket $continuation 'Out1') (Get-QuestSocket $finish 'In'))
 Write-Cr2wFile $file $raw
 Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $O ($prefix+'_after.json'))
 $changes+=,@{depot=$r.resource;before=$r.source_pin.sha256;after=(Get-FileHash -LiteralPath $raw).Hash;prefix=$prefix;preserved_native_helper='#mq007_pr_gun_re_acquiring';world_container_owner_added=$false;scope=$plan.scope}
}
@{status='SERIALIZED_FUTURE_ENTRY_ONLY_MQ007_CONTINUATION_NOT_INSTALLED';resources=$changes;native_sha256=$proposal.native_source.sha256;review=$plan.review;review_sha256=$plan.review_sha256;game_writes=0;save_writes=0;new_local_ids=$plan.node_ids}|ConvertTo-Json -Depth 40|Set-Content -LiteralPath (Join-Path $O 'patch.json') -Encoding utf8NoBOM
'SERIALIZED_FUTURE_ENTRY_ONLY_NATIVE_MQ007_CONTINUATION'
