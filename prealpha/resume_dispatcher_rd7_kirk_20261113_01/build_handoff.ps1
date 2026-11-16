# Stage the original pre-bar gates and Kirk's native call cleanup in the private root.
param([ValidatePattern('^graph_[0-9]+$')][string]$OutputDirectory = 'graph_05')
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$evidence = Join-Path $PSScriptRoot 'evidence_02'
$watch = Join-Path $evidence 'provider_watch.json'
$pins = Get-Content -Raw -LiteralPath $watch | ConvertFrom-Json -AsHashtable
$out = Join-Path $PSScriptRoot $OutputDirectory
if (Test-Path -LiteralPath $out) { throw 'Fresh graph output required' }
$archive = Join-Path $pins.game 'archive/pc/mod/zzzz_PTFR_Combined.archive'
if ((Get-FileHash -LiteralPath $archive).Hash -cne $pins.archive_sha256 -or
    (Get-FileHash -LiteralPath (Join-Path $pins.game $pins.xl.path)).Hash -cne $pins.xl.sha256) { throw 'Installed input drift' }
foreach ($part in $pins.parts.Values) {
    if ((Get-FileHash -LiteralPath $part.raw).Hash -cne $part.raw_sha256) { throw 'Staged entrance drift' }
}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$names = [WolvenKit.Common.Services.HashService]::new()
$names.Load()
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
$installed = $null
if ($reader.ReadArchive($archive, $names, [ref]$installed).ToString() -cne 'NoError') { throw 'Unreadable combined archive' }
$privateKeys = @($pins.parts.Values | ForEach-Object { [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($_.depot) })
if (@($privateKeys | Sort-Object -Unique).Count -ne $pins.parts.Count) { throw 'Private key collision' }
$archives = @(foreach ($relative in 'archive/pc','mods') {
    $root = Join-Path $pins.game $relative
    if (!(Test-Path -LiteralPath $root)) { continue }
    if ((Get-Item -LiteralPath $root -Force).Attributes -band [IO.FileAttributes]::ReparsePoint -or
        @(Get-ChildItem -LiteralPath $root -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked archive tree' }
    Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.archive'
})
$seen = [Collections.Generic.HashSet[uint64]]::new()
foreach ($file in $archives) {
    $stamp = @($file.Length,$file.LastWriteTimeUtc.Ticks)
    $provider = $null
    if ($reader.ReadArchive($file.FullName, $names, [ref]$provider).ToString() -cne 'NoError') { throw "Unreadable archive $file" }
    foreach ($key in $privateKeys) {
        if ($provider.Files.ContainsKey($key)) { throw "Private depot is already occupied $key" }
    }
    foreach ($pin in $pins.resources) {
        $key = [uint64]$pin.key
        if ($key -ne [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($pin.depot)) { throw 'Provider key drift' }
        if (!$provider.Files.ContainsKey($key)) { continue }
        if ($pin.archive -ine $file.FullName -or !$seen.Add($key)) { throw "Unexpected provider for $($pin.depot)" }
        $memory = [IO.MemoryStream]::new()
        try {
            $provider.Files[$key].Extract($memory)
            $memory.Position = 0
            if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory)) -cne $pin.sha256) { throw "Provider drift for $($pin.depot)" }
        } finally { $memory.Dispose() }
    }
    $file.Refresh()
    if ($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1]) { throw 'Archive changed during review' }
}
if ($seen.Count -ne $pins.resources.Count) { throw 'Missing provider' }
[void][IO.Directory]::CreateDirectory($out)

