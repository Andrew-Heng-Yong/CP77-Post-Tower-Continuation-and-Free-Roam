Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$source=Join-Path $ws 'prealpha/world_workspots_w2/candidate_04/archive_source/towercontinued/world_interactions'
$dest=Join-Path $PSScriptRoot 'candidate_04/world_coaster_review'
[void][IO.Directory]::CreateDirectory($dest)
foreach($name in @('coaster.scene','coaster_ride.questphase','coaster_owner.questphase','coaster_gate.questphase')){
 $inputPath=Join-Path $source $name
 $outputPath=Join-Path $dest ($name+'.json')
 if(Test-Path -LiteralPath $outputPath){throw ('Preserve export '+$name)}
 Export-Cr2wJson (Read-Cr2wFile $inputPath) $outputPath
}
@{status='EXPORTED_READ_ONLY';files=4}|ConvertTo-Json
