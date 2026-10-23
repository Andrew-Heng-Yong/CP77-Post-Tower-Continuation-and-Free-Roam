param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\side_job_cleanup_s1_1'
$out=Join-Path $WorkspaceRoot 'build\SideJobCleanupS1_1';$source=Join-Path $out 'source'
New-Item -ItemType Directory -Force $audit,$source|Out-Null
$priorManifest=Get-Content (Join-Path $WorkspaceRoot 'research\side_job_pilot_s1\manifest.json') -Raw|ConvertFrom-Json
$priorArchive=Join-Path $WorkspaceRoot 'build\SideJobPilotS1\TowerContinued_SideJobPilotS1.archive'
if((Get-FileHash $priorArchive).Hash -ne $priorManifest.archive_sha256){throw 'Changed S1 archive'}
function EdgesFix($g){
 $owners=@{};$rows=[Collections.Generic.List[object]]::new()
 foreach($h in $g.Nodes){foreach($s in $h.Chunk.Sockets){$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($s.Chunk)]=[int]$h.Chunk.Id.ToString()}}
 foreach($h in $g.Nodes){foreach($s in $h.Chunk.Sockets){foreach($c in $s.Chunk.Connections){if([object]::ReferenceEquals($c.Chunk.Source.Chunk,$s.Chunk)){
  $rows.Add(@($owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($s.Chunk)],$s.Chunk.Name.ToString(),$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($c.Chunk.Destination.Chunk)],$c.Chunk.Destination.Chunk.Name.ToString()))
 }}}};return ,$rows.ToArray()
}
function RebuildFix($g,$edges){
 foreach($h in $g.Nodes){foreach($s in $h.Chunk.Sockets){$s.Chunk.Connections.Clear()}}
 foreach($e in $edges){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $e[0]) $e[1]) (Get-QuestSocket (Get-QuestNode $g $e[2]) $e[3]))}
}
function RewireFix($g,$original){
 RebuildFix $g @(EdgesFix $original|ForEach-Object {$_})
 foreach($h in $g.Nodes){$n=$h.Chunk;if($n.GetType().Name -eq 'questPhaseNodeDefinition' -and $null -ne $n.PhaseGraph.Chunk){RewireFix $n.PhaseGraph.Chunk (Get-QuestNode $original ([int]$n.Id.ToString())).PhaseGraph.Chunk}}
}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$oldPack=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($priorArchive,$hs,[ref]$oldPack).ToString() -ne 'NoError'){throw 'Read S1 failed'}
$resources=@($priorManifest.resources);$priorHashes=[ordered]@{}
foreach($entry in $oldPack.Files.Values){
 $path=Join-Path $source $entry.Name;New-Item -ItemType Directory -Force (Split-Path -Parent $path)|Out-Null
 $m=[IO.MemoryStream]::new();try{$entry.Extract($m);$bytes=$m.ToArray();$priorHashes[$entry.Name]=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes));[IO.File]::WriteAllBytes($path,$bytes)}finally{$m.Dispose()}
}
$depot='towercontinued\side_job_pilot_s1\native_owner.questphase';$path=Join-Path $source $depot
$original=Read-Cr2wFile $path;$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$original.RootChunk.DeepCopy()
RewireFix $file.RootChunk.Graph.Chunk $original.RootChunk.Graph.Chunk
$cleanup=(Get-QuestNode $file.RootChunk.Graph.Chunk 4).PhaseGraph.Chunk
# Keep the existing native distance/camera waits as the first OR branch. The
# alternative is completed-route-only and retains the exact native IsOutside.
$outside=(Get-QuestNode $cleanup 15).Condition.Chunk.Conditions[0].Chunk.DeepCopy()
$guardFacts=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRS1_Request=1;PTFRS1_Started=1;PTFRS1_Fault=0;PTFRS1_RewardClaim=1;PTFRS1_RewardAck=1;PTFRS1_RewardReplayRefused=0;PTFRS1_OwnerFinished=0;mq005_done=1;mq005_police_left=1;mq005_police_done=0;PTFRS1_CleanupDeparture=1}
foreach($id in @(10,15)){
 $node=Get-QuestNode $cleanup $id;$oldCondition=$node.Condition.Chunk
 $fallback=[WolvenKit.RED4.Types.questLogicalCondition]::new();$fallback.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
 foreach($k in $guardFacts.Keys){Add-RedHandle $fallback.Conditions (New-FactCondition $k $guardFacts[$k] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
 Add-RedHandle $fallback.Conditions ($outside.DeepCopy())
 $either=[WolvenKit.RED4.Types.questLogicalCondition]::new();$either.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
 Add-RedHandle $either.Conditions $oldCondition;Add-RedHandle $either.Conditions $fallback
 Set-RedHandleProperty $node Condition $either
}
$edges=@(EdgesFix $cleanup|ForEach-Object {$_})
# Branch acknowledgements instrument completion without re-running actions.
$acks=@(@(440,'PTFRS1_CleanupEntered',16,'Out'),@(441,'PTFRS1_CorpoDepartureAck',10,'Out'),@(442,'PTFRS1_CarsDepartureAck',15,'Out'),@(443,'PTFRS1_CorpoCleanupAck',13,'Out'),@(444,'PTFRS1_CarsCleanupAck',3,'Out'))
foreach($a in $acks){Add-RedHandle $cleanup.Nodes (New-SetFactNode $a[0] $a[1] 1);$edges+=,@($a[2],$a[3],$a[0],'In')}
Add-RedHandle $cleanup.Nodes (New-SetFactNode 445 'PTFRS1_CleanupJoined' 1)
$edges=@($edges|Where-Object {-not ($_[0] -eq 14 -and $_[2] -eq 1)})
$edges+=,@(14,'Out1',445,'In');$edges+=,@(445,'Out',1,'In');RebuildFix $cleanup $edges
Write-Cr2wFile $file $path;Export-Cr2wJson (Read-Cr2wFile $path) (Join-Path $audit 'native_owner.questphase.json')
$archive=Join-Path $out 'TowerContinued_SideJobPilotS1.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError'){throw 'Readback failed'}
if(@(Compare-Object @($resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Archive scope mismatch'}
$hashes=[ordered]@{}
foreach($entry in $packed.Files.Values){$m=[IO.MemoryStream]::new();try{$entry.Extract($m);$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()));if($hash -ne (Get-FileHash (Join-Path $source $entry.Name)).Hash){throw 'Readback mismatch'};$hashes[$entry.Name]=$hash;if($entry.Name -ne $depot -and $hash -ne $priorHashes[$entry.Name]){throw 'Unrelated resource changed'}}finally{$m.Dispose()}}
$result=[ordered]@{status='BUILT_S1_1_GUARDED_CLEANUP_FALLBACK_LIVE_PENDING';archive_sha256=(Get-FileHash $archive).Hash;predecessor_archive_sha256=$priorManifest.archive_sha256;resources=$hashes;predecessor_resources=$priorHashes;native_guard=$guardFacts;changed_resource=$depot;packed_readback=$true;quest_or_reward_reset=$false;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($result|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false));$result.status
