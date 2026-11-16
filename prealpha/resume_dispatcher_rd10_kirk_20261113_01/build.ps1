# The saved Meet Kirk stage already passed the fresh quest's content-token gate.
# Use the stock content-lock condition for the guarded post-Tower continuation.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$pins = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/inputs.json') | ConvertFrom-Json -AsHashtable
if ((Get-FileHash -LiteralPath $pins.root.path).Hash -cne $pins.root.sha256) { throw 'Root input drift' }
$out = Join-Path $PSScriptRoot 'graph_01'
if (Test-Path -LiteralPath $out) { throw 'Fresh output required' }
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$donorPath = Join-Path $pins.archive_source $pins.donor.depot
if ((Get-FileHash -LiteralPath $donorPath).Hash -cne $pins.donor.sha256) { throw 'Content-lock donor drift' }
$donor = Read-Cr2wFile $donorPath
$lock = (Get-QuestNode $donor.RootChunk.Graph.Chunk 43).Condition.Chunk
if ($lock.GetType().Name -cne 'questContentCondition' -or $lock.Type.Chunk.GetType().Name -cne 'questContentLock_ConditionType' -or
    $lock.Type.Chunk.IsContentBlocked.ToString() -cne 'False') { throw 'Unexpected content-lock condition' }
$resource = Read-Cr2wFile $pins.root.path
$graph = $resource.RootChunk.Graph.Chunk
foreach ($id in 61013,61014) {
    $condition = (Get-QuestNode $graph $id).Condition.Chunk
    $operand = $condition.Conditions[1].Chunk.Type.Chunk
    if ($condition.Operation.ToString() -cne 'AND' -or $operand.GetType().Name -cne 'questContentToken_ConditionType' -or
        $operand.Type.ToString() -cne 'MinorQuestAndSts') { throw "Unexpected content gate at $id" }
    $handleType = $condition.Conditions.GetType().GetGenericArguments()[0]
    $condition.Conditions[1] = New-RedHandle $handleType ($lock.DeepCopy())
}
$path = Join-Path $out 'root.questphase'
Write-Cr2wFile $resource $path
Export-Cr2wJson (Read-Cr2wFile $path) ($path + '.json')
@{path=$path; sha256=(Get-FileHash -LiteralPath $path).Hash; export_sha256=(Get-FileHash -LiteralPath ($path+'.json')).Hash} |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
