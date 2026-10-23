param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0',
    [switch]$PrepareActionTest
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly
. (Join-Path $PSScriptRoot 'streetkid_scene_identity.ps1')
. (Join-Path $PSScriptRoot 'streetkid_actions_revision3.ps1')
. (Join-Path $PSScriptRoot 'streetkid_presentation_revision4.ps1')
if($PrepareActionTest) {
    $live=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_streetkid_scene_load_s3\live_revision2_result.json') -Raw|ConvertFrom-Json
    if($live.status -ne 'PASS_S3_REVISION2' -or -not $live.required_facts_unchanged -or
       $live.markers.SceneRequests -ne 1 -or $live.markers.SceneReturns -ne 1) { throw 'Corrected S3 live acquisition pass required' }
}

# One-shot, opt-in Streetkid stool + original fix-nose animation. The q000
# story scene is only a source for V-only events and its stool workspots.
# The existing S1 archive is left untouched as rollback.
$s1 = Join-Path $WorkspaceRoot 'archive\b0_streetkid_seat_s1\source'
$source = Join-Path $WorkspaceRoot 'archive\b0_streetkid_seat_mirror_s2\source'
$build = Join-Path $WorkspaceRoot 'build\Streetkid_Seat_Mirror_S2'
$audit = Join-Path $WorkspaceRoot 'research\b0_streetkid_seat_mirror_s2'
$oldDepot = 'towercontinued\streetkid_seat_s1'
$newDepot = 'towercontinued\streetkid_seat_mirror_s2'
$sceneDepot = "$newDepot\seat_mirror.scene"
$gateDepot = "$newDepot\gate.questphase"
$ownerDepot = "$newDepot\owner.questphase"
$archiveName = 'TowerContinued_Streetkid_Seat_Mirror_S2.archive'
$marker = '$/03_night_city/#c_heywood/glen/loc_sq022_el_coyote_cojo_bar_prefabKDIAKFA/loc_sq022_el_coyote_cojo_bar_questdesign_prefabRNA3BGI/#q000_kid_pr_coyote_cojo/#q000_kid_01b_meet_your_fixer/#q000_kid_01b_meet_your_fixer_bar'
New-Item -ItemType Directory -Force -Path $source,$build,$audit | Out-Null
$scene = Read-Cr2wFile (Join-Path $s1 "$oldDepot\seat.scene")
$q000 = Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\b0_general_mirrors_devices\q000_meet_fixer\raw\base\quest\main_quests\prologue\q000\scenes\q000_kid_01b_meet_your_fixer.scene')
$root = $scene.RootChunk
$graph = $root.SceneGraph.Chunk.Graph
$qroot = $q000.RootChunk
$qgraph = $qroot.SceneGraph.Chunk.Graph
function Find-SceneNode($g,[int]$id) {
    $found=@($g | Where-Object {$_.Chunk.NodeId.Id.ToString() -eq $id.ToString()})
    if ($found.Count -ne 1) { throw "Scene node $id not unique" }
    return $found[0].Chunk
}
function Set-SceneDest($socket,[int]$id) {
    if ($socket.Destinations.Count -ne 1) { throw "Expected one scene destination to $id" }
    $socket.Destinations[0].NodeId.Id = [WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]$id)
}
function Set-SceneTime($value,[int]$stu) { $value.Stu = [WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]$stu) }
if ($graph.Count -ne 9 -or $root.WorkspotInstances.Count -ne 1 -or
    $root.WorkspotInstances[0].WorkspotInstanceId.Id.ToString() -ne '686') {
    throw 'S1 seat foundation changed'
}

# The S1 precedent used Kerry's chair Sit animation. It was never armed and
# would be wrong for this barstool. Drive the q000 stool workspot directly.
$sit = Find-SceneNode $graph 8
$sit.Events.Clear()
$sitSource=Find-SceneNode (Read-Cr2wFile (Join-Path $s1 "$oldDepot\seat.scene")).RootChunk.SceneGraph.Chunk.Graph 8
$sitEvent = $sitSource.Events[2].Chunk.DeepCopy()
if ($sitEvent.GetType().Name -ne 'scneventsSocket') { throw 'S1 sit socket precedent changed' }
$sitEvent.StartTime = [WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]0)
$sitEvent.OsockStamp.Name = [WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]2)
$sitEvent.OsockStamp.Ordinal = [WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]0)
Add-RedHandle $sit.Events $sitEvent
Set-SceneTime $sit.SectionDuration 3000

