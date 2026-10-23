param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$oldHash = '3E060AC9AB7A284265E822FF1FDAA22FCACAE1AAB013C80AE159B41BF6644203'
$newHash = 'F8E8D001FB639F62FD5FB040F3455B834FB618C24F76F5B96BF6F69C18742DA4'
$source = Join-Path $WorkspaceRoot 'build\B0_H10_Persistent\TowerContinued_B0_H10_Persistent.archive'
$target = Join-Path $GameRoot 'archive\pc\mod\TowerContinued_B0_H10_Persistent.archive'
$backup = Join-Path $WorkspaceRoot 'build\B0_H10_Persistent\backup\TowerContinued_B0_H10_Persistent_v2.archive'
$resolvedWorkspace = (Resolve-Path -LiteralPath $WorkspaceRoot).Path.TrimEnd('\')
$resolvedGame = (Resolve-Path -LiteralPath $GameRoot).Path.TrimEnd('\')
$resolvedSource = (Resolve-Path -LiteralPath $source).Path
$resolvedTarget = (Resolve-Path -LiteralPath $target).Path
$backupParent = Split-Path -Parent $backup
if (-not $resolvedSource.StartsWith("$resolvedWorkspace\", [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Source is outside the workspace'
}
if (-not $resolvedTarget.StartsWith("$resolvedGame\", [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Target is outside the game directory'
}
if (-not $backupParent.StartsWith("$resolvedWorkspace\", [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Backup is outside the workspace'
}
if (@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'Close Cyberpunk 2077 completely before replacing the archive'
}
if ((Get-FileHash -LiteralPath $resolvedSource -Algorithm SHA256).Hash -ne $newHash) {
    throw 'Candidate archive hash mismatch'
}
if ((Get-FileHash -LiteralPath $resolvedTarget -Algorithm SHA256).Hash -ne $oldHash) {
    throw 'Installed archive is not the exact tested v2; refusing overwrite'
}
New-Item -ItemType Directory -Force -Path $backupParent | Out-Null
if (Test-Path -LiteralPath $backup) {
    if ((Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash -ne $oldHash) {
        throw 'Existing backup differs from tested v2; refusing overwrite'
    }
} else {
    Copy-Item -LiteralPath $resolvedTarget -Destination $backup
}
if ((Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash -ne $oldHash) {
    throw 'Backup verification failed'
}
if (@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'Game started during preflight; refusing replacement'
}
Copy-Item -LiteralPath $resolvedSource -Destination $resolvedTarget -Force
if ((Get-FileHash -LiteralPath $resolvedTarget -Algorithm SHA256).Hash -ne $newHash) {
    throw 'Installed archive verification failed; the v2 backup remains in the workspace'
}
Write-Output "Installed mirror-actions archive: $newHash"
Write-Output "Recoverable v2 backup: $backup"
