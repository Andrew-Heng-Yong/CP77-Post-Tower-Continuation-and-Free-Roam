param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count) {
    throw 'Cyberpunk 2077 is running. Exit fully before replacing C3 with automatic C4.'
}
$workspace = [IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
$root = [IO.Path]::GetFullPath($GameRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
if (-not (Test-Path -LiteralPath (Join-Path $root 'archive\pc\content') -PathType Container)) {
    throw "Unexpected game root: $root"
}
$manifest = Get-Content -LiteralPath (Join-Path $workspace 'research\b0_mirror_rollout\validation_c4\build_manifest.json') -Raw | ConvertFrom-Json
if ($manifest.status -ne 'WORKSPACE_ONLY_UNINSTALLED' -or -not $manifest.automatic -or
    $manifest.sites.Count -ne 25 -or $manifest.resources.Count -ne 75 -or
    $manifest.vanilla_replacements.Count -ne 0 -or $null -ne $manifest.opt_in_fact) {
    throw 'Automatic C4 scope changed'
}
$archive = Join-Path $workspace 'build\OrdinaryMirrors_C4\TowerContinued_OrdinaryMirrors_C4.archive'
$xl = $archive+'.xl'
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $manifest.sha256) {
    throw 'C4 archive differs from reviewed build'
}
$protected = [ordered]@{
    (Join-Path $root 'archive\pc\mod\TowerContinued_Afterlife_NativeScene_A2.archive') = '9025E676069478FFFCD6DCED71850383126BF09C1C0C4842B4A56A2AA9BBBDFC'
    (Join-Path $root 'r6\scripts\PTFR_Afterlife_NativeBootstrap_A4\AfterlifeNativeBootstrapA4.reds') = 'F9A1FBA35C295664D04D2F3B9338CE6E54E21B82AC3AF658A1C8A18A0F39B059'
    (Join-Path $root 'archive\pc\mod\TowerContinued_Coyote_NativeScene_C2.archive') = 'FC6EA666DFAA15F35B1978009975BE94A4E5641CCF20F1DC571678EDA49DD5F1'
}
foreach ($path in $protected.Keys) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $protected[$path]) {
        throw "Working component changed: $path"
    }
}
$c3manifest = Get-Content -LiteralPath (Join-Path $workspace 'research\b0_mirror_rollout\validation_c3\build_manifest.json') -Raw | ConvertFrom-Json
$old = @(
    [pscustomobject]@{Source=(Join-Path $root 'archive\pc\mod\TowerContinued_OrdinaryMirrors_C3.archive');Expected=$c3manifest.sha256;Name='C3.archive'},
    [pscustomobject]@{Source=(Join-Path $root 'archive\pc\mod\TowerContinued_OrdinaryMirrors_C3.archive.xl');Expected=(Get-FileHash -LiteralPath (Join-Path $workspace 'build\OrdinaryMirrors_C3\TowerContinued_OrdinaryMirrors_C3.archive.xl') -Algorithm SHA256).Hash;Name='C3.archive.xl'},
    [pscustomobject]@{Source=(Join-Path $root 'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_OrdinaryMirrors_C3\init.lua');Expected=(Get-FileHash -LiteralPath (Join-Path $workspace 'diagnostics\PTFR_OrdinaryMirrors_C3\init.lua') -Algorithm SHA256).Hash;Name='C3.init.lua'}
)
$backup = [IO.Path]::GetFullPath((Join-Path $workspace 'build\OrdinaryMirrors_C4\c3_installed_backup'))
if (-not $backup.StartsWith($workspace+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or
    (Test-Path -LiteralPath $backup)) { throw 'Backup path is unsafe or already exists' }
foreach ($item in $old) {
    if ((Get-FileHash -LiteralPath $item.Source -Algorithm SHA256).Hash -ne $item.Expected) {
        throw "C3 rollback source differs: $($item.Source)"
    }
}
$new = @(
    [pscustomobject]@{Source=$archive;Target=(Join-Path $root 'archive\pc\mod\TowerContinued_OrdinaryMirrors_C4.archive')},
    [pscustomobject]@{Source=$xl;Target=(Join-Path $root 'archive\pc\mod\TowerContinued_OrdinaryMirrors_C4.archive.xl')}
)
foreach ($item in $new) {
    if (Test-Path -LiteralPath $item.Target) { throw "Refusing to overwrite C4 target: $($item.Target)" }
    if (-not [IO.Path]::GetFullPath($item.Target).StartsWith($root+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {
        throw "C4 target escaped game root: $($item.Target)"
    }
}
New-Item -ItemType Directory -Path $backup -ErrorAction Stop | Out-Null
$moved = [System.Collections.Generic.List[object]]::new()
$copied = [System.Collections.Generic.List[string]]::new()
try {
    foreach ($item in $old) {
        $dest = Join-Path $backup $item.Name
        Move-Item -LiteralPath $item.Source -Destination $dest -ErrorAction Stop
        $moved.Add([pscustomobject]@{Original=$item.Source;Backup=$dest})
    }
    foreach ($item in $new) {
        Copy-Item -LiteralPath $item.Source -Destination $item.Target -ErrorAction Stop
        $copied.Add($item.Target)
        if ((Get-FileHash -LiteralPath $item.Source -Algorithm SHA256).Hash -ne
            (Get-FileHash -LiteralPath $item.Target -Algorithm SHA256).Hash) {
            throw "C4 copy/hash mismatch: $($item.Target)"
        }
    }
} catch {
    foreach ($target in $copied) {
        if (Test-Path -LiteralPath $target -PathType Leaf) { Remove-Item -LiteralPath $target -ErrorAction Stop }
    }
    foreach ($item in $moved) {
        if (Test-Path -LiteralPath $item.Backup -PathType Leaf) {
            Move-Item -LiteralPath $item.Backup -Destination $item.Original -ErrorAction Stop
        }
    }
    throw
}
foreach ($path in $protected.Keys) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $protected[$path]) {
        throw "Working component changed during C4 installation: $path"
    }
}
[pscustomobject]@{AutomaticOrdinaryMirrorSites=25; Archive=$new[0].Target;
    Registration=$new[1].Target; C3Rollback=$backup;
    CETOptInRequired=$false; VanillaResourcesReplaced=$false;
    SavesOrStoryFactsChanged=$false}
