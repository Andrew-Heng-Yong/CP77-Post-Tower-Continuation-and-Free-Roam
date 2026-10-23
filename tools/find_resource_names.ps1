param(
    [Parameter(Mandatory=$true)][string]$Pattern,
    [string]$WolvenKitRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0',
    [string]$ArchiveRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc',
    [int]$Limit = 100,
    [switch]$PathsOnly
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
foreach ($name in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')) {
    [void][Reflection.Assembly]::LoadFrom((Join-Path $WolvenKitRoot $name))
}
$hashes = [WolvenKit.Common.Services.HashService]::new()
$hashes.Load()
$count = 0
foreach ($folder in @('content','ep1')) {
    foreach ($file in (Get-ChildItem -LiteralPath (Join-Path $ArchiveRoot $folder) -Filter '*.archive' -File)) {
        $archive = $null
        $result = ([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hashes,[ref]$archive)
        if ($result.ToString() -ne 'NoError') { throw "Archive read failed: $($file.FullName)" }
        foreach ($entry in $archive.Files.Values) {
            if ($entry.Name -match $Pattern) {
                if ($PathsOnly) { $entry.Name }
                else { [pscustomobject]@{Archive=$file.Name; Resource=$entry.Name} }
                $count++
                if ($count -ge $Limit) { return }
            }
        }
    }
}
