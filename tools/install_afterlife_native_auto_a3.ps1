param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count) {
    throw 'Cyberpunk 2077 must be fully closed before installing A3.'
}
$root = [IO.Path]::GetFullPath($GameRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
if (-not (Test-Path -LiteralPath (Join-Path $root 'archive\pc\content') -PathType Container) -or
    -not (Test-Path -LiteralPath (Join-Path $root 'bin\x64\plugins\cyber_engine_tweaks\mods') -PathType Container)) {
    throw "Unexpected Cyberpunk installation: $root"
}
$expected = [ordered]@{
    'archive\pc\mod\TowerContinued_B0_Afterlife_Mirror.archive' = '2643F18D8946FB9C96FB479FD91418D3446E4792CE21562A11CBEC371D534003'
    'r6\scripts\PTFR_B0_Afterlife_Mirror\AfterlifeMirrorDriver.reds' = '0F8F2ADB277DC0D59F70951D7A84DF41DDA9D0B44CEDE0F212B5CBA046BB3BB2'
    'archive\pc\mod\TowerContinued_Afterlife_NativeScene_A2.archive' = '9025E676069478FFFCD6DCED71850383126BF09C1C0C4842B4A56A2AA9BBBDFC'
    'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_Afterlife_NativeScene_A2\init.lua' = 'F0830CCACDAE51DEB15F7CA43CF849616A73E70D7C6BF448276C441FDF886AE0'
}
foreach ($relative in $expected.Keys) {
    $path = Join-Path $root $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf) -or
        (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $expected[$relative]) {
        throw "Validated rollback/A2 file missing or changed: $relative"
    }
}
$sourceDir = Join-Path $WorkspaceRoot 'diagnostics\PTFR_Afterlife_Native_Auto_A3'
$targetDir = Join-Path $root 'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_Afterlife_Native_Auto_A3'
$pairs = @(
    [pscustomobject]@{Source=(Join-Path $sourceDir 'init.lua'); Target=(Join-Path $targetDir 'init.lua')},
    [pscustomobject]@{Source=(Join-Path $sourceDir 'afterlife_native_auto_a3_quota.txt'); Target=(Join-Path $targetDir 'afterlife_native_auto_a3_quota.txt')}
)
if (Test-Path -LiteralPath $targetDir) { throw "Refusing to overwrite existing A3 target: $targetDir" }
foreach ($pair in $pairs) {
    if (-not (Test-Path -LiteralPath $pair.Source -PathType Leaf)) { throw "Missing source: $($pair.Source)" }
    $absolute = [IO.Path]::GetFullPath($pair.Target)
    if (-not $absolute.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Target escaped game root: $absolute"
    }
}
if ((Get-Content -LiteralPath $pairs[1].Source -Raw).Trim() -ne '2') {
    throw 'A3 source quota must start at exactly two successful cold-load arms.'
}
New-Item -ItemType Directory -Path $targetDir -ErrorAction Stop | Out-Null
foreach ($pair in $pairs) {
    Copy-Item -LiteralPath $pair.Source -Destination $pair.Target -ErrorAction Stop
    if ((Get-FileHash -LiteralPath $pair.Source -Algorithm SHA256).Hash -ne
        (Get-FileHash -LiteralPath $pair.Target -Algorithm SHA256).Hash) {
        throw "A3 installation hash mismatch: $($pair.Target)"
    }
}
foreach ($relative in $expected.Keys) {
    if ((Get-FileHash -LiteralPath (Join-Path $root $relative) -Algorithm SHA256).Hash -ne $expected[$relative]) {
        throw "Existing tested file changed during A3 installation: $relative"
    }
}
[pscustomobject]@{
    A3Controller = $pairs[0].Target
    A3Sha256 = (Get-FileHash -LiteralPath $pairs[0].Target -Algorithm SHA256).Hash
    Quota = (Get-Content -LiteralPath $pairs[1].Target -Raw).Trim()
    Scope = 'Afterlife only; two cold-load auto-arm attempts; A2 guard is the only fact writer'
    ExistingV5V6A2 = 'installed and hash-unchanged'
    SavesChanged = $false
    StoryFactsChanged = $false
}
