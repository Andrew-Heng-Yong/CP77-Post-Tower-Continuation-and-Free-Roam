param([string]$OutputName = 'saved_01.json', [string]$SavePinsName = '', [switch]$CaptureGraph)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($OutputName -cnotmatch '^[a-z][a-z0-9_]+\.json$') { throw 'Use a simple fresh JSON output name' }
$output = Join-Path $PSScriptRoot $OutputName
if (Test-Path -LiteralPath $output) { throw 'Fresh output required' }
$workspace = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$readerHash = (Get-FileHash -LiteralPath ([WolvenKit.RED4.Save.PersistencySystem2].Assembly.Location)).Hash
if ($readerHash -cne 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987') { throw 'Pinned save reader drift' }
$pinsHash = $null
if ($SavePinsName) {
    if ($SavePinsName -cnotmatch '^[a-z][a-z0-9_]+\.json$') { throw 'Use a simple JSON pins filename' }
    $pinsPath = Join-Path $PSScriptRoot $SavePinsName
    $pinsHash = (Get-FileHash -LiteralPath $pinsPath).Hash
    $pins = @(Get-Content -Raw -LiteralPath $pinsPath | ConvertFrom-Json)
    if ($pins.Count -lt 1 -or $pins.Count -gt 4) { throw 'Expected one to four pinned save bodies' }
} else {
    $post = Get-Content -Raw -LiteralPath (Join-Path $workspace 'prealpha/quest_restoration_qr15/lifecycle_01/save_community/capture_01/capture.json') | ConvertFrom-Json
    $prior = Get-Content -Raw -LiteralPath (Join-Path $workspace 'prealpha/quest_restoration_qr15/earlier_saves_01/analysis_02/result.json') | ConvertFrom-Json -Depth 80
    $earlier = @($prior.earlier_bodies | Where-Object name -ceq wa1backup16)
    if ($earlier.Count -ne 1) { throw 'Earlier pinned save missing' }
    $pins = @($earlier[0], $post)
}
$candidateKeys = @{
    '4332298668526107917' = 'door placement raw ID'
    '12853314834284644214' = 'door placement + native controller PS2 key'
    '17573531461158215226' = 'door placement + Component PS2 key'
    '5071238858877156917' = 'keypad placement raw ID'
    '9989375000956130078' = 'keypad placement + native controller PS2 key'
    '17097965322572148530' = 'keypad placement + Component PS2 key'
    '7120437687000861668' = 'stash shell placement raw ID'
    '16080207676021322947' = 'stash shell placement + native controller PS2 key'
    '16339985917071610199' = 'stash shell placement + Component PS2 key'
    '10192301459743777947' = 'loot container placement raw ID'
    '1076966674056833684' = 'loot container placement + Component PS2 key'
}
$names = @(
    'q304_05_slider_stash_info_downloaded', '941229',
    'PTFRS23_VOODOO_Ready','PTFRS23_VOODOO_Permit','PTFRS23_VOODOO_Issued',
    'PTFRS23_VOODOO_Entered','PTFRS23_VOODOO_Finished','PTFRS23_VOODOO_Fault'
)
$factHash = @([WolvenKit.RED4.Save.Fact].GetMethods() | Where-Object { $_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32] })
if ($factHash.Count -ne 1) { throw 'Fact hash method ambiguous' }
$wanted = @{}
foreach ($name in $names) {
    $id = [uint32]$factHash[0].Invoke($null, [object[]]@([WolvenKit.RED4.Save.Fact]::op_Implicit([string]$name)))
    if ($wanted.ContainsKey($id)) { throw 'Selected fact hash collision' }
    $wanted[$id] = $name
}
$rewardIds = @{'118124605694' = 'Rook'; '127255451537' = 'stash shard'; '51369838828' = 'money'}
$itemHash = @([WolvenKit.RED4.Types.TweakDBID].GetMethods() | Where-Object { $_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint64] })
if ($itemHash.Count -ne 1) { throw 'Item ID conversion ambiguous' }

function Read-GraphComponents($Save, [byte[]]$Bytes) {
    $quest = @($Save.Nodes | Where-Object Name -ceq 'questSystem')
    if ($quest.Count -ne 1) { throw 'Ambiguous quest system root' }
    $quest = $quest[0]
    $binary = [IO.BinaryReader]::new([IO.MemoryStream]::new($Bytes, $false))
    $decompressed = $null
    try {
        $settings = $null
        $decompressed = [WolvenKit.RED4.Save.Compression]::Decompress($binary, [ref]$settings)
        $view = [IO.BinaryReader]::new($decompressed, [Text.Encoding]::UTF8, $true)
        try {
            $components = @{}
            foreach ($name in @('customArray','eventManager','questPhaseFreezer')) {
                $nodes = @($quest.Children | Where-Object Name -ceq $name)
                if ($nodes.Count -ne 1) { throw "Ambiguous graph component $name" }
                $node = $nodes[0]
                if ($node.Children.Count -or $node.TrailingSize -or $node.Size -ne $node.DataSize -or
                    $node.Size -lt 8 -or $node.Size -gt 1048576 -or ([long]$node.Offset + $node.Size) -gt $decompressed.Length) {
                    throw "Unexpected graph component span $name"
                }
                $decompressed.Position = $node.Offset
                $raw = $view.ReadBytes($node.Size)
                if ($raw.Length -ne $node.Size -or [BitConverter]::ToInt32($raw,0) -ne $node.Id) {
                    throw "Graph component offset mismatch $name"
                }
                $components[$name] = @{id = $node.Id; size = $node.Size; base64 = [Convert]::ToBase64String($raw)}
            }
            return $components
        } finally { $view.Dispose() }
    } finally {
        if ($null -ne $decompressed) { $decompressed.Dispose() }
        $binary.Dispose()
    }
}

