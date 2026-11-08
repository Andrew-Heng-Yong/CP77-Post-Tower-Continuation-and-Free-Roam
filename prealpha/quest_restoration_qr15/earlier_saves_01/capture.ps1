param([Parameter(Mandatory)][ValidatePattern('^capture_[0-9]{2}$')][string]$OutputName,
      [ValidateSet('before_tomorrow','remaining_leads','positive_wait')][string]$Group='before_tomorrow')
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = (Get-Item -LiteralPath (Join-Path $PSScriptRoot '../../..')).FullName
$output = Join-Path $PSScriptRoot $OutputName
if (Test-Path -LiteralPath $output) { throw 'Use a fresh output directory' }

function Assert-UnlinkedPath([string]$Path) {
    $item = Get-Item -LiteralPath $Path
    while ($null -ne $item) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked path refused: $Path" }
        $item = if ($item -is [IO.DirectoryInfo]) { $item.Parent } else { $item.Directory }
    }
}

function Assert-Hash([string]$Path, [string]$Expected) {
    if ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -cne $Expected) { throw "Pinned input changed: $Path" }
}

function Get-SingleNode($Nodes, [string]$Name) {
    $foundNodes = @($Nodes | Where-Object Name -CEQ $Name)
    if ($foundNodes.Count -ne 1) { throw "Ambiguous or absent $Name" }
    return $foundNodes[0]
}

function Get-NameHash([string]$Name) {
    $value = [uint64]2166136261
    foreach ($byte in [Text.Encoding]::UTF8.GetBytes($Name)) {
        $value = (($value -bxor $byte) * 16777619) -band [uint64]4294967295
    }
    return [uint32]$value
}

Assert-UnlinkedPath $PSScriptRoot
$inventoryPath = Join-Path $workspace 'prealpha/quest_restoration_qr12/analysis_final_02/verified_fixture_inventory.json'
$inventoryHash = '8046C8E580AD007AED9E94A6655B08BBB1955A8569A974EC95FBA15E1950AB81'
Assert-UnlinkedPath $inventoryPath
Assert-Hash $inventoryPath $inventoryHash
$inventory = Get-Content -LiteralPath $inventoryPath -Raw | ConvertFrom-Json
$selected = if ($Group -ceq 'before_tomorrow') {
    @(
        @{name='manual09'; slot='ManualSave-9'; kind='GAME_SAVE'; stamp='16:53:43, 8.10.2026'},
        @{name='backup03'; slot='AutoSave-3'; kind='OFFLINE_BACKUP'; stamp='13:41:31, 12.10.2026'; backup='recovery/pre_alpha_clean_20261013T022533186Z/save'},
        @{name='backup14'; slot='AutoSave-14'; kind='OFFLINE_BACKUP'; stamp='21:17:46, 12.10.2026'; backup='recovery/pre_alpha_clean_20261013T022533186Z/save'}
    )
} elseif ($Group -ceq 'remaining_leads') {
    @(
        @{name='ponr00'; slot='PointOfNoReturnSave-0'; kind='GAME_SAVE'; stamp='22:25:24, 6.09.2026'},
        @{name='ponr01'; slot='PointOfNoReturnSave-1'; kind='GAME_SAVE'; stamp='19:10:50, 20.09.2026'},
        @{name='wa1backup08'; slot='AutoSave-8'; kind='OFFLINE_BACKUP'; stamp='00:58:30, 26.10.2026'; backup='recovery/world_combat_wa1_01/autosaves_before_test'},
        @{name='wa1backup16'; slot='AutoSave-16'; kind='OFFLINE_BACKUP'; stamp='16:05:11, 26.10.2026'; backup='recovery/world_combat_wa1_01/autosaves_before_test'}
    )
} else {
    @(@{name='wa1backup16'; slot='AutoSave-16'; kind='OFFLINE_BACKUP'; stamp='16:05:11, 26.10.2026'; backup='recovery/world_combat_wa1_01/autosaves_before_test'})
}
$factNames = @('q307_active','q307_done','q307_finished','q307_2079','q307_ep1_killed','q307_main_game_killed',
    'sts_ep1_03_start_community','sts_ep1_03_start','sts_ep1_03_active','sts_ep1_03_done','sts_ep1_03_shard_cracked',
    'sts_ep_03_wagner_chicken_test','sts_ep_03_wagner_chicken_test_02','sa_ep1_114_toggledoff_force',
    'sa_ep1_114_toggledoff','sa_ep1_courier_allow_unrestricted_cleanup','sa_ep1_courier_spot_force_toggled_off')
