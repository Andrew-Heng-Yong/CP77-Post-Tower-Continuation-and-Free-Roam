Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')

$prior = Join-Path $ws 'prealpha/raymond_rc1/candidate_03'
$out = Join-Path $PSScriptRoot 'candidate_01'
if (Test-Path $out) { throw 'Use a successor candidate; do not overwrite JC1.' }
$source = Join-Path $out 'archive_source'
$package = Join-Path $out 'package'
Copy-Item -LiteralPath (Join-Path $prior 'archive_source') -Destination $source -Recurse
Copy-Item -LiteralPath (Join-Path $prior 'package') -Destination $package -Recurse

$before = @{}
foreach ($p in Get-ChildItem $source -File -Recurse) {
  $rel = [IO.Path]::GetRelativePath($source, $p.FullName).Replace('/', '\')
  $before[$rel] = (Get-FileHash $p.FullName).Hash
}
if ($before.Count -ne 1172) { throw "Unexpected RC2 resource count $($before.Count)" }

# The native standalone route sets this before the player actually rides.
# Admit 0 or 1 only while every other untouched-story condition still passes.
$entryRel = 'towercontinued\sidejobs_s30\entries\mq006_rollercoaster.questphase'
$entryPath = Join-Path $source $entryRel
$entry = Read-Cr2wFile $entryPath
foreach ($id in @(65003, 65004)) {
  $node = Get-QuestNode $entry.RootChunk.Graph.Chunk $id
  $condition = $node.Condition.Chunk
  if ($condition.Operation.ToString() -cne 'AND') { throw "Entry guard $id changed" }
  $matches = @($condition.Conditions | Where-Object {
    $_.Chunk -is [WolvenKit.RED4.Types.questFactsDBCondition] -and
    $_.Chunk.Type.Chunk.FactName -ceq 'mq006_ride_no_quest'
  })
  if ($matches.Count -ne 1) { throw "Ride flag guard count changed at $id" }
  $v = $matches[0].Chunk.Type.Chunk
  if ($v.ComparisonType.ToString() -cne 'Equal' -or [int]$v.Value -ne 0) { throw "Ride flag guard changed at $id" }
  $v.ComparisonType = [WolvenKit.RED4.Types.Enums+EComparisonType]::LessOrEqual
  $v.Value = 1
  Add-RedHandle $condition.Conditions (New-FactCondition 'mq006_ride_no_quest' 0 'GreaterOrEqual')
}
Write-Cr2wFile $entry $entryPath
foreach ($id in @(65003, 65004)) {
  $conditions = (Get-QuestNode (Read-Cr2wFile $entryPath).RootChunk.Graph.Chunk $id).Condition.Chunk.Conditions
  $values = @($conditions | Where-Object {
    $_.Chunk -is [WolvenKit.RED4.Types.questFactsDBCondition] -and
    $_.Chunk.Type.Chunk.FactName -ceq 'mq006_ride_no_quest'
  } | ForEach-Object { "$($_.Chunk.Type.Chunk.ComparisonType):$($_.Chunk.Type.Chunk.Value)" } | Sort-Object)
  if (($values -join ',') -cne 'GreaterOrEqual:0,LessOrEqual:1') { throw "Entry readback failed $id" }
}

# The private story finale's five native no-quest tests must use the active
# one-time owner lease; the saved standalone-route history remains untouched.
$sceneRel = 'towercontinued\sidejobs_s30\native\base\quest\minor_quests\mq006\scenes\mq006_02_finale.scene'
$scenePath = Join-Path $source $sceneRel
$sceneJson = Join-Path $ws 'prealpha/sidejobs_s30/prepared_02/json/towercontinued/sidejobs_s30/native/base/quest/minor_quests/mq006/scenes/mq006_02_finale.scene.json'
$originalJson = [IO.File]::ReadAllText($sceneJson)
$opt = [WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
$originalDto = [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto], $originalJson, $opt)
$checkPath = Join-Path $out 'scene_roundtrip_baseline.scene'
$baselineFile = [WolvenKit.RED4.Archive.CR2W.CR2WFile]::new()
$baselineFile.RootChunk = $originalDto.Data.RootChunk
Write-Cr2wFile $baselineFile $checkPath
if ((Get-FileHash $checkPath).Hash -cne $before[$sceneRel]) { throw 'Private finale baseline roundtrip differs from RC2' }
Remove-Item -LiteralPath $checkPath

$pattern = '"comparisonType": "GreaterOrEqual",\s*"factName": "mq006_ride_no_quest",\s*"value": 1'
$replacement = '"comparisonType": "Equal", "factName": "PTFRWORLD_Coaster_QuestOwns", "value": 0'
$matches = [regex]::Matches($originalJson, $pattern)
if ($matches.Count -ne 5) { throw "Expected five private finale no-quest tests; found $($matches.Count)" }
$modifiedJson = [regex]::Replace($originalJson, $pattern, $replacement)
$dto = [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto], $modifiedJson, $opt)
$scene = [WolvenKit.RED4.Archive.CR2W.CR2WFile]::new()
$scene.RootChunk = $dto.Data.RootChunk
Write-Cr2wFile $scene $scenePath
$sceneReadback = Join-Path $out 'scene_readback_01.json'
Export-Cr2wJson (Read-Cr2wFile $scenePath) $sceneReadback
$readbackText = [IO.File]::ReadAllText($sceneReadback)
if ([regex]::Matches($readbackText, '"factName": "PTFRWORLD_Coaster_QuestOwns"').Count -ne 5 -or
    [regex]::Matches($readbackText, '"factName": "mq006_ride_no_quest"').Count -ne 0) {
  throw 'Private finale condition readback failed'
}

