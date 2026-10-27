Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$c=Join-Path $PSScriptRoot 'candidate_04'
$inputPath=Join-Path $c 'scene_roundtrip_01.scene'
$outputPath=Join-Path $c 'scene_roundtrip_readback_01.json'
if(Test-Path -LiteralPath $outputPath){throw 'Preserve scene roundtrip readback'}
Export-Cr2wJson (Read-Cr2wFile $inputPath) $outputPath
@{status='EXPORTED';sha256=(Get-FileHash -LiteralPath $inputPath -Algorithm SHA256).Hash}|ConvertTo-Json
