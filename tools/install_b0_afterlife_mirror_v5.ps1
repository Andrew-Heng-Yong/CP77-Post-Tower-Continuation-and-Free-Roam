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
$backupRoot = Join-Path $WorkspaceRoot 'build\B0_Afterlife_Mirror_V5\backup'
$items = @(
    [pscustomobject]@{
        Source = Join-Path $WorkspaceRoot 'build\B0_Afterlife_Mirror_V5\TowerContinued_B0_Afterlife_Mirror.archive'
        Target = Join-Path $root 'archive\pc\mod\TowerContinued_B0_Afterlife_Mirror.archive'
        Backup = Join-Path $backupRoot 'TowerContinued_B0_Afterlife_Mirror_v4.archive'
        OldHash = '07A6A90D036D3E6061EF093C137D7388FFDBACB7DF0A127ABE6439AC20E05407'
        NewHash = '2643F18D8946FB9C96FB479FD91418D3446E4792CE21562A11CBEC371D534003'
    },
    [pscustomobject]@{
        Source = Join-Path $WorkspaceRoot 'diagnostics\PTFR_B0_Afterlife_Mirror\init.lua'
        Target = Join-Path $root 'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_B0_Afterlife_Mirror\init.lua'
        Backup = Join-Path $backupRoot 'PTFR_B0_Afterlife_Mirror_v4_init.lua'
        OldHash = '5E947591DEDDD522C9FEF99294EDCE8CABE9797CFA0D90178B6687A002064D46'
        NewHash = 'C56FE010E8549B9DF3ECDC97A4A573469523CEFEFD4B41E0A0DFCEEB194795B4'
    }
)
foreach ($item in $items) {
    $target = [IO.Path]::GetFullPath($item.Target)
    if (-not $target.StartsWith($root + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {
        throw "Target escaped game directory: $target"
    }
    if (-not (Test-Path -LiteralPath $item.Source -PathType Leaf)) { throw "Missing source: $($item.Source)" }
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { throw "Missing exact target: $target" }
    if (Test-Path -LiteralPath $item.Backup) { throw "Refusing to overwrite backup: $($item.Backup)" }
    if ((Get-FileHash -LiteralPath $item.Source -Algorithm SHA256).Hash -ne $item.NewHash) { throw "Unexpected source hash: $($item.Source)" }
    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $item.OldHash) { throw "Unexpected installed hash: $target" }
}
New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
foreach ($item in $items) {
    Copy-Item -LiteralPath $item.Target -Destination $item.Backup -ErrorAction Stop
    if ((Get-FileHash -LiteralPath $item.Backup -Algorithm SHA256).Hash -ne $item.OldHash) { throw "Backup hash mismatch: $($item.Backup)" }
}
if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'Cyberpunk2077 started during backup; replacement stopped.'
}
foreach ($item in $items) {
    Copy-Item -LiteralPath $item.Source -Destination $item.Target -Force -ErrorAction Stop
    if ((Get-FileHash -LiteralPath $item.Target -Algorithm SHA256).Hash -ne $item.NewHash) { throw "Installed hash mismatch: $($item.Target)" }
    [pscustomobject]@{Target=$item.Target;SHA256=$item.NewHash;Backup=$item.Backup}
}
