param([Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$work=(Get-Location).Path
if(Test-Path -LiteralPath $Output){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $Output|Out-Null
. (Join-Path $work 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $work 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$pins=Get-Content -Raw -LiteralPath 'prealpha/quest_restoration_qr6/groups/A01/comparison_02/source_pins.json'|ConvertFrom-Json
$rows=@();$idx=0
foreach($pin in $pins){
 if((Get-FileHash -LiteralPath $pin.binary).Hash -cne $pin.sha256){throw 'Pinned resource changed'}
 $json=Join-Path $Output ('resource_'+$idx+'.json')
 Export-Cr2wJson (Read-Cr2wFile $pin.binary) $json
 $rows+=@{depot=$pin.depot;binary=$pin.binary;sha256=$pin.sha256;json=[IO.Path]::GetFullPath($json);json_sha256=(Get-FileHash -LiteralPath $json).Hash;scope='Fresh existing serialized-resource read; exports only, no serialization/runtime/build writes'}
 $idx+=1
}
$rows|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $Output 'manifest.json') -Encoding utf8
Write-Output ('Exported '+$rows.Count+' pinned resources')
