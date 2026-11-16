# Read exact installed providers and emit an unregistered quest-phase entrance.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$out = Join-Path $PSScriptRoot 'graph_03'
if (Test-Path -LiteralPath $out) { throw 'Fresh output required' }
$pins = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'evidence_02/inputs.json') | ConvertFrom-Json -AsHashtable
$specPath = Join-Path $PSScriptRoot 'entrance.json'
if ((Get-FileHash -LiteralPath $specPath).Hash -cne $pins.entrance_sha256) { throw 'Entrance plan drift' }
$spec = Get-Content -Raw -LiteralPath $specPath | ConvertFrom-Json -AsHashtable
$installed = Join-Path $pins.game 'archive/pc/mod/zzzz_PTFR_Combined.archive'
if ((Get-FileHash -LiteralPath $installed).Hash -cne $pins.archive_sha256) { throw 'Installed archive drift' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$names = [WolvenKit.Common.Services.HashService]::new()
$names.Load()

$watch = @{}
foreach ($pin in $pins.resources) {
    $key = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($pin.depot)
    if ($key -ne [uint64]$pin.key -or $watch.ContainsKey($key)) { throw 'Provider key drift' }
    $watch[$key] = $pin
}
$private = @{}
$sourceIds = @($spec.resources.Values | ForEach-Object { $_.rid })
foreach ($part in $spec.resources.Keys) {
    $depot = $spec.prefix + $part + '.questphase'
    $key = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
    if ($private.ContainsKey($key) -or $watch.ContainsKey($key)) { throw 'Planned key collision' }
    $private[$key] = $depot
}

[void][IO.Directory]::CreateDirectory($out)
$seen = [Collections.Generic.HashSet[uint64]]::new()
$archives = 0
$roots = @((Join-Path $pins.game 'archive/pc'), (Join-Path $pins.game 'mods')) | Where-Object { Test-Path -LiteralPath $_ }
foreach ($root in $roots) {
    $rootItem = Get-Item -LiteralPath $root
    if (($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
        @(Get-ChildItem -LiteralPath $root -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked archive tree' }
    foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.archive') {
        $stamp = @($file.Length, $file.LastWriteTimeUtc.Ticks)
        $archive = $null
        $status = ([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName, $names, [ref]$archive)
        if ($status.ToString() -cne 'NoError') { throw "Unreadable archive $file" }
        foreach ($key in $private.Keys) {
            if ($archive.Files.ContainsKey($key)) { throw "Private depot already provided $($private[$key])" }
        }
        foreach ($key in $watch.Keys) {
            if (!$archive.Files.ContainsKey($key)) { continue }
            $pin = $watch[$key]
            if ($pin.archive -ine $file.FullName -or !$seen.Add($key)) { throw "Unexpected provider for $($pin.depot)" }
            $memory = [IO.MemoryStream]::new()
            try { $archive.Files[$key].Extract($memory); $bytes = $memory.ToArray() } finally { $memory.Dispose() }
            if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $pin.sha256) {
                throw "Provider drift for $($pin.depot)"
            }
            if ($pin.rid -in $sourceIds) { [IO.File]::WriteAllBytes((Join-Path $out "$($pin.rid).original.questphase"), $bytes) }
        }
        $file.Refresh()
        if ($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1]) { throw "Archive changed during scan $file" }
        $archives++
    }
}
if ($seen.Count -ne $watch.Count) { throw 'Missing provider' }

function Add-Node($Graph, $Node) {
    if (@($Graph.Nodes | Where-Object { $_.Chunk.Id.ToString() -eq $Node.Id.ToString() }).Count) { throw 'Occupied graph ID' }
    Add-RedHandle $Graph.Nodes $Node
}

function Copy-NestedConnections($SourceGraph, $CopyGraph) {
    $endpoints = [Collections.Generic.Dictionary[object, object]]::new([Collections.Generic.ReferenceEqualityComparer]::Instance)
    foreach ($handle in $SourceGraph.Nodes) {
        $sourceNode = $handle.Chunk
        $copyNode = Get-QuestNode $CopyGraph ([int]$sourceNode.Id.ToString())
        foreach ($socket in $sourceNode.Sockets) {
            $copySocket = Get-QuestSocket $copyNode $socket.Chunk.Name.ToString()
            $copySocket.Connections.Clear()
            $endpoints.Add($socket.Chunk, $copySocket)
        }
    }
    foreach ($sourceSocket in $endpoints.Keys) {
        foreach ($handle in $sourceSocket.Connections) {
            $edge = $handle.Chunk
            if ([object]::ReferenceEquals($edge.Source.Chunk, $sourceSocket)) {
                [void](Connect-QuestSockets $endpoints[$sourceSocket] $endpoints[$edge.Destination.Chunk])
            }
        }
    }
}

$results = foreach ($part in $spec.resources.Keys) {
    $edit = $spec.resources[$part]
    $sourceFile = Join-Path $out "$($edit.rid).original.questphase"
    $body = Read-Cr2wFile $sourceFile
    $graph = $body.RootChunk.Graph.Chunk
    Add-Node $graph (New-InputNode $edit.entry $spec.socket)
    if ($edit.Contains('calls')) {
        foreach ($call in $edit.calls) {
            $node = Get-QuestNode $graph $call[0]
            $node.PhaseResource = [WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($spec.prefix + $call[1] + '.questphase')
            [void](New-QuestSocket $node $spec.socket ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
            # External phase wrappers list the callable input in the local shell as well.
            Add-Node $node.PhaseGraph.Chunk (New-InputNode $edit.shell_entry $spec.socket)
        }
    }
    if ($edit.Contains('clones')) {
        foreach ($clone in $edit.clones) {
            $sourceNode = Get-QuestNode $graph $clone[0]
            $node = $sourceNode.DeepCopy()
            foreach ($socket in $node.Sockets) { $socket.Chunk.Connections.Clear() }
            if ($sourceNode -is [WolvenKit.RED4.Types.questPhaseNodeDefinition]) {
                Copy-NestedConnections $sourceNode.PhaseGraph.Chunk $node.PhaseGraph.Chunk
            }
            $node.Id = [uint16]$clone[1]
            Add-Node $graph $node
        }
    }
    foreach ($edge in $edit.edges) {
        [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $edge[0]) $edge[1]) (Get-QuestSocket (Get-QuestNode $graph $edge[2]) $edge[3]))
    }
    $file = Join-Path $out ($part + '.questphase')
    Write-Cr2wFile $body $file
    Export-Cr2wJson (Read-Cr2wFile $file) ($file + '.json')
    @{
        name = $part
        depot = $spec.prefix + $part + '.questphase'
        source_sha256 = (Get-FileHash -LiteralPath $sourceFile).Hash
        raw_sha256 = (Get-FileHash -LiteralPath $file).Hash
        export_sha256 = (Get-FileHash -LiteralPath ($file + '.json')).Hash
    }
}

@{ status = 'UNREGISTERED_GRAPH_READBACK'; scanned_archives = $archives; pinned_providers = $seen.Count; resources = @($results) } |
    ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
Write-Output "Serialized $($results.Count) private phases with $($seen.Count) providers checked across $archives archives."
