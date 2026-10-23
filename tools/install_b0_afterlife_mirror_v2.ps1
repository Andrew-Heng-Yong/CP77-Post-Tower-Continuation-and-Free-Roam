param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'Cyberpunk2077 is running; close it before replacement.'
}
$root = [IO.Path]::GetFullPath($GameRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
if (-not (Test-Path -LiteralPath (Join-Path $root 'archive\pc\content') -PathType Container)) {
    throw "Not a Cyberpunk 2077 installation: $root"
}
$relative = 'archive\pc\mod\TowerContinued_B0_Afterlife_Mirror.archive'
$target = [IO.Path]::GetFullPath((Join-Path $root $relative))
if (-not $target.StartsWith($root + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {
    throw "Target escaped game directory: $target"
}
$source = Join-Path $WorkspaceRoot 'build\B0_Afterlife_Mirror_V2\TowerContinued_B0_Afterlife_Mirror.archive'
$backup = Join-Path $WorkspaceRoot 'build\B0_Afterlife_Mirror_V2\backup\TowerContinued_B0_Afterlife_Mirror_v1.archive'
$v1Hash = 'FF013D15E9255EF78769A108C193194F8BB958B8453E5A7B734BCFBF68BE87A8'
$v2Hash = 'BAE339F2D61806DE691A78CC083FA6BE1BCB3660B60C374C69A7F57ABEE34090'
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing v2 archive: $source" }
if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { throw "Missing exact v1 target: $target" }
if (Test-Path -LiteralPath $backup) { throw "Refusing to overwrite backup: $backup" }
if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $v2Hash) { throw 'Unexpected v2 source hash' }
if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $v1Hash) { throw 'Installed archive is not the expected v1' }

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $backup) | Out-Null
Copy-Item -LiteralPath $target -Destination $backup -ErrorAction Stop
if ((Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash -ne $v1Hash) { throw 'Backup hash mismatch' }
if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'Cyberpunk2077 started during backup; replacement stopped.'
}
Copy-Item -LiteralPath $source -Destination $target -Force -ErrorAction Stop
if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $v2Hash) { throw 'Installed v2 hash mismatch' }
[pscustomobject]@{Target=$target;SHA256=$v2Hash;Backup=$backup;BackupSHA256=$v1Hash}
