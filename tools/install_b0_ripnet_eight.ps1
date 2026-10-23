param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
    [switch]$PreflightOnly
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count) {
    throw 'Cyberpunk 2077 is running. Exit before installing the opt-in eight-site cohort.'
}
if (-not (Test-Path -LiteralPath (Join-Path $game 'archive\pc\content') -PathType Container) -or
    -not (Test-Path -LiteralPath (Join-Path $game 'bin\x64\plugins\cyber_engine_tweaks\mods') -PathType Container)) {
    throw "Unexpected game installation: $game"
}
$manifest=Get-Content -LiteralPath (Join-Path $workspace 'research\b0_ripnet_eight\validation\build_manifest.json') -Raw | ConvertFrom-Json
$expected=@($manifest.sites | ForEach-Object {'towercontinued\b0_ripnet_eight\'+$_.name+'_owner.questphase'})
if ($manifest.status -ne 'STATIC_EXPERIMENTAL_NOT_INSTALLED' -or
    @($manifest.sites).Count -ne 8 -or
    @(Compare-Object @($manifest.resources | Sort-Object) @($expected | Sort-Object)).Count -ne 0 -or
    @($manifest.vanilla_replacements).Count -ne 0 -or
    @($manifest.enable_facts).Count -ne 8) {
    throw 'Build is outside the reviewed eight-site opt-in scope'
}
$xl=Join-Path $workspace 'archive\b0_ripnet_eight\TowerContinued_B0_RipNetEight.archive.xl'
$xlText=Get-Content -LiteralPath $xl -Raw
if (@([regex]::Matches($xlText,'- path:')).Count -ne 8 -or
    @([regex]::Matches($xlText,'parent: ep1\\quest\\ep1.quest')).Count -ne 8) {
    throw 'Eight-site registry count/parent mismatch'
}
foreach ($depot in $expected) { if (-not $xlText.Contains($depot)) { throw "Missing registry path: $depot" } }
$items=@(
    [pscustomobject]@{Source=(Join-Path $workspace 'build\B0_RipNetEight\TowerContinued_B0_RipNetEight.archive');Relative='archive\pc\mod\TowerContinued_B0_RipNetEight.archive'},
    [pscustomobject]@{Source=$xl;Relative='archive\pc\mod\TowerContinued_B0_RipNetEight.archive.xl'},
    [pscustomobject]@{Source=(Join-Path $workspace 'diagnostics\PTFR_B0_RipNet_Eight\init.lua');Relative='bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_B0_RipNet_Eight\init.lua'}
)
if ((Get-FileHash -LiteralPath $items[0].Source -Algorithm SHA256).Hash -ne $manifest.sha256) {
    throw 'Archive differs from reviewed build'
}
foreach ($item in $items) {
    if (-not (Test-Path -LiteralPath $item.Source -PathType Leaf)) { throw "Missing source: $($item.Source)" }
    $target=[IO.Path]::GetFullPath((Join-Path $game $item.Relative))
    if (-not $target.StartsWith($game + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {
        throw "Target escaped game directory: $target"
    }
    if (Test-Path -LiteralPath $target) { throw "Refusing to overwrite: $target" }
    $item | Add-Member -NotePropertyName Target -NotePropertyValue $target
    $item | Add-Member -NotePropertyName SourceHash -NotePropertyValue ((Get-FileHash -LiteralPath $item.Source -Algorithm SHA256).Hash)
}
if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count) { throw 'Game started during preflight' }
if ($PreflightOnly) {
    [pscustomobject]@{status='PREFLIGHT_OK';newFiles=$items.Count;modOwnedResources=$expected.Count;vanillaReplacements=0}
    return
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
        if ($absolute.StartsWith($game + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -and
            (Test-Path -LiteralPath $absolute -PathType Leaf)) { Remove-Item -LiteralPath $absolute -ErrorAction Stop }
    }
    throw
}
$receipt=[ordered]@{
    status='INSTALLED_IDLE_OPT_IN_RIPNET_EIGHT'
    installedAtUtc=(Get-Date).ToUniversalTime().ToString('o')
    files=@($items | ForEach-Object {[ordered]@{path=$_.Target;sha256=$_.SourceHash}})
    vanillaReplacements=@();savesModified=$false;storyFactsModified=$false
    testResult='PENDING_DISPOSABLE_RIPPERDOC_AND_NETRUNNER_REPRESENTATIVES'
}
$receiptPath=Join-Path $workspace 'research\b0_ripnet_eight\validation\install_receipt.json'
[IO.File]::WriteAllText($receiptPath,($receipt | ConvertTo-Json -Depth 7),[Text.UTF8Encoding]::new($false))
$receipt | ConvertTo-Json -Depth 7
