param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly

$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$prior=Get-Content (Join-Path $audit 'details_r7_manifest.json') -Raw|ConvertFrom-Json
if($prior.status -ne 'BUILT_R7_DETAILS_NOT_INSTALLED_OR_LIVE' -or $prior.resources.Count -ne 23){throw 'R7 source manifest changed'}
$out=Join-Path $WorkspaceRoot 'build\MistyViktorAccessR9'
$source=Join-Path $out 'source'
New-Item -ItemType Directory -Force $source|Out-Null
foreach($depot in $prior.resources){
 $src=Join-Path $WorkspaceRoot ('build\MistyViktorDetailsR7\source\'+$depot)
 $dst=Join-Path $source $depot
 New-Item -ItemType Directory -Force (Split-Path -Parent $dst)|Out-Null
 Copy-Item -LiteralPath $src -Destination $dst -Force
}

$phaseDepot='towercontinued\misty_viktor_world\shell_optin.questphase'
$phase=Read-Cr2wFile (Join-Path $source $phaseDepot)
$graph=$phase.RootChunk.Graph.Chunk
if($graph.Nodes.Count -ne 30){throw 'R7 controller changed'}
$revision=(Get-QuestNode $graph 18).Type.Chunk
if($revision.FactName.ToString() -ne 'PTFRMV_Revision' -or $revision.Value.ToString() -ne '7'){throw 'R7 compatibility revision changed'}
# A saved R7 controller can already be parked in its active wait node. Add one
# private migration invalidator so that state releases once, then traverses the
# new acquisition actions. This does not broaden the Tower completion guard.
$stop=(Get-QuestNode $graph 5).Condition.Chunk
if($stop.GetType().Name -ne 'questLogicalCondition' -or $stop.Operation.ToString() -ne 'OR'){throw 'R7 stop condition changed'}
$migration=$stop.Conditions[0].Chunk.DeepCopy()
$migration.Type.Chunk.FactName='PTFRMV_AccessRevision'
$migration.Type.Chunk.Value=[int32]9
[void](Add-RedHandle $stop.Conditions $migration)

$viktor=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\main_quests\q307\phases\q307_06_viktor.questphase')
$front='$/03_night_city/c_watson/little_china/loc_mystic_mistys_ripperdoc_prefabH2DWJJI/#loc_mystic_mistys_ripperdoc_gameplay/{q307_zetatech_door}_prefabQZIZFAI/#q307_zetatech_door'
$rear='$/03_night_city/c_watson/little_china/loc_mystic_mistys_ripperdoc_prefabH2DWJJI/#loc_mystic_mistys_ripperdoc_gameplay/single_door_1_prefab6TT3B7Y/#q115_misty_door_back;#q307_zetatech_doors_02'

function Door([int]$id,[string]$ref,[string]$action){
 $node=(Get-QuestNode $script:viktor.RootChunk.Graph.Chunk 19).DeepCopy();$node.Id=[uint16]$id
 foreach($socket in $node.Sockets){$socket.Chunk.Connections.Clear()}
 if($node.Type.Chunk.Params.Count -ne 1){throw 'Unexpected door precedent'}
 $p=$node.Type.Chunk.Params[0].Chunk
 if($p.ObjectRef.ToString() -ne '#q115_misty_door_back' -or $p.DeviceControllerClass.ToString() -ne 'DoorControllerPS' -or $p.ActionProperties.Count -ne 0){throw 'Unexpected door action payload'}
 $p.ObjectRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref)
 $p.DeviceAction=[WolvenKit.RED4.Types.CName]::op_Implicit($action)
 return $node
}
function Clerk([int]$id,[string]$action){
 $node=(Get-QuestNode $script:viktor.RootChunk.Graph.Chunk 30).DeepCopy();$node.Id=[uint16]$id
 foreach($socket in $node.Sockets){$socket.Chunk.Connections.Clear()}
 $selected=@($node.Actions|Where-Object {
   $_.Type.Chunk.GetType().Name -eq 'questCommunityTemplate_NodeType' -and
   $_.Type.Chunk.CommunityEntryName.ToString() -eq 'q307_zetatech_clerk'
 })
 if($selected.Count -ne 1 -or $selected[0].Type.Chunk.SpawnerReference.ToString() -ne '#q307_com_main' -or
    $selected[0].Type.Chunk.CommunityEntryPhaseName.ToString() -ne 'q307_ws_zetatech_clerk_return' -or
    $selected[0].Type.Chunk.Action.ToString() -ne 'Reactivate'){throw 'Unexpected post-scene clerk precedent'}
 $one=$selected[0].DeepCopy()
 if($action -eq 'Deactivate'){$one.Type.Chunk.Action=[WolvenKit.RED4.Types.Enums+populationSpawnerObjectCtrlAction]::Deactivate}
 elseif($action -ne 'Reactivate'){throw 'Unsupported clerk action'}
 $node.Actions.Clear();[void]$node.Actions.Add($one)
 return $node
}
function Counter([int]$id,[string]$name){$n=New-SetFactNode $id $name 1;$n.Type.Chunk.SetExactValue=$false;return $n}

