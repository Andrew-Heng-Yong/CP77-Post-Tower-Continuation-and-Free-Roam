param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'Cyberpunk2077 is running; close it before installation.'
}
$root = [IO.Path]::GetFullPath($GameRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
if (-not (Test-Path -LiteralPath (Join-Path $root 'archive\pc\content') -PathType Container)) {
    throw "Not a Cyberpunk 2077 installation: $root"
}
$items = @(
    [pscustomobject]@{
        Source = Join-Path $WorkspaceRoot 'build\B0_Afterlife_Mirror\TowerContinued_B0_Afterlife_Mirror.archive'
        Target = Join-Path $root 'archive\pc\mod\TowerContinued_B0_Afterlife_Mirror.archive'
    },
    [pscustomobject]@{
        Source = Join-Path $WorkspaceRoot 'archive\b0_afterlife_mirror\TowerContinued_B0_Afterlife_Mirror.archive.xl'
        Target = Join-Path $root 'archive\pc\mod\TowerContinued_B0_Afterlife_Mirror.archive.xl'
    },
    [pscustomobject]@{
        Source = Join-Path $WorkspaceRoot 'diagnostics\PTFR_B0_Afterlife_Mirror\init.lua'
        Target = Join-Path $root 'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_B0_Afterlife_Mirror\init.lua'
    }
)
foreach ($item in $items) {
    $target = [IO.Path]::GetFullPath($item.Target)
    if (-not $target.StartsWith($root + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {
        throw "Target escaped game directory: $target"
    }
    if (-not (Test-Path -LiteralPath $item.Source -PathType Leaf)) { throw "Missing source: $($item.Source)" }
    if (Test-Path -LiteralPath $target) { throw "Refusing to overwrite existing target: $target" }
}
foreach ($item in $items) {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $item.Target) | Out-Null
    Copy-Item -LiteralPath $item.Source -Destination $item.Target -ErrorAction Stop
    $sourceHash = (Get-FileHash -LiteralPath $item.Source -Algorithm SHA256).Hash
    $targetHash = (Get-FileHash -LiteralPath $item.Target -Algorithm SHA256).Hash
    if ($targetHash -ne $sourceHash) { throw "Installed hash mismatch: $($item.Target)" }
    [pscustomobject]@{ Target=$item.Target; SHA256=$targetHash }
}
