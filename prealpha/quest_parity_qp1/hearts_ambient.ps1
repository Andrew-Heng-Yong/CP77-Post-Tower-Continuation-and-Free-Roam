# Used by heavy_hearts.ps1 with the pinned native club and marker providers.
function AmbientLogic([string]$op) {
    $condition = [WolvenKit.RED4.Types.questLogicalCondition]::new()
    $condition.Operation = [WolvenKit.RED4.Types.Enums+questLogicalOperation]::$op
    return $condition
}
function AmbientWait([int]$id, $condition) {
    $node = [WolvenKit.RED4.Types.questPauseConditionNodeDefinition]::new()
    $node.Id = [uint16]$id
    Set-RedHandleProperty $node Condition $condition
    [void](New-QuestSocket $node 'CutDestination' CutDestination)
    [void](New-QuestSocket $node 'In' Input)
    [void](New-QuestSocket $node 'Out' Output)
    return $node
}
function AmbientEdge($graph, [int]$from, [string]$output, [int]$to, [string]$inputSocket) {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $from) $output) (Get-QuestSocket (Get-QuestNode $graph $to) $inputSocket))
}
function AmbientCut([int]$id) {
    $node = [WolvenKit.RED4.Types.questCutControlNodeDefinition]::new()
    $node.Id = [uint16]$id
    [void](New-QuestSocket $node 'In' Input)
    [void](New-QuestSocket $node 'CutSource' CutSource)
    [void](New-QuestSocket $node 'Out' Output)
    return $node
}
function AmbientPhase([int]$id, $inner) {
    $node = [WolvenKit.RED4.Types.questPhaseNodeDefinition]::new()
    $node.Id = [uint16]$id
    Set-RedHandleProperty $node PhaseGraph $inner
    [void](New-QuestSocket $node 'CutDestination' CutDestination)
    [void](New-QuestSocket $node 'In1' Input)
    [void](New-QuestSocket $node 'Out1' Output)
    return $node
}
function AmbientCaller($donor, [string]$inputSocket, [string]$endSocket) {
    $null = Get-QuestSocket $donor $inputSocket
    if ($endSocket) { $null = Get-QuestSocket $donor $endSocket }
    if (!$markerRows.ContainsKey($donor.SceneLocation.NodeRef.ToString())) { throw 'Unverified ambient scene marker' }
    $node = [WolvenKit.RED4.Types.questSceneNodeDefinition]::new()
    $node.Id = [uint16]1
    $node.SceneFile = $donor.SceneFile
    $node.SceneLocation = $donor.SceneLocation.DeepCopy()
    $node.NotAllowedToBeFrozen = $donor.NotAllowedToBeFrozen
    $node.ReapplyInterruptionOperationsAfterGameLoad = $donor.ReapplyInterruptionOperationsAfterGameLoad
    $node.SyncToMusic = $donor.SyncToMusic
    foreach ($operation in $donor.InterruptionOperations) {
        Add-RedHandle $node.InterruptionOperations ($operation.Chunk.DeepCopy())
    }
    [void](New-QuestSocket $node 'CutDestination' CutDestination)
    [void](New-QuestSocket $node $inputSocket Input)
    if ($endSocket) { [void](New-QuestSocket $node $endSocket Output) }
    return $node
}
function AmbientFacts($values, [bool]$enter) {
    $condition = if ($enter) { AmbientLogic 'AND' } else { AmbientLogic 'OR' }
    $compare = if ($enter) { 'Equal' } else { 'NotEqual' }
    foreach ($fact in ($values.Keys | Sort-Object)) {
        Add-RedHandle $condition.Conditions (New-FactCondition $fact $values[$fact] $compare)
    }
    return $condition
}
function AmbientActor($donor, [string]$actor, [bool]$present) {
    $condition = $donor.DeepCopy()
    $type = $condition.Type.Chunk
    if ($type.GetType().Name -cne 'questCharacterSpawned_ConditionType' -or $type.ObjectRef.Names.Count -ne 1 -or
        $type.ObjectRef.Reference.ToString() -cne '#sts_ep1_06_com_civilians') { throw 'NPC condition donor drift' }
    $type.ObjectRef.Names[0] = [WolvenKit.RED4.Types.CName]::op_Implicit($actor)
    if (!$present) { $type.ComparisonParams.Chunk.ComparisonType = [WolvenKit.RED4.Types.Enums+EComparisonType]::NotEqual }
    return $condition
}
function AddAmbientRoute($holder, $spec, $facts, $spawned) {
    $id = $spec.id
    $ready = AmbientFacts $facts $true
    $stop = AmbientFacts $facts $false
    Add-RedHandle $ready.Conditions ($spec.approach.DeepCopy())
    Add-RedHandle $ready.Conditions (New-FactCondition $spec.earned 1 GreaterOrEqual)
    Add-RedHandle $stop.Conditions (New-FactCondition $spec.earned 1 Less)
    foreach ($actor in $spec.actors) {
        Add-RedHandle $ready.Conditions (AmbientActor $spawned $actor $true)
        Add-RedHandle $stop.Conditions (AmbientActor $spawned $actor $false)
    }
    if ($spec.rearm) { Add-RedHandle $stop.Conditions ($spec.departure.DeepCopy()) }

    $inner = [WolvenKit.RED4.Types.questGraphDefinition]::new()
    Add-RedHandle $inner.Nodes (New-InputNode 0 'In1')
    Add-RedHandle $inner.Nodes (AmbientCaller $spec.donor $spec.input $spec.end)
    Add-RedHandle $inner.Nodes (AmbientWait 2 $stop)
    Add-RedHandle $inner.Nodes (New-OutputNode 3 'Out1')
    AmbientEdge $inner 0 'Out' 1 $spec.input
    AmbientEdge $inner 0 'Out' 2 'In'
    AmbientEdge $inner 2 'Out' 3 'In'
    if ($spec.end) { AmbientEdge $inner 1 $spec.end 3 'In' }

    Add-RedHandle $holder.Nodes (AmbientWait $id $ready)
    Add-RedHandle $holder.Nodes (New-ConditionNode ($id+1) ($ready.DeepCopy()))
    Add-RedHandle $holder.Nodes (AmbientPhase ($id+2) $inner)
    Add-RedHandle $holder.Nodes (AmbientCut ($id+3))
    AmbientEdge $holder 0 'Out' $id 'In'
    AmbientEdge $holder $id 'Out' ($id+1) 'In'
    AmbientEdge $holder ($id+1) 'False' $id 'In'
    AmbientEdge $holder ($id+1) 'True' ($id+2) 'In1'
    AmbientEdge $holder ($id+2) 'Out1' ($id+3) 'In'
    AmbientEdge $holder ($id+3) 'CutSource' ($id+2) 'CutDestination'
    if ($spec.rearm) { AmbientEdge $holder ($id+3) 'Out' $id 'In' }
}
function NewHeavyHeartsAmbient {
    $ambient = (Get-QuestNode $club.Graph.Chunk 1).PhaseGraph.Chunk
    $dealer = (Get-QuestNode $ambient 341).PhaseGraph.Chunk
    $spawned = (Get-QuestNode $dealer 6).Condition.Chunk

    $base = [ordered]@{}
    $available = @{}
    foreach ($fact in ($hh1Plan.guard.Keys | Sort-Object)) {
        if ($fact.StartsWith('sts_ep1_06_')) { $available.Add($fact, $hh1Plan.guard[$fact]) }
        else { $base.Add($fact, $hh1Plan.guard[$fact]) }
    }
    $base.Add('PTFRPA2_Fault',0)
    $base.Add('q307_debug_reset',0)
    $available.Add('sts_ep1_06_active',0)
    $available.Add('sts_ep1_06_alarm_raised',0)
    $chats = $available.Clone()
    $chats.Add('mq304_active',0)
    $vendor = $available.Clone()
    $vendor.Add('sts_ep1_06_dealer_scared',0)
    $vendor.Add('sts_ep1_06_drug_dealer_default_on',1)

    $holder = [WolvenKit.RED4.Types.questGraphDefinition]::new()
    Add-RedHandle $holder.Nodes (New-InputNode 0 'In1')
    Add-RedHandle $holder.Nodes (AmbientWait 1 (AmbientFacts $base $false))
    Add-RedHandle $holder.Nodes (New-OutputNode 2 'Out1')
    AmbientEdge $holder 0 'Out' 1 'In'
    AmbientEdge $holder 1 'Out' 2 'In'
    AddAmbientRoute $holder @{
        id=10; donor=(Get-QuestNode $ambient 370); input='Start 0'; end='End 0'; rearm=$false
        approach=(Get-QuestNode $ambient 369).Condition.Chunk; earned='q304_kurt_dead'
        actors=@('chat_kurtz_001a','chat_kurtz_001b')
    } $chats $spawned
    AddAmbientRoute $holder @{
        id=20; donor=(Get-QuestNode $ambient 371); input='Start1'; end='End1'; rearm=$false
        approach=(Get-QuestNode $ambient 372).Condition.Chunk; earned='q304_kurt_dead'
        actors=@('chat_kurtz_002a','chat_kurtz_002b')
    } $chats $spawned
    AddAmbientRoute $holder @{
        id=30; donor=(Get-QuestNode $dealer 2); input='dealing'; end=''; rearm=$true
        approach=(Get-QuestNode $ambient 342).Condition.Chunk; earned='sts_ep1_06_drug_dealer_info'
        departure=(Get-QuestNode $dealer 3).Condition.Chunk; actors=@('drug_dealer')
    } $vendor $spawned

    $graph = [WolvenKit.RED4.Types.questGraphDefinition]::new()
    $ready = AmbientFacts $base $true
    $lease = AmbientPhase 3 $holder
    $lease.PhaseInstancePrefabs.Add((LeasePrefab $areaSets[1].ref))
    Add-RedHandle $graph.Nodes (New-InputNode 0 'In1')
    Add-RedHandle $graph.Nodes (AmbientWait 1 $ready)
    Add-RedHandle $graph.Nodes (New-ConditionNode 2 ($ready.DeepCopy()))
    Add-RedHandle $graph.Nodes $lease
    Add-RedHandle $graph.Nodes (AmbientCut 4)
    AmbientEdge $graph 0 'Out' 1 'In'
    AmbientEdge $graph 1 'Out' 2 'In'
    AmbientEdge $graph 2 'False' 1 'In'
    AmbientEdge $graph 2 'True' 3 'In1'
    AmbientEdge $graph 3 'Out1' 4 'In'
    AmbientEdge $graph 4 'CutSource' 3 'CutDestination'

    $root = [WolvenKit.RED4.Types.questQuestPhaseResource]::new()
    $root.CookingPlatform = [WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
    Set-RedHandleProperty $root Graph $graph
    $file = [WolvenKit.RED4.Archive.CR2W.CR2WFile]::new()
    $file.RootChunk = $root
    return $file
}