foreach($node in @(
 (Door 30 $front 'ForceCloseImmediate'),
 (Door 31 $front 'ForceUnlock'),
 (Door 32 $rear 'ForceCloseImmediate'),
 (Clerk 33 'Reactivate'),
 (Clerk 34 'Deactivate'),
 (New-SetFactNode 35 'PTFRMV_AccessRevision' 9),
 (Counter 36 'PTFRMV_DoorRequests'),
 (Counter 37 'PTFRMV_ClerkRequests'),
 (Counter 38 'PTFRMV_ClerkReleaseRequests')
)){Add-RedHandle $graph.Nodes $node}

# Preserve the R7 graph except for the exact activation and release splice.
foreach($node in $graph.Nodes){foreach($socket in $node.Chunk.Sockets){$socket.Chunk.Connections.Clear()}}
$edges=@(
 @(0,'Out',1),@(1,'Out',18),@(18,'Out',2),
 @(2,'Out',3),@(3,'Out',35),@(35,'Out',30),@(30,'Out',31),@(31,'Out',32),@(32,'Out',21),
 @(21,'Out',10),@(10,'Out',19),@(19,'Out',22),@(22,'Out',11),@(11,'Out',36),
 @(36,'Out',33),@(33,'Out',37),@(37,'Out',12),@(12,'Out',8),@(8,'Out',4),
 @(4,'Out',5),@(5,'Out',24),@(24,'Out',20),@(20,'Out',34),@(34,'Out',38),@(38,'Out',13),
 @(13,'True',14),@(14,'Out',15),@(15,'Out',16),@(16,'Out',17),@(17,'Out',6),
 @(13,'False',6),@(6,'Out',9),@(9,'Out',7),@(7,'Out',2),
 @(19,'Out',25),@(25,'Out',26),@(26,'True',23),@(23,'Out',29),@(29,'Out',27),
 @(27,'Out',28),@(28,'True',25)
)
foreach($edge in $edges){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $edge[0]) $edge[1]) (Get-QuestSocket (Get-QuestNode $graph $edge[2]) 'In'))}

Write-Cr2wFile $phase (Join-Path $source $phaseDepot)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $phaseDepot)) (Join-Path $audit 'access_r9_phase.json')
Copy-Item -LiteralPath ($prior.archive+'.xl') -Destination (Join-Path $out 'TowerContinued_MistyViktorShellOptIn.archive.xl') -Force
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$archive=Join-Path $out 'TowerContinued_MistyViktorShellOptIn.archive'
$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'R9 pack failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hash,[ref]$packed).ToString() -ne 'NoError'){throw 'R9 reopen failed'}
if(@(Compare-Object @($prior.resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'R9 resource scope mismatch'}
$manifest=[ordered]@{
 status='BUILT_R9_ACCESS_CLERK_NOT_INSTALLED_OR_LIVE';archive=$archive
 sha256=(Get-FileHash $archive).Hash;xl_sha256=(Get-FileHash ($archive+'.xl')).Hash
 resources=$prior.resources;guards=$prior.guards;edges=$edges
 compatibility_revision=7;access_revision=9
 saved_r7_active_migration='PTFRMV_AccessRevision!=9 triggers one guarded release/reacquire'
 front_door=$front;rear_door=$rear
 door_actions=@('front:ForceCloseImmediate','front:ForceUnlock','rear:ForceCloseImmediate','rear:ForceUnlock')
 clerk=@{spawner='#q307_com_main';entry='q307_zetatech_clerk';phase='q307_ws_zetatech_clerk_return';activate='Reactivate';release='Deactivate'}
 original_world_resource_overrides=0;native_scene_starts=0;story_fact_writes=0;save_files_modified=$false;live_tested=$false
}
[IO.File]::WriteAllText((Join-Path $audit 'access_r9_manifest.json'),($manifest|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
[pscustomobject]$manifest|Select-Object status,sha256,compatibility_revision,access_revision,original_world_resource_overrides,native_scene_starts|ConvertTo-Json
