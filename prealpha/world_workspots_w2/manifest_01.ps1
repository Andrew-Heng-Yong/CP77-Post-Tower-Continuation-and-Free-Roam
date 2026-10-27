Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$inputPath = Join-Path $PSScriptRoot 'audit_01.json'
$outPath = Join-Path $PSScriptRoot 'manifest_01.json'
if (Test-Path -LiteralPath $outPath) { throw 'Preserve prior manifest; use a successor' }
$audit = Get-Content -LiteralPath $inputPath -Raw | ConvertFrom-Json -Depth 80
if ($audit.status -cne 'STATIC_SUPPORT_CANDIDATES_NOT_PRODUCTION_ALLOWLIST' -or $audit.rows -ne 477) { throw 'Audit changed' }
$groups = [Collections.Generic.List[object]]::new()
$allHashes = [Collections.Generic.HashSet[string]]::new()
foreach ($g in $audit.groups) {
  $hashes = [Collections.Generic.List[string]]::new()
  foreach ($ref in $g.community_refs) {
    $hash = [WolvenKit.RED4.Types.NodeRef]::CalculateHash($ref).ToString()
    if (-not $allHashes.Add($hash)) { throw "Repeated community hash: $hash" }
    $hashes.Add($hash)
  }
  $native = Join-Path $ws ($g.source -replace '\.json$','')
  if (-not (Test-Path -LiteralPath $native -PathType Leaf)) { throw "Native owner source missing: $native" }
  $id = [int]$g.candidate_index
  $prefix = if ($id -eq 183) { 'PTFRWW1_CVI116_' } else { 'PTFRWW2_' + $id.ToString('D3') + '_' }
  $groups.Add([ordered]@{
    id = $id; prefix = $prefix; prefab = $g.prefab;
    community_refs = @($g.community_refs); spawner_hashes = @($hashes);
    source = $g.source; native_binary = [IO.Path]::GetRelativePath($ws,$native);
    native_binary_sha256 = (Get-FileHash -LiteralPath $native -Algorithm SHA256).Hash;
    node_path = $g.node_path; resource = $g.resource;
    asset_sha256 = $g.asset_sha256; binding = $g.binding;
  })
}
if ($groups.Count -ne 237) { throw "Candidate count drift: $($groups.Count)" }
$ww1 = @($groups | Where-Object { $_.id -eq 183 })
if ($ww1.Count -ne 1 -or $ww1[0].spawner_hashes.Count -ne 1 -or $ww1[0].spawner_hashes[0] -cne '13399962301655001666') { throw 'Live WW1 identity drift' }
$output = [ordered]@{
  status = 'STATIC_IDENTITY_MANIFEST_NOT_DEPLOYABLE';
  audit_sha256 = (Get-FileHash -LiteralPath $inputPath -Algorithm SHA256).Hash;
  owner_count = $groups.Count; spawner_count = $allHashes.Count;
  live_proven_owner_id = 183;
  groups = @($groups);
  caveats = @('No exact live actor has been observed for the other owners',
    'Prefab-only ownership still requires independent semantic checks',
    'The census does not cover all NPC families',
    'No game files, saved games or facts changed');
}
[IO.File]::WriteAllText($outPath,($output | ConvertTo-Json -Depth 80) + "`n",[Text.UTF8Encoding]::new($false))
$output | Select-Object status,owner_count,spawner_count,live_proven_owner_id | ConvertTo-Json
