# Render and independently parse the XL only. Never run the pinned B7 builder.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'gig_family_b7_1_xl.ps1')
$workspace = Split-Path -Parent $PSScriptRoot
$root = Join-Path $workspace 'research/gig_restoration/family_b7_1'
if (Test-Path -LiteralPath (Join-Path $root 'install_receipt.json')) { throw 'Installed B7.1 evidence pinned' }
$parser = B71Parser
$manifest = B71Manifest $workspace
$oldReceiptPath = Join-Path $workspace 'research/gig_restoration/family_b7/install_receipt.json'
R5Match $oldReceiptPath '24A90BDCC694FAD4099668453D98B37A83D9D0B1BFBD2B536FC3DA4607B5D405'
$old = Get-Content -LiteralPath $oldReceiptPath -Raw | ConvertFrom-Json
$oldXl = Join-Path $workspace 'build/GigFamilyB7/TowerContinued_FamilyB7.archive.xl'
R5Match $oldXl '58DC55116DD316975EC1EE48C56F80FAA55B2D7268327F39775EFDAF0A26259F'
foreach ($f in $old.files) {
    R5Match (Join-Path $workspace $f.source) $f.sha256
    R5Match (Join-Path $old.game_root $f.relative) $f.sha256
}
$pins = [ordered]@{}
foreach ($name in @('manifest.json','install_receipt.json','assessment.json','tests.json','deployment_tests.json','compile_result.json','build_plan.json','owner_review.json','fixer_review.json')) {
    $rel = 'research/gig_restoration/family_b7/' + $name
    $pins[$rel] = R5Hash (Join-Path $workspace $rel)
}
foreach ($name in @('build_gig_family_b7.ps1','prepare_gig_family_b7.py','audit_gig_family_b7.py','compile_gig_family_b7.py','test_gig_family_b7.py','test_gig_family_b7_deployment.ps1','deploy_gig_family_b7.ps1')) {
    $rel = 'tools/' + $name
    $pins[$rel] = R5Hash (Join-Path $workspace $rel)
}
foreach ($f in $old.files) { $pins[$f.source] = $f.sha256 }
$oldText = Get-Content -LiteralPath $oldXl -Raw
$parserError = ''
try { B71Parse $oldText | Out-Null } catch { $parserError = $_.Exception.Message }
if (-not $parserError) { throw 'Regression: old malformed YAML must fail the actual parser' }
$text = B71Render $manifest.boots
$validation = B71Validate $text $manifest
$mutants = [ordered]@{
    legacy_collapsed=$oldText
    wrong_parent=$text.Replace('ep1\quest\ep1.quest','base\quest\quest.quest')
    wrong_socket=$text.Replace('socket: Out','socket: In')
    wrong_node=$text.Replace('node: [1]','node: [2]')
    scalar_node=$text.Replace('node: [1]','node: 1')
    extra_node=$text.Replace('node: [1]','node: [1, 2]')
    duplicate_boot=$text.Replace($manifest.boots[1],$manifest.boots[0])
    missing_boot=(B71Render $manifest.boots[0..74])
    extra_key=$text.Replace('      input:',"      unknown: true`n      input:")
    wrong_case=$text.Replace('socket: Out','socket: out')
    extra_document=($text + "---`nquest: {phases: []}`n")
}
$rejected = [Collections.Generic.List[string]]::new()
foreach ($name in $mutants.Keys) {
    $refused = $false
    try { B71Validate $mutants[$name] $manifest | Out-Null } catch { $refused = $true }
    if (-not $refused) { throw "Accepted invalid XL mutant: $name" }
    $rejected.Add($name)
}
New-Item -ItemType Directory -Force (Join-Path $root 'predecessor') | Out-Null
Copy-Item -LiteralPath $oldXl -Destination (Join-Path $root 'predecessor/TowerContinued_FamilyB7.archive.xl')
$relativeSource = 'build/GigFamilyB7_1/TowerContinued_FamilyB7.archive.xl'
$output = Join-Path $workspace $relativeSource
New-Item -ItemType Directory -Force (Split-Path -Parent $output) | Out-Null
[IO.File]::WriteAllText($output,$text,[Text.UTF8Encoding]::new($false))
B71Validate (Get-Content -LiteralPath $output -Raw) $manifest | Out-Null
$log = Join-Path $old.game_root 'red4ext/plugins/ArchiveXL/ArchiveXL.log'
$lines = @(Get-Content -LiteralPath $log | Where-Object { $_ -match 'FamilyB7' })
if (-not @($lines | Where-Object { $_ -match 'illegal map value' }).Count) { throw 'Expected live parse failure evidence missing' }
R5Json (Join-Path $root 'startup_failure.json') ([ordered]@{
    captured_utc=[DateTime]::UtcNow.ToString('o'); source=$log; source_sha256=R5Hash $log
    lines=$lines; independent_parser_error=$parserError
    cause='B7 renderer collapsed path, parent and input fields onto one YAML line. ArchiveXL rejected configuration before the boot phases could register.'
    scope='Config parse failure confirmed; no new-owner gameplay proof.'
})
$tools = [ordered]@{}
foreach ($name in @('gig_family_b7_1_xl.ps1','prepare_gig_family_b7_1.ps1','test_gig_family_b7_1_deployment.ps1','afterlife_faces_r5_deployment.ps1')) {
    $rel = 'tools/' + $name
    $tools[$rel] = R5Hash (Join-Path $workspace $rel)
}
foreach ($p in $pins.Keys) { R5Match (Join-Path $workspace $p) $pins[$p] }
$result = [ordered]@{
    status='PASS_B7_1_YAML_REGRESSION_ENGINE_PENDING'; utc=[DateTime]::UtcNow.ToString('o')
    configuration_only=$true; validation=$validation; legacy_parser_rejected=$true; refused_mutants=@($rejected)
    parser_path=$parser; parser_sha256=R5Hash $parser; pinned_predecessor_evidence=$pins; tools=$tools
    files=@([ordered]@{source=$relativeSource; relative='archive/pc/mod/TowerContinued_FamilyB7.archive.xl'; predecessor=R5Hash $oldXl; sha256=R5Hash $output})
    other_b7_files=@($old.files | Where-Object { $_.relative -ne 'archive/pc/mod/TowerContinued_FamilyB7.archive.xl' })
    new_archive_build=$false; script_recompile=$false; engine_proof=$false
}
R5Json (Join-Path $root 'tests.json') $result
[pscustomobject]$result | Select-Object status,validation,refused_mutants,files | ConvertTo-Json -Depth 6