$reds = Join-Path $package 'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds'
$old = [IO.File]::ReadAllText($reds)
$needle = 'public static func FactMax0() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 0]; }'
$replacementReds = 'public static func FactMax0() -> array<Int32> { return [0, 0, 0, 0, 1, 0, 0]; }'
if ($old.Split(@($needle), [StringSplitOptions]::None).Count -ne 2) { throw 'S30 fact max table changed' }
[IO.File]::WriteAllText($reds, $old.Replace($needle, $replacementReds), [Text.UTF8Encoding]::new($false))

$changed = @($entryRel, $sceneRel)
$after = @{}
foreach ($p in Get-ChildItem $source -File -Recurse) {
  $rel = [IO.Path]::GetRelativePath($source, $p.FullName).Replace('/', '\')
  $after[$rel] = (Get-FileHash $p.FullName).Hash
  if ($rel -cnotin $changed -and $after[$rel] -cne $before[$rel]) { throw "Unchanged resource drift $rel" }
}
if ($after.Count -ne 1172) { throw "Resource count changed to $($after.Count)" }
foreach ($rel in $changed) { if ($after[$rel] -ceq $before[$rel]) { throw "Expected changed resource unchanged $rel" } }

$archive = Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$stream = [IO.File]::Create($archive)
$hs = [WolvenKit.Common.Services.HashService]::new(); $hs.Load()
try {
  if (-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs, [WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source), $stream)) { throw 'Archive writer failed' }
} finally { $stream.Dispose() }
$packed = $null
if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive, $hs, [ref]$packed).ToString() -cne 'NoError' -or $packed.Files.Count -ne 1172) { throw 'Archive readback failed' }
foreach ($e in $packed.Files.Values) {
  $expected = $after[$e.Name]
  if (!$expected) { throw "Unexpected packed resource $($e.Name)" }
  $m = [IO.MemoryStream]::new()
  try { $e.Extract($m); $hash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray())) } finally { $m.Dispose() }
  if ($hash -cne $expected) { throw "Packed resource mismatch $($e.Name)" }
}
$files = @(Get-ChildItem $package -File -Recurse)
if ($files.Count -ne 51) { throw "Package file count $($files.Count)" }
$manifest = [ordered]@{
  status = 'JC1_51_FILE_SUCCESSOR_STAGED_LIVE_TEST_PENDING'
  source_members = 1172
  changed_resources = $changed
  changed_resource_before = @($changed | ForEach-Object { $before[$_] })
  changed_resource_after = @($changed | ForEach-Object { $after[$_] })
  finale_noquest_condition_count = 5
  files = @($files | ForEach-Object {
    @{ path = [IO.Path]::GetRelativePath($package, $_.FullName).Replace('\', '/'); sha256 = (Get-FileHash $_.FullName).Hash }
  })
}
[IO.File]::WriteAllText((Join-Path $out 'manifest.json'), ($manifest | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))
@{ status = $manifest.status; members = 1172; changed_resources = $changed.Count; files = 51 } | ConvertTo-Json
