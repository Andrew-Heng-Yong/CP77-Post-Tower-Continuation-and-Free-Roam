param([int[]]$Groups,[ValidateSet('01','02')][string]$Revision='01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$C=Join-Path $PSScriptRoot 'candidate_01'
if(-not $Groups){$Groups=@(Get-ChildItem $C -Filter "owner_*_qualified_${Revision}.json"|ForEach-Object {[int]($_.Name.Split('_')[1])})}
foreach($group in $Groups){
 $inputPath=Join-Path $C "owner_${group}_qualified_${Revision}.json"
 $outputPath=Join-Path $C "source/towercontinued/world_actions_wa2/group_${group}_action.questphase"
 $readback=Join-Path $C "owner_${group}_readback_${Revision}.json"
 if(Test-Path $readback){continue}
 if(Test-Path $outputPath){
  if($Revision -ne '02'){throw 'Unexpected existing resource'}
  $rejected=Join-Path $C "rejected_vehicle_v1/group_${group}_action.questphase"
  [void][IO.Directory]::CreateDirectory((Split-Path $rejected -Parent))
  if(Test-Path $rejected){throw 'Preserve rejected evidence'}
  Move-Item -LiteralPath $outputPath -Destination $rejected
 }
 $opt=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
 $dto=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],[IO.File]::ReadAllText($inputPath),$opt)
 $file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$dto.Data.RootChunk
 Write-Cr2wFile $file $outputPath
 Export-Cr2wJson (Read-Cr2wFile $outputPath) $readback
 Write-Output "Cooked $group $((Get-FileHash $outputPath).Hash)"
}
