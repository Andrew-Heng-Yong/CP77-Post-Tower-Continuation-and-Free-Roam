# Read only the saved Dogtown briefing records and their authored fact controls.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = (Get-Item -LiteralPath $PSScriptRoot).Parent.Parent.Parent.FullName
$out = Join-Path $PSScriptRoot 'evidence_01/saved_briefs.json'
if (Test-Path -LiteralPath $out) { throw 'Fresh evidence required' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$parserHash = (Get-FileHash -LiteralPath ([WolvenKit.RED4.Save.IO.CyberpunkSaveReader].Assembly.Location)).Hash
if ($parserHash -cne 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987') { throw 'Parser drift' }

$objectives = @(
  'ep1/quests/street_stories/sts_ep1_12/sts_ep1_12/01_get_inside_complex',
  'ep1/quests/street_stories/sts_ep1_13/sts_ep1_13/meet_mr_hands_contact'
)
$paths = $objectives + @(
  'contacts/mr_hands/sts_ep1_12/brief',
  'contacts/mr_hands/sts_ep1_13/sts_ep1_13_holocall_prebrief',
  'ep1/quests/street_stories/sts_ep1_12/brief',
  'ep1/quests/street_stories/sts_ep1_13/brief'
)
$facts = @(
  'sts_ep1_12_briefings_done', 'codex_milko_alexis', 'codex_voodoo_boys_in_dogtown',
  'sts_ep1_13_prebrief_received', 'sts_ep1_13_holo_obj_done', 'codex_fiona_vargas',
  'CP77-36823', 'CP77-58921', 'CP77-58937', 'wst_ep1_02_start', 'wst_ep1_02_finished'
)
$journalKeys = @{}
foreach ($path in $paths) {
  $key = [WolvenKit.Core.Murmur3.Murmur32]::Hash($path, [uint32]0x5EEDBA5E, [Text.Encoding]::UTF8)
  if ($journalKeys.ContainsKey($key)) { throw 'Selected journal hash collision' }
  $journalKeys[$key] = $path
}
$factHash = @([WolvenKit.RED4.Save.Fact].GetMethods() | Where-Object { $_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32] })[0]
$factKeys = @{}
foreach ($name in $facts) {
  $fact = [WolvenKit.RED4.Save.Fact]::op_Implicit($name)
  $key = [uint32]$factHash.Invoke($null, [object[]]@($fact))
  if ($factKeys.ContainsKey($key)) { throw 'Selected fact hash collision' }
  $factKeys[$key] = $name
}

$manifests = [ordered]@{
  'ManualSave-26' = 'prealpha/handler_preservation_hp1_20261112_01/saves_01/ManualSave-26/manifest.json'
  'AutoSave-3' = 'prealpha/resume_dispatcher_rd5_gigs_20261113_01/saves_01/AutoSave-3/manifest.json'
  'AutoSave-5' = 'prealpha/resume_dispatcher_rd5_gigs_20261113_01/saves_01/AutoSave-5/manifest.json'
}
$results = @(foreach ($slot in $manifests.Keys) {
  $manifest = Join-Path $workspace $manifests[$slot]
  $pin = Get-Content -Raw -LiteralPath $manifest | ConvertFrom-Json
  if ($pin.slot -cne $slot) { throw 'Save slot drift' }
  for ($item = Get-Item -LiteralPath $pin.source; $null -ne $item;) {
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked save input' }
    $item = if ($item -is [IO.FileInfo]) { $item.Directory } else { $item.Parent }
  }
  $bytes = [IO.File]::ReadAllBytes($pin.source)
  if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $pin.source_sha256) { throw 'Save drift' }
  $memory = [IO.MemoryStream]::new($bytes, $false)
  $reader = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($memory)
  try {
    $save = $null
    if ($reader.ReadFile([ref]$save).ToString() -cne 'NoError') { throw 'Save read failed' }
    $journal = @($save.Nodes | Where-Object Name -CEQ 'JournalManager')
    if ($journal.Count -ne 1) { throw 'Ambiguous saved journal' }
    $foundJournal = @{}
    foreach ($entry in $journal[0].Value.Entries) {
      $raw = [byte[]]$entry.UnkownBytes
      if ($raw.Length -ne 15) { throw 'Journal framing drift' }
      $key = [BitConverter]::ToUInt32($raw, 0)
      if ($journalKeys.ContainsKey($key)) {
        $path = $journalKeys[$key]
        if ($foundJournal.ContainsKey($path)) { throw 'Duplicate saved journal hash' }
        $foundJournal[$path] = @{ hash_u32 = $key; raw15 = [Convert]::ToHexString($raw); state_u32 = [BitConverter]::ToUInt32($raw, 4) }
      }
    }
    $objectiveState = if ($slot -ceq 'ManualSave-26') { 2 } else { 4 }
    foreach ($objective in $objectives) {
      if (!$foundJournal.ContainsKey($objective) -or $foundJournal[$objective].state_u32 -ne $objectiveState) { throw 'Objective control failed' }
    }
    $quest = @($save.Nodes | Where-Object Name -CEQ 'questSystem')
    if ($quest.Count -ne 1) { throw 'Ambiguous saved quest root' }
    $database = @($quest[0].Children | Where-Object Name -CEQ 'FactsDB')
    if ($database.Count -ne 1 -or $database[0].Children.Count -ne 10) { throw 'Unexpected saved fact layout' }
    $foundFacts = @{}
    foreach ($entry in $database[0].Children[0].Value.FactEntries) {
      $key = [uint32]$factHash.Invoke($null, [object[]]@($entry.FactName))
      if ($factKeys.ContainsKey($key)) {
        $name = $factKeys[$key]
        if ($foundFacts.ContainsKey($name)) { throw 'Duplicate saved fact hash' }
        $foundFacts[$name] = [uint32]$entry.Value
      }
    }
    if ((Get-FileHash -LiteralPath $pin.source).Hash -cne $pin.source_sha256) { throw 'Save changed during read' }
    @{
      slot = $slot; source_sha256 = $pin.source_sha256; manifest_sha256 = (Get-FileHash -LiteralPath $manifest).Hash
      journals = $foundJournal; facts = $foundFacts
      absent_journal_records = @($paths | Where-Object { !$foundJournal.ContainsKey($_) })
      absent_fact_records = @($facts | Where-Object { !$foundFacts.ContainsKey($_) })
    }
  } finally { $reader.Dispose(); $memory.Dispose() }
})
@{ status = 'READ_ONLY_DOGTOWN_BRIEFINGS'; parser_sha256 = $parserHash; saves = $results; save_writes = 0 } |
  ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $out -Encoding utf8NoBOM
Write-Output "Read the selected Dogtown briefing evidence in $($results.Count) pinned saves."
