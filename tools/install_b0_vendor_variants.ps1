param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[switch]$PreflightOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$val=Join-Path $WorkspaceRoot 'research\b0_vendor_variants\validation'
$tests=Get-Content (Join-Path $val 'tests.json') -Raw | ConvertFrom-Json
$manifest=Get-Content (Join-Path $val 'build_manifest.json') -Raw | ConvertFrom-Json
if($tests.status -ne 'PASS' -or $tests.owners -ne 6 -or $manifest.resources.Count -ne 6 -or $tests.archive_sha256 -ne $manifest.sha256){throw 'Validation mismatch'}
if(@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Close Cyberpunk before installation'}
$items=@(
    [pscustomobject]@{Source='build\B0_VendorVariants\TowerContinued_B0_VendorVariants.archive';Relative='archive\pc\mod\TowerContinued_B0_VendorVariants.archive';Expected=$tests.archive_sha256},
    [pscustomobject]@{Source='archive\b0_vendor_variants\TowerContinued_B0_VendorVariants.archive.xl';Relative='archive\pc\mod\TowerContinued_B0_VendorVariants.archive.xl';Expected=$tests.xl_sha256},
    [pscustomobject]@{Source='redscript\PTFR_B0_VendorVariants\VendorVariantDriver.reds';Relative='r6\scripts\PTFR_B0_VendorVariants\VendorVariantDriver.reds';Expected=$tests.driver_sha256},
    [pscustomobject]@{Source='diagnostics\PTFR_B0_VendorVariants\init.lua';Relative='bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_B0_VendorVariants\init.lua';Expected=$tests.controller_sha256}
)
foreach($item in $items){
    $item.Source=Join-Path $WorkspaceRoot $item.Source
    $target=[IO.Path]::GetFullPath((Join-Path $game $item.Relative))
    if(-not $target.StartsWith($game+'\',[StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $target)){throw "Unsafe/existing target: $target"}
    $hash=(Get-FileHash -LiteralPath $item.Source).Hash
    if($item.Expected -and $hash -ne $item.Expected){throw 'Source changed since validation'}
    $item | Add-Member -NotePropertyName Target -NotePropertyValue $target
    $item | Add-Member -NotePropertyName Hash -NotePropertyValue $hash
}
$xl=Get-Content -LiteralPath $items[1].Source -Raw
if([regex]::Matches($xl,'- path:').Count -ne 6 -or [regex]::Matches($xl,'parent: ep1\\quest\\ep1.quest').Count -ne 6){throw 'Registry scope changed'}
foreach($p in $manifest.resources){if(-not $xl.Contains($p) -or -not $p.StartsWith('towercontinued\b0_vendor_variants\')){throw 'Registry paths changed'}}
if($PreflightOnly){'PREFLIGHT_OK: six narrow owners, four new files, zero overwrites';return}
if(@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game started during preflight'}
$copied=[Collections.Generic.List[string]]::new()
try{
    foreach($item in $items){
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $item.Target) | Out-Null
        Copy-Item -LiteralPath $item.Source -Destination $item.Target;$copied.Add($item.Target)
        if((Get-FileHash -LiteralPath $item.Target).Hash -ne $item.Hash){throw 'Installed hash mismatch'}
    }
}catch{
    foreach($p in $copied){if(([IO.Path]::GetFullPath($p)).StartsWith($game+'\',[StringComparison]::OrdinalIgnoreCase)){Remove-Item -LiteralPath $p}}
    throw
}
$receipt=[ordered]@{status='INSTALLED_AUTOMATIC_SIX_SITE_CANDIDATE';installedAtUtc=(Get-Date).ToUniversalTime().ToString('o');files=@($items|ForEach-Object {[ordered]@{path=$_.Target;sha256=$_.Hash}});overwrites=0;sceneReplacements=0;savesModified=$false;storyFactsForced=$false;live='PENDING_USER_CHECKS'}
[IO.File]::WriteAllText((Join-Path $val 'install_receipt.json'),($receipt|ConvertTo-Json -Depth 6))
$receipt|ConvertTo-Json -Depth 6
