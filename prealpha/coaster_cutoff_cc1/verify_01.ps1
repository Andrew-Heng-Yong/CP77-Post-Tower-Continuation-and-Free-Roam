Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$rel='towercontinued\sidejobs_s30\entries\mq006_rollercoaster.questphase'
$old=Join-Path $ws ('prealpha/skippy_ambient_sc3/candidate_02/archive_source/'+$rel)
$new=Join-Path $PSScriptRoot ('candidate_01/archive_source/'+$rel)
$out=Join-Path $PSScriptRoot 'candidate_01'
Export-Cr2wJson (Read-Cr2wFile $old) (Join-Path $out 'entry_before_01.json')
Export-Cr2wJson (Read-Cr2wFile $new) (Join-Path $out 'entry_after_01.json')
@{status='EXPORTED';old=(Get-FileHash $old).Hash;new=(Get-FileHash $new).Hash}|ConvertTo-Json
