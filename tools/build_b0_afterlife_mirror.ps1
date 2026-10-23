param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0',
    [switch]$UsePlaneDistance,
    [switch]$FactOnlyOneShot,
    [switch]$UseAbsolutePlaneDistance,
    [switch]$UseModProximityFact,
    [switch]$UseAbsoluteTrigger
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly
if (([int]([bool]$UsePlaneDistance) + [int]([bool]$FactOnlyOneShot) + [int]([bool]$UseAbsolutePlaneDistance) + [int]([bool]$UseModProximityFact) + [int]([bool]$UseAbsoluteTrigger)) -gt 1) {
    throw 'Choose one Afterlife mirror experiment mode'
}
$UseDistance = $UsePlaneDistance -or $UseAbsolutePlaneDistance
$UseModScene = $UseDistance -or $FactOnlyOneShot -or $UseModProximityFact -or $UseAbsoluteTrigger

# Single-site, opt-in Afterlife mirror owner. Reuse the *unchanged* vanilla
# mirror scene and the isolated vanilla leaf's trigger, scene node and delay.
# Do not restart its 44-mirror parent or write any vanilla fact.
$mirrorPath = Join-Path $WorkspaceRoot 'research\b0_mirror_investigation\extracted\raw\base\open_world\scenes\mirrors\mirror_interactions_control.questphase'
$basePath = Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase'
$scenePath = Join-Path $WorkspaceRoot 'research\b0_afterlife_mirror\extracted\raw\base\open_world\scenes\mirrors\mirror_scene_afterlife.scene'
$distancePath = Join-Path $WorkspaceRoot 'research\phase2b_p4\vendor_owner\raw\base\open_world\vendors\watson\little_china\little_china_vendors.questphase'
$inputs = @($mirrorPath,$basePath,$scenePath)
if ($UseDistance) { $inputs += $distancePath }
foreach ($path in $inputs) { if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing reviewed input: $path" } }
$inputHashes = @{}
foreach ($path in $inputs) { $inputHashes[$path] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash }

$src = Join-Path $WorkspaceRoot $(if ($UseAbsoluteTrigger) { 'archive\b0_afterlife_mirror_v7\source' } elseif ($UseModProximityFact) { 'archive\b0_afterlife_mirror_v5\source' } elseif ($UseAbsolutePlaneDistance) { 'archive\b0_afterlife_mirror_v4\source' } elseif ($FactOnlyOneShot) { 'archive\b0_afterlife_mirror_v3\source' } elseif ($UsePlaneDistance) { 'archive\b0_afterlife_mirror_v2\source' } else { 'archive\b0_afterlife_mirror\source' })
$out = Join-Path $WorkspaceRoot $(if ($UseAbsoluteTrigger) { 'build\B0_Afterlife_Mirror_V7' } elseif ($UseModProximityFact) { 'build\B0_Afterlife_Mirror_V5' } elseif ($UseAbsolutePlaneDistance) { 'build\B0_Afterlife_Mirror_V4' } elseif ($FactOnlyOneShot) { 'build\B0_Afterlife_Mirror_V3' } elseif ($UsePlaneDistance) { 'build\B0_Afterlife_Mirror_V2' } else { 'build\B0_Afterlife_Mirror' })
$val = Join-Path $WorkspaceRoot $(if ($UseAbsoluteTrigger) { 'research\b0_afterlife_mirror\validation_v7' } elseif ($UseModProximityFact) { 'research\b0_afterlife_mirror\validation_v5' } elseif ($UseAbsolutePlaneDistance) { 'research\b0_afterlife_mirror\validation_v4' } elseif ($FactOnlyOneShot) { 'research\b0_afterlife_mirror\validation_v3' } elseif ($UsePlaneDistance) { 'research\b0_afterlife_mirror\validation_v2' } else { 'research\b0_afterlife_mirror\validation' })
New-Item -ItemType Directory -Force -Path $src,$out,$val | Out-Null
$phaseDepot = 'towercontinued\b0_afterlife_mirror\afterlife_mirror_owner.questphase'
$sceneDepot = 'towercontinued\b0_afterlife_mirror\afterlife_mirror_scene.scene'
$archiveName = 'TowerContinued_B0_Afterlife_Mirror.archive'
$prefix = 'PTFRB0ALM_'

$mirror = Read-Cr2wFile $mirrorPath
$base = Read-Cr2wFile $basePath
$outer = Get-QuestNode $mirror.RootChunk.Graph.Chunk 42
$outerGraph = $outer.PhaseGraph.Chunk
$afterlifeLeaf = @( $outerGraph.Nodes | Where-Object {
    $_.Chunk.GetType().Name -eq 'questPhaseNodeDefinition' -and
    @($_.Chunk.PhaseGraph.Chunk.Nodes | Where-Object {
        $_.Chunk.GetType().Name -eq 'questSceneNodeDefinition' -and
        $_.Chunk.SceneFile.DepotPath.ToString() -eq 'base\open_world\scenes\mirrors\mirror_scene_afterlife.scene'
    }).Count -eq 1
} )
if ($afterlifeLeaf.Count -ne 1) { throw 'Vanilla Afterlife mirror leaf not unique' }
$leaf = $afterlifeLeaf[0].Chunk.PhaseGraph.Chunk
$trigger = (Get-QuestNode $leaf 3).Condition.Chunk.DeepCopy()
if ($trigger.GetType().Name -ne 'questTriggerCondition' -or
    $trigger.TriggerAreaRef.ToString() -ne '#mirror_tr_afterlife') { throw 'Afterlife trigger changed' }
$absoluteTrigger = '$/03_night_city/c_watson/little_china/#loc_q103_afterlife/#loc_q103_afterlife_openworld/#mirror_scene_afterlife/#mirror_tr_afterlife'
if ($UseAbsoluteTrigger) {
    $sectorPath = Join-Path $WorkspaceRoot 'research\phase2b_p4\staging_scan\ep1_1_nightcity\json\base\worlds\03_night_city\_compiled\default\always_loaded_1.streamingsector.json'
    if (-not (Test-Path -LiteralPath $sectorPath -PathType Leaf) -or
        -not (Select-String -LiteralPath $sectorPath -Pattern $absoluteTrigger -SimpleMatch -Quiet)) {
        throw 'Full Afterlife trigger reference missing from reviewed always-loaded sector'
    }
    $trigger.TriggerAreaRef = [WolvenKit.RED4.Types.NodeRef]::op_Implicit($absoluteTrigger)
}
$sceneTemplate = Get-QuestNode $leaf 2
if ($sceneTemplate.SceneFile.DepotPath.ToString() -ne 'base\open_world\scenes\mirrors\mirror_scene_afterlife.scene' -or
    $sceneTemplate.SceneLocation.NodeRef.ToString() -ne '#mirror_sm_scene_afterlife') { throw 'Afterlife scene/marker changed' }
$delayTemplate = Get-QuestNode $leaf 4
$delayCondition = $delayTemplate.Condition.Chunk
if ($delayCondition.GetType().Name -ne 'questTimeCondition' -or
    $delayCondition.Type.Chunk.GetType().Name -ne 'questRealtimeDelay_ConditionType' -or
    $delayCondition.Type.Chunk.Seconds.ToString() -ne '1') { throw 'Vanilla one-second mirror rearm changed' }
$combatTemplate = (Get-QuestNode $outerGraph 57).Condition.Chunk.DeepCopy()
if ($combatTemplate.GetType().Name -ne 'questCharacterCondition' -or
    $combatTemplate.Type.Chunk.GetType().Name -ne 'questCharacterCombat_ConditionType' -or
    $combatTemplate.Type.Chunk.Inverted.ToString() -ne 'False') { throw 'Vanilla combat gate changed' }
$combatTemplate.Type.Chunk.Inverted = $true

if ($UseDistance) {
    $vendor = Read-Cr2wFile $distancePath
    $clothing = (Get-QuestNode $vendor.RootChunk.Graph.Chunk 2).PhaseGraph.Chunk
    $distanceTemplate = (Get-QuestNode $clothing 14).Condition.Chunk
    if ($distanceTemplate.GetType().Name -ne 'questDistanceCondition' -or
        $distanceTemplate.Type.Chunk.GetType().Name -ne 'questDistanceComparison_ConditionType' -or
        $distanceTemplate.Type.Chunk.ComparisonType.ToString() -ne 'Less' -or
        $distanceTemplate.Type.Chunk.DistanceDefinition2.Chunk.DistanceValue.ToString() -ne '50') {
        throw 'Reviewed vanilla distance condition changed'
    }
    function New-PlaneDistance([string]$Comparison) {
        $c = $distanceTemplate.DeepCopy()
        $c.Type.Chunk.ComparisonType = [WolvenKit.RED4.Types.Enums+EComparisonType]::$Comparison
        $nodeRef = if ($UseAbsolutePlaneDistance) {
            '$/03_night_city/c_watson/little_china/#loc_q103_afterlife/#loc_q103_afterlife_gameplay/#loc_q103_afterlife_devices/#mirror_plane_afterlife'
        } else { '#mirror_plane_afterlife' }
        $c.Type.Chunk.DistanceDefinition1.Chunk.NodeRef2.Reference =
            [WolvenKit.RED4.Types.NodeRef]::op_Implicit($nodeRef)
        $c.Type.Chunk.DistanceDefinition2.Chunk.DistanceValue = [single]4
        return $c
    }
    $entryDistance = New-PlaneDistance 'Less'
    $sceneExitDistance = New-PlaneDistance 'Greater'
}
if ($UseModScene) {
    $modScene = Read-Cr2wFile $scenePath
    $exitMatches = @($modScene.RootChunk.SceneGraph.Chunk.Graph | Where-Object { $_.Chunk.NodeId.Id.ToString() -eq '4398' })
    if ($exitMatches.Count -ne 1 -or $exitMatches[0].Chunk.GetType().Name -ne 'scnQuestNode' -or
        $exitMatches[0].Chunk.QuestNode.Chunk.Condition.Chunk.GetType().Name -ne 'questTriggerCondition' -or
        $exitMatches[0].Chunk.QuestNode.Chunk.Condition.Chunk.Type.ToString() -ne 'IsOutside') {
        throw 'Vanilla Afterlife mirror scene exit changed'
    }
    if ($FactOnlyOneShot) {
        $timedExit = $delayTemplate.Condition.Chunk.DeepCopy()
        $timedExit.Type.Chunk.Seconds = [uint32]30
        $timedExit.Type.Chunk.Miliseconds = [uint32]0
        Set-RedHandleProperty $exitMatches[0].Chunk.QuestNode.Chunk Condition $timedExit
    } elseif ($UseModProximityFact) {
        Set-RedHandleProperty $exitMatches[0].Chunk.QuestNode.Chunk Condition (
            New-FactCondition ($prefix+'Near') 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
    } elseif ($UseAbsoluteTrigger) {
        $exitTrigger = $exitMatches[0].Chunk.QuestNode.Chunk.Condition.Chunk.DeepCopy()
        $exitTrigger.TriggerAreaRef = [WolvenKit.RED4.Types.NodeRef]::op_Implicit($absoluteTrigger)
        Set-RedHandleProperty $exitMatches[0].Chunk.QuestNode.Chunk Condition $exitTrigger
    } else {
        Set-RedHandleProperty $exitMatches[0].Chunk.QuestNode.Chunk Condition $sceneExitDistance
    }
    $modScenePath = Join-Path $src $sceneDepot
    Write-Cr2wFile $modScene $modScenePath
    Export-Cr2wJson (Read-Cr2wFile $modScenePath) (Join-Path $val 'afterlife_mirror_scene.scene.json')
}

$guardFacts = [ordered]@{
    PostTowerFreeRoamActive=1; PTFRP0_DR13=1; q307_active=0; q307_done=1;
    q307_finished=1; q307_2079=1; q307_main_game_killed=1;
    q305_johnny_scene_active=0; mirror_interaction_disabled=0;
    q115_point_of_no_return=0; PTFRB0ALM_Enabled=1; PTFRB0ALM_Interrupted=0
}
$condition = [WolvenKit.RED4.Types.questLogicalCondition]::new()
$condition.Operation = [WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
foreach ($fact in $guardFacts.Keys) {
    Add-RedHandle $condition.Conditions (New-FactCondition $fact $guardFacts[$fact] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
}
if ($UseModProximityFact) {
    Add-RedHandle $condition.Conditions (New-FactCondition ($prefix+'Near') 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
} elseif (-not $FactOnlyOneShot) {
    Add-RedHandle $condition.Conditions $(if ($UseDistance) { $entryDistance } else { $trigger })
}
Add-RedHandle $condition.Conditions $combatTemplate

$graph = [WolvenKit.RED4.Types.questGraphDefinition]::new()
function Put($node) { Add-RedHandle $graph.Nodes $node }
function Link($from,$socket,$to,$dest='In') {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $from) $socket) (Get-QuestSocket (Get-QuestNode $graph $to) $dest))
}
Put (New-InputNode 0 'In1')
Put (New-SetFactNode 1 ($prefix+'Ready') 1)
$wait = (Get-QuestNode $base.RootChunk.Graph.Chunk 106).DeepCopy(); $wait.Id = [uint16]2
foreach ($socket in $wait.Sockets) { $socket.Chunk.Connections.Clear() }
Set-RedHandleProperty $wait Condition $condition
Put $wait
Put (New-SetFactNode 3 ($prefix+'Active') 1)
$sceneNode = $sceneTemplate.DeepCopy(); $sceneNode.Id = [uint16]4
foreach ($socket in $sceneNode.Sockets) { $socket.Chunk.Connections.Clear() }
if ($UseModScene) {
    $resourcePath = [WolvenKit.RED4.Types.ResourcePath]::op_Implicit($sceneDepot)
    $sceneNode.SceneFile = [Activator]::CreateInstance($sceneNode.GetType().GetProperty('SceneFile').PropertyType,[object[]]@($resourcePath))
}
Put $sceneNode
Put (New-SetFactNode 5 ($prefix+'Active') 0)
Put (New-SetFactNode 6 ($prefix+'Completed') 1)
$delay = $delayTemplate.DeepCopy(); $delay.Id = [uint16]7
foreach ($socket in $delay.Sockets) { $socket.Chunk.Connections.Clear() }
Put $delay
Put (New-SetFactNode 8 ($prefix+'Interrupted') 1)
Put (New-SetFactNode 9 ($prefix+'Active') 0)
Link 0 Out 1; Link 1 Out 2; Link 2 Out 3; Link 3 Out 4 mirror_interaction
Link 4 mirror_interaction_out 5; Link 5 Out 6
if (-not $FactOnlyOneShot) { Link 6 Out 7; Link 7 Out 2 }
Link 4 'Default INT' 8; Link 8 Out 9

$root = [WolvenKit.RED4.Types.questQuestPhaseResource]::new()
$root.CookingPlatform = [WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
Set-RedHandleProperty $root Graph $graph
$phase = [WolvenKit.RED4.Archive.CR2W.CR2WFile]::new(); $phase.RootChunk = $root
$phasePath = Join-Path $src $phaseDepot
Write-Cr2wFile $phase $phasePath
Export-Cr2wJson (Read-Cr2wFile $phasePath) (Join-Path $val 'afterlife_mirror_owner.questphase.json')
foreach ($path in $inputs) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $inputHashes[$path]) { throw "Reviewed input changed during build: $path" }
}
$actual = @(Get-ChildItem -LiteralPath $src -File -Recurse | ForEach-Object { [IO.Path]::GetRelativePath($src,$_.FullName) } | Sort-Object)
$allowed = @($phaseDepot)
if ($UseModScene) { $allowed += $sceneDepot }
$allowed = @($allowed | Sort-Object)
if (@(Compare-Object $actual $allowed).Count) { throw 'Unexpected source files in Afterlife mirror archive' }
$hashService = [WolvenKit.Common.Services.HashService]::new(); $hashService.Load()
$archivePath = Join-Path $out $archiveName
$stream = [IO.File]::Create($archivePath)
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService,[WolvenKit.SerilogWrapper]::new())
    if (-not $writer.WriteArchive([IO.DirectoryInfo]::new($src),$stream)) { throw 'Archive write failed' }
} finally { $stream.Dispose() }
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new(); $archive = $null
if ($reader.ReadArchive($archivePath,$hashService,[ref]$archive).ToString() -ne 'NoError') { throw 'Archive did not reopen' }
$packed = @($archive.Files.Values | ForEach-Object { $_.Name } | Sort-Object)
if (@(Compare-Object $packed $allowed).Count) { throw 'Archive manifest mismatch' }
foreach ($entry in $archive.Files.Values) {
    $memory = [IO.MemoryStream]::new()
    try {
        $entry.Extract($memory)
        if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray())) -ne
            (Get-FileHash -LiteralPath (Join-Path $src $entry.Name) -Algorithm SHA256).Hash) { throw "Packed bytes differ: $($entry.Name)" }
    } finally { $memory.Dispose() }
}
$manifest = [ordered]@{
    status=$(if ($UseAbsoluteTrigger) { 'EXPERIMENTAL_V7_ABSOLUTE_TRIGGER_NOT_INSTALLED' } elseif ($UseModProximityFact) { 'EXPERIMENTAL_V5_CET_PROXIMITY_NOT_INSTALLED' } elseif ($UseAbsolutePlaneDistance) { 'EXPERIMENTAL_V4_ABSOLUTE_PLANE_DISTANCE_NOT_INSTALLED' } elseif ($FactOnlyOneShot) { 'EXPERIMENTAL_V3_FACT_ONLY_ONESHOT_NOT_INSTALLED' } elseif ($UsePlaneDistance) { 'EXPERIMENTAL_V2_PLANE_DISTANCE_NOT_INSTALLED' } else { 'EXPERIMENTAL_OPT_IN_SINGLE_SITE_DISPOSABLE_ONLY' })
    archive=$archiveName
    sha256=(Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
    resources=$packed
    scene=$(if ($UseModScene) { $sceneDepot } else { 'base\open_world\scenes\mirrors\mirror_scene_afterlife.scene' })
    entry_gate=$(if ($UseAbsoluteTrigger) { "IsInside $absoluteTrigger" } elseif ($UseModProximityFact) { 'Mod-owned PTFRB0ALM_Near=1; CET dev-only proximity writer' } elseif ($FactOnlyOneShot) { 'CET opt-in at mirror; Tower facts + no combat, no native spatial gate' } elseif ($UseAbsolutePlaneDistance) { 'Less than 4m from absolute mirror-plane NodeRef' } elseif ($UsePlaneDistance) { 'Less than 4m from #mirror_plane_afterlife' } else { 'IsInside #mirror_tr_afterlife' })
    exit_gate=$(if ($UseAbsoluteTrigger) { "IsOutside $absoluteTrigger" } elseif ($UseModProximityFact) { 'Mod-owned PTFRB0ALM_Near=0; native scene exit/rearm' } elseif ($FactOnlyOneShot) { 'Single use; scene 30s timed fallback exit' } elseif ($UseAbsolutePlaneDistance) { 'Greater than 4m from absolute mirror-plane NodeRef' } elseif ($UsePlaneDistance) { 'Greater than 4m from #mirror_plane_afterlife' } else { 'IsOutside #mirror_tr_afterlife' })
    source_hashes=$inputHashes
    guard_facts=$guardFacts
    vanilla_replacements=@()
    enable_fact=$prefix+'Enabled'
    known_limits=@('Afterlife v1/v2 entry never fired on observed save','v3 isolates scene startup but is not a lasting restoration','Native spatial reference unresolved','Normal mirror exit and reload unvalidated','No general mirror controller restoration')
}
[IO.File]::WriteAllText((Join-Path $val 'build_manifest.json'),($manifest | ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$manifest | ConvertTo-Json -Depth 10
