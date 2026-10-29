Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$path=Join-Path $PSScriptRoot 'extract_01/ep1_1_nightcity_10971083935992963809.streamingsector'
$f=Read-Cr2wFile $path
$f.RootChunk.GetType().GetProperties().Name|ConvertTo-Json
foreach($name in @('NodeRanges','Variants','NodeDataRanges','NodeRefs')){
 if($f.RootChunk.PSObject.Properties.Name -contains $name){
  $v=$f.RootChunk.$name
  Write-Output $name
  if($name -ne 'NodeRefs'){$v|Format-List|Out-String|Write-Output}
 }
}
