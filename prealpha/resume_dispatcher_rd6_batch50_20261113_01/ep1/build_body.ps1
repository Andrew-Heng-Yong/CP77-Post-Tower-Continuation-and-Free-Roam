# Write an unregistered body with an additive stage entrance and verify its source providers.
param([string]$PlanRoot = $PSScriptRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = (Get-Item -LiteralPath $PSScriptRoot).Parent.Parent.Parent.FullName
$out = Join-Path $PlanRoot 'graph_01'
if (Test-Path -LiteralPath $out) { throw 'Fresh output required' }
$pins = Get-Content -Raw -LiteralPath (Join-Path $PlanRoot 'evidence_01/inputs.json') | ConvertFrom-Json -AsHashtable
$planPath = Join-Path $PlanRoot 'plan.json'
if ((Get-FileHash -LiteralPath $planPath).Hash -cne $pins.plan_sha256) { throw 'Stage plan drift' }
$plan = Get-Content -Raw -LiteralPath $planPath | ConvertFrom-Json -AsHashtable
$installed = Join-Path $pins.game 'archive/pc/mod/zzzz_PTFR_Combined.archive'
if ((Get-FileHash -LiteralPath $installed).Hash -cne $pins.archive_sha256) { throw 'Installed archive drift' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$names = [WolvenKit.Common.Services.HashService]::new()
$names.Load()
$watch = @{}
foreach ($pin in $pins.resources) {
  $key = [uint64]$pin.key
  if ($watch.ContainsKey($key) -or $key -ne [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($pin.depot)) { throw 'Resource key drift' }
  $watch[$key] = $pin
}
$privateKey = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($plan.private_depot)
[void][IO.Directory]::CreateDirectory($out)
$sourceFile = Join-Path $out 'original.questphase'
$seen = [Collections.Generic.HashSet[uint64]]::new()
$archives = 0
$roots = @((Join-Path $pins.game 'archive/pc'), (Join-Path $pins.game 'mods')) | Where-Object { Test-Path -LiteralPath $_ }
foreach ($root in $roots) {
  if (@(Get-ChildItem -LiteralPath $root -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked archive tree' }
  foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.archive') {
    $stamp = @($file.Length, $file.LastWriteTimeUtc.Ticks)
    $archive = $null
    if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName, $names, [ref]$archive).ToString() -cne 'NoError') { throw "Unreadable archive: $file" }
    if ($archive.Files.ContainsKey($privateKey)) { throw "Private depot exists: $($plan.private_depot)" }
    foreach ($key in $watch.Keys) {
      if (!$archive.Files.ContainsKey($key)) { continue }
      $pin = $watch[$key]
      if ($pin.archive -ine $file.FullName -or !$seen.Add($key)) { throw "Unexpected provider for $($pin.depot)" }
      $memory = [IO.MemoryStream]::new()
      try { $archive.Files[$key].Extract($memory); $bytes = $memory.ToArray() } finally { $memory.Dispose() }
      if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $pin.sha256) { throw "Provider drift: $($pin.depot)" }
      if ($pin.rid -eq $plan.body) { [IO.File]::WriteAllBytes($sourceFile, $bytes) }
    }
    $file.Refresh()
    if ($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1]) { throw 'Archive changed during review' }
    $archives++
  }
}
if ($seen.Count -ne $watch.Count) { throw 'Missing reviewed provider' }

$body = Read-Cr2wFile $sourceFile
foreach ($path in $plan.graphs.Keys) {
  $edit = $plan.graphs[$path]
  $graph = $body.RootChunk.Graph.Chunk
  foreach ($id in ($path -split '/' | Select-Object -Skip 1)) { $graph = (Get-QuestNode $graph ([int]$id)).PhaseGraph.Chunk }
  if (@($graph.Nodes | Where-Object { $_.Chunk.Id.ToString() -eq [string]$edit.input }).Count) { throw 'Occupied stage input ID' }
  Add-RedHandle $graph.Nodes (New-InputNode $edit.input $plan.socket)
  if ($edit.Contains('phase_inputs')) {
    foreach ($id in $edit.phase_inputs) {
      $node = Get-QuestNode $graph $id
      if (@($node.Sockets | Where-Object { $_.Chunk.Name.ToString() -ceq $plan.socket }).Count) { throw 'Occupied stage input socket' }
      [void](New-QuestSocket $node $plan.socket ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
    }
  }
  foreach ($edge in $edit.edges) {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $edge[0]) $edge[1]) (Get-QuestSocket (Get-QuestNode $graph $edge[2]) $edge[3]))
  }
}
$output = Join-Path $out ($plan.quest + '_body.questphase')
$export = $output + '.json'
Write-Cr2wFile $body $output
Export-Cr2wJson (Read-Cr2wFile $output) $export
@{
  status = 'UNREGISTERED_BODY_READBACK'
  private_depot = $plan.private_depot
  scanned_archives = $archives
  pinned_providers = $seen.Count
  original_sha256 = (Get-FileHash -LiteralPath $sourceFile).Hash
  body_sha256 = (Get-FileHash -LiteralPath $output).Hash
  export_sha256 = (Get-FileHash -LiteralPath $export).Hash
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
Write-Output "Serialized the unregistered body after verifying $($seen.Count) providers across $archives installed archives."
