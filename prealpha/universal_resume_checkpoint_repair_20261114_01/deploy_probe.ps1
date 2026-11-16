param(
    [ValidateSet('Preflight','Install','Verify','Rollback')][string]$Action = 'Preflight',
    [string]$FixtureRoot = ''
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$source = Join-Path $PSScriptRoot 'probe_build_02/PTFR_CheckpointRTTIProbe.dll'
$expected = '1ED02F838004645C46F1E69733D80D1779416A6766BD6E8E2EB5E1F9CA9C51C4'
$relative = 'red4ext/plugins/PTFR_CheckpointRTTIProbe/PTFR_CheckpointRTTIProbe.dll'
$realGame = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$realSave = 'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077'
$fixture = ![string]::IsNullOrWhiteSpace($FixtureRoot)
if ($fixture) {
    $allowed = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'probe_fixtures'))
    $root = [IO.Path]::GetFullPath($FixtureRoot)
    if (!$root.StartsWith($allowed + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Fixture must be beneath the dedicated probe_fixtures root'
    }
    $game = Join-Path $root 'game'
    $save = Join-Path $root 'saves'
    $receipt = Join-Path $root 'receipt.json'
} else {
    $game = $realGame
    $save = $realSave
    $receipt = Join-Path $PSScriptRoot 'probe_deployment_01/receipt.json'
}
$target = Join-Path $game $relative
$target = [IO.Path]::GetFullPath($target)
if (!$target.StartsWith([IO.Path]::GetFullPath($game).TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Probe path escaped game root'
}
function NoLinks([string]$path) {
    $cursor = [IO.Path]::GetFullPath($path)
    while ($cursor) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked path refused: $cursor" }
        }
        $parent = [IO.Path]::GetDirectoryName($cursor)
        if ($parent -eq $cursor) { break }
        $cursor = $parent
    }
}
function Hash([string]$path) { (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash }
function Closed {
    if (!$fixture) {
        $active = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -in @('Cyberpunk2077','REDlauncher') })
        if ($active.Count) { throw 'Game and launcher must be closed naturally' }
    }
}
function SaveSnapshot {
    $rows = @(Get-ChildItem -LiteralPath $save -Recurse -File -Force | ForEach-Object {
        NoLinks $_.FullName
        [pscustomobject]@{ path = [IO.Path]::GetRelativePath($save, $_.FullName); bytes = $_.Length; hash = Hash $_.FullName }
    } | Sort-Object path)
    return ($rows | ConvertTo-Json -Compress -Depth 3)
}
NoLinks $game
NoLinks $save
NoLinks $target
NoLinks $source
if ((Hash $source) -cne $expected -or (Get-Item -LiteralPath $source).Length -ne 293888) { throw 'Probe build drift' }
Closed
if (!$fixture) {
    & pwsh -NoProfile -File (Join-Path (Split-Path $PSScriptRoot -Parent) 'universal_resume_checkpoint_deploy_20261114_01/deploy_core.ps1') -Action Verify -ExpectedState Before | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'RD10 predecessor verification failed' }
}
$before = SaveSnapshot
switch ($Action) {
    'Preflight' {
        if (Test-Path -LiteralPath $target) { throw 'Probe target occupied' }
        if (Test-Path -LiteralPath $receipt) { throw 'Probe receipt occupied' }
        @{ status='PREFLIGHT_READY'; target=$target; source_sha256=$expected } | ConvertTo-Json -Compress
    }
    'Install' {
        if (Test-Path -LiteralPath $target) { throw 'Probe target occupied' }
        if (Test-Path -LiteralPath $receipt) { throw 'Probe receipt occupied' }
        $dir = Split-Path $target -Parent
        [void][IO.Directory]::CreateDirectory($dir)
        NoLinks $dir
        $stage = Join-Path $dir 'PTFR_CheckpointRTTIProbe.dll.stage'
        if (Test-Path -LiteralPath $stage) { throw 'Probe stage occupied' }
        [IO.File]::Copy($source, $stage, $false)
        if ((Hash $stage) -cne $expected) { throw 'Probe stage hash drift' }
        [IO.File]::Move($stage, $target)
        if ((Hash $target) -cne $expected -or (SaveSnapshot) -cne $before) { throw 'Probe install verification failed; preserve target for review' }
        $receiptDir = Split-Path $receipt -Parent
        [void][IO.Directory]::CreateDirectory($receiptDir)
        @{ status='INSTALLED_VERIFIED'; path=$target; sha256=$expected; source=$source; save_writes=0; game_launches=0 } |
            ConvertTo-Json | Set-Content -LiteralPath $receipt -Encoding utf8NoBOM
        @{ status='INSTALLED_VERIFIED'; target=$target; save_writes=0; game_launches=0 } | ConvertTo-Json -Compress
    }
    'Verify' {
        if (!(Test-Path -LiteralPath $receipt) -or (Hash $target) -cne $expected) { throw 'Probe receipt/target mismatch' }
        if ((SaveSnapshot) -cne $before) { throw 'Save changed during verification' }
        @{ status='VERIFIED'; target=$target; save_writes=0 } | ConvertTo-Json -Compress
    }
    'Rollback' {
        if (!(Test-Path -LiteralPath $receipt) -or (Hash $target) -cne $expected) { throw 'Probe receipt/target mismatch' }
        Remove-Item -LiteralPath $target -Force
        if (Test-Path -LiteralPath $target) { throw 'Probe target remains after rollback' }
        if ((SaveSnapshot) -cne $before) { throw 'Save changed during rollback' }
        @{ status='ROLLED_BACK_VERIFIED'; target=$target; save_writes=0 } | ConvertTo-Json -Compress
    }
}
