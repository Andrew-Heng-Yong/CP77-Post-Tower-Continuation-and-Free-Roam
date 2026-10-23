param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly

$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$aliasManifest=Get-Content (Join-Path $audit 'original_lamp_alias_s1_manifest.json') -Raw|ConvertFrom-Json
if($aliasManifest.status -ne 'BUILT_SINGLETON_ORIGINAL_ALIAS_SOURCE_ONLY_NOT_INSTALLED' -or (Get-FileHash -LiteralPath $aliasManifest.target).Hash -ne $aliasManifest.target_sha256){throw 'Alias source not validated'}
$alias=$aliasManifest.alias
$phaseDepot='towercontinued\misty_viktor_original_lamp_s1\original_lamp_s1.questphase'
$source=Join-Path $WorkspaceRoot 'build\MistyOriginalLampAliasS1\source'
$referencePhase=Join-Path $WorkspaceRoot 'build\MistyViktorLightPOC\source\towercontinued\misty_viktor_light_poc\light_poc.questphase'
$file=Read-Cr2wFile $referencePhase
if($file.RootChunk.Graph.Chunk.Nodes.Count -ne 31){throw 'Validated private light phase changed'}
$pauseTemplate=(Get-QuestNode $file.RootChunk.Graph.Chunk 7).DeepCopy()
$facts=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q305_johnny_scene_active=0;q115_point_of_no_return=0;PTFRBASE_Suspended=0;PTFRWORLD_Suspended=0;PTFRMV_Revision=7;PTFRMV_Applied=1;PTFRMVOL_Enabled=1;PTFRMVOL_Suspended=0}
function Fact($name,$value,[bool]$not=$false){
 $cmp=if($not){[WolvenKit.RED4.Types.Enums+EComparisonType]::NotEqual}else{[WolvenKit.RED4.Types.Enums+EComparisonType]::Equal}
 return New-FactCondition $name $value $cmp
}
function Logic($operation,$children){
 $c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::$operation
 foreach($child in $children){Add-RedHandle $c.Conditions $child};return $c
}
function Guard([bool]$inverse=$false){
 $children=[Collections.Generic.List[object]]::new()
 foreach($name in $script:facts.Keys){$children.Add((Fact $name $script:facts[$name] $inverse))}
 $children.Add((Logic $(if($inverse){'AND'}else{'OR'}) @((Fact 'PTFRMVOL_DesiredVisible' 0 $inverse),(Fact 'PTFRMVOL_DesiredVisible' 1 $inverse))))
 return Logic $(if($inverse){'OR'}else{'AND'}) $children
}
function ReleaseGuard{
 $children=[Collections.Generic.List[object]]::new()
 foreach($name in @('PostTowerFreeRoamActive','PTFRP0_DR13','q307_active','q307_done','q307_finished','q307_2079','q307_main_game_killed','q307_ep1_killed','q305_johnny_scene_active','q115_point_of_no_return','PTFRBASE_Suspended','PTFRWORLD_Suspended')){$children.Add((Fact $name $script:facts[$name]))}
 return Logic 'AND' $children
}
function Loaded([bool]$inverse=$false){$c=[WolvenKit.RED4.Types.questNodeLoadingCondition]::new();$c.ObjectRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($script:alias);$c.Inverted=$inverse;return $c}
function Ready{return Logic 'AND' @((Guard),(Loaded))}
function Pause($id,$condition){$n=$script:pauseTemplate.DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};Set-RedHandleProperty $n Condition $condition;return $n}
function Counter($id,$name){$n=New-SetFactNode $id $name 1;$n.Type.Chunk.SetExactValue=$false;return $n}
function ShowNode($id,[bool]$visible){
 $a=[WolvenKit.RED4.Types.questShowWorldNode_NodeType]::new()
 $a.ComponentName=[WolvenKit.RED4.Types.CName]::op_Implicit('None');$a.IsPlayer=$false
 $a.ObjectRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($script:alias);$a.Show=$visible
 $n=[WolvenKit.RED4.Types.questWorldDataManagerNodeDefinition]::new();$n.Id=[uint16]$id
 Set-RedHandleProperty $n Type $a
 [void](New-QuestSocket $n 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
 [void](New-QuestSocket $n 'In' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
 [void](New-QuestSocket $n 'Out' ([WolvenKit.RED4.Types.Enums+questSocketType]::Output));return $n
}
$graph=$file.RootChunk.Graph.Chunk;$graph.Nodes.Clear()
$nodes=@(
 (New-InputNode 0 'In1'),(New-SetFactNode 1 'PTFRMVOL_Registered' 1),(New-SetFactNode 2 'PTFRMVOL_Revision' 1),
 (New-SetFactNode 3 'PTFRMVOL_Applied' 0),(New-SetFactNode 4 'PTFRMVOL_Ready' 0),(New-SetFactNode 5 'PTFRMVOL_Enabled' 0),(New-SetFactNode 6 'PTFRMVOL_DesiredVisible' 1),
 (Pause 7 (Guard)),(New-SetFactNode 8 'PTFRMVOL_Owned' 1),(Counter 9 'PTFRMVOL_Acquires'),(New-SetFactNode 10 'PTFRMVOL_Applied' 1),
 (Pause 11 (Logic 'OR' @((Loaded),(Guard $true)))),(New-ConditionNode 12 (Ready)),(New-ConditionNode 13 (Fact 'PTFRMVOL_DesiredVisible' 1)),
 (ShowNode 14 $true),(Counter 15 'PTFRMVOL_ShowRequests'),(New-SetFactNode 16 'PTFRMVOL_LastRequested' 1),(New-SetFactNode 17 'PTFRMVOL_Ready' 1),
 (Pause 18 (Logic 'OR' @((Fact 'PTFRMVOL_DesiredVisible' 1 $true),(Loaded $true),(Guard $true)))),
 (ShowNode 19 $false),(Counter 20 'PTFRMVOL_HideRequests'),(New-SetFactNode 21 'PTFRMVOL_LastRequested' 0),(New-SetFactNode 22 'PTFRMVOL_Ready' 1),
 (Pause 23 (Logic 'OR' @((Fact 'PTFRMVOL_DesiredVisible' 0 $true),(Loaded $true),(Guard $true)))),
 (New-SetFactNode 24 'PTFRMVOL_Ready' 0),(New-ConditionNode 25 (Guard)),(New-ConditionNode 26 (ReleaseGuard)),
 (ShowNode 27 $true),(Counter 28 'PTFRMVOL_Releases'),(New-SetFactNode 29 'PTFRMVOL_Applied' 0),
 (New-SetFactNode 30 'PTFRMVOL_Ready' 0),(New-SetFactNode 31 'PTFRMVOL_Owned' 0),(New-SetFactNode 32 'PTFRMVOL_Enabled' 0)
)
foreach($n in $nodes){Add-RedHandle $graph.Nodes $n}
$edges=@(
 @(0,'Out',1),@(1,'Out',2),@(2,'Out',3),@(3,'Out',4),@(4,'Out',5),@(5,'Out',6),@(6,'Out',7),
 @(7,'Out',8),@(8,'Out',9),@(9,'Out',10),@(10,'Out',11),@(11,'Out',12),
 @(12,'True',13),@(12,'False',25),@(13,'True',14),@(13,'False',19),
 @(14,'Out',15),@(15,'Out',16),@(16,'Out',17),@(17,'Out',18),@(18,'Out',24),
 @(19,'Out',20),@(20,'Out',21),@(21,'Out',22),@(22,'Out',23),@(23,'Out',24),
 @(24,'Out',25),@(25,'True',11),@(25,'False',26),@(26,'True',27),@(26,'False',28),
 @(27,'Out',28),@(28,'Out',29),@(29,'Out',30),@(30,'Out',31),@(31,'Out',32),@(32,'Out',7)
)
foreach($e in $edges){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $e[0]) $e[1]) (Get-QuestSocket (Get-QuestNode $graph $e[2]) 'In'))}
$path=Join-Path $source $phaseDepot
Write-Cr2wFile $file $path
$readback=Read-Cr2wFile $path
Export-Cr2wJson $readback (Join-Path $audit 'original_lamp_s1_phase.json')
if($readback.RootChunk.Graph.Chunk.Nodes.Count -ne 33){throw 'Original light phase readback count mismatch'}
$manifest=[ordered]@{status='BUILT_SINGLETON_ORIGINAL_CONTROLLER_SOURCE_ONLY_NOT_INSTALLED';phase_depot=$phaseDepot;phase_sha256=(Get-FileHash $path).Hash;alias=$alias;nodes=33;edges=$edges;guards=$facts;story_fact_writes=0;variant_writes=0;original_visibility_writes=3;installed=$false;live_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'original_lamp_s1_controller_manifest.json'),($manifest|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
[pscustomobject]$manifest|Select-Object status,phase_sha256,alias,nodes|ConvertTo-Json
