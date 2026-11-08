Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$C=Join-Path $PSScriptRoot 'candidate_01';$repairDir=Join-Path $C 'repair_ronald_01'
$p=Get-Content -LiteralPath (Join-Path $repairDir 'promotion.json') -Raw|ConvertFrom-Json -Depth 100
$out=Join-Path $repairDir 'readback_02';if(Test-Path -LiteralPath $out){throw 'Fresh readback output required'}
New-Item -ItemType Directory -Path $out|Out-Null
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$rows=@();$i=0
foreach($r in $p.rows){
 $raw=Join-Path (Join-Path $C 'archive_source') $r.depot
 if((Get-FileHash -LiteralPath $raw).Hash -cne $r.after){throw 'Promoted bytes changed'}
 $f=Read-Cr2wFile $raw;$json=Join-Path $out "$i.json";Export-Cr2wJson $f $json
 $row=@{depot=$r.depot;raw=$raw;raw_sha256=$r.after;json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash;approved_json=$r.approved_json}
 if($r.depot.EndsWith('.streamingsector')){
  $buffer=Join-Path $out "$i.nodes.bin";[IO.File]::WriteAllBytes($buffer,$f.RootChunk.NodeData.Buffer.GetBytes());$row.buffer=$buffer;$row.buffer_sha256=(Get-FileHash -LiteralPath $buffer).Hash
 }
 $rows+=,$row;$i++
}
@{status='PASS_FRESH_INTEGRATED_TYPED_READBACK';rows=$rows;promotion_sha256=(Get-FileHash -LiteralPath (Join-Path $repairDir 'promotion.json')).Hash}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8NoBOM
'PASS_FRESH_INTEGRATED_TYPED_READBACK'
