param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\afterlife_world'
$source=Join-Path $WorkspaceRoot 'build\AfterlifeR1\dancers_source'
$vanillaPath=Join-Path $WorkspaceRoot 'research\phase2b_p4\vendor_owner\raw\base\open_world\community\watson\little_china\wat_lch_phase.questphase'
$vanilla=Read-Cr2wFile $vanillaPath
if($vanilla.EmbeddedFiles[1].FileName.ToString() -ne 'base\quest\main_quests\prologue\q005\afterlife\phases\afterlife_master_phase.questphase'){throw 'Vanilla Afterlife owner changed'}
$branch=(Get-QuestNode $vanilla.EmbeddedFiles[1].Content.Graph.Chunk 6).PhaseGraph.Chunk
$pauseTemplate=(Get-QuestNode $branch 12).DeepCopy()
$spawnTemplate=(Get-QuestNode $branch 24).DeepCopy()
$file=Read-Cr2wFile (Join-Path $WorkspaceRoot 'build\MistyViktorAccessR11\source\towercontinued\misty_viktor_world\access_r11.questphase')
$graph=$file.RootChunk.Graph.Chunk;$graph.Nodes.Clear();$file.EmbeddedFiles.Clear();$file.RootChunk.PhasePrefabs.Clear()
$spawner='$/03_night_city/c_watson/little_china/#loc_q103_afterlife/#loc_q103_afterlife_openworld/#q005_com_afterlife_tube_dancers'
$facts=[ordered]@{
 PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1
 q305_johnny_scene_active=0;q115_point_of_no_return=0;PTFRBASE_Suspended=0;PTFRWORLD_Suspended=0
 PTFRAL1_Enabled=1;PTFRAL1_QuestOwns=0;PTFRAL1_Suspended=0
}
function Logic([string]$op,$children){$c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::$op;foreach($v in $children){Add-RedHandle $c.Conditions $v};return $c}
function Guard([bool]$inverse=$false){$parts=[Collections.Generic.List[object]]::new();foreach($key in $script:facts.Keys){$cmp=if($inverse){[WolvenKit.RED4.Types.Enums+EComparisonType]::NotEqual}else{[WolvenKit.RED4.Types.Enums+EComparisonType]::Equal};$parts.Add((New-FactCondition $key $script:facts[$key] $cmp))};return Logic $(if($inverse){'OR'}else{'AND'}) $parts}
function Loaded([string]$ref,[bool]$inverse=$false){$c=[WolvenKit.RED4.Types.questNodeLoadingCondition]::new();$c.ObjectRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref);$c.Inverted=$inverse;return $c}
function Pause([int]$id,$condition){$n=$script:pauseTemplate.DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};Set-RedHandleProperty $n Condition $condition;return $n}
function Delay([int]$id,[int]$seconds){$c=$script:pauseTemplate.Condition.Chunk.DeepCopy();if($c.Type.Chunk.GetType().Name -ne 'questRealtimeDelay_ConditionType'){throw 'Delay precedent changed'};$c.Type.Chunk.Seconds=[uint32]$seconds;return Pause $id $c}
function Counter([int]$id,[string]$name){$n=New-SetFactNode $id $name 1;$n.Type.Chunk.SetExactValue=$false;return $n}
function Entry([int]$id,[string]$name,[string]$action){
 $n=$script:spawnTemplate.DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}
 if($n.Actions.Count -ne 1 -or $n.Actions[0].Type.Chunk.CommunityEntryPhaseName.ToString() -ne 'default'){throw 'Tube dancer precedent changed'}
 $p=$n.Actions[0].Type.Chunk;$p.Action=[WolvenKit.RED4.Types.Enums+populationSpawnerObjectCtrlAction]::$action
 $p.CommunityEntryName=[WolvenKit.RED4.Types.CName]::op_Implicit($name);$p.SpawnerReference=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($script:spawner);return $n
}
$edges=[Collections.Generic.List[object]]::new()
function Add($n){Add-RedHandle $script:graph.Nodes $n}
function Link([int]$from,[string]$socket,[int]$to){$script:edges.Add(@($from,$socket,$to));[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $script:graph $from) $socket) (Get-QuestSocket (Get-QuestNode $script:graph $to) 'In'))}
Add (New-InputNode 0 'In1');Add (New-SetFactNode 1 'PTFRAL1_DancersRegistered' 1);Link 0 'Out' 1
$delays=@(0,2,6,8,10,14,18,21,26,30)
$spots=Get-Content (Join-Path $audit 'hologram_physical_spots.json') -Raw|ConvertFrom-Json
$registry=Get-Content (Join-Path $audit 'hologram_vanilla_registry.json') -Raw|ConvertFrom-Json
$initial=@($registry[0].community.entriesInitialState)
if($spots.Count -ne 10 -or $initial.Count -ne 10 -or @($initial|Where-Object {$_.entryActiveOnStart -ne 0}).Count){throw 'Dancer source count/start policy changed'}
$specs=[Collections.Generic.List[object]]::new()
for($num=1;$num -le 10;$num++){
 $name='dancer_'+$num.ToString('00');$ref='$/03_night_city/c_watson/little_china/#loc_q103_afterlife/#loc_q103_afterlife_openworld/#afterlife_ws_'+$name
 $spot=@($spots|Where-Object {$_.ref -eq $ref});if($spot.Count -ne 1 -or $spot[0].category -ne 'Exterior' -or $spot[0].variant_ranges.Count -or $spot[0].node.'$type' -ne 'worldAISpotNode' -or $spot[0].node.isWorkspotInfinite -ne 1){throw "Physical workspot scope changed for $name"}
 $i=10+($num-1)*20;$prefix='PTFRAL1_Dancer'+$num.ToString('00')
 Add (Pause $i (Logic 'AND' @((Guard),(Loaded $ref))))
 Add (Delay ($i+1) $delays[$num-1])
 Add (New-ConditionNode ($i+2) (Logic 'AND' @((Guard),(Loaded $ref))))
 Add (Entry ($i+3) $name 'Reactivate')
 Add (Counter ($i+4) ($prefix+'Requests'))
 Add (New-SetFactNode ($i+5) ($prefix+'Ready') 1)
 Add (Pause ($i+6) (Logic 'OR' @((Guard $true),(Loaded $ref $true))))
 # Original community ownership yields when any baseline/handoff guard is lost.
 # Only safe stream-out deactivates our exact selected entry.
 Add (New-ConditionNode ($i+7) (Guard))
 Add (Entry ($i+8) $name 'Deactivate')
 Add (Counter ($i+9) ($prefix+'Releases'))
 Add (New-SetFactNode ($i+10) ($prefix+'Ready') 0)
 Link 1 'Out' $i;Link $i 'Out' ($i+1);Link ($i+1) 'Out' ($i+2);Link ($i+2) 'False' $i;Link ($i+2) 'True' ($i+3)
 foreach($j in 3..6){Link ($i+$j) 'Out' ($i+$j+1)}
 Link ($i+7) 'False' ($i+10);Link ($i+7) 'True' ($i+8);Link ($i+8) 'Out' ($i+9);Link ($i+9) 'Out' ($i+10);Link ($i+10) 'Out' $i
 $specs.Add([ordered]@{entry=$name;phase='default';ref=$ref;delay=$delays[$num-1];start=$i;source_sector=$spot[0].source_json;source_node=$spot[0].node_index;position=$spot[0].datum.Position;appearance='service__tubedancer_wa_tube_dancer_'+$num.ToString('00')})
}
$depot='towercontinued\afterlife_r1\dancers.questphase';$path=Join-Path $source $depot
Write-Cr2wFile $file $path;$readback=Read-Cr2wFile $path;Export-Cr2wJson $readback (Join-Path $audit 'dancers_phase.json')
if($readback.RootChunk.Graph.Chunk.Nodes.Count -ne 112 -or $readback.RootChunk.PhasePrefabs.Count -ne 0 -or $readback.EmbeddedFiles.Count -ne 0){throw 'Dancer phase readback scope failure'}
$manifest=[ordered]@{status='BUILT_DANCERS_OFFLINE_LIVE_PENDING';source_root=$source;resources=@($depot);sha256=(Get-FileHash $path).Hash;guards=$facts;spawner=$spawner;entries=@($specs);edges=@($edges);registered_fact='PTFRAL1_DancersRegistered';registration=[ordered]@{path=$depot;parent='ep1\quest\ep1.quest';node=@(1);socket='Out'};vanilla_owner=$vanillaPath;vanilla_owner_sha256=(Get-FileHash $vanillaPath).Hash;world_overrides=0;scene_starts=0;story_writes=0;live_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'dancers_manifest.json'),($manifest|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
[pscustomobject]$manifest|Select-Object status,sha256,source_root|ConvertTo-Json
