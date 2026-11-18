# Build a private repeatable Sit/Get Up scene at the original rooftop seat.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$work = Join-Path $PSScriptRoot 'work'
$out = Join-Path $work 'scene_01'
if (Test-Path -LiteralPath $out) { throw 'Fresh rooftop scene output required' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly `
    -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
. (Join-Path $workspace 'tools/streetkid_scene_identity.ps1')

$captured = Get-Content -LiteralPath (Join-Path $work 'native_01/providers.json') -Raw | ConvertFrom-Json
$support = Get-Content -LiteralPath (Join-Path $work 'support_02/providers.json') -Raw | ConvertFrom-Json
$baseline = 'B738804793E5E669D71F72E9FB7755B2786D2B25E3B0A212681F10427C9EF5C0'
if ($captured.manifest_sha256 -cne $baseline -or $support.manifest_sha256 -cne $baseline) { throw 'Capture baseline changed' }

function Captured($index, [string]$depot, [string]$provider = '') {
    $hit = @($index.hits | Where-Object { $_.depot -ceq $depot -and (!$provider -or (Split-Path $_.archive -Leaf) -ceq $provider) })
    if ($hit.Count -ne 1 -or (Get-FileHash -LiteralPath $hit[0].raw).Hash -cne $hit[0].sha256) { throw "Unverified input $depot" }
    return $hit[0]
}

$roofSector = 'base\worlds\03_night_city\_compiled\default\quest_0eb702d8c8f8ee5b.streamingsector'
$terminalSector = 'base\worlds\03_night_city\_compiled\default\interior_-49_37_1_0.streamingsector'
$decodedPath = Join-Path $workspace 'prealpha/misty_rooftop_lift_20261117_01/work/decoded_roof_02/manifest.json'
$decoded = Get-Content -LiteralPath $decodedPath -Raw | ConvertFrom-Json
function Sector($native) {
    $row = @($decoded.rows | Where-Object { $_.depot -ceq $native.depot -and $_.archive -ceq $native.archive })
    if ($row.Count -ne 1 -or $row[0].sha256 -cne $native.sha256 -or
        (Get-FileHash -LiteralPath $row[0].json).Hash -cne $row[0].json_sha256) { throw 'Decoded placement differs from the current provider' }
    return (Get-Content -LiteralPath $row[0].json -Raw | ConvertFrom-Json -AsHashtable -Depth 100).Data.RootChunk
}

$seatSector = Sector (Captured $captured $roofSector 'basegame_3_nightcity.archive')
$seat = @($seatSector.persistentNodes | Where-Object { $_.globalNodeId.hash -eq '1232998081395113966' })
if ($seat.Count -ne 1 -or $seatSector.nodes[[int]$seat[0].nodeIdx].Data.debugName.'$value' -cne '{q115_ws_v_sitting_final_decision}') {
    throw 'Original player seat placement changed'
}
$landingSector = Sector (Captured $support $terminalSector 'ep1_1_nightcity.archive')
$landing = @($landingSector.persistentNodes | Where-Object { $_.globalNodeId.hash -eq '6984754349946376857' })
$anchorRef = '$/03_night_city/c_watson/little_china/loc_q115_mistyc_mistys_ripperdoc_roof_prefabDR5IG6A/loc_q115_mystic_mistys_ripperdoc_roof_gameplay_prefab75UZAWI/loc_q115_mystic_mistys_ripperdoc_roof_devices_prefabNCP6VPY/lift_2_floors_prefabXK7C7ZI/lift_terminal_2'
if ($landing.Count -ne 1 -or @($landingSector.nodeRefs | Where-Object { $_.'$value' -ceq $anchorRef }).Count -ne 1) {
    throw 'Roof landing anchor changed'
}

function Vector($v) { return [Numerics.Vector3]::new($v.X, $v.Y, $v.Z) }
function Rotation($q) { return [Numerics.Quaternion]::Normalize([Numerics.Quaternion]::new($q.i, $q.j, $q.k, $q.r)) }
$anchorTransform = $landing[0].transform
$seatTransform = $seat[0].transform
$inverse = [Numerics.Quaternion]::Inverse((Rotation $anchorTransform.orientation))
$localPosition = [Numerics.Vector3]::Transform((Vector $seatTransform.position) - (Vector $anchorTransform.position), $inverse)
$localRotation = [Numerics.Quaternion]::Normalize([Numerics.Quaternion]::Multiply($inverse, (Rotation $seatTransform.orientation)))

$seatDonor = Captured $captured 'towercontinued\streetkid_seat_s1\seat.scene' 'zzzz_PTFR_Combined.archive'
$chairDonor = Captured $captured 'base\quest\side_quests\sq028\scenes\kerry_villa\sq028_kerry_villa_sit.scene' 'basegame_4_gamedata.archive'
$storyDonor = Captured $captured 'base\quest\main_quests\part1\q115\scenes\q115_02b_ripperdoc_roof.scene' 'basegame_4_gamedata.archive'
$autoScene = Captured $captured 'towercontinued\streetkid_seat_auto\seat_mirror.scene' 'zzzz_PTFR_Combined.archive'
$ownerDonor = Captured $support 'towercontinued\streetkid_seat_auto\owner.questphase' 'zzzz_PTFR_Combined.archive'

function SceneNode($graph, [int]$id) {
    $matches = @($graph | Where-Object { $_.Chunk.NodeId.Id.ToString() -eq "$id" })
    if ($matches.Count -ne 1) { throw "Ambiguous scene node $id" }
    return $matches[0].Chunk
}

$chair = (Read-Cr2wFile $chairDonor.raw).RootChunk
$story = (Read-Cr2wFile $storyDonor.raw).RootChunk
$commonWorkspot = 'base\workspots\player\chair\player__sit_chair__sit_around__01.workspot'
$retailWorkspots = @($support.hits | Where-Object depot -ceq $commonWorkspot)
if ($retailWorkspots.Count -ne 2 -or @($retailWorkspots.sha256 | Select-Object -Unique).Count -ne 1) { throw 'Ambiguous chair workspot provider' }
foreach ($row in $retailWorkspots) { if ((Get-FileHash -LiteralPath $row.raw).Hash -cne $row.sha256) { throw 'Chair workspot drift' } }
$originalData = @($story.Workspots | Where-Object { $_.Chunk.DataId.Id.ToString() -eq '3071028109' })
$originalAction = (SceneNode $story.SceneGraph.Chunk.Graph 1491).QuestNode.Chunk.ParamsV1.Chunk
if ($originalData.Count -ne 1 -or $originalData[0].Chunk.WorkspotResource.DepotPath.ToString() -cne $commonWorkspot -or
    $originalAction.EntryId.Id.ToString() -ne '11' -or !$originalAction.IsPlayer -or
    $chair.Workspots.Count -ne 1 -or $chair.Workspots[0].Chunk.WorkspotResource.DepotPath.ToString() -cne $commonWorkspot) {
    throw 'Original player chair animation changed'
}

$scene = Read-Cr2wFile $seatDonor.raw
$root = $scene.RootChunk
$root.DebugSymbols = [Activator]::CreateInstance($root.DebugSymbols.GetType())
$scene = (Repair-StreetkidSceneIdentity $scene).File
$root = $scene.RootChunk
$root.InterruptionScenarios.Clear()
$graph = $root.SceneGraph.Chunk.Graph
if ($graph.Count -ne 9 -or $root.WorkspotInstances.Count -ne 1) { throw 'Seat scene template changed' }
$root.Workspots.Clear()
Add-RedHandle $root.Workspots $chair.Workspots[0].Chunk.DeepCopy()
$root.WorkspotInstances.Clear()
$instance = $chair.WorkspotInstances[0].DeepCopy()
$instance.OriginMarker.NodeRef = [WolvenKit.RED4.Types.NodeRef]::op_Implicit($anchorRef)
$instance.PlayAtActorLocation = $false
$instance.LocalTransform.Position.X = [float]$localPosition.X
$instance.LocalTransform.Position.Y = [float]$localPosition.Y
$instance.LocalTransform.Position.Z = [float]$localPosition.Z
$instance.LocalTransform.Orientation.I = [float]$localRotation.X
$instance.LocalTransform.Orientation.J = [float]$localRotation.Y
$instance.LocalTransform.Orientation.K = [float]$localRotation.Z
$instance.LocalTransform.Orientation.R = [float]$localRotation.W
$root.WorkspotInstances.Add($instance)

$use = (SceneNode $graph 36).QuestNode.Chunk.ParamsV1.Chunk
$use.WorkspotInstanceId.Id = $instance.WorkspotInstanceId.Id
$use.EntryId.Id = $originalAction.EntryId.Id
$use.PlayAtActorLocation = $false
$choice = SceneNode $graph 4
$choice.AtwParams.EntityPosition.X = [float]$localPosition.X
$choice.AtwParams.EntityPosition.Y = [float]$localPosition.Y
$choice.AtwParams.EntityPosition.Z = [float]($localPosition.Z + 0.1)

function FactGuard($facts) {
    $test = [WolvenKit.RED4.Types.questLogicalCondition]::new()
    $test.Operation = [WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
    foreach ($entry in $facts.GetEnumerator()) {
        Add-RedHandle $test.Conditions (New-FactCondition $entry.Key $entry.Value ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
    }
    return $test
}

$interactive = (Read-Cr2wFile $autoScene.raw).RootChunk.SceneGraph.Chunk.Graph
$departure = (SceneNode $interactive 3030).DeepCopy()
Set-RedHandleProperty $departure.QuestNode.Chunk Condition (FactGuard ([ordered]@{PTFRMistySeat_Depart=1; PTFRMistySeat_Using=0}))
$using = (SceneNode $interactive 3031).DeepCopy()
Set-RedHandleProperty $using QuestNode (New-SetFactNode 3031 'PTFRMistySeat_Using' 1)
$sitDestination = $choice.OutputSockets[0].Destinations[0]
$using.OutputSockets[0].Destinations[0].NodeId.Id = $sitDestination.NodeId.Id
$using.OutputSockets[0].Destinations[0].IsockStamp.Ordinal = $sitDestination.IsockStamp.Ordinal
$sitDestination.NodeId.Id = [uint32]3031
$sitDestination.IsockStamp.Ordinal = [uint16]1
$start = SceneNode $graph 1
$start.OutputSockets[0].Destinations.Add((SceneNode $interactive 1).OutputSockets[0].Destinations[1].DeepCopy())
Add-RedHandle $graph $departure
Add-RedHandle $graph $using

$ownerTemplate = (Read-Cr2wFile $ownerDonor.raw).RootChunk.Graph.Chunk
function Pause([int]$id, $condition) {
    $node = (Get-QuestNode $ownerTemplate 10).DeepCopy()
    $node.Id = [uint16]$id
    foreach ($socket in $node.Sockets) { $socket.Chunk.Connections.Clear() }
    Set-RedHandleProperty $node Condition $condition
    return $node
}

$phase = [WolvenKit.RED4.Types.questGraphDefinition]::new()
function AddNode($node) { Add-RedHandle $phase.Nodes $node }
function Connect([int]$from,[string]$port,[int]$to,[string]$inputPort = 'In') {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $phase $from) $port) (Get-QuestSocket (Get-QuestNode $phase $to) $inputPort))
}

$guards = [ordered]@{
    PostTowerFreeRoamActive=1; PTFRP0_DR13=1; PTFRPA2_Finished=1; q307_done=1; q307_finished=1;
    q307_2079=1; q307_active=0; q307_main_game_killed=1; q307_ep1_killed=1;
    q115_point_of_no_return=0; q305_johnny_scene_active=0; PTFRBASE_Suspended=0; PTFRWORLD_Suspended=0;
    PTFRMV_Suspended=0; PTFRMV_QuestOwns=0; PTFRMistySeat_Permit=1; PTFRMistySeat_Depart=0;
    PTFRMistySeat_Active=0; PTFRMistySeat_Interrupted=0
}
$gateDepot = 'towercontinued\misty_rooftop_seat\gate.questphase'
$sceneDepot = 'towercontinued\misty_rooftop_seat\sit.scene'
$sceneNode = (Get-QuestNode $ownerTemplate 3).DeepCopy()
$sceneNode.Id = [uint16]7
foreach ($socket in $sceneNode.Sockets) { $socket.Chunk.Connections.Clear() }
$sceneNode.SceneFile = [Activator]::CreateInstance($sceneNode.GetType().GetProperty('SceneFile').PropertyType,
    [object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($sceneDepot)))
$sceneNode.SceneLocation.NodeRef = [WolvenKit.RED4.Types.NodeRef]::op_Implicit($anchorRef)

AddNode (New-InputNode 0 'In1')
AddNode (New-SetFactNode 1 'PTFRMistySeat_Registered' 1)
AddNode (Pause 2 (FactGuard $guards))
AddNode (New-ConditionNode 3 (FactGuard $guards))
AddNode (New-SetFactNode 4 'PTFRMistySeat_Active' 1)
AddNode (New-SetFactNode 5 'PTFRMistySeat_Permit' 0)
AddNode (New-SetFactNode 6 'PTFRMistySeat_Using' 0)
AddNode $sceneNode
AddNode (New-SetFactNode 8 'PTFRMistySeat_Active' 0)
AddNode (Pause 9 (Get-QuestNode $ownerTemplate 9).Condition.Chunk.DeepCopy())
AddNode (New-SetFactNode 10 'PTFRMistySeat_Interrupted' 1)
AddNode (New-SetFactNode 11 'PTFRMistySeat_Active' 0)
AddNode (Pause 12 (FactGuard ([ordered]@{PTFRMistySeat_Depart=1})))
AddNode (New-SetFactNode 13 'PTFRMistySeat_Interrupted' 0)

Connect 0 Out 1
Connect 1 Out 2
Connect 2 Out 3
Connect 3 True 4
Connect 3 False 2
Connect 4 Out 5
Connect 5 Out 6
Connect 6 Out 7 in
Connect 7 out 8
Connect 8 Out 9
Connect 9 Out 2
Connect 7 'Default INT' 10
Connect 10 Out 11
Connect 11 Out 12
Connect 12 Out 13
Connect 13 Out 9

$file = [WolvenKit.RED4.Archive.CR2W.CR2WFile]::new()
$file.RootChunk = [WolvenKit.RED4.Types.questQuestPhaseResource]::new()
$file.RootChunk.CookingPlatform = [WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
Set-RedHandleProperty $file.RootChunk Graph $phase
[void][IO.Directory]::CreateDirectory($out)
$resources = @(foreach ($entry in @(@{name='gate';depot=$gateDepot;file=$file},@{name='sit';depot=$sceneDepot;file=$scene})) {
    $dest = Join-Path $out ('source/' + $entry.depot)
    Write-Cr2wFile $entry.file $dest
    $export = Join-Path $out ($entry.name + '.json')
    Export-Cr2wJson (Read-Cr2wFile $dest) $export
    @{depot=$entry.depot;raw=$dest;sha256=(Get-FileHash -LiteralPath $dest).Hash;json=$export;json_sha256=(Get-FileHash -LiteralPath $export).Hash}
})
@{status='SERIALIZED';baseline_sha256=$baseline;resources=$resources;guards=$guards;anchor_ref=$anchorRef;
    anchor=$anchorTransform;seat=$seatTransform;relative_position=@($localPosition.X,$localPosition.Y,$localPosition.Z);
    relative_orientation=@($localRotation.X,$localRotation.Y,$localRotation.Z,$localRotation.W);
    workspot=$commonWorkspot;source_decoded_sha256=(Get-FileHash -LiteralPath $decodedPath).Hash;
    native_sources=@($seatDonor,$chairDonor,$storyDonor,$autoScene,$ownerDonor)|ForEach-Object {@{depot=$_.depot;sha256=$_.sha256}}} |
    ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8NoBOM
Write-Output 'Serialized the private roof seat and native repeatable phase.'
