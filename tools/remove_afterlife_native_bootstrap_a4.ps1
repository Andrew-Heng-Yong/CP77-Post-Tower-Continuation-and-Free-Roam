param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count) {
    throw 'Exit Cyberpunk 2077 before removing A4.'
}
$root = [IO.Path]::GetFullPath($GameRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
$source = Join-Path $WorkspaceRoot 'redscript\PTFR_Afterlife_NativeBootstrap_A4\AfterlifeNativeBootstrapA4.reds'
$target = Join-Path $root 'r6\scripts\PTFR_Afterlife_NativeBootstrap_A4\AfterlifeNativeBootstrapA4.reds'
$absolute = [IO.Path]::GetFullPath($target)
if (-not $absolute.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw "A4 target escaped game root: $absolute"
}
if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { throw 'A4 is not installed.' }
if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne
    (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash) {
    throw 'Installed A4 differs from reviewed source; refusing removal.'
}
Remove-Item -LiteralPath $target -Force -ErrorAction Stop
[pscustomobject]@{
    Removed = $target
    RecoverableFrom = $source
    OtherGameFilesChanged = $false
    SavesChanged = $false
}
