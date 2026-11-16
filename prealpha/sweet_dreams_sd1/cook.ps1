Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$planPath=Join-Path $PSScriptRoot 'input_02/plan.json'
$plan=Get-Content -LiteralPath $planPath -Raw|ConvertFrom-Json -Depth 80
if($plan.epoch -cne 'SD1' -or $plan.predecessor -cne 'KM2' -or $plan.edits.Count -ne 2){throw 'Unexpected SD1 scope'}
$out=Join-Path $PSScriptRoot 'readback_01'
if(Test-Path -LiteralPath $out){throw 'Fresh readback required'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
New-Item -ItemType Directory -Path $out|Out-Null
$rows=@(foreach($edit in $plan.edits){
 if((Get-FileHash -LiteralPath $edit.edited_json).Hash -cne $edit.edited_json_sha256){throw 'Changed edited input'}
 $target=Join-Path (Join-Path $plan.candidate 'archive_source') $edit.depot
 if((Get-FileHash -LiteralPath $target).Hash -cne $edit.source.sha256){throw 'Wrong PE1 predecessor payload'}
 $dto=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],[IO.File]::ReadAllText($edit.edited_json),[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
 Write-Cr2wFile $dto.Data $target
 $json=Join-Path $out (([WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($edit.depot).ToString())+'.json')
 Export-Cr2wJson (Read-Cr2wFile $target) $json
 @{depot=$edit.depot;raw=$target;sha256=(Get-FileHash -LiteralPath $target).Hash;json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash}
})
@{status='SD1_TWO_PRIVATE_RESOURCES_COOKED_AND_READ_BACK';plan_sha256=(Get-FileHash -LiteralPath $planPath).Hash;resources=$rows;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8NoBOM
Write-Output "Cooked and read back $($rows.Count) private resources."
