param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\b0_streetkid_auto'
$source=Join-Path $WorkspaceRoot 'archive\b0_streetkid_auto\source'
$build=Join-Path $WorkspaceRoot 'build\Streetkid_Auto'
New-Item -ItemType Directory -Force -Path $audit,$source,$build|Out-Null
$old=Join-Path $WorkspaceRoot 'archive\b0_streetkid_seat_mirror_s2\source\towercontinued\streetkid_seat_mirror_s2'
$r4=Get-Content (Join-Path $WorkspaceRoot 'research\b0_streetkid_seat_mirror_s2\build_manifest.json') -Raw|ConvertFrom-Json
if($r4.revision -ne 4){throw 'Validated revision4 foundation required'}
function Copy-Resource($path) {
 $f=Read-Cr2wFile $path
 $opt=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
 $dto=[WolvenKit.Common.Conversion.RedFileDto]::new($f,$false)
 $json=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($dto,$opt).Replace('PTFRSKS2','PTFRSKA').Replace('streetkid_seat_mirror_s2','streetkid_seat_auto')
 return [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],$json,$opt).Data
}
$gate=Copy-Resource (Join-Path $old 'gate.questphase')
$owner=Copy-Resource (Join-Path $old 'owner.questphase')
$scene=Copy-Resource (Join-Path $old 'seat_mirror.scene')
$gg=$gate.RootChunk.Graph.Chunk;$og=$owner.RootChunk.Graph.Chunk
$guard=(Get-QuestNode $gg 2).Condition.Chunk
foreach($fact in 'PTFRSKS2_Enabled','PTFRSKS2_Active','PTFRBASE_Suspended','PTFRSKA_Suspended','q115_point_of_no_return'){
 Add-RedHandle $guard.Conditions (New-FactCondition $fact 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
}
(Get-QuestNode $gg 9).Type.Chunk.Value=[WolvenKit.RED4.Types.CInt32]::op_Implicit(5)
function Link($g,$a,$port,$b,$inputName='In'){
 [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $port) (Get-QuestSocket (Get-QuestNode $g $b) $inputName))
}
function Pause($id,$condition) {
 $p=(Get-QuestNode $gg 2).DeepCopy();$p.Id=[uint16]$id
 foreach($s in $p.Sockets){$s.Chunk.Connections.Clear()}
 Set-RedHandleProperty $p Condition $condition
 return $p
}
# Consume permission atomically; every cycle rechecks native guard facts.
$delay=[WolvenKit.RED4.Types.questTimeCondition]::new()
$seconds=[WolvenKit.RED4.Types.questRealtimeDelay_ConditionType]::new();$seconds.Seconds=[uint32]1
Set-RedHandleProperty $delay Type $seconds
Add-RedHandle $og.Nodes (Pause 9 $delay)
Add-RedHandle $og.Nodes (Pause 10 $guard.DeepCopy())
foreach($spec in @(@(26,'Enabled'),@(27,'Completed'),@(28,'Using'))){Add-RedHandle $og.Nodes (New-SetFactNode $spec[0] ('PTFRSKA_'+$spec[1]) 0)}
(Get-QuestSocket (Get-QuestNode $og 0) 'Out').Connections.Clear()
(Get-QuestSocket (Get-QuestNode $og 1) 'In').Connections.Clear()
Link $og 0 Out 10;Link $og 10 Out 26;Link $og 26 Out 27;Link $og 27 Out 28;Link $og 28 Out 1
Link $og 6 Out 9;Link $og 9 Out 10
# Interrupted branch remains terminal/fail-closed; never clear Interrupted.
$g=$scene.RootChunk.SceneGraph.Chunk.Graph
function SN($id){return @($g|Where-Object {$_.Chunk.NodeId.Id.ToString() -eq "$id"})[0].Chunk}
$template=(SN 595).DeepCopy()
function SceneQuest($id,$quest,$target,$inputOrdinal) {
 $n=$template.DeepCopy();$n.NodeId.Id=[uint32]$id
 Set-RedHandleProperty $n QuestNode $quest
 $n.OsockMappings.Clear();$n.OsockMappings.Add([WolvenKit.RED4.Types.CName]::op_Implicit('Out'))
 while($n.OutputSockets.Count -gt 1){$n.OutputSockets.RemoveAt(1)}
 $d=$n.OutputSockets[0].Destinations[0];$d.NodeId.Id=[uint32]$target;$d.IsockStamp.Ordinal=[uint16]$inputOrdinal
 return $n
}
$leave=[WolvenKit.RED4.Types.questLogicalCondition]::new();$leave.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
Add-RedHandle $leave.Conditions (New-FactCondition 'PTFRSKA_Depart' 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
Add-RedHandle $leave.Conditions (New-FactCondition 'PTFRSKA_Using' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
Add-RedHandle $g (SceneQuest 3030 (Pause 3030 $leave) 2000 0)
Add-RedHandle $g (SceneQuest 3031 (New-SetFactNode 3031 'PTFRSKA_Using' 1) 595 1)
(SN 4).OutputSockets[0].Destinations[0].NodeId.Id=[uint32]3031
$depart=(SN 1).OutputSockets[0].Destinations[0].DeepCopy();$depart.NodeId.Id=[uint32]3030;$depart.IsockStamp.Ordinal=[uint16]1
(SN 1).OutputSockets[0].Destinations.Add($depart)
foreach($name in 'gate','owner','seat_mirror'){
 $file=switch($name){gate{$gate}owner{$owner}seat_mirror{$scene}}
 $ext=if($name -eq 'seat_mirror'){'scene'}else{'questphase'}
 $depot="towercontinued\streetkid_seat_auto\$name.$ext"
 Write-Cr2wFile $file (Join-Path $source $depot)
 Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) (Join-Path $audit "$name.json")
}
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$archive=Join-Path $build 'TowerContinued_Streetkid_Auto.archive'
$stream=[IO.File]::Create($archive)
try{$writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new());if(-not $writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Archive failed'}}finally{$stream.Dispose()}
$reader=[WolvenKit.RED4.Archive.IO.ArchiveReader]::new();$packed=$null
if($reader.ReadArchive($archive,$hash,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne 3){throw 'Packed resource verification failed'}
$ep1=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\ep1.quest')
if(@($ep1.RootChunk.Graph.Chunk.Nodes|Where-Object {$_.Chunk.Id.ToString() -eq '50754'}).Count){throw 'Parent registration collision'}
Copy-Item (Join-Path $WorkspaceRoot 'archive\b0_streetkid_auto\TowerContinued_Streetkid_Auto.archive.xl') ($archive+'.xl') -Force
$manifest=@{revision=5;status='AUTOMATIC_CANDIDATE';sha256=(Get-FileHash $archive).Hash;scene_foundation=4;native_rearm_seconds=1;story_fact_writes=@();vanilla_replacements=@();legacy_resources_preserved=$true}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($manifest|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
$manifest|ConvertTo-Json
