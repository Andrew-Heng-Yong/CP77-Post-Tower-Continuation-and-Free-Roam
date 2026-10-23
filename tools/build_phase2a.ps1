param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0',
    [switch]$HelpersOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$vanillaDepotPath = 'base\quest\main_quests\epilogue\final_boards.questphase'
$hookDepotPath = 'towercontinued\quest\post_tower_hook.questphase'
$pristinePath = Join-Path $WorkspaceRoot 'research\phase2a\pristine\base\quest\main_quests\epilogue\final_boards.questphase'
$sourceRoot = Join-Path $WorkspaceRoot 'archive\source'
$patchedPath = Join-Path $sourceRoot $vanillaDepotPath
$hookPath = Join-Path $sourceRoot $hookDepotPath
$buildRoot = Join-Path $WorkspaceRoot 'build'
$archivePath = Join-Path $buildRoot 'TowerContinued_Phase2A.archive'
$validationRoot = Join-Path $WorkspaceRoot 'research\phase2a\validation'

foreach ($assemblyName in @(
    'WolvenKit.Core.dll',
    'WolvenKit.Common.dll',
    'WolvenKit.RED4.dll',
    'WolvenKit.Modkit.dll'
)) {
    [void][System.Reflection.Assembly]::LoadFrom((Join-Path $WolvenKitRoot $assemblyName))
}

function Read-Cr2wFile {
    param([Parameter(Mandatory = $true)][string]$Path)

    $stream = [System.IO.File]::OpenRead($Path)
    try {
        $reader = [WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
        $file = $null
        $result = $reader.ReadFile([ref]$file, $true)
        if ($result.ToString() -ne 'NoError') {
            throw "Unable to decode $Path`: $result"
        }
        return $file
    }
    finally {
        $stream.Dispose()
    }
}

function Write-Cr2wFile {
    param(
        [Parameter(Mandatory = $true)]$File,
        [Parameter(Mandatory = $true)][string]$Path
    )

    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Path) | Out-Null
    $stream = [System.IO.File]::Create($Path)
    try {
        $writer = [WolvenKit.RED4.Archive.IO.CR2WWriter]::new($stream)
        $result = $writer.WriteFile($File)
        if ($null -ne $result -and $result.ToString() -notin @('True', 'NoError')) {
            throw "Unable to write $Path`: $result"
        }
    }
    finally {
        $stream.Dispose()
    }
}

function New-RedHandle {
    param(
        [Parameter(Mandatory = $true)][type]$HandleType,
        [Parameter(Mandatory = $true)]$Chunk
    )

    return [System.Activator]::CreateInstance($HandleType, [object[]]@($Chunk))
}

function Add-RedHandle {
    param(
        [Parameter(Mandatory = $true)]$Array,
        [Parameter(Mandatory = $true)]$Chunk
    )

    $handleType = $Array.GetType().GetGenericArguments()[0]
    [void]$Array.Add((New-RedHandle -HandleType $handleType -Chunk $Chunk))
}

function Set-RedHandleProperty {
    param(
        [Parameter(Mandatory = $true)]$Owner,
        [Parameter(Mandatory = $true)][string]$PropertyName,
        [Parameter(Mandatory = $true)]$Chunk
    )

    $property = $Owner.GetType().GetProperty($PropertyName)
    if ($null -eq $property) {
        throw "Property $PropertyName does not exist on $($Owner.GetType().FullName)."
    }
    $property.SetValue($Owner, (New-RedHandle -HandleType $property.PropertyType -Chunk $Chunk))
}

function New-QuestSocket {
    param(
        [Parameter(Mandatory = $true)]$Node,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][WolvenKit.RED4.Types.Enums+questSocketType]$Type
    )

    $socket = [WolvenKit.RED4.Types.questSocketDefinition]::new()
    $socket.Name = $Name
    $socket.Type = $Type
    Add-RedHandle -Array $Node.Sockets -Chunk $socket
    return $socket
}

