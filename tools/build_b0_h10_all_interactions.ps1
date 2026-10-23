param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly

# Five additive, manually requested H10 interactions. No original game
# resource is replaced and no scene starts merely because the archive loads.
$vanillaScenePath = Join-Path $WorkspaceRoot 'research\b0_h10_generalization\extracted_interactions\raw\base\quest\minor_quests\mq000\scenes\mq000_01_apartment.scene'
$mirrorScenePath = Join-Path $WorkspaceRoot 'archive\b0_h10_mirror_prompt\source\towercontinued\b0_h10_mirror_prompt\mirror_prompt.scene'
$vanillaPhasePath = Join-Path $WorkspaceRoot 'research\b0_h10_generalization\extracted\raw\base\quest\minor_quests\mq000\phases\mq000_vs_apartment_interactions.questphase'
$basePath = Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase'
$inputs = @($vanillaScenePath,$mirrorScenePath,$vanillaPhasePath,$basePath)
foreach ($path in $inputs) { if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing reviewed input: $path" } }
$inputHashes = @{}
foreach ($path in $inputs) { $inputHashes[$path] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash }
$src = Join-Path $WorkspaceRoot 'archive\b0_h10_all_interactions\source'
$out = Join-Path $WorkspaceRoot 'build\B0_H10_AllInteractions'
$val = Join-Path $WorkspaceRoot 'research\b0_h10_all_interactions\validation'
New-Item -ItemType Directory -Force -Path $src,$out,$val | Out-Null
$archiveName = 'TowerContinued_B0_H10_Interactions.archive'

$script:sceneNodes = $null
function SceneNode([int]$id) {
    $matches = @($script:sceneNodes | Where-Object { $_.Chunk.NodeId.Id.ToString() -eq "$id" })
    if ($matches.Count -ne 1) { throw "Scene node $id is not unique" }
    return $matches[0].Chunk
}
function EditDest([int]$id,[int]$socket,[int]$from,[int]$to) {
    $ds = (SceneNode $id).OutputSockets[$socket].Destinations
    $matches = @($ds | Where-Object { $_.NodeId.Id.ToString() -eq "$from" })
    if ($matches.Count -ne 1) { throw "Expected exactly one scene edge $id/$socket->$from" }
    $matches[0].NodeId.Id = [WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]$to)
}
function SetDestOrdinal([int]$id,[int]$socket,[int]$target,[int]$ordinal) {
    $ds = (SceneNode $id).OutputSockets[$socket].Destinations
    $matches = @($ds | Where-Object { $_.NodeId.Id.ToString() -eq "$target" })
    if ($matches.Count -ne 1) { throw "Expected exactly one scene edge $id/$socket->$target" }
    $matches[0].IsockStamp.Ordinal = [WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]$ordinal)
}
function DropDest([int]$id,[int]$socket,[int]$target) {
    $ds = (SceneNode $id).OutputSockets[$socket].Destinations
    $indices = @(for ($i=0; $i -lt $ds.Count; $i++) { if ($ds[$i].NodeId.Id.ToString() -eq "$target") { $i } })
    if ($indices.Count -ne 1) { throw "Expected exactly one removable scene edge $id/$socket->$target" }
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
function AddDest([int]$id,[int]$socket,[int]$target) {
    $ds = (SceneNode $id).OutputSockets[$socket].Destinations
    if ($ds.Count -lt 1) { throw "No template edge at $id/$socket" }
    if (@($ds | Where-Object { $_.NodeId.Id.ToString() -eq "$target" }).Count -ne 0) { throw "Duplicate scene edge $id->$target" }
    $edge = $ds[0].DeepCopy()
    $edge.NodeId.Id = [WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]$target)
    $ds.Add($edge)
}
function SetChoiceUnconditional([int]$id) {
    $choice = SceneNode $id
    if ($choice.GetType().Name -ne 'scnChoiceNode' -or $choice.Options.Count -ne 1 -or $null -eq $choice.Options[0].QuestCondition) {
        throw "Expected one condition-bearing choice at $id"
    }
    $choice.Options[0].QuestCondition = $null
}
function ConfigureProps($scene,[string]$kind) {
    $expected = @('shower','tv_lookat')
    $actual = @($scene.RootChunk.Props | ForEach-Object { $_.PropName.ToString() } | Sort-Object)
    if (@(Compare-Object $expected $actual).Count) { throw 'Vanilla scene prop inventory changed' }
    foreach ($prop in $scene.RootChunk.Props) {
        $name = $prop.PropName.ToString()
        $prop.SpawnDespawnParams.SpawnOnStart = (($kind -eq 'shower' -and $name -eq 'shower') -or ($kind -eq 'sofa' -and $name -eq 'tv_lookat'))
    }
    foreach ($actor in $scene.RootChunk.Actors) {
        if ($actor.SpawnDespawnParams.SpawnOnStart.ToString() -ne 'False') { throw "Unexpected actor spawn-on-start: $($actor.ActorName)" }
    }
}

