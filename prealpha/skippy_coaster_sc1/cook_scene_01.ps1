Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$C=Join-Path $PSScriptRoot 'candidate_04'
$inputPath=Join-Path $C 'scene_after_01.json'
$outputPath=Join-Path $C 'scene_after_01.scene'
$readback=Join-Path $C 'scene_readback_01.json'
if((Test-Path -LiteralPath $outputPath) -or (Test-Path -LiteralPath $readback)){throw 'Preserve cooked scene evidence'}
$opt=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
$dto=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],[IO.File]::ReadAllText($inputPath),$opt)
$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$dto.Data.RootChunk
Write-Cr2wFile $file $outputPath
Export-Cr2wJson (Read-Cr2wFile $outputPath) $readback
@{status='SCENE_COOKED_AND_READ_BACK';sha256=(Get-FileHash -LiteralPath $outputPath -Algorithm SHA256).Hash;readback_sha256=(Get-FileHash -LiteralPath $readback -Algorithm SHA256).Hash}|ConvertTo-Json
