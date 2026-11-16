# Generate both private body entrances from one stage inventory and read back the exact serialization.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out = Join-Path $PSScriptRoot 'graph_02'
if (Test-Path -LiteralPath $out) { throw 'Fresh output required' }
$pins = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'evidence_02/inputs.json') | ConvertFrom-Json -AsHashtable
$planPath = Join-Path $PSScriptRoot 'entrances.json'
if ((Get-FileHash -LiteralPath $planPath).Hash -cne $pins.plan_sha256) { throw 'Stage inventory drift' }
$plan = (Get-Content -Raw -LiteralPath $planPath | ConvertFrom-Json -AsHashtable).quests
$installed = Join-Path $pins.game 'archive/pc/mod/zzzz_PTFR_Combined.archive'
if ((Get-FileHash -LiteralPath $installed).Hash -cne $pins.archive_sha256) { throw 'Installed archive drift' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$names = [WolvenKit.Common.Services.HashService]::new()
$names.Load()
$watch = @{}
$private = @{}
foreach ($pin in $pins.resources) {
  $key = [uint64]$pin.key
  if ($watch.ContainsKey($key) -or $key -ne [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($pin.depot)) { throw 'Resource key drift' }
  $watch[$key] = $pin
}
foreach ($quest in $plan) {
  $depot = 'towercontinued\native_gigs_u9\resume\' + $quest.id + '_body.questphase'
  $key = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
  if ($private.ContainsKey($key) -or $watch.ContainsKey($key)) { throw 'Planned private key collision' }
  $private[$key] = $depot
}
[void][IO.Directory]::CreateDirectory($out)
$seen = [Collections.Generic.HashSet[uint64]]::new()
$archives = 0
$roots = @((Join-Path $pins.game 'archive/pc'),(Join-Path $pins.game 'mods')) | Where-Object { Test-Path -LiteralPath $_ }
foreach ($root in $roots) {
  if (@(Get-ChildItem -LiteralPath $root -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked archive tree' }
  foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.archive') {
    $stamp = @($file.Length,$file.LastWriteTimeUtc.Ticks)
    $archive = $null
    if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$names,[ref]$archive).ToString() -cne 'NoError') { throw "Unreadable archive: $file" }
    foreach ($key in $private.Keys) {
      if ($archive.Files.ContainsKey($key)) { throw "Private depot exists: $($private[$key])" }
    }
    foreach ($key in $watch.Keys) {
      if (!$archive.Files.ContainsKey($key)) { continue }
      $pin = $watch[$key]
      if ($pin.archive -ine $file.FullName -or !$seen.Add($key)) { throw "Unexpected provider for $($pin.depot)" }
      $memory = [IO.MemoryStream]::new()
      try { $archive.Files[$key].Extract($memory); $bytes = $memory.ToArray() } finally { $memory.Dispose() }
      if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $pin.sha256) { throw "Provider drift: $($pin.depot)" }
      if ($pin.rid -in $plan.body) { [IO.File]::WriteAllBytes((Join-Path $out "$($pin.rid).original.questphase"),$bytes) }
    }
    $file.Refresh()
    if ($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1]) { throw 'Archive changed during review' }
    $archives++
  }
}
if ($seen.Count -ne $watch.Count) { throw 'Missing reviewed provider' }

function Remove-Edge($Graph, $Edge) {
  $src = Get-QuestSocket (Get-QuestNode $Graph $Edge[0]) $Edge[1]
  $dst = Get-QuestSocket (Get-QuestNode $Graph $Edge[2]) $Edge[3]
  $matches = @(for ($i = 0; $i -lt $src.Connections.Count; $i++) {
    $c = $src.Connections[$i].Chunk
    if ([object]::ReferenceEquals($c.Source.Chunk, $src) -and [object]::ReferenceEquals($c.Destination.Chunk, $dst)) { $i }
  })
  if ($matches.Count -ne 1) { throw 'Expected exactly one outgoing edge' }
  $handle = $src.Connections[$matches[0]].Chunk
  $incoming = @(for ($i = 0; $i -lt $dst.Connections.Count; $i++) {
    if ([object]::ReferenceEquals($dst.Connections[$i].Chunk, $handle)) { $i }
  })
  if ($incoming.Count -ne 1) { throw 'Expected matching incoming handle' }
  $src.Connections.RemoveAt($matches[0])
  $dst.Connections.RemoveAt($incoming[0])
}

$results = foreach ($quest in $plan) {
  $body = Read-Cr2wFile (Join-Path $out "$($quest.body).original.questphase")
  foreach ($path in $quest.graphs.Keys) {
    $spec = $quest.graphs[$path]
    $graph = $body.RootChunk.Graph.Chunk
    foreach ($id in ($path -split '/' | Select-Object -Skip 1)) { $graph = (Get-QuestNode $graph ([int]$id)).PhaseGraph.Chunk }
    if ($spec.Contains('input')) {
      if (@($graph.Nodes | Where-Object { $_.Chunk.Id.ToString() -eq [string]$spec.input }).Count) { throw 'Occupied stage input node' }
      Add-RedHandle $graph.Nodes (New-InputNode $spec.input $quest.socket)
    }
    if ($spec.Contains('phase_inputs')) {
      foreach ($id in $spec.phase_inputs) {
        [void](New-QuestSocket (Get-QuestNode $graph $id) $quest.socket ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
      }
    }
    if ($spec.Contains('remove_edges')) {
      foreach ($edge in $spec.remove_edges) { Remove-Edge $graph $edge }
    }
    foreach ($edge in $spec.edges) {
      [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $edge[0]) $edge[1]) (Get-QuestSocket (Get-QuestNode $graph $edge[2]) $edge[3]))
    }
  }
  $file = Join-Path $out ($quest.id+'_body.questphase')
  Write-Cr2wFile $body $file
  Export-Cr2wJson (Read-Cr2wFile $file) ($file+'.json')
  @{id=$quest.id; sha256=(Get-FileHash -LiteralPath $file).Hash; export_sha256=(Get-FileHash -LiteralPath ($file+'.json')).Hash}
}
@{status='UNREGISTERED_BODY_READBACK'; scanned_archives=$archives; pinned_providers=$seen.Count; bodies=@($results)} |
  ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
Write-Output "Generated both bodies and verified $($seen.Count) providers across $archives installed archives."
