param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count) {
    throw 'Cyberpunk 2077 must be fully closed before installing A4.'
}
$root = [IO.Path]::GetFullPath($GameRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
if (-not (Test-Path -LiteralPath (Join-Path $root 'archive\pc\content') -PathType Container) -or
    -not (Test-Path -LiteralPath (Join-Path $root 'r6\scripts') -PathType Container)) {
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
$quota = Join-Path $root 'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_Afterlife_Native_Auto_A3\afterlife_native_auto_a3_quota.txt'
if ((Get-Content -LiteralPath $quota -Raw).Trim() -ne '0') {
    throw 'A3 must be inert (quota 0) before installing production A4.'
}
$source = Join-Path $WorkspaceRoot 'redscript\PTFR_Afterlife_NativeBootstrap_A4\AfterlifeNativeBootstrapA4.reds'
$target = Join-Path $root 'r6\scripts\PTFR_Afterlife_NativeBootstrap_A4\AfterlifeNativeBootstrapA4.reds'
$absolute = [IO.Path]::GetFullPath($target)
if (-not $absolute.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw "A4 target escaped game root: $absolute"
}
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing A4 source: $source" }
if (Test-Path -LiteralPath $target) { throw "Refusing to overwrite existing A4: $target" }
$text = Get-Content -LiteralPath $source -Raw
$writes = [regex]::Matches($text, 'quests\.SetFact\(n"([^"]+)"\s*,') | ForEach-Object { $_.Groups[1].Value }
if (($writes -join ',') -ne 'PTFRB0ALM_Enabled,PTFRALMA2_Requested,PTFRB0ALM_Enabled') {
    throw 'A4 writer scope differs from the reviewed two mod-owned facts.'
}
New-Item -ItemType Directory -Path (Split-Path -Parent $target) -ErrorAction Stop | Out-Null
Copy-Item -LiteralPath $source -Destination $target -ErrorAction Stop
$sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $sourceHash) {
    throw 'A4 copy/hash mismatch.'
}
foreach ($relative in $expected.Keys) {
    if ((Get-FileHash -LiteralPath (Join-Path $root $relative) -Algorithm SHA256).Hash -ne $expected[$relative]) {
        throw "Existing tested file changed during A4 installation: $relative"
    }
}
[pscustomobject]@{
    A4Source = $source
    A4Installed = $target
    A4Sha256 = $sourceHash
    Scope = 'Afterlife only; redscript startup; existing v5/v6 and A2 unchanged'
    SavesChanged = $false
    StoryFactsChanged = $false
}
