param([ValidatePattern('^built_[0-9]{2}$')][string]$BuildName = 'built_01')
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$native = Join-Path $PSScriptRoot 'native_01'
$built = Join-Path $PSScriptRoot $BuildName
if (Test-Path -LiteralPath $built) { throw 'Fresh build output required' }
$plan = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'plan.json') -Raw | ConvertFrom-Json -AsHashtable
$capturePath = Join-Path $native 'capture.json'
if ((Get-FileHash -LiteralPath $capturePath).Hash -cne $plan.capture_sha256) { throw 'Capture drift' }
$capture = Get-Content -LiteralPath $capturePath -Raw | ConvertFrom-Json -AsHashtable
$sources = Join-Path $built 'source'

function Read-World([string]$path) {
    $stream = [IO.File]::OpenRead($path)
    try {
        $reader = [WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
        $reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{ param($e) return $e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs] })
        $file = $null
        if ($reader.ReadFile([ref]$file,$true).ToString() -cne 'NoError') { throw "Unable to read $path" }
        return $file
    } finally { $stream.Dispose() }
}
function Read-Pinned([string]$leaf, [string]$digest) {
    $path = Join-Path $native $leaf
    if ((Get-FileHash -LiteralPath $path).Hash -cne $digest) { throw "Donor changed: $path" }
    return Read-World $path
}
function Write-Resource($file, [string]$depot) {
    $path = Join-Path $sources $depot
    Write-Cr2wFile $file $path
    return @{ depot=$depot; sha256=(Get-FileHash -LiteralPath $path).Hash }
}
function New-Logical([WolvenKit.RED4.Types.Enums+questLogicalOperation]$operation) {
    $condition = [WolvenKit.RED4.Types.questLogicalCondition]::new()
    $condition.Operation = $operation
    return $condition
}
function New-SpawnCheck([string]$ref) {
    $condition = $spawnTemplate.DeepCopy()
    $type = $condition.Type.Chunk
    $comparison = $type.ComparisonParams.Chunk
    $comparison.ComparisonType = [WolvenKit.RED4.Types.Enums+EComparisonType]::GreaterOrEqual
    $comparison.Count = [uint32]1
    $comparison.EntireCommunity = $true
    $type.ObjectRef.Names.Clear()
    $type.ObjectRef.Reference = [WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref)
    return $condition
}
function New-Pause([int]$id, $condition) {
    $node = [WolvenKit.RED4.Types.questPauseConditionNodeDefinition]::new()
    $node.Id = [uint16]$id
    Set-RedHandleProperty $node Condition $condition
    [void](New-QuestSocket $node 'CutDestination' CutDestination)
    [void](New-QuestSocket $node 'In' Input)
    [void](New-QuestSocket $node 'Out' Output)
    return $node
}
function Add-Edge($graph, [int]$from, [string]$output, [int]$to, [string]$inputSocket) {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $from) $output) (Get-QuestSocket (Get-QuestNode $graph $to) $inputSocket))
}
$block = Read-Pinned 'block.streamingblock' $capture.pins.block
$descriptors = @($block.RootChunk.Descriptors)
$block.RootChunk.Descriptors.Clear()
$club = Read-Pinned 'club.questphase' $capture.pins.club
$prefabs = @($club.RootChunk.PhasePrefabs)
$logic = (Get-QuestNode $club.RootChunk.Graph.Chunk 64).Condition.Chunk
$spawnTemplate = @($logic.Conditions | ForEach-Object Chunk | Where-Object {
    $_.GetType().Name -ceq 'questCharacterCondition' -and $_.Type.Chunk.GetType().Name -ceq 'questCharacterSpawned_ConditionType'
}) | Select-Object -First 1
if ($null -eq $spawnTemplate) { throw 'Native spawned-condition donor missing' }
$graph = [WolvenKit.RED4.Types.questGraphDefinition]::new()
Add-RedHandle $graph.Nodes (New-InputNode 0 'In1')
$resources = @()
$rows = @()
$id = 10
foreach ($spec in $plan.sectors) {
    $file = Read-Pinned ($spec.name+'.streamingsector') $spec.sha256
    $sector = $file.RootChunk
    $baseEnd = if ($sector.VariantIndices.Count -gt 1) { [int]$sector.VariantIndices[1].ToString() } else { $sector.Nodes.Count }
    if ($sector.Version.ToString() -cne '68' -or $sector.PersistentNodes.Count -ne 0 -or
        @($sector.VariantNodes | Where-Object { $_.Count -ne 0 }).Count -ne 0 -or $sector.Nodes.Count -ne $spec.source_nodes) {
        throw 'Unexpected sector layout'
    }
    $mapping = @{}
    foreach ($old in $spec.keep) {
        if ($old -lt 0 -or $old -ge $baseEnd -or $sector.Nodes[$old].Chunk.GetType().Name -cne 'worldAISpotNode') {
            throw "Invalid passive base spot: $old"
        }
        $mapping.Add([int]$old, $mapping.Count)
    }
    $original = $sector.NodeData.Buffer.GetBytes()
    if ($original.Length -ne 144*$sector.NodeData.Data.Count) { throw 'Placement stride drift' }
    $bytes = [Collections.Generic.List[byte]]::new()
    for ($offset=0; $offset -lt $original.Length; $offset+=144) {
        $bits = [BitConverter]::ToUInt64($original,$offset+112)
        $old = [int]($bits -band 0x7FFFF)
        if (!$mapping.ContainsKey($old)) { continue }
        $record = [byte[]]$original[$offset..($offset+143)]
        $bits = ($bits -band ([uint64]::MaxValue -bxor [uint64]0x7FFFF)) -bor [uint64]$mapping[$old]
        [Array]::Copy([BitConverter]::GetBytes($bits),0,$record,112,8)
        $bytes.AddRange($record)
    }
    for ($old=$sector.Nodes.Count-1; $old -ge 0; $old--) {
        if (!$mapping.ContainsKey($old)) { $sector.Nodes.RemoveAt($old) }
    }
    # All retained placements came from the native base range.
    $sector.VariantNodes.Clear()
    $sector.VariantIndices.Clear()
    $sector.VariantIndices.Add([WolvenKit.RED4.Types.CInt32]::op_Implicit(0))
    $sector.NodeData.Buffer.Data = $null
    $sector.NodeData.Buffer.SetBytes($bytes.ToArray())

    $matches = @($descriptors | Where-Object { $_.Data.DepotPath.ToString() -ceq $spec.donor })
    if ($matches.Count -ne 1 -or $matches[0].Category.ToString() -cne 'Quest') { throw 'Native descriptor mismatch' }
    $descriptor = $matches[0].DeepCopy()
    $nativeRef = $descriptor.QuestPrefabNodeRef.ToString()
    $hash = [WolvenKit.RED4.Types.NodeRef]::CalculateHash($spec.private_ref)
    $depot = 'base\worlds\03_night_city\_compiled\default\ep1\quest_'+$hash.ToString('x16')+'.streamingsector'
    $descriptor.QuestPrefabNodeRef = [WolvenKit.RED4.Types.NodeRef]::op_Implicit($spec.private_ref)
    $descriptor.Data = [Activator]::CreateInstance($descriptor.GetType().GetProperty('Data').PropertyType,
        [object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($depot)))
    $descriptor.Variants.Clear()
    $descriptor.NumNodeRanges = [uint32]1
    $block.RootChunk.Descriptors.Add($descriptor)
    $resources += Write-Resource $file $depot

    $prefix = 'PTFRHH1_'+$spec.name+'_'
    $guard = New-Logical AND
    foreach ($fact in $plan.guard.Keys) {
        Add-RedHandle $guard.Conditions (New-FactCondition $fact $plan.guard[$fact] Equal)
    }
    foreach ($receipt in @('Claimed','Entered','Hold')) {
        Add-RedHandle $guard.Conditions (New-FactCondition ($prefix+$receipt) 0 Equal)
    }
    $spawned = New-Logical OR
    foreach ($ref in $spec.communities) { Add-RedHandle $spawned.Conditions (New-SpawnCheck $ref) }
    Add-RedHandle $guard.Conditions $spawned

    $inner = [WolvenKit.RED4.Types.questGraphDefinition]::new()
    Add-RedHandle $inner.Nodes (New-InputNode 0 'In1')
    Add-RedHandle $inner.Nodes (New-SetFactNode 1 ($prefix+'Entered') 1)
    Add-RedHandle $inner.Nodes (New-Pause 2 (New-FactCondition ($prefix+'Hold') 1 Equal))
    Add-Edge $inner 0 'Out' 1 'In'
    Add-Edge $inner 1 'Out' 2 'In'

    $nativeName = $nativeRef.Substring($nativeRef.LastIndexOf('/')+1)
    $matchingPrefabs = @($prefabs | Where-Object { $_.PrefabNodeRef.ToString() -ceq $nativeName })
    if ($matchingPrefabs.Count -ne 1) { throw 'Native club root ownership mismatch' }
    $entry = $matchingPrefabs[0].DeepCopy()
    $entry.PrefabNodeRef = [WolvenKit.RED4.Types.NodeRef]::op_Implicit($spec.private_ref)
    $owner = [WolvenKit.RED4.Types.questPhaseNodeDefinition]::new()
    $owner.Id = [uint16]($id+3)
    $owner.PhaseInstancePrefabs.Add($entry)
    Set-RedHandleProperty $owner PhaseGraph $inner
    [void](New-QuestSocket $owner 'CutDestination' CutDestination)
    [void](New-QuestSocket $owner 'In1' Input)
    Add-RedHandle $graph.Nodes (New-Pause $id $guard)
    Add-RedHandle $graph.Nodes (New-ConditionNode ($id+1) ($guard.DeepCopy()))
    Add-RedHandle $graph.Nodes (New-SetFactNode ($id+2) ($prefix+'Claimed') 1)
    Add-RedHandle $graph.Nodes $owner
    Add-Edge $graph 0 'Out' $id 'In'
    Add-Edge $graph $id 'Out' ($id+1) 'In'
    Add-Edge $graph ($id+1) 'False' $id 'In'
    Add-Edge $graph ($id+1) 'True' ($id+2) 'In'
    Add-Edge $graph ($id+2) 'Out' ($id+3) 'In1'
    $rows += @{ name=$spec.name; depot=$depot; native_ref=$nativeRef; private_ref=$spec.private_ref; node=$id }
    $id += 10
}
$root = [WolvenKit.RED4.Types.questQuestPhaseResource]::new()
$root.CookingPlatform = [WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
Set-RedHandleProperty $root Graph $graph
$ownerFile = [WolvenKit.RED4.Archive.CR2W.CR2WFile]::new()
$ownerFile.RootChunk = $root
$resources += Write-Resource $ownerFile $plan.owner
$resources += Write-Resource $block $plan.block
Export-Cr2wJson (Read-Cr2wFile (Join-Path $sources $plan.owner)) (Join-Path $built 'owner.json')
@{ resources=$resources; sectors=$rows; plan_sha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'plan.json')).Hash } |
    ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $built 'build.json') -Encoding utf8NoBOM
