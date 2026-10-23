param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count) {
    throw 'Cyberpunk 2077 is running. Exit fully before installing ordinary mirrors C3.'
}
$root = [IO.Path]::GetFullPath($GameRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
if (-not (Test-Path -LiteralPath (Join-Path $root 'archive\pc\content') -PathType Container) -or
    -not (Test-Path -LiteralPath (Join-Path $root 'bin\x64\plugins\cyber_engine_tweaks\mods') -PathType Container)) {
    throw "Unexpected game/CET root: $root"
}
$protected = [ordered]@{
    (Join-Path $root 'archive\pc\mod\TowerContinued_Coyote_NativeScene_C2.archive') = 'FC6EA666DFAA15F35B1978009975BE94A4E5641CCF20F1DC571678EDA49DD5F1'
    (Join-Path $root 'archive\pc\mod\TowerContinued_Afterlife_NativeScene_A2.archive') = '9025E676069478FFFCD6DCED71850383126BF09C1C0C4842B4A56A2AA9BBBDFC'
    (Join-Path $root 'r6\scripts\PTFR_Afterlife_NativeBootstrap_A4\AfterlifeNativeBootstrapA4.reds') = 'F9A1FBA35C295664D04D2F3B9338CE6E54E21B82AC3AF658A1C8A18A0F39B059'
    (Join-Path $root 'archive\pc\mod\TowerContinued_B0_Afterlife_Mirror.archive') = '2643F18D8946FB9C96FB479FD91418D3446E4792CE21562A11CBEC371D534003'
}
foreach ($path in $protected.Keys) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $protected[$path]) {
        throw "Previously installed mirror component changed: $path"
    }
}
$manifest = Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_mirror_rollout\validation_c3\build_manifest.json') -Raw | ConvertFrom-Json
if ($manifest.status -ne 'WORKSPACE_ONLY_UNINSTALLED' -or $manifest.sites.Count -ne 25 -or
    $manifest.resources.Count -ne 75 -or $manifest.vanilla_replacements.Count -ne 0 -or
    $manifest.opt_in_fact -ne 'PTFRBM_Enabled') { throw 'C3 package scope changed' }
$archive = Join-Path $WorkspaceRoot 'build\OrdinaryMirrors_C3\TowerContinued_OrdinaryMirrors_C3.archive'
$xl = $archive+'.xl'
$logger = Join-Path $WorkspaceRoot 'diagnostics\PTFR_OrdinaryMirrors_C3\init.lua'
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $manifest.sha256) {
    throw 'C3 archive differs from reviewed build'
}
$pairs = @(
    [pscustomobject]@{Source=$archive;Target=(Join-Path $root 'archive\pc\mod\TowerContinued_OrdinaryMirrors_C3.archive')},
    [pscustomobject]@{Source=$xl;Target=(Join-Path $root 'archive\pc\mod\TowerContinued_OrdinaryMirrors_C3.archive.xl')},
    [pscustomobject]@{Source=$logger;Target=(Join-Path $root 'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_OrdinaryMirrors_C3\init.lua')}
)
foreach ($pair in $pairs) {
    if (-not (Test-Path -LiteralPath $pair.Source -PathType Leaf)) { throw "Missing C3 source: $($pair.Source)" }
    if (Test-Path -LiteralPath $pair.Target) { throw "Refusing to overwrite existing C3 target: $($pair.Target)" }
    if (-not [IO.Path]::GetFullPath($pair.Target).StartsWith($root+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {
        throw "C3 target escaped game root: $($pair.Target)"
    }
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $pairs[2].Target) | Out-Null
foreach ($pair in $pairs) {
    Copy-Item -LiteralPath $pair.Source -Destination $pair.Target -ErrorAction Stop
    if ((Get-FileHash -LiteralPath $pair.Source -Algorithm SHA256).Hash -ne
        (Get-FileHash -LiteralPath $pair.Target -Algorithm SHA256).Hash) { throw "C3 copy/hash mismatch: $($pair.Target)" }
}
foreach ($path in $protected.Keys) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $protected[$path]) {
        throw "Previously installed component changed during C3 installation: $path"
    }
}
[pscustomobject]@{OrdinaryMirrorSites=25; OptInFact='PTFRBM_Enabled';
    Archive=$pairs[0].Target; Registration=$pairs[1].Target; Logger=$pairs[2].Target;
    StreetkidIncluded=$false; AfterlifeAndCoyoteUnchanged=$true;
    SavesOrStoryFactsChanged=$false}
