param([Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
if(Test-Path -LiteralPath $Output){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $Output|Out-Null
. ./tools/build_phase2a.ps1 -HelpersOnly -WolvenKitRoot (Join-Path (Get-Location).Path 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$inputs=Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'inputs.json')|ConvertFrom-Json
$rows=@()
foreach($x in $inputs){
 if((Get-FileHash -LiteralPath $x.raw -Algorithm SHA256).Hash -cne $x.sha256){throw ('Input changed: '+$x.name)}
 $j=Join-Path $Output ($x.name+'.json')
 Export-Cr2wJson (Read-Cr2wFile $x.raw) $j
 $rows+=@{name=$x.name;depot=$x.depot;binary=$x.raw;sha256=$x.sha256;json=[IO.Path]::GetFullPath($j);json_sha256=(Get-FileHash -LiteralPath $j -Algorithm SHA256).Hash;tool='WolvenKit9.1 Read-Cr2wFile/Export-Cr2wJson; no binary write'}
}
$rows|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $Output 'manifest.json') -Encoding utf8NoBOM
Write-Output ('Independent raw exports '+$rows.Count)
