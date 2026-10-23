param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly

# Two standard-shaped Badlands regional leaves. Their vanilla regional root is
# not restarted; each mod-owned phase retains its own exact local default gate.
$vendorPath = Join-Path $WorkspaceRoot 'research\b0_vendor_rollout\regional_sources\raw\base\open_world\vendors\badlands\inland_avenue_se5\inland_avenue_se5_vendors.questphase'
$basePath = Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase'
$specs = @(
    [pscustomobject]@{Name='junk'; Outer=6; Phase=9; Distance=14; Scene=16; Spawn=17; Despawn=18; Far=19;
        Id='bls_ina_se5_junkshop_01'; Marker='#bls_sm_ina_se5_junkshop_01'; Prefix='PTFRB0SE5J_';
        ScenePath='base\open_world\vendors\badlands\inland_avenue_se5\bls_ina_se5_junkshop_01\bls_ina_se5_junkshop_01.scene'},
    [pscustomobject]@{Name='melee'; Outer=7; Phase=11; Distance=15; Scene=17; Spawn=18; Despawn=19; Far=20;
        Id='bls_ina_se5_melee_01'; Marker='#bls_sm_ina_se5_melee_01'; Prefix='PTFRB0SE5M_';
        ScenePath='base\open_world\vendors\badlands\inland_avenue_se5\bls_ina_se5_melee_01\bls_ina_se5_melee_01.scene'}
)
$inputs = @($vendorPath,$basePath) + @($specs | ForEach-Object {
    Join-Path $WorkspaceRoot ('research\b0_vendor_rollout\regional_scene_sources\raw\'+$_.ScenePath)
})
foreach ($path in $inputs) { if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing reviewed input: $path" } }
$inputHashes = @{}
foreach ($path in $inputs) { $inputHashes[$path]=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash }

$source = Join-Path $WorkspaceRoot 'archive\b0_junk_melee_pair\source'
$output = Join-Path $WorkspaceRoot 'build\B0_JunkMeleePair'
$validation = Join-Path $WorkspaceRoot 'research\b0_junk_melee_pair\validation'
New-Item -ItemType Directory -Force -Path $source,$output,$validation | Out-Null
$archiveName = 'TowerContinued_B0_JunkMeleePair.archive'
$vendor = Read-Cr2wFile $vendorPath
$base = Read-Cr2wFile $basePath
$packedPaths = [System.Collections.Generic.List[string]]::new()
$guardRecords = [ordered]@{}

foreach ($spec in $specs) {
    $branch=(Get-QuestNode $vendor.RootChunk.Graph.Chunk $spec.Outer).PhaseGraph.Chunk
    $distanceTemplate=Get-QuestNode $branch $spec.Distance
    $phaseTemplate=Get-QuestNode $branch $spec.Phase
    if ($branch.Nodes.Count -ne 7 -or
        $distanceTemplate.GetType().Name -ne 'questPauseConditionNodeDefinition' -or
        $distanceTemplate.Condition.Chunk.GetType().Name -ne 'questDistanceCondition' -or
        $distanceTemplate.Condition.Chunk.Type.Chunk.ComparisonType.ToString() -ne 'Less' -or
        $distanceTemplate.Condition.Chunk.Type.Chunk.DistanceDefinition2.Chunk.DistanceValue.ToString() -ne '50' -or
        $phaseTemplate.GetType().Name -ne 'questPhaseNodeDefinition') {
        throw "$($spec.Name) outer owner changed"
    }
    $inner=$phaseTemplate.PhaseGraph.Chunk
    $spawn=Get-QuestNode $inner $spec.Spawn
    $despawn=Get-QuestNode $inner $spec.Despawn
    $scene=Get-QuestNode $inner $spec.Scene
    $far=Get-QuestNode $inner $spec.Far
    $close=Get-QuestNode $inner 3
    if ($inner.Nodes.Count -ne 7 -or $spawn.Actions.Count -ne 1 -or $despawn.Actions.Count -ne 1 -or
        $spawn.Actions[0].Type.Chunk.Action.ToString() -ne 'Activate' -or
        $despawn.Actions[0].Type.Chunk.Action.ToString() -ne 'Deactivate' -or
        $spawn.Actions[0].Type.Chunk.Reference.ToString() -ne ('#'+$spec.Id) -or
        $despawn.Actions[0].Type.Chunk.Reference.ToString() -ne ('#'+$spec.Id) -or
        $spawn.Actions[0].Type.Chunk.EntryName.ToString() -ne $spec.Id -or
        $despawn.Actions[0].Type.Chunk.EntryName.ToString() -ne $spec.Id -or
        $spawn.Actions[0].Type.Chunk.PhaseName.ToString() -ne 'default' -or
        $despawn.Actions[0].Type.Chunk.PhaseName.ToString() -ne 'default' -or
        $scene.SceneFile.DepotPath.ToString() -ne $spec.ScenePath -or
        $scene.SceneLocation.NodeRef.ToString() -ne $spec.Marker -or
        $close.Condition.Chunk.Type.Chunk.ComparisonType.ToString() -ne 'Less' -or
        $close.Condition.Chunk.Type.Chunk.DistanceDefinition2.Chunk.DistanceValue.ToString() -ne '12' -or
        $far.Condition.Chunk.Type.Chunk.ComparisonType.ToString() -ne 'Greater' -or
        $far.Condition.Chunk.Type.Chunk.DistanceDefinition2.Chunk.DistanceValue.ToString() -ne '50') {
        throw "$($spec.Name) spawn, scene or departure leaf changed"
    }
    $guards=[ordered]@{
        PostTowerFreeRoamActive=1; PTFRP0_DR13=1; q307_active=0; q307_done=1;
        q307_finished=1; q307_2079=1; q307_main_game_killed=1;
        q305_johnny_scene_active=0; q115_point_of_no_return=0; q000_done=1
    }
    $guards[$spec.Id+'_default_on']=1
    $guards[$spec.Prefix+'Enabled']=1
    $guardRecords[$spec.Name]=$guards
    $condition=[WolvenKit.RED4.Types.questLogicalCondition]::new()
    $condition.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
    foreach ($fact in $guards.Keys) {
        Add-RedHandle $condition.Conditions (New-FactCondition $fact $guards[$fact] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
    }
    $graph=[WolvenKit.RED4.Types.questGraphDefinition]::new()
    function Put($node) { Add-RedHandle $graph.Nodes $node }
    function Link($from,$socket,$to,$dest='In') {
        [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $from) $socket) (Get-QuestSocket (Get-QuestNode $graph $to) $dest))
    }
    Put (New-InputNode 0 'In1')
    Put (New-SetFactNode 1 ($spec.Prefix+'Ready') 1)
    $guard=(Get-QuestNode $base.RootChunk.Graph.Chunk 106).DeepCopy();$guard.Id=[uint16]2
    foreach ($socket in $guard.Sockets) { $socket.Chunk.Connections.Clear() }
    Set-RedHandleProperty $guard Condition $condition
    Put $guard
    $distance=$distanceTemplate.DeepCopy();$distance.Id=[uint16]3
    foreach ($socket in $distance.Sockets) { $socket.Chunk.Connections.Clear() }
    Put $distance
    Put (New-SetFactNode 4 ($spec.Prefix+'Near') 1)
    $phase=$phaseTemplate.DeepCopy();$phase.Id=[uint16]5
    foreach ($socket in $phase.Sockets) { $socket.Chunk.Connections.Clear() }
    $innerCopy=$phase.PhaseGraph.Chunk
    foreach ($nodeHandle in $innerCopy.Nodes) {
        foreach ($socket in $nodeHandle.Chunk.Sockets) { $socket.Chunk.Connections.Clear() }
    }
    Add-RedHandle $innerCopy.Nodes (New-SetFactNode 30 ($spec.Prefix+'SpawnActionOut') 1)
    Add-RedHandle $innerCopy.Nodes (New-SetFactNode 31 ($spec.Prefix+'ActorDistanceGate') 1)
    Add-RedHandle $innerCopy.Nodes (New-SetFactNode 32 ($spec.Prefix+'ExitWatchArmed') 1)
    Add-RedHandle $innerCopy.Nodes (New-SetFactNode 33 ($spec.Prefix+'DespawnActionOut') 1)
    $farWait=Get-QuestNode $innerCopy $spec.Far
    Set-RedHandleProperty $farWait Condition (New-FactCondition ($spec.Prefix+'Far') 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
    function LinkInner($from,$socket,$to,$dest='In') {
        [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $innerCopy $from) $socket) (Get-QuestSocket (Get-QuestNode $innerCopy $to) $dest))
    }
    LinkInner 0 Out $spec.Spawn;LinkInner 0 Out 32;LinkInner 32 Out $spec.Far
    LinkInner $spec.Spawn Out 30;LinkInner 30 Out 3;LinkInner 3 Out 31
    LinkInner 31 Out $spec.Scene $spec.Id
    LinkInner $spec.Far Out $spec.Despawn;LinkInner $spec.Despawn Out 33;LinkInner 33 Out 1
    Put $phase
    Put (New-SetFactNode 6 ($spec.Prefix+'Departed') 1)
    Put (New-SetFactNode 7 ($spec.Prefix+'Near') 0)
    $rearm=(Get-QuestNode $base.RootChunk.Graph.Chunk 106).DeepCopy();$rearm.Id=[uint16]8
    foreach ($socket in $rearm.Sockets) { $socket.Chunk.Connections.Clear() }
    Set-RedHandleProperty $rearm Condition (New-FactCondition ($spec.Prefix+'Far') 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
    Put $rearm
    Link 0 Out 1;Link 1 Out 2;Link 2 Out 3;Link 3 Out 4;Link 4 Out 5 In1
    Link 5 Out1 6;Link 6 Out 7;Link 7 Out 8;Link 8 Out 2
    $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new()
    $root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
    Set-RedHandleProperty $root Graph $graph
    $resource=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$resource.RootChunk=$root
    $depot='towercontinued\b0_junk_melee_pair\'+$spec.Name+'_owner.questphase'
    Write-Cr2wFile $resource (Join-Path $source $depot)
    Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) (Join-Path $validation ($spec.Name+'_owner.questphase.json'))
    $packedPaths.Add($depot)
}
foreach ($path in $inputs) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $inputHashes[$path]) { throw "Reviewed input changed: $path" }
}
$actual=@(Get-ChildItem -LiteralPath $source -File -Recurse | ForEach-Object { [IO.Path]::GetRelativePath($source,$_.FullName) })
if (@(Compare-Object ($actual | Sort-Object) ($packedPaths | Sort-Object)).Count) { throw 'Unexpected two-site source manifest' }
$hashService=[WolvenKit.Common.Services.HashService]::new();$hashService.Load()
$archivePath=Join-Path $output $archiveName
$stream=[IO.File]::Create($archivePath)
try {
    $writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService,[WolvenKit.SerilogWrapper]::new())
    if (-not $writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)) { throw 'Archive write failed' }
} finally { $stream.Dispose() }
$reader=[WolvenKit.RED4.Archive.IO.ArchiveReader]::new();$archive=$null
if ($reader.ReadArchive($archivePath,$hashService,[ref]$archive).ToString() -ne 'NoError') { throw 'Archive did not reopen' }
$packed=@($archive.Files.Values | ForEach-Object { $_.Name })
if (@(Compare-Object ($packed | Sort-Object) ($packedPaths | Sort-Object)).Count) { throw 'Archive manifest mismatch' }
foreach ($entry in $archive.Files.Values) {
    $memory=[IO.MemoryStream]::new()
    try {
        $entry.Extract($memory)
        if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray())) -ne
            (Get-FileHash -LiteralPath (Join-Path $source $entry.Name) -Algorithm SHA256).Hash) { throw "Packed bytes differ: $($entry.Name)" }
    } finally { $memory.Dispose() }
}
$manifest=[ordered]@{
    status='STATIC_EXPERIMENTAL_NOT_INSTALLED';archive=$archiveName
    sha256=(Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
    resources=$packed;source_hashes=$inputHashes;guard_facts=$guardRecords
    vanilla_replacements=@();enable_facts=@('PTFRB0SE5J_Enabled','PTFRB0SE5M_Enabled')
    known_limits=@('Two Badlands service actors only','Far exit is a development distance flag','Baseline physical absence and current access require live checks','No save/reload claim')
}
[IO.File]::WriteAllText((Join-Path $validation 'build_manifest.json'),($manifest | ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
$manifest | ConvertTo-Json -Depth 12
