Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$plan=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'plan_01.json') -Raw|ConvertFrom-Json
$r=@($plan.installed|Where-Object depot -ceq 'towercontinued\b0_story_eight\yoko.scene')
if($r.Count -ne 1){throw 'Yoko source ambiguous'}
$src=Join-Path $ws $r[0].raw
if((Get-FileHash -LiteralPath $src).Hash -cne $r[0].sha256){throw 'Yoko source drift'}
$out=Join-Path $PSScriptRoot 'candidate_02/baseline_yoko'
if(Test-Path -LiteralPath $out){throw 'Baseline exists'}
$f=Read-Cr2wFile $src;Write-Cr2wFile $f ($out+'.scene')
Export-Cr2wJson (Read-Cr2wFile ($out+'.scene')) ($out+'.json')
@{status='UNMODIFIED_SERIALIZER_BASELINE';source_sha256=$r[0].sha256;roundtrip_sha256=(Get-FileHash -LiteralPath ($out+'.scene')).Hash;json_sha256=(Get-FileHash -LiteralPath ($out+'.json')).Hash;game_writes=0;save_writes=0}|ConvertTo-Json|Set-Content -LiteralPath ($out+'_proof.json') -Encoding utf8