$kinds = @(
    [pscustomobject]@{Name='mirror'; Code='M'; Entry='in_mirror'},
    [pscustomobject]@{Name='shower'; Code='H'; Entry='in_shower'},
    [pscustomobject]@{Name='sleep'; Code='B'; Entry='in_bed'},
    [pscustomobject]@{Name='sofa'; Code='S'; Entry='in'},
    [pscustomobject]@{Name='wardrobe'; Code='W'; Entry='in'}
)
$resourcePaths = [System.Collections.Generic.List[string]]::new()
foreach ($kind in $kinds) {
    $scene = Read-Cr2wFile ($(if ($kind.Name -eq 'mirror') { $mirrorScenePath } else { $vanillaScenePath }))
    $script:sceneNodes = $scene.RootChunk.SceneGraph.Chunk.Graph
    if ($kind.Name -ne 'mirror') {
        ConfigureProps $scene $kind.Name
        switch ($kind.Name) {
            'shower' {
                # V-only, clothed shower proof: no persistent clothing stash,
                # old MQ055 wait, Relic randomizer, or q203 blood-shower branch.
                AddDest 495 0 1112
                EditDest 1112 0 1109 2
                DropDest 47 0 1163
                EditDest 51 0 1404 193
                SetDestOrdinal 51 0 193 0
                DropDest 202 0 1173
            }
            'sleep' {
                AddDest 490 0 1112
                EditDest 1112 0 1109 2
                SetChoiceUnconditional 6
                DropDest 6 0 1591
                EditDest 1353 0 1469 22
                SetDestOrdinal 1353 0 22 0
                EditDest 24 0 501 6
            }
            'sofa' {
                SetDests 1 0 @(328,1112)
                EditDest 1112 0 1109 2
                SetChoiceUnconditional 328
            }
            'wardrobe' {
                SetDests 1 0 @(1339,1112)
                EditDest 1112 0 1109 2
                DropDest 1345 0 1428
            }
        }
    }
    # A scene quest node's In socket is ordinal 1, while the terminating
    # scnEndNode's input is ordinal 0. Copied edges retain their old stamp.
    # Validate/correct both sides of the outside-only exit before packaging.
    switch ($kind.Name) {
        'mirror' { SetDestOrdinal 434 0 1112 1 }
        'shower' { SetDestOrdinal 495 0 1112 1; SetDestOrdinal 1112 0 2 0 }
        'sleep' { SetDestOrdinal 490 0 1112 1; SetDestOrdinal 1112 0 2 0 }
        'sofa' { SetDestOrdinal 1 0 1112 1; SetDestOrdinal 1112 0 2 0 }
        'wardrobe' { SetDestOrdinal 1 0 1112 1; SetDestOrdinal 1112 0 2 0 }
    }
    $depot = 'towercontinued\b0_h10_interactions\' + $kind.Name + '.scene'
    $path = Join-Path $src $depot
    Write-Cr2wFile $scene $path
    Export-Cr2wJson (Read-Cr2wFile $path) (Join-Path $val ($kind.Name + '.scene.json'))
    $resourcePaths.Add($depot)
}

