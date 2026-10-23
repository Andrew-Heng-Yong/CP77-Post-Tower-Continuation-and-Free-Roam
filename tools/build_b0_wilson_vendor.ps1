param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly

# Opt-in Wilson-only disposable-save experiment. Keep his native spawn/market
# identity and physical Shop choice; never execute old q001/q101/mq011 content.
$vendorPath = Join-Path $WorkspaceRoot 'research\phase2b_p4\vendor_owner\raw\base\quest\default_dialogs.questphase'
$scenePath = Join-Path $WorkspaceRoot 'research\b0_wilson_vendor\dialogue_extract\raw\base\open_world\vendors\watson\little_china\wat_lch_gunsmith_01\wat_lch_gunsmith_01.scene'
$basePath = Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase'
$inputs = @($vendorPath,$scenePath,$basePath)
$hashes = [ordered]@{}
foreach ($path in $inputs) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing reviewed input: $path" }
    $hashes[$path] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
}
$src = Join-Path $WorkspaceRoot 'archive\b0_wilson_vendor\source'
$out = Join-Path $WorkspaceRoot 'build\B0_Wilson_Vendor'
$val = Join-Path $WorkspaceRoot 'research\b0_wilson_vendor\validation'
New-Item -ItemType Directory -Force -Path $src,$out,$val | Out-Null
$archiveName = 'TowerContinued_B0_Wilson_Vendor.archive'
$rootDepot = 'towercontinued\b0_wilson_vendor\owner.questphase'
$sceneDepot = 'towercontinued\b0_wilson_vendor\shop.scene'
$prefix = 'PTFRB0WV_'
$fullTrigger = '$/03_night_city/c_watson/little_china/loc_megabuilding_a_prefab4KCU2IQ/loc_megabuilding_a_openworld_prefabM5EXU4A/#wat_lch_gunsmith_01_tr_met'
$fullMarker = '$/03_night_city/c_watson/little_china/loc_megabuilding_a_prefab4KCU2IQ/loc_megabuilding_a_openworld_prefabM5EXU4A/wat_lch_gunsmith_01_prefabD2IBAZA/#wat_sm_lch_gunsmith_01'

$vendor = Read-Cr2wFile $vendorPath
$base = Read-Cr2wFile $basePath
$outer = (Get-QuestNode (Get-QuestNode (Get-QuestNode $vendor.RootChunk.Graph.Chunk 7).PhaseGraph.Chunk 33).PhaseGraph.Chunk 4).PhaseGraph.Chunk
$inner = (Get-QuestNode $outer 11).PhaseGraph.Chunk
$spawn = Get-QuestNode $inner 5
$despawn = Get-QuestNode $inner 9
$sceneNode = Get-QuestNode $inner 4
$close = Get-QuestNode $inner 53
$wanted = Get-QuestNode $inner 55
$cut = Get-QuestNode $inner 56
$safe = Get-QuestNode $inner 57
if ($spawn.Actions.Count -ne 1 -or $despawn.Actions.Count -ne 1 -or
    $spawn.Actions[0].Type.Chunk.Action.ToString() -ne 'Activate' -or
    $despawn.Actions[0].Type.Chunk.Action.ToString() -ne 'Deactivate' -or
    $spawn.Actions[0].Type.Chunk.Reference.ToString() -ne '#wilson' -or
    $despawn.Actions[0].Type.Chunk.Reference.ToString() -ne '#wilson' -or
    $spawn.Actions[0].Type.Chunk.EntryName.ToString() -ne 'wilson' -or
    $spawn.Actions[0].Type.Chunk.PhaseName.ToString() -ne 'q001_give_weapon' -or
    $sceneNode.SceneFile.DepotPath.ToString() -ne 'base\open_world\vendors\watson\little_china\wat_lch_gunsmith_01\wat_lch_gunsmith_01.scene' -or
    $sceneNode.SceneLocation.NodeRef.ToString() -ne '#wat_sm_lch_gunsmith_01' -or
    $close.Condition.Chunk.Type.Chunk.DistanceDefinition2.Chunk.DistanceValue.ToString() -ne '30' -or
    $wanted.Condition.Chunk.Type.Chunk.FactName.ToString() -ne 'wanted_level' -or
    $safe.Condition.Chunk.Type.Chunk.FactName.ToString() -ne 'wanted_level' -or
    $cut.GetType().Name -ne 'questCutControlNodeDefinition') {
    throw 'Reviewed vanilla Wilson owner changed'
}

