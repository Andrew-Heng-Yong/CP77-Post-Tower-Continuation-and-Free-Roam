# Serialize the private quest-phase bodies in a fresh workspace for semantic review.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out = Join-Path $PSScriptRoot 'graph_01'
if (Test-Path -LiteralPath $out) { throw 'Fresh graph output required' }
$contract = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'entrance.json') | ConvertFrom-Json -AsHashtable
$review = Get-Content -Raw -LiteralPath (Join-Path $workspace 'prealpha/resume_dispatcher_rd5_gigs_20261113_01/evidence_02/rite_route.json') | ConvertFrom-Json
$proof = Join-Path $workspace 'prealpha/resume_dispatcher_rd5_gigs_20261113_01/evidence_02/provider_readback.json'
if ((Get-FileHash -LiteralPath $proof).Hash -cne $review.provider_proof_sha256) { throw 'Provider evidence drift' }
$installed = Get-Content -Raw -LiteralPath $proof | ConvertFrom-Json
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$source = $null
$archivePath = ($review.providers | Where-Object rid -EQ 6756).archive
$manifest = Join-Path $workspace 'prealpha/resume_dispatcher_rd4_20261113_01/deployment_01/installed_manifest_01.json'
if ((Get-FileHash -LiteralPath $manifest).Hash -cne '3DDA172011D2049A0EDBC4E006E6F40AE79F8751B23FAF0BEBCDC1706A62F0BC') { throw 'Baseline drift' }
$game = (Get-Content -Raw -LiteralPath $manifest | ConvertFrom-Json).game_root
$active = Join-Path $game 'archive/pc/mod/zzzz_PTFR_Combined.archive'
if ((Get-FileHash -LiteralPath $active).Hash -cne $installed.installed_archive_sha256) { throw 'Installed archive drift' }
if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archivePath, $hashService, [ref]$source).ToString() -cne 'NoError') { throw 'Unreadable source archive' }

function Add-Node($Graph, $Node) {
  if (@($Graph.Nodes | Where-Object { $_.Chunk.Id.ToString() -eq $Node.Id.ToString() }).Count) { throw 'Occupied node ID' }
  Add-RedHandle $Graph.Nodes $Node
}
function Scope($Graph, [string]$Path) {
  foreach ($id in ($Path -split '/' | Select-Object -Skip 1)) { $Graph = (Get-QuestNode $Graph ([int]$id)).PhaseGraph.Chunk }
  return $Graph
}
function Input-Socket($Node) {
  [void](New-QuestSocket $Node $contract.socket ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
}

# These private copies keep their original graph identities and own independent deserialized handles.
New-Item -ItemType Directory -Path $out | Out-Null
$rows = foreach ($name in $contract.resources.Keys) {
  $spec = $contract.resources[$name]
  $pin = @($review.providers | Where-Object rid -EQ $spec.rid)
  if ($pin.Count -ne 1 -or $pin[0].archive -cne $archivePath) { throw 'Invalid provider pin' }
  $pin = $pin[0]
  $member = Join-Path $out ($name + '.stock.questphase')
  $file = [IO.File]::Open($member, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
  try { $source.Files[[uint64]$pin.key].Extract($file) } finally { $file.Dispose() }
  if ((Get-FileHash -LiteralPath $member).Hash -cne $pin.sha256) { throw 'Raw member drift' }
  $quest = Read-Cr2wFile $member
  foreach ($path in $spec.graphs.Keys) {
    $edit = $spec.graphs[$path]
    $graph = Scope $quest.RootChunk.Graph.Chunk $path
    Add-Node $graph (New-InputNode $edit.entry $contract.socket)
    if ($edit.Contains('clones')) {
      foreach ($clone in $edit.clones) {
        $node = (Get-QuestNode $graph $clone[0]).DeepCopy()
        foreach ($socket in $node.Sockets) { $socket.Chunk.Connections.Clear() }
        $node.Id = [uint16]$clone[1]
        Add-Node $graph $node
      }
    }
    if ($edit.Contains('exit')) {
      $exitId, $exitName, $phaseId = $edit.exit
      Add-Node $graph (New-OutputNode $exitId $exitName)
      [void](New-QuestSocket (Get-QuestNode $quest.RootChunk.Graph.Chunk $phaseId) $exitName ([WolvenKit.RED4.Types.Enums+questSocketType]::Output))
    }
    if ($edit.Contains('sockets')) {
      foreach ($id in $edit.sockets) { Input-Socket (Get-QuestNode $graph $id) }
    }
    if ($edit.Contains('calls')) {
      foreach ($call in $edit.calls) {
        $node = Get-QuestNode $graph $call[0]
        $node.PhaseResource = [WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($contract.private_prefix + $call[1] + '.questphase')
        Input-Socket $node
      }
    }
  }
  foreach ($path in $spec.graphs.Keys) {
    $edit = $spec.graphs[$path]
    if (!$edit.Contains('edges')) { continue }
    $graph = Scope $quest.RootChunk.Graph.Chunk $path
    foreach ($edge in $edit.edges) {
      [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $edge[0]) $edge[1]) (Get-QuestSocket (Get-QuestNode $graph $edge[2]) $edge[3]))
    }
  }
  $output = Join-Path $out ($name + '.questphase')
  Write-Cr2wFile $quest $output
  Export-Cr2wJson (Read-Cr2wFile $output) ($output + '.json')
  @{name=$name; original_sha256=$pin.sha256; raw_sha256=(Get-FileHash -LiteralPath $output).Hash; depot=$contract.private_prefix + $name + '.questphase'}
}
@{status='UNREGISTERED_GRAPH_READBACK'; installed_archive_sha256=$installed.installed_archive_sha256; resources=@($rows)} |
  ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