$vanillaPhase = Read-Cr2wFile $vanillaPhasePath
$base = Read-Cr2wFile $basePath
$pauseTemplate = Get-QuestNode $base.RootChunk.Graph.Chunk 106
$sceneTemplate = Get-QuestNode $vanillaPhase.RootChunk.Graph.Chunk 2
$h10Gate = (Get-QuestNode $vanillaPhase.RootChunk.Graph.Chunk 19).Condition.Chunk
$h10Trigger = @($h10Gate.Conditions | Where-Object { $_.Chunk.GetType().Name -eq 'questTriggerCondition' })
$noIncomingCall = @($h10Gate.Conditions | Where-Object { $_.Chunk.GetType().Name -eq 'questUICondition' })
if ($h10Trigger.Count -ne 1 -or $noIncomingCall.Count -ne 1) { throw 'Vanilla H10 context gate changed' }
function Pause([int]$id,[string]$fact,[int]$value) {
    $node = $pauseTemplate.DeepCopy(); $node.Id = [uint16]$id
    foreach ($socket in $node.Sockets) { $socket.Chunk.Connections.Clear() }
    Set-RedHandleProperty $node Condition (New-FactCondition $fact $value ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
    return $node
}
function Put($graph,$node) { Add-RedHandle $graph.Nodes $node }
function Link($graph,$from,$socket,$to,$dest='In') {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $from) $socket) (Get-QuestSocket (Get-QuestNode $graph $to) $dest))
}
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
    PTFRB0H10I_W_Active=0
}
foreach ($kind in $kinds) {
    $prefix = 'PTFRB0H10I_' + $kind.Code + '_'
    $depot = 'towercontinued\b0_h10_interactions\' + $kind.Name + '.scene'
    $condition = [WolvenKit.RED4.Types.questLogicalCondition]::new()
    $condition.Operation = [WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
    foreach ($fact in $guardFacts.Keys) {
        Add-RedHandle $condition.Conditions (New-FactCondition $fact $guardFacts[$fact] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
    }
    Add-RedHandle $condition.Conditions $h10Trigger[0].Chunk.DeepCopy()
    Add-RedHandle $condition.Conditions $noIncomingCall[0].Chunk.DeepCopy()
    $graph = [WolvenKit.RED4.Types.questGraphDefinition]::new()
    Put $graph (New-InputNode 0 'In1')
    Put $graph (New-SetFactNode 1 ($prefix+'Ready') 1)
    Put $graph (Pause 2 ($prefix+'Request') 1)
    Put $graph (New-SetFactNode 3 ($prefix+'Request') 0)
    Put $graph (New-ConditionNode 4 $condition)
    Put $graph (New-SetFactNode 5 ($prefix+'Rejected') 1)
    Put $graph (New-SetFactNode 6 ($prefix+'Active') 1)
    $sceneNode = $sceneTemplate.DeepCopy(); $sceneNode.Id = [uint16]7
    foreach ($socket in $sceneNode.Sockets) { $socket.Chunk.Connections.Clear() }
    $resourcePath = [WolvenKit.RED4.Types.ResourcePath]::op_Implicit($depot)
    $sceneNode.SceneFile = [Activator]::CreateInstance($sceneNode.GetType().GetProperty('SceneFile').PropertyType,[object[]]@($resourcePath))
    Put $graph $sceneNode
    Put $graph (New-SetFactNode 8 ($prefix+'Active') 0)
    Put $graph (New-SetFactNode 9 ($prefix+'Completed') 1)
    Put $graph (New-SetFactNode 10 ($prefix+'Ready') 1)
    Put $graph (New-SetFactNode 11 ($prefix+'Interrupted') 1)
    Link $graph 0 Out 1; Link $graph 1 Out 2; Link $graph 2 Out 3; Link $graph 3 Out 4
    Link $graph 4 False 5; Link $graph 5 Out 2
    Link $graph 4 True 6; Link $graph 6 Out 7 $kind.Entry
    Link $graph 7 out 8; Link $graph 8 Out 9; Link $graph 9 Out 10; Link $graph 10 Out 2
    Link $graph 7 'Default INT' 11
    $root = [WolvenKit.RED4.Types.questQuestPhaseResource]::new()
    $root.CookingPlatform = [WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
    Set-RedHandleProperty $root Graph $graph
    $gate = [WolvenKit.RED4.Archive.CR2W.CR2WFile]::new(); $gate.RootChunk = $root
    $gateDepot = 'towercontinued\b0_h10_interactions\' + $kind.Name + '_gate.questphase'
    $gatePath = Join-Path $src $gateDepot
    Write-Cr2wFile $gate $gatePath
    Export-Cr2wJson (Read-Cr2wFile $gatePath) (Join-Path $val ($kind.Name + '_gate.questphase.json'))
    $resourcePaths.Add($gateDepot)
}

foreach ($path in $inputs) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $inputHashes[$path]) { throw "Reviewed input changed during build: $path" }
}
$allowed = @($resourcePaths | Sort-Object)
$actual = @(Get-ChildItem -LiteralPath $src -File -Recurse | ForEach-Object { [IO.Path]::GetRelativePath($src,$_.FullName) } | Sort-Object)
if (@(Compare-Object $allowed $actual).Count) { throw 'Unexpected source file in interactions archive' }
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
    status = 'EXPERIMENTAL_MANUAL_DISPOSABLE_ONLY'
    risks = @('Outside/forced scene exits and Default INT have no validated active-action cleanup','No Phase 5 ownership entitlement yet','Shower deliberately omits undress/dress; sleep gameplay effects not tuned to Tower profiles')
    archive = $archiveName
    sha256 = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
    resources = $packed
    source_hashes = $inputHashes
    guard_facts = $guardFacts
    vanilla_replacements = @()
    manual_facts = @($kinds | ForEach-Object { 'PTFRB0H10I_' + $_.Code + '_Request' })
}
[IO.File]::WriteAllText((Join-Path $val 'build_manifest.json'),($manifest | ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$manifest | ConvertTo-Json -Depth 10
