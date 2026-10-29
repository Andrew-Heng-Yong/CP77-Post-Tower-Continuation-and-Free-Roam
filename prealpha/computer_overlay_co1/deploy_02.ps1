param(
  [ValidateSet('Validate','Install','Verify','ValidateRollback','Rollback')]
  [string]$Action = 'Validate',
  [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
  [string]$RecoveryDir = ''
)
$ErrorActionPreference = 'Stop'
$relative = 'r6\scripts\virtual-atelier-full\SetupNewTab.reds'
$target = Join-Path $GameRoot $relative
$candidate = Join-Path $PSScriptRoot 'candidate_02\SetupNewTab.reds'
$original = Join-Path $PSScriptRoot 'candidate_02\original\SetupNewTab.reds'
$proof = Join-Path $PSScriptRoot 'candidate_02\compile_01\result.json'
$workspace = (Get-Item -LiteralPath (Join-Path $PSScriptRoot '..\..')).FullName
if (-not $RecoveryDir) { $RecoveryDir = Join-Path $workspace 'recovery\computer_overlay_co1_01' }
$backup = Join-Path $RecoveryDir 'SetupNewTab.reds'
$oldHash = '14B651576CC6D1FCEDBC11A48A96D1A2AC79DD84FCCFB90097F4169057378F80'
$newHash = '5743CDCD6F8CD46A58F9642002F75EBCA25D84BE340856C2E6D85B15DAD973F8'
function Assert-Hash([string]$Path, [string]$Expected) {
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Missing file: $Path" }
  $actual = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
  if ($actual -ne $Expected) { throw "Hash mismatch: $Path expected $Expected got $actual" }
}
function Assert-Closed {
  if (Get-Process | Where-Object { $_.ProcessName -match 'Cyberpunk2077|REDprelauncher' }) { throw 'Close Cyberpunk 2077 and REDprelauncher first' }
}
Assert-Hash $candidate $newHash
Assert-Hash $original $oldHash
$compilation = Get-Content -LiteralPath $proof -Raw | ConvertFrom-Json
if ($compilation.status -ne 'PASS' -or $compilation.candidate_sha256 -ne $newHash -or -not $compilation.source_hashes_unchanged) { throw 'Candidate compilation proof invalid' }
switch ($Action) {
  'Validate' {
    Assert-Hash $target $oldHash
  }
  'Install' {
    Assert-Closed
    Assert-Hash $target $oldHash
    if (Test-Path -LiteralPath $backup) { Assert-Hash $backup $oldHash }
    else {
      New-Item -ItemType Directory -Force -Path $RecoveryDir | Out-Null
      Copy-Item -LiteralPath $target -Destination $backup
      Assert-Hash $backup $oldHash
    }
    try {
      Copy-Item -LiteralPath $candidate -Destination $target -Force
      Assert-Hash $target $newHash
    } catch {
      Copy-Item -LiteralPath $backup -Destination $target -Force
      throw
    }
  }
  'Verify' { Assert-Hash $target $newHash }
  'ValidateRollback' {
    Assert-Hash $target $newHash
    Assert-Hash $backup $oldHash
  }
  'Rollback' {
    Assert-Closed
    Assert-Hash $target $newHash
    Assert-Hash $backup $oldHash
    Copy-Item -LiteralPath $backup -Destination $target -Force
    Assert-Hash $target $oldHash
  }
}
[pscustomobject]@{Status='PASS';Action=$Action;Target=$target;SHA256=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash} | Format-List
