param([string]$OutputName='buffers_01')
# Read-only decompression. No writer or quest controller is invoked.
$ErrorActionPreference='Stop'
$ws=(Get-Location).Path;$taskDir=Join-Path $ws 'prealpha/quest_restoration_qr8/worker_b';$out=Join-Path $taskDir $OutputName
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $out|Out-Null
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$p=(Get-Content -Raw -LiteralPath (Join-Path $taskDir 'readback_02/manifest.json')|ConvertFrom-Json|Where-Object {$_.depot -like '*quest_7abca2b8d18f8562.streamingsector'})
$markers=Get-Content -Raw -LiteralPath (Join-Path $ws 'prealpha/quest_restoration_qr7/shared/marker_providers_01/manifest.json')|ConvertFrom-Json
$targets=@(@{name='bar';raw=$p.raw;sha=$p.raw_sha256},@{name='always0';raw=$markers.providers[2].raw;sha=$markers.providers[2].raw_sha256})
$rows=@()
foreach($t in $targets){
 if((Get-FileHash -LiteralPath $t.raw).Hash -cne $t.sha){throw 'Source drift'}
 $file=Read-Cr2wFile $t.raw;$bytes=$file.RootChunk.NodeData.Buffer.GetBytes();$path=Join-Path $out ($t.name+'.buffer')
 [IO.File]::WriteAllBytes($path,$bytes)
 $rows+=@{name=$t.name;raw=$t.raw;raw_sha256=$t.sha;buffer=$path;buffer_sha256=(Get-FileHash -LiteralPath $path).Hash;length=$bytes.Length;extraction='RootChunk.NodeData.Buffer.GetBytes()';serialized=$false}
}
ConvertTo-Json -InputObject @($rows) -Depth 10|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8
Write-Output 'Two raw setup buffers decompressed; no serialization'
