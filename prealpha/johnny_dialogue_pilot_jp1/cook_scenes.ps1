param([ValidatePattern('^[A-F0-9]{64}$')][Parameter(Mandatory)][string]$PlanSHA)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$planPath=Join-Path $PSScriptRoot 'input_03/plan.json'
if((Get-FileHash -LiteralPath $planPath).Hash -cne $PlanSHA){throw 'Plan changed'}
$plan=Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json -Depth 100
if($plan.epoch -cne 'JP1' -or $plan.revision -cne '03' -or $plan.edits.Count -ne 3){throw 'Unexpected pilot plan'}
$out=Join-Path $PSScriptRoot 'readback_03'
if(Test-Path -LiteralPath $out){throw 'Fresh readback output required'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
New-Item -ItemType Directory -Path $out | Out-Null
$rows=@(foreach($edit in $plan.edits){
    if((Get-FileHash -LiteralPath $edit.edited_json).Hash -cne $edit.edited_json_sha256){throw 'Edited scene input changed'}
    $opt=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
    $dto=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],[IO.File]::ReadAllText($edit.edited_json),$opt)
    if($dto.Data.EmbeddedFiles.Count -ne 0){throw 'Embedded scene resources need explicit preservation review'}
    $file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new()
    $file.RootChunk=$dto.Data.RootChunk
    $target=Join-Path (Join-Path $plan.candidate_directory 'archive_source') $edit.resource.depot
    if((Get-FileHash -LiteralPath $target).Hash -cne $edit.resource.raw_sha256){throw 'Wrong candidate predecessor payload'}
    Write-Cr2wFile $file $target
    $json=Join-Path $out ($edit.resource.resource_id+'.json')
    Export-Cr2wJson (Read-Cr2wFile $target) $json
    @{depot=$edit.resource.depot;resource_id=$edit.resource.resource_id;path=$target;sha256=(Get-FileHash -LiteralPath $target).Hash;
      readback=$json;readback_sha256=(Get-FileHash -LiteralPath $json).Hash}
})
@{status='JP1_THREE_SCENES_COOKED_AND_READ_BACK';plan_sha256=$PlanSHA;resources=$rows;game_writes=0;save_writes=0} |
    ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $out 'cooked.json') -Encoding utf8NoBOM
Write-Output "Cooked and read back $($rows.Count) private pilot scenes"
