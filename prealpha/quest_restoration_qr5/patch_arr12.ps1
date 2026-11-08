Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$C=Join-Path $PSScriptRoot 'candidate_01';$O=Join-Path $C 'repair_arr12'
if(Test-Path -LiteralPath $O){throw 'Fresh repair output required'}
$p=Get-Content -LiteralPath (Join-Path $C 'repair_plan.json') -Raw|ConvertFrom-Json -Depth 100
foreach($pin in @(@{path=$p.proposal;sha=$p.proposal_sha256},@{path=$p.review;sha=$p.review_sha256},@{path=$p.native.binary;sha=$p.native.sha256})){
 if((Get-FileHash -LiteralPath $pin.path).Hash -cne $pin.sha){throw 'Approved input changed'}
}
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
function ClearLocal($n){foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}}
function EdgesLocal($g){
 $owners=@{};foreach($h in $g.Nodes){foreach($s in $h.Chunk.Sockets){$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($s.Chunk)]=[int]$h.Chunk.Id.ToString()}}
 $rows=[Collections.Generic.List[object]]::new()
 foreach($h in $g.Nodes){foreach($s in $h.Chunk.Sockets){foreach($c in $s.Chunk.Connections){if([object]::ReferenceEquals($c.Chunk.Source.Chunk,$s.Chunk)){$rows.Add(@($owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($s.Chunk)],$s.Chunk.Name.ToString(),$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($c.Chunk.Destination.Chunk)],$c.Chunk.Destination.Chunk.Name.ToString()))}}}}
 return ,$rows.ToArray()
}
function RewireLocal($g,$original){
 $edges=@(EdgesLocal $original|ForEach-Object{$_});foreach($h in $g.Nodes){ClearLocal $h.Chunk}
 foreach($e in $edges){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $e[0]) $e[1]) (Get-QuestSocket (Get-QuestNode $g $e[2]) $e[3]))}
 foreach($h in $g.Nodes){$n=$h.Chunk;if($n.GetType().Name -eq 'questPhaseNodeDefinition' -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireLocal $n.PhaseGraph.Chunk (Get-QuestNode $original ([int]$n.Id.ToString())).PhaseGraph.Chunk}}
}
function RemoveLocal($g,[int]$a,[string]$out,[int]$b,[string]$in){
 $s=Get-QuestSocket (Get-QuestNode $g $a) $out;$d=Get-QuestSocket (Get-QuestNode $g $b) $in;$found=@()
 foreach($h in $s.Connections){if([object]::ReferenceEquals($h.Chunk.Source.Chunk,$s) -and [object]::ReferenceEquals($h.Chunk.Destination.Chunk,$d)){$found+=,$h.Chunk}}
 if($found.Count -ne 1){throw 'Expected exactly one approved edge'};$co=$found[0]
 foreach($socket in @($s,$d)){$matches=@();for($i=0;$i -lt $socket.Connections.Count;$i++){if([object]::ReferenceEquals($socket.Connections[$i].Chunk,$co)){$matches+=,$i}};if($matches.Count -ne 1){throw 'Reciprocal edge mismatch'};$socket.Connections.RemoveAt($matches[0])}
}
$raw=Join-Path (Join-Path $C 'archive_source') $p.depot
if((Get-FileHash -LiteralPath $raw).Hash -cne $p.before){throw 'Wrong predecessor bytes'}
$native=Read-Cr2wFile $p.native.binary;$template=Get-QuestNode $native.RootChunk.Graph.Chunk 3
$file=Read-Cr2wFile $raw;$g=(Get-QuestNode $file.RootChunk.Graph.Chunk 10).PhaseGraph.Chunk
foreach($id in $p.new_ids){if(@($g.Nodes|Where-Object{[int]$_.Chunk.Id.ToString() -eq $id}).Count){throw 'Local node ID collision'}}
if($template.PhaseInstancePrefabs.Count -ne 0){throw 'Unexpected native monitor lease'}
[IO.Directory]::CreateDirectory($O)|Out-Null
Export-Cr2wJson $native (Join-Path $O 'native.json');Export-Cr2wJson $file (Join-Path $O 'before.json')
$cond=[WolvenKit.RED4.Types.questLogicalCondition]::new();$cond.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
foreach($f in $p.guard_facts.PSObject.Properties){Add-RedHandle $cond.Conditions (New-FactCondition $f.Name ([int]$f.Value) ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
$guard=(Get-QuestNode $template.PhaseGraph.Chunk 15).DeepCopy();$guard.Id=[uint16]1200;ClearLocal $guard;Set-RedHandleProperty $guard Condition $cond
$claim=New-SetFactNode -Id 1201 -FactName $p.claim_fact -Value 1
$monitor=$template.DeepCopy();$monitor.Id=[uint16]1202;ClearLocal $monitor;RewireLocal $monitor.PhaseGraph.Chunk $template.PhaseGraph.Chunk
RemoveLocal $monitor.PhaseGraph.Chunk 0 'Out' 15 'In'
[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $monitor.PhaseGraph.Chunk 0) 'Out') (Get-QuestSocket (Get-QuestNode $monitor.PhaseGraph.Chunk 13) 'In'))
RemoveLocal $g 65003 'Out' 8 'In'
foreach($n in @($guard,$claim,$monitor)){Add-RedHandle $g.Nodes $n}
foreach($e in @(@(65003,'Out',1200,'In'),@(1200,'True',1201,'In'),@(1201,'Out',1202,'In1'),@(1201,'Out',8,'In'))){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $e[0]) $e[1]) (Get-QuestSocket (Get-QuestNode $g $e[2]) $e[3]))}
Write-Cr2wFile $file $raw;Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $O 'after.json')
@{status='SERIALIZED_FUTURE_EVENT_ONLY_ARR12_MONITOR_NOT_INSTALLED';depot=$p.depot;before=$p.before;after=(Get-FileHash -LiteralPath $raw).Hash;native=$p.native;review=$p.review;review_sha256=$p.review_sha256;guard_facts=$p.guard_facts;new_local_ids=$p.new_ids;retained_native_arm_nodes=@(14,15);native_arm_writes_active=$false;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 100|Set-Content -LiteralPath (Join-Path $O 'patch.json') -Encoding utf8NoBOM
'SERIALIZED_FUTURE_EVENT_ONLY_ARR12_MONITOR'
