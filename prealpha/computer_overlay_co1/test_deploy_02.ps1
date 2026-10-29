$ErrorActionPreference = 'Stop'
$root = Join-Path $PSScriptRoot 'candidate_02\fixture_01'
if (Test-Path -LiteralPath $root) { throw 'Fixture already exists; preserve evidence' }
$game = Join-Path $root 'game'
$recovery = Join-Path $root 'recovery'
$target = Join-Path $game 'r6\scripts\virtual-atelier-full\SetupNewTab.reds'
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'candidate_02\original\SetupNewTab.reds') -Destination $target
$deploy = Join-Path $PSScriptRoot 'deploy_02.ps1'
$actions = @('Validate','Install','Verify','ValidateRollback','Rollback','Validate')
$out = foreach ($action in $actions) {
  & $deploy -Action $action -GameRoot $game -RecoveryDir $recovery | Out-Null
  if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { throw "Fixture action failed: $action" }
  [pscustomobject]@{Action=$action;SHA256=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash}
}
$negative = $false
[IO.File]::AppendAllText($target, 'tampered')
try { & $deploy -Action Validate -GameRoot $game -RecoveryDir $recovery 2>$null | Out-Null }
catch { $negative = $true }
if (-not $negative) { throw 'Hash mismatch was not rejected' }
$result = [pscustomobject]@{Status='PASS';Actions=$out;HashMismatchRejected=$negative;GameWrites=0}
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'candidate_02\fixture_result_01.json') -Encoding utf8
$result | Select-Object Status,@{N='ActionCount';E={$_.Actions.Count}},HashMismatchRejected,GameWrites | Format-List
