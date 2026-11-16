Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$plan = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'baseline.json') -Raw | ConvertFrom-Json -AsHashtable
$input = $plan.entry
$target = Join-Path $PSScriptRoot ('candidate_01/archive_source/' + $input.depot)
$out = Join-Path $PSScriptRoot 'candidate_01/entry_readback'
if (Test-Path -LiteralPath $out) { throw 'Fresh entry readback required' }
if ((Get-FileHash -LiteralPath $target).Hash -cne $input.before -or
    (Get-FileHash -LiteralPath $input.donor).Hash -cne $input.donor_sha256) { throw 'Entry inputs changed' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$current = Read-Cr2wFile $target
$donor = Read-Cr2wFile $input.donor
$owner = Get-QuestNode $current.RootChunk.Graph.Chunk 50
$from = Get-QuestNode $donor.RootChunk.Graph.Chunk 50
if ($owner.GetType().Name -cne 'questPhaseNodeDefinition' -or $from.GetType().Name -cne $owner.GetType().Name -or
    $owner.PhaseInstancePrefabs.Count -ne 0 -or $from.PhaseInstancePrefabs.Count -ne 1) { throw 'Unexpected entry lease' }
New-Item -ItemType Directory -Path $out | Out-Null
Export-Cr2wJson $current (Join-Path $out 'before.json')
Export-Cr2wJson $donor (Join-Path $out 'donor.json')
$owner.PhaseInstancePrefabs.Add($from.PhaseInstancePrefabs[0].DeepCopy())
Write-Cr2wFile $current $target
Export-Cr2wJson (Read-Cr2wFile $target) (Join-Path $out 'after.json')
@{
    status='COOKED_QP2_ENTRY'; before=$input.before; donor=$input.donor_sha256
    after=(Get-FileHash -LiteralPath $target).Hash
    before_json=(Get-FileHash -LiteralPath (Join-Path $out 'before.json')).Hash
    donor_json=(Get-FileHash -LiteralPath (Join-Path $out 'donor.json')).Hash
    after_json=(Get-FileHash -LiteralPath (Join-Path $out 'after.json')).Hash
    owner=50; prefab=$from.PhaseInstancePrefabs[0].PrefabNodeRef.ToString()
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $out 'result.json') -Encoding utf8NoBOM
Write-Output 'Cooked the current U9 entry with the reviewed native trigger lease.'
