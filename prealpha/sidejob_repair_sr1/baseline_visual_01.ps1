Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $PSScriptRoot 'candidate_02/visual_baseline_01'
if(Test-Path -LiteralPath $out){throw 'Baseline exists'}
New-Item -ItemType Directory -Path $out -Force|Out-Null
foreach($pair in @(@('1572008326021521841','sweet'),@('16983850208085794969','sinnerman'))){
 $src=Join-Path $ws ('diagnostics/stefan_lipsync_20261025_01/installed_audit_01/scenes/00000000_TowerContinued_SideJobs_S29.archive/'+$pair[0]+'.scene')
 $f=Read-Cr2wFile $src;$raw=Join-Path $out ($pair[1]+'.scene')
 Write-Cr2wFile $f $raw;Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $out ($pair[1]+'.json'))
}
