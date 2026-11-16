# Resolve the exact native sector and keep the provider bytes and decode result.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out = Join-Path $PSScriptRoot 'evidence_01'
if (Test-Path -LiteralPath $out) { throw 'Fresh sector evidence required' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$manifest = Join-Path $workspace 'prealpha/resume_dispatcher_rd4_20261113_01/deployment_01/installed_manifest_01.json'
if ((Get-FileHash -LiteralPath $manifest).Hash -cne '3DDA172011D2049A0EDBC4E006E6F40AE79F8751B23FAF0BEBCDC1706A62F0BC') { throw 'Baseline drift' }
$game = (Get-Content -Raw -LiteralPath $manifest | ConvertFrom-Json).game_root
$depots = @('base\worlds\03_night_city\_compiled\default\quest_72f6950589fce407.streamingsector',
  'base\worlds\03_night_city\_compiled\default\all.streamingblock')
$names = [WolvenKit.Common.Services.HashService]::new()
$names.Load()
[void][IO.Directory]::CreateDirectory($out)
$roots = @((Join-Path $game 'archive/pc'), (Join-Path $game 'mods')) | Where-Object { Test-Path -LiteralPath $_ }
$rows = @(foreach ($root in $roots) {
  if (@(Get-ChildItem -LiteralPath $root -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked archive tree' }
  foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.archive') {
    $stamp = @($file.Length, $file.LastWriteTimeUtc.Ticks)
    $archive = $null
    if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName, $names, [ref]$archive).ToString() -cne 'NoError') { throw "Unreadable archive: $file" }
    foreach ($depot in $depots) {
      $key = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
      if (!$archive.Files.ContainsKey($key)) { continue }
      $raw = Join-Path $out ($file.BaseName + '_' + (Split-Path $depot -Leaf))
      $stream = [IO.File]::Open($raw,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
      try { $archive.Files[$key].Extract($stream) } finally { $stream.Dispose() }
      $errorText = $null
      $export = $raw + '.json'
      try { Export-Cr2wJson (Read-Cr2wFile $raw) $export } catch { $errorText = $_.Exception.Message }
      @{depot=$depot; archive=$file.FullName; sha256=(Get-FileHash -LiteralPath $raw).Hash;
        raw=$raw; export=if ($null -eq $errorText) { $export }; decode_error=$errorText}
    }
    $file.Refresh()
    if ($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1]) { throw 'Archive changed during read' }
  }
})
if (@($rows | Where-Object depot -CEQ $depots[0]).Count -eq 0) { throw 'Missing quest sector' }
@{providers=$rows; game_writes=0} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $out 'world.json') -Encoding utf8NoBOM
$rows | Select-Object depot,sha256,decode_error | Format-List
