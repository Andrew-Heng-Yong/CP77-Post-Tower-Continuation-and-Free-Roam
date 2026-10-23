param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$out=Join-Path $WorkspaceRoot 'build\MistyViktorLightPOC'
$source=Join-Path $out 'source'
$worldPath=Join-Path $audit 'light_poc_world_manifest.json'
$world=Get-Content -LiteralPath $worldPath -Raw|ConvertFrom-Json
$nodeRef='$/03_night_city/#PTFRMV_LightPOC01'
$variant='PTFRMV_LightPOC'
if($world.status -ne 'BUILT_SINGLE_LIGHT_POC_SOURCE_ONLY_NOT_PACKED_INSTALLED_OR_LIVE' -or $world.private_ref -ne $nodeRef -or $world.variant_name -ne $variant -or $world.resources.Count -ne 2){throw 'Unexpected isolated-light world scope'}
$resources=[Collections.Generic.List[string]]::new()
foreach($depot in $world.resources){
 if(-not $depot.StartsWith('towercontinued\misty_viktor_light_poc\') -or $depot.Contains('..')){throw 'World resource escaped private namespace'}
 $src=Join-Path $world.source_root $depot
 $expected=if($depot.EndsWith('.streamingsector')){$world.sector_sha256}else{$world.block_sha256}
 if((Get-FileHash -LiteralPath $src).Hash -ne $expected){throw 'World source hash changed'}
 $dst=Join-Path $source $depot
 New-Item -ItemType Directory -Force (Split-Path -Parent $dst)|Out-Null
 Copy-Item -LiteralPath $src -Destination $dst -Force
 $resources.Add($depot)
}
$file=Read-Cr2wFile (Join-Path $WorkspaceRoot 'archive\b0_ordinary_mirrors_c5_red_dirt\source\towercontinued\ordinary_mirrors_c5_red_dirt\m42_gate.questphase')
if($file.RootChunk.PhasePrefabs.Count -ne 0){throw 'Unexpected foundation prefabs'}
$pauseTemplate=(Get-QuestNode $file.RootChunk.Graph.Chunk 1).DeepCopy()
$cleanup=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\main_quests\q307\phases\q307_cleanup.questphase')
$toggleTemplate=(Get-QuestNode $cleanup.RootChunk.Graph.Chunk 22).DeepCopy()
$matches=@($toggleTemplate.Type.Chunk.Params|Where-Object {$_.GetType().Name -eq 'questTogglePrefabVariant_NodeTypeParams' -and @($_.VariantStates|Where-Object {$_.Name.ToString() -eq 'q307_zetatech'}).Count})
if($matches.Count -ne 1 -or $matches[0].VariantStates.Count -ne 1){throw 'Vanilla variant precedent drifted'}
$param=$matches[0].DeepCopy()
$param.PrefabNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($world.variant_owner)
$param.VariantStates[0].Name=[WolvenKit.RED4.Types.CName]::op_Implicit($variant)
$toggleTemplate.Type.Chunk.Params.Clear();[void]$toggleTemplate.Type.Chunk.Params.Add($param)
$facts=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q305_johnny_scene_active=0;q115_point_of_no_return=0;PTFRBASE_Suspended=0;PTFRWORLD_Suspended=0;PTFRMVLP_Enabled=1;PTFRMVLP_Suspended=0;PTFRMVLP_QuestOwns=0}
function Fact($name,$value,[bool]$not=$false){
 $comparison=if($not){[WolvenKit.RED4.Types.Enums+EComparisonType]::NotEqual}else{[WolvenKit.RED4.Types.Enums+EComparisonType]::Equal}
 return New-FactCondition $name $value $comparison
}
function Logic($operation,$children){
 $c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::$operation
 foreach($child in $children){Add-RedHandle $c.Conditions $child};return $c
}
function Guard([bool]$inverse=$false){
 $children=[Collections.Generic.List[object]]::new()
 foreach($name in $script:facts.Keys){$children.Add((Fact $name $script:facts[$name] $inverse))}
 # Reject corrupt/out-of-range desired-state values, rather than treating any
 # non-one value as a hide command.
 $children.Add((Logic $(if($inverse){'AND'}else{'OR'}) @((Fact 'PTFRMVLP_DesiredVisible' 0 $inverse),(Fact 'PTFRMVLP_DesiredVisible' 1 $inverse))))
 return Logic $(if($inverse){'OR'}else{'AND'}) $children
}
function Loaded([bool]$inverse=$false){
 $c=[WolvenKit.RED4.Types.questNodeLoadingCondition]::new();$c.ObjectRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($script:nodeRef);$c.Inverted=$inverse;return $c
}
function Ready{return Logic 'AND' @((Guard),(Loaded))}
function Pause($id,$condition){
 $n=$script:pauseTemplate.DeepCopy();$n.Id=[uint16]$id
 foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}
 Set-RedHandleProperty $n Condition $condition;return $n
}
function Toggle($id,[bool]$visible){
 $n=$script:toggleTemplate.DeepCopy();$n.Id=[uint16]$id
 foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}
 $n.Type.Chunk.Params[0].VariantStates[0].Show=$visible;return $n
}
function Counter($id,$name){$n=New-SetFactNode $id $name 1;$n.Type.Chunk.SetExactValue=$false;return $n}
function ShowNode($id,[bool]$visible){
 # Exact mq016_02_afterlife.scene790/792 action shape; only objectRef differs.
 $a=[WolvenKit.RED4.Types.questShowWorldNode_NodeType]::new()
 $a.ComponentName=[WolvenKit.RED4.Types.CName]::op_Implicit('None');$a.IsPlayer=$false
 $a.ObjectRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($script:nodeRef);$a.Show=$visible
 $n=[WolvenKit.RED4.Types.questWorldDataManagerNodeDefinition]::new();$n.Id=[uint16]$id
 Set-RedHandleProperty $n Type $a
 [void](New-QuestSocket $n 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
 [void](New-QuestSocket $n 'In' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
 [void](New-QuestSocket $n 'Out' ([WolvenKit.RED4.Types.Enums+questSocketType]::Output));return $n
}
$graph=$file.RootChunk.Graph.Chunk;$graph.Nodes.Clear()
$nodes=@(
 (New-InputNode 0 'In1'),(New-SetFactNode 1 'PTFRMVLP_Registered' 1),(New-SetFactNode 2 'PTFRMVLP_Revision' 1),
 (New-SetFactNode 3 'PTFRMVLP_Applied' 0),(New-SetFactNode 4 'PTFRMVLP_Ready' 0),(New-SetFactNode 5 'PTFRMVLP_Enabled' 0),(New-SetFactNode 6 'PTFRMVLP_DesiredVisible' 1),
 (Pause 7 (Guard)),(Toggle 8 $true),(Counter 9 'PTFRMVLP_Acquires'),(New-SetFactNode 10 'PTFRMVLP_Applied' 1),
 (Pause 11 (Logic 'OR' @((Loaded),(Guard $true)))),(New-ConditionNode 12 (Ready)),(New-ConditionNode 13 (Fact 'PTFRMVLP_DesiredVisible' 1)),
 (ShowNode 14 $true),(Counter 15 'PTFRMVLP_ShowRequests'),(New-SetFactNode 16 'PTFRMVLP_LastRequested' 1),(New-SetFactNode 17 'PTFRMVLP_Ready' 1),
 (Pause 18 (Logic 'OR' @((Fact 'PTFRMVLP_DesiredVisible' 1 $true),(Loaded $true),(Guard $true)))),
 (ShowNode 19 $false),(Counter 20 'PTFRMVLP_HideRequests'),(New-SetFactNode 21 'PTFRMVLP_LastRequested' 0),(New-SetFactNode 22 'PTFRMVLP_Ready' 1),
 (Pause 23 (Logic 'OR' @((Fact 'PTFRMVLP_DesiredVisible' 0 $true),(Loaded $true),(Guard $true)))),
 (New-SetFactNode 24 'PTFRMVLP_Ready' 0),(New-ConditionNode 25 (Guard)),(Toggle 26 $false),
 (Counter 27 'PTFRMVLP_Releases'),(New-SetFactNode 28 'PTFRMVLP_Applied' 0),(New-SetFactNode 29 'PTFRMVLP_Ready' 0),(New-SetFactNode 30 'PTFRMVLP_Enabled' 0)
)
foreach($n in $nodes){Add-RedHandle $graph.Nodes $n}
# Single serialized loop: no parallel listeners survive stop/unload/rearm.
$edges=@(@(0,'Out',1),@(1,'Out',2),@(2,'Out',3),@(3,'Out',4),@(4,'Out',5),@(5,'Out',6),@(6,'Out',7),@(7,'Out',8),@(8,'Out',9),@(9,'Out',10),@(10,'Out',11),@(11,'Out',12),@(12,'True',13),@(12,'False',25),@(13,'True',14),@(14,'Out',15),@(15,'Out',16),@(16,'Out',17),@(17,'Out',18),@(18,'Out',24),@(13,'False',19),@(19,'Out',20),@(20,'Out',21),@(21,'Out',22),@(22,'Out',23),@(23,'Out',24),@(24,'Out',25),@(25,'True',11),@(25,'False',26),@(26,'Out',27),@(27,'Out',28),@(28,'Out',29),@(29,'Out',30),@(30,'Out',7))
foreach($e in $edges){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $e[0]) $e[1]) (Get-QuestSocket (Get-QuestNode $graph $e[2]) 'In'))}
$phaseDepot='towercontinued\misty_viktor_light_poc\light_poc.questphase'
Write-Cr2wFile $file (Join-Path $source $phaseDepot)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $phaseDepot)) (Join-Path $audit 'light_poc_phase.json')
$resources.Add($phaseDepot)
$crc=65535;foreach($byte in [Text.Encoding]::UTF8.GetBytes($phaseDepot+':1')){$x=($crc -shr 8) -bxor $byte;$x=$x -bxor ($x -shr 4);$crc=(($crc -shl 8) -bxor ($x -shl 12) -bxor ($x -shl 5) -bxor $x) -band 65535}
$parent=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\ep1.quest')
if(@($parent.RootChunk.Graph.Chunk.Nodes|Where-Object {$_.Chunk.Id.ToString() -eq "$crc"}).Count){throw 'Native parent registration ID collision'}
$xl=@('streaming:','  blocks:',('    - '+$world.block_depot),'quest:','  phases:',"    - path: $phaseDepot",'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out')
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$archive=Join-Path $out 'TowerContinued_MistyViktorLightPOC.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Light POC pack failed'}}finally{$stream.Dispose()}
[IO.File]::WriteAllLines(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hash,[ref]$packed).ToString() -ne 'NoError'){throw 'Light POC reopen failed'}
if(@(Compare-Object @($resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Light POC package scope mismatch'}
$probe=Join-Path $WorkspaceRoot 'diagnostics\PTFR_MistyViktor_Light_POC\init.lua'
$manifest=[ordered]@{status='BUILT_LIGHT_POC_NOT_INSTALLED_OR_LIVE';archive=$archive;source_root=$source;sha256=(Get-FileHash $archive).Hash;xl_sha256=(Get-FileHash ($archive+'.xl')).Hash;probe=$probe;probe_sha256=(Get-FileHash $probe).Hash;resources=@($resources);phase_depot=$phaseDepot;registration_id=$crc;world_manifest=$worldPath;world_manifest_sha256=(Get-FileHash $worldPath).Hash;guards=$facts;edges=$edges;node_ref=$nodeRef;private_variant=$variant;variant_owner=$world.variant_owner;source_light_datum=3907;native_nodes=$graph.Nodes.Count;single_serial_controller=$true;original_world_resource_overrides=0;original_lighting_changes=0;story_fact_writes=0;scene_starts=0;live_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'light_poc_manifest.json'),($manifest|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
[pscustomobject]$manifest|Select-Object status,sha256,native_nodes,registration_id,node_ref|ConvertTo-Json
