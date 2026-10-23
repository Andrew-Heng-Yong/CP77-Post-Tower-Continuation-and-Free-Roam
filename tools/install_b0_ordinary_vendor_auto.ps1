param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[switch]$PreflightOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$val=Join-Path $WorkspaceRoot 'research\b0_ordinary_vendor_batch\validation'
$original=Get-Content -LiteralPath (Join-Path $val 'install_receipt.json') -Raw | ConvertFrom-Json
$graph=Get-Content -LiteralPath (Join-Path $val 'graph_test.json') -Raw | ConvertFrom-Json
$lua=Get-Content -LiteralPath (Join-Path $val 'controller_test.json') -Raw | ConvertFrom-Json
$auto=Get-Content -LiteralPath (Join-Path $val 'auto_test.json') -Raw | ConvertFrom-Json
if($graph.status -ne 'PASS' -or $lua.status -ne 'PASS' -or $auto.status -ne 'PASS'){throw 'Validation failed'}
if(@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game must be closed'}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\'
foreach($file in $original.files){
    if(-not ([IO.Path]::GetFullPath($file.path)).StartsWith($game,[StringComparison]::OrdinalIgnoreCase)){throw 'Unexpected installed path'}
    if((Get-FileHash -LiteralPath $file.path).Hash -ne $file.sha256){throw "Original installation changed: $($file.path)"}
}
$items=@(
    [pscustomobject]@{Source=(Join-Path $WorkspaceRoot 'redscript\PTFR_B0_OrdinaryVendors\OrdinaryVendorDriver.reds');Target=$original.files[2].path;Expected=$auto.driver_sha256;Backup='OrdinaryVendorDriver.reds'},
    [pscustomobject]@{Source=(Join-Path $WorkspaceRoot 'diagnostics\PTFR_B0_OrdinaryVendors\init.lua');Target=$original.files[3].path;Expected=$lua.controller_sha256;Backup='init.lua'}
)
if($graph.driver_sha256 -ne $auto.driver_sha256){throw 'Driver validations differ'}
foreach($item in $items){if((Get-FileHash -LiteralPath $item.Source).Hash -ne $item.Expected){throw 'Validated source changed'}}
if($PreflightOnly){'PREFLIGHT_OK: two runtime files; archive and full scenes unchanged';return}
$backup=Join-Path $val ('opt_in_rollback_'+(Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $backup | Out-Null
foreach($item in $items){Copy-Item -LiteralPath $item.Target -Destination (Join-Path $backup $item.Backup)}
if(@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game started before replacement'}
try {
    foreach($item in $items){
        Copy-Item -LiteralPath $item.Source -Destination $item.Target
        if((Get-FileHash -LiteralPath $item.Target).Hash -ne $item.Expected){throw 'Installed hash mismatch'}
    }
} catch {
    foreach($item in $items){Copy-Item -LiteralPath (Join-Path $backup $item.Backup) -Destination $item.Target}
    throw
}
$receipt=[ordered]@{status='INSTALLED_AUTOMATIC_RUNTIME_UNVERIFIED';installedAtUtc=(Get-Date).ToUniversalTime().ToString('o');backup=$backup;files=@($items | ForEach-Object {[ordered]@{path=$_.Target;sha256=$_.Expected}});archiveChanged=$false;priorVendorPackagesChanged=$false;savesModified=$false;manualOptInTest='skipped at user request';liveChecks='user will check informally'}
[IO.File]::WriteAllText((Join-Path $val 'auto_install_receipt.json'),($receipt | ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
$receipt | ConvertTo-Json -Depth 5
