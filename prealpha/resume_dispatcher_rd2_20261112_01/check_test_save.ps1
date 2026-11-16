# Read only the existing stadium autosave to select a shorter gameplay fixture.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$baseline = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/baseline.json') -Raw | ConvertFrom-Json
$contract = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'contract.json') -Raw | ConvertFrom-Json
$path = Join-Path $baseline.save_root 'AutoSave-15/sav.dat'
$out = Join-Path $PSScriptRoot 'evidence_01/stadium_save.json'
if (Test-Path -LiteralPath $out) { throw 'Fresh evidence required' }
for ($p = Get-Item -LiteralPath $path; $null -ne $p;) {
  if ($p.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked save refused' }
  $p = if ($p -is [IO.FileInfo]) { $p.Directory } else { $p.Parent }
}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
if ((Get-FileHash -LiteralPath ([WolvenKit.RED4.Save.IO.CyberpunkSaveReader].Assembly.Location)).Hash -cne
    'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987') { throw 'Parser drift' }
$toHash = @([WolvenKit.RED4.Save.Fact].GetMethods() | Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32]})[0]
$names = @($contract.fixed_facts.PSObject.Properties.Name) + @($contract.live_only_facts.PSObject.Properties.Name) +
         @($contract.own_receipts) + @($contract.other_owner_receipts) +
         @('q307_done','q307_finished','q307_main_game_killed','q307_ep1_killed','q307_2079','PTFRPA2_Finished','PTFRPA2_Fault','PTFRU9_Support_Issued','PostTowerFreeRoamActive')
$factKeys = @{}
$facts = [ordered]@{}
foreach ($name in $names) {
  $key = [uint32]$toHash.Invoke($null, [object[]]@([WolvenKit.RED4.Save.Fact]::op_Implicit([string]$name)))
  if ($factKeys.ContainsKey($key)) { throw 'Fact hash collision' }
  $factKeys[$key] = $name
  $facts[$name] = $null
}
$journalKeys = @{}
$journals = [ordered]@{}
foreach ($j in $contract.journals) {
  $key = [WolvenKit.Core.Murmur3.Murmur32]::Hash([string]$j.path,[uint32]0x5EEDBA5E,[Text.Encoding]::UTF8)
  if ($journalKeys.ContainsKey($key)) { throw 'Journal hash collision' }
  $journalKeys[$key] = $j.path
  $journals[$j.path] = $null
}
$sha = (Get-FileHash -LiteralPath $path).Hash
$bytes = [IO.File]::ReadAllBytes($path)
if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $sha) { throw 'Save changed during capture' }
$stream = [IO.MemoryStream]::new($bytes,$false)
$reader = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($stream)
$save = $null
try {
  if ($reader.ReadFile([ref]$save).ToString() -cne 'NoError') { throw 'Save parse failed' }
  $quest = @($save.Nodes | Where-Object Name -ceq 'questSystem')
  $journal = @($save.Nodes | Where-Object Name -ceq 'JournalManager')
  if ($quest.Count -ne 1 -or $journal.Count -ne 1) { throw 'Ambiguous saved systems' }
  $store = @($quest[0].Children | Where-Object Name -ceq 'FactsDB')
  if ($store.Count -ne 1 -or $store[0].Children.Count -ne 10) { throw 'Unexpected fact store' }
  foreach ($entry in $store[0].Children[0].Value.FactEntries) {
    $key = [uint32]$toHash.Invoke($null,[object[]]@($entry.FactName))
    if ($factKeys.ContainsKey($key)) { $facts[$factKeys[$key]] = [uint32]$entry.Value }
  }
  foreach ($entry in $journal[0].Value.Entries) {
    $raw = [byte[]]$entry.UnkownBytes
    if ($raw.Length -ne 15) { throw 'Journal layout drift' }
    $key = [BitConverter]::ToUInt32($raw,0)
    if ($journalKeys.ContainsKey($key)) { $journals[$journalKeys[$key]] = [BitConverter]::ToUInt32($raw,4) }
  }
} finally { $reader.Dispose(); $stream.Dispose() }
if ((Get-FileHash -LiteralPath $path).Hash -cne $sha) { throw 'Save changed during read' }
@{slot='AutoSave-15'; sha256=$sha; facts=$facts; journals=$journals; save_writes=0} |
  ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $out -Encoding utf8NoBOM
Get-Content -LiteralPath $out
