param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count) {
    throw 'Exit Cyberpunk 2077 fully before installing A2.'
}
$root=[IO.Path]::GetFullPath($GameRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
if (-not (Test-Path -LiteralPath (Join-Path $root 'archive\pc\content') -PathType Container) -or
    -not (Test-Path -LiteralPath (Join-Path $root 'bin\x64\plugins\cyber_engine_tweaks\mods') -PathType Container)) {
    throw "Unexpected game installation: $root"
}
$expected=[ordered]@{
    'archive\pc\mod\TowerContinued_B0_Afterlife_Mirror.archive'='2643F18D8946FB9C96FB479FD91418D3446E4792CE21562A11CBEC371D534003'
    'r6\scripts\PTFR_B0_Afterlife_Mirror\AfterlifeMirrorDriver.reds'='0F8F2ADB277DC0D59F70951D7A84DF41DDA9D0B44CEDE0F212B5CBA046BB3BB2'
    'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_B0_Afterlife_Mirror\init.lua'='3E9C8C5A0EFA1CF5F336A1B20EA5634E1759288C3BE3320359802A65517BA35F'
    'archive\pc\mod\TowerContinued_Afterlife_TriggerAudit.archive'='153CF46BD757A42C4B1C911999DC4B3721B7033F0C6C3ED3F927CF445649E4A4'
}
foreach($rel in $expected.Keys) {
    $actual=(Get-FileHash -LiteralPath (Join-Path $root $rel) -Algorithm SHA256).Hash
    if($actual -ne $expected[$rel]) { throw "Existing file changed: $rel" }
}
$manifest=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_afterlife_native_audit\validation_a2\build_manifest.json') -Raw | ConvertFrom-Json
if($manifest.resources.Count -ne 3 -or $manifest.vanilla_replacements.Count -ne 0 -or
    $manifest.prefab -ne '#mirror_scene_afterlife' -or
    $manifest.guard_facts.PTFRB0ALM_Enabled -ne 0 -or
    $manifest.guard_facts.PTFRALMA1_Requested -ne 0) {
    throw 'A2 package scope/scene isolation is not the reviewed one.'
}
$archiveSource=Join-Path $WorkspaceRoot 'build\Afterlife_NativeScene_A2\TowerContinued_Afterlife_NativeScene_A2.archive'
$xlSource=$archiveSource+'.xl'
$luaSource=Join-Path $WorkspaceRoot 'diagnostics\PTFR_Afterlife_NativeScene_A2\init.lua'
$archiveTarget=Join-Path $root 'archive\pc\mod\TowerContinued_Afterlife_NativeScene_A2.archive'
$xlTarget=$archiveTarget+'.xl'
$luaTarget=Join-Path $root 'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_Afterlife_NativeScene_A2\init.lua'
$pairs=@(
    [pscustomobject]@{Source=$archiveSource;Target=$archiveTarget},
    [pscustomobject]@{Source=$xlSource;Target=$xlTarget},
    [pscustomobject]@{Source=$luaSource;Target=$luaTarget}
)
if((Get-FileHash -LiteralPath $archiveSource -Algorithm SHA256).Hash -ne $manifest.sha256) {
    throw 'The staged A2 archive differs from its validated manifest.'
}
foreach($pair in $pairs) {
    if(-not (Test-Path -LiteralPath $pair.Source -PathType Leaf)) { throw "Missing staged source: $($pair.Source)" }
    if(Test-Path -LiteralPath $pair.Target) { throw "Refusing to overwrite existing target: $($pair.Target)" }
    $absolute=[IO.Path]::GetFullPath($pair.Target)
    if(-not $absolute.StartsWith($root+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {
        throw "Target escaped game installation: $absolute"
    }
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $luaTarget) | Out-Null
foreach($pair in $pairs) {
    Copy-Item -LiteralPath $pair.Source -Destination $pair.Target -ErrorAction Stop
    if((Get-FileHash -LiteralPath $pair.Source -Algorithm SHA256).Hash -ne
       (Get-FileHash -LiteralPath $pair.Target -Algorithm SHA256).Hash) {
        throw "Copy/hash mismatch: $($pair.Target)"
    }
}
foreach($rel in $expected.Keys) {
    if((Get-FileHash -LiteralPath (Join-Path $root $rel) -Algorithm SHA256).Hash -ne $expected[$rel]) {
        throw "Working setup changed during A2 installation: $rel"
    }
}
[pscustomobject]@{
    A2Archive=$archiveTarget
    A2ArchiveSha256=(Get-FileHash -LiteralPath $archiveTarget -Algorithm SHA256).Hash
    A2Logger=$luaTarget
    A2LoggerSha256=(Get-FileHash -LiteralPath $luaTarget -Algorithm SHA256).Hash
    ExistingV5V6='installed, unchanged; A2 Arm only temporarily disables v5 via its mod-owned Enabled fact'
    StoryFactsChanged=$false
    SavesChanged=$false
}
