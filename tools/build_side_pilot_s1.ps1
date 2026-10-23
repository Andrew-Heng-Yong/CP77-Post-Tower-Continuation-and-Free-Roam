param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\side_job_pilot_s1'
$out=Join-Path $WorkspaceRoot 'build\SideJobPilotS1';$source=Join-Path $out 'source'
New-Item -ItemType Directory -Force $audit,$source|Out-Null
$raw=Join-Path $WorkspaceRoot 'research\activity_state_r3\native_sources\raw\base\quest\minor_quests\mq005\mq005.questphase'
$combatRaw=Join-Path $WorkspaceRoot 'research\activity_state_r3\native_sources\raw\base\quest\minor_quests\mq005\phases\mq005_combat.questphase'
if((Get-FileHash $raw).Hash -ne 'F59E9FE34747C11FBCBFBF36D13C01BBF169939BDF8778836130E683E3D2CDD2'){throw 'Changed native Only Pain source'}
if((Get-FileHash $combatRaw).Hash -ne '6D30A3348A8E82206C72712069FB14C2F3AF3EF8C42DFE888B07381C1ECA4EC5'){throw 'Changed native combat source'}
function EdgesS1($g){
 $owners=@{};$rows=[Collections.Generic.List[object]]::new()
 foreach($h in $g.Nodes){foreach($s in $h.Chunk.Sockets){$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($s.Chunk)]=[int]$h.Chunk.Id.ToString()}}
 foreach($h in $g.Nodes){foreach($s in $h.Chunk.Sockets){foreach($c in $s.Chunk.Connections){if([object]::ReferenceEquals($c.Chunk.Source.Chunk,$s.Chunk)){
  $rows.Add(@($owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($s.Chunk)],$s.Chunk.Name.ToString(),$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($c.Chunk.Destination.Chunk)],$c.Chunk.Destination.Chunk.Name.ToString()))
 }}}}
 return ,$rows.ToArray()
}
function RebuildS1($g,$edges){
 foreach($h in $g.Nodes){foreach($s in $h.Chunk.Sockets){$s.Chunk.Connections.Clear()}}
 foreach($e in $edges){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $e[0]) $e[1]) (Get-QuestSocket (Get-QuestNode $g $e[2]) $e[3]))}
}
function RewireS1($g,$original){
 RebuildS1 $g @(EdgesS1 $original|ForEach-Object {$_})
 foreach($h in $g.Nodes){$n=$h.Chunk;if($n.GetType().Name -eq 'questPhaseNodeDefinition' -and $null -ne $n.PhaseGraph.Chunk){RewireS1 $n.PhaseGraph.Chunk (Get-QuestNode $original ([int]$n.Id.ToString())).PhaseGraph.Chunk}}
}
$native=Read-Cr2wFile $raw;$combat=Read-Cr2wFile $combatRaw
$roots=@{native_owner=$native.RootChunk.DeepCopy();combat=$combat.RootChunk.DeepCopy()}
RewireS1 $roots.native_owner.Graph.Chunk $native.RootChunk.Graph.Chunk
RewireS1 $roots.combat.Graph.Chunk $combat.RootChunk.Graph.Chunk
$prefix='towercontinued\side_job_pilot_s1\'
$play=(Get-QuestNode $roots.native_owner.Graph.Chunk 3).PhaseGraph.Chunk
(Get-QuestNode $play 4).PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($prefix+'combat.questphase')
# Preserve authored native scene, branches, checkpoint, actors and cleanup.
# Only the main completion reward is instrumented; scene money rewards remain
# native, behind the one-shot fresh-only owner. No completed replay is offered.
$edges=@(EdgesS1 $play|ForEach-Object {$_})
$incoming=@($edges|Where-Object {$_[2] -eq 9})
$edges=@($edges|Where-Object {$_[2] -ne 9 -and -not ($_[0] -eq 9 -and $_[2] -eq 11)})
foreach($n in @((New-ConditionNode 400 (New-FactCondition 'PTFRS1_RewardClaim' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))),
 (New-SetFactNode 401 'PTFRS1_RewardClaim' 1),(New-SetFactNode 402 'PTFRS1_RewardAck' 1),(New-SetFactNode 403 'PTFRS1_RewardReplayRefused' 1))){Add-RedHandle $play.Nodes $n}
