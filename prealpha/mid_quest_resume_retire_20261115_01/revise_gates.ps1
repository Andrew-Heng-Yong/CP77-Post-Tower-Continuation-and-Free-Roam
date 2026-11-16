param([ValidatePattern('^stage_[0-9]+$')][string]$Output = 'stage_03')
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$workspace = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$archive = Join-Path $workspace 'prealpha/resume_dispatcher_rd10_kirk_20261113_01/archive_01'
$manifest = Join-Path $archive 'readback.json'
if ((Get-FileHash -LiteralPath $manifest).Hash -cne '5BBD9BB8F04AA5CC235B9845BDE691E2D6105B70E98083B36D7A8F54A3B29B81') { throw 'RD10 member inventory drift' }
$known = @{}
foreach ($row in (Get-Content -Raw -LiteralPath $manifest | ConvertFrom-Json -AsHashtable).members) { $known[$row.depot] = $row.sha256 }
$edits = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'entry_gates.json') | ConvertFrom-Json -AsHashtable
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$stage = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot $Output))
if (Test-Path -LiteralPath $stage) { throw 'Choose a fresh stage directory' }
[void][IO.Directory]::CreateDirectory($stage)

function Replace-Permit($condition, [string]$fact) {
    $type = $condition.GetType().Name
    if ($type -ceq 'questLogicalCondition') {
        $seen = 0
        foreach ($child in $condition.Conditions) { $seen += Replace-Permit $child.Chunk $fact }
        return $seen
    }
    if ($type -cne 'questFactsDBCondition') { return 0 }
    $check = $condition.Type.Chunk
    if ($check.GetType().Name -cne 'questVarComparison_ConditionType' -or $check.FactName.ToString() -cne $fact) { return 0 }
    if ($check.ComparisonType.ToString() -cne 'Equal' -or $check.Value.ToString() -cne '1') { throw "Unexpected comparison for $fact" }
    # Both the live and saved permit writers use only zero or one.
    $check.Value = [int32]2
    return 1
}

$results = foreach ($asset in ($edits | Group-Object {$_.depot})) {
    $depot = $asset.Name
    $original = Join-Path (Join-Path $archive 'source') $depot
    if ((Get-FileHash -LiteralPath $original).Hash -cne $known[$depot]) { throw "Unexpected $depot provider" }
    $resource = Read-Cr2wFile $original
    $before = Join-Path $stage ('before_' + $depot.Replace('\','_') + '.json')
    Export-Cr2wJson $resource $before
    $count = 0
    foreach ($edit in $asset.Group) {
        foreach ($id in $edit.nodes) {
            $node = Get-QuestNode $resource.RootChunk.Graph.Chunk $id
            $condition = $node.Condition.Chunk
            $changes = 0
            if ($edit.branches -eq 'all') {
                $changes = Replace-Permit $condition $edit.permit
            } else {
                if ($condition.Operation.ToString() -cne 'OR') { throw "Missing original alternatives at $depot node $id" }
                foreach ($index in $edit.branches) { $changes += Replace-Permit $condition.Conditions[$index].Chunk $edit.permit }
            }
            if (!$changes) { throw "No permit comparison at $depot node $id" }
            $count += $changes
        }
    }
    $target = Join-Path (Join-Path $stage 'revised') $depot
    [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target))
    Write-Cr2wFile $resource $target
    $after = Join-Path $stage ('after_' + $depot.Replace('\','_') + '.json')
    Export-Cr2wJson (Read-Cr2wFile $target) $after
    [ordered]@{depot=$depot;before=$before;after=$after;path=$target;sha256=(Get-FileHash -LiteralPath $target).Hash;comparisons=$count}
}
$results | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $stage 'gates.json') -Encoding utf8NoBOM
Write-Output "Serialized $($results.Count) private entry resources."
