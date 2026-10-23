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
$target = [IO.Path]::GetFullPath((Join-Path $root 'archive\pc\mod\TowerContinued_B0_Afterlife_Mirror.archive'))
if (-not $target.StartsWith($root + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {
    throw "Target escaped game directory: $target"
}
$source = Join-Path $WorkspaceRoot 'build\B0_Afterlife_Mirror_V3\TowerContinued_B0_Afterlife_Mirror.archive'
$backup = Join-Path $WorkspaceRoot 'build\B0_Afterlife_Mirror_V3\backup\TowerContinued_B0_Afterlife_Mirror_v2.archive'
$v2Hash = 'BAE339F2D61806DE691A78CC083FA6BE1BCB3660B60C374C69A7F57ABEE34090'
$v3Hash = '7646FC8C1499A1BA8F279553D0743F3EB4CA4CD25F812A7A9D562C5742C8C926'
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing v3 archive: $source" }
if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { throw "Missing exact v2 target: $target" }
if (Test-Path -LiteralPath $backup) { throw "Refusing to overwrite backup: $backup" }
if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $v3Hash) { throw 'Unexpected v3 source hash' }
if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $v2Hash) { throw 'Installed archive is not the expected v2' }

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $backup) | Out-Null
Copy-Item -LiteralPath $target -Destination $backup -ErrorAction Stop
if ((Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash -ne $v2Hash) { throw 'Backup hash mismatch' }
if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'Cyberpunk2077 started during backup; replacement stopped.'
}
Copy-Item -LiteralPath $source -Destination $target -Force -ErrorAction Stop
if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $v3Hash) { throw 'Installed v3 hash mismatch' }
[pscustomobject]@{Target=$target;SHA256=$v3Hash;Backup=$backup;BackupSHA256=$v2Hash}
