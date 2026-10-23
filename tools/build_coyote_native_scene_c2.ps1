param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly

$src = Join-Path $WorkspaceRoot 'archive\b0_coyote_native_scene_c2\source'
$out = Join-Path $WorkspaceRoot 'build\Coyote_NativeScene_C2'
$val = Join-Path $WorkspaceRoot 'research\b0_second_mirror\validation_c2'
$gateDepot = 'towercontinued\coyote_native_scene_c2\gate.questphase'
$ownerDepot = 'towercontinued\coyote_native_scene_c2\owner.questphase'
$sceneDepot = 'towercontinued\coyote_native_scene_c2\scene.scene'
$archiveName = 'TowerContinued_Coyote_NativeScene_C2.archive'
$prefix = 'PTFRCM2_'
$fullTrigger = '$/03_night_city/#c_heywood/glen/loc_sq022_el_coyote_cojo_bar_prefabKDIAKFA/loc_sq022_el_coyote_cojo_bar_openworld_prefabOM4ONAY/#mirror_scene_el_cojote/#mirror_tr_cojote'
$mirrorPath = Join-Path $WorkspaceRoot 'research\b0_mirror_investigation\extracted\raw\base\open_world\scenes\mirrors\mirror_interactions_control.questphase'
$basePath = Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase'
$parentPath = Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\ep1.quest'
$sectorPath = Join-Path $WorkspaceRoot 'research\b0_second_mirror\vanilla\raw\base\worlds\03_night_city\_compiled\default\quest_9573f8e982c17cb0.streamingsector'
$vanillaScenePath = Join-Path $WorkspaceRoot 'research\b0_second_mirror\vanilla\raw\base\open_world\scenes\mirrors\mirror_scene_el_cojote.scene'
$hashes = @{}
foreach ($path in @($mirrorPath,$basePath,$parentPath,$sectorPath,$vanillaScenePath)) {
    $hashes[$path] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
}
$mirror = Read-Cr2wFile $mirrorPath
$base = Read-Cr2wFile $basePath
$parent = Read-Cr2wFile $parentPath
$sector = Read-Cr2wFile $sectorPath
$sceneFile = Read-Cr2wFile $vanillaScenePath
if ($sector.RootChunk.Nodes.Count -ne 1 -or $sector.RootChunk.Nodes[0].Chunk.GetType().Name -ne 'worldTriggerAreaNode' -or
    $sector.RootChunk.NodeData.Data[0].QuestPrefabRefHash.ToString() -ne $fullTrigger) {
    throw 'Reviewed single-trigger Coyote sector changed'
}
$prefab = @($mirror.RootChunk.PhasePrefabs | Where-Object {$_.PrefabNodeRef.ToString() -eq '#mirror_scene_el_cojote'})
if ($prefab.Count -ne 1) { throw 'Coyote prefab entry is not unique' }
$outer = (Get-QuestNode $mirror.RootChunk.Graph.Chunk 42).PhaseGraph.Chunk
$leaf = (Get-QuestNode $outer 48).PhaseGraph.Chunk
$nativeEntry = (Get-QuestNode $leaf 3).Condition.Chunk.DeepCopy()
if ($nativeEntry.GetType().Name -ne 'questTriggerCondition' -or $nativeEntry.Type.ToString() -ne 'IsInside' -or
    $nativeEntry.TriggerAreaRef.ToString() -ne '#mirror_tr_cojote') { throw 'Vanilla Coyote entry changed' }
