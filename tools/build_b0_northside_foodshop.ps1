param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly

# Single Northside food shop, opt-in on a disposable save. The original
# Northside root also initializes other merchants and is never started here.
$vendorPath = Join-Path $WorkspaceRoot 'research\b0_vendor_rollout\regional_sources\raw\base\open_world\vendors\watson\northside\northside_vendors.questphase'
$basePath = Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase'
$scenePath = Join-Path $WorkspaceRoot 'research\b0_vendor_rollout\regional_scene_sources\raw\base\open_world\vendors\watson\northside\wat_nid_foodshop_01\wat_nid_foodshop_01.scene'
$inputs = @($vendorPath, $basePath, $scenePath)
foreach ($path in $inputs) { if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing reviewed input: $path" } }
$inputHashes = @{}
foreach ($path in $inputs) { $inputHashes[$path] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash }

$src = Join-Path $WorkspaceRoot 'archive\b0_northside_foodshop\source'
$out = Join-Path $WorkspaceRoot 'build\B0_Northside_Foodshop'
$val = Join-Path $WorkspaceRoot 'research\b0_northside_foodshop\validation'
New-Item -ItemType Directory -Force -Path $src,$out,$val | Out-Null
$phaseDepot = 'towercontinued\b0_northside_foodshop\vendor_owner.questphase'
$archiveName = 'TowerContinued_B0_Northside_Foodshop.archive'
$prefix = 'PTFRB0NIDF_'

$vendor = Read-Cr2wFile $vendorPath
$base = Read-Cr2wFile $basePath
$regional = $vendor.RootChunk.Graph.Chunk
$foodshop = (Get-QuestNode $regional 2).PhaseGraph.Chunk
$distanceTemplate = Get-QuestNode $foodshop 15
$phaseTemplate = Get-QuestNode $foodshop 8
if ($distanceTemplate.GetType().Name -ne 'questPauseConditionNodeDefinition' -or
    $distanceTemplate.Condition.Chunk.GetType().Name -ne 'questDistanceCondition' -or
    $distanceTemplate.Condition.Chunk.Type.Chunk.ComparisonType.ToString() -ne 'Less' -or
    $distanceTemplate.Condition.Chunk.Type.Chunk.DistanceDefinition2.Chunk.DistanceValue.ToString() -ne '50' -or
    $phaseTemplate.GetType().Name -ne 'questPhaseNodeDefinition') { throw 'Northside proximity owner changed' }
$inner = $phaseTemplate.PhaseGraph.Chunk
$spawnIn = Get-QuestNode $inner 5
$spawnOut = Get-QuestNode $inner 6
$scene = Get-QuestNode $inner 2
$far = Get-QuestNode $inner 7
if ($spawnIn.Actions.Count -ne 1 -or $spawnOut.Actions.Count -ne 1 -or
    $spawnIn.Actions[0].Type.Chunk.Action.ToString() -ne 'Activate' -or
    $spawnOut.Actions[0].Type.Chunk.Action.ToString() -ne 'Deactivate' -or
    $spawnIn.Actions[0].Type.Chunk.Reference.ToString() -ne '#wat_nid_foodshop_01' -or
    $spawnOut.Actions[0].Type.Chunk.Reference.ToString() -ne '#wat_nid_foodshop_01' -or
    $spawnIn.Actions[0].Type.Chunk.EntryName.ToString() -ne 'wat_nid_foodshop_01' -or
    $spawnOut.Actions[0].Type.Chunk.EntryName.ToString() -ne 'wat_nid_foodshop_01' -or
    $scene.SceneFile.DepotPath.ToString() -ne 'base\open_world\vendors\watson\northside\wat_nid_foodshop_01\wat_nid_foodshop_01.scene' -or
    $scene.SceneLocation.NodeRef.ToString() -ne '#wat_sm_nid_foodshop_01' -or
    $far.Condition.Chunk.Type.Chunk.ComparisonType.ToString() -ne 'Greater') {
    throw 'Northside spawn, scene or departure leaf changed'
}

$guardFacts = [ordered]@{
    PostTowerFreeRoamActive=1; PTFRP0_DR13=1; q307_active=0; q307_done=1;
    q307_finished=1; q307_2079=1; q307_main_game_killed=1;
    q305_johnny_scene_active=0; q115_point_of_no_return=0;
    wat_nid_foodshop_01_default_on=1; PTFRB0NIDF_Enabled=1
}
$condition = [WolvenKit.RED4.Types.questLogicalCondition]::new()
$condition.Operation = [WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
foreach ($fact in $guardFacts.Keys) {
    Add-RedHandle $condition.Conditions (New-FactCondition $fact $guardFacts[$fact] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
}
$graph = [WolvenKit.RED4.Types.questGraphDefinition]::new()
function Put($node) { Add-RedHandle $graph.Nodes $node }
function Link($from,$socket,$to,$dest='In') {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $from) $socket) (Get-QuestSocket (Get-QuestNode $graph $to) $dest))
}
Put (New-InputNode 0 'In1')
Put (New-SetFactNode 1 ($prefix+'Ready') 1)
$guard = (Get-QuestNode $base.RootChunk.Graph.Chunk 106).DeepCopy(); $guard.Id = [uint16]2
foreach ($socket in $guard.Sockets) { $socket.Chunk.Connections.Clear() }
Set-RedHandleProperty $guard Condition $condition
Put $guard
$distance = $distanceTemplate.DeepCopy(); $distance.Id = [uint16]3
foreach ($socket in $distance.Sockets) { $socket.Chunk.Connections.Clear() }
Put $distance
Put (New-SetFactNode 4 ($prefix+'Near') 1)
$phase = $phaseTemplate.DeepCopy(); $phase.Id = [uint16]5
foreach ($socket in $phase.Sockets) { $socket.Chunk.Connections.Clear() }
$innerCopy = $phase.PhaseGraph.Chunk
# DeepCopy loses some embedded socket ownership. Reconnect the reviewed route.
foreach ($nodeHandle in $innerCopy.Nodes) {
    foreach ($socket in $nodeHandle.Chunk.Sockets) { $socket.Chunk.Connections.Clear() }
}
Add-RedHandle $innerCopy.Nodes (New-SetFactNode 8 ($prefix+'SpawnActionOut') 1)
Add-RedHandle $innerCopy.Nodes (New-SetFactNode 9 ($prefix+'ActorDistanceGate') 1)
Add-RedHandle $innerCopy.Nodes (New-SetFactNode 10 ($prefix+'ExitWatchArmed') 1)
Add-RedHandle $innerCopy.Nodes (New-SetFactNode 11 ($prefix+'DespawnActionOut') 1)
$farWait = Get-QuestNode $innerCopy 7
Set-RedHandleProperty $farWait Condition (New-FactCondition ($prefix+'Far') 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
function LinkInner($from,$socket,$to,$dest='In') {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $innerCopy $from) $socket) (Get-QuestSocket (Get-QuestNode $innerCopy $to) $dest))
}
LinkInner 0 Out 5; LinkInner 0 Out 10; LinkInner 10 Out 7
LinkInner 5 Out 8; LinkInner 8 Out 3
LinkInner 3 Out 9; LinkInner 9 Out 2 wat_nid_foodshop_01_start
LinkInner 7 Out 6; LinkInner 6 Out 11; LinkInner 11 Out 1
Put $phase
Put (New-SetFactNode 6 ($prefix+'Departed') 1)
Put (New-SetFactNode 7 ($prefix+'Near') 0)
$rearm = (Get-QuestNode $base.RootChunk.Graph.Chunk 106).DeepCopy(); $rearm.Id = [uint16]8
foreach ($socket in $rearm.Sockets) { $socket.Chunk.Connections.Clear() }
Set-RedHandleProperty $rearm Condition (New-FactCondition ($prefix+'Far') 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
Put $rearm
Link 0 Out 1; Link 1 Out 2; Link 2 Out 3; Link 3 Out 4; Link 4 Out 5 In1
Link 5 Out1 6; Link 6 Out 7; Link 7 Out 8; Link 8 Out 3

$root = [WolvenKit.RED4.Types.questQuestPhaseResource]::new()
$root.CookingPlatform = [WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
Set-RedHandleProperty $root Graph $graph
$resource = [WolvenKit.RED4.Archive.CR2W.CR2WFile]::new(); $resource.RootChunk = $root
$phasePath = Join-Path $src $phaseDepot
Write-Cr2wFile $resource $phasePath
Export-Cr2wJson (Read-Cr2wFile $phasePath) (Join-Path $val 'vendor_owner.questphase.json')
foreach ($path in $inputs) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $inputHashes[$path]) { throw "Reviewed input changed during build: $path" }
}
$actual = @(Get-ChildItem -LiteralPath $src -File -Recurse | ForEach-Object { [IO.Path]::GetRelativePath($src,$_.FullName) })
if ($actual.Count -ne 1 -or $actual[0] -ne $phaseDepot) { throw 'Unexpected one-site source manifest' }
$hashService = [WolvenKit.Common.Services.HashService]::new(); $hashService.Load()
$archivePath = Join-Path $out $archiveName
$stream = [IO.File]::Create($archivePath)
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService,[WolvenKit.SerilogWrapper]::new())
    if (-not $writer.WriteArchive([IO.DirectoryInfo]::new($src),$stream)) { throw 'Archive write failed' }
} finally { $stream.Dispose() }
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new(); $archive = $null
if ($reader.ReadArchive($archivePath,$hashService,[ref]$archive).ToString() -ne 'NoError') { throw 'Archive did not reopen' }
$packed = @($archive.Files.Values | ForEach-Object { $_.Name })
if ($packed.Count -ne 1 -or $packed[0] -ne $phaseDepot) { throw 'Archive manifest mismatch' }
$memory = [IO.MemoryStream]::new()
try {
    $archive.Files.Values | ForEach-Object { $_.Extract($memory) }
    if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray())) -ne
        (Get-FileHash -LiteralPath $phasePath -Algorithm SHA256).Hash) { throw 'Packed bytes differ' }
} finally { $memory.Dispose() }
$manifest = [ordered]@{
    status='STATIC_EXPERIMENTAL_NOT_INSTALLED'
    archive=$archiveName
    sha256=(Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
    resources=$packed
    source_hashes=$inputHashes
    guard_facts=$guardFacts
    vanilla_replacements=@()
    enable_fact=$prefix+'Enabled'
    known_limits=@('One Northside food vendor actor and scene only','Far exit uses a development distance flag','Duplicate ownership requires live observation','Transaction and save/reload unproven')
}
[IO.File]::WriteAllText((Join-Path $val 'build_manifest.json'),($manifest | ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$manifest | ConvertTo-Json -Depth 10
