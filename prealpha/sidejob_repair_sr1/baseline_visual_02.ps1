Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $PSScriptRoot 'candidate_02/visual_baseline_02'
if(Test-Path -LiteralPath $out){throw 'Baseline exists'}
New-Item -ItemType Directory -Path $out -Force|Out-Null
$srcRoot=Join-Path $ws 'diagnostics/stefan_lipsync_20261025_01/installed_audit_01/scenes/00000000_TowerContinued_SideJobs_S29.archive'
foreach($pair in @(@('12772498349548735763','delamain'),@('7916485406720080517','killing'),@('14754961886327623219','freedom'),@('3808959417876599003','kold'))){
 $src=Join-Path $srcRoot ($pair[0]+'.scene');$f=Read-Cr2wFile $src;$raw=Join-Path $out ($pair[1]+'.scene');Write-Cr2wFile $f $raw;Export-Cr2wJson (Read-Cr2wFile $raw) ($raw+'.json')
}
$src=Join-Path $PSScriptRoot 'candidate_02/kold_workspot_source_01/memoryresident_1_general.workspot'
$f=Read-Cr2wFile $src;$raw=Join-Path $out 'kold.workspot';Write-Cr2wFile $f $raw;Export-Cr2wJson (Read-Cr2wFile $raw) ($raw+'.json')
