Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $PSScriptRoot 'evidence_01'
if(Test-Path -LiteralPath $out){throw 'Use fresh pilot context evidence'}
$capture=Get-Content -LiteralPath (Join-Path $workspace 'prealpha/johnny_dialogue_removal_20261107_01/step1_01/capture.json') -Raw | ConvertFrom-Json -Depth 100
$depots=@(
    'towercontinued\sidejobs_s29\entries\sq023_hit_order.questphase',
    'towercontinued\sidejobs_s29\native\base\quest\side_quests\sq023\sq023.questphase',
    'towercontinued\sidejobs_s29\native\base\quest\side_quests\sq023\phases\sq023_restaurant.questphase'
)
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
New-Item -ItemType Directory -Path $out | Out-Null
$rows=@(foreach($depot in $depots){
    $source=@($capture.resources | Where-Object {$_.depot -ceq $depot -and $_.archive -like '*zzzz_PTFR_Combined.archive'})
    if($source.Count -ne 1){throw "Expected one exact private source $depot"}
    $source=$source[0]
    if((Get-FileHash -LiteralPath $source.raw).Hash -cne $source.sha256){throw 'Pinned source changed'}
    $json=Join-Path $out ($source.key+'.json')
    Export-Cr2wJson (Read-Cr2wFile $source.raw) $json
    @{depot=$depot;archive=$source.archive;key=$source.key;raw=$source.raw;sha256=$source.sha256;
      json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash}
})
@{resources=$rows;game_writes=0;save_writes=0} | ConvertTo-Json -Depth 12 |
    Set-Content -LiteralPath (Join-Path $out 'sources.json') -Encoding utf8NoBOM
Write-Output "Exported $($rows.Count) exact private caller resources for the pilot"
