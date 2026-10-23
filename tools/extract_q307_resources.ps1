param(
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0',
    [string]$OutputRoot = (Join-Path $PSScriptRoot '..\research\q307_extracted')
)

$ErrorActionPreference = 'Stop'

foreach ($assemblyName in @('WolvenKit.Core.dll', 'WolvenKit.Common.dll', 'WolvenKit.RED4.dll')) {
    [void][System.Reflection.Assembly]::LoadFrom((Join-Path $WolvenKitRoot $assemblyName))
}

$archivePaths = @(
    (Join-Path $GameRoot 'archive\pc\ep1\ep1_2_gamedata.archive'),
    (Join-Path $GameRoot 'archive\pc\content\basegame_4_gamedata.archive')
)
foreach ($archivePath in $archivePaths) {
    if (-not (Test-Path -LiteralPath $archivePath -PathType Leaf)) {
        throw "Archive not found: $archivePath"
    }
}

$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()

$resourcePattern = '(?i)^(ep1\\quest\\main_quests\\q307\\.*\.(questphase|quest|scene|gamedef)|ep1\\quest\\main_quests\\q305\\phases\\q305_08_border_crossing\.questphase|ep1\\quest\\main_quests\\q306\\phases\\q306_05_launchpad\.questphase|ep1\\openworld\\community\\quest_communities\\q307_despawn\.questphase|ep1\\quest\\bugfixing\\main_quests\\q307_bugfixing\.questphase|ep1\\quest\\bugfixing\\main_quests\\q304_bugfixing\.questphase|ep1\\quest\\bugfixing\\additional_content\\ep1_media_bugfixing\.questphase|ep1\\quest\\minor_quests\\mq307\\mq307_preorder_car\.questphase|ep1\\quest\\ep1\.(quest|questphase)|ep1\\quest\\ep1_persistent_content\.questphase|ep1\\quest\\main_quests\\ep1_main_quests\.questphase|ep1\\gameplay\\gui\\world\\internet\\internet_2_years_later\\internet_2_years_later\.questphase|ep1\\gameplay\\air_traffic\\phases\\ep1_air_traffic\.questphase|base\\gameplay\\air_traffic\\phases\\air_traffic(_disabling_phase)?\.questphase|base\\quest\\hiding_av_loops\.questphase|base\\quest\\main_quests\\epilogue\\final_boards\.questphase|base\\quest\\bugfixing\.questphase|base\\quest\\bugfixing\\sidequests\\sq025\\sq025_quest_bugfixes\.questphase|base\\quest\\cyberpunk2077\.questphase|base\\quest\\minor_quests\\mq056\\mq056\.questphase)$'
$entries = @(
    foreach ($archivePath in $archivePaths) {
        $archiveReader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
        $archive = $null
        $archiveResult = $archiveReader.ReadArchive($archivePath, $hashService, [ref]$archive)
        if ($archiveResult.ToString() -ne 'NoError') {
            throw "Unable to read archive $archivePath`: $archiveResult"
        }
        foreach ($entry in ($archive.Files.Values | Where-Object { $_.Name -match $resourcePattern })) {
            [pscustomobject]@{ ArchivePath = $archivePath; Entry = $entry }
        }
    }
) | Sort-Object { $_.Entry.Name }
if ($entries.Count -eq 0) {
    throw 'No matching q307 resources were found.'
}

$rawRoot = Join-Path $OutputRoot 'raw'
$jsonRoot = Join-Path $OutputRoot 'json'
New-Item -ItemType Directory -Force -Path $rawRoot, $jsonRoot | Out-Null

$inventory = foreach ($archiveEntry in $entries) {
    $entry = $archiveEntry.Entry
    $archivePath = $archiveEntry.ArchivePath
    $relativePath = $entry.Name
    $rawPath = Join-Path $rawRoot $relativePath
    $jsonPath = Join-Path $jsonRoot ($relativePath + '.json')
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $rawPath), (Split-Path -Parent $jsonPath) | Out-Null

    $memory = [System.IO.MemoryStream]::new()
    try {
        $entry.Extract($memory)
        $bytes = $memory.ToArray()
        [System.IO.File]::WriteAllBytes($rawPath, $bytes)

        $memory.Position = 0
        $resourceReader = [WolvenKit.RED4.Archive.IO.CR2WReader]::new($memory)
        $resource = $null
        $readResult = $resourceReader.ReadFile([ref]$resource, $true)
        if ($readResult.ToString() -ne 'NoError') {
            throw "Unable to decode $relativePath`: $readResult"
        }

        $dto = [WolvenKit.Common.Conversion.RedFileDto]::new($resource, $false)
        $options = [WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
        $json = [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($dto, $options)
        [System.IO.File]::WriteAllText($jsonPath, $json, [System.Text.UTF8Encoding]::new($false))

        [pscustomobject]@{
            ResourcePath = $relativePath
            Archive = $archivePath
            NameHash64 = $entry.NameHash64
            RawBytes = $bytes.Length
            Sha256 = [Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant()
            RootType = $resource.RootChunk.GetType().Name
            RawOutput = [System.IO.Path]::GetRelativePath($OutputRoot, $rawPath)
            JsonOutput = [System.IO.Path]::GetRelativePath($OutputRoot, $jsonPath)
        }
    }
    finally {
        $memory.Dispose()
    }
}

$inventory |
    ConvertTo-Json -Depth 5 |
    Set-Content -LiteralPath (Join-Path $OutputRoot 'inventory.json') -Encoding utf8NoBOM

$inventory |
    Export-Csv -LiteralPath (Join-Path $OutputRoot 'inventory.csv') -NoTypeInformation -Encoding utf8NoBOM

$inventory | Format-Table ResourcePath, RawBytes, RootType -AutoSize
Write-Output "Extracted $($inventory.Count) resources to $OutputRoot"
