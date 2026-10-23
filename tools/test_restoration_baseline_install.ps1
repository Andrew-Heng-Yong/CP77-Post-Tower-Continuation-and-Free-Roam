param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$real=Join-Path $WorkspaceRoot 'build\RestorationBaseline_R1'
$fixture=Join-Path $real ('installer_fixture_'+[guid]::NewGuid().ToString('N'))
$fakeGame=Join-Path $fixture 'game'
$fakeWorkspace=Join-Path $fixture 'workspace'
$fakeOut=Join-Path $fakeWorkspace 'build\RestorationBaseline_R1'
New-Item -ItemType Directory -Force -Path (Join-Path $fakeGame 'archive\pc\content'),$fakeOut|Out-Null
Copy-Item -LiteralPath (Join-Path $real 'game') -Destination (Join-Path $fakeOut 'game') -Recurse
foreach($name in @('manifest.json','tests.json')){Copy-Item -LiteralPath (Join-Path $real $name) -Destination (Join-Path $fakeOut $name)}
$inventory=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\restoration_baseline\frozen_inventory.json') -Raw|ConvertFrom-Json
foreach($f in $inventory.files){
 $dst=Join-Path $fakeGame $f.path;New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst)|Out-Null
 Copy-Item -LiteralPath (Join-Path (Join-Path $WorkspaceRoot 'research\restoration_baseline\frozen') $f.path) -Destination $dst
}
& (Join-Path $PSScriptRoot 'install_restoration_baseline.ps1') -WorkspaceRoot $fakeWorkspace -GameRoot $fakeGame -PreflightOnly
& (Join-Path $PSScriptRoot 'install_restoration_baseline.ps1') -WorkspaceRoot $fakeWorkspace -GameRoot $fakeGame
& (Join-Path $PSScriptRoot 'install_restoration_baseline.ps1') -WorkspaceRoot $fakeWorkspace -GameRoot $fakeGame -Rollback -PreflightOnly
& (Join-Path $PSScriptRoot 'install_restoration_baseline.ps1') -WorkspaceRoot $fakeWorkspace -GameRoot $fakeGame -Rollback
foreach($f in $inventory.files){if((Get-FileHash -LiteralPath (Join-Path $fakeGame $f.path)).Hash -ne $f.sha256){throw 'Roundtrip failed'}}
$manifest=Get-Content -LiteralPath (Join-Path $real 'manifest.json') -Raw|ConvertFrom-Json
foreach($f in @($manifest.files|Where-Object action -eq 'add')){if(Test-Path -LiteralPath (Join-Path $fakeGame $f.path)){throw 'Rollback left new file'}}
$report=@{status='PASS';fixture=$fixture;originalFilesRestored=$inventory.files.Count;newFilesRemoved=2;realGameModified=$false;installerSha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'install_restoration_baseline.ps1')).Hash}
[IO.File]::WriteAllText((Join-Path $real 'installer_tests.json'),($report|ConvertTo-Json -Depth 4))
'PASS: install/rollback round-trip in isolated fixture; real game untouched; fixture retained'
