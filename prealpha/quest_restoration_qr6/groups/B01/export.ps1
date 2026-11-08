param([Parameter(Mandatory=$true)][ValidateSet('B01','B02','B03')][string]$Group,[string]$InputName='',[string]$OutputName='raw_exports_01')
$ErrorActionPreference='Stop'
$ws=(Get-Location).Path
$dir=Join-Path $ws ('prealpha/quest_restoration_qr6/groups/'+$Group)
$out=Join-Path $dir $OutputName
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $out|Out-Null
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$inputFile=if(Test-Path -LiteralPath (Join-Path $dir 'scoped_inputs_02.json')){Join-Path $dir 'scoped_inputs_02.json'}else{Join-Path $dir 'raw_inputs.json'}
if($InputName){$inputFile=Join-Path $dir $InputName}
$inputs=Get-Content -Raw -LiteralPath $inputFile|ConvertFrom-Json
$rows=@();$idx=0
foreach($row in $inputs){
 if((Get-FileHash -LiteralPath $row.raw).Hash -cne $row.hash){throw 'Pinned raw changed'}
 $json=Join-Path $out ('resource_'+$idx+'.json')
 try{
  Export-Cr2wJson (Read-Cr2wFile $row.raw) $json
  $rows+=@{depot=$row.depot;raw=$row.raw;raw_sha256=$row.hash;provider=$row.provider;json=[IO.Path]::GetFullPath($json);json_sha256=(Get-FileHash -LiteralPath $json).Hash;status='EXPORTED'}
 }catch{$rows+=@{depot=$row.depot;raw=$row.raw;raw_sha256=$row.hash;provider=$row.provider;status='OPAQUE';error=$_.Exception.Message}}
 $idx++
}
$rows|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8
Write-Output ($Group+' readback exports '+$rows.Count)
