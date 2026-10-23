param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly

$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$prior=Get-Content (Join-Path $audit 'details_r7_manifest.json') -Raw|ConvertFrom-Json
if($prior.status -ne 'BUILT_R7_DETAILS_NOT_INSTALLED_OR_LIVE' -or $prior.resources.Count -ne 23){throw 'R7 source manifest changed'}
$out=Join-Path $WorkspaceRoot 'build\MistyViktorAccessR10'
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

$front='$/03_night_city/c_watson/little_china/loc_mystic_mistys_ripperdoc_prefabH2DWJJI/#loc_mystic_mistys_ripperdoc_gameplay/{q307_zetatech_door}_prefabQZIZFAI/#q307_zetatech_door'
$inner='$/03_night_city/c_watson/little_china/loc_mystic_mistys_ripperdoc_prefabH2DWJJI/#loc_mystic_mistys_ripperdoc_env/q307_misty_zetatech_architecture_prefabLOINHOY/{single_door_}1_prefabWP57WLA/#q307_zetatech_doors_01'
$doorRefs=@($front,$inner)
$viktor=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\main_quests\q307\phases\q307_06_viktor.questphase')
$pauseTemplate=(Get-QuestNode $graph 25).DeepCopy()
$facts=[ordered]@{};foreach($p in $prior.guards.psobject.Properties){$facts[$p.Name]=[int]$p.Value}

function Fact([string]$name,[int]$value,[bool]$inverse=$false){
 $cmp=if($inverse){[WolvenKit.RED4.Types.Enums+EComparisonType]::NotEqual}else{[WolvenKit.RED4.Types.Enums+EComparisonType]::Equal}
 return New-FactCondition $name $value $cmp
}
function Logic([string]$op,$children){
 $c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::$op
 foreach($child in $children){Add-RedHandle $c.Conditions $child};return $c
}
function Guard([bool]$inverse=$false){
 $children=[Collections.Generic.List[object]]::new()
 foreach($key in $script:facts.Keys){$children.Add((Fact $key $script:facts[$key] $inverse))}
 return Logic $(if($inverse){'OR'}else{'AND'}) $children
}
function Loaded([string]$ref,[bool]$inverse=$false){
 $c=[WolvenKit.RED4.Types.questNodeLoadingCondition]::new();$c.ObjectRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref);$c.Inverted=$inverse;return $c
}
function LoadingGroup([bool]$inverse=$false){
 $parts=[Collections.Generic.List[object]]::new();foreach($ref in $script:doorRefs){$parts.Add((Loaded $ref $inverse))}
 return Logic $(if($inverse){'OR'}else{'AND'}) $parts
}
function Pause([int]$id,$condition){
 $n=$script:pauseTemplate.DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};Set-RedHandleProperty $n Condition $condition;return $n
}
function Door([int]$id,[string]$ref,[string]$action){
 $n=(Get-QuestNode $script:viktor.RootChunk.Graph.Chunk 19).DeepCopy();$n.Id=[uint16]$id
 foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}
 if($n.Type.Chunk.Params.Count -ne 1){throw 'Unexpected door precedent'}
 $p=$n.Type.Chunk.Params[0].Chunk
 if($p.ObjectRef.ToString() -ne '#q115_misty_door_back' -or $p.DeviceControllerClass.ToString() -ne 'DoorControllerPS' -or $p.ActionProperties.Count -ne 0){throw 'Unexpected door payload'}
 $p.ObjectRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref);$p.DeviceAction=[WolvenKit.RED4.Types.CName]::op_Implicit($action);return $n
}
function StreetGuard([int]$id,[string]$action){
 $n=(Get-QuestNode $script:viktor.RootChunk.Graph.Chunk 30).DeepCopy();$n.Id=[uint16]$id
 foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}
 $selected=@($n.Actions|Where-Object {$_.Type.Chunk.GetType().Name -eq 'questCommunityTemplate_NodeType' -and $_.Type.Chunk.CommunityEntryName.ToString() -eq 'q307_alley_extra_01'})
 if($selected.Count -ne 1 -or $selected[0].Type.Chunk.SpawnerReference.ToString() -ne '#q307_com_alley' -or
    $selected[0].Type.Chunk.CommunityEntryPhaseName.ToString() -ne 'return' -or $selected[0].Type.Chunk.Action.ToString() -ne 'Reactivate'){throw 'Unexpected street-guard precedent'}
 $one=$selected[0].DeepCopy()
 if($action -eq 'Deactivate'){$one.Type.Chunk.Action=[WolvenKit.RED4.Types.Enums+populationSpawnerObjectCtrlAction]::Deactivate}
 elseif($action -ne 'Reactivate'){throw 'Unsupported street-guard action'}
 $n.Actions.Clear();[void]$n.Actions.Add($one);return $n
}
function RemoveR9Clerk([int]$id){
 $n=(Get-QuestNode $script:viktor.RootChunk.Graph.Chunk 30).DeepCopy();$n.Id=[uint16]$id
 foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}
 $selected=@($n.Actions|Where-Object {$_.Type.Chunk.GetType().Name -eq 'questCommunityTemplate_NodeType' -and $_.Type.Chunk.CommunityEntryName.ToString() -eq 'q307_zetatech_clerk'})
 if($selected.Count -ne 1 -or $selected[0].Type.Chunk.SpawnerReference.ToString() -ne '#q307_com_main' -or
    $selected[0].Type.Chunk.CommunityEntryPhaseName.ToString() -ne 'q307_ws_zetatech_clerk_return' -or $selected[0].Type.Chunk.Action.ToString() -ne 'Reactivate'){throw 'Unexpected R9-clerk precedent'}
 $one=$selected[0].DeepCopy();$one.Type.Chunk.Action=[WolvenKit.RED4.Types.Enums+populationSpawnerObjectCtrlAction]::Deactivate
 $n.Actions.Clear();[void]$n.Actions.Add($one);return $n
}
function Counter([int]$id,[string]$name){$n=New-SetFactNode $id $name 1;$n.Type.Chunk.SetExactValue=$false;return $n}

