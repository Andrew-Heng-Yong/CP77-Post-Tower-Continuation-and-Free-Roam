param([string]$InputName='inputs_01.json',[string]$OutputName='readback_01')
$ErrorActionPreference='Stop'
$ws=(Get-Location).Path;$taskDir=Join-Path $ws 'prealpha/quest_restoration_qr8/worker_b';$out=Join-Path $taskDir $OutputName
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $out -Force|Out-Null
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$rows=@();$idx=0
foreach($p in (Get-Content -Raw -LiteralPath (Join-Path $taskDir $InputName)|ConvertFrom-Json)){
 if((Get-FileHash -LiteralPath $p.raw).Hash -cne $p.raw_sha256){throw 'Input drift'}
 $json=Join-Path $out ('resource_'+$idx+'.json');$errorText=$null;$status='EXPORTED'
 try{Export-Cr2wJson (Read-Cr2wFile $p.raw) $json}catch{$status='OPAQUE';$errorText=$_.Exception.Message}
 $rows+=@{depot=$p.depot;raw=$p.raw;raw_sha256=$p.raw_sha256;json=$json;json_sha256=$(if(Test-Path -LiteralPath $json){(Get-FileHash -LiteralPath $json).Hash}else{$null});status=$status;error=$errorText};$idx++
}
ConvertTo-Json -InputObject @($rows) -Depth 10|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8
Write-Output ('Fresh QR8 B readbacks '+$rows.Count)
