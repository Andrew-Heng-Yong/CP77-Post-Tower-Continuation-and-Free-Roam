param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly

# One opt-in, mod-owned H10 scene owner. The five earlier manual probes remain
# untouched and cannot be requested while this scene is active.
$vanillaScenePath = Join-Path $WorkspaceRoot 'research\b0_h10_generalization\extracted_interactions\raw\base\quest\minor_quests\mq000\scenes\mq000_01_apartment.scene'
$vanillaPhasePath = Join-Path $WorkspaceRoot 'research\b0_h10_generalization\extracted\raw\base\quest\minor_quests\mq000\phases\mq000_vs_apartment_interactions.questphase'
$basePath = Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase'
$mirrorPhasePath = Join-Path $WorkspaceRoot 'research\b0_mirror_investigation\extracted\raw\base\open_world\scenes\mirrors\mirror_interactions_control.questphase'
$inputs = @($vanillaScenePath,$vanillaPhasePath,$basePath,$mirrorPhasePath)
foreach ($path in $inputs) { if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing reviewed input: $path" } }
$inputHashes = @{}
foreach ($path in $inputs) { $inputHashes[$path] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash }
$src = Join-Path $WorkspaceRoot 'archive\b0_h10_persistent\source'
$out = Join-Path $WorkspaceRoot 'build\B0_H10_Persistent'
$val = Join-Path $WorkspaceRoot 'research\b0_h10_persistent\validation'
New-Item -ItemType Directory -Force -Path $src,$out,$val | Out-Null
$archiveName = 'TowerContinued_B0_H10_Persistent.archive'
$sceneDepot = 'towercontinued\b0_h10_persistent\h10_interactions.scene'
$gateDepot = 'towercontinued\b0_h10_persistent\h10_owner.questphase'

$scene = Read-Cr2wFile $vanillaScenePath
$script:sceneNodes = $scene.RootChunk.SceneGraph.Chunk.Graph
function SceneNode([int]$id) {
    $matches = @($script:sceneNodes | Where-Object { $_.Chunk.NodeId.Id.ToString() -eq "$id" })
    if ($matches.Count -ne 1) { throw "Scene node $id is not unique" }
    return $matches[0].Chunk
}
function EditDest([int]$id,[int]$socket,[int]$from,[int]$to) {
    $ds = (SceneNode $id).OutputSockets[$socket].Destinations
    $matches = @($ds | Where-Object { $_.NodeId.Id.ToString() -eq "$from" })
    if ($matches.Count -ne 1) { throw "Expected one scene edge $id/$socket->$from" }
    $matches[0].NodeId.Id = [WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]$to)
}
function DropDest([int]$id,[int]$socket,[int]$target) {
    $ds = (SceneNode $id).OutputSockets[$socket].Destinations
    $indices = @(for ($i=0; $i -lt $ds.Count; $i++) { if ($ds[$i].NodeId.Id.ToString() -eq "$target") { $i } })
    if ($indices.Count -ne 1) { throw "Expected one removable scene edge $id/$socket->$target" }
    $ds.RemoveAt($indices[0])
}
function SetDests([int]$id,[int]$socket,[int[]]$targets) {
    $ds = (SceneNode $id).OutputSockets[$socket].Destinations
    if ($ds.Count -lt 1) { throw "No template edge at $id/$socket" }
    $template = $ds[0].DeepCopy()
    $ds.Clear()
    foreach ($target in $targets) {
        $edge = $template.DeepCopy()
        $edge.NodeId.Id = [WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]$target)
        $ds.Add($edge)
    }
}
function SetDestOrdinal([int]$id,[int]$socket,[int]$target,[int]$ordinal) {
    $ds = (SceneNode $id).OutputSockets[$socket].Destinations
    $matches = @($ds | Where-Object { $_.NodeId.Id.ToString() -eq "$target" })
    if ($matches.Count -ne 1) { throw "Expected one stamp edge $id/$socket->$target" }
    $matches[0].IsockStamp.Ordinal = [WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]$ordinal)
}
function SetChoiceUnconditional([int]$id) {
    $choice = SceneNode $id
    if ($choice.GetType().Name -ne 'scnChoiceNode' -or $choice.Options.Count -ne 1 -or $null -eq $choice.Options[0].QuestCondition) {
        throw "Expected one conditional choice at $id"
    }
    $choice.Options[0].QuestCondition = $null
}

