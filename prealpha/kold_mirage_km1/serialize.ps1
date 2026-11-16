Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$plan=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'input_01/plan.json') -Raw|ConvertFrom-Json -Depth 30
$out=Join-Path $PSScriptRoot 'readback_01'
if(Test-Path -LiteralPath $out){throw 'Fresh readback output required'}
if($plan.depot -cne 'towercontinued\sidejobs_s29\entries\mq016_bartmoss.questphase' -or $plan.epoch -cne 'KM1'){throw 'Wrong resource scope'}
if((Get-FileHash -LiteralPath $plan.edited_json).Hash -cne $plan.edited_json_sha256){throw 'Edited input changed'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
New-Item -ItemType Directory -Path $out|Out-Null
$dto=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],[IO.File]::ReadAllText($plan.edited_json),[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
$target=Join-Path (Join-Path $plan.candidate 'archive_source') $plan.depot
if((Get-FileHash -LiteralPath $target).Hash -cne $plan.source_raw_sha256){throw 'Wrong candidate predecessor resource'}
Write-Cr2wFile $dto.Data $target
$json=Join-Path $out 'mq016_entry.json'
Export-Cr2wJson (Read-Cr2wFile $target) $json
@{status='KM1_ENTRY_COOKED_AND_READ_BACK';depot=$plan.depot;raw=$target;sha256=(Get-FileHash -LiteralPath $target).Hash;readback=$json;readback_sha256=(Get-FileHash -LiteralPath $json).Hash;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8NoBOM
Write-Output 'Cooked and read back the one private KOLD MIRAGE entry.'