foreach($e in $incoming){$edges+=,@($e[0],$e[1],400,'In')}
$edges+=,@(400,'True',401,'In');$edges+=,@(401,'Out',9,'In');$edges+=,@(9,'Out',402,'In');$edges+=,@(402,'Out',11,'Succeeded');$edges+=,@(400,'False',403,'In')
RebuildS1 $play $edges
# Boot phase deliberately owns no world prefab. The original alley binding is
# loaded only by native_owner, after exact request/outcome/ending gates.
$roots.owner=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
Set-RedHandleProperty $roots.owner Graph $g
foreach($n in @((New-InputNode 0 'In1'),(New-OutputNode 1 'Out1'))){Add-RedHandle $g.Nodes $n}
$parentRaw=Join-Path $WorkspaceRoot 'research\afterlife_world\nix_sources\raw\base\quest\minor_quests\minorquests.questphase'
if((Get-FileHash $parentRaw).Hash -ne '89E902A6BCC783325642A6DC6D1D856BB144651136C58D423FEA6B421EFCE85A'){throw 'Changed native parent source'}
$parent=Read-Cr2wFile $parentRaw
$child=(Get-QuestNode $parent.RootChunk.Graph.Chunk 19).DeepCopy();$child.Id=[uint16]405
foreach($s in $child.Sockets){$s.Chunk.Connections.Clear()}
$child.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($prefix+'native_owner.questphase')
Add-RedHandle $g.Nodes $child
$guardFacts=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRS1_Request=1;PTFRS1_Started=0;PTFRS1_Fault=0;PTFRS1_RewardClaim=0;PTFRS1_RewardAck=0;mq005_done=0;mq005_police_done=0;mq005_police_left=0;mq005_01_admition_of_guilt=0;mq005_01_admition_of_guilt_BLOCK=0;mq005_01_full_story=0;mq005_block_punching_choice=0;wanted_level=0}
$guard=[WolvenKit.RED4.Types.questLogicalCondition]::new();$guard.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
foreach($k in $guardFacts.Keys){Add-RedHandle $guard.Conditions (New-FactCondition $k $guardFacts[$k] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
foreach($k in @('q001_done','q005_done','q101_enable_side_content')){Add-RedHandle $guard.Conditions (New-FactCondition $k 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Greater))}
$pause=(Get-QuestNode (Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase')).RootChunk.Graph.Chunk 106).DeepCopy()
$pause.Id=[uint16]402;foreach($s in $pause.Sockets){$s.Chunk.Connections.Clear()};Set-RedHandleProperty $pause Condition $guard
foreach($n in @((New-SetFactNode 400 'PTFRS1_Ready' 1),(New-SetFactNode 401 'PTFRS1_NativeRevision' 1),$pause,(New-SetFactNode 403 'PTFRS1_Started' 1),(New-SetFactNode 404 'PTFRS1_OwnerFinished' 1))){Add-RedHandle $g.Nodes $n}
RebuildS1 $g @(@(0,'Out',400,'In'),@(400,'Out',401,'In'),@(401,'Out',402,'In'),@(402,'Out',403,'In'),@(403,'Out',405,'In1'),@(405,'Out1',404,'In'),@(404,'Out',1,'In'))
$resources=@()
foreach($name in @('owner','native_owner','combat')){
 $file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$roots[$name];$depot=$prefix+$name+'.questphase';$resources+=,$depot
 Write-Cr2wFile $file (Join-Path $source $depot);Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) (Join-Path $audit ($name+'.questphase.json'))
}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$archive=Join-Path $out 'TowerContinued_SideJobPilotS1.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError'){throw 'Readback failed'}
if(@(Compare-Object @($resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Archive scope mismatch'}
foreach($entry in $packed.Files.Values){$m=[IO.MemoryStream]::new();try{$entry.Extract($m);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray())) -ne (Get-FileHash (Join-Path $source $entry.Name)).Hash){throw 'Readback mismatch'}}finally{$m.Dispose()}}
$result=[ordered]@{status='BUILT_ONLY_PAIN_FRESH_PILOT_LIVE_PENDING';archive_sha256=(Get-FileHash $archive).Hash;resources=$resources;packed_readback=$true;vanilla_replacements=@();native_guard=$guardFacts;native_eligibility=@('q001_done>0','q005_done>0','q101_enable_side_content>0');completed_replay=$false;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($result|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
$result.status
