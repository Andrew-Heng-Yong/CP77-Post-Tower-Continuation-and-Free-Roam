param(
    [Parameter(Mandatory)][string]$CatalogueFile,
    [Parameter(Mandatory)][string]$Output
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$cataloguePath = [IO.Path]::GetFullPath($CatalogueFile)
$outputPath = [IO.Path]::GetFullPath($Output)
$taskPrefix = [IO.Path]::GetFullPath($PSScriptRoot) + [IO.Path]::DirectorySeparatorChar
if (-not $cataloguePath.StartsWith($taskPrefix, [StringComparison]::OrdinalIgnoreCase) -or
    -not $outputPath.StartsWith($taskPrefix, [StringComparison]::OrdinalIgnoreCase) -or
    (Test-Path -LiteralPath $outputPath) -or -not (Test-Path -LiteralPath ([IO.Path]::GetDirectoryName($outputPath)) -PathType Container)) {
    throw 'Catalogue and fresh output must stay under this task directory'
}
$catalogue = Get-Content -LiteralPath $cataloguePath -Raw | ConvertFrom-Json
if ($catalogue.status -cne 'EXACT_INSTALLED_SOURCE_CATALOGUE' -or $catalogue.entry_count -ne 161) {
    throw 'Unexpected selected journal catalogue'
}

. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$parserHash = (Get-FileHash -LiteralPath ([WolvenKit.RED4.Save.IO.CyberpunkSaveReader].Assembly.Location) -Algorithm SHA256).Hash
if ($parserHash -cne 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987') {
    throw 'Save reader bytes changed'
}

$wanted = @{}
foreach ($entry in $catalogue.entries) {
    foreach ($journal in $entry.journals) {
        $hash = [WolvenKit.Core.Murmur3.Murmur32]::Hash([string]$journal.path, [uint32]0x5EEDBA5E, [Text.Encoding]::UTF8)
        if ($wanted.ContainsKey($hash) -and $wanted[$hash].path -cne $journal.path) {
            throw "Selected journal hash collision: $($journal.path)"
        }
        $wanted[$hash] = @{path=[string]$journal.path; class=[string]$journal.class}
    }
}
if ($wanted.Count -ne $catalogue.unique_journal_paths) { throw 'Journal catalogue count mismatch' }

function Read-Slot([string]$slot) {
    $root = 'C:/Users/Ayong/Saved Games/CD Projekt Red/Cyberpunk 2077'
    $folder = Join-Path $root $slot
    $savePath = Join-Path $folder 'sav.dat'
    $metadataPath = Join-Path $folder 'metadata.9.json'
    foreach ($path in @($folder, $savePath, $metadataPath)) {
        $item = Get-Item -LiteralPath $path -ErrorAction Stop
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked save input: $slot" }
    }
    $saveHash = (Get-FileHash -LiteralPath $savePath -Algorithm SHA256).Hash
    $metadataHash = (Get-FileHash -LiteralPath $metadataPath -Algorithm SHA256).Hash
    $metadata = (Get-Content -LiteralPath $metadataPath -Raw | ConvertFrom-Json).Data.metadata
    $bytes = [IO.File]::ReadAllBytes($savePath)
    if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $saveHash) {
        throw "Save changed during memory copy: $slot"
    }
    $memory = [IO.MemoryStream]::new($bytes, $false)
    $reader = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($memory)
    try {
        $save = $null
        if ($reader.ReadFile([ref]$save).ToString() -cne 'NoError' -or $save.FileHeader.SaveVersion -ne 277) {
            throw "Unsupported save parse/version: $slot"
        }
        $managers = @($save.Nodes | Where-Object Name -CEQ 'JournalManager')
        if ($managers.Count -ne 1) { throw "Ambiguous JournalManager: $slot" }
        $found = @{}
        foreach ($record in $managers[0].Value.Entries) {
            $raw = [byte[]]$record.UnkownBytes
            if ($raw.Length -ne 15) { throw "Journal framing drift: $slot" }
            $hash = [BitConverter]::ToUInt32($raw, 0)
            if ($wanted.ContainsKey($hash)) {
                if ($found.ContainsKey($hash)) { throw "Duplicate selected journal hash: $slot/$hash" }
                $found[$hash] = @{
                    path=$wanted[$hash].path
                    class=$wanted[$hash].class
                    state_u32=[BitConverter]::ToUInt32($raw, 4)
                    raw15=[Convert]::ToHexString($raw)
                }
            }
        }
        $rows = @($found.Values | Sort-Object path)
        $counts = @($rows | Group-Object class,state_u32 | Sort-Object Name | ForEach-Object {
            @{name=$_.Name; count=$_.Count}
        })
        return @{
            slot=$slot
            save_sha256=$saveHash
            metadata_sha256=$metadataHash
            timestamp=$metadata.timestampString
            playthrough_id=$metadata.playthroughID
            point_of_no_return_id=$metadata.pointOfNoReturnId
            is_end_game_save=$metadata.isEndGameSave
            parsed_selected_paths=$rows.Count
            counts=$counts
            journal=$rows
        }
    } finally {
        $reader.Dispose()
        $memory.Dispose()
        if ((Get-FileHash -LiteralPath $savePath -Algorithm SHA256).Hash -cne $saveHash -or
            (Get-FileHash -LiteralPath $metadataPath -Algorithm SHA256).Hash -cne $metadataHash) {
            throw "Save input changed during read: $slot"
        }
    }
}

$before = Read-Slot 'ManualSave-31'
$after = Read-Slot 'EndGameSave-92'
if ($before.playthrough_id -cne $after.playthrough_id -or
    $before.point_of_no_return_id -cne $after.point_of_no_return_id -or
    $before.is_end_game_save -or -not $after.is_end_game_save) {
    throw 'Save metadata does not establish the selected before/after lineage'
}
$result = [ordered]@{
    status='READ_ONLY_SELECTED_JOURNAL_PROJECTION'
    parser_sha256=$parserHash
    catalogue_sha256=(Get-FileHash -LiteralPath $cataloguePath -Algorithm SHA256).Hash
    selected_entries=161
    map_pin_paths=$catalogue.map_pin_paths
    saves=@($before,$after)
    limits=@(
        'EndGameSave-92 was written after credits before the 21:06 post-Tower load; its journal is not a post-Ready observation.',
        'Absent journal rows are unknown, not inferred Inactive.',
        'Journal map-pin state does not prove marker registration or rendered map icons.',
        'Matching playthrough and point-of-no-return metadata does not by itself prove every individual quest history.'
    )
    save_writes=0
    game_api_calls=0
}
[IO.File]::WriteAllText($outputPath, ($result | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
Write-Output "Read $($before.parsed_selected_paths) selected journal paths in ManualSave-31 and $($after.parsed_selected_paths) in EndGameSave-92."
