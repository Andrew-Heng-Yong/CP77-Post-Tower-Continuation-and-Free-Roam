param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$game = (Get-Item -LiteralPath $GameRoot -ErrorAction Stop).FullName
if (-not (Test-Path -LiteralPath (Join-Path $game 'Cyberpunk2077.exe')) -and
    -not (Test-Path -LiteralPath (Join-Path $game 'bin\x64\Cyberpunk2077.exe'))) {
    throw "Game root does not contain Cyberpunk2077.exe: $game"
}
if (Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue) { throw 'Close Cyberpunk 2077 before installation' }

$archiveSource = Join-Path $WorkspaceRoot 'build\B0_H10_AllInteractions\TowerContinued_B0_H10_Interactions.archive'
$xlSource = Join-Path $WorkspaceRoot 'archive\b0_h10_all_interactions\TowerContinued_B0_H10_Interactions.archive.xl'
$luaSource = Join-Path $WorkspaceRoot 'diagnostics\PTFR_B0_H10_Interactions\init.lua'
$archiveTarget = Join-Path $game 'archive\pc\mod\TowerContinued_B0_H10_Interactions.archive'
$xlTarget = Join-Path $game 'archive\pc\mod\TowerContinued_B0_H10_Interactions.archive.xl'
$cetDir = Join-Path $game 'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_B0_H10_Interactions'
$luaTarget = Join-Path $cetDir 'init.lua'
$pairs = @(
    [pscustomobject]@{Source=$archiveSource;Target=$archiveTarget},
    [pscustomobject]@{Source=$xlSource;Target=$xlTarget},
    [pscustomobject]@{Source=$luaSource;Target=$luaTarget}
)
foreach ($pair in $pairs) {
    if (-not (Test-Path -LiteralPath $pair.Source -PathType Leaf)) { throw "Missing source: $($pair.Source)" }
    if (Test-Path -LiteralPath $pair.Target) { throw "Refusing to overwrite existing target: $($pair.Target)" }
}
if (Test-Path -LiteralPath $cetDir) { throw "Refusing to reuse existing CET mod directory: $cetDir" }
if (-not (Test-Path -LiteralPath (Split-Path -Parent $archiveTarget) -PathType Container)) { throw 'Game archive mod directory missing' }
if (-not (Test-Path -LiteralPath (Split-Path -Parent $cetDir) -PathType Container)) { throw 'CET mods directory missing' }

New-Item -ItemType Directory -Path $cetDir -ErrorAction Stop | Out-Null
foreach ($pair in $pairs) {
    if (Test-Path -LiteralPath $pair.Target) { throw "Target appeared during install: $($pair.Target)" }
    Copy-Item -LiteralPath $pair.Source -Destination $pair.Target -ErrorAction Stop
    $sourceHash = (Get-FileHash -LiteralPath $pair.Source -Algorithm SHA256).Hash
    $targetHash = (Get-FileHash -LiteralPath $pair.Target -Algorithm SHA256).Hash
    if ($sourceHash -ne $targetHash) { throw "Installed hash mismatch: $($pair.Target)" }
    [pscustomobject]@{Target=$pair.Target;SHA256=$targetHash}
}