# Copy only the ordinary Shop path. Preserve the vanilla scene objects and
# executable input stamps; remove all old story branches and q001 gun prop.
$shop = Read-Cr2wFile $scenePath
$nodes = $shop.RootChunk.SceneGraph.Chunk.Graph
function SceneNode([int]$id) {
    $matches = @($nodes | Where-Object { $_.Chunk.NodeId.Id.ToString() -eq "$id" })
    if ($matches.Count -ne 1) { throw "Scene node $id is not unique" }
    return $matches[0].Chunk
}
function Set-OnlySceneEdge([int]$from,[int]$target,[int]$ordinal) {
    $sockets = (SceneNode $from).OutputSockets
    if ($sockets.Count -lt 1 -or $sockets[0].Destinations.Count -lt 1) { throw "No scene edge template at $from" }
    $edge = $sockets[0].Destinations[0].DeepCopy()
    $edge.NodeId.Id = [WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]$target)
    $edge.IsockStamp.Ordinal = [WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]$ordinal)
    $sockets[0].Destinations.Clear()
    $sockets[0].Destinations.Add($edge)
}
if (@($shop.RootChunk.EntryPoints).Count -ne 2 -or
    $shop.RootChunk.EntryPoints[0].Name.ToString() -ne 'wilson_default_in' -or
    $shop.RootChunk.EntryPoints[1].Name.ToString() -ne 'backup_lines' -or
    @($shop.RootChunk.Props).Count -ne 1 -or
    $shop.RootChunk.Props[0].PropName.ToString() -ne 'wilson_gun') {
    throw 'Reviewed Wilson scene entry/prop inventory changed'
}
$choice = SceneNode 177
$panel = SceneNode 215
$gate = SceneNode 224
if ($choice.GetType().Name -ne 'scnChoiceNode' -or $choice.Options.Count -ne 2 -or
    $choice.Options[0].Caption.ToString() -ne 'Shop' -or
    $panel.QuestNode.Chunk.Type.Chunk.GetType().Name -ne 'questVendorPanel_NodeType' -or
    $panel.QuestNode.Chunk.Type.Chunk.VendorId.ToString() -ne 'Vendors.wat_lch_gunsmith_01' -or
    $gate.QuestNode.Chunk.Condition.Chunk.GetType().Name -ne 'questTriggerCondition' -or
    $gate.QuestNode.Chunk.Condition.Chunk.TriggerAreaRef.ToString() -ne '#wat_lch_gunsmith_01_tr_met') {
    throw 'Reviewed Wilson Shop path changed'
}
$gate.QuestNode.Chunk.Condition.Chunk.TriggerAreaRef = [WolvenKit.RED4.Types.NodeRef]::op_Implicit($fullTrigger)
Set-OnlySceneEdge 0 678 0
Set-OnlySceneEdge 678 224 1
Set-OnlySceneEdge 224 177 0
Set-OnlySceneEdge 177 215 1
Set-OnlySceneEdge 215 177 0
$choice.Options.RemoveAt(1)
$keep = @(0,678,224,177,215)
for ($i=$nodes.Count-1; $i -ge 0; $i--) {
    if ([int]::Parse($nodes[$i].Chunk.NodeId.Id.ToString()) -notin $keep) { $nodes.RemoveAt($i) }
}
$shop.RootChunk.EntryPoints.RemoveAt(1)
$shop.RootChunk.SceneGraph.Chunk.StartNodes.RemoveAt(1)
$shop.RootChunk.Props.Clear()
$shopPath = Join-Path $src $sceneDepot
Write-Cr2wFile $shop $shopPath
Export-Cr2wJson (Read-Cr2wFile $shopPath) (Join-Path $val 'shop.scene.json')