# Preserve the original authored transition to the lean0/fix-nose pose.
# Its first three events are V FPP, male TPP, and female TPP only.
$qfix = Find-SceneNode $qgraph 197
$fix = $sit.DeepCopy()
$fix.NodeId.Id = [WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]2010)
$fix.Events.Clear()
foreach ($socket in $fix.OutputSockets) { $socket.Destinations.Clear() }
Set-SceneTime $fix.SectionDuration 9500
foreach ($index in 0,1,2,19,20,21) {
    $event=$qfix.Events[$index].Chunk.DeepCopy()
    if ($index -lt 3) {
        $old=[int]$event.Performer.Id.ToString()
        $new=switch ($old) {1281 {769} 769 {1} 1025 {257} default {throw 'Unexpected Q000 V performer'}}
        $event.Performer.Id = [WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]$new)
        $event.RootMotionData.OriginMarker.NodeRef = [WolvenKit.RED4.Types.NodeRef]::op_Implicit($marker)
        if ($event.PoseBlendOutWorkspot -and $event.PoseBlendOutWorkspot.Chunk) {
            $wsid=[int]$event.PoseBlendOutWorkspot.Chunk.WorkspotId.Id.ToString()
            if ($wsid -notin 664,1697,1699) { throw 'Unexpected fix-nose workspot' }
        }
    }
    Add-RedHandle $fix.Events $event
}
$fix.OutputSockets[0].Destinations.Add($sit.OutputSockets[0].Destinations[0].DeepCopy())
Set-SceneDest $fix.OutputSockets[0] 33
foreach ($name in 3,7,8) {
    $s=@($qfix.OutputSockets | Where-Object {$_.Stamp.Name.ToString() -eq $name.ToString()})
    if ($s.Count -ne 1) { throw "Fix-nose workspot socket $name changed" }
    $fix.OutputSockets.Add($s[0].DeepCopy())
}
Add-RedHandle $graph $fix

# Q000 changes the workspot at the end of the nose animation. These are the
# three V-only workspot targets, not bartender or quest progression nodes.
foreach ($id in 664,1697,1699) {
    $node=(Find-SceneNode $qgraph $id).DeepCopy()
    if ($node.GetType().Name -ne 'scnQuestNode' -or
        $node.QuestNode.Chunk.ParamsV1.Chunk.Function.ToString() -ne 'UseWorkspot') { throw 'Q000 workspot node changed' }
    if ($id -eq 1697) { $node.QuestNode.Chunk.EntityReference.DynamicEntityUniqueName=[WolvenKit.RED4.Types.CName]::op_Implicit('a_sq028_kerry_villa_sit_v_female_tpp') }
    if ($id -eq 1699) { $node.QuestNode.Chunk.EntityReference.DynamicEntityUniqueName=[WolvenKit.RED4.Types.CName]::op_Implicit('a_sq028_kerry_villa_sit_v_male_tpp') }
    Add-RedHandle $graph $node
    $instance=@($qroot.WorkspotInstances | Where-Object {$_.WorkspotInstanceId.Id.ToString() -eq $id.ToString()})
    if ($instance.Count -ne 1) { throw "Q000 workspot instance $id changed" }
    $copy=$instance[0].DeepCopy()
    $copy.OriginMarker.NodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($marker)
    $root.WorkspotInstances.Add($copy)
    $dataId=$copy.DataId.Id.ToString()
    if (-not @($root.Workspots | Where-Object {$_.Chunk.DataId.Id.ToString() -eq $dataId}).Count) {
        $data=@($qroot.Workspots | Where-Object {$_.Chunk.DataId.Id.ToString() -eq $dataId})
        if ($data.Count -ne 1) { throw "Q000 workspot data $dataId changed" }
        Add-RedHandle $root.Workspots $data[0].Chunk.DeepCopy()
    }
}

