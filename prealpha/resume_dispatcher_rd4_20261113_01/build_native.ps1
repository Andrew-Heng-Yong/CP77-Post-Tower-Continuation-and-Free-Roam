# Change only the two pre-claim conditions of the installed boxing owner.
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out = Join-Path $PSScriptRoot 'archive_01'
if (Test-Path -LiteralPath $out) { throw 'Fresh archive output required' }
$baselinePath = Join-Path $workspace 'prealpha/resume_dispatcher_rd3_deploy_20261113_02/deployment_01/installed_manifest_01.json'
if ((Get-FileHash -LiteralPath $baselinePath).Hash -cne 'FEC7BB5DAD74C59E1114D39B9B456FE827FA371CE45FE3B3C27AF73476FFBF05') { throw 'Baseline drift' }
$baseline = Get-Content -LiteralPath $baselinePath -Raw | ConvertFrom-Json
$contract = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'contract.json') -Raw | ConvertFrom-Json
$pins = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/sources.json') -Raw | ConvertFrom-Json
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
function Logic([string]$Operation, $Children) {
  $r = [WolvenKit.RED4.Types.questLogicalCondition]::new()
  $r.Operation = [Enum]::Parse([WolvenKit.RED4.Types.Enums+questLogicalOperation], $Operation)
  foreach ($c in $Children) { Add-RedHandle $r.Conditions $c }
  return $r
}
function Fact([string]$Name, [int]$Value) {
  return New-FactCondition $Name $Value ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)
}
function Journal($Definition) {
  $states = [Collections.Generic.List[object]]::new()
  foreach ($v in $Definition.live) {
    $p = [WolvenKit.RED4.Types.gameJournalPath]::new()
    $p.ClassName = [string]$Definition.class
    $p.RealPath = [string]$Definition.path
    $p.FileEntryIndex = [int32]2
    $t = [WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new()
    Set-RedHandleProperty $t 'Path' $p
    $t.State = [Enum]::Parse([WolvenKit.RED4.Types.Enums+gameJournalEntryState], @('Undefined','Inactive','Active','Succeeded','Failed')[[int]$v])
    $c = [WolvenKit.RED4.Types.questJournalCondition]::new()
    Set-RedHandleProperty $c 'Type' $t
    $states.Add($c)
  }
  return Logic 'OR' $states
}
function Contains-Journal($Condition) {
  if ($Condition -is [WolvenKit.RED4.Types.questJournalCondition]) { return $true }
  if ($Condition -is [WolvenKit.RED4.Types.questLogicalCondition]) {
    foreach ($h in $Condition.Conditions) { if (Contains-Journal $h.Chunk) { return $true } }
  }
  return $false
}

foreach ($row in @($baseline.core_files) + @($baseline.required_files)) {
  $p = Join-Path $baseline.game_root $row.path
  Assert-Plain $p
  if ((Get-FileHash -LiteralPath $p).Hash -cne $row.sha256) { throw "Installed input drift: $p" }
}
$watch = @{}
$donor = $baseline.archive_source
Assert-Plain $donor
$installedArchive = Join-Path $baseline.game_root 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$overrides = @{}
foreach ($p in $pins) {
  $key = [uint64]$p.key
  if ($watch.ContainsKey($key) -or $key -ne (Key $p.depot)) { throw 'Ambiguous reviewed provider' }
  $watch[$key] = $p
  if ($p.archive -ine $installedArchive) {
    $member = Join-Path $donor $p.depot
    if (Test-Path -LiteralPath $member -PathType Leaf) {
      # Only established Tower overrides can coexist with the native provider.
      if ($p.depot -cnotin @('ep1\quest\main_quests\q307\phases\q307_01_pickup.questphase',
                            'ep1\quest\main_quests\q307\phases\q307_cleanup.questphase',
                            'ep1\quest\main_quests\q307\q307.quest')) { throw "Unexpected Core overlay: $($p.depot)" }
      Assert-Plain $member
      $overrides[$key] = (Get-FileHash -LiteralPath $member).Hash
    }
  }
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
$current = $null
foreach ($file in $files) {
  $stamp = @($file.Length, $file.LastWriteTimeUtc.Ticks)
  $a = Open-Archive $file.FullName
  if ($file.FullName -ieq $installedArchive) { $current = $a }
  foreach ($key in $watch.Keys) {
    if (!$a.Files.ContainsKey($key)) { continue }
    $p = $watch[$key]
    $hash = Member-Hash $a.Files[$key]
    $reviewed = $file.FullName -ieq $p.archive -and $hash -ceq $p.sha256
    $baselineOverlay = $file.FullName -ieq $installedArchive -and $overrides.ContainsKey($key) -and $hash -ceq $overrides[$key]
    if (!$reviewed -and !$baselineOverlay) { throw "Unreviewed provider: $($p.depot) in $($file.FullName)" }
    $providers.Add(@{depot=$p.depot; archive=$file.FullName; sha256=$hash})
  }
  $file.Refresh()
  if ($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1]) { throw 'Archive drift during read' }
  $inventory.Add(@{path=$file.FullName; bytes=$stamp[0]; mtime_ticks=$stamp[1]})
}
if ($providers.Count -ne ($pins.Count + $overrides.Count) -or $null -eq $current -or $current.Files.Count -ne 1742) { throw 'Incomplete archive/provider review' }

if (@(Get-ChildItem -LiteralPath $donor -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked source tree' }
$source = Join-Path $out 'archive_source'
[void][IO.Directory]::CreateDirectory($source)
$expected = @{}
foreach ($file in Get-ChildItem -LiteralPath $donor -Recurse -File) {
  $depot = [IO.Path]::GetRelativePath($donor, $file.FullName).Replace('/','\')
  $key = Key $depot
  $hash = (Get-FileHash -LiteralPath $file.FullName).Hash
  if ($expected.ContainsKey($key) -or !$current.Files.ContainsKey($key) -or (Member-Hash $current.Files[$key]) -cne $hash) {
    throw "Donor does not match the installed member: $depot"
  }
  $dest = Join-Path $source $depot
  [void][IO.Directory]::CreateDirectory((Split-Path -Parent $dest))
  [IO.File]::Copy($file.FullName, $dest, $false)
  $expected[$key] = @{depot=$depot; sha256=$hash}
}
if ($expected.Count -ne $current.Files.Count) { throw 'Incomplete donor tree' }
foreach ($key in $overrides.Keys) {
  $d = $watch[$key].depot
  Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $d)) (Join-Path $out ((Split-Path $d -Leaf) + '.json'))
}

if (@($contract.depots).Count -ne 1) { throw 'Expected one boxing owner' }
$depot = [string]$contract.depots[0]
$target = Join-Path $source $depot
$quest = Read-Cr2wFile $target
$graph = $quest.RootChunk.Graph.Chunk
Export-Cr2wJson $quest (Join-Path $out 'before.questphase.json')
foreach ($id in $contract.native_guards) {
  $node = Get-QuestNode $graph $id
  $old = $node.Condition.Chunk
  if ($old -isnot [WolvenKit.RED4.Types.questLogicalCondition] -or $old.Operation.ToString() -cne 'AND') { throw "Guard $id shape drift" }
  $earned = [Collections.Generic.List[object]]::new()
  foreach ($h in $old.Conditions) {
    if (!(Contains-Journal $h.Chunk)) { $earned.Add($h.Chunk.DeepCopy()) }
  }
  foreach ($bag in @($contract.fixed_facts, $contract.live_only_facts)) {
    foreach ($p in $bag.PSObject.Properties) {
      $already = @($earned | Where-Object {
        $_ -is [WolvenKit.RED4.Types.questFactsDBCondition] -and $_.Type.Chunk.FactName.ToString() -ceq $p.Name
      })
      if ($already.Count -eq 0) { $earned.Add((Fact $p.Name $p.Value)) }
      elseif ($already.Count -ne 1 -or $already[0].Type.Chunk.Value.ToString() -cne [string]$p.Value) { throw "Conflicting fact $($p.Name)" }
    }
  }
  foreach ($name in @($contract.other_owner_receipts) + @($contract.own_receipts)) {
    if (!@($earned | Where-Object {
      $_ -is [WolvenKit.RED4.Types.questFactsDBCondition] -and $_.Type.Chunk.FactName.ToString() -ceq $name
    }).Count) { $earned.Add((Fact $name 0)) }
  }
  foreach ($j in $contract.journals) { $earned.Add((Journal $j)) }
  Set-RedHandleProperty $node 'Condition' (Logic 'OR' @($old.DeepCopy(), (Logic 'AND' $earned)))
}
Write-Cr2wFile $quest $target
$expected[(Key $depot)].sha256 = (Get-FileHash -LiteralPath $target).Hash
$packedPath = Join-Path $out 'zzzz_PTFR_Combined.archive'
$stream = [IO.File]::Open($packedPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
try {
  $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService, [WolvenKit.SerilogWrapper]::new())
  if (!$writer.WriteArchive([IO.DirectoryInfo]::new($source), $stream)) { throw 'Archive pack failed' }
} finally { $stream.Dispose() }
$packed = Open-Archive $packedPath
if ($packed.Files.Count -ne $expected.Count) { throw 'Packed member count drift' }
$members = foreach ($pair in $packed.Files.GetEnumerator()) {
  $r = $expected[$pair.Key]
  if ($null -eq $r -or (Member-Hash $pair.Value) -cne $r.sha256) { throw 'Packed member hash mismatch' }
  @{depot=$r.depot; key=$pair.Key.ToString(); sha256=$r.sha256}
}
$serialized = Join-Path $out 'readback.questphase'
$stream = [IO.File]::Open($serialized, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
try { $packed.Files[(Key $depot)].Extract($stream) } finally { $stream.Dispose() }
Export-Cr2wJson (Read-Cr2wFile $serialized) (Join-Path $out 'after.questphase.json')
@{status='MEMBERS_VERIFIED'; archive_sha256=(Get-FileHash -LiteralPath $packedPath).Hash; members=@($members);
  providers=$providers.ToArray(); archive_inventory=$inventory.ToArray(); changed=@($depot);
  contract_sha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'contract.json')).Hash} |
  ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
Write-Output "Verified $($packed.Files.Count) packed members and exported the changed graph for semantic review."
