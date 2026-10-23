param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly

$src = Join-Path $WorkspaceRoot 'archive\b0_afterlife_native_scene_a2\source'
$out = Join-Path $WorkspaceRoot 'build\Afterlife_NativeScene_A2'
$val = Join-Path $WorkspaceRoot 'research\b0_afterlife_native_audit\validation_a2'
$gateDepot = 'towercontinued\afterlife_native_scene_a2\gate.questphase'
$ownerDepot = 'towercontinued\afterlife_native_scene_a2\owner.questphase'
$sceneDepot = 'towercontinued\afterlife_native_scene_a2\scene.scene'
$archiveName = 'TowerContinued_Afterlife_NativeScene_A2.archive'
$prefix = 'PTFRALMA2_'
$fullTrigger = '$/03_night_city/c_watson/little_china/#loc_q103_afterlife/#loc_q103_afterlife_openworld/#mirror_scene_afterlife/#mirror_tr_afterlife'
$mirrorPath = Join-Path $WorkspaceRoot 'research\b0_mirror_investigation\extracted\raw\base\open_world\scenes\mirrors\mirror_interactions_control.questphase'
$basePath = Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase'
$parentPath = Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\ep1.quest'
$v7OwnerPath = Join-Path $WorkspaceRoot 'archive\b0_afterlife_mirror_v7\source\towercontinued\b0_afterlife_mirror\afterlife_mirror_owner.questphase'
$v7ScenePath = Join-Path $WorkspaceRoot 'archive\b0_afterlife_mirror_v7\source\towercontinued\b0_afterlife_mirror\afterlife_mirror_scene.scene'
$sectorPath = Join-Path $WorkspaceRoot 'research\b0_afterlife_native_audit\trigger_owner\basegame_3_nightcity\raw\base\worlds\03_night_city\_compiled\default\quest_9e8d73fad623f1b1.streamingsector'
$sourceHashes = @{}
foreach ($path in @($mirrorPath,$basePath,$parentPath,$v7OwnerPath,$v7ScenePath,$sectorPath)) {
    $sourceHashes[$path] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
}
$mirror = Read-Cr2wFile $mirrorPath
$base = Read-Cr2wFile $basePath
$parent = Read-Cr2wFile $parentPath
$v7Owner = Read-Cr2wFile $v7OwnerPath
$v7Scene = Read-Cr2wFile $v7ScenePath
$sector = Read-Cr2wFile $sectorPath
if (@(Compare-Object @($sector.RootChunk.Nodes | ForEach-Object {$_.Chunk.GetType().Name} | Sort-Object) @('worldStaticOccluderMeshNode','worldTriggerAreaNode')).Count) {
    throw 'Reviewed trigger sector is no longer just the trigger and occluder'
}
$prefab = @($mirror.RootChunk.PhasePrefabs | Where-Object {$_.PrefabNodeRef.ToString() -eq '#mirror_scene_afterlife'})
if ($prefab.Count -ne 1) { throw 'Vanilla Afterlife ownership entry is not unique' }
$template = $v7Owner.RootChunk.Graph.Chunk
$templateWait = Get-QuestNode $template 2
$templateScene = Get-QuestNode $template 4
$templateDelay = Get-QuestNode $template 7
$nativeEntry = @($templateWait.Condition.Chunk.Conditions | Where-Object {$_.Chunk.GetType().Name -eq 'questTriggerCondition'})
if ($nativeEntry.Count -ne 1 -or $nativeEntry[0].Chunk.TriggerAreaRef.ToString() -ne $fullTrigger -or
    $nativeEntry[0].Chunk.Type.ToString() -ne 'IsInside') { throw 'V7 native entry precedent changed' }
