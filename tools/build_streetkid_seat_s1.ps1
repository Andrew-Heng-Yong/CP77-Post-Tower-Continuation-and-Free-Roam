param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly

# Development-only, one-site scene candidate. Build and audit before it is
# registered or installed. No q000 quest resource is replaced.
$kerryPath = Join-Path $WorkspaceRoot 'research\b0_general_mirrors_devices\kerry_sit_reference\raw\base\quest\side_quests\sq028\scenes\kerry_villa\sq028_kerry_villa_sit.scene'
$streetkidPath = Join-Path $WorkspaceRoot 'research\b0_general_mirrors_devices\q000_meet_fixer\raw\base\quest\main_quests\prologue\q000\scenes\q000_kid_01b_meet_your_fixer.scene'
$coyotePath = Join-Path $WorkspaceRoot 'research\b0_second_mirror\vanilla\raw\base\open_world\scenes\mirrors\mirror_scene_el_cojote.scene'
$out = Join-Path $WorkspaceRoot 'build\Streetkid_Seat_S1_Research'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$scene = Read-Cr2wFile $kerryPath
$original = Read-Cr2wFile $streetkidPath
$endSource = Read-Cr2wFile $coyotePath
$root = $scene.RootChunk
$graph = $root.SceneGraph.Chunk.Graph
function Node([int]$id) {
    $found = @($graph | Where-Object { $_.Chunk.NodeId.Id.ToString() -eq $id.ToString() })
    if ($found.Count -ne 1) { throw "Scene node $id not unique" }
    return $found[0].Chunk
}
if ($graph.Count -ne 10 -or $root.Actors.Count -ne 3 -or $root.Actors[2].ActorName.ToString() -ne 'johnny_mirror' -or
    $root.Workspots.Count -ne 1 -or $root.WorkspotInstances.Count -ne 1) {
    throw 'Small sit-scene precedent changed'
}
$root.Actors.RemoveAt(2)
foreach ($handle in $graph) {
    $node = $handle.Chunk
    if ($null -ne $node.PSObject.Properties['ActorBehaviors']) {
        $behaviors = $node.ActorBehaviors
        for ($i = $behaviors.Count - 1; $i -ge 0; $i--) {
            if ($behaviors[$i].ActorId.Id.ToString() -eq '2') { $behaviors.RemoveAt($i) }
        }
    }
}
$workspot = @($original.RootChunk.WorkspotInstances | Where-Object { $_.WorkspotInstanceId.Id.ToString() -eq '686' })
$workspotData = @($original.RootChunk.Workspots | Where-Object { $_.Chunk.DataId.Id.ToString() -eq '4044508841' })
if ($workspot.Count -ne 1 -or $workspotData.Count -ne 1 -or
    $workspot[0].OriginMarker.NodeRef.ToString() -ne '#q000_kid_01b_meet_your_fixer_bar') {
    throw 'Streetkid stool workspot precedent changed'
}
$fullMarker = '$/03_night_city/#c_heywood/glen/loc_sq022_el_coyote_cojo_bar_prefabKDIAKFA/loc_sq022_el_coyote_cojo_bar_questdesign_prefabRNA3BGI/#q000_kid_pr_coyote_cojo/#q000_kid_01b_meet_your_fixer/#q000_kid_01b_meet_your_fixer_bar'
$root.Workspots.Clear()
Add-RedHandle $root.Workspots $workspotData[0].Chunk.DeepCopy()
$root.WorkspotInstances.Clear()
$instance = $workspot[0].DeepCopy()
$instance.OriginMarker.NodeRef = [WolvenKit.RED4.Types.NodeRef]::op_Implicit($fullMarker)
$root.WorkspotInstances.Add($instance)
$sit = Node 36
if ($sit.QuestNode.Chunk.ParamsV1.Chunk.Function.ToString() -ne 'UseWorkspot') { throw 'Sit node changed' }
$sit.QuestNode.Chunk.ParamsV1.Chunk.WorkspotInstanceId.Id = [WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]686)
$sit.QuestNode.Chunk.ParamsV1.Chunk.EntryId.Id = [WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]2)

# The authored q000 instance sits 2.401 m west and 0.455 m north of the
# always-loaded bar marker. Position the Sit visualizer there, not at Kerry's.
$choice = Node 4
if ($choice.GetType().Name -ne 'scnChoiceNode' -or $choice.Options.Count -ne 1) { throw 'Sit choice changed' }
$choice.AtwParams.EntityPosition.X = [WolvenKit.RED4.Types.CFloat]::op_Implicit([float]-2.4010036)
$choice.AtwParams.EntityPosition.Y = [WolvenKit.RED4.Types.CFloat]::op_Implicit([float]0.45498991)
$choice.AtwParams.EntityPosition.Z = [WolvenKit.RED4.Types.CFloat]::op_Implicit([float]0.1)

