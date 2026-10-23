param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$world=Get-Content (Join-Path $audit 'lighting_r8_world_manifest.json') -Raw|ConvertFrom-Json
if($world.status -ne 'BUILT_R8_WORLD_SOURCE_NOT_INSTALLED' -or $world.original_alias_count -ne 12 -or $world.cold_clone_count -ne 5){throw 'R8 world source changed'}
$source=Join-Path $WorkspaceRoot 'build\MistyLightingR8\source'
$template=Join-Path $WorkspaceRoot 'build\MistyOriginalLampAliasS1\source\towercontinued\misty_viktor_original_lamp_s1\original_lamp_s1.questphase'
$fileTemplate=Read-Cr2wFile $template
$pauseTemplate=(Get-QuestNode $fileTemplate.RootChunk.Graph.Chunk 7).DeepCopy()
$cleanup=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\main_quests\q307\phases\q307_cleanup.questphase')
$toggleTemplate=(Get-QuestNode $cleanup.RootChunk.Graph.Chunk 22).DeepCopy()
$toggleParam=@($toggleTemplate.Type.Chunk.Params|Where-Object {$_.GetType().Name -eq 'questTogglePrefabVariant_NodeTypeParams' -and @($_.VariantStates|Where-Object {$_.Name.ToString() -eq 'q307_zetatech'}).Count})
if($toggleParam.Count -ne 1 -or $toggleParam[0].VariantStates.Count -ne 1){throw 'Vanilla variant action precedent changed'}
$base=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q305_johnny_scene_active=0;q115_point_of_no_return=0;PTFRBASE_Suspended=0;PTFRWORLD_Suspended=0}
function Fact([string]$name,[int]$value,[bool]$inverse=$false){
 $cmp=if($inverse){[WolvenKit.RED4.Types.Enums+EComparisonType]::NotEqual}else{[WolvenKit.RED4.Types.Enums+EComparisonType]::Equal}
 return New-FactCondition $name $value $cmp
}
function Logic([string]$op,$children){
 $c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::$op
 foreach($child in $children){Add-RedHandle $c.Conditions $child};return $c
}
function Guard($facts,[bool]$inverse=$false){
 $children=[Collections.Generic.List[object]]::new()
 foreach($key in $facts.Keys){$children.Add((Fact $key $facts[$key] $inverse))}
 return Logic $(if($inverse){'OR'}else{'AND'}) $children
}
function Loaded([string]$ref,[bool]$inverse=$false){
 $c=[WolvenKit.RED4.Types.questNodeLoadingCondition]::new()
 $c.ObjectRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref);$c.Inverted=$inverse;return $c
}
function LoadingGroup($refs,[bool]$inverse=$false){
 $parts=[Collections.Generic.List[object]]::new()
 foreach($ref in $refs){$parts.Add((Loaded $ref $inverse))}
 return Logic $(if($inverse){'OR'}else{'AND'}) $parts
}
function Pause([int]$id,$condition){
 $n=$script:pauseTemplate.DeepCopy();$n.Id=[uint16]$id
 foreach($socket in $n.Sockets){$socket.Chunk.Connections.Clear()}
 Set-RedHandleProperty $n Condition $condition;return $n
}
function ShowNode([int]$id,[string]$alias,[bool]$visible){
 $a=[WolvenKit.RED4.Types.questShowWorldNode_NodeType]::new()
 $a.ComponentName=[WolvenKit.RED4.Types.CName]::op_Implicit('None');$a.IsPlayer=$false
 $a.ObjectRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($alias);$a.Show=$visible
 $n=[WolvenKit.RED4.Types.questWorldDataManagerNodeDefinition]::new();$n.Id=[uint16]$id
 Set-RedHandleProperty $n Type $a
 [void](New-QuestSocket $n 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
 [void](New-QuestSocket $n 'In' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
 [void](New-QuestSocket $n 'Out' ([WolvenKit.RED4.Types.Enums+questSocketType]::Output));return $n
}
function Variant([int]$id,[bool]$visible){
 $n=$script:toggleTemplate.DeepCopy();$n.Id=[uint16]$id
 foreach($socket in $n.Sockets){$socket.Chunk.Connections.Clear()}
 $n.Type.Chunk.Params.Clear();$p=$script:toggleParam[0].DeepCopy()
 $p.PrefabNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($script:world.private_variant_owner)
 $p.VariantStates[0].Name=[WolvenKit.RED4.Types.CName]::op_Implicit($script:world.private_variant)
 $p.VariantStates[0].Show=$visible
 [void]$n.Type.Chunk.Params.Add($p);return $n
}
function Build([string]$group,[string]$prefix,$original,$cold,$extra,[bool]$hasVariant){
 $file=Read-Cr2wFile $script:template;$graph=$file.RootChunk.Graph.Chunk;$graph.Nodes.Clear()
 $facts=[ordered]@{};foreach($key in $script:base.Keys){$facts[$key]=$script:base[$key]}
 foreach($key in $extra.Keys){$facts[$key]=$extra[$key]}
 $safe=[ordered]@{q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q305_johnny_scene_active=0;q115_point_of_no_return=0}
 $originalRefs=@($original|ForEach-Object {$_.alias});$allRefs=@($originalRefs)+@($cold|ForEach-Object {$_.alias})
 $ids=[Collections.Generic.List[int]]::new();$edges=[Collections.Generic.List[object]]::new();$actions=[Collections.Generic.List[object]]::new()
 $next=0
 function Add($node){$idValue=[int]::Parse($node.Id.ToString());Add-RedHandle $graph.Nodes $node;$ids.Add($idValue);return $idValue}
 function Link([int]$from,[string]$socket,[int]$to){$edges.Add(@($from,$socket,$to));[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $from) $socket) (Get-QuestSocket (Get-QuestNode $graph $to) 'In'))}
 function Linear([int]$start,$created){$last=$start;foreach($id in $created){Link $last 'Out' $id;$last=$id};return $last}
 $input=Add (New-InputNode ($next++) 'In1')
 $reg=Add (New-SetFactNode ($next++) ($prefix+'Registered') 1)
 $rev=Add (New-SetFactNode ($next++) ($prefix+'Revision') 8)
 $clear=Add (New-SetFactNode ($next++) ($prefix+'Applied') 0)
 $readyClear=Add (New-SetFactNode ($next++) ($prefix+'Ready') 0)
 $guardWait=Add (Pause ($next++) (Guard $facts))
 $variantOn=-1;if($hasVariant){$variantOn=Add (Variant ($next++) $true)}
 $loadedWait=Add (Pause ($next++) (Logic 'OR' @((LoadingGroup $allRefs),(Guard $facts $true))))
 $guardCheck=Add (New-ConditionNode ($next++) (Guard $facts))
 $loadedCheck=Add (New-ConditionNode ($next++) (LoadingGroup $allRefs))
 $apply=[Collections.Generic.List[int]]::new()
 foreach($item in $cold){$id=Add (ShowNode ($next++) $item.alias $true);$apply.Add($id);$actions.Add(@{id=$id;alias=$item.alias;show=$true;phase='apply'})}
 foreach($item in $original){$id=Add (ShowNode ($next++) $item.alias $false);$apply.Add($id);$actions.Add(@{id=$id;alias=$item.alias;show=$false;phase='apply'})}
 $count=Add (New-SetFactNode ($next++) ($prefix+'ApplyRequests') 1);(Get-QuestNode $graph $count).Type.Chunk.SetExactValue=$false
 $applied=Add (New-SetFactNode ($next++) ($prefix+'Applied') 1)
 $ready=Add (New-SetFactNode ($next++) ($prefix+'Ready') 1)
 $invalidWait=Add (Pause ($next++) (Logic 'OR' @((Guard $facts $true),(LoadingGroup $allRefs $true))))
 $readyOff=Add (New-SetFactNode ($next++) ($prefix+'Ready') 0)
 $guardAgain=Add (New-ConditionNode ($next++) (Guard $facts))
 $variantOff=-1;if($hasVariant){$variantOff=Add (Variant ($next++) $false)}
 $releaseWait=Add (Pause ($next++) (Logic 'OR' @((LoadingGroup $originalRefs),(Guard $safe $true))))
 $safeCheck=Add (New-ConditionNode ($next++) (Guard $safe))
 $restore=[Collections.Generic.List[int]]::new()
 foreach($item in $original){$id=Add (ShowNode ($next++) $item.alias $true);$restore.Add($id);$actions.Add(@{id=$id;alias=$item.alias;show=$true;phase='release'})}
 $releaseCount=Add (New-SetFactNode ($next++) ($prefix+'ReleaseRequests') 1);(Get-QuestNode $graph $releaseCount).Type.Chunk.SetExactValue=$false
 $releaseClear=Add (New-SetFactNode ($next++) ($prefix+'Applied') 0)
 $releaseReady=Add (New-SetFactNode ($next++) ($prefix+'Ready') 0)
 [void](Linear $input @($reg,$rev,$clear,$readyClear,$guardWait))
 if($hasVariant){Link $guardWait 'Out' $variantOn;Link $variantOn 'Out' $loadedWait}else{Link $guardWait 'Out' $loadedWait}
 Link $loadedWait 'Out' $guardCheck;Link $guardCheck 'True' $loadedCheck
 Link $loadedCheck 'False' $loadedWait
 if($apply.Count){Link $loadedCheck 'True' $apply[0];[void](Linear $apply[0] @($apply|Select-Object -Skip 1));Link $apply[$apply.Count-1] 'Out' $count}
 else{Link $loadedCheck 'True' $count}
 [void](Linear $count @($applied,$ready,$invalidWait,$readyOff,$guardAgain))
 Link $guardAgain 'True' $loadedWait
 if($hasVariant){Link $guardCheck 'False' $variantOff;Link $guardAgain 'False' $variantOff;Link $variantOff 'Out' $releaseWait}
 else{Link $guardCheck 'False' $releaseWait;Link $guardAgain 'False' $releaseWait}
 Link $releaseWait 'Out' $safeCheck
 if($restore.Count){Link $safeCheck 'True' $restore[0];[void](Linear $restore[0] @($restore|Select-Object -Skip 1));Link $restore[$restore.Count-1] 'Out' $releaseCount}
 else{Link $safeCheck 'True' $releaseCount}
 Link $safeCheck 'False' $releaseCount
 [void](Linear $releaseCount @($releaseClear,$releaseReady,$guardWait))
 if(@($ids|Sort-Object -Unique).Count -ne $next -or $graph.Nodes.Count -ne $next){throw ('Graph node IDs not unique: '+$group)}
 $depot="towercontinued\misty_viktor_lighting_r8\$group.questphase"
 $path=Join-Path $script:source $depot
 Write-Cr2wFile $file $path
 $readback=Read-Cr2wFile $path
 Export-Cr2wJson $readback (Join-Path $script:audit ("lighting_r8_$group`_phase.json"))
 if($readback.RootChunk.Graph.Chunk.Nodes.Count -ne $next){throw ('Phase readback mismatch: '+$group)}
 return [ordered]@{group=$group;prefix=$prefix;depot=$depot;path=$path;sha256=(Get-FileHash $path).Hash;nodes=$next;edges=@($edges);actions=@($actions);guard=$facts;original_refs=$originalRefs;cold_refs=@($cold|ForEach-Object {$_.alias});automatic=$true;requires_private_variant=$hasVariant}
}
$pink=@($world.original_targets|Where-Object {$_.group -eq 'pink'})
$police=@($world.original_targets|Where-Object {$_.group -eq 'police'})
$neon=Build 'neon' 'PTFRMVN_' $pink @($world.cold_targets) ([ordered]@{PTFRMVN_Suspended=0}) $true
$cop=Build 'police' 'PTFRMVP_' $police @() ([ordered]@{PTFRMV_Revision=7;PTFRMV_Applied=1;PTFRMV_Suspended=0;PTFRMVP_Suspended=0}) $false
$manifest=[ordered]@{status='BUILT_R8_AUTOMATIC_NATIVE_PHASES_NOT_INSTALLED';neon=$neon;police=$cop;story_fact_writes=0;original_variant_writes=0;private_variant_writes=2;opt_in_fact=0;installed=$false;live_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'lighting_r8_phase_manifest.json'),($manifest|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))
[pscustomobject]@{status=$manifest.status;neon_nodes=$neon.nodes;police_nodes=$cop.nodes;neon_sha256=$neon.sha256;police_sha256=$cop.sha256}|ConvertTo-Json
