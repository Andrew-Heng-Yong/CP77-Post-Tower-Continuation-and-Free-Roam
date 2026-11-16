Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$inventory=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'inventory_01.json') -Raw|ConvertFrom-Json -Depth 100
$out=Join-Path $PSScriptRoot 'fresh_01'
if(Test-Path -LiteralPath $out){throw 'Fresh export output required'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
New-Item -ItemType Directory -Path $out|Out-Null
$rows=@(foreach($row in $inventory.fresh_exports){
 if((Get-FileHash -LiteralPath $row.raw).Hash -cne $row.sha256){throw 'Pinned source changed'}
 $key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($row.depot).ToString()
 $json=Join-Path $out ($key+'.json')
 Export-Cr2wJson (Read-Cr2wFile $row.raw) $json
 @{depot=$row.depot;sha256=$row.sha256;raw=$row.raw;json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash}
})
@{status='CURRENT_MISSING_MODELS_EXPORTED';resources=$rows;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8NoBOM
Write-Output "Exported $($rows.Count) current phase resources."
