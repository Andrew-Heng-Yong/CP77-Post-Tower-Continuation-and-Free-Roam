param([string]$Output='resource_exports_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$O=Join-Path $PSScriptRoot $Output
if(Test-Path -LiteralPath $O){throw 'Fresh worker output required'}
$inputPath=Join-Path $PSScriptRoot 'targets_01.json'
$data=Get-Content -LiteralPath $inputPath -Raw|ConvertFrom-Json -Depth 100
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
[IO.Directory]::CreateDirectory($O)|Out-Null
$rows=@();$i=0
foreach($r in $data.targets){
 if((Get-FileHash -LiteralPath $r.raw).Hash -cne $r.raw_sha256){throw ('Input drift '+$r.depot)}
 $json=Join-Path $O ('resource_'+$i+'.json');$i++
 $item=@{depot=$r.depot;raw=$r.raw;raw_sha256=$r.raw_sha256;source_manifest=$r.source_manifest;source_manifest_sha256=$r.source_manifest_sha256}
 try{Export-Cr2wJson (Read-Cr2wFile $r.raw) $json;$item.json=$json;$item.json_sha256=(Get-FileHash -LiteralPath $json).Hash;$item.status='EXPORTED'}
 catch{$item.status='OPAQUE';$item.error=$_.Exception.Message}
 if((Get-FileHash -LiteralPath $r.raw).Hash -cne $r.raw_sha256){throw 'Readback input changed'}
 $rows+=,$item
}
@{status='FRESH_READ_ONLY_TARGETED_READBACK';resources=$rows;input=@{path=$inputPath;sha256=(Get-FileHash -LiteralPath $inputPath).Hash};code_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 30|Set-Content -LiteralPath (Join-Path $O 'manifest.json') -Encoding utf8NoBOM
@{resources=$rows.Count;opaque=@($rows|Where-Object status -eq 'OPAQUE').Count;output=$O}|ConvertTo-Json -Compress
