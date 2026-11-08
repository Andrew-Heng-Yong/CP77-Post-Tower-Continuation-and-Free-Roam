param([Parameter(Mandatory=$true)][string]$Epoch,[Parameter(Mandatory=$true)][string]$ApprovedChanges,[Parameter(Mandatory=$true)][string]$FinalManifest,[Parameter(Mandatory=$true)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$w=(Get-Location).Path;$o=if([IO.Path]::IsPathRooted($Output)){[IO.Path]::GetFullPath($Output)}else{[IO.Path]::GetFullPath((Join-Path $w $Output))}
if(-not $o.StartsWith([IO.Path]::GetFullPath($PSScriptRoot)+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Private worker output containment required'}
if(Test-Path -LiteralPath $o){throw 'Fresh output required'}
$py='C:/Users/Ayong/.local/bin/python3.14.exe'
& $py -X utf8 -B (Join-Path $PSScriptRoot 'prepare_final_inputs.py') --epoch $Epoch --approved $ApprovedChanges --manifest $FinalManifest --output (Join-Path $o 'expected')
if($LASTEXITCODE -ne 0){throw 'Independent expectation preparation failed'}
$inputs=Join-Path $o 'expected/inputs.json';$capture=Join-Path $o 'readback'
& (Join-Path $PSScriptRoot 'extract_final_archive.ps1') -Inputs $inputs -Output $capture
& $py -X utf8 -B (Join-Path $PSScriptRoot 'verify_final_package.py') --inputs $inputs --capture (Join-Path $capture 'manifest.json') --output (Join-Path $o 'verification')
if($LASTEXITCODE -ne 0){throw 'Independent final package verification failed'}
