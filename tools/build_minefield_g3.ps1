param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\gig_restoration\minefield_g3';$out=Join-Path $WorkspaceRoot 'build\MinefieldG3';$source=Join-Path $out 'source'
if(Test-Path (Join-Path $audit 'install_receipt.json')){throw 'Installed evidence pinned'}
New-Item -ItemType Directory -Force $source|Out-Null
$raw=Join-Path $WorkspaceRoot 'research\gig_restoration\fresh_candidates\local_sources\raw\base\open_world\street_stories\badlands\inland_avenue\sts_bls_inland_avenue.questphase'
$native=Read-Cr2wFile $raw;$prefix='towercontinued\minefield_g3\'
function ClearG3($n){foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}}
function LinkG3($g,$f,$s,$t,$d='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $f) $s) (Get-QuestSocket (Get-QuestNode $g $t) $d))}
function EdgesG3($g){
 $owners=@{};foreach($h in $g.Nodes){foreach($s in $h.Chunk.Sockets){$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($s.Chunk)]=[int]$h.Chunk.Id.ToString()}}
 $rows=[Collections.Generic.List[object]]::new()
 foreach($h in $g.Nodes){foreach($s in $h.Chunk.Sockets){foreach($c in $s.Chunk.Connections){if([object]::ReferenceEquals($c.Chunk.Source.Chunk,$s.Chunk)){$rows.Add(@($owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($s.Chunk)],$s.Chunk.Name.ToString(),$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($c.Chunk.Destination.Chunk)],$c.Chunk.Destination.Chunk.Name.ToString()))}}}}
 return ,$rows.ToArray()
}
function RebuildG3($g,$edges){foreach($h in $g.Nodes){ClearG3 $h.Chunk};foreach($e in $edges){LinkG3 $g $e[0] $e[1] $e[2] $e[3]}}
function RewireG3($g,$original){
 RebuildG3 $g @(EdgesG3 $original|ForEach-Object {$_})
 foreach($h in $g.Nodes){$n=$h.Chunk;if($n.GetType().Name -eq 'questPhaseNodeDefinition' -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireG3 $n.PhaseGraph.Chunk (Get-QuestNode $original ([int]$n.Id.ToString())).PhaseGraph.Chunk}}
}
function AllG3($pairs){$c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND;foreach($k in $pairs.Keys){Add-RedHandle $c.Conditions (New-FactCondition $k $pairs[$k] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))};return $c}
function EqFactsG3($a,$b){$v=[WolvenKit.RED4.Types.questVarVsVarComparison_ConditionType]::new();$v.FactName1=$a;$v.FactName2=$b;$v.ComparisonType=[WolvenKit.RED4.Types.Enums+EComparisonType]::Equal;$c=[WolvenKit.RED4.Types.questFactsDBCondition]::new();Set-RedHandleProperty $c Type $v;return $c}
function AddGateG3($g,$id,$condition){Add-RedHandle $g.Nodes (New-ConditionNode $id $condition)}
$roots=@{};$names=@('native_owner','ow','gameplay');$indices=@(24,5,20)
for($i=0;$i -lt 3;$i++){$root=$native.EmbeddedFiles[$indices[$i]].Content.DeepCopy();RewireG3 $root.Graph.Chunk $native.EmbeddedFiles[$indices[$i]].Content.Graph.Chunk;$roots[$names[$i]]=$root}
$changes=[Collections.Generic.List[object]]::new()
# Skip initial ready/start additions and discovery/briefing work. Existing ready
# is an actual GPL input dependency, checked by the script and boot condition.
$ow=$roots.ow.Graph.Chunk;$edges=@(EdgesG3 $ow|ForEach-Object {$_})
$edges=@($edges|Where-Object {-not ($_[0] -eq 0 -and $_[2] -eq 10)})
$edges+=,@(0,'Out',11,'In1');$edges+=,@(0,'Out',18,'In1')
# One native completion payout. Failure output bypasses it, as in stock.
foreach($n in @((New-ConditionNode 400 (AllG3 ([ordered]@{PTFRG3_RewardClaim=0;PTFRG3_RewardAck=0;PTFRG3_Fault=0}))), (New-SetFactNode 401 'PTFRG3_RewardClaim' 1),(New-SetFactNode 402 'PTFRG3_RewardAck' 1),(New-SetFactNode 403 'PTFRG3_RewardReplayRefused' 1))){Add-RedHandle $ow.Nodes $n}
$edges=@($edges|Where-Object {-not ($_[0] -eq 11 -and $_[1] -eq 'Out1') -and $_[0] -ne 17})
foreach($e in @(@(11,'Out1',400,'In'),@(400,'True',401,'In'),@(401,'Out',17,'In'),@(17,'Out',402,'In'),@(402,'Out',13,'In1'),@(400,'False',403,'In'))){$edges+=,$e}
RebuildG3 $ow $edges
$play=(Get-QuestNode $ow 11).PhaseGraph.Chunk;$edges=@(EdgesG3 $play|ForEach-Object {$_})
# Saved briefing already happened. Native success/failure debrief text routes
# avoid global Dakota holocall facts entirely, including RET/INT retries.
$edges=@($edges|Where-Object {-not ($_[0] -eq 0 -and $_[2] -eq 598)})
foreach($e in $edges){if($e[2] -eq 557 -and $e[3] -eq 'Start 0'){$e[2]=603;$e[3]='Active'}}
$new=[Collections.Generic.List[object]]::new()
foreach($e in $edges){if($e[2] -eq 550 -and $e[3] -eq 'Start 0'){$new.Add(@($e[0],$e[1],606,'In'));$new.Add(@($e[0],$e[1],607,'In'))}else{$new.Add($e)}}
$edges=$new.ToArray()
# Stock includes a detached cross-gig antenna-car deactivation. No G3 owner
# ever acquires this Radar Love entry, so it remains an unconnected node.
$edges=@($edges|Where-Object {-not ($_[0] -eq 645 -and $_[2] -eq 590)})
RebuildG3 $play $edges
# Do not repeat an already-finished body investigation/comment (additive scan).
$parallel=(Get-QuestNode $ow 18).PhaseGraph.Chunk;$edges=@(EdgesG3 $parallel|ForEach-Object {$_})
AddGateG3 $parallel 400 (New-FactCondition '#ina_07_body_scan' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
$edges=@($edges|Where-Object {-not ($_[0] -eq 0 -and $_[2] -eq 25)})
$edges+=,@(0,'Out',400,'In');$edges+=,@(400,'True',25,'In');RebuildG3 $parallel $edges
# Separate derived fixer and achievement baselines; they need not be equal.
$cleanup=(Get-QuestNode $ow 13).PhaseGraph.Chunk;$edges=@(EdgesG3 $cleanup|ForEach-Object {$_})
$account=AllG3 ([ordered]@{PTFRG3_AccountClaim=0;PTFRG3_AccountAck=0;PTFRG3_Fault=0})
Add-RedHandle $account.Conditions (EqFactsG3 'PTFRG3_CountBase' 'bls_sts_counter')
Add-RedHandle $account.Conditions (EqFactsG3 'PTFRG3_AchBase' 'bls_achievement')
foreach($n in @((New-ConditionNode 400 $account),(New-SetFactNode 401 'PTFRG3_AccountClaim' 1),(New-SetFactNode 402 'PTFRG3_AccountAck' 1),(New-SetFactNode 403 'PTFRG3_Fault' 1),(New-SetFactNode 404 'PTFRG3_AccountRequest' 1))){Add-RedHandle $cleanup.Nodes $n}
$accountWait=(Get-QuestNode $cleanup 29).DeepCopy();$accountWait.Id=[uint16]405;ClearG3 $accountWait;Set-RedHandleProperty $accountWait Condition (New-FactCondition 'PTFRG3_AccountReady' 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal));Add-RedHandle $cleanup.Nodes $accountWait
$edges=@($edges|Where-Object {-not ($_[2] -eq 9) -and $_[0] -ne 9})
foreach($e in @(@(3,'Out',404,'In'),@(17,'Out',404,'In'),@(404,'Out',405,'In'),@(405,'Out',400,'In'),@(400,'True',401,'In'),@(401,'Out',9,'In'),@(9,'Out',402,'In'),@(402,'Out',28,'In'),@(400,'False',403,'In'))){$edges+=,$e};RebuildG3 $cleanup $edges
# Borrow flags precede each native shared-patrol combat command. Cleanup only
# targets a patrol actor if this owner entered its command and it is still present.
$release=(Get-QuestNode $cleanup 25).PhaseGraph.Chunk
$borrow=@{};$keys=@();$releaseNodes=@(11,12,13,14,15,16)
foreach($id in $releaseNodes){$n=Get-QuestNode $release $id;$key=$n.EntityReference.Reference.ToString()+'|'+$n.EntityReference.Names[0].ToString();$borrow[$key]=$keys.Count;$keys+=,$key}
foreach($path in @(@(7,54),@(9,140))){
 $g=(Get-QuestNode (Get-QuestNode $roots.gameplay.Graph.Chunk $path[0]).PhaseGraph.Chunk $path[1]).PhaseGraph.Chunk
 $edges=@(EdgesG3 $g|ForEach-Object {$_})
 foreach($id in @(10,11,12,13,14,15)){
  $n=Get-QuestNode $g $id;$key=$n.EntityReference.Reference.ToString()+'|'+$n.EntityReference.Names[0].ToString();if(-not $borrow.ContainsKey($key)){throw 'Unmatched shared combat target'}
  $flag=400+$id;Add-RedHandle $g.Nodes (New-SetFactNode $flag ('PTFRG3_Borrow'+$borrow[$key]) 1)
  foreach($e in $edges){if($e[2] -eq $id -and $e[3] -eq 'In'){$e[2]=$flag}}
  $edges+=,@($flag,'Out',$id,'In')
 }
 RebuildG3 $g $edges
}
$spawnCondition=(Get-QuestNode $roots.native_owner.Graph.Chunk 273).Condition.Chunk
$edges=@(EdgesG3 $release|ForEach-Object {$_})
for($i=0;$i -lt 6;$i++){
 $id=$releaseNodes[$i];$cond=AllG3 ([ordered]@{('PTFRG3_Borrow'+$i)=1})
 $spawn=$spawnCondition.DeepCopy();$spawn.Type.Chunk.ObjectRef=(Get-QuestNode $release $id).EntityReference.DeepCopy();$spawn.Type.Chunk.ComparisonParams.Chunk.EntireCommunity=[WolvenKit.RED4.Types.CBool]::op_Implicit($false)
 Add-RedHandle $cond.Conditions $spawn;AddGateG3 $release (400+$i) $cond
 foreach($e in $edges){if($e[2] -eq $id -and $e[3] -eq 'In'){$e[2]=400+$i}}
 $next=if($i -eq 5){1}else{400+$i+1}
 $edges+=,@((400+$i),'True',$id,'In');$edges+=,@((400+$i),'False',$next,'In')
}
RebuildG3 $release $edges
# Keep the original physical prefab/vehicle/OW-GPL owner. Existing vehicle
# skips visual damage; a newly activated entry receives absolute, not accumulated,
# authored deformation. Neither path resets HP, loot or a car outcome.
$parent=$roots.native_owner.Graph.Chunk;$edges=@(EdgesG3 $parent|ForEach-Object {$_})
AddGateG3 $parent 400 ($spawnCondition.DeepCopy())
AddGateG3 $parent 402 (New-FactCondition 'PTFRG3_NewCar' 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
Add-RedHandle $parent.Nodes (New-SetFactNode 410 'PTFRG3_NewCar' 1)
$edges=@($edges|Where-Object {-not ($_[0] -eq 1) -and -not ($_[0] -eq 270 -and $_[2] -eq 264) -and $_[0] -ne 282 -and $_[0] -ne 251})
foreach($e in @(@(1,'Out',400,'In'),@(400,'True',275,'In'),@(400,'False',410,'In'),@(410,'Out',254,'In'),@(270,'Out',402,'In'),@(402,'True',264,'In'),@(402,'False',253,'In'),@(282,'Out',117,'In1'),@(282,'Out',118,'In1'))){$edges+=,$e}
(Get-QuestNode $parent 264).Event.Chunk.Accumulate=[WolvenKit.RED4.Types.CBool]::op_Implicit($false)
(Get-QuestNode $parent 275).Type.Chunk.Phase=[WolvenKit.RED4.Types.Enums+gamedataMappinPhase]::DiscoveredPhase
foreach($id in @(117,118)){(Get-QuestNode $parent $id).PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($prefix+$(if($id -eq 117){'gameplay'}else{'ow'})+'.questphase')}
RebuildG3 $parent $edges
$roots.owner=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$g=[WolvenKit.RED4.Types.questGraphDefinition]::new();Set-RedHandleProperty $roots.owner Graph $g
foreach($n in @((New-InputNode 0 'In1'),(New-OutputNode 1 'Out1'))){Add-RedHandle $g.Nodes $n}
$child=(Get-QuestNode $parent 118).DeepCopy();$child.Id=[uint16]405;ClearG3 $child;$child.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($prefix+'native_owner.questphase');Add-RedHandle $g.Nodes $child
$guardFacts=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRG3_Request=1;PTFRG3_Started=0;PTFRG3_Fault=0;PTFRG3_RewardClaim=0;PTFRG3_AccountClaim=0;ina_07_finished=0;ina_07_failed=0;ina_07_perfect=0;ina_07_test_def=0;sts_bls_ina_07_delivery_status=0;sts_bls_ina_07_chase_spawned=0;sts_bls_ina_07_reworked_chase_triggered=0}
$guard=AllG3 $guardFacts
foreach($name in @('ina_07_start','#ina_07_ready')){Add-RedHandle $guard.Conditions (New-FactCondition $name 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Greater))}
# No boot equality on incidental totals: accounting snapshots them only at its
# completion handshake. An unrelated achievement before owner start is safe.
$pause=(Get-QuestNode (Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase')).RootChunk.Graph.Chunk 106).DeepCopy();$pause.Id=[uint16]402;ClearG3 $pause;Set-RedHandleProperty $pause Condition $guard
foreach($n in @((New-SetFactNode 400 'PTFRG3_Ready' 1),(New-SetFactNode 401 'PTFRG3_NativeRevision' 1),$pause,(New-SetFactNode 403 'PTFRG3_Started' 1),(New-SetFactNode 404 'PTFRG3_OwnerFinished' 1))){Add-RedHandle $g.Nodes $n}
RebuildG3 $g @(@(0,'Out',400,'In'),@(400,'Out',401,'In'),@(401,'Out',402,'In'),@(402,'Out',403,'In'),@(403,'Out',405,'In1'),@(405,'Out1',404,'In'),@(404,'Out',1,'In'))
$names+=,'owner';$resources=@()
foreach($name in $names){$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$roots[$name];$depot=$prefix+$name+'.questphase';$resources+=,$depot;Write-Cr2wFile $file (Join-Path $source $depot);Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) (Join-Path $audit ($name+'.questphase.json'))}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$archive=Join-Path $out 'TowerContinued_MinefieldG3.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError'){throw 'Readback failed'}
if(@(Compare-Object @($resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Archive scope mismatch'}
foreach($entry in $packed.Files.Values){$m=[IO.MemoryStream]::new();try{$entry.Extract($m);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray())) -ne (Get-FileHash (Join-Path $source $entry.Name)).Hash){throw 'Packed mismatch'}}finally{$m.Dispose()}}
$manifest=[ordered]@{status='BUILT_G3_EARLY_CONTINUATION_LIVE_PENDING';archive_sha256=(Get-FileHash $archive).Hash;native_raw_sha256=(Get-FileHash $raw).Hash;resources=$resources;packed_readback=$true;native_guard=$guardFacts;separate_derived_baselines=$true;shared_targets=$keys;completed_replay=$false;vanilla_replacements=@();game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($manifest|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false));[pscustomobject]$manifest|Select-Object status,archive_sha256,packed_readback|ConvertTo-Json
