param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
$game = [IO.Path]::GetFullPath($GameRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count) {
    throw 'Cyberpunk 2077 is running. Exit before installing the clothing-vendor opt-in.'
}
if (-not (Test-Path -LiteralPath (Join-Path $game 'archive\pc\content') -PathType Container) -or
    -not (Test-Path -LiteralPath (Join-Path $game 'bin\x64\plugins\cyber_engine_tweaks\mods') -PathType Container)) {
    throw "Unexpected game installation: $game"
}
$manifest = Get-Content -LiteralPath (Join-Path $workspace 'research\b0_lch_clothing_vendor\validation\build_manifest.json') -Raw | ConvertFrom-Json
if ($manifest.status -ne 'STATIC_EXPERIMENTAL_NOT_INSTALLED' -or
    @($manifest.resources).Count -ne 1 -or
    $manifest.resources[0] -ne 'towercontinued\b0_lch_clothing_vendor\vendor_owner.questphase' -or
    @($manifest.vanilla_replacements).Count -ne 0 -or
    $manifest.enable_fact -ne 'PTFRB0LCHV_Enabled') {
    throw 'Clothing-vendor build is outside the reviewed one-shop scope'
}
$items = @(
    [pscustomobject]@{Source=(Join-Path $workspace 'build\B0_LCH_Clothing_Vendor\TowerContinued_B0_LCH_Clothing_Vendor.archive');Relative='archive\pc\mod\TowerContinued_B0_LCH_Clothing_Vendor.archive'},
    [pscustomobject]@{Source=(Join-Path $workspace 'archive\b0_lch_clothing_vendor\TowerContinued_B0_LCH_Clothing_Vendor.archive.xl');Relative='archive\pc\mod\TowerContinued_B0_LCH_Clothing_Vendor.archive.xl'},
    [pscustomobject]@{Source=(Join-Path $workspace 'diagnostics\PTFR_B0_LCH_Clothing_Vendor\init.lua');Relative='bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_B0_LCH_Clothing_Vendor\init.lua'}
)
if ((Get-FileHash -LiteralPath $items[0].Source -Algorithm SHA256).Hash -ne $manifest.sha256) {
    throw 'Clothing-vendor archive differs from its checked build'
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
    status='INSTALLED_OPT_IN_LCH_CLOTHING_ONLY'
    installedAtUtc=(Get-Date).ToUniversalTime().ToString('o')
    files=@($items | ForEach-Object {[ordered]@{path=$_.Target;sha256=$_.SourceHash}})
    vanillaReplacements=@()
    savesModified=$false
    storyFactsModified=$false
    testResult='PENDING_DISPOSABLE_IN_GAME_TEST'
}
$receiptPath = Join-Path $workspace 'research\b0_lch_clothing_vendor\validation\install_receipt.json'
[IO.File]::WriteAllText($receiptPath, ($receipt | ConvertTo-Json -Depth 7), [Text.UTF8Encoding]::new($false))
$receipt | ConvertTo-Json -Depth 7
