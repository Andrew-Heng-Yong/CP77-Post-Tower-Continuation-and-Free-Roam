param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
    [switch]$PreflightOnly
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
$game = [IO.Path]::GetFullPath($GameRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count) {
    throw 'Cyberpunk 2077 is running. Exit before installing the paired opt-in.'
}
if (-not (Test-Path -LiteralPath (Join-Path $game 'archive\pc\content') -PathType Container) -or
    -not (Test-Path -LiteralPath (Join-Path $game 'bin\x64\plugins\cyber_engine_tweaks\mods') -PathType Container)) {
    throw "Unexpected game installation: $game"
}
$manifest = Get-Content -LiteralPath (Join-Path $workspace 'research\b0_junk_melee_pair\validation\build_manifest.json') -Raw | ConvertFrom-Json
$expected = @('towercontinued\b0_junk_melee_pair\junk_owner.questphase',
              'towercontinued\b0_junk_melee_pair\melee_owner.questphase')
if ($manifest.status -ne 'STATIC_EXPERIMENTAL_NOT_INSTALLED' -or
    @(Compare-Object @($manifest.resources | Sort-Object) @($expected | Sort-Object)).Count -ne 0 -or
    @($manifest.vanilla_replacements).Count -ne 0 -or
    @(Compare-Object @($manifest.enable_facts | Sort-Object) @('PTFRB0SE5J_Enabled','PTFRB0SE5M_Enabled' | Sort-Object)).Count -ne 0) {
    throw 'Paired build is outside the reviewed two-shop scope'
}
$items = @(
    [pscustomobject]@{Source=(Join-Path $workspace 'build\B0_JunkMeleePair\TowerContinued_B0_JunkMeleePair.archive');Relative='archive\pc\mod\TowerContinued_B0_JunkMeleePair.archive'},
    [pscustomobject]@{Source=(Join-Path $workspace 'archive\b0_junk_melee_pair\TowerContinued_B0_JunkMeleePair.archive.xl');Relative='archive\pc\mod\TowerContinued_B0_JunkMeleePair.archive.xl'},
    [pscustomobject]@{Source=(Join-Path $workspace 'diagnostics\PTFR_B0_JunkMelee_Pair\init.lua');Relative='bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_B0_JunkMelee_Pair\init.lua'}
)
if ((Get-FileHash -LiteralPath $items[0].Source -Algorithm SHA256).Hash -ne $manifest.sha256) {
    throw 'Paired archive differs from the checked build'
}
foreach ($item in $items) {
    if (-not (Test-Path -LiteralPath $item.Source -PathType Leaf)) { throw "Missing source: $($item.Source)" }
    $target = [IO.Path]::GetFullPath((Join-Path $game $item.Relative))
    if (-not $target.StartsWith($game + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Target escaped game directory: $target"
    }
    if (Test-Path -LiteralPath $target) { throw "Refusing to overwrite: $target" }
    $item | Add-Member -NotePropertyName Target -NotePropertyValue $target
    $item | Add-Member -NotePropertyName SourceHash -NotePropertyValue ((Get-FileHash -LiteralPath $item.Source -Algorithm SHA256).Hash)
}
if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count) { throw 'Game started during preflight' }
if ($PreflightOnly) {
    [pscustomobject]@{status='PREFLIGHT_OK';newFiles=$items.Count;resources=$expected;vanillaReplacements=0}
    return
}
$copied = [System.Collections.Generic.List[string]]::new()
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
        $absolute = [IO.Path]::GetFullPath($target)
        if ($absolute.StartsWith($game + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -and
            (Test-Path -LiteralPath $absolute -PathType Leaf)) {
            Remove-Item -LiteralPath $absolute -ErrorAction Stop
        }
    }
    throw
}
$receipt = [ordered]@{
    status='INSTALLED_OPT_IN_JUNK_AND_MELEE_ONLY'
    installedAtUtc=(Get-Date).ToUniversalTime().ToString('o')
    files=@($items | ForEach-Object {[ordered]@{path=$_.Target;sha256=$_.SourceHash}})
    vanillaReplacements=@();savesModified=$false;storyFactsModified=$false
    testResult='PENDING_PAIRED_DISPOSABLE_IN_GAME_TEST'
}
$receiptPath = Join-Path $workspace 'research\b0_junk_melee_pair\validation\install_receipt.json'
[IO.File]::WriteAllText($receiptPath, ($receipt | ConvertTo-Json -Depth 7), [Text.UTF8Encoding]::new($false))
$receipt | ConvertTo-Json -Depth 7
