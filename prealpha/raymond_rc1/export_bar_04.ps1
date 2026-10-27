Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$source=Join-Path $PSScriptRoot 'candidate_03/archive_source/towercontinued/sidejobs_s29/native/base/quest/minor_quests/mq040/phases/mq040_bar_corpo.questphase'
$dir=Join-Path $PSScriptRoot 'evidence_04'
if(Test-Path $dir){throw 'Use successor evidence directory'}
New-Item -ItemType Directory -Path $dir|Out-Null
Export-Cr2wJson (Read-Cr2wFile $source) (Join-Path $dir 'bar_corpo.json')
Get-FileHash (Join-Path $dir 'bar_corpo.json') | Select-Object Hash,Path
