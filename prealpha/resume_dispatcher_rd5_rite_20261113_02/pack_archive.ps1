# Pack the exact installed donor plus the four reviewed Rite of Passage resources.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out = Join-Path $PSScriptRoot 'archive_01'
if (Test-Path -LiteralPath $out) { throw 'Fresh archive output required' }
$base = Join-Path $workspace 'prealpha/resume_dispatcher_rd4_20261113_01/deployment_01/installed_manifest_01.json'
if ((Get-FileHash -LiteralPath $base).Hash -cne '3DDA172011D2049A0EDBC4E006E6F40AE79F8751B23FAF0BEBCDC1706A62F0BC') { throw 'Baseline drift' }
$manifest = Get-Content -Raw -LiteralPath $base | ConvertFrom-Json
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$names = [WolvenKit.Common.Services.HashService]::new()
$names.Load()

function Key([string]$Depot) { [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($Depot) }
function Open-Archive([string]$ArchiveFile) {
  $archive = $null
  if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($ArchiveFile,$names,[ref]$archive).ToString() -cne 'NoError') { throw "Unreadable archive: $ArchiveFile" }
  return $archive
}
function Member-Hash($Entry) {
  $memory = [IO.MemoryStream]::new()
  try { $Entry.Extract($memory); return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray())) }
  finally { $memory.Dispose() }
}
function Assert-Plain([string]$Path) {
  for ($item = Get-Item -LiteralPath $Path; $null -ne $item;) {
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked input refused: $Path" }
    $item = if ($item -is [IO.FileInfo]) { $item.Directory } else { $item.Parent }
  }
}

$archiveRel = 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$currentPath = Join-Path $manifest.game_root $archiveRel
Assert-Plain $currentPath
if ((Get-FileHash -LiteralPath $currentPath).Hash -cne ($manifest.core_files | Where-Object path -CEQ $archiveRel).sha256) { throw 'Installed archive drift' }
$current = Open-Archive $currentPath
$donor = $manifest.archive_source
Assert-Plain $donor
if (@(Get-ChildItem -LiteralPath $donor -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked donor tree' }
$private = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'graph_01/readback.json') | ConvertFrom-Json
$entry = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'graph_06/readback.json') | ConvertFrom-Json
$qualified = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/wrapper_assessment.json') | ConvertFrom-Json
if ($entry.raw_sha256 -cne $qualified.raw_sha256 -or $qualified.status -cne 'PASS_UNPACKED_NATIVE_WRAPPER') { throw 'Wrapper review drift' }
$privateCheck = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/entrance_assessment.json') | ConvertFrom-Json
if ((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'graph_01/readback.json')).Hash -cne $privateCheck.readback_sha256) { throw 'Private phase review drift' }
$changes = @{}
foreach ($row in $private.resources) {
  $changes[$row.depot] = @{source=(Join-Path $PSScriptRoot ('graph_01/'+$row.name+'.questphase')); sha256=$row.raw_sha256}
}
$changes[$entry.depot] = @{source=(Join-Path $PSScriptRoot 'graph_06/entry.questphase'); sha256=$entry.raw_sha256}
$keys = @{}
foreach ($depot in $changes.Keys) {
  $key = Key $depot
  if ($keys.ContainsKey($key)) { throw 'Candidate depot hash collision' }
  $keys[$key] = $depot
}
$archives = 0
foreach ($root in @('archive/pc','mods')) {
  $folder = Join-Path $manifest.game_root $root
  if (!(Test-Path -LiteralPath $folder)) { continue }
  Assert-Plain $folder
  if (@(Get-ChildItem -LiteralPath $folder -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked archive tree' }
  foreach ($item in Get-ChildItem -LiteralPath $folder -Recurse -File -Filter '*.archive') {
    $stamp = @($item.Length,$item.LastWriteTimeUtc.Ticks)
    $archive = Open-Archive $item.FullName
    foreach ($key in $keys.Keys) {
      $expected = $keys[$key] -ceq $entry.depot -and $item.FullName -ieq $currentPath
      if ($archive.Files.ContainsKey($key) -ne $expected) { throw "Unexpected provider for $($keys[$key]) in $item" }
    }
    $item.Refresh()
    if ($item.Length -ne $stamp[0] -or $item.LastWriteTimeUtc.Ticks -ne $stamp[1]) { throw 'Archive changed during check' }
    $archives++
  }
}
$sourceRoot = Join-Path $out 'source'
[void][IO.Directory]::CreateDirectory($sourceRoot)
$members = @{}
foreach ($file in Get-ChildItem -LiteralPath $donor -Recurse -File) {
  $depot = [IO.Path]::GetRelativePath($donor,$file.FullName)
  $key = Key $depot
  if ($members.ContainsKey($key) -or !$current.Files.ContainsKey($key)) { throw "Unexpected donor depot: $depot" }
  $hash = (Get-FileHash -LiteralPath $file.FullName).Hash
  if ((Member-Hash $current.Files[$key]) -cne $hash) { throw "Donor drift: $depot" }
  $members[$key] = @{depot=$depot; sha256=$hash}
  if ($changes.ContainsKey($depot)) { continue }
  $dest = Join-Path $sourceRoot $depot
  [void][IO.Directory]::CreateDirectory((Split-Path -Parent $dest))
  [IO.File]::Copy($file.FullName,$dest,$false)
}
if ($members.Count -ne 1742 -or $current.Files.Count -ne $members.Count) { throw 'Incomplete donor' }
foreach ($depot in $changes.Keys) {
  $row = $changes[$depot]
  Assert-Plain $row.source
  if ((Get-FileHash -LiteralPath $row.source).Hash -cne $row.sha256) { throw 'Reviewed payload drift' }
  $dest = Join-Path $sourceRoot $depot
  [void][IO.Directory]::CreateDirectory((Split-Path -Parent $dest))
  [IO.File]::Copy($row.source,$dest,$false)
  $members[(Key $depot)] = @{depot=$depot; sha256=$row.sha256}
}
$packed = Join-Path $out 'zzzz_PTFR_Combined.archive'
$stream = [IO.File]::Open($packed,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
try {
  if (!([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($names,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($sourceRoot),$stream)) { throw 'Packing failed' }
} finally { $stream.Dispose() }
$readback = Open-Archive $packed
if ($readback.Files.Count -ne $members.Count -or $members.Count -ne 1745) { throw 'Packed count drift' }
foreach ($key in $members.Keys) {
  if (!$readback.Files.ContainsKey($key) -or (Member-Hash $readback.Files[$key]) -cne $members[$key].sha256) { throw "Packed member drift: $($members[$key].depot)" }
}
@{status='MEMBERS_VERIFIED'; archive_sha256=(Get-FileHash -LiteralPath $packed).Hash; scanned_archives=$archives;
  registered_paths_changed=0; changes=@($changes.Keys); members=@($members.Values)} |
  ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
Write-Output "Verified $($members.Count) packed members against RD4 and the four reviewed payloads."
