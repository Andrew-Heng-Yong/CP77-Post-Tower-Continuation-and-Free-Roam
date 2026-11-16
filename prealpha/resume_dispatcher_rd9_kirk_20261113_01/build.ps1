# Replace the distance operand of the two existing resume waits.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$pins = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/inputs.json') | ConvertFrom-Json -AsHashtable
$source = $pins.root.raw
if ((Get-FileHash -LiteralPath $source).Hash -cne $pins.root.raw_sha256) { throw 'Root input drift' }
$out = Join-Path $PSScriptRoot 'graph_01'
if (Test-Path -LiteralPath $out) { throw 'Fresh output required' }
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$resource = Read-Cr2wFile $source
$graph = $resource.RootChunk.Graph.Chunk
foreach ($id in 61013,61014) {
    $condition = (Get-QuestNode $graph $id).Condition.Chunk
    if ($condition.Operation.ToString() -cne 'AND' -or $condition.Conditions[0].Chunk.GetType().Name -cne 'questDistanceCondition' -or
        $condition.Conditions[0].Chunk.Type.Chunk.DistanceDefinition2.Chunk.DistanceValue.ToString() -cne '50') {
        throw "Unexpected distance gate at $id"
    }
    $distance = New-FactCondition $pins.fact 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)
    $handleType = $condition.Conditions.GetType().GetGenericArguments()[0]
    $condition.Conditions[0] = New-RedHandle $handleType $distance
}
$path = Join-Path $out 'root.questphase'
Write-Cr2wFile $resource $path
Export-Cr2wJson (Read-Cr2wFile $path) ($path + '.json')
@{path=$path; sha256=(Get-FileHash -LiteralPath $path).Hash; export_sha256=(Get-FileHash -LiteralPath ($path+'.json')).Hash} |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
