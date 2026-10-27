Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')

$prior = Join-Path $ws 'prealpha/coaster_jean_jc1/candidate_01'
$out = Join-Path $PSScriptRoot 'candidate_04'
if (Test-Path -LiteralPath $out) { throw 'Use a successor candidate, never overwrite an earlier build.' }
$source = Join-Path $out 'archive_source'
$package = Join-Path $out 'package'
Copy-Item -LiteralPath (Join-Path $prior 'archive_source') -Destination $source -Recurse
Copy-Item -LiteralPath (Join-Path $prior 'package') -Destination $package -Recurse

$before = @{}
foreach ($p in Get-ChildItem -LiteralPath $source -File -Recurse) {
  $rel = [IO.Path]::GetRelativePath($source, $p.FullName).Replace('/', '\')
  $before[$rel] = (Get-FileHash -LiteralPath $p.FullName).Hash
}
if ($before.Count -ne 1172) { throw "JC1 baseline has $($before.Count) resources, expected 1172" }

# Rehost only vanilla Coastview combat-event loop 116. It is dormant until
# explicitly requested on a disposable completed-Tower save. This is a
# diagnostic successor, not the citywide production repair.
$nativePath = Join-Path $ws 'diagnostics/world_npc_idle_20261026_01/combat_owners/base_open_world_combat_events_pacifica_coastview_ce_pac_cvi_phase.questphase'
$native = Read-Cr2wFile $nativePath
$nested = (Get-QuestNode -Graph $native.RootChunk.Graph.Chunk -Id 28).PhaseGraph.Chunk
$loop = (Get-QuestNode -Graph $nested -Id 18).PhaseGraph.Chunk.DeepCopy()
$input = Get-QuestNode -Graph $loop -Id 0
$reactivate = Get-QuestNode -Graph $loop -Id 2
$inOut = Get-QuestSocket -Node $input -Name 'Out'
$reactivateIn = Get-QuestSocket -Node $reactivate -Name 'In'
if ($inOut.Connections.Count -ne 1 -or $reactivateIn.Connections.Count -ne 2) { throw 'Native loop input contract changed' }
# Nested graph handles do not preserve connection identity when moved into a
# standalone CR2W resource. Rebuild each original edge from a pinned decode.
foreach ($node in $loop.Nodes) {
  foreach ($socket in $node.Chunk.Sockets) { $socket.Chunk.Connections.Clear() }
}

$entryTemplate = Read-Cr2wFile (Join-Path $source 'towercontinued/sidejobs_s30/entries/mq006_rollercoaster.questphase')
$pauseTemplate = Get-QuestNode -Graph $entryTemplate.RootChunk.Graph.Chunk -Id 65003
$gate = $pauseTemplate.DeepCopy()
$gate.Id = [uint16]65000
foreach ($socket in $gate.Sockets) { $socket.Chunk.Connections.Clear() }
$condition = [WolvenKit.RED4.Types.questLogicalCondition]::new()
$condition.Operation = [WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
foreach ($f in @('q307_main_game_killed', 'q307_ep1_killed', 'PTFRWA1_TestRequest')) {
  Add-RedHandle -Array $condition.Conditions -Chunk (New-FactCondition -FactName $f -Value 1 -Comparison ([WolvenKit.RED4.Types.Enums+EComparisonType]::GreaterOrEqual))
}
Set-RedHandleProperty -Owner $gate -PropertyName 'Condition' -Chunk $condition
Add-RedHandle -Array $loop.Nodes -Chunk $gate
$nativeEdges = @(Get-Content -LiteralPath (Join-Path $PSScriptRoot 'native_loop_edges_01.json') -Raw | ConvertFrom-Json)
if ($nativeEdges.Count -ne 13 -or $nativeEdges[0][0] -ne 0 -or $nativeEdges[0][2] -ne 2) { throw 'Native edge contract changed' }
foreach ($edge in $nativeEdges | Select-Object -Skip 1) {
  $from = Get-QuestSocket -Node (Get-QuestNode -Graph $loop -Id ([int]$edge[0])) -Name ([string]$edge[1])
  $to = Get-QuestSocket -Node (Get-QuestNode -Graph $loop -Id ([int]$edge[2])) -Name ([string]$edge[3])
  [void](Connect-QuestSockets -Source $from -Destination $to)
}
[void](Connect-QuestSockets -Source $inOut -Destination (Get-QuestSocket -Node $gate -Name 'In'))
[void](Connect-QuestSockets -Source (Get-QuestSocket -Node $gate -Name 'Out') -Destination $reactivateIn)

$resource = Read-Cr2wFile (Join-Path $source 'towercontinued/sidejobs_s30/entries/mq006_rollercoaster.questphase')
Set-RedHandleProperty -Owner $resource.RootChunk -PropertyName 'Graph' -Chunk $loop
$relative = 'towercontinued\world_combat_wa1\ce_pac_cvi_116_probe.questphase'
$target = Join-Path $source $relative
New-Item -ItemType Directory -Force (Split-Path $target -Parent) | Out-Null
Write-Cr2wFile $resource $target
$readback = Join-Path $out 'probe_readback_01.json'
Export-Cr2wJson (Read-Cr2wFile $target) $readback

$xlPath = Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
$xl = [IO.File]::ReadAllText($xlPath)
$newline = if ($xl.Contains("`r`n")) { "`r`n" } else { "`n" }
$head = "quest:${newline}  phases:${newline}"
if (!$xl.StartsWith($head, [StringComparison]::Ordinal) -or $xl.Contains('ce_pac_cvi_116_probe.questphase')) { throw 'Unexpected XL phase list' }
$stanza = @"
    - path: towercontinued\world_combat_wa1\ce_pac_cvi_116_probe.questphase
      parent: ep1\quest\ep1.quest
      input:
        node: [1]
        socket: Out
"@
$xl = $xl.Replace($head, $head + $stanza.Replace("`r`n", "`n").Replace("`n", $newline) + $newline)
[IO.File]::WriteAllText($xlPath, $xl, [Text.UTF8Encoding]::new($false))

$after = @{}
foreach ($p in Get-ChildItem -LiteralPath $source -File -Recurse) {
  $rel = [IO.Path]::GetRelativePath($source, $p.FullName).Replace('/', '\')
  $after[$rel] = (Get-FileHash -LiteralPath $p.FullName).Hash
  if ($before.ContainsKey($rel) -and $after[$rel] -cne $before[$rel]) { throw "Baseline resource drift $rel" }
}
if ($after.Count -ne 1173 -or !$after.ContainsKey($relative)) { throw 'Probe resource census failed' }

$archivePath = Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$stream = [IO.File]::Create($archivePath)
$hs = [WolvenKit.Common.Services.HashService]::new(); $hs.Load()
try {
  if (-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs, [WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source), $stream)) { throw 'Archive writer failed' }
} finally { $stream.Dispose() }
$packed = $null
if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archivePath, $hs, [ref]$packed).ToString() -cne 'NoError' -or $packed.Files.Count -ne 1173) { throw 'Archive readback failed' }
foreach ($e in $packed.Files.Values) {
  $expected = $after[$e.Name]
  if (!$expected) { throw "Unexpected packed resource $($e.Name)" }
  $m = [IO.MemoryStream]::new()
  try { $e.Extract($m); $hash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray())) } finally { $m.Dispose() }
  if ($hash -cne $expected) { throw "Packed resource mismatch $($e.Name)" }
}
$files = @(Get-ChildItem -LiteralPath $package -File -Recurse)
if ($files.Count -ne 51) { throw "Package file count $($files.Count)" }
$manifest = [ordered]@{
  status = 'WA1_ONE_GROUP_GATED_TEST_STAGED_NOT_INSTALLED'
  source_members = 1173
  new_resource = $relative
  files = @($files | ForEach-Object { @{ path = [IO.Path]::GetRelativePath($package, $_.FullName).Replace('\', '/'); sha256 = (Get-FileHash -LiteralPath $_.FullName).Hash } })
}
[IO.File]::WriteAllText((Join-Path $out 'manifest.json'), ($manifest | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))
@{ status = $manifest.status; members = 1173; package_files = 51 } | ConvertTo-Json
