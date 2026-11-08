param([string]$OutputName='bar_buffer_01')
$ErrorActionPreference='Stop'
$ws=(Get-Location).Path;$homeDir=Join-Path $ws 'prealpha/quest_restoration_qr7/worker_b';$out=Join-Path $homeDir $OutputName
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $out|Out-Null
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$pin=Get-Content -Raw -LiteralPath (Join-Path $homeDir 'bar_provider_02/manifest.json')|ConvertFrom-Json
$p=$pin.providers[0];if((Get-FileHash -LiteralPath $p.raw).Hash -cne $p.raw_sha256){throw 'Raw provider changed'}
$resource=Read-Cr2wFile $p.raw
$bytes=$resource.RootChunk.NodeData.Buffer.GetBytes()
$path=Join-Path $out 'node_setups.bin';[IO.File]::WriteAllBytes($path,$bytes)
@{raw=$p.raw;raw_sha256=$p.raw_sha256;buffer=$path;buffer_sha256=(Get-FileHash -LiteralPath $path).Hash;length=$bytes.Length;extraction='RootChunk.NodeData.Buffer.GetBytes()';serialized=$false}|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8
Write-Output ('Exact node setup bytes '+$bytes.Length)
