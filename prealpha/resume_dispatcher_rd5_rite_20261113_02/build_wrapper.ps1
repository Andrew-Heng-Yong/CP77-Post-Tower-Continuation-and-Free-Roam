# Add resume admission to the existing U9 owner. The graph is staged without registration or packing.
param([ValidatePattern('^graph_[0-9]+$')][string]$OutputDirectory = 'graph_06')
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out = Join-Path $PSScriptRoot $OutputDirectory
if (Test-Path -LiteralPath $out) { throw 'Fresh wrapper output required' }
$contract = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'entrance.json') | ConvertFrom-Json -AsHashtable
$guard = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/admission.json') | ConvertFrom-Json -AsHashtable
$check = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/entrance_assessment.json') | ConvertFrom-Json
if ($check.status -cne 'PASS_PRIVATE_PHASE_READBACK' -or (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'entrance.json')).Hash -cne $check.entrance_sha256) { throw 'Private graph review drift' }
$base = Join-Path $workspace 'prealpha/resume_dispatcher_rd4_20261113_01/deployment_01/installed_manifest_01.json'
if ((Get-FileHash -LiteralPath $base).Hash -cne '3DDA172011D2049A0EDBC4E006E6F40AE79F8751B23FAF0BEBCDC1706A62F0BC') { throw 'Baseline drift' }
$manifest = Get-Content -Raw -LiteralPath $base | ConvertFrom-Json
$path = 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$installedArchive = Join-Path $manifest.game_root $path
if ((Get-FileHash -LiteralPath $installedArchive).Hash -cne ($manifest.core_files | Where-Object path -CEQ $path).sha256) { throw 'Installed archive drift' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$names = [WolvenKit.Common.Services.HashService]::new()
$names.Load()
$archive = $null
if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($installedArchive, $names, [ref]$archive).ToString() -cne 'NoError') { throw 'Unreadable baseline archive' }
$depot = 'towercontinued\native_gigs_u9\sts_wat_nid_05_entry.questphase'
$key = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
$member = $archive.Files[[uint64]$key]
if ($null -eq $member) { throw "Missing installed entry: $key" }
[void][IO.Directory]::CreateDirectory($out)
$source = Join-Path $out 'entry.before.questphase'
$stream = [IO.File]::Open($source, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
try { $member.Extract($stream) } finally { $stream.Dispose() }
if ((Get-FileHash -LiteralPath $source).Hash -cne '750169485576D4ED9C4E635EEDBDA232F95AF56662A5D2ADD3268A201423C3B0') { throw 'Installed entry drift' }
$file = Read-Cr2wFile $source
$graph = $file.RootChunk.Graph.Chunk

function Fact([string]$Name,[int]$Value) {
  New-FactCondition $Name $Value ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)
}
function Logic([string]$Operation) {
  $condition = [WolvenKit.RED4.Types.questLogicalCondition]::new()
  $condition.Operation = [Enum]::Parse([WolvenKit.RED4.Types.Enums+questLogicalOperation], $Operation)
  return $condition
}
function Journal([string]$Path, [string]$Class, [int]$State, [int]$FileIndex) {
  $pathValue = [WolvenKit.RED4.Types.gameJournalPath]::new()
  $pathValue.ClassName = $Class
  $pathValue.RealPath = $Path
  $pathValue.FileEntryIndex = $FileIndex
  $type = [WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new()
  $type.State = [Enum]::Parse([WolvenKit.RED4.Types.Enums+gameJournalEntryState], @('Undefined','Inactive','Active','Succeeded','Failed')[$State])
  Set-RedHandleProperty $type 'Path' $pathValue
  $condition = [WolvenKit.RED4.Types.questJournalCondition]::new()
  Set-RedHandleProperty $condition 'Type' $type
  return $condition
}
function Add-Node($Node) {
  if (@($graph.Nodes | Where-Object { $_.Chunk.Id.ToString() -eq $Node.Id.ToString() }).Count) { throw 'Occupied node ID' }
  Add-RedHandle $graph.Nodes $Node
}
function Link([int]$From,[string]$SourceSocket,[int]$To,[string]$DestinationSocket) {
  [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $From) $SourceSocket) (Get-QuestSocket (Get-QuestNode $graph $To) $DestinationSocket))
}