# Do not borrow the Kerry/H10 NoPhone restriction source. The seat workspot
# itself drives posture; its Get Up section retains StopWorkspot and Tier1.
function DropDest([int]$source,[int]$target) {
    $node = Node $source
    $all = @($node.OutputSockets | ForEach-Object { $_.Destinations } | Where-Object { $_.NodeId.Id.ToString() -eq $target.ToString() })
    if ($all.Count -ne 1) { throw "Expected scene edge $source->$target" }
    foreach ($socket in $node.OutputSockets) {
        for ($i=$socket.Destinations.Count-1; $i -ge 0; $i--) {
            if ($socket.Destinations[$i].NodeId.Id.ToString() -eq $target.ToString()) { $socket.Destinations.RemoveAt($i) }
        }
    }
}
DropDest 4 1059
DropDest 33 1061
for ($i=$graph.Count-1; $i -ge 0; $i--) {
    if ($graph[$i].Chunk.NodeId.Id.ToString() -in @('1059','1061')) { $graph.RemoveAt($i) }
}
# Drop dead Johnny debug/resource metadata; no Johnny actor, asset or behavior
# should remain in this post-Tower scene.
for ($i=$root.DebugSymbols.PerformersDebugSymbols.Count-1; $i -ge 0; $i--) {
    if ($root.DebugSymbols.PerformersDebugSymbols[$i].EntityRef.DynamicEntityUniqueName.ToString() -like '*johnny*') {
        $root.DebugSymbols.PerformersDebugSymbols.RemoveAt($i)
    }
}
for ($i=$root.ResouresReferences.GameplayAnimSets.Count-1; $i -ge 0; $i--) {
    if ($root.ResouresReferences.GameplayAnimSets[$i].AsyncAnimSet.DepotPath.ToString() -like '*johnny*') {
        $root.ResouresReferences.GameplayAnimSets.RemoveAt($i)
    }
}
$endTemplate = @($endSource.RootChunk.SceneGraph.Chunk.Graph | Where-Object { $_.Chunk.GetType().Name -eq 'scnEndNode' })
if ($endTemplate.Count -ne 1 -or $root.ExitPoints.Count -ne 0) { throw 'End-node precedent changed' }
$end = $endTemplate[0].Chunk.DeepCopy()
$end.NodeId.Id = [WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]2000)
Add-RedHandle $graph $end
$endId = $endSource.RootChunk.SceneGraph.Chunk.EndNodes[0].DeepCopy()
$endId.Id = [WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]2000)
$root.SceneGraph.Chunk.EndNodes.Add($endId)
$exit = $endSource.RootChunk.ExitPoints[0].DeepCopy()
$exit.Name = [WolvenKit.RED4.Types.CName]::op_Implicit('out')
$exit.NodeId.Id = [WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]2000)
$root.ExitPoints.Add($exit)
$stand = Node 33
$back = @($stand.OutputSockets | ForEach-Object { $_.Destinations } | Where-Object { $_.NodeId.Id.ToString() -eq '4' })
if ($back.Count -ne 1) { throw 'Expected Get Up loop edge' }
$back[0].NodeId.Id = [WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]2000)
$back[0].IsockStamp.Ordinal = [WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]0)

$path = Join-Path $out 'seat.scene'
Write-Cr2wFile $scene $path
$check = Read-Cr2wFile $path
Export-Cr2wJson $check (Join-Path $out 'seat.scene.json')
if ($check.RootChunk.SceneGraph.Chunk.Graph.Count -ne 9 -or $check.RootChunk.Actors.Count -ne 2 -or
    $check.RootChunk.WorkspotInstances[0].OriginMarker.NodeRef.ToString() -ne $fullMarker -or
    $check.RootChunk.ExitPoints[0].Name.ToString() -ne 'out') {
    throw 'Seat scene round-trip validation failed'
}
Write-Output "Workspace-only seat-scene research artifact: $path"

# Package the tested one-shot scene behind a mod-owned opt-in fact. CET is
# development control only; no q000 resource or original quest fact is written.
$sourceRoot = Join-Path $WorkspaceRoot 'archive\b0_streetkid_seat_s1\source'
$buildRoot = Join-Path $WorkspaceRoot 'build\Streetkid_Seat_S1'
$auditRoot = Join-Path $WorkspaceRoot 'research\b0_streetkid_seat_s1'
$gateDepot = 'towercontinued\streetkid_seat_s1\gate.questphase'
$ownerDepot = 'towercontinued\streetkid_seat_s1\owner.questphase'
$sceneDepot = 'towercontinued\streetkid_seat_s1\seat.scene'
$archiveName = 'TowerContinued_Streetkid_Seat_S1.archive'
New-Item -ItemType Directory -Force -Path $sourceRoot,$buildRoot,$auditRoot | Out-Null
Write-Cr2wFile $scene (Join-Path $sourceRoot $sceneDepot)

