Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$plan = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'proposal_01/plan.json') -Raw | ConvertFrom-Json
$output = Join-Path $PSScriptRoot 'serialized_01'
if (Test-Path -LiteralPath $output) { throw 'Fresh output required' }
$allowed = @(
    'towercontinued\sidejobs_s29\entries\mq018_writer.questphase',
    'towercontinued\sidejobs_s29\native\base\quest\minor_quests\mq018\mq018.questphase',
    'towercontinued\sidejobs_s29\native\base\quest\minor_quests\mq018\phases\mq018_01_msgs.questphase'
)
if ((@($plan.resources.depot | Sort-Object) -join '|') -cne (($allowed | Sort-Object) -join '|')) { throw 'Unexpected resource set' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
New-Item -ItemType Directory -Path $output | Out-Null
$rows = foreach ($resource in $plan.resources) {
    if ((Get-FileHash -LiteralPath $resource.proposed_json).Hash -cne $resource.proposed_json_sha256) {
        throw 'Changed proposal'
    }
    $raw = Join-Path $output (Split-Path -Leaf $resource.depot)
    $json = $raw + '.json'
    $dto = [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize(
        [WolvenKit.Common.Conversion.RedFileDto], [IO.File]::ReadAllText($resource.proposed_json),
        [WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
    Write-Cr2wFile $dto.Data $raw
    Export-Cr2wJson (Read-Cr2wFile $raw) $json
    @{
        depot = $resource.depot; raw = $raw; sha256 = (Get-FileHash -LiteralPath $raw).Hash
        readback = $json; readback_sha256 = (Get-FileHash -LiteralPath $json).Hash
    }
}
@{resources = @($rows)} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $output 'manifest.json') -Encoding utf8NoBOM
