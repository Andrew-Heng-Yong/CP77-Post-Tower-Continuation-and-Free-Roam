# Serialize the offline body and verify its reviewed providers and private depot against installed archives.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = (Get-Item -LiteralPath $PSScriptRoot).Parent.Parent.Parent.FullName
$out = Join-Path $PSScriptRoot 'graph_01'
if (Test-Path -LiteralPath $out) { throw 'Fresh output required' }
$pins = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/inputs.json') | ConvertFrom-Json -AsHashtable
$planPath = Join-Path $PSScriptRoot 'empathy.json'
if ((Get-FileHash -LiteralPath $planPath).Hash -cne $pins.plan_sha256) { throw 'Stage plan drift' }
$plan = Get-Content -Raw -LiteralPath $planPath | ConvertFrom-Json -AsHashtable
$installed = Join-Path $pins.game 'archive/pc/mod/zzzz_PTFR_Combined.archive'
if ((Get-FileHash -LiteralPath $installed).Hash -cne $pins.archive_sha256) { throw 'Installed archive drift' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$names = [WolvenKit.Common.Services.HashService]::new()
$names.Load()
$privateKey = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($plan.depot)
$watch = @{}
foreach ($pin in $pins.resources) {
  $key = [uint64]$pin.key
  if ($key -eq $privateKey -or $watch.ContainsKey($key) -or $key -ne [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($pin.depot)) { throw 'Provider key drift or collision' }
  $watch[$key] = $pin
}
$seen = [Collections.Generic.HashSet[uint64]]::new()
$archives = 0
$bodyBytes = $null
$roots = @((Join-Path $pins.game 'archive/pc'), (Join-Path $pins.game 'mods')) | Where-Object { Test-Path -LiteralPath $_ }
foreach ($root in $roots) {
  if ((Get-Item -LiteralPath $root).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked archive root' }
  if (@(Get-ChildItem -LiteralPath $root -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked archive tree' }
  foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.archive') {
    $stamp = @($file.Length, $file.LastWriteTimeUtc.Ticks)
    $archive = $null
    $result = ([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName, $names, [ref]$archive)
    if ($result.ToString() -cne 'NoError') { throw "Unreadable archive: $file" }
    if ($archive.Files.ContainsKey($privateKey)) { throw "Private depot exists: $($plan.depot)" }
    foreach ($key in $watch.Keys) {
      if (!$archive.Files.ContainsKey($key)) { continue }
      $pin = $watch[$key]
      if ($pin.archive -ine $file.FullName -or !$seen.Add($key)) { throw "Unexpected provider for $($pin.depot)" }
      $memory = [IO.MemoryStream]::new()
      try { $archive.Files[$key].Extract($memory); $bytes = $memory.ToArray() } finally { $memory.Dispose() }
      if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $pin.sha256) { throw "Provider drift: $($pin.depot)" }
      if ($pin.rid -eq $plan.body) { $bodyBytes = $bytes }
    }
    $file.Refresh()
    if ($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1]) { throw 'Archive changed during review' }
    $archives++
  }
}
if ($seen.Count -ne $watch.Count -or $null -eq $bodyBytes) { throw 'Missing reviewed provider' }
[void][IO.Directory]::CreateDirectory($out)
$original = Join-Path $out 'original.questphase'
[IO.File]::WriteAllBytes($original, $bodyBytes)
$body = Read-Cr2wFile $original
foreach ($path in $plan.graphs.Keys) {
  $spec = $plan.graphs[$path]
  $graph = $body.RootChunk.Graph.Chunk
  foreach ($id in ($path -split '/' | Select-Object -Skip 1)) { $graph = (Get-QuestNode $graph ([int]$id)).PhaseGraph.Chunk }
  if (@($graph.Nodes | Where-Object { $_.Chunk.Id.ToString() -eq [string]$spec.input }).Count) { throw 'Occupied stage input node' }
  Add-RedHandle $graph.Nodes (New-InputNode $spec.input $plan.socket)
  if ($spec.Contains('phase_inputs')) {
    foreach ($id in $spec.phase_inputs) {
      [void](New-QuestSocket (Get-QuestNode $graph $id) $plan.socket ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
    }
  }
  foreach ($edge in $spec.edges) {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $edge[0]) $edge[1]) (Get-QuestSocket (Get-QuestNode $graph $edge[2]) $edge[3]))
  }
}
$file = Join-Path $out ($plan.id + '_body.questphase')
Write-Cr2wFile $body $file
Export-Cr2wJson (Read-Cr2wFile $file) ($file + '.json')
@{
  status = 'UNREGISTERED_BODY_READBACK'
  scanned_archives = $archives
  pinned_providers = $seen.Count
  body_sha256 = (Get-FileHash -LiteralPath $file).Hash
  export_sha256 = (Get-FileHash -LiteralPath ($file + '.json')).Hash
} | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
Write-Output "Serialized the unregistered Empathy body and verified $($seen.Count) providers across $archives archives."