function Get-QuestNode {
    param(
        [Parameter(Mandatory = $true)]$Graph,
        [Parameter(Mandatory = $true)][int]$Id
    )

    $matches = @($Graph.Nodes | Where-Object { [int]::Parse($_.Chunk.Id.ToString()) -eq $Id })
    if ($matches.Count -ne 1) {
        throw "Expected exactly one graph node with id $Id; found $($matches.Count)."
    }
    return $matches[0].Chunk
}

function Get-QuestSocket {
    param(
        [Parameter(Mandatory = $true)]$Node,
        [Parameter(Mandatory = $true)][string]$Name
    )

    $matches = @($Node.Sockets | Where-Object { $_.Chunk.Name.ToString() -eq $Name })
    if ($matches.Count -ne 1) {
        throw "Expected exactly one '$Name' socket on node $($Node.Id); found $($matches.Count)."
    }
    return $matches[0].Chunk
}

function Connect-QuestSockets {
    param(
        [Parameter(Mandatory = $true)]$Source,
        [Parameter(Mandatory = $true)]$Destination
    )

    $connection = [WolvenKit.RED4.Types.graphGraphConnectionDefinition]::new()
    Set-RedHandleProperty -Owner $connection -PropertyName 'Source' -Chunk $Source
    Set-RedHandleProperty -Owner $connection -PropertyName 'Destination' -Chunk $Destination
    Add-RedHandle -Array $Source.Connections -Chunk $connection
    Add-RedHandle -Array $Destination.Connections -Chunk $connection
    return $connection
}

function New-FactCondition {
    param(
        [Parameter(Mandatory = $true)][string]$FactName,
        [Parameter(Mandatory = $true)][int]$Value,
        [Parameter(Mandatory = $true)][WolvenKit.RED4.Types.Enums+EComparisonType]$Comparison
    )

    $comparisonType = [WolvenKit.RED4.Types.questVarComparison_ConditionType]::new()
    $comparisonType.FactName = $FactName
    $comparisonType.Value = $Value
    $comparisonType.ComparisonType = $Comparison

    $condition = [WolvenKit.RED4.Types.questFactsDBCondition]::new()
    Set-RedHandleProperty -Owner $condition -PropertyName 'Type' -Chunk $comparisonType
    return $condition
}

