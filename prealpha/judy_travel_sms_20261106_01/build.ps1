Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$serialized = Join-Path $PSScriptRoot 'serialized_01'
if (Test-Path -LiteralPath $serialized) { throw 'Fresh serialized output required' }
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')

$depotRoot = 'base\quest\side_quests\sq030\phases'
$pins = [ordered]@{
    'sq030'             = '42417C9BDB93A595476433A2C875292E0062A5BD65377F6AF7A51A161A2400C9'
    'sq030_msg_left_01' = '320F74E69A032CAA639B4DF01DA15495AA7CCF70D8111279BC4A237764A537E6'
    'sq030_msg_left_02' = 'FB99752F6D9E4E87DA44874F11DB923BF205A2B108A2D0BC4B095E9E361C4179'
    'sq030_msg_left_03' = '723722CB1338AB19760FC50DED123754F290D3329B2C8EC6E494884C408BDC44'
}
$guard = [ordered]@{
    PostTowerFreeRoamActive = 1
    PTFRP0_DR13 = 1
    q307_active = 0
    q307_done = 1
    q307_finished = 1
    q307_2079 = 1
}
$phases = @(
    @{ name = 'sq030_msg_left_01'; boundaries = @(0, 2, 7, 8, 15, 16); expiry = 26 },
    @{ name = 'sq030_msg_left_02'; boundaries = @(0); expiry = $null },
    @{ name = 'sq030_msg_left_03'; boundaries = @(0, 2, 6, 7, 19, 20, 30, 31); expiry = 11 }
)

$installed = Get-Content -LiteralPath (Join-Path $ws 'prealpha/quest_restoration_qr19/deployment_01/installed_manifest_01.json') -Raw | ConvertFrom-Json
if ($installed.core_epoch -cne 'QR19') { throw 'Unexpected installed baseline' }
$gameArchive = Join-Path $installed.game_root 'archive/pc'
$cache = Join-Path $ws 'diagnostics/vanilla_parity_20261029_01/pass_02/raw/basegame_4_gamedata'
$nativeArchive = Join-Path $gameArchive 'content/basegame_4_gamedata.archive'
$hs = [WolvenKit.Common.Services.HashService]::new()
$hs.Load()
$keys = @{}
foreach ($name in $pins.Keys) {
    $depot = "$depotRoot\$name.questphase"
    $key = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
    $keys.Add($key, $name)
    if ((Get-FileHash -LiteralPath (Join-Path $cache $depot)).Hash -cne $pins[$name]) {
        throw "Native cache pin differs: $depot"
    }
}
$providers = @{}
$archives = @(Get-ChildItem -LiteralPath $gameArchive -Filter '*.archive' -Recurse -File)
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
foreach ($archive in $archives) {
    $parsed = $null
    if ($reader.ReadArchive($archive.FullName, $hs, [ref]$parsed).ToString() -cne 'NoError') {
        throw "Unreadable provider: $archive"
    }
    foreach ($key in $keys.Keys) {
        if (!$parsed.Files.ContainsKey([uint64]$key)) { continue }
        $name = $keys[$key]
        if ($archive.FullName -ine $nativeArchive -or $providers.ContainsKey($name)) {
            throw "Unexpected provider for ${name}: $archive"
        }
        $memory = [IO.MemoryStream]::new()
        try {
            $parsed.Files[[uint64]$key].Extract($memory)
            $digest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray()))
        } finally { $memory.Dispose() }
        if ($digest -cne $pins[$name]) { throw "Native provider pin differs: $name" }
        $providers.Add($name, @{ archive = $archive.FullName; key = $key.ToString(); sha256 = $digest })
    }
}
if ($providers.Count -ne $pins.Count) { throw 'Missing native phase provider' }
$xlFiles = @(Get-ChildItem -LiteralPath $gameArchive -Filter '*.xl' -Recurse -File)
foreach ($xl in $xlFiles) {
    if ([IO.File]::ReadAllText($xl.FullName) -match 'sq030_msg_left_0[123]\.questphase') {
        throw "Review external registration before adding local node IDs: $xl"
    }
}

function New-TowerGuard {
    $all = [WolvenKit.RED4.Types.questLogicalCondition]::new()
    $all.Operation = [WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
    foreach ($fact in $guard.Keys) {
        $condition = New-FactCondition $fact $guard[$fact] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)
        Add-RedHandle -Array $all.Conditions -Chunk $condition
    }
    return $all
}

New-Item -ItemType Directory -Path $serialized | Out-Null
$rows = foreach ($phase in $phases) {
    $depot = "$depotRoot\$($phase.name).questphase"
    $resource = Read-Cr2wFile (Join-Path $cache $depot)
    $graph = $resource.RootChunk.Graph.Chunk
    foreach ($id in $phase.boundaries) {
        $source = Get-QuestSocket (Get-QuestNode $graph $id) 'Out'
        if (!$source.Connections.Count) { throw "Missing native boundary at $id in $depot" }
        $gate = New-ConditionNode (100 + $id) (New-TowerGuard)
        Add-RedHandle -Array $graph.Nodes -Chunk $gate
        $allow = Get-QuestSocket $gate 'False'

        # Keep each destination and both ends of each existing connection.
        foreach ($handle in $source.Connections) {
            $connection = $handle.Chunk
            if (![object]::ReferenceEquals($connection.Source.Chunk, $source)) {
                throw "Unexpected connection orientation at $id in $depot"
            }
            Set-RedHandleProperty -Owner $connection -PropertyName 'Source' -Chunk $allow
            Add-RedHandle -Array $allow.Connections -Chunk $connection
        }
        $source.Connections.Clear()
        [void](Connect-QuestSockets $source (Get-QuestSocket $gate 'In'))

        # Entry can end before touching the journal. A started exchange uses
        # its native timeout cleanup, which closes only active reply groups.
        $exit = if ($id -eq 0) { 1 } else { $phase.expiry }
        [void](Connect-QuestSockets (Get-QuestSocket $gate 'True') (Get-QuestSocket (Get-QuestNode $graph $exit) 'In'))
    }
    $raw = Join-Path $serialized (Split-Path -Leaf $depot)
    Write-Cr2wFile $resource $raw
    Export-Cr2wJson (Read-Cr2wFile $raw) ($raw + '.json')
    @{
        depot = $depot
        sha256 = (Get-FileHash -LiteralPath $raw).Hash
        readback_sha256 = (Get-FileHash -LiteralPath ($raw + '.json')).Hash
    }
}
@{
    resources = @($rows)
    providers = $providers
    archives_scanned = $archives.Count
    xl_files_scanned = $xlFiles.Count
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $serialized 'manifest.json') -Encoding utf8NoBOM
