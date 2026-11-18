Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$pins=Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'work/inputs.json')|ConvertFrom-Json -AsHashtable
if((Get-FileHash -LiteralPath $pins.edited).Hash -cne $pins.edited_sha256){throw 'Edited JSON drift'}
$out=Join-Path $PSScriptRoot 'work/graph_01/entry.questphase'
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$text=Get-Content -Raw -LiteralPath $pins.edited
$dto=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],$text,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
Write-Cr2wFile $dto.Data $out
Export-Cr2wJson (Read-Cr2wFile $out) ($out+'.json')
@{path=$out;sha256=(Get-FileHash -LiteralPath $out).Hash;export_sha256=(Get-FileHash -LiteralPath ($out+'.json')).Hash}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'work/graph_01/readback.json') -Encoding utf8NoBOM
Write-Output 'Cooked and read back the private KOLD entry.'
