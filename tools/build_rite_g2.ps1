param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\gig_restoration\rite_g2'
$out=Join-Path $WorkspaceRoot 'build\RiteG2';$source=Join-Path $out 'source'
if(Test-Path (Join-Path $audit 'install_receipt.json')){throw 'Installed evidence pinned; do not rebuild'}
New-Item -ItemType Directory -Force $audit,$source|Out-Null
$raw=Join-Path $WorkspaceRoot 'research\gig_restoration\watson_sources\raw\base\open_world\street_stories\watson\northside_industrial_district\sts_wat_northside_industrial_district.questphase'
if((Get-FileHash $raw).Hash -ne '43D163168D0241F3B7E56C1D116575B65E0C488FDA14498F709828C943126DF5'){throw 'Native district changed'}
$native=Read-Cr2wFile $raw;$prefix='towercontinued\rite_g2\'
function ClearG2($n){foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}}
function LinkG2($g,$from,$socket,$to,$dest='In'){
 [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $from) $socket) (Get-QuestSocket (Get-QuestNode $g $to) $dest))
}
function EdgesG2($g){
 $owners=@{};foreach($h in $g.Nodes){foreach($s in $h.Chunk.Sockets){$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($s.Chunk)]=$h.Chunk.Id.ToString()}}
 $rows=[Collections.Generic.List[object]]::new()
 foreach($h in $g.Nodes){foreach($s in $h.Chunk.Sockets){foreach($c in $s.Chunk.Connections){
  if([object]::ReferenceEquals($c.Chunk.Source.Chunk,$s.Chunk)){$rows.Add(@([int]$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($s.Chunk)],$s.Chunk.Name.ToString(),[int]$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($c.Chunk.Destination.Chunk)],$c.Chunk.Destination.Chunk.Name.ToString()))}
 }}}
 return ,$rows.ToArray()
}
function RebuildG2($g,$edges){foreach($h in $g.Nodes){ClearG2 $h.Chunk};foreach($e in $edges){LinkG2 $g $e[0] $e[1] $e[2] $e[3]}}
function RewireG2($g,$original){
 RebuildG2 $g @(EdgesG2 $original|ForEach-Object {$_})
 foreach($h in $g.Nodes){$n=$h.Chunk;if($n.GetType().Name -eq 'questPhaseNodeDefinition' -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireG2 $n.PhaseGraph.Chunk (Get-QuestNode $original ([int]$n.Id.ToString())).PhaseGraph.Chunk}}
}
function AllFactsG2($pairs){
 $c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
 foreach($k in $pairs.Keys){Add-RedHandle $c.Conditions (New-FactCondition $k $pairs[$k] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))};return $c
}
$roots=@{};$names=@('native_owner','ow','combat');$indices=@(26,2,22)
for($i=0;$i -lt 3;$i++){$root=$native.EmbeddedFiles[$indices[$i]].Content.DeepCopy();RewireG2 $root.Graph.Chunk $native.EmbeddedFiles[$indices[$i]].Content.Graph.Chunk;$roots[$names[$i]]=$root}
# This save already passed the native outer trigger/setup. Do not repeat its
# checkpoint or ForcePower operations on the three clinic doors.
$owRoot=$roots.ow.Graph.Chunk
$edges=@(EdgesG2 $owRoot|ForEach-Object {$_})
$edges=@($edges|Where-Object {-not ($_[0] -eq 0 -and $_[2] -eq 2)})
$edges+=,@(0,'Out',3,'In1');RebuildG2 $owRoot $edges
# Resume before clinic entry; briefing, start flag and description initialization
# are not repeated. The existing device PS and owned keycard are required.
$play=(Get-QuestNode $roots.ow.Graph.Chunk 3).PhaseGraph.Chunk
$edges=@(EdgesG2 $play|ForEach-Object {$_})
$edges=@($edges|Where-Object {-not ($_[0] -eq 0 -and $_[2] -in @(105,134,146))})
$edges+=,@(0,'Out',42,'In');$edges+=,@(0,'Out',102,'In')
RebuildG2 $play $edges
# These run before the native briefing even on an early-stage save. Never grant
# the keycard again or reinject the two readable shards into Enemy9.
$setup=(Get-QuestNode $roots.combat.Graph.Chunk 2).PhaseGraph.Chunk
$edges=@(EdgesG2 $setup|ForEach-Object {$_})
$edges=@($edges|Where-Object {-not ($_[0] -eq 5 -and $_[2] -in @(6,7))})
$edges+=,@(5,'Out',8,'In2');$edges+=,@(5,'Out',8,'In3');RebuildG2 $setup $edges
$encounter=(Get-QuestNode $roots.combat.Graph.Chunk 3).PhaseGraph.Chunk
$edges=@(EdgesG2 $encounter|ForEach-Object {$_})
RebuildG2 $encounter @($edges|Where-Object {-not ($_[0] -eq 0 -and $_[2] -eq 17)})
# Native text debrief is an authored muted-phone route. No global phone restart.
$cleanup=(Get-QuestNode $roots.ow.Graph.Chunk 5).PhaseGraph.Chunk
$edges=@(EdgesG2 $cleanup|ForEach-Object {$_})
foreach($e in $edges){if($e[0] -eq 62 -and $e[1] -eq 'False'){$e[2]=61;$e[3]='Active'}}
# The native achievement increment must observe the captured 4 baseline;
# two native guards plus claim/ack make its additive operation one-shot.
$account=[WolvenKit.RED4.Types.questLogicalCondition]::new();$account.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
foreach($b in @(4)){Add-RedHandle $account.Conditions (AllFactsG2 ([ordered]@{PTFRG2_CountBase=$b;wat_sts_counter=$b;wat_achievement=$b;PTFRG2_AccountClaim=0;PTFRG2_AccountAck=0;PTFRG2_Fault=0}))}
foreach($n in @((New-ConditionNode 400 $account),(New-SetFactNode 401 'PTFRG2_AccountClaim' 1),(New-SetFactNode 402 'PTFRG2_AccountAck' 1),(New-SetFactNode 403 'PTFRG2_Fault' 1),
 (New-ConditionNode 410 (AllFactsG2 ([ordered]@{PTFRG2_RewardClaim=0;PTFRG2_RewardAck=0;PTFRG2_Fault=0}))),
 (New-SetFactNode 411 'PTFRG2_RewardClaim' 1),(New-SetFactNode 412 'PTFRG2_RewardAck' 1),(New-SetFactNode 413 'PTFRG2_RewardReplayRefused' 1))){Add-RedHandle $cleanup.Nodes $n}