# After the action, use Q000's V-only barstool stand animations and Kerry's
# proven StopWorkspot/Tier1 cleanup sockets. No Q000 dialogue or fact nodes.
$qstand=Find-SceneNode $qgraph 404
$stand=Find-SceneNode $graph 33
$stand.Events.Clear()
foreach ($index in 1,4,7) {
    $event=$qstand.Events[$index].Chunk.DeepCopy()
    if ($event.GetType().Name -ne 'scnPlaySkAnimEvent') { throw 'Q000 stand animation changed' }
    $old=[int]$event.Performer.Id.ToString()
    $new=switch ($old) {1281 {769} 769 {1} 1025 {257} default {throw 'Unexpected stand performer'}}
    $event.Performer.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]$new)
    $event.RootMotionData.OriginMarker.NodeRef = [WolvenKit.RED4.Types.NodeRef]::op_Implicit($marker)
    Add-RedHandle $stand.Events $event
}
foreach ($index in 4,5,6,7,8) {
    $sourceStand=Find-SceneNode (Read-Cr2wFile (Join-Path $s1 "$oldDepot\seat.scene")).RootChunk.SceneGraph.Chunk.Graph 33
    $event=$sourceStand.Events[$index].Chunk.DeepCopy()
    $event.StartTime=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]4533)
    Add-RedHandle $stand.Events $event
}
Set-SceneTime $stand.SectionDuration 4550
$sitChoice=Find-SceneNode $graph 10
if ($sitChoice.Options.Count -ne 1 -or $sitChoice.OutputSockets[0].Destinations.Count -ne 1) { throw 'Seated choice changed' }
$qChoice=Find-SceneNode $qgraph 396
if ($qChoice.Options[0].Caption.ToString() -ne 'fix_nose') { throw 'Fix-nose choice changed' }
$sitChoice.Options.Clear()
$sitChoice.Options.Add($qChoice.Options[0].DeepCopy())
Set-SceneDest $sitChoice.OutputSockets[0] 2010
$screenplay=@($qroot.ScreenplayStore.Options | Where-Object {$_.ItemId.Id.ToString() -eq '3842'})
if ($screenplay.Count -ne 1) { throw 'Fix-nose localized caption changed' }
$root.ScreenplayStore.Options.Add($screenplay[0].DeepCopy())
# The borrowed Kerry dialogue and Get Up label are unreachable in this
# one-shot route; keep only the Sit and original Q000 fix-nose captions.
$root.ScreenplayStore.Lines.Clear()
for ($i=$root.ScreenplayStore.Options.Count-1; $i -ge 0; $i--) {
    if ($root.ScreenplayStore.Options[$i].ItemId.Id.ToString() -eq '258') {
        $root.ScreenplayStore.Options.RemoveAt($i)
    }
}

