param(
    [Parameter(Mandatory = $true)]
    [string[]]$Strings,
    [switch]$IncludeScenes,
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0',
    [string]$OutputPath = (Join-Path $PSScriptRoot '..\research\q307_analysis\quest_string_matches.csv')
)

$ErrorActionPreference = 'Stop'

foreach ($assemblyName in @('WolvenKit.Core.dll', 'WolvenKit.Common.dll', 'WolvenKit.RED4.dll')) {
    [void][System.Reflection.Assembly]::LoadFrom((Join-Path $WolvenKitRoot $assemblyName))
}

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

    $extensions=@('.quest', '.questphase', '.gamedef')
    if($IncludeScenes){$extensions+= '.scene'}
    $entries = @($archive.Files.Values | Where-Object { $_.Extension -in $extensions })
    Write-Output "Scanning $($entries.Count) quest resources in $archivePath"
    foreach ($entry in $entries) {
        $memory = [System.IO.MemoryStream]::new()
        try {
            $entry.Extract($memory)
            $text = [System.Text.Encoding]::UTF8.GetString($memory.ToArray())
            foreach ($needle in $Strings) {
                if ($text.Contains($needle, [System.StringComparison]::Ordinal)) {
                    $results.Add([pscustomobject]@{
                        String = $needle
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

$results | Sort-Object String, Resource | Export-Csv -LiteralPath $OutputPath -NoTypeInformation -Encoding utf8NoBOM
$results | Sort-Object String, Resource | Format-Table String, Resource -AutoSize
Write-Output "Matches: $($results.Count)"
