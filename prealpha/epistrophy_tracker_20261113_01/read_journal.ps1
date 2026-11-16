# Compare saved Epistrophy journal and tracking fields before and during both cab encounters.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out = Join-Path $PSScriptRoot 'evidence_01/journal.json'
if (Test-Path -LiteralPath $out) { throw 'Fresh journal evidence required' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$parserHash = (Get-FileHash -LiteralPath ([WolvenKit.RED4.Save.IO.CyberpunkSaveReader].Assembly.Location)).Hash
if ($parserHash -cne 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987') { throw 'Parser drift' }
$pins = [ordered]@{
  'AutoSave-18' = '3FBC9A0DC94A7D56FD3242C60677E740B64E02140DBB0B99E1AB94A0B918B5C5'
  'AutoSave-19' = '2EE25709AFCD069AD53DB1E8FEA2948954B1A07D6216FD8E872936D65017723A'
  'AutoSave-2' = 'BAF340B8AD16979C8E2CC70C17C5BC28BD5820C8A0D21FA56856C90ADB031A77'
  'AutoSave-0' = 'F8BE714A3EC7B11B615FA49CBF0013435487492431E2E0D5CA07DE55CAAED7AC'
  'AutoSave-1' = 'EA8D6E562522D797BA378B6DE6B3CA34ABB93FB653FEBD132FAB2593DEB7F675'
  'AutoSave-3' = 'EE66B0FFE1683CEC794CE912CD7165D1452E55FED327BB23F07E94510D5466A5'
}
$parent = 'quests/side_quest/sq025_delamain'
$scan = "$parent/03_scan/03_02_scan_delamains"
$northside = 'quests/side_quest/sq025c05_scared'
$wellsprings = 'quests/side_quest/sq025c01_angry'
$paths = @($parent, "$parent/03_scan", $scan, "$scan/wellsprings", "$scan/northside")
foreach ($cab in @(@($northside,'05','scared'), @($wellsprings,'01','angry'))) {
  $quest, $number, $name = $cab
  $phase = "$quest/${number}_find_$name"
  $paths += @($quest, $phase, "$phase/${number}_find_$name")
  foreach ($task in 'a_scan','b_disable','c_return','d_destroy','w_wait','x_complete') {
    $paths += "$phase/$number${task}_$name"
  }
}
$keys = @{}
foreach ($path in $paths) {
  $key = [WolvenKit.Core.Murmur3.Murmur32]::Hash($path, [uint32]0x5EEDBA5E, [Text.Encoding]::UTF8)
  if ($keys.ContainsKey($key)) { throw 'Collision in selected paths' }
  $keys[$key] = $path
}
$saveRoot = 'C:/Users/Ayong/Saved Games/CD Projekt Red/Cyberpunk 2077'
$rows = @(foreach ($slot in $pins.Keys) {
  $source = Join-Path $saveRoot "$slot/sav.dat"
  for ($item = Get-Item -LiteralPath $source; $null -ne $item;) {
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked input' }
    $item = if ($item -is [IO.FileInfo]) { $item.Directory } else { $item.Parent }
  }
  $bytes = [IO.File]::ReadAllBytes($source)
  if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $pins[$slot]) { throw "Save drift: $slot" }
  $memory = [IO.MemoryStream]::new($bytes, $false)
  $reader = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($memory)
  try {
    $save = $null
    if ($reader.ReadFile([ref]$save).ToString() -cne 'NoError') { throw "Save parse failed: $slot" }
    $journal = @($save.Nodes | Where-Object Name -CEQ 'JournalManager')
    if ($journal.Count -ne 1) { throw 'Ambiguous saved journal' }
    $matches = @{}
    foreach ($entry in $journal[0].Value.Entries) {
      $raw = [byte[]]$entry.UnkownBytes
      if ($raw.Length -ne 15) { throw 'Journal framing drift' }
      $hash = [BitConverter]::ToUInt32($raw, 0)
      if ($keys.ContainsKey($hash)) {
        $name = $keys[$hash]
        if ($matches.ContainsKey($name)) { throw 'Duplicate selected hash' }
        $matches[$name] = @{state=[BitConverter]::ToUInt32($raw,4); hash_u32=$hash; raw15=[Convert]::ToHexString($raw)}
      }
    }
    if ((Get-FileHash -LiteralPath $source).Hash -cne $pins[$slot]) { throw "Save changed during read: $slot" }
    $tracked = [uint32]$journal[0].Value.Unk1_TrackedQuestPath
    @{slot=$slot; sha256=$pins[$slot]; tracked_hash=$tracked; matched_tracking_path=$keys[$tracked]; journal=$matches}
  } finally { $reader.Dispose(); $memory.Dispose() }
})
[void][IO.Directory]::CreateDirectory((Split-Path $out -Parent))
@{status='READ_ONLY'; parser_sha256=$parserHash; save_writes=0; saves=$rows} |
  ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $out -Encoding utf8NoBOM
$rows | Select-Object slot,tracked_hash,matched_tracking_path | Format-Table
