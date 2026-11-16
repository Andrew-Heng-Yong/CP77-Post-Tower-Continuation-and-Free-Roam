# Read the exact persisted quest keycard in the existing stage fixtures.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out = Join-Path $PSScriptRoot 'evidence_01/keycard.json'
if (Test-Path -LiteralPath $out) { throw 'Fresh inventory evidence required' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$readerType = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]
if ((Get-FileHash -LiteralPath $readerType.Assembly.Location).Hash -cne 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987') { throw 'Save parser drift' }
$prior = Join-Path $workspace 'prealpha/resume_dispatcher_rd5_gigs_20261113_01'
$files = @((Join-Path $workspace 'prealpha/handler_preservation_hp1_20261112_01/saves_01/ManualSave-26/manifest.json'),
  (Join-Path $prior 'saves_01/AutoSave-3/manifest.json'), (Join-Path $prior 'saves_01/AutoSave-5/manifest.json'))
$cast = [WolvenKit.RED4.Types.TweakDBID].GetMethods() | Where-Object { $_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint64] }
$rows = @(foreach ($manifest in $files) {
  $pin = Get-Content -Raw -LiteralPath $manifest | ConvertFrom-Json
  $bytes = [IO.File]::ReadAllBytes($pin.source)
  if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $pin.source_sha256) { throw 'Save drift' }
  $memory = [IO.MemoryStream]::new($bytes, $false)
  $reader = $readerType::new($memory)
  try {
    $save = $null
    if ($reader.ReadFile([ref]$save).ToString() -cne 'NoError') { throw 'Save decode failed' }
    $inventory = @($save.Nodes | Where-Object { $_.Value -is [WolvenKit.RED4.Save.Inventory] })
    if ($inventory.Count -ne 1) { throw 'Unexpected inventory structure' }
    $hits = @(foreach ($container in $inventory[0].Value.SubInventories) {
      foreach ($item in $container.Items) {
        $key = [uint64]$cast.Invoke($null, [object[]]@($item.ItemInfo.ItemId.Id.PSObject.BaseObject))
        if ($key -eq 100486752765ul) {
          @{inventory=$container.InventoryId.ToString(); quantity=[int]$item.Quantity; flags=$item.Flags.ToString(); structure=$item.ItemInfo.ItemStructure.ToString()}
        }
      }
    })
    if ((Get-FileHash -LiteralPath $pin.source).Hash -cne $pin.source_sha256) { throw 'Save changed during read' }
    @{source=$pin.source; sha256=$pin.source_sha256; matching_items=$hits; inventories=@($inventory[0].Value.SubInventories | ForEach-Object { @{id=$_.InventoryId.ToString(); entries=$_.Items.Count} })}
  } finally { $reader.Dispose(); $memory.Dispose() }
})
@{status='READ_ONLY'; tweak_id='Keycards.nid_05_keycard'; tweak_id_u64='100486752765'; saves=$rows} |
  ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $out -Encoding utf8NoBOM
$rows | ConvertTo-Json -Depth 7
