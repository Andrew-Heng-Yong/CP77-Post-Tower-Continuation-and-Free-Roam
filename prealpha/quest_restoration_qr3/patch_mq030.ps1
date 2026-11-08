Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$C=Join-Path $PSScriptRoot 'candidate_01';$O=Join-Path $C 'repair_mq030'
if(Test-Path -LiteralPath $O){throw 'Fresh repair evidence required'}
$reviewPath=Join-Path $PSScriptRoot 'agents/agent_d/reviews/mq030_duplicate_owner.json'
$review=Get-Content -LiteralPath $reviewPath -Raw|ConvertFrom-Json -Depth 60
if($review.status -cne 'APPROVE_NATIVE_RETIREMENT_ACKNOWLEDGED_LEASE_REPAIR'){throw 'Independent approval missing'}
$b=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'baseline.json') -Raw|ConvertFrom-Json -Depth 100
$dep='towercontinued\sidejobs_s23\base_b\mq030.questphase';$raw=Join-Path (Join-Path $C 'archive_source') $dep
$before=(Get-FileHash -LiteralPath $raw).Hash
if($before -cne $b.private_resources.$dep){throw 'Unexpected predecessor'}
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
[IO.Directory]::CreateDirectory($O)|Out-Null
$res=Read-Cr2wFile $raw;Export-Cr2wJson $res (Join-Path $O 'before.json');$g=$res.RootChunk.Graph.Chunk
function EdgesLocal($graph){
 $owners=@{};foreach($h in $graph.Nodes){foreach($s in $h.Chunk.Sockets){$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($s.Chunk)]=[int]$h.Chunk.Id.ToString()}}
 $rows=[Collections.Generic.List[object]]::new()
 foreach($h in $graph.Nodes){foreach($s in $h.Chunk.Sockets){foreach($c in $s.Chunk.Connections){if([object]::ReferenceEquals($c.Chunk.Source.Chunk,$s.Chunk)){$rows.Add(@($owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($s.Chunk)],$s.Chunk.Name.ToString(),$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($c.Chunk.Destination.Chunk)],$c.Chunk.Destination.Chunk.Name.ToString()))}}}}
 return ,$rows.ToArray()
}
function FinishedCondition {return New-FactCondition 'PTFRS23_MQ030_Finished' 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)}
function AddFinishedWakeup($node){
 $condition=[WolvenKit.RED4.Types.questLogicalCondition]::new();$condition.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
 Add-RedHandle $condition.Conditions ($node.Condition.Chunk.DeepCopy())
 Add-RedHandle $condition.Conditions (FinishedCondition)
 Set-RedHandleProperty $node Condition $condition
}
$old=@(EdgesLocal $g|ForEach-Object{$_});$remove=@('1007|Out|1012|In','1020|Out1|1021|In','1021|Out|1020|In1')
foreach($key in $remove){if(@($old|Where-Object{($_ -join '|') -ceq $key}).Count -ne 1){throw ('Missing expected edge '+$key)}}
foreach($id in @(1022,1023)){
 if(@($g.Nodes|Where-Object{[int]$_.Chunk.Id.ToString() -eq $id}).Count){throw 'New ID collision'}
 $node=(Get-QuestNode $g 1004).DeepCopy();$node.Id=[uint16]$id
 foreach($s in $node.Sockets){$s.Chunk.Connections.Clear()}
 Set-RedHandleProperty $node Condition (FinishedCondition);Add-RedHandle $g.Nodes $node
}
$helper=(Get-QuestNode $g 1020).PhaseGraph.Chunk
AddFinishedWakeup (Get-QuestNode $helper 3)
AddFinishedWakeup (Get-QuestNode $g 1021)
$edges=@($old|Where-Object{($_ -join '|') -cnotin $remove})
$edges+=,@(1020,'Out1',1022,'In');$edges+=,@(1022,'True',1012,'In');$edges+=,@(1022,'False',1021,'In')
$edges+=,@(1021,'Out',1023,'In');$edges+=,@(1023,'True',1012,'In');$edges+=,@(1023,'False',1020,'In1')
foreach($h in $g.Nodes){foreach($s in $h.Chunk.Sockets){$s.Chunk.Connections.Clear()}}
foreach($e in $edges){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $e[0]) $e[1]) (Get-QuestSocket (Get-QuestNode $g $e[2]) $e[3]))}
Write-Cr2wFile $res $raw;Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $O 'after.json')
@{depot=$dep;before=$before;after=(Get-FileHash -LiteralPath $raw).Hash;review=$reviewPath;review_sha256=(Get-FileHash -LiteralPath $reviewPath).Hash;new_nodes=@(1022,1023);scope='Native helper retirement acknowledgement precedes lease release; pending rearm wait also wakes on real Finished receipt';game_writes=0;save_writes=0;not_installed=$true}|ConvertTo-Json -Depth 30|Set-Content -LiteralPath (Join-Path $O 'patch.json') -Encoding utf8NoBOM
'SERIALIZED_MQ030_RETIREMENT_LEASE_REPAIR_NOT_INSTALLED'
