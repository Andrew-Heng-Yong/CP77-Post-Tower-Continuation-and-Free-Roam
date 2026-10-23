param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count) {
    throw 'Cyberpunk 2077 is running. Fully exit before installing Wilson opt-in.'
}
$workspace = [IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
$game = [IO.Path]::GetFullPath($GameRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
if (-not (Test-Path -LiteralPath (Join-Path $game 'archive\pc\content') -PathType Container) -or
    -not (Test-Path -LiteralPath (Join-Path $game 'bin\x64\plugins\cyber_engine_tweaks\mods') -PathType Container)) {
    throw "Unexpected game installation: $game"
}
$manifestPath=Join-Path $workspace 'research\b0_wilson_vendor\validation\build_manifest.json'
$manifest=Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$expectedResources=@(
    'towercontinued\b0_wilson_vendor\body.questphase',
    'towercontinued\b0_wilson_vendor\owner.questphase',
    'towercontinued\b0_wilson_vendor\shop.scene'
)
if ($manifest.status -ne 'OPT_IN_DISPOSABLE_BUILD_NOT_INSTALLED' -or
    @(Compare-Object $expectedResources @($manifest.resources)).Count -or
    @($manifest.vanilla_replacements).Count -ne 0 -or
    @($manifest.scene_nodes).Count -ne 5 -or
    $manifest.enabled_fact -ne 'PTFRB0WV_Enabled' -or
    $manifest.near_fact -ne 'PTFRB0WV_Near') {
    throw 'Wilson build is outside reviewed one-shop scope'
}
$archiveSource=Join-Path $workspace 'build\B0_Wilson_Vendor\TowerContinued_B0_Wilson_Vendor.archive'
$registrationSource=Join-Path $workspace 'archive\b0_wilson_vendor\TowerContinued_B0_Wilson_Vendor.archive.xl'
$luaSource=Join-Path $workspace 'diagnostics\PTFR_B0_Wilson_Vendor\init.lua'
$items=@(
    [pscustomobject]@{Source=$archiveSource;Relative='archive\pc\mod\TowerContinued_B0_Wilson_Vendor.archive'},
    [pscustomobject]@{Source=$registrationSource;Relative='archive\pc\mod\TowerContinued_B0_Wilson_Vendor.archive.xl'},
    [pscustomobject]@{Source=$luaSource;Relative='bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_B0_Wilson_Vendor\init.lua'}
)
if ((Get-FileHash -LiteralPath $archiveSource -Algorithm SHA256).Hash -ne $manifest.sha256) {
    throw 'Wilson archive differs from validated build'
}
foreach ($item in $items) {
    $item | Add-Member -NotePropertyName Target -NotePropertyValue ([IO.Path]::GetFullPath((Join-Path $game $item.Relative)))
    if (-not $item.Target.StartsWith($game+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {
        throw "Target escaped game directory: $($item.Target)"
    }
    if (-not (Test-Path -LiteralPath $item.Source -PathType Leaf)) { throw "Missing source: $($item.Source)" }
    if (Test-Path -LiteralPath $item.Target) { throw "Refusing to overwrite: $($item.Target)" }
    $item | Add-Member -NotePropertyName SourceHash -NotePropertyValue ((Get-FileHash -LiteralPath $item.Source -Algorithm SHA256).Hash)
}
if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count) {
    throw 'Cyberpunk 2077 started during Wilson preflight'
}
$copied=[System.Collections.Generic.List[string]]::new()
try {
    foreach ($item in $items) {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $item.Target) | Out-Null
        Copy-Item -LiteralPath $item.Source -Destination $item.Target -ErrorAction Stop
        $copied.Add($item.Target)
        if ((Get-FileHash -LiteralPath $item.Target -Algorithm SHA256).Hash -ne $item.SourceHash) {
            throw "Installed hash mismatch: $($item.Target)"
        }
    }
} catch {
    foreach ($target in $copied) {
        $absolute=[IO.Path]::GetFullPath($target)
        if ($absolute.StartsWith($game+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -and
            (Test-Path -LiteralPath $absolute -PathType Leaf)) {
            Remove-Item -LiteralPath $absolute -ErrorAction Stop
        }
    }
    throw
}
$receipt=[ordered]@{
    status='INSTALLED_OPT_IN_WILSON_ONLY'; installedAtUtc=(Get-Date).ToUniversalTime().ToString('o')
    files=@($items|ForEach-Object {[ordered]@{path=$_.Target;sha256=$_.SourceHash}})
    vanillaReplacements=@(); savesModified=$false; storyFactsModified=$false
    testResult='PENDING_DISPOSABLE_IN_GAME_TEST'
}
$receiptPath=Join-Path $workspace 'research\b0_wilson_vendor\validation\install_receipt.json'
[IO.File]::WriteAllText($receiptPath,($receipt|ConvertTo-Json -Depth 7),[Text.UTF8Encoding]::new($false))
$receipt|ConvertTo-Json -Depth 7
