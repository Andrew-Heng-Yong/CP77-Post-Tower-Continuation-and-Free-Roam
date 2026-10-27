Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$m = Get-Content (Join-Path $PSScriptRoot 'candidate_01/manifest.json') -Raw | ConvertFrom-Json -Depth 50
$paths = @($m.changed_resources)
if ($paths.Count -ne 2) { throw 'Expected two changed resource paths' }
$keys = @{}
foreach ($path in $paths) {
  $keys[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($path).ToString()] = $path
}
$mod = 'C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/archive/pc/mod'
$archives = @(Get-ChildItem -LiteralPath $mod -Filter '*.archive' -File | Where-Object { $_.Name -cne 'zzzz_PTFR_Combined.archive' })
$hs = [WolvenKit.Common.Services.HashService]::new(); $hs.Load()
$hits = [Collections.Generic.List[object]]::new()
foreach ($f in $archives) {
  $archive = $null
  if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName, $hs, [ref]$archive).ToString() -cne 'NoError') { throw ('Unreadable archive ' + $f.FullName) }
  foreach ($entry in $archive.Files.Values) {
    if ($keys.ContainsKey($entry.Key.ToString())) {
      $hits.Add(@{ archive = $f.FullName; name = $entry.Name; depot = $keys[$entry.Key.ToString()] })
    }
  }
}
$result = @{ status = 'READ_ONLY_COLLISION_SCAN'; archives = $archives.Count; changed_paths = $paths.Count; collisions = $hits.ToArray() }
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'candidate_01/collisions_01.json'), ($result | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))
@{ archives = $archives.Count; changed_paths = $paths.Count; collisions = $hits.Count } | ConvertTo-Json
if ($hits.Count) { throw 'Changed resource path collision' }
