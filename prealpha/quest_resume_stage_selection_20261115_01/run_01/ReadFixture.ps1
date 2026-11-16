param([Parameter(Mandatory)][string]$Directory)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$output = Get-Item -LiteralPath $Directory
if ($output.Parent.FullName -cne (Split-Path $PSScriptRoot -Parent) -or $output.Name -cnotmatch '^run_[0-9]{2}$' -or
    (Get-ChildItem -LiteralPath $output.FullName -File | Where-Object Name -cnotin @('selection.json','ReadFixture.ps1'))) {
    throw 'Use a fresh fixture-search directory'
}
$workspace = Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$parser = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]
if ((Get-FileHash -LiteralPath $parser.Assembly.Location).Hash -cne 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987') {
    throw 'Unexpected save reader'
}

function Single($Nodes, [string]$Name) {
    $found = @($Nodes | Where-Object Name -ceq $Name)
    if ($found.Count -ne 1) { throw "Ambiguous or missing node $Name" }
    $found[0]
}
function Read-Span($View, $Node) {
    if ($Node.Size -lt 4 -or $Node.Size -gt 1048576 -or $Node.Children.Count -ne 0) {
        throw "Unsupported span $($Node.Name)"
    }
    $View.BaseStream.Position = $Node.Offset
    $raw = $View.ReadBytes($Node.Size)
    if ($raw.Length -ne $Node.Size -or [BitConverter]::ToInt32($raw, 0) -ne $Node.Id) {
        throw "Unexpected framing at $($Node.Name)"
    }
    return ,$raw
}

$selection = Get-Content -LiteralPath (Join-Path $output.FullName 'selection.json') -Raw | ConvertFrom-Json
$phaseKeys = [Collections.Generic.HashSet[uint32]]::new()
$journalKeys = [Collections.Generic.HashSet[uint32]]::new()
foreach ($hash in $selection.phase_hashes) { [void]$phaseKeys.Add([uint32]$hash) }
foreach ($hash in $selection.journal_hashes) { [void]$journalKeys.Add([uint32]$hash) }
$factKeys = @{}
$factNames = @('q307_done', 'q307_finished', 'q307_2079', 'q307_main_game_killed', 'q307_ep1_killed',
    'q307_point_of_no_return', 'q115_point_of_no_return', 'q307_active', 'q307_ready', 'q307_visited_rooftop') + @($selection.fact_names)
$toHash = @([WolvenKit.RED4.Save.Fact].GetMethods() | Where-Object {
    $_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32]
})[0]
foreach ($name in $factNames) {
    $fact = [WolvenKit.RED4.Save.Fact]::op_Implicit([string]$name)
    $factKeys.Add([uint32]$toHash.Invoke($null, [object[]]@($fact)), $name)
}