function Read-Donor([int]$Id) {
    $pin = @($pins.resources | Where-Object rid -EQ $Id)
    if ($pin.Count -ne 1 -or $pin[0].archive -ine $archive) { throw "Unpinned donor $Id" }
    $path = Join-Path $out "$Id.original.questphase"
    $file = [IO.File]::Open($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
    try { $installed.Files[[uint64]$pin[0].key].Extract($file) } finally { $file.Dispose() }
    if ((Get-FileHash -LiteralPath $path).Hash -cne $pin[0].sha256) { throw "Donor drift $Id" }
    (Read-Cr2wFile $path).RootChunk.Graph.Chunk
}
function Add-Node($Node) {
    if (@($graph.Nodes | Where-Object { $_.Chunk.Id.ToString() -eq $Node.Id.ToString() }).Count) { throw 'Occupied graph ID' }
    Add-RedHandle $graph.Nodes $Node
}
function Copy-Node($Source, [int]$SourceId, [int]$NewId) {
    $node = (Get-QuestNode $Source $SourceId).DeepCopy()
    $node.Id = [uint16]$NewId
    foreach ($socket in $node.Sockets) { $socket.Chunk.Connections.Clear() }
    Add-Node $node
    return $node
}
function Link([int]$From,[string]$FromSocket,[int]$To,[string]$ToSocket) {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $From) $FromSocket) (Get-QuestSocket (Get-QuestNode $graph $To) $ToSocket))
}
function Equal-Fact([string]$Name,[int]$Value) {
    New-FactCondition $Name $Value ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)
}
function Logic([string]$Operation) {
    $condition = [WolvenKit.RED4.Types.questLogicalCondition]::new()
    $condition.Operation = [Enum]::Parse([WolvenKit.RED4.Types.Enums+questLogicalOperation], $Operation)
    return $condition
}
function Equal-Counters([string]$Prefix) {
    $type = [WolvenKit.RED4.Types.questVarVsVarComparison_ConditionType]::new()
    $type.FactName1 = $Prefix + '_start_count'
    $type.FactName2 = $Prefix + '_end_count'
    $type.ComparisonType = [WolvenKit.RED4.Types.Enums+EComparisonType]::Equal
    $condition = [WolvenKit.RED4.Types.questFactsDBCondition]::new()
    Set-RedHandleProperty $condition Type $type
    return $condition
}

$body = Read-Cr2wFile $pins.parts.root.raw
$graph = $body.RootChunk.Graph.Chunk
[void](Read-Donor 14599)
$phoneFile = Read-Cr2wFile (Join-Path $out '14599.original.questphase')
$phone = $phoneFile.RootChunk.Graph.Chunk
$cleanup = Read-Donor 15154
$direct = Get-QuestSocket (Get-QuestNode $graph 61000) 'Out'
$target = Get-QuestSocket (Get-QuestNode $graph 24) 'ResumeMeetKirk'
if ($direct.Connections.Count -ne 1 -or $target.Connections.Count -ne 1 -or
    ![object]::ReferenceEquals($direct.Connections[0].Chunk,$target.Connections[0].Chunk)) { throw 'Stage boundary drift' }
$direct.Connections.Clear()
$target.Connections.Clear()

# Clone the native route selection and both spatial/content waits. A rejected
# lifepath has a distinct exit so a future caller cannot treat it as completion.
$nativeGates = @{61010=9; 61011=31; 61012=28; 61013=23; 61014=33}
foreach ($id in ($nativeGates.Keys | Sort-Object)) { [void](Copy-Node $graph $nativeGates[$id] $id) }
Add-Node (New-OutputNode 61020 'ResumeRejected')

$receipt = 'PTFRS29_mq017_streetkid_ResumePhoneReleased'
$claim = 'PTFRS29_mq017_streetkid_ResumeClaimed'
$permit = 'PTFRS29_mq017_streetkid_Permit'
$issued = 'PTFRS29_PHONE_kirk_Issued'
$before = Copy-Node $phone 1002 61015
$clauses = $before.Condition.Chunk.Conditions
$permitLeaf = @($clauses | Where-Object { $_.Chunk.Type.Chunk.FactName.ToString() -ceq $permit })
if ($permitLeaf.Count -ne 1 -or $permitLeaf[0].Chunk.Type.Chunk.Value.ToString() -cne '1') { throw 'Phone permit predicate drift' }
$permitLeaf[0].Chunk.Type.Chunk.Value = 0
Add-RedHandle $clauses (Equal-Fact $receipt 0)
Add-RedHandle $clauses (Equal-Fact $claim 1)
Add-RedHandle $clauses (Equal-Fact 'PTFRPH3_Entered' 1)
Add-RedHandle $clauses (Equal-Fact 'PTFRPH3_Ready' 1)
[void](Copy-Node $cleanup 1201 61016)
$released = Copy-Node $graph 61015 61017
$releasedClauses = $released.Condition.Chunk.Conditions
Add-RedHandle $releasedClauses (Equal-Fact 'holo_kirk_calls_v_start_count' 2)
Add-RedHandle $releasedClauses (Equal-Fact 'holo_kirk_calls_v_end_count' 2)
Add-RedHandle $releasedClauses (Equal-Fact 'holo_v_calls_kirk_start_count' 0)
Add-RedHandle $releasedClauses (Equal-Fact 'holo_v_calls_kirk_end_count' 0)
Add-RedHandle $clauses (Equal-Fact 'holo_kirk_calls_v_start_count' 2)
Add-RedHandle $clauses (Equal-Fact 'holo_kirk_calls_v_end_count' 1)
Add-RedHandle $clauses (Equal-Fact 'holo_kirk_calls_v_interrupted' 1)
Add-RedHandle $clauses (Equal-Fact 'holo_v_calls_kirk_start_count' 0)
Add-RedHandle $clauses (Equal-Fact 'holo_v_calls_kirk_end_count' 0)
Add-RedHandle $clauses (Equal-Fact 'holo_kirk_calls_v_rejected_branch' 0)
Add-Node (New-SetFactNode 61018 $receipt 1)
$listener = Copy-Node $phone 1002 61019
$condition = Logic 'AND'
Add-RedHandle $condition.Conditions (Equal-Fact $claim 1)
Add-RedHandle $condition.Conditions (Equal-Fact $receipt 1)
Add-RedHandle $condition.Conditions (Equal-Fact $issued 1)
Set-RedHandleProperty $listener Condition $condition