# Vanilla's single apartment entry reaches hub 215, which owns all five
# physical choices. Remove the old story/partner start streams and add only
# the already tested outside-H10 idle exit monitor.
SetDests 1 0 @(215,1112)
SetDestOrdinal 1 0 1112 1
EditDest 1112 0 1109 2
SetDestOrdinal 1112 0 2 0

# V-only mirror: keep native V workspot, mirror device, variant and cleanup;
# omit q101/MQ055/Johnny while retaining the locally audited appearance
# menu and facial-expression branches.
EditDest 220 0 1586 386
# Vanilla 222 -> 1418 eventually enters both 1246 (appearance/facial
# choices) and 1270 (the Stop looking chooser). The old MQ055/Johnny
# condition chain at 1418/1156 is inappropriate after Tower. Feed both
# native local choice nodes directly; input stamp 0 is the executable In
# route, unlike the name-1 choice-attachment edges from node 226.
SetDests 222 0 @(1246,1270)
SetDestOrdinal 222 0 1246 0
SetDestOrdinal 222 0 1270 0
DropDest 220 0 1624
EditDest 226 0 1000 397
DropDest 1051 0 1414
# Do not write old mq000 hairdresser history on a post-Tower save. The menu
# opens directly after the native appearance-choice hub and delay.
EditDest 1250 0 1325 1329
# The ordinary mirror root sets mirror_interactions_facials globally, but
# that old owner is gone here. Scope the five facial choices to this scene
# without forcing a global fact that affects unrelated mirrors.
$facialChoice = SceneNode 1125
if ($facialChoice.GetType().Name -ne 'scnChoiceNode' -or $facialChoice.Options.Count -ne 6) {
    throw 'Vanilla H10 facial choice shape changed'
}
for ($i=0; $i -lt 5; $i++) {
    $condition = $facialChoice.Options[$i].QuestCondition
    if ($null -eq $condition -or $condition.Chunk.Type.Chunk.FactName.ToString() -ne 'mirror_interactions_facials') {
        throw "Expected mirror-interactions facial fact gate at option $i"
    }
    $facialChoice.Options[$i].QuestCondition = $null
}
DropDest 242 0 1084
# The previous prompt-loop did not visibly rearm on a second mirror use.
# End only after vanilla's normal Leave cleanup, then restart the single
# apartment scene via the native one-second delayed owner loop.
EditDest 242 0 509 2
SetDestOrdinal 242 0 2 0

# Shower: preserve native water/workspot/effect/cleanup, but do not touch
# the persistent clothing stash or old MQ055/q101/blood-shower branch.
DropDest 47 0 1163
EditDest 51 0 1404 193
SetDestOrdinal 51 0 193 0
DropDest 202 0 1173

# Sleep: preserve menu and normal bed cleanup, omit old MQ055 history write
# and its incompatible post-action branch. Restrictions/profile balancing
# remain a separate validation gate.
SetChoiceUnconditional 6
DropDest 6 0 1591
EditDest 1353 0 1469 22
SetDestOrdinal 1353 0 22 0
EditDest 24 0 501 6

# Sofa/TV and wardrobe: retain native action/cleanup loops, not the old
# Johnny/MQ055 choice gate or old wardrobe-history writer.
SetChoiceUnconditional 328
DropDest 1345 0 1428

