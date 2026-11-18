param(
  [string[]]$Slots = @('AutoSave-16', 'ManualSave-33', 'EndGameSave-106')
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$saveRoot = 'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077'
$wk = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0'
foreach ($name in @('WolvenKit.Core.dll', 'WolvenKit.Common.dll', 'WolvenKit.RED4.dll')) {
  [void][Reflection.Assembly]::LoadFrom((Join-Path $wk $name))
}
$names = @(
  'PTFRWO1_CleanupRegistered', 'PTFRWO1_CleanupPermit', 'PTFRWO1_CleanupDone',
  'PTFRMV_Applied', 'PTFRMV_Enabled', 'PostTowerFreeRoamActive',
  'PTFRP0_DR13', 'q307_active', 'q307_done', 'q307_finished', 'q307_2079',
  'q307_main_game_killed', 'q307_ep1_killed', 'q305_johnny_scene_active',
  'q115_point_of_no_return', 'PTFRBASE_Suspended', 'PTFRWORLD_Suspended',
  'PTFRMV_Suspended', 'PTFRMV_QuestOwns', 'PTFRMV_Registered', 'PTFRMV_Revision'
)
$hashMethod = [WolvenKit.RED4.Save.Fact].GetMethods() | Where-Object {
  $_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32]
}
$wanted = @{}
foreach ($name in $names) {
  $fact = [WolvenKit.RED4.Save.Fact]::op_Implicit($name)
  $wanted[[uint32]$hashMethod.Invoke($null, [object[]]@($fact))] = $name
}
$rows = foreach ($slot in $Slots) {
  $savePath = Join-Path (Join-Path $saveRoot $slot) 'sav.dat'
  $before = (Get-FileHash -LiteralPath $savePath -Algorithm SHA256).Hash
  $values = [ordered]@{}
  foreach ($name in $names) { $values[$name] = @() }
  $stream = [IO.File]::Open($savePath, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
  try {
    $save = $null
    $result = ([WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($stream)).ReadFile([ref]$save).ToString()
    if ($result -ne 'NoError') { throw "Save parse $result for $slot" }
    function Walk-FactNodes($nodes) {
      foreach ($node in $nodes) {
        if ($node.Value -is [WolvenKit.RED4.Save.FactsTable]) {
          foreach ($entry in $node.Value.FactEntries) {
            $key = [uint32]$script:hashMethod.Invoke($null, [object[]]@($entry.FactName))
            if ($script:wanted.ContainsKey($key)) {
              $factName = $script:wanted[$key]
              $script:values[$factName] += [uint32]$entry.Value
            }
          }
        }
        if ($node.Children.Count) { Walk-FactNodes $node.Children }
      }
    }
    Walk-FactNodes $save.Nodes
  } finally {
    $stream.Dispose()
  }
  $after = (Get-FileHash -LiteralPath $savePath -Algorithm SHA256).Hash
  if ($before -cne $after) { throw "Save changed during read: $slot" }
  [ordered]@{ slot = $slot; sha256 = $before; facts = $values }
}
@{ status = 'READ_ONLY_SERIALIZED_FACTS'; rows = @($rows); note = 'Empty arrays mean absent from serialized fact tables, not a live runtime zero.' } | ConvertTo-Json -Depth 8
