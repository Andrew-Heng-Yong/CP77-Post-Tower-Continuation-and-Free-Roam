param(
    [Parameter(Mandatory = $true)]
    [string[]]$ResourcePaths,
    [Parameter(Mandatory = $true)]
    [string]$OutputRoot,
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0',
    [string[]]$ArchivePaths
)

$ErrorActionPreference = 'Stop'

foreach ($assemblyName in @('WolvenKit.Core.dll', 'WolvenKit.Common.dll', 'WolvenKit.RED4.dll')) {
    [void][System.Reflection.Assembly]::LoadFrom((Join-Path $WolvenKitRoot $assemblyName))
}

$resolvedArchivePaths = if ($ArchivePaths.Count -gt 0) { $ArchivePaths } else { @(
    Get-ChildItem -LiteralPath (Join-Path $GameRoot 'archive\pc\content') -Filter 'basegame_*.archive' -File
    Get-ChildItem -LiteralPath (Join-Path $GameRoot 'archive\pc\ep1') -Filter 'ep1_*.archive' -File
) | Select-Object -ExpandProperty FullName }
$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$wanted = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($path in $ResourcePaths) { [void]$wanted.Add($path) }

$matches = [System.Collections.Generic.List[object]]::new()
foreach ($archivePath in $resolvedArchivePaths) {
    $archiveReader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
    $archive = $null
    $archiveResult = $archiveReader.ReadArchive($archivePath, $hashService, [ref]$archive)
    if ($archiveResult.ToString() -ne 'NoError') {
        throw "Unable to read archive $archivePath`: $archiveResult"
    }
    foreach ($entry in $archive.Files.Values) {
        if ($wanted.Contains($entry.Name)) {
            $matches.Add([pscustomobject]@{ ArchivePath = $archivePath; Entry = $entry })
        }
    }
}

$found = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($match in $matches) { [void]$found.Add($match.Entry.Name) }
$missing = @($ResourcePaths | Where-Object { -not $found.Contains($_) })
if ($missing.Count -gt 0) {
    throw "Resources not found: $($missing -join ', ')"
}

$rawRoot = Join-Path $OutputRoot 'raw'
$jsonRoot = Join-Path $OutputRoot 'json'
New-Item -ItemType Directory -Force -Path $rawRoot, $jsonRoot | Out-Null

$inventory = foreach ($match in ($matches | Sort-Object { $_.Entry.Name })) {
    $entry = $match.Entry
    $rawPath = Join-Path $rawRoot $entry.Name
    $jsonPath = Join-Path $jsonRoot ($entry.Name + '.json')
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $rawPath), (Split-Path -Parent $jsonPath) | Out-Null

    $memory = [System.IO.MemoryStream]::new()
    try {
        $entry.Extract($memory)
        $bytes = $memory.ToArray()
        [System.IO.File]::WriteAllBytes($rawPath, $bytes)
        $memory.Position = 0
        $reader = [WolvenKit.RED4.Archive.IO.CR2WReader]::new($memory)
        $resource = $null
        $readResult = $reader.ReadFile([ref]$resource, $true)
        if ($readResult.ToString() -ne 'NoError') {
            throw "Unable to decode $($entry.Name): $readResult"
        }
        $dto = [WolvenKit.Common.Conversion.RedFileDto]::new($resource, $false)
        $options = [WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
        $json = [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($dto, $options)
        [System.IO.File]::WriteAllText($jsonPath, $json, [System.Text.UTF8Encoding]::new($false))
        [pscustomobject]@{
            ResourcePath = $entry.Name
            Archive = $match.ArchivePath
            RawBytes = $bytes.Length
            RootType = $resource.RootChunk.GetType().Name
            RawOutput = [System.IO.Path]::GetRelativePath($OutputRoot, $rawPath)
            JsonOutput = [System.IO.Path]::GetRelativePath($OutputRoot, $jsonPath)
        }
    }
    finally { $memory.Dispose() }
}

$inventory | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $OutputRoot 'inventory.json') -Encoding utf8NoBOM
$inventory | Export-Csv -LiteralPath (Join-Path $OutputRoot 'inventory.csv') -NoTypeInformation -Encoding utf8NoBOM
$inventory | Format-Table ResourcePath, RawBytes, RootType -AutoSize
Write-Output "Extracted $($inventory.Count) resources to $OutputRoot"
