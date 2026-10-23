param([string]$BuildName='camera_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))
if($BuildName -notmatch '^camera_[0-9]{2}$'){throw 'Fresh camera_NN build required'}
$out=Join-Path $ws ('prealpha/postending_pa5/camera/build/'+$BuildName)
if(Test-Path -LiteralPath $out){throw 'Never overwrite a prior candidate'}
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly
function J($v){[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($v,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())}
function Report($p,$v){[IO.File]::WriteAllText($p,($v|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))}
function Hash($p){(Get-FileHash -LiteralPath $p).Hash}
$h10path=Join-Path $ws 'research/b0_h10_generalization/extracted_interactions/raw/base/quest/minor_quests/mq000/scenes/mq000_01_apartment.scene'
if((Hash $h10path) -cne 'BEC5AD07A4FCDB0515BF749392F5634D359C2F7688EBFEE2BD4A26AD9EDB2188'){throw 'Native H10 source changed'}
$roguepath=Join-Path $ws 'research/q307_extracted/raw/ep1/quest/main_quests/q307/scenes/final_boards/q307_ending_01_rogue.scene'
$boardpath=Join-Path $ws 'research/q307_extracted/raw/ep1/quest/main_quests/q307/phases/q307_ending_board.questphase'
$cppath=Join-Path $ws 'research/gig_restoration/batch_b4/sources/raw/base/open_world/street_stories/city_center/corpo_plaza/sts_cct_cpz_01/phases/sts_cct_cpz_01_combat.questphase'
$sourceHashes=@{};foreach($p in @($h10path,$roguepath,$boardpath,$cppath)){$sourceHashes[$p]=Hash $p}
$h10=Read-Cr2wFile $h10path;$rogue=Read-Cr2wFile $roguepath;$board=Read-Cr2wFile $boardpath;$cp=Read-Cr2wFile $cppath
$section=@($h10.RootChunk.SceneGraph.Chunk.Graph|Where-Object {$_.Chunk.NodeId.Id.ToString() -eq '660'})[0].Chunk.DeepCopy()
if($section.GetType().Name -ne 'scnSectionNode' -or $section.Events.Count -ne 1 -or $section.SectionDuration.Stu.ToString() -ne '1500'){throw 'Native reset section changed'}
$ev=$section.Events[0].Chunk
if($ev.GetType().Name -ne 'scneventsCameraParamsEvent' -or $ev.IsPlayerCamera.ToString() -ne 'True' -or $ev.CameraRef.ToString() -ne '0' -or
 $ev.CameraOverrideSettings.ResetDof.ToString() -ne 'True' -or $ev.CameraOverrideSettings.ResetFov.ToString() -ne 'True' -or $ev.CameraOverrideSettings.OverrideDof.ToString() -ne 'False' -or $ev.CameraOverrideSettings.OverrideFov.ToString() -ne 'False' -or
 $ev.StartTime.ToString() -ne '0' -or $ev.Duration.ToString() -ne '1500' -or $ev.TargetActor.Id.ToString() -ne '4294967040'){throw 'Expected player-only native reset semantics changed'}
$stockEvent=J $ev
$sceneDepot='towercontinued\postending_pa5\camera\optics_reset.scene'
$ownerDepot='towercontinued\postending_pa5\camera\owner.questphase'
$source=Join-Path $out 'source';$package=Join-Path $out 'package'
New-Item -ItemType Directory -Force -Path $out,$source,(Join-Path $package 'archive/pc/mod'),(Join-Path $package 'r6/scripts/PTFR_PreAlpha/PA5')|Out-Null
Report (Join-Path $out 'stock_reset_event.json') ($stockEvent|ConvertFrom-Json -Depth 100)

# Player camera is directly selected by IsPlayerCamera, with no performer ID.
# The same primitive in stock Rogue has zero PlayerActors. No actor, animation,
# external camera, audio, workspot, tier, teleport, shader or UI operation copied.
$root=[WolvenKit.RED4.Types.scnSceneResource]::new()
$root.CookingPlatform=$h10.RootChunk.CookingPlatform;$root.Version=$h10.RootChunk.Version
$root.SceneCategoryTag=$h10.RootChunk.SceneCategoryTag;$root.SceneSolutionHash=$h10.RootChunk.SceneSolutionHash.DeepCopy()
$sg=[WolvenKit.RED4.Types.scnSceneGraph]::new()
$start=@($rogue.RootChunk.SceneGraph.Chunk.Graph|Where-Object {$_.Chunk.NodeId.Id.ToString() -eq '1'})[0].Chunk.DeepCopy()
$end=@($rogue.RootChunk.SceneGraph.Chunk.Graph|Where-Object {$_.Chunk.NodeId.Id.ToString() -eq '2'})[0].Chunk.DeepCopy()
function SceneEdge($node,$target){
 $d=$start.OutputSockets[0].Destinations[0].DeepCopy();$d.NodeId.Id=[uint32]$target;$d.IsockStamp.Name=[uint16]0;$d.IsockStamp.Ordinal=[uint16]0
 foreach($s in $node.OutputSockets){$s.Destinations.Clear()};[void]$node.OutputSockets[0].Destinations.Add($d)
}
SceneEdge $start 660;SceneEdge $section 2
$section.ActorBehaviors.Clear()
foreach($s in $end.OutputSockets){$s.Destinations.Clear()}
foreach($n in @($start,$section,$end)){Add-RedHandle $sg.Graph $n}
[void]$sg.StartNodes.Add($start.NodeId.DeepCopy());[void]$sg.EndNodes.Add($end.NodeId.DeepCopy())
Set-RedHandleProperty $root SceneGraph $sg
[void]$root.EntryPoints.Add($rogue.RootChunk.EntryPoints[0].DeepCopy());[void]$root.ExitPoints.Add($rogue.RootChunk.ExitPoints[0].DeepCopy())
$sceneFile=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$sceneFile.RootChunk=$root
Write-Cr2wFile $sceneFile (Join-Path $source $sceneDepot)
$sr=Read-Cr2wFile (Join-Path $source $sceneDepot)
Export-Cr2wJson $sr (Join-Path $out 'scene.json')
if((J $sr.RootChunk.SceneGraph.Chunk.Graph[1].Chunk.Events[0].Chunk) -cne $stockEvent){throw 'Reset event not exact native payload'}
if($sr.RootChunk.Actors.Count -or $sr.RootChunk.PlayerActors.Count -or $sr.RootChunk.Props.Count -or $sr.RootChunk.RidResources.Count -or
 $sr.RootChunk.Workspots.Count -or $sr.RootChunk.EffectDefinitions.Count -or $sr.RootChunk.SceneGraph.Chunk.Graph.Count -ne 3){throw 'Unexpected scene dependency/action'}

$g=[WolvenKit.RED4.Types.questGraphDefinition]::new();$bg=$board.RootChunk.Graph.Chunk
function Put($n){Add-RedHandle $g.Nodes $n;return $n}
function Link($a,$s,$b,$d='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $s) (Get-QuestSocket (Get-QuestNode $g $b) $d))}
function Clone($n,$id){$c=$n.DeepCopy();$c.Id=[uint16]$id;foreach($s in $c.Sockets){$s.Chunk.Connections.Clear()};return $c}
function Fact($id,$name,$v){[void](Put (New-SetFactNode $id ('PTFRPA5O_'+$name) $v))}
$gateFacts=[ordered]@{q307_done=1;q307_finished=1;q307_active=0;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;PTFRP0_DR07=1;PTFRPA2_Started=1;PTFRPA2_Teleported=1;PTFRPA3_CoverReleased=1;PTFRPA2_ControlReady=1;PTFRPA4_CameraAligned=1;PTFRPA2_Fault=0;PTFRPA5O_Request=1;PTFRPA5O_Permit=1;PTFRPA5O_Issued=0;PTFRPA5O_NativeOut=0;PTFRPA5O_Done=0;PTFRPA5O_Fault=0}
function Guard(){
 $c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
 foreach($name in $gateFacts.Keys){Add-RedHandle $c.Conditions (New-FactCondition $name $gateFacts[$name] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))};return $c
}
function Delay($id,$ms){$n=Clone (Get-QuestNode $bg 11) $id;$t=$n.Condition.Chunk.Type.Chunk;$t.Hours=[uint32]0;$t.Minutes=[uint32]0;$t.Seconds=[uint32][Math]::Floor($ms/1000);$t.Miliseconds=[uint32]($ms%1000);[void](Put $n)}
[void](Put (New-InputNode 0 'In1'));Fact 1 Ready 1
$wait=Clone (Get-QuestNode $bg 13) 2;Set-RedHandleProperty $wait Condition (Guard);[void](Put $wait)
[void](Put (New-ConditionNode 3 (Get-QuestNode $bg 13).Condition.Chunk.DeepCopy()))
[void](Put (New-ConditionNode 4 (Guard)));Fact 5 Issued 1
$sn=[WolvenKit.RED4.Types.questSceneNodeDefinition]::new();$sn.Id=[uint16]6
$rp=[WolvenKit.RED4.Types.ResourcePath]::op_Implicit($sceneDepot)
$sn.SceneFile=[Activator]::CreateInstance($sn.GetType().GetProperty('SceneFile').PropertyType,[object[]]@($rp))
# Native no-fixed-anchor scene-location precedent: stock CPZ workers chat.
function FindUnanchored($graph){foreach($h in $graph.Nodes){$n=$h.Chunk;if($n.GetType().Name -eq 'questSceneNodeDefinition' -and $n.SceneLocation.NodeRef.ToString() -eq '0' -and $n.SceneLocation.Type.ToString() -eq 'Tag' -and $n.SceneLocation.Tag.ToString() -eq 'around_player'){return $n};if($n.GetType().Name -eq 'questPhaseNodeDefinition' -and $n.PhaseGraph -and $n.PhaseGraph.Chunk){$v=FindUnanchored $n.PhaseGraph.Chunk;if($null -ne $v){return $v}}};return $null}
$unanchored=FindUnanchored $cp.RootChunk.Graph.Chunk;if($null -eq $unanchored){throw 'Native around_player scene location missing'}
$sn.SceneLocation=$unanchored.SceneLocation.DeepCopy()
foreach($spec in @(@('CutDestination','CutDestination'),@('Start 0','Input'),@('End 0','Output'),@('Default INT','Output'),@('Default RET','Output'))){[void](New-QuestSocket $sn $spec[0] ([WolvenKit.RED4.Types.Enums+questSocketType]::$($spec[1])))}
[void](Put $sn);Fact 7 NativeOut 1
[void](Put (Clone (Get-QuestNode $bg 6) 8));[void](Put (New-OutputNode 9 'Out'))
Fact 10 Fault 2;[void](Put (Clone (Get-QuestNode $bg 6) 11));Delay 12 250
Fact 13 Fault 4;Delay 20 10000;Fact 21 Fault 1
Link 0 Out 1;Link 1 Out 2;Link 2 Out 3;Link 3 True 12;Link 12 Out 2;Link 3 False 4
Link 4 True 5;Link 4 False 13;Link 13 Out 11
Link 5 Out 6 'Start 0';Link 5 Out 20
Link 6 'End 0' 7;Link 7 Out 8;Link 8 CutSource 20 CutDestination;Link 8 Out 9
Link 6 'Default INT' 10;Link 6 'Default RET' 10;Link 10 Out 11
Link 20 Out 21;Link 21 Out 11;Link 11 CutSource 6 CutDestination;Link 11 CutSource 20 CutDestination;Link 11 Out 9
$pr=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$pr.CookingPlatform=$h10.RootChunk.CookingPlatform;Set-RedHandleProperty $pr Graph $g
$pf=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$pf.RootChunk=$pr;Write-Cr2wFile $pf (Join-Path $source $ownerDepot)
$or=Read-Cr2wFile (Join-Path $source $ownerDepot);Export-Cr2wJson $or (Join-Path $out 'owner.json')
$edges=@(Get-GraphEdges $g);$rbEdges=@(Get-GraphEdges $or.RootChunk.Graph.Chunk)
if(@(Compare-Object $edges $rbEdges).Count){throw 'Owner edge readback mismatch'}
foreach($h in $or.RootChunk.Graph.Chunk.Nodes){$n=$h.Chunk;if($n.GetType().Name -eq 'questFactsDBManagerNodeDefinition' -and !$n.Type.Chunk.FactName.ToString().StartsWith('PTFRPA5O_')){throw 'Non-owned fact writer'}}
$crc=65535;foreach($b in [Text.Encoding]::UTF8.GetBytes($ownerDepot+':1')){$x=($crc -shr 8) -bxor $b;$x=$x -bxor ($x -shr 4);$crc=(($crc -shl 8) -bxor ($x -shl 12) -bxor ($x -shl 5) -bxor $x) -band 65535}
$parent=Read-Cr2wFile (Join-Path $ws 'research/q307_extracted/raw/ep1/quest/ep1.quest')
if(@($parent.RootChunk.Graph.Chunk.Nodes|Where-Object {$_.Chunk.Id.ToString() -eq "$crc"}).Count){throw 'EP1 injection ID collision'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$archiveRel='archive/pc/mod/TowerContinued_Optics_PA5.archive';$archivePath=Join-Path $package $archiveRel
$stream=[IO.File]::Create($archivePath)
try{$writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new());if(!$writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$reader=[WolvenKit.RED4.Archive.IO.ArchiveReader]::new();$a=$null
if($reader.ReadArchive($archivePath,$hs,[ref]$a).ToString() -ne 'NoError'){throw 'Archive reopen failed'}
$depots=@($sceneDepot,$ownerDepot)|Sort-Object
if(@(Compare-Object $depots @($a.Files.Values|ForEach-Object Name|Sort-Object)).Count){throw 'Unexpected archive contents'}
foreach($e in $a.Files.Values){$memory=[IO.MemoryStream]::new();try{$e.Extract($memory);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray())) -cne (Hash (Join-Path $source $e.Name))){throw 'Packed resource SHA mismatch'}}finally{$memory.Dispose()}}
Copy-Item -LiteralPath (Join-Path $PSScriptRoot '../TowerContinued_Optics_PA5.archive.xl') -Destination ($archivePath+'.xl')
Copy-Item -LiteralPath (Join-Path $PSScriptRoot '../scripts/CameraOpticsPA5.reds') -Destination (Join-Path $package 'r6/scripts/PTFR_PreAlpha/PA5/CameraOpticsPA5.reds')
foreach($p in $sourceHashes.Keys){if((Hash $p) -cne $sourceHashes[$p]){throw 'Native input changed'}}
$files=@(Get-ChildItem -LiteralPath $package -Recurse -File|ForEach-Object {@{relative=[IO.Path]::GetRelativePath($package,$_.FullName).Replace('\','/');sha256=Hash $_.FullName;bytes=$_.Length}})
Report (Join-Path $out 'build.json') @{status='CAMERA_PA5_BUILT_NOT_LIVE';package_root=$package;package_files=$files;resources=$depots;registration_id=$crc;native_source_hashes=$sourceHashes;native_event_exact=$true;event_source='mq000_01_apartment section660 event2318495296198189056';scene_nodes=3;scene_events=1;scene_duration_ms=1500;scene_player_actors=0;owner_nodes=$g.Nodes.Count;edges=$edges;gate_facts=$gateFacts;watchdog_ms=10000;scene_location_precedent=@{resource=$cppath;node=$unanchored.Id.ToString();location=(J $unanchored.SceneLocation|ConvertFrom-Json -Depth 20)};source_changes=@('Three-node isolated reset scene with native event unchanged; remove unrelated H10 actorBehaviors and rewire only section output.','Stock around_player scene marker binding; no fixed world camera or actor acquisition.','Add owner-only acknowledgement/guard/watchdog facts.');limitations=@('Native reset execution and visual DOF improvement require playtest.','Native scene cut/output is not optical-state readback.','Admission permit is refreshed by script; save/load exactly during the short reset still needs testing.');game_save_cache_settings_writes=$false}
Write-Output ('CAMERA_BUILD_PASS='+$out)
