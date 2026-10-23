param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count) {
    throw 'Cyberpunk 2077 is running. Exit fully before installation.'
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
}
foreach ($path in $protected.Keys) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $protected[$path]) {
        throw "Working Afterlife component changed: $path"
    }
}
$manifestPath = Join-Path $WorkspaceRoot 'research\b0_second_mirror\validation_c1\build_manifest.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.status -ne 'WORKSPACE_ONLY_UNINSTALLED' -or $manifest.scene_owners -ne 0 -or
    $manifest.vanilla_replacements.Count -ne 0 -or $manifest.resources.Count -ne 2 -or
    $manifest.registration_id -ne 17990) { throw 'C1 scope or registration changed' }
$archive = Join-Path $WorkspaceRoot 'build\Coyote_TriggerAudit_C1\TowerContinued_Coyote_TriggerAudit.archive'
$xl = $archive + '.xl'
$lua = Join-Path $WorkspaceRoot 'diagnostics\PTFR_Coyote_TriggerAudit\init.lua'
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $manifest.sha256) {
    throw 'C1 archive differs from the validated build'
}
$pairs = @(
    [pscustomobject]@{Source=$archive;Target=(Join-Path $root 'archive\pc\mod\TowerContinued_Coyote_TriggerAudit.archive')},
    [pscustomobject]@{Source=$xl;Target=(Join-Path $root 'archive\pc\mod\TowerContinued_Coyote_TriggerAudit.archive.xl')},
    [pscustomobject]@{Source=$lua;Target=(Join-Path $root 'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_Coyote_TriggerAudit\init.lua')}
)
foreach ($pair in $pairs) {
    if (-not (Test-Path -LiteralPath $pair.Source -PathType Leaf)) { throw "Missing C1 source: $($pair.Source)" }
    if (Test-Path -LiteralPath $pair.Target) { throw "Refusing to overwrite existing C1 target: $($pair.Target)" }
    if (-not [IO.Path]::GetFullPath($pair.Target).StartsWith($root+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {
        throw "Target escaped game root: $($pair.Target)"
    }
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $pairs[2].Target) | Out-Null
foreach ($pair in $pairs) {
    Copy-Item -LiteralPath $pair.Source -Destination $pair.Target -ErrorAction Stop
    if ((Get-FileHash -LiteralPath $pair.Source -Algorithm SHA256).Hash -ne
        (Get-FileHash -LiteralPath $pair.Target -Algorithm SHA256).Hash) { throw "C1 copy/hash mismatch: $($pair.Target)" }
}
foreach ($path in $protected.Keys) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $protected[$path]) {
        throw "Working Afterlife component changed during installation: $path"
    }
}
[pscustomobject]@{
    AuditArchive=$pairs[0].Target
    AuditXL=$pairs[1].Target
    AuditLogger=$pairs[2].Target
    AddedSceneOwners=0
    AfterlifeImplementation='unchanged'
    SavesOrStoryFactsChanged=$false
}