$factKeys = @{}
foreach ($name in $factNames) { $factKeys[(Get-NameHash $name).ToString()] = $name }
if ($factKeys.Count -ne $factNames.Count -or (Get-NameHash 'q307_active') -ne 4269385191) { throw 'Fact name hash control failed' }

. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$readerHash = 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987'
Assert-Hash ([WolvenKit.RED4.Save.IO.CyberpunkSaveReader].Assembly.Location) $readerHash
$factConversion = @([WolvenKit.RED4.Save.Fact].GetMethods() | Where-Object { $_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32] })
if ($factConversion.Count -ne 1) { throw 'Ambiguous saved fact key conversion' }

$captures = foreach ($spec in $selected) {
    $rows = @($inventory.rows | Where-Object { $_.slot_directory -ceq $spec.slot -and $_.kind -ceq $spec.kind -and $_.metadata.timestampString -ceq $spec.stamp })
    if ($rows.Count -ne 1) { throw "Ambiguous input $($spec.name)" }
    $row = $rows[0]
    $root = if ($spec.kind -ceq 'GAME_SAVE') { 'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077' } else {
        Join-Path $workspace $spec.backup
    }
    $slot = Join-Path $root $spec.slot
    $source = [IO.Path]::GetFullPath((Join-Path $slot 'sav.dat'))
    $metadata = [IO.Path]::GetFullPath((Join-Path $slot 'metadata.9.json'))
    if ($source -ine $row.source -or $metadata -ine $row.metadata_source) { throw 'Inventory does not match the exact selected paths' }
    foreach ($path in @($source, $metadata)) { Assert-UnlinkedPath $path }
    Assert-Hash $source $row.sha256
    Assert-Hash $metadata $row.metadata_sha256
    $bytes = [IO.File]::ReadAllBytes($source)
    if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $row.sha256) { throw 'Unstable body snapshot' }

    $headerReader = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new([IO.MemoryStream]::new($bytes, $false))
    $header = $null
    try {
        if ($headerReader.ReadFileInfo([ref]$header).ToString() -cne 'NoError') { throw 'Save header read failed' }
        if ($header.SaveVersion -ne $row.metadata.saveVersion -or $header.GameVersion -ne $row.metadata.gameVersion -or
            "$($header.GameVersion)/$($header.SaveVersion)" -cnotin @('2310/269','2500/277')) { throw 'Unexpected older save version' }
    } finally { $headerReader.Dispose() }
    $saveReader = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new([IO.MemoryStream]::new($bytes, $false))
    $save = $null
    try {
        if ($saveReader.ReadFile([ref]$save).ToString() -cne 'NoError') { throw 'Save parser failed' }
        $quest = Get-SingleNode $save.Nodes 'questSystem'
        $facts = Get-SingleNode $quest.Children 'FactsDB'
        $paths = Get-SingleNode $quest.Children 'customArray'
        $events = Get-SingleNode $quest.Children 'eventManager'
        $nodesForOffsets = @($quest,$facts,$paths,$events) + @($facts.Children)
        if ($Group -ceq 'positive_wait') {
            $queued = Get-SingleNode $quest.Children 'QueuedData'
            $nodesForOffsets += @($queued)
        }
        if ($facts.Children.Count -ne 10 -or $facts.Children[0].Value -isnot [WolvenKit.RED4.Save.FactsTable]) { throw 'Unexpected physical fact table layout' }
        $knownFacts = @{}
        foreach ($record in $facts.Children[0].Value.FactEntries) {
            $key = ([uint32]$factConversion[0].Invoke($null,[object[]]@($record.FactName))).ToString()
            if ($factKeys.ContainsKey($key)) {
                $name = $factKeys[$key]
                if ($knownFacts.ContainsKey($name)) { throw "Duplicate named fact key for $name" }
                $knownFacts[$name] = [uint32]$record.Value
            }
        }
        $expectedActive = $row.saved_parse.facts.PSObject.Properties['q307_active']
        if ($null -eq $expectedActive -or @($expectedActive.Value).Count -eq 0) {
            if ($knownFacts.ContainsKey('q307_active')) { throw 'Unexpected q307_active record' }
        } elseif (@($expectedActive.Value).Count -ne 1 -or !$knownFacts.ContainsKey('q307_active') -or
                  $knownFacts['q307_active'] -ne $expectedActive.Value[0].value_u32) { throw 'Named-fact positive control failed' }

        $binary = [IO.BinaryReader]::new([IO.MemoryStream]::new($bytes, $false))
        $settings = $null
        try {
            $decompressed = [WolvenKit.RED4.Save.Compression]::Decompress($binary, [ref]$settings)
            $view = [IO.BinaryReader]::new($decompressed)
            try {
                foreach ($node in $nodesForOffsets) {
                    $decompressed.Position = $node.Offset
                    if ($view.ReadInt32() -ne $node.Id) { throw "Offset/ID mismatch for $($node.Name)" }
                }
                $start = [long]$facts.Offset + $facts.Size
                $length = [long]$paths.Offset - $start
                if ($length -le 0 -or $length -gt 513 -or $length -ne $facts.TrailingSize) { throw 'Unexpected saved resource array span' }
                $decompressed.Position = $start
                $gap = $view.ReadBytes([int]$length)
                if ($gap.Length -ne $length) { throw 'Truncated saved resource array' }
                $components = @{}
                foreach ($node in @($paths,$events)) {
                    if ($node.Children.Count -ne 0 -or $node.TrailingSize -ne 0 -or $node.Size -ne $node.DataSize -or $node.Size -lt 8 -or $node.Size -gt 1048576) { throw 'Unexpected component span' }
                    $decompressed.Position = $node.Offset
                    $raw = $view.ReadBytes($node.Size)
                    $count = [BitConverter]::ToUInt32($raw,4)
                    $stride = if ($node.Name -ceq 'customArray') { 2 } else { 16 }
                    if ($raw.Length -ne $node.Size -or (8 + [long]$stride * $count) -ne $raw.Length -or $count -ne $node.Value.Unknown.Count) { throw 'Raw/managed component length mismatch' }
                    for ($i=0; $i -lt $count; $i++) {
                        $at = 8 + $i * $stride
                        $entry = $node.Value.Unknown[$i]
                        if ($stride -eq 2) {
                            if ([BitConverter]::ToUInt16($raw,$at) -ne $entry) { throw 'Path word mismatch' }
                        } elseif ([BitConverter]::ToUInt64($raw,$at) -ne $entry.Unknown1 -or [BitConverter]::ToUInt32($raw,$at+8) -ne $entry.Unknown2 -or
                                  [BitConverter]::ToUInt16($raw,$at+12) -ne $entry.Unknown3 -or [BitConverter]::ToUInt16($raw,$at+14) -ne $entry.Unknown4) { throw 'Event record mismatch' }
                    }
                    $components[$node.Name] = @{id=$node.Id; offset=$node.Offset; bytes=$raw.Length; count=$count; base64=[Convert]::ToBase64String($raw)}
                }
                if ($Group -ceq 'positive_wait') {
                    if ($queued.Children.Count -ne 0 -or $queued.TrailingSize -ne 0 -or $queued.Size -ne $queued.DataSize -or
                        $queued.Size -lt 9 -or $queued.Size -gt 1048576) { throw 'Unexpected QueuedData span' }
                    $decompressed.Position = $queued.Offset
                    $raw = $view.ReadBytes($queued.Size)
                    if ($raw.Length -ne $queued.Size) { throw 'Truncated QueuedData' }
                    $components['QueuedData'] = @{id=$queued.Id; offset=$queued.Offset; bytes=$raw.Length; base64=[Convert]::ToBase64String($raw)}
                }
            } finally { $view.Dispose() }
        } finally { $binary.Dispose() }
    } finally { $saveReader.Dispose() }
    Assert-Hash $source $row.sha256
    Assert-Hash $metadata $row.metadata_sha256
    @{
        name=$spec.name; slot=$spec.slot; kind=$spec.kind; timestamp=$spec.stamp
        source=$source; source_sha256=$row.sha256; metadata=$metadata; metadata_sha256=$row.metadata_sha256
        save_version=$header.SaveVersion; game_version=$header.GameVersion; archive_version=$header.ArchiveVersion
        named_facts=$knownFacts; named_fact_physical_ordinal=1; offset_id_checks=$nodesForOffsets.Count
        resource_array_base64=[Convert]::ToBase64String($gap); components=$components; unchanged=$true
    }
}

New-Item -ItemType Directory -Path $output | Out-Null
foreach ($row in $captures) {
    $row | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $output ($row.name + '.json')) -Encoding utf8NoBOM
}
@{status='READ_ONLY_EARLIER_SAVE_CAPTURE'; group=$Group; bodies=@($captures).Count; reader_sha256=$readerHash; inventory_sha256=$inventoryHash; output=$output; save_writes=0; game_calls=0} | ConvertTo-Json
