Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')

$out = Join-Path $PSScriptRoot 'candidate_01'
$readback = Join-Path $out 'truck'
if (Test-Path -LiteralPath $readback) { throw 'Fresh truck readback required' }
$pins = (Get-Content -LiteralPath (Join-Path $out 'inputs.json') -Raw | ConvertFrom-Json).truck
$target = Join-Path (Join-Path $out 'archive_source') $pins.before.depot
if ((Get-FileHash -LiteralPath $target).Hash -cne $pins.before.sha256 -or
    (Get-FileHash -LiteralPath $pins.stock.raw).Hash -cne $pins.stock.sha256) { throw 'Truck scene baseline drift' }

function SceneNodes($file) {
    $nodes = @{}
    foreach ($node in $file.RootChunk.SceneGraph.Chunk.Graph) { $nodes.Add([int]$node.Chunk.NodeId.Id.ToString(), $node.Chunk) }
    return $nodes
}
$current = Read-Cr2wFile $target
$nodes = SceneNodes $current
$stock = SceneNodes (Read-Cr2wFile $pins.stock.raw)
$return = $nodes[618].OutputSockets[0]
$wait = $stock[507].OutputSockets[0].Destinations[0]
if ($return.Destinations.Count -ne 0 -or $wait.NodeId.Id.ToString() -cne '210' -or
    $wait.IsockStamp.Ordinal.ToString() -cne '1') { throw 'Unexpected return-stage socket' }
# Keep the clothes reaction and Return to Kirk update, then resume the native exit wait.
$return.Destinations.Add($wait.DeepCopy())
Write-Cr2wFile $current $target
New-Item -ItemType Directory -Path $readback | Out-Null
Export-Cr2wJson (Read-Cr2wFile $target) (Join-Path $readback 'scene.json')
Write-Output "Truck scene SHA256 $((Get-FileHash -LiteralPath $target).Hash)"
