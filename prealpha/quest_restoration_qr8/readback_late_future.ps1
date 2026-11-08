Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$candidate=Join-Path $PSScriptRoot 'candidate_01';$repairDir=Join-Path $candidate 'repair_late_future_01'
$promotion=Get-Content -LiteralPath (Join-Path $repairDir 'promotion.json') -Raw|ConvertFrom-Json -Depth 100
$out=Join-Path $repairDir 'readback_01';if(Test-Path -LiteralPath $out){throw 'Fresh readback output required'}
$raw=Join-Path (Join-Path $candidate 'archive_source') $promotion.depot
if((Get-FileHash -LiteralPath $raw).Hash -cne $promotion.after){throw 'Promoted bytes changed'}
New-Item -ItemType Directory -Path $out|Out-Null
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
Export-Cr2wJson (Read-Cr2wFile (Join-Path $repairDir 'before.questphase')) (Join-Path $out 'before.json')
Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $out 'after.json')
@{status='PASS_FRESH_ACTUAL_SUCCESSOR_TYPED_READBACK';raw=$raw;raw_sha256=$promotion.after;before_json=(Join-Path $out 'before.json');before_json_sha256=(Get-FileHash -LiteralPath (Join-Path $out 'before.json')).Hash;after_json=(Join-Path $out 'after.json');after_json_sha256=(Get-FileHash -LiteralPath (Join-Path $out 'after.json')).Hash;promotion_sha256=(Get-FileHash -LiteralPath (Join-Path $repairDir 'promotion.json')).Hash}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8NoBOM
'PASS_FRESH_ACTUAL_SUCCESSOR_TYPED_READBACK'
