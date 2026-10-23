param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count) {
    throw 'Cyberpunk 2077 is running. Exit fully before installing C2.'
}
$root = [IO.Path]::GetFullPath($GameRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
if (-not (Test-Path -LiteralPath (Join-Path $root 'archive\pc\content') -PathType Container) -or
    -not (Test-Path -LiteralPath (Join-Path $root 'bin\x64\plugins\cyber_engine_tweaks\mods') -PathType Container)) {
    throw "Unexpected game/CET root: $root"
}
$protected = [ordered]@{
    (Join-Path $root 'archive\pc\mod\TowerContinued_Afterlife_NativeScene_A2.archive') = '9025E676069478FFFCD6DCED71850383126BF09C1C0C4842B4A56A2AA9BBBDFC'
    (Join-Path $root 'r6\scripts\PTFR_Afterlife_NativeBootstrap_A4\AfterlifeNativeBootstrapA4.reds') = 'F9A1FBA35C295664D04D2F3B9338CE6E54E21B82AC3AF658A1C8A18A0F39B059'
    (Join-Path $root 'archive\pc\mod\TowerContinued_B0_Afterlife_Mirror.archive') = '2643F18D8946FB9C96FB479FD91418D3446E4792CE21562A11CBEC371D534003'
    (Join-Path $root 'r6\scripts\PTFR_B0_Afterlife_Mirror\AfterlifeMirrorDriver.reds') = '0F8F2ADB277DC0D59F70951D7A84DF41DDA9D0B44CEDE0F212B5CBA046BB3BB2'
    (Join-Path $root 'archive\pc\mod\TowerContinued_Coyote_TriggerAudit.archive') = 'B4A8596888F0177037F3E0BAD37D3334673AE57FE99814DCE88A79B191264079'
}
foreach ($path in $protected.Keys) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $protected[$path]) {
        throw "Previously installed component changed: $path"
    }
}
$manifest = Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_second_mirror\validation_c2\build_manifest.json') -Raw | ConvertFrom-Json
if ($manifest.status -ne 'WORKSPACE_ONLY_UNINSTALLED' -or $manifest.registration_id -ne 13823 -or
    $manifest.resources.Count -ne 3 -or $manifest.prefab -ne '#mirror_scene_el_cojote' -or
    $manifest.vanilla_replacements.Count -ne 0) { throw 'C2 package scope changed' }
$archive = Join-Path $WorkspaceRoot 'build\Coyote_NativeScene_C2\TowerContinued_Coyote_NativeScene_C2.archive'
$xl = $archive + '.xl'
$logger = Join-Path $WorkspaceRoot 'diagnostics\PTFR_Coyote_TwoMirrorProbe\init.lua'
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $manifest.sha256) {
    throw 'C2 archive differs from reviewed build'
}
$pairs = @(
    [pscustomobject]@{Source=$archive;Target=(Join-Path $root 'archive\pc\mod\TowerContinued_Coyote_NativeScene_C2.archive')},
    [pscustomobject]@{Source=$xl;Target=(Join-Path $root 'archive\pc\mod\TowerContinued_Coyote_NativeScene_C2.archive.xl')},
    [pscustomobject]@{Source=$logger;Target=(Join-Path $root 'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_Coyote_TwoMirrorProbe\init.lua')}
)
foreach ($pair in $pairs) {
    if (-not (Test-Path -LiteralPath $pair.Source -PathType Leaf)) { throw "Missing C2 source: $($pair.Source)" }
    if (Test-Path -LiteralPath $pair.Target) { throw "Refusing to overwrite existing C2 target: $($pair.Target)" }
    if (-not [IO.Path]::GetFullPath($pair.Target).StartsWith($root+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {
        throw "Target escaped game root: $($pair.Target)"
    }
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $pairs[2].Target) | Out-Null
foreach ($pair in $pairs) {
    Copy-Item -LiteralPath $pair.Source -Destination $pair.Target -ErrorAction Stop
    if ((Get-FileHash -LiteralPath $pair.Source -Algorithm SHA256).Hash -ne
        (Get-FileHash -LiteralPath $pair.Target -Algorithm SHA256).Hash) { throw "C2 copy/hash mismatch: $($pair.Target)" }
}
foreach ($path in $protected.Keys) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $protected[$path]) {
        throw "Previously installed component changed during installation: $path"
    }
}
[pscustomobject]@{
    PublicCoyoteMirrorArchive=$pairs[0].Target
    Registration=$pairs[1].Target
    TwoSiteDiagnostic=$pairs[2].Target
    StreetkidMirrorInteractionAdded=$false
    AfterlifeImplementation='unchanged'
    SavesOrStoryFactsChanged=$false
}
