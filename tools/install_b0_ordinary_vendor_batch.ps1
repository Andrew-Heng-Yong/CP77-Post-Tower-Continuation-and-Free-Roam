param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',[switch]$PreflightOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
if(@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game must be closed for installation'}
if(-not(Test-Path -LiteralPath (Join-Path $game 'r6\cache\final.redscripts'))){throw 'Unexpected game path'}
$val=Join-Path $WorkspaceRoot 'research\b0_ordinary_vendor_batch\validation'
$manifest=Get-Content -LiteralPath (Join-Path $val 'build_manifest.json') -Raw | ConvertFrom-Json
$graphTest=Get-Content -LiteralPath (Join-Path $val 'graph_test.json') -Raw | ConvertFrom-Json
$luaTest=Get-Content -LiteralPath (Join-Path $val 'controller_test.json') -Raw | ConvertFrom-Json
if($manifest.new_sites -ne 25 -or @($manifest.scene_replacements).Count -ne 0 -or @($manifest.vanilla_replacements).Count -ne 0 -or
   $graphTest.status -ne 'PASS' -or $luaTest.status -ne 'PASS' -or
   (Get-FileHash -LiteralPath (Join-Path $val 'build_manifest.json')).Hash -ne $graphTest.build_manifest_sha256 -or
   (Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_ordinary_vendor_batch\cohort.json')).Hash -ne $manifest.cohort_sha256){throw 'Scope or validated build changed'}
$items=@(
    [pscustomobject]@{Source='build\B0_OrdinaryVendorBatch\TowerContinued_B0_OrdinaryVendorBatch.archive';Relative='archive\pc\mod\TowerContinued_B0_OrdinaryVendorBatch.archive';Expected=$manifest.sha256},
    [pscustomobject]@{Source='archive\b0_ordinary_vendor_batch\TowerContinued_B0_OrdinaryVendorBatch.archive.xl';Relative='archive\pc\mod\TowerContinued_B0_OrdinaryVendorBatch.archive.xl';Expected=''},
    [pscustomobject]@{Source='redscript\PTFR_B0_OrdinaryVendors\OrdinaryVendorDriver.reds';Relative='r6\scripts\PTFR_B0_OrdinaryVendors\OrdinaryVendorDriver.reds';Expected=$graphTest.driver_sha256},
    [pscustomobject]@{Source='diagnostics\PTFR_B0_OrdinaryVendors\init.lua';Relative='bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_B0_OrdinaryVendors\init.lua';Expected=$luaTest.controller_sha256}
)
foreach($item in $items){
    $item.Source=Join-Path $WorkspaceRoot $item.Source
    $target=[IO.Path]::GetFullPath((Join-Path $game $item.Relative))
    if(-not $target.StartsWith($game+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Target outside game'}
    if(Test-Path -LiteralPath $target){throw "Refusing to overwrite $target"}
    $hash=(Get-FileHash -LiteralPath $item.Source).Hash
    if($item.Expected -and $item.Expected -ne $hash){throw "Untested source: $($item.Source)"}
    $item | Add-Member -NotePropertyName Hash -NotePropertyValue $hash
    $item | Add-Member -NotePropertyName Target -NotePropertyValue $target
}
$xl=Get-Content -LiteralPath $items[1].Source -Raw
if(@([regex]::Matches($xl,'- path:')).Count -ne 25 -or @([regex]::Matches($xl,'parent: ep1\\quest\\ep1.quest')).Count -ne 25){throw 'Registry scope changed'}
foreach($depot in $manifest.resources){if(-not $xl.Contains($depot) -or -not $depot.StartsWith('towercontinued\b0_ordinary_vendor_batch\')){throw 'Registry resource mismatch'}}
if(@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game started during preflight'}
if($PreflightOnly){[pscustomobject]@{status='PREFLIGHT_OK';newFiles=4;newOwners=25;overwrites=0};return}
$copied=[Collections.Generic.List[string]]::new()
try {
    foreach($item in $items){
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $item.Target) | Out-Null
        Copy-Item -LiteralPath $item.Source -Destination $item.Target -ErrorAction Stop
        $copied.Add($item.Target)
        if((Get-FileHash -LiteralPath $item.Target).Hash -ne $item.Hash){throw 'Installed hash mismatch'}
    }
} catch {
    foreach($target in $copied){
        $absolute=[IO.Path]::GetFullPath($target)
        if($absolute.StartsWith($game+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -and (Test-Path -LiteralPath $absolute -PathType Leaf)){Remove-Item -LiteralPath $absolute}
    }
    throw
}
$receipt=[ordered]@{status='INSTALLED_IDLE_OPT_IN_25';installedAtUtc=(Get-Date).ToUniversalTime().ToString('o');files=@($items | ForEach-Object {[ordered]@{path=$_.Target;sha256=$_.Hash}});overwrites=0;sceneReplacements=0;savesModified=$false;storyFactsModified=$false;liveTest='PENDING_COMBINED_LIFECYCLE_AND_COLD_RELOAD'}
[IO.File]::WriteAllText((Join-Path $val 'install_receipt.json'),($receipt | ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
$receipt | ConvertTo-Json -Depth 6