$basePhase = Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase')
$ep1 = Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\ep1.quest')
$coyotePhase = Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\b0_mirror_investigation\extracted\raw\base\open_world\scenes\mirrors\mirror_interactions_control.questphase')
$coyoteLeaf = (Get-QuestNode ((Get-QuestNode $coyotePhase.RootChunk.Graph.Chunk 42).PhaseGraph.Chunk) 48).PhaseGraph.Chunk
$sceneTemplate = (Get-QuestNode $coyoteLeaf 2)
$pauseTemplate = (Get-QuestNode $basePhase.RootChunk.Graph.Chunk 106)
if ($sceneTemplate.GetType().Name -ne 'questSceneNodeDefinition') { throw 'Scene-node precedent changed' }
function Put($graph,$node) { Add-RedHandle $graph.Nodes $node }
function Link($graph,$from,$socket,$to,$dest='In') {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $from) $socket) (Get-QuestSocket (Get-QuestNode $graph $to) $dest))
}
function Pause($id,$condition) {
    $node = $pauseTemplate.DeepCopy(); $node.Id = [uint16]$id
    foreach ($socket in $node.Sockets) { $socket.Chunk.Connections.Clear() }
    Set-RedHandleProperty $node Condition $condition
    return $node
}
function FactGuard() {
    $condition = [WolvenKit.RED4.Types.questLogicalCondition]::new()
    $condition.Operation = [WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
    $facts = [ordered]@{
        PostTowerFreeRoamActive=1; PTFRP0_DR13=1; q307_active=0; q307_done=1
        q307_finished=1; q307_2079=1; q305_johnny_scene_active=0
        q000_done=1; PTFRSKS1_Enabled=1; PTFRSKS1_Interrupted=0
    }
    foreach ($name in $facts.Keys) {
        Add-RedHandle $condition.Conditions (New-FactCondition $name $facts[$name] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
    }
    return $condition
}
function PhaseFile($graph) {
    $phase = [WolvenKit.RED4.Types.questQuestPhaseResource]::new()
    $phase.CookingPlatform = [WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
    Set-RedHandleProperty $phase Graph $graph
    $file = [WolvenKit.RED4.Archive.CR2W.CR2WFile]::new()
    $file.RootChunk = $phase
    return $file
}
function Count($id,$name) {
    $node = New-SetFactNode $id ('PTFRSKS1_'+$name) 1
    $node.Type.Chunk.SetExactValue = $false
    return $node
}
$gateGraph = [WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $gateGraph (New-InputNode 0 'In1')
Put $gateGraph (Count 1 'Boot')
Put $gateGraph (Pause 2 (FactGuard))
Put $gateGraph (New-SetFactNode 3 'PTFRSKS1_Ready' 1)
$child = [WolvenKit.RED4.Types.questPhaseNodeDefinition]::new(); $child.Id = [uint16]4
$childPath = [WolvenKit.RED4.Types.ResourcePath]::op_Implicit($ownerDepot)
$child.PhaseResource = [Activator]::CreateInstance($child.GetType().GetProperty('PhaseResource').PropertyType,[object[]]@($childPath))
[void](New-QuestSocket $child 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
[void](New-QuestSocket $child 'In1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
Put $gateGraph $child
Link $gateGraph 0 Out 1; Link $gateGraph 1 Out 2; Link $gateGraph 2 Out 3; Link $gateGraph 3 Out 4 In1
$gateFile = PhaseFile $gateGraph

$ownerGraph = [WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $ownerGraph (New-InputNode 0 'In1')
Put $ownerGraph (Count 1 'SceneRequests')
Put $ownerGraph (New-SetFactNode 2 'PTFRSKS1_Active' 1)
$sceneNode = $sceneTemplate.DeepCopy(); $sceneNode.Id = [uint16]3
foreach ($socket in $sceneNode.Sockets) { $socket.Chunk.Connections.Clear() }
$scenePath = [WolvenKit.RED4.Types.ResourcePath]::op_Implicit($sceneDepot)
$sceneNode.SceneFile = [Activator]::CreateInstance($sceneNode.GetType().GetProperty('SceneFile').PropertyType,[object[]]@($scenePath))
$sceneNode.SceneLocation.NodeRef = [WolvenKit.RED4.Types.NodeRef]::op_Implicit($fullMarker)
foreach ($socket in $sceneNode.Sockets) {
    if ($socket.Chunk.Name.ToString() -eq 'mirror_interaction') { $socket.Chunk.Name = [WolvenKit.RED4.Types.CName]::op_Implicit('in') }
    if ($socket.Chunk.Name.ToString() -eq 'mirror_interaction_out') { $socket.Chunk.Name = [WolvenKit.RED4.Types.CName]::op_Implicit('out') }
}
Put $ownerGraph $sceneNode
Put $ownerGraph (New-SetFactNode 4 'PTFRSKS1_Active' 0)
Put $ownerGraph (Count 5 'SceneReturns')
Put $ownerGraph (New-SetFactNode 6 'PTFRSKS1_Completed' 1)
Put $ownerGraph (New-SetFactNode 7 'PTFRSKS1_Interrupted' 1)
Put $ownerGraph (New-SetFactNode 8 'PTFRSKS1_Active' 0)
Link $ownerGraph 0 Out 1; Link $ownerGraph 1 Out 2; Link $ownerGraph 2 Out 3 in
Link $ownerGraph 3 out 4; Link $ownerGraph 4 Out 5; Link $ownerGraph 5 Out 6
Link $ownerGraph 3 'Default INT' 7; Link $ownerGraph 7 Out 8
$ownerFile = PhaseFile $ownerGraph
Write-Cr2wFile $gateFile (Join-Path $sourceRoot $gateDepot)
Write-Cr2wFile $ownerFile (Join-Path $sourceRoot $ownerDepot)
foreach ($item in @(@{name='gate';depot=$gateDepot;nodes=5},@{name='owner';depot=$ownerDepot;nodes=9})) {
    $file = Read-Cr2wFile (Join-Path $sourceRoot $item.depot)
    Export-Cr2wJson $file (Join-Path $auditRoot ($item.name+'.json'))
    if ($file.RootChunk.Graph.Chunk.Nodes.Count -ne $item.nodes -or $file.RootChunk.PhasePrefabs.Count -ne 0) { throw 'Quest graph round-trip changed' }
    foreach ($handle in $file.RootChunk.Graph.Chunk.Nodes) {
        $node = $handle.Chunk
        if ($node.GetType().Name -eq 'questFactsDBManagerNodeDefinition' -and
            -not $node.Type.Chunk.FactName.ToString().StartsWith('PTFRSKS1_')) { throw 'Non-probe fact writer' }
    }
}
$expected = @($gateDepot,$ownerDepot,$sceneDepot) | Sort-Object
$actual = @(Get-ChildItem -LiteralPath $sourceRoot -Recurse -File | ForEach-Object {[IO.Path]::GetRelativePath($sourceRoot,$_.FullName)} | Sort-Object)
if (@(Compare-Object $expected $actual).Count) { throw 'Unexpected source resources' }
$hashService = [WolvenKit.Common.Services.HashService]::new(); $hashService.Load()
$archivePath = Join-Path $buildRoot $archiveName
$stream = [IO.File]::Create($archivePath)
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService,[WolvenKit.SerilogWrapper]::new())
    if (-not $writer.WriteArchive([IO.DirectoryInfo]::new($sourceRoot),$stream)) { throw 'Archive write failed' }
} finally { $stream.Dispose() }
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new(); $archive = $null
if ($reader.ReadArchive($archivePath,$hashService,[ref]$archive).ToString() -ne 'NoError') { throw 'Archive reopen failed' }
$packed = @($archive.Files.Values | ForEach-Object {$_.Name} | Sort-Object)
if (@(Compare-Object $expected $packed).Count) { throw 'Archive manifest mismatch' }
$crc = 65535
foreach ($byte in [Text.Encoding]::UTF8.GetBytes($gateDepot+':1')) {
    $x = ($crc -shr 8) -bxor $byte; $x = $x -bxor ($x -shr 4)
    $crc = (($crc -shl 8) -bxor ($x -shl 12) -bxor ($x -shl 5) -bxor $x) -band 65535
}
if (@($ep1.RootChunk.Graph.Chunk.Nodes | Where-Object {$_.Chunk.Id.ToString() -eq "$crc"}).Count) { throw 'EP1 registration collision' }
$xlSource = Join-Path $WorkspaceRoot ('archive\b0_streetkid_seat_s1\'+$archiveName+'.xl')
$xlBuild = $archivePath+'.xl'
Copy-Item -LiteralPath $xlSource -Destination $xlBuild -Force
$manifest = [ordered]@{
    status='WORKSPACE_ONLY_UNINSTALLED'; archive=$archiveName; sha256=(Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
    xl_sha256=(Get-FileHash -LiteralPath $xlBuild -Algorithm SHA256).Hash
    resources=$packed; registration_id=$crc; marker=$fullMarker
    vanilla_replacements=@(); story_fact_writes=@(); opt_in_fact='PTFRSKS1_Enabled'
    first_test='one Sit/Get Up only; mirror action excluded until seat passes'
}
[IO.File]::WriteAllText((Join-Path $auditRoot 'build_manifest.json'),($manifest | ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
$manifest | ConvertTo-Json -Depth 6
