param([string]$InputName='raw_inputs_01.json',[string]$OutputName='readback_01')
$ErrorActionPreference='Stop'
$ws=(Get-Location).Path;$dir=Join-Path $ws 'prealpha/quest_restoration_qr7/worker_b';$out=Join-Path $dir $OutputName
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $out -Force|Out-Null
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$inputs=Get-Content -Raw -LiteralPath (Join-Path $dir $InputName)|ConvertFrom-Json;$rows=@();$idx=0
foreach($row in $inputs){
 if((Get-FileHash -LiteralPath $row.raw).Hash -cne $row.raw_sha256){throw 'Pinned raw changed'}
 $json=Join-Path $out ('resource_'+$idx+'.json')
 try{Export-Cr2wJson (Read-Cr2wFile $row.raw) $json;$rows+=@{depot=$row.depot;raw=$row.raw;raw_sha256=$row.raw_sha256;json=[IO.Path]::GetFullPath($json);json_sha256=(Get-FileHash -LiteralPath $json).Hash;status='EXPORTED'}}
 catch{$rows+=@{depot=$row.depot;raw=$row.raw;raw_sha256=$row.raw_sha256;status='OPAQUE';error=$_.Exception.Message}}
 $idx++
}
$rows|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8
Write-Output ('Ronald fresh readback exports '+$rows.Count)
