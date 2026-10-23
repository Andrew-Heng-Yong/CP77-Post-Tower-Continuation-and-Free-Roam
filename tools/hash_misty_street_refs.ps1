param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$plan=Get-Content (Join-Path $audit 'street_selection_plan.json') -Raw|ConvertFrom-Json
$refs=[ordered]@{}
foreach($row in $plan.source_ranges){
 if($row.selected.Count -eq 0){continue}
 $path=Join-Path $WorkspaceRoot ($row.raw_path.Replace('\raw\','\json\')+'.json')
 $world=Get-Content -LiteralPath $path -Raw|ConvertFrom-Json -Depth 100
 $data=@($world.Data.RootChunk.nodeData.Data)
 foreach($item in $row.selected){
  $ref=$data[[int]$item.data_index].UkHash1
  if($null -ne $ref -and $ref.'$storage' -eq 'string'){
   $name=$ref.'$value'
   if(-not $refs.Contains($name)){$refs[$name]=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($name)}
  }
 }
}
if($refs.Count -ne 7){throw "Expected seven qualified sub-prefab refs, found $($refs.Count)"}
[IO.File]::WriteAllText((Join-Path $audit 'street_ref_hashes.json'),($refs|ConvertTo-Json -Depth 2))
$refs.Count
