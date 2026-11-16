Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$output = Join-Path $PSScriptRoot 'inventory.json'
if (Test-Path -LiteralPath $output) { throw 'Inventory output already exists' }
$workspace = Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$readerType = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]
if ((Get-FileHash -LiteralPath $readerType.Assembly.Location).Hash -cne 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987') { throw 'Save parser drift' }
$selection = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'selection.json') -Raw | ConvertFrom-Json -AsHashtable
$cast = [WolvenKit.RED4.Types.TweakDBID].GetMethods() | Where-Object { $_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint64] }
$saveRoot = 'C:/Users/Ayong/Saved Games/CD Projekt Red/Cyberpunk 2077'
$rows = @(foreach ($slot in $selection.slots.Keys) {
  if ($slot -cnotmatch '^(?:AutoSave-(?:13|17)|ManualSave-(?:26|31))$') { throw 'Unexpected slot' }
  $folder = Get-Item -LiteralPath (Join-Path $saveRoot $slot)
  $file = Get-Item -LiteralPath (Join-Path $folder.FullName 'sav.dat')
  if (($folder.Attributes -bor $file.Attributes) -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked save path' }
  $bytes = [IO.File]::ReadAllBytes($file.FullName)
  $expected = $selection.slots[$slot]
  if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $expected) { throw 'Save drift' }
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
        if ($key -in $selection.item_ids.Values) {
          @{inventory=$container.InventoryId.ToString(); item_id=$key; quantity=[int]$item.Quantity}
        }
      }
    })
    if ((Get-FileHash -LiteralPath $file.FullName).Hash -cne $expected) { throw 'Save changed during read' }
    @{slot=$slot; sha256=$expected; matching_items=$hits; inspected_subinventories=$inventory[0].Value.SubInventories.Count}
  } finally { $reader.Dispose(); $memory.Dispose() }
})
@{status='READ_ONLY'; item_ids=$selection.item_ids; saves=$rows} |
  ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $output -Encoding utf8NoBOM
