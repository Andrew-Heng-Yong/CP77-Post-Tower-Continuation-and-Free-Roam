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
$source = Join-Path $WorkspaceRoot 'build\B0_Afterlife_Mirror_V4\TowerContinued_B0_Afterlife_Mirror.archive'
$backup = Join-Path $WorkspaceRoot 'build\B0_Afterlife_Mirror_V4\backup\TowerContinued_B0_Afterlife_Mirror_v3.archive'
$v3Hash = '7646FC8C1499A1BA8F279553D0743F3EB4CA4CD25F812A7A9D562C5742C8C926'
$v4Hash = '07A6A90D036D3E6061EF093C137D7388FFDBACB7DF0A127ABE6439AC20E05407'
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing v4 archive: $source" }
if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { throw "Missing exact v3 target: $target" }
if (Test-Path -LiteralPath $backup) { throw "Refusing to overwrite backup: $backup" }
if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $v4Hash) { throw 'Unexpected v4 source hash' }
if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $v3Hash) { throw 'Installed archive is not the expected v3' }

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $backup) | Out-Null
Copy-Item -LiteralPath $target -Destination $backup -ErrorAction Stop
if ((Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash -ne $v3Hash) { throw 'Backup hash mismatch' }
if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'Cyberpunk2077 started during backup; replacement stopped.'
}
Copy-Item -LiteralPath $source -Destination $target -Force -ErrorAction Stop
if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $v4Hash) { throw 'Installed v4 hash mismatch' }
[pscustomobject]@{Target=$target;SHA256=$v4Hash;Backup=$backup;BackupSHA256=$v3Hash}
