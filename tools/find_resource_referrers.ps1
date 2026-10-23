param(
    [Parameter(Mandatory = $true)]
    [string[]]$Targets,
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0',
    [string]$OutputPath = (Join-Path $PSScriptRoot '..\research\resource_referrers.csv')
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
$failures = [System.Collections.Generic.List[object]]::new()

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
            $memory.Position = 0
            $reader = [WolvenKit.RED4.Archive.IO.CR2WReader]::new($memory)
            $resource = $null
            $readResult = $reader.ReadFile([ref]$resource, $true)
            if ($readResult.ToString() -ne 'NoError') {
                $failures.Add([pscustomobject]@{ Resource = $entry.Name; Error = $readResult.ToString() })
                continue
            }
            $imports = @($resource.GetImports() | ForEach-Object { $_.ToString() })
            foreach ($target in $Targets) {
                if ($imports -contains $target) {
                    $results.Add([pscustomobject]@{
                        Target = $target
                        Referrer = $entry.Name
                        Archive = $archivePath
                    })
                }
            }
        }
        catch {
            $failures.Add([pscustomobject]@{ Resource = $entry.Name; Error = $_.Exception.Message })
        }
        finally {
            $memory.Dispose()
        }
    }
}

$results | Sort-Object Target, Referrer |
    Export-Csv -LiteralPath $OutputPath -NoTypeInformation -Encoding utf8NoBOM
$failurePath = [System.IO.Path]::ChangeExtension($OutputPath, '.failures.csv')
$failures | Sort-Object Resource |
    Export-Csv -LiteralPath $failurePath -NoTypeInformation -Encoding utf8NoBOM

$results | Sort-Object Target, Referrer | Format-Table Target, Referrer -AutoSize
Write-Output "Matches: $($results.Count); decode failures: $($failures.Count)"