function Copy-Node($source,[int]$id) {
    $node = $source.DeepCopy(); $node.Id = [uint16]$id
    foreach ($socket in $node.Sockets) { $socket.Chunk.Connections.Clear() }
    return $node
}
function New-Wait([int]$id,$condition) {
    $node = Copy-Node (Get-QuestNode $base.RootChunk.Graph.Chunk 106) $id
    Set-RedHandleProperty $node Condition $condition
    return $node
}
function Fact([string]$name,[int]$value,[string]$operator='Equal') {
    return New-FactCondition $name $value ([WolvenKit.RED4.Types.Enums+EComparisonType]::$operator)
}
function New-PhaseFile($graph) {
    $resource = [WolvenKit.RED4.Types.questQuestPhaseResource]::new()
    $resource.CookingPlatform = [WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
    Set-RedHandleProperty $resource Graph $graph
    $file = [WolvenKit.RED4.Archive.CR2W.CR2WFile]::new(); $file.RootChunk=$resource
    return $file
}

# Inner owner uses the game's native Wilson spawn and wanted-level cut. The
# sole non-native distance check is the mod-owned 80m Near fact from CET.
$body = [WolvenKit.RED4.Types.questGraphDefinition]::new()
function PutBody($node) { Add-RedHandle $body.Nodes $node }
function LinkBody([int]$from,[string]$socket,[int]$to,[string]$dest='In') {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $body $from) $socket) (Get-QuestSocket (Get-QuestNode $body $to) $dest))
}
PutBody (New-InputNode 0 'In1')
PutBody (Copy-Node $spawn 1)
PutBody (New-SetFactNode 2 ($prefix+'SpawnActionOut') 1)
PutBody (Copy-Node $close 3)
PutBody (New-SetFactNode 4 ($prefix+'ActorDistanceGate') 1)
$localScene = Copy-Node $sceneNode 5
$localScene.SceneLocation.NodeRef = [WolvenKit.RED4.Types.NodeRef]::op_Implicit($fullMarker)
$resourcePath = [WolvenKit.RED4.Types.ResourcePath]::op_Implicit($sceneDepot)
$localScene.SceneFile = [Activator]::CreateInstance($localScene.GetType().GetProperty('SceneFile').PropertyType,[object[]]@($resourcePath))
PutBody $localScene
PutBody (New-Wait 6 (Fact ($prefix+'Near') 0))
PutBody (Copy-Node $despawn 7)
PutBody (New-SetFactNode 8 ($prefix+'SpawnActionOut') 0)
PutBody (New-SetFactNode 9 ($prefix+'ActorDistanceGate') 0)
PutBody (New-OutputNode 10 'Out1')
PutBody (Copy-Node $wanted 11)
PutBody (Copy-Node $cut 12)
PutBody (Copy-Node $safe 13)
LinkBody 0 Out 1
LinkBody 1 Out 2
LinkBody 2 Out 3
LinkBody 3 Out 4
LinkBody 4 Out 5 wilson_default_in
LinkBody 4 Out 11
LinkBody 6 Out 7
LinkBody 7 Out 8
LinkBody 8 Out 9
LinkBody 9 Out 10
LinkBody 11 Out 12
LinkBody 11 Out 13
LinkBody 12 CutSource 5 CutDestination
LinkBody 13 Out 3
LinkBody 0 Out 6

$bodyDepot = 'towercontinued\b0_wilson_vendor\body.questphase'
$bodyPath = Join-Path $src $bodyDepot
Write-Cr2wFile (New-PhaseFile $body) $bodyPath
Export-Cr2wJson (Read-Cr2wFile $bodyPath) (Join-Path $val 'body.questphase.json')

