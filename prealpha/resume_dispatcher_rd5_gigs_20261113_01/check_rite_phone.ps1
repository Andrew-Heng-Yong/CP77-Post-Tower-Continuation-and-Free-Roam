# Read only the authored Rite of Passage phone records and a quest-state control.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out = Join-Path $PSScriptRoot 'evidence_01/rite_phone_readback.json'
if (Test-Path -LiteralPath $out) { throw 'Fresh evidence required' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$parserHash = (Get-FileHash -LiteralPath ([WolvenKit.RED4.Save.IO.CyberpunkSaveReader].Assembly.Location)).Hash
if ($parserHash -cne 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987') { throw 'Parser drift' }
$paths = @(
  'contacts/regina_jones/sts_wat_nid_05',
  'contacts/regina_jones/sts_wat_nid_05/brief',
  'contacts/regina_jones/sts_wat_nid_05/debrief',
  'contacts/regina_jones/sts_wat_nid_05/sts_wat_nid_05_debrief',
  'quests/street_stories/watson/northside_industrial_district/sts_wat_nid_05/sts_wat_nid_05/get_to_clinic'
)
$keys = @{}
foreach ($path in $paths) {
  $key = [WolvenKit.Core.Murmur3.Murmur32]::Hash($path, [uint32]0x5EEDBA5E, [Text.Encoding]::UTF8)
  if ($keys.ContainsKey($key)) { throw 'Journal hash collision in selected paths' }
  $keys[$key] = $path
}
$controls = @{
  'ManualSave-26' = 2
  'AutoSave-3' = 4
  'AutoSave-5' = 4
}
$manifests = @(
  (Join-Path $workspace 'prealpha/handler_preservation_hp1_20261112_01/saves_01/ManualSave-26/manifest.json'),
  (Join-Path $PSScriptRoot 'saves_01/AutoSave-3/manifest.json'),
  (Join-Path $PSScriptRoot 'saves_01/AutoSave-5/manifest.json')
)
$results = @(foreach ($manifest in $manifests) {
  $pin = Get-Content -Raw -LiteralPath $manifest | ConvertFrom-Json
  for ($item = Get-Item -LiteralPath $pin.source; $null -ne $item;) {
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked save input' }
    $item = if ($item -is [IO.FileInfo]) { $item.Directory } else { $item.Parent }
  }
  $bytes = [IO.File]::ReadAllBytes($pin.source)
  if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $pin.source_sha256) { throw 'Save drift' }
  $slot = Split-Path (Split-Path $pin.source -Parent) -Leaf
  $memory = [IO.MemoryStream]::new($bytes, $false)
  $reader = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($memory)
  try {
    $save = $null
    if ($reader.ReadFile([ref]$save).ToString() -cne 'NoError') { throw 'Save read failed' }
    $journal = @($save.Nodes | Where-Object Name -CEQ 'JournalManager')
    if ($journal.Count -ne 1) { throw 'Ambiguous saved journal' }
    $found = @{}
    foreach ($row in $journal[0].Value.Entries) {
      $raw = [byte[]]$row.UnkownBytes
      if ($raw.Length -ne 15) { throw 'Journal framing drift' }
      $key = [BitConverter]::ToUInt32($raw, 0)
      if ($keys.ContainsKey($key)) {
        if ($found.ContainsKey($keys[$key])) { throw 'Duplicate selected saved journal hash' }
        $found[$keys[$key]] = @{hash_u32=$key; raw15=[Convert]::ToHexString($raw); state_u32=[BitConverter]::ToUInt32($raw,4)}
      }
    }
    if (!$found.ContainsKey($paths[-1]) -or $found[$paths[-1]].state_u32 -ne $controls[$slot]) { throw 'Quest state control failed' }
    if ((Get-FileHash -LiteralPath $pin.source).Hash -cne $pin.source_sha256) { throw 'Save changed during read' }
    @{slot=$slot; source_sha256=$pin.source_sha256; raw_journal_records=$found; absent_paths=@($paths | Where-Object {!$found.ContainsKey($_)})}
  } finally { $reader.Dispose(); $memory.Dispose() }
})
@{status='READ_ONLY'; parser_sha256=$parserHash; saves=$results; save_writes=0} |
  ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $out -Encoding utf8NoBOM
$results | ConvertTo-Json -Depth 8