$edges=@($edges|Where-Object {-not ($_[0] -eq 16 -and $_[2] -eq 12) -and -not ($_[0] -eq 12) -and $_[2] -ne 46 -and -not ($_[0] -eq 46 -and $_[2] -eq 63)})
foreach($e in @(@(16,'Out',400,'In'),@(400,'True',401,'In'),@(401,'Out',12,'In'),@(12,'Out',402,'In'),@(402,'Out',14,'In'),@(402,'Out',52,'In'),@(400,'False',403,'In'),
 @(61,'Out',410,'In'),@(45,'End 0',410,'In'),@(410,'True',411,'In'),@(411,'Out',46,'In'),@(46,'Out',412,'In'),@(412,'Out',63,'In'),@(410,'False',413,'In'))){$edges+=,$e}
RebuildG2 $cleanup $edges
# Original nine-node physical owner, typo binding and native combat lifecycle.
$parent=$roots.native_owner.Graph.Chunk
foreach($id in @(9,10)){$n=Get-QuestNode $parent $id;$n.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($prefix+$(if($id -eq 9){'combat'}else{'ow'})+'.questphase')}
$roots.owner=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$g=[WolvenKit.RED4.Types.questGraphDefinition]::new();Set-RedHandleProperty $roots.owner Graph $g
foreach($n in @((New-InputNode 0 'In1'),(New-OutputNode 1 'Out1'))){Add-RedHandle $g.Nodes $n}
$child=(Get-QuestNode $parent 10).DeepCopy();$child.Id=[uint16]405;ClearG2 $child
foreach($s in $child.Sockets){if($s.Chunk.Name.ToString() -eq 'In1'){$s.Chunk.Name=[WolvenKit.RED4.Types.CName]::op_Implicit('IN')};if($s.Chunk.Name.ToString() -eq 'Out1'){$s.Chunk.Name=[WolvenKit.RED4.Types.CName]::op_Implicit('OUT')}}
$child.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($prefix+'native_owner.questphase');Add-RedHandle $g.Nodes $child
$guardFacts=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRG2_Request=1;PTFRG2_Started=0;PTFRG2_Fault=0;PTFRG2_RewardClaim=0;PTFRG2_AccountClaim=0;PTFRG2_CountBase=4;wat_sts_counter=4;wat_achievement=4;nid_02_finished=1;PTFRG1_CounterAck=1;PTFRG1_RewardClaim=1;PTFRG1_RewardAck=1;nid_05_start=1;nid_05_finished=0;sts_wat_kab_nid_05_combat=0;nid_05_after_holocall=0;nid_05_gang_retaliation=0;sts_wat_nid_05_ce_after_start=0}
$guard=AllFactsG2 $guardFacts
$pause=(Get-QuestNode (Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase')).RootChunk.Graph.Chunk 106).DeepCopy()
$pause.Id=[uint16]402;ClearG2 $pause;Set-RedHandleProperty $pause Condition $guard
foreach($n in @((New-SetFactNode 400 'PTFRG2_Ready' 1),(New-SetFactNode 401 'PTFRG2_NativeRevision' 1),$pause,(New-SetFactNode 403 'PTFRG2_Started' 1),(New-SetFactNode 404 'PTFRG2_OwnerFinished' 1))){Add-RedHandle $g.Nodes $n}
RebuildG2 $g @(@(0,'Out',400,'In'),@(400,'Out',401,'In'),@(401,'Out',402,'In'),@(402,'Out',403,'In'),@(403,'Out',405,'IN'),@(405,'OUT',404,'In'),@(404,'Out',1,'In'))
$names+=,'owner';$resources=@()
foreach($name in $names){$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$roots[$name];$depot=$prefix+$name+'.questphase';$resources+=,$depot;Write-Cr2wFile $file (Join-Path $source $depot);Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) (Join-Path $audit ($name+'.questphase.json'))}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$archive=Join-Path $out 'TowerContinued_RiteG2.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError'){throw 'Readback failed'}
if(@(Compare-Object @($resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Archive scope mismatch'}
foreach($entry in $packed.Files.Values){$m=[IO.MemoryStream]::new();try{$entry.Extract($m);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray())) -ne (Get-FileHash (Join-Path $source $entry.Name)).Hash){throw 'Packed readback mismatch'}}finally{$m.Dispose()}}
$manifest=[ordered]@{status='BUILT_RITE_G2_EXACT_RESUME_LIVE_PENDING';archive_sha256=(Get-FileHash $archive).Hash;resources=$resources;source_sha256=(Get-FileHash $raw).Hash;packed_readback=$true;native_guard=$guardFacts;vanilla_replacements=@();entry='get_to_clinic';completed_replay=$false;item_and_loot_replay=$false;fixer_tier_or_final_reward_restored=$false;counter_baselines=@(4);native_recording='Personal Link, 3-second download';game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($manifest|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false));[pscustomobject]$manifest|Select-Object status,archive_sha256,packed_readback|ConvertTo-Json
