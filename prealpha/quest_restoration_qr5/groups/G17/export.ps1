$ErrorActionPreference='Stop'
$workspace=(Get-Location).Path
$out=Join-Path $PSScriptRoot 'raw_exports_01'
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $out|Out-Null
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$rows=@();$i=0
foreach($p in (Get-Content -LiteralPath (Join-Path $PSScriptRoot 'raw_export_inputs.json') -Raw|ConvertFrom-Json)){
 if((Get-FileHash -LiteralPath $p.raw).Hash -cne $p.raw_sha256){throw 'Pinned input changed'}
 $j=Join-Path $out ('resource_'+$i+'.json')
 Export-Cr2wJson (Read-Cr2wFile $p.raw) $j
 $rows+=@{depot=$p.depot;raw=$p.raw;raw_sha256=$p.raw_sha256;json=$j;json_sha256=(Get-FileHash -LiteralPath $j).Hash;scope='Fresh read-only deserialize/export; no raw or game writes'}
 $i+=1
}
$rows|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8
Write-Output ('Exported '+$rows.Count+' pinned G17 resources')
