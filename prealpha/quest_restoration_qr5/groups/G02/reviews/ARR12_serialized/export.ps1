param([Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$workspace=(Get-Location).Path
if(Test-Path -LiteralPath $Output){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $Output | Out-Null
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$inputs=Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'inputs.json') | ConvertFrom-Json
$rows=@()
foreach($row in $inputs){
 if((Get-FileHash -LiteralPath $row.raw -Algorithm SHA256).Hash -cne $row.sha256){throw ('Input changed: '+$row.name)}
 $json=Join-Path $Output ($row.name+'.json')
 Export-Cr2wJson (Read-Cr2wFile $row.raw) $json
 $rows+=@{name=$row.name;raw=$row.raw;depot=$row.depot;raw_sha256=$row.sha256;json=[IO.Path]::GetFullPath($json);json_sha256=(Get-FileHash -LiteralPath $json -Algorithm SHA256).Hash;scope='Read exact pinned resource; fresh WKit9.1 JSON export only'}
}
$rows|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $Output 'manifest.json') -Encoding utf8NoBOM
Write-Output ('Fresh independent exports: '+$rows.Count)