# Repair the complete scene acquisition contract, not merely graph edges.
# Bind only the original V animation assets; the assets contain animation
# data, not executable Q000 quest/scene paths. All actor-specific indices are
# rebuilt against the new table, and unused props/lipsync are not acquired.
$refs=[Activator]::CreateInstance($root.ResouresReferences.GetType())
$cineMap=@{}
foreach ($oldIndex in 0,1,5,6,17,18,19,20) {
    $cineMap[$oldIndex]=$refs.CinematicAnimSets.Count
    $refs.CinematicAnimSets.Add($qroot.ResouresReferences.CinematicAnimSets[$oldIndex].DeepCopy())
    $refs.CinematicAnimNames.Add($qroot.ResouresReferences.CinematicAnimNames[$oldIndex].DeepCopy())
}
# Stand cleanup references gameplayAnimName fpp_idle_stand. Preserve both
# original sex-specific scene-level pairs as authored in Q000 (also Kerry).
foreach($oldIndex in 4,5) {
    $refs.GameplayAnimSets.Add($qroot.ResouresReferences.GameplayAnimSets[$oldIndex].DeepCopy())
    $refs.GameplayAnimNames.Add($qroot.ResouresReferences.GameplayAnimNames[$oldIndex].DeepCopy())
}
$root.ResouresReferences=$refs
$root.Actors.Clear()
foreach ($spec in @(@{name='v_male_tpp';id=0;unique='a_PTFRSKS2_v_male_tpp'},@{name='v_female_tpp';id=1;unique='a_PTFRSKS2_v_female_tpp'})) {
    $found=@($qroot.Actors | Where-Object {$_.ActorName.ToString() -eq $spec.name})
    if ($found.Count -ne 1) { throw "Q000 V actor changed: $($spec.name)" }
    $actor=$found[0].DeepCopy()
    $actor.ActorId.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]$spec.id)
    $actor.SpawnDespawnParams.DynamicEntityUniqueName=[WolvenKit.RED4.Types.CName]::op_Implicit($spec.unique)
    # This exact marker is present in the always-loaded El Coyote sector.
    $actor.SpawnDespawnParams.SpawnMarkerNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($marker.Replace('#q000_kid_01b_meet_your_fixer_bar','#q000_kid_player_tpp'))
    foreach ($binding in $actor.BodyCinematicAnimSets) {
        $oldIndex=[int]$binding.Id.ToString()
        if (-not $cineMap.ContainsKey($oldIndex)) { throw "Unmapped V animation index $oldIndex" }
        $binding.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]$cineMap[$oldIndex])
    }
    $actor.LipsyncAnimSet.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]::MaxValue)
    $root.Actors.Add($actor)
}
if ($qroot.PlayerActors.Count -ne 1) { throw 'Q000 player definition changed' }
$player=$qroot.PlayerActors[0].DeepCopy()
$player.ActorId.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]3)
foreach ($binding in $player.BodyCinematicAnimSets) {
    $oldIndex=[int]$binding.Id.ToString()
    if (-not $cineMap.ContainsKey($oldIndex)) { throw "Unmapped player animation index $oldIndex" }
    $binding.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]$cineMap[$oldIndex])
}
# Retain the original player's valid V-only lipsync dependency. A player
# sentinel was not a vanilla precedent; no dialogue event is introduced.
$playerLip=[int]$qroot.PlayerActors[0].LipsyncAnimSet.Id.ToString()
$root.ResouresReferences.LipsyncAnimSets.Add($qroot.ResouresReferences.LipsyncAnimSets[$playerLip].DeepCopy())
$player.LipsyncAnimSet.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]0)
$root.PlayerActors.Clear(); $root.PlayerActors.Add($player)
(Find-SceneNode $graph 1697).QuestNode.Chunk.EntityReference.DynamicEntityUniqueName=[WolvenKit.RED4.Types.CName]::op_Implicit('a_PTFRSKS2_v_female_tpp')
(Find-SceneNode $graph 1699).QuestNode.Chunk.EntityReference.DynamicEntityUniqueName=[WolvenKit.RED4.Types.CName]::op_Implicit('a_PTFRSKS2_v_male_tpp')
for ($i=$root.DebugSymbols.PerformersDebugSymbols.Count-1; $i -ge 0; $i--) {
    $symbol=$root.DebugSymbols.PerformersDebugSymbols[$i]
    switch ($symbol.PerformerId.Id.ToString()) {
        '1' {$symbol.EntityRef.DynamicEntityUniqueName=[WolvenKit.RED4.Types.CName]::op_Implicit('a_PTFRSKS2_v_male_tpp')}
        '257' {$symbol.EntityRef.DynamicEntityUniqueName=[WolvenKit.RED4.Types.CName]::op_Implicit('a_PTFRSKS2_v_female_tpp')}
        '769' { }
        default {$root.DebugSymbols.PerformersDebugSymbols.RemoveAt($i)}
    }
}
$root.Props.Clear()
$root.NotablePoints.Clear()
# This inherited speaker-distance scenario assumes dialogue speakers that
# this optional one-shot does not contain. Do not carry it into the probe.
$root.InterruptionScenarios.Clear()

# Screenplay option IDs are local to a scene; copying just a RUID is not
# enough. Rebuild descriptor/payload tables for the two actual captions.
$oldLoc=$root.LocStore.DeepCopy()
$root.LocStore.VdEntries.Clear(); $root.LocStore.VpEntries.Clear()
foreach ($choiceLoc in @(@{store=$oldLoc;ruid='2028697799592157188'},@{store=$qroot.LocStore;ruid='1902575182399250436'})) {
    $descriptors=@($choiceLoc.store.VdEntries | Where-Object {$_.LocstringId.Ruid.ToString() -eq $choiceLoc.ruid})
    if (-not $descriptors.Count) { throw "Missing caption localization $($choiceLoc.ruid)" }
    foreach ($descriptor in $descriptors) {
        $oldIndex=[int]$descriptor.VpeIndex.ToString()
        $payload=$choiceLoc.store.VpEntries[$oldIndex]
        if ($payload.VariantId.Ruid.ToString() -ne $descriptor.VariantId.Ruid.ToString()) { throw 'Caption payload index mismatch' }
        $copy=$descriptor.DeepCopy()
        $copy.VpeIndex=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]$root.LocStore.VpEntries.Count)
        $root.LocStore.VpEntries.Add($payload.DeepCopy())
        $root.LocStore.VdEntries.Add($copy)
    }
}
# The original Kerry template had Johnny actor2, removed by S1. Native player
# lookup indexes (actorId - Actors.Count); leaving V at3 with 2 actors causes
# an out-of-bounds player slot and read0x34. Remap typed identities everywhere.
$root.DebugSymbols=[Activator]::CreateInstance($root.DebugSymbols.GetType())
$identityRepair=Repair-StreetkidSceneIdentity $scene
$scene=$identityRepair.File
$root=$scene.RootChunk
$graph=$root.SceneGraph.Chunk.Graph
Add-StreetkidRevision3Actions $scene $qroot $marker
Add-StreetkidRevision4Presentation $scene $qroot $marker $WorkspaceRoot
Write-Cr2wFile $scene (Join-Path $source $sceneDepot)

