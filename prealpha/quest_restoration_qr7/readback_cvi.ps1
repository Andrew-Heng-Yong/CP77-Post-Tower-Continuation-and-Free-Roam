Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$C=Join-Path $PSScriptRoot 'candidate_01';$O=Join-Path $C 'repair_cvi_02'
$p=Get-Content -LiteralPath (Join-Path $O 'promotion.json') -Raw|ConvertFrom-Json -Depth 100
if(Test-Path -LiteralPath (Join-Path $O 'after.json')){throw 'Fresh candidate readback required'}
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$raw=Join-Path (Join-Path $C 'archive_source') $p.depot
if((Get-FileHash -LiteralPath $raw).Hash -cne $p.after){throw 'Promoted bytes changed'}
Export-Cr2wJson (Read-Cr2wFile (Join-Path $O 'before.questphase')) (Join-Path $O 'before.json')
Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $O 'after.json')
@{status='PASS_ACTUAL_PROMOTED_CANDIDATE_READBACK';raw=$raw;raw_sha256=$p.after;json=(Join-Path $O 'after.json');json_sha256=(Get-FileHash -LiteralPath (Join-Path $O 'after.json')).Hash;source_manifest_sha256=$p.source_manifest_sha256;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $O 'readback.json') -Encoding utf8NoBOM
'PASS_ACTUAL_PROMOTED_CANDIDATE_READBACK'
