# Build the existing S29 wrapper successor and the guarded private hook.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$pins = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/inputs.json') | ConvertFrom-Json -AsHashtable
$out = Join-Path $PSScriptRoot 'graph_02'
if (Test-Path -LiteralPath $out) { throw 'Fresh graph output required' }
$archive = Join-Path $pins.game 'archive/pc/mod/zzzz_PTFR_Combined.archive'
if ((Get-FileHash -LiteralPath $archive).Hash -cne $pins.archive_sha256) { throw 'Baseline drift' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$names = [WolvenKit.Common.Services.HashService]::new()
$names.Load()
$current = $null
if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$names,[ref]$current).ToString() -cne 'NoError') { throw 'Unreadable baseline' }
[void][IO.Directory]::CreateDirectory($out)
$original = Join-Path $out 'wrapper.original.questphase'
$stream = [IO.File]::Open($original,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
try { $current.Files[[uint64]$pins.wrapper.key].Extract($stream) } finally { $stream.Dispose() }
if ((Get-FileHash -LiteralPath $original).Hash -cne $pins.wrapper.sha256) { throw 'Wrapper drift' }
if ((Get-FileHash -LiteralPath $pins.parts.hook.raw).Hash -cne $pins.parts.hook.raw_sha256) { throw 'Hook drift' }
$tag = $pins.tag

function Logic([string]$Operation) {
    $node = [WolvenKit.RED4.Types.questLogicalCondition]::new()
    $node.Operation = [Enum]::Parse([WolvenKit.RED4.Types.Enums+questLogicalOperation],$Operation)
    $node
}
function Fact([string]$Name,[int]$Value) {
    New-FactCondition $Name $Value ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)
}
function Journal($Row,[int]$State) {
    $path = [WolvenKit.RED4.Types.gameJournalPath]::new()
    $path.RealPath = $Row.path
    $path.ClassName = $Row.class
    $path.FileEntryIndex = 2
    $leaf = [WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new()
    $leaf.State = [Enum]::Parse([WolvenKit.RED4.Types.Enums+gameJournalEntryState], @('Undefined','Inactive','Active','Succeeded','Failed')[$State])
    Set-RedHandleProperty $leaf Path $path
    $condition = [WolvenKit.RED4.Types.questJournalCondition]::new()
    Set-RedHandleProperty $condition Type $leaf
    $condition
}
function Add-Node($Graph,$Node) {
    if (@($Graph.Nodes | Where-Object { $_.Chunk.Id.ToString() -eq $Node.Id.ToString() }).Count) { throw 'Occupied node ID' }
    Add-RedHandle $Graph.Nodes $Node
}
function Copy-Node($Graph,$Node,[int]$Id) {
    $copy = $Node.DeepCopy()
    foreach ($socket in $copy.Sockets) { $socket.Chunk.Connections.Clear() }
    $copy.Id = [uint16]$Id
    Add-Node $Graph $copy
    $copy
}
function Wire($Graph,[int]$From,[string]$FromSocket,[int]$To,[string]$ToSocket) {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $Graph $From) $FromSocket) (Get-QuestSocket (Get-QuestNode $Graph $To) $ToSocket))
}
function Unwire($Graph,[int]$From,[string]$FromSocket,[int]$To,[string]$ToSocket) {
    $src = Get-QuestSocket (Get-QuestNode $Graph $From) $FromSocket
    $dst = Get-QuestSocket (Get-QuestNode $Graph $To) $ToSocket
    $edge = @($src.Connections | Where-Object { [object]::ReferenceEquals($_.Chunk.Source.Chunk,$src) -and [object]::ReferenceEquals($_.Chunk.Destination.Chunk,$dst) })
    if ($edge.Count -ne 1) { throw 'Expected one edge' }
    for ($i=$src.Connections.Count-1; $i -ge 0; $i--) {
        if ([object]::ReferenceEquals($src.Connections[$i].Chunk,$edge[0].Chunk)) { $src.Connections.RemoveAt($i) }
    }
    for ($i=$dst.Connections.Count-1; $i -ge 0; $i--) {
        if ([object]::ReferenceEquals($dst.Connections[$i].Chunk,$edge[0].Chunk)) { $dst.Connections.RemoveAt($i) }
    }
}
function Save-Part($File,[string]$Name,[string]$Depot) {
    $path = Join-Path $out "$Name.questphase"
    Write-Cr2wFile $File $path
    Export-Cr2wJson (Read-Cr2wFile $path) ($path + '.json')
    @{name=$Name; depot=$Depot; path=$path; sha256=(Get-FileHash -LiteralPath $path).Hash; export_sha256=(Get-FileHash -LiteralPath ($path+'.json')).Hash}
}

