param([string[]]$Slots = @('AutoSave-16', 'ManualSave-33'))
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$saveRoot = 'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077'
$wk = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0'
foreach ($name in @('WolvenKit.Core.dll', 'WolvenKit.Common.dll', 'WolvenKit.RED4.dll')) {
  [void][Reflection.Assembly]::LoadFrom((Join-Path $wk $name))
}
function Get-PhaseHash([int[]]$Path) {
  if ($Path.Count -eq 0 -or $Path[0] -notin @(0, 1)) { throw 'Unbound phase root' }
  [uint64]$hash = if ($Path[0] -eq 0) { 0x811C9DC5 } else { 0x01800013 }
  foreach ($word in $Path) {
    $bytes = @(($word -band 255), (($word -shr 8) -band 255))
    foreach ($byte in $bytes) {
      $hash = (($hash -bxor [uint64]$byte) * [uint64]16777619) -band [uint64]4294967295
    }
  }
  return [uint32]$hash
}
$rows = foreach ($slot in $Slots) {
  $savePath = Join-Path (Join-Path $saveRoot $slot) 'sav.dat'
  $before = (Get-FileHash -LiteralPath $savePath -Algorithm SHA256).Hash
  $stream = [IO.File]::Open($savePath, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
  try {
    $save = $null
    $status = ([WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($stream)).ReadFile([ref]$save).ToString()
    if ($status -ne 'NoError') { throw "Save parse $status for $slot" }
    $quest = @($save.Nodes | Where-Object Name -eq 'questSystem')
    if ($quest.Count -ne 1) { throw 'Ambiguous questSystem' }
    $custom = @($quest[0].Children | Where-Object Name -eq 'customArray')
    $event = @($quest[0].Children | Where-Object Name -eq 'eventManager')
    if ($custom.Count -ne 1 -or $event.Count -ne 1) { throw 'Missing graph store' }
    if ($custom[0].Value -isnot [WolvenKit.RED4.Save.CustomArray] -or
        $event[0].Value -isnot [WolvenKit.RED4.Save.EventManager]) { throw 'Unexpected parser type' }
    $words = $custom[0].Value.Unknown
    $paths = [Collections.Generic.List[object]]::new()
    $at = 0
    while ($at -lt $words.Count) {
      $length = [int]$words[$at]; $at++
      if ($length -lt 0 -or $at + $length -gt $words.Count) { throw 'Malformed saved path list' }
      if ($length -eq 0) { continue }
      $path = [int[]]@($words[$at..($at+$length-1)])
      if ($path -contains 42351) { $paths.Add($path) }
      $at += $length
    }
    $contexts = [Collections.Generic.List[object]]::new()
    foreach ($path in $paths) {
      if ($path[0] -in @(0, 1)) {
        $contexts.Add(@{ path = $path; hash = (Get-PhaseHash $path) })
      }
    }
    $parentContexts = @(@{ path = [int[]]@(1); hash = (Get-PhaseHash ([int[]]@(1))) })
    $selected = [Collections.Generic.List[object]]::new()
    $ordinal = 0
    foreach ($record in $event[0].Value.Unknown) {
      $nodeId = [uint32]$record.Unknown3 -bor ([uint32]$record.Unknown4 -shl 16)
      $phaseHash = [uint32]$record.Unknown2
      if (($phaseHash -eq $parentContexts[0].hash -and $nodeId -eq 42351) -or
          @($contexts | Where-Object { $_.hash -eq $phaseHash }).Count -gt 0) {
        $selected.Add(@{ ordinal = $ordinal; token = $record.Unknown1.ToString(); hash = $phaseHash; node = $nodeId })
      }
      $ordinal++
    }
    [ordered]@{
      slot = $slot; sha256 = $before; custom_array_words = $words.Count;
      phase_paths_containing_42351 = @($paths.ToArray());
      registered_child_contexts = @($contexts.ToArray());
      parent_context = $parentContexts[0];
      event_manager_slots = $ordinal;
      exact_event_rows = @($selected.ToArray())
    }
  } finally { $stream.Dispose() }
  if ((Get-FileHash -LiteralPath $savePath -Algorithm SHA256).Hash -cne $before) { throw "Save changed: $slot" }
}
@{ status = 'READ_ONLY_SAVED_PHASE_MEMBERSHIP'; rows = @($rows);
   limit = 'CustomArray membership is retained path history, not current owner proof; EventManager rows are saved registrations, not action completion.' } | ConvertTo-Json -Depth 8
