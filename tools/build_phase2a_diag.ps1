param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Build and validate the baseline first, and retain its RED4 helper functions in this scope.
$baselineOutput = . (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot

$vanillaDepotPath = 'base\quest\main_quests\epilogue\final_boards.questphase'
$hookDepotPath = 'towercontinued\quest\post_tower_hook.questphase'
$baselineSourceRoot = Join-Path $WorkspaceRoot 'archive\source'
$diagSourceRoot = Join-Path $WorkspaceRoot 'archive\diag_source'
$diagFinalBoardsPath = Join-Path $diagSourceRoot $vanillaDepotPath
$diagHookPath = Join-Path $diagSourceRoot $hookDepotPath
$diagArchivePath = Join-Path $WorkspaceRoot 'build\TowerContinued_Phase2A_DIAG.archive'
$validationRoot = Join-Path $WorkspaceRoot 'research\phase2a_diag\validation'

function Disconnect-QuestSockets {
    param(
        [Parameter(Mandatory = $true)]$Source,
        [Parameter(Mandatory = $true)]$Destination
    )

    $sourceMatches = @($Source.Connections | Where-Object {
        [object]::ReferenceEquals($_.Chunk.Source.Chunk, $Source) -and
        [object]::ReferenceEquals($_.Chunk.Destination.Chunk, $Destination)
    })
    if ($sourceMatches.Count -ne 1) {
        throw "Expected exactly one connection from $($Source.Name) to $($Destination.Name); found $($sourceMatches.Count)."
    }
    $connection = $sourceMatches[0].Chunk

    for ($index = $Source.Connections.Count - 1; $index -ge 0; $index--) {
        if ([object]::ReferenceEquals($Source.Connections[$index].Chunk, $connection)) {
            $Source.Connections.RemoveAt($index)
        }
    }
    for ($index = $Destination.Connections.Count - 1; $index -ge 0; $index--) {
        if ([object]::ReferenceEquals($Destination.Connections[$index].Chunk, $connection)) {
            $Destination.Connections.RemoveAt($index)
        }
    }
}

function Add-DiagnosticSegment {
    param(
        [Parameter(Mandatory = $true)]$Graph,
        [Parameter(Mandatory = $true)]$Source,
        [Parameter(Mandatory = $true)]$Destination,
        [Parameter(Mandatory = $true)][int]$FactNodeId,
        [Parameter(Mandatory = $true)][int]$MessageNodeId,
        [Parameter(Mandatory = $true)][string]$FactName,
        [Parameter(Mandatory = $true)][string]$Message
    )

    Disconnect-QuestSockets -Source $Source -Destination $Destination
    $factNode = New-SetFactNode -Id $FactNodeId -FactName $FactName -Value 1
    $messageNode = New-WarningNode -Id $MessageNodeId -Message $Message
    $messageNode.Type.Chunk.Duration = [single]3.0
    Add-RedHandle -Array $Graph.Nodes -Chunk $factNode
    Add-RedHandle -Array $Graph.Nodes -Chunk $messageNode
    [void](Connect-QuestSockets -Source $Source -Destination (Get-QuestSocket -Node $factNode -Name 'In'))
    [void](Connect-QuestSockets -Source (Get-QuestSocket -Node $factNode -Name 'Out') -Destination (Get-QuestSocket -Node $messageNode -Name 'In'))
    [void](Connect-QuestSockets -Source (Get-QuestSocket -Node $messageNode -Name 'Out') -Destination $Destination)
}

function Assert-DiagnosticNode {
    param(
        [Parameter(Mandatory = $true)]$Graph,
        [Parameter(Mandatory = $true)][int]$FactNodeId,
        [Parameter(Mandatory = $true)][int]$MessageNodeId,
        [Parameter(Mandatory = $true)][string]$FactName,
        [Parameter(Mandatory = $true)][string]$Message
    )

    $factType = (Get-QuestNode -Graph $Graph -Id $FactNodeId).Type.Chunk
    if ($factType.GetType().Name -ne 'questSetVar_NodeType' -or
        $factType.FactName.ToString() -ne $FactName -or
        $factType.Value.ToString() -ne '1' -or
        $factType.SetExactValue.ToString() -ne 'True') {
        throw "Diagnostic fact node $FactNodeId did not round-trip as exact $FactName = 1."
    }

    $messageType = (Get-QuestNode -Graph $Graph -Id $MessageNodeId).Type.Chunk
    if ($messageType.GetType().Name -ne 'questWarningMessage_NodeType' -or
        $messageType.Message.ToString() -ne $Message -or
        $messageType.Show.ToString() -ne 'True') {
        throw "Diagnostic message node $MessageNodeId did not round-trip as '$Message'."
    }
}

New-Item -ItemType Directory -Force -Path $diagSourceRoot, $validationRoot | Out-Null

# Instrument the baseline final-boards patch.
$diagFinalBoardsFile = Read-Cr2wFile -Path (Join-Path $baselineSourceRoot $vanillaDepotPath)
$diagFinalBoardsGraph = $diagFinalBoardsFile.RootChunk.Graph.Chunk

$node55 = Get-QuestNode -Graph $diagFinalBoardsGraph -Id 55
$node53 = Get-QuestNode -Graph $diagFinalBoardsGraph -Id 53
$node27 = Get-QuestNode -Graph $diagFinalBoardsGraph -Id 27
$node56 = Get-QuestNode -Graph $diagFinalBoardsGraph -Id 56
$node57 = Get-QuestNode -Graph $diagFinalBoardsGraph -Id 57

# A: q307 ending-board external phase has returned, before it rejoins the shared hub.
Add-DiagnosticSegment -Graph $diagFinalBoardsGraph `
    -Source (Get-QuestSocket -Node $node55 -Name 'Out1') `
    -Destination (Get-QuestSocket -Node $node53 -Name 'In1') `
    -FactNodeId 59 -MessageNodeId 60 `
    -FactName 'PostTowerDiag_EndingBoardReturned' `
    -Message '[PTFR DIAG A] Q307 ending board returned'

# B: closest graph-level equivalent to entering node 27: immediately before node 27.In.
Add-DiagnosticSegment -Graph $diagFinalBoardsGraph `
    -Source (Get-QuestSocket -Node $node53 -Name 'Out1') `
    -Destination (Get-QuestSocket -Node $node27 -Name 'In') `
    -FactNodeId 61 -MessageNodeId 62 `
    -FactName 'PostTowerDiag_Node27Entered' `
    -Message '[PTFR DIAG B] Node 27 input reached'

# C: the native node 27 action has returned control through its Out socket.
Add-DiagnosticSegment -Graph $diagFinalBoardsGraph `
    -Source (Get-QuestSocket -Node $node27 -Name 'Out') `
    -Destination (Get-QuestSocket -Node $node56 -Name 'In') `
    -FactNodeId 63 -MessageNodeId 64 `
    -FactName 'PostTowerDiag_Node27Out' `
    -Message '[PTFR DIAG C] Node 27 Out reached'

# D: the completed-Q307 condition selected its true output, before the phase call.
Add-DiagnosticSegment -Graph $diagFinalBoardsGraph `
    -Source (Get-QuestSocket -Node $node56 -Name 'True') `
    -Destination (Get-QuestSocket -Node $node57 -Name 'In1') `
    -FactNodeId 65 -MessageNodeId 66 `
    -FactName 'PostTowerDiag_GuardTrue' `
    -Message '[PTFR DIAG D] Q307 guard true'

Write-Cr2wFile -File $diagFinalBoardsFile -Path $diagFinalBoardsPath

# E: first operations after the mod-owned phase input socket is traversed.
$diagHookFile = Read-Cr2wFile -Path (Join-Path $baselineSourceRoot $hookDepotPath)
$diagHookGraph = $diagHookFile.RootChunk.Graph.Chunk
$hookInput = Get-QuestNode -Graph $diagHookGraph -Id 0
$oneShotCondition = Get-QuestNode -Graph $diagHookGraph -Id 1
Add-DiagnosticSegment -Graph $diagHookGraph `
    -Source (Get-QuestSocket -Node $hookInput -Name 'Out') `
    -Destination (Get-QuestSocket -Node $oneShotCondition -Name 'In') `
    -FactNodeId 6 -MessageNodeId 7 `
    -FactName 'PostTowerDiag_ModPhaseEntered' `
    -Message '[PTFR DIAG E] Mod phase entered'

Write-Cr2wFile -File $diagHookFile -Path $diagHookPath

# Decode and validate the cooked resources.
$validatedFinalBoardsFile = Read-Cr2wFile -Path $diagFinalBoardsPath
$validatedHookFile = Read-Cr2wFile -Path $diagHookPath
$validatedFinalBoardsGraph = $validatedFinalBoardsFile.RootChunk.Graph.Chunk
$validatedHookGraph = $validatedHookFile.RootChunk.Graph.Chunk

if ($validatedFinalBoardsFile.MetaData.Version -ne 195 -or $validatedHookFile.MetaData.Version -ne 195) {
    throw 'Diagnostic resources did not round-trip as CR2W v195.'
}
if ($validatedFinalBoardsGraph.Nodes.Count -ne 41) {
    throw "Diagnostic final_boards contains $($validatedFinalBoardsGraph.Nodes.Count) nodes; expected 41."
}
if ($validatedHookGraph.Nodes.Count -ne 8) {
    throw "Diagnostic mod phase contains $($validatedHookGraph.Nodes.Count) nodes; expected 8."
}

$diagnostics = @(
    @{ Graph = $validatedFinalBoardsGraph; FactNode = 59; MessageNode = 60; Fact = 'PostTowerDiag_EndingBoardReturned'; Message = '[PTFR DIAG A] Q307 ending board returned' },
    @{ Graph = $validatedFinalBoardsGraph; FactNode = 61; MessageNode = 62; Fact = 'PostTowerDiag_Node27Entered'; Message = '[PTFR DIAG B] Node 27 input reached' },
    @{ Graph = $validatedFinalBoardsGraph; FactNode = 63; MessageNode = 64; Fact = 'PostTowerDiag_Node27Out'; Message = '[PTFR DIAG C] Node 27 Out reached' },
    @{ Graph = $validatedFinalBoardsGraph; FactNode = 65; MessageNode = 66; Fact = 'PostTowerDiag_GuardTrue'; Message = '[PTFR DIAG D] Q307 guard true' },
    @{ Graph = $validatedHookGraph; FactNode = 6; MessageNode = 7; Fact = 'PostTowerDiag_ModPhaseEntered'; Message = '[PTFR DIAG E] Mod phase entered' }
)
foreach ($diagnostic in $diagnostics) {
    Assert-DiagnosticNode -Graph $diagnostic.Graph -FactNodeId $diagnostic.FactNode -MessageNodeId $diagnostic.MessageNode -FactName $diagnostic.Fact -Message $diagnostic.Message
}

$finalBoardsEdges = @(Get-GraphEdges -Graph $validatedFinalBoardsGraph)
foreach ($edge in @(
    '55.Out1 -> 59.In', '59.Out -> 60.In', '60.Out -> 53.In1',
    '53.Out1 -> 61.In', '61.Out -> 62.In', '62.Out -> 27.In',
    '27.Out -> 63.In', '63.Out -> 64.In', '64.Out -> 56.In',
    '56.True -> 65.In', '65.Out -> 66.In', '66.Out -> 57.In1',
    '56.False -> 58.In1', '57.Out1 -> 58.In2', '58.Out1 -> 28.In'
)) {
    Assert-ContainsExactlyOnce -Values $finalBoardsEdges -Expected $edge -Context 'Phase 2A-DIAG final_boards'
}

$hookEdges = @(Get-GraphEdges -Graph $validatedHookGraph)
foreach ($edge in @(
    '0.Out -> 6.In', '6.Out -> 7.In', '7.Out -> 1.In',
    '1.True -> 2.In', '2.Out -> 3.In', '3.Out -> 4.In1',
    '1.False -> 4.In2', '4.Out1 -> 5.In'
)) {
    Assert-ContainsExactlyOnce -Values $hookEdges -Expected $edge -Context 'Phase 2A-DIAG mod phase'
}

Export-Cr2wJson -File $validatedFinalBoardsFile -Path (Join-Path $validationRoot 'final_boards.diag.json')
Export-Cr2wJson -File $validatedHookFile -Path (Join-Path $validationRoot 'post_tower_hook.diag.json')

# Pack only the two diagnostic resources.
$diagFiles = @(Get-ChildItem -LiteralPath $diagSourceRoot -Recurse -File)
$diagRelativePaths = @($diagFiles | ForEach-Object { [System.IO.Path]::GetRelativePath($diagSourceRoot, $_.FullName) } | Sort-Object)
$expectedPaths = @($vanillaDepotPath, $hookDepotPath) | Sort-Object
if ($diagFiles.Count -ne 2 -or @(Compare-Object -ReferenceObject $expectedPaths -DifferenceObject $diagRelativePaths).Count -ne 0) {
    throw "Diagnostic source contains unintended resources: $($diagRelativePaths -join ', ')"
}

$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$logger = [WolvenKit.SerilogWrapper]::new()
$archiveStream = [System.IO.File]::Create($diagArchivePath)
try {
    $archiveWriter = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService, $logger)
    if (-not $archiveWriter.WriteArchive([System.IO.DirectoryInfo]::new($diagSourceRoot), $archiveStream)) {
        throw 'WolvenKit ArchiveWriter returned false for the diagnostic archive.'
    }
}
finally {
    $archiveStream.Dispose()
}

$archiveReader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
$archive = $null
$archiveResult = $archiveReader.ReadArchive($diagArchivePath, $hashService, [ref]$archive)
if ($archiveResult.ToString() -ne 'NoError') {
    throw "Unable to reopen the diagnostic archive: $archiveResult"
}
$packedPaths = @($archive.Files.Values | ForEach-Object { $_.Name } | Sort-Object)
if ($packedPaths.Count -ne 2 -or @(Compare-Object -ReferenceObject $expectedPaths -DifferenceObject $packedPaths).Count -ne 0) {
    throw "Diagnostic archive contains unintended resources: $($packedPaths -join ', ')"
}

$manifest = [ordered]@{
    buildStatus = 'success'
    archive = [System.IO.Path]::GetRelativePath($WorkspaceRoot, $diagArchivePath)
    archiveSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $diagArchivePath).Hash
    resources = $packedPaths
    originalFadePath = '56.False -> 58.In1; 57.Out1 -> 58.In2; 58.Out1 -> 28.In'
    instrumentation = @(
        @{ point = 'A'; fact = 'PostTowerDiag_EndingBoardReturned'; message = '[PTFR DIAG A] Q307 ending board returned' },
        @{ point = 'B'; fact = 'PostTowerDiag_Node27Entered'; message = '[PTFR DIAG B] Node 27 input reached'; note = 'Immediately before node 27.In; native node body has no separate editable entry point.' },
        @{ point = 'C'; fact = 'PostTowerDiag_Node27Out'; message = '[PTFR DIAG C] Node 27 Out reached' },
        @{ point = 'D'; fact = 'PostTowerDiag_GuardTrue'; message = '[PTFR DIAG D] Q307 guard true' },
        @{ point = 'E'; fact = 'PostTowerDiag_ModPhaseEntered'; message = '[PTFR DIAG E] Mod phase entered' }
    )
    validation = @(
        'Both cooked resources decode as CR2W v195',
        'All five exact diagnostic fact writes and messages round-trip',
        'All instrumented edges round-trip',
        'Original node-28 fade join remains connected',
        'Archive reopens with exactly two intended resource paths'
    )
}
$manifestJson = $manifest | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText((Join-Path $validationRoot 'build_manifest.json'), $manifestJson, [System.Text.UTF8Encoding]::new($false))
$manifestJson
