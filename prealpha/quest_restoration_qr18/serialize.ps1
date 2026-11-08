Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$plan = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'proposal_01/plan.json') -Raw | ConvertFrom-Json
$output = Join-Path $PSScriptRoot 'serialized_01'
if (Test-Path -LiteralPath $output) { throw 'Fresh output required' }
$resource = @($plan.resources)[0]
if ($resource.depot -cne 'towercontinued\sidejobs_s23\base_b\mq037.questphase' -or
    (Get-FileHash -LiteralPath $resource.proposed_json).Hash -cne $resource.proposed_json_sha256) {
    throw 'Unapproved graph input'
}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
New-Item -ItemType Directory -Path $output | Out-Null
$raw = Join-Path $output 'mq037.questphase'
$json = $raw + '.json'
$dto = [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize(
    [WolvenKit.Common.Conversion.RedFileDto], [IO.File]::ReadAllText($resource.proposed_json),
    [WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
Write-Cr2wFile $dto.Data $raw
Export-Cr2wJson (Read-Cr2wFile $raw) $json
@{
    depot = $resource.depot
    raw = $raw
    sha256 = (Get-FileHash -LiteralPath $raw).Hash
    readback = $json
    readback_sha256 = (Get-FileHash -LiteralPath $json).Hash
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $output 'manifest.json') -Encoding utf8NoBOM