# Copy the native S1 guard and scene ownership but give S2 distinct resources
# and probe facts. Both opt-ins default off; never enable them together.
$gate=Read-Cr2wFile (Join-Path $s1 "$oldDepot\gate.questphase")
$owner=Read-Cr2wFile (Join-Path $s1 "$oldDepot\owner.questphase")
foreach ($file in $gate,$owner) {
    foreach ($handle in $file.RootChunk.Graph.Chunk.Nodes) {
        $node=$handle.Chunk
        if ($node.GetType().Name -eq 'questFactsDBManagerNodeDefinition') {
            $fact=$node.Type.Chunk.FactName.ToString()
            if (-not $fact.StartsWith('PTFRSKS1_')) { throw "Unexpected writer $fact" }
            $node.Type.Chunk.FactName=[WolvenKit.RED4.Types.CString]::op_Implicit($fact.Replace('PTFRSKS1_','PTFRSKS2_'))
        }
        if ($node.GetType().Name -eq 'questPauseConditionNodeDefinition') {
            foreach ($condition in $node.Condition.Chunk.Conditions) {
                $fact=$condition.Chunk.Type.Chunk.FactName.ToString()
                if ($fact.StartsWith('PTFRSKS1_')) {
                    $condition.Chunk.Type.Chunk.FactName=[WolvenKit.RED4.Types.CString]::op_Implicit($fact.Replace('PTFRSKS1_','PTFRSKS2_'))
                }
            }
        }
        if ($node.GetType().Name -eq 'questPhaseNodeDefinition') {
            $path=[WolvenKit.RED4.Types.ResourcePath]::op_Implicit($ownerDepot)
            $node.PhaseResource=[Activator]::CreateInstance($node.GetType().GetProperty('PhaseResource').PropertyType,[object[]]@($path))
        }
        if ($node.GetType().Name -eq 'questSceneNodeDefinition') {
            $path=[WolvenKit.RED4.Types.ResourcePath]::op_Implicit($sceneDepot)
            $node.SceneFile=[Activator]::CreateInstance($node.GetType().GetProperty('SceneFile').PropertyType,[object[]]@($path))
        }
    }
}
$nativeGuard=(Get-QuestNode $gate.RootChunk.Graph.Chunk 2).Condition.Chunk
if ($nativeGuard.GetType().Name -ne 'questLogicalCondition') { throw 'S2 native guard changed' }
Add-RedHandle $nativeGuard.Conditions (New-FactCondition 'PTFRSKS1_Enabled' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
Add-RedHandle $nativeGuard.Conditions (New-FactCondition 'PTFRSKS3_Enabled' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
Add-RedHandle $nativeGuard.Conditions (New-FactCondition 'PTFRSKS3_Active' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
$gateGraph=$gate.RootChunk.Graph.Chunk
$revision=New-SetFactNode 9 'PTFRSKS2_Revision' 4
Add-RedHandle $gateGraph.Nodes $revision
$input=Get-QuestSocket (Get-QuestNode $gateGraph 0) 'Out'
$boot=Get-QuestSocket (Get-QuestNode $gateGraph 1) 'In'
$input.Connections.Clear();$boot.Connections.Clear()
[void](Connect-QuestSockets $input (Get-QuestSocket $revision 'In'))
[void](Connect-QuestSockets (Get-QuestSocket $revision 'Out') $boot)
Write-Cr2wFile $gate (Join-Path $source $gateDepot)
Add-StreetkidMirrorOwnerCleanup $owner $qgraph
Write-Cr2wFile $owner (Join-Path $source $ownerDepot)
foreach ($item in @(@{name='scene';depot=$sceneDepot},@{name='gate';depot=$gateDepot},@{name='owner';depot=$ownerDepot})) {
    $file=Read-Cr2wFile (Join-Path $source $item.depot)
    Export-Cr2wJson $file (Join-Path $audit ($item.name+'.json'))
}
$sceneCheck=Read-Cr2wFile (Join-Path $source $sceneDepot)
# The first live S2 activation crashed. The original validator covered the
# route, not the scene resource acquisition contract. Fail closed until the
# transplant's paired resource tables and unrelated props are repaired.
if ($sceneCheck.RootChunk.ResouresReferences.GameplayAnimNames.Count -ne
    $sceneCheck.RootChunk.ResouresReferences.GameplayAnimSets.Count -or
    $sceneCheck.RootChunk.Props.Count -ne 1) {
    throw 'Rejected S2 scene resource contract: paired animation tables or unrelated acquired props are invalid. Do not install.'
}
$ids=@($sceneCheck.RootChunk.SceneGraph.Chunk.Graph | ForEach-Object {[int]$_.Chunk.NodeId.Id.ToString()})
if ($ids.Count -ne 28 -or @($ids | Sort-Object -Unique).Count -ne 28 -or
    $sceneCheck.RootChunk.WorkspotInstances.Count -ne 7 -or $sceneCheck.RootChunk.ExitPoints.Count -ne 1) {
    throw 'S2 scene round-trip or graph count changed'
}
$expected=@($sceneDepot,$gateDepot,$ownerDepot)|Sort-Object
$actual=@(Get-ChildItem -LiteralPath $source -Recurse -File | ForEach-Object {[IO.Path]::GetRelativePath($source,$_.FullName)} | Sort-Object)
if (@(Compare-Object $expected $actual).Count) { throw 'Unexpected S2 resource' }
$hashService=[WolvenKit.Common.Services.HashService]::new(); $hashService.Load()
$archivePath=Join-Path $build $archiveName
$stream=[IO.File]::Create($archivePath)
try {
    $writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService,[WolvenKit.SerilogWrapper]::new())
    if (-not $writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)) { throw 'Archive write failed' }
} finally { $stream.Dispose() }
$reader=[WolvenKit.RED4.Archive.IO.ArchiveReader]::new(); $archive=$null
if ($reader.ReadArchive($archivePath,$hashService,[ref]$archive).ToString() -ne 'NoError') { throw 'Archive reopen failed' }
$packed=@($archive.Files.Values | ForEach-Object {$_.Name}|Sort-Object)
if (@(Compare-Object $expected $packed).Count) { throw 'Archive manifest mismatch' }
$ep1=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\ep1.quest')
$crc=65535
foreach ($byte in [Text.Encoding]::UTF8.GetBytes($gateDepot+':1')) {
    $x=($crc -shr 8) -bxor $byte; $x=$x -bxor ($x -shr 4)
    $crc=(($crc -shl 8) -bxor ($x -shl 12) -bxor ($x -shl 5) -bxor $x) -band 65535
}
if (@($ep1.RootChunk.Graph.Chunk.Nodes | Where-Object {$_.Chunk.Id.ToString() -eq "$crc"}).Count -ne 0 -or $crc -eq 11985) {
    throw "EP1 or S1 registration collision: $crc"
}
$xlSource=Join-Path $WorkspaceRoot "archive\b0_streetkid_seat_mirror_s2\$archiveName.xl"
Copy-Item -LiteralPath $xlSource -Destination ($archivePath+'.xl') -Force
$manifest=[ordered]@{
    status=$(if($PrepareActionTest){'ACTION_TEST_BUILT_AFTER_S3_PASS'}else{'WORKSPACE_REPAIR_UNVALIDATED_NOT_FOR_INSTALL'}); archive=$archiveName
    sha256=(Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
    xl_sha256=(Get-FileHash -LiteralPath ($archivePath+'.xl') -Algorithm SHA256).Hash
    resources=$packed; vanilla_replacements=@(); story_fact_writes=@()
    opt_in_fact='PTFRSKS2_Enabled'; registration_id=$crc; S1_rollback_preserved=$true
    revision=4; repaired_metadata=$true; scene_load_probe_required=(-not $PrepareActionTest); action_install_authorized=[bool]$PrepareActionTest
    presentation_repair=@('body-type branch','scene body Activate/spawn wait/workspot','public mirror default appearance','normal Deactivate','bar-relative pickup transform')
    staged_choices=@('Sit','Fix nose / Drink','Get up'); mirror_cleanup=@('normal','interrupted'); scene_owned_props=@('Props.q000_vodka_shot')
    dense_actor_ids=@(0,1,2); crash_actor_index_fixed=$true
    original_q000_components=@('stool workspots 686/664/1697/1699','fix_nose player events 0/1/2','fix_nose workspot sockets 19/20/21','stand player events 1/4/7')
}
[IO.File]::WriteAllText((Join-Path $audit 'build_manifest.json'),($manifest|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
$manifest|ConvertTo-Json -Depth 6