$expectedProps = @('shower','tv_lookat')
$actualProps = @($scene.RootChunk.Props | ForEach-Object { $_.PropName.ToString() } | Sort-Object)
if (@(Compare-Object $expectedProps $actualProps).Count) { throw 'Vanilla scene prop inventory changed' }
foreach ($prop in $scene.RootChunk.Props) { $prop.SpawnDespawnParams.SpawnOnStart = $true }
foreach ($actor in $scene.RootChunk.Actors) {
    if ($actor.SpawnDespawnParams.SpawnOnStart.ToString() -ne 'False') { throw "Unexpected actor spawn-on-start: $($actor.ActorName)" }
}
$scenePath = Join-Path $src $sceneDepot
Write-Cr2wFile $scene $scenePath
Export-Cr2wJson (Read-Cr2wFile $scenePath) (Join-Path $val 'h10_interactions.scene.json')

$vanillaPhase = Read-Cr2wFile $vanillaPhasePath
$base = Read-Cr2wFile $basePath
$mirrorPhase = Read-Cr2wFile $mirrorPhasePath
$pauseTemplate = Get-QuestNode $base.RootChunk.Graph.Chunk 106
$sceneTemplate = Get-QuestNode $vanillaPhase.RootChunk.Graph.Chunk 2
$mirrorLeaf = (Get-QuestNode (Get-QuestNode $mirrorPhase.RootChunk.Graph.Chunk 42).PhaseGraph.Chunk 12).PhaseGraph.Chunk
$delayTemplate = Get-QuestNode $mirrorLeaf 4
if ($delayTemplate.Condition.Chunk.GetType().Name -ne 'questTimeCondition') { throw 'Expected vanilla one-second delay changed' }
$h10Gate = (Get-QuestNode $vanillaPhase.RootChunk.Graph.Chunk 19).Condition.Chunk
$h10Trigger = @($h10Gate.Conditions | Where-Object { $_.Chunk.GetType().Name -eq 'questTriggerCondition' })
$noIncomingCall = @($h10Gate.Conditions | Where-Object { $_.Chunk.GetType().Name -eq 'questUICondition' })
if ($h10Trigger.Count -ne 1 -or $noIncomingCall.Count -ne 1) { throw 'Vanilla H10 context gate changed' }
$prefix = 'PTFRB0H10P_'
$guardFacts = [ordered]@{
    PostTowerFreeRoamActive=1; PTFRP0_DR13=1; q307_active=0; q307_done=1;
    q307_finished=1; q307_2079=1; q307_main_game_killed=1;
    q305_johnny_scene_active=0; apartment_on=1; interior_manager_on=0;
    PTFRB0H10_Claimed=1; PTFRB0H10_OwnerEntered=1;
    PTFRB0H10L_Claimed=1; PTFRB0H10L_OwnerEntered=1;
    PTFRB0H10A_E_Claimed=1; PTFRB0H10A_E_OwnerEntered=1;
    PTFRB0H10A_B_Claimed=1; PTFRB0H10A_B_OwnerEntered=1;
    PTFRB0H10A_W_Claimed=1; PTFRB0H10A_W_OwnerEntered=1;
    PTFRB0H10M_Active=0;
    PTFRB0H10I_M_Active=0; PTFRB0H10I_H_Active=0;
    PTFRB0H10I_B_Active=0; PTFRB0H10I_S_Active=0;
    PTFRB0H10I_W_Active=0;
    PTFRB0H10P_Enabled=1; PTFRB0H10P_Interrupted=0
}
$condition = [WolvenKit.RED4.Types.questLogicalCondition]::new()
$condition.Operation = [WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
foreach ($fact in $guardFacts.Keys) {
    Add-RedHandle $condition.Conditions (New-FactCondition $fact $guardFacts[$fact] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
}
Add-RedHandle $condition.Conditions $h10Trigger[0].Chunk.DeepCopy()
Add-RedHandle $condition.Conditions $noIncomingCall[0].Chunk.DeepCopy()
$graph = [WolvenKit.RED4.Types.questGraphDefinition]::new()
function Put($node) { Add-RedHandle $graph.Nodes $node }
function Link($from,$socket,$to,$dest='In') {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $from) $socket) (Get-QuestSocket (Get-QuestNode $graph $to) $dest))
}
Put (New-InputNode 0 'In1')
Put (New-SetFactNode 1 ($prefix+'Ready') 1)
$wait = $pauseTemplate.DeepCopy(); $wait.Id = [uint16]2
foreach ($socket in $wait.Sockets) { $socket.Chunk.Connections.Clear() }
Set-RedHandleProperty $wait Condition $condition
Put $wait
Put (New-SetFactNode 3 ($prefix+'Active') 1)
$sceneNode = $sceneTemplate.DeepCopy(); $sceneNode.Id = [uint16]4
foreach ($socket in $sceneNode.Sockets) { $socket.Chunk.Connections.Clear() }
$resourcePath = [WolvenKit.RED4.Types.ResourcePath]::op_Implicit($sceneDepot)
$sceneNode.SceneFile = [Activator]::CreateInstance($sceneNode.GetType().GetProperty('SceneFile').PropertyType,[object[]]@($resourcePath))
Put $sceneNode
Put (New-SetFactNode 5 ($prefix+'Active') 0)
Put (New-SetFactNode 6 ($prefix+'Completed') 1)
$delay = $delayTemplate.DeepCopy(); $delay.Id = [uint16]7
foreach ($socket in $delay.Sockets) { $socket.Chunk.Connections.Clear() }
Put $delay
Put (New-SetFactNode 8 ($prefix+'Interrupted') 1)
Put (New-SetFactNode 9 ($prefix+'Active') 0)
Link 0 Out 1; Link 1 Out 2; Link 2 Out 3; Link 3 Out 4 in
Link 4 out 5; Link 5 Out 6; Link 6 Out 7; Link 7 Out 2
Link 4 'Default INT' 8; Link 8 Out 9
$root = [WolvenKit.RED4.Types.questQuestPhaseResource]::new()
$root.CookingPlatform = [WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
Set-RedHandleProperty $root Graph $graph
$gate = [WolvenKit.RED4.Archive.CR2W.CR2WFile]::new(); $gate.RootChunk = $root
$gatePath = Join-Path $src $gateDepot
Write-Cr2wFile $gate $gatePath
Export-Cr2wJson (Read-Cr2wFile $gatePath) (Join-Path $val 'h10_owner.questphase.json')

foreach ($path in $inputs) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $inputHashes[$path]) { throw "Reviewed input changed during build: $path" }
}
$allowed = @($sceneDepot,$gateDepot) | Sort-Object
$actual = @(Get-ChildItem -LiteralPath $src -File -Recurse | ForEach-Object { [IO.Path]::GetRelativePath($src,$_.FullName) } | Sort-Object)
if (@(Compare-Object $allowed $actual).Count) { throw 'Unexpected source file in persistent H10 archive' }
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
if (@(Compare-Object $allowed $packed).Count) { throw 'Archive manifest mismatch' }
foreach ($entry in $archive.Files.Values) {
    $memory = [IO.MemoryStream]::new()
    try {
        $entry.Extract($memory)
        $hash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray()))
        if ($hash -ne (Get-FileHash -LiteralPath (Join-Path $src $entry.Name) -Algorithm SHA256).Hash) { throw "Packed bytes differ: $($entry.Name)" }
    } finally { $memory.Dispose() }
}
$manifest = [ordered]@{
    status = 'EXPERIMENTAL_OPT_IN_REARM_DISPOSABLE_ONLY'
    archive = $archiveName
    sha256 = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
    resources = $packed
    source_hashes = $inputHashes
    guard_facts = $guardFacts
    vanilla_replacements = @()
    enable_fact = $prefix+'Enabled'
    known_limits = @('Full mirror appearance/facial routes statically restored but not live-tested','Active-action forced exit/interruption cleanup unvalidated','Shower remains clothed','Sleep effects not yet balanced for Tower restriction profiles','Phase 5 post-Tower ownership entitlement not implemented')
}
[IO.File]::WriteAllText((Join-Path $val 'build_manifest.json'),($manifest | ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$manifest | ConvertTo-Json -Depth 10