function Read-Fixture($File, [hashtable]$Result) {
    $bytes = [IO.File]::ReadAllBytes($File.FullName)
    $Result.sha256 = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
    $stream = [IO.MemoryStream]::new($bytes, $false)
    $reader = $parser::new($stream)
    try {
        $save = $null
        $status = $reader.ReadFile([ref]$save).ToString()
        if ($status -cne 'NoError') { throw "Save reader status $status" }
        $Result.version = $save.FileHeader.SaveVersion
        if ($Result.version -notin @(269, 277)) { throw 'Unsupported save version' }
        $root = Single $save.Nodes 'questSystem'
        $facts = Single $root.Children 'FactsDB'
        if ($facts.Children.Count -ne 10) { throw 'Unexpected fact stores' }
        $recorded = [ordered]@{}
        foreach ($name in $factNames) { $recorded[$name] = $null }
        foreach ($entry in $facts.Children[0].Value.FactEntries) {
            $key = [uint32]$toHash.Invoke($null, [object[]]@($entry.FactName))
            if ($factKeys.ContainsKey($key)) { $recorded[$factKeys[$key]] = [uint32]$entry.Value }
        }
        $Result.facts = $recorded
        $eventNode = Single $root.Children 'eventManager'
        $events = $eventNode.Value.Unknown
        $members = @(for ($slot = 0; $slot -lt $events.Count; ++$slot) {
            $row = $events[$slot]
            if ($phaseKeys.Contains([uint32]$row.Unknown2) -and $row.Unknown4 -eq 0) {
                ,@($slot, $row.Unknown1.ToString('x16'), $row.Unknown2, $row.Unknown3)
            }
        })
        $Result.phase_registrations = $members
        $journal = Single $save.Nodes 'JournalManager'
        $journalRows = @{}
        foreach ($row in $journal.Value.Entries) {
            $raw = [byte[]]$row.UnkownBytes
            if ($raw.Length -ne 15) { throw 'Unexpected journal row' }
            $key = [BitConverter]::ToUInt32($raw, 0)
            if ($journalKeys.Contains($key)) {
                if (!$journalRows.ContainsKey($key)) { $journalRows[$key] = [Collections.Generic.List[uint32]]::new() }
                $journalRows[$key].Add([BitConverter]::ToUInt32($raw, 4))
            }
        }
        $Result.journal = @(foreach ($key in $journalRows.Keys) { ,@($key, $journalRows[$key].ToArray()) })

        $paths = Single $root.Children 'customArray'
        $delay = Single $save.Nodes 'DelaySystem'
        $time = Single $save.Nodes 'TimeSystem'
        $nodes = [ordered]@{
            paths = $paths
            instances = Single $root.Children 'nodeInstanceDataManager'
            delay_structs = Single $delay.Children '"DelayedStructs"'
            time_core = Single $time.Children '"Core"'
            time_timers = Single $time.Children '"Timers"'
        }
        $binary = [IO.BinaryReader]::new([IO.MemoryStream]::new($bytes, $false))
        $settings = $null
        $decoded = $null
        try {
            $decoded = [WolvenKit.RED4.Save.Compression]::Decompress($binary, [ref]$settings)
            $view = [IO.BinaryReader]::new($decoded, [Text.Encoding]::UTF8, $true)
            try {
                $gapSize = $paths.Offset - ($facts.Offset + $facts.Size)
                if ($gapSize -le 0 -or $gapSize -gt 128) { throw 'Unexpected root array extent' }
                $decoded.Position = $facts.Offset + $facts.Size
                $Result.root_array = [Convert]::ToHexString($view.ReadBytes($gapSize))
                $eventBytes = Read-Span $view $eventNode
                if ($eventBytes.Length -ne (8 + 16 * $events.Count) -or
                    [BitConverter]::ToUInt32($eventBytes, 4) -ne $events.Count) { throw 'Unexpected event framing' }
                foreach ($item in $members) {
                    $i = 8 + 16 * $item[0]
                    if ([BitConverter]::ToUInt64($eventBytes, $i).ToString('x16') -cne $item[1] -or
                        [BitConverter]::ToUInt32($eventBytes, $i+8) -ne $item[2] -or
                        [BitConverter]::ToUInt32($eventBytes, $i+12) -ne $item[3]) { throw 'Event table mismatch' }
                }
                $Result.components = [ordered]@{}
                foreach ($key in $nodes.Keys) {
                    $node = $nodes[$key]
                    $raw = Read-Span $view $node
                    $Result.components[$key] = @{ id = $node.Id; size = $node.Size; hex = [Convert]::ToHexString($raw) }
                }
                $Result.decision = 'read_for_binding'
            } finally { $view.Dispose() }
        } finally {
            if ($decoded) { $decoded.Dispose() }
            $binary.Dispose()
        }
    } finally { $reader.Dispose(); $stream.Dispose() }
}

$saveRoot = 'C:/Users/Ayong/Saved Games/CD Projekt Red/Cyberpunk 2077'
foreach ($folder in Get-ChildItem -LiteralPath $saveRoot -Directory) {
    if ($folder.Name -cnotmatch '^(?:ManualSave-(?:26|29|30|31)|AutoSave-(?:6|13|14|15|17))$' -or
        ($selection.slots.Count -and $folder.Name -cnotin $selection.slots) -or
        ($folder.Attributes -band [IO.FileAttributes]::ReparsePoint)) { continue }
    $file = Get-Item -LiteralPath (Join-Path $folder.FullName 'sav.dat') -ErrorAction SilentlyContinue
    if (!$file -or ($file.Attributes -band [IO.FileAttributes]::ReparsePoint)) { continue }
    $result = @{ slot = $folder.Name }
    try { Read-Fixture $file $result } catch {
        $result.decision = 'schema_deferred'
        $result.binding_error = $_.Exception.Message
        $result.Remove('components')
    }
    if (!$result.ContainsKey('sha256') -or (Get-FileHash -LiteralPath $file.FullName).Hash -cne $result.sha256) {
        throw "Source changed during capture: $($folder.Name)"
    }
    $result | ConvertTo-Json -Depth 8 |
        Set-Content -LiteralPath (Join-Path $output.FullName "$($folder.Name).json") -Encoding utf8NoBOM
}
