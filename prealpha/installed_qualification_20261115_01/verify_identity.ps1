param([Parameter(Mandatory)][string]$Output)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$manifestPath = Join-Path $workspace 'prealpha/mid_quest_resume_retire_20261115_01/stage_08/deployment_01/installed_manifest_01.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.core_epoch -cne 'RD10_MID_QUEST_RESUME_RETIRED' -or
    $manifest.core_files.Count -ne 51 -or $manifest.required_files.Count -ne 26) {
    throw 'Unexpected installed baseline or inventory'
}
$gameRoot = [IO.Path]::GetFullPath([string]$manifest.game_root)
if ((Get-Item -LiteralPath $gameRoot).Attributes -band [IO.FileAttributes]::ReparsePoint) {
    throw 'Linked game root'
}

function Check-File([string]$relative, [long]$bytes, [string]$expected) {
    if ([IO.Path]::IsPathRooted($relative) -or $relative -match '(^|[\\/])\.\.([\\/]|$)' -or $relative -match ':') {
        throw "Invalid managed path: $relative"
    }
    $parts = $relative -split '[\\/]'
    if ($parts.Count -lt 2 -or $parts -contains '') { throw "Invalid managed path: $relative" }
    $path = $gameRoot
    foreach ($part in $parts) {
        $path = Join-Path $path $part
        $item = Get-Item -LiteralPath $path -ErrorAction Stop
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked managed path: $relative" }
    }
    $file = Get-Item -LiteralPath $path -ErrorAction Stop
    if ($file.PSIsContainer -or ($bytes -gt 0 -and $file.Length -ne $bytes)) { throw "Managed size mismatch: $relative" }
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
    if ($actual -cne $expected) { throw "Managed hash mismatch: $relative" }
    return @{ path = $relative.Replace('\\','/'); bytes = $file.Length; sha256 = $actual }
}

$seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$rows = [Collections.Generic.List[object]]::new()
foreach ($group in @(@($manifest.core_files), @($manifest.required_files))) {
    foreach ($entry in $group) {
        if (-not $seen.Add([string]$entry.path)) { throw "Duplicate managed path: $($entry.path)" }
        $rows.Add((Check-File ([string]$entry.path) ([long]$entry.bytes) ([string]$entry.sha256)))
    }
}
$atelierPath = 'r6/scripts/virtual-atelier-full/SetupNewTab.reds'
$atelier = @($manifest.required_files | Where-Object path -CEQ $atelierPath)
if ($atelier.Count -ne 1 -or $atelier[0].sha256 -cne '5743CDCD6F8CD46A58F9642002F75EBCA25D84BE340856C2E6D85B15DAD973F8') {
    throw 'Required Atelier correction differs from the reviewed hash'
}

$outPath = [IO.Path]::GetFullPath($Output)
$outParent = [IO.Path]::GetDirectoryName($outPath)
if (-not $outPath.StartsWith(([IO.Path]::GetFullPath($PSScriptRoot) + [IO.Path]::DirectorySeparatorChar), [StringComparison]::OrdinalIgnoreCase) -or
    (Test-Path -LiteralPath $outPath) -or -not (Test-Path -LiteralPath $outParent -PathType Container)) {
    throw 'Output must be a fresh file under this task directory'
}
$result = [ordered]@{
    status = 'PASS_CURRENT_INSTALLED_HASHES'
    checked_at_utc = [DateTime]::UtcNow.ToString('o')
    core_epoch = $manifest.core_epoch
    manifest_sha256 = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash
    core_count = $manifest.core_files.Count
    required_count = $manifest.required_files.Count
    atelier_sha256 = $atelier[0].sha256
    changed_paths = @($manifest.changed_paths)
    rows = @($rows.ToArray())
    save_reads = 0
    save_writes = 0
    game_launches = 0
}
[IO.File]::WriteAllText($outPath, ($result | ConvertTo-Json -Depth 6), [Text.UTF8Encoding]::new($false))
Write-Output "Verified $($result.core_count) Core paths, $($result.required_count) required files and Atelier compatibility file."
