param([ValidateRange(1,99)][int]$Attempt = 1)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out = Join-Path $PSScriptRoot ('graph_{0:00}' -f $Attempt)
if (Test-Path -LiteralPath $out) { throw 'Fresh graph output required' }
$base = Join-Path $workspace 'prealpha/resume_dispatcher_rd10_kirk_20261113_01/archive_01/source/towercontinued/sidejobs_s29'
$entryPath = Join-Path $base 'entries/mq058_semimaru_crystalcoat.questphase'
$donorPath = Join-Path $base 'native/base/quest/minor_quests/mq058/phases/mq058_quest_resolution.questphase'
if ((Get-FileHash -LiteralPath $entryPath).Hash -cne '01DCC1A2957CAF0C165E6C931F17D87588062BDF7D42BD531A4B2D1AB7FF0AA3' -or
    (Get-FileHash -LiteralPath $donorPath).Hash -cne 'AC7834AEE036F3F69A917C945FC7A3E9EBF8CFC160FC03B3A1222D75E04E3D2D') {
    throw 'S29 resource drift'
}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')

function Add-Node($Graph,$Node) {
    if (@($Graph.Nodes | Where-Object { $_.Chunk.Id.ToString() -ceq $Node.Id.ToString() }).Count) {
        throw "Occupied graph node $($Node.Id)"
    }
    Add-RedHandle $Graph.Nodes $Node
}
function Link($Graph,[int]$From,[string]$FromSocket,[int]$To,[string]$ToSocket) {
    $source = Get-QuestSocket (Get-QuestNode $Graph $From) $FromSocket
    $destination = Get-QuestSocket (Get-QuestNode $Graph $To) $ToSocket
    [void](Connect-QuestSockets $source $destination)
}

# The reply child owns phone journal listeners and the native timer only.
$reply = Read-Cr2wFile $donorPath
$graph = $reply.RootChunk.Graph.Chunk
if ($reply.RootChunk.PhasePrefabs.Count -ne 0 -or $reply.RootChunk.InplacePhases.Count -ne 0) {
    throw 'Unexpected support on reply donor'
}
$keep = [Collections.Generic.HashSet[int]]::new()
foreach ($id in 1,80,84,88,89,90,91,92,93,94,95,96,97,98,99,104,106,108,109,110,111,114,115,116,117,118,119,190,191,198,201,203,205,206,208,209,210) {
    [void]$keep.Add($id)
}
$nodes = @{}
$sockets = [Collections.Generic.List[object]]::new()
foreach ($handle in $graph.Nodes) {
    $node = $handle.Chunk
    $id = [int]::Parse($node.Id.ToString())
    if (!$keep.Contains($id)) { continue }
    $nodes.Add($id, $node)
    foreach ($socket in $node.Sockets) {
        $sockets.Add(@($id, $socket.Chunk))
    }
}
if ($nodes.Count -ne $keep.Count) { throw 'Missing original reply nodes' }
$edges = [Collections.Generic.List[object]]::new()
foreach ($record in $sockets) {
    $source = $record[1]
    if ($source.Type.ToString() -notin @('Output','CutSource')) { continue }
    foreach ($link in $source.Connections) {
        $to = $link.Chunk.Destination.Chunk
        foreach ($target in $sockets) {
            if ([object]::ReferenceEquals($to, $target[1])) {
                $edges.Add(@($record[0], $source.Name.ToString(), $target[0], $to.Name.ToString()))
                break
            }
        }
    }
}
# Require the native timer's saved ID to be attached before listeners become
# actionable. The terminal reply never needs a callback for an unfunded wait.
$graph.Nodes.Clear()
foreach ($id in $nodes.Keys | Sort-Object) {
    $copy = $nodes[$id].DeepCopy()
    foreach ($socket in $copy.Sockets) { $socket.Chunk.Connections.Clear() }
    Add-Node $graph $copy
}
foreach ($edge in $edges) { Link $graph @edge }
Add-Node $graph (New-InputNode 61110 'Resume Claire Reply')
Link $graph 61110 'Out' 80 'In'
$arm = [WolvenKit.RED4.Types.questPauseConditionNodeDefinition]::new()
$arm.Id = [uint16]61111
Set-RedHandleProperty $arm 'Condition' (New-FactCondition 'PTFRClaire_TimerReady' 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
[void](New-QuestSocket $arm 'In' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
[void](New-QuestSocket $arm 'Out' ([WolvenKit.RED4.Types.Enums+questSocketType]::Output))
[void](New-QuestSocket $arm 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
Add-Node $graph $arm
Link $graph 61110 'Out' 61111 'In'
Link $graph 61111 'Out' 191 'In1'

$entry = Read-Cr2wFile $entryPath
$top = $entry.RootChunk.Graph.Chunk
$permit = [WolvenKit.RED4.Types.questPauseConditionNodeDefinition]::new()
$permit.Id = [uint16]61100
$requirements = [WolvenKit.RED4.Types.questLogicalCondition]::new()
$requirements.Operation = [WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
foreach ($required in @(@('PTFRClaire_Permit',1),@('PTFRClaire_Issued',0),@('PostTowerFreeRoamActive',1),
    @('q307_done',1),@('q307_finished',1),@('q307_main_game_killed',1),@('q307_ep1_killed',1),
    @('mq058_done',1),@('mq058_update_applied',1),@('mq058_active',0),@('PTFRS29_mq058_semimaru_crystalcoat_Issued',0))) {
    Add-RedHandle $requirements.Conditions (New-FactCondition $required[0] $required[1] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
}
Set-RedHandleProperty $permit 'Condition' $requirements
[void](New-QuestSocket $permit 'In' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
[void](New-QuestSocket $permit 'Out' ([WolvenKit.RED4.Types.Enums+questSocketType]::Output))
[void](New-QuestSocket $permit 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
Add-Node $top $permit
Add-Node $top (New-SetFactNode 61101 'PTFRClaire_Issued' 1)
$child = [WolvenKit.RED4.Types.questPhaseNodeDefinition]::new()
$child.Id = [uint16]61102
$depot = 'towercontinued\sidejobs_s29\continuation\mq058_claire_reply.questphase'
$child.PhaseResource = [Activator]::CreateInstance($child.GetType().GetProperty('PhaseResource').PropertyType,
    [object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($depot)))
[void](New-QuestSocket $child 'Resume Claire Reply' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
[void](New-QuestSocket $child 'Output' ([WolvenKit.RED4.Types.Enums+questSocketType]::Output))
[void](New-QuestSocket $child 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
Add-Node $top $child
Add-Node $top (New-SetFactNode 61103 'PTFRClaire_Finished' 1)
Link $top 65000 'Out' 61100 'In'
Link $top 61100 'Out' 61101 'In'
Link $top 61101 'Out' 61102 'Resume Claire Reply'
Link $top 61102 'Output' 61103 'In'

foreach ($part in @(@('entry',$entry),@('reply',$reply))) {
    $path = Join-Path $out ($part[0] + '.questphase')
    Write-Cr2wFile $part[1] $path
    Export-Cr2wJson (Read-Cr2wFile $path) ($path + '.json')
}
