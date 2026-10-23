param(
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0',
    [string]$OutputPath = (Join-Path $PSScriptRoot '..\research\q307_analysis\fact_string_referrers.csv')
)

$ErrorActionPreference = 'Stop'

foreach ($assemblyName in @('WolvenKit.Core.dll', 'WolvenKit.Common.dll', 'WolvenKit.RED4.dll')) {
    [void][System.Reflection.Assembly]::LoadFrom((Join-Path $WolvenKitRoot $assemblyName))
}

$facts = @(
    'q307_active',
    'q307_done',
    'q307_finished',
    'q307_2079',
    'q307_point_of_no_return',
    'q307_hub_disabled_except_journal',
    'q307_main_game_killed',
    'q307_start'
)

$archivePaths = @(
    (Join-Path $GameRoot 'archive\pc\ep1\ep1_2_gamedata.archive'),
    (Join-Path $GameRoot 'archive\pc\content\basegame_4_gamedata.archive')
)

$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$results = [System.Collections.Generic.List[object]]::new()

foreach ($archivePath in $archivePaths) {
    $archiveReader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
    $archive = $null
    $archiveResult = $archiveReader.ReadArchive($archivePath, $hashService, [ref]$archive)
    if ($archiveResult.ToString() -ne 'NoError') {
        throw "Unable to read archive $archivePath`: $archiveResult"
    }

    $entries = @($archive.Files.Values | Where-Object { $_.Extension -in @('.quest', '.questphase', '.gamedef') })
    Write-Output "Scanning $($entries.Count) quest resources in $archivePath"
    foreach ($entry in $entries) {
        $memory = [System.IO.MemoryStream]::new()
        try {
            $entry.Extract($memory)
            $text = [System.Text.Encoding]::UTF8.GetString($memory.ToArray())
            foreach ($fact in $facts) {
                if ($text.Contains($fact, [System.StringComparison]::Ordinal)) {
                    $results.Add([pscustomobject]@{
                        Fact = $fact
                        Resource = $entry.Name
                        Archive = $archivePath
                    })
                }
            }
        }
        finally {
            $memory.Dispose()
        }
    }
}

$results |
    Sort-Object Fact, Resource |
    Export-Csv -LiteralPath $OutputPath -NoTypeInformation -Encoding utf8NoBOM

$results | Sort-Object Fact, Resource | Format-Table Fact, Resource -AutoSize
Write-Output "Matches: $($results.Count)"