$nativeEntry.TriggerAreaRef = [WolvenKit.RED4.Types.NodeRef]::op_Implicit($fullTrigger)
$templateScene = Get-QuestNode $leaf 2
$templateDelay = Get-QuestNode $leaf 4
if ($templateScene.SceneLocation.NodeRef.ToString() -ne '#mirror_sm_scene_el_cojote' -or
    $templateScene.SceneFile.DepotPath.ToString() -ne 'base\open_world\scenes\mirrors\mirror_scene_el_cojote.scene' -or
    $templateDelay.Condition.Chunk.Type.Chunk.Seconds.ToString() -ne '1') {
    throw 'Coyote scene marker or rearm precedent changed'
}
$exit = @($sceneFile.RootChunk.SceneGraph.Chunk.Graph | Where-Object {$_.Chunk.NodeId.Id.ToString() -eq '4395'})
if ($exit.Count -ne 1 -or $exit[0].Chunk.QuestNode.Chunk.Condition.Chunk.GetType().Name -ne 'questTriggerCondition' -or
    $exit[0].Chunk.QuestNode.Chunk.Condition.Chunk.Type.ToString() -ne 'IsOutside' -or
    $exit[0].Chunk.QuestNode.Chunk.Condition.Chunk.TriggerAreaRef.ToString() -ne '#mirror_tr_cojote') {
    throw 'Coyote scene exit precedent changed'
}
# The one source-scene edit: make its relative exit NodeRef resolve from this mod-owned phase.
$exit[0].Chunk.QuestNode.Chunk.Condition.Chunk.TriggerAreaRef = [WolvenKit.RED4.Types.NodeRef]::op_Implicit($fullTrigger)
$combat = (Get-QuestNode $outer 57).Condition.Chunk.DeepCopy()
if ($combat.Type.Chunk.GetType().Name -ne 'questCharacterCombat_ConditionType') { throw 'Vanilla combat guard changed' }
$combat.Type.Chunk.Inverted = $true
$pauseTemplate = Get-QuestNode $base.RootChunk.Graph.Chunk 106
New-Item -ItemType Directory -Force -Path $src,$out,$val | Out-Null
function Put($graph,$node) { Add-RedHandle $graph.Nodes $node }
function Link($graph,$from,$socket,$to,$dest='In') {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $from) $socket) (Get-QuestSocket (Get-QuestNode $graph $to) $dest))
}
function Count($id,$name) {
    $node = New-SetFactNode $id ($prefix+$name) 1
    $node.Type.Chunk.SetExactValue = $false
    return $node
}
function Pause($id,$condition) {
    $node = $pauseTemplate.DeepCopy(); $node.Id = [uint16]$id
    foreach ($socket in $node.Sockets) { $socket.Chunk.Connections.Clear() }
    Set-RedHandleProperty $node Condition $condition
    return $node
}
function PhaseFile($graph) {
    $root = [WolvenKit.RED4.Types.questQuestPhaseResource]::new()
    $root.CookingPlatform = [WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
    Set-RedHandleProperty $root Graph $graph
    $file = [WolvenKit.RED4.Archive.CR2W.CR2WFile]::new(); $file.RootChunk = $root
    return $file
}
$guardFacts = [ordered]@{
    PostTowerFreeRoamActive=1; PTFRP0_DR13=1; q307_active=0; q307_done=1
    q307_finished=1; q307_2079=1; q307_main_game_killed=1
    q305_johnny_scene_active=0; mirror_interaction_disabled=0; q115_point_of_no_return=0
    PTFRCM1_Requested=0; PTFRCM2_Requested=1; PTFRCM2_Interrupted=0
}
function Guard([bool]$includeEntry) {
    $condition = [WolvenKit.RED4.Types.questLogicalCondition]::new()
    $condition.Operation = [WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
    foreach ($fact in $guardFacts.Keys) {
        Add-RedHandle $condition.Conditions (New-FactCondition $fact $guardFacts[$fact] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
    }
    if ($includeEntry) { Add-RedHandle $condition.Conditions $nativeEntry.DeepCopy() }
    Add-RedHandle $condition.Conditions $combat.DeepCopy()
    return $condition
}
$gate = [WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $gate (New-InputNode 0 'In1')
Put $gate (Count 1 'Boot')
Put $gate (Pause 2 (Guard $false))
Put $gate (Count 3 'Guard')
$child = [WolvenKit.RED4.Types.questPhaseNodeDefinition]::new(); $child.Id = [uint16]4
$rp = [WolvenKit.RED4.Types.ResourcePath]::op_Implicit($ownerDepot)
$child.PhaseResource = [Activator]::CreateInstance($child.GetType().GetProperty('PhaseResource').PropertyType,[object[]]@($rp))
[void](New-QuestSocket $child 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
[void](New-QuestSocket $child 'In1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
Put $gate $child
Link $gate 0 Out 1; Link $gate 1 Out 2; Link $gate 2 Out 3; Link $gate 3 Out 4 In1
$gateFile = PhaseFile $gate

$owner = [WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $owner (New-InputNode 0 'In1')
Put $owner (New-SetFactNode 1 ($prefix+'Ready') 1)
Put $owner (Pause 2 (Guard $true))
Put $owner (New-SetFactNode 3 ($prefix+'Active') 1)
$sceneNode = $templateScene.DeepCopy(); $sceneNode.Id = [uint16]4
foreach ($socket in $sceneNode.Sockets) { $socket.Chunk.Connections.Clear() }
$sceneResource = [WolvenKit.RED4.Types.ResourcePath]::op_Implicit($sceneDepot)
$sceneNode.SceneFile = [Activator]::CreateInstance($sceneNode.GetType().GetProperty('SceneFile').PropertyType,[object[]]@($sceneResource))
Put $owner $sceneNode
Put $owner (New-SetFactNode 5 ($prefix+'Active') 0)
Put $owner (New-SetFactNode 6 ($prefix+'Completed') 1)
$delay = $templateDelay.DeepCopy(); $delay.Id = [uint16]7
foreach ($socket in $delay.Sockets) { $socket.Chunk.Connections.Clear() }
Put $owner $delay
Put $owner (New-SetFactNode 8 ($prefix+'Interrupted') 1)
Put $owner (New-SetFactNode 9 ($prefix+'Active') 0)
Put $owner (Count 10 'SceneRequests')
Put $owner (Count 11 'SceneReturns')
Put $owner (Count 12 'Rearms')
Link $owner 0 Out 1; Link $owner 1 Out 2; Link $owner 2 Out 3; Link $owner 3 Out 10
Link $owner 10 Out 4 mirror_interaction
Link $owner 4 mirror_interaction_out 5; Link $owner 5 Out 11; Link $owner 11 Out 6
Link $owner 6 Out 7; Link $owner 7 Out 12; Link $owner 12 Out 2
Link $owner 4 'Default INT' 8; Link $owner 8 Out 9
$ownerFile = PhaseFile $owner
$ownerFile.RootChunk.PhasePrefabs.Add($prefab[0].DeepCopy())

Write-Cr2wFile $gateFile (Join-Path $src $gateDepot)
Write-Cr2wFile $ownerFile (Join-Path $src $ownerDepot)
Write-Cr2wFile $sceneFile (Join-Path $src $sceneDepot)
$expected = @($gateDepot,$ownerDepot,$sceneDepot) | Sort-Object
$actual = @(Get-ChildItem -LiteralPath $src -Recurse -File | ForEach-Object {[IO.Path]::GetRelativePath($src,$_.FullName)} | Sort-Object)
if (@(Compare-Object $expected $actual).Count) { throw 'Unexpected source resources' }
foreach ($entry in @(@{name='gate';path=$gateDepot;count=5;prefabs=0},@{name='owner';path=$ownerDepot;count=13;prefabs=1})) {
    $file = Read-Cr2wFile (Join-Path $src $entry.path)
    Export-Cr2wJson $file (Join-Path $val ($entry.name+'.json'))
    if ($file.RootChunk.Graph.Chunk.Nodes.Count -ne $entry.count -or $file.RootChunk.PhasePrefabs.Count -ne $entry.prefabs -or
        $file.EmbeddedFiles.Count -or $file.RootChunk.InplacePhases.Count) { throw 'Unexpected graph scope' }
    foreach ($handle in $file.RootChunk.Graph.Chunk.Nodes) {
        $node = $handle.Chunk
        if ($node.GetType().Name -eq 'questFactsDBManagerNodeDefinition' -and
            -not $node.Type.Chunk.FactName.ToString().StartsWith($prefix)) { throw 'Non-probe fact writer found' }
    }
}
$sceneCheck = Read-Cr2wFile (Join-Path $src $sceneDepot)
Export-Cr2wJson $sceneCheck (Join-Path $val 'scene.json')
$checkExit = @($sceneCheck.RootChunk.SceneGraph.Chunk.Graph | Where-Object {$_.Chunk.NodeId.Id.ToString() -eq '4395'})
if ($sceneCheck.RootChunk.SceneGraph.Chunk.Graph.Count -ne 37 -or $checkExit.Count -ne 1 -or
    $checkExit[0].Chunk.QuestNode.Chunk.Condition.Chunk.TriggerAreaRef.ToString() -ne $fullTrigger) {
    throw 'Round-trip Coyote scene exit differs'
}
foreach ($path in $hashes.Keys) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $hashes[$path]) { throw "Research input changed: $path" }
}
$crc = 65535
foreach ($byte in [Text.Encoding]::UTF8.GetBytes($gateDepot+':1')) {
    $x = ($crc -shr 8) -bxor $byte; $x = $x -bxor ($x -shr 4)
    $crc = (($crc -shl 8) -bxor ($x -shl 12) -bxor ($x -shl 5) -bxor $x) -band 65535
}
if (@($parent.RootChunk.Graph.Chunk.Nodes | Where-Object {$_.Chunk.Id.ToString() -eq "$crc"}).Count) { throw 'ArchiveXL node ID collision with EP1' }
$hashService = [WolvenKit.Common.Services.HashService]::new(); $hashService.Load()
$archivePath = Join-Path $out $archiveName
$stream = [IO.File]::Create($archivePath)
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService,[WolvenKit.SerilogWrapper]::new())
    if (-not $writer.WriteArchive([IO.DirectoryInfo]::new($src),$stream)) { throw 'Archive write failed' }
} finally { $stream.Dispose() }
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new(); $archive = $null
if ($reader.ReadArchive($archivePath,$hashService,[ref]$archive).ToString() -ne 'NoError') { throw 'Archive reopen failed' }
$packed = @($archive.Files.Values | ForEach-Object {$_.Name} | Sort-Object)
if (@(Compare-Object $expected $packed).Count) { throw 'Archive manifest mismatch' }
foreach ($file in $archive.Files.Values) {
    $memory = [IO.MemoryStream]::new()
    try {
        $file.Extract($memory)
        if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray())) -ne
            (Get-FileHash -LiteralPath (Join-Path $src $file.Name) -Algorithm SHA256).Hash) { throw 'Packed bytes differ' }
    } finally { $memory.Dispose() }
}
Copy-Item -LiteralPath (Join-Path $WorkspaceRoot ('archive\b0_coyote_native_scene_c2\'+$archiveName+'.xl')) -Destination (Join-Path $out ($archiveName+'.xl'))
$manifest = [ordered]@{
    status='WORKSPACE_ONLY_UNINSTALLED'; archive=$archiveName
    sha256=(Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
    resources=$packed; registration_id=$crc; trigger=$fullTrigger; guard_facts=$guardFacts
    prefab='#mirror_scene_el_cojote'; scene_exit_patch='4395: relative #mirror_tr_cojote -> reviewed full NodeRef'
    vanilla_replacements=@(); runtime_writes='PTFRCM2_* facts only'; source_hashes=$hashes
}
[IO.File]::WriteAllText((Join-Path $val 'build_manifest.json'),($manifest | ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$manifest | ConvertTo-Json -Depth 6
