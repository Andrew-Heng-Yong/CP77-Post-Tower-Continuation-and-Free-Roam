param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count -ne 0) {
    throw 'Cyberpunk2077 is running; close it before restoring the validated driver.'
}
$root = [IO.Path]::GetFullPath($GameRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
if (-not (Test-Path -LiteralPath (Join-Path $root 'archive\pc\content') -PathType Container)) {
    throw "Not a Cyberpunk 2077 installation: $root"
}
$source = Join-Path $WorkspaceRoot 'redscript\PTFR_B0_Afterlife_Mirror\AfterlifeMirrorDriver.reds'
$target = Join-Path $root 'r6\scripts\PTFR_B0_Afterlife_Mirror\AfterlifeMirrorDriver.reds'
$observer = Join-Path $root 'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_B0_Afterlife_Mirror\init.lua'
$archive = Join-Path $root 'archive\pc\mod\TowerContinued_B0_Afterlife_Mirror.archive'
if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne
    '0F8F2ADB277DC0D59F70951D7A84DF41DDA9D0B44CEDE0F212B5CBA046BB3BB2') {
    throw 'Workspace source is not the validated v6 driver.'
}
if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne
    'A186EDF4F6B5A20FB27A7EA9D61DA9F80968CAC81F8FC0CC59715D2DFB492636') {
    throw 'Installed target is not the untested bootstrap revision.'
}
if ((Get-FileHash -LiteralPath $observer -Algorithm SHA256).Hash -ne
    '3E9C8C5A0EFA1CF5F336A1B20EA5634E1759288C3BE3320359802A65517BA35F') {
    throw 'Read-only observer changed unexpectedly.'
}
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne
    '2643F18D8946FB9C96FB479FD91418D3446E4792CE21562A11CBEC371D534003') {
    throw 'Native Afterlife archive changed unexpectedly.'
}
Copy-Item -LiteralPath $source -Destination $target -Force -ErrorAction Stop
$hash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
if ($hash -ne '0F8F2ADB277DC0D59F70951D7A84DF41DDA9D0B44CEDE0F212B5CBA046BB3BB2') {
    throw 'Restored redscript hash mismatch.'
}
[pscustomobject]@{ Target=$target; SHA256=$hash; Observer='unchanged'; NativeArchive='unchanged' }
