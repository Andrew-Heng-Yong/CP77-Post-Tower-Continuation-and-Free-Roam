# Project only the Meet Kirk admission evidence from the before and playtest saves.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$candidate = Join-Path $workspace 'prealpha/resume_dispatcher_rd8_kirk_20261113_01'
$pins = Get-Content -Raw -LiteralPath (Join-Path $candidate 'evidence_01/inputs.json') | ConvertFrom-Json -AsHashtable
$manifest = Get-Content -Raw -LiteralPath (Join-Path $candidate 'deployment_01/installed_manifest_01.json') | ConvertFrom-Json -AsHashtable
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$parser = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]
$parserHash = (Get-FileHash -LiteralPath $parser.Assembly.Location).Hash
if ($parserHash -cne 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987') { throw 'Unexpected reader' }
function Plain([string]$Path) {
    for ($item = Get-Item -LiteralPath $Path -Force; $null -ne $item;) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked path $Path" }
        $item = if ($item -is [IO.FileInfo]) { $item.Directory } else { $item.Parent }
    }
}
$names = @($pins.facts.Keys) + @(
    'PostTowerFreeRoamActive','PTFRP0_DR13','PTFRPA2_Finished','PTFRPA2_Fault',
    'q307_done','q307_finished','q307_2079','q307_main_game_killed','q307_ep1_killed',
    'q307_active','q307_debug_reset','q115_point_of_no_return','q305_johnny_scene_active',
    'PTFRPH3_Entered','PTFRPH3_Ready','PTFRS29_PHONE_kirk_Issued',
    'PTFRHS3_GateTicket','holo_kirk_calls_v_start_activate','holo_kirk_calls_v_end_activate')
$names += @('Ready','Revision','Issued','Entered','Finished','Fault','Permit','ResumeClaimed','ResumePhoneReleased','ResumePermit' |
    ForEach-Object { $pins.tag + $_ })
