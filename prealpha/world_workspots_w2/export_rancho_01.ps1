Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$source=@(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'candidate_03/source') -Filter '*.questphase' -Recurse -File)
if($source.Count -ne 1){throw 'Rancho resource count drift'}
$out=Join-Path $PSScriptRoot 'candidate_03/graph_export_01.json'
if(Test-Path -LiteralPath $out){throw 'Preserve graph export'}
$file=Read-Cr2wFile $source[0].FullName
Export-Cr2wJson $file $out
@{status='RANCHO_GRAPH_EXPORTED';sha256=(Get-FileHash -LiteralPath $out -Algorithm SHA256).Hash}|ConvertTo-Json