$wait = Get-QuestNode $graph 65002
$choice = Logic 'OR'
$fresh = $wait.Condition.Chunk.DeepCopy()
Add-RedHandle $fresh.Conditions (Fact ($guard.tag+'ResumeRequested') 0)
Add-RedHandle $choice.Conditions $fresh
$earned = Logic 'AND'
foreach ($name in $guard.native_facts.Keys) { Add-RedHandle $earned.Conditions (Fact $name $guard.native_facts[$name]) }
foreach ($row in $guard.journals) { Add-RedHandle $earned.Conditions (Journal $row.path $row.class $row.live 4) }
foreach ($name in $guard.live_phone.Keys) { Add-RedHandle $earned.Conditions (Journal $name 'gameJournalPhoneMessage' $guard.live_phone[$name] 1) }
Add-RedHandle $choice.Conditions $earned
Set-RedHandleProperty $wait 'Condition' $choice

$claimOut = Get-QuestSocket (Get-QuestNode $graph 65003) 'Out'
$freshIn = Get-QuestSocket (Get-QuestNode $graph 2) 'In1'
if ($claimOut.Connections.Count -ne 1 -or $freshIn.Connections.Count -ne 1 -or
    ![object]::ReferenceEquals($claimOut.Connections[0].Chunk,$freshIn.Connections[0].Chunk)) { throw 'Claim boundary drift' }
$claimOut.Connections.Clear()
$freshIn.Connections.Clear()
Add-Node (New-ConditionNode 65010 (Fact ($guard.tag+'ResumeRequested') 1))
Add-Node (New-SetFactNode 65011 ($guard.tag+'Started') 1)
$resumed = (Get-QuestNode $graph 10).DeepCopy()
foreach ($socket in $resumed.Sockets) { $socket.Chunk.Connections.Clear() }
$resumed.Id = [uint16]65012
(Get-QuestSocket $resumed 'IN').Name = $contract.socket
$resumed.PhaseResource = [WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($contract.private_prefix + 'main.questphase')
Add-Node $resumed
$stock = Read-Cr2wFile (Join-Path $PSScriptRoot 'graph_01/streetstory.stock.questphase')
$template = Get-QuestNode (Get-QuestNode $stock.RootChunk.Graph.Chunk 3).PhaseGraph.Chunk 43
$ack = Logic 'AND'
for ($i = 0; $i -lt 2; $i++) {
  $row = $guard.journals[$i]
  if ($row.class -cnotin @('gameJournalQuest','gameJournalQuestPhase') -or $row.live -ne 4) { throw 'Quest hierarchy drift' }
  $node = $template.DeepCopy()
  foreach ($socket in $node.Sockets) { $socket.Chunk.Connections.Clear() }
  $node.Id = [uint16](65013 + $i)
  $node.Type.Chunk.Path.Chunk.RealPath = $row.path
  $node.Type.Chunk.Path.Chunk.ClassName = $row.class
  $node.Type.Chunk.SendNotification = $false
  $node.Type.Chunk.TrackQuest = $false
  Add-Node $node
  Add-RedHandle $ack.Conditions (Journal $row.path $row.class 2 4)
}
$acknowledgement = (Get-QuestNode $graph 65002).DeepCopy()
foreach ($socket in $acknowledgement.Sockets) { $socket.Chunk.Connections.Clear() }
$acknowledgement.Id = [uint16]65015
Set-RedHandleProperty $acknowledgement 'Condition' $ack
Add-Node $acknowledgement
Link 65003 'Out' 65010 'In'
Link 65010 'False' 2 'In1'
Link 65010 'True' 65013 'Active'
Link 65013 'Out' 65014 'Active'
Link 65014 'Out' 65015 'In'
Link 65015 'Out' 65011 'In'
Link 65011 'Out' 65012 $contract.socket
Link 65012 'OUT' 65005 'In'

$output = Join-Path $out 'entry.questphase'
Write-Cr2wFile $file $output
Export-Cr2wJson (Read-Cr2wFile $output) ($output+'.json')
@{status='UNPACKED_WRAPPER_READBACK'; depot=$depot; raw_sha256=(Get-FileHash -LiteralPath $output).Hash} |
  ConvertTo-Json | Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
