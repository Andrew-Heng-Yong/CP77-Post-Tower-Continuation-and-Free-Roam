param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count) {
    throw 'Cyberpunk 2077 is running. Exit fully before installing S2.'
}
$root=[IO.Path]::GetFullPath($GameRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
$archiveDir=Join-Path $root 'archive\pc\mod'
$cetDir=Join-Path $root 'bin\x64\plugins\cyber_engine_tweaks\mods'
$scriptDir=Join-Path $root 'r6\scripts'
foreach ($dir in @($archiveDir,$cetDir,$scriptDir)) {
    if (-not (Test-Path -LiteralPath $dir -PathType Container)) { throw "Unexpected game root: $dir" }
}
$manifestPath=Join-Path $WorkspaceRoot 'research\b0_streetkid_seat_mirror_s2\build_manifest.json'
$manifest=Get-Content -LiteralPath $manifestPath -Raw|ConvertFrom-Json
if ($manifest.status -ne 'WORKSPACE_ONLY_UNINSTALLED' -or $manifest.registration_id -ne 51719 -or
    $manifest.resources.Count -ne 3 -or $manifest.vanilla_replacements.Count -ne 0 -or
    $manifest.story_fact_writes.Count -ne 0 -or $manifest.opt_in_fact -ne 'PTFRSKS2_Enabled' -or
    -not $manifest.S1_rollback_preserved) { throw 'S2 manifest scope changed' }
$archive=Join-Path $WorkspaceRoot 'build\Streetkid_Seat_Mirror_S2\TowerContinued_Streetkid_Seat_Mirror_S2.archive'
$xl=$archive+'.xl'
$lua=Join-Path $WorkspaceRoot 'diagnostics\PTFR_Streetkid_Seat_Mirror_S2\init.lua'
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $manifest.sha256 -or
    (Get-FileHash -LiteralPath $xl -Algorithm SHA256).Hash -ne $manifest.xl_sha256) {
    throw 'S2 build differs from reviewed manifest'
}
$s1Receipt=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_streetkid_seat_s1\install_receipt.json') -Raw|ConvertFrom-Json
if ($s1Receipt.status -ne 'INSTALLED_IDLE' -or $s1Receipt.additive_files.Count -ne 3) { throw 'S1 rollback receipt absent' }
for ($i=0;$i -lt 3;$i++) {
    if ((Get-FileHash -LiteralPath $s1Receipt.additive_files[$i] -Algorithm SHA256).Hash -ne $s1Receipt.additive_sha256[$i]) {
        throw 'S1 rollback changed before S2 installation'
    }
}
$pairs=@(
    [pscustomobject]@{Source=$archive;Target=(Join-Path $archiveDir 'TowerContinued_Streetkid_Seat_Mirror_S2.archive')},
    [pscustomobject]@{Source=$xl;Target=(Join-Path $archiveDir 'TowerContinued_Streetkid_Seat_Mirror_S2.archive.xl')},
    [pscustomobject]@{Source=$lua;Target=(Join-Path $cetDir 'PTFR_Streetkid_Seat_Mirror_S2\init.lua')}
)
foreach ($pair in $pairs) {
    if (-not (Test-Path -LiteralPath $pair.Source -PathType Leaf)) { throw "Missing source: $($pair.Source)" }
    if (Test-Path -LiteralPath $pair.Target) { throw "Refusing to overwrite: $($pair.Target)" }
    if (-not [IO.Path]::GetFullPath($pair.Target).StartsWith($root+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {
        throw "Target escaped game root: $($pair.Target)"
    }
}
$protected=[ordered]@{}
foreach ($dir in @($archiveDir,$cetDir,$scriptDir)) {
    foreach ($file in (Get-ChildItem -LiteralPath $dir -File -Recurse -ErrorAction Stop|Where-Object {
        $_.Name -like '*TowerContinued*' -or $_.FullName -match '[\\/]PTFR_'
    })) { $protected[$file.FullName]=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash }
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $pairs[2].Target)|Out-Null
foreach ($pair in $pairs) {
    Copy-Item -LiteralPath $pair.Source -Destination $pair.Target -ErrorAction Stop
    if ((Get-FileHash -LiteralPath $pair.Source -Algorithm SHA256).Hash -ne
        (Get-FileHash -LiteralPath $pair.Target -Algorithm SHA256).Hash) {
        throw "S2 copy/hash mismatch: $($pair.Target)"
    }
}
foreach ($path in $protected.Keys) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $protected[$path]) {
        throw "Previously installed component changed during S2 installation: $path"
    }
}
$receipt=[ordered]@{
    status='INSTALLED_IDLE'; installed_utc=[DateTime]::UtcNow.ToString('o')
    additive_files=@($pairs|ForEach-Object {$_.Target})
    additive_sha256=@($pairs|ForEach-Object {(Get-FileHash -LiteralPath $_.Target -Algorithm SHA256).Hash})
    preserved_files=$protected.Count
    S1_rollback_preserved=$true
    save_or_story_fact_change=$false
    live_scene_tested=$false
}
$receiptPath=Join-Path $WorkspaceRoot 'research\b0_streetkid_seat_mirror_s2\install_receipt.json'
[IO.File]::WriteAllText($receiptPath,($receipt|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
$receipt|ConvertTo-Json -Depth 6
