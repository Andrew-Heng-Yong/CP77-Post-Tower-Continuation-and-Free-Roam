param([ValidatePattern('^evidence_[0-9]+$')][string]$Evidence = 'evidence_01')
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$evidenceRoot = Join-Path $PSScriptRoot $Evidence
$out = Join-Path $evidenceRoot 'provider_readback.json'
if (Test-Path -LiteralPath $out) { throw 'Fresh provider evidence required' }
$baselinePath = Join-Path $workspace 'prealpha/resume_dispatcher_rd4_20261113_01/deployment_01/installed_manifest_01.json'
if ((Get-FileHash -LiteralPath $baselinePath).Hash -cne '3DDA172011D2049A0EDBC4E006E6F40AE79F8751B23FAF0BEBCDC1706A62F0BC') { throw 'Baseline drift' }
$baseline = Get-Content -LiteralPath $baselinePath -Raw | ConvertFrom-Json
$pins = Get-Content -LiteralPath (Join-Path $evidenceRoot 'provider_inputs.json') -Raw | ConvertFrom-Json -AsHashtable
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()

function Assert-Plain([string]$Path) {
  for ($item = Get-Item -LiteralPath $Path; $null -ne $item;) {
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked input refused: $Path" }
    $item = if ($item -is [IO.FileInfo]) { $item.Directory } else { $item.Parent }
  }
}
function Open-Archive([string]$Path) {
  $archive = $null
  $status = ([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($Path, $hashService, [ref]$archive)
  if ($status.ToString() -cne 'NoError') { throw "Unreadable archive: $Path" }
  return $archive
}
function Member-Hash($Entry) {
  $memory = [IO.MemoryStream]::new()
  try {
    $Entry.Extract($memory)
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray()))
  } finally { $memory.Dispose() }
}
function Key([string]$Depot) { return [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($Depot) }

$installedArchive = Join-Path $baseline.game_root 'archive/pc/mod/zzzz_PTFR_Combined.archive'
Assert-Plain $evidenceRoot
$archiveRow = $baseline.core_files | Where-Object path -CEQ 'archive/pc/mod/zzzz_PTFR_Combined.archive'
if ((Get-FileHash -LiteralPath $installedArchive).Hash -cne $archiveRow.sha256) { throw 'Installed archive drift' }
$watch = @{}
$expected = @{}
foreach ($p in $pins.resources) {
  $key = [uint64]$p.key
  if ($watch.ContainsKey($key) -or $key -ne (Key $p.depot)) { throw "Provider key collision: $($p.depot)" }
  if ((Get-FileHash -LiteralPath $p.export_path).Hash -cne $p.export_sha256) { throw "Export drift: $($p.depot)" }
  $watch[$key] = $p
  $expected[$key] = @{}
  $expected[$key][$p.archive] = $p.sha256
  if ($pins.existing_overlays.Contains($p.depot)) { $expected[$key][$installedArchive] = $pins.existing_overlays[$p.depot] }
}
$providers = [Collections.Generic.List[object]]::new()
$inventory = [Collections.Generic.List[object]]::new()
$files = foreach ($root in @('archive/pc', 'mods')) {
  $folder = Join-Path $baseline.game_root $root
  if (Test-Path -LiteralPath $folder) {
    Assert-Plain $folder
    if (@(Get-ChildItem -LiteralPath $folder -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked archive tree' }
    Get-ChildItem -LiteralPath $folder -Recurse -File -Filter '*.archive'
  }
}
foreach ($file in $files) {
  $stamp = @($file.Length, $file.LastWriteTimeUtc.Ticks)
  $archive = Open-Archive $file.FullName
  foreach ($key in $watch.Keys) {
    if (!$archive.Files.ContainsKey($key)) { continue }
    $p = $watch[$key]
    $actual = Member-Hash $archive.Files[$key]
    if (!$expected[$key].ContainsKey($file.FullName) -or $actual -cne $expected[$key][$file.FullName]) {
      throw "Unreviewed provider: $($p.depot) in $($file.FullName)"
    }
    $providers.Add(@{depot=$p.depot; archive=$file.FullName; sha256=$actual})
    $expected[$key].Remove($file.FullName)
  }
  $file.Refresh()
  if ($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1]) { throw 'Archive changed during review' }
  $inventory.Add(@{path=$file.FullName; bytes=$stamp[0]; mtime_ticks=$stamp[1]})
}
if (@($expected.Values | Where-Object Count -ne 0).Count) { throw 'Expected provider is missing' }
@{status='PASS'; providers=$providers.ToArray(); archive_inventory=$inventory.ToArray();
  installed_archive_sha256=$archiveRow.sha256} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $out -Encoding utf8NoBOM
Write-Output "Verified $($providers.Count) matching providers across $($inventory.Count) installed archives."