$exitNode = @($v7Scene.RootChunk.SceneGraph.Chunk.Graph | Where-Object {$_.Chunk.NodeId.Id.ToString() -eq '4398'})
if ($exitNode.Count -ne 1 -or $exitNode[0].Chunk.QuestNode.Chunk.Condition.Chunk.GetType().Name -ne 'questTriggerCondition' -or
    $exitNode[0].Chunk.QuestNode.Chunk.Condition.Chunk.Type.ToString() -ne 'IsOutside' -or
    $exitNode[0].Chunk.QuestNode.Chunk.Condition.Chunk.TriggerAreaRef.ToString() -ne $fullTrigger) {
    throw 'V7 native scene exit precedent changed'
}
if ($templateScene.SceneLocation.NodeRef.ToString() -ne '#mirror_sm_scene_afterlife' -or
    $templateDelay.Condition.Chunk.Type.Chunk.Seconds.ToString() -ne '1') {
    throw 'Afterlife marker or one-second rearm changed'
}
New-Item -ItemType Directory -Force -Path $src,$out,$val | Out-Null
function Put($g,$n) { Add-RedHandle $g.Nodes $n }
function Link($g,$a,$socket,$b,$dest='In') {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $socket) (Get-QuestSocket (Get-QuestNode $g $b) $dest))
}
function Count($id,$name) {
    $n = New-SetFactNode $id ($prefix+$name) 1
    $n.Type.Chunk.SetExactValue = $false
    return $n
}
function Pause($id,$condition) {
    $n = (Get-QuestNode $base.RootChunk.Graph.Chunk 106).DeepCopy(); $n.Id=[uint16]$id
    foreach ($s in $n.Sockets) { $s.Chunk.Connections.Clear() }
    Set-RedHandleProperty $n Condition $condition
    return $n
}
function PhaseFile($g) {
    $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new()
    $root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
    Set-RedHandleProperty $root Graph $g
    $file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new(); $file.RootChunk=$root
    return $file
}
$guardFacts=[ordered]@{
    PostTowerFreeRoamActive=1; PTFRP0_DR13=1; q307_active=0; q307_done=1
    q307_finished=1; q307_2079=1; q307_main_game_killed=1
    q305_johnny_scene_active=0; mirror_interaction_disabled=0; q115_point_of_no_return=0
    PTFRB0ALM_Enabled=0; PTFRB0ALM_Interrupted=0; PTFRALMA1_Requested=0
    PTFRALMA2_Requested=1; PTFRALMA2_Interrupted=0
}
$combat=(Get-QuestNode (Get-QuestNode $mirror.RootChunk.Graph.Chunk 42).PhaseGraph.Chunk 57).Condition.Chunk.DeepCopy()
if ($combat.Type.Chunk.GetType().Name -ne 'questCharacterCombat_ConditionType') { throw 'Vanilla combat guard changed' }
$combat.Type.Chunk.Inverted=$true
function Guard([bool]$includeNative) {
    $c=[WolvenKit.RED4.Types.questLogicalCondition]::new()
    $c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
    foreach ($name in $guardFacts.Keys) {
        Add-RedHandle $c.Conditions (New-FactCondition $name $guardFacts[$name] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
    }
    if ($includeNative) { Add-RedHandle $c.Conditions $nativeEntry[0].Chunk.DeepCopy() }
    Add-RedHandle $c.Conditions $combat.DeepCopy()
    return $c
}

$gate=[WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $gate (New-InputNode 0 'In1')
Put $gate (Count 1 'Boot')
Put $gate (Pause 2 (Guard $false))
Put $gate (Count 3 'Guard')
$child=[WolvenKit.RED4.Types.questPhaseNodeDefinition]::new(); $child.Id=[uint16]4
$rp=[WolvenKit.RED4.Types.ResourcePath]::op_Implicit($ownerDepot)
$child.PhaseResource=[Activator]::CreateInstance($child.GetType().GetProperty('PhaseResource').PropertyType,[object[]]@($rp))
[void](New-QuestSocket $child 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
[void](New-QuestSocket $child 'In1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
Put $gate $child
Link $gate 0 Out 1; Link $gate 1 Out 2; Link $gate 2 Out 3; Link $gate 3 Out 4 In1
$gateFile=PhaseFile $gate

$owner=[WolvenKit.RED4.Types.questGraphDefinition]::new()
Put $owner (New-InputNode 0 'In1')
Put $owner (New-SetFactNode 1 ($prefix+'Ready') 1)
Put $owner (Pause 2 (Guard $true))
Put $owner (New-SetFactNode 3 ($prefix+'Active') 1)
$sceneNode=$templateScene.DeepCopy(); $sceneNode.Id=[uint16]4
foreach ($s in $sceneNode.Sockets) { $s.Chunk.Connections.Clear() }
$sceneResource=[WolvenKit.RED4.Types.ResourcePath]::op_Implicit($sceneDepot)
$sceneNode.SceneFile=[Activator]::CreateInstance($sceneNode.GetType().GetProperty('SceneFile').PropertyType,[object[]]@($sceneResource))
Put $owner $sceneNode
Put $owner (New-SetFactNode 5 ($prefix+'Active') 0)
Put $owner (New-SetFactNode 6 ($prefix+'Completed') 1)
$delay=$templateDelay.DeepCopy(); $delay.Id=[uint16]7
foreach ($s in $delay.Sockets) { $s.Chunk.Connections.Clear() }
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
$ownerFile=PhaseFile $owner
$ownerFile.RootChunk.PhasePrefabs.Add($prefab[0].DeepCopy())

$sceneFile=Read-Cr2wFile $v7ScenePath
Write-Cr2wFile $gateFile (Join-Path $src $gateDepot)
Write-Cr2wFile $ownerFile (Join-Path $src $ownerDepot)
Write-Cr2wFile $sceneFile (Join-Path $src $sceneDepot)
$paths=@($gateDepot,$ownerDepot,$sceneDepot) | Sort-Object
$graphs=@{}
foreach ($path in @($gateDepot,$ownerDepot)) {
    $file=Read-Cr2wFile (Join-Path $src $path)
    $key=if($path -eq $gateDepot){'gate'}else{'owner'}
    Export-Cr2wJson $file (Join-Path $val ($key+'.json'))
    $graphs[$key]=[ordered]@{
        nodes=$file.RootChunk.Graph.Chunk.Nodes.Count
        edges=@(Get-GraphEdges $file.RootChunk.Graph.Chunk)
        prefabs=@($file.RootChunk.PhasePrefabs | ForEach-Object {$_.PrefabNodeRef.ToString()})
    }
    if ($file.EmbeddedFiles.Count -or $file.RootChunk.InplacePhases.Count) { throw 'Unexpected embedded phase content' }
    foreach ($h in $file.RootChunk.Graph.Chunk.Nodes) {
        $n=$h.Chunk
        if($n.GetType().Name -eq 'questFactsDBManagerNodeDefinition' -and
            -not $n.Type.Chunk.FactName.ToString().StartsWith($prefix)) { throw 'Non-audit fact writer found' }
    }
}
$sceneCheck=Read-Cr2wFile (Join-Path $src $sceneDepot)
Export-Cr2wJson $sceneCheck (Join-Path $val 'scene.json')
if ($graphs.gate.nodes -ne 5 -or $graphs.gate.prefabs.Count -or
    $graphs.owner.nodes -ne 13 -or $graphs.owner.prefabs.Count -ne 1 -or
    $graphs.owner.prefabs[0] -ne '#mirror_scene_afterlife' -or
    $sceneCheck.RootChunk.SceneGraph.Chunk.Graph.Count -ne 37) { throw 'Unexpected graph, prefab, or scene scope' }
$actual=@(Get-ChildItem -LiteralPath $src -Recurse -File | ForEach-Object {[IO.Path]::GetRelativePath($src,$_.FullName)} | Sort-Object)
if (@(Compare-Object $paths $actual).Count) { throw 'Unexpected archive source file' }
foreach ($path in $sourceHashes.Keys) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $sourceHashes[$path]) { throw "Reviewed source changed: $path" }
}
$crc=65535
foreach ($b in [Text.Encoding]::UTF8.GetBytes($gateDepot+':1')) {
    $x=($crc -shr 8) -bxor $b; $x=$x -bxor ($x -shr 4)
    $crc=(($crc -shl 8) -bxor ($x -shl 12) -bxor ($x -shl 5) -bxor $x) -band 65535
}
if (@($parent.RootChunk.Graph.Chunk.Nodes | Where-Object {$_.Chunk.Id.ToString() -eq "$crc"}).Count) {
    throw 'A2 ArchiveXL ID collides with vanilla EP1 node'
}
$hs=[WolvenKit.Common.Services.HashService]::new(); $hs.Load()
$archivePath=Join-Path $out $archiveName
$stream=[IO.File]::Create($archivePath)
try {
    $writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())
    if(-not $writer.WriteArchive([IO.DirectoryInfo]::new($src),$stream)) { throw 'Archive write failed' }
} finally { $stream.Dispose() }
$reader=[WolvenKit.RED4.Archive.IO.ArchiveReader]::new(); $packedArchive=$null
if($reader.ReadArchive($archivePath,$hs,[ref]$packedArchive).ToString() -ne 'NoError') { throw 'Archive reopen failed' }
$packed=@($packedArchive.Files.Values | ForEach-Object {$_.Name} | Sort-Object)
if(@(Compare-Object $paths $packed).Count) { throw 'Archive manifest mismatch' }
foreach($entry in $packedArchive.Files.Values) {
    $memory=[IO.MemoryStream]::new()
    try {
        $entry.Extract($memory)
        if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray())) -ne
            (Get-FileHash -LiteralPath (Join-Path $src $entry.Name) -Algorithm SHA256).Hash) { throw 'Packed bytes differ' }
    } finally { $memory.Dispose() }
}
Copy-Item -LiteralPath (Join-Path $WorkspaceRoot ('archive\b0_afterlife_native_scene_a2\'+$archiveName+'.xl')) -Destination (Join-Path $out ($archiveName+'.xl'))
$manifest=[ordered]@{
    status='WORKSPACE_ONLY_NATIVE_SCENE_A2_RUNTIME_UNTESTED'
    archive=$archiveName; sha256=(Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
    resources=$packed; registration_id=$crc; guard_facts=$guardFacts; graphs=$graphs
    entry_gate="IsInside $fullTrigger"; exit_gate="IsOutside $fullTrigger"
    vanilla_replacements=@(); prefab='#mirror_scene_afterlife'
    runtime_writes='PTFRALMA2_* facts only'; source_hashes=$sourceHashes
}
[IO.File]::WriteAllText((Join-Path $val 'build_manifest.json'),($manifest|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$manifest|ConvertTo-Json -Depth 7
