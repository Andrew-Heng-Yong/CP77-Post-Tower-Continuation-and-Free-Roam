Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$manifestPath = Join-Path $PSScriptRoot 'manifest_01.json'
$outPath = Join-Path $PSScriptRoot 'native_validation_01.json'
if (Test-Path -LiteralPath $outPath) { throw 'Preserve prior validation; use a successor' }
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json -Depth 80
if ($manifest.status -cne 'STATIC_IDENTITY_MANIFEST_NOT_DEPLOYABLE' -or $manifest.owner_count -ne 237) { throw 'Manifest changed' }
$sources = @{}
$results = [Collections.Generic.List[object]]::new()
foreach ($g in $manifest.groups) {
  $nativePath = Join-Path $ws $g.native_binary
  if ((Get-FileHash -LiteralPath $nativePath -Algorithm SHA256).Hash -cne $g.native_binary_sha256) { throw "Native owner source changed: $nativePath" }
  if (-not $sources.ContainsKey($nativePath)) { $sources[$nativePath] = Read-Cr2wFile $nativePath }
  $graph = $sources[$nativePath].RootChunk.Graph.Chunk
  $ids = @($g.node_path.Split('/') | Select-Object -Skip 1)
  $owner = $null
  for ($i=0; $i -lt $ids.Count; $i++) {
    $id = $ids[$i]
    $owner = Get-QuestNode $graph ([int]$id)
    if (-not $owner) { throw "Owner node absent: $($g.id) $($g.node_path)" }
    if ($i -lt $ids.Count - 1) { $graph = $owner.PhaseGraph.Chunk }
  }
  $prefabCount = $owner.PhaseInstancePrefabs.Count
  $storedRefs = @($owner.PhaseInstancePrefabs | ForEach-Object { $_.PrefabNodeRef.ToString() })
  $expectedAlias = $g.prefab.Substring($g.prefab.LastIndexOf('/') + 1)
  $exact = $prefabCount -eq 1 -and ($storedRefs[0] -ceq $expectedAlias -or $storedRefs[0] -ceq $g.prefab)
  $results.Add([ordered]@{ id=$g.id; node_path=$g.node_path; owner_type=$owner.GetType().Name;
      prefab_count=$prefabCount; stored_refs=$storedRefs; expected_alias=$expectedAlias; exact=$exact })
}
$failed = @($results | Where-Object { -not $_.exact })
$output = [ordered]@{ status=if($failed.Count){'REVIEW_REQUIRED'}else{'PASS'};
  manifest_sha256=(Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash;
  owner_count=$results.Count; source_count=$sources.Count; failed_count=$failed.Count;
  failures=$failed; results=$results }
[IO.File]::WriteAllText($outPath,($output | ConvertTo-Json -Depth 80)+"`n",[Text.UTF8Encoding]::new($false))
@{status=$output.status;owner_count=$results.Count;failed=$failed.Count;source_count=$sources.Count}|ConvertTo-Json