$wrapper = Read-Cr2wFile $original
$graph = $wrapper.RootChunk.Graph.Chunk
$wait = Get-QuestNode $graph 65003
$native = $wait.Condition.Chunk
$fresh = $native.DeepCopy()
Add-RedHandle $fresh.Conditions (Fact ($tag+'ResumeClaimed') 0)
$resume = Logic 'AND'
foreach ($leaf in $native.Conditions) {
    if ($leaf.Chunk -isnot [WolvenKit.RED4.Types.questFactsDBCondition]) { continue }
    $name = $leaf.Chunk.Type.Chunk.FactName.ToString()
    if ($name -match '^mq017_' -or $name -in @('PTFRS29_PHONE_kirk_Issued',($tag+'Permit'))) { continue }
    Add-RedHandle $resume.Conditions $leaf.Chunk.DeepCopy()
}
foreach ($name in $pins.facts.Keys) { Add-RedHandle $resume.Conditions (Fact $name $pins.facts[$name]) }
foreach ($name in @('PTFRS29_PHONE_kirk_Issued',($tag+'Permit'),($tag+'ResumeClaimed'),($tag+'ResumePhoneReleased'))) {
    Add-RedHandle $resume.Conditions (Fact $name 0)
}
foreach ($name in 'PTFRPH3_Entered','PTFRPH3_Ready',($tag+'ResumePermit')) { Add-RedHandle $resume.Conditions (Fact $name 1) }
foreach ($row in $pins.journals) { Add-RedHandle $resume.Conditions (Journal $row $row.live) }
$choice = Logic 'OR'
Add-RedHandle $choice.Conditions $fresh
Add-RedHandle $choice.Conditions $resume
Set-RedHandleProperty $wait Condition $choice
$gate = Get-QuestNode $graph 65004
Set-RedHandleProperty $gate Condition $fresh.DeepCopy()
Unwire $graph 65003 Out 65004 In
Add-Node $graph (New-ConditionNode 61000 $resume.DeepCopy())
Add-Node $graph (New-SetFactNode 61001 ($tag+'ResumeClaimed') 1)
$call = Copy-Node $graph (Get-QuestNode $graph 22) 61002
$call.PhaseResource = [WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($pins.parts.root.depot)
(Get-QuestSocket $call In1).Name = 'ResumeMeetKirk'
(Get-QuestNode $call.PhaseGraph.Chunk 0).SocketName = 'ResumeMeetKirk'
[void](New-QuestSocket $call ResumeRejected ([WolvenKit.RED4.Types.Enums+questSocketType]::Output))
Add-Node $call.PhaseGraph.Chunk (New-OutputNode 61020 ResumeRejected)
Add-Node $graph (New-SetFactNode 61003 ($tag+'Fault') 1)
Wire $graph 65003 Out 61000 In
Wire $graph 61000 True 61001 In
Wire $graph 61000 False 65004 In
Wire $graph 61001 Out 61002 ResumeMeetKirk
Wire $graph 61002 Out1 65007 In
Wire $graph 61002 ResumeRejected 61003 In

$hook = Read-Cr2wFile $pins.parts.hook.raw
$graph = $hook.RootChunk.Graph.Chunk
Unwire $graph 61000 Out 61001 Active
$journalTemplate = Get-QuestNode $graph 61001
$parents = @($pins.journals | Where-Object class -In 'gameJournalQuest','gameJournalQuestPhase' | Sort-Object { $_.path.Length })
if ($parents.Count -ne 2) { throw 'Unexpected quest hierarchy' }
$ack = Logic 'AND'
for ($i=0; $i -lt 2; $i++) {
    $row = $parents[$i]
    $journal = Copy-Node $graph $journalTemplate (61010+$i)
    $journal.Type.Chunk.Path.Chunk.ClassName = $row.class
    $journal.Type.Chunk.Path.Chunk.RealPath = $row.path
    $journal.Type.Chunk.SendNotification = $false
    $journal.Type.Chunk.TrackQuest = $false
    Add-RedHandle $ack.Conditions (Journal $row 2)
}
$objective = @($pins.journals | Where-Object { $_.path.EndsWith('/01_meet_kirk') })[0]
Add-RedHandle $ack.Conditions (Journal $objective 2)
$waitAck = Copy-Node $graph $wait 61012
Set-RedHandleProperty $waitAck Condition $ack
Add-Node $graph (New-SetFactNode 61013 ($tag+'Issued') 1)
Add-Node $graph (New-SetFactNode 61014 ($tag+'Entered') 1)
Unwire $graph 61001 Out 61002 In1
Wire $graph 61000 Out 61010 Active
Wire $graph 61010 Out 61011 Active
Wire $graph 61011 Out 61001 Active
Wire $graph 61001 Out 61012 In
Wire $graph 61012 Out 61013 In
Wire $graph 61013 Out 61014 In
Wire $graph 61014 Out 61002 In1

$bar = (Get-QuestNode $graph 61002).PhaseGraph.Chunk
$activate = Get-QuestNode $bar 3
$kirkWait = Get-QuestNode $bar 4
$spawnJoe = Copy-Node $bar $activate 10
$spawnJoe.Actions.RemoveAt(0)
$activate.Actions.RemoveAt(1)
$joeWait = Copy-Node $bar $kirkWait 11
$joeWait.Condition.Chunk.Type.Chunk.ObjectRef.Reference = '#mq017_big_joe'
$kirkCheck = New-ConditionNode 12 $kirkWait.Condition.Chunk.DeepCopy()
$joeCheck = New-ConditionNode 13 $joeWait.Condition.Chunk.DeepCopy()
Add-Node $bar $kirkCheck
Add-Node $bar $joeCheck
Unwire $bar 0 Out 3 In
Unwire $bar 4 Out 6 In
Wire $bar 0 Out 12 In
Wire $bar 12 True 13 In
Wire $bar 12 False 3 In
Wire $bar 4 Out 13 In
Wire $bar 13 True 6 In
Wire $bar 13 False 10 In
Wire $bar 10 Out 11 In
Wire $bar 11 Out 6 In

$results = @(Save-Part $wrapper wrapper $pins.wrapper.depot; Save-Part $hook hook $pins.parts.hook.depot)
@{resources=$results; input_sha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/inputs.json')).Hash} |
    ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