# Force one migration from an already-active R9 controller.
$stop=(Get-QuestNode $graph 5).Condition.Chunk
$migration=$stop.Conditions[0].Chunk.DeepCopy();$migration.Type.Chunk.FactName='PTFRMV_AccessRevision';$migration.Type.Chunk.Value=[int32]10
[void](Add-RedHandle $stop.Conditions $migration)

foreach($n in @(
 (New-SetFactNode 30 'PTFRMV_AccessRevision' 10),
 (Pause 31 (Logic 'OR' @((LoadingGroup),(Guard $true)))),
 (New-ConditionNode 32 (Guard)),(New-ConditionNode 33 (LoadingGroup)),
 (Door 34 $front 'ForceCloseImmediate'),(Door 35 $front 'ForceUnlock'),
 (Door 36 $inner 'ForceCloseImmediate'),(Door 37 $inner 'ForceUnlock'),
 (Counter 38 'PTFRMV_DoorRequests'),(New-SetFactNode 39 'PTFRMV_DoorReady' 1),
 (Pause 40 (Logic 'OR' @((Guard $true),(LoadingGroup $true)))),
 (New-SetFactNode 41 'PTFRMV_DoorReady' 0),(New-ConditionNode 42 (Guard)),(Pause 43 (Guard)),
 (StreetGuard 44 'Reactivate'),(Counter 45 'PTFRMV_StreetNPCRequests'),
 (StreetGuard 46 'Deactivate'),(Counter 47 'PTFRMV_StreetNPCReleaseRequests'),
 (RemoveR9Clerk 48),(Counter 49 'PTFRMV_ClerkRemovalRequests')
)){Add-RedHandle $graph.Nodes $n}

