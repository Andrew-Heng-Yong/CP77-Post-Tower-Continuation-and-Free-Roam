Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$request=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/source_inventory.json') -Raw | ConvertFrom-Json -Depth 100
$out=Join-Path $PSScriptRoot 'evidence_02'
if(Test-Path -LiteralPath $out){throw 'Use a fresh source-export revision'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
New-Item -ItemType Directory -Path $out | Out-Null
$rows=@(foreach($source in $request.phase_exports){
    if((Get-FileHash -LiteralPath $source.raw).Hash -cne $source.sha256){throw 'Pinned source changed'}
    $json=Join-Path $out ($source.export_key+'.json')
    try {
        Export-Cr2wJson (Read-Cr2wFile $source.raw) $json
        @{depot=$source.depot;archive=$source.archive;raw=$source.raw;sha256=$source.sha256;
          json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash;status='EXPORTED'}
    } catch {
        @{depot=$source.depot;archive=$source.archive;raw=$source.raw;sha256=$source.sha256;
          status='DECODE_BLOCKER';error=$_.Exception.Message}
    }
})
@{resources=$rows;game_writes=0;save_writes=0} | ConvertTo-Json -Depth 15 |
    Set-Content -LiteralPath (Join-Path $out 'sources.json') -Encoding utf8NoBOM
Write-Output "Recorded $($rows.Count) source exports for the five-quest review"