$guardFacts = [ordered]@{
    PostTowerFreeRoamActive=1; PTFRP0_DR13=1; q307_active=0; q307_done=1;
    q307_finished=1; q307_2079=1; q307_main_game_killed=1;
    q305_johnny_scene_active=0; q115_point_of_no_return=0;
    wat_lch_gunsmith_01_default_on=1; q001_spawn_wilson_attention=0;
    q101_spawn_wilson_attention=0; mq011_active=0; PTFRB0WV_Enabled=1
}
$combined = [WolvenKit.RED4.Types.questLogicalCondition]::new()
$combined.Operation = [WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
foreach ($key in $guardFacts.Keys) { Add-RedHandle $combined.Conditions (Fact $key $guardFacts[$key]) }
$rootGraph = [WolvenKit.RED4.Types.questGraphDefinition]::new()
function PutRoot($node) { Add-RedHandle $rootGraph.Nodes $node }
function LinkRoot([int]$from,[string]$socket,[int]$to,[string]$dest='In') {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $rootGraph $from) $socket) (Get-QuestSocket (Get-QuestNode $rootGraph $to) $dest))
}
PutRoot (New-InputNode 0 'In1')
PutRoot (New-SetFactNode 1 ($prefix+'Ready') 1)
PutRoot (New-Wait 2 $combined)
PutRoot (New-Wait 3 (Fact ($prefix+'Near') 1))
$phase = [WolvenKit.RED4.Types.questPhaseNodeDefinition]::new()
$phase.Id=[uint16]4
$phase.PhaseResource = [Activator]::CreateInstance($phase.GetType().GetProperty('PhaseResource').PropertyType,[object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($bodyDepot)))
[void](New-QuestSocket $phase 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
[void](New-QuestSocket $phase 'In1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
[void](New-QuestSocket $phase 'Out1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Output))
PutRoot $phase
$departed = New-SetFactNode 5 ($prefix+'Departed') 1
$departed.Type.Chunk.SetExactValue = $false
PutRoot $departed
LinkRoot 0 Out 1
LinkRoot 1 Out 2
LinkRoot 2 Out 3
LinkRoot 3 Out 4 In1
LinkRoot 4 Out1 5
LinkRoot 5 Out 3
$rootPath=Join-Path $src $rootDepot
Write-Cr2wFile (New-PhaseFile $rootGraph) $rootPath
Export-Cr2wJson (Read-Cr2wFile $rootPath) (Join-Path $val 'owner.questphase.json')

foreach ($path in $inputs) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $hashes[$path]) { throw "Reviewed source changed: $path" }
}
$allowed=@($rootDepot,$bodyDepot,$sceneDepot)|Sort-Object
$actual=@(Get-ChildItem -LiteralPath $src -File -Recurse | ForEach-Object { [IO.Path]::GetRelativePath($src,$_.FullName) }|Sort-Object)
if (@(Compare-Object $allowed $actual).Count) { throw 'Unexpected Wilson source files' }
$hashService=[WolvenKit.Common.Services.HashService]::new();$hashService.Load()
$archivePath=Join-Path $out $archiveName
$stream=[IO.File]::Create($archivePath)
try {
    $writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService,[WolvenKit.SerilogWrapper]::new())
    if (-not $writer.WriteArchive([IO.DirectoryInfo]::new($src),$stream)) { throw 'Archive write failed' }
} finally { $stream.Dispose() }
$reader=[WolvenKit.RED4.Archive.IO.ArchiveReader]::new();$archive=$null
if ($reader.ReadArchive($archivePath,$hashService,[ref]$archive).ToString() -ne 'NoError') { throw 'Archive did not reopen' }
$packed=@($archive.Files.Values|ForEach-Object {$_.Name}|Sort-Object)
if (@(Compare-Object $allowed $packed).Count) { throw 'Packed Wilson resources differ' }
foreach ($entry in $archive.Files.Values) {
    $memory=[IO.MemoryStream]::new()
    try {
        $entry.Extract($memory)
        if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray())) -ne
            (Get-FileHash -LiteralPath (Join-Path $src $entry.Name) -Algorithm SHA256).Hash) { throw "Packed bytes differ: $($entry.Name)" }
    } finally { $memory.Dispose() }
}
$manifest=[ordered]@{
    status='OPT_IN_DISPOSABLE_BUILD_NOT_INSTALLED'
    archive=$archiveName; sha256=(Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
    resources=$packed; vanilla_replacements=@(); source_hashes=$hashes
    guard_facts=$guardFacts; enabled_fact=$prefix+'Enabled'; near_fact=$prefix+'Near'
    scene_entry='wilson_default_in'; scene_nodes=@(0,678,224,177,215)
    native_actor='#wilson / wilson / q001_give_weapon'; market='Vendors.wat_lch_gunsmith_01'
    known_limits=@('First runtime test pending','CET development gate at 80m','Actor/trigger registration and trade UI unproven','No transaction/reload result')
}
[IO.File]::WriteAllText((Join-Path $val 'build_manifest.json'),($manifest|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$manifest|ConvertTo-Json -Depth 10
