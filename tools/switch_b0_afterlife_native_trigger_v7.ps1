param(
    [switch]$Rollback,
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'Cyberpunk2077 is running; close it before switching the Afterlife mirror candidate.'
}
$root = [IO.Path]::GetFullPath($GameRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
if (-not (Test-Path -LiteralPath (Join-Path $root 'archive\pc\content') -PathType Container)) {
    throw "Not a Cyberpunk 2077 installation: $root"
}
$archiveTarget = Join-Path $root 'archive\pc\mod\TowerContinued_B0_Afterlife_Mirror.archive'
$scriptTarget = Join-Path $root 'r6\scripts\PTFR_B0_Afterlife_Mirror\AfterlifeMirrorDriver.reds'
$observerTarget = Join-Path $root 'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_B0_Afterlife_Mirror\init.lua'
foreach ($target in @($archiveTarget, $scriptTarget, $observerTarget)) {
    $resolved = [IO.Path]::GetFullPath($target)
    if (-not $resolved.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Target escaped game directory: $resolved"
    }
}
if ((Get-FileHash -LiteralPath $observerTarget -Algorithm SHA256).Hash -ne
    '3E9C8C5A0EFA1CF5F336A1B20EA5634E1759288C3BE3320359802A65517BA35F') {
    throw 'Read-only CET observer changed unexpectedly.'
}

$v5Archive = Join-Path $WorkspaceRoot 'build\B0_Afterlife_Mirror_V5\TowerContinued_B0_Afterlife_Mirror.archive'
$v7Archive = Join-Path $WorkspaceRoot 'build\B0_Afterlife_Mirror_V7\TowerContinued_B0_Afterlife_Mirror.archive'
$v6Script = Join-Path $WorkspaceRoot 'redscript\PTFR_B0_Afterlife_Mirror\AfterlifeMirrorDriver.reds'
$trialScript = Join-Path $WorkspaceRoot 'redscript\PTFR_B0_Afterlife_Mirror_NativeTest\AfterlifeMirrorDriver.reds'
$v5Hash = '2643F18D8946FB9C96FB479FD91418D3446E4792CE21562A11CBEC371D534003'
$v7Hash = 'A6D422EC36A3AB77C4E9394E8D09ED7C11C8E5B4B1F1194FB118464F7611562E'
$v6ScriptHash = '0F8F2ADB277DC0D59F70951D7A84DF41DDA9D0B44CEDE0F212B5CBA046BB3BB2'
$trialScriptHash = '08DA5EBEBE06E7799B5DE05DB9B7BB9A98896B1F81E4BC2AA0FD60C7EAAAE17E'

foreach ($pair in @(
    @($v5Archive,$v5Hash), @($v7Archive,$v7Hash),
    @($v6Script,$v6ScriptHash), @($trialScript,$trialScriptHash))) {
    if ((Get-FileHash -LiteralPath $pair[0] -Algorithm SHA256).Hash -ne $pair[1]) {
        throw "Reviewed source changed: $($pair[0])"
    }
}

if ($Rollback) {
    $expectedArchiveHash,$expectedScriptHash = $v7Hash,$trialScriptHash
    $archiveSource,$scriptSource = $v5Archive,$v6Script
    $wantedArchiveHash,$wantedScriptHash = $v5Hash,$v6ScriptHash
} else {
    $expectedArchiveHash,$expectedScriptHash = $v5Hash,$v6ScriptHash
    $archiveSource,$scriptSource = $v7Archive,$trialScript
    $wantedArchiveHash,$wantedScriptHash = $v7Hash,$trialScriptHash
}
if ((Get-FileHash -LiteralPath $archiveTarget -Algorithm SHA256).Hash -ne $expectedArchiveHash -or
    (Get-FileHash -LiteralPath $scriptTarget -Algorithm SHA256).Hash -ne $expectedScriptHash) {
    throw 'Installed files differ from the expected starting candidate; refusing switch.'
}

Copy-Item -LiteralPath $archiveSource -Destination $archiveTarget -Force -ErrorAction Stop
Copy-Item -LiteralPath $scriptSource -Destination $scriptTarget -Force -ErrorAction Stop
if ((Get-FileHash -LiteralPath $archiveTarget -Algorithm SHA256).Hash -ne $wantedArchiveHash -or
    (Get-FileHash -LiteralPath $scriptTarget -Algorithm SHA256).Hash -ne $wantedScriptHash) {
    throw 'Installed candidate hash mismatch; inspect before launching game.'
}
[pscustomobject]@{
    Candidate = $(if ($Rollback) { 'v5 archive + v6 redscript driver restored' } else { 'v7 absolute native trigger + no-op redscript trial' })
    ArchiveSHA256 = $wantedArchiveHash
    ScriptSHA256 = $wantedScriptHash
    Observer = 'unchanged and read-only'
}
