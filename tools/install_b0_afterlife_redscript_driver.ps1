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

$archive = Join-Path $root 'archive\pc\mod\TowerContinued_B0_Afterlife_Mirror.archive'
$nativeHash = '2643F18D8946FB9C96FB479FD91418D3446E4792CE21562A11CBEC371D534003'
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $nativeHash) {
    throw 'Installed Afterlife v5 archive differs from the validated package.'
}

$oldSource = Join-Path $WorkspaceRoot 'diagnostics\PTFR_B0_Afterlife_Mirror\init.lua'
$observerSource = Join-Path $WorkspaceRoot 'diagnostics\PTFR_B0_Afterlife_Mirror_v6\init.lua'
$scriptSource = Join-Path $WorkspaceRoot 'redscript\PTFR_B0_Afterlife_Mirror\AfterlifeMirrorDriver.reds'
$observerTarget = Join-Path $root 'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_B0_Afterlife_Mirror\init.lua'
$scriptTarget = Join-Path $root 'r6\scripts\PTFR_B0_Afterlife_Mirror\AfterlifeMirrorDriver.reds'
foreach ($source in @($oldSource, $observerSource, $scriptSource)) {
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing source: $source" }
}
foreach ($target in @($observerTarget, $scriptTarget)) {
    $resolved = [IO.Path]::GetFullPath($target)
    if (-not $resolved.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Target escaped game directory: $resolved"
    }
}
if ((Get-FileHash -LiteralPath $observerTarget -Algorithm SHA256).Hash -ne
    (Get-FileHash -LiteralPath $oldSource -Algorithm SHA256).Hash) {
    throw 'Installed CET helper is not the expected v5 source; refusing replacement.'
}
if (Test-Path -LiteralPath $scriptTarget) {
    throw "Refusing to overwrite existing redscript target: $scriptTarget"
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $scriptTarget) | Out-Null
Copy-Item -LiteralPath $scriptSource -Destination $scriptTarget -ErrorAction Stop
if ((Get-FileHash -LiteralPath $scriptSource -Algorithm SHA256).Hash -ne
    (Get-FileHash -LiteralPath $scriptTarget -Algorithm SHA256).Hash) {
    throw 'Installed redscript hash mismatch.'
}
Copy-Item -LiteralPath $observerSource -Destination $observerTarget -Force -ErrorAction Stop
if ((Get-FileHash -LiteralPath $observerSource -Algorithm SHA256).Hash -ne
    (Get-FileHash -LiteralPath $observerTarget -Algorithm SHA256).Hash) {
    throw 'Installed read-only CET observer hash mismatch.'
}

[pscustomobject]@{
    RedscriptTarget = $scriptTarget
    RedscriptSHA256 = (Get-FileHash -LiteralPath $scriptTarget -Algorithm SHA256).Hash
    ObserverTarget = $observerTarget
    ObserverSHA256 = (Get-FileHash -LiteralPath $observerTarget -Algorithm SHA256).Hash
    NativeArchiveSHA256 = $nativeHash
}