foreach($n in $graph.Nodes){foreach($s in $n.Chunk.Sockets){$s.Chunk.Connections.Clear()}}
$edges=@(
 @(0,'Out',1),@(1,'Out',18),@(18,'Out',2),@(2,'Out',3),@(3,'Out',30),
 # Main R7 owner, with obsolete door actions 11/14/15 bypassed.
 @(30,'Out',21),@(21,'Out',10),@(10,'Out',19),@(19,'Out',22),@(22,'Out',12),
 @(12,'Out',44),@(44,'Out',45),@(45,'Out',8),@(8,'Out',4),@(4,'Out',5),
 @(5,'Out',24),@(24,'Out',20),@(20,'Out',48),@(48,'Out',49),@(49,'Out',46),@(46,'Out',47),@(47,'Out',13),
 @(13,'True',16),@(16,'Out',17),@(17,'Out',6),@(13,'False',6),@(6,'Out',9),@(9,'Out',7),@(7,'Out',2),
 # Existing stream-aware crowd-null branch.
 @(19,'Out',25),@(25,'Out',26),@(26,'True',23),@(23,'Out',29),@(29,'Out',27),@(27,'Out',28),@(28,'True',25),
 # Exact two-door stream-aware branch; re-arms after either node unloads.
 @(30,'Out',31),@(31,'Out',32),@(32,'True',33),@(32,'False',43),@(33,'False',31),
 @(33,'True',34),@(34,'Out',35),@(35,'Out',36),@(36,'Out',37),@(37,'Out',38),@(38,'Out',39),
 @(39,'Out',40),@(40,'Out',41),@(41,'Out',42),@(42,'True',31),@(42,'False',43),@(43,'Out',31)
)
foreach($e in $edges){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $e[0]) $e[1]) (Get-QuestSocket (Get-QuestNode $graph $e[2]) 'In'))}

Write-Cr2wFile $phase (Join-Path $source $phaseDepot)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $phaseDepot)) (Join-Path $audit 'access_r10_phase.json')
Copy-Item -LiteralPath ($prior.archive+'.xl') -Destination (Join-Path $out 'TowerContinued_MistyViktorShellOptIn.archive.xl') -Force
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load();$archive=Join-Path $out 'TowerContinued_MistyViktorShellOptIn.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'R10 pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hash,[ref]$packed).ToString() -ne 'NoError'){throw 'R10 reopen failed'}
if(@(Compare-Object @($prior.resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'R10 resource scope mismatch'}
$manifest=[ordered]@{
 status='BUILT_R10_STREAMED_DOORS_STREET_NPC_NOT_INSTALLED_OR_LIVE';archive=$archive;sha256=(Get-FileHash $archive).Hash;xl_sha256=(Get-FileHash ($archive+'.xl')).Hash
 resources=$prior.resources;guards=$prior.guards;edges=$edges;compatibility_revision=7;access_revision=10
 front_door=@{ref=$front;reported_position=@(-1548.5966796875,1191.4342041016,16.215202331543)}
 inner_door=@{ref=$inner;reported_position=@(-1542.2309570313,1200.6055908203,15.869735717773)}
 door_readiness='both exact door refs loaded';door_rearm='either exact door ref unloaded';door_actions=@('front:ForceCloseImmediate','front:ForceUnlock','inner:ForceCloseImmediate','inner:ForceUnlock')
 street_npc=@{spawner='#q307_com_alley';entry='q307_alley_extra_01';phase='return';record='Character.q307_zetatech_guard';workspot='#q307_ws_alley_extra_01_return';position=@(-1543.66968,1194.16675,15.8481941);activate='Reactivate';release='Deactivate'}
 removed_r9_clerk=$true;clerk_cleanup=@{spawner='#q307_com_main';entry='q307_zetatech_clerk';phase='q307_ws_zetatech_clerk_return';action='Deactivate'};obsolete_door_actions_bypassed=@(11,14,15);saved_r9_active_migration='PTFRMV_AccessRevision!=10 triggers one guarded release/reacquire and exact R9 clerk deactivation'
 original_world_resource_overrides=0;native_scene_starts=0;story_fact_writes=0;save_files_modified=$false;live_tested=$false
}
[IO.File]::WriteAllText((Join-Path $audit 'access_r10_manifest.json'),($manifest|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
[pscustomobject]$manifest|Select-Object status,sha256,access_revision,door_readiness,removed_r9_clerk,original_world_resource_overrides,native_scene_starts|ConvertTo-Json