$toHash = @([WolvenKit.RED4.Save.Fact].GetMethods() | Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32]})[0]
$factKeys = @{}
foreach ($name in $names) {
    $fact = [WolvenKit.RED4.Save.Fact]::op_Implicit([string]$name)
    $key = [uint32]$toHash.Invoke($null, [object[]]@($fact))
    if ($factKeys.ContainsKey($key)) { throw "Selected fact collision $name" }
    $factKeys[$key] = $name
}
$journalKeys = @{}
foreach ($row in $pins.journals) {
    $key = [WolvenKit.Core.Murmur3.Murmur32]::Hash($row.path, [uint32]0x5EEDBA5E, [Text.Encoding]::UTF8)
    if ($journalKeys.ContainsKey($key)) { throw "Selected journal collision $($row.path)" }
    $journalKeys[$key] = $row.path
}
function PhaseKey([uint16[]]$Words) {
    $hash = if ($Words[0] -eq 0) { [uint64]2166136261 } elseif ($Words[0] -eq 1) { [uint64]0x01800013 }
    else { throw 'Unknown root seed' }
    foreach ($word in $Words) {
        $hash = (($hash -bxor ($word -band 255)) * 16777619) -band 4294967295
        $hash = (($hash -bxor ($word -shr 8)) * 16777619) -band 4294967295
    }
    [uint32]$hash
}
function QuestHandlers($Quest, $FactsNode, $Bytes) {
    $catalog = @($Quest.Children | Where-Object Name -CEQ 'customArray')
    $events = @($Quest.Children | Where-Object Name -CEQ 'eventManager')
    if ($catalog.Count -ne 1 -or $events.Count -ne 1) { throw 'Ambiguous owner stores' }
    $stream = [IO.MemoryStream]::new($Bytes, $false)
    $binary = [IO.BinaryReader]::new($stream)
    $settings = $null
    $decompressed = $null
    try {
        $decompressed = [WolvenKit.RED4.Save.Compression]::Decompress($binary, [ref]$settings)
        $view = [IO.BinaryReader]::new($decompressed, [Text.Encoding]::UTF8, $true)
        try {
            $decompressed.Position = $FactsNode.Offset + $FactsNode.Size
            $gapLength = $catalog[0].Offset - $decompressed.Position
            if ($gapLength -ne 17 -or [Convert]::ToHexString($view.ReadBytes(17)) -cne '026B577A51814903CAE118A84B9942C8C4') {
                throw 'Unmatched root resource array'
            }
            foreach ($node in @($catalog[0], $events[0])) {
                $decompressed.Position = $node.Offset
                if ($view.ReadInt32() -ne $node.Id) { throw 'Wrong component ID' }
                $stride = if ($node.Name -ceq 'customArray') { 2 } else { 16 }
                $count = $view.ReadUInt32()
                if ($count -ne $node.Value.Unknown.Count -or 8 + $stride * $count -ne $node.Size) { throw 'Owner store framing drift' }
            }
        } finally { $view.Dispose() }
    } finally {
        if ($null -ne $decompressed) { $decompressed.Dispose() }
        $binary.Dispose()
    }
    $words = $catalog[0].Value.Unknown
    $paths = @{}
    $selected = @{}
    for ($at = 0; $at -lt $words.Count;) {
        $length = [int]$words[$at]
        $at++
        if ($length -lt 1 -or $length -gt $words.Count - $at) { throw 'Invalid path length' }
        $route = [uint16[]]::new($length)
        for ($i = 0; $i -lt $length; $i++) { $route[$i] = $words[$at + $i] }
        $at += $length
        $key = PhaseKey $route
        $routeString = $route -join '/'
        if (!$paths.ContainsKey($key)) { $paths[$key] = [Collections.Generic.HashSet[string]]::new() }
        [void]$paths[$key].Add($routeString)
        if ($route[0] -eq 1 -and ($route -contains 40866 -or $route -contains 17376)) { $selected[$key] = $routeString }
    }
    foreach ($key in $selected.Keys) {
        if ($paths[$key].Count -ne 1) { throw 'Ambiguous saved phase hash' }
    }
    $handlers = @(foreach ($row in $events[0].Value.Unknown) {
        if ($row.Unknown1 -and $row.Unknown3 -ne 65535 -and $selected.ContainsKey($row.Unknown2)) {
            @{ route = $selected[$row.Unknown2]; node = [int]$row.Unknown3; type_token = [string]$row.Unknown1 }
        }
    })
    return @{ paths = @($selected.Values | Sort-Object); handlers = $handlers }
}
$results = @(foreach ($slot in 'ManualSave-27','AutoSave-8') {
    $source = Join-Path $manifest.save_root "$slot/sav.dat"
    $meta = Join-Path $manifest.save_root "$slot/metadata.9.json"
    Plain $source
    Plain $meta
    $before = (Get-FileHash -LiteralPath $source).Hash
    $metaBefore = (Get-FileHash -LiteralPath $meta).Hash
    $bytes = [IO.File]::ReadAllBytes($source)
    if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $before) { throw 'Input drift' }
    $data = (Get-Content -Raw -LiteralPath $meta | ConvertFrom-Json).Data.metadata
    $memory = [IO.MemoryStream]::new($bytes, $false)
    $reader = $parser::new($memory)
    try {
        $save = $null
        if ($reader.ReadFile([ref]$save).ToString() -cne 'NoError') { throw 'Save parse failed' }
        $root = @($save.Nodes | Where-Object Name -ceq 'questSystem')
        $journal = @($save.Nodes | Where-Object Name -ceq 'JournalManager')
        if ($root.Count -ne 1 -or $journal.Count -ne 1) { throw 'Ambiguous save nodes' }
        $db = @($root[0].Children | Where-Object Name -ceq 'FactsDB')
        if ($db.Count -ne 1 -or $db[0].Children.Count -ne 10) { throw 'Unexpected facts stores' }
        $values = [ordered]@{}
        foreach ($name in $names) { $values[$name] = $null }
        foreach ($entry in $db[0].Children[0].Value.FactEntries) {
            $key = [uint32]$toHash.Invoke($null, [object[]]@($entry.FactName))
            if (!$factKeys.ContainsKey($key)) { continue }
            $name = $factKeys[$key]
            if ($null -ne $values[$name]) { throw "Duplicate named fact $name" }
            $values[$name] = [uint32]$entry.Value
        }
        $journalRows = @(foreach ($entry in $journal[0].Value.Entries) {
            $raw = [byte[]]$entry.UnkownBytes
            if ($raw.Length -ne 15) { throw 'Unexpected journal format' }
            $key = [BitConverter]::ToUInt32($raw, 0)
            if ($journalKeys.ContainsKey($key)) {
                @{ path = $journalKeys[$key]; state_u32 = [BitConverter]::ToUInt32($raw, 4); raw15 = [Convert]::ToHexString($raw) }
            }
        })
        if ((Get-FileHash -LiteralPath $source).Hash -cne $before -or (Get-FileHash -LiteralPath $meta).Hash -cne $metaBefore) {
            throw 'Save changed during read'
        }
        $owner = QuestHandlers $root[0] $db[0] $bytes
        @{ slot = $slot; sha256 = $before; metadata_sha256 = $metaBefore; facts = $values; journals = $journalRows; owner = $owner;
            tracked = $data.trackedQuestEntry; life_path = $data.lifePath; location = $data.locationName;
            time = $data.timestampString; play_time = $data.playthroughTime; visit = $data.visitID }
    } finally {
        $reader.Dispose()
        $memory.Dispose()
    }
})
Plain $PSScriptRoot
$output = Join-Path $PSScriptRoot 'saved_stage_and_handlers_02.json'
$stream = [IO.File]::Open($output, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
try {
    $body = @{ parser_sha256 = $parserHash; saves = $results; save_writes = 0 } | ConvertTo-Json -Depth 8
    $stream.Write([Text.Encoding]::UTF8.GetBytes($body))
} finally { $stream.Dispose() }