Link 61000 Out 61010 In
Link 61010 True 61015 In
Link 61010 False 61020 In
Link 61011 True 61012 In
Link 61011 False 61014 In
Link 61012 Out 61013 In
Link 61013 Out 24 ResumeMeetKirk
Link 61014 Out 24 ResumeMeetKirk
Link 61015 Out 61016 In28
Link 61016 Out28 61017 In
Link 61017 Out 61018 In
Link 61018 Out 61019 In
Link 61019 Out 61011 In

# Use the already-registered Kirk listener and its real Issued writer. Only the
# fresh Permit leaf is widened. Both the wait and the final check use it.
foreach ($id in 1002,1003) {
    $clauses = (Get-QuestNode $phone $id).Condition.Chunk.Conditions
    $index = @(for ($i=0; $i -lt $clauses.Count; $i++) {
        if ($clauses[$i].Chunk.Type.Chunk.FactName.ToString() -ceq $permit) { $i }
    })
    if ($index.Count -ne 1) { throw 'Missing phone permit predicate' }
    $choose = Logic 'OR'
    Add-RedHandle $choose.Conditions $clauses[$index[0]].Chunk.DeepCopy()
    $resume = Logic 'AND'
    Add-RedHandle $resume.Conditions (Equal-Fact $claim 1)
    Add-RedHandle $resume.Conditions (Equal-Fact $receipt 1)
    Add-RedHandle $resume.Conditions (Equal-Fact $permit 0)
    Add-RedHandle $resume.Conditions (Equal-Fact 'PTFRPH3_Entered' 1)
    Add-RedHandle $resume.Conditions (Equal-Fact 'PTFRPH3_Ready' 1)
    Add-RedHandle $resume.Conditions (Equal-Counters 'holo_kirk_calls_v')
    Add-RedHandle $resume.Conditions (Equal-Counters 'holo_v_calls_kirk')
    Add-RedHandle $choose.Conditions $resume
    $clauses.RemoveAt($index[0])
    Add-RedHandle $clauses $choose
}

$output = Join-Path $out 'root.questphase'
Write-Cr2wFile $body $output
Export-Cr2wJson (Read-Cr2wFile $output) ($output + '.json')
$phoneOutput = Join-Path $out 'kirk.questphase'
Write-Cr2wFile $phoneFile $phoneOutput
Export-Cr2wJson (Read-Cr2wFile $phoneOutput) ($phoneOutput + '.json')
@{status='UNREGISTERED_KIRK_HANDOFF'; archive_count=$archives.Count; provider_count=$seen.Count;
    source_sha256=$pins.parts.root.raw_sha256; raw_sha256=(Get-FileHash -LiteralPath $output).Hash;
    export_sha256=(Get-FileHash -LiteralPath ($output + '.json')).Hash; depot=$pins.parts.root.depot;
    phone=@{rid=14599; raw_sha256=(Get-FileHash -LiteralPath $phoneOutput).Hash;
        export_sha256=(Get-FileHash -LiteralPath ($phoneOutput + '.json')).Hash}} |
  ConvertTo-Json | Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
