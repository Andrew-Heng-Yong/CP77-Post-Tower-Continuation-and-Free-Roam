Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$plan=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'input_02/plan.json') -Raw|ConvertFrom-Json -Depth 40
$out=Join-Path $PSScriptRoot 'readback_01'
if(Test-Path -LiteralPath $out){throw 'Fresh readback output required'}
if($plan.epoch -cne 'PE1' -or $plan.resources.Count -ne 12){throw 'Unexpected resource scope'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
New-Item -ItemType Directory -Path $out|Out-Null
$rows=@(foreach($r in $plan.resources){
 if((Get-FileHash -LiteralPath $r.source_json).Hash -cne $r.source_json_sha256 -or (Get-FileHash -LiteralPath $r.edited_json).Hash -cne $r.edited_json_sha256){throw 'Changed input JSON'}
 $target=Join-Path (Join-Path $plan.candidate 'archive_source') $r.depot
 if((Get-FileHash -LiteralPath $target).Hash -cne $r.source_raw_sha256){throw 'Wrong predecessor payload'}
 $dto=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],[IO.File]::ReadAllText($r.edited_json),[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
 Write-Cr2wFile $dto.Data $target
 $json=Join-Path $out (([WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($r.depot).ToString())+'.json')
 Export-Cr2wJson (Read-Cr2wFile $target) $json
 @{depot=$r.depot;raw=$target;sha256=(Get-FileHash -LiteralPath $target).Hash;json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash}
})
@{status='PE1_PRIVATE_ENTRIES_COOKED_AND_READ_BACK';resources=$rows;plan_sha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'input_02/plan.json')).Hash;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8NoBOM
Write-Output "Cooked and read back $($rows.Count) private entry resources."
