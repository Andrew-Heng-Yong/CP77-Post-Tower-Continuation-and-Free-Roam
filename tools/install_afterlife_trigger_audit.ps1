param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count) {
    throw 'Cyberpunk 2077 is running. Exit fully before installing this audit.'
}
$root = [IO.Path]::GetFullPath($GameRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
if (-not (Test-Path -LiteralPath (Join-Path $root 'archive\pc\content') -PathType Container) -or
    -not (Test-Path -LiteralPath (Join-Path $root 'bin\x64\plugins\cyber_engine_tweaks\mods') -PathType Container)) {
    throw "The selected directory is not the expected Cyberpunk/CET installation: $root"
}
$v5 = Join-Path $root 'archive\pc\mod\TowerContinued_B0_Afterlife_Mirror.archive'
$v6 = Join-Path $root 'r6\scripts\PTFR_B0_Afterlife_Mirror\AfterlifeMirrorDriver.reds'
$observer = Join-Path $root 'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_B0_Afterlife_Mirror\init.lua'
$rollback = [ordered]@{
    $v5 = '2643F18D8946FB9C96FB479FD91418D3446E4792CE21562A11CBEC371D534003'
    $v6 = '0F8F2ADB277DC0D59F70951D7A84DF41DDA9D0B44CEDE0F212B5CBA046BB3BB2'
    $observer = '3E9C8C5A0EFA1CF5F336A1B20EA5634E1759288C3BE3320359802A65517BA35F'
}
foreach ($path in $rollback.Keys) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $rollback[$path]) {
        throw "Existing working setup differs from its validated hash: $path"
    }
}
$sourceArchive = Join-Path $WorkspaceRoot 'build\Afterlife_TriggerAudit_A1\TowerContinued_Afterlife_TriggerAudit.archive'
$sourceXl = $sourceArchive + '.xl'
$sourceLua = Join-Path $WorkspaceRoot 'diagnostics\PTFR_Afterlife_TriggerAudit\init.lua'
$targetArchive = Join-Path $root 'archive\pc\mod\TowerContinued_Afterlife_TriggerAudit.archive'
$targetXl = $targetArchive + '.xl'
$targetLua = Join-Path $root 'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_Afterlife_TriggerAudit\init.lua'
$pairs = @(
    [pscustomobject]@{Source=$sourceArchive;Target=$targetArchive},
    [pscustomobject]@{Source=$sourceXl;Target=$targetXl},
    [pscustomobject]@{Source=$sourceLua;Target=$targetLua}
)
if ((Get-FileHash -LiteralPath $sourceArchive -Algorithm SHA256).Hash -ne
    '153CF46BD757A42C4B1C911999DC4B3721B7033F0C6C3ED3F927CF445649E4A4') {
    throw 'Audit archive differs from its validated offline build.'
}
$manifest = Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_afterlife_native_audit\validation_a1\build_manifest.json') -Raw | ConvertFrom-Json
if ($manifest.resources.Count -ne 2 -or $manifest.scene_owners -ne 0 -or $manifest.vanilla_replacements.Count -ne 0) {
    throw 'Audit manifest is broader than the reviewed two-resource, zero-scene scope.'
}
foreach ($pair in $pairs) {
    if (-not (Test-Path -LiteralPath $pair.Source -PathType Leaf)) { throw "Missing audit source: $($pair.Source)" }
    if (Test-Path -LiteralPath $pair.Target) { throw "Audit target already exists; refusing overwrite: $($pair.Target)" }
    $absolute = [IO.Path]::GetFullPath($pair.Target)
    if (-not $absolute.StartsWith($root + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {
        throw "Audit target escaped the game directory: $absolute"
    }
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $targetLua) | Out-Null
foreach ($pair in $pairs) {
    Copy-Item -LiteralPath $pair.Source -Destination $pair.Target -ErrorAction Stop
    if ((Get-FileHash -LiteralPath $pair.Source -Algorithm SHA256).Hash -ne
        (Get-FileHash -LiteralPath $pair.Target -Algorithm SHA256).Hash) {
        throw "Audit file copy/hash mismatch: $($pair.Target)"
    }
}
foreach ($path in $rollback.Keys) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $rollback[$path]) {
        throw "The existing working setup changed during audit installation: $path"
    }
}
[pscustomobject]@{
    AuditArchive=$targetArchive
    AuditArchiveSha256=(Get-FileHash -LiteralPath $targetArchive -Algorithm SHA256).Hash
    AuditXL=$targetXl
    AuditLogger=$targetLua
    AuditLoggerSha256=(Get-FileHash -LiteralPath $targetLua -Algorithm SHA256).Hash
    ExistingAfterlifeSetup='v5 archive + v6 redscript + read-only observer unchanged'
    SceneOwnersAdded=0
    SavesOrStoryFactsChanged=$false
}
