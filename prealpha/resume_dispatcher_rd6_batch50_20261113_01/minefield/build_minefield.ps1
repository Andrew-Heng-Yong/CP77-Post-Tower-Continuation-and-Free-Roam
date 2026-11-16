# Preserve the prior offline body and serialize a successor at the same staged private depot.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$prealpha = (Get-Item -LiteralPath $PSScriptRoot).Parent.Parent.FullName
$workspace = Split-Path -Parent $prealpha
$prior = Join-Path $prealpha 'resume_dispatcher_rd6_gigs_20261113_01/graph_02/sts_bls_ina_07_body.questphase'
$priorHash = 'BE396E57630034C5814B41A5DC06A93B053E8D03DA34E85681C7278CEEA38CC6'
if ((Get-FileHash -LiteralPath $prior).Hash -cne $priorHash) { throw 'Prior Minefield body drift' }
$manifest = Join-Path $prealpha 'resume_dispatcher_rd5_rite_20261113_02/deployment_01/installed_manifest_01.json'
$manifestHash = 'C298EA55F984CB0CAC95388848705C9B15C7CCD74958EE901C794BDFDEE28C36'
if ((Get-FileHash -LiteralPath $manifest).Hash -cne $manifestHash) { throw 'Installed manifest drift' }
$baseline = Get-Content -Raw -LiteralPath $manifest | ConvertFrom-Json -AsHashtable
$installed = Join-Path $baseline.game_root 'archive/pc/mod/zzzz_PTFR_Combined.archive'
if ((Get-FileHash -LiteralPath $installed).Hash -cne $baseline.archive_sha256) { throw 'Installed archive drift' }
$out = Join-Path $PSScriptRoot 'graph_01'
if (Test-Path -LiteralPath $out) { throw 'Fresh output required' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$names = [WolvenKit.Common.Services.HashService]::new()
$names.Load()
$depot = 'towercontinued\native_gigs_u9\resume\sts_bls_ina_07_body.questphase'
$key = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
$archives = 0
$roots = @((Join-Path $baseline.game_root 'archive/pc'), (Join-Path $baseline.game_root 'mods')) | Where-Object { Test-Path -LiteralPath $_ }
foreach ($root in $roots) {
  if ((Get-Item -LiteralPath $root).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked archive root' }
  if (@(Get-ChildItem -LiteralPath $root -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked archive tree' }
  foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.archive') {
    $stamp = @($file.Length, $file.LastWriteTimeUtc.Ticks)
    $archive = $null
    $status = ([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName, $names, [ref]$archive)
    if ($status.ToString() -cne 'NoError') { throw "Unreadable archive: $file" }
    if ($archive.Files.ContainsKey($key)) { throw "Staged depot already exists: $depot" }
    $file.Refresh()
    if ($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1]) { throw 'Archive changed during review' }
    $archives++
  }
}

function Remove-Edge($Source, $Destination) {
  $outgoing = @(for ($i = 0; $i -lt $Source.Connections.Count; $i++) {
    $edge = $Source.Connections[$i].Chunk
    if ([object]::ReferenceEquals($edge.Source.Chunk, $Source) -and [object]::ReferenceEquals($edge.Destination.Chunk, $Destination)) { $i }
  })
  if ($outgoing.Count -ne 1) { throw 'Expected one outgoing edge' }
  $target = $Source.Connections[$outgoing[0]].Chunk
  $incoming = @(for ($i = 0; $i -lt $Destination.Connections.Count; $i++) {
    if ([object]::ReferenceEquals($Destination.Connections[$i].Chunk, $target)) { $i }
  })
  if ($incoming.Count -ne 1) { throw 'Expected one matching incoming edge' }
  $Source.Connections.RemoveAt($outgoing[0])
  $Destination.Connections.RemoveAt($incoming[0])
}

$body = Read-Cr2wFile $prior
if ((Get-FileHash -LiteralPath $prior).Hash -cne $priorHash) { throw 'Prior body changed during read' }
$stage = (Get-QuestNode $body.RootChunk.Graph.Chunk 11).PhaseGraph.Chunk
$graph = (Get-QuestNode $stage 620).PhaseGraph.Chunk
$mount = Get-QuestSocket (Get-QuestNode $graph 18) 'True'
$unmount = Get-QuestSocket (Get-QuestNode $graph 8) 'In'
$foreign = Get-QuestNode $graph 38
Remove-Edge $mount (Get-QuestSocket $foreign 'Inactive')
Remove-Edge (Get-QuestSocket $foreign 'Out') $unmount
[void](Connect-QuestSockets $mount $unmount)

$file = Join-Path $out 'sts_bls_ina_07_body.questphase'
Write-Cr2wFile $body $file
Export-Cr2wJson (Read-Cr2wFile $file) ($file + '.json')
@{
  status = 'UNREGISTERED_BODY_READBACK'
  depot = $depot
  depot_key = $key.ToString()
  scanned_archives = $archives
  archive_sha256 = $baseline.archive_sha256
  prior_sha256 = $priorHash
  body_sha256 = (Get-FileHash -LiteralPath $file).Hash
  export_sha256 = (Get-FileHash -LiteralPath ($file + '.json')).Hash
} | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
Write-Output "Serialized the unregistered Minefield successor and checked its private depot across $archives archives."