$outputRows = foreach ($pin in $pins) {
    foreach ($path in @($pin.source, $pin.metadata)) {
        $item = Get-Item -LiteralPath $path
        while ($null -ne $item) {
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked source path refused' }
            $item = if ($item -is [IO.DirectoryInfo]) { $item.Parent } else { $item.Directory }
        }
    }
    if ((Get-FileHash -LiteralPath $pin.metadata).Hash -cne $pin.metadata_sha256) { throw 'Pinned metadata drift' }
    $bytes = [IO.File]::ReadAllBytes($pin.source)
    if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $pin.source_sha256) { throw 'Pinned save drift' }
    $memory = [IO.MemoryStream]::new($bytes, $false)
    $reader = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($memory)
    try {
        $save = $null
        if ($reader.ReadFile([ref]$save).ToString() -ne 'NoError') { throw 'Save read failed' }
        $facts = [Collections.Generic.List[object]]::new()
        $psMatches = [Collections.Generic.List[object]]::new()
        $inventoryMatches = [Collections.Generic.List[object]]::new()
        $rewardMatches = [Collections.Generic.List[object]]::new()
        $stack = [Collections.Generic.Stack[object]]::new()
        foreach ($node in $save.Nodes) { $stack.Push(@{node = $node; path = $node.Name}) }
        $counts = @{facts = 0; ps2 = 0; inventory = 0}
        $properties = [WolvenKit.RED4.Types.RedBaseClass].GetField('_properties', [Reflection.BindingFlags]'Instance,NonPublic')
        while ($stack.Count -gt 0) {
            $current = $stack.Pop()
            $node = $current.node
            if ($node.Value -is [WolvenKit.RED4.Save.FactsTable]) {
                $counts.facts++
                foreach ($fact in $node.Value.FactEntries) {
                    $hash = [uint32]$factHash[0].Invoke($null, [object[]]@($fact.FactName))
                    if ($wanted.ContainsKey($hash)) { $facts.Add(@{name = $wanted[$hash]; hash = $hash; value = $fact.Value; table = $current.path}) }
                }
            }
            if ($node.Value -is [WolvenKit.RED4.Save.PersistencySystem2]) {
                foreach ($entry in $node.Value.Entries) {
                    $counts.ps2++
                    $id = $entry.Id.ToString()
                    if (-not $candidateKeys.ContainsKey($id)) { continue }
                    $class = if ($null -eq $entry.Data) { 'NULL' } else { $entry.Data.GetType().Name }
                    $fields = @{}
                    if ($null -ne $entry.Data) {
                        $dictionary = $properties.GetValue($entry.Data)
                        foreach ($key in $dictionary.Keys) {
                            if ($key -match '(?i)open|lock|deviceState|loot|disabl|markAsQuest|started') {
                                $value = $dictionary[$key]
                                if ($null -ne $value) { $fields[$key] = $value.ToString() }
                            }
                        }
                    }
                    $psMatches.Add(@{id = $id; candidate = $candidateKeys[$id]; parsed_class = $class; parsed_properties = $fields})
                }
            }
            if ($node.Value -is [WolvenKit.RED4.Save.Inventory]) {
                foreach ($inventory in $node.Value.SubInventories) {
                    $counts.inventory++
                    $id = $inventory.InventoryId.ToString()
                    if ($candidateKeys.ContainsKey($id)) {
                        $inventoryMatches.Add(@{id = $id; candidate = $candidateKeys[$id]; item_records = $inventory.Items.Count})
                    }
                    if ($SavePinsName -and -not $CaptureGraph) {
                        foreach ($item in $inventory.Items) {
                            $key = $itemHash[0].Invoke($null, [object[]]@($item.ItemInfo.ItemId.Id)).ToString()
                            if ($rewardIds.ContainsKey($key)) {
                                $rewardMatches.Add(@{inventory_id = $id; item = $rewardIds[$key]; quantity = $item.Quantity; structure = $item.ItemInfo.ItemStructure.ToString()})
                            }
                        }
                    }
                }
            }
            foreach ($child in $node.Children) { $stack.Push(@{node = $child; path = $current.path + '/' + $child.Name}) }
        }
        if ($counts.facts -eq 0 -or $counts.ps2 -eq 0) { throw 'Expected save surfaces unavailable' }
        $graphComponents = if ($CaptureGraph) { Read-GraphComponents $save $bytes } else { $null }
        if ((Get-FileHash -LiteralPath $pin.source).Hash -cne $pin.source_sha256 -or (Get-FileHash -LiteralPath $pin.metadata).Hash -cne $pin.metadata_sha256) {
            throw 'Source changed during inspection'
        }
        @{
            source = $pin.source; sha256 = $pin.source_sha256; metadata_sha256 = $pin.metadata_sha256
            searched = $counts; fact_matches = @($facts); ps2_matches = @($psMatches)
            matching_subinventories = @($inventoryMatches); reward_records = @($rewardMatches)
            graph_components = $graphComponents; source_unchanged = $true
        }
    } finally { $reader.Dispose(); $memory.Dispose() }
}
if ($SavePinsName -and (Get-FileHash -LiteralPath $pinsPath).Hash -cne $pinsHash) { throw 'Save pins changed during inspection' }
@{reader_sha256 = $readerHash; pins_sha256 = $pinsHash; candidates = $candidateKeys; results = $outputRows; save_writes = 0; game_calls = 0} |
    ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $output -Encoding utf8NoBOM
$outputRows | ConvertTo-Json -Depth 10
