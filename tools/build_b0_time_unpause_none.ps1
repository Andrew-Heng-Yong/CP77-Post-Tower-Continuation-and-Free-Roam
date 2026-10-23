param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly

# Manual, one-shot post-credit test. This does not alter q307, the shared
# final-board resource, time-of-day, or any vanilla fact.
$precedentPath = Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\main_quests\q305\phases\q305_08_border_crossing.questphase'
$towerBoardPath = Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\main_quests\q307\phases\q307_ending_board.questphase'
$basePath = Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase'
$inputHashes = [ordered]@{}
foreach ($path in @($precedentPath,$towerBoardPath,$basePath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing reviewed input: $path" }
    $inputHashes[$path] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
}
$q305 = Read-Cr2wFile $precedentPath
$creditEntry = $q305.RootChunk.Graph.Chunk.Nodes[4].Chunk
if ($creditEntry.Id.ToString() -ne '6' -or $creditEntry.GetType().Name -ne 'questPhaseNodeDefinition') { throw 'q305 unpause precedent owner changed' }
$unpauseTemplate = Get-QuestNode $creditEntry.PhaseGraph.Chunk 16
if ($unpauseTemplate.GetType().Name -ne 'questTimeManagerNodeDefinition' -or
    $unpauseTemplate.Type.Chunk.GetType().Name -ne 'questPauseTime_NodeType' -or
    $unpauseTemplate.Type.Chunk.Pause.ToString() -ne 'False' -or
    $unpauseTemplate.Type.Chunk.Source.ToString() -ne 'None') { throw 'q305 source-None unpause precedent changed' }

$board = Read-Cr2wFile $towerBoardPath
$boardJsonPath = Join-Path $WorkspaceRoot 'research\q307_extracted\json\ep1\quest\main_quests\q307\phases\q307_ending_board.questphase.json'
if (-not (Test-Path -LiteralPath $boardJsonPath)) { throw 'Missing Tower board export' }
$boardText = [IO.File]::ReadAllText($boardJsonPath)
if ($boardText -notmatch 'q307_ending_04_reed\.scene' -or $boardText -notmatch 'MenuScenario_FinalBoards') { throw 'Tower final-board owner changed' }

$prefix = 'PTFRB0TU_'
$guards = [ordered]@{
    PostTowerFreeRoamActive=1; PTFRP0_DR13=1; q307_active=0;
    q307_done=1; q307_finished=1; q307_2079=1; q307_main_game_killed=1;
    PTFRB0H10M_Active=0; PTFRB0H10I_M_Active=0;
    PTFRB0H10I_H_Active=0; PTFRB0H10I_B_Active=0;
    PTFRB0H10I_S_Active=0; PTFRB0H10I_W_Active=0;
    PTFRB0TU_Done=0
}
$condition = [WolvenKit.RED4.Types.questLogicalCondition]::new()
$condition.Operation = [WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
foreach ($fact in $guards.Keys) {
    Add-RedHandle $condition.Conditions (New-FactCondition $fact $guards[$fact] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
}
$graph = [WolvenKit.RED4.Types.questGraphDefinition]::new()
function Put($node) { Add-RedHandle $graph.Nodes $node }
function Link([int]$from,[string]$socket,[int]$to,[string]$dest='In') {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $from) $socket) (Get-QuestSocket (Get-QuestNode $graph $to) $dest))
}
Put (New-InputNode 0 'In1')
Put (New-SetFactNode 1 ($prefix+'Ready') 1)
$base = Read-Cr2wFile $basePath
$pauseRequest = (Get-QuestNode $base.RootChunk.Graph.Chunk 106).DeepCopy()
if ($pauseRequest.GetType().Name -ne 'questPauseConditionNodeDefinition') { throw 'base pause-condition template changed' }
$pauseRequest.Id=[uint16]2
foreach ($socket in $pauseRequest.Sockets) { $socket.Chunk.Connections.Clear() }
Set-RedHandleProperty $pauseRequest Condition (New-FactCondition ($prefix+'Request') 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
Put $pauseRequest
Put (New-SetFactNode 3 ($prefix+'Request') 0)
Put (New-ConditionNode 4 $condition)
Put (New-SetFactNode 5 ($prefix+'Rejected') 1)
$unpause = $unpauseTemplate.DeepCopy(); $unpause.Id=[uint16]6
foreach ($socket in $unpause.Sockets) { $socket.Chunk.Connections.Clear() }
Put $unpause
Put (New-SetFactNode 7 ($prefix+'Done') 1)
Put (New-SetFactNode 8 ($prefix+'Ready') 0)
Put (New-OutputNode 9 'Out1')
Link 0 Out 1; Link 1 Out 2; Link 2 Out 3; Link 3 Out 4
Link 4 False 5; Link 5 Out 9
Link 4 True 6; Link 6 Out 7; Link 7 Out 8; Link 8 Out 9

$root = [WolvenKit.RED4.Types.questQuestPhaseResource]::new()
$root.CookingPlatform = [WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
Set-RedHandleProperty $root Graph $graph
$file = [WolvenKit.RED4.Archive.CR2W.CR2WFile]::new(); $file.RootChunk=$root
$depot = 'towercontinued\b0_time_unpause_none\manual_unpause.questphase'
$src = Join-Path $WorkspaceRoot 'archive\b0_time_unpause_none\source'
$out = Join-Path $WorkspaceRoot 'build\B0_TimeUnpauseNone'
$val = Join-Path $WorkspaceRoot 'research\b0_time_pause\validation'
New-Item -ItemType Directory -Force -Path $src,$out,$val | Out-Null
$resourcePath = Join-Path $src $depot
Write-Cr2wFile $file $resourcePath
Export-Cr2wJson (Read-Cr2wFile $resourcePath) (Join-Path $val 'manual_unpause.questphase.json')
foreach ($path in $inputHashes.Keys) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $inputHashes[$path]) { throw "Reviewed input changed during build: $path" }
}
$hashService = [WolvenKit.Common.Services.HashService]::new(); $hashService.Load()
$archivePath = Join-Path $out 'TowerContinued_B0_TimeUnpauseNone.archive'
$stream = [IO.File]::Create($archivePath)
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService,[WolvenKit.SerilogWrapper]::new())
    if (-not $writer.WriteArchive([IO.DirectoryInfo]::new($src),$stream)) { throw 'Archive write failed' }
} finally { $stream.Dispose() }
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new(); $archive=$null
if ($reader.ReadArchive($archivePath,$hashService,[ref]$archive).ToString() -ne 'NoError') { throw 'Archive did not reopen' }
$packed=@($archive.Files.Values)
if ($packed.Count -ne 1 -or $packed[0].Name -ne $depot) { throw 'Unexpected archive manifest' }
$memory=[IO.MemoryStream]::new()
try {
    $packed[0].Extract($memory)
    $packedHash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray()))
    if ($packedHash -ne (Get-FileHash -LiteralPath $resourcePath -Algorithm SHA256).Hash) { throw 'Packed resource bytes differ' }
} finally { $memory.Dispose() }
$manifest=[ordered]@{
    status='EXPERIMENTAL_MANUAL_DISPOSABLE_ONLY'
    archive='TowerContinued_B0_TimeUnpauseNone.archive'
    sha256=(Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
    resources=@($depot)
    source_hashes=$inputHashes
    guard_facts=$guards
    action=[ordered]@{type='questPauseTime_NodeType';pause=$false;source='None';precedent='q305_08_border_crossing.questphase nested node 16'}
    vanilla_replacements=@()
    manual_fact=$prefix+'Request'
}
[IO.File]::WriteAllText((Join-Path $val 'build_manifest.json'),($manifest | ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$manifest | ConvertTo-Json -Depth 10