function New-ConditionNode {
    param(
        [Parameter(Mandatory = $true)][int]$Id,
        [Parameter(Mandatory = $true)]$Condition
    )

    $node = [WolvenKit.RED4.Types.questConditionNodeDefinition]::new()
    $node.Id = [uint16]$Id
    Set-RedHandleProperty -Owner $node -PropertyName 'Condition' -Chunk $Condition
    [void](New-QuestSocket -Node $node -Name 'CutDestination' -Type ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
    [void](New-QuestSocket -Node $node -Name 'In' -Type ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
    [void](New-QuestSocket -Node $node -Name 'True' -Type ([WolvenKit.RED4.Types.Enums+questSocketType]::Output))
    [void](New-QuestSocket -Node $node -Name 'False' -Type ([WolvenKit.RED4.Types.Enums+questSocketType]::Output))
    return $node
}

function New-XorNode {
    param(
        [Parameter(Mandatory = $true)][int]$Id,
        [Parameter(Mandatory = $true)][int]$InputCount
    )

    $node = [WolvenKit.RED4.Types.questLogicalXorNodeDefinition]::new()
    $node.Id = [uint16]$Id
    $node.InputSocketCount = [uint32]$InputCount
    $node.OutputSocketCount = [uint32]1
    [void](New-QuestSocket -Node $node -Name 'CutDestination' -Type ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
    foreach ($index in 1..$InputCount) {
        [void](New-QuestSocket -Node $node -Name "In$index" -Type ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
    }
    [void](New-QuestSocket -Node $node -Name 'Out1' -Type ([WolvenKit.RED4.Types.Enums+questSocketType]::Output))
    return $node
}

function New-WarningNode {
    param(
        [Parameter(Mandatory = $true)][int]$Id,
        [Parameter(Mandatory = $true)][string]$Message
    )

    $warning = [WolvenKit.RED4.Types.questWarningMessage_NodeType]::new()
    $warning.Message = $Message
    $warning.Duration = [single]5.0
    $warning.Show = $true
    $warning.Instant = $false
    $warning.Type = [WolvenKit.RED4.Types.Enums+gameSimpleMessageType]::Undefined

    $node = [WolvenKit.RED4.Types.questUIManagerNodeDefinition]::new()
    $node.Id = [uint16]$Id
    Set-RedHandleProperty -Owner $node -PropertyName 'Type' -Chunk $warning
    [void](New-QuestSocket -Node $node -Name 'CutDestination' -Type ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
    [void](New-QuestSocket -Node $node -Name 'In' -Type ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
    [void](New-QuestSocket -Node $node -Name 'Out' -Type ([WolvenKit.RED4.Types.Enums+questSocketType]::Output))
    return $node
}

function New-SetFactNode {
    param(
        [Parameter(Mandatory = $true)][int]$Id,
        [Parameter(Mandatory = $true)][string]$FactName,
        [Parameter(Mandatory = $true)][int]$Value
    )

    $setVar = [WolvenKit.RED4.Types.questSetVar_NodeType]::new()
    $setVar.FactName = $FactName
    $setVar.Value = $Value
    $setVar.SetExactValue = $true

    $node = [WolvenKit.RED4.Types.questFactsDBManagerNodeDefinition]::new()
    $node.Id = [uint16]$Id
    Set-RedHandleProperty -Owner $node -PropertyName 'Type' -Chunk $setVar
    [void](New-QuestSocket -Node $node -Name 'CutDestination' -Type ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
    [void](New-QuestSocket -Node $node -Name 'In' -Type ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
    [void](New-QuestSocket -Node $node -Name 'Out' -Type ([WolvenKit.RED4.Types.Enums+questSocketType]::Output))
    return $node
}

function New-InputNode {
    param(
        [Parameter(Mandatory = $true)][int]$Id,
        [Parameter(Mandatory = $true)][string]$SocketName
    )

    $node = [WolvenKit.RED4.Types.questInputNodeDefinition]::new()
    $node.Id = [uint16]$Id
    $node.SocketName = $SocketName
    [void](New-QuestSocket -Node $node -Name 'CutDestination' -Type ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
    [void](New-QuestSocket -Node $node -Name 'Out' -Type ([WolvenKit.RED4.Types.Enums+questSocketType]::Output))
    return $node
}

function New-OutputNode {
    param(
        [Parameter(Mandatory = $true)][int]$Id,
        [Parameter(Mandatory = $true)][string]$SocketName
    )

    $node = [WolvenKit.RED4.Types.questOutputNodeDefinition]::new()
    $node.Id = [uint16]$Id
    $node.SocketName = $SocketName
    $node.Type = [WolvenKit.RED4.Types.Enums+questExitType]::Terminating
    [void](New-QuestSocket -Node $node -Name 'CutDestination' -Type ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
    [void](New-QuestSocket -Node $node -Name 'In' -Type ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
    return $node
}

function Export-Cr2wJson {
    param(
        [Parameter(Mandatory = $true)]$File,
        [Parameter(Mandatory = $true)][string]$Path
    )

    $dto = [WolvenKit.Common.Conversion.RedFileDto]::new($File, $false)
    $options = [WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
    $json = [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($dto, $options)
    [System.IO.File]::WriteAllText($Path, $json, [System.Text.UTF8Encoding]::new($false))
}

function Get-GraphEdges {
    param([Parameter(Mandatory = $true)]$Graph)

    $owners = @{}
    foreach ($nodeHandle in $Graph.Nodes) {
        $node = $nodeHandle.Chunk
        foreach ($socketHandle in $node.Sockets) {
            $socket = $socketHandle.Chunk
            $owners[[System.Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($socket)] = $node.Id.ToString()
        }
    }

    $edges = [System.Collections.Generic.List[string]]::new()
    foreach ($nodeHandle in $Graph.Nodes) {
        $node = $nodeHandle.Chunk
        foreach ($socketHandle in $node.Sockets) {
            $socket = $socketHandle.Chunk
            foreach ($connectionHandle in $socket.Connections) {
                $connection = $connectionHandle.Chunk
                if ([object]::ReferenceEquals($connection.Source.Chunk, $socket)) {
                    $sourceId = $owners[[System.Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($connection.Source.Chunk)]
                    $destinationId = $owners[[System.Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($connection.Destination.Chunk)]
                    $edges.Add("$sourceId.$($connection.Source.Chunk.Name) -> $destinationId.$($connection.Destination.Chunk.Name)")
                }
            }
        }
    }
    return @($edges | Sort-Object)
}

function Assert-ContainsExactlyOnce {
    param(
        [Parameter(Mandatory = $true)][string[]]$Values,
        [Parameter(Mandatory = $true)][string]$Expected,
        [Parameter(Mandatory = $true)][string]$Context
    )

    $count = @($Values | Where-Object { $_ -eq $Expected }).Count
    if ($count -ne 1) {
        throw "$Context expected exactly one '$Expected' edge; found $count."
    }
}

function Get-NodeWithoutConnectionsJson {
    param([Parameter(Mandatory = $true)]$Node)

    $copy = $Node.DeepCopy()
    foreach ($socketHandle in $copy.Sockets) {
        $socketHandle.Chunk.Connections.Clear()
    }
    $options = [WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
    return [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($copy, $options)
}

if ($HelpersOnly) { return }

if (-not (Test-Path -LiteralPath $pristinePath -PathType Leaf)) {
    throw "Pristine vanilla resource is missing: $pristinePath"
}

New-Item -ItemType Directory -Force -Path $sourceRoot, $buildRoot, $validationRoot | Out-Null

# Patch only the output edge from vanilla node 27 to vanilla node 28.
$patchedFile = Read-Cr2wFile -Path $pristinePath
$patchedGraph = $patchedFile.RootChunk.Graph.Chunk
$node27 = Get-QuestNode -Graph $patchedGraph -Id 27
$node28 = Get-QuestNode -Graph $patchedGraph -Id 28
$node27Out = Get-QuestSocket -Node $node27 -Name 'Out'
$node28In = Get-QuestSocket -Node $node28 -Name 'In'
if ($node27Out.Connections.Count -ne 1 -or $node28In.Connections.Count -ne 1) {
    throw 'Vanilla node 27 -> node 28 edge no longer has the expected one-to-one socket shape.'
}
$oldConnection = $node27Out.Connections[0].Chunk
if (-not [object]::ReferenceEquals($oldConnection, $node28In.Connections[0].Chunk)) {
    throw 'Node 27 Out and node 28 In do not share the same vanilla connection object.'
}
if (-not [object]::ReferenceEquals($oldConnection.Source.Chunk, $node27Out) -or
    -not [object]::ReferenceEquals($oldConnection.Destination.Chunk, $node28In)) {
    throw 'Unexpected source/destination on the vanilla node 27 -> node 28 connection.'
}

$reservedIds = @(56, 57, 58)
$existingIds = @($patchedGraph.Nodes | ForEach-Object { [int]::Parse($_.Chunk.Id.ToString()) })
foreach ($id in $reservedIds) {
    if ($existingIds -contains $id) {
        throw "Cannot add Phase 2A node $id because that id already exists."
    }
}

$guardLogic = [WolvenKit.RED4.Types.questLogicalCondition]::new()
$guardLogic.Operation = [WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
foreach ($guard in @(
    @{ Name = 'q307_active'; Value = 0; Comparison = [WolvenKit.RED4.Types.Enums+EComparisonType]::Equal },
    @{ Name = 'q307_done'; Value = 1; Comparison = [WolvenKit.RED4.Types.Enums+EComparisonType]::GreaterOrEqual },
    @{ Name = 'q307_finished'; Value = 1; Comparison = [WolvenKit.RED4.Types.Enums+EComparisonType]::GreaterOrEqual },
    @{ Name = 'q307_2079'; Value = 1; Comparison = [WolvenKit.RED4.Types.Enums+EComparisonType]::GreaterOrEqual }
)) {
    Add-RedHandle -Array $guardLogic.Conditions -Chunk (New-FactCondition -FactName $guard.Name -Value $guard.Value -Comparison $guard.Comparison)
}
$guardNode = New-ConditionNode -Id 56 -Condition $guardLogic

$q307PhaseTemplate = Get-QuestNode -Graph $patchedGraph -Id 55
if ($q307PhaseTemplate.GetType().Name -ne 'questPhaseNodeDefinition') {
    throw 'Expected vanilla node 55 to be the external q307 ending-board phase node used as the phase-node template.'
}
$hookPhaseNode = $q307PhaseTemplate.DeepCopy()
$hookPhaseNode.Id = [uint16]57
$hookResourcePath = [WolvenKit.RED4.Types.ResourcePath]::op_Implicit($hookDepotPath)
$hookPhaseNode.PhaseResource = [System.Activator]::CreateInstance(
    $hookPhaseNode.GetType().GetProperty('PhaseResource').PropertyType,
    [object[]]@($hookResourcePath)
)
foreach ($socketHandle in $hookPhaseNode.Sockets) {
    $socketHandle.Chunk.Connections.Clear()
}

$joinNode = New-XorNode -Id 58 -InputCount 2

$node27Out.Connections.Clear()
$node28In.Connections.Clear()
Add-RedHandle -Array $patchedGraph.Nodes -Chunk $guardNode
Add-RedHandle -Array $patchedGraph.Nodes -Chunk $hookPhaseNode
Add-RedHandle -Array $patchedGraph.Nodes -Chunk $joinNode

[void](Connect-QuestSockets -Source $node27Out -Destination (Get-QuestSocket -Node $guardNode -Name 'In'))
[void](Connect-QuestSockets -Source (Get-QuestSocket -Node $guardNode -Name 'True') -Destination (Get-QuestSocket -Node $hookPhaseNode -Name 'In1'))
[void](Connect-QuestSockets -Source (Get-QuestSocket -Node $guardNode -Name 'False') -Destination (Get-QuestSocket -Node $joinNode -Name 'In1'))
[void](Connect-QuestSockets -Source (Get-QuestSocket -Node $hookPhaseNode -Name 'Out1') -Destination (Get-QuestSocket -Node $joinNode -Name 'In2'))
[void](Connect-QuestSockets -Source (Get-QuestSocket -Node $joinNode -Name 'Out1') -Destination $node28In)

Write-Cr2wFile -File $patchedFile -Path $patchedPath

# Build the mod-owned one-shot diagnostic phase.
$hookGraph = [WolvenKit.RED4.Types.questGraphDefinition]::new()
$hookInput = New-InputNode -Id 0 -SocketName 'In1'
$notSeen = New-FactCondition -FactName 'PostTowerFreeRoamHookSeen' -Value 0 -Comparison ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)
$oneShotCondition = New-ConditionNode -Id 1 -Condition $notSeen
$warningNode = New-WarningNode -Id 2 -Message 'Tower Continued hook reached.'
$markerNode = New-SetFactNode -Id 3 -FactName 'PostTowerFreeRoamHookSeen' -Value 1
$oneShotJoin = New-XorNode -Id 4 -InputCount 2
$hookOutput = New-OutputNode -Id 5 -SocketName 'Out1'
foreach ($node in @($hookInput, $oneShotCondition, $warningNode, $markerNode, $oneShotJoin, $hookOutput)) {
    Add-RedHandle -Array $hookGraph.Nodes -Chunk $node
}

[void](Connect-QuestSockets -Source (Get-QuestSocket -Node $hookInput -Name 'Out') -Destination (Get-QuestSocket -Node $oneShotCondition -Name 'In'))
[void](Connect-QuestSockets -Source (Get-QuestSocket -Node $oneShotCondition -Name 'True') -Destination (Get-QuestSocket -Node $warningNode -Name 'In'))
[void](Connect-QuestSockets -Source (Get-QuestSocket -Node $warningNode -Name 'Out') -Destination (Get-QuestSocket -Node $markerNode -Name 'In'))
[void](Connect-QuestSockets -Source (Get-QuestSocket -Node $markerNode -Name 'Out') -Destination (Get-QuestSocket -Node $oneShotJoin -Name 'In1'))
[void](Connect-QuestSockets -Source (Get-QuestSocket -Node $oneShotCondition -Name 'False') -Destination (Get-QuestSocket -Node $oneShotJoin -Name 'In2'))
[void](Connect-QuestSockets -Source (Get-QuestSocket -Node $oneShotJoin -Name 'Out1') -Destination (Get-QuestSocket -Node $hookOutput -Name 'In'))

$hookRoot = [WolvenKit.RED4.Types.questQuestPhaseResource]::new()
$hookRoot.CookingPlatform = [WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
Set-RedHandleProperty -Owner $hookRoot -PropertyName 'Graph' -Chunk $hookGraph
$hookFile = [WolvenKit.RED4.Archive.CR2W.CR2WFile]::new()
$hookFile.RootChunk = $hookRoot
Write-Cr2wFile -File $hookFile -Path $hookPath

# Decode both generated resources again before packaging.
$validatedPatchedFile = Read-Cr2wFile -Path $patchedPath
$validatedHookFile = Read-Cr2wFile -Path $hookPath
$validatedPatchedGraph = $validatedPatchedFile.RootChunk.Graph.Chunk
$validatedHookGraph = $validatedHookFile.RootChunk.Graph.Chunk
if ($validatedPatchedGraph.Nodes.Count -ne ($existingIds.Count + 3)) {
    throw 'Patched final_boards node count does not equal vanilla count plus three nodes.'
}
if ($validatedHookGraph.Nodes.Count -ne 6) {
    throw 'Mod-owned diagnostic phase did not round-trip with exactly six nodes.'
}

$patchedEdges = @(Get-GraphEdges -Graph $validatedPatchedGraph)
foreach ($edge in @(
    '27.Out -> 56.In',
    '56.True -> 57.In1',
    '56.False -> 58.In1',
    '57.Out1 -> 58.In2',
    '58.Out1 -> 28.In'
)) {
    Assert-ContainsExactlyOnce -Values $patchedEdges -Expected $edge -Context 'Patched final_boards'
}
if ($patchedEdges -contains '27.Out -> 28.In') {
    throw 'The original direct node 27 -> node 28 edge still exists alongside the hook splice.'
}

$validatedGuardNode = Get-QuestNode -Graph $validatedPatchedGraph -Id 56
$validatedGuardLogic = $validatedGuardNode.Condition.Chunk
if ($validatedGuardLogic.GetType().Name -ne 'questLogicalCondition' -or $validatedGuardLogic.Operation.ToString() -ne 'AND') {
    throw 'Q307 guard did not round-trip as a logical AND condition.'
}
$validatedGuardTerms = @($validatedGuardLogic.Conditions | ForEach-Object {
    $factCondition = $_.Chunk
    $comparison = $factCondition.Type.Chunk
    "$($comparison.FactName)|$($comparison.ComparisonType)|$($comparison.Value)"
} | Sort-Object)
$expectedGuardTerms = @(
    'q307_2079|GreaterOrEqual|1',
    'q307_active|Equal|0',
    'q307_done|GreaterOrEqual|1',
    'q307_finished|GreaterOrEqual|1'
) | Sort-Object
if (@(Compare-Object -ReferenceObject $expectedGuardTerms -DifferenceObject $validatedGuardTerms).Count -ne 0) {
    throw "Q307 guard terms did not round-trip as expected: $($validatedGuardTerms -join ', ')"
}

$validatedHookPhaseNode = Get-QuestNode -Graph $validatedPatchedGraph -Id 57
if ($validatedHookPhaseNode.PhaseResource.DepotPath.ToString() -ne $hookDepotPath) {
    throw "Patched phase node references '$($validatedHookPhaseNode.PhaseResource.DepotPath)' instead of '$hookDepotPath'."
}

$hookEdges = @(Get-GraphEdges -Graph $validatedHookGraph)
foreach ($edge in @(
    '0.Out -> 1.In',
    '1.True -> 2.In',
    '2.Out -> 3.In',
    '3.Out -> 4.In1',
    '1.False -> 4.In2',
    '4.Out1 -> 5.In'
)) {
    Assert-ContainsExactlyOnce -Values $hookEdges -Expected $edge -Context 'Mod-owned diagnostic phase'
}

$validatedOneShotCondition = (Get-QuestNode -Graph $validatedHookGraph -Id 1).Condition.Chunk.Type.Chunk
if ($validatedOneShotCondition.FactName.ToString() -ne 'PostTowerFreeRoamHookSeen' -or
    $validatedOneShotCondition.ComparisonType.ToString() -ne 'Equal' -or
    $validatedOneShotCondition.Value.ToString() -ne '0') {
    throw 'Mod-owned one-shot condition did not round-trip as PostTowerFreeRoamHookSeen == 0.'
}
$validatedWarning = (Get-QuestNode -Graph $validatedHookGraph -Id 2).Type.Chunk
if ($validatedWarning.Message.ToString() -ne 'Tower Continued hook reached.' -or -not [bool]$validatedWarning.Show) {
    throw 'Diagnostic warning node did not round-trip with the expected visible message.'
}
$validatedMarker = (Get-QuestNode -Graph $validatedHookGraph -Id 3).Type.Chunk
if ($validatedMarker.FactName.ToString() -ne 'PostTowerFreeRoamHookSeen' -or
    $validatedMarker.Value.ToString() -ne '1' -or
    -not [bool]$validatedMarker.SetExactValue) {
    throw 'Marker writer did not round-trip as exact PostTowerFreeRoamHookSeen = 1.'
}

$pristineValidationFile = Read-Cr2wFile -Path $pristinePath
$pristineValidationGraph = $pristineValidationFile.RootChunk.Graph.Chunk
foreach ($originalNodeHandle in $pristineValidationGraph.Nodes) {
    $originalNode = $originalNodeHandle.Chunk
    $originalId = [int]::Parse($originalNode.Id.ToString())
    $roundTripNode = Get-QuestNode -Graph $validatedPatchedGraph -Id $originalId
    if ((Get-NodeWithoutConnectionsJson -Node $originalNode) -ne (Get-NodeWithoutConnectionsJson -Node $roundTripNode)) {
        throw "Existing vanilla node $originalId changed beyond its top-level socket connection arrays."
    }
}

# Export readable JSON and a targeted semantic diff for inspection.
Export-Cr2wJson -File (Read-Cr2wFile -Path $pristinePath) -Path (Join-Path $validationRoot 'final_boards.original.json')
Export-Cr2wJson -File $validatedPatchedFile -Path (Join-Path $validationRoot 'final_boards.patched.json')
Export-Cr2wJson -File $validatedHookFile -Path (Join-Path $validationRoot 'post_tower_hook.json')

$originalHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $pristinePath).Hash
$patchedHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $patchedPath).Hash
$hookHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $hookPath).Hash
$diffLines = @(
    "Vanilla depot path: $vanillaDepotPath",
    "Original SHA256: $originalHash",
    "Patched SHA256:  $patchedHash",
    '',
    'Removed edge:',
    '  27.Out -> 28.In',
    '',
    'Added nodes:',
    '  56 questConditionNodeDefinition (Q307 completion AND guard)',
    "  57 questPhaseNodeDefinition ($hookDepotPath)",
    '  58 questLogicalXorNodeDefinition (two-input join)',
    '',
    'Added edges:',
    '  27.Out -> 56.In',
    '  56.True -> 57.In1',
    '  56.False -> 58.In1',
    '  57.Out1 -> 58.In2',
    '  58.Out1 -> 28.In',
    '',
    'Existing node properties changed:',
    '  node 27 Out connection only',
    '  node 28 In connection only',
    '',
    "Mod phase SHA256: $hookHash"
)
[System.IO.File]::WriteAllLines((Join-Path $validationRoot 'final_boards.graph_diff.txt'), $diffLines, [System.Text.UTF8Encoding]::new($false))

# The pack source must contain exactly the two intended cooked resources.
$sourceFiles = @(Get-ChildItem -LiteralPath $sourceRoot -Recurse -File)
if ($sourceFiles.Count -ne 2) {
    throw "Archive source contains $($sourceFiles.Count) files; expected exactly two."
}
$sourceRelativePaths = @($sourceFiles | ForEach-Object { [System.IO.Path]::GetRelativePath($sourceRoot, $_.FullName) } | Sort-Object)
$expectedRelativePaths = @($vanillaDepotPath, $hookDepotPath) | Sort-Object
if (@(Compare-Object -ReferenceObject $expectedRelativePaths -DifferenceObject $sourceRelativePaths).Count -ne 0) {
    throw "Archive source contains unexpected paths: $($sourceRelativePaths -join ', ')"
}

$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$logger = [WolvenKit.SerilogWrapper]::new()
$archiveStream = [System.IO.File]::Create($archivePath)
try {
    $archiveWriter = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService, $logger)
    if (-not $archiveWriter.WriteArchive([System.IO.DirectoryInfo]::new($sourceRoot), $archiveStream)) {
        throw 'WolvenKit ArchiveWriter returned false.'
    }
}
finally {
    $archiveStream.Dispose()
}

# Re-open the archive and require exactly the intended depot paths.
$archiveReader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
$archive = $null
$archiveResult = $archiveReader.ReadArchive($archivePath, $hashService, [ref]$archive)
if ($archiveResult.ToString() -ne 'NoError') {
    throw "Unable to validate generated archive: $archiveResult"
}
$packedPaths = @($archive.Files.Values | ForEach-Object { $_.Name } | Sort-Object)
if ($packedPaths.Count -ne 2 -or @(Compare-Object -ReferenceObject $expectedRelativePaths -DifferenceObject $packedPaths).Count -ne 0) {
    throw "Generated archive contains unexpected paths: $($packedPaths -join ', ')"
}

$manifest = [ordered]@{
    buildStatus = 'success'
    archive = [System.IO.Path]::GetRelativePath($WorkspaceRoot, $archivePath)
    archiveSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $archivePath).Hash
    resources = $packedPaths
    pristineVanillaSha256 = $originalHash
    patchedVanillaSha256 = $patchedHash
    modPhaseSha256 = $hookHash
    q307Guard = @(
        'q307_active == 0',
        'q307_done >= 1',
        'q307_finished >= 1',
        'q307_2079 >= 1'
    )
    marker = 'PostTowerFreeRoamHookSeen == 0 -> diagnostic -> set exact 1'
    validation = @(
        'Both cooked resources decode as CR2W v195',
        'All 30 original top-level nodes match after ignoring socket connection arrays',
        'Five hook-splice edges and six mod-phase edges round-trip exactly',
        'Archive reopens with exactly two intended resource paths'
    )
}
$manifestJson = $manifest | ConvertTo-Json -Depth 6
[System.IO.File]::WriteAllText((Join-Path $validationRoot 'build_manifest.json'), $manifestJson, [System.Text.UTF8Encoding]::new($false))

$manifestJson
